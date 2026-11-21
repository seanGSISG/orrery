class_name LevelSelectScreen
extends Screen
## The level select: the levels of one tier on a ring (OrbitMap). The dial in the middle
## shows the level that has the focus: its name, the best time, the gold and par times, the
## medal and the egg. A locked level, and a level that is not built yet, shows that in place
## of the times. The corner shows the gold medals and the eggs of the tier.
##
## ui_accept plays the level with the focus, tab_prev and tab_next (LB and RB, Q and E) change
## the tier, and ui_cancel goes back to the title.

## The tiers and levels to show. A test can set its own before the screen opens.
var catalog: LevelCatalog = LevelCatalog.of_game()
## The tier that shows.
var tier: StringName = &""
## The level that gets the focus when the screen opens; Ui sets it to the level played last.
var last_level: StringName = &""
## The chart with the marks of the tier that shows.
var map: OrbitMap = OrbitMap.new()

var _tier_name: Label = UiTheme.label("", &"Heading")
var _tabs: Array[InputGlyph] = [InputGlyph.new(), InputGlyph.new()]
var _other_tiers: VBoxContainer = UiTheme.column(8)
var _medals: Label = UiTheme.label("", &"DataStrong")
var _eggs: Label = UiTheme.label("", &"DataStrong")
var _name: Label = UiTheme.label("", &"LevelName")
var _time: Label = UiTheme.label("", &"BestTime")
var _targets: HBoxContainer = UiTheme.row(24)
var _gold: Label = UiTheme.label("")
var _par: Label = UiTheme.label("")
var _marks: HBoxContainer = UiTheme.row(24)
var _medal_icon: Icon = Icon.new(&"", UiLook.GOLD, 40.0)
var _egg_icon: Icon = Icon.new(&"", UiLook.GOLD, 40.0)
var _status: HBoxContainer = UiTheme.row(14)
var _status_icon: Icon = Icon.new(&"lock", UiLook.INK_3, 26.0)
var _status_text: Label = UiTheme.label("", &"Caps")
var _play_hint: Control


func _init() -> void:
	super()
	var wash: Wash = Wash.new()
	wash.dim = Vector2(0.62, 0.9)
	add_child(wash)
	add_child(map)
	map.level_focused.connect(_show_level)
	map.level_chosen.connect(_play)
	_build_dial()
	var area: Control = add_safe_area()
	area.add_child(_build_header())
	area.add_child(_build_totals())
	var hints: Hints = Hints.new()
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	hints.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_play_hint = hints.add_hint(&"ui_accept", "HINT_PLAY")
	hints.add_hint(&"ui_cancel", "HINT_BACK")
	area.add_child(hints)


## Shows the tier of the level played last, else the first tier, with the saved progress.
func open() -> void:
	var from: StringName = catalog.tier_of(last_level)
	if from != &"":
		tier = from
	elif not catalog.tiers.has(tier):
		tier = catalog.tiers[0] if not catalog.tiers.is_empty() else &""
	_show_tier(last_level)


func back() -> bool:
	Game.screen = &"title"
	return true


## Changes the tier with tab_prev and tab_next.
func _unhandled_input(event: InputEvent) -> void:
	super(event)
	if not is_visible_in_tree() or catalog.tiers.size() < 2:
		return
	var step: int = 0
	if event.is_action_pressed(&"tab_prev"):
		step = -1
	elif event.is_action_pressed(&"tab_next"):
		step = 1
	if step != 0:
		accept_event()
		tier = catalog.tiers[posmod(catalog.tiers.find(tier) + step, catalog.tiers.size())]
		_show_tier(&"")


## Shows the levels of `tier` and gives the focus to level focus_id, else to the first level
## that the player can play and has not qualified on, else to the first level.
func _show_tier(focus_id: StringName) -> void:
	var ids: Array[StringName] = catalog.levels(tier)
	_tier_name.text = _tier_key(tier)
	for glyph: InputGlyph in _tabs:
		glyph.modulate.a = 1.0 if catalog.tiers.size() > 1 else 0.0
	for child: Node in _other_tiers.get_children():
		_other_tiers.remove_child(child)
		child.queue_free()
	map.outer_names.clear()
	for other: StringName in catalog.tiers:
		if other != tier:
			_other_tiers.add_child(_tier_line(other))
			map.outer_names.append(tr(_tier_key(other)).to_upper())
	var gold: int = 0
	var eggs: int = 0
	var focus: StringName = &""
	for id: StringName in ids:
		var record: LevelRecord = Save.level(id)
		gold += 1 if record.medal == &"gold" else 0
		eggs += 1 if record.egg else 0
		if focus == &"" and catalog.can_play(id) and not record.qualified():
			focus = id
	if focus == &"" and not ids.is_empty():
		focus = ids[0]
	_medals.text = "%d/%d" % [gold, ids.size()]
	_eggs.text = "%d/%d" % [eggs, ids.size()]
	map.show_levels(catalog, ids)
	var node: LevelNode = map.node_of(focus_id if ids.has(focus_id) else focus)
	if node != null:
		node.grab_focus()
	else:
		_show_level(&"")


