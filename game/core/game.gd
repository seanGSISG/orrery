extends Node
## Autoload Game: the game flow. It loads levels, holds the screen that shows, and gives the
## observable snapshot. The `restart` action restarts the current run. It has no class_name,
## because a class_name would hide the autoload.
##
## Screens: &"title", &"level_select" and &"settings" are menus; &"play" is the level with
## the HUD; &"pause" and &"results" lie over a level. Set `screen` to change it; game/ui/ui.gd
## shows it. The rules of a change are in _apply_screen().

## Emitted after `screen` changes.
signal screen_changed(screen: StringName)

const BUILT_LEVEL: String = "res://levels/built/%s.glb"
const TEST_LEVEL: String = "res://test/levels/%s.tscn"
## The screens that have no run: to show one ends the current run.
const MENU_SCREENS: Array[StringName] = [&"title", &"level_select"]
## The screens of a run on which the `restart` action works.
const RUN_SCREENS: Array[StringName] = [&"play", &"pause", &"results"]

## The current run; null in menus.
var run: LevelRun
## The screen that shows. It stays &"play" when nothing shows screens (tests, `just feel`).
var screen: StringName = &"play":
	set(value):
		if value == screen:
			return
		screen = value
		_apply_screen()
		screen_changed.emit(screen)

## True while the results hold a run that stepped itself before; &"play" lets it step again.
var _held: bool = false


## Keeps the `restart` action working while the game is paused.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


## Returns the scene file of level id: the built level res://levels/built/<id>.glb, else the
## test level res://test/levels/<id>.tscn. Returns "" when neither exists.
func level_path(id: StringName) -> String:
	for pattern: String in [BUILT_LEVEL, TEST_LEVEL]:
		if ResourceLoader.exists(pattern % id):
			return pattern % id
	return ""


## Replaces the current run with a run of level id that has a follow camera, and shows the
## &"play" screen. Returns null, and keeps the current run and screen, when level id has no
## scene (see level_path()) or the scene root is not a Level.
func load_level(id: StringName) -> LevelRun:
	var path: String = level_path(id)
	var scene: PackedScene = load(path) as PackedScene if path != "" else null
	var root: Node = scene.instantiate() if scene != null else null
	var level: Level = root as Level
	if level == null:
		push_error("Game.load_level: no Level scene for %s" % id)
		if root != null:
			root.free()
		return null
	_end_run()
	run = LevelRun.create(level)
	# Game runs in pause, but its run must not.
	run.process_mode = Node.PROCESS_MODE_PAUSABLE
	var camera: FollowCamera = FollowCamera.new()
	camera.run = run
	run.add_child(camera)
	add_child(run)
	camera.make_current()
	screen = &"play"
	_apply_screen()
	return run


## Starts the current run again at once and shows it. Does nothing with no run.
func restart() -> void:
	if run == null:
		return
	run.restart()
	screen = &"play"


## Returns the run's state (or a new GameState in menus) with screen and input_device set.
func snapshot() -> GameState:
	var state: GameState = run.state if run != null else GameState.new()
	state.screen = screen
	state.input_device = InputHub.device
	return state


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"restart") and screen in RUN_SCREENS:
		restart()


## Makes the run and the scene tree fit `screen`:
## - a menu screen ends the run;
## - the tree is paused under &"pause" and under &"settings" over a run, so the run and the
##   sound effects stop (docs/design/audio.md);
## - &"results" does not pause, so the finish sound plays out. A run that steps itself stops
##   there, and steps again on &"play". A run that its caller steps (auto_step false) stays
##   with its caller.
func _apply_screen() -> void:
	if screen in MENU_SCREENS:
		_end_run()
	if run != null and screen == &"results" and run.auto_step:
		run.auto_step = false
		_held = true
	elif run != null and screen == &"play" and _held:
		run.auto_step = true
		_held = false
	get_tree().paused = run != null and screen not in [&"play", &"results"]


## Frees the current run, if there is one.
func _end_run() -> void:
	_held = false
	if run != null:
		remove_child(run)
		run.queue_free()
		run = null
