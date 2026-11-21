extends Node
## Autoload Graphics: keeps the current graphics preset (GraphicsPreset) applied to the game
## window, its environment and its suns. The project setting orrery/graphics/preset names the
## preset: low, medium (the default), high or ultra. Change it with use(), or with the harness
## `set_setting orrery/graphics/preset high`; the change applies at once. A level that loads
## later gets the preset too. The settings menu (#23) builds on use(). It has no class_name,
## because a class_name would hide the autoload.

const SETTING: String = "orrery/graphics/preset"
const PRESETS: String = "res://settings/presets/%s.tres"

## The applied preset's name, or "" before the first apply.
var current: String = ""
var _preset: GraphicsPreset


func _ready() -> void:
	ProjectSettings.settings_changed.connect(_sync)
	get_tree().node_added.connect(_on_node_added)
	_sync()


## Makes preset_name the current preset and applies it. Returns false, and keeps the current
## preset, when res://settings/presets/<preset_name>.tres does not exist.
func use(preset_name: String) -> bool:
	if not ResourceLoader.exists(PRESETS % preset_name):
		push_error("Graphics: no preset %s" % preset_name)
		return false
	ProjectSettings.set_setting(SETTING, preset_name)
	_sync()
	return true


## Applies the preset that the setting names when it is not the current one.
func _sync() -> void:
	var wanted: String = ProjectSettings.get_setting(SETTING, "medium")
	if wanted == current:
		return
	var preset: GraphicsPreset = load(PRESETS % wanted) as GraphicsPreset
	if preset == null:
		push_error("Graphics: no preset %s" % wanted)
		return
	current = wanted
	_preset = preset
	_preset.apply(get_viewport())


## A new environment or sun gets the current preset after it has entered the world.
func _on_node_added(node: Node) -> void:
	if _preset != null and (node is WorldEnvironment or node is DirectionalLight3D):
		_preset.apply.call_deferred(get_viewport())
