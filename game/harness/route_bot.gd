class_name RouteBot
extends InputSource
## The route bot (docs/plan.md §4.6): plays a level along one of its routes
## (objects/route/route.gd) with the same MarbleInput as a player. Each tick it steers from the
## GameState toward the next point, so small physics differences between runs, and between
## Linux and Windows, do not break it. It never moves the marble itself. Besides the state it
## reads only what a player sees: the period of a mover it waits for, and the velocity of the
## mover under the marble (Marble.touches).
##
##     var bot: RouteBot = RouteBot.new(run, RouteBot.find(run, "expert"))
##     if bot.problems.is_empty():
##         var result: Dictionary = bot.drive()
##
## drive() restarts the run and plays it to the end at full speed. The result is
## {finished, time, falls}, and {stuck_at, waypoint, reason} when the bot gives up. reason is
## "stuck" (no progress for STUCK_SECONDS), "fell" (MAX_FALLS falls; stuck_at is the last
## ground position), "route_end" (the bot reached the last point, but the run did not finish
## in STUCK_SECONDS: a gem is missing) or "timeout" (MAX_SECONDS).

## The bot gives up after this much run time, s.
const MAX_SECONDS: float = 300.0
## The bot gives up when the distance to the next point does not shrink by PROGRESS in this
## time, s.
const STUCK_SECONDS: float = 5.0
const PROGRESS: float = 0.25
## The bot gives up at this fall.
const MAX_FALLS: int = 3
## The marble reaches a point within this distance across the floor, m, or when it crosses the
## line through the point across the way there, within PASS_WIDTH of the point.
const REACH: float = 0.35
const PASS_WIDTH: float = 1.5
## The marble reaches a stop within this distance, m, at less than this speed over the ground,
## m/s.
const STOP_REACH: float = 0.5
const STOP_SPEED: float = 0.75
## A point more than this far above or below the marble is on another floor, m.
const HEIGHT_TOLERANCE: float = 2.0
## Deceleration that the speed plan expects on the ground and in the air, m/s². The marble
## brakes at 15 m/s² on the ground and 5 m/s² in the air; the margin covers a crest that
## throws the marble into the air while it brakes.
const GROUND_BRAKE: float = 8.0
const AIR_BRAKE: float = 3.0
## A turn of angle a at speed v carries the marble about (v sin a)² / (2 TURN_ACCELERATION)
## wide (v² / (2 TURN_ACCELERATION) past 90°); the plan keeps that under TURN_ROOM, m.
const TURN_ACCELERATION: float = 12.0
const TURN_ROOM: float = 0.5
## The bot steers back to the line between two points at this speed per metre off the line,
## 1/s, and at most MAX_CORRECTION m/s.
const LINE_GAIN: float = 4.0
const MAX_CORRECTION: float = 5.0
## To slow down the bot pulls the stick back this far, when the speed on an axis is this much
## too high, m/s. A push in the direction of travel never slows the marble.
const PULL_BACK: float = 0.02
const SLOW_MARGIN: float = 0.1
## In the air the bot pushes only when the velocity is this far from the wish, m/s.
const AIR_DEADBAND: float = 0.3
## The bot holds a jump for at most this many ticks, until the marble rises at half the jump
## impulse.
const JUMP_TICKS: int = 36

## The route problems that stop drive(): bad actions, or a missing mover.
var problems: PackedStringArray = []
## True after the run finished or the bot gave up.
var done: bool = false
var finished: bool = false
## Falls out of bounds in this drive.
var falls: int = 0
## The index of the point that the bot heads for.
var waypoint: int = 0
## Why and where the bot gave up: &"stuck", &"fell", &"route_end" or &"timeout".
var reason: StringName = &""
var stuck_at: Vector3 = Vector3.ZERO

var _run: LevelRun
var _tuning: MarbleTuning
var _dt: float = 1.0 / Engine.physics_ticks_per_second
var _points: Array[Route.Waypoint] = []
## Top speed on the way to each point, and the speed plan's speed at each point, m/s.
var _caps: PackedFloat64Array = []
var _limits: PackedFloat64Array = []
## (period, offset) of each mover that a point waits for.
var _cycles: Dictionary[StringName, Vector2] = {}
## Where the way to the current point starts.
var _from: Vector3 = Vector3.ZERO
var _waiting: bool = false
var _wait_left: float = 0.0
var _use_ticks: int = 0
var _jump_ticks: int = 0
var _yaw: float = 0.0
var _best: float = INF
var _since_best: float = 0.0
var _falling: bool = false
## True after the marble reached the last point.
var _at_end: bool = false
var _ground_at: Vector3 = Vector3.ZERO


