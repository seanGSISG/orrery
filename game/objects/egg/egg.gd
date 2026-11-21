class_name Egg
extends LevelObject
## The `egg` marker: the level's hidden Clockwork Egg, a jewelled brass egg on a foot, 0.7 m
## tall. Put the marker on the floor. When the marble finds it, it tells the rules once and
## opens in OPEN_TIME: the lid tips back on its hinge, and the clockwork rises and spins. A
## restart closes it again; a checkpoint respawn keeps it open. A small warm light stands
## above the egg, so the room that hides it is not dark.
##
## The shapes come from res://objects/egg/egg.glb (tools/blender/egg.py, `just build-egg`):
## `shell`, `lid` with its origin on the hinge, and `gear` with its origin on its axis.

## Time to open, s.
const OPEN_TIME: float = 0.8
## The height of the widest ring, where the lid meets the shell, m.
const WAIST: float = 0.3
## The open lid's angle around the hinge at the back, rad.
const LID_ANGLE: float = 1.9
## Heights of the clockwork's origin when the egg is closed and when it is open, m.
const GEAR_DOWN: float = 0.2
const GEAR_UP: float = WAIST + 0.12
## Clockwork spin while open, rad/s.
const GEAR_SPIN: float = 3.0

var _found: bool = false
## Run time when the egg was found; negative until the next advance() after the find.
var _found_at: float = -1.0

@onready var _lid: Node3D = $Model/lid
@onready var _gear: Node3D = $Model/gear


## Starts closed, with the clockwork hidden.
func _ready() -> void:
	_pose(0.0, 0.0)


## Closes the egg again at a restart. A checkpoint respawn keeps it open.
func reset(restart: bool) -> void:
	if restart:
		_found = false
		_found_at = -1.0
		_pose(0.0, 0.0)


## Plays the opening from the run time.
func advance(_run: LevelRun, t: float) -> void:
	if not _found:
		return
	if _found_at < 0.0:
		_found_at = t
	_pose(clampf((t - _found_at) / OPEN_TIME, 0.0, 1.0), t)


## Finds the egg once, if the rules count it, and starts the opening.
func on_overlap(run: LevelRun, _first: bool) -> void:
	if _found or not run.rules.find_egg():
		return
	_found = true
	feedback.emit(&"egg.open", 1.0, _lid.global_position)


## Sets the lid and the clockwork for open (0 closed, 1 open) at run time t.
func _pose(open: float, t: float) -> void:
	var eased: float = smoothstep(0.0, 1.0, open)
	_lid.rotation.x = -LID_ANGLE * eased
	_gear.visible = open > 0.0
	_gear.position.y = lerpf(GEAR_DOWN, GEAR_UP, eased)
	_gear.rotation.y = t * GEAR_SPIN
