class_name AscentRecord
extends SaveRecord
## The saved Ascent climb (docs/plan.md §2.9). Save.ascent holds the one instance. The Ascent
## ticket (#27) fills these vars and calls Save.write(). The ghost of the best climb goes
## through Save.finish() like the ghost of any level.

## True when spot_position holds the place to continue from.
var has_spot: bool = false
## Marble centre and velocity at quit, and the clock then, s.
var spot_position: Vector3 = Vector3.ZERO
var spot_velocity: Vector3 = Vector3.ZERO
var spot_time: float = 0.0
## True when Assist was on in this climb.
var assisted: bool = false
## Stats of the current climb: falls and total metres fallen.
var falls: int = 0
var fallen: float = 0.0
## Best height above the climb start, m, and the best time to the top, s (negative: none).
var best_height: float = 0.0
var best_time: float = -1.0
