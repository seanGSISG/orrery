class_name Turner
extends LevelObject
## The motion that turning_gear and turning_arm share: the object's $Solid turns at a steady
## speed round the marker's up axis (Blender z), and a marble that touches it takes on the
## surface velocity there. The object starts at the marker's pose at run time 0. A subclass
## builds its shapes and look on $Solid in _ready(), then calls super() to start the turn.

## Seconds for one full turn.
@export var period: float = 8.0
## True: clockwise seen from above (the marker's up side). False: counter-clockwise.
@export var clockwise: bool = false

## Angular velocity, rad/s, in world space.
var _spin: Vector3 = Vector3.ZERO

@onready var _solid: Solid = $Solid


## Works out the angular velocity from period and clockwise.
func _ready() -> void:
	if period > 0.0:
		_spin = global_basis.y.normalized() * (TAU / period) * _way()
	else:
		push_error("%s: period must be above 0 s, got %.2f" % [name, period])


## Puts the object at its start turn.
func reset(restart: bool) -> void:
	if restart:
		_place(0.0)
		_solid.reset_physics_interpolation()


## Turns the object to its pose at run time t.
func advance(_run: LevelRun, t: float) -> void:
	_place(t)


## Returns 1 for a counter-clockwise turn and -1 for a clockwise one.
func _way() -> float:
	return -1.0 if clockwise else 1.0


## Moves the Solid to the turn at run time t, with the angular velocity.
func _place(t: float) -> void:
	var turn: float = 0.0
	if period > 0.0:
		turn = TAU * fposmod(t / period, 1.0) * _way()
	var basis: Basis = global_basis * Basis(Vector3.UP, turn)
	_solid.move(Transform3D(basis, global_position), Vector3.ZERO, _spin)
