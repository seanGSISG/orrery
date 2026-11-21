extends GutTest
## The look rules of LevelConverter on scenes built in code: kit materials, the tier skies with
## their sun, and the reflection probes (docs/design/visual-quality.md).

const SETS: Array[String] = ["a", "b", "c"]
const SKIES: Dictionary[String, String] = {
	"beginner": "dawn",
	"intermediate": "noon",
	"advanced": "dusk",
	"test": "dawn",
}


## Returns a scene like an imported .glb: a root with a level marker that holds level, and a
## start and a finish marker. It is a test-tier level unless level names another tier.
func _scene(level: Dictionary = {}) -> Node3D:
	var root: Node3D = autofree(Node3D.new())
	root.name = "scene"
	var data: Dictionary = {"type": "level", "id": "t", "tier": "test"}
	data.merge(level, true)
	for marker: Dictionary in [data, {"type": "start"}, {"type": "finish"}]:
		var node: Node3D = Node3D.new()
		node.name = str(marker["type"])
		node.set_meta(&"extras", {"orrery": marker})
		root.add_child(node)
	return root


## Adds a box mesh of size at position to scene. extras are the extras of its material.
func _add_mesh(
	scene: Node3D, extras: Dictionary, size: Vector3, position: Vector3
) -> MeshInstance3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.set_meta(&"extras", extras)
	var box: BoxMesh = BoxMesh.new()
	box.size = size
	box.material = material
	var node: MeshInstance3D = MeshInstance3D.new()
	node.name = "mesh_%d" % scene.get_child_count()
	node.mesh = box
	node.position = position
	scene.add_child(node)
	return node


## Returns the nodes of class type under scene after a conversion.
func _converted(scene: Node3D, type: String) -> Array[Node]:
	LevelConverter.new().convert(scene)
	return scene.find_children("*", type, true, false)


func test_surface_with_a_kit_material_name_gets_the_library_material() -> void:
	var scene: Node3D = _scene()
	var extras: Dictionary = {"surface": "default", "material": "limestone"}
	var mesh: MeshInstance3D = _add_mesh(scene, extras, Vector3.ONE, Vector3.ZERO)
	assert_not_null(LevelConverter.new().convert(scene))
	var material: Material = mesh.mesh.surface_get_material(0)
	assert_eq(material, KitMaterials.find("limestone"))
	assert_eq(material.resource_path, "res://materials/%s/limestone.tres" % KitMaterials.SET)


func test_surface_without_a_kit_material_name_keeps_its_material() -> void:
	var scene: Node3D = _scene()
	var mesh: MeshInstance3D = _add_mesh(scene, {"surface": "default"}, Vector3.ONE, Vector3.ZERO)
	var before: Material = mesh.mesh.surface_get_material(0)
	assert_not_null(LevelConverter.new().convert(scene))
	assert_eq(mesh.mesh.surface_get_material(0), before)


func test_unknown_kit_material_fails() -> void:
	var scene: Node3D = _scene()
	_add_mesh(scene, {"material": "cheese"}, Vector3.ONE, Vector3.ZERO)
	var converter: LevelConverter = LevelConverter.new()
	assert_null(converter.convert(scene))
	assert_string_contains("\n".join(converter.errors), "unknown kit material `cheese`")


## A change of KitMaterials.SET must find every material, so each set holds the same names.
func test_every_set_has_every_kit_material_with_its_textures() -> void:
	for set_name: String in SETS:
		for kit_name: String in ["limestone", "brass", "gold"]:
			var path: String = "res://materials/%s/%s.tres" % [set_name, kit_name]
			if not ResourceLoader.exists(path):
				path = "res://materials/%s.tres" % kit_name
			var material: ShaderMaterial = load(path) as ShaderMaterial
			assert_not_null(material, path)
			if material != null:
				assert_eq(material.shader.resource_path, "res://materials/kit_surface.gdshader")
				var albedo: Texture2D = material.get_shader_parameter(&"albedo_map")
				assert_not_null(albedo, path)


