class_name Route
extends LevelObject
## The `route` marker: a line through the level for the route bot (harness/route_bot.gd,
## docs/plan.md §4.6). The bot rolls through the marker's points in order and does the actions
## of each point. Each level script places two routes: kind `first_run`, the line of a player
## who plays the level for the first time, and kind `expert`, the fastest line. `just
## test-levels` drives both: first_run must finish under par and expert under gold, and `just
## suggest-times <id>` prints par = first_run time × 1.5 and gold = expert time × 1.15.
##
##     kit.marker("route", at=(0, 2, 0), name="route_first_run", kind="first_run",
##                points=[(0, 7, 0), (0, 10, 0), (0, 34, 0)],
##                actions="0 wait_until moving_platform_00 8.6 0.2; 2 speed 8")
##
## points: positions on the floor, in order. The marker's own position is not a point. Put a
## point on each gem and on the finish pad: the bot passes within 0.35 m of each point.
## actions: entries `<point> <action> [values]`, separated by `;`. <point> is the 0-based index
## in points, the same number as the point's name suffix `_pNN`.
## - `jump`: jump at the point.
## - `use`: use the held power-up at the point.
## - `wait <s>`: stop at the point and wait s seconds.
## - `wait_until <object> <from> <to>`: stop at the point and wait until the cycle time of the
##   named object, fposmod(t + offset, period) in s, is in [from, to). from > to wraps round
##   the end of the cycle. The object needs a `period` setting (a moving platform, a gear). On
##   a moving platform the marble rides along while it waits.
## - `speed <m/s>`: the top speed on the way to the point. The bot also slows down before the
##   way starts. A flight keeps its take-off speed, so give a jump's landing point a speed.
## At one point the bot first waits, then uses, then jumps.

## The route kinds; a level has at most one route of each kind.
const KINDS: Array[StringName] = [&"first_run", &"expert"]
## The number of values that each action takes.
const VALUES: Dictionary[String, int] = {
	"jump": 0, "use": 0, "wait": 1, "wait_until": 3, "speed": 1
}

## &"first_run" or &"expert".
@export var kind: StringName = &""
## The actions of the points, as above.
@export var actions: String = ""


## Returns the points with their actions, and the problems of the actions text.
func plan() -> Plan:
	var points: PackedVector3Array = []
	for child: Node in get_children():
		var point: Marker3D = child as Marker3D
		if point != null:
			points.append(point.global_position)
	return parse(actions, points)


## Returns the waypoints at points with the actions of text. Each problem names its entry.
static func parse(text: String, points: PackedVector3Array) -> Plan:
	var out: Plan = Plan.new()
	for at: Vector3 in points:
		var waypoint: Waypoint = Waypoint.new()
		waypoint.position = at
		out.waypoints.append(waypoint)
	for entry: String in text.split(";", false):
		var words: PackedStringArray = entry.strip_edges().split(" ", false)
		if words.is_empty():
			continue
		var problem: String = _read(words, out.waypoints)
		if problem != "":
			out.problems.append("action `%s`: %s" % [" ".join(words), problem])
	return out


## Applies one action entry to its waypoint. Returns the problem, or "".
static func _read(words: PackedStringArray, waypoints: Array[Waypoint]) -> String:
	if not words[0].is_valid_int():
		return "start with the point index"
	var index: int = words[0].to_int()
	if index < 0 or index >= waypoints.size():
		return "the route has no point %d; it has %d points" % [index, waypoints.size()]
	var point: Waypoint = waypoints[index]
	var action: String = words[1] if words.size() > 1 else ""
	var values: PackedStringArray = words.slice(2)
	if not VALUES.has(action):
		return "unknown action `%s`; use jump, use, wait, wait_until or speed" % action
	if values.size() != VALUES[action]:
		return "%s takes %d values" % [action, VALUES[action]]
	var numbers: PackedFloat64Array = []
	for value: String in values.slice(1 if action == "wait_until" else 0):
		if not value.is_valid_float() or value.to_float() < 0.0:
			return "`%s` is not a number of 0 or more" % value
		numbers.append(value.to_float())
	match action:
		"jump":
			point.jump = true
		"use":
			point.use = true
		"wait":
			point.wait = numbers[0]
		"wait_until":
			if numbers[0] == numbers[1]:
				return "from and to are the same time"
			point.mover = StringName(values[0])
			point.window_from = numbers[0]
			point.window_to = numbers[1]
		"speed":
			if numbers[0] == 0.0:
				return "speed must be more than 0"
			point.speed = numbers[0]
	return ""


## One point of a route and what the bot does there.
class Waypoint:
	extends RefCounted
	## World position, on the floor.
	var position: Vector3 = Vector3.ZERO
	var jump: bool = false
	var use: bool = false
	## Seconds to wait at the point; negative means no wait.
	var wait: float = -1.0
	## The object whose cycle the bot waits for; empty means none.
	var mover: StringName = &""
	## The cycle times [window_from, window_to) in s that end the wait for mover. Two floats,
	## not a Vector2, so they keep the precision of the period.
	var window_from: float = 0.0
	var window_to: float = 0.0
	## Top speed on the way to the point, m/s; 0 means no limit.
	var speed: float = 0.0

	## True when the bot stops at the point.
	func stops() -> bool:
		return wait >= 0.0 or mover != &""


## The waypoints of a route, and the problems that stop the bot from driving it.
class Plan:
	extends RefCounted
	var waypoints: Array[Waypoint] = []
	var problems: PackedStringArray = []
