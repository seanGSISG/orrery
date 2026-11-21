class_name SettingsTabs
extends VBoxContainer
## The tabs of the settings screen: the names in a line between the glyphs of tab_prev and
## tab_next (LB and RB, Q and E), over a ruler with a mark under each name and the accent
## pointer under the one that shows. Make it with SettingsTabs.new(keys); set `current` to
## show a tab. A click on a name emits `chosen`.

## Emitted when the player clicks the name of tab index.
signal chosen(index: int)

## Height of the room for the ruler under the names.
const RULER: float = 44.0

## The tab that shows.
var current: int = 0:
	set(value):
		current = value
		_refresh()

var _names: Array[Label] = []
var _ruler: Control = Control.new()


func _init(keys: Array[String]) -> void:
	theme_type_variation = &"Gap0"
	var line: HBoxContainer = UiTheme.row(24)
	line.add_child(_glyph(&"tab_prev"))
	for i: int in keys.size():
		var label: Label = UiTheme.label(keys[i], &"Caps")
		label.uppercase = true
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		label.mouse_filter = Control.MOUSE_FILTER_STOP
		label.gui_input.connect(_on_name_input.bind(i))
		line.add_child(label)
		_names.append(label)
	line.add_child(_glyph(&"tab_next"))
	add_child(line)
	_ruler.custom_minimum_size = Vector2(0.0, RULER)
	_ruler.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ruler.draw.connect(_draw_ruler)
	line.sort_children.connect(_ruler.queue_redraw)
	add_child(_ruler)
	_refresh()


## Returns the glyph of action, shown for the device used last.
static func _glyph(action: StringName) -> InputGlyph:
	var glyph: InputGlyph = InputGlyph.new()
	glyph.action = action
	return glyph


## Draws the base line, a mark under each name and the pointer under the current one.
func _draw_ruler() -> void:
	var y: float = _ruler.size.y - 2.0
	_ruler.draw_line(Vector2(0.0, y), Vector2(_ruler.size.x, y), UiLook.LINE, UiLook.THIN)
	for i: int in _names.size():
		# The line of names and the ruler both start at x = 0 in this container.
		var x: float = _names[i].position.x + _names[i].size.x * 0.5
		_ruler.draw_line(Vector2(x, y), Vector2(x, y - 14.0), UiLook.LINE, UiLook.THIN)
		if i == current:
			var pointer: PackedVector2Array = [
				Vector2(x - 11.0, y - 32.0), Vector2(x + 11.0, y - 32.0), Vector2(x, y - 16.0)
			]
			_ruler.draw_colored_polygon(pointer, UiLook.ACCENT)


## Shows the current name strong and the others faint.
func _refresh() -> void:
	for i: int in _names.size():
		_names[i].theme_type_variation = &"CapsStrong" if i == current else &"Caps"
	_ruler.queue_redraw()


## Emits `chosen` for a click on the name of tab index.
func _on_name_input(event: InputEvent, index: int) -> void:
	var click: InputEventMouseButton = event as InputEventMouseButton
	if click != null and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
		chosen.emit(index)
