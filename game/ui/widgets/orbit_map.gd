class_name OrbitMap
extends Control
## The chart of the level select. The levels of one tier are marks (LevelNode) on a ring, in
## play order, clockwise from the top. Inside the ring is a dial, which the screen fills with
## the level that has the focus. Outside it are fainter rings for the other tiers, with their
## names. Left and right (or up and down) move along the ring.

## Emitted when the focus moves to the mark of level id.
signal level_focused(id: StringName)
## Emitted when the player chooses the mark of level id.
signal level_chosen(id: StringName)

## Radius of the dial in the middle, of the ring of levels and of the two outer rings.
const DIAL: float = 222.0
const RING: float = 300.0
const OUTER: Array[float] = [384.0, 462.0]
## Part of a turn between two levels; a tier with more than 20 levels packs them closer.
const STEP: float = 0.05
## The middle of the chart, from the middle of the screen.
const OFFSET: Vector2 = Vector2(0.0, 12.0)

## The marks of the tier that shows, in play order.
var nodes: Array[LevelNode] = []
## Names of the other tiers, for the outer rings.
var outer_names: Array[String] = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(_place)


## Returns the middle of the chart.
func center() -> Vector2:
	return size * 0.5 + OFFSET


## Replaces the marks with those of the levels ids of catalog, in order.
func show_levels(catalog: LevelCatalog, ids: Array[StringName]) -> void:
	for node: LevelNode in nodes:
		remove_child(node)
		node.queue_free()
	nodes.clear()
	for i: int in ids.size():
		var id: StringName = ids[i]
		var record: LevelRecord = Save.level(id)
		var node: LevelNode = LevelNode.new()
		node.id = id
		node.number = i + 1
		if not Save.is_unlocked(id):
			node.state = &"locked"
		elif not catalog.info(id).built:
			node.state = &"unbuilt"
		node.medal = record.medal
		node.egg = record.egg
		node.focus_entered.connect(_on_focus.bind(id))
		node.pressed.connect(level_chosen.emit.bind(id))
		add_child(node)
		nodes.append(node)
	# The ring is a circle, so the focus goes round it with either pair of directions.
	var marks: Array[FocusButton] = []
	marks.assign(nodes)
	FocusButton.link(marks)
	FocusButton.link(marks, true)
	_place()


## Returns the mark of level id, or null.
func node_of(id: StringName) -> LevelNode:
	for node: LevelNode in nodes:
		if node.id == id:
			return node
	return null


func _draw() -> void:
	var middle: Vector2 = center()
	Chart.disc(self, middle, DIAL, Color(UiLook.NIGHT, 0.55))
	Chart.ring(self, middle, DIAL, UiLook.LINE_2)
	Chart.ticks(self, middle, DIAL - 12.0, 120, 12.0, UiLook.LINE_3, 1.5)
	Chart.ring(self, middle, RING, UiLook.LINE_2)
	for i: int in OUTER.size():
		Chart.ring(self, middle, OUTER[i], UiLook.LINE_3)
		for dot: int in 20:
			Chart.disc(self, Chart.at(middle, OUTER[i], (dot + 0.5 * i) / 20.0), 3.0, UiLook.LINE_2)
		if i < outer_names.size():
			var font: Font = get_theme_font(&"font", &"Caps")
			var size_px: int = get_theme_font_size(&"font_size", &"Caps")
			var at: float = 0.035 + 0.015 * i
			Chart.arc_text(self, middle, OUTER[i] + 10.0, at, outer_names[i], font, size_px, UiLook.INK_3)
	for node: LevelNode in nodes:
		if node.has_focus():
			# A pointer from the dial to the level that it shows.
			var turn: float = _turn(nodes.find(node))
			draw_line(
				Chart.at(middle, DIAL + 4.0, turn),
				Chart.at(middle, RING - LevelNode.RADIUS - 14.0, turn),
				UiLook.ACCENT,
				UiLook.THIN,
				true
			)


## Returns the place of mark index on the ring, in turns.
func _turn(index: int) -> float:
	return index * minf(STEP, 1.0 / maxi(nodes.size(), 1))


## Puts each mark at its place on the ring.
func _place() -> void:
	for i: int in nodes.size():
		var node: LevelNode = nodes[i]
		node.outward = Vector2.UP.rotated(_turn(i) * TAU)
		node.position = Chart.at(center(), RING, _turn(i)) - node.size * 0.5
		node.queue_redraw()
	queue_redraw()


func _on_focus(id: StringName) -> void:
	queue_redraw()
	level_focused.emit(id)
