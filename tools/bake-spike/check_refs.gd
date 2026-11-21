extends SceneTree
## Prints the lightmap data that each imported level references, and the atlas sizes.


func _initialize() -> void:
	for id in ["test", "second", "big"]:
		var level: Node = load("res://level/%s.glb" % id).instantiate()
		var data: LightmapGIData = level.get_node("lightmap").light_data
		var sizes: Array[String] = []
		if data != null:
			for t: TextureLayered in data.lightmap_textures + data.shadowmask_textures:
				sizes.append("%s %dx%d" % [t.resource_path.get_file(), t.get_width(), t.get_height()])
		print("REF %s -> %s %s" % [id, data.resource_path if data else "none", sizes])
		level.free()
	quit()
