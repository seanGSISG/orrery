class_name HeightMeter
extends GlassPanel
## The Ascent height meter of the HUD: the marble's height in metres over the scale of the
## climb (HeightScale), on a glass panel. Hud puts it on the left edge and calls show_climb()
## each frame of a climb.

## The height in whole metres: "132" and " m".
var height: Readout = Readout.new(UiLook.HUD_GEMS_SIZE, UiLook.HUD_GEMS_SMALL)
## The scale; a test reads nothing of it, the screenshot shows it.
var scale_line: HeightScale = HeightScale.new()


func _init() -> void:
	super()
	var column: VBoxContainer = UiTheme.column(14)
	column.add_child(height)
	column.add_child(scale_line)
	add_child(column)


## Shows the marble at marble_height and the best height, on a climb whose zones start at the
## heights of zones and whose gate is at top. All are m above the climb start.
func show_climb(marble_height: float, best: float, zones: PackedFloat32Array, top: float) -> void:
	height.show_text(HeightText.whole(marble_height), HeightText.unit())
	scale_line.show_climb(marble_height, best, zones, top)
