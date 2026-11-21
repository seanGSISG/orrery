class_name PowerUpSlot
extends RefCounted
## The one held power-up. LevelRun makes one and calls before_step() each tick; pickups call
## take(). This is the #7 stub: it holds nothing. #17 adds the logic.

## Held power-up id; empty when the slot is empty.
var held: StringName = &""

var _run: LevelRun


func _init(run: LevelRun) -> void:
	_run = run


## Holds id if the slot is empty. Returns false when the slot is full; then the pickup stays.
## The stub always returns false.
func take(_id: StringName) -> bool:
	return false


## On a new use press, applies the held effect and empties the slot.
func before_step(_input: MarbleInput) -> void:
	pass