## Fills the dial with level id; &"" (a tier with no levels) empties it.
func _show_level(id: StringName) -> void:
	var info: LevelInfo = catalog.info(id)
	var record: LevelRecord = Save.level(id)
	var open_level: bool = id != &"" and catalog.can_play(id)
	var number: int = catalog.levels(tier).find(id) + 1
	_name.text = info.title if info.title != "" else tr("LEVEL_NUMBER") % number
	_name.visible = id != &""
	_time.text = TimeText.full(record.best_time) if record.best_time >= 0.0 else "TIME_NONE"
	_time.theme_type_variation = &"BestTime" if record.best_time >= 0.0 else &"BestTimeNone"
	_time.visible = open_level
	_gold.text = TimeText.full(info.gold)
	_par.text = TimeText.full(info.par)
	_targets.visible = open_level and info.par > 0.0
	_medal_icon.icon = &"star" if record.medal == &"gold" else &"check"
	_medal_icon.color = UiLook.GOLD if record.medal == &"gold" else UiLook.INK
	_medal_icon.visible = record.qualified()
	_egg_icon.icon = &"egg" if record.egg else &"egg_empty"
	_egg_icon.color = UiLook.GOLD if record.egg else UiLook.INK_3
	_marks.visible = open_level
	var locked: bool = not Save.is_unlocked(id)
	_status.visible = id != &"" and not open_level
	_status_icon.visible = locked
	_status_text.text = "LEVELS_LOCKED" if locked else "LEVELS_UNBUILT"
	_play_hint.visible = open_level


## Plays level id when the player can play it.
func _play(id: StringName) -> void:
	if catalog.can_play(id):
		Game.load_level(id)


## Builds the content of the dial, in the middle of the chart.
func _build_dial() -> void:
	var column: VBoxContainer = UiTheme.column(8)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	column.grow_horizontal = Control.GROW_DIRECTION_BOTH
	column.grow_vertical = Control.GROW_DIRECTION_BOTH
	column.offset_top += OrbitMap.OFFSET.y
	column.offset_bottom += OrbitMap.OFFSET.y
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_targets.add_child(_target(&"star", _gold))
	_targets.add_child(_target(&"check", _par))
	_marks.add_child(_medal_icon)
	_marks.add_child(_egg_icon)
	_status_text.uppercase = true
	_status.add_child(_status_icon)
	_status.add_child(_status_text)
	for line: Control in [_name, _time, _targets, _marks, _status]:
		line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		column.add_child(line)
	_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(column)


## Returns one target time of the dial: an icon and the time.
func _target(icon: StringName, time: Label) -> Control:
	var target: HBoxContainer = UiTheme.row(8)
	target.add_child(Icon.new(icon, UiLook.INK_2, 20.0))
	target.add_child(time)
	return target


## Builds the top left corner: the tier that shows between its two tab glyphs, and the other
## tiers below.
func _build_header() -> Control:
	var header: VBoxContainer = UiTheme.column(14)
	var row: HBoxContainer = UiTheme.row(24)
	_tabs[0].action = &"tab_prev"
	_tabs[1].action = &"tab_next"
	row.add_child(_tabs[0])
	row.add_child(_tier_name)
	row.add_child(_tabs[1])
	header.add_child(row)
	header.add_child(_other_tiers)
	return header


## Builds the top right corner: the gold medals and the eggs of the tier.
func _build_totals() -> Control:
	var totals: VBoxContainer = UiTheme.column(14)
	totals.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	totals.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	for line: Array in [[&"star", _medals], [&"egg", _eggs]]:
		var row: HBoxContainer = UiTheme.row(14)
		row.alignment = BoxContainer.ALIGNMENT_END
		var icon: StringName = line[0]
		var count: Label = line[1]
		row.add_child(Icon.new(icon, UiLook.GOLD, 28.0))
		row.add_child(count)
		totals.add_child(row)
	return totals


## Returns the line of another tier under the header: a lock while it is locked, and its
## name.
func _tier_line(other: StringName) -> Control:
	var line: HBoxContainer = UiTheme.row(14)
	var lock: Icon = Icon.new(&"lock", UiLook.INK_3, 20.0)
	lock.modulate.a = 0.0 if catalog.is_tier_unlocked(other) else 1.0
	var text: Label = UiTheme.label(_tier_key(other), &"Caps")
	text.uppercase = true
	line.add_child(lock)
	line.add_child(text)
	return line


## Returns the translation key of the name of a tier: TIER_BEGINNER for &"beginner".
static func _tier_key(of_tier: StringName) -> String:
	return "TIER_" + String(of_tier).to_upper()
