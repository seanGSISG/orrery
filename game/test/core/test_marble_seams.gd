extends RunTest
## Seams between flush Solids, through the boundary only: MarbleInput in, GameState out. The
## course copies the floors fixture: a trimesh track, a box trapdoor, four rows of two 2 m box
## tiles and a trimesh track, each its own Solid. Camera yaw 0 looks along -Z, so forward
## input rolls toward -Z.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## Height of the course's floor tops. The floor of flat.tscn is 3 m below.
const TOP: float = 3.0
## The marble crosses the course from z = START to z = END.
const START: float = 5.0
const END: float = -15.0
## Largest vertical speed that a flush seam may give, m/s. At 0.2 m/s the marble rises 1 mm.
const SMOOTH: float = 0.2
const SPEEDS: Array[float] = [5.0, 10.0, 15.0]
## Paths across the course: inside one tile column, and along the seam between the columns.
const LANES: Array[float] = [0.5, 0.0]


## What _cross() measured.
class Crossing:
	## Largest vertical speed, m/s, up or down.
	var vertical: float = 0.0
	## Largest upward speed, m/s.
	var upward: float = 0.0
	## Ticks that ended with on_ground false.
	var airborne: int = 0


## A floor object for the touch test: a 4 m wide, 2 m long box Solid from z = 0 to -2, with
## its top flush at TOP. It keeps the marble centre's z at its first touch.
class Pad:
	extends LevelObject

	## Marble centre z at the first touch; INF before it.
	var first_touch: float = INF

	## Builds the box Solid, owned by the pad so that its contacts name the pad.
	func _init() -> void:
		var box: BoxShape3D = BoxShape3D.new()
		box.size = Vector3(4, 0.5, 2)
		var shape: CollisionShape3D = CollisionShape3D.new()
		shape.shape = box
		var solid: Solid = Solid.new()
		solid.add_child(shape)
		solid.position = Vector3(0, TOP - box.size.y / 2.0, -box.size.z / 2.0)
		add_child(solid)
		solid.owner = self

	## Keeps the marble centre's z at the first touch.
	func on_touch(run: LevelRun, _contact: Contact) -> void:
		if first_touch == INF:
			first_touch = run.marble.position.z


## A marble that rolls at 5, 10 or 15 m/s across the seams between flush Solids crosses the
## course on the floor and gets no vertical speed: trimesh to box, box to box and box to
## trimesh, also along the seam between the tile columns, over the tile corners.
func test_rolls_smoothly_across_flush_seams() -> void:
	start_run(FLAT, _course(0.0))
	for x: float in LANES:
		for speed: float in SPEEDS:
			var crossing: Crossing = _cross(speed, x)
			var case: String = "at %.0f m/s, x = %.1f" % [speed, x]
			assert_lt(run.state.position.z, END, "crossed the course " + case)
			assert_lt(crossing.vertical, SMOOTH, "vertical speed " + case)
			assert_eq(crossing.airborne, 0, "ticks in the air " + case)


## A real 0.1 m step up between two Solids still throws the marble up. The course has no
## other step, so all the upward speed comes from this one.
func test_step_between_solids_is_felt() -> void:
	start_run(FLAT, _course(0.1))
	for speed: float in SPEEDS:
		var upward: float = _cross(speed, LANES[0]).upward
		assert_gt(upward, 5.0 * SMOOTH, "upward speed at %.0f m/s" % speed)


## A marble at 15 m/s that rolls onto a 10° ramp Solid, flush with the floor, moves as far as
## its speed carries it and climbs the ramp. The foot of a ramp rises, so it is no flush seam,
## and the sweep must not stop the move there. Each start puts the sub-steps at a new place.
func test_rolls_onto_a_flush_ramp_without_a_stall() -> void:
	var pieces: Array[Node3D] = _floor(6.0, 0.0, 0.0, true)
	pieces.append(_ramp(deg_to_rad(10.0)))
	start_run(FLAT, pieces)
	var input: MarbleInput = rolling(Vector2(0, 1))
	var rate: float = Engine.physics_ticks_per_second
	for k: int in 13:
		var at: float = 1.5 + 0.005 * k
		run.marble.teleport(Vector3(0.5, TOP + TUNING.radius, at), Vector3(0, 0, -15))
		run.step(input)
		var lost: float = 0.0
		for _i: int in 30:
			var before: Vector3 = run.state.position
			var speed: float = run.state.velocity.length()
			run.step(input)
			var carried: float = (speed + run.state.velocity.length()) * 0.5 / rate
			lost += carried - (run.state.position - before).length()
		assert_lt(lost, 0.01, "travel lost from z = %.3f" % at)
		var rise: float = run.state.position.y - TOP - TUNING.radius
		assert_gt(rise, 0.2, "height gained on the ramp from z = %.3f" % at)


