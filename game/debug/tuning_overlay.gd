class_name TuningOverlay
extends CanvasLayer
## Debug-only live tuning panel for the feel review (#19). game/debug/feel.gd adds it; the
## release exports leave game/debug/ out. It lists the marble feel values (MarbleTuning),
## the FollowCamera settings and the input settings, and shows the marble speed. Changes
## apply at once; Save writes the changed values into the files that hold their defaults
## (TuningSetting.save()).
##
## Controller: hold LB and press Y to open or close. D-pad up and down pick a value, left
## and right change it (hold to repeat), RB saves. Keyboard: F1, the arrow keys and F5.
## Not listed: radius, mass and the solver limits (not feel values), and the camera
## clearance (the camera reads it only once, when it starts).

const MARBLE_FILE: String = "res://core/marble_tuning.tres"
const CAMERA_FILE: String = "res://core/camera/follow_camera.gd"
const HUB_FILE: String = "res://core/input/input_hub.gd"
const PLAYER_FILE: String = "res://core/input/player_source.gd"
const RUMBLE_FILE: String = "res://core/input/rumble.gd"
## A held left or right repeats after this delay, then at this interval, s.
const REPEAT_DELAY: float = 0.35
const REPEAT_EVERY: float = 0.06
const PICKED: Color = Color(1.0, 0.8, 0.25)
const HELP: String = "D-pad: pick, change    RB: save    LB+Y: close"

const PAD: Dictionary[JoyButton, StringName] = {
	JOY_BUTTON_DPAD_UP: &"up",
	JOY_BUTTON_DPAD_DOWN: &"down",
	JOY_BUTTON_DPAD_LEFT: &"left",
	JOY_BUTTON_DPAD_RIGHT: &"right",
	JOY_BUTTON_RIGHT_SHOULDER: &"save",
}
const KEYS: Dictionary[Key, StringName] = {
	KEY_F1: &"toggle",
	KEY_UP: &"up",
	KEY_DOWN: &"down",
	KEY_LEFT: &"left",
	KEY_RIGHT: &"right",
	KEY_F5: &"save",
}

## The values in the panel, in display order. Made at the first open.
var settings: Array[TuningSetting] = []

## The run whose speed the panel shows.
var _run: LevelRun
var _picked: int = 0
## The held change direction (-1 or 1), 0 when none is held, and how long it is held, s.
var _held: int = 0
var _held_for: float = 0.0
var _grid: GridContainer = GridContainer.new()
## Scrolls the grid when the window is too short for every row.
var _scroll: ScrollContainer = ScrollContainer.new()
var _names: Array[Label] = []
var _values: Array[Label] = []
var _speed: Label = Label.new()
var _status: Label = Label.new()


## Builds the hidden panel.
func _ready() -> void:
	layer = 10
	visible = false
	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(16, 16)
	panel.modulate = Color(1, 1, 1, 0.92)
	add_child(panel)
	var column: VBoxContainer = VBoxContainer.new()
	panel.add_child(column)
	column.add_child(_speed)
	_grid.columns = 2
	_grid.add_theme_constant_override(&"h_separation", 24)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.add_child(_grid)
	column.add_child(_scroll)
	column.add_child(_status)
	_status.text = HELP
	get_viewport().size_changed.connect(_refresh)


## Shows the panel. The first open builds it for Game.run and the current camera.
func open() -> void:
	if settings.is_empty():
		build(Game.run, get_viewport().get_camera_3d() as FollowCamera)
	visible = true
	_refresh()


## Opens or closes the panel.
func toggle() -> void:
	_held = 0
	if visible:
		visible = false
	else:
		open()


## Picks the setting at index and changes it by direction steps; the controls call it.
func change(index: int, direction: int) -> void:
	_picked = index
	settings[index].adjust(direction)
	_refresh()


## Saves the changed values and shows the result.
func save() -> void:
	var count: int = settings.filter(
		func(s: TuningSetting) -> bool: return s.file != "" and s.changed()
	).size()
	var problems: PackedStringArray = TuningSetting.save(settings)
	var result: String = "Saved %d values" % count if problems.is_empty() else "\n".join(problems)
	_status.text = result + "\n" + HELP
	_refresh()


## Handles the controls; it takes the events it uses, so the game does not see them.
func _input(event: InputEvent) -> void:
	var command: StringName = _command(event)
	if command == &"" or event.is_echo() or (command != &"toggle" and not visible):
		return
	get_viewport().set_input_as_handled()
	if not event.is_pressed():
		if command == &"left" or command == &"right":
			_held = 0
	elif command == &"toggle":
		toggle()
	elif command == &"up" or command == &"down":
		_held = 0
		_picked = wrapi(_picked + (1 if command == &"down" else -1), 0, settings.size())
		_refresh()
	elif command == &"left" or command == &"right":
		var direction: int = 1 if command == &"right" else -1
		# A held bool does not repeat, so it does not flip on and off.
		_held = 0 if settings[_picked].value() is bool else direction
		_held_for = 0.0
		change(_picked, direction)
	elif command == &"save":
		save()


## Repeats a held change and updates the speed.
func _process(delta: float) -> void:
	if not visible:
		return
	if _held != 0:
		_held_for += delta
		if _held_for >= REPEAT_DELAY:
			_held_for -= REPEAT_EVERY
			change(_picked, _held)
	if _run != null:
		_speed.text = "Speed %.1f m/s" % _run.state.velocity.length()


