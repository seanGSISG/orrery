extends RunTest
## Turning gears, through the boundary: a marble that rests on a flat gear rides round with
## it, and a gear that stands on its rim lifts a marble in a notch between two teeth.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const GEAR: PackedScene = preload("res://objects/turning_gear/turning_gear.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The top face of the flat gear, m.
const TOP: Vector3 = Vector3(0, 1, 0)


## Returns a gear with the top face centre at `at` that turns once in period seconds.
func _gear(at: Vector3, period: float, clockwise: bool) -> TurningGear:
	var gear: TurningGear = GEAR.instantiate() as TurningGear
	gear.position = at
	gear.period = period
	gear.clockwise = clockwise
	return gear


## Returns the angle of the marble round the y axis through TOP, counter-clockwise seen from
## above, from +x.
func _angle() -> float:
	var offset: Vector3 = run.state.position - TOP
	return atan2(-offset.z, offset.x)


## Starts a run with a flat gear and puts the marble still on the face, 1.2 m out along +x.
func _ride(clockwise: bool) -> void:
	start_run(FLAT, [_gear(TOP, 8.0, clockwise)])
	run.marble.teleport(TOP + Vector3(1.2, TUNING.radius, 0), Vector3.ZERO)


func test_marble_rides_round_on_a_flat_gear() -> void:
	_ride(false)
	hold(rolling(Vector2.ZERO), 2.0)
	assert_almost_eq(_angle(), PI / 2.0, 0.25, "a quarter turn in 2 s")
	hold(rolling(Vector2.ZERO), 6.0)
	assert_almost_eq(_angle(), 0.0, 0.3, "a full turn in 8 s")
	var offset: Vector3 = run.state.position - TOP
	assert_almost_eq(offset.y, TUNING.radius, 0.02, "the marble is on the face")
	assert_almost_eq(Vector2(offset.x, offset.z).length(), 1.2, 0.3, "it stays near its radius")
	assert_true(run.state.on_ground)


func test_clockwise_gear_turns_the_other_way() -> void:
	_ride(true)
	hold(rolling(Vector2.ZERO), 2.0)
	assert_almost_eq(_angle(), -PI / 2.0, 0.25)


func test_gear_on_its_rim_lifts_the_marble_in_a_notch() -> void:
	# The axis lies along +z, so the +x side rises. Tooth 0 points along +x, and tooth 1 is
	# 30° above it; the notch between them holds the marble against the rim.
	var gear: TurningGear = _gear(Vector3(0, 4, 0.25), 12.0, false)
	gear.basis = Basis(Vector3.RIGHT, PI / 2.0)
	start_run(FLAT, [gear])
	var notch: float = PI / 12.0
	var rim: float = gear.radius - TurningGear.TOOTH_LENGTH + TUNING.radius
	var at: Vector3 = Vector3(cos(notch) * rim, 4 + sin(notch) * rim, 0)
	run.marble.teleport(at, Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 2.0)
	# 2 s is 60° of turn, so the notch is now at 75°.
	assert_gt(run.state.position.y, 4.0 + rim * 0.9, "the marble rose with the notch")
	assert_lt(absf(run.state.position.z), 0.25, "it stays on the gear")


func test_disc_and_teeth_are_the_kit_brass() -> void:
	var gear: TurningGear = _gear(TOP, 8.0, false)
	add_child_autofree(gear)
	var brass: Material = KitMaterials.find("brass")
	var looks: int = 0
	for node: Node in gear.get_node("Solid").get_children():
		var look: MeshInstance3D = node as MeshInstance3D
		if look != null:
			assert_eq(look.material_override, brass)
			looks += 1
	assert_eq(looks, gear.teeth + 1, "the disc and every tooth")
