extends GutTest
## The Graphics autoload applies the preset that orrery/graphics/preset names
## (docs/design/visual-quality.md §2), at once and to environments that load later.


func after_each() -> void:
	Graphics.use("medium")


## use() sets the game window's values and the effects of an environment that enters later.
func test_use_applies_the_preset_to_the_window_and_a_new_environment() -> void:
	assert_true(Graphics.use("high"))
	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = Environment.new()
	add_child_autofree(world)
	await wait_process_frames(2)
	assert_eq(get_viewport().scaling_3d_mode, Viewport.SCALING_3D_MODE_FSR2)
	assert_true(world.environment.ssao_enabled)
	assert_true(world.environment.volumetric_fog_enabled)


## A preset change right after an environment enters wins over the apply that the entry queued.
func test_a_preset_change_after_a_new_environment_stays() -> void:
	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = Environment.new()
	add_child_autofree(world)
	Graphics.use("ultra")
	await wait_process_frames(2)
	assert_true(world.environment.ssil_enabled)


## A change of the project setting, as the harness `set_setting` makes it, applies the preset.
func test_a_setting_change_applies_the_preset() -> void:
	ProjectSettings.set_setting(Graphics.SETTING, "low")
	await wait_process_frames(2)
	assert_eq(Graphics.current, "low")
	assert_eq(get_viewport().screen_space_aa, Viewport.SCREEN_SPACE_AA_FXAA)
	assert_eq(get_viewport().msaa_3d, Viewport.MSAA_DISABLED)
