extends Node
## Saves one screenshot of each UI screen, for a review of the look. `just ui-shots` runs it
## in gamescope at 1920 × 1080 and 3840 × 2160 and writes build/ui/<height>/<name>.png:
##     godot --audio-driver Dummy --path game --resolution 1920x1080
##         res://test/ui/ui_shots.tscn -- --out <dir>
## The Dummy audio driver keeps the run silent.
##
## It runs the real main scene with a demo save in user://ui-shots/, so the player's save is
## not touched. It changes the screen through Game, as the menus do. Without `--out` it saves
## to user://ui-shots/.

## Frames to wait before a screenshot, so that fonts, shaders and the backdrop are ready.
const SETTLE: int = 12
const SAVE_DIR: String = "user://ui-shots"
## The level of the HUD, pause and results screenshots.
const LEVEL: StringName = &"core_loop"

var _out: String = SAVE_DIR
## Screenshots that could not be saved.
var _failed: int = 0


## Goes through the screens in the order of a play session, saves each, and quits. It prints
## "ui-shots: done" when every screenshot is saved, and quits with 1 when one is not.
func _ready() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var at: int = args.find("--out")
	if at >= 0 and at + 1 < args.size():
		_out = args[at + 1]
	_load_demo_save()
	add_child((load("res://main.tscn") as PackedScene).instantiate())
	_use_pad(true)
	await _save("title")
	Game.screen = &"level_select"
	await _save("level_select_locked")
	_press(&"tab_next")
	_press(&"ui_left")
	_press(&"ui_left")
	await _save("level_select")
	Game.screen = &"title"
	Game.screen = &"settings"
	for tab: String in ["graphics", "display", "audio", "controls", "accessibility"]:
		if tab != "graphics":
			_press(&"tab_next")
		await _save("settings_" + tab)
	_press(&"tab_prev")
	# D-pad events, not actions: the focus moves only for a real button.
	for _i: int in 9:
		for pressed: bool in [true, false]:
			var down: InputEventJoypadButton = InputEventJoypadButton.new()
			down.button_index = JOY_BUTTON_DPAD_DOWN
			down.pressed = pressed
			Input.parse_input_event(down)
		Input.flush_buffered_events()
		await get_tree().process_frame
	await _save("settings_controls_buttons")
	var run: LevelRun = Game.load_level(LEVEL)
	run.auto_step = false
	_play(run, 12.4)
	await _save("hud_empty")
	run.slot.take(CoilSpringPowerUp.new(20.0))
	_play(run, 0.1)
	await _save("hud")
	_use_pad(false)
	await _save("hud_keys")
	_use_pad(true)
	Game.screen = &"pause"
	await _save("pause")
	Game.screen = &"play"
	_finish(run)
	await _save("results")
	await _save_ascent()
	# `just ui-shots` looks for this line: gamescope does not pass the exit code on.
	if _failed == 0:
		print("ui-shots: done")
	get_tree().quit(mini(_failed, 1))


## Saves the Ascent screens: the menu with a saved climb, the HUD of a climb with the height
## meter, its pause menu and the stats at the gate. The climb is of the built zones of the
## game, or of the fixture zones while none is built.
func _save_ascent() -> void:
	var zones: Array[StringName] = Ascent.zones()
	if zones.is_empty():
		zones = Ascent.FIXTURE
	var ui: Ui = get_tree().root.find_child("Ui", true, false) as Ui
	ui.ascent.zones = zones
	Save.finish(Ascent.record_id(zones), 552.4, &"none", null)
	Save.ascent.has_spot = true
	Save.ascent.spot_zones = ",".join(PackedStringArray(zones))
	Save.ascent.spot_height = 132.0
	Save.ascent.spot_time = 431.27
	Save.ascent.best_height = 187.0
	Game.screen = &"ascent"
	await _save("ascent")
	var run: LevelRun = Ascent.start(true, zones)
	if run == null:
		push_error("ui-shots: no Ascent zone is built")
		_failed += 1
		return
	run.auto_step = false
	var climb: Ascent = Ascent.of(run)
	# The marble stands a little above the start of the second zone, under its best height.
	Save.ascent.best_height = lerpf(climb.zone_heights[-1], climb.top, 0.5)
	_play(run, 0.5)
	run.teleport(climb.start_of(mini(1, climb.zone_heights.size() - 1)), Vector3.ZERO)
	_play(run, 61.3)
	await _save("hud_ascent")
	Game.screen = &"pause"
	await _save("pause_ascent")
	Game.screen = &"play"
	_finish(run)
	await _save("ascent_stats")


## Points Save at a new demo save: some medals and best times in the test tier, and the egg
## of LEVEL.
func _load_demo_save() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_DIR).path_join(SaveGame.FILE))
	Save.dir = SAVE_DIR
	Save.read()
	Save.settings.apply()
	Save.finish(LEVEL, 21.84, &"qualified", null)
	Save.find_egg(LEVEL, &"egg_00")
	Save.finish(&"feel", 46.82, &"gold", null)
	Save.finish(&"fixture", 8.05, &"gold", null)
	Save.finish(&"floors", 73.5, &"none", null)
	Save.finish(&"movers", 31.27, &"qualified", null)


## Makes the pad, or the keyboard, the device used last, so that the glyphs show its buttons.
func _use_pad(pad: bool) -> void:
	for pressed: bool in [true, false]:
		if pad:
			var button: InputEventJoypadButton = InputEventJoypadButton.new()
			button.button_index = JOY_BUTTON_Y
			button.pressed = pressed
			Input.parse_input_event(button)
		else:
			var key: InputEventKey = InputEventKey.new()
			key.physical_keycode = KEY_F12
			key.pressed = pressed
			Input.parse_input_event(key)
	Input.flush_buffered_events()


## Presses and releases the input action.
func _press(action: StringName) -> void:
	for pressed: bool in [true, false]:
		var event: InputEventAction = InputEventAction.new()
		event.action = action
		event.pressed = pressed
		Input.parse_input_event(event)
	Input.flush_buffered_events()


## Starts the level clock with one tick of roll input, then lets seconds of level time pass.
func _play(run: LevelRun, seconds: float) -> void:
	var input: MarbleInput = MarbleInput.new()
	input.camera_pitch = PlayerSource.START_PITCH
	input.move = Vector2(0.0, 0.1)
	run.step(input)
	input.move = Vector2.ZERO
	for _i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(input)


## Puts the marble on each gem and then on the finish, so that the run finishes.
func _finish(run: LevelRun) -> void:
	var stops: Array[LevelObject] = []
	stops.assign(run.objects.filter(func(object: LevelObject) -> bool: return object is Gem))
	stops.append_array(run.objects.filter(func(object: LevelObject) -> bool: return object is Egg))
	stops.append_array(run.objects.filter(func(object: LevelObject) -> bool: return object is Finish))
	for stop: LevelObject in stops:
		run.teleport(run.spawn_point(stop), Vector3.ZERO)
		run.step(run.last_input)


## Waits for the screen to settle and saves the frame as <out>/<name>.png.
func _save(name: String) -> void:
	for _i: int in SETTLE:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path: String = ProjectSettings.globalize_path(_out).path_join(name + ".png")
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var error: Error = get_viewport().get_texture().get_image().save_png(path)
	print("ui-shots: %s %s" % [path, error_string(error)])
	if error != OK:
		_failed += 1
