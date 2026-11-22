extends AscentTest
## The Ascent mode on the fixture climb (levels/test/ascent_fixture_<n>.py): the zones, the
## height, the light, Assist, the falls and the flag. test_ascent_spot.gd has the spot, the
## gate and the ghost.

const FALL: float = AscentFalls.FALL_HEIGHT


## Every zone loads at the start, into one run: the climb has the three zone levels, the
## objects of each, and one finish.
func test_all_zones_load_at_the_start() -> void:
	if not climb():
		return
	assert_eq(run.state.level, &"ascent:ascent_fixture_1+ascent_fixture_2+ascent_fixture_3")
	assert_eq(run.level.tier, Ascent.ID)
	assert_eq(run.level.get_children().filter(_is_level).size(), 3, "zone levels")
	assert_not_null(run.level.find_child("lift", true, false), "the lift of zone 2")
	assert_not_null(run.level.find_child("flight_8", true, false), "a ramp of zone 3")
	assert_eq(objects(func(o: LevelObject) -> bool: return o is Finish).size(), 1)
	assert_eq(ascent.zone_heights, PackedFloat32Array([0.0, 12.0, 24.0]))
	assert_almost_eq(ascent.top, 36.0, 0.001)


## The climb of the game is its built zones up to the first one that is not built: a zone
## above a gap does not join the climb.
func test_climb_stops_at_the_first_zone_that_is_not_built() -> void:
	var ids: Array[StringName] = [Ascent.FIXTURE[0], &"no_such_zone", Ascent.FIXTURE[2]]
	var first: Array[StringName] = [Ascent.FIXTURE[0]]
	assert_eq(Ascent.built_from_bottom(ids), first)
	assert_eq(Ascent.built_from_bottom(Ascent.FIXTURE), Ascent.FIXTURE)


## Every mesh of the zones has a visibility range, so far geometry is not drawn.
func test_far_geometry_has_a_visibility_range() -> void:
	if not climb():
		return
	var meshes: Array[Node] = run.level.find_children("*", "MeshInstance3D", true, false)
	assert_gt(meshes.size(), 20, "the meshes of the zones")
	for node: Node in meshes:
		var mesh: MeshInstance3D = node as MeshInstance3D
		if mesh.get_parent() is AscentGate:
			continue
		assert_gte(mesh.visibility_range_end, Ascent.FAR, mesh.name)


## The climb has one sun and one sky: those of the zones are gone. Of the reflection probes,
## only a room's stays (zone 1 has one).
func test_the_climb_has_one_sun_and_one_sky() -> void:
	if not climb():
		return
	assert_eq(run.find_children("*", "DirectionalLight3D", true, false).size(), 1)
	assert_eq(run.find_children("*", "WorldEnvironment", true, false).size(), 1)
	assert_eq(run.find_children("*", "LightmapGI", true, false).size(), 0)
	var probes: Array[Node] = run.find_children("*", "ReflectionProbe", true, false)
	assert_eq(probes.size(), 1)
	if probes.size() == 1:
		assert_true(probes[0].get_parent() is RoomProbe, "the room's probe")


## The state gives the height above the climb start.
func test_state_gives_the_height() -> void:
	if not climb():
		return
	assert_almost_eq(run.state.height, 0.0, 0.01)
	put(ZONE_2)
	assert_almost_eq(run.state.height, 12.0, 0.01)
	put(GATE - Vector3(0, 4, 0))
	assert_almost_eq(run.state.height, 36.0, 0.01)
	var reported: float = Game.snapshot().to_dict()["height"]
	assert_almost_eq(reported, 36.0, 0.01, "the harness gets the same height")
	run.teleport(on(ZONE_3), Vector3.ZERO)
	assert_almost_eq(run.state.height, 24.0, 0.01, "a teleport shows with no step")


## The marble is in a zone from the height of its start up, and goes back to the zone below
## when it falls under it.
func test_zone_follows_the_height() -> void:
	if not climb():
		return
	watch_signals(ascent)
	assert_eq(ascent.zone, 0)
	put(ZONE_2)
	assert_eq(ascent.zone, 1)
	put(ZONE_3 + Vector3(0, 0, 6))
	assert_eq(ascent.zone, 2)
	put(START)
	assert_eq(ascent.zone, 0)
	assert_signal_emit_count(ascent, "zone_changed", 3)


## The time of day follows the height: the sun stands higher at the gate than at the start.
func test_time_of_day_follows_the_height() -> void:
	if not climb():
		return
	var dawn: float = ascent.sky.elevation
	put(GATE - Vector3(0, 4, 0))
	assert_gt(ascent.sky.elevation, dawn)


