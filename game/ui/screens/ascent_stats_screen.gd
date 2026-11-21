class_name AscentStatsScreen
extends Screen
## The stats of an Ascent climb that reached the gate, over the climb: the time on the dial
## with "To be continued", and a table with the record, the height, the falls, the metres
## fallen and, for a climb that used Assist, the Assist mark. Done or ui_cancel goes to the
## Ascent menu.
##
## Ui sets `previous_best` before it shows the screen. A climb is a new record when it beats
## previous_best: the save of the finish can land a tick after the finish, so the screen does
## not ask Save for it. An assisted climb is never a new record: the screen shows its time,
## the Assist mark and the best time as it was.

## Width of the table.
const TABLE_WIDTH: float = 640.0
## The part of the screen width, from the left, that the dial has its middle in.
const DIAL_SIDE: float = 0.625

## The best time of the climb before this one, s; negative for no climb to the gate before.
var previous_best: float = -1.0
## True when the climb that shows beat previous_best, or is the first to the gate, and did
## not use Assist. open() sets it.
var new_record: bool = false
## The values that show; a test reads them.
var time: Label = UiTheme.label("", &"BigTime")
var falls: Label = UiTheme.label("", &"DataStrong")
var fallen: Label = UiTheme.label("", &"DataStrong")
## The line of the Assist mark; it shows for a climb that used Assist.
var assist_line: Control

var _dial: Dial = Dial.new()
var _record_name: Label = UiTheme.label("", &"Row")
var _record: Label = UiTheme.label("", &"DataStrong")
var _height: Label = UiTheme.label("", &"DataStrong")
var _done: MenuItem = MenuItem.new("ASCENT_DONE", &"ui_accept")


func _init() -> void:
	super()
	add_child(Wash.new())
	_build_dial()
	var area: Control = add_safe_area()
	var table: StatTable = StatTable.new(TABLE_WIDTH)
	table.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT)
	table.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	table.grow_vertical = Control.GROW_DIRECTION_BOTH
	table.add_line(_record_name, _record)
	table.add_line(UiTheme.label("ASCENT_HEIGHT", &"Row"), _height)
	table.add_line(UiTheme.label("ASCENT_FALLS", &"Row"), falls)
	table.add_line(UiTheme.label("ASCENT_FALLEN", &"Row"), fallen)
	var used: Label = UiTheme.label("ASCENT_ASSIST_USED", &"DataStrong")
	assist_line = table.add_line(UiTheme.label("ASCENT_ASSIST", &"Row"), used)
	area.add_child(table)
	_done.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	_done.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_done.grow_vertical = Control.GROW_DIRECTION_BEGIN
	area.add_child(_done)
	_done.pressed.connect(back)


## Shows the finished climb of Game, and gives the focus to Done.
func open() -> void:
	var climb: Ascent = Ascent.of(Game.run)
	if climb == null:
		return
	var state: GameState = Game.run.state
	time.text = TimeText.full(state.timer)
	_dial.show_times(state.timer, 0.0, 0.0, true)
	var faster: bool = previous_best < 0.0 or state.timer < previous_best
	new_record = faster and not climb.assisted
	_record_name.text = "RESULTS_NEW_RECORD" if new_record else "RESULTS_BEST"
	_record_name.theme_type_variation = &"RowAccent" if new_record else &"Row"
	_record.theme_type_variation = &"DataAccent" if new_record else &"DataStrong"
	if not new_record:
		_record.text = TimeText.full(previous_best) if previous_best >= 0.0 else "TIME_NONE"
	elif previous_best >= 0.0:
		_record.text = "−" + TimeText.difference(previous_best - state.timer)
	else:
		_record.text = ""
	_height.text = HeightText.metres(climb.top)
	falls.text = str(climb.falls)
	fallen.text = HeightText.metres(climb.fallen)
	assist_line.visible = climb.assisted
	_done.grab_focus()


func back() -> bool:
	Game.screen = &"ascent"
	return true


## Builds the dial with the name of the mode, the time and "To be continued" in it.
func _build_dial() -> void:
	var side: CenterContainer = CenterContainer.new()
	side.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	side.anchor_right = DIAL_SIDE
	side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side.add_child(_dial)
	var column: VBoxContainer = UiTheme.column(0)
	var words: Label = UiTheme.label("ASCENT_GATE", &"CapsStrong")
	words.uppercase = true
	for line: Control in [UiTheme.label("TITLE_ASCENT", &"Subtitle"), time, words]:
		line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		column.add_child(line)
	side.add_child(column)
	add_child(side)
