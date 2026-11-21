extends "res://main.gd"
## The scene that `just feel` plays (#19): main.gd with a sun, a sky and the TuningOverlay.
## It plays the level of `--level <id>`, else the feel-review course levels/test/feel.py.
## The user argument `--tuning` opens the overlay at the start, for harness screenshots.
## Debug-only: the release exports leave game/debug/ out.

const COURSE: StringName = &"feel"


## Starts main.gd, loads the course when no level was given, and adds the overlay.
func _ready() -> void:
	super()
	if Game.run == null:
		Game.load_level(COURSE)
	var overlay: TuningOverlay = TuningOverlay.new()
	add_child(overlay)
	if "--tuning" in OS.get_cmdline_user_args():
		overlay.open()