## Returns the command of a pad button or key event, or &"". Y is the toggle only while LB
## is held.
func _command(event: InputEvent) -> StringName:
	var button: InputEventJoypadButton = event as InputEventJoypadButton
	var command: StringName = &""
	if button != null and button.button_index == JOY_BUTTON_Y:
		if Input.is_joy_button_pressed(button.device, JOY_BUTTON_LEFT_SHOULDER):
			command = &"toggle"
	elif button != null:
		command = PAD.get(button.button_index, &"")
	var key: InputEventKey = event as InputEventKey
	if key != null:
		command = KEYS.get(key.keycode, &"")
	return command


## Makes the settings and their rows: the marble of run and camera (each may be null),
## and the input settings. Call it once.
func build(run: LevelRun, camera: FollowCamera) -> void:
	_run = run
	if run != null:
		_heading("Marble")
		var tuning: MarbleTuning = run.marble.tuning
		_add(tuning, &"gravity", 0.5, 5.0, 40.0, MARBLE_FILE)
		_add(tuning, &"max_roll_speed", 0.5, 5.0, 30.0, MARBLE_FILE)
		_add(tuning, &"angular_acceleration", 5.0, 10.0, 200.0, MARBLE_FILE)
		_add(tuning, &"braking_acceleration", 5.0, 0.0, 150.0, MARBLE_FILE)
		_add(tuning, &"air_acceleration", 0.5, 0.0, 20.0, MARBLE_FILE)
		_add(tuning, &"jump_impulse", 0.25, 2.0, 15.0, MARBLE_FILE)
		_add(tuning, &"floor_min_up", 0.05, 0.0, 1.0, MARBLE_FILE)
		_add(tuning, &"static_friction", 0.05, 0.0, 3.0, MARBLE_FILE)
		_add(tuning, &"kinetic_friction", 0.05, 0.0, 3.0, MARBLE_FILE)
		_add(tuning, &"bounce_friction", 0.05, 0.0, 1.0, MARBLE_FILE)
		_add(tuning, &"restitution", 0.05, 0.0, 1.5, MARBLE_FILE)
		_add(tuning, &"slide_threshold", 0.05, 0.0, 1.0, MARBLE_FILE)
		_add(tuning, &"min_bounce_speed", 0.05, 0.0, 3.0, MARBLE_FILE)
		_add(tuning, &"hard_impact_speed", 1.0, 1.0, 50.0, MARBLE_FILE)
	if camera != null:
		_heading("Camera")
		_add(camera, &"distance", 0.1, 1.0, 8.0, CAMERA_FILE)
		_add(camera, &"min_distance", 0.05, 0.2, 3.0, CAMERA_FILE)
		_add(camera, &"up_rate", 0.5, 0.5, 30.0, CAMERA_FILE)
		_add(camera, &"return_rate", 0.5, 0.5, 30.0, CAMERA_FILE)
		_add(camera, &"hard_landing", 0.05, 0.0, 1.0, CAMERA_FILE)
		_add(camera, &"shake_angle", 0.005, 0.0, 0.2, CAMERA_FILE)
		_add(camera, &"shake_decay", 0.25, 0.25, 10.0, CAMERA_FILE)
		_add(load(CAMERA_FILE), &"shake_enabled", 0.0, 0.0, 0.0, CAMERA_FILE)
		_add(camera, &"fov", 1.0, 50.0, 100.0, "", "fov (not saved)")
	_heading("Input")
	_add(InputHub, &"dead_zone", 0.01, 0.0, 0.5, HUB_FILE)
	_add(load(PLAYER_FILE), &"look_sensitivity", 0.05, 0.1, 3.0, PLAYER_FILE)
	_add(load(PLAYER_FILE), &"invert_y", 0.0, 0.0, 0.0, PLAYER_FILE)
	_add(load(RUMBLE_FILE), &"enabled", 0.0, 0.0, 0.0, RUMBLE_FILE, "rumble")


## Adds a setting and its row. title defaults to the property name.
func _add(
	on: Object,
	key: StringName,
	step: float,
	low: float,
	high: float,
	file: String,
	title: String = "",
) -> void:
	var setting: TuningSetting = TuningSetting.new(
		title if title != "" else String(key), on, key, step, Vector2(low, high), file
	)
	settings.append(setting)
	_names.append(_label(setting.label))
	_values.append(_label(""))


## Adds a row with a group name and no value.
func _heading(text: String) -> void:
	_label(text).add_theme_color_override(&"font_color", Color(0.6, 0.75, 1.0))
	_label("")


## Adds a label to the grid and returns it.
func _label(text: String) -> Label:
	var label: Label = Label.new()
	label.text = text
	_grid.add_child(label)
	return label


## Shows each value, marks unsaved ones with *, colours the picked row, fits the rows to
## the window height and scrolls the picked row into view.
func _refresh() -> void:
	var room: float = get_viewport().get_visible_rect().size.y - 160.0
	_scroll.custom_minimum_size.y = minf(_grid.get_combined_minimum_size().y, room)
	if not _names.is_empty():
		_scroll.ensure_control_visible.call_deferred(_names[_picked])
	for i: int in settings.size():
		var setting: TuningSetting = settings[i]
		_values[i].text = setting.text() + (" *" if setting.changed() else "")
		var colour: Color = PICKED if i == _picked else Color.WHITE
		_names[i].modulate = colour
		_values[i].modulate = colour
