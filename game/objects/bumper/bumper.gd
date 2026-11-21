class_name Bumper
extends LevelObject
## The `bumper` marker: a drum that stands on the floor and pushes a marble that touches it
## away from its axis (the marker's up axis, Blender z) at `speed`. The push is across the
## floor, also from the top face, so a bumper never lifts the marble onto a ledge. A marble
## that already leaves faster keeps its speed. The bottom face is at the marker. Each push
## emits `bumper.hit` and makes the drum pulse. The drum has the hazard colour of Palette.

## Seconds that the pulse lasts.
const PULSE_TIME: float = 0.15
## The drum grows by this part of its radius at the peak of the pulse.
const PULSE_GROWTH: float = 0.15

## Speed away from the axis after a push, m/s.
@export var speed: float = 15.0
## Radius of the drum, m.
@export var radius: float = 0.5
## Height of the drum above the marker, m.
@export var height: float = 1.0

## Run time of this tick, s. advance() sets it before the marble moves.
var _t: float = 0.0
## Run time of the last push, s.
var _pushed_at: float = -INF

@onready var _solid: Solid = $Solid
@onready var _look: MeshInstance3D = $Solid/Mesh


## Sizes the drum from the settings.
func _ready() -> void:
	var drum: CylinderShape3D = CylinderShape3D.new()
	drum.radius = radius
	drum.height = height
	var shape: CollisionShape3D = $Solid/Shape
	shape.shape = drum
	shape.position.y = height / 2.0
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	_look.mesh = mesh
	_look.position = shape.position
	add_to_group(Palette.GROUP)
	apply_palette()


## Colours the drum with the hazard colour of the palette. Every bumper shares the material.
func apply_palette() -> void:
	(_look.material_override as StandardMaterial3D).albedo_color = Palette.hazard()


## Ends a pulse.
func reset(_restart: bool) -> void:
	_pushed_at = -INF
	_look.scale = Vector3.ONE


## Records the run time and shows the pulse at that time.
func advance(_run: LevelRun, t: float) -> void:
	_t = t
	var k: float = (t - _pushed_at) / PULSE_TIME
	var grow: float = PULSE_GROWTH * sin(PI * k) if k < 1.0 else 0.0
	_look.scale = Vector3(1.0 + grow, 1.0, 1.0 + grow)


## Raises the marble's speed away from the axis to `speed`, relative to the drum. Emits
## bumper.hit with the part of `speed` that the push added.
func on_touch(run: LevelRun, contact: Contact) -> void:
	var axis: Vector3 = global_basis.y.normalized()
	var out: Vector3 = run.marble.position - global_position
	out -= axis * out.dot(axis)
	# A marble on the centre of the top face has no direction away from the axis.
	out = out.normalized() if out.length() > 0.001 else global_basis.x.normalized()
	var rise: float = speed - (run.marble.velocity - contact.velocity).dot(out)
	if rise <= 0.0:
		return
	run.marble.add_velocity(out * rise)
	_pushed_at = _t
	feedback.emit(&"bumper.hit", minf(rise / speed, 1.0), contact.point)
