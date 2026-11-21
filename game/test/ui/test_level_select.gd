extends UiTest
## The level select: tiers, saved progress, locked levels and levels with no scene, and the
## way into a level with the controller alone. The catalogue of the tests has the campaign
## and a tier of two test levels and one level that does not exist.

const MISSING: StringName = &"no_such_level"


func before_each() -> void:
	super()
	var catalog: LevelCatalog = LevelCatalog.new()
	for tier: StringName in Campaign.TIERS:
		catalog.add_tier(tier, Campaign.levels(tier))
	catalog.add_tier(LevelCatalog.TEST_TIER, [&"flat", &"rules", MISSING])
	ui.level_select.catalog = catalog


## RB changes to the next tier; the D-pad moves along the ring; A plays the level.
func test_pad_plays_a_level() -> void:
	tap_button(JOY_BUTTON_A)
	tap_button(JOY_BUTTON_RIGHT_SHOULDER)
	assert_eq(ui.level_select.tier, LevelCatalog.TEST_TIER)
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"play")
	assert_eq(Game.snapshot().level, &"rules")


## E changes the tier, Right moves along the ring and Enter plays, as on the pad.
func test_keyboard_plays_a_level() -> void:
	tap_key(KEY_ENTER)
	tap_key(KEY_E)
	tap_key(KEY_RIGHT)
	tap_key(KEY_ENTER)
	assert_eq(Game.snapshot().level, &"rules")


## A level after one that is not qualified is locked, and A does not play it.
func test_locked_level_does_not_play() -> void:
	var second: StringName = Campaign.levels(&"beginner")[1]
	tap_button(JOY_BUTTON_A)
	assert_eq(ui.level_select.map.node_of(second).state, &"locked")
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"level_select")


## A level with no scene shows as not built, and A does not play it.
func test_level_with_no_scene_does_not_play() -> void:
	tap_button(JOY_BUTTON_A)
	tap_button(JOY_BUTTON_RIGHT_SHOULDER)
	assert_eq(ui.level_select.map.node_of(MISSING).state, &"unbuilt")
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"level_select")


## The mark of a level shows its saved medal and egg, and the level select opens on the first
## level that is not qualified yet.
func test_shows_saved_progress() -> void:
	Save.finish(&"flat", 8.0, &"gold", null)
	Save.find_egg(&"flat")
	tap_button(JOY_BUTTON_A)
	tap_button(JOY_BUTTON_RIGHT_SHOULDER)
	var mark: LevelNode = ui.level_select.map.node_of(&"flat")
	assert_eq(mark.medal, &"gold")
	assert_true(mark.egg)
	assert_true(ui.level_select.map.node_of(&"rules").has_focus(), "the next level to beat")


## After a level, the level select opens on that level.
func test_reopens_on_the_level_played_last() -> void:
	start_level(&"rules")
	Game.screen = &"level_select"
	assert_eq(ui.level_select.tier, LevelCatalog.TEST_TIER)
	assert_true(ui.level_select.map.node_of(&"rules").has_focus())
