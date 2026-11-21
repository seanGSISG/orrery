class_name SettingsScreen
extends Screen
## The settings screen: its frame only. #23 fills it: add the controls to `content`, which
## takes the room between the title and the Back item, and give the first one the focus in
## open(). The title menu and the pause menu open it; Back and ui_cancel return to the one
## that did.

## The screen that Back returns to; Ui sets it to the screen that opened the settings.
var return_to: StringName = &"title"
## The room for the settings controls.
var content: VBoxContainer = UiTheme.column(0)

var _back: MenuItem = MenuItem.new("SETTINGS_BACK", &"ui_cancel")


func _init() -> void:
	super()
	var wash: Wash = Wash.new()
	wash.dim = Vector2(0.72, 0.92)
	add_child(wash)
	var column: VBoxContainer = UiTheme.column(24)
	column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	column.add_child(UiTheme.label("SETTINGS_TITLE", &"Title"))
	column.add_child(TickRule.new(48.0))
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(content)
	_back.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	column.add_child(_back)
	add_safe_area().add_child(column)
	_back.pressed.connect(back)


func open() -> void:
	_back.grab_focus()


func back() -> bool:
	Game.screen = return_to
	return true
