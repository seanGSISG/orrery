class_name Trapdoor
extends LevelObject
## The `trapdoor` marker: a floor panel that swings down open `delay` s after the marble first
## touches it, and swings shut again `close_after` s after it starts to open. While it is open,
## the marble falls through. The top face is at the marker, centred on it. The hinge runs along
## the marker's x axis at the bottom of the back edge (Blender -y), so the front edge drops. A
## respawn or a restart shuts the door at once. The door is a plate of the kit's brass
## (KitMaterials), so it reads as a hinged metal plate set into the stone.

## Seconds for the door to swing open, and again to swing shut.
const SWING: float = 0.3
## The open door hangs straight down.
const OPEN_ANGLE: float = PI / 2.0
## Gap round the panel that shows on screen, m. The collider has no gap.
const GAP: float = 0.02

## Seconds from the first touch until the door starts to open.
@export var delay: float = 0.5
## Seconds from the start of the drop until the door starts to shut.
@export var close_after: float = 5.0
## Panel size along the marker's x axis (the hinge), m.
@export var width: float = 4.0
## Panel size along the marker's forward axis (Blender y), m.
@export var depth: float = 4.0
## Panel size down from the top face, m.
@export var thickness: float = 0.5

## Run time of the touch that started the drop; INF while the door is shut and waits.
var _touched_at: float = INF
## True after trapdoor.open for the current drop.
var _opened: bool = false
## Run time of the current tick, from advance().
var _now: float = 0.0
## The hinge line in the marker's frame: the bottom of the back edge.
var _hinge: Vector3 = Vector3.ZERO

@onready var _solid: Solid = $Solid


## Sizes the panel round a Solid origin on the hinge line, so that the swing turns round it,
## and gives it the kit's brass.
func _ready() -> void:
	if delay < 0.0 or close_after < SWING:
		push_error("trapdoor %s: needs delay >= 0 and close_after >= %.2f s" % [name, SWING])
		delay = maxf(delay, 0.0)
		close_after = maxf(close_after, SWING)
	_hinge = Vector3(0, -thickness, depth / 2.0)
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(width, thickness, depth)
	var shape: CollisionShape3D = $Solid/Shape
	shape.shape = box
	shape.position = Vector3(0, thickness / 2.0, -depth / 2.0)
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = box.size - Vector3(GAP, 0, GAP)
	var look: MeshInstance3D = $Solid/Mesh
	look.mesh = mesh
	look.material_override = _plate_look()
	look.position = shape.position
	_place(-INF)


## Returns this door's brass: a copy of the kit brass whose texture spans the whole door once,
## so a large door shows no repeat.
func _plate_look() -> ShaderMaterial:
	var brass: ShaderMaterial = KitMaterials.find("brass").duplicate() as ShaderMaterial
	brass.set_shader_parameter("tile", maxf(width, depth))
	return brass


## Shuts the door at once and waits for the next touch.
func reset(_restart: bool) -> void:
	_touched_at = INF
	_opened = false
	_place(-INF)
	_solid.reset_physics_interpolation()


## Swings the door for run time t, emits trapdoor.open when the drop starts, and waits again
## once the door is shut.
func advance(_run: LevelRun, t: float) -> void:
	_now = t
	var drop: float = t - _touched_at - delay
	if drop >= close_after + SWING:
		_touched_at = INF
		_opened = false
		drop = -INF
	if drop >= 0.0 and not _opened:
		_opened = true
		feedback.emit(&"trapdoor.open", 0.6, global_position)
	_place(drop)


## Starts the drop on the first touch while the door is shut.
func on_touch(_run: LevelRun, _contact: Contact) -> void:
	if _touched_at == INF:
		_touched_at = _now


## Moves the Solid to the door pose at `drop` s after the drop starts (negative: shut), with
## the swing's angular velocity. Each swing eases out and in.
func _place(drop: float) -> void:
	var open: float = 0.0
	var speed: float = 0.0
	if drop >= close_after:
		var u: float = minf((drop - close_after) / SWING, 1.0)
		open = 0.5 + 0.5 * cos(PI * u)
		speed = -0.5 * PI / SWING * sin(PI * u)
	elif drop >= 0.0:
		var u: float = minf(drop / SWING, 1.0)
		open = 0.5 - 0.5 * cos(PI * u)
		speed = 0.5 * PI / SWING * sin(PI * u)
	var axis: Vector3 = global_basis.x.normalized()
	var basis: Basis = global_basis * Basis(Vector3.RIGHT, -OPEN_ANGLE * open)
	var hinge: Vector3 = global_transform * _hinge
	_solid.move(Transform3D(basis, hinge), Vector3.ZERO, axis * -OPEN_ANGLE * speed)
