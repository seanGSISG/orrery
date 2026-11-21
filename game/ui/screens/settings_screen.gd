class_name SettingsScreen
extends Screen
## The settings screen (docs/plan.md §2.4, §2.13), in the look of the C chart mockup
## (docs/ui-mockups/c-chart/settings.html). Five tabs: graphics, display, audio, controls and
## accessibility. tab_prev and tab_next (LB and RB, Q and E) change the tab; the D-pad, the
## left stick and the arrow keys move between the rows and change a value (OptionRow); A or
## Enter on a button row binds a new button (BindRow). settings_defaults (Y or Backspace)
## puts the settings of the tab back to their defaults. Back and ui_cancel return to the
## screen that opened it.
##
## Each change goes through Save.change_settings(), so it applies at once and is saved.

## The text keys of the tabs, in order.
const TABS: Array[String] = [
	"SETTINGS_GRAPHICS",
	"SETTINGS_DISPLAY",
	"SETTINGS_AUDIO",
	"SETTINGS_CONTROLS",
	"SETTINGS_ACCESSIBILITY",
]
## Window sizes that the resolution row offers, where they fit on the screen: 16:9, the
## common laptop size, and ultrawide (21:9 and 32:9).
const RESOLUTIONS: Array[Vector2i] = [
	Vector2i(1280, 720),
	Vector2i(1366, 768),
	Vector2i(1600, 900),
	Vector2i(1920, 1080),
	Vector2i(2560, 1080),
	Vector2i(2560, 1440),
	Vector2i(3440, 1440),
	Vector2i(3840, 1600),
	Vector2i(3840, 2160),
	Vector2i(5120, 1440),
	Vector2i(5120, 2160),
]
## Frame caps; 0 is uncapped.
const FRAME_CAPS: Array[int] = [30, 60, 90, 120, 144, 165, 240, 0]
## The values and texts of an on/off row.
const SWITCH: Array[bool] = [false, true]
const OFF_ON: Array[String] = ["SETTINGS_OFF", "SETTINGS_ON"]

## The screen that Back returns to; Ui sets it to the screen that opened the settings.
var return_to: StringName = &"title"
## The rows of the tab that shows.
var content: VBoxContainer = UiTheme.column(0)
var tabs: SettingsTabs = SettingsTabs.new(TABS)
## The index of the tab that shows.
var tab: int = 0

var _scroll: ScrollContainer = ScrollContainer.new()
var _rows: Array[FocusButton] = []
## The Settings vars of the tab that shows; settings_defaults resets them.
var _fields: Array[String] = []


func _init() -> void:
	super()
	var wash: Wash = Wash.new()
	wash.dim = Vector2(0.72, 0.92)
	add_child(wash)
	var column: VBoxContainer = UiTheme.column(24)
	column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	column.add_child(UiTheme.label("SETTINGS_TITLE", &"Title"))
	column.add_child(tabs)
	tabs.chosen.connect(_show_tab)
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.follow_focus = true
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(content)
	column.add_child(_scroll)
	var hints: Hints = Hints.new()
	hints.add_hint(&"ui_cancel", "HINT_BACK")
	hints.add_hint(&"settings_defaults", "HINT_DEFAULTS")
	column.add_child(hints)
	add_safe_area().add_child(column)


## Shows the first tab, with the focus on its first row.
func open() -> void:
	_show_tab(0)


func back() -> bool:
	Game.screen = return_to
	return true


## Changes the tab with tab_prev and tab_next, and resets the tab with settings_defaults.
func _unhandled_input(event: InputEvent) -> void:
	super(event)
	if not is_visible_in_tree():
		return
	var step: int = 0
	if event.is_action_pressed(&"tab_prev"):
		step = -1
	elif event.is_action_pressed(&"tab_next"):
		step = 1
	elif event.is_action_pressed(&"settings_defaults"):
		accept_event()
		_reset()
		return
	if step != 0:
		accept_event()
		Music.play_ui(&"move")
		_show_tab(posmod(tab + step, TABS.size()))


