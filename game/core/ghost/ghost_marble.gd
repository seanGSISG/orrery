class_name GhostMarble
extends Node3D
## A see-through marble that plays back a Ghost. Set ghost, add the node to a run, and call
## show_at() with the level clock. It moves only by its samples and has no physics.

const LOOK: Shader = preload("res://core/ghost/ghost.gdshader")

var ghost: Ghost


## Makes the ball mesh of radius m.
func _init(radius: float = 0.2) -> void:
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = LOOK
	mesh.material = material
	var ball: MeshInstance3D = MeshInstance3D.new()
	ball.mesh = mesh
	ball.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(ball)


## Puts the ball at the ghost's pose at time, s of level clock. Hidden without samples.
func show_at(time: float) -> void:
	if ghost == null or ghost.size() == 0:
		hide()
		return
	transform = ghost.transform_at(time)
