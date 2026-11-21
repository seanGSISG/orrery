extends RunTest
## The live tuning overlay of the feel review (#19): TuningSetting writes a changed value
## into the line that holds its default and leaves the rest of the file alone, and the
## overlay changes live values from the controller. The tests save into copies in user://,
## never into the real files.

const COURSE: String = "res://levels/built/feel.glb"
const TUNING_FILE: String = "res://core/marble_tuning.tres"
const COPY: String = "user://test_tuning/marble_tuning.tres"
const SCRIPT_COPY: String = "user://test_tuning/defaults.gd"
## Device id of the test events; far above the ids that real pads get.
const PAD: int = 7


## Holds the fields of a .gd defaults file, as a camera or the input scripts do.
class Defaults extends RefCounted:
	var distance: float = 2.5
	var invert_y: bool = false


func before_each() -> void:
	DirAccess.make_dir_recursive_absolute(COPY.get_base_dir())
	DirAccess.copy_absolute(TUNING_FILE, COPY)


func after_each() -> void:
	for button: JoyButton in [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_Y, JOY_BUTTON_DPAD_RIGHT]:
		_button(button, false)
	# A key press makes the keyboard the active device again, as before the test.
	var key: InputEventKey = InputEventKey.new()
	key.keycode = KEY_W
	key.pressed = true
	Input.parse_input_event(key)
	key = key.duplicate() as InputEventKey
	key.pressed = false
	Input.parse_input_event(key)
	Input.flush_buffered_events()


## A saved .tres value loads back, and only its line changes.
func test_save_round_trips_a_tuning_value() -> void:
	var before: String = FileAccess.get_file_as_string(COPY)
	var tuning: MarbleTuning = _load_copy()
	var start: float = tuning.gravity
	var gravity: TuningSetting = TuningSetting.new(
		"gravity", tuning, &"gravity", 0.5, Vector2(5, 40), COPY
	)
	gravity.adjust(1)
	gravity.adjust(1)
	assert_true(gravity.changed())
	assert_eq(TuningSetting.save([gravity]), PackedStringArray())
	assert_false(gravity.changed(), "saved")
	var loaded: float = _load_copy().gravity
	assert_almost_eq(loaded, start + 1.0, 0.0001)
	var after: String = FileAccess.get_file_as_string(COPY)
	var line: String = "gravity = %s\n"
	var expected: String = before.replace(line % _plain(start), line % _plain(start + 1.0))
	assert_eq(after, expected, "only the gravity line changes")


## A saved .gd default changes only the value of its declaration, for floats and bools.
func test_save_rewrites_script_defaults() -> void:
	var source: String = "@export var distance: float = 2.5\nstatic var invert_y: bool = false\n"
	_write(SCRIPT_COPY, source)
	var holder: Defaults = Defaults.new()
	var distance: TuningSetting = TuningSetting.new(
		"distance", holder, &"distance", 0.1, Vector2(1, 8), SCRIPT_COPY
	)
	var invert: TuningSetting = TuningSetting.new(
		"invert_y", holder, &"invert_y", 0.0, Vector2.ZERO, SCRIPT_COPY
	)
	distance.adjust(-1)
	invert.adjust(1)
	assert_eq(TuningSetting.save([distance, invert]), PackedStringArray())
	var expected: String = "@export var distance: float = 2.4\nstatic var invert_y: bool = true\n"
	assert_eq(FileAccess.get_file_as_string(SCRIPT_COPY), expected)


## A setting whose line is missing is not saved, and the save says why.
func test_save_reports_a_missing_line() -> void:
	_write(SCRIPT_COPY, "var other: float = 1.0\n")
	var holder: Defaults = Defaults.new()
	var distance: TuningSetting = TuningSetting.new(
		"distance", holder, &"distance", 0.1, Vector2(1, 8), SCRIPT_COPY
	)
	distance.adjust(1)
	assert_eq(TuningSetting.save([distance]).size(), 1)
	assert_true(distance.changed(), "still unsaved")


## Values stay within their limits and at the precision of their step.
func test_adjust_clamps_and_rounds() -> void:
	var holder: Defaults = Defaults.new()
	var distance: TuningSetting = TuningSetting.new(
		"distance", holder, &"distance", 0.1, Vector2(2, 2.7)
	)
	for _i: int in 5:
		distance.adjust(1)
	assert_eq(holder.distance, 2.7)
	distance.adjust(-1)
	assert_eq(distance.text(), "2.6")


