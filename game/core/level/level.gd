class_name Level
extends Node3D
## The root of every level scene. The importer (#8) fills these from the level script's root
## data. Give a Level to LevelRun.create() to play it.

## The scene of the `egg` marker.
const EGG_SCENE: String = "res://objects/egg/egg.tscn"
## The id of an egg whose level has no scene to ask: the first name that the kit gives an egg
## marker.
const DEFAULT_EGG: String = "egg_00"

@export var id: StringName = &""
@export var title: String = ""
@export var tier: StringName = &""
## Par time and gold time, s.
@export var par: float = 0.0
@export var gold: float = 0.0
@export var music: StringName = &""
@export var sky: StringName = &""


## Returns the ids of the Clockwork Eggs in the level scene at path, in scene order. The id of
## an egg is its node name. It reads the scene file and makes no level. Empty when path has
## no scene.
static func egg_ids(path: String) -> PackedStringArray:
	var ids: PackedStringArray = []
	var scene: PackedScene = load(path) as PackedScene if ResourceLoader.exists(path) else null
	if scene == null:
		return ids
	var state: SceneState = scene.get_state()
	for i: int in state.get_node_count():
		var instance: PackedScene = state.get_node_instance(i)
		if instance != null and instance.resource_path == EGG_SCENE:
			ids.append(state.get_node_name(i))
	return ids
