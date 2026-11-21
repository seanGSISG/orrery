class_name Dial
extends Control
## The round dial of the pause and results screens: a ring of tick marks on a dark disc, with
## the level time as an arc from the top. One full circle is the par time, so the mark at the
## top is par, and the gold time has a star on the ring. A level with no par shows the ring
## alone. The dial lays out nothing; put its content over it.

## Radius of the ring.
const RADIUS: float = 340.0
## Width of the dark band outside the ring, which holds the tick marks.
const BAND: float = 36.0
## Room outside the band for the par and gold marks.
const ROOM: float = 44.0

var _time: float = 0.0
var _gold: float = 0.0
var _par: float = 0.0
var _finished: bool = false


func _init() -> void:
	var side: float = (RADIUS + BAND + ROOM) * 2.0
	custom_minimum_size = Vector2(side, side)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Shows time against the gold and par times, in seconds. finished ends the arc with a solid
## dot (a final time); otherwise it ends with the ring of a running clock.
func show_times(time: float, gold: float, par: float, finished: bool) -> void:
	_time = time
	_gold = gold
	_par = par
	_finished = finished
	queue_redraw()


func _draw() -> void:
	var center: Vector2 = size * 0.5
	Chart.disc(self, center, RADIUS + BAND, Color(UiLook.NIGHT, 0.5))
	Chart.ring(self, center, RADIUS, UiLook.LINE_2)
	Chart.ticks(self, center, RADIUS + 8.0, 60, 10.0, UiLook.LINE_3)
	Chart.ticks(self, center, RADIUS + 8.0, 12, 18.0, UiLook.LINE)
	if _par <= 0.0:
		return
	var part: float = clampf(_time / _par, 0.0, 1.0)
	Chart.arc(self, center, RADIUS, 0.0, part, UiLook.LINE, UiLook.STRONG)
	Chart.tick(self, center, RADIUS - 14.0, 0.0, 36.0, UiLook.INK)
	Icons.draw(self, &"check", Chart.at(center, RADIUS + BAND + 22.0, 0.0), 22.0, UiLook.INK)
	if _gold > 0.0 and _gold < _par:
		var gold_turn: float = _gold / _par
		Chart.tick(self, center, RADIUS - 10.0, gold_turn, 46.0, UiLook.GOLD)
		Icons.draw(self, &"star", Chart.at(center, RADIUS + BAND + 22.0, gold_turn), 26.0, UiLook.GOLD)
	var head: Vector2 = Chart.at(center, RADIUS, part)
	if _finished:
		Chart.disc(self, head, 10.0, UiLook.INK)
	else:
		Chart.body(self, head, 10.0, UiLook.ACCENT, UiLook.STRONG)
