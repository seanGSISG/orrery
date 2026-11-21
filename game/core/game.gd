extends Node
## Autoload Game: loads levels and gives the observable snapshot. The `restart` action
## restarts the current run. #22 adds the menu screens. It has no class_name, because a
## class_name would hide the autoload.

const BUILT_LEVEL: String = "res://levels/built/%s.glb"
const TEST_LEVEL: String = "res://test/levels/%s.tscn"

## The current run; null in menus.
var run: LevelRun
var screen: StringName = &"play"


## Replaces the current run with a run of level id that has a follow camera. Loads the built
## level res://levels/built/<id>.glb, else the test level res://test/levels/<id>.tscn.
## Returns null when neither exists.
func load_level(id: StringName) -> LevelRun:
	var path: String = BUILT_LEVEL % id
	if not ResourceLoader.exists(path):
		path = TEST_LEVEL % id
	if not ResourceLoader.exists(path):
		push_error("Game.load_level: no level named %s" % id)
		return null
	if run != null:
		remove_child(run)
		run.queue_free()
	var scene: PackedScene = load(path) as PackedScene
	run = LevelRun.create(scene.instantiate() as Level)
	var camera: FollowCamera = FollowCamera.new()
	camera.run = run
	run.add_child(camera)
	add_child(run)
	camera.make_current()
	return run


## Returns the run's state (or a new GameState in menus) with screen and input_device set.
func snapshot() -> GameState:
	var state: GameState = run.state if run != null else GameState.new()
	state.screen = screen
	state.input_device = InputHub.device
	return state


func _unhandled_input(event: InputEvent) -> void:
	if run != null and event.is_action_pressed(&"restart"):
		run.restart()
