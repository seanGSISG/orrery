extends RunTest
## Full marble physics through the boundary only: MarbleInput in, GameState out. Jumps,
## bounces, slides, air control, surfaces, the sweep, gravity fields and movers. The marble
## rests SKIN (0.1 mm) above a surface, so position checks use tolerances.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const PHYSICS: PackedScene = preload("res://test/levels/physics.tscn")
const FIELD: PackedScene = preload("res://core/gravity/uniform_gravity.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")

# The layout of physics.tscn. Its floor top is at y = 0.
## Front face of Wall, normal +Z, from y = 0 to 20.
const WALL_Z: float = -20.0
## Centre and normal of the 30° ramp's top face.
const RAMP_TOP: Vector3 = Vector3(12, 2, 10)
const RAMP_NORMAL: Vector3 = Vector3(-0.5, 0.8660254, 0)
## Centre of the ice top face, and the friction of its Surface.
const ICE: Vector3 = Vector3(30, 0, 0)
const ICE_FRICTION: float = 0.1
## Centre of SideGravity, a 10 m cube field with up = +X and the default strength.
const ISLAND: Vector3 = Vector3(0, 5, 40)
const SIDE_GRAVITY: float = 20.0
## Face of IslandWall, normal +X: the floor under SideGravity.
const ISLAND_WALL_X: float = -5.0

## Kinds of the run's feedback in this test, in order.
var heard: Array[StringName] = []


func before_each() -> void:
	heard.clear()


## A jump from rest rises jump_impulse² / (2 × gravity) above the rest height.
func test_jump_reaches_expected_apex() -> void:
	_start(FLAT)
	hold(MarbleInput.new(), 0.1)
	var rest: float = run.state.position.y
	run.step(_jumping())
	assert_almost_eq(run.state.velocity, Vector3.UP * TUNING.jump_impulse, Vector3.ONE * 0.01)
	var expected: float = TUNING.jump_impulse ** 2.0 / (2.0 * TUNING.gravity)
	assert_almost_eq(_apex() - rest, expected, 0.05)
	assert_eq(heard, [&"marble.jump"] as Array[StringName])


## A held jump jumps again at the next landing, and only once in each flight.
func test_held_jump_repeats_on_landing() -> void:
	_start(FLAT)
	var flight: float = 2.0 * TUNING.jump_impulse / TUNING.gravity
	hold(_jumping(), flight * 1.6)
	assert_eq(heard.count(&"marble.jump"), 2)


## Jumps do not add speed along the ground: a glancing landing slides and loses only its
## speed into the floor. Held jump and forward at top speed stay at top speed.
func test_hopping_does_not_gain_speed() -> void:
	_start(FLAT)
	run.marble.teleport(Vector3(0, TUNING.radius, 30), Vector3(0, 0, -TUNING.max_roll_speed))
	var input: MarbleInput = _jumping()
	input.move = Vector2(0, 1)
	hold(input, 3.0)
	var along: Vector3 = Vector3(run.state.velocity.x, 0, run.state.velocity.z)
	assert_lt(along.length(), TUNING.max_roll_speed + 0.5)


## The jump goes along the contact normal, also on a slope.
func test_jump_follows_contact_normal() -> void:
	_start(PHYSICS)
	run.marble.teleport(RAMP_TOP + RAMP_NORMAL * TUNING.radius, Vector3.ZERO)
	run.step(_jumping())
	assert_almost_eq(run.state.velocity.normalized(), RAMP_NORMAL, Vector3.ONE * 0.02)
	assert_almost_eq(run.state.velocity.length(), TUNING.jump_impulse, 0.1)


## A marble dropped onto the floor bounces to restitution² times the drop height. The hit
## ends a flight, so it is a landing.
func test_bounces_by_restitution() -> void:
	_start(FLAT)
	var drop: float = 2.0
	run.marble.teleport(Vector3(0, TUNING.radius + drop, 0), Vector3.ZERO)
	for _i: int in 200:
		run.step(MarbleInput.new())
		if run.state.velocity.y > 0.0:
			break
	var height: float = _apex() - TUNING.radius
	assert_almost_eq(height, TUNING.restitution ** 2.0 * drop, 0.05)
	assert_eq(heard, [&"marble.land"] as Array[StringName])


