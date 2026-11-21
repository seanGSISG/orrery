class_name LevelRecord
extends SaveRecord
## The saved progress of one level. Read it with Save.level(id); Save.finish() and
## Save.find_egg() write it.

## Best finish time, s; negative before the first finish.
var best_time: float = -1.0
## Best medal: &"none", &"qualified" or &"gold".
var medal: StringName = &"none"
## The ids of the Clockwork Eggs that the player found in the level, sorted. The id of an egg
## is its node name, which is its marker name in the level script. A campaign level has one
## egg; an Ascent zone can have more.
var eggs: PackedStringArray = []


## Returns true when the level has a finish at or under par.
func qualified() -> bool:
	return medal == &"qualified" or medal == &"gold"


## Returns true when the player found every egg of the level, which has total eggs
## (LevelInfo.eggs). False for a level with no egg.
func has_eggs(total: int) -> bool:
	return total > 0 and eggs.size() >= total
