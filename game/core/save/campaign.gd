class_name Campaign
extends RefCounted
## The campaign levels in play order (docs/plan.md §2.2, §2.3). Level 1 of Beginner is open.
## Each other level unlocks when the player qualifies on the level before it, also across
## tiers. So a tier unlocks when the player qualifies on the last level of the tier before it.

## The tiers in play order. M2 adds intermediate and advanced.
const TIERS: Array[StringName] = [&"beginner"]
const BEGINNER: Array[StringName] = [&"b01", &"b02", &"b03"]


## Returns the level ids of tier in play order; empty for a tier with no levels.
static func levels(tier: StringName) -> Array[StringName]:
	match tier:
		&"beginner":
			return BEGINNER
	return []


## Returns the level before id in the campaign, across tiers. Returns &"" for the first level
## and for a level outside the campaign (Ascent, test levels).
static func previous(id: StringName) -> StringName:
	var last: StringName = &""
	for tier: StringName in TIERS:
		for level: StringName in levels(tier):
			if level == id:
				return last
			last = level
	return &""
