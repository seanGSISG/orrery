class_name AscentHour
extends Resource
## The time of day at one height of the Ascent climb: where the sun stands and how the sky
## looks. The hours are res://modes/ascent/hours/<name>.tres; AscentSky blends from one to the
## next as the marble climbs. To change the light of the climb, change those files.

## Height above the climb start at which this hour shows in full, m.
@export var height: float = 0.0
## The sun: degrees above the horizon, compass turn in degrees, colour and energy.
@export var elevation: float = 45.0
@export var turn: float = 45.0
@export var sun_color: Color = Color.WHITE
@export var sun_energy: float = 1.0
## The sky: its colour overhead, at the horizon and far below the horizon (the haze under the
## climb), and how bright it is. The sky also lights the shade.
@export var sky_top: Color = Color(0.24, 0.45, 0.82)
@export var sky_horizon: Color = Color(0.7, 0.8, 0.9)
@export var sky_below: Color = Color(0.6, 0.66, 0.74)
@export var sky_energy: float = 1.0
## Environment.tonemap_exposure (docs/design/visual-quality.md: Ascent sets the exposure from
## the height).
@export var exposure: float = 1.0
