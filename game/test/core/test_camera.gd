extends RunTest
## The follow camera and the blob shadow. The run steps with MarbleInput, and the camera then
## follows run.state each tick, as in the game. The up test gives the camera a GameState with
## a new up directly, so it does not need the gravity fields of #10.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const WALL: PackedScene = preload("res://test/levels/wall.tscn")
const DT: float = 1.0 / 120.0

var camera: FollowCamera
## A thin cast for the line of sight from the camera to the marble.
var sight: WorldQuery


func after_each() -> void:
	FollowCamera.shake_enabled = true


## Yaw turns the camera around the marble, the camera looks at the marble, and the pitch stays
## inside the PlayerSource limits.
func test_orbits_at_input_yaw_within_pitch_limits() -> void:
	_start(FLAT)
	var input: MarbleInput = _looking(PI / 2, -0.45)
	_play(input, 0.1)
	var offset: Vector3 = camera.global_position - run.state.position
	assert_almost_eq(offset.length(), camera.distance, 0.01)
	assert_almost_eq(offset.normalized(), Vector3(cos(0.45), sin(0.45), 0), Vector3.ONE * 0.01)
	assert_almost_eq(-camera.global_basis.z, -offset.normalized(), Vector3.ONE * 0.001)
	_play(_looking(0.0, -3.0), 0.1)
	offset = camera.global_position - run.state.position
	assert_almost_eq(asin(offset.normalized().y), -PlayerSource.PITCH_MIN, 0.01)


## The marble rolls past a wall that stands between it and the camera. The camera pulls in,
## so the marble is in the frame centre and in clear sight on every tick, and it moves out again
## after the wall.
func test_marble_stays_in_view_past_a_wall() -> void:
	_start(WALL)
	var input: MarbleInput = _looking(0.0, PlayerSource.START_PITCH)
	input.move = Vector2(1, 0)
	var hidden: Array[int] = [0]
	var closest: Array[float] = [INF]
	var check: Callable = func() -> void:
		var eye: Vector3 = camera.global_position
		var marble: Vector3 = run.state.position
		var centred: bool = (-camera.global_basis.z).angle_to(marble - eye) < 0.05
		if not centred or sight.sweep(eye, marble - eye) < 1.0:
			hidden[0] += 1
		closest[0] = minf(closest[0], eye.distance_to(marble))
	_play(input, 1.2, check)
	assert_gt(run.state.position.x, 7.0, "the marble rolled past the wall")
	assert_eq(hidden[0], 0, "ticks with the marble hidden")
	assert_lt(closest[0], 1.2, "the camera pulled in")
	_play(_looking(0.0, PlayerSource.START_PITCH), 1.5)
	assert_almost_eq(camera.global_position.distance_to(run.state.position), camera.distance, 0.05)


## With the marble against the wall and the camera on the wall side, the camera stays
## min_distance from the marble centre, outside the marble.
func test_camera_stays_outside_the_marble_at_a_wall() -> void:
	_start(WALL)
	run.marble.teleport(Vector3(4, 0.2, 0.8 - Marble.SKIN), Vector3.ZERO)
	_play(_looking(0.0, PlayerSource.START_PITCH), 0.2)
	var gap: float = camera.global_position.distance_to(run.state.position)
	assert_almost_eq(gap, camera.min_distance, 0.001)


## After a change of up, the camera's up turns to the new up over a short time, not at once,
## and the camera stays on the up side of the marble. Also for a full flip of up.
func test_up_follows_a_change_smoothly() -> void:
	var input: MarbleInput = _looking(0.0, PlayerSource.START_PITCH)
	for up: Vector3 in [Vector3.RIGHT, Vector3.DOWN]:
		camera = FollowCamera.new()
		add_child_autofree(camera)
		var state: GameState = GameState.new()
		state.position = Vector3(0, 5, 0)
		for _i: int in 120:
			camera.follow(state, input, DT)
		var start: Vector3 = _camera_up(input)
		state.up = up
		camera.follow(state, input, DT)
		assert_gt(_camera_up(input).angle_to(up), start.angle_to(up) * 0.9, "not at once")
		for _i: int in 120:
			camera.follow(state, input, DT)
		assert_lt(_camera_up(input).angle_to(up), 0.05, "turned to the new up")
		assert_gt((camera.global_position - state.position).dot(up), 0.5, "above the marble")


## With the marble against a 0.2 m wall and the camera on its far side, min_distance would put
## the camera past the wall. The camera stops inside the wall, so a ray from the camera to the
## marble meets no face that the camera sees from the front.
func test_marble_stays_in_sight_behind_a_thin_wall() -> void:
	_start(FLAT, [_thin_wall()])
	run.marble.teleport(Vector3(0, 0.2, 0.4 - 0.2 - Marble.SKIN), Vector3.ZERO)
	_play(_looking(0.0, PlayerSource.START_PITCH), 0.2)
	var ray: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		camera.global_position, run.state.position, WorldQuery.SOLID_MASK
	)
	ray.hit_back_faces = false
	var hit: Dictionary = camera.get_world_3d().direct_space_state.intersect_ray(ray)
	assert_true(hit.is_empty(), "a front face hides the marble: %s" % [hit])
	assert_gt(camera.global_position.z, 0.4, "the camera went into the wall")


