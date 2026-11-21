class_name UiTest
extends GutTest
## Base for tests of the HUD and the menus. Each test gets an empty save in user://test_ui/
## and a new Ui that starts as in a new game: no run, and the default screen &"play". So the
## Ui itself shows the title. A test sends controller and keyboard events with
## Input.parse_input_event, as a real pad and keyboard do, and reads the screen from
## Game.snapshot().
##
## The pause screen pauses the scene tree, and GUT cannot wait while it is paused. So a test
## does not await on the pause screen.

const ROOT: String = "user://test_ui"
## Device id of the test events; far above the ids that real pads get.
const PAD: int = 7

var ui: Ui


func before_each() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(ROOT).path_join(SaveGame.FILE))
	Save.dir = ROOT
	Save.read()
	# A menu screen ends a run that an earlier test left. Then &"play" is the state of a new
	# game.
	Game.screen = &"title"
	Game.screen = &"play"
	ui = Ui.new()
	add_child_autofree(ui)


## Ends the run, and puts back the screen, the save and the device of the other tests.
func after_each() -> void:
	Game.screen = &"title"
	Game.screen = &"play"
	Save.dir = "user://"
	Save.read()
	tap_key(KEY_F12)


## Returns the screen that the game state reports.
func shown() -> StringName:
	return Game.snapshot().screen


## Presses and releases a pad button.
func tap_button(button: JoyButton) -> void:
	for pressed: bool in [true, false]:
		var event: InputEventJoypadButton = InputEventJoypadButton.new()
		event.device = PAD
		event.button_index = button
		event.pressed = pressed
		_send(event)


## Presses and releases a key.
func tap_key(key: Key) -> void:
	for pressed: bool in [true, false]:
		var event: InputEventKey = InputEventKey.new()
		event.keycode = key
		event.physical_keycode = key
		event.pressed = pressed
		_send(event)


## Starts level id as the level select does, and returns its run. The run steps only when
## the test steps it.
func start_level(id: StringName) -> LevelRun:
	var run: LevelRun = Game.load_level(id)
	run.auto_step = false
	return run


## Steps run for ticks with one tick of roll input first, which starts the level clock.
func step_run(run: LevelRun, ticks: int) -> void:
	var input: MarbleInput = MarbleInput.new()
	input.move = Vector2(0.0, 0.1)
	run.step(input)
	for _i: int in ticks - 1:
		run.step(MarbleInput.new())


## Finishes run: puts the marble on each gem and then on the finish, one tick each.
func finish_run(run: LevelRun) -> void:
	var stops: Array[LevelObject] = []
	stops.assign(run.objects.filter(func(object: LevelObject) -> bool: return object is Gem))
	stops.append_array(run.objects.filter(func(object: LevelObject) -> bool: return object is Finish))
	step_run(run, 1)
	for stop: LevelObject in stops:
		run.teleport(run.spawn_point(stop), Vector3.ZERO)
		run.step(MarbleInput.new())


func _send(event: InputEvent) -> void:
	Input.parse_input_event(event)
	Input.flush_buffered_events()
