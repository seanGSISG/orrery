class_name BlobShadow
extends Decal
## A crisp round shadow straight down under the marble (docs/plan.md §2.11), in addition to
## the sun's shadow, so the player can judge where a jump lands. Call place() once per tick.
## A thin cast finds the first Solid below; the decal box reaches from the marble centre to
## just below that Solid, so the shadow falls on that surface and not on surfaces further
## down. Walls and the underside of the marble face away from the projection, so normal
## fading leaves them clear.

## Shadow diameter, m: a little less than the marble's 0.4 m, so the edge shows round.
const SIZE: float = 0.34
## How far down the cast looks for a surface, m. With no surface in reach, the shadow hides.
const REACH: float = 200.0
## How far past the first surface the box reaches, so that a slope under the shadow gets
## all of it, m.
const BELOW: float = 0.3
## Radius of the downward cast, m: thin, almost a ray.
const CAST_RADIUS: float = 0.01

var _world: WorldQuery


## Makes the shadow texture and settings. The shadow ignores its parent's transform.
func _init() -> void:
	top_level = true
	texture_albedo = _texture()
	upper_fade = 0.0
	lower_fade = 0.0
	normal_fade = 0.5


## Gets the space to cast in.
func _ready() -> void:
	_world = WorldQuery.new(get_world_3d().direct_space_state, CAST_RADIUS, 0.0)


## Puts the shadow on the first Solid straight down (along -up) from the marble at center.
func place(center: Vector3, up: Vector3) -> void:
	var drop: float = REACH * _world.sweep(center, -up * REACH)
	visible = drop < REACH
	var depth: float = drop + BELOW
	size = Vector3(SIZE, depth, SIZE)
	var turn: Basis = Basis(Quaternion(Vector3.UP, up))
	global_transform = Transform3D(turn, center - up * (depth * 0.5))


## A dark disc with a short soft edge, so the shadow reads as crisp.
static func _texture() -> GradientTexture2D:
	var gradient: Gradient = Gradient.new()
	gradient.offsets = PackedFloat32Array([0.0, 0.9, 1.0])
	gradient.colors = PackedColorArray([Color(0, 0, 0, 0.85), Color(0, 0, 0, 0.8), Color(0, 0, 0, 0)])
	var texture: GradientTexture2D = GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(1.0, 0.5)
	texture.width = 128
	texture.height = 128
	return texture
