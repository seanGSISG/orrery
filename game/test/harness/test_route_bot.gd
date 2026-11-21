extends RunTest
## The route bot (harness/route_bot.gd) on test/levels/route_bot.tscn: two slabs with a 3 m gap
## between them. Both routes jump the gap; first_run takes off at 8 m/s, expert at full speed.

const LEVEL: PackedScene = preload("res://test/levels/route_bot.tscn")
const ROUTE: PackedScene = preload("res://objects/route/route.tscn")


func after_each() -> void:
	InputHub.use_source(PlayerSource.new())


## Starts a run of LEVEL with the extra nodes, drives its route which and returns the bot.
func _drive(which: String, extra: Array[Node3D] = []) -> RouteBot:
	start_run(LEVEL, extra)
	var bot: RouteBot = RouteBot.new(run, RouteBot.find(run, which))
	assert_eq(bot.problems, PackedStringArray())
	bot.drive()
	return bot


func test_first_run_jumps_the_gap_and_finishes_under_par() -> void:
	var bot: RouteBot = _drive("first_run")
	assert_eq([bot.finished, bot.falls], [true, 0])
	assert_eq([run.state.status, run.state.medal], [&"finished", &"qualified"])
	assert_eq(bot.result(), {"finished": true, "time": run.state.timer, "falls": 0})


func test_expert_route_takes_gold() -> void:
	var bot: RouteBot = _drive("expert")
	assert_true(bot.finished)
	assert_eq(run.state.medal, &"gold")


func test_a_route_into_the_gap_falls_and_gives_up_at_the_edge() -> void:
	var route: Route = ROUTE.instantiate() as Route
	route.name = &"IntoTheGap"
	route.actions = "0 wait 0"
	var point: Marker3D = Marker3D.new()
	point.position = Vector3(0, 0, -11.5)
	route.add_child(point)
	var bot: RouteBot = _drive("IntoTheGap", [route])
	assert_false(bot.finished)
	assert_eq([bot.falls, bot.reason, bot.waypoint], [RouteBot.MAX_FALLS, &"fell", 0])
	assert_almost_eq(bot.stuck_at.z, -10.0, 0.5, "the last ground is the edge of the near slab")
	var reason: String = bot.result()["reason"]
	assert_eq(reason, "fell")


func test_the_last_point_jumps_once_then_the_route_ends_without_a_finish() -> void:
	var route: Route = ROUTE.instantiate() as Route
	route.name = &"JumpAtTheEnd"
	route.actions = "0 speed 3; 0 jump"
	var point: Marker3D = Marker3D.new()
	point.position = Vector3(0, 0, -4)
	route.add_child(point)
	start_run(LEVEL, [route])
	var jumps: Array[int] = [0]
	run.feedback.connect(
		func(kind: StringName, _strength: float, _at: Vector3) -> void:
			if kind == &"marble.jump":
				jumps[0] += 1
	)
	var bot: RouteBot = RouteBot.new(run, RouteBot.find(run, "JumpAtTheEnd"))
	bot.drive()
	assert_eq([bot.finished, bot.reason, jumps[0]], [false, &"route_end", 1])
