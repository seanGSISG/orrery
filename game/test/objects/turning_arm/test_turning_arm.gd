extends RunTest
## Turning arms, through the boundary: a bar that turns on its period sweeps round the floor
## and pushes a marble in its way along the way it turns.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const ARM: PackedScene = preload("res://objects/turning_arm/turning_arm.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")


## Returns an arm on the floor, 5 cm up, that turns counter-clockwise once in period seconds:
## a bar 0.3 m wide from 0.5 m to 3 m along +x from its axis, given as its outline points.
func _arm(period: float) -> TurningArm:
	var arm: TurningArm = ARM.instantiate() as TurningArm
	arm.position = Vector3(0, 0.05, 0)
	arm.period = period
	for corner: Vector3 in [
		Vector3(0.5, 0, 0.15), Vector3(3.0, 0, 0.15), Vector3(3.0, 0, -0.15), Vector3(0.5, 0, -0.15)
	]:
		var point: Marker3D = Marker3D.new()
		point.position = corner
		arm.add_child(point)
	return arm


func test_arm_turns_on_its_period_and_pushes_a_marble_in_its_way() -> void:
	start_run(FLAT, [_arm(8.0)])
	# A quarter turn counter-clockwise (seen from above) takes the bar from +x to -z in 2 s.
	run.marble.teleport(Vector3(0, TUNING.radius, -2.0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 1.6)
	assert_almost_eq(run.state.velocity.length(), 0.0, 0.01, "the bar has not come round yet")
	hold(rolling(Vector2.ZERO), 0.8)
	# At 2 m from the axis the bar moves at 2π × 2 / 8 ≈ 1.6 m/s, along -x there.
	assert_lt(run.state.velocity.x, -1.0, "the bar pushes the marble the way it turns")
	assert_lt(run.state.position.x, -0.3, "the marble moved ahead of the bar")
	assert_almost_eq(run.state.position.y, TUNING.radius, 0.05, "pushed along the floor, not over")


func test_bar_takes_its_finish() -> void:
	var steel: Material = KitMaterials.find("blued_steel")
	assert_not_null(steel, "the kit has blued steel")
	var arm: TurningArm = _arm(8.0)
	arm.finish = steel
	add_child_autofree(arm)
	var look: MeshInstance3D = arm.get_node("Solid/Mesh") as MeshInstance3D
	assert_not_null(look.mesh, "the bar is built from its outline")
	assert_eq(look.material_override, steel)
