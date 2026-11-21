class_name GraphicsPreset
extends Resource
## One graphics preset: a row of the preset table in docs/design/visual-quality.md §2. The
## four presets are res://settings/presets/<name>.tres. The Graphics autoload applies the
## current one; call apply() yourself only for a viewport that is not the game window.
##
## A preset changes only real-time cost. The level's environment keeps its sky, fog, tonemap
## and exposure. Not here yet: SDFGI (Ascent and Planetarium only), the marble reflection
## probe and the lower distance fog under volumetric fog. They come with #23 and #24.

@export_group("Viewport")
@export var screen_space_aa: Viewport.ScreenSpaceAA = Viewport.SCREEN_SPACE_AA_DISABLED
@export var msaa_3d: Viewport.MSAA = Viewport.MSAA_DISABLED
@export var scaling_3d_mode: Viewport.Scaling3DMode = Viewport.SCALING_3D_MODE_BILINEAR
## 0 is the sharpest. Used only by the FSR scaling modes.
@export var fsr_sharpness: float = 0.2
@export var texture_mipmap_bias: float = 0.0
@export var anisotropic_filtering_level: Viewport.AnisotropicFiltering = (
	Viewport.ANISOTROPY_16X
)
@export var positional_shadow_atlas_size: int = 2048
## Pixels; higher is coarser.
@export var mesh_lod_threshold: float = 1.0

@export_group("Environment")
@export var glow: bool = false
@export var ssao: bool = false
@export var ssao_quality: RenderingServer.EnvironmentSSAOQuality = (
	RenderingServer.ENV_SSAO_QUALITY_MEDIUM
)
@export var ssao_half_size: bool = true
@export var ssil: bool = false
@export var ssil_quality: RenderingServer.EnvironmentSSILQuality = (
	RenderingServer.ENV_SSIL_QUALITY_MEDIUM
)
@export var ssr: bool = false
@export var ssr_half_size: bool = true
@export var volumetric_fog: bool = false
## Froxels across; the depth stays at the engine default of 64.
@export var volumetric_fog_size: int = 64

@export_group("Sun and lightmaps")
@export var sun_shadow_atlas_size: int = 4096
@export var sun_shadow_filter: RenderingServer.ShadowQuality = (
	RenderingServer.SHADOW_QUALITY_SOFT_LOW
)
@export var sun_shadow_mode: DirectionalLight3D.ShadowMode = (
	DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
)
@export var sun_shadow_distance: float = 80.0
## Degrees. Above 0 the sun casts soft PCSS shadows.
@export var sun_angular_size: float = 0.0
@export var lightmap_bicubic: bool = true


## Writes the preset to viewport, to the environment of its world and to every
## DirectionalLight3D under it, and sets the renderer-wide values.
func apply(viewport: Viewport) -> void:
	viewport.screen_space_aa = screen_space_aa
	viewport.msaa_3d = msaa_3d
	viewport.scaling_3d_mode = scaling_3d_mode
	viewport.scaling_3d_scale = 1.0
	viewport.fsr_sharpness = fsr_sharpness
	viewport.texture_mipmap_bias = texture_mipmap_bias
	viewport.anisotropic_filtering_level = anisotropic_filtering_level
	viewport.positional_shadow_atlas_size = positional_shadow_atlas_size
	viewport.mesh_lod_threshold = mesh_lod_threshold
	viewport.use_debanding = true
	RenderingServer.screen_space_roughness_limiter_set_active(true, 0.25, 0.18)
	RenderingServer.environment_set_ssao_quality(ssao_quality, ssao_half_size, 0.5, 2, 50.0, 300.0)
	RenderingServer.environment_set_ssil_quality(ssil_quality, true, 0.5, 4, 50.0, 300.0)
	RenderingServer.environment_set_ssr_half_size(ssr_half_size)
	RenderingServer.environment_set_volumetric_fog_volume_size(volumetric_fog_size, 64)
	RenderingServer.directional_shadow_atlas_set_size(sun_shadow_atlas_size, true)
	RenderingServer.directional_soft_shadow_filter_set_quality(sun_shadow_filter)
	RenderingServer.lightmaps_set_bicubic_filter(lightmap_bicubic)
	var world: World3D = viewport.find_world_3d()
	if world != null and world.environment != null:
		_apply_environment(world.environment)
	for node: Node in viewport.find_children("*", "DirectionalLight3D", true, false):
		var sun: DirectionalLight3D = node as DirectionalLight3D
		sun.directional_shadow_mode = sun_shadow_mode
		sun.directional_shadow_max_distance = sun_shadow_distance
		sun.light_angular_distance = sun_angular_size


## Turns the environment's real-time effects on or off.
func _apply_environment(environment: Environment) -> void:
	environment.glow_enabled = glow
	environment.ssao_enabled = ssao
	environment.ssil_enabled = ssil
	environment.ssr_enabled = ssr
	environment.volumetric_fog_enabled = volumetric_fog
