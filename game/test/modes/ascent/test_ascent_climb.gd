extends AscentTest
## The route bot climbs the real Ascent zones 1 to 3 in one run (docs/design/ascent.md §8.2):
## from the climb start, the bot of each zone drives that zone's route in turn through
## MarbleInput, with no restart, and the bot of zone 3 reaches the gate. Each test takes about
## 15 s, most of it the physics of the climb.


## The expert route of each zone climbs to the gate with no fall.
func test_expert_routes_climb_to_the_gate() -> void:
	climb_to_the_gate(&"expert")


## The first-run route of each zone climbs to the gate with no fall.
func test_first_run_routes_climb_to_the_gate() -> void:
	climb_to_the_gate(&"first_run")


## Starts a new climb of Ascent.ZONES and lets a bot drive the route of kind in each zone, from
## the bottom. The bot of a lower zone comes to rest on its last point and gives up there
## ("route_end"), as the zone has no finish in the climb; the next bot starts from there.
func climb_to_the_gate(kind: StringName) -> void:
	run = Ascent.start(true, Ascent.ZONES)
	ascent = Ascent.of(run)
	if ascent == null or ascent.zone_heights.size() != Ascent.ZONES.size():
		fail_test("zones 1 to 3 are not built: run `just build-levels`")
		return
	run.auto_step = false
	var zones: Array[Node] = []
	zones.assign(run.level.get_children().filter(func(node: Node) -> bool: return node is Level))
	for i: int in zones.size():
		var zone: Node = zones[i]
		var route: Route = route_in(zone, kind)
		if route == null:
			fail_test("%s has no %s route" % [zone.name, kind])
			return
		var bot: RouteBot = RouteBot.new(run, route)
		assert_eq(bot.problems.size(), 0, route.name)
		InputHub.use_source(bot)
		while not bot.done:
			run.step(InputHub.next_input(run.state))
		var want: StringName = &"finished" if i == zones.size() - 1 else &"route_end"
		var ended: StringName = &"finished" if bot.finished else bot.reason
		assert_eq(ended, want, "%s %s" % [zone.name, kind])
		assert_eq(bot.falls, 0, "no fall out of the world in %s" % zone.name)
		if ended != want:
			break
	InputHub.use_source(PlayerSource.new())
	assert_eq(run.state.status, &"finished", "at the gate")
	assert_eq(ascent.falls, 0, "no fall in the climb")


## Returns the route of kind that the zone level holds, or null.
func route_in(zone: Node, kind: StringName) -> Route:
	for object: LevelObject in run.objects:
		var route: Route = object as Route
		if route != null and route.kind == kind and zone.is_ancestor_of(route):
			return route
	return null
