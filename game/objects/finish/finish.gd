class_name Finish
extends LevelObject
## The `finish` marker: a pad, 2 m wide. It stays closed until every gem is collected. Then its
## lens lights up and it shows a beam, and the marble that enters it ends the run. The pad is a
## raised plate of stone in a brass rim with a green lens (PadLook); while the finish is closed
## the lens is pale and does not glow.

const COLOUR: Color = Color(0.0, 0.62, 0.45)
## Radius of the pad, m: the trigger's radius.
const RADIUS: float = 1.0
## Glow of the open lens, times its colour.
const GLOW: float = 1.5

var _open: bool = false
var _lens: StandardMaterial3D = PadLook.lens(COLOUR, false, GLOW)

@onready var _pad: MeshInstance3D = $Mesh
@onready var _beam: GeometryInstance3D = $Beam


## Builds the pad and shows it closed.
func _ready() -> void:
	_pad.mesh = PadLook.mesh(RADIUS)
	PadLook.dress(_pad, _lens)
	_beam.set_instance_shader_parameter(&"colour", COLOUR)
	_show(false)


## Closes the finish again at a restart.
func reset(restart: bool) -> void:
	if restart:
		_show(false)


## Opens the finish on the tick after the last gem, and sounds `finish.open` unless the run has
## finished. Rules sounds `finish.reach` in the tick that finishes the run.
func advance(run: LevelRun, _t: float) -> void:
	var open: bool = run.state.gems_collected >= run.state.gems_total
	if open != _open:
		_show(open)
		if open and run.state.gems_total > 0 and run.state.status != &"finished":
			feedback.emit(&"finish.open", 1.0, global_position)


## Tells the rules that the marble is on the finish in this tick.
func on_overlap(run: LevelRun, _first: bool) -> void:
	run.rules.reach_finish(self)


## Lights the lens and shows the beam when open; makes the lens pale and hides the beam when
## closed.
func _show(open: bool) -> void:
	_open = open
	_beam.visible = open
	PadLook.light(_lens, COLOUR, open, GLOW)
