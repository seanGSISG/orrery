extends UiTest
## The results screen: it shows when the run finishes, locks the marble, tells a new record
## from the best time before the run, and goes on to the next level, a retry or the level
## select with the controller alone.


func before_each() -> void:
	super()
	var catalog: LevelCatalog = LevelCatalog.new()
	catalog.add_tier(LevelCatalog.TEST_TIER, [&"rules", &"flat"])
	ui.level_select.catalog = catalog


## A finished run shows the results. The marble stays still on the finish, and a run that
## steps itself stops, so player input no longer moves the marble.
func test_finish_shows_results() -> void:
	var run: LevelRun = Game.load_level(&"rules")
	finish_run(run)
	await wait_process_frames(2)
	assert_eq(shown(), &"results")
	assert_eq(run.state.velocity, Vector3.ZERO)
	assert_false(run.auto_step, "the run stops")


## The first finish of a level is a new record.
func test_first_finish_is_a_new_record() -> void:
	finish_run(start_level(&"rules"))
	await wait_process_frames(2)
	assert_true(ui.results.new_record)


## A finish that is slower than the saved best time is not a new record.
func test_slower_finish_is_no_record() -> void:
	Save.finish(&"rules", 0.001, &"gold", null)
	finish_run(start_level(&"rules"))
	await wait_process_frames(2)
	assert_false(ui.results.new_record)


## A level that loads over another level, with no change of screen, compares with its own
## best time, also when it finishes before the next frame (as a harness run can).
func test_record_is_of_the_level_that_finished() -> void:
	Save.finish(&"rules", 0.001, &"gold", null)
	start_level(&"flat")
	finish_run(start_level(&"rules"))
	await wait_process_frames(2)
	assert_false(ui.results.new_record)


## A level with two eggs shows how many of them are found: one in the first run, and both
## in a later run that finds the other one.
func test_two_eggs_show_a_count() -> void:
	var level: Level = Game.make_level(&"rules")
	var second: Egg = (load(Level.EGG_SCENE) as PackedScene).instantiate() as Egg
	second.name = &"Egg2"
	second.position = Vector3(6, 0, -10)
	level.add_child(second)
	var run: LevelRun = Game.play(level)
	run.auto_step = false
	step_run(run, 1)
	run.teleport(run.spawn_point(second), Vector3.ZERO)
	run.step(MarbleInput.new())
	finish_run(run)
	await wait_process_frames(2)
	assert_eq(ui.results.egg.text, "1/2")
	run.restart()
	await wait_process_frames(2)
	step_run(run, 1)
	run.teleport(run.spawn_point(run.find_child("Egg", true, false) as LevelObject), Vector3.ZERO)
	run.step(MarbleInput.new())
	finish_run(run)
	await wait_process_frames(2)
	assert_eq(ui.results.egg.text, "2/2", "the egg of the first run is in the save")


## A on Next plays the level after this one.
func test_pad_plays_next_level() -> void:
	finish_run(start_level(&"rules"))
	await wait_process_frames(2)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"play")
	assert_eq(Game.snapshot().level, &"flat")


## View retries: the same level starts again, and a run that stepped itself does so again.
func test_pad_retries() -> void:
	var run: LevelRun = Game.load_level(&"rules")
	finish_run(run)
	await wait_process_frames(2)
	tap_button(JOY_BUTTON_BACK)
	assert_eq(shown(), &"play")
	assert_eq(run.state.status, &"playing")
	assert_eq(run.state.tick, 0)
	assert_true(run.auto_step, "the run steps itself again")


## B goes to the level select and ends the run.
func test_pad_goes_to_level_select() -> void:
	finish_run(start_level(&"rules"))
	await wait_process_frames(2)
	tap_button(JOY_BUTTON_B)
	assert_eq(shown(), &"level_select")
	assert_null(Game.run)
