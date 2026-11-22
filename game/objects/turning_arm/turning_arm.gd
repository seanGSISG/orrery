class_name TurningArm
extends Turner
## The `turning_arm` marker: a flat bar that turns at a steady speed round the marker's up axis
## (Blender z) and pushes aside a marble in its way. The bar's outline is the marker's points
## (kit.marker(points=...)): give them in order round the bar, in the marker's own plane, at
## the arm's pose at run time 0. The bar stands `height` m up from that plane, with a chamfer
## round its top edge, and its shape is the same solid as its look. The look is the kit
## material `finish` (KitMaterials), mapped in the arm's own space, so it turns with the arm.
## Turner gives the settings `period` and `clockwise` and the motion. Ascent 2's clock hands
## use it; the Clock Hands of M3 build on it (docs/plan.md §2.6).

## The chamfer round the top edge: how far it cuts into the top face and into the sides, m.
const BEVEL: float = 0.02

## Size up from the marker's plane, m.
@export var height: float = 0.25
## The kit material of the bar (KitMaterials.find), for example "brass" or "blued_steel".
@export var finish: String = "brass"


## Builds the bar from the outline, then starts the turn.
func _ready() -> void:
	var outline: PackedVector2Array = _outline()
	var triangles: PackedInt32Array = Geometry2D.triangulate_polygon(outline)
	if outline.size() < 3 or triangles.is_empty():
		push_error("turning_arm %s: the points are not the outline of a bar" % name)
	else:
		var look: MeshInstance3D = $Solid/Mesh
		look.mesh = _bar(outline, triangles)
		look.material_override = KitMaterials.find(finish)
		var shape: CollisionShape3D = $Solid/Shape
		shape.shape = look.mesh.create_trimesh_shape()
	super()


## Returns the outline from the points, in the marker's plane as (x, z), counter-clockwise in
## those axes.
func _outline() -> PackedVector2Array:
	var out: PackedVector2Array = []
	for child: Node in get_children():
		var point: Marker3D = child as Marker3D
		if point != null:
			out.append(Vector2(point.position.x, point.position.z))
	if Geometry2D.is_polygon_clockwise(out):
		out.reverse()
	return out


## Returns the bar's mesh: the bottom, the sides, the chamfer and the top, with flat normals.
## Every face is clockwise seen from outside (Godot's front faces).
func _bar(outline: PackedVector2Array, triangles: PackedInt32Array) -> ArrayMesh:
	var bevel: float = minf(BEVEL, height / 4.0)
	var inset: PackedVector2Array = _inset(outline, bevel)
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i: int in range(0, triangles.size(), 3):
		var k: PackedInt32Array = triangles.slice(i, i + 3)
		var low: Array[Vector3] = [_at(outline[k[0]], 0.0), _at(outline[k[1]], 0.0)]
		low.append(_at(outline[k[2]], 0.0))
		_face(tool, low, Vector3.DOWN)
		var high: Array[Vector3] = [_at(inset[k[0]], height), _at(inset[k[1]], height)]
		high.append(_at(inset[k[2]], height))
		_face(tool, high, Vector3.UP)
	var n: int = outline.size()
	var side: float = height - bevel
	for i: int in n:
		var j: int = (i + 1) % n
		# The outline is counter-clockwise, so the bar is on the left of each edge.
		var edge: Vector2 = outline[j] - outline[i]
		var out: Vector3 = Vector3(edge.y, 0.0, -edge.x)
		var a: Vector3 = _at(outline[i], 0.0)
		var b: Vector3 = _at(outline[j], 0.0)
		var c: Vector3 = _at(outline[j], side)
		var d: Vector3 = _at(outline[i], side)
		var e: Vector3 = _at(inset[j], height)
		var f: Vector3 = _at(inset[i], height)
		_face(tool, [a, b, c], out)
		_face(tool, [a, c, d], out)
		_face(tool, [d, c, e], out + Vector3.UP)
		_face(tool, [d, e, f], out + Vector3.UP)
	var mesh: ArrayMesh = ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, tool.commit_to_arrays())
	return mesh


## Adds one triangle with its flat normal, wound clockwise seen from the side that `out`
## points to.
func _face(tool: SurfaceTool, points: Array[Vector3], out: Vector3) -> void:
	var normal: Vector3 = (points[2] - points[0]).cross(points[1] - points[0]).normalized()
	if normal.dot(out) < 0.0:
		points = [points[0], points[2], points[1]]
		normal = -normal
	for point: Vector3 in points:
		tool.set_normal(normal)
		tool.add_vertex(point)


## Returns the point of the outline at (x, z), `up` m above the marker's plane.
func _at(point: Vector2, up: float) -> Vector3:
	return Vector3(point.x, up, point.y)


## Returns the counter-clockwise outline moved `d` m inward, with mitred corners. A sharp
## corner moves at most 5 d, so the tip of a pointed bar keeps its place.
func _inset(outline: PackedVector2Array, d: float) -> PackedVector2Array:
	var out: PackedVector2Array = []
	var n: int = outline.size()
	for i: int in n:
		var e0: Vector2 = (outline[i] - outline[i - 1]).normalized()
		var e1: Vector2 = (outline[(i + 1) % n] - outline[i]).normalized()
		var n0: Vector2 = Vector2(-e0.y, e0.x)
		var bisect: Vector2 = (n0 + Vector2(-e1.y, e1.x)).normalized()
		if bisect == Vector2.ZERO:
			bisect = n0
		out.append(outline[i] + bisect * d / maxf(0.2, bisect.dot(n0)))
	return out
