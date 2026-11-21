class_name SaveGame
extends Node
## Progress, settings, the Ascent climb and ghosts (docs/plan.md §2.3, §2.13, §4.4). The
## autoload Save (save.gd) is the one instance in the game; tests make their own with another
## dir. read() loads the file; every change through finish() or find_egg() writes it at once.
## After a change to settings or ascent, call write().
##
## Files in dir:
## - save.json: {"version": 1, "levels": {id: LevelRecord}, "settings": Settings,
##   "ascent": AscentRecord}, each record as SaveRecord.to_dict() gives it.
## - ghosts/<id>.ghost: the ghost of the best run of level id, in the Ghost file format.
##
## Each write goes to <file>.tmp first and then renames it over the file, so a crash leaves
## the old file or the new one. A file that read() cannot use leaves the defaults in place,
## and the next write first keeps a copy of it as save.json.bad.

const VERSION: int = 1
const FILE: String = "save.json"
const GHOSTS: String = "ghosts"
const MEDALS: Array[StringName] = [&"none", &"qualified", &"gold"]

## Folder of the save file and the ghosts.
var dir: String = "user://"
var settings: Settings = Settings.new()
var ascent: AscentRecord = AscentRecord.new()

var _levels: Dictionary[StringName, LevelRecord] = {}
## The file that read() could not fully use; write() keeps a copy of it first. Empty: none.
var _damaged: String = ""


## Loads save.json from dir, or the defaults when it is missing or damaged. Writes nothing.
func read() -> void:
	settings = Settings.new()
	ascent = AscentRecord.new()
	_levels.clear()
	_damaged = ""
	var path: String = _path()
	if not FileAccess.file_exists(path):
		# A crash between the two steps of a write on Windows can leave only the new file.
		path += ".tmp"
		if not FileAccess.file_exists(path):
			return
	var json: JSON = JSON.new()
	var data: Dictionary = {}
	if json.parse(FileAccess.get_file_as_string(path)) == OK and json.data is Dictionary:
		data = json.data
	var found: Variant = data.get("version")
	var number: float = found if found is float or found is int else 0.0
	var version: int = roundi(number)
	if version < 1:
		push_warning("Save: %s is damaged; using the defaults" % path)
		_damaged = path
		return
	if version > VERSION:
		push_warning("Save: %s is from a newer version; reading the known keys" % path)
		_damaged = path
	data = _migrate(data, version)
	settings.fill(_section(data, "settings"))
	ascent.fill(_section(data, "ascent"))
	var levels: Dictionary = _section(data, "levels")
	for id: Variant in levels:
		var value: Variant = levels[id]
		if id is String and value is Dictionary:
			var fields: Dictionary = value
			var record: LevelRecord = LevelRecord.new()
			record.fill(fields)
			_levels[StringName(str(id))] = record


## Writes save.json. Returns false when the file could not be written.
func write() -> bool:
	if _damaged != "" and FileAccess.file_exists(_damaged):
		var error: Error = DirAccess.copy_absolute(_damaged, _path() + ".bad")
		if error != OK:
			push_warning("Save: cannot keep a copy of %s (%s)" % [_damaged, error_string(error)])
			return false
	_damaged = ""
	var levels: Dictionary[String, Variant] = {}
	for id: StringName in _levels:
		levels[String(id)] = _levels[id].to_dict()
	var data: Dictionary[String, Variant] = {
		"version": VERSION,
		"levels": levels,
		"settings": settings.to_dict(),
		"ascent": ascent.to_dict(),
	}
	return _write_atomic(_path(), JSON.stringify(data, "\t", true, true).to_utf8_buffer())


## Returns the saved progress of level id. A level with no progress gives a new default
## record that is not kept. Read it only; finish() and find_egg() change it.
func level(id: StringName) -> LevelRecord:
	return _levels.get(id, LevelRecord.new())


## Returns true when the player may play level id: the first campaign level, a level after a
## qualified one, and every level outside the campaign.
func is_unlocked(id: StringName) -> bool:
	var before: StringName = Campaign.previous(id)
	return before == &"" or level(before).qualified()


## Returns true when the first level of tier is unlocked.
func is_tier_unlocked(tier: StringName) -> bool:
	var levels: Array[StringName] = Campaign.levels(tier)
	return not levels.is_empty() and is_unlocked(levels[0])


## Keeps a finish of level id in time with medal. A new best time also keeps ghost as the
## level's ghost. The best medal stays. Writes the file on a change. Returns true for a new
## best time.
func finish(id: StringName, time: float, medal: StringName, ghost: Ghost) -> bool:
	var record: LevelRecord = _record(id)
	var best: bool = record.best_time < 0.0 or time < record.best_time
	var better: bool = MEDALS.find(medal) > MEDALS.find(record.medal)
	if best:
		record.best_time = time
		if ghost != null and ghost.size() > 0:
			keep_ghost(id, ghost)
	if better:
		record.medal = medal
	if best or better:
		write()
	return best


## Keeps the Clockwork Egg of level id as found, and writes the file the first time.
func find_egg(id: StringName) -> void:
	var record: LevelRecord = _record(id)
	if not record.egg:
		record.egg = true
		write()


## Writes ghost as the ghost file of id. finish() keeps the ghost of a best run this way.
## Ascent also keeps the recording of a climb that is not finished, under an id of its own.
## Returns false when the file could not be written.
func keep_ghost(id: StringName, ghost: Ghost) -> bool:
	return _write_atomic(_ghost_path(id), ghost.to_bytes())


## Returns the ghost that finish() or keep_ghost() wrote for id, or null when there is none
## or its file is damaged.
func ghost(id: StringName) -> Ghost:
	var path: String = _ghost_path(id)
	if not FileAccess.file_exists(path):
		return null
	return Ghost.from_bytes(FileAccess.get_file_as_bytes(path))


## Returns the kept record of level id, and makes it when it is new.
func _record(id: StringName) -> LevelRecord:
	if not _levels.has(id):
		_levels[id] = LevelRecord.new()
	return _levels[id]


## Returns the path of save.json.
func _path() -> String:
	return dir.path_join(FILE)


## Returns the path of the ghost file of level id.
func _ghost_path(id: StringName) -> String:
	return dir.path_join(GHOSTS).path_join("%s.ghost" % id.validate_filename())


## Turns the data of an older format version into the current one. Each new version adds one
## step here. Version 1 is the first.
static func _migrate(data: Dictionary, _from: int) -> Dictionary:
	return data


## Returns data[key] when it is a dictionary, else an empty one.
static func _section(data: Dictionary, key: String) -> Dictionary:
	var value: Variant = data.get(key)
	return value if value is Dictionary else {}


## Writes bytes to path.tmp and renames it over path. Returns false on an error. A path.tmp
## with no path is the last good write (read() falls back to it), so it becomes path first.
static func _write_atomic(path: String, bytes: PackedByteArray) -> bool:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var temp: String = path + ".tmp"
	if not FileAccess.file_exists(path) and FileAccess.file_exists(temp):
		if DirAccess.rename_absolute(temp, path) != OK:
			push_warning("Save: cannot recover %s" % temp)
			return false
	var file: FileAccess = FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		push_warning("Save: cannot write %s (%s)" % [temp, error_string(FileAccess.get_open_error())])
		return false
	var stored: bool = file.store_buffer(bytes)
	file.close()
	if not stored or DirAccess.rename_absolute(temp, path) != OK:
		push_warning("Save: cannot write %s" % path)
		return false
	return true
