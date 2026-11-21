class_name BindRow
extends SettingRow
## A settings row that binds one gameplay action: BindRow.new(action). It shows the action's
## keyboard button and its controller button (Bindings). ui_accept or a click makes it listen;
## then the next key, mouse button, pad button or stick push is the new button of its device,
## and the row emits `bound`. ui_cancel (B or Esc) stops the listening with no change, so
## those buttons cannot be bound. A move of the focus away stops it too.

## Emitted when the player presses a new button for the action: device is &"keyboard" or
## &"pad", and code is its Bindings code.
signal bound(device: StringName, code: String)

## Width of the room for the button of one device.
const SLOT_WIDTH: float = 220.0

var action: StringName
## True while the row waits for a button.
var listening: bool = false

var _slots: HBoxContainer = UiTheme.row(0)
var _glyphs: Array[InputGlyph] = []
var _dashes: Array[Label] = []
var _prompt: Label = UiTheme.label("SETTINGS_PRESS", &"RowAccent")


func _init(bound_action: StringName) -> void:
	super("ACTION_" + String(bound_action).to_upper())
	action = bound_action
	for device: StringName in Bindings.DEVICES:
		var slot: CenterContainer = CenterContainer.new()
		slot.custom_minimum_size = Vector2(SLOT_WIDTH, 0.0)
		var glyph: InputGlyph = InputGlyph.new()
		glyph.device = device
		glyph.action = action
		var dash: Label = UiTheme.label("–", &"Caps")
		var both: HBoxContainer = UiTheme.row(0)
		both.add_child(glyph)
		both.add_child(dash)
		slot.add_child(both)
		_slots.add_child(slot)
		_glyphs.append(glyph)
		_dashes.append(dash)
	_prompt.visible = false
	value.add_child(_prompt)
	value.add_child(_slots)
	focus_exited.connect(_stop)


## Shows the action's buttons now in the input map, and a dash for a device with none.
func show_buttons() -> void:
	for i: int in Bindings.DEVICES.size():
		_glyphs[i].action = action
		_dashes[i].visible = InputGlyph.for_action(action, Bindings.DEVICES[i]) == ""


func _ready() -> void:
	super()
	show_buttons()


## Starts to listen for a button.
func _pressed() -> void:
	super()
	listening = true
	_prompt.visible = true
	_slots.visible = false


## While the row listens, takes every press before the menus see it: ui_cancel stops, and a
## button that can be bound ends the listening with `bound`.
func _input(event: InputEvent) -> void:
	if not listening:
		return
	var code: String = Bindings.code(event)
	if event.is_action_pressed(&"ui_cancel"):
		code = ""
		_stop()
	elif code != "":
		_stop()
		bound.emit(Bindings.device_of(event), code)
		show_buttons()
	if event.is_pressed() or code != "":
		get_viewport().set_input_as_handled()


## Stops listening and shows the buttons again.
func _stop() -> void:
	listening = false
	_prompt.visible = false
	_slots.visible = true
