extends GutTest
## SaveGame through its public API and its file: a save and a load give the same data, a
## missing or damaged file gives the defaults, and the unlock rules. Each test uses its own
## folder under user://test_save/.

const ROOT: String = "user://test_save"

var save: SaveGame


func before_each() -> void:
	_remove(ROOT)
	save = _fresh()


func after_all() -> void:
	_remove(ROOT)


## A save and a load give back every section unchanged.
func test_save_then_load_is_unchanged() -> void:
	save.finish(&"b01", 12.345678901234, &"gold", null)
	save.find_egg(&"b02", &"egg_01")
	save.find_egg(&"b02", &"egg_00")
	save.find_egg(&"b02", &"egg_01")
	save.settings.dead_zone = 0.27
	save.settings.invert_y = true
	save.settings.graphics_preset = &"low"
	save.ascent.has_spot = true
	save.ascent.spot_position = Vector3(1.5, 230.25, -7.125)
	save.ascent.falls = 3
	assert_true(save.write())
	var loaded: SaveGame = _fresh()
	loaded.read()
	assert_eq(loaded.level(&"b01").best_time, 12.345678901234)
	assert_eq(loaded.level(&"b01").medal, &"gold")
	assert_eq(loaded.level(&"b02").eggs, PackedStringArray(["egg_00", "egg_01"]))
	assert_eq(loaded.settings.to_dict(), save.settings.to_dict())
	assert_eq(loaded.ascent.to_dict(), save.ascent.to_dict())
	assert_eq(loaded.ascent.spot_position, Vector3(1.5, 230.25, -7.125))
	assert_eq(loaded.settings.graphics_preset, &"low")


## The file holds the format version, and no temporary file stays.
func test_file_is_versioned() -> void:
	save.find_egg(&"b01", &"egg_00")
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(_file()))
	assert_true(data is Dictionary)
	var fields: Dictionary = data if data is Dictionary else {}
	var version: float = fields.get("version", 0.0)
	assert_eq(version, float(SaveGame.VERSION))
	assert_false(FileAccess.file_exists(_file() + ".tmp"))


## No file gives the defaults.
func test_missing_file_gives_defaults() -> void:
	save.read()
	assert_eq(save.level(&"b01").best_time, -1.0)
	assert_eq(save.settings.to_dict(), Settings.new().to_dict())
	assert_eq(save.ascent.to_dict(), AscentRecord.new().to_dict())


## A damaged file gives the defaults, and the next write keeps a copy of it.
func test_damaged_file_gives_defaults_and_is_kept() -> void:
	DirAccess.make_dir_recursive_absolute(save.dir)
	_put(_file(), "{\"version\": 1, \"levels\": {\"b01\": {\"best_ti")
	save.read()
	assert_eq(save.level(&"b01").best_time, -1.0)
	save.settings.rumble = false
	assert_true(save.write())
	assert_true(FileAccess.get_file_as_string(_file() + ".bad").begins_with("{\"version\": 1"))
	var loaded: SaveGame = _fresh()
	loaded.read()
	assert_false(loaded.settings.rumble)


## A value of the wrong type keeps that default; the other values load.
func test_wrong_types_keep_defaults() -> void:
	DirAccess.make_dir_recursive_absolute(save.dir)
	var text: String = JSON.stringify(
		{
			"version": 2,
			"levels": {"b01": {"best_time": "fast", "medal": "gold", "eggs": ["egg_00", 2]}},
			"settings":
			{
				"dead_zone": [0.3],
				"invert_y": true,
				"resolution": [1280],
				"bindings": {"jump.pad": 3},
			},
			"ascent": {"spot_position": [1, 2]},
		}
	)
	_put(_file(), text)
	save.read()
	assert_eq(save.level(&"b01").best_time, -1.0)
	assert_eq(save.level(&"b01").medal, &"gold")
	assert_eq(save.level(&"b01").eggs.size(), 0, "an egg id that is not text")
	assert_eq(save.settings.dead_zone, Settings.new().dead_zone)
	assert_true(save.settings.invert_y)
	assert_eq(save.settings.resolution, Vector2i.ZERO)
	assert_eq(save.settings.bindings.size(), 0, "a binding that is not text")
	assert_eq(save.ascent.spot_position, Vector3.ZERO)


