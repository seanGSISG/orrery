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


## A gem and a bumper in the scene take the new colours at once.
func test_objects_follow_the_switch() -> void:
	var gem: Gem = GEM.instantiate()
	gem.cut = 1
	add_child_autofree(gem)
	var bumper: Bumper = BUMPER.instantiate()
	add_child_autofree(bumper)
	var glow: OmniLight3D = gem.get_node("Glow")
	var drum: MeshInstance3D = bumper.get_node("Solid/Mesh")
	var look: StandardMaterial3D = drum.material_override
	assert_eq(glow.light_color, Palette.GEMS[1])
	assert_eq(look.albedo_color, Palette.HAZARD)
	Palette.use(true)
	assert_eq(glow.light_color, Palette.GEMS_COLOURBLIND[1])
	assert_eq(look.albedo_color, Palette.HAZARD_COLOURBLIND)
