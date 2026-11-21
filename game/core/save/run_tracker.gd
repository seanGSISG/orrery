class_name RunTracker
extends LevelObject
## Saves one run as it happens, and races it against the best run's ghost. Make it with
## attach(run, save) after the run's _ready(); the autoload Save does this for every run that
## Game loads.
##
## Each tick it reads run.state (the state after the last tick) and:
## - records the marble's pose into a Ghost at Ghost.RATE per second of level clock;
## - puts the ghost marble of the best run at the current level clock, shown while
##   save.settings.ghost is true.
## It calls save.find_egg() when egg_found becomes true, and save.finish() with the recorded
## ghost when the status becomes &"finished". It checks for both on each tick, each frame
## (also when the run no longer steps or the game is paused), at a restart and when the run
## leaves the tree, so no event is lost. A restart starts a new recording, and the ghost of a
## new best run races from then on.
##
## No marker places it. It is a LevelObject only because advance() is the one hook that
## LevelRun calls on every tick, also when the harness or a test steps many ticks at once.

var save: SaveGame
var run: LevelRun
## The ghost marble of the best run; null before the level has a finish.
var ghost_marble: GhostMarble
## The ghost of this attempt so far.
var recording: Ghost = Ghost.new()

var _dt: float = 1.0 / Engine.physics_ticks_per_second
## The ball mesh of the marble, which carries its rotation.
var _ball: Node3D
var _egg_saved: bool = false
var _finish_saved: bool = false
## The ghost of a new best in this attempt; the ghost marble takes it at the next restart.
var _new_best: Ghost


## Adds a tracker to run, which must be ready, and returns it. The ghost marble shows the
## best run that save holds for the level.
static func attach(run: LevelRun, save: SaveGame) -> RunTracker:
	var tracker: RunTracker = RunTracker.new()
	tracker.name = &"RunTracker"
	tracker.save = save
	tracker.run = run
	tracker._ball = run.marble.get_node_or_null(^"Ball") as Node3D
	run.add_child(tracker)
	run.objects.append(tracker)
	tracker._race(save.ghost(run.level.id))
	tracker.reset(true)
	return tracker


## Saves what the ending attempt still owes, then starts a new recording at a restart. A
## respawn keeps the recording.
func reset(restart: bool) -> void:
	if not restart:
		return
	_save_events()
	recording = Ghost.new()
	_egg_saved = false
	_finish_saved = false
	if _new_best != null:
		_race(_new_best)
		_new_best = null
	if ghost_marble != null:
		ghost_marble.show_at(0.0)
		ghost_marble.reset_physics_interpolation()


## Keeps _process() running while the game is paused.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


## Saves an egg or a finish that the steps of this frame made.
func _process(_delta: float) -> void:
	_save_events()


## Saves an egg or a finish before the run goes away.
func _exit_tree() -> void:
	_save_events()


## Records, saves and moves the ghost marble from the state of the last tick.
func advance(_run: LevelRun, _t: float) -> void:
	var state: GameState = run.state
	_save_events()
	if state.status == &"playing" or state.status == &"respawning":
		recording.record(state.timer, state.position, _rotation())
	if ghost_marble != null:
		ghost_marble.visible = save.settings.ghost
		# The clock runs on by one tick in this step, unless it has not started yet.
		var running: bool = state.timer > 0.0 and state.status != &"finished"
		ghost_marble.show_at(state.timer + (_dt if running else 0.0))


## Saves the egg once when egg_found is true, and the finish with the recording once when the
## status is &"finished".
func _save_events() -> void:
	var state: GameState = run.state
	var level: StringName = run.level.id
	if state.egg_found and not _egg_saved:
		_egg_saved = true
		save.find_egg(level)
	if state.status == &"finished" and not _finish_saved:
		_finish_saved = true
		recording.finish(state.timer, state.position, _rotation())
		if save.finish(level, state.timer, state.medal, recording):
			_new_best = recording


## Returns the rotation of the marble's ball.
func _rotation() -> Quaternion:
	return _ball.quaternion if _ball != null else Quaternion()


## Makes the ghost marble play ghost, when there is one.
func _race(ghost: Ghost) -> void:
	if ghost == null:
		return
	if ghost_marble == null:
		ghost_marble = GhostMarble.new(run.marble.tuning.radius)
		ghost_marble.name = &"Ghost"
		add_child(ghost_marble)
	ghost_marble.ghost = ghost
