extends RunTest
## Trapdoors, through the boundary: the door holds a marble for `delay` s, then drops it,
## shuts after `close_after` s and drops the next marble too. A respawn or a restart shuts it.
## The built fixture levels/test/floors.py has the marker settings.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const TRAPDOOR: PackedScene = preload("res://objects/trapdoor/trapdoor.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
const FIXTURE: String = "res://levels/built/floors.glb"
## Top centre of the test door, high enough that the shutting door misses a marble on the
## floor under it.
const DOOR: Vector3 = Vector3(6, 6, 0)
## The fixture's trapdoor marker, Blender (0, 10, 0), in Godot axes.
const FIXTURE_DOOR: Vector3 = Vector3(0, 0, -10)

## Kinds of the run's feedback in this test, in order.
var heard: Array[StringName] = []


func before_each() -> void:
	heard.clear()


func test_door_holds_for_the_delay_then_drops_the_marble() -> void:
	_start(FLAT, [_door(5.0)])
	_put_on(DOOR)
	hold(MarbleInput.new(), 0.45)
	_assert_on(DOOR)
	assert_false(heard.has(&"trapdoor.open"), "the door is still shut")
	hold(MarbleInput.new(), 1.0)
	assert_eq(heard.count(&"trapdoor.open"), 1)
	assert_lt(run.state.position.y, DOOR.y - 2.0, "the marble fell through")


func test_door_shuts_after_close_after_and_drops_the_next_marble() -> void:
	_start(FLAT, [_door(2.0)])
	_put_on(DOOR)
	hold(MarbleInput.new(), 1.0)
	assert_lt(run.state.position.y, DOOR.y - 2.0, "the marble fell through")
	# The drop starts at 0.5 s, the door starts to shut at 2.5 s and is shut at 2.8 s.
	hold(MarbleInput.new(), 2.0)
	_put_on(DOOR)
	hold(MarbleInput.new(), 0.45)
	_assert_on(DOOR)
	hold(MarbleInput.new(), 1.0)
	assert_eq(heard.count(&"trapdoor.open"), 2)
	assert_lt(run.state.position.y, DOOR.y - 2.0, "the next marble fell through")


func test_respawn_and_restart_shut_an_open_door() -> void:
	_start(FLAT, [_door(5.0)])
	_put_on(DOOR)
	hold(MarbleInput.new(), 1.0)
	run.respawn(DOOR + Vector3.UP * TUNING.radius)
	hold(MarbleInput.new(), 0.45)
	_assert_on(DOOR)
	hold(MarbleInput.new(), 1.0)
	run.restart()
	_put_on(DOOR)
	hold(MarbleInput.new(), 0.45)
	_assert_on(DOOR)


func test_fixture_door_has_its_marker_settings_and_drops_the_marble() -> void:
	if not ResourceLoader.exists(FIXTURE):
		fail_test("%s is missing: run `just build-levels`" % FIXTURE)
		return
	_start(load(FIXTURE) as PackedScene)
	var door: Trapdoor = null
	for object: LevelObject in run.objects:
		if object is Trapdoor:
			door = object as Trapdoor
	assert_not_null(door)
	if door == null:
		return
	assert_almost_eq(door.delay, 0.5, 0.001)
	assert_almost_eq(door.close_after, 4.0, 0.001)
	assert_almost_eq(door.global_position, FIXTURE_DOOR, Vector3.ONE * 0.001)
	_put_on(FIXTURE_DOOR)
	hold(MarbleInput.new(), 1.5)
	assert_eq(heard.count(&"trapdoor.open"), 1)
	assert_lt(run.state.position.y, -2.0, "the marble fell through")


func test_door_is_a_plate_of_the_kit_brass() -> void:
	var door: Trapdoor = _door(5.0)
	add_child_autofree(door)
	var brass: ShaderMaterial = KitMaterials.find("brass") as ShaderMaterial
	var brass_map: Texture2D = brass.get_shader_parameter("albedo_map")
	var look: MeshInstance3D = door.get_node("Solid/Mesh") as MeshInstance3D
	var plate: ShaderMaterial = look.material_override as ShaderMaterial
	assert_not_null(plate)
	if plate == null:
		return
	var plate_map: Texture2D = plate.get_shader_parameter("albedo_map")
	var repeat: float = plate.get_shader_parameter("tile")
	assert_eq(plate.shader, brass.shader, "the kit shader")
	assert_eq(plate_map, brass_map, "the kit brass texture")
	assert_almost_eq(repeat, door.width, 0.001, "one texture repeat across the door")


## Returns a test door at DOOR that starts to shut close_after s after its drop.
func _door(close_after: float) -> Trapdoor:
	var door: Trapdoor = TRAPDOOR.instantiate() as Trapdoor
	door.position = DOOR
	door.close_after = close_after
	return door


## Starts a run of level with the extra nodes and records its feedback in heard.
func _start(level: PackedScene, extra: Array[Node3D] = []) -> void:
	start_run(level, extra)
	run.feedback.connect(_hear)


## Puts the marble still on the floor at top.
func _put_on(top: Vector3) -> void:
	run.teleport(top + Vector3.UP * TUNING.radius, Vector3.ZERO)


## Asserts that the marble rests on the floor whose top is at top.
func _assert_on(top: Vector3) -> void:
	assert_almost_eq(run.state.position.y, top.y + TUNING.radius, 0.02, "marble on the door")
	assert_true(run.state.on_ground)


## Records the kind of one feedback.
func _hear(kind: StringName, _strength: float, _at: Vector3) -> void:
	heard.append(kind)
