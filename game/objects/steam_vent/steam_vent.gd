class_name SteamVent
extends LevelObject
## The `steam_vent` marker: a column of steam that rises `lift` m along the marker's up axis
## (Blender z) from a grate at the marker. Inside the column the steam pushes the marble up at
## `push` until it rises fast enough to coast to the top of the column, so the marble reaches
## `lift` m above the grate from any entry speed, and hovers there while it stays inside. A
## marble that drifts through the column leaves it on an arc: steer it over the next vent or a
## ledge. The column is a trigger, so the marble passes through it; put the grate on a floor.
## The lift assumes the axis points against gravity, at MarbleTuning.gravity. Entry emits
## `steam_vent.blow`.

## Height of the column above the grate, and so the height that the marble reaches, m.
@export var lift: float = 8.0
## Radius of the column, m.
@export var radius: float = 1.0
## Steam acceleration along the axis, m/s². It must be above the gravity (20 m/s²). At 60,
## a marble at rest on the grate gets its full speed in 0.37 s and 2.7 m, and reaches 8 m in
## 1.1 s; so a marble that drifts across the column at 3.5 m/s still gets its full lift.
@export var push: float = 60.0


## Sizes the column from the settings.
func _ready() -> void:
	var column: CylinderShape3D = CylinderShape3D.new()
	column.radius = radius
	column.height = lift
	var shape: CollisionShape3D = $Trigger/Shape
	shape.shape = column
	shape.position.y = lift / 2.0
	var steam: CylinderMesh = CylinderMesh.new()
	steam.top_radius = radius
	steam.bottom_radius = radius * 0.7
	steam.height = lift
	var look: MeshInstance3D = $Steam
	look.mesh = steam
	look.position = shape.position
	var grate: CylinderMesh = CylinderMesh.new()
	grate.top_radius = radius
	grate.bottom_radius = radius
	grate.height = 0.04
	var plate: MeshInstance3D = $Grate
	plate.mesh = grate
	plate.position.y = grate.height / 2.0


## Raises the marble's speed along the axis toward the speed that coasts to the top of the
## column, by at most push for one tick. Emits steam_vent.blow on entry with the part of the
## full lift speed that the marble still needs.
func on_overlap(run: LevelRun, first: bool) -> void:
	var marble: Marble = run.marble
	var axis: Vector3 = global_basis.y.normalized()
	var gravity: float = marble.tuning.gravity
	var height: float = (marble.position - global_position).dot(axis)
	var needed: float = sqrt(2.0 * gravity * maxf(lift - height, 0.0))
	var rise: float = needed - marble.velocity.dot(axis)
	if first:
		var full: float = sqrt(2.0 * gravity * maxf(lift, 0.0))
		var strength: float = clampf(rise / full, 0.0, 1.0) if full > 0.0 else 0.0
		feedback.emit(&"steam_vent.blow", strength, marble.position)
	if rise > 0.0:
		var dt: float = 1.0 / Engine.physics_ticks_per_second
		marble.add_velocity(axis * minf(rise, push * dt))
