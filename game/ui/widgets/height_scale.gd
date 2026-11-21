class_name HeightScale
extends Control
## The scale of the Ascent height meter: an upright line from the climb start (bottom) to the
## gate (top). The part below the marble is bright. A tick marks each zone start, a ring marks
## the gate, a gold pennant marks the best height, and a ring in the accent colour marks the
## marble. Call show_climb() for each new value; the height of the control sets its length.

## Distance of the line from the left edge, and of its ends from the top and the bottom.
const LINE_X: float = 12.0
const END: float = 14.0
## Half the length of a zone tick, the radius of the gate ring and of the marble's ring.
const TICK: float = 9.0
const GATE: float = 6.0
const MARK: float = 7.0
## The pennant: its pole stands this far right of the line, and it is this long and this high.
const POLE_X: float = 14.0
const PENNANT: Vector2 = Vector2(17.0, 12.0)

var _height: float = 0.0
var _best: float = 0.0
var _zones: PackedFloat32Array = []
var _top: float = 0.0


func _init(length: float = 320.0) -> void:
	custom_minimum_size = Vector2(LINE_X + POLE_X + PENNANT.x + 2.0, length)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Shows the marble at height and the pennant at best, on a climb whose zones start at the
## heights of zones and whose gate is at top. All are m above the climb start.
func show_climb(height: float, best: float, zones: PackedFloat32Array, top: float) -> void:
	# The marks move by less than a pixel in most frames, so the scale draws again only for a
	# change that shows.
	var moved: float = maxf(absf(_y(height) - _y(_height)), absf(_y(best) - _y(_best)))
	if moved < 0.25 and zones == _zones and top == _top:
		return
	_height = height
	_best = best
	_zones = zones
	_top = top
	queue_redraw()


func _draw() -> void:
	var bottom: Vector2 = Vector2(LINE_X, _y(0.0))
	var top: Vector2 = Vector2(LINE_X, _y(_top))
	var now: Vector2 = Vector2(LINE_X, _y(_height))
	draw_line(bottom, top, UiLook.LINE_3, UiLook.STRONG, true)
	draw_line(bottom, now, UiLook.INK, UiLook.STRONG, true)
	for zone: float in _zones:
		var at: Vector2 = Vector2(LINE_X, _y(zone))
		draw_line(at - Vector2(TICK, 0.0), at + Vector2(TICK, 0.0), UiLook.LINE, UiLook.THIN, true)
	Chart.body(self, top, GATE, UiLook.LINE)
	if _best > 0.0:
		var foot: Vector2 = Vector2(LINE_X + POLE_X, _y(_best))
		var tip: Vector2 = foot - Vector2(0.0, PENNANT.y * 1.6)
		draw_line(Vector2(LINE_X, foot.y), foot, UiLook.GOLD, UiLook.THIN, true)
		draw_line(foot, tip, UiLook.GOLD, UiLook.THIN, true)
		var pennant: PackedVector2Array = [
			tip, tip + Vector2(PENNANT.x, PENNANT.y * 0.5), tip + Vector2(0.0, PENNANT.y)
		]
		draw_colored_polygon(pennant, UiLook.GOLD)
	Chart.body(self, now, MARK, UiLook.ACCENT, 3.0)


## Returns the y of height on the line. Heights outside the climb stay at its ends.
func _y(height: float) -> float:
	var part: float = clampf(height / _top, 0.0, 1.0) if _top > 0.0 else 0.0
	return lerpf(size.y - END, END, part)
