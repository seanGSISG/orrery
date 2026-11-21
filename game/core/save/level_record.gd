class_name LevelRecord
extends SaveRecord
## The saved progress of one level. Read it with Save.level(id); Save.finish() and
## Save.find_egg() write it.

## Best finish time, s; negative before the first finish.
var best_time: float = -1.0
## Best medal: &"none", &"qualified" or &"gold".
var medal: StringName = &"none"
## True when the player found the level's Clockwork Egg.
var egg: bool = false


## Returns true when the level has a finish at or under par.
func qualified() -> bool:
	return medal == &"qualified" or medal == &"gold"
