class_name Solid
extends StaticBody3D
## Every collider that the marble can touch: level geometry and the solid parts of objects.
## Keep it on the `solid` physics layer. A mover calls move() in LevelObject.advance(); do not
## move a Solid through its parent or with an AnimationPlayer.

const DEFAULT_SURFACE: Surface = preload("res://core/level/default_surface.tres")

@export var surface: Surface = DEFAULT_SURFACE


## Moves the node and the physics body to `to` at once, so the next query sees the new pose,
## and records the surface velocity: linear (m/s) and angular (rad/s around the origin).
func move(to: Transform3D, linear: Vector3, angular: Vector3) -> void:
	global_transform = to
	PhysicsServer3D.body_set_state(get_rid(), PhysicsServer3D.BODY_STATE_TRANSFORM, to)
	constant_linear_velocity = linear
	constant_angular_velocity = angular


## Returns the world velocity of the surface at point.
func velocity_at(point: Vector3) -> Vector3:
	return constant_linear_velocity + constant_angular_velocity.cross(point - global_position)