## The light is the ground dawn at the climb start and noon at the top of zone 3, and a blend
## of the two between them.
func test_light_goes_from_the_ground_dawn_to_noon() -> void:
	var sky: AscentSky = AscentSky.new()
	autofree(sky)
	var sun: DirectionalLight3D = sky.get_node(^"sun") as DirectionalLight3D
	assert_almost_eq(sky.elevation, AscentSky.GROUND_DAWN.sun_elevation, 0.001)
	assert_almost_eq(sun.light_energy, AscentSky.GROUND_DAWN.sun_energy, 0.001)
	sky.show_height(AscentSky.NOON_HEIGHT - 0.5)
	sky.show_height(AscentSky.NOON_HEIGHT)
	assert_almost_eq(sky.elevation, AscentSky.NOON.sun_elevation, 0.001, "a short last step")
	assert_almost_eq(sun.light_energy, AscentSky.NOON.sun_energy, 0.001)
	sky.show_height(AscentSky.NOON_HEIGHT * 0.5)
	var between: float = (AscentSky.GROUND_DAWN.sun_elevation + AscentSky.NOON.sun_elevation) * 0.5
	assert_almost_eq(sky.elevation, between, 0.001)


## The climb has no lightmap: the fill of the first stop stands in for bounce light at every
## height, and it grows with the sunlight on a floor. At the climb start the ambient light is
## that of the zone played alone.
func test_fill_follows_the_sunlight_on_a_floor() -> void:
	var sky: AscentSky = AscentSky.new()
	autofree(sky)
	var environment: Environment = (sky.get_node(^"sky") as WorldEnvironment).environment
	var dawn: SkyPreset = AscentSky.GROUND_DAWN
	var noon: SkyPreset = AscentSky.NOON
	var share: float = dawn.sky_share
	assert_almost_eq(environment.ambient_light_energy, 1.0, 0.001)
	assert_eq(environment.ambient_light_color, dawn.fill_color)
	assert_almost_eq(environment.ambient_light_sky_contribution, share, 0.001)
	sky.show_height(AscentSky.NOON_HEIGHT)
	var rise: float = noon.sun_energy * noon.to_sun().y / (dawn.sun_energy * dawn.to_sun().y)
	assert_almost_eq(environment.ambient_light_energy, rise, 0.001)
	assert_gt(rise, 2.0, "the noon sun puts more than twice the light on a floor")
	assert_eq(environment.ambient_light_color, dawn.fill_color, "the fill keeps its colour")
	assert_almost_eq(environment.ambient_light_sky_contribution, share, 0.001)


## Between two stops the sky shows the panoramas of those two presets, blended by the share of
## the way from the lower stop. The stops rise from the climb start.
func test_sky_blends_the_two_stops_round_the_height() -> void:
	var heights: Array[float] = []
	for height: float in AscentSky.STOPS:
		heights.append(height)
	assert_eq(heights[0], 0.0, "the first stop is the climb start")
	for i: int in range(1, heights.size()):
		assert_gt(heights[i], heights[i - 1], "the stops rise")
	var sky: AscentSky = AscentSky.new()
	autofree(sky)
	var world: WorldEnvironment = sky.get_node(^"sky") as WorldEnvironment
	var material: ShaderMaterial = world.environment.sky.sky_material as ShaderMaterial
	var low: float = heights[0]
	var high: float = heights[1]
	sky.show_height(lerpf(low, high, 0.3))
	var blend: float = material.get_shader_parameter(&"blend")
	var from: Texture2D = material.get_shader_parameter(&"from_panorama")
	var to: Texture2D = material.get_shader_parameter(&"to_panorama")
	assert_almost_eq(blend, 0.3, 0.001)
	assert_eq(from, AscentSky.STOPS[low].panorama)
	assert_eq(to, AscentSky.STOPS[high].panorama)


## The climb has no checkpoint: a marble that leaves the world comes back at the climb start.
func test_no_checkpoints_by_default() -> void:
	if not climb():
		return
	assert_eq(objects(_is_checkpoint).size(), 0)
	assert_false(ascent.assisted)
	put(ZONE_2)
	run.teleport(Vector3(0, run.rules.kill_height - 1.0, 0), Vector3.ZERO)
	hold(Rules.RESPAWN_DELAY + 0.1)
	assert_almost_eq(run.state.position, on(START), Vector3.ONE * 0.05)
	assert_eq(run.state.checkpoint, &"")


## A checkpoint that a zone has for a play of its own is not in the climb.
func test_checkpoint_of_a_zone_goes_away() -> void:
	var zones: Array[StringName] = [&"rules"]
	run = Ascent.start(true, zones)
	assert_not_null(run, "the test level rules, which has a checkpoint, is the zone")
	if run != null:
		assert_eq(objects(_is_checkpoint).size(), 0)


