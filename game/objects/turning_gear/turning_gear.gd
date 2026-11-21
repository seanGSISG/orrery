class_name TurningGear
extends LevelObject
## The `turning_gear` marker: a toothed disc that turns at a steady speed round the marker's
## up axis (Blender z). A marble on its face, or in the notch between two teeth, rides round
## with it through friction. The top face is at the marker, and the disc reaches `thickness`
## down from it. Turn the marker to tilt the axis: a gear that stands on its rim is a lift, and
## its notches carry the marble up the rising side.

## Teeth stick out this far from the rim, m.
const TOOTH_LENGTH: float = 0.4
## Width of a tooth across the radius, m.
const TOOTH_WIDTH: float = 0.4
## Each tooth reaches this far into the disc, so that no gap opens at its corners, m.
const TOOTH_ROOT: float = 0.1

## Seconds for one full turn.
@export var period: float = 8.0
## True: clockwise seen from above the top face. False: counter-clockwise.
@export var clockwise: bool = false
## Radius to the tooth tips, m. A gear 4.2 m across has radius 2.1.
@export var radius: float = 2.1
## Size along the axis, m.
@export var thickness: float = 0.5
## Teeth round the rim. 0 gives a plain disc.
@export var teeth: int = 12

## Angular velocity, rad/s, in world space.
var _spin: Vector3 = Vector3.ZERO

@onready var _solid: Solid = $Solid


## Builds the disc and its teeth from the settings.
func _ready() -> void:
	var disc: CylinderShape3D = CylinderShape3D.new()
	disc.radius = radius - TOOTH_LENGTH if teeth > 0 else radius
	disc.height = thickness
	var shape: CollisionShape3D = $Solid/Shape
	shape.shape = disc
	shape.position.y = -thickness / 2.0
	var look: MeshInstance3D = $Solid/Mesh
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = disc.radius
	mesh.bottom_radius = disc.radius
	mesh.height = thickness
	look.mesh = mesh
	look.position = shape.position
	_add_teeth(look.material_override)
	if period > 0.0:
		_spin = global_basis.y.normalized() * (TAU / period) * (-1.0 if clockwise else 1.0)
	else:
		push_error("turning_gear %s: period must be above 0 s, got %.2f" % [name, period])


## Puts the gear at its start turn.
func reset(restart: bool) -> void:
	if restart:
		_place(0.0)
		_solid.reset_physics_interpolation()


## Turns the gear to its pose at run time t.
func advance(_run: LevelRun, t: float) -> void:
	_place(t)


## Adds one box Solid shape and one mesh for each tooth, spaced evenly round the rim. The first
## tooth points along the marker's x axis.
func _add_teeth(material: Material) -> void:
	var length: float = TOOTH_LENGTH + TOOTH_ROOT
	var size: Vector3 = Vector3(length, thickness, TOOTH_WIDTH)
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size
	for i: int in teeth:
		var turn: Basis = Basis(Vector3.UP, TAU * i / teeth)
		var pose: Transform3D = Transform3D(turn, turn * Vector3(radius - length / 2.0, 0, 0))
		pose.origin.y = -thickness / 2.0
		var shape: CollisionShape3D = CollisionShape3D.new()
		shape.shape = box
		shape.transform = pose
		_solid.add_child(shape)
		var look: MeshInstance3D = MeshInstance3D.new()
		look.mesh = mesh
		look.material_override = material
		look.transform = pose
		_solid.add_child(look)


## Moves the Solid to the gear's turn at run time t, with the gear's angular velocity.
func _place(t: float) -> void:
	var turn: float = 0.0
	if period > 0.0:
		turn = TAU * fposmod(t / period, 1.0) * (-1.0 if clockwise else 1.0)
	var basis: Basis = global_basis * Basis(Vector3.UP, turn)
	_solid.move(Transform3D(basis, global_position), Vector3.ZERO, _spin)
