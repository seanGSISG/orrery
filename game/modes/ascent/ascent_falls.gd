class_name AscentFalls
extends RefCounted
## Counts the falls of an Ascent climb and the metres that they cost. Call track() once per
## tick while the run plays. `falls` and `fallen` are the two stats.
##
## - The floor is the highest height at which the marble was on the ground. On lower ground the
##   marble forgets it after FLOOR_MEMORY s, so a slow way down is not a fall.
## - A fall starts when the marble is more than FALL_HEIGHT below the floor. FALL_HEIGHT is 3 m:
##   a jump is 1.4 m high and the highest step that a level asks for is 1.3 m
##   (docs/levels/README.md), so a move of the normal game never counts.
## - The fall ends when the marble stays on the ground for SETTLE s and gets no lower. So the
##   bounces and the slides on the way down belong to the same fall. `fallen` grows by the way
##   from the floor to the lowest point.
## - A move of more than TELEPORT m in one tick is a teleport (a respawn, a continued climb, the
##   harness): it ends the fall, and the new place is the floor.

const FALL_HEIGHT: float = 3.0
const FLOOR_MEMORY: float = 2.0
const SETTLE: float = 0.25
const TELEPORT: float = 3.0
## A height this far under the lowest point is a new lowest point, m.
const LOWER: float = 0.01

## Falls so far, and the metres that they cost.
var falls: int = 0
var fallen: float = 0.0
## True from the start of a fall to its end.
var falling: bool = false

var _ticks_per_second: int = Engine.physics_ticks_per_second
var _floor: float = 0.0
## Ticks on the ground below the floor since the marble was last at the floor.
var _below: int = 0
## The lowest point of the fall in progress, and the ticks on the ground since it.
var _low: float = 0.0
var _still: int = 0
## The position of the last tick; INF before the first.
var _last: Vector3 = Vector3.INF


## Follows one tick: the marble centre is at position, height m above the climb start, and
## on_ground tells if it touches a Solid. Returns true on the tick that a fall starts.
func track(position: Vector3, height: float, on_ground: bool) -> bool:
	if _last == Vector3.INF or position.distance_to(_last) > TELEPORT:
		_stand(height)
	_last = position
	if falling:
		if height < _low - LOWER:
			fallen += _low - height
			_low = height
			_still = 0
		elif on_ground:
			_still += 1
			if _still >= roundi(SETTLE * _ticks_per_second):
				_stand(height)
		else:
			_still = 0
		return false
	if on_ground:
		_below += 1
		if height >= _floor or _below > roundi(FLOOR_MEMORY * _ticks_per_second):
			_stand(height)
	if height >= _floor - FALL_HEIGHT:
		return false
	falling = true
	falls += 1
	fallen += _floor - height
	_low = height
	_still = 0
	return true


## Ends a fall in progress and makes height the floor.
func _stand(height: float) -> void:
	falling = false
	_floor = height
	_below = 0
