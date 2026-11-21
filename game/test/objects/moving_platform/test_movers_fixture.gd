extends RunTest
## The mover fixture levels/test/movers.py, built by `just build-levels`: kit.marker places a
## moving platform and a turning gear, the importer writes their settings, and both carry the
## marble in the built level.

const FIXTURE: String = "res://levels/built/movers.glb"
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The fixture's markers, Blender (0, 10, 0), (0, 22, 0) and (0, 26.1, 0), in Godot axes.
const DECK_FROM: Vector3 = Vector3(0, 0, -10)
const DECK_TO: Vector3 = Vector3(0, 0, -22)
const GEAR_AT: Vector3 = Vector3(0, 0, -26.1)


## Starts a run of the built fixture. Returns false (and fails the test) when it is not built.
func _start_fixture() -> bool:
	if not ResourceLoader.exists(FIXTURE):
		fail_test("%s is missing: run `just build-levels`" % FIXTURE)
		return false
	start_run(load(FIXTURE) as PackedScene)
	return true


## Returns the first object of the run that has the script class type.
func _find(type: Script) -> LevelObject:
	for object: LevelObject in run.objects:
		if object.get_script() == type:
			return object
	return null


func test_fixture_platform_has_its_marker_settings_and_carries_the_marble() -> void:
	if not _start_fixture():
		return
	var platform: MovingPlatform = _find(MovingPlatform) as MovingPlatform
	assert_not_null(platform)
	if platform == null:
		return
	assert_almost_eq(platform.period, 8.0, 0.001)
	assert_almost_eq(platform.stop, 1.5, 0.001)
	assert_almost_eq(platform.global_position, DECK_FROM, Vector3.ONE * 0.001)
	run.marble.teleport(DECK_FROM + Vector3.UP * TUNING.radius, Vector3.ZERO)
	# Wait 1.5 s, then move 2.5 s, then wait at the far point.
	hold(rolling(Vector2.ZERO), 4.5)
	assert_almost_eq(run.state.position, DECK_TO + Vector3.UP * TUNING.radius, Vector3.ONE * 0.2)
	assert_true(run.state.on_ground)


func test_fixture_gear_has_its_marker_settings_and_carries_the_marble() -> void:
	if not _start_fixture():
		return
	var gear: TurningGear = _find(TurningGear) as TurningGear
	assert_not_null(gear)
	if gear == null:
		return
	assert_eq(gear.teeth, 12)
	assert_almost_eq(gear.global_position, GEAR_AT, Vector3.ONE * 0.001)
	run.marble.teleport(GEAR_AT + Vector3(1.2, TUNING.radius, 0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 2.0)
	# A quarter turn counter-clockwise from above takes +x to -z.
	var expected: Vector3 = GEAR_AT + Vector3(0, TUNING.radius, -1.2)
	assert_almost_eq(run.state.position, expected, Vector3.ONE * 0.3)
