extends UiTest
## The settings menu with the controller alone and with the keyboard (docs/plan.md §2.4,
## §2.13): each test changes one setting on its tab, once with pad events and once with key
## events, and checks the game and the save file. The menu opens from the title, so the tree
## is not paused and a test may wait for a frame.

## Tab indexes of SettingsScreen.TABS.
const GRAPHICS: int = 0
const DISPLAY: int = 1
const AUDIO: int = 2
const CONTROLS: int = 3
const ACCESSIBILITY: int = 4
## The pad button and the key of each move in the menu.
const PAD_MOVES: Dictionary[StringName, JoyButton] = {
	&"down": JOY_BUTTON_DPAD_DOWN,
	&"left": JOY_BUTTON_DPAD_LEFT,
	&"right": JOY_BUTTON_DPAD_RIGHT,
	&"accept": JOY_BUTTON_A,
	&"cancel": JOY_BUTTON_B,
	&"tab_prev": JOY_BUTTON_LEFT_SHOULDER,
	&"tab_next": JOY_BUTTON_RIGHT_SHOULDER,
	&"defaults": JOY_BUTTON_Y,
}
const KEY_MOVES: Dictionary[StringName, Key] = {
	&"down": KEY_DOWN,
	&"left": KEY_LEFT,
	&"right": KEY_RIGHT,
	&"accept": KEY_ENTER,
	&"cancel": KEY_ESCAPE,
	&"tab_prev": KEY_Q,
	&"tab_next": KEY_E,
	&"defaults": KEY_BACKSPACE,
}

var _window_size: Vector2i


func before_each() -> void:
	super()
	_window_size = get_window().size


func after_each() -> void:
	super()
	get_window().mode = Window.MODE_WINDOWED
	get_window().size = _window_size


## The tabs change with both devices, B or Esc goes back, and so does a click on the Back
## hint, for a player with only the mouse.
func test_tabs_and_back() -> void:
	for pad: bool in [true, false]:
		Game.screen = &"settings"
		assert_eq(ui.settings.tab, GRAPHICS)
		_move(pad, &"tab_prev")
		assert_eq(ui.settings.tab, ACCESSIBILITY, "tab_prev goes round")
		_move(pad, &"tab_next")
		_move(pad, &"tab_next")
		assert_eq(ui.settings.tab, DISPLAY)
		_move(pad, &"cancel")
		assert_eq(shown(), &"title")
	Game.screen = &"settings"
	var hints: Hints = ui.settings.find_children("*", "Hints", true, false)[0]
	var click: InputEventMouseButton = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	(hints.get_child(0) as Control).gui_input.emit(click)
	assert_eq(shown(), &"title", "a click on the Back hint")


func test_graphics_preset() -> void:
	for pad: bool in [true, false]:
		_open(GRAPHICS, 0)
		_move(pad, &"right")
		assert_eq(Graphics.current, "high")
		_assert_saved("graphics_preset", "high")
		_move(pad, &"left")
		_move(pad, &"left")
		assert_eq(Graphics.current, "low")
		_reset()


func test_ghost() -> void:
	for pad: bool in [true, false]:
		_open(GRAPHICS, 1)
		_move(pad, &"down")
		_move(pad, &"accept")
		_assert_saved("ghost", false)
		_reset()


## Borderless and fullscreen turn the resolution row off. The headless display server has no
## window modes, so the test checks the mode that the settings ask for.
func test_window_mode() -> void:
	for pad: bool in [true, false]:
		_open(DISPLAY, 0)
		_move(pad, &"right")
		assert_eq(Save.settings.window_mode_id(), Window.MODE_FULLSCREEN)
		_assert_saved("window_mode", "borderless")
		await wait_process_frames(1)
		var resolution: OptionRow = ui.settings.content.get_child(1)
		assert_true(resolution.disabled, "no resolution for a window that fills the screen")
		_move(pad, &"right")
		assert_eq(Save.settings.window_mode_id(), Window.MODE_EXCLUSIVE_FULLSCREEN)
		_reset()
		get_window().mode = Window.MODE_WINDOWED


## The headless window is tiny, so the test starts from a 1920 × 1080 window.
func test_resolution() -> void:
	for pad: bool in [true, false]:
		get_window().size = Vector2i(1920, 1080)
		_open(DISPLAY, 1)
		var resolution: OptionRow = ui.settings.content.get_child(1)
		var before: Vector2i = get_window().size
		_move(pad, &"down")
		_move(pad, &"left")
		var after: Vector2i = get_window().size
		assert_lt(after.x * after.y, before.x * before.y, "a smaller window")
		assert_eq(resolution.texts[resolution.index], "%d × %d" % [after.x, after.y])
		_assert_saved("resolution", [after.x, after.y])
		_reset()
		get_window().size = _window_size


func test_frame_cap() -> void:
	for pad: bool in [true, false]:
		_open(DISPLAY, 2)
		_down(pad, 2)
		_move(pad, &"left")
		assert_eq(Engine.max_fps, 240, "one step down from uncapped")
		_assert_saved("frame_cap", 240)
		_reset()


func test_vsync() -> void:
	for pad: bool in [true, false]:
		_open(DISPLAY, 3)
		_down(pad, 3)
		_move(pad, &"accept")
		assert_eq(Save.settings.vsync_mode(), DisplayServer.VSYNC_DISABLED)
		_assert_saved("vsync", false)
		_reset()


## The HDR row shows only where the display can output HDR.
func test_hdr_row_needs_support() -> void:
	_open(DISPLAY, 0)
	var rows: int = ui.settings.content.get_child_count()
	assert_eq(rows, 5 if DisplayServer.window_is_hdr_output_supported() else 4)