## A slow fall that starts inside the contact margin still ends in marble.land, not a bounce.
func test_landing_from_inside_margin_is_a_landing() -> void:
	_start(FLAT)
	run.marble.teleport(Vector3(0, TUNING.radius + TUNING.contact_margin * 0.8, 0), Vector3.ZERO)
	hold(MarbleInput.new(), 0.2)
	assert_gt(heard.size(), 0)
	if not heard.is_empty():
		assert_eq(heard[0], &"marble.land")


## A drop into a 90° V hits both slopes at once, and lands once.
func test_one_landing_per_flight() -> void:
	var bottom: Vector3 = Vector3(0, 2, 20)
	_start(FLAT, [_slab(PI / 4, bottom), _slab(-PI / 4, bottom)])
	run.marble.teleport(bottom + Vector3.UP * (TUNING.radius * sqrt(2.0) + 1.0), Vector3.ZERO)
	for _i: int in 120:
		run.step(MarbleInput.new())
		if not heard.is_empty():
			break
	assert_eq(heard.count(&"marble.land"), 1)


## A fast fall gains exactly gravity × time, also when the sub-steps are short.
func test_fast_fall_gains_gravity_times_time() -> void:
	_start(FLAT)
	run.marble.teleport(Vector3(0, 100, 0), Vector3(0, -30, 0))
	hold(MarbleInput.new(), 0.5)
	assert_almost_eq(run.state.velocity.y, -30.0 - TUNING.gravity * 0.5, 0.002)


## Below min_bounce_speed a hit stops the marble; above it the marble bounces back.
func test_bounces_only_above_min_bounce_speed() -> void:
	_start(PHYSICS)
	var at: Vector3 = Vector3(0, 10, WALL_Z + TUNING.radius)
	var slow: float = TUNING.min_bounce_speed * 0.5
	run.marble.teleport(at, Vector3(0, 0, -slow))
	run.step(MarbleInput.new())
	assert_almost_eq(run.state.velocity.z, 0.0, 0.001)
	var fast: float = TUNING.min_bounce_speed * 2.0
	run.marble.teleport(at, Vector3(0, 0, -fast))
	run.step(MarbleInput.new())
	assert_almost_eq(run.state.velocity.z, fast * TUNING.restitution, 0.001)


## A glancing hit slides along the wall and keeps its speed along it; a steep hit bounces.
func test_glancing_hit_slides() -> void:
	_start(PHYSICS)
	var at: Vector3 = Vector3(0, 10, WALL_Z + TUNING.radius)
	var limit: float = asin(TUNING.slide_threshold)
	var glancing: Vector3 = _toward_wall(limit * 0.6, 10.0)
	run.marble.teleport(at, glancing)
	run.step(MarbleInput.new())
	assert_almost_eq(run.state.velocity.x, glancing.x, 0.01)
	assert_almost_eq(run.state.velocity.z, 0.0, 0.01)
	var steep: Vector3 = _toward_wall(limit * 1.5, 10.0)
	run.marble.teleport(at, steep)
	run.step(MarbleInput.new())
	assert_almost_eq(run.state.velocity.z, -steep.z * TUNING.restitution, 0.01)


## Only a floor (floor_min_up) is ground. on_ground is true on the floor and on the 30° ramp,
## and false in the air against a wall. In a hit on a wall, the floor stays the ground: a jump
## goes up, not off the wall.
func test_only_a_floor_is_ground() -> void:
	_start(PHYSICS)
	var cases: Dictionary[String, Vector3] = {
		"floor": Vector3(0, TUNING.radius, 0),
		"ramp": RAMP_TOP + RAMP_NORMAL * TUNING.radius,
	}
	for case: String in cases:
		run.marble.teleport(cases[case], Vector3.ZERO)
		hold(MarbleInput.new(), 0.1)
		assert_true(run.state.on_ground, case)
	run.marble.teleport(Vector3(0, 10, WALL_Z + TUNING.radius), Vector3.ZERO)
	for _i: int in 30:
		run.step(rolling(Vector2(0, 1)))
		assert_false(run.state.on_ground, "in the air against the wall")
	assert_lt(run.state.position.z, WALL_Z + TUNING.radius + 0.01, "the marble stays on the wall")
	var at: Vector3 = Vector3(0, TUNING.radius, WALL_Z + TUNING.radius)
	run.marble.teleport(at, _toward_wall(asin(TUNING.slide_threshold) * 0.6, 10.0))
	run.step(_jumping())
	assert_almost_eq(run.state.velocity.y, TUNING.jump_impulse, 0.05)
	assert_lt(absf(run.state.velocity.z), 0.2)