func test_each_tier_gets_its_sky_and_its_sun() -> void:
	for tier: String in SKIES:
		var preset: SkyPreset = load(LevelConverter.SKY % SKIES[tier]) as SkyPreset
		var scene: Node3D = _scene({"tier": tier})
		var worlds: Array[Node] = _converted(scene, "WorldEnvironment")
		var suns: Array[Node] = scene.find_children("*", "DirectionalLight3D", true, false)
		assert_eq(worlds.size(), 1, tier)
		assert_eq(suns.size(), 1, tier)
		if worlds.size() != 1 or suns.size() != 1:
			continue
		var environment: Environment = (worlds[0] as WorldEnvironment).environment
		var sky: PanoramaSkyMaterial = environment.sky.sky_material as PanoramaSkyMaterial
		assert_eq(sky.panorama, preset.panorama, tier)
		assert_eq(environment.tonemap_mode, Environment.TONE_MAPPER_AGX, tier)
		var sun: DirectionalLight3D = suns[0] as DirectionalLight3D
		assert_almost_eq(sun.basis.z, preset.to_sun(), Vector3.ONE * 0.001, tier)
		assert_true(sun.shadow_enabled, tier)
		assert_eq(sun.light_bake_mode, Light3D.BAKE_DYNAMIC, tier)


func test_the_three_tier_skies_differ() -> void:
	var dawn: SkyPreset = load(LevelConverter.SKY % "dawn") as SkyPreset
	var noon: SkyPreset = load(LevelConverter.SKY % "noon") as SkyPreset
	var dusk: SkyPreset = load(LevelConverter.SKY % "dusk") as SkyPreset
	assert_ne(dawn.panorama, noon.panorama)
	assert_ne(noon.panorama, dusk.panorama)
	assert_gt(noon.sun_elevation, dawn.sun_elevation, "the noon sun is the highest")
	assert_gt(noon.sun_elevation, dusk.sun_elevation, "the noon sun is the highest")


func test_level_sky_setting_wins_over_the_tier() -> void:
	var scene: Node3D = _scene({"tier": "beginner", "sky": "dusk"})
	var worlds: Array[Node] = _converted(scene, "WorldEnvironment")
	var dusk: SkyPreset = load(LevelConverter.SKY % "dusk") as SkyPreset
	var environment: Environment = (worlds[0] as WorldEnvironment).environment
	assert_eq((environment.sky.sky_material as PanoramaSkyMaterial).panorama, dusk.panorama)


func test_unknown_sky_fails() -> void:
	var converter: LevelConverter = LevelConverter.new()
	assert_null(converter.convert(_scene({"sky": "midnight"})))
	assert_string_contains("\n".join(converter.errors), "unknown sky `midnight`")


## The kit's (x, y, z) is Godot's (x, z, -y): azimuth 90 is the kit's +y, which is Godot's -z.
func test_sky_preset_points_to_its_sun() -> void:
	var preset: SkyPreset = SkyPreset.new()
	preset.sun_azimuth = 90.0
	preset.sun_elevation = 30.0
	assert_almost_eq(preset.to_sun(), Vector3(0.0, 0.5, -sqrt(0.75)), Vector3.ONE * 0.0001)
	assert_almost_eq(preset.sun().basis.z, preset.to_sun(), Vector3.ONE * 0.0001)


func test_probes_cover_a_long_level_and_stay_small() -> void:
	var scene: Node3D = _scene()
	var mesh: MeshInstance3D = _add_mesh(scene, {}, Vector3(4, 0.5, 70), Vector3(0, 0, -35))
	var probes: Array[Node] = _converted(scene, "ReflectionProbe")
	assert_eq(probes.size(), 3, "76 m with the margin needs three probes of at most 30 m")
	var covered: AABB = AABB()
	for node: Node in probes:
		var probe: ReflectionProbe = node as ReflectionProbe
		assert_eq(probe.update_mode, ReflectionProbe.UPDATE_ONCE)
		assert_gt(probe.position.y + probe.origin_offset.y, 0.25, "it looks from above the mesh")
		assert_lte(probe.size[probe.size.max_axis_index()], LevelConverter.PROBE_SIZE)
		var box: AABB = AABB(probe.position - probe.size / 2.0, probe.size)
		covered = box if covered.size == Vector3.ZERO else covered.merge(box)
	assert_true(covered.encloses(mesh.transform * mesh.get_aabb()), "the probes enclose the mesh")


func test_a_gap_between_two_islands_gets_no_probe() -> void:
	var scene: Node3D = _scene()
	_add_mesh(scene, {}, Vector3(4, 0.5, 4), Vector3.ZERO)
	_add_mesh(scene, {}, Vector3(4, 0.5, 4), Vector3(0, 0, -100))
	assert_eq(_converted(scene, "ReflectionProbe").size(), 2)