## Returns the route of run whose kind or node name is which, or null.
static func find(run: LevelRun, which: String) -> Route:
	for object: LevelObject in run.objects:
		var route: Route = object as Route
		if route != null and (String(route.kind) == which or String(route.name) == which):
			return route
	return null


## Makes a bot that drives route in run. Check problems before drive().
func _init(run: LevelRun, route: Route) -> void:
	_run = run
	_tuning = run.marble.tuning
	var plan: Route.Plan = route.plan()
	_points = plan.waypoints
	problems = plan.problems
	if _points.is_empty():
		problems.append("the route has no points")
	for point: Route.Waypoint in _points:
		if point.mover != &"":
			_bind(point)


## Restarts the run and plays the route to its end at full speed, through InputHub. Returns
## the result (see above). Make your own source active again afterwards.
func drive() -> Dictionary:
	if not problems.is_empty():
		push_error("RouteBot: %s" % "; ".join(problems))
		return {"finished": false, "time": 0.0, "falls": 0}
	_run.auto_step = false
	_run.restart()
	_start(_run.state)
	InputHub.use_source(self)
	while not done:
		_run.step(InputHub.next_input(_run.state))
	return result()


## {finished, time, falls}, and {stuck_at, waypoint, reason} when the bot gave up.
func result() -> Dictionary:
	var out: Dictionary = {"finished": finished, "time": _run.state.timer, "falls": falls}
	if done and not finished:
		out["stuck_at"] = [stuck_at.x, stuck_at.y, stuck_at.z]
		out["waypoint"] = waypoint
		out["reason"] = String(reason)
	return out


## Returns the input for the next tick.
func next_input(state: GameState) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.camera_pitch = PlayerSource.START_PITCH
	if _follow(state):
		_act(state, input)
	input.camera_yaw = _yaw
	return input


## Starts at the first point, with the speed plan from the marble's start position.
func _start(state: GameState) -> void:
	waypoint = 0
	_from = state.position
	_ground_at = state.position
	_plan_speeds(state.position, state.up)
	_yaw = _yaw_toward(state.frame, _flat(_points[0].position - state.position, state.up))


## Follows the run: the finish, falls, the respawn and the time limit. Returns true while the
## bot steers.
func _follow(state: GameState) -> bool:
	if done:
		return false
	if state.status == &"finished":
		done = true
		finished = true
		return false
	if state.status == &"respawning":
		if not _falling:
			_falling = true
			falls += 1
			if falls >= MAX_FALLS:
				_give_up(&"fell", _ground_at)
		return false
	if _falling:
		_falling = false
		_resume(state)
	if state.tick * _dt >= MAX_SECONDS:
		_give_up(&"timeout", state.position)
		return false
	if state.on_ground:
		_ground_at = state.position
	return true


## Goes along the route: waits at a stop, leaves each point it reached, then steers to the next.
## The bot does not leave the last point: it steers back to it until the run finishes, because a
## jump can fly over the finish.
func _act(state: GameState, input: MarbleInput) -> void:
	while waypoint < _points.size():
		var point: Route.Waypoint = _points[waypoint]
		if _waiting:
			if _holding(point, state):
				return
			_waiting = false
			_leave(point, state.position)
		elif not _reached(point, state):
			break
		elif point.stops():
			_waiting = true
			_wait_left = maxf(point.wait, 0.0)
		elif waypoint == _points.size() - 1:
			_at_end = true
			break
		else:
			_leave(point, point.position)
	if waypoint >= _points.size():
		_give_up(&"route_end", state.position)
		return
	_press(state, input)
	_steer(state, input)
	_watch_progress(state)


## True when the marble reached point. A stop needs the marble within STOP_REACH and nearly
## still over the ground. Another point needs it past the line through the point across the
## way there, within PASS_WIDTH; a point without a jump or a use also counts within REACH. A
## point on another floor does not count.
func _reached(point: Route.Waypoint, state: GameState) -> bool:
	var up: Vector3 = state.up
	var offset: Vector3 = point.position - state.position
	if absf(offset.dot(up)) > HEIGHT_TOLERANCE:
		return false
	var to: Vector3 = _flat(offset, up)
	if point.stops():
		var slip: Vector3 = _flat(state.velocity - _ground_velocity(up), up)
		return to.length() < STOP_REACH and slip.length() < STOP_SPEED
	var near: bool = to.length() < REACH
	if near and not (point.jump or point.use):
		return true
	var way: Vector3 = _flat(point.position - _from, up)
	if way.length() < REACH:
		return near
	var along: Vector3 = way.normalized()
	var ahead: float = to.dot(along)
	return ahead <= 0.0 and (to - along * ahead).length() < PASS_WIDTH


