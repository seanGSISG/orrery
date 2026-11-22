class_name Bumper
extends LevelObject
## The `bumper` marker: a drum that stands on the floor and pushes a marble that touches it
## away from its axis (the marker's up axis, Blender z) at `speed`. The push is across the
## floor, also from the top face, so a bumper never lifts the marble onto a ledge. A marble
## that already leaves faster keeps its speed. The bottom face is at the marker. Each push
## emits `bumper.hit` and makes the drum pulse. The drum is a band of enamel in the hazard
## colour of Palette between a base and a cap of the kit's brass (KitMaterials).

## Seconds that the pulse lasts.
const PULSE_TIME: float = 0.15
## The drum grows by this part of its radius at the peak of the pulse.
const PULSE_GROWTH: float = 0.15
## The brass base and cap: their height as shares of the drum's height, and how far they stand
## out from the enamel, m. The cap reaches CAP_PROUD above the top face, so it hides it.
const BASE_SHARE: float = 0.26
const CAP_SHARE: float = 0.22
const BRASS_PROUD: float = 0.035
const CAP_PROUD: float = 0.004

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


## Sizes the drum and its brass base and cap from the settings. The base and cap are children
## of the drum in the scene, so they pulse with it, and a mode that sets a range on every mesh
## of a level before the level's _ready (Ascent) finds them.
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
	var base: float = BASE_SHARE * height
	var cap: float = CAP_SHARE * height
	_ring($Solid/Mesh/Base as MeshInstance3D, base, (base - height) / 2.0)
	_ring($Solid/Mesh/Cap as MeshInstance3D, cap + CAP_PROUD, (height - cap + CAP_PROUD) / 2.0)
	add_to_group(Palette.GROUP)
	apply_palette()


## Makes part a brass ring of the drum: a cylinder `tall` m high that stands BRASS_PROUD out
## from the enamel, its middle `at` m above the drum's middle, with a small bevel on its top
## edge.
func _ring(part: MeshInstance3D, tall: float, at: float) -> void:
	var ring: CylinderMesh = CylinderMesh.new()
	ring.top_radius = radius + BRASS_PROUD - 0.012
	ring.bottom_radius = radius + BRASS_PROUD
	ring.height = tall
	part.mesh = ring
	part.material_override = KitMaterials.find("brass")
	part.position.y = at


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
