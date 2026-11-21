class_name GravityField
extends LevelObject
## A volume that sets the marble's gravity while the marble overlaps it (docs/plan.md §4.2).
## The volume is an Area3D on the trigger layer that belongs to this object. Of the fields
## that the marble overlaps, the one with the highest priority wins. Outside every field the
## marble falls straight down at MarbleTuning.gravity. Up is always the opposite of the
## gravity, for the camera and for jumps. Extend this class and override gravity_at().

## Of the fields that overlap the marble, the highest priority wins. Give overlapping fields
## different priorities.
@export var priority: int = 0


## Returns the gravity at point, m/s². This base field has none, so the marble keeps its up.
func gravity_at(_point: Vector3) -> Vector3:
	return Vector3.ZERO
