@tool
extends EditorScenePostImport
## The post-import script of every built level, res://levels/built/<id>.glb. The build
## (tools/blender/build_levels.py) names it in each .glb.import file. It turns the imported
## scene into a Level with LevelConverter, or fails the import and prints the errors.


## Returns the converted Level, or null (a failed import) when the level has errors.
func _post_import(scene: Node) -> Object:
	var converter: LevelConverter = LevelConverter.new()
	var level: Level = converter.convert(scene as Node3D)
	for message: String in converter.errors:
		push_error(message)
	if level == null:
		scene.free()
	return level
