class_name Palette
extends RefCounted
## The colours of the gems and the hazards, in one place (docs/plan.md §2.13). Two palettes:
## the standard one, and a colourblind one that the setting Settings.colourblind turns on.
## Gems also differ by shape, so colour is never the only cue.
##
## The standard gems have the colours of the style board (docs/style/README.md): amber, deep
## blue and magenta, which are deep tones of the orange, blue and reddish purple of the
## Okabe-Ito colourblind-safe set. The board has three colours and the game has four cuts, so
## the fourth is emerald green: a deep tone of the bluish green of the same set. All four have
## one lightness (gem_lightness() is 1), as on the board.
##
## The colourblind gems are colours of the Okabe-Ito set itself. A yellow takes the place of
## the green, because players with tritanopia mix up blue and green. The four also differ in
## lightness (gem_lightness()): blue is the darkest, then reddish purple, orange and yellow.
## The colourblind hazard is vermilion, which players with protanopia or deuteranopia see as
## bright, not as dark as the stone round it.
##
## An object that uses these colours joins GROUP and has a method apply_palette(), which reads
## gem(), gem_lightness() or hazard(); use() calls it on every one after a change.

## The group of the objects that colour themselves from the palette.
const GROUP: StringName = &"palette"
## The colour of each gem cut (GemCut), standard and colourblind.
const GEMS: Array[Color] = [
	Color(0.91, 0.58, 0.0),  # amber
	Color(0.10, 0.35, 0.77),  # deep blue
	Color(0.0, 0.60, 0.35),  # emerald green
	Color(0.80, 0.15, 0.57),  # magenta
]
const GEMS_COLOURBLIND: Array[Color] = [
	Color(0.90, 0.62, 0.0),  # orange
	Color(0.0, 0.45, 0.70),  # blue
	Color(0.94, 0.89, 0.26),  # yellow
	Color(0.80, 0.47, 0.65),  # reddish purple
]
## The colour of an object that pushes or hurts the marble (Bumper).
const HAZARD: Color = Color(0.72, 0.2, 0.14)  # red
const HAZARD_COLOURBLIND: Color = Color(0.84, 0.37, 0.0)  # vermilion

## True while the colourblind palette is on. Change it with use().
static var colourblind: bool = false


## Turns the colourblind palette on or off, and colours every object of GROUP again.
static func use(on: bool) -> void:
	colourblind = on
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	tree.call_group(GROUP, &"apply_palette")


## Returns the colour of gem cut (0 to 3) in the palette that is on.
static func gem(cut: int) -> Color:
	var colours: Array[Color] = GEMS_COLOURBLIND if colourblind else GEMS
	return colours[posmod(cut, colours.size())]


## Returns how light gem cut (0 to 3) is against the other gems of the palette that is on. The
## standard gems all have one lightness, 1.0, as on the style board. The colourblind gems
## keep the steps of lightness of their colours: the luminance of the cut's colour in linear
## light, divided by the mean of the four. Gem gives it to the jewel's shader.
static func gem_lightness(cut: int) -> float:
	if not colourblind:
		return 1.0
	var total: float = 0.0
	for colour: Color in GEMS_COLOURBLIND:
		total += _luminance(colour)
	return _luminance(gem(cut)) * GEMS_COLOURBLIND.size() / total


## Returns the hazard colour of the palette that is on.
static func hazard() -> Color:
	return HAZARD_COLOURBLIND if colourblind else HAZARD


## Returns the relative luminance of colour in linear light (Rec. 709 weights).
static func _luminance(colour: Color) -> float:
	var linear: Color = colour.srgb_to_linear()
	return 0.2126 * linear.r + 0.7152 * linear.g + 0.0722 * linear.b
