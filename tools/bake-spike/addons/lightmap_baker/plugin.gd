@tool
extends EditorPlugin
## Bakes the LightmapGI of each given scene, then quits the editor. It does nothing unless the
## editor starts with the user argument --bake-lightmaps. Run it with a real GPU, for example:
##     gamescope --backend headless -W 1280 -H 720 -- \
##         godot --editor --path proj -- --bake-lightmaps res://level/test.glb
## Each scene needs exactly one LightmapGI. Its bake goes to res://lightmaps/<scene basename>.lmbake
## (plus <basename>.exr and <basename>_shadow.png). The log has one "BAKE ok" or "BAKE FAIL"
## line per scene and ends with "BAKE done: <baked> of <total> baked". Check that line, not the
## exit code: gamescope does not pass on Godot's exit code.
##
## Godot 4.7.2 does not expose LightmapGI.bake() to scripts. This plugin selects the
## LightmapGI, so that the built-in LightmapGIEditorPlugin edits it, and calls that plugin's
## bound _bake method, the same call as the "Bake Lightmaps" button.

const FLAG := "--bake-lightmaps"
const DATA_PATH := "res://lightmaps/%s.lmbake"


func _enter_tree() -> void:
	var args := OS.get_cmdline_user_args()
	var at := args.find(FLAG)
	if at != -1:
		_bake_all.call_deferred(args.slice(at + 1))


func _bake_all(scenes: PackedStringArray) -> void:
	var filesystem := EditorInterface.get_resource_filesystem()
	# Let the first scan, and the editor's reopening of the last session's scenes, finish first.
	await _frames(10)
	while filesystem.is_scanning():
		await _frames(1)
	await _frames(30)
	var baked := 0
	for path in scenes:
		# A script error inside _bake() makes the await return null, so count only "" as baked.
		var error: Variant = await _bake(path)
		if error is String and error == "":
			baked += 1
		else:
			printerr("BAKE FAIL %s: %s" % [path, error])
	print("BAKE done: %d of %d baked" % [baked, scenes.size()])
	get_tree().quit(0 if baked == scenes.size() else 1)


## Bakes one scene. Returns an empty string on success, else the error.
func _bake(scene_path: String) -> String:
	# An imported scene (.glb) opens only as a new inherited scene. It is never saved: the bake
	# writes its own files, and the baked node paths are relative to the LightmapGI, so they
	# match the imported scene.
	var before := EditorInterface.get_edited_scene_root()
	EditorInterface.open_scene_from_path(scene_path, true)
	var root: Node
	for i in 120:
		await _frames(1)
		root = EditorInterface.get_edited_scene_root()
		if root != null and root != before:
			break
	if root == null or root == before:
		return "the scene did not open"
	var lightmaps := root.find_children("*", "LightmapGI", true, false)
	if lightmaps.size() != 1:
		return "needs exactly one LightmapGI, found %d" % lightmaps.size()
	var lightmap: LightmapGI = lightmaps[0]
	var data_path := DATA_PATH % scene_path.get_file().get_basename()
	# The bake writes next to light_data's path. A fresh level has no data yet, so give it an
	# empty one at the stable path, and reimport the scene afterwards so that it references it.
	var reimport := lightmap.light_data == null or lightmap.light_data.resource_path != data_path
	if reimport:
		var placeholder := LightmapGIData.new()
		DirAccess.make_dir_recursive_absolute(data_path.get_base_dir())
		var save_error := ResourceSaver.save(placeholder, data_path)
		if save_error != OK:
			return "cannot save %s: %s" % [data_path, error_string(save_error)]
		lightmap.light_data = load(data_path)
	EditorInterface.edit_node(lightmap)
	await _frames(2)
	var editors := get_tree().root.find_children("*", "LightmapGIEditorPlugin", true, false)
	if editors.is_empty():
		return "LightmapGIEditorPlugin not found"
	var started := Time.get_ticks_msec()
	editors[0].call("_bake")
	var seconds := (Time.get_ticks_msec() - started) / 1000.0
	var data := lightmap.light_data
	EditorInterface.close_scene()
	if data == null or data.resource_path != data_path or data.lightmap_textures.is_empty():
		return "the bake wrote no lightmap (see the errors above)"
	if reimport:
		EditorInterface.get_resource_filesystem().reimport_files([scene_path])
	print("BAKE ok %s -> %s in %.1f s (%d lightmap, %d shadowmask textures)" % [
		scene_path, data_path, seconds, data.lightmap_textures.size(),
		data.shadowmask_textures.size()])
	return ""


func _frames(count: int) -> void:
	for i in count:
		await get_tree().process_frame
