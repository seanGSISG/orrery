class_name PowerUpSlot
extends RefCounted
## The one held power-up (docs/plan.md §2.5). LevelRun makes a new slot at each restart, so a
## restart empties it, and keeps it through a checkpoint respawn. Pickups call take(); LevelRun
## calls before_step() at the start of each tick. The slot writes GameState.power_up.
##
## - The slot holds at most one power-up, and only while the status is &"playing".
## - A new press of `use` applies the held power-up, empties the slot and emits the run's
##   feedback `<id>.use` at the marble, with strength 1. A use that is held down from before
##   does nothing, so one press uses one power-up.

## The held power-up; null when the slot is empty.
var held: PowerUp = null

var _run: LevelRun
## MarbleInput.use of the last tick.
var _use_was_down: bool = false


## Makes an empty slot for run.
func _init(run: LevelRun) -> void:
	_run = run
	_run.state.power_up = &""


## Holds power_up if the slot is empty and the run is playing. Returns false when it does not;
## then the pickup stays in place.
func take(power_up: PowerUp) -> bool:
	if held != null or _run.state.status != &"playing":
		return false
	held = power_up
	_run.state.power_up = power_up.id
	return true


## On a new use press while playing, empties the slot, applies the held power-up and emits
## its `.use` feedback.
func before_step(input: MarbleInput) -> void:
	var pressed: bool = input.use and not _use_was_down
	_use_was_down = input.use
	if not pressed or held == null or _run.state.status != &"playing":
		return
	var power_up: PowerUp = held
	held = null
	_run.state.power_up = &""
	power_up.use(_run)
	_run.feedback.emit(StringName("%s.use" % power_up.id), 1.0, _run.marble.position)
