class_name AscentRecord
extends SaveRecord
## The saved Ascent climb (docs/plan.md §2.9). Save.ascent holds the one instance. The Ascent
## mode (game/modes/ascent/ascent.gd) fills these vars and calls Save.write(). The best time
## to the top and the ghost of the best climb are not here: they go through Save.finish() like
## those of any level, under the level id Ascent.ID.

## True when Assist is on: the next start of the climb has a checkpoint at each zone start.
var assist: bool = false
## True when spot_position holds the place to continue from.
var has_spot: bool = false
## Marble centre and velocity at quit, the level clock then, s, the run's tick then, and the
## height above the climb start, m.
var spot_position: Vector3 = Vector3.ZERO
var spot_velocity: Vector3 = Vector3.ZERO
var spot_time: float = 0.0
var spot_tick: int = 0
var spot_height: float = 0.0
## The zone level ids of the climb of the spot, from the bottom, with a comma between them.
## The spot counts only in a climb that starts with these zones.
var spot_zones: String = ""
## The zone index of the last Assist checkpoint at quit; -1 for none.
var spot_checkpoint: int = -1
## AscentFalls.floor_height and low_height at quit, so that a fall goes on as the same fall.
var spot_floor: float = 0.0
var spot_low: float = 0.0
## True when Assist was on at any time in this climb.
var assisted: bool = false
## Stats of the current climb: falls and total metres fallen.
var falls: int = 0
var fallen: float = 0.0
## Best height above the climb start in any climb, m, and the marble centre there. The flag
## stands at this place.
var best_height: float = 0.0
var best_position: Vector3 = Vector3.ZERO