## Input partly into a surface never stalls the move along it: the marble moves as far as its
## speed carries it along a wall on the floor, along a wall in the air (air control), and
## along the seam of a 60° V.
func test_input_into_surfaces_does_not_stall_the_move() -> void:
	var seam: Vector3 = Vector3(0, 2, 5)
	_start(PHYSICS, [_slab(PI / 3, seam), _slab(-PI / 3, seam)])
	var into: MarbleInput = rolling(Vector2(1, 1).normalized())
	var cases: Dictionary[String, Vector3] = {
		"floor and wall": Vector3(-10, TUNING.radius, WALL_Z + TUNING.radius),
		"wall in the air": Vector3(-10, 10, WALL_Z + TUNING.radius),
	}
	for case: String in cases:
		run.marble.teleport(cases[case], Vector3(10, 0, 0))
		_assert_moves_at_speed(into, 0.5, case)
	run.marble.teleport(seam + Vector3(0, TUNING.radius / cos(PI / 3), 8), Vector3(0, 0, -10))
	_assert_moves_at_speed(into, 0.5, "60° V seam")


## In the air, input changes the velocity at air_acceleration and leaves the spin alone.
func test_air_control_steers_in_flight() -> void:
	_start(FLAT)
	run.marble.teleport(Vector3(0, 10, 0), Vector3.ZERO)
	hold(rolling(Vector2(1, 0)), 0.5)
	assert_almost_eq(run.state.velocity.x, TUNING.air_acceleration * 0.5, 0.01)
	assert_almost_eq(run.state.spin, Vector3.ZERO, Vector3.ONE * 0.001)


