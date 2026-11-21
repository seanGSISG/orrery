class_name TickRule
extends Control
## A horizontal line with small marks on it, like the edge of a ruler. It fills the width that
## its parent gives it. Make it with TickRule.new(step): the distance between the marks.

var _step: float


func _init(step: float = 20.0) -> void:
	_step = step
	custom_minimum_size = Vector2(0.0, 14.0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	var y: float = size.y - 1.0
	draw_line(Vector2(0.0, y), Vector2(size.x, y), UiLook.LINE, UiLook.THIN)
	var x: float = _step
	while x < size.x:
		draw_line(Vector2(x, y), Vector2(x, y - 12.0), UiLook.LINE_2, 1.0)
		x += _step
