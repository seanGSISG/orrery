extends Node3D
## Toolchain probe for tools/setup/check.sh. Picks a mode from the user args after `--`:
##   --mode=render --out=<png>  renders a lit cube; fails on a blank frame
##   --mode=joypad              waits up to 15 s for a joypad A press
##   --mode=boot                prints a marker and quits (Windows export under Wine)
## Each mode prints one "PROBE <mode> ok|..." line and quits with 0 on success.


func _ready() -> void:
	var args: Dictionary = {}
	for arg: String in OS.get_cmdline_user_args():
		var kv: PackedStringArray = arg.trim_prefix("--").split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	match str(args.get("mode", "boot")):
		"render":
			await _render(str(args.get("out", "user://probe.png")))
		"joypad":
			await _joypad()
		_:
			print("PROBE boot ok")
			get_tree().quit(0)


func _render(out: String) -> void:
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.08, 0.1, 0.18)
	var world := WorldEnvironment.new()
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50.0, 30.0, 0.0)
	add_child(sun)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.95, 0.65, 0.2)
	var cube := MeshInstance3D.new()
	cube.mesh = BoxMesh.new()
	cube.material_override = material
	cube.rotation_degrees = Vector3(20.0, 35.0, 0.0)
	add_child(cube)
	var camera := Camera3D.new()
	camera.position = Vector3(0.0, 0.0, 3.0)
	add_child(camera)
	camera.make_current()
	for i: int in 10:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image: Image = get_viewport().get_texture().get_image()
	image.save_png(out)
	var low: float = 1.0
	var high: float = 0.0
	for y: int in range(0, image.get_height(), 8):
		for x: int in range(0, image.get_width(), 8):
			var lum: float = image.get_pixel(x, y).get_luminance()
			low = minf(low, lum)
			high = maxf(high, lum)
	var passed: bool = high - low > 0.2
	print(
		(
			"PROBE render %s contrast=%.2f size=%dx%d gpu=%s"
			% [
				"ok" if passed else "blank",
				high - low,
				image.get_width(),
				image.get_height(),
				RenderingServer.get_video_adapter_name()
			]
		)
	)
	get_tree().quit(0 if passed else 1)


func _joypad() -> void:
	var deadline: int = Time.get_ticks_msec() + 15000
	var seen: String = "none"
	while Time.get_ticks_msec() < deadline:
		for id: int in Input.get_connected_joypads():
			seen = Input.get_joy_name(id)
			if Input.is_joy_button_pressed(id, JOY_BUTTON_A):
				print("PROBE joypad ok name=%s" % seen)
				get_tree().quit(0)
				return
		await get_tree().process_frame
	print("PROBE joypad missing seen=%s" % seen)
	get_tree().quit(1)
