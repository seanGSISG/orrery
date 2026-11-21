class_name OptionRow
extends SettingRow
## A setting row whose value is one of a list: OptionRow.new(name_key, texts, index, look).
## texts are the shown values (text keys or final text); index is the one that holds now.
## ui_left and ui_right step through the list and stop at its ends; ui_accept (or a click)
## goes to the next value of a choice or a switch, and goes round. A click on a stepper or a
## scale steps toward the side of the click. Each change emits `changed`.
##
## Looks, as in the C chart mockup (docs/ui-mockups/c-chart/settings.html):
## - &"choice": every value in a line, with a radio dot at the one that holds.
## - &"stepper": the value between two chevrons.
## - &"scale": a ruler with a pointer, and the value beside it.
## - &"switch": OFF or ON and a switch; texts are the two values, off first.

## Emitted after the player changes the value; index is the new one.
signal changed(index: int)

var index: int
var texts: Array[String]
var look: StringName

var _dots: Array[ValueMark] = []
var _labels: Array[Label] = []
var _text: Label = UiTheme.label("", &"DataStrong")
var _mark: ValueMark
## True while a mouse button is down on the row, so that a click steps toward its side.
var _by_mouse: bool = false


func _init(name_key: String, value_texts: Array[String], at: int, row_look: StringName) -> void:
	super(name_key)
	texts = value_texts
	index = clampi(at, 0, texts.size() - 1)
	look = row_look
	match look:
		&"choice":
			value.theme_type_variation = &"Gap44"
			for text: String in texts:
				var option: HBoxContainer = UiTheme.row(14)
				var dot: ValueMark = ValueMark.new(&"radio")
				var label: Label = UiTheme.label(text, &"Caps")
				label.uppercase = true
				option.add_child(dot)
				option.add_child(label)
				value.add_child(option)
				_dots.append(dot)
				_labels.append(label)
		&"stepper":
			value.add_child(ValueMark.new(&"left"))
			value.add_child(_text)
			value.add_child(ValueMark.new(&"right"))
		&"scale":
			_mark = ValueMark.new(&"ruler")
			_mark.steps = texts.size()
			_text.custom_minimum_size = Vector2(110.0, 0.0)
			_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			value.theme_type_variation = &"Gap44"
			value.add_child(_mark)
			value.add_child(_text)
		&"switch":
			_text.theme_type_variation = &"Caps"
			_text.uppercase = true
			_mark = ValueMark.new(&"switch")
			value.add_child(_text)
			value.add_child(_mark)
	_show_value()


## Moves the value by step, within the list. With wrap, it goes round at the ends. Emits
## `changed` when the value changes.
func step(by: int, wrap: bool = false) -> void:
	var last: int = texts.size() - 1
	var next: int = posmod(index + by, last + 1) if wrap else clampi(index + by, 0, last)
	if next == index:
		return
	index = next
	_show_value()
	changed.emit(index)


## Steps with ui_left and ui_right, and notes a mouse button for _pressed().
func _gui_input(event: InputEvent) -> void:
	super(event)
	if event is InputEventMouseButton:
		_by_mouse = event.is_pressed() or _by_mouse
	var by: int = 0
	if event.is_action_pressed(&"ui_left", true):
		by = -1
	elif event.is_action_pressed(&"ui_right", true):
		by = 1
	if by != 0:
		accept_event()
		var before: int = index
		step(by)
		if index != before:
			Music.play_ui(&"move")


## Goes to the next value of a choice or a switch. A click on a stepper or a scale steps
## toward the side of the click.
func _pressed() -> void:
	super()
	var mouse: bool = _by_mouse
	_by_mouse = false
	if look == &"choice" or look == &"switch":
		step(1, true)
	elif mouse:
		var middle: float = value.get_global_rect().get_center().x
		step(-1 if get_global_mouse_position().x < middle else 1)


## Shows the value that holds now.
func _show_value() -> void:
	match look:
		&"choice":
			for i: int in _dots.size():
				_dots[i].on = i == index
				_labels[i].theme_type_variation = &"CapsStrong" if i == index else &"Caps"
		&"stepper", &"scale":
			_text.text = texts[index]
			if _mark != null:
				_mark.part = float(index) / maxf(texts.size() - 1, 1)
		&"switch":
			_text.text = texts[index]
			_text.theme_type_variation = &"CapsStrong" if index == 1 else &"Caps"
			_mark.on = index == 1
