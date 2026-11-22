class_name Checkpoint
extends LevelObject
## The `checkpoint` marker: a pad, 1.5 m wide. When the marble reaches it, the next fall
## respawns the marble on it. The pad is a raised plate of stone in a brass rim with a blue
## lens (PadLook); the lens glows while the pad is the last checkpoint.

const COLOUR: Color = Color(0.34, 0.71, 0.91)
## Radius of the pad, m: the trigger's radius.
const RADIUS: float = 0.75
## Glow of the lit lens, times its colour.
const GLOW: float = 1.0

var _lit: bool = false
var _lens: StandardMaterial3D = PadLook.lens(COLOUR, false, GLOW)

@onready var _pad: MeshInstance3D = $Mesh


## Builds the pad and shows it unlit.
func _ready() -> void:
	_pad.mesh = PadLook.mesh(RADIUS)
	PadLook.dress(_pad, _lens)
	_light(false)


## Puts the light out at a restart. A respawn keeps it.
func reset(restart: bool) -> void:
	if restart:
		_light(false)


## Lights the pad while it is the rules' last checkpoint.
func advance(run: LevelRun, _t: float) -> void:
	var lit: bool = run.rules.checkpoint == self
	if lit != _lit:
		_light(lit)


## Tells the rules when the marble enters the checkpoint.
func on_overlap(run: LevelRun, first: bool) -> void:
	if first and run.rules.reach_checkpoint(self):
		feedback.emit(&"checkpoint.reach", 1.0, global_position)


## Makes the lens glow when lit, and pale when not.
func _light(lit: bool) -> void:
	_lit = lit
	PadLook.light(_lens, COLOUR, lit, GLOW)
