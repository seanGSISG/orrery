class_name Chart
extends RefCounted
## Drawing helpers for the line art of the menus: rings, arcs, tick marks and text on a ring,
## as on an astronomical chart. Call them from the _draw() of the CanvasItem `on`.
##
## Angles are turns: 0 is up (12 o'clock) and 1 is one full circle clockwise.

const LEFT: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT


## Returns the point on the circle round center at turn.
static func at(center: Vector2, radius: float, turn: float) -> Vector2:
	return center + Vector2.UP.rotated(turn * TAU) * radius


## Draws a full circle line.
static func ring(
	on: CanvasItem, center: Vector2, radius: float, color: Color, width: float = UiLook.THIN
) -> void:
	on.draw_arc(center, radius, 0.0, TAU, _points(radius, 1.0), color, width, true)


## Draws the part of a circle line from from_turn clockwise to to_turn.
static func arc(
	on: CanvasItem,
	center: Vector2,
	radius: float,
	from_turn: float,
	to_turn: float,
	color: Color,
	width: float = UiLook.THIN
) -> void:
	if to_turn <= from_turn:
		return
	var start: float = from_turn * TAU - PI / 2.0
	var end: float = to_turn * TAU - PI / 2.0
	var points: int = _points(radius, to_turn - from_turn)
	on.draw_arc(center, radius, start, end, points, color, width, true)


## Draws count tick marks, evenly spaced from turn 0, each from radius outward by length.
static func ticks(
	on: CanvasItem,
	center: Vector2,
	radius: float,
	count: int,
	length: float,
	color: Color,
	width: float = UiLook.THIN
) -> void:
	for i: int in count:
		tick(on, center, radius, float(i) / count, length, color, width)


## Draws one tick mark at turn, from radius outward by length.
static func tick(
	on: CanvasItem,
	center: Vector2,
	radius: float,
	turn: float,
	length: float,
	color: Color,
	width: float = UiLook.THIN
) -> void:
	on.draw_line(at(center, radius, turn), at(center, radius + length, turn), color, width, true)


## Draws a filled circle.
static func disc(on: CanvasItem, center: Vector2, radius: float, color: Color) -> void:
	on.draw_circle(center, radius, color, true, -1.0, true)


## Draws a hollow mark: a disc in the night colour that hides the lines behind it, with a
## circle line of color round it.
static func body(
	on: CanvasItem, center: Vector2, radius: float, color: Color, width: float = UiLook.THIN
) -> void:
	disc(on, center, radius, UiLook.NIGHT)
	ring(on, center, radius, color, width)


## Draws text along the outside of a circle, centred on turn, reading clockwise.
static func arc_text(
	on: CanvasItem,
	center: Vector2,
	radius: float,
	turn: float,
	text: String,
	font: Font,
	size: int,
	color: Color
) -> void:
	var widths: PackedFloat32Array = []
	var total: float = 0.0
	for i: int in text.length():
		widths.append(font.get_string_size(text[i], LEFT, -1.0, size).x)
		total += widths[i]
	var angle: float = turn * TAU - total / radius * 0.5
	for i: int in text.length():
		var middle: float = angle + widths[i] / radius * 0.5
		on.draw_set_transform(center + Vector2.UP.rotated(middle) * radius, middle)
		on.draw_string(font, Vector2(-widths[i] * 0.5, 0.0), text[i], LEFT, -1.0, size, color)
		angle += widths[i] / radius
	on.draw_set_transform(Vector2.ZERO)


## Returns the number of line segments for a smooth arc of part of a circle of radius.
static func _points(radius: float, part: float) -> int:
	return clampi(ceili(radius * part), 12, 360)
