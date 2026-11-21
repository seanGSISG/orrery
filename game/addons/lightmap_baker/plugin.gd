@tool
extends EditorPlugin
## Bakes the LightmapGI of each given built level, then quits the editor. It does nothing unless
## the editor starts with the user argument --bake-lightmaps. `just bake <id>...` runs it in a
## hidden gamescope display, because a bake needs a real GPU:
##     gamescope --backend headless -W 1280 -H 720 -- \
##         godot --editor --path game -- --bake-lightmaps res://levels/built/<id>.glb ...
## Each scene needs exactly one LightmapGI (LevelConverter adds it). The bake goes to
## LevelConverter.LIGHTMAP_DATA, res://levels/lightmaps/<id>.lmbake, plus <id>.exr and
## <id>_shadow.png. The log has one "BAKE ok" or "BAKE FAIL" line per scene and ends with
## "BAKE done: <baked> of <total> baked". Check that line, not the exit code: gamescope does not
## pass on Godot's exit code.
##
## Godot 4.7.2 does not expose LightmapGI.bake() to scripts. This plugin selects the LightmapGI,
## so that the built-in LightmapGIEditorPlugin edits it, and calls that plugin's bound _bake
## method, the same call as the "Bake Lightmaps" button. Recheck this on a Godot upgrade.

const FLAG: String = "--bake-lightmaps"


## Starts the bake when the editor has the --bake-lightmaps user argument.
func _enter_tree() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var at: int = args.find(FLAG)
	if at != -1:
		_bake_all.call_deferred(args.slice(at + 1))


## Bakes each scene in turn, prints the summary line and quits.
func _bake_all(scenes: PackedStringArray) -> void:
	var filesystem: EditorFileSystem = EditorInterface.get_resource_filesystem()
	# Let the first scan, and the editor's reopening of the last session's scenes, finish first.
	await _frames(10)
	while filesystem.is_scanning():
		await _frames(1)
	await _frames(30)
	var baked: int = 0
	for path: String in scenes:
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
	var before: Node = EditorInterface.get_edited_scene_root()
	EditorInterface.open_scene_from_path(scene_path, true)
	var root: Node = null
	for i: int in 120:
		await _frames(1)
		root = EditorInterface.get_edited_scene_root()
		if root != null and root != before:
			break
	if root == null or root == before:
		return "the scene did not open (if a dependency is missing, `just build-levels` reimports it)"
	var lightmaps: Array[Node] = root.find_children("*", "LightmapGI", true, false)
	if lightmaps.size() != 1:
		return "needs exactly one LightmapGI, found %d" % lightmaps.size()
	var lightmap: LightmapGI = lightmaps[0] as LightmapGI
	var data_path: String = LevelConverter.LIGHTMAP_DATA % scene_path.get_file().get_basename()
	# The bake writes next to light_data's path. A level without a bake has no data yet, so give
	# it an empty one at the stable path, and reimport the scene afterwards so that it
	# references it.
	var reimport: bool = (
		lightmap.light_data == null or lightmap.light_data.resource_path != data_path
	)
	if reimport:
		DirAccess.make_dir_recursive_absolute(data_path.get_base_dir())
		var save_error: Error = ResourceSaver.save(LightmapGIData.new(), data_path)
		if save_error != OK:
			return "cannot save %s: %s" % [data_path, error_string(save_error)]
		# The bake imports its .exr through the editor's file system, which must know the folder.
		var filesystem: EditorFileSystem = EditorInterface.get_resource_filesystem()
		filesystem.scan()
		while filesystem.is_scanning():
			await _frames(1)
		lightmap.light_data = load(data_path) as LightmapGIData
	EditorInterface.edit_node(lightmap)
	await _frames(2)
	var editors: Array[Node] = get_tree().root.find_children(
		"*", "LightmapGIEditorPlugin", true, false
	)
	if editors.is_empty():
		return "LightmapGIEditorPlugin not found"
	# Forget the last bake's textures (in memory only), so a bake that fails before it writes
	# anything cannot pass the check below with the old lightmap.
	var none: Array[TextureLayered] = []
	lightmap.light_data.lightmap_textures = none
	var started: int = Time.get_ticks_msec()
	editors[0].call("_bake")
	var seconds: float = (Time.get_ticks_msec() - started) / 1000.0
	var data: LightmapGIData = lightmap.light_data
	EditorInterface.close_scene()
	if data == null or data.resource_path != data_path or data.lightmap_textures.is_empty():
		return "the bake wrote no lightmap (see the errors above)"
	_remove_orphans(data)
	if reimport:
		EditorInterface.get_resource_filesystem().reimport_files([scene_path])
	print(
		(
			"BAKE ok %s -> %s in %.1f s (%d lightmap, %d shadowmask textures)"
			% [
				scene_path,
				data_path,
				seconds,
				data.lightmap_textures.size(),
				data.shadowmask_textures.size(),
			]
		)
	)
	return ""


## Deletes the atlas files of an earlier bake of data's level that this bake did not write, for
## example <id>_1.exr after a level shrank to one atlas. Deleting them before the bake does not
## work: the editor does not open a scene whose dependencies are missing.
func _remove_orphans(data: LightmapGIData) -> void:
	var kept: PackedStringArray = []
	for texture: Texture in data.lightmap_textures + data.shadowmask_textures:
		kept.append(texture.resource_path)
	var folder: String = data.resource_path.get_base_dir()
	var id: String = data.resource_path.get_file().get_basename()
	var atlas: RegEx = RegEx.create_from_string(
		"^%s(_\\d+\\.exr|\\.exr|_shadow(_\\d+)?\\.png)$" % id
	)
	for file: String in DirAccess.get_files_at(folder):
		var path: String = folder.path_join(file)
		# <id>_1.exr is also the atlas of a level named <id>_1, when that level has a bake.
		var other_level: bool = FileAccess.file_exists(path.get_basename() + ".lmbake")
		if atlas.search(file) != null and path not in kept and not other_level:
			print("BAKE removes %s" % path)
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path + ".import"))


## Waits count process frames.
func _frames(count: int) -> void:
	for i: int in count:
		await get_tree().process_frame
