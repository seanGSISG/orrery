class_name TitleScreen
extends Screen
## The title screen: the name of the game, the chart, and the menu Play, Ascent, Settings and
## Quit. The live level behind it is Ui's Backdrop.
##
## Ascent has no mode yet, so its item is off. #27 turns it on with ascent.set_enabled(true)
## and starts the mode in _on_ascent().

## Width of the name and the rule under it.
const NAME_WIDTH: float = 640.0

var play: MenuItem = MenuItem.new("TITLE_PLAY", &"ui_accept", true)
var ascent: MenuItem = MenuItem.new("TITLE_ASCENT", &"ui_accept", true)
var settings: MenuItem = MenuItem.new("TITLE_SETTINGS", &"ui_accept", true)
var quit: MenuItem = MenuItem.new("TITLE_QUIT", &"ui_accept", true)


func _init() -> void:
	super()
	var wash: Wash = Wash.new()
	wash.blur = UiLook.TITLE_BLUR
	wash.dim = Vector2(0.58, 0.92)
	wash.left = true
	add_child(wash)
	add_child(OrreryDiagram.new())
	var column: VBoxContainer = UiTheme.column(0)
	column.set_anchors_and_offsets_preset(Control.PRESET_LEFT_WIDE)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.custom_minimum_size.x = NAME_WIDTH
	column.add_child(UiTheme.label("GAME_NAME", &"Logo"))
	column.add_child(TickRule.new())
	var menu: VBoxContainer = UiTheme.column(8)
	menu.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	for item: MenuItem in [play, ascent, settings, quit]:
		item.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		menu.add_child(item)
	var gap: Control = Control.new()
	gap.custom_minimum_size.y = 56.0
	column.add_child(gap)
	column.add_child(menu)
	add_safe_area().add_child(column)
	ascent.set_enabled(false)
	play.pressed.connect(func() -> void: Game.screen = &"level_select")
	ascent.pressed.connect(_on_ascent)
	settings.pressed.connect(func() -> void: Game.screen = &"settings")
	quit.pressed.connect(func() -> void: get_tree().quit())


func _ready() -> void:
	FocusButton.link([play, ascent, settings, quit])


func open() -> void:
	play.grab_focus()


## Starts Ascent. #27 fills it in.
func _on_ascent() -> void:
	pass
