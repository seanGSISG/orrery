class_name SettingRow
extends FocusButton
## One row of the settings screen: the name of a setting on the left and its value on the
## right, over a thin line. The focus mark is the bracket of the theme type MenuItem. The
## subclasses (OptionRow, BindRow) fill `value`.
##
## set_enabled(false) turns the row off: it shows faint, and the focus passes it by.

## Height of a row, design units.
const HEIGHT: float = 108.0

## The room for the value, at the right end of the row.
var value: HBoxContainer = UiTheme.row(24)

var _name: Label = Label.new()
var _row: HBoxContainer = UiTheme.row(24)


func _init(name_key: String) -> void:
	super()
	_name.text = name_key
	_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_row.add_child(_name)
	value.mouse_filter = Control.MOUSE_FILTER_IGNORE
	value.alignment = BoxContainer.ALIGNMENT_END
	_row.add_child(value)
	add_child(_row)
	custom_minimum_size = Vector2(0.0, HEIGHT)


## Turns the row on or off. A row that is off cannot be chosen and takes no focus.
func set_enabled(enabled: bool) -> void:
	disabled = not enabled
	focus_mode = Control.FOCUS_ALL if enabled else Control.FOCUS_NONE
	modulate.a = 1.0 if enabled else 0.45
	_refresh()


func _ready() -> void:
	_row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_row.offset_left = 30.0
	_row.offset_right = -30.0
	_row.minimum_size_changed.connect(update_minimum_size)
	focus_entered.connect(_refresh)
	focus_exited.connect(_refresh)
	_refresh()


func _get_minimum_size() -> Vector2:
	return Vector2(_row.get_combined_minimum_size().x + 60.0, HEIGHT)


func _draw() -> void:
	var y: float = size.y - 1.0
	draw_line(Vector2(0.0, y), Vector2(size.x, y), UiLook.LINE_3, 1.0)
	if has_focus():
		draw_style_box(get_theme_stylebox(&"focus", &"MenuItem"), Rect2(Vector2.ZERO, size))


## Shows the name in the style of the row's state.
func _refresh() -> void:
	_name.theme_type_variation = &"RowFocus" if has_focus() else &"Row"
	queue_redraw()
