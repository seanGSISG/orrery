class_name TuningSetting
extends RefCounted
## One value that the tuning overlay edits live: a float or bool property of target (a
## resource, a node, or a script for a static var). file is the res:// file that holds its
## default, or "" for a value that is live only. TuningSetting.save() writes the changed
## values back into those files, so the next run starts with them:
##     var gravity: TuningSetting = TuningSetting.new("gravity", tuning, &"gravity", 0.5,
##             Vector2(5, 40), "res://core/marble_tuning.tres")
##     gravity.adjust(1)                       # one step up, live
##     TuningSetting.save([gravity])           # rewrites the `gravity = ...` line
## In a .tres file the line is `<property> = <value>`; in a .gd file it is the declaration
## `[@export] [static] var <property>: <type> = <value>`. Only the value text changes.

## The value line in a .tres file and in a .gd file; %s is the property name.
const TRES_LINE: String = "^(%s = )(.*)$"
const GD_LINE: String = "^((?:@export )?(?:static )?var %s: \\w+ = )(\\S+)$"

## The name the overlay shows.
var label: String
var target: Object
var property: StringName
## Change for one press; 0 for a bool, which a press turns over.
var step: float
## Lowest and highest value (x, y).
var limits: Vector2
var file: String
## The value in file: at the start, and after each save.
var saved: Variant


## Makes a setting for property of target. Its saved value is the live value now.
func _init(
	title: String,
	on: Object,
	key: StringName,
	change: float = 0.0,
	bounds: Vector2 = Vector2.ZERO,
	path: String = "",
) -> void:
	label = title
	target = on
	property = key
	step = change
	limits = bounds
	file = path
	saved = value()


## Returns the live value.
func value() -> Variant:
	return target.get(property)


## Changes the live value by direction steps (-1 or 1), within limits, at the precision of
## step. A press on a bool turns it over.
func adjust(direction: int) -> void:
	var now: Variant = value()
	if now is bool:
		var on: bool = now
		target.set(property, not on)
		return
	var number: float = now
	var next: float = clampf(number + direction * step, limits.x, limits.y)
	target.set(property, float(String.num(next, _decimals())))


## Returns the value as it appears in the file: `true`, `false` or a float with a point.
func text() -> String:
	var now: Variant = value()
	if now is bool:
		return "true" if now else "false"
	var number: float = now
	var out: String = String.num(number, _decimals())
	return out if out.contains(".") else out + ".0"


## True when the live value differs from the value in file.
func changed() -> bool:
	return value() != saved


## Writes the changed values of settings that have a file into their files, one write per
## file, and marks them saved. Returns the problems; an empty array means every write worked.
static func save(settings: Array[TuningSetting]) -> PackedStringArray:
	var problems: PackedStringArray = []
	var by_file: Dictionary[String, Array] = {}
	for setting: TuningSetting in settings:
		if setting.file != "" and setting.changed():
			var group: Array = by_file.get(setting.file, [])
			group.append(setting)
			by_file[setting.file] = group
	for path: String in by_file:
		var source: String = FileAccess.get_file_as_string(path)
		if source == "":
			problems.append("cannot read %s (%s)" % [path, error_string(FileAccess.get_open_error())])
			continue
		var done: Array[TuningSetting] = []
		for item: Variant in by_file[path]:
			var setting: TuningSetting = item
			var next: String = setting._rewrite(source)
			if next == "":
				problems.append("%s: no line for %s" % [path, setting.property])
			else:
				source = next
				done.append(setting)
		var out: FileAccess = FileAccess.open(path, FileAccess.WRITE)
		if out == null:
			problems.append("cannot write %s (%s)" % [path, error_string(FileAccess.get_open_error())])
			continue
		var written: bool = out.store_string(source)
		out.close()
		if not written:
			problems.append("cannot write %s; restore it with git" % path)
			continue
		for setting: TuningSetting in done:
			setting.saved = setting.value()
	return problems


## Returns source with this setting's value line set to text(), or "" when the line is missing.
func _rewrite(source: String) -> String:
	var line: String = TRES_LINE if file.ends_with(".tres") else GD_LINE
	var pattern: RegEx = RegEx.create_from_string("(?m)" + line % property)
	var found: RegExMatch = pattern.search(source)
	if found == null:
		return ""
	return source.substr(0, found.get_start(2)) + text() + source.substr(found.get_end(2))


## Returns the number of decimals that step needs.
func _decimals() -> int:
	var digits: String = String.num(step, 4)
	return digits.get_slice(".", 1).length() if digits.contains(".") else 0

