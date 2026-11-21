extends GutTest
## The `route` marker (objects/route/route.gd): its actions text, and the route lint of the
## level converter.


## Returns count points, 1 m apart along -z.
func _points(count: int) -> PackedVector3Array:
	var points: PackedVector3Array = []
	for i: int in count:
		points.append(Vector3(0, 0, -1 - i))
	return points


## Returns a scene like an imported .glb: a level of tier with a start, a finish and markers.
func _scene(tier: String, markers: Array[Dictionary]) -> Node3D:
	var root: Node3D = autofree(Node3D.new())
	root.name = "scene"
	var all: Array[Dictionary] = [{"type": "level", "id": "t", "tier": tier}, {"type": "start"}]
	all.append({"type": "finish"})
	all.append_array(markers)
	for data: Dictionary in all:
		var node: Node3D = Node3D.new()
		node.name = "%s_%d" % [data["type"], root.get_child_count()]
		node.set_meta(&"extras", {"orrery": data})
		root.add_child(node)
	return root


## Returns the errors of converting scene.
func _errors(scene: Node3D) -> String:
	var converter: LevelConverter = LevelConverter.new()
	converter.convert(scene)
	return "\n".join(converter.errors)


func test_actions_set_their_waypoints() -> void:
	var text: String = "0 speed 6; 0 jump;1 use ; 1 wait 1.5; 2 wait_until gear_00 7.5 0.5"
	var plan: Route.Plan = Route.parse(text, _points(3))
	assert_eq(plan.problems, PackedStringArray())
	var first: Route.Waypoint = plan.waypoints[0]
	assert_eq([first.speed, first.jump, first.use, first.stops()], [6.0, true, false, false])
	var second: Route.Waypoint = plan.waypoints[1]
	assert_eq([second.use, second.wait, second.stops()], [true, 1.5, true])
	var third: Route.Waypoint = plan.waypoints[2]
	assert_eq([third.mover, third.window_from, third.window_to], [&"gear_00", 7.5, 0.5])
	assert_true(third.stops())
	assert_eq(third.position, Vector3(0, 0, -3))


func test_each_bad_action_is_one_problem_that_quotes_it() -> void:
	var text: String = "jump; 3 jump; 0 fly; 0 wait; 0 wait -1; 0 speed 0; 1 wait_until g 2 2"
	var plan: Route.Plan = Route.parse(text, _points(2))
	assert_eq(plan.problems.size(), 7)
	assert_string_contains(plan.problems[1], "`3 jump`: the route has no point 3")
	assert_string_contains(plan.problems[2], "unknown action `fly`")
	assert_eq(plan.waypoints[0].wait, -1.0, "a bad entry changes nothing")


func test_a_level_outside_the_test_tier_needs_a_first_run_route() -> void:
	assert_eq(_errors(_scene("test", [])), "")
	var expert: Array[Dictionary] = [{"type": "route", "kind": "expert"}]
	var error: String = _errors(_scene("beginner", expert))
	assert_string_contains(error, "level t: node scene: needs a `route` marker of kind first_run")
	var first_run: Array[Dictionary] = [{"type": "route", "kind": "first_run"}]
	assert_false(_errors(_scene("beginner", first_run)).contains("needs a `route`"))


func test_route_kinds_are_first_run_or_expert_once_each() -> void:
	var routes: Array[Dictionary] = [{"type": "route", "kind": "first_run"}]
	routes.append({"type": "route", "kind": "first_run"})
	routes.append({"type": "route", "kind": "fast"})
	var errors: String = _errors(_scene("test", routes))
	assert_string_contains(errors, "node route_4: a second `first_run` route")
	assert_string_contains(errors, "node route_5: a `route` needs the kind first_run or expert")
