class_name GameState
extends RefCounted
## The one observable snapshot of the game (docs/design/core-runtime.md §6). GUT tests read
## LevelRun.state; the harness sends Game.snapshot().to_dict() as JSON. Each field has one
## writer, named at the field.

## Ticks since the start or the last restart. Run.
var tick: int = 0
## Level id; empty in menus. Run.
var level: StringName = &""
## &"none", &"playing", &"respawning" or &"finished". Run (&"none"), then rules.
var status: StringName = &"none"
## &"title", &"level_select", &"settings", &"play", &"pause", &"results", &"ascent" or
## &"ascent_stats". Game.
var screen: StringName = &"play"
## &"keyboard" or &"pad". Game.snapshot().
var input_device: StringName = &"keyboard"
## Marble centre in world space (m), velocity (m/s) and spin (rad/s). Run.
var position: Vector3 = Vector3.ZERO
var velocity: Vector3 = Vector3.ZERO
var spin: Vector3 = Vector3.ZERO
## Unit vector opposite of gravity. Run.
var up: Vector3 = Vector3.UP
## Marble.frame: the reference for MarbleInput.camera_yaw, with y = up. Run.
var frame: Basis = Basis.IDENTITY
## True when the last sub-step stood on a floor (MarbleTuning.floor_min_up), not a wall. Run.
var on_ground: bool = false
## Gems collected in this run, and gems in the level. Rules.
var gems_collected: int = 0
var gems_total: int = 0
## Level clock, s. It starts at the first move, jump or use input and stops at the finish.
## Rules.
var timer: float = 0.0
## &"none", &"qualified" (at or under par) or &"gold", set at the finish. Rules.
var medal: StringName = &"none"
## Held power-up id; empty when the slot is empty. Slot (#17).
var power_up: StringName = &""
## Node name of the last checkpoint; empty means the start pad. Rules.
var checkpoint: StringName = &""
## True when an egg was found in this run. Rules.
var egg_found: bool = false
## Ascent only: m above the climb start, along up. Ascent mode (#27).
var height: float = 0.0


## Returns every field above by name, with vectors as [x, y, z], a basis as its columns
## [[x], [y], [z]] and names as strings. A new field reaches the dictionary with no other edit.
func to_dict() -> Dictionary:
	var out: Dictionary = {}
	for property: Dictionary in get_property_list():
		var usage: int = property["usage"]
		if usage & PROPERTY_USAGE_SCRIPT_VARIABLE:
			var key: String = property["name"]
			out[key] = _plain(get(key))
	return out


## Returns value as a plain JSON value.
static func _plain(value: Variant) -> Variant:
	if value is Vector3:
		var vector: Vector3 = value
		return [vector.x, vector.y, vector.z]
	if value is Basis:
		var basis: Basis = value
		return [_plain(basis.x), _plain(basis.y), _plain(basis.z)]
	if value is StringName:
		var name: StringName = value
		return String(name)
	return value
