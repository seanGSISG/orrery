class_name AscentScreen
extends Screen
## The Ascent menu, between the title and the climb: Continue (when a spot is saved), New
## climb and the Assist switch, under the facts of the saved climb and of the best climb. B
## or Esc goes back to the title.
##
## Continue and New climb start the mode (Ascent.start()). Continue shows only for a spot that
## the climb continues (Ascent.has_spot()). While no zone of the climb is built, New climb is
## off. Assist is Save.ascent.assist: the item turns it on and off and saves it. It counts from
## the next start of the climb.

## Width of the title, the rule and the facts.
const WIDTH: float = 640.0

## The zone level ids of the climb, from the bottom; empty for the built zones of the game. A
## test sets it to the fixture zones.
var zones: Array[StringName] = []
var continue_item: MenuItem = MenuItem.new("ASCENT_CONTINUE", &"ui_accept", true)
var new_item: MenuItem = MenuItem.new("ASCENT_NEW", &"ui_accept", true)
var assist_item: MenuItem = MenuItem.new("ASCENT_ASSIST_OFF", &"ui_accept", true)

var _table: StatTable = StatTable.new(WIDTH, false)
var _spot: Label = UiTheme.label("", &"DataStrong")
var _best_height: Label = UiTheme.label("", &"DataStrong")
var _best_time: Label = UiTheme.label("", &"DataStrong")
var _spot_line: Control
var _height_line: Control
var _time_line: Control


func _init() -> void:
	super()
	var wash: Wash = Wash.new()
	wash.blur = UiLook.TITLE_BLUR
	wash.dim = Vector2(0.58, 0.92)
	wash.left = true
	add_child(wash)
	var column: VBoxContainer = UiTheme.column(0)
	column.set_anchors_and_offsets_preset(Control.PRESET_LEFT_WIDE)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.custom_minimum_size.x = WIDTH
	column.add_child(UiTheme.label("TITLE_ASCENT", &"Title"))
	column.add_child(TickRule.new())
	_spot_line = _table.add_line(UiTheme.label("ASCENT_SPOT", &"Row"), _spot)
	_height_line = _table.add_line(UiTheme.label("ASCENT_BEST_HEIGHT", &"Row"), _best_height)
	_time_line = _table.add_line(UiTheme.label("ASCENT_BEST_TIME", &"Row"), _best_time)
	column.add_child(_table)
	column.add_child(_gap(36.0))
	var menu: VBoxContainer = UiTheme.column(8)
	menu.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	for item: MenuItem in [continue_item, new_item, assist_item]:
		item.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		menu.add_child(item)
	column.add_child(menu)
	var hints: Hints = Hints.new()
	hints.add_hint(&"ui_cancel", "HINT_BACK")
	column.add_child(_gap(36.0))
	column.add_child(hints)
	add_safe_area().add_child(column)
	continue_item.pressed.connect(func() -> void: Ascent.start(false, _climb()))
	new_item.pressed.connect(func() -> void: Ascent.start(true, _climb()))
	assist_item.pressed.connect(_on_assist)


func _ready() -> void:
	FocusButton.link([continue_item, new_item, assist_item])


## Shows the saved climb and the best climb, and gives the focus to Continue, or to New
## climb when no spot is saved, or to Assist when there is no climb yet.
func open() -> void:
	var record: AscentRecord = Save.ascent
	var built: bool = not _climb().is_empty()
	var spot: bool = Ascent.has_spot(_climb())
	var best_time: float = Save.level(Ascent.ID).best_time
	_spot.text = "%s · %s" % [HeightText.metres(record.spot_height), TimeText.full(record.spot_time)]
	_best_height.text = HeightText.metres(record.best_height)
	_best_time.text = TimeText.full(best_time)
	_spot_line.visible = spot
	_height_line.visible = record.best_height >= 1.0
	_time_line.visible = best_time >= 0.0
	_table.visible = _spot_line.visible or _height_line.visible or _time_line.visible
	continue_item.visible = spot
	new_item.set_enabled(built)
	_show_assist()
	if continue_item.visible:
		continue_item.grab_focus()
	elif built:
		new_item.grab_focus()
	else:
		assist_item.grab_focus()


func back() -> bool:
	Game.screen = &"title"
	return true


## Returns the zone level ids that Continue and New climb start.
func _climb() -> Array[StringName]:
	return zones if not zones.is_empty() else Ascent.zones()


## Turns Assist on or off, and saves it.
func _on_assist() -> void:
	Save.ascent.assist = not Save.ascent.assist
	Save.write()
	_show_assist()


## Shows on the Assist item if Assist is on.
func _show_assist() -> void:
	assist_item.set_text("ASCENT_ASSIST_ON" if Save.ascent.assist else "ASCENT_ASSIST_OFF")


## Returns an empty control that is high m units high.
static func _gap(high: float) -> Control:
	var gap: Control = Control.new()
	gap.custom_minimum_size.y = high
	return gap
