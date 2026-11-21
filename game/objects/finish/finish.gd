class_name Finish
extends LevelObject
## The `finish` marker: a pad, 2 m wide. It stays dark and closed until every gem is
## collected. Then it lights up and shows a beam, and the marble that enters it ends the run.

const COLOUR: Color = Color(0.0, 0.62, 0.45)

var _open: bool = false
var _reached: bool = false
var _look: StandardMaterial3D = StandardMaterial3D.new()

@onready var _pad: MeshInstance3D = $Mesh
@onready var _beam: GeometryInstance3D = $Beam


## Gives the pad its own material and shows it closed.
func _ready() -> void:
	_pad.material_override = _look
	_beam.set_instance_shader_parameter(&"colour", COLOUR)
	_show(false)


## Closes the finish again at a restart.
func reset(restart: bool) -> void:
	if restart:
		_reached = false
		_show(false)


## Opens the finish on the tick after the last gem, and sounds on the tick after the run
## finished.
func advance(run: LevelRun, _t: float) -> void:
	if run.state.status == &"finished" and not _reached:
		_reached = true
		feedback.emit(&"finish.reach", 1.0, global_position)
	var open: bool = run.state.gems_collected >= run.state.gems_total
	if open == _open:
		return
	_show(open)
	if open and run.state.gems_total > 0:
		feedback.emit(&"finish.open", 1.0, global_position)


## Tells the rules that the marble is on the finish in this tick.
func on_overlap(run: LevelRun, _first: bool) -> void:
	run.rules.reach_finish()


## Lights the pad and shows the beam when open; dims both when closed.
func _show(open: bool) -> void:
	_open = open
	_beam.visible = open
	_look.albedo_color = COLOUR if open else Color(0.22, 0.26, 0.25)
	_look.emission_enabled = open
	_look.emission = COLOUR
	_look.emission_energy_multiplier = 1.5
