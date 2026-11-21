class_name AscentTest
extends UiTest
## Base for the Ascent tests: UiTest (an empty save in user://test_ui/ and a new Ui) with no
## ghost files, and helpers for the fixture climb levels/test/ascent_fixture_<n>.py. That
## file tells the layout: nine flights of 4 m, three for each zone, so the zones start at 0,
## 12 and 24 m and the gate is at 36 m.
##
## A test drives the climb through the boundary: MarbleInput and LevelRun.teleport() in,
## GameState, the Ascent node and the save out.

const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## Floor points of the fixture, in level script axes (Blender x, y, z).
const START: Vector3 = Vector3(-4, 0, 0)
const ZONE_2: Vector3 = Vector3(8, 18, 12)
const ZONE_3: Vector3 = Vector3(20, 2, 24)
const GATE: Vector3 = Vector3(28, 21, 36)
## The landing above flight 3, at 16 m: open ground lies east of it, 16 m below.
const LANDING: Vector3 = Vector3(10, 2, 16)
## The middle of the lift's deck at the bottom of its way, at 16 m.
const LIFT: Vector3 = Vector3(12, 6, 16)

var run: LevelRun
var ascent: Ascent


func before_each() -> void:
	super()
	var ghosts: String = ROOT.path_join(SaveGame.GHOSTS)
	if DirAccess.dir_exists_absolute(ghosts):
		for file: String in DirAccess.get_files_at(ghosts):
			DirAccess.remove_absolute(ghosts.path_join(file))


## Starts the fixture climb as the Ascent menu does: it continues the saved spot, or starts a
## new climb when new_climb is true. The run steps only when the test steps it. Returns false
## (and fails the test) when the fixture is not built.
func climb(new_climb: bool = false) -> bool:
	run = Ascent.start(new_climb, Ascent.FIXTURE)
	ascent = Ascent.of(run)
	if ascent == null or ascent.zone_heights.size() != Ascent.FIXTURE.size():
		fail_test("the fixture climb is not built: run `just build-levels`")
		return false
	run.auto_step = false
	return true


## Returns the marble centre that rests on the floor point, which is in level script axes.
func on(point: Vector3) -> Vector3:
	return Vector3(point.x, point.z + TUNING.radius, -point.y)


## Puts the marble still on the floor point and steps one tick.
func put(point: Vector3) -> void:
	run.teleport(on(point), Vector3.ZERO)
	run.step(MarbleInput.new())


## Steps the run for seconds with one held input (default: none).
func hold(seconds: float, input: MarbleInput = MarbleInput.new()) -> void:
	for _i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(input)


## Returns an input that rolls along move (x right, y forward): forward is north (+y in level
## script axes) and right is east.
func roll(move: Vector2) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.move = move
	return input


## Rolls the marble slowly off the east side of LANDING, and waits until it lies on the ground
## 16 m below (with Assist: until it is back on its checkpoint).
func fall_from_landing() -> void:
	put(LANDING)
	hold(1.5, roll(Vector2(0.3, 0)))
	hold(5.0)


## Returns the objects of the run for which wanted returns true.
func objects(wanted: Callable) -> Array[LevelObject]:
	var found: Array[LevelObject] = []
	found.assign(run.objects.filter(wanted))
	return found


## Returns the deck of the lift of zone 2.
func lift() -> Node3D:
	return run.level.find_child("lift", true, false).get_node(^"Solid") as Node3D


## Leaves the climb as the pause menu does: the run ends, and the spot saves.
func quit_climb() -> void:
	Game.screen = &"ascent"
