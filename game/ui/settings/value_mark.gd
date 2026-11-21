class_name ValueMark
extends Control
## A small drawn mark that shows the value of a setting: a radio dot, an on/off switch, a ruler
## with a pointer, or a chevron. Make it with ValueMark.new(kind) and set the vars; it draws
## again after each change. Its colours come from UiLook.
##
## Kinds: &"radio" (on: chosen), &"switch" (on: on), &"ruler" (part: the pointer, 0..1;
## steps: the number of marks), &"left" and &"right" (the chevrons of a stepper).

const SIZES: Dictionary[StringName, Vector2] = {
	&"radio": Vector2(24.0, 24.0),
	&"switch": Vector2(84.0, 30.0),
	&"ruler": Vector2(420.0, 34.0),
	&"left": Vector2(24.0, 36.0),
	&"right": Vector2(24.0, 36.0),
}

var kind: StringName
var on: bool = false:
	set(value):
		on = value
		queue_redraw()
var part: float = 0.0:
	set(value):
		part = value
		queue_redraw()
var steps: int = 2:
	set(value):
		steps = value
		queue_redraw()


func _init(mark_kind: StringName) -> void:
	kind = mark_kind
	custom_minimum_size = SIZES[kind]
	size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	match kind:
		&"radio":
			_draw_radio()
		&"switch":
			_draw_switch()
		&"ruler":
			_draw_ruler()
		&"left", &"right":
			_draw_chevron(-1.0 if kind == &"left" else 1.0)


## A ring; a chosen one is bright and has a dot in it.
func _draw_radio() -> void:
	var middle: Vector2 = size * 0.5
	var color: Color = UiLook.INK if on else UiLook.INK_3
	draw_arc(middle, 10.0, 0.0, TAU, 32, color, UiLook.THIN, true)
	if on:
		draw_circle(middle, 5.5, color, true, -1.0, true)


## Two rings joined by a line; the knob (a ring with a dot) is on the right when on.
func _draw_switch() -> void:
	var y: float = size.y * 0.5
	var radius: float = 12.0
	var left: Vector2 = Vector2(radius + 1.0, y)
	var right: Vector2 = Vector2(size.x - radius - 1.0, y)
	var color: Color = UiLook.INK if on else UiLook.INK_3
	draw_line(left + Vector2(radius, 0.0), right - Vector2(radius, 0.0), color, UiLook.THIN, true)
	for end: Vector2 in [left, right]:
		draw_arc(end, radius, 0.0, TAU, 32, color, UiLook.THIN, true)
	draw_circle(right if on else left, radius - 5.0, color, true, -1.0, true)


## A base line with `steps` marks and a pointer above it at `part`.
func _draw_ruler() -> void:
	var y: float = size.y - 2.0
	draw_line(Vector2(0.0, y), Vector2(size.x, y), UiLook.LINE_2, UiLook.THIN)
	for i: int in steps:
		var x: float = size.x * i / maxf(steps - 1, 1)
		draw_line(Vector2(x, y), Vector2(x, y - 12.0), UiLook.LINE_2, 1.0)
	var at: float = clampf(part, 0.0, 1.0) * size.x
	var pointer: PackedVector2Array = [
		Vector2(at - 10.0, y - 30.0), Vector2(at + 10.0, y - 30.0), Vector2(at, y - 12.0)
	]
	draw_colored_polygon(pointer, UiLook.INK)


## A chevron that points along direction (-1 left, 1 right).
func _draw_chevron(direction: float) -> void:
	var middle: Vector2 = size * 0.5
	var points: PackedVector2Array = [
		middle + Vector2(-5.0 * direction, -11.0),
		middle + Vector2(5.0 * direction, 0.0),
		middle + Vector2(-5.0 * direction, 11.0),
	]
	draw_polyline(points, UiLook.ACCENT, 3.0, true)
