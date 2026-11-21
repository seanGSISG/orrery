extends RunTest
## Steam vents, through the boundary: a marble on the grate rises to the top of the column and
## hovers there, a marble that drifts across the column still reaches the lift height and comes
## down beyond it, and entry emits steam_vent.blow once.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const VENT: PackedScene = preload("res://objects/steam_vent/steam_vent.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## Height that the test vent lifts the marble, m.
const LIFT: float = 6.0


## Starts a run with one vent on the floor at the origin and watches the run's feedback.
func _start() -> void:
	var vent: SteamVent = VENT.instantiate() as SteamVent
	vent.lift = LIFT
	start_run(FLAT, [vent])
	watch_signals(run)


## Returns the strength of each feedback of kind that the run emitted, in order.
func _strengths(kind: StringName) -> Array[float]:
	var out: Array[float] = []
	for i: int in get_signal_emit_count(run, "feedback"):
		var args: Array = get_signal_parameters(run, "feedback", i)
		if args[0] == kind:
			out.append(args[1])
	return out


## Steps for seconds with no input and returns the highest marble centre, m.
func _highest(seconds: float) -> float:
	var top: float = -INF
	for _i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(rolling(Vector2.ZERO))
		top = maxf(top, run.state.position.y)
	return top


func test_marble_on_the_grate_rises_to_the_lift_height_and_hovers() -> void:
	_start()
	run.marble.teleport(Vector3(0, TUNING.radius, 0), Vector3.ZERO)
	# From rest: full speed after 2 m, then a coast to 6 m, 0.95 s in all.
	assert_gt(_highest(1.0), LIFT - 0.3, "near the top after 1 s")
	assert_lt(_highest(2.0), LIFT + TUNING.radius + 0.1, "no higher than the column")
	assert_almost_eq(run.state.position.y, LIFT, 0.4, "it hovers at the top")
	var blows: Array[float] = _strengths(&"steam_vent.blow")
	assert_eq(blows.size(), 1, "one entry, one steam_vent.blow")
	if blows.size() == 1:
		# The marble centre is one radius above the grate, so it needs a little less.
		assert_almost_eq(blows[0], sqrt((LIFT - TUNING.radius) / LIFT), 0.01)


func test_marble_that_drifts_across_reaches_the_lift_height_and_comes_down_beyond() -> void:
	_start()
	run.marble.teleport(Vector3(-1.4, TUNING.radius, 0), Vector3(3.5, 0, 0))
	assert_almost_eq(_highest(1.2), LIFT, 0.5, "the drift does not cost the lift")
	hold(rolling(Vector2.ZERO), 1.5)
	assert_gt(run.state.position.x, 3.0, "it left the column on an arc")
	assert_lt(run.state.position.y, 2.0, "and came down")
	assert_eq(_strengths(&"steam_vent.blow").size(), 1)


func test_marble_beside_the_column_feels_nothing() -> void:
	_start()
	run.marble.teleport(Vector3(2.0, TUNING.radius, 0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 0.5)
	assert_almost_eq(run.state.position.y, TUNING.radius, 0.01)
	assert_eq(_strengths(&"steam_vent.blow").size(), 0)
