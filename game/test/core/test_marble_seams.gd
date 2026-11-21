extends RunTest
## Seams between flush Solids, through the boundary only: MarbleInput in, GameState out. The
## course copies the floors fixture: a trimesh track, a box trapdoor, a row of box tiles and a
## trimesh track, each its own Solid. Camera yaw 0 looks along -Z, so forward input rolls
## toward -Z.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## Height of the course's floor tops. The floor of flat.tscn is 3 m below.
const TOP: float = 3.0
## Largest vertical speed that a flush seam may give, m/s. At 0.2 m/s the marble rises 1 mm.
const SMOOTH: float = 0.2
const SPEEDS: Array[float] = [5.0, 10.0, 15.0]


## What _cross() measured.
class Crossing:
	## Largest vertical speed, m/s.
	var vertical: float = 0.0
	## Ticks that ended with on_ground false.
	var airborne: int = 0


## A marble that rolls at 5, 10 or 15 m/s across the seams between flush Solids stays on the
## floor and gets no vertical speed: trimesh to box, box to box and box to trimesh.
func test_rolls_smoothly_across_flush_seams() -> void:
	start_run(FLAT, _course(0.0))
	for speed: float in SPEEDS:
		var crossing: Crossing = _cross(speed)
		assert_lt(crossing.vertical, SMOOTH, "vertical speed at %.0f m/s" % speed)
		assert_eq(crossing.airborne, 0, "ticks in the air at %.0f m/s" % speed)


## A real 0.1 m step up between two Solids still throws the marble up.
func test_step_between_solids_is_felt() -> void:
	start_run(FLAT, _course(0.1))
	for speed: float in SPEEDS:
		assert_gt(_cross(speed).vertical, 5.0 * SMOOTH, "vertical speed at %.0f m/s" % speed)


## Rolls the marble from z = 5 along -Z with the input that keeps speed, until it passes
## z = -15 or 4 s pass, and returns the largest vertical speed and the ticks in the air.
func _cross(speed: float) -> Crossing:
	var input: MarbleInput = rolling(Vector2(0, speed / TUNING.max_roll_speed))
	run.marble.teleport(Vector3(0.5, TOP + TUNING.radius, 5), Vector3(0, 0, -speed))
	var crossing: Crossing = Crossing.new()
	for _i: int in 4 * Engine.physics_ticks_per_second:
		run.step(input)
		crossing.vertical = maxf(crossing.vertical, absf(run.state.velocity.y))
		if not run.state.on_ground:
			crossing.airborne += 1
		if run.state.position.z < -15.0:
			break
	return crossing


## Returns the course along -Z, 4 m wide, each piece its own Solid: a trimesh track from
## z = 6 to 0, a 4 m box door, four 2 m box tile rows and a trimesh track to z = -18. The
## boxes rise by step above the tracks; at 0 every top is flush at TOP.
func _course(step: float) -> Array[Node3D]:
	var pieces: Array[Node3D] = [_floor(6.0, 0.0, 0.0, true), _floor(0.0, -4.0, step, false)]
	for row: int in 4:
		pieces.append(_floor(-4.0 - 2.0 * row, -6.0 - 2.0 * row, step, false))
	pieces.append(_floor(-12.0, -18.0, 0.0, true))
	return pieces


## Returns a 4 m wide, 0.5 m thick floor Solid from z = near to z = far with its top at
## TOP + rise: a closed trimesh when trimesh is true, else a box.
func _floor(near: float, far: float, rise: float, trimesh: bool) -> Solid:
	var size: Vector3 = Vector3(4, 0.5, near - far)
	var shape: CollisionShape3D = CollisionShape3D.new()
	if trimesh:
		var mesh: BoxMesh = BoxMesh.new()
		mesh.size = size
		shape.shape = mesh.create_trimesh_shape()
	else:
		var box: BoxShape3D = BoxShape3D.new()
		box.size = size
		shape.shape = box
	var solid: Solid = Solid.new()
	solid.add_child(shape)
	solid.position = Vector3(0, TOP + rise - size.y / 2.0, (near + far) / 2.0)
	return solid
