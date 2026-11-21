@abstract
class_name PowerUp
extends RefCounted
## A power-up that the PowerUpSlot holds (docs/plan.md §2.5). A pickup object makes one from
## its own settings and gives it to run.slot.take(). Extend it once per power-up type: pass the
## id (the marker type, for example &"coil_spring") to super() and implement use().

## The power-up type. GameState.power_up shows it while the slot holds this power-up.
var id: StringName


## Makes a power-up of the type power_up_id.
func _init(power_up_id: StringName) -> void:
	id = power_up_id


## Applies the effect once, before the marble moves in this tick. The slot is already empty,
## and it emits the `<id>.use` feedback after this call.
@abstract func use(run: LevelRun) -> void
