class_name LevelObject
extends Node3D
## The base of every object that a level marker places (docs/design/core-runtime.md §5). The
## @export vars are the object's settings. LevelRun calls the four hooks; override the ones
## the object needs. An object acts only through the run: run.marble.add_velocity() and
## teleport(), run.rules, run.slot.take(), Solid.move(), its own collision_layer, and feedback.

## Rumble and sound. kind is &"<type>.<event>", strength is 0..1, at is a world position.
@warning_ignore("unused_signal")
signal feedback(kind: StringName, strength: float, at: Vector3)


## Goes back to the start state. restart is false for a checkpoint respawn.
func reset(_restart: bool) -> void:
	pass


## Runs each tick, before the marble moves. t is the run time in seconds. Movers set their
## pose from t here.
func advance(_run: LevelRun, _t: float) -> void:
	pass


## Runs when the marble touched one of this object's Solids in this tick.
func on_touch(_run: LevelRun, _contact: Contact) -> void:
	pass


## Runs each tick while the marble overlaps one of this object's triggers. first is true on
## the tick that the overlap starts.
func on_overlap(_run: LevelRun, _first: bool) -> void:
	pass
