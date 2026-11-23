extends RunTest
## The land, through the boundary: a marble that leaves the floor lands on the grass, does not
## fall through it, and comes back on the start pad.

const RULES: PackedScene = preload("res://test/levels/rules.tscn")
const LAND: PackedScene = preload("res://objects/land/land.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The grass, just under the floor of rules.tscn (y = 0), as the land marker of a town.
const GRASS: float = -0.03
## A point past the floor's east edge, 1 m above the grass.
const FIELD: Vector3 = Vector3(30, 1, 0)


func test_land_holds_the_marble_and_puts_it_out_of_bounds() -> void:
	var land: Node3D = LAND.instantiate() as Node3D
	land.position = Vector3(0, GRASS, 0)
	start_run(RULES, [land])
	run.teleport(FIELD, Vector3.ZERO)
	var lowest: float = FIELD.y
	var ticks: int = 0
	var saw_respawning: bool = false
	while ticks < 240 and not (saw_respawning and run.state.status == &"playing"):
		run.step(MarbleInput.new())
		ticks += 1
		lowest = minf(lowest, run.state.position.y)
		saw_respawning = saw_respawning or run.state.status == &"respawning"
	assert_true(saw_respawning, "out of bounds")
	assert_gt(lowest, GRASS + TUNING.radius - 0.01, "held by the grass")
	assert_almost_eq(run.state.position, Vector3.UP * TUNING.radius, Vector3.ONE * 0.001)
