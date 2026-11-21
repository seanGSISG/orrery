class_name Readout
extends Control
## A number in two sizes on one baseline: a large part and a small part, such as "0:42" and
## ".37", or "3" and "/5". Make it with Readout.new(large_size, small_size), then call
## show_text() for each new value. The fonts and colours come from UiLook.

## The two parts that show; set them with show_text().
var large: String = ""
var small: String = ""

var _large_size: int
var _small_size: int


func _init(large_size: int, small_size: int) -> void:
	_large_size = large_size
	_small_size = small_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size_flags_vertical = Control.SIZE_SHRINK_CENTER


## Shows large_part and small_part side by side. Does nothing when both are as before.
func show_text(large_part: String, small_part: String) -> void:
	if large_part == large and small_part == small:
		return
	large = large_part
	small = small_part
	update_minimum_size()
	queue_redraw()


func _get_minimum_size() -> Vector2:
	var font: Font = UiLook.DATA_STRONG_FONT
	var width: float = _width(font, large, _large_size)
	width += _width(UiLook.DATA_FONT, small, _small_size)
	# The height of the digits alone, so the number sits in the optical middle of its panel.
	return Vector2(ceilf(width), ceilf(font.get_ascent(_large_size) * 0.78))


func _draw() -> void:
	var font: Font = UiLook.DATA_STRONG_FONT
	var baseline: Vector2 = Vector2(0.0, size.y)
	draw_string(font, baseline, large, HORIZONTAL_ALIGNMENT_LEFT, -1.0, _large_size, UiLook.INK)
	baseline.x += _width(font, large, _large_size)
	draw_string(
		UiLook.DATA_FONT, baseline, small, HORIZONTAL_ALIGNMENT_LEFT, -1.0, _small_size, UiLook.INK_2
	)


## Returns the width of text in font at size.
static func _width(font: Font, text: String, size: int) -> float:
	return font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size).x
