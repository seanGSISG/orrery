extends Node
## The level test of `just test-levels [id ...]` and `just suggest-times <id>` (docs/plan.md
## §5.2): the route bot drives the routes of built levels, headless and at full speed. Run the
## scene with the level ids as user arguments:
##     godot --headless --path game res://harness/route_bot_levels.tscn -- [--suggest] [id ...]
## With no ids it tests every level in res://levels/built/. The first_run route must finish
## under par and the expert route under gold, with no fall. A level skips a kind that it has no
## route of. With --suggest it prints the par and gold that the bot's times give instead:
## par = first_run time × 1.5 and gold = expert time × 1.15. It exits 1 when a route fails.
## It is a scene, not a --script SceneTree, because a --script compiles before the autoloads
## exist.

const BUILT: String = "res://levels/built/"
## The par and gold rule (docs/plan.md §4.6), by route kind.
const FACTORS: Dictionary[StringName, float] = {&"first_run": 1.5, &"expert": 1.15}
const LIMITS: Dictionary[StringName, String] = {&"first_run": "par", &"expert": "gold"}


## Tests the levels of the user arguments, prints a report and quits with the exit code.
func _ready() -> void:
	var ids: PackedStringArray = OS.get_cmdline_user_args()
	var suggest: bool = "--suggest" in ids
	ids.erase("--suggest")
	if ids.is_empty():
		ids = _built_ids()
	if ids.is_empty():
		print("test-levels: no built levels in %s; run `just build-levels`" % BUILT)
		get_tree().quit(1)
		return
	var counts: Dictionary[StringName, int] = {&"pass": 0, &"fail": 0, &"skip": 0}
	for id: String in ids:
		var run: LevelRun = Game.load_level(StringName(id))
		if run == null:
			print("%-12s no level %s%s.glb: run `just build-levels %s`" % [id, BUILT, id, id])
			counts[&"fail"] += 1
			continue
		var times: PackedStringArray = []
		for kind: StringName in Route.KINDS:
			var outcome: Outcome = _drive(run, kind, INF if suggest else _limit(run, kind))
			counts[outcome.status] += 1
			print("%-12s %-10s %-5s %s" % [id, kind, outcome.status, outcome.why])
			if outcome.status == &"pass":
				var value: float = ceilf(run.state.timer * FACTORS[kind] * 10.0) / 10.0
				times.append("%s=%.1f" % [LIMITS[kind], value])
		if suggest and not times.is_empty():
			var now: String = "par=%.1f, gold=%.1f" % [run.level.par, run.level.gold]
			print("%-12s suggest kit.level(%s); it has %s" % [id, ", ".join(times), now])
	var summary: String = "%d passed, %d failed, %d skipped"
	print("test-levels: " + summary % [counts[&"pass"], counts[&"fail"], counts[&"skip"]])
	get_tree().quit(1 if counts[&"fail"] > 0 else 0)


## Drives the route of kind on run. limit is the time to beat.
static func _drive(run: LevelRun, kind: StringName, limit: float) -> Outcome:
	var route: Route = RouteBot.find(run, kind)
	if route == null:
		return Outcome.new(&"skip", "no %s route" % kind)
	var bot: RouteBot = RouteBot.new(run, route)
	if not bot.problems.is_empty():
		return Outcome.new(&"fail", "route %s: %s" % [route.name, "; ".join(bot.problems)])
	bot.drive()
	var time: float = run.state.timer
	if not bot.finished:
		return Outcome.new(&"fail", _why_not(run, bot))
	if bot.falls > 0:
		return Outcome.new(&"fail", "finished in %.2f s, but fell %d times" % [time, bot.falls])
	if time > limit:
		return Outcome.new(&"fail", "%.2f s is over %s %.2f s" % [time, LIMITS[kind], limit])
	var against: String = " (%s %.2f s)" % [LIMITS[kind], limit] if is_finite(limit) else ""
	return Outcome.new(&"pass", "%.2f s%s" % [time, against])


## Explains a drive that did not finish, with positions in level script axes (Blender x, y, z).
static func _why_not(run: LevelRun, bot: RouteBot) -> String:
	var godot: Vector3 = bot.stuck_at
	var at: String = "(%.1f, %.1f, %.1f)" % [godot.x, -godot.z, godot.y]
	var gems: String = "gems %d/%d" % [run.state.gems_collected, run.state.gems_total]
	match bot.reason:
		&"fell":
			return "fell %d times; last on the ground at %s on the way to point %d" % [
				bot.falls, at, bot.waypoint
			]
		&"route_end":
			return "passed the last point at %s without the finish; %s" % [at, gems]
		&"timeout":
			return "no finish after %.0f s; at %s, %s" % [RouteBot.MAX_SECONDS, at, gems]
	return "stuck at %s on the way to point %d after %.2f s" % [at, bot.waypoint, run.state.timer]


## The time to beat for kind: par for first_run, gold for expert.
static func _limit(run: LevelRun, kind: StringName) -> float:
	return run.level.par if kind == &"first_run" else run.level.gold


## The ids of the built levels, sorted.
static func _built_ids() -> PackedStringArray:
	var ids: PackedStringArray = []
	for file: String in DirAccess.get_files_at(BUILT):
		if file.get_extension() == "glb":
			ids.append(file.get_basename())
	ids.sort()
	return ids


## The result of one route: status &"pass", &"fail" or &"skip", and a line that explains it.
class Outcome:
	extends RefCounted
	var status: StringName
	var why: String

	func _init(result: StringName, line: String) -> void:
		status = result
		why = line
