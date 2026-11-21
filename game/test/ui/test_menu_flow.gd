extends UiTest
## The menu flow with the controller alone and with the keyboard (docs/plan.md §2.4): each
## step sends pad or key events, and the game state reports the screen.


## A new game has no level, and Game.screen is &"play" (UiTest starts each Ui so). The Ui
## shows the title, and the state reports it.
func test_starts_on_title() -> void:
	assert_eq(shown(), &"title")
	var reported: String = Game.snapshot().to_dict()["screen"]
	assert_eq(reported, "title", "the harness gets the same screen")


## The level behind the menus has no colliders in the physics space, so the marble of a
## level that loads cannot touch them.
func test_backdrop_has_no_colliders() -> void:
	await wait_process_frames(2)
	var bodies: Array[Node] = ui.find_children("*", "StaticBody3D", true, false)
	assert_gt(bodies.size(), 0, "the backdrop shows a level")
	for body: StaticBody3D in bodies:
		assert_false(PhysicsServer3D.body_get_space(body.get_rid()).is_valid(), body.name)


## A on Play opens the level select; B goes back to the title.
func test_pad_opens_level_select_and_goes_back() -> void:
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"level_select")
	tap_button(JOY_BUTTON_B)
	assert_eq(shown(), &"title")


## Enter on Play opens the level select; Esc goes back to the title.
func test_keyboard_opens_level_select_and_goes_back() -> void:
	tap_key(KEY_ENTER)
	assert_eq(shown(), &"level_select")
	tap_key(KEY_ESCAPE)
	assert_eq(shown(), &"title")


## The D-pad moves from Play to Settings, past Ascent, which is off until it has a mode. A
## opens the settings, and B returns to the title.
func test_pad_opens_settings_from_title() -> void:
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"settings")
	tap_button(JOY_BUTTON_B)
	assert_eq(shown(), &"title")


## A loaded level shows the play screen.
func test_level_shows_play_screen() -> void:
	start_level(&"rules")
	assert_eq(shown(), &"play")


## Menu pauses the level and the scene tree; Menu again resumes both. A run that its caller
## steps does not start to step itself.
func test_pad_pauses_and_resumes() -> void:
	var run: LevelRun = start_level(&"rules")
	tap_button(JOY_BUTTON_START)
	assert_eq(shown(), &"pause")
	assert_true(get_tree().paused, "paused")
	tap_button(JOY_BUTTON_START)
	assert_eq(shown(), &"play")
	assert_false(get_tree().paused, "resumed")
	assert_false(run.auto_step, "the caller still steps the run")


## Esc pauses; A on Resume, the first item, resumes.
func test_keyboard_pauses_and_resume_item_resumes() -> void:
	start_level(&"rules")
	tap_key(KEY_ESCAPE)
	assert_eq(shown(), &"pause")
	tap_key(KEY_ENTER)
	assert_eq(shown(), &"play")
	assert_false(get_tree().paused)


## View restarts the level from the pause menu: the run starts again and plays.
func test_pad_restarts_from_pause() -> void:
	var run: LevelRun = start_level(&"rules")
	step_run(run, 30)
	tap_button(JOY_BUTTON_START)
	tap_button(JOY_BUTTON_BACK)
	assert_eq(shown(), &"play")
	assert_eq(run.state.tick, 0)
	assert_false(get_tree().paused)


## Settings in the pause menu opens the settings over the paused level; B returns to the
## pause menu.
func test_pad_opens_settings_from_pause() -> void:
	start_level(&"rules")
	tap_button(JOY_BUTTON_START)
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"settings")
	assert_true(get_tree().paused, "the level stays paused")
	tap_button(JOY_BUTTON_B)
	assert_eq(shown(), &"pause")


## Levels in the pause menu ends the run and opens the level select.
func test_pad_quits_from_pause_to_level_select() -> void:
	start_level(&"rules")
	tap_button(JOY_BUTTON_START)
	for _i: int in 3:
		tap_button(JOY_BUTTON_DPAD_DOWN)
	tap_button(JOY_BUTTON_A)
	assert_eq(shown(), &"level_select")
	assert_null(Game.run)
	assert_false(get_tree().paused)


## A move of the focus plays the move sound, and a choice plays the select sound.
func test_menu_sounds_play() -> void:
	tap_button(JOY_BUTTON_DPAD_DOWN)
	assert_true(_sound(&"move").playing, "move")
	tap_button(JOY_BUTTON_DPAD_UP)
	tap_button(JOY_BUTTON_A)
	assert_true(_sound(&"select").playing, "select")
	tap_button(JOY_BUTTON_B)
	assert_true(_sound(&"back").playing, "back")


## Returns the player of the menu sound in the Music autoload.
func _sound(sound: StringName) -> AudioStreamPlayer:
	for child: Node in Music.get_children():
		var player: AudioStreamPlayer = child as AudioStreamPlayer
		if player != null and player.stream != null:
			if player.stream.resource_path == Music.UI_PATH % sound:
				return player
	return null
