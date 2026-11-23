class_name Chamfer
extends Object
## Box meshes with chamfered edges, for the brass parts that objects build in code (the kit cuts
## its own in kit/masonry.py). A chamfer is a narrow face across an edge. It catches a highlight
## where a sharp edge shows none, so a brass box reads as cast metal and not as a sawn block.
## Only the look changes: keep the object's box collider.
##
##     look.mesh = Chamfer.box(Vector3(0.5, 0.5, 0.4))

## The width of a chamfer on each face it cuts, as the kit's EDGE_BEVEL, m.
const BEVEL: float = 0.02


## Returns a box mesh of `size`, centred on the origin, with each of its twelve edges cut by a
## flat chamfer `bevel` m wide on each face. The bevel is at most a quarter of the smallest
## side. The faces have flat normals and no UV: the kit shader maps a piece from its sides.
static func box(size: Vector3, bevel: float = BEVEL) -> ArrayMesh:
	var cut: float = minf(bevel, minf(size.x, minf(size.y, size.z)) / 4.0)
	var inner: Vector3 = size / 2.0 - Vector3.ONE * cut
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	# One face for each way out of the box: through a side (6), an edge (12) or a corner (8).
	for x: int in [-1, 0, 1]:
		for y: int in [-1, 0, 1]:
			for z: int in [-1, 0, 1]:
				if x != 0 or y != 0 or z != 0:
					_face(tool, Vector3(x, y, z), inner, cut)
	var out: ArrayMesh = ArrayMesh.new()
	out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, tool.commit_to_arrays())
	return out


## Adds the face of the chamfered box that faces `way`, one of the 26 directions with parts -1,
## 0 and 1. Its points are next to the box's corners on that side: from each corner of the
## `inner` box, `cut` m out along each axis of `way`.
static func _face(tool: SurfaceTool, way: Vector3, inner: Vector3, cut: float) -> void:
	var points: Array[Vector3] = []
	for corner: int in 8:
		var side: Vector3 = Vector3(corner & 1, (corner >> 1) & 1, (corner >> 2) & 1) * 2.0
		side -= Vector3.ONE
		var on_side: bool = true
		for axis: int in 3:
			on_side = on_side and (way[axis] == 0.0 or side[axis] == way[axis])
		if not on_side:
			continue
		for axis: int in 3:
			if way[axis] != 0.0:
				var point: Vector3 = side * inner
				point[axis] += side[axis] * cut
				points.append(point)
	# Sort the points round the face's middle, clockwise seen from outside (Godot's front
	# faces), and fan them into triangles.
	var normal: Vector3 = way.normalized()
	var middle: Vector3 = Vector3.ZERO
	for point: Vector3 in points:
		middle += point / points.size()
	var across: Vector3 = (points[0] - middle).normalized()
	var up: Vector3 = normal.cross(across)
	points.sort_custom(
		func(a: Vector3, b: Vector3) -> bool:
			return (
				atan2((a - middle).dot(up), (a - middle).dot(across))
				> atan2((b - middle).dot(up), (b - middle).dot(across))
			)
	)
	for i: int in range(1, points.size() - 1):
		for point: Vector3 in [points[0], points[i], points[i + 1]]:
			tool.set_normal(normal)
			tool.add_vertex(point)
