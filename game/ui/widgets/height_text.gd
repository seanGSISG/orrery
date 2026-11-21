class_name HeightText
extends RefCounted
## Writes the heights of Ascent as text, in whole metres. The metres are cut, not rounded, so
## the text never shows a height that the marble did not reach.


## Returns height as whole metres with the unit: "132 m".
static func metres(height: float) -> String:
	return whole(height) + unit()


## Returns the whole metres of height: "132". A height below the climb start gives "0".
static func whole(height: float) -> String:
	# The small sum hides the float error of a marble that stands at a whole height.
	return str(floori(maxf(height, 0.0) + 0.001))


## Returns the unit as it stands after the number: " m".
static func unit() -> String:
	return " " + TranslationServer.translate(&"UNIT_M")