## Shows tab index with the focus on row focus_row, built again from Save.settings.
func _show_tab(index: int, focus_row: int = 0) -> void:
	tab = index
	tabs.current = index
	# Freed at once, not queued: no row of the old tab runs code now (a new window mode builds
	# the tab in a deferred call), and the new rows take their places.
	for child: Node in content.get_children():
		child.free()
	_rows.clear()
	_fields.clear()
	match index:
		0:
			_build_graphics()
		1:
			_build_display()
		2:
			_build_audio()
		3:
			_build_controls()
		4:
			_build_accessibility()
	FocusButton.link(_rows)
	_scroll.scroll_vertical = 0
	var focus: FocusButton = _rows[clampi(focus_row, 0, _rows.size() - 1)]
	if focus.focus_mode == Control.FOCUS_NONE:
		focus = _rows[0]
	focus.grab_focus()


func _build_graphics() -> void:
	var names: Array[String] = ["SETTINGS_LOW", "SETTINGS_MEDIUM", "SETTINGS_HIGH", "SETTINGS_ULTRA"]
	_option("graphics_preset", "SETTINGS_PRESET", Settings.PRESETS, names, &"choice")
	_option("ghost", "SETTINGS_GHOST", SWITCH, OFF_ON, &"switch")


func _build_display() -> void:
	var modes: Array[String] = ["SETTINGS_WINDOWED", "SETTINGS_BORDERLESS", "SETTINGS_FULLSCREEN"]
	_option("window_mode", "SETTINGS_MODE", Settings.WINDOW_MODES.keys(), modes, &"choice")
	var sizes: Array[Vector2i] = _resolutions()
	var size_texts: Array[String] = []
	for each: Vector2i in sizes:
		size_texts.append("%d × %d" % [each.x, each.y])
	var resolution: OptionRow = _option(
		"resolution", "SETTINGS_RESOLUTION", sizes, size_texts, &"stepper", _window_size()
	)
	resolution.set_enabled(Save.settings.window_mode == &"windowed")
	var caps: Array[String] = []
	for cap: int in FRAME_CAPS:
		caps.append(str(cap) if cap > 0 else "SETTINGS_OFF")
	_option("frame_cap", "SETTINGS_FRAME_CAP", FRAME_CAPS, caps, &"scale")
	_option("vsync", "SETTINGS_VSYNC", SWITCH, OFF_ON, &"switch")
	if DisplayServer.window_is_hdr_output_supported():
		_option("hdr", "SETTINGS_HDR", SWITCH, OFF_ON, &"switch")


func _build_audio() -> void:
	var volumes: Array[float] = []
	var texts: Array[String] = []
	for step: int in 21:
		volumes.append(step * 0.05)
		texts.append(str(step * 5))
	_option("master_volume", "SETTINGS_MASTER", volumes, texts, &"scale")
	_option("music_volume", "SETTINGS_MUSIC", volumes, texts, &"scale")
	_option("sfx_volume", "SETTINGS_EFFECTS", volumes, texts, &"scale")
	_option("ui_volume", "SETTINGS_INTERFACE", volumes, texts, &"scale")


func _build_controls() -> void:
	var speeds: Array[float] = []
	var speed_texts: Array[String] = []
	for step: int in range(1, 13):
		speeds.append(step * 0.25)
		speed_texts.append("%.2f" % (step * 0.25))
	_option("look_sensitivity", "SETTINGS_SENSITIVITY", speeds, speed_texts, &"scale")
	_option("invert_y", "SETTINGS_INVERT_Y", SWITCH, OFF_ON, &"switch")
	var zones: Array[float] = []
	var zone_texts: Array[String] = []
	for step: int in range(1, 9):
		zones.append(step * 0.05)
		zone_texts.append("%d%%" % (step * 5))
	_option("dead_zone", "SETTINGS_DEAD_ZONE", zones, zone_texts, &"scale")
	_option("rumble", "SETTINGS_RUMBLE", SWITCH, OFF_ON, &"switch")
	content.add_child(_bind_header())
	_fields.append("bindings")
	for action: StringName in Bindings.ACTIONS:
		var row: BindRow = BindRow.new(action)
		row.bound.connect(_bind.bind(action))
		_add(row)


