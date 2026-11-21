class_name Gem
extends LevelObject
## The `gem` marker: a cut jewel, 0.5 m tall, that floats LIFT m above the marker and spins
## slowly. Put the marker on the floor. The marble collects the gem when it grazes the
## trigger; then the gem hides until a restart, and a checkpoint respawn keeps it collected.
## A faint beam above the gem shows it across the level. Each cut has its own shape and its
## own colour from Palette, which the colourblind setting changes.

## Gap between the floor and the gem's lowest point, m.
const LIFT: float = 0.3
## Height and girdle radius of the jewel, m.
const HEIGHT: float = 0.5
const RADIUS: float = 0.25
## Turn rate of the jewel, rad/s.
const SPIN: float = 1.2
## The number of sides of each cut: trillion, princess, hexagon, octagon.
const SIDES: Array[int] = [3, 4, 6, 8]

## The cut, 0 to 3. A negative value picks a cut from the node name, so the gems of a level
## mix without settings.
@export var cut: int = -1

var _collected: bool = false
## The cut in use, 0 to 3.
var _cut: int = 0

@onready var _jewel: MeshInstance3D = $Jewel
@onready var _glow: OmniLight3D = $Glow
@onready var _beam: GeometryInstance3D = $Beam


## Picks the cut, builds its jewel and follows the palette.
func _ready() -> void:
	_cut = (cut if cut >= 0 else absi(hash(String(name)))) % SIDES.size()
	_jewel.position.y = LIFT + HEIGHT * 0.6
	add_to_group(Palette.GROUP)
	apply_palette()


## Builds the jewel of the cut in its palette colour, and colours the glow and the beam.
func apply_palette() -> void:
	var colour: Color = Palette.gem(_cut)
	_jewel.mesh = _jewel_mesh(SIDES[_cut], colour)
	_glow.light_color = colour
	_beam.set_instance_shader_parameter(&"colour", colour)


## Shows the gem again at a restart. A checkpoint respawn keeps it collected.
func reset(restart: bool) -> void:
	if restart:
		_collected = false
		visible = true


## Turns the jewel from the run time.
func advance(_run: LevelRun, t: float) -> void:
	_jewel.rotation.y = t * SPIN


## Collects the gem once, if the rules count it, and hides it.
func on_overlap(run: LevelRun, _first: bool) -> void:
	if _collected or not run.rules.collect_gem():
		return
	_collected = true
	visible = false
	feedback.emit(&"gem.collect", 1.0, _jewel.global_position)


## A faceted jewel with flat facets: a crown from the girdle up to a flat table, and a
## pavilion from the girdle down to a point. The girdle is at y = 0.
static func _jewel_mesh(sides: int, colour: Color) -> ArrayMesh:
	var crown: float = HEIGHT * 0.4
	var pavilion: float = HEIGHT * 0.6
	var table: float = RADIUS * 0.55
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var top: Vector3 = Vector3(0, crown, 0)
	var tip: Vector3 = Vector3(0, -pavilion, 0)
	for i: int in sides:
		var a: float = TAU * i / sides
		var b: float = TAU * (i + 1) / sides
		var girdle_a: Vector3 = Vector3(cos(a), 0, sin(a)) * RADIUS
		var girdle_b: Vector3 = Vector3(cos(b), 0, sin(b)) * RADIUS
		var table_a: Vector3 = Vector3(cos(a) * table, crown, sin(a) * table)
		var table_b: Vector3 = Vector3(cos(b) * table, crown, sin(b) * table)
		_facet(tool, [top, table_a, table_b])
		_facet(tool, [table_a, girdle_a, girdle_b, table_b])
		_facet(tool, [girdle_a, tip, girdle_b])
	var mesh: ArrayMesh = tool.commit()
	var look: StandardMaterial3D = StandardMaterial3D.new()
	look.albedo_color = colour
	look.metallic = 0.2
	look.roughness = 0.15
	look.emission_enabled = true
	look.emission = colour
	look.emission_energy_multiplier = 1.2
	mesh.surface_set_material(0, look)
	return mesh


## Adds one flat facet with one normal: a convex polygon whose corners turn clockwise seen
## from outside, the front-face order of Godot and of F6 in docs/design/core-runtime.md.
static func _facet(tool: SurfaceTool, corners: Array[Vector3]) -> void:
	tool.set_normal((corners[2] - corners[0]).cross(corners[1] - corners[0]).normalized())
	for i: int in range(1, corners.size() - 1):
		tool.add_vertex(corners[0])
		tool.add_vertex(corners[i])
		tool.add_vertex(corners[i + 1])
