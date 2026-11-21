extends GutTest
## The keyboard reaches MarbleInput through the project's input actions.

const KEYS: Array[Key] = [KEY_W, KEY_D, KEY_SPACE]


func after_each() -> void:
	for key: Key in KEYS:
		_press(key, false)


## W and D roll forward and right at full length; Space holds jump.
func test_keys_fill_marble_input() -> void:
	for key: Key in KEYS:
		_press(key, true)
	var input: MarbleInput = PlayerSource.new().next_input(GameState.new())
	assert_almost_eq(input.move, Vector2(1, 1).normalized(), Vector2.ONE * 0.001)
	assert_true(input.jump)
	assert_false(input.use)


func _press(key: Key, pressed: bool) -> void:
	var event: InputEventKey = InputEventKey.new()
	event.physical_keycode = key
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()
