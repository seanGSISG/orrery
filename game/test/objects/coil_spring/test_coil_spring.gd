extends RunTest
## The Coil Spring and the power-up slot through the boundary: LevelRun.teleport() and
## MarbleInput in, GameState and the run's feedback out. The springs stand on
## test/levels/rules.tscn, whose floor is at y = 0 from x = -20 to 20 and z = -30 to 10.

const RULES: PackedScene = preload("res://test/levels/rules.tscn")
const SPRING: PackedScene = preload("res://objects/coil_spring/coil_spring.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
const FIXTURE: String = "res://levels/built/spring.glb"

const WEST: Vector3 = Vector3(-6, 0, 5)
const EAST: Vector3 = Vector3(6, 0, 5)
## A free floor point away from every object.
const AWAY: Vector3 = Vector3(12, 0, 5)
const CHECKPOINT: Vector3 = Vector3(0, 0, -10)
## A point past the floor's east edge.
const VOID: Vector3 = Vector3(30, 0, 0)

## Kinds of the run's feedback in this test, in order.
var heard: Array[StringName] = []
var west: CoilSpring
var east: CoilSpring


func before_each() -> void:
	heard.clear()


## A pickup fills the empty slot, hides, and the state reports the held spring.
func test_pickup_fills_the_empty_slot() -> void:
	start()
	assert_eq(run.state.power_up, &"")
	visit(WEST)
	assert_eq(run.state.power_up, &"coil_spring")
	assert_false(west.visible)
	assert_eq(heard, [&"coil_spring.pickup"] as Array[StringName])


## While the slot is full, another pickup stays in place; after the use it can be taken.
func test_full_slot_leaves_other_pickups_in_place() -> void:
	start()
	visit(WEST)
	visit(EAST)
	assert_true(east.visible)
	assert_eq(heard.count(&"coil_spring.pickup"), 1)
	run.teleport(AWAY + Vector3.UP * TUNING.radius, Vector3.ZERO)
	run.step(using())
	assert_eq(run.state.power_up, &"")
	visit(EAST)
	assert_eq(run.state.power_up, &"coil_spring")
	assert_false(east.visible)


## The use launches the marble at 20 m/s along up, to about 10 m, and empties the slot.
func test_use_launches_about_ten_metres() -> void:
	start()
	visit(WEST)
	run.step(using())
	assert_eq(run.state.power_up, &"")
	assert_eq(heard.count(&"coil_spring.use"), 1)
	assert_gt(run.state.velocity.y, 19.0)
	assert_almost_eq(apex(), 10.0, 0.3)


## One press uses one power-up: a use held from before the pickup does nothing, and a press
## with an empty slot does nothing.
func test_one_press_uses_one_power_up() -> void:
	start()
	run.step(using())
	assert_eq(heard.count(&"coil_spring.use"), 0)
	run.teleport(WEST + Vector3.UP * TUNING.radius, Vector3.ZERO)
	run.step(using())
	run.step(using())
	assert_eq(run.state.power_up, &"coil_spring")
	run.step(MarbleInput.new())
	run.step(using())
	assert_eq(run.state.power_up, &"")
	assert_eq(heard.count(&"coil_spring.use"), 1)


## A checkpoint respawn keeps the held spring, and it still works.
func test_checkpoint_respawn_keeps_the_spring() -> void:
	start()
	visit(WEST)
	visit(CHECKPOINT)
	run.teleport(VOID + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(MarbleInput.new(), 2.0)
	assert_almost_eq(run.state.position, CHECKPOINT + Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
	assert_eq(run.state.power_up, &"coil_spring")
	run.step(using())
	assert_almost_eq(apex(), 10.0, 0.3)


## A restart empties the slot and puts the pickup back at once.
func test_restart_clears_the_slot_and_brings_back_the_pickup() -> void:
	start()
	visit(WEST)
	run.restart()
	assert_eq(run.state.power_up, &"")
	assert_true(west.visible)
	visit(WEST)
	assert_eq(run.state.power_up, &"coil_spring")


## A taken pickup comes back respawn_delay (5 s) after the pickup, not before.
func test_pickup_returns_after_the_delay() -> void:
	start()
	visit(WEST)
	var taken: int = run.state.tick
	run.step(using())
	run.teleport(AWAY + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold_until(taken + seconds(4.9))
	assert_false(west.visible)
	visit(WEST)
	assert_eq(run.state.power_up, &"")
	run.teleport(AWAY + Vector3.UP * TUNING.radius, Vector3.ZERO)
	# The float run time can put the return one tick past 5 s.
	hold_until(taken + seconds(5.0) + 1)
	assert_true(west.visible)
	visit(WEST)
	assert_eq(run.state.power_up, &"coil_spring")
	assert_eq(heard.count(&"coil_spring.pickup"), 2)


## The built fixture levels/test/spring.py: kit.marker places both springs with their
## settings, and the spring with launch_speed 18 rises 18² / (2 × 20) = 8.1 m.
func test_fixture_springs_have_their_marker_settings() -> void:
	if not ResourceLoader.exists(FIXTURE):
		fail_test("%s is missing: run `just build-levels`" % FIXTURE)
		return
	start_run(load(FIXTURE) as PackedScene)
	var springs: Array[CoilSpring] = []
	for object: LevelObject in run.objects:
		if object is CoilSpring:
			springs.append(object as CoilSpring)
	assert_eq(springs.size(), 2)
	if springs.size() != 2:
		return
	assert_almost_eq(springs[0].launch_speed, 20.0, 0.001)
	assert_almost_eq(springs[0].respawn_delay, 5.0, 0.001)
	assert_almost_eq(springs[1].launch_speed, 18.0, 0.001)
	assert_almost_eq(springs[1].respawn_delay, 3.0, 0.001)
	# Blender (1.5, 6, 0) in Godot axes.
	var at: Vector3 = Vector3(1.5, 0, -6)
	assert_almost_eq(springs[1].global_position, at, Vector3.ONE * 0.001)
	visit(at)
	run.step(using())
	assert_almost_eq(apex(), 8.1, 0.3)


## Starts a run of rules.tscn with a spring at WEST and at EAST, and records its feedback.
func start() -> void:
	west = SPRING.instantiate() as CoilSpring
	west.position = WEST
	east = SPRING.instantiate() as CoilSpring
	east.position = EAST
	start_run(RULES, [west, east])
	run.feedback.connect(_hear)


## Puts the marble still on the floor at point and steps one tick.
func visit(point: Vector3) -> void:
	run.teleport(point + Vector3.UP * TUNING.radius, Vector3.ZERO)
	run.step(MarbleInput.new())


## A MarbleInput that holds the use button.
func using() -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.use = true
	return input


## Steps with no input while the marble rises, and returns the top height of its lowest
## point above the floor at y = 0.
func apex() -> float:
	var top: float = run.state.position.y
	while run.state.velocity.y > 0.0:
		run.step(MarbleInput.new())
		top = maxf(top, run.state.position.y)
	return top - TUNING.radius


## Ticks in seconds of run time.
func seconds(time: float) -> int:
	return roundi(time * Engine.physics_ticks_per_second)


## Steps with no input until the state shows tick.
func hold_until(tick: int) -> void:
	while run.state.tick < tick:
		run.step(MarbleInput.new())


## Records the kind of each feedback.
func _hear(kind: StringName, _strength: float, _at: Vector3) -> void:
	heard.append(kind)
