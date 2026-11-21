class_name TestPusher
extends LevelObject
## Test mover: a 1 m cube Solid that starts at `from` and slides along +X at `speed`. It is
## fast enough to pass over the marble centre within one tick. Add it with
## RunTest.start_run(level, [pusher]).

## Start position of the cube centre.
@export var from: Vector3 = Vector3.ZERO
## m/s along +X.
@export var speed: float = 0.0

var _solid: Solid = Solid.new()


## Builds the cube Solid.
func _init() -> void:
	var shape: CollisionShape3D = CollisionShape3D.new()
	shape.shape = BoxShape3D.new()
	_solid.add_child(shape)
	add_child(_solid)


## Puts the cube back at the start, still.
func reset(_restart: bool) -> void:
	_solid.move(Transform3D(Basis.IDENTITY, from), Vector3.ZERO, Vector3.ZERO)


## Moves the cube to its pose at run time t.
func advance(_run: LevelRun, t: float) -> void:
	var to: Transform3D = Transform3D(Basis.IDENTITY, from + Vector3.RIGHT * speed * t)
	_solid.move(to, Vector3.RIGHT * speed, Vector3.ZERO)
