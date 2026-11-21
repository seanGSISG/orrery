extends SceneTree
## Checks that built levels load as Level scenes; exits 1 when one does not. Run it after an
## import, as tools/blender/build_levels.py does:
##     godot --headless --path game --script res://levels/check_levels.gd -- <id> ...


func _initialize() -> void:
	var failed: int = 0
	for id: String in OS.get_cmdline_user_args():
		var path: String = "res://levels/built/%s.glb" % id
		var scene: PackedScene = load(path) as PackedScene if ResourceLoader.exists(path) else null
		var root: Node = scene.instantiate() if scene != null else null
		if not root is Level:
			printerr("level %s: %s did not import as a Level" % [id, path])
			failed += 1
		if root != null:
			root.free()
	quit(1 if failed > 0 else 0)
