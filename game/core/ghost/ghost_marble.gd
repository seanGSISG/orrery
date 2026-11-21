class_name GhostMarble
extends Node3D
## A see-through marble that plays back a Ghost: the shapes of the marble's skin in the ghost
## look (ghost.gdshader). Set ghost, add the node to a run, and call show_at() with the level
## clock. It moves only by its samples and has no physics.

## The skin that the ghost shows: the skin of the marble (res://core/marble/marble.tscn).
const SKIN: PackedScene = preload("res://core/marble/skins/glass_orrery.tscn")
## The radius that a skin scene has, m.
const SKIN_RADIUS: float = 0.2
const LOOK: Shader = preload("res://core/ghost/ghost.gdshader")

var ghost: Ghost


## Makes the skin for a marble of radius m and gives each part the ghost look. A ghost casts
## no shadow, so a part that only casts one is hidden. No part sorts in front of its place:
## where the ghost and the marble are at one place (the start), the marble's glass draws last
## and stays clear.
func _init(radius: float = SKIN_RADIUS) -> void:
	var look: ShaderMaterial = ShaderMaterial.new()
	look.shader = LOOK
	var skin: Node3D = SKIN.instantiate() as Node3D
	skin.scale = Vector3.ONE * (radius / SKIN_RADIUS)
	for node: Node in skin.find_children("*", "GeometryInstance3D", true, false):
		var part: GeometryInstance3D = node as GeometryInstance3D
		part.visible = part.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		part.material_override = look
		part.sorting_offset = 0.0
	add_child(skin)


## Puts the ball at the ghost's pose at time, s of level clock. Hidden without samples.
func show_at(time: float) -> void:
	if ghost == null or ghost.size() == 0:
		hide()
		return
	transform = ghost.transform_at(time)
