class_name ResultsScreen
extends Screen
## The results of a finished run, over the level: the time and the medal on the dial, and a
## table with the record, the gems, the egg and the target times. Next plays the level after
## this one, Retry restarts (so does the `restart` action; Game handles it), and Levels or
## ui_cancel goes to the level select.
##
## Ui sets `catalog` and `previous_best` before it shows the screen. A run is a new record
## when it beats previous_best: the save of the finish can land a tick after the finish, so
## the screen does not ask Save for it.

## Width of the table.
const TABLE_WIDTH: float = 640.0
## The part of the screen width, from the left, that the dial has its middle in.
const DIAL_SIDE: float = 0.625

## Gives the level after this one.
var catalog: LevelCatalog
## The best time of the level before this run, s; negative for no finish before.
var previous_best: float = -1.0
## True when the run that shows beat previous_best, or is the first finish. open() sets it.
var new_record: bool = false

var _dial: Dial = Dial.new()
var _name: Label = UiTheme.label("", &"Subtitle")
var _time: Label = UiTheme.label("", &"BigTime")
var _medal_icon: Icon = Icon.new(&"", UiLook.GOLD, 32.0)
var _medal: Label = UiTheme.label("", &"CapsGold")
var _record_name: Label = UiTheme.label("", &"Row")
var _record: Label = UiTheme.label("", &"DataStrong")
var _gems: Label = UiTheme.label("", &"DataStrong")
var _egg_icon: Icon = Icon.new(&"check", UiLook.INK, 18.0)
var _egg: Label = UiTheme.label("", &"DataStrong")
var _gold: Label = UiTheme.label("", &"DataStrong")
var _par: Label = UiTheme.label("", &"DataStrong")
var _gold_line: Control
var _par_line: Control
var _next: MenuItem = MenuItem.new("RESULTS_NEXT", &"ui_accept", true)
var _retry: MenuItem = MenuItem.new("RESULTS_RETRY", &"restart")
var _levels: MenuItem = MenuItem.new("RESULTS_LEVELS", &"ui_cancel")
var _next_id: StringName = &""


func _init() -> void:
	super()
	add_child(Wash.new())
	_build_dial()
	var area: Control = add_safe_area()
	area.add_child(_build_table())
	var items: HBoxContainer = UiTheme.row(8)
	items.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	items.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	items.grow_vertical = Control.GROW_DIRECTION_BEGIN
	for item: MenuItem in [_next, _retry, _levels]:
		items.add_child(item)
	area.add_child(items)
	_next.pressed.connect(func() -> void: Game.load_level(_next_id))
	_retry.pressed.connect(Game.restart)
	_levels.pressed.connect(func() -> void: Game.screen = &"level_select")


func _ready() -> void:
	FocusButton.link([_next, _retry, _levels], true)


## Shows the finished run of Game, and gives the focus to Next, or to Retry when there is no
## next level to play.
func open() -> void:
	var run: LevelRun = Game.run
	if run == null:
		return
	var state: GameState = run.state
	var level: Level = run.level
	_name.text = tr(level.title)
	_time.text = TimeText.full(state.timer)
	_dial.show_times(state.timer, level.gold, level.par, true)
	_medal_icon.icon = &"star" if state.medal == &"gold" else &"check"
	_medal_icon.color = UiLook.GOLD if state.medal == &"gold" else UiLook.INK
	_medal_icon.visible = state.medal != &"none"
	_medal.text = "MEDAL_" + String(state.medal).to_upper()
	_medal.theme_type_variation = &"CapsGold" if state.medal == &"gold" else &"CapsStrong"
	new_record = previous_best < 0.0 or state.timer < previous_best
	_record_name.text = "RESULTS_NEW_RECORD" if new_record else "RESULTS_BEST"
	_record_name.theme_type_variation = &"RowAccent" if new_record else &"Row"
	_record.theme_type_variation = &"DataAccent" if new_record else &"DataStrong"
	if not new_record:
		_record.text = TimeText.full(previous_best)
	elif previous_best >= 0.0:
		_record.text = "−" + TimeText.difference(previous_best - state.timer)
	else:
		_record.text = ""
	_gems.text = "%d/%d" % [state.gems_collected, state.gems_total]
	var egg: bool = state.egg_found or Save.level(level.id).egg
	_egg_icon.visible = egg
	_egg.text = "RESULTS_EGG_FOUND" if egg else "RESULTS_EGG_MISSING"
	_gold.text = TimeText.full(level.gold)
	_par.text = TimeText.full(level.par)
	_gold_line.visible = level.gold > 0.0
	_par_line.visible = level.par > 0.0
	_next_id = catalog.next(level.id) if catalog != null else &""
	# This run can be the one that unlocks the next level, before its save lands.
	var unlocked: bool = _next_id != &"" and (Save.is_unlocked(_next_id) or state.medal != &"none")
	_next.visible = unlocked and catalog.info(_next_id).built
	if _next.visible:
		_next.grab_focus()
	else:
		_retry.grab_focus()


func back() -> bool:
	Game.screen = &"level_select"
	return true


## Builds the dial with the level name, the time and the medal in it.
func _build_dial() -> void:
	var side: CenterContainer = CenterContainer.new()
	side.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	side.anchor_right = DIAL_SIDE
	side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side.add_child(_dial)
	var column: VBoxContainer = UiTheme.column(0)
	var medal: HBoxContainer = UiTheme.row(14)
	_medal.uppercase = true
	medal.add_child(_medal_icon)
	medal.add_child(_medal)
	for line: Control in [_name, _time, medal]:
		line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		column.add_child(line)
	side.add_child(column)
	add_child(side)


## Builds the table on the right: one line per fact, with a rule between the lines.
func _build_table() -> Control:
	var table: VBoxContainer = UiTheme.column(0)
	table.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT)
	table.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	table.grow_vertical = Control.GROW_DIRECTION_BOTH
	table.custom_minimum_size.x = TABLE_WIDTH
	var top: HSeparator = HSeparator.new()
	top.theme_type_variation = &"RuleStrong"
	table.add_child(top)
	var egg: HBoxContainer = UiTheme.row(14)
	egg.add_child(_egg_icon)
	egg.add_child(_egg)
	_add_line(table, _record_name, _record)
	_add_line(table, UiTheme.label("RESULTS_GEMS", &"Row"), _gems)
	_add_line(table, UiTheme.label("RESULTS_EGG", &"Row"), egg)
	_gold_line = _add_line(table, UiTheme.label("RESULTS_GOLD", &"Row"), _gold)
	_par_line = _add_line(table, UiTheme.label("RESULTS_PAR", &"Row"), _par)
	return table


## Adds one line to table: name on the left, value on the right, and a rule below. Returns
## the line.
func _add_line(table: VBoxContainer, name_label: Label, value: Control) -> Control:
	var line: VBoxContainer = UiTheme.column(0)
	var row: HBoxContainer = UiTheme.row(24)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	value.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(name_label)
	row.add_child(value)
	var inset: MarginContainer = MarginContainer.new()
	inset.theme_type_variation = &"TableLine"
	inset.add_child(row)
	line.add_child(inset)
	var rule: HSeparator = HSeparator.new()
	rule.theme_type_variation = &"Rule"
	line.add_child(rule)
	table.add_child(line)
	return line
