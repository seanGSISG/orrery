class_name StatTable
extends VBoxContainer
## A table of facts, as on the results screen: one line per fact, the name on the left and
## the value on the right, with a strong rule above the first line and a thin rule below each
## line. Make it with StatTable.new(width) and add each line with add_line().


func _init(width: float) -> void:
	theme_type_variation = &"Gap0"
	custom_minimum_size.x = width
	var top: HSeparator = HSeparator.new()
	top.theme_type_variation = &"RuleStrong"
	add_child(top)


## Adds one line: name_label on the left, value on the right, and a rule below. Returns the
## line, so that a screen can hide it.
func add_line(name_label: Label, value: Control) -> Control:
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
	add_child(line)
	return line
