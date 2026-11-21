class_name Palette
extends RefCounted
## The colours of the gems and the hazards, in one place (docs/plan.md §2.13). Two palettes:
## the standard one, and a colourblind one that the setting Settings.colourblind turns on.
## Gems also differ by shape, so colour is never the only cue.
##
## Both palettes take their hues from the Okabe-Ito colourblind-safe set. The colourblind one
## makes the four gem cuts differ in lightness too: it swaps sky blue and bluish green, which
## players with tritanopia mix up, for a dark blue and a bright yellow. It makes the hazard
## red vermilion, which players with protanopia or deuteranopia see as bright, not as dark as
## the stone round it.
##
## An object that uses these colours joins GROUP and has a method apply_palette(), which reads
## gem() or hazard(); use() calls it on every one after a change.

## The group of the objects that colour themselves from the palette.
const GROUP: StringName = &"palette"
## The colour of each gem cut (Gem.SIDES), standard and colourblind.
const GEMS: Array[Color] = [
	Color(0.90, 0.62, 0.0),  # orange
	Color(0.34, 0.71, 0.91),  # sky blue
	Color(0.0, 0.62, 0.45),  # bluish green
	Color(0.80, 0.47, 0.65),  # reddish purple
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


## Returns the hazard colour of the palette that is on.
static func hazard() -> Color:
	return HAZARD_COLOURBLIND if colourblind else HAZARD
