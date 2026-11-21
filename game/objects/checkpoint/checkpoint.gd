class_name Checkpoint
extends LevelObject
## The `checkpoint` marker: a fall respawns the marble at the last one reached. Placeholder
## from #7: it only calls the rule. #13 adds the logic.


## Tells the rules about the checkpoint when the marble enters its trigger.
func on_overlap(run: LevelRun, first: bool) -> void:
	if first:
		run.rules.reach_checkpoint(self)
