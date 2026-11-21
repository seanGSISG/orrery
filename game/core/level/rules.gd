class_name Rules
extends RefCounted
## The level rules (docs/plan.md §2.3). LevelRun makes one, calls reset() at each restart and
## after_step() at the end of each tick. The gem, checkpoint, finish and egg objects call the
## other methods. Rules writes these GameState fields: status (after the run sets
## &"playing"), gems_collected, gems_total, timer, medal, checkpoint and egg_found.
##
## - The clock starts on the first tick with a move, jump or use input. So a restart has no
##   wait, and the player can turn the camera first. It runs on through respawns and stops at
##   the finish.
## - The finish takes the marble only when all gems are collected. The medal is &"gold" at or
##   under Level.gold, &"qualified" at or under Level.par, else &"none".
## - Out of bounds is a marble centre below kill_height. The status is &"respawning" for
##   RESPAWN_DELAY, then the marble comes back still on the last checkpoint, else on the start
##   pad. Collected gems, the egg and the held power-up stay.

## Out of bounds starts this far below the lowest Solid of the level, m.
const KILL_DEPTH: float = 5.0
## Time from out of bounds to the respawn, s.
const RESPAWN_DELAY: float = 0.5

## World y below which the marble is out of bounds: KILL_DEPTH under the lowest Solid at the
## start of the run.
var kill_height: float = -KILL_DEPTH

var _run: LevelRun
var _dt: float = 1.0 / Engine.physics_ticks_per_second
## The last checkpoint reached; null means the start pad.
var _checkpoint: LevelObject = null
## Ticks since the clock started; -1 before the first input.
var _clock: int = -1
## Ticks left until the respawn while the status is &"respawning".
var _respawn_left: int = 0


func _init(run: LevelRun) -> void:
	_run = run
	var lowest: float = _lowest_solid(run.level)
	kill_height = (lowest if is_finite(lowest) else 0.0) - KILL_DEPTH


## Goes back to the start state of a new attempt: no gems, no time, no checkpoint, no egg.
func reset() -> void:
	var state: GameState = _run.state
	var gems: int = 0
	for object: LevelObject in _run.objects:
		if object is Gem:
			gems += 1
	state.gems_total = gems
	state.gems_collected = 0
	state.timer = 0.0
	state.medal = &"none"
	state.checkpoint = &""
	state.egg_found = false
	_checkpoint = null
	_clock = -1
	_respawn_left = 0


## Runs at the end of each tick, after the objects' hooks: the clock, out of bounds and the
## respawn. Does nothing after the finish.
func after_step() -> void:
	var state: GameState = _run.state
	if state.status == &"finished":
		return
	if _clock < 0 and _wants_to_move(_run.last_input):
		_clock = 0
	if _clock >= 0:
		_clock += 1
		state.timer = _clock * _dt
	if state.status == &"respawning":
		_respawn_left -= 1
		if _respawn_left <= 0:
			_run.respawn(_run.spawn_point(_checkpoint if _checkpoint != null else _run.start))
			state.status = &"playing"
	elif state.status == &"playing" and _run.marble.position.y < kill_height:
		state.status = &"respawning"
		_respawn_left = roundi(RESPAWN_DELAY / _dt)


## A gem calls this once when the marble collects it.
func collect_gem() -> void:
	_run.state.gems_collected += 1


## A checkpoint calls this when the marble reaches it. Later respawns put the marble there.
func reach_checkpoint(checkpoint: LevelObject) -> void:
	if _run.state.status != &"playing":
		return
	_checkpoint = checkpoint
	_run.state.checkpoint = checkpoint.name


## The finish calls this while the marble is on it. Returns true when the run finishes now:
## the run is playing and every gem is collected. Then the clock stops and the medal is set.
func reach_finish() -> bool:
	var state: GameState = _run.state
	if state.status != &"playing" or state.gems_collected < state.gems_total:
		return false
	state.status = &"finished"
	if state.timer <= _run.level.gold:
		state.medal = &"gold"
	elif state.timer <= _run.level.par:
		state.medal = &"qualified"
	return true


## The egg calls this once when the marble finds it.
func find_egg() -> void:
	_run.state.egg_found = true


## True when input asks the marble to do something; camera turns do not count.
static func _wants_to_move(input: MarbleInput) -> bool:
	return input.move != Vector2.ZERO or input.jump or input.use


## The lowest world y of every Solid shape under node, or INF when there is none.
static func _lowest_solid(node: Node) -> float:
	var lowest: float = INF
	var shape_node: CollisionShape3D = node as CollisionShape3D
	if shape_node != null and shape_node.shape != null and shape_node.get_parent() is Solid:
		var bounds: AABB = shape_node.global_transform * shape_node.shape.get_debug_mesh().get_aabb()
		lowest = bounds.position.y
	for child: Node in node.get_children():
		lowest = minf(lowest, _lowest_solid(child))
	return lowest
