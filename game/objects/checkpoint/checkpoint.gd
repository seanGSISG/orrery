class_name Checkpoint
extends LevelObject
## The `checkpoint` marker: a pad, 1.5 m wide. When the marble reaches it, the next fall
## respawns the marble on it. It glows while it is the last checkpoint.

const COLOUR: Color = Color(0.34, 0.71, 0.91)

var _lit: bool = false
var _look: StandardMaterial3D = StandardMaterial3D.new()

@onready var _pad: MeshInstance3D = $Mesh


## Gives the pad its own material and shows it unlit.
func _ready() -> void:
	_pad.material_override = _look
	_light(false)


## Lights the pad while the rules name it as the last checkpoint.
func advance(run: LevelRun, _t: float) -> void:
	var lit: bool = run.state.checkpoint == name
	if lit != _lit:
		_light(lit)


## Tells the rules when the marble enters a checkpoint that is not the last one.
func on_overlap(run: LevelRun, first: bool) -> void:
	if not first or run.state.checkpoint == name:
		return
	run.rules.reach_checkpoint(self)
	if run.state.checkpoint == name:
		feedback.emit(&"checkpoint.reach", 1.0, global_position)


## Makes the pad bright and glowing when lit, dim when not.
func _light(lit: bool) -> void:
	_lit = lit
	_look.albedo_color = COLOUR if lit else COLOUR.darkened(0.6)
	_look.emission_enabled = lit
	_look.emission = COLOUR
	_look.emission_energy_multiplier = 1.0
