extends SceneTree
## Writes res://level/test.glb: a floor, two boxes, a sphere and a torus, with colored
## materials. It stands in for a Blender-built level .glb. Run it headless:
##     godot --headless --path proj --script res://tools/make_glb.gd


func _initialize() -> void:
	var root := Node3D.new()
	root.name = "test"
	_add(root, "floor", _box(Vector3(20, 0.5, 20)), Vector3(0, -0.25, 0), Color(0.8, 0.8, 0.78))
	_add(root, "wall", _box(Vector3(0.5, 4, 12)), Vector3(-4, 2, 0), Color(0.9, 0.2, 0.15))
	_add(root, "pillar", _box(Vector3(1.5, 3, 1.5)), Vector3(2, 1.5, -2), Color(0.2, 0.5, 0.9))
	var sphere := SphereMesh.new()
	sphere.radius = 1.0
	sphere.height = 2.0
	_add(root, "ball", sphere, Vector3(1, 1, 2.5), Color(0.95, 0.8, 0.2))
	var torus := TorusMesh.new()
	torus.inner_radius = 0.6
	torus.outer_radius = 1.2
	_add(root, "ring", torus, Vector3(-1.5, 0.3, -3.5), Color(0.3, 0.85, 0.4))
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_scene(root, state)
	if err == OK:
		err = doc.write_to_filesystem(state, "res://level/test.glb")
	print("make_glb: ", error_string(err))
	root.free()
	quit(0 if err == OK else 1)


func _box(size: Vector3) -> BoxMesh:
	var box := BoxMesh.new()
	box.size = size
	return box


func _add(root: Node3D, node_name: String, mesh: PrimitiveMesh, at: Vector3, color: Color) -> void:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.8
	mesh.material = material
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.position = at
	root.add_child(instance)
	instance.owner = root
