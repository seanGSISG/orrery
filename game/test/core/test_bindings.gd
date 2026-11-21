extends GutTest
## Bindings: the codes of the bindable events, and apply(), which replaces an action's
## buttons on the bound device only (docs/plan.md §2.4).


func after_each() -> void:
	Bindings.apply({})


## Each kind of event gives a code, and the code gives back the same button.
func test_code_round_trip() -> void:
	var key: InputEventKey = InputEventKey.new()
	key.physical_keycode = KEY_K
	key.pressed = true
	var mouse: InputEventMouseButton = InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_RIGHT
	mouse.pressed = true
	var button: InputEventJoypadButton = InputEventJoypadButton.new()
	button.button_index = JOY_BUTTON_Y
	button.pressed = true
	var axis: InputEventJoypadMotion = InputEventJoypadMotion.new()
	axis.axis = JOY_AXIS_TRIGGER_LEFT
	axis.axis_value = 0.9
	var expected: Dictionary[String, InputEvent] = {
		"key:%d" % KEY_K: key,
		"mouse:%d" % MOUSE_BUTTON_RIGHT: mouse,
		"button:%d" % JOY_BUTTON_Y: button,
		"axis:%d:1" % JOY_AXIS_TRIGGER_LEFT: axis,
	}
	for code: String in expected:
		var event: InputEvent = expected[code]
		assert_eq(Bindings.code(event), code)
		assert_true(Bindings.event(code).is_match(event), code + " gives the same button")


## A release, a small stick push and the mouse wheel cannot be bindings.
func test_events_that_are_not_bindings() -> void:
	var release: InputEventKey = InputEventKey.new()
	release.physical_keycode = KEY_K
	var nudge: InputEventJoypadMotion = InputEventJoypadMotion.new()
	nudge.axis = JOY_AXIS_LEFT_X
	nudge.axis_value = 0.3
	var wheel: InputEventMouseButton = InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	for event: InputEvent in [release, nudge, wheel]:
		assert_eq(Bindings.code(event), "", event.as_text())
	assert_null(Bindings.event("key:x"))
	assert_null(Bindings.event("laser:1"))


## A pad binding replaces the pad buttons of the action and keeps its key; an empty set of
## bindings gives the defaults back.
func test_apply_replaces_one_device() -> void:
	Bindings.apply({Bindings.key(&"use", &"pad"): "button:%d" % JOY_BUTTON_B})
	assert_eq(InputGlyph.for_action(&"use", &"pad"), "B")
	assert_eq(InputGlyph.for_action(&"use", &"keyboard"), "LMB")
	var pad_events: int = 0
	for event: InputEvent in InputMap.action_get_events(&"use"):
		if Bindings.device_of(event) == &"pad":
			pad_events += 1
	assert_eq(pad_events, 1, "X and RT are gone")
	Bindings.apply({})
	assert_eq(InputGlyph.for_action(&"use", &"pad"), "X")


## A glyph draws the new button after a rebind.
func test_glyphs_follow_a_rebind() -> void:
	var glyph: InputGlyph = InputGlyph.new()
	glyph.device = &"keyboard"
	glyph.action = &"jump"
	add_child_autofree(glyph)
	var label: Label = glyph.get_child(0)
	assert_eq(label.text, "Space")
	Bindings.apply({Bindings.key(&"jump", &"keyboard"): "key:%d" % KEY_K})
	assert_eq(label.text, "K")
