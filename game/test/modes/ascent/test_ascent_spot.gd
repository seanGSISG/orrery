extends AscentTest
## The Ascent mode on the fixture climb (levels/test/ascent_fixture_<n>.py): the saved spot,
## a new climb, the gate, the ghost of the best climb and the route bot. test_ascent.gd has
## the zones, the falls and the flag.


## A quit saves the exact spot with the clock and the stats, and the next start continues
## there: same place, same velocity, same clock, and the lift where it was.
func test_quit_saves_the_spot_and_the_climb_continues_there() -> void:
	if not climb():
		return
	fall_from_landing()
	# The lift is at the bottom again from 8 s: get on there, and quit while it rises.
	hold(8.2 - float(run.state.tick) / Engine.physics_ticks_per_second)
	put(LIFT)
	hold(2.5)
	var before: GameState = run.state
	var lift: Vector3 = lift().global_position
	var falls: int = ascent.falls
	var fallen: float = ascent.fallen
	assert_gt(before.velocity.length(), 0.1, "the marble moves at the quit")
	quit_climb()
	assert_null(Game.run)
	var saved: SaveGame = SaveGame.new()
	saved.dir = ROOT
	saved.read()
	autofree(saved)
	assert_true(saved.ascent.has_spot, "the spot is in the file")
	assert_eq(saved.ascent.spot_position, before.position)
	assert_eq(saved.ascent.falls, falls)
	if not climb():
		return
	assert_eq(run.state.position, before.position)
	assert_eq(run.state.velocity, before.velocity)
	assert_eq(run.state.timer, before.timer)
	assert_eq(run.state.tick, before.tick)
	assert_almost_eq(run.state.height, before.height, 0.001)
	assert_almost_eq(lift().global_position, lift, Vector3.ONE * 0.001, "the lift is where it was")
	assert_eq(ascent.falls, falls)
	assert_eq(ascent.fallen, fallen)
	hold(0.5)
	assert_almost_eq(run.state.timer, before.timer + 0.5, 0.001, "the clock runs on")


## A quit in the middle of a fall does not cut the fall in two: after the continue it is
## still one fall of its whole height.
func test_fall_with_a_quit_in_it_counts_once() -> void:
	if not climb():
		return
	put(LANDING)
	hold(1.5, roll(Vector2(0.3, 0)))
	hold(0.5)
	assert_false(run.state.on_ground, "the marble is in the air")
	assert_eq(ascent.falls, 1, "the fall started")
	quit_climb()
	if not climb():
		return
	hold(5.0)
	assert_true(run.state.on_ground)
	assert_eq(ascent.falls, 1)
	assert_almost_eq(ascent.fallen, 16.0, 0.1)


## With Assist, the continue keeps the last checkpoint that the marble reached, not the one of
## the zone that the marble is in.
func test_continue_keeps_the_last_checkpoint() -> void:
	Save.ascent.assist = true
	if not climb():
		return
	put(ZONE_2)
	# A landing of zone 3: the marble is above the start of zone 3, but was not on its pad.
	put(Vector3(22, 18, 28))
	assert_eq(run.state.checkpoint, &"assist_2")
	quit_climb()
	if not climb():
		return
	assert_eq(run.state.checkpoint, &"assist_2")
	assert_eq(ascent.zone, 2)


## A spot counts only in a climb that starts with the zones of the spot. A climb with one
## more zone on top continues; a climb of other zones starts at the bottom.
func test_spot_counts_only_in_its_zones() -> void:
	var lower: Array[StringName] = [Ascent.FIXTURE[0], Ascent.FIXTURE[1]]
	var upper: Array[StringName] = [Ascent.FIXTURE[1], Ascent.FIXTURE[2]]
	run = Ascent.start(true, lower)
	if run == null:
		fail_test("the fixture climb is not built: run `just build-levels`")
		return
	run.auto_step = false
	put(ZONE_2)
	quit_climb()
	run = Ascent.start(false, Ascent.FIXTURE)
	assert_almost_eq(run.state.height, 12.0, 0.01, "one more zone on top: the spot counts")
	quit_climb()
	run = Ascent.start(false, upper)
	assert_almost_eq(run.state.height, 0.0, 0.01, "other zones: a new climb")


## The pause saves the spot too, so a crash in the pause menu loses nothing.
func test_pause_saves_the_spot() -> void:
	if not climb():
		return
	put(ZONE_2)
	Game.screen = &"pause"
	var saved: SaveGame = SaveGame.new()
	saved.dir = ROOT
	saved.read()
	autofree(saved)
	assert_true(saved.ascent.has_spot)
	assert_almost_eq(saved.ascent.spot_position, on(ZONE_2), Vector3.ONE * 0.01)


