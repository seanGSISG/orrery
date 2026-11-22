extends RunTest
## The Clockwork Egg through the boundary: the marble finds it, the lid tips back and the
## clockwork rises; a restart closes it. The egg has a small warm light of its own.

const RULES: PackedScene = preload("res://test/levels/rules.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The egg of rules.tscn, on the floor.
const EGG: Vector3 = Vector3(-6, 0, -10)

var _egg: Egg


func before_each() -> void:
	start_run(RULES)
	_egg = run.level.find_children("*", "Egg", true, false)[0] as Egg


## The egg lights the room that hides it: one warm light in real time, about 4 m far, that no
## lightmap holds.
func test_egg_has_a_small_warm_light() -> void:
	var lights: Array[Node] = _egg.find_children("*", "OmniLight3D", true, false)
	assert_eq(lights.size(), 1)
	var light: OmniLight3D = lights[0]
	assert_almost_eq(light.omni_range, 4.0, 0.5)
	assert_gt(light.light_color.r, light.light_color.b, "the light is warm")
	assert_eq(light.light_bake_mode, Light3D.BAKE_DISABLED)


## The egg's light stops at walls (it casts shadows), but the egg casts none, so its own
## shell does not put its foot in shadow.
func test_egg_light_casts_shadows_but_not_the_eggs_own() -> void:
	var light: OmniLight3D = _egg.find_children("*", "OmniLight3D", true, false)[0]
	assert_true(light.shadow_enabled, "the light stops at walls")
	var shapes: Array[Node] = _egg.get_node("Model").find_children("*", "GeometryInstance3D")
	assert_gt(shapes.size(), 0)
	for node: Node in shapes:
		var shape: GeometryInstance3D = node as GeometryInstance3D
		assert_eq(shape.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, shape.name)


## The egg starts closed with the clockwork hidden, opens when the marble finds it, and a
## restart closes it again.
func test_egg_opens_when_found_and_closes_at_restart() -> void:
	var lid: Node3D = _egg.get_node("Model/lid")
	var gear: Node3D = _egg.get_node("Model/gear")
	assert_eq(lid.rotation.x, 0.0)
	assert_false(gear.visible)
	run.teleport(EGG + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(MarbleInput.new(), Egg.OPEN_TIME + 0.1)
	assert_true(run.state.egg_found)
	assert_almost_eq(lid.rotation.x, -Egg.LID_ANGLE, 0.001)
	assert_true(gear.visible)
	assert_almost_eq(gear.position.y, Egg.GEAR_UP, 0.001)
	run.restart()
	assert_eq(lid.rotation.x, 0.0)
	assert_false(gear.visible)
