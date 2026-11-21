class_name LevelCatalog
extends RefCounted
## The tiers and levels of the level select, in play order. LevelCatalog.of_game() gives the
## campaign (Campaign). In a debug build it adds the tier &"test": every built level and test
## level outside the campaign, so that they can be played from the menu. A release build has
## no such tier. A test makes its own catalogue with add_tier().

const TEST_TIER: StringName = &"test"
const LEVEL_DIRS: Array[String] = ["res://levels/built", "res://test/levels"]
const LEVEL_TYPES: Array[String] = ["glb", "tscn"]

## The tiers in play order.
var tiers: Array[StringName] = []

var _levels: Dictionary[StringName, Array] = {}
var _info: Dictionary[StringName, LevelInfo] = {}


## Returns the catalogue of the game.
static func of_game() -> LevelCatalog:
	var catalog: LevelCatalog = LevelCatalog.new()
	for tier: StringName in Campaign.TIERS:
		catalog.add_tier(tier, Campaign.levels(tier))
	if OS.is_debug_build():
		var others: Array[StringName] = _other_levels(catalog)
		if not others.is_empty():
			catalog.add_tier(TEST_TIER, others)
	return catalog


## Adds tier with its level ids in play order, after the tiers so far.
func add_tier(tier: StringName, ids: Array[StringName]) -> void:
	tiers.append(tier)
	_levels[tier] = ids.duplicate()


## Returns the level ids of tier in play order; empty for an unknown tier.
func levels(tier: StringName) -> Array[StringName]:
	var ids: Array[StringName] = []
	var stored: Array = _levels.get(tier, [])
	ids.assign(stored)
	return ids


## Returns the tier of level id, or &"" when the catalogue does not have it.
func tier_of(id: StringName) -> StringName:
	for tier: StringName in tiers:
		if levels(tier).has(id):
			return tier
	return &""


## Returns the level after id in play order, across tiers; &"" after the last level and for
## an unknown level.
func next(id: StringName) -> StringName:
	var found: bool = false
	for tier: StringName in tiers:
		for level: StringName in levels(tier):
			if found:
				return level
			found = level == id
	return &""


## Returns the name and target times of level id. It reads each level scene once.
func info(id: StringName) -> LevelInfo:
	if not _info.has(id):
		_info[id] = LevelInfo.read(id)
	return _info[id]


## Returns true when the player may open tier: its first level is unlocked.
func is_tier_unlocked(tier: StringName) -> bool:
	var ids: Array[StringName] = levels(tier)
	return not ids.is_empty() and Save.is_unlocked(ids[0])


## Returns true when the player can play level id now: it is built and unlocked.
func can_play(id: StringName) -> bool:
	return Save.is_unlocked(id) and info(id).built


## Returns the ids of every level scene in LEVEL_DIRS that catalog does not have, by name.
## An exported build lists a file as <name>.import or <name>.remap, so both ends come off.
static func _other_levels(catalog: LevelCatalog) -> Array[StringName]:
	var ids: Array[StringName] = []
	for dir: String in LEVEL_DIRS:
		# A checkout with no built levels has no res://levels/built/.
		if not DirAccess.dir_exists_absolute(dir):
			continue
		for file: String in DirAccess.get_files_at(dir):
			var name: String = file.trim_suffix(".import").trim_suffix(".remap")
			var id: StringName = StringName(name.get_basename())
			if name.get_extension() in LEVEL_TYPES and catalog.tier_of(id) == &"" and not ids.has(id):
				ids.append(id)
	ids.sort_custom(func(a: StringName, b: StringName) -> bool: return String(a) < String(b))
	return ids