## A file of version 1 had one egg flag for each level. A found egg becomes the id of the
## level's one egg: its node name in the level's scene, or the kit's first egg name for a
## level with no scene. The next write gives a file of the version of today.
func test_version_1_egg_becomes_the_egg_id() -> void:
	DirAccess.make_dir_recursive_absolute(save.dir)
	var levels: Dictionary = {
		"rules": {"best_time": 9.5, "medal": "gold", "egg": true},
		"no_such_level": {"egg": true},
		"flat": {"best_time": 4.0, "egg": false},
	}
	_put(_file(), JSON.stringify({"version": 1, "levels": levels}))
	save.read()
	assert_eq(save.level(&"rules").eggs, PackedStringArray(["Egg"]), "the name in rules.tscn")
	assert_eq(save.level(&"rules").best_time, 9.5)
	assert_eq(save.level(&"no_such_level").eggs, PackedStringArray([Level.DEFAULT_EGG]))
	assert_eq(save.level(&"flat").eggs.size(), 0)
	assert_true(save.write())
	var text: String = FileAccess.get_file_as_string(_file())
	assert_true(text.contains("\"version\": 2"))
	assert_false(text.contains("\"egg\":"), "the flag of version 1 is gone")


## The eggs of a level are a set: has_eggs() is true when every egg of the level is found.
func test_every_egg_of_a_level() -> void:
	save.find_egg(&"zone_3", &"egg_crate")
	assert_false(save.level(&"zone_3").has_eggs(2))
	save.find_egg(&"zone_3", &"egg_fin")
	assert_true(save.level(&"zone_3").has_eggs(2))
	assert_false(save.level(&"zone_3").has_eggs(0), "a level with no egg")


## Beginner level 1 is open; each next level opens when the one before it is qualified.
func test_qualifying_unlocks_the_next_level() -> void:
	assert_true(save.is_unlocked(&"b01"))
	assert_false(save.is_unlocked(&"b02"))
	save.finish(&"b01", 40.0, &"none", null)
	assert_false(save.is_unlocked(&"b02"), "a finish over par does not unlock")
	save.finish(&"b01", 25.0, &"qualified", null)
	assert_true(save.is_unlocked(&"b02"))
	assert_false(save.is_unlocked(&"b03"))
	assert_true(save.is_unlocked(&"core_loop"), "levels outside the campaign are open")
	assert_true(save.is_tier_unlocked(&"beginner"))
	assert_false(save.is_tier_unlocked(&"intermediate"))


## The best time only improves, the best medal stays, and only a new best keeps the ghost.
func test_finish_keeps_the_best() -> void:
	assert_true(save.finish(&"b01", 20.0, &"qualified", _line(1.0)))
	assert_false(save.finish(&"b01", 22.0, &"qualified", _line(2.0)))
	assert_eq(save.level(&"b01").best_time, 20.0)
	assert_almost_eq(save.ghost(&"b01").transform_at(1.0).origin.x, 1.0, 0.001)
	assert_true(save.finish(&"b01", 14.0, &"gold", _line(3.0)))
	assert_false(save.finish(&"b01", 15.0, &"qualified", null))
	assert_eq(save.level(&"b01").medal, &"gold")
	assert_almost_eq(save.ghost(&"b01").transform_at(1.0).origin.x, 3.0, 0.001)
	assert_null(save.ghost(&"b02"))


## A damaged ghost file reads as no ghost.
func test_damaged_ghost_is_none() -> void:
	save.finish(&"b01", 20.0, &"qualified", _line(1.0))
	var path: String = save.dir.path_join("ghosts/b01.ghost")
	_put(path, "ORGH not a ghost")
	assert_null(save.ghost(&"b01"))


## Returns a SaveGame in this test's folder.
func _fresh() -> SaveGame:
	var fresh: SaveGame = SaveGame.new()
	fresh.dir = ROOT.path_join("case")
	autofree(fresh)
	return fresh


## Returns the path of the save file.
func _file() -> String:
	return save.dir.path_join(SaveGame.FILE)


## Returns a 2 s ghost that moves along x at speed m/s.
static func _line(speed: float) -> Ghost:
	var ghost: Ghost = Ghost.new()
	for tick: int in 241:
		var time: float = tick / 120.0
		ghost.record(time, Vector3(speed * time, 0, 0), Quaternion())
	return ghost


## Writes text to path.
static func _put(path: String, text: String) -> void:
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	file.store_string(text)
	file.close()


## Deletes the folder at path and everything in it.
static func _remove(path: String) -> void:
	if not DirAccess.dir_exists_absolute(path):
		return
	for sub: String in DirAccess.get_directories_at(path):
		_remove(path.path_join(sub))
	for file: String in DirAccess.get_files_at(path):
		DirAccess.remove_absolute(path.path_join(file))
	DirAccess.remove_absolute(path)
