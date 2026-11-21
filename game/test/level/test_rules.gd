extends RunTest
## The level rules through the boundary: MarbleInput and LevelRun.teleport() in (the harness
## `teleport` command uses the same call), GameState and the run's feedback out. One test per
## rule, on test/levels/rules.tscn.

const RULES: PackedScene = preload("res://test/levels/rules.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")

# The layout of rules.tscn: a floor at y = 0 from x = -20 to 20 and z = -30 to 10, par 10 s
# and gold 5 s. Object positions are on the floor.
const GEM_WEST: Vector3 = Vector3(-6, 0, 0)
const GEM_EAST: Vector3 = Vector3(6, 0, 0)
const CHECKPOINT: Vector3 = Vector3(0, 0, -10)
const EGG: Vector3 = Vector3(-6, 0, -10)
const FINISH: Vector3 = Vector3(0, 0, -20)
## A point past the floor's east edge.
const VOID: Vector3 = Vector3(30, 0, 0)

## Kinds of the run's feedback in this test, in order.
var heard: Array[StringName] = []


func before_each() -> void:
	heard.clear()
	start_run(RULES)
	run.feedback.connect(_hear)


## The gems are counted, and each gem counts once and hides.
func test_gems_are_counted_and_collected_once() -> void:
	assert_eq(run.state.gems_total, 2)
	visit(GEM_WEST)
	visit(Vector3.ZERO)
	visit(GEM_WEST)
	assert_eq(run.state.gems_collected, 1)
	assert_eq(heard.count(&"gem.collect"), 1)
	visit(GEM_EAST)
	assert_eq(run.state.gems_collected, 2)


## The finish ends the run only after the last gem.
func test_finish_opens_only_with_every_gem() -> void:
	visit(GEM_WEST)
	visit(FINISH)
	assert_eq(run.state.status, &"playing")
	visit(GEM_EAST)
	visit(FINISH)
	assert_eq(run.state.status, &"finished")
	assert_eq(heard.count(&"finish.open"), 1)
	assert_eq(heard.count(&"finish.reach"), 1)


## The clock waits for the first move, jump or use input, then runs with or without input.
func test_clock_starts_at_first_input() -> void:
	var look: MarbleInput = MarbleInput.new()
	look.camera_yaw = 1.0
	hold(look, 1.0)
	assert_eq(run.state.timer, 0.0)
	hold(rolling(Vector2(0, 1)), 0.5)
	assert_almost_eq(run.state.timer, 0.5, 0.0001)
	hold(MarbleInput.new(), 0.5)
	assert_almost_eq(run.state.timer, 1.0, 0.0001)


## The clock stops at the finish.
func test_clock_stops_at_finish() -> void:
	finish_after(2.0)
	var at_finish: float = run.state.timer
	hold(MarbleInput.new(), 1.0)
	assert_eq(run.state.timer, at_finish)


## The medal is gold at or under the gold time, qualified at or under par, else none.
func test_medal_follows_par_and_gold() -> void:
	finish_after(3.0)
	assert_eq(run.state.medal, &"gold")
	run.restart()
	finish_after(8.0)
	assert_eq(run.state.medal, &"qualified")
	run.restart()
	finish_after(12.0)
	assert_eq(run.state.medal, &"none")


## A fall below the kill height respawns the marble still on the start pad in under 2 s,
## and the clock runs on.
func test_fall_respawns_on_start_pad_within_two_seconds() -> void:
	run.step(rolling(Vector2(0, 1)))
	run.teleport(VOID + Vector3.UP * TUNING.radius, Vector3.ZERO)
	var ticks: int = 0
	var saw_respawning: bool = false
	while ticks < 240 and not (saw_respawning and run.state.status == &"playing"):
		run.step(MarbleInput.new())
		ticks += 1
		saw_respawning = saw_respawning or run.state.status == &"respawning"
	assert_true(saw_respawning)
	assert_lt(ticks / float(Engine.physics_ticks_per_second), 2.0)
	assert_almost_eq(run.state.position, Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
	assert_eq(run.state.velocity, Vector3.ZERO)
	assert_almost_eq(run.state.timer, (ticks + 1) / float(Engine.physics_ticks_per_second), 0.0001)


## A respawn after a checkpoint puts the marble on it and keeps the gems, the egg and the
## held power-up.
func test_checkpoint_respawn_keeps_progress() -> void:
	visit(GEM_WEST)
	visit(EGG)
	visit(CHECKPOINT)
	assert_eq(run.state.checkpoint, &"Checkpoint")
	assert_eq(heard.count(&"checkpoint.reach"), 1)
	run.slot.held = &"coil_spring"
	run.teleport(VOID + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(MarbleInput.new(), 2.0)
	assert_almost_eq(run.state.position, CHECKPOINT + Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
	assert_eq(run.state.status, &"playing")
	assert_eq(run.state.gems_collected, 1)
	assert_true(run.state.egg_found)
	assert_eq(run.slot.held, &"coil_spring")
	visit(GEM_WEST)
	assert_eq(run.state.gems_collected, 1)


## A restart starts a fresh attempt at once: no time, gems, checkpoint, egg or power-up, and
## the marble still on the start pad.
func test_restart_starts_fresh_at_once() -> void:
	run.step(rolling(Vector2(0, 1)))
	visit(GEM_WEST)
	visit(EGG)
	visit(CHECKPOINT)
	run.slot.held = &"coil_spring"
	run.restart()
	assert_eq(run.state.tick, 0)
	assert_eq(run.state.timer, 0.0)
	assert_eq(run.state.gems_collected, 0)
	assert_eq(run.state.checkpoint, &"")
	assert_false(run.state.egg_found)
	assert_eq(run.state.status, &"playing")
	assert_eq(run.slot.held, &"")
	assert_almost_eq(run.state.position, Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
	visit(GEM_WEST)
	assert_eq(run.state.gems_collected, 1)


## The egg opens once per run.
func test_egg_is_found_once() -> void:
	visit(EGG)
	assert_true(run.state.egg_found)
	visit(Vector3.ZERO)
	visit(EGG)
	assert_eq(heard.count(&"egg.open"), 1)


## LevelRun.teleport() shows the new place in the state before the next tick.
func test_teleport_writes_state_at_once() -> void:
	run.teleport(Vector3(3, 1, 2), Vector3(1, 0, 0))
	assert_eq(run.state.position, Vector3(3, 1, 2))
	assert_eq(run.state.velocity, Vector3(1, 0, 0))


## Puts the marble still on the floor at point and steps one tick.
func visit(point: Vector3) -> void:
	run.teleport(point + Vector3.UP * TUNING.radius, Vector3.ZERO)
	run.step(MarbleInput.new())


## Starts the clock, collects both gems, waits until the clock shows seconds, and finishes.
func finish_after(seconds: float) -> void:
	run.step(rolling(Vector2(0, 1)))
	visit(GEM_WEST)
	visit(GEM_EAST)
	hold(MarbleInput.new(), seconds - run.state.timer)
	visit(FINISH)
	assert_eq(run.state.status, &"finished")


## Records the kind of each feedback.
func _hear(kind: StringName, _strength: float, _at: Vector3) -> void:
	heard.append(kind)
