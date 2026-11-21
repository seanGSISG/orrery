class_name ResultsScreen
extends Screen
## The results of a finished run, over the level: the time and the medal on the dial, and a
## table with the record, the gems, the egg (for a level with several eggs: how many of them
## are found) and the target times. Next plays the level after
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
## The egg line: Found or Not found, or for a level with several eggs how many of them are
## found ("1/2"). A test reads it.
var egg: Label = UiTheme.label("", &"DataStrong")

var _dial: Dial = Dial.new()
var _name: Label = UiTheme.label("", &"Subtitle")
var _time: Label = UiTheme.label("", &"BigTime")
var _medal_icon: Icon = Icon.new(&"", UiLook.GOLD, 32.0)
var _medal: Label = UiTheme.label("", &"CapsGold")
var _record_name: Label = UiTheme.label("", &"Row")
var _record: Label = UiTheme.label("", &"DataStrong")
var _gems: Label = UiTheme.label("", &"DataStrong")
var _egg_icon: Icon = Icon.new(&"check", UiLook.INK, 18.0)
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
	# An egg of the level is found when the save has its id or this run found it: the save
	# of a find can land a tick after it.
	var saved: PackedStringArray = Save.level(level.id).eggs
	var total: int = 0
	var found: int = 0
	for object: LevelObject in run.objects:
		if object is Egg:
			total += 1
			var known: bool = saved.has(String(object.name)) or run.rules.found_eggs.has(object)
			found += 1 if known else 0
	var every: bool = total > 0 and found == total
	_egg_icon.visible = every
	egg.text = "RESULTS_EGG_FOUND" if every else "RESULTS_EGG_MISSING"
	if total > 1:
		egg.text = "%d/%d" % [found, total]
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


## Builds the table on the right: one line per fact.
func _build_table() -> Control:
	var table: StatTable = StatTable.new(TABLE_WIDTH)
	table.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT)
	table.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	table.grow_vertical = Control.GROW_DIRECTION_BOTH
	var egg_row: HBoxContainer = UiTheme.row(14)
	egg_row.add_child(_egg_icon)
	egg_row.add_child(egg)
	table.add_line(_record_name, _record)
	table.add_line(UiTheme.label("RESULTS_GEMS", &"Row"), _gems)
	table.add_line(UiTheme.label("RESULTS_EGG", &"Row"), egg_row)
	_gold_line = table.add_line(UiTheme.label("RESULTS_GOLD", &"Row"), _gold)
	_par_line = table.add_line(UiTheme.label("RESULTS_PAR", &"Row"), _par)
	return table
