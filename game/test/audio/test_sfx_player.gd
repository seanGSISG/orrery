extends RunTest
## Sound effects, through the boundary: feedback and state from a LevelRun in, a playing
## player on the SFX bus out.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const BUMPER: PackedScene = preload("res://objects/bumper/bumper.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## Feedback kind to the sound it must play. The last rows are kinds that no object emits yet;
## they play through the type and event fallbacks.
const EXPECTED: Dictionary[StringName, StringName] = {
	&"marble.jump": &"jump",
	&"marble.bounce": &"bounce",
	&"bumper.hit": &"bumper",
	&"steam_vent.blow": &"steam_vent",
	&"pendulum.hit": &"pendulum",
	&"gem.collect": &"gem",
	&"egg.open": &"egg",
	&"checkpoint.reach": &"checkpoint",
	&"finish.open": &"finish_open",
	&"finish.reach": &"finish_reach",
	&"coil_spring.pickup": &"powerup_pickup",
	&"coil_spring.use": &"powerup_use",
	&"trapdoor.open": &"trapdoor",
	&"tile.crack": &"tile_crack",
	&"tile.fall": &"tile_fall",
	&"super_jump.use": &"powerup_use",
}

var sfx: SfxPlayer


func before_each() -> void:
	sfx = SfxPlayer.new()
	add_child_autofree(sfx)


## Starts a run of the flat level with extra nodes, and attaches the SfxPlayer to it.
func _start(extra: Array[Node3D] = []) -> void:
	start_run(FLAT, extra)
	sfx.attach(run)


## Steps the run for seconds with input, and lets the SfxPlayer read each tick.
func _hold_heard(input: MarbleInput, seconds: float) -> void:
	var dt: float = 1.0 / Engine.physics_ticks_per_second
	for i: int in roundi(seconds * Engine.physics_ticks_per_second):
		run.step(input)
		sfx.observe(dt)


## Checks that sound plays from res://audio/sfx/<sound>.ogg on the SFX bus.
func _assert_plays(sound: StringName, context: String) -> void:
	var node: Node = sfx.player(sound)
	var path: String = SfxPlayer.SOUND_PATH % sound
	var flat: AudioStreamPlayer = node as AudioStreamPlayer
	var spatial: AudioStreamPlayer3D = node as AudioStreamPlayer3D
	if flat != null:
		assert_true(flat.playing, "%s: %s plays" % [context, sound])
		assert_eq(flat.bus, AudioBuses.SFX, context)
		assert_eq(flat.stream.resource_path, path, context)
	elif spatial != null:
		assert_true(spatial.playing, "%s: %s plays" % [context, sound])
		assert_eq(spatial.bus, AudioBuses.SFX, context)
		assert_eq(spatial.stream.resource_path, path, context)
	else:
		fail_test("%s: no player for %s" % [context, sound])


## Returns how many sound players play now, the roll loop not counted.
func _playing_count() -> int:
	var count: int = 0
	for node: Node in sfx.get_children():
		var flat: AudioStreamPlayer = node as AudioStreamPlayer
		var spatial: AudioStreamPlayer3D = node as AudioStreamPlayer3D
		if (flat != null and flat != sfx.roll and flat.playing) or (spatial != null and spatial.playing):
			count += 1
	return count


func test_each_feedback_kind_plays_its_sound_on_the_sfx_bus() -> void:
	_start()
	for kind: StringName in EXPECTED:
		var before: Node = sfx.player(EXPECTED[kind])
		run.feedback.emit(kind, 0.8, Vector3(1, 0, -2))
		assert_ne(sfx.player(EXPECTED[kind]), before, "%s starts a new voice" % kind)
		_assert_plays(EXPECTED[kind], kind)
		hold(rolling(Vector2.ZERO), 0.05)


func test_landing_strength_picks_soft_or_hard() -> void:
	_start()
	run.feedback.emit(&"marble.land", 0.2, Vector3.ZERO)
	_assert_plays(&"land_soft", "soft landing")
	assert_eq(_playing_count(), 1, "only the soft landing plays")
	run.feedback.emit(&"marble.land", 0.9, Vector3.ZERO)
	_assert_plays(&"land_hard", "hard landing")


func test_strength_sets_the_volume() -> void:
	_start()
	run.feedback.emit(&"gem.collect", 0.0, Vector3.ZERO)
	var quiet: float = (sfx.player(&"gem") as AudioStreamPlayer).volume_db
	hold(rolling(Vector2.ZERO), 0.1)
	run.feedback.emit(&"gem.collect", 1.0, Vector3.ZERO)
	var loud: float = (sfx.player(&"gem") as AudioStreamPlayer).volume_db
	assert_almost_eq(loud, 0.0, 0.01, "full strength plays at full volume")
	assert_lt(quiet, loud - 6.0, "a weak event plays quieter")


