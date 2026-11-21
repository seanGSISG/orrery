@tool
class_name SkyPreset
extends Resource
## One sky and the light that goes with it. The three tier skies are res://skies/dawn.tres
## (Beginner), noon.tres (Intermediate) and dusk.tres (Advanced). LevelConverter gives a level
## the preset that its `sky` names, or else the preset of its tier, as the nodes that
## environment() and sun() return.
##
## The panorama is a path-traced backdrop from `just bake-skies` (tools/blender/bake_skies.py).
## It holds no full-strength sun: the DirectionalLight3D is the sun. The energies already hold
## the exposure of the sky, so `exposure` stays near 1 and a glowing object looks the same
## under every sky. The graphics preset (GraphicsPreset) turns the real-time effects on.

## Equirectangular; its centre looks along +z, and its sun stands at sun_azimuth.
@export var panorama: Texture2D
## Scales the panorama on screen, in reflections and as ambient light.
@export var sky_energy: float = 1.0

@export_group("Sun")
## Degrees above the horizon.
@export var sun_elevation: float = 45.0
## Degrees counter-clockwise from the kit's +x axis, seen from above.
@export var sun_azimuth: float = 135.0
@export var sun_color: Color = Color.WHITE
@export var sun_energy: float = 1.0

@export_group("Fill")
## The share of the ambient light that comes from the panorama. The rest is fill_color, from
## every direction. A dark sky needs fill, so that shadows keep their detail. The lightmap
## bake takes the same mix.
@export_range(0.0, 1.0) var sky_share: float = 1.0
@export var fill_color: Color = Color.BLACK

@export_group("Tone and haze")
## Environment.tonemap_exposure. Auto exposure stays off.
@export var exposure: float = 1.0
## The distance-fog density, 1/m. The fog takes its colour from the sky behind it.
@export var fog_density: float = 0.001


## Returns a new Environment: the panorama as the sky, AgX tonemapping, glow for emitters
## and the sun only, and haze. The real-time effects are off until a GraphicsPreset applies.
func environment() -> Environment:
	var material: PanoramaSkyMaterial = PanoramaSkyMaterial.new()
	material.panorama = panorama
	material.energy_multiplier = sky_energy
	var sky: Sky = Sky.new()
	sky.sky_material = material
	var result: Environment = Environment.new()
	result.background_mode = Environment.BG_SKY
	result.sky = sky
	result.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	result.ambient_light_sky_contribution = sky_share
	result.ambient_light_color = fill_color
	result.tonemap_mode = Environment.TONE_MAPPER_AGX
	result.tonemap_exposure = exposure
	result.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	result.glow_intensity = 0.3
	result.glow_bloom = 0.0
	result.glow_hdr_threshold = 1.0
	# Aerial perspective: far geometry fades into the sky behind it. The sky itself stays clear.
	result.fog_enabled = true
	result.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	result.fog_density = fog_density
	result.fog_aerial_perspective = 1.0
	result.fog_sky_affect = 0.0
	# The graphics preset shares this haze between the distance fog and the volumetric fog.
	result.set_meta(GraphicsPreset.HAZE, fog_density)
	result.volumetric_fog_density = fog_density * GraphicsPreset.VOLUMETRIC_FOG_SHARE
	result.volumetric_fog_sky_affect = 0.0
	result.volumetric_fog_length = 128.0
	return result


## Returns a new sun: the one key light, with real-time shadows and baked bounce light
## (docs/design/visual-quality.md §4).
func sun() -> DirectionalLight3D:
	var result: DirectionalLight3D = DirectionalLight3D.new()
	result.light_color = sun_color
	result.light_energy = sun_energy
	result.light_bake_mode = Light3D.BAKE_DYNAMIC
	result.shadow_enabled = true
	result.directional_shadow_blend_splits = true
	result.basis = Basis.looking_at(-to_sun())
	return result


## Returns the unit vector from the level to the sun, in Godot's axes: the kit's (x, y, z)
## is Godot's (x, z, -y).
func to_sun() -> Vector3:
	var azimuth: float = deg_to_rad(sun_azimuth)
	var elevation: float = deg_to_rad(sun_elevation)
	var flat: float = cos(elevation)
	return Vector3(cos(azimuth) * flat, sin(elevation), -sin(azimuth) * flat)
