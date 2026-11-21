extends Node3D
## The entry scene. Its child Ui (ui/ui.gd) shows the HUD and the menus: the title when no
## level loads here. User arguments (after `--`):
## - `--smoke` prints the boot marker "ORRERY boot ok" and quits; `just smoke-wine` and CI use
##   it to check that an export boots.
## - `--level <id>` plays level <id> (see Game.load_level); `just run` uses it.
## - `--harness-port=<port>` starts the debug harness (harness/harness.gd) on that port. Only
##   debug builds have it; the release exports leave game/harness/ out.

const HARNESS: String = "res://harness/harness.gd"


## Handles the user arguments.
func _ready() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if "--smoke" in args:
		print("ORRERY boot ok")
		get_tree().quit()
		return
	if OS.is_debug_build() and ResourceLoader.exists(HARNESS):
		if Array(args).any(func(arg: String) -> bool: return arg.begins_with("--harness-port=")):
			var harness: Node = Node.new()
			harness.name = &"Harness"
			harness.set_script(load(HARNESS))
			get_tree().root.add_child.call_deferred(harness)
	var at: int = args.find("--level")
	if at >= 0 and at + 1 < args.size():
		Game.load_level(StringName(args[at + 1]))
