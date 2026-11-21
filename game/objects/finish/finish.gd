class_name Finish
extends LevelObject
## The `finish` marker: the level ends here. Placeholder from #7: it only calls the rule. #13
## adds the logic.


## Tells the rules about the finish when the marble enters its trigger.
func on_overlap(run: LevelRun, first: bool) -> void:
	if first:
		run.rules.reach_finish()
