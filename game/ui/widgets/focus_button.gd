class_name FocusButton
extends BaseButton
## The base of the things that a player chooses in a menu (MenuItem, LevelNode). The focus
## marks the one that ui_accept chooses. A move of the mouse over the button gives it the
## focus, so the mouse and the pad share one mark. A choice plays the select sound.

## True after the button is drawn at its place since it last became visible.
var _placed: bool = false


## Makes items one list for the focus: ui_up and ui_down (ui_left and ui_right when
## horizontal is true) move to the item before and the item after, and go round at the ends.
## The items must be in the scene tree. The focus skips an item that is hidden.
static func link(items: Array[FocusButton], horizontal: bool = false) -> void:
	for i: int in items.size():
		var item: FocusButton = items[i]
		var before: NodePath = item.get_path_to(items[i - 1])
		var after: NodePath = item.get_path_to(items[(i + 1) % items.size()])
		item.focus_previous = before
		item.focus_next = after
		if horizontal:
			item.focus_neighbor_left = before
			item.focus_neighbor_right = after
		else:
			item.focus_neighbor_top = before
			item.focus_neighbor_bottom = after


func _init() -> void:
	focus_mode = Control.FOCUS_ALL


## Notes when the button is drawn in its place, and when it shows again.
func _notification(what: int) -> void:
	if what == NOTIFICATION_DRAW:
		_placed = true
	elif what == NOTIFICATION_VISIBILITY_CHANGED:
		_placed = false


## Takes the focus when the mouse moves over the button. A mouse that only rests there does
## not, so it cannot take the focus from the pad. A button that is not drawn yet does not
## either: its container has not put it in its place, so the mouse is not really over it.
func _gui_input(event: InputEvent) -> void:
	var can_focus: bool = _placed and focus_mode != Control.FOCUS_NONE and not has_focus()
	if event is InputEventMouseMotion and can_focus:
		grab_focus()


func _pressed() -> void:
	Music.play_ui(&"select")
