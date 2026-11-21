extends RunTest
## The level rules through the boundary: MarbleInput and LevelRun.teleport() in (the harness
## `teleport` command uses the same call), GameState and the run's feedback out. One test per
## rule, on test/levels/rules.tscn.

const RULES: PackedScene = preload("res://test/levels/rules.tscn")
const GEM: PackedScene = preload("res://objects/gem/gem.tscn")
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


## The gems are counted, and each gem counts once and hides.
func test_gems_are_counted_and_collected_once() -> void:
	start(RULES)
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
	start(RULES)
	visit(GEM_WEST)
	visit(FINISH)
	assert_eq(run.state.status, &"playing")
	visit(GEM_EAST)
	visit(FINISH)
	assert_eq(run.state.status, &"finished")
	assert_eq(heard.count(&"finish.open"), 1)
	assert_eq(heard.count(&"finish.reach"), 1, "in the tick that finishes the run")
	run.step(MarbleInput.new())
	assert_eq(heard.count(&"finish.reach"), 1, "once")


## The last gem and the finish in one tick finish the run in that tick, whatever the order
## of their hooks. The finish sounds its reach, and no open chime after it.
func test_last_gem_on_the_finish_finishes_at_once() -> void:
	var gem: Gem = GEM.instantiate() as Gem
	gem.position = FINISH + Vector3(0.6, 0, 0)
	start(RULES, [gem])
	visit(GEM_WEST)
	visit(GEM_EAST)
	visit(FINISH + Vector3(0.3, 0, 0))
	assert_eq(run.state.gems_collected, 3)
	assert_eq(run.state.status, &"finished")
	assert_eq(heard.count(&"finish.reach"), 1)
	run.step(MarbleInput.new())
	assert_false(heard.has(&"finish.open"))


## The clock counts the tick that finishes the run.
func test_finish_on_the_first_input_tick_counts_that_tick() -> void:
	start(RULES)
	visit(GEM_WEST)
	visit(GEM_EAST)
	run.teleport(FINISH + Vector3.UP * TUNING.radius, Vector3.ZERO)
	run.step(rolling(Vector2(0, 1)))
	assert_eq(run.state.status, &"finished")
	assert_almost_eq(run.state.timer, 1.0 / Engine.physics_ticks_per_second, 0.0001)


## Gems and the egg do not count while respawning or after the finish.
func test_pickups_count_only_while_playing() -> void:
	start(RULES)
	run.teleport(VOID + Vector3.UP * TUNING.radius, Vector3.ZERO)
	for _i: int in Engine.physics_ticks_per_second * 2:
		if run.state.status == &"respawning":
			break
		run.step(MarbleInput.new())
	assert_eq(run.state.status, &"respawning")
	visit(GEM_WEST)
	assert_eq(run.state.gems_collected, 0)
	hold(MarbleInput.new(), 1.0)
	visit(GEM_WEST)
	visit(GEM_EAST)
	visit(FINISH)
	visit(EGG)
	assert_eq(run.state.status, &"finished")
	assert_false(run.state.egg_found)
	assert_eq(heard.count(&"egg.open"), 0)


## The clock waits for the first move, jump or use input, then runs with or without input.
func test_clock_starts_at_first_input() -> void:
	start(RULES)
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
	start(RULES)
	finish_after(2.0)
	var at_finish: float = run.state.timer
	hold(MarbleInput.new(), 1.0)
	assert_eq(run.state.timer, at_finish)


## The medal is gold at or under the gold time, qualified at or under par, else none.
func test_medal_follows_par_and_gold() -> void:
	start(RULES)
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
	start(RULES)
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
	start(RULES)
	visit(GEM_WEST)
	visit(EGG)
	visit(CHECKPOINT)
	assert_eq(run.state.checkpoint, &"Checkpoint")
	assert_eq(heard.count(&"checkpoint.reach"), 1)
	assert_true(run.slot.take(CoilSpringPowerUp.new(20.0)))
	run.teleport(VOID + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(MarbleInput.new(), 2.0)
	assert_almost_eq(run.state.position, CHECKPOINT + Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
	assert_eq(run.state.status, &"playing")
	assert_eq(run.state.gems_collected, 1)
	assert_true(run.state.egg_found)
	assert_eq(run.state.power_up, &"coil_spring")
	visit(GEM_WEST)
	assert_eq(run.state.gems_collected, 1)


## A restart starts a fresh attempt at once: no time, gems, checkpoint, egg or power-up, and
## the marble still on the start pad.
func test_restart_starts_fresh_at_once() -> void:
	start(RULES)
	run.step(rolling(Vector2(0, 1)))
	visit(GEM_WEST)
	visit(EGG)
	visit(CHECKPOINT)
	assert_true(run.slot.take(CoilSpringPowerUp.new(20.0)))
	run.restart()
	assert_eq(run.state.tick, 0)
	assert_eq(run.state.timer, 0.0)
	assert_eq(run.state.gems_collected, 0)
	assert_eq(run.state.checkpoint, &"")
	assert_false(run.state.egg_found)
	assert_eq(run.state.status, &"playing")
	assert_eq(run.state.power_up, &"")
	assert_almost_eq(run.state.position, Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
	visit(GEM_WEST)
	assert_eq(run.state.gems_collected, 1)


## The egg opens once per run.
func test_egg_is_found_once() -> void:
	start(RULES)
	visit(EGG)
	assert_true(run.state.egg_found)
	visit(Vector3.ZERO)
	visit(EGG)
	assert_eq(heard.count(&"egg.open"), 1)


## The kill height is KILL_DEPTH under the lowest Solid, also below the world origin.
func test_kill_height_follows_the_lowest_solid() -> void:
	var pit: Solid = Solid.new()
	pit.position = Vector3(0, -20, 0)
	var shape: CollisionShape3D = CollisionShape3D.new()
	shape.shape = BoxShape3D.new()
	pit.add_child(shape)
	start(RULES, [pit])
	assert_almost_eq(run.rules.kill_height, -20.5 - Rules.KILL_DEPTH, 0.001)


## LevelRun.teleport() shows the new place in the state before the next tick.
func test_teleport_writes_state_at_once() -> void:
	start(RULES)
	run.teleport(Vector3(3, 1, 2), Vector3(1, 0, 0))
	assert_eq(run.state.position, Vector3(3, 1, 2))
	assert_eq(run.state.velocity, Vector3(1, 0, 0))


## Starts a run of level with the extra nodes and records its feedback in heard.
func start(level: PackedScene, extra: Array[Node3D] = []) -> void:
	start_run(level, extra)
	run.feedback.connect(_hear)


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
