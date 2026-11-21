extends AscentTest
## Ascent in the menus and the HUD, with the controller: the Ascent menu from the title, the
## height meter, the pause menu of a climb and the stats screen at the gate. The climb is the
## fixture climb (levels/test/ascent_fixture_<n>.py).


func before_each() -> void:
	super()
	ui.ascent.zones = Ascent.FIXTURE


## Ascent is open from the start: with a new save, A on Ascent opens its menu and A on New
## climb starts the climb at the bottom. B in the menu goes back to the title.
func test_ascent_is_open_from_the_start() -> void:
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"ascent")
	assert_false(ui.ascent.continue_item.visible, "nothing to continue yet")
	tap_button(JOY_BUTTON_B)
	assert_eq(shown(), &"title")
	Game.screen = &"ascent"
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"play")
	assert_eq(Game.snapshot().level, Ascent.ID)
	assert_almost_eq(Game.snapshot().height, 0.0, 0.01)


## After a quit, Continue is the first item, and it goes on at the saved spot.
func test_continue_goes_on_at_the_spot() -> void:
	if not climb():
		return
	put(ZONE_2)
	quit_climb()
	assert_eq(shown(), &"ascent")
	assert_true(ui.ascent.continue_item.visible)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"play")
	assert_almost_eq(Game.snapshot().height, 12.0, 0.01)


## New climb, the item below Continue, starts at the bottom though a spot is saved.
func test_new_climb_starts_at_the_bottom() -> void:
	if not climb():
		return
	put(ZONE_2)
	quit_climb()
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"play")
	assert_almost_eq(Game.snapshot().height, 0.0, 0.01)


## The Assist item turns Assist on and saves it; the next climb has the checkpoints.
func test_assist_item_turns_assist_on() -> void:
	Game.screen = &"ascent"
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"ascent", "the item does not leave the menu")
	var saved: SaveGame = SaveGame.new()
	saved.dir = ROOT
	saved.read()
	autofree(saved)
	assert_true(saved.ascent.assist)
	tap_button(JOY_BUTTON_DPAD_UP)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"play")
	assert_true(Ascent.of(Game.run).assisted)
	assert_not_null(Game.run.level.find_child("assist_2", true, false))


## In a climb the HUD shows the height meter and the clock, and no gems.
func test_hud_shows_the_height_meter_in_a_climb() -> void:
	if not climb():
		return
	put(ZONE_2 + Vector3(0, -8, 2.7))
	await wait_process_frames(2)
	var meter: HeightMeter = ui.hud.height_meter
	assert_true(meter.is_visible_in_tree())
	assert_eq(meter.height.large + meter.height.small, "14 m", "cut to whole metres")
	assert_false(ui.hud.gems.is_visible_in_tree(), "a climb has no gems")
	assert_true(ui.hud.time.is_visible_in_tree())


## A level has no height meter.
func test_level_has_no_height_meter() -> void:
	if not climb():
		return
	await wait_process_frames(2)
	start_level(&"rules")
	await wait_process_frames(2)
	assert_false(ui.hud.height_meter.is_visible_in_tree())
	assert_true(ui.hud.gems.is_visible_in_tree())


## The `restart` button does not restart a climb: a long climb is not lost to one press.
func test_restart_button_does_not_restart_a_climb() -> void:
	if not climb():
		return
	put(ZONE_2)
	hold(0.5)
	var tick: int = run.state.tick
	tap_button(JOY_BUTTON_BACK)
	tap_button(JOY_BUTTON_START)
	tap_button(JOY_BUTTON_BACK)
	assert_eq(shown(), &"pause")
	assert_eq(run.state.tick, tick)
	assert_almost_eq(run.state.height, 12.0, 0.01)


## The pause menu of a climb has Resume, Settings and Save and quit. Save and quit ends the
## run, saves the spot and opens the Ascent menu.
func test_pause_menu_saves_and_quits() -> void:
	if not climb():
		return
	put(ZONE_2)
	tap_button(JOY_BUTTON_START)
	assert_eq(shown(), &"pause")
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"ascent")
	assert_null(Game.run)
	assert_false(get_tree().paused)
	assert_true(Save.ascent.has_spot)
	assert_almost_eq(Save.ascent.spot_height, 12.0, 0.01)


## The gate shows the stats of the climb: its time, its falls and the metres fallen. The
## first climb to the gate is a new record. A on Done opens the Ascent menu.
func test_gate_shows_the_stats() -> void:
	if not climb():
		return
	run.step(roll(Vector2(0, 1)))
	fall_from_landing()
	put(GATE)
	await wait_process_frames(2)
	assert_eq(shown(), &"ascent_stats")
	var stats: AscentStatsScreen = ui.ascent_stats
	assert_eq(stats.time.text, TimeText.full(run.state.timer))
	assert_eq(stats.falls.text, "1")
	assert_eq(stats.fallen.text, "16 m")
	assert_true(stats.new_record)
	assert_false(stats.assist_line.visible, "no Assist in this climb")
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"ascent")
	assert_null(Game.run)
	assert_false(ui.ascent.continue_item.visible, "a finished climb has no spot")


## The stats mark a climb that used Assist, and a slower climb is no new record.
func test_stats_mark_an_assisted_climb() -> void:
	Save.finish(Ascent.ID, 0.001, &"none", null)
	Save.ascent.assist = true
	if not climb():
		return
	run.step(roll(Vector2(0, 1)))
	put(GATE)
	await wait_process_frames(2)
	assert_eq(shown(), &"ascent_stats")
	assert_true(ui.ascent_stats.assist_line.visible)
	assert_false(ui.ascent_stats.new_record)
