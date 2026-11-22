extends GutTest
## The Graphics autoload applies the preset that orrery/graphics/preset names
## (docs/design/visual-quality.md §2), at once and to environments that load later.

## What each preset must set, from the preset table: anti-aliasing (screen-space mode, MSAA,
## scaling mode), anisotropic level, mipmap bias, the environment effects (glow, SSAO, SSIL,
## SSR, volumetric fog) and the sun (shadow distance in m, split mode, angular size).
const TABLE: Dictionary[String, Dictionary] = {
	"low": {
		"aa": [Viewport.SCREEN_SPACE_AA_FXAA, Viewport.MSAA_DISABLED, Viewport.SCALING_3D_MODE_BILINEAR],
		"anisotropy": Viewport.ANISOTROPY_4X,
		"bias": 0.0,
		"effects": [false, false, false, false, false],
		"sun": [50.0, DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS, 0.0],
	},
	"medium": {
		"aa": [Viewport.SCREEN_SPACE_AA_DISABLED, Viewport.MSAA_2X, Viewport.SCALING_3D_MODE_BILINEAR],
		"anisotropy": Viewport.ANISOTROPY_16X,
		"bias": 0.0,
		"effects": [true, false, false, false, false],
		"sun": [80.0, DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS, 0.0],
	},
	"high": {
		"aa": [Viewport.SCREEN_SPACE_AA_DISABLED, Viewport.MSAA_DISABLED, Viewport.SCALING_3D_MODE_FSR2],
		"anisotropy": Viewport.ANISOTROPY_16X,
		"bias": -0.5,
		"effects": [true, true, false, true, true],
		"sun": [120.0, DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS, 0.0],
	},
	"ultra": {
		"aa": [Viewport.SCREEN_SPACE_AA_DISABLED, Viewport.MSAA_DISABLED, Viewport.SCALING_3D_MODE_FSR2],
		"anisotropy": Viewport.ANISOTROPY_16X,
		"bias": -0.5,
		"effects": [true, true, true, true, true],
		"sun": [160.0, DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS, 0.5],
	},
}


func after_each() -> void:
	Graphics.use("medium")


## Adds an environment with haze, as SkyPreset makes it, and returns it.
func _add_environment(haze: float) -> Environment:
	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = Environment.new()
	world.environment.set_meta(GraphicsPreset.HAZE, haze)
	add_child_autofree(world)
	return world.environment


func test_each_preset_sets_its_rendering_settings() -> void:
	var environment: Environment = _add_environment(0.002)
	var sun: DirectionalLight3D = DirectionalLight3D.new()
	add_child_autofree(sun)
	var viewport: Viewport = get_viewport()
	for preset: String in TABLE:
		var row: Dictionary = TABLE[preset]
		var want_aa: Array = row["aa"]
		var want_anisotropy: int = row["anisotropy"]
		var want_bias: float = row["bias"]
		var want_effects: Array = row["effects"]
		var want_sun: Array = row["sun"]
		assert_true(Graphics.use(preset), preset)
		await wait_process_frames(2)
		var aa: Array = [viewport.screen_space_aa, viewport.msaa_3d, viewport.scaling_3d_mode]
		assert_eq(aa, want_aa, "%s anti-aliasing" % preset)
		assert_eq(viewport.anisotropic_filtering_level, want_anisotropy, "%s anisotropy" % preset)
		assert_eq(viewport.texture_mipmap_bias, want_bias, "%s mipmap bias" % preset)
		var effects: Array = [environment.glow_enabled, environment.ssao_enabled]
		effects.append_array([environment.ssil_enabled, environment.ssr_enabled])
		effects.append(environment.volumetric_fog_enabled)
		assert_eq(effects, want_effects, "%s glow, SSAO, SSIL, SSR, volumetric fog" % preset)
		var shadow: Array = [sun.directional_shadow_max_distance, sun.directional_shadow_mode]
		shadow.append(sun.light_angular_distance)
		assert_eq(shadow, want_sun, "%s sun shadow distance, splits, angular size" % preset)


## With volumetric fog on, the distance fog gives up the volumetric share of the haze.
func test_volumetric_fog_takes_its_share_of_the_haze() -> void:
	var environment: Environment = _add_environment(0.002)
	Graphics.use("medium")
	await wait_process_frames(2)
	assert_almost_eq(environment.fog_density, 0.002, 0.000001)
	Graphics.use("high")
	await wait_process_frames(2)
	var volumetric: float = 0.002 * GraphicsPreset.VOLUMETRIC_FOG_SHARE
	assert_almost_eq(environment.volumetric_fog_density, volumetric, 0.000001)
	assert_almost_eq(environment.fog_density, 0.002 - volumetric, 0.000001)
	Graphics.use("high")
	await wait_process_frames(2)
	assert_almost_eq(environment.fog_density, 0.002 - volumetric, 0.000001, "a second apply")


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