## True while the bot waits at the stop point: for its wait, then until its mover's cycle time
## is in the window. The bot gives no move, so the marble stops, or rides the mover under it.
func _holding(point: Route.Waypoint, state: GameState) -> bool:
	if _wait_left > 0.0:
		_wait_left -= _dt
		return true
	if point.mover == &"":
		return false
	var cycle: Vector2 = _cycles[point.mover]
	var at: float = fposmod(state.tick * _dt + cycle.y, cycle.x)
	var from: float = point.window.x
	var to: float = point.window.y
	var open: bool = (from <= at and at < to) if from < to else (at >= from or at < to)
	return not open


## Queues the point's use and jump presses and heads for the next point, on the line from
## from. After a stop, from is the marble, because a mover can carry it away from the point.
func _leave(point: Route.Waypoint, from: Vector3) -> void:
	if point.use:
		_use_ticks = 1
	if point.jump:
		_jump_ticks = JUMP_TICKS
	_from = from
	waypoint += 1
	_best = INF
	_since_best = 0.0


## Presses the queued actions: use for one tick, jump until the marble rises.
func _press(state: GameState, input: MarbleInput) -> void:
	if _use_ticks > 0:
		_use_ticks -= 1
		input.use = true
	if _jump_ticks > 0:
		var rise: float = (state.velocity - _ground_velocity(state.up)).dot(state.up)
		if rise > 0.5 * _tuning.jump_impulse:
			_jump_ticks = 0
		else:
			_jump_ticks -= 1
			input.jump = true


## Steers along the line from the last point to the next one. The wished speed along the line
## is the most from which the marble can still brake to the plan's speed at the point; past the
## point it turns back. A pull toward the line keeps the marble on it, so it passes each point
## and its gem. The camera looks along the line. On the ground the move asks for the wished
## velocity over the ground; in the air it only steers and brakes, so a flight keeps its
## take-off speed.
func _steer(state: GameState, input: MarbleInput) -> void:
	var point: Route.Waypoint = _points[waypoint]
	var up: Vector3 = state.up
	var along: Vector3 = _along(point, state)
	var back: Vector3 = _flat(state.position - point.position, up)
	var ahead: float = -back.dot(along)
	var off: Vector3 = back + along * ahead
	var room: float = maxf(absf(ahead) - (STOP_REACH / 2.0 if point.stops() else REACH), 0.0)
	var air: bool = not state.on_ground
	var brake: float = AIR_BRAKE if air else GROUND_BRAKE
	var speed: float = minf(_caps[waypoint], sqrt(_limits[waypoint] ** 2 + 2.0 * brake * room))
	var want: Vector3 = along * signf(ahead) * speed - (off * LINE_GAIN).limit_length(MAX_CORRECTION)
	want = want.limit_length(_caps[waypoint])
	var velocity: Vector3 = _flat(state.velocity, up)
	_yaw = _yaw_toward(state.frame, along)
	var axes: Basis = _camera_axes(state.frame, up)
	if air:
		var push: Vector3 = want.limit_length(velocity.length()) - velocity
		if push.length() > AIR_DEADBAND:
			input.move = Vector2(push.dot(axes.x), push.dot(axes.z)).normalized()
		return
	var ground: Vector3 = _flat(_ground_velocity(up), up)
	var wish: Vector3 = want - ground
	var over: Vector3 = velocity - ground
	var move: Vector2 = Vector2(
		_axis(wish.dot(axes.x), over.dot(axes.x)), _axis(wish.dot(axes.z), over.dot(axes.z))
	)
	input.move = move.limit_length(1.0)


## The direction of the line to point, across the floor: from the last point, or straight at
## the point when the line is too short, or the camera's forward when the marble is on it.
func _along(point: Route.Waypoint, state: GameState) -> Vector3:
	var way: Vector3 = _flat(point.position - _from, state.up)
	if way.length() < REACH:
		way = _flat(point.position - state.position, state.up)
	return way.normalized() if not way.is_zero_approx() else _camera_axes(state.frame, state.up).z


## The move on one camera axis that turns the speed over the ground into the wished speed.
func _axis(wish: float, speed: float) -> float:
	if wish * speed > 0.0 and absf(speed) > absf(wish) + SLOW_MARGIN:
		return -signf(speed) * PULL_BACK
	return wish / _tuning.max_roll_speed


