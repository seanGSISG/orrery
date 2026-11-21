class_name Ascent
extends Node3D
## The Ascent mode (docs/plan.md §2.9): one climb through every zone, with no checkpoints.
## Ascent.start() builds the climb from the zone levels, plays it through Game and adds one
## Ascent node to the run. Ascent.of(run) returns that node; the HUD and the stats screen read
## it. The climb is a Level with the tier and the music group ID. Its level id is
## record_id() of its zones, so its best time and the ghost of the best climb save through
## Save.finish() like those of any level, and a climb of other zones has a record of its own.
## An egg saves under the id of its zone, so it stays found when the climb gets more zones.
##
## How a zone plugs in. A zone is a level script of its own, built like any level: one start
## pad, one finish pad, both routes. It uses the climb's coordinates, so every zone loads at
## the origin, and zone N + 1 starts on its own floor beside the finish of zone N. In the
## climb:
## - the start pad of the first zone is the climb start: `height` is 0 there;
## - the start pad of each zone is the zone start. The marble is in a zone from the height of
##   its start pad up. A change of zone changes the music (Music.set_zone());
## - the finish pads go away, except the last one, which gets the "to be continued" gate
##   (AscentGate) and ends the run;
## - the sun, the sky, the lightmap and the reflection probes of each zone go away: AscentSky
##   (a child of the Ascent node) lights the climb by the height;
## - a checkpoint of a zone goes away too: the climb has no checkpoints but those of Assist;
## - every mesh gets a visibility range, so the zones far above and below are not drawn.
##
## What the mode does in a climb:
## - Height. It writes GameState.height each tick: m above the climb start, along its up.
## - Falls. AscentFalls counts the falls and the metres fallen.
## - Best height. The highest floor of the level geometry that the marble stood on, in any
##   climb, with the place. The floor of an object (a lift, a trapdoor) does not count: it can
##   move away. AscentFlag stands there: it moves when a fall starts, so it is never under a
##   marble that climbs past its best.
## - Assist (Save.ascent.assist). The climb has a checkpoint at each zone start. A fall of
##   ASSIST_DROP m below the last one puts the marble back on it. The climb is marked as
##   assisted, for good. An assisted climb never replaces a record: it writes no best time,
##   no ghost and no best height (Sean, 2026-11-21). The stats screen shows its time.
## - The spot. save_spot() keeps the place, the clock, the stats and the recording of the
##   climb so far. It runs when the game pauses and when the run ends, also by a closed
##   window. The next start() continues there: the movers are where they were, the last
##   Assist checkpoint is the same, and a fall goes on as the same fall. The spot counts only
##   in a climb that starts with the zones that it was saved in. The gate ends the climb and
##   removes the spot.
## - A restart (LevelRun.restart(); the player has no button for it) starts a new climb.

## Emitted when the marble enters another zone; zone is its index, 0 for the first.
signal zone_changed(zone: int)

## The tier and the music group of the climb, and the start of its level id (record_id()).
const ID: StringName = &"ascent"
## The zone levels of the game, from the bottom (levels/ascent/zone_<n>.py).
const ZONES: Array[StringName] = [&"zone_1", &"zone_2", &"zone_3"]
## The zones of the test climb (levels/test/). The tests climb it, and so do the harness and
## the screenshot run while no zone of the game is built. The game itself never does: its
## save is of its own zones.
const FIXTURE: Array[StringName] = [
	&"ascent_fixture_1", &"ascent_fixture_2", &"ascent_fixture_3"
]
## The ghost id of the recording of the climb in progress (SaveGame.keep_ghost()).
const CLIMB_GHOST: StringName = &"ascent_climb"
const CHECKPOINT: PackedScene = preload("res://objects/checkpoint/checkpoint.tscn")
## A mesh is drawn up to FAR m from its nearest side, and fades out over the last FAR_FADE m.
const FAR: float = 300.0
const FAR_FADE: float = 40.0
## With Assist, the marble is out of bounds this far below its last checkpoint, m.
const ASSIST_DROP: float = 10.0
## The marble enters a zone ZONE_ENTER m below its start, and leaves it ZONE_LEAVE m below.
const ZONE_ENTER: float = 0.5
const ZONE_LEAVE: float = 3.0
## A contact is a floor when its normal has at least this dot with up (60° at most).
const FLOOR_UP: float = 0.5
## A new best height is at least this far above the last, m.
const BEST_STEP: float = 0.01

## The zone that the marble is in: an index into zone_heights.
var zone: int = 0
## The height of each zone start above the climb start, m, from the bottom.
var zone_heights: PackedFloat32Array = []
## The height of the gate above the climb start, m.
var top: float = 0.0
## The marble's height above the climb start, m; GameState.height has the same value.
var height: float = 0.0
var flag: AscentFlag = AscentFlag.new()
var sky: AscentSky = AscentSky.new()
## Falls and metres fallen in this climb.
var falls: int:
	get:
		return _falls.falls
