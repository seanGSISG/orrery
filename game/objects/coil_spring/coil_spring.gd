class_name CoilSpring
extends LevelObject
## The `coil_spring` marker: a brass coil that floats above the marker and turns slowly. Put
## the marker on the floor. The marble takes it into the power-up slot when it touches the
## trigger and the slot is empty; while the slot is full, the pickup stays. A taken pickup
## hides and comes back respawn_delay s later, and at a restart. A checkpoint respawn does not
## change the wait. The `use` button then launches the marble along up (CoilSpringPowerUp).
## Feedback: `coil_spring.pickup` here, and `coil_spring.use` from the slot.

## Coil size, m: height, radius of the turns, radius of the wire. The scene puts the bottom of
## the coil 0.3 m above the floor.
const HEIGHT: float = 0.4
const RADIUS: float = 0.17
const WIRE: float = 0.025
const TURNS: float = 4.0
## Turn rate of the coil, rad/s.
const SPIN: float = 1.2
const BRASS: Color = Color(0.85, 0.62, 0.25)

## Speed along up after the use, m/s. 20 m/s rises 10 m at gravity 20 m/s².
@export var launch_speed: float = 20.0
## Time from the pickup to the return of the pickup, s.
@export var respawn_delay: float = 5.0

## Run time at which the pickup is back. It is in place while the run time is at or past it.
var _back_at: float = 0.0
## The run time of this tick, from advance().
var _t: float = 0.0

@onready var _coil: MeshInstance3D = $Coil


## Builds the coil mesh.
func _ready() -> void:
	_coil.mesh = _coil_mesh()


## Puts the pickup back in place at a restart. A checkpoint respawn keeps the wait.
func reset(restart: bool) -> void:
	if restart:
		_back_at = 0.0
		_t = 0.0
		visible = true


## Turns the coil and shows the pickup again when its wait is over.
func advance(_run: LevelRun, t: float) -> void:
	_t = t
	visible = t >= _back_at
	_coil.rotation.y = t * SPIN


## Gives a Coil Spring to the slot while the pickup is in place; hides the pickup if the slot
## takes it.
func on_overlap(run: LevelRun, _first: bool) -> void:
	if _t < _back_at or not run.slot.take(CoilSpringPowerUp.new(launch_speed)):
		return
	_back_at = _t + respawn_delay
	visible = false
	feedback.emit(&"coil_spring.pickup", 1.0, _coil.global_position)


## A helix of round wire around y, from y = 0 to HEIGHT, with flat end turns.
static func _coil_mesh() -> ArrayMesh:
	var steps: int = 96
	var sides: int = 8
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i: int in steps + 1:
		var f: float = float(i) / steps
		var angle: float = TAU * TURNS * f
		var centre: Vector3 = Vector3(cos(angle) * RADIUS, _rise(f) * HEIGHT, sin(angle) * RADIUS)
		var out: Vector3 = Vector3(cos(angle), 0.0, sin(angle))
		for j: int in sides:
			var a: float = TAU * j / sides
			var normal: Vector3 = out * cos(a) + Vector3.UP * sin(a)
			tool.set_normal(normal)
			tool.add_vertex(centre + normal * WIRE)
	for i: int in steps:
		for j: int in sides:
			var a: int = i * sides + j
			var b: int = i * sides + (j + 1) % sides
			tool.add_index(a)
			tool.add_index(a + sides)
			tool.add_index(b)
			tool.add_index(b)
			tool.add_index(a + sides)
			tool.add_index(b + sides)
	var mesh: ArrayMesh = tool.commit()
	var look: StandardMaterial3D = StandardMaterial3D.new()
	look.albedo_color = BRASS
	look.metallic = 0.8
	look.roughness = 0.3
	look.emission_enabled = true
	look.emission = BRASS
	look.emission_energy_multiplier = 0.4
	look.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.surface_set_material(0, look)
	return mesh


## Height of the helix at f (0..1) along the wire, 0..1. The first and the last half turn stay
## flat, so the coil stands on its end turns.
static func _rise(f: float) -> float:
	var flat: float = 0.5 / TURNS
	return clampf((f - flat) / (1.0 - 2.0 * flat), 0.0, 1.0)
