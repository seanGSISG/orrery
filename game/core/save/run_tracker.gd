class_name RunTracker
extends Node
## Saves one run as it happens, and races it against the best run's ghost. Make it with
## attach(run, save) after the run's _ready(); the autoload Save does this for every run that
## Game loads.
##
## On each LevelRun.stepped it reads run.state (the state of the new tick) and:
## - calls save.find_egg() when egg_found becomes true, and save.finish() with the recorded
##   ghost when the status becomes &"finished", so no event waits for a later tick;
## - records the marble's pose into a Ghost at Ghost.RATE per second of level clock;
## - puts the ghost marble of the best run at the level clock, shown while
##   save.settings.ghost is true.
## Tick 1 starts a new attempt (only restart() sets the tick back): a new recording, and the
## ghost of a new best races from then on.

var save: SaveGame
var run: LevelRun
## The ghost marble of the best run; null before the level has a finish.
var ghost_marble: GhostMarble
## The ghost of this attempt so far.
var recording: Ghost = Ghost.new()

var _egg_saved: bool = false
var _finish_saved: bool = false
## The ghost of a new best in this attempt; the ghost marble takes it in the next attempt.
var _new_best: Ghost


## Adds a tracker to run, which must be ready, and returns it. The ghost marble shows the
## best run that save holds for the level.
static func attach(run: LevelRun, save: SaveGame) -> RunTracker:
	var tracker: RunTracker = RunTracker.new()
	tracker.name = &"RunTracker"
	tracker.save = save
	tracker.run = run
	run.add_child(tracker)
	run.stepped.connect(tracker._on_stepped)
	tracker._race(save.ghost(run.level.id))
	return tracker


## Saves, records and moves the ghost marble from the state of the tick that just ran.
func _on_stepped() -> void:
	var state: GameState = run.state
	var first: bool = state.tick == 1
	if first:
		_start_attempt()
	_save_events()
	if state.status == &"playing" or state.status == &"respawning":
		recording.record(state.timer, state.position, run.marble.ball_rotation)
	if ghost_marble != null:
		ghost_marble.visible = save.settings.ghost
		ghost_marble.show_at(state.timer)
		if first:
			# Draw the jump back to the start at once, not as a slide across the level.
			ghost_marble.reset_physics_interpolation()


## Starts a new recording, and makes the ghost marble race a new best of the last attempt.
func _start_attempt() -> void:
	recording = Ghost.new()
	_egg_saved = false
	_finish_saved = false
	if _new_best != null:
		_race(_new_best)
		_new_best = null


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
		recording.finish(state.timer, state.position, run.marble.ball_rotation)
		if save.finish(level, state.timer, state.medal, recording):
			_new_best = recording


## Makes the ghost marble play ghost, when there is one.
func _race(ghost: Ghost) -> void:
	if ghost == null:
		return
	if ghost_marble == null:
		ghost_marble = GhostMarble.new(run.marble.tuning.radius)
		ghost_marble.name = &"Ghost"
		add_child(ghost_marble)
	ghost_marble.ghost = ghost
	ghost_marble.visible = save.settings.ghost
	ghost_marble.show_at(0.0)
