extends RunTest
## Crumbling tiles, through the boundary: a touched tile cracks, holds the marble for `delay` s,
## then falls and stays gone while the other tiles hold. A respawn or a restart brings every
## tile back. The built fixture levels/test/floors.py has the marker settings.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const TILES: PackedScene = preload("res://objects/crumbling_tiles/crumbling_tiles.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
const FIXTURE: String = "res://levels/built/floors.glb"
## Top centre of the test grid: 4 x 4 m of 2 m tiles.
const GRID: Vector3 = Vector3(6, 6, 0)
## Top centres of two tiles of the test grid.
const TILE_A: Vector3 = GRID + Vector3(1, 0, 1)
const TILE_B: Vector3 = GRID + Vector3(-1, 0, -1)
## The fixture's crumbling_tiles marker, Blender (0, 20, 0), in Godot axes.
const FIXTURE_GRID: Vector3 = Vector3(0, 0, -20)

## Kinds of the run's feedback in this test, in order.
var heard: Array[StringName] = []


func before_each() -> void:
	heard.clear()


func test_touched_tile_cracks_holds_for_the_delay_then_falls() -> void:
	_start(FLAT, [TILES.instantiate() as CrumblingTiles])
	_put_on(TILE_A)
	hold(MarbleInput.new(), 0.45)
	_assert_on(TILE_A)
	assert_eq(heard.count(&"tile.crack"), 1)
	assert_false(heard.has(&"tile.fall"), "the tile still holds")
	hold(MarbleInput.new(), 1.0)
	assert_eq(heard.count(&"tile.fall"), 1)
	assert_lt(run.state.position.y, GRID.y - 2.0, "the marble fell through")


func test_marble_on_a_seam_cracks_the_tiles_on_both_sides() -> void:
	_start(FLAT, [TILES.instantiate() as CrumblingTiles])
	# On the seam between TILE_A and the tile to its west.
	_put_on(TILE_A + Vector3(-1, 0, 0))
	hold(MarbleInput.new(), 0.45)
	assert_eq(heard.count(&"tile.crack"), 2)
	hold(MarbleInput.new(), 1.0)
	assert_eq(heard.count(&"tile.fall"), 2)
	assert_lt(run.state.position.y, GRID.y - 2.0, "the marble fell through")


func test_broken_tile_stays_gone_and_the_others_hold() -> void:
	_start(FLAT, [TILES.instantiate() as CrumblingTiles])
	_put_on(TILE_A)
	hold(MarbleInput.new(), 1.0)
	hold(MarbleInput.new(), 6.0)
	_put_on(TILE_A)
	hold(MarbleInput.new(), 0.3)
	assert_lt(run.state.position.y, GRID.y - 0.1, "the broken tile is still gone")
	_put_on(TILE_B)
	hold(MarbleInput.new(), 0.45)
	_assert_on(TILE_B)
	assert_eq(heard.count(&"tile.crack"), 2)


func test_respawn_and_restart_bring_the_tiles_back() -> void:
	_start(FLAT, [TILES.instantiate() as CrumblingTiles])
	_put_on(TILE_A)
	hold(MarbleInput.new(), 1.0)
	run.respawn(TILE_A + Vector3.UP * TUNING.radius)
	hold(MarbleInput.new(), 0.45)
	_assert_on(TILE_A)
	hold(MarbleInput.new(), 1.0)
	assert_eq(heard.count(&"tile.fall"), 2)
	run.restart()
	_put_on(TILE_A)
	hold(MarbleInput.new(), 0.45)
	_assert_on(TILE_A)


func test_fixture_tiles_have_their_marker_settings_and_drop_the_marble() -> void:
	if not ResourceLoader.exists(FIXTURE):
		fail_test("%s is missing: run `just build-levels`" % FIXTURE)
		return
	_start(load(FIXTURE) as PackedScene)
	var tiles: CrumblingTiles = null
	for object: LevelObject in run.objects:
		if object is CrumblingTiles:
			tiles = object as CrumblingTiles
	assert_not_null(tiles)
	if tiles == null:
		return
	assert_almost_eq(tiles.delay, 0.6, 0.001)
	assert_almost_eq(tiles.depth, 8.0, 0.001)
	assert_almost_eq(tiles.global_position, FIXTURE_GRID, Vector3.ONE * 0.001)
	# A tile of the second row, which holds for 0.6 s.
	var tile: Vector3 = FIXTURE_GRID + Vector3(1, 0, 1)
	_put_on(tile)
	hold(MarbleInput.new(), 0.55)
	_assert_on(tile)
	hold(MarbleInput.new(), 1.0)
	assert_eq(heard.count(&"tile.fall"), 1)
	assert_lt(run.state.position.y, -2.0, "the marble fell through")


## Starts a run of level with the extra nodes and records its feedback in heard.
func _start(level: PackedScene, extra: Array[Node3D] = []) -> void:
	for node: Node3D in extra:
		node.position = GRID
	start_run(level, extra)
	run.feedback.connect(_hear)


## Puts the marble still on the floor at top.
func _put_on(top: Vector3) -> void:
	run.teleport(top + Vector3.UP * TUNING.radius, Vector3.ZERO)


## Asserts that the marble rests on the floor whose top is at top.
func _assert_on(top: Vector3) -> void:
	assert_almost_eq(run.state.position.y, top.y + TUNING.radius, 0.02, "marble on the tile")
	assert_true(run.state.on_ground)


## Records the kind of one feedback.
func _hear(kind: StringName, _strength: float, _at: Vector3) -> void:
	heard.append(kind)
