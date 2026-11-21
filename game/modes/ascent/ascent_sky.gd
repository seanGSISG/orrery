class_name AscentSky
extends Node3D
## The light of Ascent: one sun and one sky for the whole climb. The time of day follows the
## height (docs/plan.md §2.9): show_height() blends from the sky preset DAWN at the climb
## start to NOON at NOON_HEIGHT, the top of zone 3. Zones 1 to 3 are on the Earth only. M2
## adds the skies of the higher zones (the sunset, the stars).
##
## The presets are the tier skies of the look baseline (res://skies/, SkyPreset). The
## environment and the sun are those that DAWN makes, so the tonemap, the glow and the haze
## are as in a level. _apply() is the one place that blends the values of the two presets:
## the panoramas (ascent_sky.gdshader), the sun, the fill light, the exposure and the haze.
## The Graphics autoload gives the environment and the sun the graphics preset, as it does for
## a level's own.

const SHADER: Shader = preload("res://modes/ascent/ascent_sky.gdshader")
const DAWN: SkyPreset = preload("res://skies/dawn.tres")
const NOON: SkyPreset = preload("res://skies/noon.tres")
## The height at which the sky is NOON in full: the top of zone 3, m.
const NOON_HEIGHT: float = 500.0
## The light changes when the height is this far from the height of the last change, m. Each
## change makes Godot draw the light of the sky again, so it does not happen every tick.
const STEP: float = 1.0

## The sun's elevation now, degrees.
var elevation: float = 0.0

var _sun: DirectionalLight3D = DAWN.sun()
var _environment: Environment = DAWN.environment()
var _material: ShaderMaterial = ShaderMaterial.new()
## The sun angles of now, in a preset, so that SkyPreset.to_sun() gives the direction.
var _now: SkyPreset = SkyPreset.new()
## The height of the last change, from 0 to NOON_HEIGHT; INF before the first.
var _shown: float = INF


## Builds the sun and the sky of DAWN, with the blend shader in place of its panorama.
func _init() -> void:
	_material.shader = SHADER
	_material.set_shader_parameter(&"from_panorama", DAWN.panorama)
	_material.set_shader_parameter(&"to_panorama", NOON.panorama)
	_material.set_shader_parameter(&"from_energy", DAWN.sky_energy)
	_material.set_shader_parameter(&"to_energy", NOON.sky_energy)
	_environment.sky.sky_material = _material
	# The light of the sky follows a change over a few frames, with no long frame.
	_environment.sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = &"sky"
	world.environment = _environment
	add_child(world)
	_sun.name = &"sun"
	add_child(_sun)
	show_height(0.0)


## Shows the time of day of height, m above the climb start. Below the climb start it shows
## DAWN, and above NOON_HEIGHT it shows NOON. A change of less than STEP waits, but not the
## change that reaches one of the two ends. Outside the ends nothing changes.
func show_height(height: float) -> void:
	var at: float = clampf(height, 0.0, NOON_HEIGHT)
	var end: bool = at == 0.0 or at == NOON_HEIGHT
	if at == _shown or (absf(at - _shown) < STEP and not end):
		return
	_shown = at
	_apply(at / NOON_HEIGHT)


## Writes the blend of DAWN and NOON to the sky, the sun and the environment: weight 0 is
## DAWN, 1 is NOON.
func _apply(weight: float) -> void:
	_material.set_shader_parameter(&"blend", weight)
	elevation = lerpf(DAWN.sun_elevation, NOON.sun_elevation, weight)
	_now.sun_elevation = elevation
	_now.sun_azimuth = lerpf(DAWN.sun_azimuth, NOON.sun_azimuth, weight)
	_sun.basis = Basis.looking_at(-_now.to_sun())
	_sun.light_color = DAWN.sun_color.lerp(NOON.sun_color, weight)
	_sun.light_energy = lerpf(DAWN.sun_energy, NOON.sun_energy, weight)
	_environment.ambient_light_sky_contribution = lerpf(DAWN.sky_share, NOON.sky_share, weight)
	_environment.ambient_light_color = DAWN.fill_color.lerp(NOON.fill_color, weight)
	_environment.tonemap_exposure = lerpf(DAWN.exposure, NOON.exposure, weight)
	# The haze, shared between the distance fog and the volumetric fog as GraphicsPreset does.
	var haze: float = lerpf(DAWN.fog_density, NOON.fog_density, weight)
	var volumetric: float = haze * GraphicsPreset.VOLUMETRIC_FOG_SHARE
	_environment.set_meta(GraphicsPreset.HAZE, haze)
	_environment.volumetric_fog_density = volumetric
	_environment.fog_density = haze - volumetric if _environment.volumetric_fog_enabled else haze