## An egg of a zone saves under the id of the zone, with its name, so it stays found when
## the climb gets more zones.
func test_egg_saves_under_its_zone() -> void:
	var zones: Array[StringName] = [&"rules"]
	run = Ascent.start(true, zones)
	assert_not_null(run, "the test level rules, which has an egg, is the zone")
	if run == null:
		return
	run.auto_step = false
	run.teleport(Vector3(-6, TUNING.radius, -10), Vector3.ZERO)
	run.step(MarbleInput.new())
	assert_true(run.state.egg_found)
	assert_eq(Save.level(&"rules").eggs, PackedStringArray(["Egg"]))
	assert_eq(Save.level(run.level.id).eggs.size(), 0, "not under the id of the climb")


## Assist puts a checkpoint on each zone start and marks the climb.
func test_assist_adds_a_checkpoint_at_each_zone_start() -> void:
	Save.ascent.assist = true
	if not climb():
		return
	var checkpoints: Array[LevelObject] = objects(_is_checkpoint)
	assert_eq(checkpoints.size(), 3)
	var pad: Vector3 = on(ZONE_2) - Vector3.UP * TUNING.radius
	assert_almost_eq(checkpoints[1].global_position, pad, Vector3.ONE * 0.01)
	assert_true(ascent.assisted, "the climb is marked")


## With Assist, a fall of ASSIST_DROP below the last checkpoint puts the marble back on it.
func test_assist_fall_returns_to_the_zone_start() -> void:
	Save.ascent.assist = true
	if not climb():
		return
	put(ZONE_2)
	assert_eq(run.state.checkpoint, &"assist_2")
	fall_from_landing()
	assert_almost_eq(run.state.position, on(ZONE_2), Vector3.ONE * 0.05)
	assert_eq(ascent.falls, 1)
	assert_almost_eq(ascent.fallen, 4.0 + Ascent.ASSIST_DROP, 0.5, "to 10 m below the checkpoint")


## A mark of Assist stays on the climb when the player turns Assist off again.
func test_assist_mark_stays_on_the_climb() -> void:
	Save.ascent.assist = true
	if not climb():
		return
	put(ZONE_2)
	quit_climb()
	Save.ascent.assist = false
	if not climb():
		return
	assert_eq(objects(_is_checkpoint).size(), 0, "no checkpoints now")
	assert_true(ascent.assisted, "the mark stays")
	if not climb(true):
		return
	assert_false(ascent.assisted, "a new climb has no mark")


## A fall counts once, with the metres from the floor that the marble left to its lowest
## point. The bounces on the ground belong to it.
func test_fall_counts_once_with_its_metres() -> void:
	if not climb():
		return
	fall_from_landing()
	assert_true(run.state.on_ground, "the marble lies on the ground")
	assert_almost_eq(run.state.height, 0.0, 0.01)
	assert_eq(ascent.falls, 1)
	assert_almost_eq(ascent.fallen, 16.0, 0.1)


## A drop of less than FALL_HEIGHT is not a fall: one flight ends 4 m above the landing below
## it, so a drop of 2 m from its middle stays under the limit.
func test_small_drop_is_no_fall() -> void:
	if not climb():
		return
	put(START)
	run.teleport(on(START) + Vector3.UP * (FALL - 0.5), Vector3.ZERO)
	hold(2.0)
	assert_true(run.state.on_ground)
	assert_eq(ascent.falls, 0)
	assert_eq(ascent.fallen, 0.0)


## The best height is the highest floor that the marble stood on. The flag stands there after
## the marble falls.
func test_flag_marks_the_best_height_after_a_fall() -> void:
	if not climb():
		return
	assert_false(ascent.flag.visible, "no flag before the first climb")
	put(LANDING)
	hold(0.2)
	assert_almost_eq(ascent.best_height, 16.0, 0.01)
	assert_false(ascent.flag.visible, "the flag is not under a marble that climbs")
	fall_from_landing()
	assert_true(ascent.flag.visible)
	var foot: Vector3 = on(LANDING) - Vector3.UP * TUNING.radius
	assert_almost_eq(ascent.flag.global_position.y, foot.y, 0.01)
	assert_almost_eq(ascent.flag.global_position, foot, Vector3.ONE * 2.5, "on the landing")
	assert_almost_eq(ascent.best_height, 16.0, 0.01, "a fall keeps the best height")


## The deck of a lift is not a best height: the flag would stand in the air when it goes.
func test_lift_is_no_best_height() -> void:
	if not climb():
		return
	put(LANDING)
	hold(0.2)
	var best: float = ascent.best_height
	# The lift leaves the bottom at cycle time 1.5 s and is at the top from 4 to 5.5 s.
	put(LIFT)
	hold(4.4)
	assert_almost_eq(run.state.height, 20.0, 0.1, "the lift carried the marble up")
	assert_almost_eq(ascent.best_height, best, 0.01)


func _is_level(node: Node) -> bool:
	return node is Level


func _is_checkpoint(object: LevelObject) -> bool:
	return object is Checkpoint
