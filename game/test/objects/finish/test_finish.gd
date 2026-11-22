extends RunTest
## The finish's look (PadLook): a raised pad of stone in a brass rim, with a lens that is pale
## while the finish is closed and glows in the finish's colour once it opens.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const FINISH: PackedScene = preload("res://objects/finish/finish.tscn")


func test_pad_is_raised_stone_in_brass_and_its_lens_lights_when_open() -> void:
	var finish: Finish = FINISH.instantiate() as Finish
	finish.position = Vector3(0, 0, -6)
	start_run(FLAT, [finish])
	var pad: MeshInstance3D = finish.get_node("Mesh") as MeshInstance3D
	var rim: Material = pad.get_surface_override_material(PadLook.Part.RIM)
	var stone: Material = pad.get_surface_override_material(PadLook.Part.STONE)
	var lens: StandardMaterial3D = (
		pad.get_surface_override_material(PadLook.Part.LENS) as StandardMaterial3D
	)
	assert_eq(rim, KitMaterials.find("brass"), "the rim is the kit brass")
	assert_eq(stone, PadLook.stone(), "the plate is the pad stone")
	assert_gt(pad.get_aabb().end.y, 0.03, "the pad stands proud of the floor")
	assert_false(lens.emission_enabled, "a closed finish does not glow")
	assert_gt(lens.albedo_color.get_luminance(), 0.3, "a closed lens is pale, not dark like a hole")
	# A level with no gems opens the finish on its first tick.
	hold(rolling(Vector2.ZERO), 0.1)
	assert_true(lens.emission_enabled, "an open finish glows")
	assert_eq(lens.emission, Finish.COLOUR)
