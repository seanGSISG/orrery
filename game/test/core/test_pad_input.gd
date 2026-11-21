extends RunTest
## The Xbox controller through the boundary (docs/plan.md §2.4): pad events go in with
## Input.parse_input_event, as a real pad's do, and come out as MarbleInput, the active
## device in GameState, button glyphs and rumble. test_virtual_pad uses a real uinput device
## and runs only under `just test-pad`.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
## Device id of the test events; far above the ids that real pads get.
const PAD: int = 7
## Vendor and product of tools/pad/virtual_pad.py in a Godot joypad GUID.
const VIRTUAL_PAD_ID: String = "5e0400008e020000"
const BUTTONS: Array[JoyButton] = [JOY_BUTTON_A, JOY_BUTTON_X, JOY_BUTTON_BACK, JOY_BUTTON_START]

var _dead_zone: float = InputHub.dead_zone
var _look_sensitivity: float = PlayerSource.look_sensitivity
var _invert_y: bool = PlayerSource.invert_y
var _rumble_enabled: bool = Rumble.enabled


func after_each() -> void:
	for axis: int in JOY_AXIS_SDL_MAX:
		_axis(axis as JoyAxis, 0.0)
	for button: JoyButton in BUTTONS:
		_button(button, false)
	InputHub.dead_zone = _dead_zone
	PlayerSource.look_sensitivity = _look_sensitivity
	PlayerSource.invert_y = _invert_y
	Rumble.enabled = _rumble_enabled
	Input.stop_joy_vibration(PAD)
	_key(KEY_W)


## The left stick rolls at the strength of the push, rescaled outside the dead zone, and a
## diagonal push keeps its direction.
func test_left_stick_rolls_analog() -> void:
	var zone: float = InputHub.dead_zone
	_axis(JOY_AXIS_LEFT_Y, -0.6)
	var input: MarbleInput = PlayerSource.new().next_input(GameState.new())
	assert_almost_eq(input.move, Vector2(0.0, (0.6 - zone) / (1.0 - zone)), Vector2.ONE * 0.01)
	_axis(JOY_AXIS_LEFT_X, 0.6)
	input = PlayerSource.new().next_input(GameState.new())
	var push: float = Vector2(0.6, 0.6).length()
	assert_almost_eq(input.move.normalized(), Vector2(1, 1).normalized(), Vector2.ONE * 0.01)
	assert_almost_eq(input.move.length(), (push - zone) / (1.0 - zone), 0.01)


## A push inside the dead zone setting rolls nothing; the setting applies at once.
func test_dead_zone_setting_applies() -> void:
	_axis(JOY_AXIS_LEFT_X, 0.25)
	assert_gt(PlayerSource.new().next_input(GameState.new()).move.x, 0.0)
	InputHub.dead_zone = 0.3
	assert_eq(PlayerSource.new().next_input(GameState.new()).move, Vector2.ZERO)


## A jumps; X or RT uses; View restarts; Menu pauses.
func test_buttons_map_to_actions() -> void:
	_button(JOY_BUTTON_A, true)
	_button(JOY_BUTTON_X, true)
	var input: MarbleInput = PlayerSource.new().next_input(GameState.new())
	assert_true(input.jump)
	assert_true(input.use)
	_button(JOY_BUTTON_X, false)
	_axis(JOY_AXIS_TRIGGER_RIGHT, 1.0)
	assert_true(PlayerSource.new().next_input(GameState.new()).use, "RT uses")
	_button(JOY_BUTTON_BACK, true)
	_button(JOY_BUTTON_START, true)
	assert_true(Input.is_action_pressed(&"restart"))
	assert_true(Input.is_action_pressed(&"pause"))


## The right stick turns the camera at the stick rate; sensitivity scales it, invert Y flips
## the pitch.
func test_right_stick_turns_camera() -> void:
	var source: PlayerSource = PlayerSource.new()
	_axis(JOY_AXIS_RIGHT_X, 1.0)
	var yaw: float = _turned(source, 0.5).x
	assert_almost_eq(yaw, -0.5 * PlayerSource.STICK_YAW_RATE, 0.01, "right turns right")
	_axis(JOY_AXIS_RIGHT_X, 0.0)
	_axis(JOY_AXIS_RIGHT_Y, -1.0)
	var pitch: float = _turned(source, 0.1).y
	assert_almost_eq(pitch, 0.1 * PlayerSource.STICK_PITCH_RATE, 0.01, "up looks up")
	PlayerSource.look_sensitivity = 0.5
	PlayerSource.invert_y = true
	pitch = _turned(source, 0.1).y
	assert_almost_eq(pitch, -0.05 * PlayerSource.STICK_PITCH_RATE, 0.01, "inverted, half speed")


