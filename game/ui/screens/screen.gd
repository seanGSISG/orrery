class_name Screen
extends Control
## One full-screen menu. Ui shows one screen at a time, by the value of Game.screen. A screen
## builds its controls once, in _init(); Ui calls open() each time the screen shows.
##
## To add a screen: extend Screen, build the controls in _init() (call super() first), fill
## them and take the focus in open(), and add the screen to Ui.screens under a new name. To
## show it, set Game.screen to that name; to leave it, set Game.screen to another.


## Fills the whole window and takes the mouse, so that no click reaches the game below.
func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP


## Shows the state of the game now and gives the focus to one item. Ui calls it each time
## the screen shows.
func open() -> void:
	pass


## Leaves the screen as B or Esc does. Returns false when the screen has no way back.
func back() -> bool:
	return false


## Makes B or Esc (ui_cancel) go back.
func _unhandled_input(event: InputEvent) -> void:
	if is_visible_in_tree() and event.is_action_pressed(&"ui_cancel"):
		accept_event()
		if back():
			Music.play_ui(&"back")


## Adds and returns a container that fills the screen and keeps its children off the screen
## edges (UiLook.SAFE). Anchor the content inside it.
func add_safe_area() -> Control:
	var margin: MarginContainer = MarginContainer.new()
	margin.theme_type_variation = &"Safe"
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var area: Control = Control.new()
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(area)
	add_child(margin)
	return area
