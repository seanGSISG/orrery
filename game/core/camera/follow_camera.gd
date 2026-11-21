class_name FollowCamera
extends Camera3D
## Third-person orbit camera (docs/plan.md §2.4). Set run, add the camera to the run, and make
## it current. Each tick, after the run steps, it orbits the marble at the yaw and pitch of the
## run's last MarbleInput, pulls in when a Solid blocks the view, turns smoothly to the
## marble's up, shakes on hard landings, and puts the BlobShadow under the marble.
##
## It moves only in _physics_process, so Godot's physics interpolation draws the camera, the
## marble and the shadow between ticks on displays faster than the 120 Hz tick.

## A focus move longer than this in one tick is a teleport (restart, respawn): the camera
## snaps instead of smoothing, m.
const SNAP_DISTANCE: float = 1.0
## Radius of the cast that finds the far face of a thin Solid, m. The camera stops this far
## inside that face, so it sees the face from behind.
const INSIDE: float = 0.02

## Turn camera shake off or on (the accessibility setting of docs/plan.md §2.13). It applies
## to every camera, also to cameras made later.
static var shake_enabled: bool = true

## Distance from the marble centre when nothing blocks the view, m.
@export var distance: float = 2.5
## Closest distance from the marble centre, m, so the camera never goes into the marble. When
## a Solid is nearer (the marble rests against a wall behind it), the camera goes into the
## Solid: faces seen from behind are not drawn, so the marble stays in view. When the Solid is
## thinner than that, the camera stops inside it, not past it.
@export var min_distance: float = 0.5
## Radius of the sphere that keeps the camera away from Solids, m. Keep it below the marble
## radius: the cast starts at the marble centre and ignores a Solid that it already overlaps.
## The camera reads it each tick.
@export var clearance: float = 0.15
## Vertical field of view, degrees. The camera sets Camera3D.fov from it each tick.
@export var field_of_view: float = 75.0
## How fast the camera's up turns to a new up, 1/s. 6 turns 95% of the way in 0.5 s.
@export var up_rate: float = 6.0
## How fast the camera moves back out after a pull-in, 1/s. A pull-in is instant.
@export var return_rate: float = 4.0
## Landing strength (of &"marble.land" feedback, 0..1) from which the camera shakes.
@export var hard_landing: float = 0.5
## Largest shake angle, radians.
@export var shake_angle: float = 0.03
## Shake decay, per second: a full shake stops after 1 / shake_decay seconds.
@export var shake_decay: float = 2.5

## The run to follow.
var run: LevelRun

## The shadow under the marble. The camera places it each tick.
var shadow: BlobShadow = BlobShadow.new()

## The cast at clearance, made again when clearance changes.
var _world: WorldQuery
var _world_radius: float = 0.0
## The thin cast that finds the far face of a thin Solid.
var _inside: WorldQuery
## Yaw reference, as Marble.frame: y is the marble's up, and it turns by the shortest arc.
var _frame: Basis = Basis.IDENTITY
## The camera's up, which turns toward the marble's up at up_rate.
var _up: Vector3 = Vector3.UP
## The distance after pull-in and return.
var _distance: float = 0.0
## The focus of the last tick; INF before the first tick.
var _focus: Vector3 = Vector3.INF
## Shake left, 0..1. The shake angle is shake_angle × _shake².
var _shake: float = 0.0
var _time: float = 0.0


## Adds the shadow and listens to the run's feedback for landings.
func _ready() -> void:
	process_physics_priority = 1
	add_child(shadow)
	_inside = WorldQuery.new(get_world_3d().direct_space_state, INSIDE, 0.0)
	if run != null:
		run.feedback.connect(_on_feedback)


## Follows the run after its step: priority 1 runs after the run's own _physics_process.
func _physics_process(delta: float) -> void:
	if run != null:
		follow(run.state, run.last_input, delta)


## Places the camera and the shadow for one tick of dt seconds from the marble in state and
## the camera angles in input. Pitch stays within the PlayerSource limits.
func follow(state: GameState, input: MarbleInput, dt: float) -> void:
	_frame = (Basis(Quaternion(_frame.y, state.up)) * _frame).orthonormalized()
	var snap: bool = state.position.distance_to(_focus) > SNAP_DISTANCE
	_focus = state.position
	if snap:
		_up = state.up
		_shake = 0.0
	else:
		var turn: Quaternion = Quaternion(_up, state.up)
		_up = (Quaternion.IDENTITY.slerp(turn, _rate(up_rate, dt)) * _up).normalized()
	var pitch: float = clampf(input.camera_pitch, PlayerSource.PITCH_MIN, PlayerSource.PITCH_MAX)
	var tilt: Basis = Basis(Quaternion(_frame.y, _up))
	var view: Basis = tilt * _frame * Basis(Vector3.UP, input.camera_yaw)
	view = view * Basis(Vector3.RIGHT, pitch)
	var open: float = _open_distance(view.z)
	if snap or open < _distance:
		_distance = open
	else:
		_distance = lerpf(_distance, open, _rate(return_rate, dt))
	fov = field_of_view
	global_transform = Transform3D(view * _shake_turn(dt), _focus + view.z * _distance)
	shadow.place(_focus, state.up)
	if snap:
		_reset_interpolation()


## Returns the camera distance along back (a unit vector) at which no Solid hides the marble.
## It is where the clearance cast from the focus stops, but at least min_distance. When
## min_distance puts the camera past the far face of a thin Solid, the camera moves in to just
## inside that face: from there it sees the Solid's faces from behind, which are not drawn.
func _open_distance(back: Vector3) -> float:
	if _world == null or _world_radius != clearance:
		_world = WorldQuery.new(get_world_3d().direct_space_state, clearance, 0.0)
		_world_radius = clearance
	var open: float = distance * _world.sweep(_focus, back * distance)
	if open >= min_distance:
		return open
	# The thin cast ignores a Solid that the camera is already in, and the back faces of
	# a Solid around it, so it stops only at a far face that the camera sees from the front.
	var eye: Vector3 = _focus + back * min_distance
	var past: float = min_distance * _inside.sweep(eye, -back * min_distance)
	return min_distance if past >= min_distance else min_distance - past - 2.0 * INSIDE


## Returns the small turn of the camera for the shake left, and lets the shake decay.
func _shake_turn(dt: float) -> Basis:
	_time += dt
	_shake = maxf(_shake - shake_decay * dt, 0.0)
	var angle: float = shake_angle * _shake * _shake
	# Sums of sines at unrelated frequencies give a smooth shake without random jumps.
	var x: float = sin(_time * 47.0) + 0.5 * sin(_time * 83.0 + 1.3)
	var y: float = sin(_time * 59.0 + 2.1) + 0.5 * sin(_time * 97.0 + 0.4)
	return Basis(Vector3.RIGHT, angle * x / 1.5) * Basis(Vector3.UP, angle * y / 1.5)


## Starts a shake when the marble lands hard and shake is on.
func _on_feedback(kind: StringName, strength: float, _at: Vector3) -> void:
	if kind == &"marble.land" and shake_enabled and strength >= hard_landing:
		_shake = maxf(_shake, strength)


## After a teleport, draws the camera, the shadow and the marble at their new place at once,
## not on a path from the old place.
func _reset_interpolation() -> void:
	reset_physics_interpolation()
	if run != null and run.marble != null:
		run.marble.reset_physics_interpolation()


## Returns the part of the way that exponential smoothing at rate covers in dt seconds.
static func _rate(rate: float, dt: float) -> float:
	return 1.0 - exp(-rate * dt)