## Gives up when the distance to the next point stops shrinking.
func _watch_progress(state: GameState) -> void:
	var distance: float = _flat(_points[waypoint].position - state.position, state.up).length()
	if distance < _best - PROGRESS:
		_best = distance
		_since_best = 0.0
		return
	_since_best += _dt
	if _since_best >= STUCK_SECONDS:
		_give_up(&"route_end" if _at_end else &"stuck", state.position)


## After a respawn, heads for the point nearest to the marble, at or before the current one.
func _resume(state: GameState) -> void:
	var nearest: int = 0
	for i: int in range(1, mini(waypoint + 1, _points.size())):
		var gap: float = _points[i].position.distance_to(state.position)
		if gap < _points[nearest].position.distance_to(state.position):
			nearest = i
	waypoint = nearest
	_from = state.position
	_waiting = false
	_use_ticks = 0
	_jump_ticks = 0
	_best = INF
	_since_best = 0.0


## Ends the drive without a finish.
func _give_up(why: StringName, at: Vector3) -> void:
	done = true
	reason = why
	stuck_at = at


## Fills the speed plan: the top speed on each way, a stop at each stop point, a speed for each
## turn, and the braking from each point to the next.
func _plan_speeds(start: Vector3, up: Vector3) -> void:
	var count: int = _points.size()
	var top: float = _tuning.max_roll_speed
	_caps.resize(count)
	_limits.resize(count)
	for i: int in count:
		var speed: float = _points[i].speed
		_caps[i] = minf(speed, top) if speed > 0.0 else top
	for i: int in range(count - 1, -1, -1):
		var point: Route.Waypoint = _points[i]
		var limit: float = 0.0 if point.stops() else _caps[i]
		if i + 1 < count:
			var next: Route.Waypoint = _points[i + 1]
			var before: Vector3 = _points[i - 1].position if i > 0 else start
			var way_in: Vector3 = _flat(point.position - before, up)
			var way_out: Vector3 = _flat(next.position - point.position, up)
			var brake: float = AIR_BRAKE if point.jump else GROUND_BRAKE
			var after: float = sqrt(_limits[i + 1] ** 2 + 2.0 * brake * way_out.length())
			limit = minf(limit, minf(_turn_speed(way_in, way_out), minf(_caps[i + 1], after)))
		_limits[i] = limit


## Reads the period and offset of the mover that point waits for, or records a problem.
func _bind(point: Route.Waypoint) -> void:
	for object: LevelObject in _run.objects:
		if object.name != point.mover:
			continue
		var period: Variant = object.get(&"period")
		var offset: Variant = object.get(&"offset")
		var length: float = period if period is float else 0.0
		var shift: float = offset if offset is float else 0.0
		if length <= 0.0:
			problems.append("wait_until: %s has no period setting" % point.mover)
		elif point.window.x > length or point.window.y > length:
			problems.append("wait_until: %s has a period of %.2f s" % [point.mover, length])
		_cycles[point.mover] = Vector2(length, shift)
		return
	problems.append("wait_until: the level has no object named %s" % point.mover)


## The velocity of the floor under the marble in the last tick: a mover's, else zero.
func _ground_velocity(up: Vector3) -> Vector3:
	var best: Contact = null
	for contact: Contact in _run.marble.touches:
		var facing: float = contact.normal.dot(up)
		if facing >= _tuning.floor_min_up and (best == null or facing > best.normal.dot(up)):
			best = contact
	return best.velocity if best != null else Vector3.ZERO


## The camera's right (x) and forward (z) at the bot's yaw, in the plane normal to up, as
## Marble._axes() makes them.
func _camera_axes(frame: Basis, up: Vector3) -> Basis:
	var heading: Basis = frame * Basis(Vector3.UP, _yaw)
	var forward: Vector3 = (up * heading.z.dot(up) - heading.z).normalized()
	return Basis(forward.cross(up), up, forward)


## The camera yaw in frame that looks along direction; the camera looks along -z of its
## heading.
static func _yaw_toward(frame: Basis, direction: Vector3) -> float:
	var local: Vector3 = frame.inverse() * direction
	return atan2(-local.x, -local.z)


## The top speed for a turn from direction a to direction b.
static func _turn_speed(a: Vector3, b: Vector3) -> float:
	if a.is_zero_approx() or b.is_zero_approx():
		return INF
	var cosine: float = a.normalized().dot(b.normalized())
	var sine: float = 1.0 if cosine < 0.0 else sqrt(1.0 - cosine * cosine)
	return INF if sine < 0.01 else sqrt(2.0 * TURN_ACCELERATION * TURN_ROOM) / sine


## v without its part along up.
static func _flat(v: Vector3, up: Vector3) -> Vector3:
	return v - up * v.dot(up)