## The camera reads clearance and field_of_view each tick, so the tuning overlay changes them
## live: a larger clearance pulls the camera in from the wall at once.
func test_reads_clearance_and_field_of_view_each_tick() -> void:
	_start(WALL)
	run.marble.teleport(Vector3(4, 0.2, -0.5), Vector3.ZERO)
	var input: MarbleInput = _looking(0.0, PlayerSource.START_PITCH)
	_play(input, 0.5)
	var before: float = camera.global_position.distance_to(run.state.position)
	assert_lt(before, camera.distance, "the wall pulled the camera in")
	camera.clearance += 0.1
	camera.field_of_view = 70.0
	_play(input, DT)
	var after: float = camera.global_position.distance_to(run.state.position)
	assert_almost_eq(after, before - 0.1 / cos(PlayerSource.START_PITCH), 0.005)
	assert_eq(camera.fov, 70.0)


## A hard landing shakes the camera for a short time; a soft landing does not.
func test_hard_landing_shakes_the_camera() -> void:
	_start(FLAT)
	var input: MarbleInput = _looking(0.0, PlayerSource.START_PITCH)
	_play(input, 0.2)
	var rest: Basis = camera.global_basis
	run.marble.feedback.emit(&"marble.land", 0.2, run.state.position)
	assert_lt(_largest_turn(input, rest, 0.2), 0.0001, "soft landing")
	run.marble.feedback.emit(&"marble.land", 1.0, run.state.position)
	assert_gt(_largest_turn(input, rest, 0.2), 0.005, "hard landing")
	_play(input, 0.5)
	assert_lt(camera.global_basis.y.angle_to(rest.y), 0.0001, "the shake ends")


## With the shake setting off, a hard landing does not move the camera.
func test_shake_setting_turns_shake_off() -> void:
	FollowCamera.shake_enabled = false
	_start(FLAT)
	var input: MarbleInput = _looking(0.0, PlayerSource.START_PITCH)
	_play(input, 0.2)
	var rest: Basis = camera.global_basis
	run.marble.feedback.emit(&"marble.land", 1.0, run.state.position)
	assert_lt(_largest_turn(input, rest, 0.3), 0.0001)


## The shadow box reaches straight down from the marble centre to just below the floor,
## and the shadow hides where no Solid is below.
func test_blob_shadow_sits_straight_below() -> void:
	_start(FLAT)
	var input: MarbleInput = _looking(0.0, PlayerSource.START_PITCH)
	run.marble.teleport(Vector3(1, 3, 2), Vector3.ZERO)
	_play(input, DT)
	var shadow: BlobShadow = camera.shadow
	var top: Vector3 = shadow.global_position + shadow.global_basis.y * shadow.size.y * 0.5
	assert_true(shadow.visible)
	assert_almost_eq(shadow.global_basis.y, Vector3.UP, Vector3.ONE * 0.001)
	assert_almost_eq(top, run.state.position, Vector3.ONE * 0.001)
	assert_between(top.y - shadow.size.y, -BlobShadow.BELOW - 0.01, -0.01, "bottom below the floor")
	run.marble.teleport(Vector3(100, 3, 0), Vector3.ZERO)
	_play(input, DT)
	assert_false(shadow.visible, "no floor below")


## Starts a run of level and the extra nodes with a follow camera in it, as Game.load_level
## does.
func _start(level: PackedScene, extra: Array[Node3D] = []) -> void:
	start_run(level, extra)
	camera = FollowCamera.new()
	camera.run = run
	run.add_child(camera)
	sight = WorldQuery.new(camera.get_world_3d().direct_space_state, 0.01, 0.0)


## Steps the run and then the camera for seconds, and calls each after every tick.
func _play(input: MarbleInput, seconds: float, each: Callable = Callable()) -> void:
	for _i: int in maxi(roundi(seconds / DT), 1):
		run.step(input)
		camera.follow(run.state, input, DT)
		if each.is_valid():
			each.call()


## Plays seconds with input and returns the largest angle between the camera's y and rest's y.
func _largest_turn(input: MarbleInput, rest: Basis, seconds: float) -> float:
	var largest: Array[float] = [0.0]
	var measure: Callable = func() -> void:
		largest[0] = maxf(largest[0], camera.global_basis.y.angle_to(rest.y))
	_play(input, seconds, measure)
	return largest[0]


## Returns the camera's up without the pitch of input.
func _camera_up(input: MarbleInput) -> Vector3:
	return (camera.global_basis * Basis(Vector3.RIGHT, -input.camera_pitch)).y


## Returns a Solid wall 0.2 m thick from z = 0.4 to 0.6, with a one-sided triangle mesh as
## the level converter makes.
func _thin_wall() -> Solid:
	var box: BoxMesh = BoxMesh.new()
	box.size = Vector3(4, 2, 0.2)
	var mesh: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	mesh.set_faces(box.get_faces())
	var shape: CollisionShape3D = CollisionShape3D.new()
	shape.shape = mesh
	var wall: Solid = Solid.new()
	wall.position = Vector3(0, 1, 0.5)
	wall.add_child(shape)
	return wall


## Returns a MarbleInput with no move and the camera at yaw and pitch.
func _looking(yaw: float, pitch: float) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.camera_yaw = yaw
	input.camera_pitch = pitch
	return input

