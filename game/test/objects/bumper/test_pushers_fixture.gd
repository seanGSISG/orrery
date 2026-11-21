extends RunTest
## The pusher fixture levels/test/pushers.py, built by `just build-levels`: kit.marker places a
## bumper, a steam vent and a pendulum, the importer writes their settings, and each one pushes
## the marble in the built level.

const FIXTURE: String = "res://levels/built/pushers.glb"
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The fixture's markers, Blender (0, 8, 0), (0, 16, 0) and (0, 26, 4.65), in Godot axes.
const BUMPER_AT: Vector3 = Vector3(0, 0, -8)
const VENT_AT: Vector3 = Vector3(0, 0, -16)
const PIVOT_AT: Vector3 = Vector3(0, 4.65, -26)


## Starts a run of the built fixture and watches its feedback. Returns false (and fails the
## test) when the fixture is not built.
func _start_fixture() -> bool:
	if not ResourceLoader.exists(FIXTURE):
		fail_test("%s is missing: run `just build-levels`" % FIXTURE)
		return false
	start_run(load(FIXTURE) as PackedScene)
	watch_signals(run)
	return true


## Returns the first object of the run that has the script class type.
func _find(type: Script) -> LevelObject:
	for object: LevelObject in run.objects:
		if object.get_script() == type:
			return object
	return null


## Returns how many times the run emitted feedback of kind.
func _count(kind: StringName) -> int:
	var count: int = 0
	for i: int in get_signal_emit_count(run, "feedback"):
		if get_signal_parameters(run, "feedback", i)[0] == kind:
			count += 1
	return count


func test_fixture_bumper_has_its_marker_settings_and_pushes_the_marble() -> void:
	if not _start_fixture():
		return
	var bumper: Bumper = _find(Bumper) as Bumper
	assert_not_null(bumper)
	if bumper == null:
		return
	assert_almost_eq(bumper.speed, 15.0, 0.001)
	assert_almost_eq(bumper.radius, 0.5, 0.001)
	assert_almost_eq(bumper.height, 1.0, 0.001)
	assert_almost_eq(bumper.global_position, BUMPER_AT, Vector3.ONE * 0.001)
	run.marble.teleport(BUMPER_AT + Vector3(0, TUNING.radius, 1.5), Vector3(0, 0, -5))
	hold(rolling(Vector2.ZERO), 0.3)
	assert_almost_eq(run.state.velocity.z, 15.0, 1.0, "pushed back toward the start")
	assert_eq(_count(&"bumper.hit"), 1)


func test_fixture_vent_has_its_marker_settings_and_lifts_the_marble() -> void:
	if not _start_fixture():
		return
	var vent: SteamVent = _find(SteamVent) as SteamVent
	assert_not_null(vent)
	if vent == null:
		return
	assert_almost_eq(vent.lift, 6.0, 0.001)
	assert_almost_eq(vent.radius, 1.0, 0.001)
	assert_almost_eq(vent.push, 60.0, 0.001)
	assert_almost_eq(vent.global_position, VENT_AT, Vector3.ONE * 0.001)
	run.marble.teleport(VENT_AT + Vector3(0, TUNING.radius, 0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 1.5)
	assert_almost_eq(run.state.position.y, 6.0, 0.5, "it hovers at the top of the column")
	assert_eq(_count(&"steam_vent.blow"), 1)


func test_fixture_pendulum_has_its_marker_settings_and_knocks_the_marble_aside() -> void:
	if not _start_fixture():
		return
	var pendulum: Pendulum = _find(Pendulum) as Pendulum
	assert_not_null(pendulum)
	if pendulum == null:
		return
	assert_almost_eq(pendulum.period, 4.0, 0.001)
	assert_almost_eq(pendulum.swing, 60.0, 0.001)
	assert_almost_eq(pendulum.length, 4.0, 0.001)
	assert_almost_eq(pendulum.radius, 0.6, 0.001)
	assert_almost_eq(pendulum.global_position, PIVOT_AT, Vector3.ONE * 0.001)
	run.marble.teleport(PIVOT_AT + Vector3(1.0, TUNING.radius - 4.65, 0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 0.3)
	assert_gt(run.state.velocity.x, 3.0, "knocked across the track along +x")
	assert_eq(_count(&"pendulum.hit"), 1)
