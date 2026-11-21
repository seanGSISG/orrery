extends GutTest
## The text of the HUD and the menus (docs/plan.md §2.13): every text key has English text
## in res://ui/text/en.po, and times read as the clock shows them.

const UI_DIR: String = "res://ui"
## A text key in a script: capital words joined by underscores, in quotes.
const KEY_PATTERN: String = '"([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)"'


## Every text key in the UI scripts, and the key of each tier and medal, has a translation.
func test_every_text_key_has_english() -> void:
	var keys: Array[String] = []
	_collect_keys(UI_DIR, keys)
	var tiers: Array[StringName] = Campaign.TIERS.duplicate()
	tiers.append(LevelCatalog.TEST_TIER)
	for tier: StringName in tiers:
		keys.append("TIER_" + String(tier).to_upper())
	for medal: StringName in SaveGame.MEDALS:
		keys.append("MEDAL_" + String(medal).to_upper())
	assert_gt(keys.size(), 30, "the scan found the keys")
	for key: String in keys:
		assert_ne(tr(key), key, key)


## A time shows minutes, seconds and hundredths; the hundredths are cut, not rounded.
func test_time_text() -> void:
	assert_eq(TimeText.full(0.0), "0:00.00")
	assert_eq(TimeText.full(46.829), "0:46.82")
	assert_eq(TimeText.full(70.0), "1:10.00")
	assert_eq(TimeText.minutes(48.99), "0:48")
	assert_eq(TimeText.target(48.0), "0:48")
	assert_eq(TimeText.target(46.82), "0:46.82", "a target keeps its hundredths")
	assert_eq(TimeText.difference(4.38), "4.38")
	assert_eq(TimeText.difference(64.38), "1:04.38")


## Adds the text keys of every script under dir to keys. Comment lines do not count.
func _collect_keys(dir: String, keys: Array[String]) -> void:
	var pattern: RegEx = RegEx.create_from_string(KEY_PATTERN)
	for file: String in DirAccess.get_files_at(dir):
		if file.get_extension() != "gd":
			continue
		for line: String in FileAccess.get_file_as_string(dir.path_join(file)).split("\n"):
			if line.strip_edges().begins_with("#"):
				continue
			for found: RegExMatch in pattern.search_all(line):
				if not keys.has(found.get_string(1)):
					keys.append(found.get_string(1))
	for child: String in DirAccess.get_directories_at(dir):
		_collect_keys(dir.path_join(child), keys)
