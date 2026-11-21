class_name OrreryDiagram
extends Control
## The chart on the title screen: an orrery seen from above. Bodies turn slowly on five
## orbits round the centre, inside a ring of degree marks. One body, in the accent colour, is
## the marble. It draws round `center_offset` from the right edge and the vertical middle of
## its rectangle.

## Radius of the outer ring.
const RADIUS: float = 470.0
## The orbits: radius, and seconds for one turn.
const ORBITS: Array[Vector2] = [
	Vector2(96, 48), Vector2(160, 80), Vector2(232, 128), Vector2(310, 190), Vector2(392, 280)
]
## Where each body is at the start, in turns.
const STARTS: Array[float] = [0.58, 0.14, 0.42, 0.94, 0.97]
## The orbit of the marble.
const MARBLE: int = 2

## The centre of the chart, from the right edge and the vertical middle.
var center_offset: Vector2 = Vector2(-580.0, 0.0)

var _time: float = 0.0


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(delta: float) -> void:
	if is_visible_in_tree():
		_time += delta
		queue_redraw()


func _draw() -> void:
	var center: Vector2 = Vector2(size.x, size.y * 0.5) + center_offset
	Chart.ring(self, center, RADIUS, UiLook.LINE)
	Chart.ring(self, center, RADIUS - 34.0, UiLook.LINE_2)
	Chart.ticks(self, center, RADIUS - 26.0, 180, 18.0, UiLook.LINE_2, 1.5)
	Chart.ticks(self, center, RADIUS - 34.0, 36, 26.0, UiLook.LINE)
	for i: int in 8:
		Chart.tick(self, center, 26.0, i / 8.0, RADIUS - 60.0, UiLook.LINE_3)
	for orbit: Vector2 in ORBITS:
		Chart.ring(self, center, orbit.x, UiLook.LINE_2)
	for i: int in ORBITS.size():
		var turn: float = STARTS[i] + _time / ORBITS[i].y
		var at: Vector2 = Chart.at(center, ORBITS[i].x, turn)
		Chart.tick(self, center, 26.0, turn, ORBITS[i].x - 26.0, UiLook.LINE_2)
		_draw_body(i, at, turn)
	Chart.body(self, center, 26.0, UiLook.LINE)
	Chart.ticks(self, center, 34.0, 16, 12.0, UiLook.LINE)


## Draws the body of orbit index at `at`; turn is its place on the orbit.
func _draw_body(index: int, at: Vector2, turn: float) -> void:
	match index:
		0:
			Chart.disc(self, at, 6.0, UiLook.INK)
		1:
			Chart.body(self, at, 10.0, UiLook.LINE)
		MARBLE:
			Chart.ring(self, at, 24.0, UiLook.ACCENT)
			Chart.disc(self, at, 12.0, UiLook.ACCENT)
		3:
			# A ringed planet: the ring is a flat ellipse, tilted.
			Chart.body(self, at, 15.0, UiLook.LINE)
			draw_set_transform(at, -0.42, Vector2(1.0, 0.27))
			draw_arc(Vector2.ZERO, 30.0, 0.0, TAU, 48, UiLook.LINE, UiLook.THIN / 0.6, true)
			draw_set_transform(Vector2.ZERO)
		_:
			# A planet with a moon that turns round it.
			Chart.ring(self, at, 26.0, UiLook.LINE_3)
			Chart.body(self, at, 9.0, UiLook.LINE)
			Chart.disc(self, Chart.at(at, 26.0, turn * 9.0), 4.0, UiLook.INK)
