class_name Gem
extends LevelObject
## The `gem` marker: a cut jewel of coloured glass, GemCut.SIZE m across, that floats LIFT m
## above the marker and spins slowly. Put the marker on the floor. The marble collects the gem
## when it grazes the trigger; then the gem hides until a restart, and a checkpoint respawn
## keeps it collected. A faint short beam stands above the gem, and a small light below it
## marks its place on the floor, because the gem casts no shadow. Each cut has its own shape
## (GemCut) and its own colour from Palette, which the colourblind setting changes.

## Gap between the floor and the gem's lowest point, m.
const LIFT: float = 0.3
## Turn rate of the jewel, rad/s.
const SPIN: float = 1.2

## The cut, 0 to GemCut.COUNT - 1. A negative value picks a cut from the node name, so the
## gems of a level mix without settings.
@export var cut: int = -1

var _collected: bool = false
## The cut in use.
var _cut: int = 0
## The jewel's turn at run time 0, rad. It differs from gem to gem, so that the gems of a
## level do not glint all at once.
var _turn: float = 0.0

@onready var _jewel: MeshInstance3D = $Jewel
@onready var _glow: OmniLight3D = $Glow
@onready var _beam: MeshInstance3D = $Beam


## Picks the cut, puts its jewel and the beam in place and follows the palette.
func _ready() -> void:
	_cut = posmod(cut if cut >= 0 else hash(String(name)), GemCut.COUNT)
	var shape: GemCut = GemCut.of(_cut)
	_jewel.mesh = shape.mesh
	_jewel.position.y = LIFT - shape.bottom
	# The beam starts at the top of the jewel.
	var beam: CylinderMesh = _beam.mesh as CylinderMesh
	_beam.position.y = LIFT + shape.top - shape.bottom + beam.height / 2
	_turn = fposmod(global_position.x * 1.7 + global_position.z * 2.3, TAU)
	add_to_group(Palette.GROUP)
	apply_palette()


## Colours the jewel, the light and the beam from the palette, and gives the jewel the
## lightness of its colour in that palette.
func apply_palette() -> void:
	var colour: Color = Palette.gem(_cut)
	_jewel.set_instance_shader_parameter(&"colour", colour)
	_jewel.set_instance_shader_parameter(&"lightness", Palette.gem_lightness(_cut))
	_glow.light_color = colour
	_beam.set_instance_shader_parameter(&"colour", colour)


## Shows the gem again at a restart. A checkpoint respawn keeps it collected.
func reset(restart: bool) -> void:
	if restart:
		_collected = false
		visible = true


## Turns the jewel from the run time.
func advance(_run: LevelRun, t: float) -> void:
	_jewel.rotation.y = _turn + t * SPIN


## Collects the gem once, if the rules count it, and hides it.
func on_overlap(run: LevelRun, _first: bool) -> void:
	if _collected or not run.rules.collect_gem():
		return
	_collected = true
	visible = false
	feedback.emit(&"gem.collect", 1.0, _jewel.global_position)
