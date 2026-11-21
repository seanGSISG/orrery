class_name Bindings
extends RefCounted
## The player's own buttons for the gameplay actions (docs/plan.md §2.4). Settings.bindings
## stores them; apply() puts them into the input map. Each action has one binding for each
## device: &"keyboard" (a key or a mouse button) or &"pad" (a button, or a stick or trigger
## pushed one way). A binding replaces the action's default buttons on its device; the other
## device keeps its own.
##
## A binding is stored as a short code, so the save file stays plain JSON:
## "key:<physical keycode>", "mouse:<button>", "button:<joy button>" or "axis:<joy axis>:<1|-1>".
##
## The menu actions (ui_*, tab_*) are not here: they stay fixed, so a player cannot lose the
## way through the menus.

## The actions that the player can bind, in the order of the settings menu.
const ACTIONS: Array[StringName] = [
	&"roll_forward",
	&"roll_back",
	&"roll_left",
	&"roll_right",
	&"jump",
	&"use",
	&"restart",
	&"pause",
	&"look_up",
	&"look_down",
	&"look_left",
	&"look_right",
]
const DEVICES: Array[StringName] = [&"keyboard", &"pad"]
## A stick or trigger push past this part binds its axis.
const AXIS_PUSH: float = 0.6
## The group of the nodes to tell after a change: they must have a method refresh().
const GROUP: StringName = &"input_glyphs"


## Returns the key of the binding of action on device in Settings.bindings: "jump.pad".
static func key(action: StringName, device: StringName) -> String:
	return "%s.%s" % [action, device]


## Returns the code of event as a binding, or "" when event cannot be one: a release, a key
## repeat, mouse motion, the mouse wheel, or a stick push that is too small.
static func code(event: InputEvent) -> String:
	if event is InputEventJoypadMotion:
		var motion: InputEventJoypadMotion = event
		if absf(motion.axis_value) < AXIS_PUSH:
			return ""
		return "axis:%d:%d" % [motion.axis, 1 if motion.axis_value > 0.0 else -1]
	if not event.is_pressed() or event.is_echo():
		return ""
	if event is InputEventKey:
		var key_event: InputEventKey = event
		var physical: Key = key_event.physical_keycode
		if physical == KEY_NONE:
			# An event with no physical key (from code) names the key of the US layout.
			physical = key_event.keycode
		return "key:%d" % physical if physical != KEY_NONE else ""
	if event is InputEventMouseButton:
		var button: MouseButton = (event as InputEventMouseButton).button_index
		return "mouse:%d" % button if button in InputGlyph.MOUSE_BUTTONS else ""
	if event is InputEventJoypadButton:
		return "button:%d" % (event as InputEventJoypadButton).button_index
	return ""


## Returns the input event of a binding code, for any device, or null for a code that is not
## one.
static func event(binding: String) -> InputEvent:
	var parts: PackedStringArray = binding.split(":")
	if parts.size() < 2 or not parts[1].is_valid_int():
		return null
	var number: int = parts[1].to_int()
	var made: InputEvent
	match parts[0]:
		"key":
			var key_event: InputEventKey = InputEventKey.new()
			key_event.physical_keycode = number as Key
			made = key_event
		"mouse":
			var mouse: InputEventMouseButton = InputEventMouseButton.new()
			mouse.button_index = number as MouseButton
			made = mouse
		"button":
			var button: InputEventJoypadButton = InputEventJoypadButton.new()
			button.button_index = number as JoyButton
			made = button
		"axis":
			if parts.size() != 3 or not parts[2].is_valid_int():
				return null
			var motion: InputEventJoypadMotion = InputEventJoypadMotion.new()
			motion.axis = number as JoyAxis
			motion.axis_value = signf(parts[2].to_int())
			made = motion
		_:
			return null
	made.device = -1
	return made


## Returns the device of a binding event: &"pad" for a controller, else &"keyboard".
static func device_of(input: InputEvent) -> StringName:
	var pad: bool = input is InputEventJoypadButton or input is InputEventJoypadMotion
	return &"pad" if pad else &"keyboard"


## Gives each action of ACTIONS its default buttons from the project settings, then puts in
## the bindings, and tells the button glyphs (GROUP) to draw again.
static func apply(bindings: Dictionary[String, String]) -> void:
	for action: StringName in ACTIONS:
		var defaults: Dictionary = ProjectSettings.get_setting("input/" + action, {})
		var events: Array = defaults.get("events", [])
		InputMap.action_erase_events(action)
		for device: StringName in DEVICES:
			var stored: String = bindings.get(key(action, device), "")
			var bound: InputEvent = event(stored)
			if bound != null and device_of(bound) == device:
				InputMap.action_add_event(action, bound)
				continue
			for default: InputEvent in events:
				if device_of(default) == device:
					InputMap.action_add_event(action, default)
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	tree.call_group(GROUP, &"refresh")