## The state reports the device used last: a stick push outside the dead zone or a button
## press takes over; stick drift, a key release and uncaptured mouse motion do not.
func test_state_reports_last_device() -> void:
	watch_signals(InputHub)
	_axis(JOY_AXIS_LEFT_X, 0.1)
	assert_eq(Game.snapshot().input_device, &"keyboard", "drift")
	_axis(JOY_AXIS_LEFT_Y, 0.12)
	assert_eq(Game.snapshot().input_device, &"pad", "diagonal push outside the radial dead zone")
	_key(KEY_W)
	_axis(JOY_AXIS_LEFT_Y, 0.0)
	_axis(JOY_AXIS_LEFT_X, 0.0)
	_axis(JOY_AXIS_LEFT_X, 0.3)
	assert_eq(Game.snapshot().input_device, &"pad", "stick push")
	assert_eq(InputHub.pad, PAD)
	_key(KEY_W)
	assert_eq(Game.snapshot().input_device, &"keyboard", "key press")
	_button(JOY_BUTTON_A, true)
	_send(_key_event(KEY_W, false))
	assert_eq(Game.snapshot().input_device, &"pad", "key release")
	var motion: InputEventMouseMotion = InputEventMouseMotion.new()
	motion.relative = Vector2(20, 0)
	_send(motion)
	# The headless display server cannot capture the mouse, so captured motion is not tested.
	assert_eq(Game.snapshot().input_device, &"pad", "uncaptured mouse")
	assert_signal_emit_count(InputHub, "device_changed", 5)


## Unplugging the active pad mid-game falls back to the keyboard; the next pad press takes
## over again.
func test_unplugging_pad_falls_back_to_keyboard() -> void:
	_button(JOY_BUTTON_A, true)
	Input.joy_connection_changed.emit(PAD, false)
	assert_eq(InputHub.device, &"keyboard")
	assert_eq(InputHub.pad, -1)
	_button(JOY_BUTTON_A, false)
	assert_eq(InputHub.device, &"keyboard", "a release does not take over")
	_button(JOY_BUTTON_A, true)
	assert_eq(InputHub.device, &"pad")


## Landings, bumpers and power-ups rumble the active pad, scaled by strength. Weak feedback,
## keyboard play and the off setting give no rumble.
func test_feedback_rumbles_active_pad() -> void:
	start_run(FLAT)
	_button(JOY_BUTTON_A, true)
	assert_almost_eq(_rumble(&"marble.land", 1.0), Vector2(0.3, 0.7), Vector2.ONE * 0.001)
	assert_almost_eq(_rumble(&"bumper.hit", 0.5), Vector2(0.4, 0.2), Vector2.ONE * 0.001)
	assert_almost_eq(_rumble(&"coil_spring.use", 1.0), Vector2(0.5, 0.8), Vector2.ONE * 0.001)
	assert_eq(_rumble(&"marble.land", 0.05), Vector2.ZERO, "weak")
	assert_eq(_rumble(&"marble.bounce", 1.0), Vector2.ZERO, "not a rumble kind")
	Rumble.enabled = false
	assert_eq(_rumble(&"marble.land", 1.0), Vector2.ZERO, "off")
	Rumble.enabled = true
	_key(KEY_W)
	assert_eq(_rumble(&"marble.land", 1.0), Vector2.ZERO, "keyboard")


