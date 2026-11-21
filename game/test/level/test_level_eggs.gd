extends GutTest
## Level.egg_ids(): the ids of the eggs of a level, read from its scene file with no level
## made. The save uses them to migrate, and the menus to know how many eggs a level has.

const BUILT: String = "res://levels/built/core_loop.glb"


## A scene made by hand gives the node name of its egg.
func test_scene_gives_its_egg() -> void:
	assert_eq(Level.egg_ids("res://test/levels/rules.tscn"), PackedStringArray(["Egg"]))


## A built level gives the marker name of its egg; the kit names the first one egg_00.
func test_built_level_gives_its_egg() -> void:
	if not ResourceLoader.exists(BUILT):
		fail_test("%s is missing: run `just build-levels`" % BUILT)
		return
	assert_eq(Level.egg_ids(BUILT), PackedStringArray([Level.DEFAULT_EGG]))


## A level with no egg, and a path with no scene, give no ids.
func test_no_egg_gives_no_ids() -> void:
	assert_eq(Level.egg_ids("res://test/levels/flat.tscn").size(), 0)
	assert_eq(Level.egg_ids("res://test/levels/no_such_level.tscn").size(), 0)
	assert_eq(Level.egg_ids("").size(), 0)
