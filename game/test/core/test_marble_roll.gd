extends RunTest
## Rolling feel through the boundary only: MarbleInput in, GameState out. Camera yaw 0 looks
## along -Z, so forward input rolls toward -Z.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")


func before_each() -> void:
	start_run(FLAT)


## From rest, input reaches top speed in max_roll_speed / (angular_acceleration × radius).
func test_reaches_top_speed_in_expected_time() -> void:
	var expected: float = TUNING.max_roll_speed / (TUNING.angular_acceleration * TUNING.radius)
	hold(rolling(Vector2(0, 1)), expected * 0.5)
	assert_almost_eq(run.state.velocity.length(), TUNING.max_roll_speed * 0.5, 0.5)
	hold(rolling(Vector2(0, 1)), expected * 0.6)
	assert_almost_eq(run.state.velocity.length(), TUNING.max_roll_speed, 0.1)
	assert_true(run.state.on_ground)


## With no input, braking stops a marble at top speed in
## max_roll_speed / (braking_acceleration × radius).
func test_brakes_to_rest_without_input() -> void:
	run.marble.teleport(Vector3(0, TUNING.radius, 0), Vector3(0, 0, -TUNING.max_roll_speed))
	var stop: float = TUNING.max_roll_speed / (TUNING.braking_acceleration * TUNING.radius)
	hold(MarbleInput.new(), stop * 0.5)
	assert_almost_eq(run.state.velocity.length(), TUNING.max_roll_speed * 0.5, 0.5)
	hold(MarbleInput.new(), stop * 0.5 + 0.1)
	assert_almost_eq(run.state.velocity.length(), 0.0, 0.05)
	assert_almost_eq(run.state.spin.length(), 0.0, 0.05)


## A marble above top speed keeps its speed under input along its motion, also diagonal input.
func test_input_never_lowers_speed() -> void:
	for move: Vector2 in [Vector2(0, 1), Vector2(1, 1).normalized()]:
		run.marble.teleport(Vector3(0, TUNING.radius, 0), Vector3(0, 0, -25))
		hold(rolling(move), 0.5)
		assert_gte(run.state.velocity.length(), 24.99, str(move))


## Forward input rolls away from the camera: at yaw 90° (camera turned left) it rolls to -X.
func test_rolls_relative_to_camera() -> void:
	var input: MarbleInput = rolling(Vector2(0, 1))
	input.camera_yaw = PI / 2
	hold(input, 0.5)
	assert_almost_eq(run.state.velocity.normalized(), Vector3.LEFT, Vector3.ONE * 0.001)