## A new climb starts at the bottom with new stats, also when a spot is saved.
func test_new_climb_starts_at_the_bottom() -> void:
	if not climb():
		return
	fall_from_landing()
	put(ZONE_3)
	quit_climb()
	if not climb(true):
		return
	assert_almost_eq(run.state.position, on(START), Vector3.ONE * 0.01)
	assert_eq(run.state.timer, 0.0)
	assert_eq(ascent.falls, 0)
	assert_almost_eq(ascent.best_height, 24.0, 0.01, "the best height is of every climb")
	assert_true(ascent.flag.visible, "the flag of the last climb stands")


## The gate ends the run: the climb has no spot any more, and its time is the best time.
func test_gate_ends_the_run() -> void:
	if not climb():
		return
	run.step(roll(Vector2(0, 1)))
	hold(1.0)
	put(GATE)
	assert_eq(run.state.status, &"finished")
	var time: float = run.state.timer
	assert_gt(time, 1.0)
	assert_false(Save.ascent.has_spot)
	assert_eq(Save.level(Ascent.ID).best_time, time)
	quit_climb()
	assert_false(Save.ascent.has_spot, "a finished climb leaves no spot")


## The finish pads of the lower zones are gone: the marble rolls from one zone into the next.
func test_zone_finish_does_not_end_the_run() -> void:
	if not climb():
		return
	run.step(roll(Vector2(0, 1)))
	put(Vector3(4, 18, 12))
	hold(0.2)
	assert_eq(run.state.status, &"playing")


## The ghost of the best climb plays back in the next climb, also when the best climb had a
## quit in it: the recording saves with the spot.
func test_ghost_of_the_best_climb_plays_back() -> void:
	if not climb():
		return
	var path: Array[Vector3] = [run.state.position]
	for _i: int in 90:
		run.step(roll(Vector2(1, 0)))
		path.append(run.state.position)
	quit_climb()
	if not climb():
		return
	for _i: int in 90:
		run.step(roll(Vector2(1, 0)))
		path.append(run.state.position)
	put(GATE)
	assert_eq(run.state.status, &"finished")
	assert_almost_eq(Save.ghost(Ascent.ID).duration, run.state.timer, 0.0001)
	if not climb():
		return
	var tracker: RunTracker = run.get_node(^"RunTracker") as RunTracker
	run.step(roll(Vector2(0, -1)))
	assert_not_null(tracker.ghost_marble, "the ghost marble")
	for tick: int in range(2, 176):
		run.step(roll(Vector2(0, -1)))
		assert_almost_eq(tracker.ghost_marble.position, path[tick], Vector3.ONE * 0.02)
	assert_true(tracker.ghost_marble.visible)


## A restart of the run (the route bot, the harness) starts a new climb.
func test_restart_of_the_run_starts_a_new_climb() -> void:
	if not climb():
		return
	fall_from_landing()
	assert_eq(ascent.falls, 1)
	run.restart()
	run.step(MarbleInput.new())
	assert_eq(ascent.falls, 0)
	assert_eq(ascent.fallen, 0.0)
	assert_almost_eq(run.state.height, 0.0, 0.01)


## The route bot climbs the whole fixture with the first-run route of each zone in turn, from
## the climb start through the gate.
func test_route_bot_climbs_to_the_gate() -> void:
	if not climb():
		return
	var routes: Array[LevelObject] = objects(
		func(o: LevelObject) -> bool: return o is Route and (o as Route).kind == &"first_run"
	)
	assert_eq(routes.size(), 3, "one first-run route for each zone")
	for object: LevelObject in routes:
		var route: Route = object as Route
		var bot: RouteBot = RouteBot.new(run, route)
		assert_eq(bot.problems.size(), 0, route.name)
		InputHub.use_source(bot)
		while not bot.done:
			run.step(InputHub.next_input(run.state))
		assert_eq(bot.falls, 0, "no fall out of the world")
	InputHub.use_source(PlayerSource.new())
	assert_eq(run.state.status, &"finished")
	assert_eq(ascent.falls, 0)
	assert_gt(run.state.height, 35.5, "at the gate")


## Every text key of the mode has English text.
func test_gate_text_has_english() -> void:
	assert_ne(tr(AscentGate.TEXT), AscentGate.TEXT)