## A low-friction surface slips: input gains speed only at kinetic friction × the surface
## friction × gravity.
func test_surface_scales_friction() -> void:
	_start(PHYSICS)
	run.marble.teleport(ICE + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(rolling(Vector2(0, 1)), 0.5)
	var expected: float = TUNING.kinetic_friction * ICE_FRICTION * TUNING.gravity * 0.5
	assert_almost_eq(run.state.velocity.length(), expected, 0.05)
	assert_gt(run.state.spin.length() * TUNING.radius, run.state.velocity.length() * 5.0)


## A marble at 500 m/s stops on a thin one-sided floor and never passes below it.
func test_fast_marble_never_passes_thin_floor() -> void:
	_start(FLAT)
	run.marble.teleport(Vector3(0, 3, 0), Vector3(0, -500, 0))
	for _i: int in 10:
		run.step(MarbleInput.new())
		assert_gt(run.state.position.y, TUNING.radius - 0.001)


## In a gravity field the marble falls along the field and up turns to match. Outside every
## field, gravity is straight down again.
func test_gravity_field_sets_gravity_and_up() -> void:
	_start(PHYSICS)
	run.marble.teleport(ISLAND + Vector3(2, 0, 0), Vector3.ZERO)
	hold(MarbleInput.new(), 0.25)
	assert_almost_eq(run.state.up, Vector3.RIGHT, Vector3.ONE * 0.001)
	assert_almost_eq(run.state.velocity, Vector3.LEFT * SIDE_GRAVITY * 0.25, Vector3.ONE * 0.01)
	run.marble.teleport(Vector3(0, 5, 0), Vector3.ZERO)
	run.step(MarbleInput.new())
	assert_almost_eq(run.state.up, Vector3.UP, Vector3.ONE * 0.001)


## In a gravity field, the jump goes along the field's up.
func test_jump_uses_field_up() -> void:
	_start(PHYSICS)
	run.marble.teleport(Vector3(ISLAND_WALL_X + TUNING.radius, ISLAND.y, ISLAND.z), Vector3.ZERO)
	hold(MarbleInput.new(), 0.1)
	run.step(_jumping())
	assert_almost_eq(run.state.velocity, Vector3.RIGHT * TUNING.jump_impulse, Vector3.ONE * 0.05)


## Where two fields overlap, the one with the higher priority sets the gravity.
func test_highest_priority_field_wins() -> void:
	var field: UniformGravity = FIELD.instantiate() as UniformGravity
	field.priority = 1
	field.strength = 5.0
	field.transform = Transform3D(Basis(Vector3.RIGHT, PI / 2).scaled(Vector3.ONE * 4), ISLAND)
	_start(PHYSICS, [field])
	run.marble.teleport(ISLAND, Vector3.ZERO)
	hold(MarbleInput.new(), 0.2)
	assert_almost_eq(run.state.up, Vector3.BACK, Vector3.ONE * 0.001)
	assert_almost_eq(run.state.velocity, Vector3.FORWARD * 5.0 * 0.2, Vector3.ONE * 0.01)


## A mover that passes over the marble centre in one tick pushes the marble out ahead of it,
## not deeper inside.
func test_mover_over_centre_pushes_marble_out() -> void:
	var pusher: TestPusher = TestPusher.new()
	pusher.from = Vector3(-1.05, 0.5, 0)
	pusher.speed = 36.0
	_start(FLAT, [pusher])
	var ticks: int = 3
	for _i: int in ticks:
		run.step(MarbleInput.new())
	var face: float = pusher.from.x + 0.5 + pusher.speed * ticks / Engine.physics_ticks_per_second
	assert_gt(face, 0.0)
	assert_gt(run.state.position.x, face + TUNING.radius - 0.01)
	assert_gt(run.state.velocity.x, pusher.speed)


## Starts a run of level and records the kind of each feedback in heard.
func _start(level: PackedScene, extra: Array[Node3D] = []) -> void:
	start_run(level, extra)
	run.feedback.connect(_hear)


func _hear(kind: StringName, _strength: float, _at: Vector3) -> void:
	heard.append(kind)


## Returns a MarbleInput that holds jump.
func _jumping() -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.jump = true
	return input


## Steps with no input while the marble rises, and returns the highest centre height.
func _apex() -> float:
	var top: float = run.state.position.y
	for _i: int in 400:
		if run.state.velocity.y <= 0.0:
			break
		run.step(MarbleInput.new())
		top = maxf(top, run.state.position.y)
	return top


## Steps with input for `seconds` after one settling tick, and asserts that the marble moved as
## far as its speed carried it: a stalled sweep moves it less.
func _assert_moves_at_speed(input: MarbleInput, seconds: float, case: String) -> void:
	run.step(input)
	var rate: float = Engine.physics_ticks_per_second
	var moved: float = 0.0
	var carried: float = 0.0
	for _i: int in roundi(seconds * rate):
		var before: Vector3 = run.state.position
		var speed: float = run.state.velocity.length()
		run.step(input)
		moved += (run.state.position - before).length()
		carried += (speed + run.state.velocity.length()) * 0.5 / rate
	assert_gt(carried, 2.0, case)
	assert_almost_eq(moved, carried, carried * 0.02, case)


## Returns a 4 m wide, 20 m long slab Solid turned by angle around +Z, whose top face ends at
## bottom: on the +X side for a positive angle.
func _slab(angle: float, bottom: Vector3) -> Solid:
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(4, 0.2, 20)
	var shape: CollisionShape3D = CollisionShape3D.new()
	shape.shape = box
	var solid: Solid = Solid.new()
	solid.add_child(shape)
	var turn: Basis = Basis(Vector3.BACK, angle)
	var side: float = signf(angle) * 2.0
	solid.transform = Transform3D(turn, bottom + turn.x * side - turn.y * 0.1)
	return solid


## Returns a velocity of speed toward Wall at angle radians from its face, along +X.
func _toward_wall(angle: float, speed: float) -> Vector3:
	return Vector3(cos(angle), 0, -sin(angle)) * speed