var fallen: float:
	get:
		return _falls.fallen
## True when Assist was on at any time in this climb.
var assisted: bool:
	get:
		return Save.ascent.assisted
## The best height of any climb, m.
var best_height: float:
	get:
		return Save.ascent.best_height

var _run: LevelRun
var _world: WorldQuery
var _falls: AscentFalls = AscentFalls.new()
## The start pad of each zone, and its Assist checkpoint (empty with Assist off).
var _starts: Array[StartPad] = []
var _checkpoints: Array[Checkpoint] = []
## The ids of the zones in the climb, from the bottom.
var _zone_ids: Array[StringName] = []
var _gate: Finish
## The climb start (the marble centre on the first start pad) and the up there.
var _base: Vector3 = Vector3.ZERO
var _up: Vector3 = Vector3.UP
## Rules.kill_height of the climb with no checkpoint.
var _kill_height: float = 0.0
## True after the gate ended this climb.
var _ended: bool = false


## Starts the climb through Game and returns its run. It continues the saved spot when there
## is one; new_climb true starts at the bottom with new stats. ids are the zone level ids
## from the bottom; the default is the zones of the game (zones()). Returns null, and keeps
## the current run, when no zone has a scene.
static func start(new_climb: bool = false, ids: Array[StringName] = []) -> LevelRun:
	var mode: Ascent = Ascent.new()
	var level: Level = mode._build(ids if not ids.is_empty() else zones())
	if level == null:
		push_error("Ascent.start: no zone level is built")
		mode.free()
		return null
	var run: LevelRun = Game.play(level)
	run.restartable = false
	run.add_child(mode)
	mode._begin(run, new_climb)
	return run


## Returns the Ascent node of run, or null when run is null or is not a climb.
static func of(run: LevelRun) -> Ascent:
	return run.get_node_or_null(^"Ascent") as Ascent if run != null else null


## Returns the ids of the zones of the game that are built, from the bottom. With none, the
## game has no climb yet.
static func zones() -> Array[StringName]:
	var built: Array[StringName] = []
	for id: StringName in ZONES:
		if Game.level_path(id) != "":
			built.append(id)
	return built


## Returns the level id of a climb of the zones ids, from the bottom: "ascent:" and the ids
## with a + between them, for example &"ascent:zone_1+zone_2+zone_3". The best time and the
## ghost of the best climb are kept under it (Save.level(), Save.ghost()), so a record of a
## climb of fewer zones never stands for a longer climb.
static func record_id(ids: Array[StringName]) -> StringName:
	return StringName("%s:%s" % [ID, "+".join(PackedStringArray(ids))])


## Returns true when the save has a spot that a climb of the zones ids continues: the climb
## starts with the zones that the spot was saved in. More zones on top are fine. A spot of
## other zones is a place in another world, so such a climb starts at the bottom. The Ascent
## menu shows Continue by the same rule.
static func has_spot(ids: Array[StringName]) -> bool:
	var saved: PackedStringArray = Save.ascent.spot_zones.split(",", false)
	if not Save.ascent.has_spot or saved.is_empty() or saved.size() > ids.size():
		return false
	for i: int in saved.size():
		if saved[i] != String(ids[i]):
			return false
	return true


## Returns the marble centre on the start pad of the zone with index zone_index (0 is the
## first).
func start_of(zone_index: int) -> Vector3:
	return _run.spawn_point(_starts[zone_index])


## Keeps the spot, the stats and the recording of the climb, and writes the save. After the
## gate it removes the spot. While the marble waits for a respawn, the spot is the place of
## that respawn.
func save_spot() -> void:
	if _run == null:
		return
	var state: GameState = _run.state
	var record: AscentRecord = Save.ascent
	record.falls = falls
	record.fallen = fallen
	record.has_spot = state.status != &"finished"
	record.spot_position = state.position
	record.spot_velocity = state.velocity
	record.spot_time = state.timer
	record.spot_tick = state.tick
	if state.status == &"respawning":
		var rules: Rules = _run.rules
		var pad: LevelObject = rules.checkpoint if rules.checkpoint != null else _run.start
		record.spot_position = _run.spawn_point(pad)
		record.spot_velocity = Vector3.ZERO
	record.spot_height = _height_of(record.spot_position)
	record.spot_zones = ",".join(PackedStringArray(_zone_ids))
	record.spot_checkpoint = _checkpoints.find(_run.rules.checkpoint as Checkpoint)
	record.spot_floor = _falls.floor_height
	record.spot_low = _falls.low_height
	var tracker: RunTracker = _tracker()
	if record.has_spot and tracker != null:
		Save.keep_ghost(CLIMB_GHOST, tracker.recording)
	Save.write()


