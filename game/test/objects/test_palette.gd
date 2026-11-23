extends GutTest
## Palette: the colourblind setting changes the colours of the gems and the hazards, also of
## the ones that are already in a level.

const GEM: PackedScene = preload("res://objects/gem/gem.tscn")
const BUMPER: PackedScene = preload("res://objects/bumper/bumper.tscn")


func after_each() -> void:
	Palette.use(false)


## Every gem cut and the hazard have another colour in the colourblind palette, and the four
## gem colours stay apart.
func test_palettes_differ() -> void:
	assert_ne(Palette.GEMS, Palette.GEMS_COLOURBLIND)
	assert_ne(Palette.HAZARD, Palette.HAZARD_COLOURBLIND)
	for colours: Array[Color] in [Palette.GEMS, Palette.GEMS_COLOURBLIND]:
		for i: int in colours.size():
			for j: int in range(i + 1, colours.size()):
				assert_ne(colours[i], colours[j])


## gem() gives the colour of the palette that is on, for each cut.
func test_gem_colour_follows_the_mode() -> void:
	for cut: int in GemCut.COUNT:
		assert_eq(Palette.gem(cut), Palette.GEMS[cut])
	Palette.use(true)
	for cut: int in GemCut.COUNT:
		assert_eq(Palette.gem(cut), Palette.GEMS_COLOURBLIND[cut])


## The standard gems have one lightness, as on the style board. The colourblind gems keep the
## order of lightness of their colours: blue, reddish purple, orange, yellow.
func test_gem_lightness_follows_the_mode() -> void:
	for cut: int in GemCut.COUNT:
		assert_eq(Palette.gem_lightness(cut), 1.0)
	Palette.use(true)
	var order: Array[int] = [1, 3, 0, 2]
	for i: int in order.size() - 1:
		var darker: float = Palette.gem_lightness(order[i])
		var lighter: float = Palette.gem_lightness(order[i + 1])
		assert_gt(lighter, darker * 1.3, "cuts %d and %d" % [order[i], order[i + 1]])


## A gem and a bumper in the scene take the new colours at once.
func test_objects_follow_the_switch() -> void:
	var gem: Gem = GEM.instantiate()
	gem.cut = 1
	add_child_autofree(gem)
	var bumper: Bumper = BUMPER.instantiate()
	add_child_autofree(bumper)
	var glow: OmniLight3D = gem.get_node("Glow")
	var jewel: MeshInstance3D = gem.get_node("Jewel")
	var drum: MeshInstance3D = bumper.get_node("Solid/Mesh")
	var look: StandardMaterial3D = drum.material_override
	assert_eq(glow.light_color, Palette.GEMS[1])
	assert_eq(_colour(jewel), Palette.GEMS[1])
	assert_eq(look.albedo_color, Palette.HAZARD)
	Palette.use(true)
	assert_eq(glow.light_color, Palette.GEMS_COLOURBLIND[1])
	assert_eq(_colour(jewel), Palette.GEMS_COLOURBLIND[1])
	var lightness: float = jewel.get_instance_shader_parameter(&"lightness")
	assert_eq(lightness, Palette.gem_lightness(1))
	assert_lt(lightness, 1.0, "the colourblind blue is the darkest gem")
	assert_eq(look.albedo_color, Palette.HAZARD_COLOURBLIND)


## Returns the colour that a gem gave its jewel.
func _colour(jewel: MeshInstance3D) -> Color:
	var colour: Color = jewel.get_instance_shader_parameter(&"colour")
	return colour
