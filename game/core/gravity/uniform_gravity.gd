class_name UniformGravity
extends GravityField
## Gravity of one strength along the node's -Y axis everywhere in its volume, for example a
## gravity zone or a low-gravity zone. uniform_gravity.tscn has a 1 m cube volume around the
## node origin: turn the node to aim the gravity, and scale it to size the volume.

## Gravity strength, m/s². MarbleTuning.gravity is the normal value.
@export var strength: float = 20.0


## Returns -Y of the node, times strength.
func gravity_at(_point: Vector3) -> Vector3:
	return -global_basis.y.normalized() * strength
