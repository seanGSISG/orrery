extends Node
## One performance run (docs/design/visual-quality.md §8): one level, one graphics preset, at
## the window's resolution. tools/perf/perf.py starts it in gamescope, once per preset:
##     godot --path game --resolution 1920x1080 res://test/perf/perf_run.tscn --
##         --level fixture --preset medium --out build/perf/fixture-medium-1080.json
##         [--motion build/gallery/fixture/motion]
## It flies a camera along the level's shots, then once fast around the marble. It measures
## the GPU time of each frame with RenderingServer.viewport_get_measured_render_time_gpu and
## the peak VRAM with Performance.RENDER_VIDEO_MEM_USED. With --motion it then saves two orbit
## frames 1/60 s apart as motion-1.png and motion-2.png (rubric check 3). Last it writes the
## report to --out as JSON and quits; a failed run writes no report and quits with 1.

## The path visits these shots in this order, then the level's other shots.
const SHOTS: Array[String] = ["overview", "start", "finish", "egg"]
## The fewest frames before the measurement starts; the warm-up flies the whole path at least
## once, for shader compilation and the first shadow updates.
const WARMUP: int = 120
## Frames from one shot to the next; the path moves 1/60 s per frame.
const LEG: int = 120
## Frames for one turn around the marble: one turn in 1 s.
const ORBIT: int = 60
const ORBIT_RADIUS: float = 2.0
const ORBIT_HEIGHT: float = 0.8

var _camera: Camera3D = Camera3D.new()
var _poses: Array[Transform3D] = []
var _marble: Vector3


func _ready() -> void:
	_run.call_deferred()


## Runs the measurement and quits with 0, or with 1 on bad arguments or a failed save.
func _run() -> void:
	var args: Dictionary[String, String] = _args()
	var level: String = args.get("level", "")
	var out: String = args.get("out", "")
	var preset: String = args.get("preset", "medium")
	var motion: String = args.get("motion", "")
	if level == "" or out == "" or Game.load_level(StringName(level)) == null:
		printerr("perf_run: needs --level <a level that loads> and --out <json>")
		get_tree().quit(1)
		return
	# The marble stays on the start pad, so every preset sees the same frames.
	Game.run.auto_step = false
	if not Graphics.use(preset):
		get_tree().quit(1)
		return
	_marble = Game.run.marble.global_position
	_poses = _shot_poses(Game.run.level)
	Game.run.add_child(_camera)
	_camera.make_current()
	var viewport: RID = get_viewport().get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(viewport, true)
	var frames: int = maxi(_poses.size() - 1, 0) * LEG + ORBIT
	for frame: int in maxi(WARMUP, frames):
		await _draw(_pose(frame % frames))
	var times: PackedFloat64Array = []
	var vram: float = 0.0
	for frame: int in frames:
		await _draw(_pose(frame))
		times.append(RenderingServer.viewport_get_measured_render_time_gpu(viewport))
		vram = maxf(vram, Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED))
	if motion != "" and not await _save_motion(motion, frames - ORBIT):
		get_tree().quit(1)
		return
	# The size of the drawn image is the render size. The stretch mode scales the 2D sizes:
	# get_visible_rect() and ViewportTexture.get_size() do not give it.
	var size: Vector2i = get_viewport().get_texture().get_image().get_size()
	var report: Dictionary = {
		"level": level,
		"preset": Graphics.current,
		"width": size.x,
		"height": size.y,
		"adapter": RenderingServer.get_video_adapter_name(),
		"frames": times.size(),
		"gpu_ms": _stats(times),
		"vram_mb": vram / 1048576.0,
	}
	DirAccess.make_dir_recursive_absolute(out.get_base_dir())
	var file: FileAccess = FileAccess.open(out, FileAccess.WRITE)
	if file == null:
		printerr("perf_run: cannot write %s" % out)
		get_tree().quit(1)
		return
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	get_tree().quit()


## Returns the user arguments `--key value` as a dictionary.
func _args() -> Dictionary[String, String]:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var out: Dictionary[String, String] = {}
	for i: int in range(0, args.size() - 1):
		if args[i].begins_with("--"):
			out[args[i].trim_prefix("--")] = args[i + 1]
	return out


## Returns the global transforms of the level's Camera3D shots, the SHOTS first.
static func _shot_poses(level: Node) -> Array[Transform3D]:
	var cameras: Array[Node] = level.find_children("*", "Camera3D", true, false)
	cameras.sort_custom(
		func(a: Node, b: Node) -> bool: return _rank(String(a.name)) < _rank(String(b.name))
	)
	var poses: Array[Transform3D] = []
	for camera: Node in cameras:
		poses.append((camera as Camera3D).global_transform)
	return poses


## Sorts the SHOTS by their place in SHOTS and the other shots after them by name.
static func _rank(shot: String) -> String:
	var at: int = SHOTS.find(shot)
	return "%d" % at if at >= 0 else "9" + shot


## The camera pose at path frame: the legs between the shots, then the orbit.
func _pose(frame: int) -> Transform3D:
	var leg: int = floori(float(frame) / LEG)
	if leg < _poses.size() - 1:
		var weight: float = smoothstep(0.0, 1.0, float(frame % LEG) / LEG)
		return _poses[leg].interpolate_with(_poses[leg + 1], weight)
	var turn: float = TAU * float(frame - maxi(_poses.size() - 1, 0) * LEG) / ORBIT
	var eye: Vector3 = _marble + Vector3(cos(turn), 0.0, sin(turn)) * ORBIT_RADIUS
	eye.y += ORBIT_HEIGHT
	return Transform3D.IDENTITY.translated(eye).looking_at(_marble)


## Moves the camera to pose and waits until the frame is drawn.
func _draw(pose: Transform3D) -> void:
	_camera.global_transform = pose
	await get_tree().process_frame
	await RenderingServer.frame_post_draw


## Flies the orbit again from its first frame orbit_start, and saves two frames next to each
## other, half a turn in, so the upscaler has history. Returns false when a save fails.
func _save_motion(dir: String, orbit_start: int) -> bool:
	DirAccess.make_dir_recursive_absolute(dir)
	var half: int = roundi(ORBIT * 0.5)
	for frame: int in half:
		await _draw(_pose(orbit_start + frame))
	for i: int in 2:
		await _draw(_pose(orbit_start + half + i))
		var image: Image = get_viewport().get_texture().get_image()
		var path: String = dir.path_join("motion-%d.png" % (i + 1))
		var error: Error = image.save_png(path)
		if error != OK:
			printerr("perf_run: cannot save %s (%s)" % [path, error_string(error)])
			return false
	return true


## Returns the mean, median and 99th percentile (nearest rank) of times, in ms.
static func _stats(times: PackedFloat64Array) -> Dictionary:
	var sorted: PackedFloat64Array = times.duplicate()
	sorted.sort()
	var total: float = 0.0
	for time: float in sorted:
		total += time
	var count: int = sorted.size()
	return {
		"mean": total / maxi(count, 1),
		"p50": sorted[floori((count - 1) * 0.5)] if count > 0 else 0.0,
		"p99": sorted[ceili(count * 0.99) - 1] if count > 0 else 0.0,
	}