## The course builds and loads: a checkpoint for each leg and one before each of the 8 and
## 10 m gaps, a moving platform, a turning gear and three bumpers. Rolling forward from the
## start on the runway reaches the top speed and stays on the ground.
func test_course_loads_and_the_runway_reaches_top_speed() -> void:
	if not ResourceLoader.exists(COURSE):
		fail_test("%s is missing: run `just build-levels`" % COURSE)
		return
	start_run(load(COURSE) as PackedScene)
	var types: Array[String] = []
	for object: LevelObject in run.objects:
		var script: Script = object.get_script()
		types.append(script.get_global_name())
	assert_eq(types.count("Checkpoint"), 6)
	assert_eq(types.count("MovingPlatform"), 1)
	assert_eq(types.count("TurningGear"), 1)
	assert_eq(types.count("Bumper"), 3)
	hold(rolling(Vector2(0, 1)), 3.0)
	assert_true(run.state.on_ground)
	assert_eq(run.state.status, &"playing")
	assert_almost_eq(run.state.velocity.length(), run.marble.tuning.max_roll_speed, 0.3)


## The overlay lists the groups, LB+Y opens it, Y alone does not, and the d-pad changes
## the picked value live.
func test_controller_opens_the_overlay_and_changes_a_value() -> void:
	if not ResourceLoader.exists(COURSE):
		fail_test("%s is missing: run `just build-levels`" % COURSE)
		return
	start_run(load(COURSE) as PackedScene)
	run.marble.tuning = run.marble.tuning.duplicate() as MarbleTuning
	var overlay: TuningOverlay = TuningOverlay.new()
	add_child_autofree(overlay)
	overlay.build(run, null)
	var labels: Array[String] = []
	for setting: TuningSetting in overlay.settings:
		labels.append(setting.label)
	assert_has(labels, "gravity")
	assert_has(labels, "dead_zone")
	assert_does_not_have(labels, "distance", "no camera rows without a camera")
	_button(JOY_BUTTON_Y, true)
	_button(JOY_BUTTON_Y, false)
	assert_false(overlay.visible, "Y alone")
	_button(JOY_BUTTON_LEFT_SHOULDER, true)
	_button(JOY_BUTTON_Y, true)
	assert_true(overlay.visible, "LB+Y")
	var start: float = run.marble.tuning.gravity
	_button(JOY_BUTTON_DPAD_RIGHT, true)
	assert_almost_eq(run.marble.tuning.gravity, start + 0.5, 0.0001)


## Every overlay value has a file and a default line in it, so Save can write each one.
func test_every_value_has_a_line_to_save() -> void:
	start_run(preload("res://test/levels/flat.tscn"))
	var camera: FollowCamera = FollowCamera.new()
	run.add_child(camera)
	var overlay: TuningOverlay = TuningOverlay.new()
	add_child_autofree(overlay)
	overlay.build(run, camera)
	var labels: Array[String] = []
	for setting: TuningSetting in overlay.settings:
		labels.append(setting.label)
		assert_ne(setting.file, "", "%s has no file" % setting.label)
		var source: String = FileAccess.get_file_as_string(setting.file)
		assert_ne(setting._rewrite(source), "", "%s has no line in %s" % [setting.label, setting.file])
	assert_has(labels, "fov")
	assert_has(labels, "clearance")


## Returns a fresh load of the tuning copy.
func _load_copy() -> MarbleTuning:
	return ResourceLoader.load(COPY, "", ResourceLoader.CACHE_MODE_IGNORE) as MarbleTuning


## Returns value as the .tres file writes it.
func _plain(value: float) -> String:
	var text: String = String.num(value, 4)
	return text if text.contains(".") else text + ".0"


## Writes text to path.
func _write(path: String, text: String) -> void:
	var out: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	out.store_string(text)
	out.close()


## Presses or releases a pad button as a real pad does.
func _button(button: JoyButton, pressed: bool) -> void:
	var event: InputEventJoypadButton = InputEventJoypadButton.new()
	event.device = PAD
	event.button_index = button
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()
