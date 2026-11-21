class_name MenuItem
extends FocusButton
## One item of a menu: a name and, optionally, the glyph of a button beside it. Make it with
## MenuItem.new("TEXT_KEY") and connect `pressed`. The player chooses it with ui_accept while
## it has the focus, or with a click.
##
## A glyph action shows the glyph of that input action beside the name: at all times for a
## shortcut that the screen handles itself (&"pause" beside Resume), or only while the item
## has the focus (&"ui_accept" in a list with no button hints).
##
## set_enabled(false) turns the item off: it shows faint, and the focus passes it by.
##
## The text styles are MenuText, MenuTextFocus and MenuTextOff; the `normal` and `focus`
## styles of the theme type MenuItem give the margins and the focus mark.

var _row: HBoxContainer = UiTheme.row(24)
var _label: Label = Label.new()
var _glyph: InputGlyph
var _glyph_on_focus: bool


func _init(text_key: String, glyph_action: StringName = &"", glyph_on_focus: bool = false) -> void:
	super()
	_glyph_on_focus = glyph_on_focus
	_label.text = text_key
	_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_row.add_child(_label)
	if glyph_action != &"":
		_glyph = InputGlyph.new()
		_glyph.action = glyph_action
		_row.add_child(_glyph)
	add_child(_row)


## Shows the text of text_key as the name of the item.
func set_text(text_key: String) -> void:
	_label.text = text_key


## Turns the item on or off. An item that is off cannot be chosen and takes no focus.
func set_enabled(enabled: bool) -> void:
	disabled = not enabled
	focus_mode = Control.FOCUS_ALL if enabled else Control.FOCUS_NONE
	_refresh()


func _ready() -> void:
	var box: StyleBox = get_theme_stylebox(&"normal", &"MenuItem")
	_row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_row.offset_left = box.content_margin_left
	_row.offset_right = -box.content_margin_right
	_row.offset_top = box.content_margin_top
	_row.offset_bottom = -box.content_margin_bottom
	_row.minimum_size_changed.connect(update_minimum_size)
	focus_entered.connect(_refresh)
	focus_exited.connect(_refresh)
	_refresh()


func _get_minimum_size() -> Vector2:
	var box: StyleBox = get_theme_stylebox(&"normal", &"MenuItem")
	return _row.get_combined_minimum_size() + box.get_minimum_size()


func _draw() -> void:
	if has_focus():
		draw_style_box(get_theme_stylebox(&"focus", &"MenuItem"), Rect2(Vector2.ZERO, size))


## Shows the text style of the item's state. A glyph for the focus keeps its place while it
## is hidden, so the item does not change size.
func _refresh() -> void:
	if disabled:
		_label.theme_type_variation = &"MenuTextOff"
	else:
		_label.theme_type_variation = &"MenuTextFocus" if has_focus() else &"MenuText"
	if _glyph != null:
		_glyph.modulate.a = 1.0 if has_focus() or not _glyph_on_focus else 0.0
	queue_redraw()