func _init() -> void:
	name = &"Ascent"
	add_child(sky)
	add_child(flag)


## Saves the spot when the run leaves the tree: a quit to the menus, or the end of the game.
## After that the mode saves no more: the run is gone, and a later save would put its old
## spot over the save of the next run.
func _exit_tree() -> void:
	save_spot()
	_run = null


## Saves the spot when the player closes the window.
func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		save_spot()


## Returns the climb: a Level that holds the zone levels of ids that have a scene, made ready
## as the class text tells. Returns null when no zone has a scene.
func _build(ids: Array[StringName]) -> Level:
	var level: Level = Level.new()
	level.name = &"Climb"
	level.title = "TITLE_ASCENT"
	level.tier = ID
	level.music = ID
	for id: StringName in ids:
		var zone_level: Level = Game.make_level(id)
		if zone_level == null:
			push_warning("Ascent: zone %s has no scene; the climb goes on without it" % id)
			continue
		var pads: Array[Node] = []
		_find(zone_level, pads, func(node: Node) -> bool: return node is StartPad)
		if pads.is_empty():
			push_warning("Ascent: zone %s has no start pad; the climb goes on without it" % id)
			zone_level.free()
			continue
		_strip(zone_level)
		_set_ranges(zone_level)
		_starts.append(pads[0] as StartPad)
		_zone_ids.append(id)
		level.add_child(zone_level)
	if _starts.is_empty():
		level.free()
		return null
	level.id = record_id(_zone_ids)
	_keep_last_finish(level)
	if Save.ascent.assist:
		_add_checkpoints()
	return level


## Removes what a zone has for a play of its own: the sun, the sky, the lightmap and the
## reflection probes (AscentSky lights the whole climb, and its light changes with the
## height, so a probe that looks once would keep the light of the start), and every
## checkpoint (the climb has none, but those of Assist).
func _strip(zone_level: Level) -> void:
	var own: Array[Node] = []
	_find(
		zone_level,
		own,
		func(node: Node) -> bool:
			return (
				node is WorldEnvironment
				or node is DirectionalLight3D
				or node is LightmapGI
				or node is ReflectionProbe
				or node is Checkpoint
			)
	)
	for node: Node in own:
		node.get_parent().remove_child(node)
		node.free()


## Gives every mesh of a zone its visibility range: FAR from its nearest side.
func _set_ranges(zone_level: Level) -> void:
	var meshes: Array[Node] = []
	_find(zone_level, meshes, func(node: Node) -> bool: return node is GeometryInstance3D)
	for node: Node in meshes:
		var mesh: GeometryInstance3D = node as GeometryInstance3D
		mesh.visibility_range_end = FAR + mesh.get_aabb().size.length() * 0.5
		mesh.visibility_range_end_margin = FAR_FADE
		mesh.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF


## Removes every finish pad of the climb but the last, and puts the gate on that one.
func _keep_last_finish(level: Level) -> void:
	var pads: Array[Node] = []
	_find(level, pads, func(node: Node) -> bool: return node is Finish)
	if pads.is_empty():
		return
	_gate = pads[-1] as Finish
	_gate.add_child(AscentGate.new())
	for pad: Node in pads.slice(0, -1):
		pad.get_parent().remove_child(pad)
		pad.free()


## Puts an Assist checkpoint on the start pad of each zone.
func _add_checkpoints() -> void:
	for start: StartPad in _starts:
		var checkpoint: Checkpoint = CHECKPOINT.instantiate() as Checkpoint
		checkpoint.name = "assist_%d" % (_checkpoints.size() + 1)
		checkpoint.transform = start.transform
		start.get_parent().add_child(checkpoint)
		_checkpoints.append(checkpoint)


## Measures the climb in the tree, then starts a new climb or continues the saved one.
func _begin(run: LevelRun, new_climb: bool) -> void:
	_run = run
	var tuning: MarbleTuning = run.marble.tuning
	var space: PhysicsDirectSpaceState3D = run.get_world_3d().direct_space_state
	_world = WorldQuery.new(space, tuning.radius, tuning.contact_margin)
	_up = _starts[0].global_basis.y.normalized()
	_base = run.spawn_point(_starts[0])
	for start: StartPad in _starts:
		zone_heights.append(_height_of(run.spawn_point(start)))
	top = _height_of(run.spawn_point(_gate)) if _gate != null else zone_heights[-1]
	_kill_height = run.rules.kill_height
	if new_climb or not has_spot(_zone_ids):
		_new_climb()
	else:
		_continue()
	_follow()
	_plant_flag()
	run.stepped.connect(_on_stepped)
	run.teleported.connect(_follow)
	Game.screen_changed.connect(_on_screen_changed)



