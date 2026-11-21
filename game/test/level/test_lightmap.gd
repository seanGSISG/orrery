extends GutTest
## The LightmapGI rule of LevelConverter and the bakes that `just bake` commits to
## res://levels/lightmaps/. The fixture's bake is committed, so the tests use it.

const BUILT: String = "res://levels/built/%s.glb"
const BAKES: String = "res://levels/lightmaps/"


## Returns a test-tier scene like an imported .glb with the level id id, converted.
func _converted(id: String) -> Node3D:
	var root: Node3D = autofree(Node3D.new())
	root.name = "scene"
	var markers: Array[Dictionary] = [{"type": "level", "id": id, "tier": "test"}]
	markers.append_array([{"type": "start"}, {"type": "finish"}])
	for data: Dictionary in markers:
		var node: Node3D = Node3D.new()
		node.name = str(data["type"])
		node.set_meta(&"extras", {"orrery": data})
		root.add_child(node)
	var converter: LevelConverter = LevelConverter.new()
	assert_not_null(converter.convert(root), "\n".join(converter.errors))
	return root


## Returns the one LightmapGI under root, or null (and fails the test).
func _lightmap(root: Node) -> LightmapGI:
	var found: Array[Node] = root.find_children("*", "LightmapGI", true, false)
	assert_eq(found.size(), 1, "one LightmapGI")
	return found[0] as LightmapGI if found.size() == 1 else null


func test_level_gets_a_lightmap_with_the_bake_settings() -> void:
	var lightmap: LightmapGI = _lightmap(_converted("unbaked"))
	assert_eq(lightmap.owner, lightmap.get_parent(), "saved with the level")
	assert_eq(lightmap.quality, LightmapGI.BAKE_QUALITY_ULTRA)
	assert_eq(lightmap.bounces, 4)
	assert_eq(lightmap.bounce_indirect_energy, 1.0)
	assert_false(lightmap.directional)
	assert_true(lightmap.supersampling)
	assert_eq(lightmap.supersampling_factor, 2.0)
	assert_true(lightmap.use_denoiser)
	assert_almost_eq(lightmap.denoiser_strength, 0.1, 0.0001)
	assert_eq(lightmap.denoiser_range, 10)
	assert_eq(lightmap.environment_mode, LightmapGI.ENVIRONMENT_MODE_SCENE)
	assert_false(lightmap.interior)
	assert_eq(lightmap.shadowmask_mode, LightmapGIData.SHADOWMASK_MODE_REPLACE)
	assert_eq(lightmap.generate_probes_subdiv, LightmapGI.GENERATE_PROBES_SUBDIV_8)
	assert_null(lightmap.light_data, "no bake for this id")


func test_level_with_a_committed_bake_uses_it() -> void:
	var data: LightmapGIData = _lightmap(_converted("fixture")).light_data
	assert_not_null(data, "%s: run `just bake fixture`" % (LevelConverter.LIGHTMAP_DATA % "fixture"))
	if data != null:
		assert_eq(data.resource_path, LevelConverter.LIGHTMAP_DATA % "fixture")
		assert_false(data.lightmap_textures.is_empty(), "the bake has a lightmap texture")


## The import path: the built fixture references its bake, and its meshes have a lightmap UV2.
func test_built_fixture_references_its_bake() -> void:
	var path: String = BUILT % "fixture"
	if not ResourceLoader.exists(path):
		fail_test("%s is missing: run `just build-levels`" % path)
		return
	var level: Node = autofree((load(path) as PackedScene).instantiate())
	var data: LightmapGIData = _lightmap(level).light_data
	assert_eq(data.resource_path if data != null else "", LevelConverter.LIGHTMAP_DATA % "fixture")
	# The level's own meshes; the objects' scenes own theirs.
	var meshes: int = 0
	for node: Node in level.find_children("*", "MeshInstance3D", true, false):
		if node.owner == level:
			meshes += 1
			var mesh: ArrayMesh = (node as MeshInstance3D).mesh as ArrayMesh
			var format: int = mesh.surface_get_format(0)
			assert_true(format & Mesh.ARRAY_FORMAT_TEX_UV2 != 0, "%s has a UV2" % node.name)
	assert_gt(meshes, 0, "the fixture has meshes")


## Warns (as a pending test) when a bake's .sha256 sidecar does not match its built level, so
## the bake is stale. CI rebuilds the levels, so a stale bake does not fail the test.
func test_committed_bakes_match_their_levels() -> void:
	var stale: PackedStringArray = []
	for file: String in DirAccess.get_files_at(BAKES):
		if file.get_extension() != "lmbake":
			continue
		var id: String = file.get_basename()
		var recorded: String = FileAccess.get_file_as_string(BAKES + id + ".sha256").strip_edges()
		var built: String = BUILT % id
		if ResourceLoader.exists(built) and FileAccess.get_sha256(built) != recorded:
			stale.append(id)
	if stale.is_empty():
		pass_test("every bake matches its level")
	else:
		var message: String = "stale lightmaps, run `just bake %s`" % " ".join(stale)
		push_warning(message)
		pending(message)
