extends GutTest
## The ghost marble: the shapes of the marble's skin in the ghost look, with no shadow.


## Each part that the ghost shows has the ghost look and casts no shadow. The skin has the
## size of the marble.
func test_shows_the_skin_in_the_ghost_look() -> void:
	var marble: GhostMarble = GhostMarble.new(0.1)
	autofree(marble)
	var shown: int = 0
	for node: Node in marble.find_children("*", "GeometryInstance3D", true, false):
		var part: GeometryInstance3D = node as GeometryInstance3D
		assert_eq(part.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, String(part.name))
		if part.visible:
			shown += 1
			var look: ShaderMaterial = part.material_override as ShaderMaterial
			assert_eq(look.shader, GhostMarble.LOOK, String(part.name))
	assert_gt(shown, 1, "the ghost shows the glass and the core")
	var skin: Node3D = marble.get_child(0) as Node3D
	assert_almost_eq(skin.scale, Vector3.ONE * 0.5, Vector3.ONE * 0.001)