## Starts the stats of a new climb. The spot of the last climb is gone at the next save.
func _new_climb() -> void:
	_falls = AscentFalls.new()
	_ended = false
	Save.ascent.assisted = Save.ascent.assist
	_run.keeps_records = not Save.ascent.assisted


## Puts the run at the saved spot, with the stats and the recording of the climb so far.
func _continue() -> void:
	var record: AscentRecord = Save.ascent
	_run.resume(record.spot_tick, record.spot_time, record.spot_position, record.spot_velocity)
	_falls = AscentFalls.new()
	_falls.falls = record.falls
	_falls.fallen = record.fallen
	_falls.resume(record.spot_position, record.spot_floor, record.spot_low)
	record.assisted = record.assisted or record.assist
	_run.keeps_records = not record.assisted
	var tracker: RunTracker = _tracker()
	if tracker != null:
		var recording: Ghost = Save.ghost(CLIMB_GHOST)
		tracker.recording = recording if recording != null else Ghost.new()
		# A recording that is shorter than the clock stands at the spot for the missing time.
		var rotation: Quaternion = _run.marble.ball_rotation
		while float(tracker.recording.size()) / Ghost.RATE <= record.spot_time:
			var size: int = tracker.recording.size()
			tracker.recording.record(float(size) / Ghost.RATE, record.spot_position, rotation)
			if tracker.recording.size() == size:
				break
	if record.spot_checkpoint >= 0 and record.spot_checkpoint < _checkpoints.size():
		_run.rules.reach_checkpoint(_checkpoints[record.spot_checkpoint])


## Follows the tick that just ran.
func _on_stepped() -> void:
	var state: GameState = _run.state
	if state.tick == 1:
		_new_climb()
	_follow()
	if state.status == &"playing":
		var ground: Contact = _floor(state)
		if _falls.track(state.position, height, ground != null):
			_plant_flag()
		var counts: bool = ground != null and ground.object == null and _run.keeps_records
		if counts and height > Save.ascent.best_height + BEST_STEP:
			Save.ascent.best_height = height
			Save.ascent.best_position = ground.point
	elif state.status == &"finished" and not _ended:
		_ended = true
		save_spot()


## Writes the height of the marble's place into the state, and follows the zone, the Assist
## checkpoint and the light. It runs after each tick and after each teleport.
func _follow() -> void:
	var state: GameState = _run.state
	height = _height_of(state.position)
	state.height = height
	var now: int = _zone_at(height, zone)
	if now != zone:
		zone = now
		Music.set_zone(zone)
		zone_changed.emit(zone)
	var checkpoint: LevelObject = _run.rules.checkpoint
	var drop: float = checkpoint.global_position.y - ASSIST_DROP if checkpoint != null else -INF
	_run.rules.kill_height = maxf(_kill_height, drop)
	sky.show_height(height)


## Saves the spot when the game pauses, so that a crash in the pause loses nothing.
func _on_screen_changed(screen: StringName) -> void:
	if screen == &"pause":
		save_spot()


## Puts the flag at the best height, on the floor there. A best height under one fall has no
## flag: it is still on the first floor.
func _plant_flag() -> void:
	flag.visible = Save.ascent.best_height >= AscentFalls.FALL_HEIGHT
	flag.global_position = Save.ascent.best_position
	flag.global_basis = Basis(Quaternion(Vector3.UP, _up))


## Returns the floor that the marble stands on: its most upward contact that is a floor
## (FLOOR_UP). Null in the air and on a wall.
func _floor(state: GameState) -> Contact:
	var found: Contact = null
	if not state.on_ground:
		return found
	for contact: Contact in _world.contacts(state.position):
		var lean: float = contact.normal.dot(_up)
		if lean >= FLOOR_UP and (found == null or lean > found.normal.dot(_up)):
			found = contact
	return found


## Returns the zone of a marble at at_height that was in zone from before.
func _zone_at(at_height: float, from: int) -> int:
	var now: int = from
	while now + 1 < zone_heights.size() and at_height >= zone_heights[now + 1] - ZONE_ENTER:
		now += 1
	while now > 0 and at_height < zone_heights[now] - ZONE_LEAVE:
		now -= 1
	return now


## Returns the height of point above the climb start, m.
func _height_of(point: Vector3) -> float:
	return (point - _base).dot(_up)


## Returns the RunTracker that Save put into the run, or null (a run outside Game).
func _tracker() -> RunTracker:
	return _run.get_node_or_null(^"RunTracker") as RunTracker


## Adds node and every node under it for which wanted returns true to found, in tree order.
static func _find(node: Node, found: Array[Node], wanted: Callable) -> void:
	var keep: bool = wanted.call(node)
	if keep:
		found.append(node)
	for child: Node in node.get_children():
		_find(child, found, wanted)

