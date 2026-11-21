class_name LevelNode
extends FocusButton
## One level on the ring of the level select: a numbered mark that takes the focus. OrbitMap
## makes and places them. Beside the mark, away from the centre of the chart, it shows the
## medal (a star for gold, a check for qualified) and the egg when every egg of the level is
## found.
##
## - &"open": a ring with the number; the player can play the level.
## - &"locked": a dashed ring with a faint number.
## - &"unbuilt": a small ring; the level is unlocked, but it has no scene yet.

const SIDE: float = 72.0
const RADIUS: float = 24.0

var id: StringName = &""
## The place of the level in its tier, from 1.
var number: int = 1
var state: StringName = &"open"
var medal: StringName = &"none"
var egg: bool = false
## Unit vector from the centre of the chart to this mark.
var outward: Vector2 = Vector2.UP


func _init() -> void:
	super()
	custom_minimum_size = Vector2(SIDE, SIDE)
	size = custom_minimum_size
	focus_entered.connect(queue_redraw)
	focus_exited.connect(queue_redraw)


func _draw() -> void:
	var center: Vector2 = size * 0.5
	if has_focus():
		Chart.ring(self, center, RADIUS + 11.0, UiLook.ACCENT, UiLook.STRONG)
	match state:
		&"open":
			Chart.body(self, center, RADIUS, UiLook.LINE)
			_draw_number(center, UiLook.INK)
		&"locked":
			Chart.disc(self, center, RADIUS, UiLook.NIGHT)
			for i: int in 12:
				Chart.arc(self, center, RADIUS, i / 12.0, (i + 0.55) / 12.0, UiLook.LINE_2)
			_draw_number(center, UiLook.INK_3)
		_:
			Chart.body(self, center, 7.0, UiLook.LINE_2)
	var marks: Array[StringName] = []
	if medal == &"gold":
		marks.append(&"star")
	elif medal == &"qualified":
		marks.append(&"check")
	if egg:
		marks.append(&"egg")
	# The marks sit side by side across the outward direction.
	var across: Vector2 = outward.orthogonal()
	for i: int in marks.size():
		var offset: float = (i - (marks.size() - 1) * 0.5) * 26.0
		var at: Vector2 = center + outward * (RADIUS + 28.0) + across * offset
		var color: Color = UiLook.INK if marks[i] == &"check" else UiLook.GOLD
		Icons.draw(self, marks[i], at, 22.0 if marks[i] != &"check" else 17.0, color)


## Draws the level number in the middle of the mark.
func _draw_number(center: Vector2, color: Color) -> void:
	var font: Font = UiLook.DATA_STRONG_FONT
	var size_px: int = UiLook.GLYPH_SIZE
	var text: String = str(number)
	var width: float = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size_px).x
	var rise: float = (font.get_ascent(size_px) - font.get_descent(size_px)) * 0.5
	var at: Vector2 = center + Vector2(-width * 0.5, rise)
	draw_string(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size_px, color)
