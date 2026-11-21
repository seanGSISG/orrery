class_name RunTest
extends GutTest
## Base for tests that drive a LevelRun through MarbleInput and read GameState. Extend it,
## call start_run() (for example in before_each), step with hold(), and assert on run.state.
## run.marble.teleport() is allowed too, because the harness `teleport` command uses it.

var run: LevelRun


## Loads level, adds the extra nodes to it, and starts a run that steps only when told.
## GUT frees the run after the test.
func start_run(level: PackedScene, extra: Array[Node3D] = []) -> LevelRun:
	var root: Level = level.instantiate() as Level
	for node: Node3D in extra:
		root.add_child(node)
	run = LevelRun.create(root)
	run.auto_step = false
	add_child_autofree(run)
	return run


## Steps the run for `seconds` of simulated time with one held input.
func hold(input: MarbleInput, seconds: float) -> void:
	for _i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(input)


## Returns a MarbleInput that rolls along move (x = right, y = forward) at camera yaw 0.
func rolling(move: Vector2) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.move = move
	return input