## Glyphs name the button of the device used last, from the input map.
func test_glyphs_follow_device() -> void:
	assert_eq(InputGlyph.for_action(&"jump", &"pad"), "A")
	assert_eq(InputGlyph.for_action(&"jump", &"keyboard"), "Space")
	assert_eq(InputGlyph.for_action(&"use", &"pad"), "X")
	assert_eq(InputGlyph.for_action(&"use", &"keyboard"), "LMB")
	assert_eq(InputGlyph.for_action(&"restart", &"pad"), "View")
	assert_eq(InputGlyph.for_action(&"pause", &"pad"), "Menu")
	assert_eq(InputGlyph.for_action(&"roll_forward", &"pad"), "LS")
	assert_eq(InputGlyph.for_action(&"roll_forward", &"keyboard"), "W")
	assert_eq(InputGlyph.for_action(&"look_left", &"keyboard"), "")
	var glyph: InputGlyph = InputGlyph.new()
	glyph.action = &"jump"
	add_child_autofree(glyph)
	var label: Label = glyph.get_child(0) as Label
	assert_eq(label.text, "Space")
	_button(JOY_BUTTON_A, true)
	assert_eq(label.text, "A")


## A virtual Xbox pad on /dev/uinput: Godot sees it, A makes the marble jump, and the left
## stick rolls it. `just test-pad` starts the pad and sets ORRERY_VIRTUAL_PAD=1.
func test_virtual_pad() -> void:
	if OS.get_environment("ORRERY_VIRTUAL_PAD") != "1":
		pending("SKIP: needs a virtual pad on /dev/uinput; run `just test-pad`")
		return
	var pad: int = await _find_virtual_pad(20.0)
	assert_ne(pad, -1, "Godot sees the virtual pad")
	if pad == -1:
		return
	InputHub.use_source(PlayerSource.new())
	start_run(FLAT)
	run.auto_step = true
	var start: Vector3 = run.state.position
	var jumped: bool = false
	var rolled: bool = false
	var end: int = Time.get_ticks_msec() + 20000
	while not (jumped and rolled) and Time.get_ticks_msec() < end:
		await get_tree().physics_frame
		var rising: float = run.state.velocity.dot(run.state.up)
		jumped = jumped or (run.last_input.jump and rising > 1.0)
		var moved: Vector3 = run.state.position - start
		rolled = rolled or (moved - moved.project(run.state.up)).length() > 0.5
	assert_eq(InputHub.device, &"pad")
	assert_true(jumped, "A makes the marble jump")
	assert_true(rolled, "the left stick rolls the marble")


## Waits up to seconds for the virtual pad; returns its device id, or -1.
func _find_virtual_pad(seconds: float) -> int:
	var end: int = Time.get_ticks_msec() + roundi(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		for id: int in Input.get_connected_joypads():
			if Input.get_joy_guid(id).contains(VIRTUAL_PAD_ID):
				return id
		await get_tree().create_timer(0.1).timeout
	return -1


## Steps source for seconds of ticks and returns its camera turn in them (yaw, pitch).
func _turned(source: PlayerSource, seconds: float) -> Vector2:
	var first: MarbleInput = source.next_input(GameState.new())
	var last: MarbleInput = first
	for _i: int in roundi(seconds * Engine.physics_ticks_per_second):
		last = source.next_input(GameState.new())
	return Vector2(last.camera_yaw - first.camera_yaw, last.camera_pitch - first.camera_pitch)


## Emits one feedback on the run and returns the pad's rumble (weak, strong).
func _rumble(kind: StringName, strength: float) -> Vector2:
	Input.stop_joy_vibration(PAD)
	run.feedback.emit(kind, strength, Vector3.ZERO)
	return Input.get_joy_vibration_strength(PAD)


func _axis(axis: JoyAxis, value: float) -> void:
	var event: InputEventJoypadMotion = InputEventJoypadMotion.new()
	event.device = PAD
	event.axis = axis
	event.axis_value = value
	_send(event)


func _button(button: JoyButton, pressed: bool) -> void:
	var event: InputEventJoypadButton = InputEventJoypadButton.new()
	event.device = PAD
	event.button_index = button
	event.pressed = pressed
	_send(event)


## Taps a key, so the keyboard is the device used last.
func _key(key: Key) -> void:
	_send(_key_event(key, true))
	_send(_key_event(key, false))


func _key_event(key: Key, pressed: bool) -> InputEventKey:
	var event: InputEventKey = InputEventKey.new()
	event.physical_keycode = key
	event.pressed = pressed
	return event


func _send(event: InputEvent) -> void:
	Input.parse_input_event(event)
	Input.flush_buffered_events()