func test_volumes() -> void:
	var fields: Array[String] = ["master_volume", "music_volume", "sfx_volume", "ui_volume"]
	var buses: Array[StringName] = [
		AudioBuses.MASTER, AudioBuses.MUSIC, AudioBuses.SFX, AudioBuses.UI
	]
	for pad: bool in [true, false]:
		for row: int in fields.size():
			_open(AUDIO, row)
			_down(pad, row)
			_move(pad, &"left")
			assert_almost_eq(AudioBuses.volume(buses[row]), 0.95, 0.001, fields[row])
			_assert_saved(fields[row], 0.95)
			_reset()


func test_look_sensitivity() -> void:
	for pad: bool in [true, false]:
		_open(CONTROLS, 0)
		_move(pad, &"right")
		assert_almost_eq(PlayerSource.look_sensitivity, 1.25, 0.0001)
		_assert_saved("look_sensitivity", 1.25)
		_reset()


func test_invert_y() -> void:
	for pad: bool in [true, false]:
		_open(CONTROLS, 1)
		_down(pad, 1)
		_move(pad, &"accept")
		assert_true(PlayerSource.invert_y)
		_assert_saved("invert_y", true)
		_reset()


func test_dead_zone() -> void:
	for pad: bool in [true, false]:
		_open(CONTROLS, 2)
		_down(pad, 2)
		_move(pad, &"right")
		assert_almost_eq(InputHub.dead_zone, 0.2, 0.0001)
		_assert_saved("dead_zone", 0.2)
		_reset()


func test_rumble() -> void:
	for pad: bool in [true, false]:
		_open(CONTROLS, 3)
		_down(pad, 3)
		_move(pad, &"accept")
		assert_false(Rumble.enabled)
		_assert_saved("rumble", false)
		_reset()


## A on the Jump row, then Y, binds Y to jump on the pad; Enter, then K, binds K on the
## keyboard. Each keeps the other device's button.
func test_rebind_jump() -> void:
	var row: int = 4 + Bindings.ACTIONS.find(&"jump")
	_open(CONTROLS, row)
	_down(true, row)
	_move(true, &"accept")
	tap_button(JOY_BUTTON_Y)
	assert_eq(InputGlyph.for_action(&"jump", &"pad"), "Y")
	assert_eq(InputGlyph.for_action(&"jump", &"keyboard"), "Space")
	_assert_saved("bindings", {"jump.pad": "button:%d" % JOY_BUTTON_Y})
	_move(false, &"accept")
	tap_key(KEY_K)
	assert_eq(InputGlyph.for_action(&"jump", &"keyboard"), "K")
	assert_eq(InputGlyph.for_action(&"jump", &"pad"), "Y")
	_reset()


## B or Esc while a row waits for a button stops the wait and leaves the settings open.
func test_cancel_a_rebind() -> void:
	var row: int = 4 + Bindings.ACTIONS.find(&"jump")
	for pad: bool in [true, false]:
		_open(CONTROLS, row)
		_down(pad, row)
		_move(pad, &"accept")
		var bind: BindRow = ui.settings.content.get_child(row + 1)
		assert_true(bind.listening)
		_move(pad, &"cancel")
		assert_false(bind.listening)
		assert_eq(shown(), &"settings")
		assert_eq(InputGlyph.for_action(&"jump", &"pad"), "A")
		_move(pad, &"cancel")


func test_camera_shake() -> void:
	for pad: bool in [true, false]:
		_open(ACCESSIBILITY, 0)
		_move(pad, &"accept")
		assert_false(FollowCamera.shake_enabled)
		_assert_saved("camera_shake", false)
		_reset()


func test_colourblind() -> void:
	for pad: bool in [true, false]:
		_open(ACCESSIBILITY, 1)
		_down(pad, 1)
		_move(pad, &"accept")
		assert_true(Palette.colourblind)
		_assert_saved("colourblind", true)
		_reset()


## Y or Backspace puts the settings of the tab back to the defaults and leaves the others.
func test_defaults_reset_the_tab() -> void:
	for pad: bool in [true, false]:
		Save.change_settings({"invert_y": true, "camera_shake": false})
		_open(ACCESSIBILITY, 0)
		_move(pad, &"defaults")
		assert_true(FollowCamera.shake_enabled)
		_assert_saved("camera_shake", true)
		assert_true(Save.settings.invert_y, "another tab keeps its value")
		_reset()


## Opens the settings at tab, starts the device from row 0 of the tab, and checks the row
## count reaches row.
func _open(at: int, row: int) -> void:
	Game.screen = &"settings"
	for _i: int in at:
		tap_button(JOY_BUTTON_RIGHT_SHOULDER)
	assert_eq(ui.settings.tab, at)
	assert_gt(ui.settings.content.get_child_count(), row, "the tab has row %d" % row)


## Sends the pad button or the key of move.
func _move(pad: bool, move: StringName) -> void:
	if pad:
		tap_button(PAD_MOVES[move])
	else:
		tap_key(KEY_MOVES[move])


## Moves the focus down count rows.
func _down(pad: bool, count: int) -> void:
	for _i: int in count:
		_move(pad, &"down")


## Checks that the save file in UiTest.ROOT holds value for field.
func _assert_saved(field: String, value: Variant) -> void:
	var file: SaveGame = SaveGame.new()
	file.dir = ROOT
	file.read()
	# Wrapped in a Dictionary: GUT's asserts take no bare Variant (unsafe_call_argument).
	assert_eq({field: file.settings.to_dict()[field]}, {field: value}, field + " in the file")
	file.free()


## Closes the settings and puts every setting back to its default.
func _reset() -> void:
	Game.screen = &"title"
	Save.change_settings(Settings.new().to_dict())
