extends RunTest
## The checkpoint's look (PadLook): a raised pad of stone in a brass rim, with a lens that is
## pale while the pad is off and glows in the checkpoint's colour once the marble reaches it.

const FLAT: PackedScene = preload("res://test/levels/flat.tscn")
const CHECKPOINT: PackedScene = preload("res://objects/checkpoint/checkpoint.tscn")
const TUNING: MarbleTuning = preload("res://core/marble_tuning.tres")
## The pad's centre on the floor.
const AT: Vector3 = Vector3(0, 0, -3)


func test_pad_is_raised_stone_in_brass_and_its_lens_lights() -> void:
	var checkpoint: Checkpoint = CHECKPOINT.instantiate() as Checkpoint
	checkpoint.position = AT
	start_run(FLAT, [checkpoint])
	var pad: MeshInstance3D = checkpoint.get_node("Mesh") as MeshInstance3D
	var rim: Material = pad.get_surface_override_material(PadLook.Part.RIM)
	var stone: Material = pad.get_surface_override_material(PadLook.Part.STONE)
	var lens: StandardMaterial3D = (
		pad.get_surface_override_material(PadLook.Part.LENS) as StandardMaterial3D
	)
	assert_eq(rim, KitMaterials.find("brass"), "the rim is the kit brass")
	assert_eq(stone, PadLook.stone(), "the plate is the pad stone")
	assert_gt(pad.get_aabb().end.y, 0.03, "the pad stands proud of the floor")
	assert_false(lens.emission_enabled, "an unlit lens does not glow")
	assert_gt(lens.albedo_color.get_luminance(), 0.4, "an unlit lens is pale, not dark like a hole")
	run.marble.teleport(AT + Vector3.UP * TUNING.radius, Vector3.ZERO)
	hold(rolling(Vector2.ZERO), 0.1)
	assert_true(lens.emission_enabled, "the lens glows once the marble reached the pad")
	assert_eq(lens.emission, Checkpoint.COLOUR)
