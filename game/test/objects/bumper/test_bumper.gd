extends RunTest
## Bumpers, through the boundary: a marble that rolls into a bumper leaves it at the bumper's
## speed across the floor, a faster marble keeps its speed, and a marble on the top face goes
## off sideways, not up. Each push emits bumper.hit.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const BUMPER: PackedScene = preload("res://objects/bumper/bumper.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The bumper's base centre, on the floor.
const AT: Vector3 = Vector3(0, 0, -3)

var _bumper: Bumper


## Starts a run with one bumper at AT and watches the run's feedback.
func _start(speed: float) -> void:
	_bumper = BUMPER.instantiate() as Bumper
	_bumper.position = AT
	_bumper.speed = speed
	start_run(FLAT, [_bumper])
	watch_signals(run)


## Returns the strength of each feedback of kind that the run emitted, in order.
func _strengths(kind: StringName) -> Array[float]:
	var out: Array[float] = []
	for i: int in get_signal_emit_count(run, "feedback"):
		var args: Array = get_signal_parameters(run, "feedback", i)
		if args[0] == kind:
			out.append(args[1])
	return out


func test_marble_that_rolls_in_leaves_at_the_bumper_speed() -> void:
	_start(15.0)
	run.marble.teleport(Vector3(0, TUNING.radius, -1.5), Vector3(0, 0, -5))
	hold(rolling(Vector2.ZERO), 0.3)
	var v: Vector3 = run.state.velocity
	assert_almost_eq(v.z, 15.0, 1.0, "pushed back along +z at about 15 m/s")
	assert_almost_eq(v.y, 0.0, 0.5, "the push is across the floor")
	var hits: Array[float] = _strengths(&"bumper.hit")
	assert_eq(hits.size(), 1, "one push, one bumper.hit")
	if hits.size() == 1:
		# The bounce gives 2.5 m/s back; the push adds the other 12.5 of 15.
		assert_almost_eq(hits[0], 12.5 / 15.0, 0.1)


func test_faster_marble_keeps_its_bounce() -> void:
	_start(15.0)
	run.marble.teleport(Vector3(0, TUNING.radius, -1.5), Vector3(0, 0, -40))
	hold(rolling(Vector2.ZERO), 0.1)
	assert_gt(run.state.velocity.z, 15.0, "the bounce is faster than the bumper speed")
	assert_eq(_strengths(&"bumper.hit").size(), 0, "no push, no bumper.hit")


func test_marble_on_the_top_face_goes_off_sideways() -> void:
	_start(15.0)
	var top: float = _bumper.height + TUNING.radius
	run.marble.teleport(AT + Vector3(0.2, top, 0), Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 0.1)
	assert_almost_eq(run.state.velocity.x, 15.0, 1.0, "pushed away from the axis along +x")
	assert_lt(run.state.velocity.y, 0.5, "not lifted")
	assert_lt(run.state.position.y, top + 0.1, "not lifted")


func test_speed_setting_sets_the_push() -> void:
	_start(8.0)
	run.marble.teleport(Vector3(0, TUNING.radius, -1.5), Vector3(0, 0, -5))
	hold(rolling(Vector2.ZERO), 0.3)
	assert_almost_eq(run.state.velocity.z, 8.0, 0.8)


func test_drum_is_an_enamel_band_between_brass_rings() -> void:
	var bumper: Bumper = BUMPER.instantiate() as Bumper
	add_child_autofree(bumper)
	var drum: MeshInstance3D = bumper.get_node("Solid/Mesh") as MeshInstance3D
	var enamel: StandardMaterial3D = drum.material_override as StandardMaterial3D
	assert_eq(enamel.albedo_color, Palette.hazard(), "the band has the hazard colour")
	for part: String in ["Base", "Cap"]:
		var ring: MeshInstance3D = drum.get_node(part) as MeshInstance3D
		assert_eq(ring.material_override, KitMaterials.find("brass"), "%s is the kit brass" % part)
	var cap: MeshInstance3D = drum.get_node("Cap") as MeshInstance3D
	var tall: float = (cap.mesh as CylinderMesh).height
	assert_gt(cap.position.y + tall / 2.0, bumper.height / 2.0, "the cap hides the top face")
