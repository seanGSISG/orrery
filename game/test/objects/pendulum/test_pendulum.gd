extends RunTest
## Pendulums, through the boundary: the bob swings across the floor on its period and knocks a
## marble in its way aside, in the direction that it swings. Each hit emits pendulum.hit.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const PENDULUM: PackedScene = preload("res://objects/pendulum/pendulum.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")


## Starts a run with one pendulum whose bob passes 5 cm above the floor at the origin, and
## watches the run's feedback.
func _start(offset: float) -> void:
	var pendulum: Pendulum = PENDULUM.instantiate() as Pendulum
	pendulum.offset = offset
	pendulum.position = Vector3(0, pendulum.length + pendulum.radius + 0.05, 0)
	start_run(FLAT, [pendulum])
	watch_signals(run)


## Returns the strength of each feedback of kind that the run emitted, in order.
func _strengths(kind: StringName) -> Array[float]:
	var out: Array[float] = []
	for i: int in get_signal_emit_count(run, "feedback"):
		var args: Array = get_signal_parameters(run, "feedback", i)
		if args[0] == kind:
			out.append(args[1])
	return out


## Steps for seconds with no input and returns the fastest marble velocity along x, signed.
func _fastest_x(seconds: float) -> float:
	var fastest: float = 0.0
	for _i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(rolling(Vector2.ZERO))
		if absf(run.state.velocity.x) > absf(fastest):
			fastest = run.state.velocity.x
	return fastest


func test_bob_knocks_the_marble_aside_as_it_swings_to_plus_x() -> void:
	_start(0.0)
	run.marble.teleport(Vector3(1.0, TUNING.radius, 0), Vector3.ZERO)
	var fastest: float = _fastest_x(0.4)
	assert_gt(fastest, 4.0, "knocked along +x")
	assert_almost_eq(run.state.position.z, 0.0, 0.1, "along the swing, not across it")
	var hits: Array[float] = _strengths(&"pendulum.hit")
	assert_eq(hits.size(), 1, "one knock, one pendulum.hit")
	if hits.size() == 1:
		assert_between(hits[0], 0.1, 1.0)


func test_bob_swings_back_on_its_period() -> void:
	_start(0.0)
	run.marble.teleport(Vector3(-1.0, TUNING.radius, 0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 1.8)
	assert_almost_eq(run.state.velocity.length(), 0.0, 0.01, "the first half swing misses it")
	assert_lt(_fastest_x(0.6), -4.0, "at 2 s the bob comes back along -x and knocks it")
	assert_eq(_strengths(&"pendulum.hit").size(), 1)


func test_offset_shifts_the_swing() -> void:
	_start(2.0)
	run.marble.teleport(Vector3(-1.0, TUNING.radius, 0), Vector3.ZERO)
	assert_lt(_fastest_x(0.4), -4.0, "half a period on, the bob starts along -x")
