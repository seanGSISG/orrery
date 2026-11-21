class_name Gem
extends LevelObject
## The `gem` marker: the marble collects it on contact. Placeholder from #7: it only calls the
## rule. #13 hides the gem and brings it back on restart.


## Tells the rules about the gem when the marble enters its trigger.
func on_overlap(run: LevelRun, first: bool) -> void:
	if first:
		run.rules.collect_gem()
