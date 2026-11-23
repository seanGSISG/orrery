class_name PauseScreen
extends Screen
## The pause menu, over the paused level: Resume, Restart, Settings and Levels on the dial,
## with the level and its clock. The `pause` action (Menu or Esc) and ui_cancel resume; the
## `restart` action restarts (Game handles it). Levels ends the run.
##
## An Ascent climb has no restart, so Restart does not show. In place of Levels it has Save
## and quit, which ends the run and opens the Ascent menu; the mode saves the spot. The line
## under the title also gives the marble's height.

var _dial: Dial = Dial.new()
var _line: Label = UiTheme.label("")
var _resume: MenuItem = MenuItem.new("PAUSE_RESUME", &"pause")
var _restart: MenuItem = MenuItem.new("PAUSE_RESTART", &"restart")
var _settings: MenuItem = MenuItem.new("PAUSE_SETTINGS")
var _levels: MenuItem = MenuItem.new("PAUSE_LEVELS")
## The screen that the last item goes to: the level select, or the Ascent menu from a climb.
var _quit_to: StringName = &"level_select"


func _init() -> void:
	super()
	add_child(Wash.new())
	var middle: CenterContainer = CenterContainer.new()
	middle.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	middle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	middle.add_child(_dial)
	var column: VBoxContainer = UiTheme.column(0)
	column.add_child(UiTheme.label("PAUSE_TITLE", &"Title"))
	column.add_child(_line)
	var gap: Control = Control.new()
	gap.custom_minimum_size.y = 20.0
	column.add_child(gap)
	for item: MenuItem in [_resume, _restart, _settings, _levels]:
		column.add_child(item)
	var hints: Hints = Hints.new()
	hints.add_hint(&"ui_accept", "HINT_SELECT")
	gap = Control.new()
	gap.custom_minimum_size.y = 28.0
	column.add_child(gap)
	column.add_child(hints)
	for line: Control in column.get_children():
		line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	middle.add_child(column)
	add_child(middle)
	_resume.pressed.connect(func() -> void: Game.screen = &"play")
	_restart.pressed.connect(Game.restart)
	_settings.pressed.connect(func() -> void: Game.screen = &"settings")
	_levels.pressed.connect(func() -> void: Game.screen = _quit_to)


func _ready() -> void:
	FocusButton.link([_resume, _restart, _settings, _levels])


## Shows the level and its clock, and gives the focus to Resume.
func open() -> void:
	var run: LevelRun = Game.run
	if run != null:
		var climbing: bool = Ascent.of(run) != null
		_restart.visible = run.restartable
		_levels.set_text("PAUSE_SAVE_QUIT" if climbing else "PAUSE_LEVELS")
		_quit_to = &"ascent" if climbing else &"level_select"
		var level: Level = run.level
		var facts: PackedStringArray = [tr(level.title), TimeText.full(run.state.timer)]
		if climbing:
			facts.insert(1, HeightText.metres(run.state.height))
		_line.text = " · ".join(facts)
		_dial.show_times(run.state.timer, level.gold, level.par, false)
	_resume.grab_focus()


func back() -> bool:
	Game.screen = &"play"
	return true
