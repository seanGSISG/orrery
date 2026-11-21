extends UiTest
## The HUD: it shows the timer, the gems and the held power-up of the run on the play screen.


## The HUD shows on the play screen only.
func test_shows_on_play_screen_only() -> void:
	assert_false(ui.hud.visible, "title")
	start_level(&"rules")
	assert_true(ui.hud.visible, "play")
	tap_button(JOY_BUTTON_START)
	assert_false(ui.hud.visible, "pause")


## The timer shows the level clock as minutes, seconds and hundredths.
func test_shows_timer() -> void:
	var run: LevelRun = start_level(&"rules")
	step_run(run, 150)
	await wait_process_frames(2)
	assert_eq(ui.hud.time.large + ui.hud.time.small, TimeText.full(run.state.timer))
	assert_eq(ui.hud.time.large + ui.hud.time.small, "0:01.25")


## The gems readout shows the gems collected out of the total.
func test_shows_gems() -> void:
	var run: LevelRun = start_level(&"rules")
	step_run(run, 1)
	var gem: LevelObject = run.find_child("GemWest", true, false) as LevelObject
	run.teleport(run.spawn_point(gem), Vector3.ZERO)
	run.step(MarbleInput.new())
	await wait_process_frames(2)
	assert_eq(ui.hud.gems.large + ui.hud.gems.small, "1/2")


## The slot shows the held power-up, and nothing after its use.
func test_shows_held_power_up() -> void:
	var run: LevelRun = start_level(&"rules")
	await wait_process_frames(2)
	assert_eq(ui.hud.power_up.icon, &"")
	run.slot.take(CoilSpringPowerUp.new(20.0))
	await wait_process_frames(2)
	assert_eq(ui.hud.power_up.icon, &"coil_spring")


## A screenshot from a camera of the level has no HUD: it shows through the follow camera
## only.
func test_hides_for_another_camera() -> void:
	start_level(&"rules")
	var shot: Camera3D = Camera3D.new()
	add_child_autofree(shot)
	shot.make_current()
	await wait_process_frames(2)
	assert_false(ui.hud.visible)
