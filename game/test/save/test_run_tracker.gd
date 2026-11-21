extends RunTest
## RunTracker on a real run of test/levels/rules.tscn: MarbleInput and LevelRun.teleport()
## in, the SaveGame and the ghost marble out. test/level/test_rules.gd has the layout.

const RULES: PackedScene = preload("res://test/levels/rules.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
const ROOT: String = "user://test_run_tracker"
const GEM_WEST: Vector3 = Vector3(-6, 0, 0)
const GEM_EAST: Vector3 = Vector3(6, 0, 0)
const EGG: Vector3 = Vector3(-6, 0, -10)
const FINISH: Vector3 = Vector3(0, 0, -20)

var save: SaveGame
var tracker: RunTracker


func before_each() -> void:
	save = _save()
	start_run(RULES)
	tracker = RunTracker.attach(run, save)


func after_each() -> void:
	for folder: String in [ROOT.path_join(SaveGame.GHOSTS), ROOT]:
		if not DirAccess.dir_exists_absolute(folder):
			continue
		for file: String in DirAccess.get_files_at(folder):
			DirAccess.remove_absolute(folder.path_join(file))
		DirAccess.remove_absolute(folder)


## The egg saves on the tick that the marble finds it, before any finish or restart.
func test_egg_saves_when_found() -> void:
	run.step(rolling(Vector2(0, 1)))
	visit(EGG)
	assert_true(run.state.egg_found)
	var loaded: SaveGame = _save()
	loaded.read()
	assert_true(loaded.level(&"rules").egg)


## A finish saves the time, the medal and the ghost. In the next attempt the ghost marble
## is where the marble was at the same level clock in the first attempt.
func test_next_attempt_races_the_ghost() -> void:
	var path: Array[Vector3] = [run.state.position]
	for _i: int in 120:
		run.step(rolling(Vector2(0, 1)))
		path.append(run.state.position)
	visit(GEM_WEST)
	visit(GEM_EAST)
	visit(FINISH)
	assert_eq(run.state.status, &"finished")
	var time: float = run.state.timer
	# The finish saves on its tick, before any restart.
	var loaded: SaveGame = _save()
	loaded.read()
	assert_eq(loaded.level(&"rules").best_time, time)
	assert_eq(loaded.level(&"rules").medal, &"gold")
	assert_almost_eq(loaded.ghost(&"rules").duration, time, 0.0001)
	run.restart()
	# The ghost marble races the new best from the first tick of the next attempt. The last
	# sample of the roll, at 1 s, is the teleport to the first gem, so stop before the blend
	# to it.
	run.step(rolling(Vector2(1, 0)))
	assert_not_null(tracker.ghost_marble)
	for tick: int in range(2, path.size() - 4):
		run.step(rolling(Vector2(1, 0)))
		assert_almost_eq(tracker.ghost_marble.position, path[tick], Vector3.ONE * 0.01)
	assert_true(tracker.ghost_marble.visible)
	save.settings.ghost = false
	run.step(MarbleInput.new())
	assert_false(tracker.ghost_marble.visible)


## A slower finish keeps the first ghost.
func test_slower_finish_keeps_the_ghost() -> void:
	_finish_after(1.0)
	run.restart()
	var first: float = save.ghost(&"rules").duration
	_finish_after(2.0)
	run.restart()
	assert_almost_eq(save.ghost(&"rules").duration, first, 0.0001)
	assert_almost_eq(save.level(&"rules").best_time, first, 0.0001)


## Starts the clock, waits until the clock shows seconds, collects both gems and finishes.
func _finish_after(seconds: float) -> void:
	run.step(rolling(Vector2(0, 1)))
	hold(MarbleInput.new(), seconds - run.state.timer)
	visit(GEM_WEST)
	visit(GEM_EAST)
	visit(FINISH)


## Returns a SaveGame in this test's folder.
func _save() -> SaveGame:
	var fresh: SaveGame = SaveGame.new()
	fresh.dir = ROOT
	autofree(fresh)
	return fresh


## Puts the marble still on the floor at point and steps one tick.
func visit(point: Vector3) -> void:
	run.teleport(point + Vector3.UP * TUNING.radius, Vector3.ZERO)
	run.step(MarbleInput.new())
