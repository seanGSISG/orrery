extends RunTest
## Moving platforms, through the boundary: a marble that rests on the deck keeps up with it,
## stays on through each stop, and rides up a lift without a launch at the top.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const PLATFORM: PackedScene = preload("res://objects/moving_platform/moving_platform.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## Half the default deck, less the marble radius: the marble centre stays this close to the
## deck centre while it is on the deck, m.
const ON_DECK: float = 1.8


## Returns a platform whose deck top starts at path[0] and stops at each later point.
func _platform(path: Array[Vector3], period: float, stop: float, loop: bool) -> MovingPlatform:
	var platform: MovingPlatform = PLATFORM.instantiate() as MovingPlatform
	platform.position = path[0]
	platform.period = period
	platform.stop = stop
	platform.loop = loop
	for i: int in range(1, path.size()):
		var point: Marker3D = Marker3D.new()
		point.name = "p%02d" % i
		point.position = path[i] - path[0]
		platform.add_child(point)
	return platform


## Starts a run with platform and puts the marble still on its deck top at deck.
func _ride(platform: MovingPlatform, deck: Vector3) -> void:
	start_run(FLAT, [platform])
	run.marble.teleport(deck + Vector3.UP * TUNING.radius, Vector3.ZERO)


## Asserts that the marble rests on the deck whose top centre is at deck.
func _assert_on_deck(deck: Vector3) -> void:
	var offset: Vector3 = run.state.position - deck
	assert_almost_eq(offset.y, TUNING.radius, 0.02, "marble height above the deck")
	assert_lt(Vector2(offset.x, offset.z).length(), ON_DECK, "marble is over the deck")
	assert_true(run.state.on_ground)


func test_marble_keeps_up_with_a_carriage_and_stays_on_through_a_stop() -> void:
	var a: Vector3 = Vector3(0, 3, 0)
	var b: Vector3 = Vector3(12, 3, 0)
	# Cycle: wait 2 s at a, move 3 s, wait 2 s at b, move 3 s back.
	_ride(_platform([a, b], 10.0, 2.0, false), a)
	hold(rolling(Vector2.ZERO), 3.5)
	# Halfway, the deck is at the middle at its top speed: 12 m × π / (2 × 3 s).
	_assert_on_deck(a.lerp(b, 0.5))
	assert_almost_eq(run.state.velocity.x, 12.0 * PI / 6.0, 1.0)
	hold(rolling(Vector2.ZERO), 2.0)
	_assert_on_deck(b)
	hold(rolling(Vector2.ZERO), 1.4)
	_assert_on_deck(b)
	assert_lt(run.state.velocity.length(), 0.3, "the marble rests at the stop")


func test_lift_carries_the_marble_up_without_a_launch() -> void:
	var low: Vector3 = Vector3(0, 1, 0)
	var high: Vector3 = Vector3(0, 11, 0)
	# Cycle: wait 1 s, rise 5 s, wait 1 s, sink 5 s.
	_ride(_platform([low, high], 12.0, 1.0, false), low)
	hold(rolling(Vector2.ZERO), 6.0)
	_assert_on_deck(high)
	var top: float = run.state.position.y
	for _i: int in roundi(1.0 * Engine.physics_ticks_per_second):
		run.step(rolling(Vector2.ZERO))
		top = maxf(top, run.state.position.y)
	assert_almost_eq(top, high.y + TUNING.radius, 0.02, "no hop at the top stop")
	hold(rolling(Vector2.ZERO), 5.0)
	_assert_on_deck(low)


func test_loop_goes_on_from_the_last_point_to_the_first() -> void:
	var path: Array[Vector3] = [Vector3(0, 3, 0), Vector3(10, 3, 0), Vector3(10, 3, -10)]
	# 3 stops of 1 s and 7 s of moves over 34.1 m: 2.05 s, 2.05 s and 2.90 s.
	_ride(_platform(path, 10.0, 1.0, true), path[0])
	hold(rolling(Vector2.ZERO), 1.0 + 2.05 + 1.0 + 2.05 + 0.5)
	_assert_on_deck(path[2])
	hold(rolling(Vector2.ZERO), 0.5 + 2.9 + 0.5)
	_assert_on_deck(path[0])


func test_offset_and_restart_set_the_start_of_the_cycle() -> void:
	var a: Vector3 = Vector3(0, 3, 0)
	var b: Vector3 = Vector3(12, 3, 0)
	var platform: MovingPlatform = _platform([a, b], 10.0, 2.0, false)
	platform.offset = 5.0
	_ride(platform, b)
	hold(rolling(Vector2.ZERO), 1.0)
	_assert_on_deck(b)
	hold(rolling(Vector2.ZERO), 3.0)
	run.restart()
	run.marble.teleport(b + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 0.5)
	_assert_on_deck(b)


func test_finish_gives_the_deck_a_kit_material() -> void:
	var platform: MovingPlatform = PLATFORM.instantiate() as MovingPlatform
	platform.finish = "wood"
	add_child_autofree(platform)
	var look: MeshInstance3D = platform.get_node("Solid/Mesh") as MeshInstance3D
	var wood: Material = KitMaterials.find("wood")
	assert_not_null(wood, "the kit has a wood material")
	assert_eq(look.material_override, wood)
