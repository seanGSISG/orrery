class_name PadLook
extends Object
## The look of a pad on the floor: the checkpoint and the finish. A round plate of the kit's
## stone in a bevelled rim of the kit's brass, with a glass lens in the middle that shows the
## pad's colour, dim while the pad is off and glowing while it is on. The plate stands a few
## centimetres proud of the floor, so it reads as a raised pad and not as a hole. It does not
## collide: the marble rolls on the floor under it.
##
##     var pad: MeshInstance3D = $Mesh
##     pad.mesh = PadLook.mesh(1.0)
##     PadLook.dress(pad, lens_material)

## The surfaces of mesh(), in order.
enum Part { RIM, STONE, LENS }

## Heights above the floor, m: the top of the rim, the stone and the lens.
const RIM_TOP: float = 0.045
const STONE_TOP: float = 0.028
const LENS_TOP: float = 0.04
## Radii as shares of the pad's radius: the top of the rim's outer bevel, the inner edge of the
## rim, the top of the lens, and its foot on the stone.
const RIM_OUTER: float = 0.96
const RIM_INNER: float = 0.84
const LENS: float = 0.42
const LENS_FOOT: float = 0.47
## Round sides of the mesh.
const SIDES: int = 48
## The plate's stone against the kit limestone: a little lighter, and smoother.
const STONE_SHADE: float = 1.12
const STONE_ROUGHNESS: float = 0.7

## The plate's stone of every pad; stone() makes it once.
static var _stone: ShaderMaterial = null


## Returns the pad mesh of `radius` m with one surface for each Part, its bottom on the floor.
static func mesh(radius: float) -> ArrayMesh:
	var r: float = radius
	var profiles: Array[PackedVector2Array] = [
		# Rim: up the outer bevel, across the top, down the inner bevel to the stone.
		PackedVector2Array(
			[
				Vector2(r, 0.0),
				Vector2(r, 0.012),
				Vector2(RIM_OUTER * r, RIM_TOP),
				Vector2((RIM_INNER + 0.04) * r, RIM_TOP),
				Vector2(RIM_INNER * r, STONE_TOP),
			]
		),
		# Stone: flat from the rim to the lens.
		PackedVector2Array(
			[Vector2(RIM_INNER * r, STONE_TOP), Vector2(LENS_FOOT * r, STONE_TOP)]
		),
		# Lens: a sloped glass edge up from the stone, then a low dome.
		PackedVector2Array(
			[
				Vector2(LENS_FOOT * r, STONE_TOP),
				Vector2(LENS * r, LENS_TOP),
				Vector2(0.5 * LENS * r, LENS_TOP + 0.006),
				Vector2(0.0, LENS_TOP + 0.008),
			]
		),
	]
	var out: ArrayMesh = ArrayMesh.new()
	for profile: PackedVector2Array in profiles:
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, _revolve(profile))
	return out


## Gives the pad its materials: the kit brass on the rim, the plate's stone, and lens.
static func dress(pad: MeshInstance3D, lens: Material) -> void:
	pad.set_surface_override_material(Part.RIM, KitMaterials.find("brass"))
	pad.set_surface_override_material(Part.STONE, stone())
	pad.set_surface_override_material(Part.LENS, lens)


## Returns a lens material of colour: clear coloured glass, glowing when lit.
static func lens(colour: Color, lit: bool, glow: float) -> StandardMaterial3D:
	var glass: StandardMaterial3D = StandardMaterial3D.new()
	glass.roughness = 0.12
	glass.clearcoat_enabled = true
	glass.clearcoat = 1.0
	light(glass, colour, lit, glow)
	return glass


## Shows lens lit, glowing `glow` times its colour, or off: the colour, paler and not glowing.
static func light(glass: StandardMaterial3D, colour: Color, lit: bool, glow: float) -> void:
	glass.albedo_color = colour if lit else colour.lerp(Color(0.62, 0.64, 0.62), 0.55)
	glass.emission_enabled = lit
	glass.emission = colour
	glass.emission_energy_multiplier = glow


## Returns the plate's stone: a copy of the kit limestone, a little lighter and smoother, with
## no paving, so the joints of the floor do not run across a pad.
static func stone() -> ShaderMaterial:
	if _stone == null:
		var plate: ShaderMaterial = KitMaterials.find("limestone").duplicate() as ShaderMaterial
		var tint: Vector3 = plate.get_shader_parameter("tint")
		plate.set_shader_parameter("tint", tint * STONE_SHADE)
		plate.set_shader_parameter("roughness_scale", STONE_ROUGHNESS)
		plate.set_shader_parameter("slab_size", Vector2.ZERO)
		_stone = plate
	return _stone


## Returns the arrays of the surface that the profile (radius, height) makes when it turns
## round the vertical axis. Each point of the profile is at the same radius as the point
## before it or nearer the axis, so the surface faces out and up. A point on the axis closes
## the surface in a tip.
static func _revolve(profile: PackedVector2Array) -> Array:
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i: int in profile.size() - 1:
		var a: Vector2 = profile[i]
		var b: Vector2 = profile[i + 1]
		# The normal of the segment from a to b in the (radius, height) plane, out and up.
		var side: Vector2 = Vector2(b.y - a.y, a.x - b.x).normalized()
		for k: int in SIDES:
			var turn: Array[float] = [TAU * k / SIDES, TAU * (k + 1) / SIDES]
			var corners: Array[Vector3] = []
			var normals: Array[Vector3] = []
			for angle: float in turn:
				var out: Vector3 = Vector3(cos(angle), 0.0, sin(angle))
				var normal: Vector3 = (out * side.x + Vector3.UP * side.y).normalized()
				corners.append_array([out * a.x + Vector3.UP * a.y, out * b.x + Vector3.UP * b.y])
				normals.append_array([normal, normal])
			# Two triangles, clockwise seen from the side they face (Godot's front faces):
			# a0 b1 b0 and a0 a1 b1.
			for j: int in [0, 3, 1, 0, 2, 3]:
				tool.set_normal(normals[j])
				tool.add_vertex(corners[j])
	return tool.commit_to_arrays()
