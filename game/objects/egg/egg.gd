class_name Egg
extends LevelObject
## The `egg` marker: the level's hidden Clockwork Egg. Placeholder from #7: it only calls the
## rule. #13 adds the logic.


## Tells the rules about the egg when the marble enters its trigger.
func on_overlap(run: LevelRun, first: bool) -> void:
	if first:
		run.rules.find_egg()
