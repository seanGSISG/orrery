class_name Backdrop
extends Node3D
## The live scene behind the menus while no level runs: one built level, with a camera that
## turns slowly round it. Ui adds it for the title, the level select and the settings, and
## frees it when a level loads. Nothing steps the level, so its objects stand still. With no
## scene for LEVEL, the menus show on the plain clear colour.

## The level to show.
const LEVEL: StringName = &"core_loop"
## Seconds for one turn of the camera.
const PERIOD: float = 240.0
## The camera's distance and height, as parts of the level's size.
const DISTANCE: float = 0.8
const HEIGHT: float = 0.3

var _camera: Camera3D
var _center: Vector3 = Vector3.ZERO
var _radius: float = 10.0
var _time: float = 0.0


## Adds the level and the camera, and measures the level. With no level scene it adds
## nothing, and _process() stays off.
func _ready() -> void:
	set_process(false)
	var path: String = Game.level_path(LEVEL)
	var scene: PackedScene = load(path) as PackedScene if path != "" else null
	if scene == null:
		return
	var level: Node3D = scene.instantiate() as Node3D
	add_child(level)
	var bounds: AABB = AABB()
	for node: Node in level.find_children("*", "VisualInstance3D", true, false):
		var visual: VisualInstance3D = node as VisualInstance3D
		var box: AABB = visual.global_transform * visual.get_aabb()
		bounds = box if bounds.size == Vector3.ZERO else bounds.merge(box)
	_center = bounds.get_center()
	_radius = maxf(bounds.size.length() * 0.5, 4.0)
	_camera = Camera3D.new()
	_camera.fov = 50.0
	add_child(_camera)
	_camera.make_current()
	set_process(true)
	_process(0.0)


## Turns the camera round the level.
func _process(delta: float) -> void:
	_time += delta
	var turn: float = _time / PERIOD * TAU
	var offset: Vector3 = Vector3(sin(turn), 0.0, cos(turn)) * _radius * DISTANCE
	_camera.position = _center + offset + Vector3.UP * _radius * HEIGHT
	_camera.look_at(_center + Vector3.DOWN * _radius * 0.1)