func test_overlapping_hits_keep_their_own_positions() -> void:
	_start()
	run.feedback.emit(&"bumper.hit", 1.0, Vector3(-5, 0, 0))
	var first: AudioStreamPlayer3D = sfx.player(&"bumper") as AudioStreamPlayer3D
	hold(rolling(Vector2.ZERO), 0.1)
	run.feedback.emit(&"bumper.hit", 1.0, Vector3(5, 0, 0))
	var second: AudioStreamPlayer3D = sfx.player(&"bumper") as AudioStreamPlayer3D
	assert_ne(first, second, "the second hit gets its own voice")
	assert_true(first.playing and second.playing, "both hits ring")
	assert_eq(first.global_position, Vector3(-5, 0, 0), "the first hit stays where it was")
	assert_eq(second.global_position, Vector3(5, 0, 0))


func test_restart_clears_the_retrigger_gap() -> void:
	_start()
	_hold_heard(rolling(Vector2.ZERO), 0.1)
	run.feedback.emit(&"gem.collect", 1.0, Vector3.ZERO)
	var before: Node = sfx.player(&"gem")
	run.restart()
	_hold_heard(rolling(Vector2.ZERO), 0.1)
	run.feedback.emit(&"gem.collect", 1.0, Vector3.ZERO)
	assert_ne(sfx.player(&"gem"), before, "the same tick after a restart plays again")


func test_unknown_kind_plays_nothing() -> void:
	_start()
	run.feedback.emit(&"gizmo.wobble", 1.0, Vector3.ZERO)
	assert_eq(_playing_count(), 0)


func test_bumper_hit_plays_at_the_contact() -> void:
	var bumper: Bumper = BUMPER.instantiate() as Bumper
	bumper.position = Vector3(0, 0, -3)
	_start([bumper])
	run.marble.teleport(Vector3(0, TUNING.radius, -1.5), Vector3(0, 0, -5))
	_hold_heard(rolling(Vector2.ZERO), 0.3)
	_assert_plays(&"bumper", "bumper hit")
	var spatial: AudioStreamPlayer3D = sfx.player(&"bumper") as AudioStreamPlayer3D
	assert_almost_eq(spatial.global_position.z, -3.0, 1.0, "the sound plays at the bumper")


func test_roll_volume_follows_speed_and_ground() -> void:
	_start()
	assert_true(sfx.roll.playing, "the roll loop runs while attached")
	_hold_heard(rolling(Vector2.ZERO), 0.2)
	assert_almost_eq(sfx.roll_level, 0.0, 0.01, "silent at rest")
	run.marble.teleport(Vector3(0, TUNING.radius, 0), Vector3(0, 0, -4))
	_hold_heard(rolling(Vector2.ZERO), 0.4)
	var slow: float = sfx.roll.volume_db
	var slow_pitch: float = sfx.roll.pitch_scale
	run.marble.teleport(Vector3(0, TUNING.radius, 0), Vector3(0, 0, -16))
	_hold_heard(rolling(Vector2.ZERO), 0.4)
	assert_gt(sfx.roll.volume_db, slow + 6.0, "faster rolls louder")
	assert_gt(sfx.roll.pitch_scale, slow_pitch, "faster rolls higher")
	run.marble.teleport(Vector3(0, 5, 0), Vector3(0, 0, -16))
	_hold_heard(rolling(Vector2.ZERO), 0.3)
	assert_lt(sfx.roll_level, 0.01, "silent in the air")


func test_respawn_plays_when_the_marble_comes_back() -> void:
	_start()
	run.marble.teleport(Vector3(0, run.rules.kill_height - 1.0, 0), Vector3.ZERO)
	_hold_heard(rolling(Vector2.ZERO), Rules.RESPAWN_DELAY * 0.5)
	assert_eq(run.state.status, &"respawning")
	assert_false((sfx.player(&"respawn") as AudioStreamPlayer).playing, "no respawn sound yet")
	_hold_heard(rolling(Vector2.ZERO), Rules.RESPAWN_DELAY)
	assert_eq(run.state.status, &"playing")
	_assert_plays(&"respawn", "respawn")


func test_restart_plays_the_respawn_sound() -> void:
	_start()
	_hold_heard(rolling(Vector2(0, 1)), 0.2)
	run.restart()
	sfx.observe(1.0 / Engine.physics_ticks_per_second)
	_assert_plays(&"respawn", "restart")


func test_detach_stops_every_sound() -> void:
	_start()
	run.feedback.emit(&"egg.open", 1.0, Vector3.ZERO)
	sfx.attach(null)
	assert_false(sfx.roll.playing)
	assert_eq(_playing_count(), 0, "the egg chime stops with the run")
	run.feedback.emit(&"gem.collect", 1.0, Vector3.ZERO)
	assert_eq(_playing_count(), 0, "a detached player ignores the old run")
