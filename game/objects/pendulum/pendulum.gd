class_name Pendulum
extends LevelObject
## The `pendulum` marker: a rod and a ball bob that hang from a pivot at the marker and swing
## round the marker's forward axis (Blender y), so the bob moves along the marker's x axis.
## Point the forward axis along the track and the bob swings across it. The bob knocks a
## marble aside: the marble solver bounces the marble off the moving bob. Each hit emits
## `pendulum.hit`. For a bob that sweeps the track, put the pivot about length + radius m
## above it. At t = 0 (with offset 0) the bob hangs straight down and moves toward +x.

## Radius of the rod, m.
const ROD_RADIUS: float = 0.08
## The bob must move toward the marble faster than this for a hit, m/s.
const HIT_SPEED: float = 0.5

## Seconds for one full swing, there and back.
@export var period: float = 4.0
## Largest angle from straight down, to each side, degrees.
@export var swing: float = 60.0
## Pivot to bob centre, m.
@export var length: float = 4.0
## Radius of the bob, m.
@export var radius: float = 0.6
## Seconds into the swing at t = 0. Give the second of two pendulums period / 2.
@export var offset: float = 0.0

## True when the marble touched the pendulum in this tick.
var _touching: bool = false
## True when the marble touched the pendulum in the last tick.
var _touched: bool = false

@onready var _solid: Solid = $Solid


## Sizes the rod and the bob from the settings.
func _ready() -> void:
	var rod: CylinderShape3D = CylinderShape3D.new()
	rod.radius = ROD_RADIUS
	rod.height = length
	var rod_mesh: CylinderMesh = CylinderMesh.new()
	rod_mesh.top_radius = ROD_RADIUS
	rod_mesh.bottom_radius = ROD_RADIUS
	rod_mesh.height = length
	_size(&"Rod", rod, rod_mesh, -length / 2.0)
	var bob: SphereShape3D = SphereShape3D.new()
	bob.radius = radius
	var bob_mesh: SphereMesh = SphereMesh.new()
	bob_mesh.radius = radius
	bob_mesh.height = radius * 2.0
	_size(&"Bob", bob, bob_mesh, -length)
	if period <= 0.0:
		push_error("pendulum %s: period must be above 0 s, got %.2f" % [name, period])


## Puts the pendulum at its start angle.
func reset(restart: bool) -> void:
	_touching = false
	_touched = false
	if restart:
		_place(0.0)
		_solid.reset_physics_interpolation()


## Swings the pendulum to its pose at run time t.
func advance(_run: LevelRun, t: float) -> void:
	_touched = _touching
	_touching = false
	_place(t)


## Emits pendulum.hit when the marble's first touch in a row meets a bob that moves toward
## it. The strength is that speed over MarbleTuning.hard_impact_speed.
func on_touch(run: LevelRun, contact: Contact) -> void:
	var closing: float = contact.velocity.dot(contact.normal)
	if not _touched and closing > HIT_SPEED:
		var strength: float = minf(closing / run.marble.tuning.hard_impact_speed, 1.0)
		feedback.emit(&"pendulum.hit", strength, contact.point)
	_touching = true


## Gives the part's Shape and Mesh nodes (RodShape and RodMesh for &"Rod") their resources,
## `down` m down the rod from the pivot.
func _size(part: StringName, form: Shape3D, mesh: Mesh, down: float) -> void:
	var shape: CollisionShape3D = _solid.get_node(NodePath(part + "Shape"))
	shape.shape = form
	shape.position.y = down
	var look: MeshInstance3D = _solid.get_node(NodePath(part + "Mesh"))
	look.mesh = mesh
	look.position.y = down


## Moves the Solid to the swing angle at run time t, with the swing's angular velocity.
func _place(t: float) -> void:
	var angle: float = 0.0
	var rate: float = 0.0
	if period > 0.0:
		var phase: float = TAU * fposmod((t + offset) / period, 1.0)
		var amplitude: float = deg_to_rad(swing)
		angle = amplitude * sin(phase)
		rate = amplitude * TAU / period * cos(phase)
	# A turn round +z by a positive angle takes the bob at -y toward +x.
	var axis: Vector3 = (global_basis * Vector3.BACK).normalized()
	var basis: Basis = global_basis * Basis(Vector3.BACK, angle)
	_solid.move(Transform3D(basis, global_position), Vector3.ZERO, axis * rate)
