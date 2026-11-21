class_name InputGlyph
extends PanelContainer
## The button icon for one action. It follows the device used last (docs/plan.md §2.4): Xbox
## buttons for a pad, key caps for the keyboard and mouse. Make one with InputGlyph.new(),
## set action, and add it to a HUD or menu; it redraws when InputHub.device changes. Use
## for_action() for the button name alone, for example in a text prompt. Both read the
## input map, so a rebound action shows its new button.
##
## The art is a placeholder: a round badge in the Xbox button colour, or a dark key cap.

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
## Badge colours of the Xbox face buttons; other pad buttons use PAD_COLOR.
const FACE_COLORS: Dictionary[String, Color] = {
	"A": Color("#4caf50"),
	"B": Color("#e53935"),
	"X": Color("#1e88e5"),
	"Y": Color("#c79100"),
}
const PAD_COLOR: Color = Color("#3c4250")
const KEY_COLOR: Color = Color("#23262e")
const KEY_BORDER: Color = Color("#8a90a0")

## The input action to show, for example &"jump".
@export var action: StringName = &"":
	set(value):
		action = value
		_refresh()

var _label: Label = Label.new()
var _style: StyleBoxFlat = StyleBoxFlat.new()


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
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_style.set_content_margin_all(6.0)
	_style.content_margin_left = 10.0
	_style.content_margin_right = 10.0
	add_theme_stylebox_override(&"panel", _style)
	add_child(_label)
	custom_minimum_size = Vector2(32.0, 32.0)
	InputHub.device_changed.connect(_refresh.unbind(1))
	_refresh()


## Shows the button for action on the device used last.
func _refresh() -> void:
	if not is_node_ready():
		return
	var on_pad: bool = InputHub.device == &"pad"
	var text: String = for_action(action, InputHub.device)
	_label.text = text
	visible = text != ""
	var color: Color = FACE_COLORS.get(text, PAD_COLOR)
	_style.bg_color = color if on_pad else KEY_COLOR
	_style.set_corner_radius_all(16 if on_pad else 4)
	_style.set_border_width_all(0 if on_pad else 2)
	_style.border_color = KEY_BORDER
	_label.add_theme_color_override(&"font_color", Color.WHITE)
