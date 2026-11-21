extends GutTest
## Rules that every built campaign level keeps. A level under levels/test/ (tier `test`) is
## not a campaign level. `just test` builds the levels first.
## - One Clockwork Egg, off the main route (docs/plan.md §2.3 and §2.7): the first-run route
##   does not pass within OFF_ROUTE of it.

const BUILT: String = "res://levels/built/"
## The first-run route stays this far from the egg, m.
const OFF_ROUTE: float = 5.0


func test_each_campaign_level_has_one_egg_off_the_first_run_route() -> void:
	var checked: int = 0
	for file: String in DirAccess.get_files_at(BUILT):
		if file.get_extension() != "glb":
			continue
		var level: Level = (load(BUILT + file) as PackedScene).instantiate() as Level
		if level == null or level.tier == &"test":
			if level != null:
				level.free()
			continue
		add_child_autofree(level)
		checked += 1
		var eggs: Array[Egg] = []
		var start: StartPad = null
		var route: Route = null
		for node: Node in level.find_children("*", "", true, false):
			if node is Egg:
				eggs.append(node as Egg)
			elif node is StartPad:
				start = node as StartPad
			elif node is Route and (node as Route).kind == &"first_run":
				route = node as Route
		assert_eq(eggs.size(), 1, "%s has one Clockwork Egg" % level.id)
		# The level lint gives every campaign level one start and one first-run route.
		assert_not_null(start, "%s has a start pad" % level.id)
		assert_not_null(route, "%s has a first-run route" % level.id)
		if eggs.size() != 1 or start == null or route == null:
			continue
		var line: PackedVector3Array = [start.global_position]
		for point: Route.Waypoint in route.plan().waypoints:
			line.append(point.position)
		var nearest: float = INF
		for i: int in line.size() - 1:
			var on_line: Vector3 = Geometry3D.get_closest_point_to_segment(
				eggs[0].global_position, line[i], line[i + 1]
			)
			nearest = minf(nearest, on_line.distance_to(eggs[0].global_position))
		var where: String = "%s: the first-run route passes %.1f m from the egg" % [level.id, nearest]
		assert_gt(nearest, OFF_ROUTE, where)
	assert_gt(checked, 0, "a campaign level is built: run `just build-levels`")
