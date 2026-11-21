extends GutTest
## AscentFalls: the falls and the metres fallen that it counts from the marble's height and
## its contact with the ground, one call per tick.

var counter: AscentFalls


func before_each() -> void:
	counter = AscentFalls.new()


## A drop through the air of more than FALL_HEIGHT is one fall of its whole height.
func test_drop_over_the_limit_is_one_fall() -> void:
	_stand(10.0, 0.1)
	_move(10.0, 2.0, 1.0, false)
	assert_true(counter.falling, "the fall is in progress in the air")
	_stand(2.0, 0.5)
	assert_false(counter.falling)
	assert_eq(counter.falls, 1)
	assert_almost_eq(counter.fallen, 8.0, 0.001)


## A drop of less than FALL_HEIGHT is not a fall.
func test_drop_under_the_limit_is_no_fall() -> void:
	_stand(10.0, 0.1)
	_move(10.0, 10.0 - AscentFalls.FALL_HEIGHT + 0.1, 0.5, false)
	_stand(10.0 - AscentFalls.FALL_HEIGHT + 0.1, 0.5)
	assert_eq(counter.falls, 0)
	assert_eq(counter.fallen, 0.0)


## The bounces after a landing belong to the same fall, and add no metres.
func test_bounces_belong_to_the_fall() -> void:
	_stand(20.0, 0.1)
	_move(20.0, 0.0, 1.4, false)
	_stand(0.0, 0.02)
	_move(0.0, 5.0, 0.5, false)
	_move(5.0, 0.0, 0.5, false)
	_stand(0.0, 0.5)
	assert_eq(counter.falls, 1)
	assert_almost_eq(counter.fallen, 20.0, 0.001)


## A ledge that the marble only touches on the way down does not end the fall.
func test_touched_ledge_does_not_end_the_fall() -> void:
	_stand(30.0, 0.1)
	_move(30.0, 20.0, 1.0, false)
	_stand(20.0, 0.1)
	_move(20.0, 5.0, 1.0, false)
	_stand(5.0, 0.5)
	assert_eq(counter.falls, 1)
	assert_almost_eq(counter.fallen, 25.0, 0.001)


## A fall after the marble came to rest is a new fall.
func test_fall_after_a_rest_is_a_new_fall() -> void:
	_stand(30.0, 0.1)
	_move(30.0, 20.0, 1.0, false)
	_stand(20.0, 0.5)
	_move(20.0, 5.0, 1.0, false)
	_stand(5.0, 0.5)
	assert_eq(counter.falls, 2)
	assert_almost_eq(counter.fallen, 25.0, 0.001)


## A slow way down on the ground is not a fall: the marble forgets the old floor.
func test_slow_way_down_is_no_fall() -> void:
	_stand(10.0, 0.1)
	_move(10.0, 0.0, 10.0, true)
	assert_eq(counter.falls, 0)
	assert_eq(counter.fallen, 0.0)


## A fast slide down a slope is a fall, though the marble never leaves the ground.
func test_fast_slide_down_is_a_fall() -> void:
	_stand(10.0, 0.1)
	_move(10.0, 0.0, 2.0, true)
	_stand(0.0, 0.5)
	assert_eq(counter.falls, 1)
	assert_almost_eq(counter.fallen, 10.0, 0.001)


## A teleport to a lower place (a respawn, the harness) is not a fall, and it ends a fall in
## progress.
func test_teleport_is_no_fall() -> void:
	_stand(50.0, 0.1)
	_stand(10.0, 0.1)
	assert_eq(counter.falls, 0)
	_move(10.0, 4.0, 0.5, false)
	assert_true(counter.falling)
	_stand(40.0, 0.1)
	assert_false(counter.falling)
	assert_eq(counter.falls, 1)
	assert_almost_eq(counter.fallen, 6.0, 0.001)


## A new counter that resumes the floor and the lowest point of a saved fall goes on with
## the same fall.
func test_resumed_fall_is_the_same_fall() -> void:
	_stand(20.0, 0.1)
	_move(20.0, 12.0, 0.8, false)
	var saved: AscentFalls = counter
	counter = AscentFalls.new()
	counter.falls = saved.falls
	counter.fallen = saved.fallen
	counter.resume(Vector3(0.0, 12.0, 0.0), saved.floor_height, saved.low_height)
	assert_true(counter.falling)
	_move(12.0, 0.0, 0.8, false)
	_stand(0.0, 0.5)
	assert_eq(counter.falls, 1)
	assert_almost_eq(counter.fallen, 20.0, 0.001)


## The first call of track() tells the start of a fall.
func test_track_tells_the_start_of_a_fall() -> void:
	_stand(10.0, 0.1)
	var starts: int = 0
	for tick: int in 120:
		var height: float = 10.0 - 8.0 * (tick + 1) / 120.0
		if counter.track(Vector3(0.0, height, 0.0), height, false):
			starts += 1
	assert_eq(starts, 1)


## Keeps the marble on the ground at height for seconds.
func _stand(height: float, seconds: float) -> void:
	_move(height, height, seconds, true)


## Moves the marble from one height to another in seconds, on the ground or in the air.
func _move(from: float, to: float, seconds: float, on_ground: bool) -> void:
	var ticks: int = roundi(seconds * Engine.physics_ticks_per_second)
	for tick: int in ticks:
		var height: float = lerpf(from, to, float(tick + 1) / ticks)
		counter.track(Vector3(0.0, height, 0.0), height, on_ground)
