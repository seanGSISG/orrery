class_name Rules
extends RefCounted
## The level rules: clock, gems, checkpoints, finish, egg, out of bounds. LevelRun makes one
## and calls reset() and after_step(); objects call the other methods. This is the #7 stub:
## it only counts the gems. #13 adds the logic.

var _run: LevelRun


func _init(run: LevelRun) -> void:
	_run = run


## Goes back to the start state. restart is false for a checkpoint respawn.
func reset(_restart: bool) -> void:
	var gems: int = 0
	for object: LevelObject in _run.objects:
		if object is Gem:
			gems += 1
	_run.state.gems_total = gems


## Runs at the end of each tick: clock, out of bounds, respawn, finish.
func after_step() -> void:
	pass


## A gem calls this when the marble collects it.
func collect_gem() -> void:
	pass


## A checkpoint calls this when the marble reaches it.
func reach_checkpoint(_checkpoint: LevelObject) -> void:
	pass


## The finish calls this when the marble reaches it.
func reach_finish() -> void:
	pass


## The egg calls this when the marble finds it.
func find_egg() -> void:
	pass
