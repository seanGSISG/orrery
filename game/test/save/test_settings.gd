extends GutTest
## Each setting saves and applies at start (docs/plan.md §2.13): a SaveGame changes it through
## change_settings(), a new SaveGame reads the file as Save does at start, and its apply()
## puts the value into the game.

const DIR: String = "user://test_settings"

var _window_size: Vector2i


func before_each() -> void:
	_window_size = get_window().size
	DirAccess.remove_absolute(ProjectSettings.globalize_path(DIR).path_join(SaveGame.FILE))


## Puts back the defaults, the window and the save of the other tests.
func after_each() -> void:
	Settings.new().apply()
	get_window().mode = Window.MODE_WINDOWED
	get_window().size = _window_size
	DirAccess.remove_absolute(ProjectSettings.globalize_path(DIR).path_join(SaveGame.FILE))


func test_camera_shake() -> void:
	_start({"camera_shake": false})
	assert_false(FollowCamera.shake_enabled)


func test_rumble() -> void:
	_start({"rumble": false})
	assert_false(Rumble.enabled)


func test_dead_zone() -> void:
	_start({"dead_zone": 0.3})
	assert_almost_eq(InputHub.dead_zone, 0.3, 0.0001)


func test_look_sensitivity() -> void:
	_start({"look_sensitivity": 2.5})
	assert_almost_eq(PlayerSource.look_sensitivity, 2.5, 0.0001)


func test_invert_y() -> void:
	_start({"invert_y": true})
	assert_true(PlayerSource.invert_y)


func test_graphics_preset() -> void:
	_start({"graphics_preset": &"ultra"})
	assert_eq(Graphics.current, "ultra")


func test_volumes() -> void:
	_start({"master_volume": 0.8, "music_volume": 0.6, "sfx_volume": 0.4, "ui_volume": 0.2})
	assert_almost_eq(AudioBuses.volume(AudioBuses.MASTER), 0.8, 0.001)
	assert_almost_eq(AudioBuses.volume(AudioBuses.MUSIC), 0.6, 0.001)
	assert_almost_eq(AudioBuses.volume(AudioBuses.SFX), 0.4, 0.001)
	assert_almost_eq(AudioBuses.volume(AudioBuses.UI), 0.2, 0.001)


## The ghost setting is read by RunTracker at each run, so the loaded value is enough.
func test_ghost() -> void:
	assert_false(_start({"ghost": false}).ghost)


## The headless display server has no window modes, so the test checks the mode that apply()
## asks for, and the real mode where there is a display.
func test_window_mode() -> void:
	var modes: Dictionary[StringName, Window.Mode] = {
		&"borderless": Window.MODE_FULLSCREEN, &"fullscreen": Window.MODE_EXCLUSIVE_FULLSCREEN
	}
	for mode: StringName in modes:
		var settings: Settings = _start({"window_mode": mode})
		assert_eq(settings.window_mode_id(), modes[mode])
		if DisplayServer.get_name() != "headless":
			assert_eq(get_window().mode, modes[mode])


func test_resolution() -> void:
	_start({"resolution": Vector2i(1280, 720)})
	assert_eq(get_window().size, Vector2i(1280, 720))


func test_frame_cap() -> void:
	_start({"frame_cap": 144})
	assert_eq(Engine.max_fps, 144)


## The headless display server has no V-Sync, so the test checks the mode that apply() asks
## for, and the real mode where there is a display.
func test_vsync() -> void:
	var settings: Settings = _start({"vsync": false})
	assert_eq(settings.vsync_mode(), DisplayServer.VSYNC_DISABLED)
	if DisplayServer.get_name() != "headless":
		assert_eq(DisplayServer.window_get_vsync_mode(), DisplayServer.VSYNC_DISABLED)


## HDR output is asked for only where the display supports it.
func test_hdr() -> void:
	assert_true(_start({"hdr": true}).hdr)
	var supported: bool = DisplayServer.window_is_hdr_output_supported()
	assert_eq(get_window().hdr_output_requested, supported)


func test_colourblind() -> void:
	_start({"colourblind": true})
	assert_true(Palette.colourblind)


func test_bindings() -> void:
	_start({"bindings": {Bindings.key(&"jump", &"pad"): "button:3"}})
	var events: Array[InputEvent] = InputMap.action_get_events(&"jump")
	var buttons: Array[int] = []
	for event: InputEvent in events:
		if event is InputEventJoypadButton:
			buttons.append((event as InputEventJoypadButton).button_index)
	assert_eq(buttons, [JOY_BUTTON_Y] as Array[int])


## Writes values through change_settings() in one SaveGame, then reads the file in a new one
## and applies it, as Save does at start. Returns the loaded settings.
func _start(values: Dictionary) -> Settings:
	var before: SaveGame = _save_game()
	assert_true(before.change_settings(values), "written")
	Settings.new().apply()
	var after: SaveGame = _save_game()
	after.read()
	for key: String in values:
		# Wrapped in a Dictionary: GUT's asserts take no bare Variant (unsafe_call_argument).
		var saved: Dictionary = {key: after.settings.to_dict()[key]}
		assert_eq(saved, {key: before.settings.to_dict()[key]}, key + " saved")
	after.settings.apply()
	return after.settings


## Returns a SaveGame in DIR that the test frees.
func _save_game() -> SaveGame:
	var made: SaveGame = SaveGame.new()
	made.dir = DIR
	autofree(made)
	return made
