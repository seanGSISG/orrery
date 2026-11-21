class_name Settings
extends SaveRecord
## The player's settings (docs/plan.md §2.4, §2.13). Save.settings holds the one instance.
## Change a var, then call Save.write(). To add a setting, add a var with its default here;
## the file keeps it with no other change. The settings ticket (#23) applies them at start.

## Camera shake on landings (FollowCamera.shake_enabled).
var camera_shake: bool = true
## Controller rumble (Rumble.enabled).
var rumble: bool = true
## Radial stick dead zone, 0..1 (InputHub.dead_zone).
var dead_zone: float = 0.15
## Camera turn speed factor (PlayerSource.look_sensitivity).
var look_sensitivity: float = 1.0
## Up on the stick or the mouse looks down (PlayerSource.invert_y).
var invert_y: bool = false
## &"low", &"medium", &"high" or &"ultra" (Graphics.use()).
var graphics_preset: StringName = &"medium"
## Bus volumes, 0..1.
var master_volume: float = 1.0
var music_volume: float = 1.0
var sfx_volume: float = 1.0
var ui_volume: float = 1.0
## Show the ghost of the best run while playing a level.
var ghost: bool = true
