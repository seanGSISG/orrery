class_name LevelInfo
extends RefCounted
## What the menus show of one level before it is played: its name and its target times. Get
## one with LevelInfo.read(id); it reads the root of the level scene and makes no level.

var id: StringName = &""
## False when the level has no scene: its level script is not built yet.
var built: bool = false
var title: String = ""
## Par time and gold time, s; 0 when the level has none.
var par: float = 0.0
var gold: float = 0.0
## The ids of the Clockwork Eggs in the level (Level.egg_ids()).
var eggs: PackedStringArray = []


## Returns the info of level id. A level with no scene gives built false and no name.
static func read(level_id: StringName) -> LevelInfo:
	var info: LevelInfo = LevelInfo.new()
	info.id = level_id
	var path: String = Game.level_path(level_id)
	var scene: PackedScene = load(path) as PackedScene if path != "" else null
	if scene == null:
		return info
	info.built = true
	info.eggs = Level.egg_ids(path)
	var state: SceneState = scene.get_state()
	for i: int in state.get_node_property_count(0):
		var value: Variant = state.get_node_property_value(0, i)
		match state.get_node_property_name(0, i):
			&"title" when value is String:
				info.title = value
			&"par" when value is float:
				info.par = value
			&"gold" when value is float:
				info.gold = value
	return info
