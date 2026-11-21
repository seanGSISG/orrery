extends Node3D
## The entry scene. User arguments (after `--`):
## - `--smoke` prints the boot marker "ORRERY boot ok" and quits; `just smoke-wine` and CI use
##   it to check that an export boots.
## - `--level <id>` plays level <id> (see Game.load_level); `just run` uses it.


## Handles the user arguments.
func _ready() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if "--smoke" in args:
		print("ORRERY boot ok")
		get_tree().quit()
		return
	var at: int = args.find("--level")
	if at >= 0 and at + 1 < args.size():
		Game.load_level(StringName(args[at + 1]))
