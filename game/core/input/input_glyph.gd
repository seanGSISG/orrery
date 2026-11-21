class_name InputGlyph
extends PanelContainer
## The button icon for one action. It follows the device used last (docs/plan.md §2.4): Xbox
## buttons for a pad, key caps for the keyboard and mouse. Make one with InputGlyph.new(),
## set action, and add it to a HUD or menu; it redraws when InputHub.device changes. Use
## for_action() for the button name alone, for example in a text prompt. Both read the
## input map, so a rebound action shows its new button.
##
## The look comes from the Theme (game/ui/look/ui_theme.gd): the panel is the type GlyphPad
## for a pad button and GlyphKey for a key, and the name is a Label of the type GlyphText.
## The Menu and View buttons show their symbol in place of their name.

## Names of the Xbox buttons, by JoyButton.
const PAD_BUTTONS: Dictionary[int, String] = {
	JOY_BUTTON_A: "A",
	JOY_BUTTON_B: "B",
	JOY_BUTTON_X: "X",
	JOY_BUTTON_Y: "Y",
	JOY_BUTTON_BACK: "View",
	JOY_BUTTON_GUIDE: "Xbox",
	JOY_BUTTON_START: "Menu",
	JOY_BUTTON_LEFT_STICK: "LS",
	JOY_BUTTON_RIGHT_STICK: "RS",
	JOY_BUTTON_LEFT_SHOULDER: "LB",
	JOY_BUTTON_RIGHT_SHOULDER: "RB",
	JOY_BUTTON_DPAD_UP: "D-pad Up",
	JOY_BUTTON_DPAD_DOWN: "D-pad Down",
	JOY_BUTTON_DPAD_LEFT: "D-pad Left",
	JOY_BUTTON_DPAD_RIGHT: "D-pad Right",
}
## Names of the Xbox sticks and triggers, by JoyAxis.
const PAD_AXES: Dictionary[int, String] = {
	JOY_AXIS_LEFT_X: "LS",
	JOY_AXIS_LEFT_Y: "LS",
	JOY_AXIS_RIGHT_X: "RS",
	JOY_AXIS_RIGHT_Y: "RS",
	JOY_AXIS_TRIGGER_LEFT: "LT",
	JOY_AXIS_TRIGGER_RIGHT: "RT",
}
const MOUSE_BUTTONS: Dictionary[int, String] = {
	MOUSE_BUTTON_LEFT: "LMB",
	MOUSE_BUTTON_RIGHT: "RMB",
	MOUSE_BUTTON_MIDDLE: "MMB",
}
## Pad buttons that show a symbol in place of their name.
const SYMBOLS: Array[String] = ["Menu", "View"]
## The part of the View symbol's back window that shows behind the front one, round the
## middle of the glyph.
const VIEW_BACK: Array[Vector2] = [
	Vector2(-3, -3), Vector2(-3, -8), Vector2(9, -8), Vector2(9, 2), Vector2(4, 2)
]
## Width and height of a glyph with one letter.
const SIDE: float = 44.0

## The input action to show, for example &"jump".
@export var action: StringName = &"":
	set(value):
		action = value
		_refresh()

var _label: Label = Label.new()
## The pad button whose symbol _draw() shows; "" shows the name in the label.
var _symbol: String = ""


## Returns the name of the first button for action on device (&"pad" or &"keyboard"), for
## example "A" or "Space". Returns "" when action has no button on that device.
static func for_action(action_name: StringName, on_device: StringName) -> String:
	if not InputMap.has_action(action_name):
		return ""
	for event: InputEvent in InputMap.action_get_events(action_name):
		var label: String = _name(event)
		if label != "" and _is_pad(event) == (on_device == &"pad"):
			return label
	return ""


## Returns the name of one input event's button, or "" for an event type without a glyph.
static func _name(event: InputEvent) -> String:
	if event is InputEventJoypadButton:
		return PAD_BUTTONS.get((event as InputEventJoypadButton).button_index, "")
	if event is InputEventJoypadMotion:
		return PAD_AXES.get((event as InputEventJoypadMotion).axis, "")
	if event is InputEventMouseButton:
		return MOUSE_BUTTONS.get((event as InputEventMouseButton).button_index, "")
	var key: InputEventKey = event as InputEventKey
	if key == null:
		return ""
	if key.physical_keycode == KEY_NONE:
		return OS.get_keycode_string(key.keycode)
	# Name the key of the player's layout (Z on AZERTY for the W position). The headless
	# display server has no layout, so it names the US key.
	var keycode: Key = key.physical_keycode
	if DisplayServer.get_name() != "headless":
		keycode = DisplayServer.keyboard_get_keycode_from_physical(keycode)
	return OS.get_keycode_string(keycode)


## Returns true for a controller event.
static func _is_pad(event: InputEvent) -> bool:
	return event is InputEventJoypadButton or event is InputEventJoypadMotion


## Builds the badge and follows InputHub's device.
func _ready() -> void:
	_label.theme_type_variation = &"GlyphText"
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(_label)
	custom_minimum_size = Vector2(SIDE, SIDE)
	size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	InputHub.device_changed.connect(_refresh.unbind(1))
	_refresh()


## Draws the symbol of the Menu button (three lines) or the View button (two windows).
func _draw() -> void:
	var color: Color = get_theme_color(&"font_color", &"GlyphText")
	var middle: Vector2 = size * 0.5
	if _symbol == "Menu":
		for y: float in [-6.0, 0.0, 6.0]:
			draw_line(middle + Vector2(-8.0, y), middle + Vector2(8.0, y), color, 2.0, true)
	elif _symbol == "View":
		var back: PackedVector2Array = []
		for corner: Vector2 in VIEW_BACK:
			back.append(middle + corner)
		draw_polyline(back, color, 2.0, true)
		draw_rect(Rect2(middle + Vector2(-9.0, -3.0), Vector2(13.0, 10.0)), color, false, 2.0)


## Shows the button for action on the device used last.
func _refresh() -> void:
	if not is_node_ready():
		return
	var on_pad: bool = InputHub.device == &"pad"
	var text: String = for_action(action, InputHub.device)
	_symbol = text if on_pad and text in SYMBOLS else ""
	_label.text = "" if _symbol != "" else text
	visible = text != ""
	theme_type_variation = &"GlyphPad" if on_pad else &"GlyphKey"
	queue_redraw()
