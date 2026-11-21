extends RunTest
## The marble's look through the boundary: MarbleInput in, node transforms out. The brass core
## of the skin must turn with the roll, because the core shows the player the roll.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")


## Forward input rolls toward -Z. The core turns about -X by the spin of each tick.
func test_core_turns_with_the_roll() -> void:
	start_run(FLAT)
	var core: Node3D = run.marble.get_node(^"Ball/Skin/Core") as Node3D
	var start: Basis = core.global_basis
	var tick: float = 1.0 / Engine.physics_ticks_per_second
	var rolled: float = 0.0
	for _i: int in 20:
		run.step(rolling(Vector2(0, 1)))
		rolled += run.state.spin.length() * tick
	var turn: Quaternion = (core.global_basis * start.inverse()).get_rotation_quaternion()
	assert_gt(rolled, 0.5, "the marble rolls")
	assert_almost_eq(turn.get_angle(), rolled, 0.01)
	assert_almost_eq(turn.get_axis(), Vector3.LEFT, Vector3.ONE * 0.01)
