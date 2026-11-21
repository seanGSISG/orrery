extends SceneTree
## Writes res://level/big.glb: a 120 m x 120 m floor and 80 boxes and spheres, a rough stand-in
## for a full level, to measure bake time and file size at 0.1 m texels.


func _initialize() -> void:
	var root := Node3D.new()
	root.name = "big"
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var floor_mesh := BoxMesh.new()
	floor_mesh.size = Vector3(120, 0.5, 120)
	_add(root, "floor", floor_mesh, Vector3(0, -0.25, 0), Color(0.8, 0.8, 0.78))
	for i in 80:
		var mesh: PrimitiveMesh
		if i % 2 == 0:
			var box := BoxMesh.new()
			box.size = Vector3(rng.randf_range(1, 6), rng.randf_range(1, 8), rng.randf_range(1, 6))
			mesh = box
		else:
			var sphere := SphereMesh.new()
			sphere.radius = rng.randf_range(0.5, 2.5)
			sphere.height = sphere.radius * 2
			mesh = sphere
		var at := Vector3(rng.randf_range(-55, 55), 2, rng.randf_range(-55, 55))
		_add(root, "prop_%02d" % i, mesh, at, Color.from_hsv(rng.randf(), 0.6, 0.9))
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_scene(root, state)
	if err == OK:
		err = doc.write_to_filesystem(state, "res://level/big.glb")
	print("make_big_glb: ", error_string(err))
	root.free()
	quit(0 if err == OK else 1)


func _add(root: Node3D, node_name: String, mesh: PrimitiveMesh, at: Vector3, color: Color) -> void:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	mesh.material = material
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.position = at
	root.add_child(instance)
	instance.owner = root
