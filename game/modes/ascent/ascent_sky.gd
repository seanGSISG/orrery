class_name AscentSky
extends Node3D
## The light of Ascent: one sun and one sky for the whole climb. The time of day follows the
## height (docs/plan.md §2.9): show_height() blends the sun, the sky colours and the exposure
## between the hours of HOURS. Zones 1 to 3 are on Earth, from dawn at the town square to noon
## at the gate; M2 adds the hours of the higher zones (sunset, the stars) to HOURS.
##
## The Graphics autoload gives the environment and the sun the graphics preset, as it does
## for a level's own. To use other skies (the tier skies of the look baseline, #24), change
## _apply(): it is the only place that writes the sun and the environment.

## The light changes when the height is this far from the height of the last change, m. Each
## change makes Godot draw the sky's light again, so it does not happen every tick.
const STEP: float = 1.0
## The time of day at a height: the sun's elevation and compass turn, degrees, its colour and
## energy, the sky colours and the exposure. Sorted by height.
const HOURS: Array[Dictionary] = [
	{
		"height": 0.0,
		"elevation": 12.0,
		"turn": 78.0,
		"sun": Color(1.0, 0.74, 0.54),
		"energy": 0.95,
		"top": Color(0.27, 0.37, 0.62),
		"horizon": Color(0.96, 0.72, 0.55),
		"exposure": 1.05,
	},
	{
		"height": 150.0,
		"elevation": 30.0,
		"turn": 62.0,
		"sun": Color(1.0, 0.87, 0.73),
		"energy": 1.1,
		"top": Color(0.25, 0.42, 0.74),
		"horizon": Color(0.84, 0.8, 0.78),
		"exposure": 1.0,
	},
	{
		"height": 500.0,
		"elevation": 62.0,
		"turn": 35.0,
		"sun": Color(1.0, 0.97, 0.92),
		"energy": 1.25,
		"top": Color(0.22, 0.44, 0.84),
		"horizon": Color(0.7, 0.8, 0.92),
		"exposure": 1.0,
	},
]

## The sun's elevation now, degrees. A test reads it.
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
	# The sky's light follows a change over a few frames, with no long frame.
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


## Shows the time of day of height, m above the climb start.
func show_height(height: float) -> void:
	if absf(height - _shown) < STEP:
		return
	_shown = height
	var last: int = HOURS.size() - 1
	var next: int = 1
	while next < last and height > _number(HOURS[next], "height"):
		next += 1
	var from: Dictionary = HOURS[next - 1]
	var to: Dictionary = HOURS[next]
	var span: float = _number(to, "height") - _number(from, "height")
	_apply(from, to, clampf((height - _number(from, "height")) / span, 0.0, 1.0))


## Writes the blend of the hours from and to (weight 0 is from, 1 is to) to the sun and the
## environment.
func _apply(from: Dictionary, to: Dictionary, weight: float) -> void:
	elevation = lerpf(_number(from, "elevation"), _number(to, "elevation"), weight)
	var turn: float = lerpf(_number(from, "turn"), _number(to, "turn"), weight)
	_sun.rotation_degrees = Vector3(-elevation, turn, 0.0)
	_sun.light_color = _color(from, "sun").lerp(_color(to, "sun"), weight)
	_sun.light_energy = lerpf(_number(from, "energy"), _number(to, "energy"), weight)
	var horizon: Color = _color(from, "horizon").lerp(_color(to, "horizon"), weight)
	_material.sky_top_color = _color(from, "top").lerp(_color(to, "top"), weight)
	_material.sky_horizon_color = horizon
	_material.ground_horizon_color = horizon
	_environment.tonemap_exposure = lerpf(_number(from, "exposure"), _number(to, "exposure"), weight)


## Returns the number of key in hour.
static func _number(hour: Dictionary, key: String) -> float:
	var value: float = hour[key]
	return value


## Returns the colour of key in hour.
static func _color(hour: Dictionary, key: String) -> Color:
	var value: Color = hour[key]
	return value
