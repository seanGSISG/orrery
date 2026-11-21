extends RunTest
## The level pipeline. The fixture levels/test/fixture.py, built by `just build-levels`, plays
## through the boundary. The LevelConverter rules run on scenes built in code.

const FIXTURE: String = "res://levels/built/fixture.glb"
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The fixture's start marker, Blender (0, 2, 0), in Godot axes.
const FIXTURE_START: Vector3 = Vector3(0, 0, -2)
const FIXTURE_GEMS: int = 3


## Starts a run of the built fixture. Returns false (and fails the test) when it is not built.
func _start_fixture() -> bool:
	if not ResourceLoader.exists(FIXTURE):
		fail_test("%s is missing: run `just build-levels`" % FIXTURE)
		return false
	start_run(load(FIXTURE) as PackedScene)
	return true


## Returns a scene like an imported .glb: a root with one marker node for each data entry.
## The default markers make a test-tier level that passes the lint.
func _scene(markers: Array[Dictionary] = []) -> Node3D:
	var root: Node3D = autofree(Node3D.new())
	root.name = "scene"
	var all: Array[Dictionary] = [{"type": "level", "id": "t", "tier": "test"}]
	all.append({"type": "start"})
	all.append({"type": "finish"})
	all.append_array(markers)
	for data: Dictionary in all:
		var node: Node3D = Node3D.new()
		node.name = "%s_%d" % [data["type"], root.get_child_count()]
		node.set_meta(&"extras", {"orrery": data})
		root.add_child(node)
	return root


## Returns a mesh node named name whose material has the surface extra surface_id.
func _mesh(name: String, surface_id: String) -> MeshInstance3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.set_meta(&"extras", {"surface": surface_id})
	var box: BoxMesh = BoxMesh.new()
	box.material = material
	var node: MeshInstance3D = MeshInstance3D.new()
	node.name = name
	node.mesh = box
	return node


## Returns the errors of converting scene, which must fail.
func _errors(scene: Node3D) -> String:
	var converter: LevelConverter = LevelConverter.new()
	assert_null(converter.convert(scene))
	return "\n".join(converter.errors)


func test_fixture_spawns_the_marble_on_the_start_marker() -> void:
	if _start_fixture():
		var expected: Vector3 = FIXTURE_START + Vector3.UP * TUNING.radius
		assert_almost_eq(run.state.position, expected, Vector3.ONE * 0.001)
		assert_eq(run.state.level, &"fixture")


func test_fixture_reports_its_gem_total() -> void:
	if _start_fixture():
		assert_eq(run.state.gems_total, FIXTURE_GEMS)


## The track faces point outward, so the marble rests on top (core-runtime A4).
func test_marble_rests_on_a_built_track_piece() -> void:
	if _start_fixture():
		hold(MarbleInput.new(), 1.0)
		assert_true(run.state.on_ground)
		assert_almost_eq(run.state.position.y, TUNING.radius, 0.01)


func test_level_marker_fills_the_root_data() -> void:
	var scene: Node3D = _scene()
	var data: Dictionary = {"type": "level", "id": "t", "tier": "test", "par": 30}
	scene.get_child(0).set_meta(&"extras", {"orrery": data})
	var level: Level = LevelConverter.new().convert(scene)
	assert_eq(level.id, &"t")
	assert_eq(level.par, 30.0)
	assert_null(scene.get_node_or_null(^"level_0"))


func test_marker_becomes_its_object_with_points_in_name_order() -> void:
	var scene: Node3D = _scene([{"type": "gem"}])
	var marker: Node = scene.get_child(3)
	for point: String in ["gem_3_p01", "gem_3_p00"]:
		var child: Node3D = Node3D.new()
		child.name = point
		marker.add_child(child)
	LevelConverter.new().convert(scene)
	var gem: Node = scene.get_node(^"gem_3")
	assert_true(gem is Gem)
	var points: Array[Node] = gem.find_children("*", "Marker3D", false)
	var names: Array = points.map(func(point: Node) -> String: return point.name)
	assert_eq(names, ["gem_3_p00", "gem_3_p01"])


