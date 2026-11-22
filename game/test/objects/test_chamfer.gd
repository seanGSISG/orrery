extends GutTest
## Chamfer.box(): a box mesh of the given size whose edges are cut by flat chamfers.

const SIZE: Vector3 = Vector3(0.5, 0.14, 0.4)


## The mesh fills the box and no more, and no point of it is on an edge of the box: each edge
## is cut. 26 faces: 6 sides and 12 chamfers of two triangles, and 8 corner triangles.
func test_box_fills_its_size_with_every_edge_cut() -> void:
	var mesh: ArrayMesh = Chamfer.box(SIZE)
	var bounds: AABB = mesh.get_aabb()
	assert_true(bounds.is_equal_approx(AABB(-SIZE / 2.0, SIZE)), "the box's size, centred")
	var points: PackedVector3Array = mesh.get_faces()
	assert_eq(points.size(), (6 * 2 + 12 * 2 + 8) * 3)
	var on_edge: int = 0
	for point: Vector3 in points:
		var outside: int = 0
		for axis: int in 3:
			if is_equal_approx(absf(point[axis]), SIZE[axis] / 2.0):
				outside += 1
		if outside > 1:
			on_edge += 1
	assert_eq(on_edge, 0, "no point on an edge of the box")


## Every triangle faces out, with its normal, and is clockwise seen from outside (Godot's front
## faces), so the renderer culls none of them.
func test_box_faces_out() -> void:
	var arrays: Array = Chamfer.box(SIZE).surface_get_arrays(0)
	var points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	for i: int in range(0, points.size(), 3):
		var a: Vector3 = points[i]
		var turn: Vector3 = (points[i + 1] - a).cross(points[i + 2] - a)
		var middle: Vector3 = (a + points[i + 1] + points[i + 2]) / 3.0
		assert_gt(normals[i].dot(middle), 0.0, "the triangle at %d faces out" % i)
		assert_lt(turn.dot(normals[i]), 0.0, "the triangle at %d is clockwise from outside" % i)
