class_name AscentSky
extends Node3D
## The light of Ascent: one sun and one sky for the whole climb. The time of day follows the
## height (docs/plan.md §2.9): show_height() blends the sun, the sky and the exposure from one
## AscentHour to the next. Zones 1 to 3 are on the Earth: dawn at the town square, morning at
## the top of zone 1 and noon at the gate. M2 adds the hours of the higher zones (the sunset,
## the stars) to HOURS.
##
## The Graphics autoload gives the environment and the sun the graphics preset, as it does
## for a level's own. To light the climb with other skies (the tier skies of the look
## baseline, #24), change _apply(): it is the only place that writes the sun and the
## environment.

## The hours of the climb, from the bottom.
const HOURS: Array[AscentHour] = [
	preload("res://modes/ascent/hours/dawn.tres"),
	preload("res://modes/ascent/hours/morning.tres"),
	preload("res://modes/ascent/hours/noon.tres"),
]
## The light changes when the height is this far from the height of the last change, m. Each
## change makes Godot draw the light of the sky again, so it does not happen every tick.
const STEP: float = 1.0

## The sun's elevation now, degrees.
var elevation: float = 0.0

var _sun: DirectionalLight3D = DirectionalLight3D.new()
var _material: ProceduralSkyMaterial = ProceduralSkyMaterial.new()
var _environment: Environment = Environment.new()
## The height of the last change; INF before the first.
var _shown: float = INF


## Builds the sun and the sky, at the first hour.
func _init() -> void:
	var sky: Sky = Sky.new()
	sky.sky_material = _material
	# The light of the sky follows a change over a few frames, with no long frame.
	sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	_environment.background_mode = Environment.BG_SKY
	_environment.sky = sky
	_environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	# A light haze for the presets that turn volumetric fog on; the default washes out the sky.
	_environment.volumetric_fog_density = 0.002
	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = &"sky"
	world.environment = _environment
	add_child(world)
	_sun.name = &"sun"
	_sun.shadow_enabled = true
	add_child(_sun)
	show_height(0.0)


## Shows the time of day of height, m above the climb start. Below the first hour and above
## the last, it shows that hour.
func show_height(height: float) -> void:
	if absf(height - _shown) < STEP:
		return
	_shown = height
	var next: int = 1
	while next < HOURS.size() - 1 and height > HOURS[next].height:
		next += 1
	var from: AscentHour = HOURS[next - 1]
	var to: AscentHour = HOURS[next]
	_apply(from, to, clampf(inverse_lerp(from.height, to.height, height), 0.0, 1.0))


## Writes the blend of two hours to the sun and the environment: weight 0 is from, 1 is to.
func _apply(from: AscentHour, to: AscentHour, weight: float) -> void:
	elevation = lerpf(from.elevation, to.elevation, weight)
	_sun.rotation_degrees = Vector3(-elevation, lerpf(from.turn, to.turn, weight), 0.0)
	_sun.light_color = from.sun_color.lerp(to.sun_color, weight)
	_sun.light_energy = lerpf(from.sun_energy, to.sun_energy, weight)
	var horizon: Color = from.sky_horizon.lerp(to.sky_horizon, weight)
	_material.sky_top_color = from.sky_top.lerp(to.sky_top, weight)
	_material.sky_horizon_color = horizon
	_material.ground_horizon_color = horizon
	_material.ground_bottom_color = from.sky_below.lerp(to.sky_below, weight)
	_environment.background_energy_multiplier = lerpf(from.sky_energy, to.sky_energy, weight)
	_environment.tonemap_exposure = lerpf(from.exposure, to.exposure, weight)