func test_shot_marker_becomes_a_camera_named_after_it() -> void:
	var scene: Node3D = _scene()
	var marker: Node3D = Node3D.new()
	marker.name = "overview"
	marker.position = Vector3(1, 2, 3)
	marker.set_meta(&"extras", {"orrery": {"type": "shot"}})
	scene.add_child(marker)
	LevelConverter.new().convert(scene)
	var camera: Camera3D = scene.get_node(^"overview") as Camera3D
	assert_not_null(camera)
	assert_eq(camera.position, Vector3(1, 2, 3))


func test_wrong_setting_type_fails_with_level_id_and_node_name() -> void:
	var scene: Node3D = _scene()
	var data: Dictionary = {"type": "level", "id": "t", "par": "fast"}
	scene.get_child(0).set_meta(&"extras", {"orrery": data})
	var errors: String = _errors(scene)
	assert_string_contains(errors, "level t: node level: setting `par` must be float")


func test_unknown_setting_fails() -> void:
	var errors: String = _errors(_scene([{"type": "gem", "speed": 2.0}]))
	assert_string_contains(errors, "level t: node gem_3: unknown setting `speed`")


func test_unknown_marker_type_fails() -> void:
	var errors: String = _errors(_scene([{"type": "nothing"}]))
	assert_string_contains(errors, "unknown marker type `nothing`")


## Only a level in levels/test/ may leave out the gallery shots.
func test_level_outside_the_test_tier_needs_the_gallery_shots() -> void:
	var scene: Node3D = _scene([{"type": "shot"}])
	scene.get_child(3).name = "overview"
	var data: Dictionary = {"type": "level", "id": "t", "tier": "beginner"}
	scene.get_child(0).set_meta(&"extras", {"orrery": data})
	var errors: String = _errors(scene)
	assert_string_contains(errors, "needs the gallery shot `egg`")
	assert_string_contains(errors, "needs the gallery shot `finish`")
	assert_false(errors.contains("shot `overview`"))


## A level that brings its own sun keeps it and gets no sky (test_level_look.gd has the rest).
func test_level_with_its_own_sun_gets_no_rig() -> void:
	var scene: Node3D = _scene()
	scene.add_child(DirectionalLight3D.new())
	LevelConverter.new().convert(scene)
	assert_eq(scene.find_children("*", "DirectionalLight3D", true, false).size(), 1)
	assert_eq(scene.find_children("*", "WorldEnvironment", true, false).size(), 0)


func test_level_without_a_start_fails() -> void:
	var scene: Node3D = _scene()
	scene.get_child(1).free()
	assert_string_contains(_errors(scene), "needs exactly one `start` marker, found 0")


func test_level_without_a_finish_fails() -> void:
	var scene: Node3D = _scene()
	scene.get_child(2).free()
	assert_string_contains(_errors(scene), "needs exactly one `finish` marker, found 0")


func test_collision_meshes_of_one_surface_become_one_solid() -> void:
	var scene: Node3D = _scene()
	scene.add_child(_mesh("floor-col", "default"))
	scene.add_child(_mesh("wall-colonly", "default"))
	LevelConverter.new().convert(scene)
	var solids: Array[Node] = scene.find_children("*", "StaticBody3D", false)
	assert_eq(solids.size(), 1)
	var solid: Solid = solids[0] as Solid
	assert_eq(solid.surface, Solid.DEFAULT_SURFACE)
	var shape: ConcavePolygonShape3D = (solid.get_child(0) as CollisionShape3D).shape
	assert_eq(shape.get_faces().size(), 2 * 36)
	assert_not_null(scene.get_node_or_null(^"floor"))
	assert_null(scene.get_node_or_null(^"wall-colonly"))


func test_unknown_surface_fails() -> void:
	var scene: Node3D = _scene()
	scene.add_child(_mesh("floor-col", "lava"))
	assert_string_contains(_errors(scene), "unknown surface `lava`")
