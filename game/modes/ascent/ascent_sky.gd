class_name AscentSky
extends Node3D
## The light of Ascent: one sun and one sky for the whole climb. The time of day follows the
## height (docs/plan.md §2.9). STOPS holds the skies of the climb from the bottom: each sky
## preset shows in full at its height, and between two stops show_height() blends from the lower
## preset to the upper one. Now the climb starts in the ground dawn, a town on the Earth at dawn,
## and reaches noon at NOON_HEIGHT, the top of zone 3. Zones 1 to 3 are on the Earth only. M2
## adds the stops of the higher zones (the sunset, the stars).
##
## The presets are SkyPresets (res://skies/). The environment and the sun are those that the
## first preset makes, so the tonemap, the glow and the haze are as in a level. _apply() is the
## one place that blends two presets: the panoramas (ascent_sky.gdshader), the sun, the exposure
## and the haze. The Graphics autoload gives the environment and the sun the graphics preset, as
## it does for a level's own.
##
## The climb has no lightmap, so no bounce light. The fill of the first preset stands in for it
## at every height: the light that sunlit stone throws into the shade. Bounce light grows with
## the sunlight on the ground, so _apply() scales the fill by the sunlight on a floor. The noon
## sky gives a floor little light, so without this the shade goes near black as the sun rises.

const SHADER: Shader = preload("res://modes/ascent/ascent_sky.gdshader")
const GROUND_DAWN: SkyPreset = preload("res://skies/ground_dawn.tres")
const NOON: SkyPreset = preload("res://skies/noon.tres")
## The height at which the sky is NOON in full: the top of zone 3, m.
const NOON_HEIGHT: float = 500.0
## The skies of the climb: each preset at its height above the climb start, m. The heights rise,
## and the first is the climb start.
const STOPS: Dictionary[float, SkyPreset] = {0.0: GROUND_DAWN, NOON_HEIGHT: NOON}
## The light changes when the height is this far from the height of the last change, m. Each
## change makes Godot draw the light of the sky again, so it does not happen every tick.
const STEP: float = 1.0

## The sun's elevation now, degrees.
var elevation: float = 0.0

var _first: SkyPreset = STOPS.values().front()
var _sun: DirectionalLight3D = _first.sun()
var _environment: Environment = _first.environment()
var _material: ShaderMaterial = ShaderMaterial.new()
## The sun angles of now, in a preset, so that SkyPreset.to_sun() gives the direction.
var _now: SkyPreset = SkyPreset.new()
## The sunlight on a floor at the first stop: the sun's energy times the sine of its elevation.
var _first_light: float = _first.sun_energy * _first.to_sun().y
## The heights of the first and the last stop, m.
var _bottom: float = STOPS.keys().front()
var _top: float = STOPS.keys().back()
## The height of the last change, from _bottom to _top; INF before the first.
var _shown: float = INF


## Builds the sun and the sky of the first stop, with the blend shader in place of its panorama.
func _init() -> void:
	_material.shader = SHADER
	_environment.sky.sky_material = _material
	# The light of the sky follows a change over a few frames, with no long frame.
	_environment.sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = &"sky"
	world.environment = _environment
	add_child(world)
	_sun.name = &"sun"
	add_child(_sun)
	show_height(_bottom)


## Shows the time of day of height, m above the climb start. Below the first stop it shows the
## first sky, and above the last stop the last sky. A change of less than STEP waits, but not
## the change that reaches the first or the last stop. Outside them nothing changes.
func show_height(height: float) -> void:
	var at: float = clampf(height, _bottom, _top)
	var end: bool = at == _bottom or at == _top
	if at == _shown or (absf(at - _shown) < STEP and not end):
		return
	_shown = at
	_apply(at)


## Writes the light of height to the sky, the sun and the environment: the blend of the two
## stops round it, by the share of the way from the lower stop to the upper one.
func _apply(height: float) -> void:
	var low: float = _bottom
	var high: float = _bottom
	for stop: float in STOPS:
		high = stop
		if stop >= height:
			break
		low = stop
	var lower: SkyPreset = STOPS[low]
	var upper: SkyPreset = STOPS[high]
	var weight: float = inverse_lerp(low, high, height) if high > low else 0.0
	_material.set_shader_parameter(&"from_panorama", lower.panorama)
	_material.set_shader_parameter(&"to_panorama", upper.panorama)
	_material.set_shader_parameter(&"from_energy", lower.sky_energy)
	_material.set_shader_parameter(&"to_energy", upper.sky_energy)
	_material.set_shader_parameter(&"blend", weight)
	elevation = lerpf(lower.sun_elevation, upper.sun_elevation, weight)
	_now.sun_elevation = elevation
	_now.sun_azimuth = lerpf(lower.sun_azimuth, upper.sun_azimuth, weight)
	_sun.basis = Basis.looking_at(-_now.to_sun())
	_sun.light_color = lower.sun_color.lerp(upper.sun_color, weight)
	_sun.light_energy = lerpf(lower.sun_energy, upper.sun_energy, weight)
	# The fill of the first preset, scaled by the sunlight on a floor. The energy scales the fill
	# colour only, not the light of the sky.
	_environment.ambient_light_energy = _sun.light_energy * _now.to_sun().y / _first_light
	_environment.tonemap_exposure = lerpf(lower.exposure, upper.exposure, weight)
	# The haze, shared between the distance fog and the volumetric fog as GraphicsPreset does.
	var haze: float = lerpf(lower.fog_density, upper.fog_density, weight)
	var volumetric: float = haze * GraphicsPreset.VOLUMETRIC_FOG_SHARE
	_environment.set_meta(GraphicsPreset.HAZE, haze)
	_environment.volumetric_fog_density = volumetric
	_environment.fog_density = haze - volumetric if _environment.volumetric_fog_enabled else haze
