class_name GemCut
extends RefCounted
## One cut of a gem (docs/style/README.md): a convex jewel, SIZE m across, made of rings around
## the vertical axis that flat facets join. Use GemCut.of(index). The cuts are built once, and
## every gem of a cut shares its mesh and its material; a gem sets its own colour and
## lightness as the instance parameters `colour` and `lightness`.
##
## Each cut has its own outline from any side, so the outline alone tells the cuts apart:
## 0 hexagon (flat at both ends), 1 double pyramid (pointed at both ends), 2 rose (pointed on
## top, flat below), 3 brilliant (flat on top, pointed below).

## The largest dimension of a gem, m.
const SIZE: float = 0.5
## The number of cuts.
const COUNT: int = 4
## The most facets that the shader reads (MAX_FACETS in gem.gdshader).
const MAX_FACETS: int = 64
const SHADER: Shader = preload("res://objects/gem/gem.gdshader")
## The number of sides of each cut.
const SIDES: Array[int] = [6, 6, 6, 12]
## The rings of each cut from top to bottom, in units of SIZE: x is the radius and y the
## height. A ring with z = 0.5 is turned by half a side; the band between it and a ring with
## z = 0 is made of triangles. A ring of radius 0 is a point. An end ring with a radius is a
## flat face.
const RINGS: Array[Array] = [
	[
		Vector3(0.26, 0.44, 0),
		Vector3(0.42, 0.32, 0),
		Vector3(0.5, 0.16, 0),
		Vector3(0.5, -0.16, 0),
		Vector3(0.42, -0.32, 0),
		Vector3(0.26, -0.44, 0),
	],
	[
		Vector3(0.0, 0.5, 0),
		Vector3(0.24, 0.19, 0),
		Vector3(0.33, 0.025, 0),
		Vector3(0.33, -0.025, 0),
		Vector3(0.24, -0.19, 0),
		Vector3(0.0, -0.5, 0),
	],
	[
		Vector3(0.0, 0.44, 0),
		Vector3(0.24, 0.26, 0.5),
		Vector3(0.42, 0.05, 0),
		Vector3(0.5, -0.22, 0.5),
		Vector3(0.5, -0.27, 0.5),
		Vector3(0.38, -0.36, 0.5),
	],
	[
		Vector3(0.28, 0.24, 0),
		Vector3(0.42, 0.17, 0),
		Vector3(0.5, 0.05, 0),
		Vector3(0.5, -0.01, 0),
		Vector3(0.3, -0.3, 0),
		Vector3(0.0, -0.58, 0),
	],
]

static var _cuts: Array[GemCut] = []

## The jewel, with its material. The origin is on the axis, at height 0 of the rings.
var mesh: ArrayMesh
## One plane per facet: xyz is the unit normal, which points out of the gem, and w is the
## distance of the plane from the origin, m.
var facets: PackedVector4Array = []
## The heights of the highest and the lowest point, m.
var top: float
var bottom: float


## Builds cut index (0 to COUNT - 1). Use of(), which builds each cut once.
func _init(index: int) -> void:
	var rings: Array[Vector3] = []
	rings.assign(RINGS[index])
	var sides: int = SIDES[index]
	top = rings[0].y * SIZE
	bottom = rings[rings.size() - 1].y * SIZE
	var inside: Vector3 = Vector3(0, (top + bottom) / 2, 0)
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for end: int in [0, rings.size() - 1]:
		var cap: Array[Vector3] = []
		for i: int in sides:
			cap.append(_corner(rings[end], i, sides))
		_facet(tool, cap, inside)
	for k: int in rings.size() - 1:
		var upper: Vector3 = rings[k]
		var lower: Vector3 = rings[k + 1]
		for i: int in sides:
			var a: Vector3 = _corner(upper, i, sides)
			var b: Vector3 = _corner(upper, i + 1, sides)
			var c: Vector3 = _corner(lower, i + 1, sides)
			var d: Vector3 = _corner(lower, i, sides)
			if is_equal_approx(upper.z, lower.z):
				_facet(tool, [a, b, c, d], inside)
			else:
				# The corner of the other ring that lies between the two corners of an edge.
				var turned: bool = lower.z > upper.z
				_facet(tool, [a, b, d if turned else c], inside)
				_facet(tool, [d, c, b if turned else a], inside)
	mesh = tool.commit()
	assert(facets.size() <= MAX_FACETS, "a gem cut has more facets than the shader reads")
	var look: ShaderMaterial = ShaderMaterial.new()
	look.shader = SHADER
	look.set_shader_parameter(&"facets", facets)
	# Never more than the shader's array holds, also where assert() does not run.
	look.set_shader_parameter(&"facet_count", mini(facets.size(), MAX_FACETS))
	mesh.surface_set_material(0, look)


## Returns cut index (any integer; it wraps to 0 to COUNT - 1).
static func of(index: int) -> GemCut:
	if _cuts.is_empty():
		for i: int in COUNT:
			_cuts.append(GemCut.new(i))
	return _cuts[posmod(index, COUNT)]


## Returns corner i of a ring, m.
static func _corner(ring: Vector3, i: int, sides: int) -> Vector3:
	var angle: float = TAU * (i + ring.z) / sides
	return Vector3(cos(angle) * ring.x, ring.y, sin(angle) * ring.x) * SIZE


## Adds one flat facet with one normal, and its plane. corners is a convex polygon in either
## turn direction; corners that are the same point count once, and a polygon with less than
## three points is no facet. inside is a point inside the gem.
func _facet(tool: SurfaceTool, corners: Array[Vector3], inside: Vector3) -> void:
	var ring: Array[Vector3] = []
	for corner: Vector3 in corners:
		if ring.is_empty() or not (corner.is_equal_approx(ring[-1]) or corner.is_equal_approx(ring[0])):
			ring.append(corner)
	if ring.size() < 3:
		return
	var normal: Vector3 = (ring[2] - ring[0]).cross(ring[1] - ring[0]).normalized()
	# Front faces turn clockwise seen from outside (F6 in docs/design/core-runtime.md).
	if normal.dot(ring[0] - inside) < 0.0:
		ring.reverse()
		normal = -normal
	facets.append(Vector4(normal.x, normal.y, normal.z, normal.dot(ring[0])))
	tool.set_normal(normal)
	for i: int in range(1, ring.size() - 1):
		tool.add_vertex(ring[0])
		tool.add_vertex(ring[i])
		tool.add_vertex(ring[i + 1])
