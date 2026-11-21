extends Node3D
## The entry scene. Give the user argument `--smoke` (after `--`) to print the boot
## marker "ORRERY boot ok" and quit; `just smoke-wine` and CI use it to check that an
## export boots.


## Prints the boot marker and quits when the `--smoke` user argument is present.
func _ready() -> void:
	if "--smoke" in OS.get_cmdline_user_args():
		print("ORRERY boot ok")
		get_tree().quit()