## A flush object still gets its touch through its joined edge contact: the marble touches a
## pad flush with the floor while its centre is still over the floor, inside the contact
## margin of the pad's edge at z = 0.
func test_flush_object_gets_its_touch_at_the_seam() -> void:
	var pad: Pad = Pad.new()
	var pieces: Array[Node3D] = _floor(6.0, 0.0, 0.0, true)
	pieces.append(pad)
	start_run(FLAT, pieces)
	run.marble.teleport(Vector3(0.5, TOP + TUNING.radius, 0.5), Vector3(0, 0, -1))
	hold(rolling(Vector2(0, 1.0 / TUNING.max_roll_speed)), 1.0)
	assert_gt(pad.first_touch, 0.03, "first touch with the centre before the seam")


## Rolls the marble along -Z at x from START with the input that keeps speed, until it passes
## END or 6 s pass, and returns what it measured.
func _cross(speed: float, x: float) -> Crossing:
	var input: MarbleInput = rolling(Vector2(0, speed / TUNING.max_roll_speed))
	run.marble.teleport(Vector3(x, TOP + TUNING.radius, START), Vector3(0, 0, -speed))
	var crossing: Crossing = Crossing.new()
	for _i: int in 6 * Engine.physics_ticks_per_second:
		run.step(input)
		crossing.vertical = maxf(crossing.vertical, absf(run.state.velocity.y))
		crossing.upward = maxf(crossing.upward, run.state.velocity.y)
		if not run.state.on_ground:
			crossing.airborne += 1
		if run.state.position.z < END:
			break
	return crossing


## Returns the course along -Z, 4 m wide: a trimesh track from z = 6 to 0, a 4 m box door,
## four rows of two 2 m box tiles and a trimesh track to z = -18. Every piece after the first
## track rises by step; at 0 every top is flush at TOP.
func _course(step: float) -> Array[Node3D]:
	var pieces: Array[Node3D] = _floor(6.0, 0.0, 0.0, true)
	pieces.append_array(_floor(0.0, -4.0, step, false))
	for row: int in 4:
		pieces.append_array(_floor(-4.0 - 2.0 * row, -6.0 - 2.0 * row, step, false, 2))
	pieces.append_array(_floor(-12.0, -18.0, step, true))
	return pieces


## Returns a 4 m wide, 0.5 m thick floor from z = near to z = far with its top at TOP + rise,
## as `columns` Solids side by side: closed trimeshes when trimesh is true, else boxes.
func _floor(
	near: float, far: float, rise: float, trimesh: bool, columns: int = 1
) -> Array[Node3D]:
	var size: Vector3 = Vector3(4.0 / columns, 0.5, near - far)
	var out: Array[Node3D] = []
	for column: int in columns:
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
		var x: float = (column + 0.5) * size.x - 2.0
		solid.position = Vector3(x, TOP + rise - size.y / 2.0, (near + far) / 2.0)
		out.append(solid)
	return out


## Returns a 4 m wide, 12 m long box ramp Solid that climbs toward -Z at angle from its foot,
## the top edge at z = 0 and y = TOP, flush with a floor from _floor().
func _ramp(angle: float) -> Solid:
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(4, 0.5, 12)
	var shape: CollisionShape3D = CollisionShape3D.new()
	shape.shape = box
	var solid: Solid = Solid.new()
	solid.add_child(shape)
	var turn: Basis = Basis(Vector3.RIGHT, angle)
	var foot: Vector3 = turn * Vector3(0, box.size.y / 2.0, box.size.z / 2.0)
	solid.transform = Transform3D(turn, Vector3(0, TOP, 0) - foot)
	return solid
