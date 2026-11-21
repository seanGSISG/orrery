extends GutTest
## The look of a gem: the cuts differ by outline, the jewel hangs LIFT above the marker and
## casts no shadow, and the shader gets the planes of a convex cut.

const GEM: PackedScene = preload("res://objects/gem/gem.tscn")


## Each cut has another pair of ends: flat or pointed on top, flat or pointed below.
func test_each_cut_has_its_own_outline() -> void:
	var outlines: Array[Vector2i] = []
	for index: int in GemCut.COUNT:
		var cut: GemCut = GemCut.of(index)
		var flat_top: bool = _width_at(cut, cut.top) > 0.01
		var flat_bottom: bool = _width_at(cut, cut.bottom) > 0.01
		var outline: Vector2i = Vector2i(int(flat_top), int(flat_bottom))
		assert_does_not_have(outlines, outline, "cut %d repeats an outline" % index)
		outlines.append(outline)


## A gem is GemCut.SIZE across at its largest.
func test_each_cut_is_half_a_metre_across() -> void:
	for index: int in GemCut.COUNT:
		var size: Vector3 = GemCut.of(index).mesh.get_aabb().size
		assert_almost_eq(maxf(size.x, maxf(size.y, size.z)), GemCut.SIZE, 0.01, "cut %d" % index)


## The shader follows a ray inside the planes of the facets. That is correct only when the
## cut is convex: every corner lies on or behind every plane.
func test_each_cut_is_convex_inside_its_planes() -> void:
	for index: int in GemCut.COUNT:
		var cut: GemCut = GemCut.of(index)
		assert_between(cut.facets.size(), 4, GemCut.MAX_FACETS)
		var worst: float = 0.0
		for corner: Vector3 in cut.mesh.get_faces():
			for plane: Vector4 in cut.facets:
				worst = maxf(worst, Vector3(plane.x, plane.y, plane.z).dot(corner) - plane.w)
		assert_lt(worst, 0.0001, "cut %d has a corner outside a facet plane" % index)


## The jewel's lowest point is LIFT above the marker, whatever the cut.
func test_jewel_hangs_at_lift() -> void:
	for index: int in GemCut.COUNT:
		var jewel: MeshInstance3D = _gem(index).get_node("Jewel")
		assert_almost_eq(jewel.position.y + GemCut.of(index).bottom, Gem.LIFT, 0.001)


## No part of a gem casts a shadow: the light below the gem marks its place.
func test_gem_casts_no_shadow() -> void:
	var gem: Gem = _gem(0)
	var parts: Array[Node] = gem.find_children("*", "GeometryInstance3D", true, false)
	assert_gt(parts.size(), 0)
	for node: Node in parts:
		var part: GeometryInstance3D = node as GeometryInstance3D
		assert_eq(part.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, String(part.name))
	var glow: OmniLight3D = gem.get_node("Glow")
	assert_false(glow.shadow_enabled)


## Returns a gem of cut index in the tree.
func _gem(index: int) -> Gem:
	var gem: Gem = GEM.instantiate()
	gem.cut = index
	add_child_autofree(gem)
	return gem


## Returns the largest distance from the axis of the corners of cut at height, m.
func _width_at(cut: GemCut, height: float) -> float:
	var width: float = 0.0
	for corner: Vector3 in cut.mesh.get_faces():
		if absf(corner.y - height) < 0.0001:
			width = maxf(width, Vector2(corner.x, corner.z).length())
	return width
