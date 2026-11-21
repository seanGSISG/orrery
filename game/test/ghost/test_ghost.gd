extends GutTest
## Ghost recording and playback through record(), finish(), transform_at() and the file
## format: 30 samples a second of level clock, and playback that matches the recorded poses.

const TICK: float = 1.0 / 120.0


## One call per tick keeps one sample each 1/30 s, plus the finish sample.
func test_records_at_30_hz() -> void:
	var ghost: Ghost = _spiral(2.0)
	assert_eq(ghost.size(), 2 * Ghost.RATE + 1)
	ghost.finish(2.01, _spiral_point(2.01), Quaternion())
	assert_eq(ghost.size(), 2 * Ghost.RATE + 2)
	assert_eq(ghost.duration, 2.01)


## Playback at any time matches the recorded path within 1 cm, and the rotation matches.
func test_playback_matches_the_recording() -> void:
	var ghost: Ghost = _spiral(3.0)
	for i: int in 300:
		var time: float = i * 0.01
		var pose: Transform3D = ghost.transform_at(time)
		assert_almost_eq(pose.origin, _spiral_point(time), Vector3.ONE * 0.01, "at %.2f s" % time)
	var turned: Quaternion = ghost.transform_at(1.0).basis.get_rotation_quaternion()
	assert_almost_eq(turned.angle_to(_spin(1.0)), 0.0, 0.001)
	assert_eq(ghost.transform_at(-1.0).origin, _spiral_point(0.0))
	assert_eq(ghost.transform_at(99.0).origin, _spiral_point(3.0))


## The bytes give back the same poses, at about 20 bytes a sample before compression.
func test_bytes_round_trip() -> void:
	var ghost: Ghost = _spiral(60.0)
	ghost.finish(60.004, _spiral_point(60.0), _spin(60.0))
	var bytes: PackedByteArray = ghost.to_bytes()
	assert_lt(bytes.size(), 60 * Ghost.RATE * Ghost.SAMPLE_BYTES + Ghost.HEADER)
	var loaded: Ghost = Ghost.from_bytes(bytes)
	assert_not_null(loaded)
	assert_eq(loaded.size(), ghost.size())
	assert_almost_eq(loaded.duration, ghost.duration, 0.0001)
	for time: float in [0.0, 0.5, 17.25, 59.99, 60.004]:
		var want: Transform3D = ghost.transform_at(time)
		var got: Transform3D = loaded.transform_at(time)
		assert_almost_eq(got.origin, want.origin, Vector3.ONE * 0.0001)
		var angle: float = got.basis.get_rotation_quaternion().angle_to(
			want.basis.get_rotation_quaternion()
		)
		assert_almost_eq(angle, 0.0, 0.001)


## Bytes that are no ghost give null.
func test_bad_bytes_give_null() -> void:
	assert_null(Ghost.from_bytes(PackedByteArray()))
	assert_null(Ghost.from_bytes("ORGH and some text".to_utf8_buffer()))
	var bytes: PackedByteArray = _spiral(1.0).to_bytes()
	assert_null(Ghost.from_bytes(bytes.slice(0, bytes.size() - 4)))


## Returns a ghost recorded once per tick for seconds along _spiral_point().
static func _spiral(seconds: float) -> Ghost:
	var ghost: Ghost = Ghost.new()
	for tick: int in roundi(seconds / TICK) + 1:
		var time: float = tick * TICK
		ghost.record(time, _spiral_point(time), _spin(time))
	return ghost


## A smooth 3D path, m.
static func _spiral_point(time: float) -> Vector3:
	return Vector3(cos(time) * 5.0, time * 2.0, sin(time) * 5.0)


## A roll about a turning axis.
static func _spin(time: float) -> Quaternion:
	return Quaternion(Vector3(1, time * 0.1, 0).normalized(), time * 4.0)
