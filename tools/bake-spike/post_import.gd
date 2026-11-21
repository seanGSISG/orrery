@tool
extends EditorScenePostImport
## Post-import script of res://level/test.glb. It stands in for the repo's LevelConverter: it
## adds the sun, the sky and a LightmapGI node with the visual-quality bake settings. The
## LightmapGI's light_data is res://lightmaps/<glb basename>.lmbake when that file exists, so the
## imported scene references the committed bake by a stable path.

const LIGHTMAP_PATH := "res://lightmaps/%s.lmbake"


func _post_import(scene: Node) -> Object:
	var sun := DirectionalLight3D.new()
	sun.name = "sun"
	sun.light_bake_mode = Light3D.BAKE_DYNAMIC
	sun.shadow_enabled = true
	sun.rotation_degrees = Vector3(-50, -35, 0)
	_add(scene, sun)

	var sky_material := ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = sky_material
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky
	environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	var world := WorldEnvironment.new()
	world.name = "world"
	world.environment = environment
	_add(scene, world)

	var lightmap := LightmapGI.new()
	lightmap.name = "lightmap"
	lightmap.quality = LightmapGI.BAKE_QUALITY_ULTRA
	lightmap.bounces = 4
	lightmap.bounce_indirect_energy = 1.0
	lightmap.directional = false
	lightmap.supersampling = true
	lightmap.supersampling_factor = 2.0
	lightmap.use_denoiser = true
	lightmap.denoiser_strength = 0.1
	lightmap.denoiser_range = 10
	lightmap.environment_mode = LightmapGI.ENVIRONMENT_MODE_SCENE
	lightmap.interior = false
	lightmap.shadowmask_mode = LightmapGIData.SHADOWMASK_MODE_REPLACE
	lightmap.generate_probes_subdiv = LightmapGI.GENERATE_PROBES_SUBDIV_8
	var data_path := LIGHTMAP_PATH % get_source_file().get_file().get_basename()
	if ResourceLoader.exists(data_path):
		lightmap.light_data = load(data_path)
	_add(scene, lightmap)
	return scene


func _add(scene: Node, node: Node) -> void:
	scene.add_child(node)
	node.owner = scene
