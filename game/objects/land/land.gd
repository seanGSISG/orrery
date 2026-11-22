class_name Land
extends LevelObject
## The `land` marker: flat open country round a level, out to the far haze. Put the marker in
## the middle of the town, a few centimetres below the town's ground. It is a square of
## 12 km under land.gdshader: grass at its true size, and fields with hedges between them
## past the meadow round the marker. It casts no shadow and stays out of the lightmap. The
## sky's distance fog (SkyPreset.fog_density) fades it into the horizon.
##
## The land is past the play space, but it is solid ground: a world boundary at the grass holds
## a marble that leaves the town, and the touch puts the marble out of bounds. So the marble
## never falls through the grass, and it is never stranded in the fields.


func on_touch(run: LevelRun, _contact: Contact) -> void:
	run.rules.leave_bounds()
