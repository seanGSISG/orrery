class_name Hints
extends HBoxContainer
## A row of button hints, such as "A Play   B Back". Each hint is the glyph of an input
## action and a short text. Add them with add_hint().


func _init() -> void:
	theme_type_variation = &"Gap44"
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Adds the hint for action with the text of text_key, and returns its row, so that a screen
## can hide it.
func add_hint(action: StringName, text_key: String) -> Control:
	var hint: HBoxContainer = UiTheme.row(14)
	var glyph: InputGlyph = InputGlyph.new()
	glyph.action = action
	hint.add_child(glyph)
	hint.add_child(UiTheme.label(text_key))
	add_child(hint)
	return hint
