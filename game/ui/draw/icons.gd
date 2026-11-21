class_name Icons
extends RefCounted
## The icons of the HUD and the menus, drawn as shapes so that they stay sharp at any size.
## Call draw() from the _draw() of a CanvasItem, or use the Icon control.
##
## Names: &"star" (gold medal), &"check" (qualified), &"egg", &"egg_empty", &"lock", &"gem"
## and &"coil_spring". A power-up icon has the id of its power-up as its name.

## Outlines and lines, in units of half the icon size round its centre; y points down.
const CHECK: Array[Vector2] = [Vector2(-0.8, 0.05), Vector2(-0.25, 0.6), Vector2(0.8, -0.6)]
const EGG_MARK: Array[Vector2] = [
	Vector2(0, -0.3), Vector2(0.2, 0.1), Vector2(0, 0.5), Vector2(-0.2, 0.1)
]
const LOCK_BODY: Array[Vector2] = [
	Vector2(-0.7, -0.15), Vector2(0.7, -0.15), Vector2(0.7, 0.85), Vector2(-0.7, 0.85)
]
const GEM: Array[Vector2] = [
	Vector2(-0.5, -0.7), Vector2(0.5, -0.7), Vector2(1, -0.2), Vector2(0, 0.85), Vector2(-1, -0.2)
]
const GEM_GIRDLE: Array[Vector2] = [Vector2(-1, -0.2), Vector2(1, -0.2)]
const GEM_FACETS: Array[Vector2] = [
	Vector2(-0.5, -0.7),
	Vector2(-0.38, -0.2),
	Vector2(0, 0.85),
	Vector2(0.38, -0.2),
	Vector2(0.5, -0.7),
]
const SPRING_ARROW: Array[Vector2] = [Vector2(-0.42, -0.62), Vector2(0, -1), Vector2(0.42, -0.62)]
const SPRING_COIL: Array[Vector2] = [
	Vector2(-0.5, -0.3),
	Vector2(0.5, -0.14),
	Vector2(-0.5, 0.1),
	Vector2(0.5, 0.26),
	Vector2(-0.5, 0.5),
	Vector2(0.5, 0.62),
]
const SPRING_BASE: Array[Vector2] = [Vector2(-0.62, 0.95), Vector2(0.62, 0.95)]


## Draws the icon name in color, in a square of size round center. An unknown name draws
## nothing.
static func draw(
	on: CanvasItem, name: StringName, center: Vector2, size: float, color: Color
) -> void:
	var r: float = size * 0.5
	var pen: float = maxf(size * 0.09, 1.5)
	var cut: Color = Color(UiLook.NIGHT, 0.45)
	match name:
		&"star":
			_fill(on, _star(center, r), color)
		&"check":
			_stroke(on, center, r, CHECK, color, pen)
		&"egg":
			_fill(on, _egg(center, r), color)
			_fill(on, _scaled(center, r, EGG_MARK), UiLook.NIGHT)
		&"egg_empty":
			var shell: PackedVector2Array = _egg(center, r)
			shell.append(shell[0])
			on.draw_polyline(shell, color, pen * 0.8, true)
		&"lock":
			on.draw_arc(center + Vector2(0, -0.15) * r, r * 0.42, PI, TAU, 16, color, pen, true)
			_fill(on, _scaled(center, r, LOCK_BODY), color)
		&"gem":
			_fill(on, _scaled(center, r, GEM), color)
			_stroke(on, center, r, GEM_GIRDLE, cut, pen * 0.6)
			_stroke(on, center, r, GEM_FACETS, cut, pen * 0.6)
		&"coil_spring":
			_stroke(on, center, r, SPRING_ARROW, color, pen)
			_stroke(on, center, r, SPRING_COIL, color, pen)
			_stroke(on, center, r, SPRING_BASE, color, pen)


## Fills the polygon points, with a thin outline that smooths its edge.
static func _fill(on: CanvasItem, points: PackedVector2Array, color: Color) -> void:
	on.draw_colored_polygon(points, color)
	var outline: PackedVector2Array = points.duplicate()
	outline.append(points[0])
	on.draw_polyline(outline, color, 1.0, true)


## Draws the line through points, which are in units of r round center.
static func _stroke(
	on: CanvasItem, center: Vector2, r: float, points: Array[Vector2], color: Color, pen: float
) -> void:
	on.draw_polyline(_scaled(center, r, points), color, pen, true)


## Returns points, which are in units of r round center, in canvas units.
static func _scaled(center: Vector2, r: float, points: Array[Vector2]) -> PackedVector2Array:
	var out: PackedVector2Array = []
	for point: Vector2 in points:
		out.append(center + point * r)
	return out


## Returns a five-point star of radius r.
static func _star(center: Vector2, r: float) -> PackedVector2Array:
	var points: PackedVector2Array = []
	for i: int in 10:
		points.append(Chart.at(center, r if i % 2 == 0 else r * 0.42, i / 10.0))
	return points


## Returns an egg of height 2 r: narrow at the top, wide below the middle.
static func _egg(center: Vector2, r: float) -> PackedVector2Array:
	var points: PackedVector2Array = []
	for i: int in 32:
		var angle: float = i / 32.0 * TAU
		var half_width: float = 0.68 * sin(angle) * (1.0 - 0.2 * cos(angle))
		points.append(center + Vector2(half_width, -cos(angle)) * r)
	return points
