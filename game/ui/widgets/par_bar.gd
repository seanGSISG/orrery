class_name ParBar
extends Control
## The scale under the HUD timer: the level time as a bar that is full at the par time. The
## gold time is a diamond on the bar, par is the tick at its end, and a ring in the accent
## colour marks the time now. A level with no par shows an empty bar.

var _part: float = 0.0
var _gold_part: float = -1.0


func _init() -> void:
	custom_minimum_size = Vector2(0.0, 22.0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Shows time against the gold and par times, in seconds.
func show_times(time: float, gold: float, par: float) -> void:
	var part: float = clampf(time / par, 0.0, 1.0) if par > 0.0 else 0.0
	var gold_part: float = gold / par if par > 0.0 and gold > 0.0 and gold < par else -1.0
	# The bar moves by less than a pixel in most frames, so it draws again only for a change
	# that shows.
	if absf(part - _part) * size.x < 0.25 and gold_part == _gold_part:
		return
	_part = part
	_gold_part = gold_part
	queue_redraw()


func _draw() -> void:
	var y: float = size.y * 0.5
	var end: float = size.x - 2.0
	draw_line(Vector2(0.0, y), Vector2(end, y), UiLook.LINE_3, UiLook.STRONG, true)
	draw_line(Vector2(0.0, y), Vector2(end * _part, y), UiLook.INK, UiLook.STRONG, true)
	draw_line(Vector2(end, y - 10.0), Vector2(end, y + 10.0), UiLook.INK, UiLook.STRONG, true)
	if _gold_part >= 0.0:
		var at: Vector2 = Vector2(end * _gold_part, y)
		var diamond: PackedVector2Array = [
			at + Vector2(0, -8), at + Vector2(8, 0), at + Vector2(0, 8), at + Vector2(-8, 0)
		]
		draw_colored_polygon(diamond, UiLook.GOLD)
	Chart.body(self, Vector2(end * _part, y), 7.0, UiLook.ACCENT, 3.0)