func _build_accessibility() -> void:
	_option("camera_shake", "SETTINGS_CAMERA_SHAKE", SWITCH, OFF_ON, &"switch")
	_option("colourblind", "SETTINGS_COLOURBLIND", SWITCH, OFF_ON, &"switch")


## Adds a row for the Settings var field: values are its choices, texts show them. The row
## shows the value of current, else the saved value. Returns the row.
func _option(
	field: String,
	name_key: String,
	values: Array,
	texts: Array[String],
	look: StringName,
	current: Variant = null,
) -> OptionRow:
	var now: Variant = current if current != null else Save.settings.get(field)
	var row: OptionRow = OptionRow.new(name_key, texts, _index_of(values, now), look)
	row.changed.connect(func(index: int) -> void: _change(field, values[index]))
	_add(row)
	_fields.append(field)
	return row


## Adds row to the tab and to its list for the focus.
func _add(row: FocusButton) -> void:
	content.add_child(row)
	_rows.append(row)


## Saves and applies a new value of field. A new window mode turns the resolution row on or
## off, so the tab is built again.
func _change(field: String, value: Variant) -> void:
	Save.change_settings({field: value})
	if field == "window_mode":
		_show_tab.call_deferred(tab, 0)


## Saves and applies a new button of action on device.
func _bind(device: StringName, code: String, action: StringName) -> void:
	var bindings: Dictionary[String, String] = Save.settings.bindings.duplicate()
	bindings[Bindings.key(action, device)] = code
	Save.change_settings({"bindings": bindings})


## Puts the settings of the tab that shows back to their defaults, and keeps the focus on its
## row.
func _reset() -> void:
	var defaults: Dictionary[String, Variant] = Settings.new().to_dict()
	var values: Dictionary = {}
	for field: String in _fields:
		values[field] = defaults[field]
	Save.change_settings(values)
	Music.play_ui(&"select")
	var focused: Control = get_viewport().gui_get_focus_owner()
	_show_tab(tab, _rows.find(focused as FocusButton))


## The column titles over the button rows: Keyboard and Controller, over their slots.
static func _bind_header() -> Control:
	var margin: MarginContainer = MarginContainer.new()
	margin.add_theme_constant_override(&"margin_right", 30)
	margin.add_theme_constant_override(&"margin_top", 30)
	var line: HBoxContainer = UiTheme.row(0)
	line.alignment = BoxContainer.ALIGNMENT_END
	for key: String in ["SETTINGS_KEYBOARD", "SETTINGS_CONTROLLER"]:
		var title: Label = UiTheme.label(key, &"Caps")
		title.uppercase = true
		title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		title.custom_minimum_size = Vector2(BindRow.SLOT_WIDTH, 0.0)
		line.add_child(title)
	margin.add_child(line)
	return margin


## Returns the window sizes that fit on the screen of the window, with the size of the window
## now among them, from the smallest.
func _resolutions() -> Array[Vector2i]:
	var screen: Vector2i = DisplayServer.screen_get_usable_rect(get_window().current_screen).size
	var sizes: Array[Vector2i] = []
	for each: Vector2i in RESOLUTIONS:
		if screen == Vector2i.ZERO or (each.x <= screen.x and each.y <= screen.y):
			sizes.append(each)
	var now: Vector2i = _window_size()
	if not sizes.has(now):
		sizes.append(now)
		sizes.sort_custom(func(a: Vector2i, b: Vector2i) -> bool: return a.x * a.y < b.x * b.y)
	return sizes


## Returns the window size that the resolution setting names, else the size of the window.
func _window_size() -> Vector2i:
	var saved: Vector2i = Save.settings.resolution
	return saved if saved != Vector2i.ZERO else get_window().size


## Returns the index of value in values: the nearest one for a number, else the equal one, else
## 0.
static func _index_of(values: Array, value: Variant) -> int:
	if value is float:
		var target: float = value
		var best: int = 0
		for i: int in values.size():
			var each: float = values[i]
			var best_value: float = values[best]
			if absf(each - target) < absf(best_value - target):
				best = i
		return best
	return maxi(values.find(value), 0)
