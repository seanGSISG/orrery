class_name Settings
extends SaveRecord
## The player's settings (docs/plan.md §2.4, §2.13). Save.settings holds the one instance.
## To add a setting, add a var with its default here, and put it into the game in apply();
## the file keeps it with no other change.
##
## Change settings with Save.change_settings({key: value}): it sets the vars, calls apply()
## and writes the file. The settings menu and the harness `set_setting` both use it. Save
## applies the settings once at start.

## The graphics presets, from the cheapest (Graphics.use()).
const PRESETS: Array[StringName] = [&"low", &"medium", &"high", &"ultra"]
## The window modes and the Window.Mode of each. Borderless is a window that fills the
## screen; fullscreen takes the screen for the game alone.
const WINDOW_MODES: Dictionary[StringName, Window.Mode] = {
	&"windowed": Window.MODE_WINDOWED,
	&"borderless": Window.MODE_FULLSCREEN,
	&"fullscreen": Window.MODE_EXCLUSIVE_FULLSCREEN,
}

## Camera shake on landings (FollowCamera.shake_enabled).
var camera_shake: bool = true
## Controller rumble (Rumble.enabled).
var rumble: bool = true
## Radial stick dead zone, 0..1 (InputHub.dead_zone).
var dead_zone: float = 0.15
## Camera turn speed factor (PlayerSource.look_sensitivity).
var look_sensitivity: float = 1.0
## Up on the stick or the mouse looks down (PlayerSource.invert_y).
var invert_y: bool = false
## One of PRESETS (Graphics.use()).
var graphics_preset: StringName = &"medium"
## Bus volumes, 0..1 (AudioBuses).
var master_volume: float = 1.0
var music_volume: float = 1.0
var sfx_volume: float = 1.0
var ui_volume: float = 1.0
## Show the ghost of the best run while playing a level.
var ghost: bool = true
## One of WINDOW_MODES.
var window_mode: StringName = &"windowed"
## Size of the window in windowed mode. (0, 0) keeps the size that the game starts with.
var resolution: Vector2i = Vector2i.ZERO
## Frames per second at most (Engine.max_fps); 0 is uncapped.
var frame_cap: int = 0
## Wait for the display's refresh before each frame.
var vsync: bool = true
## HDR output, where the display and the driver support it (Window.hdr_output_requested).
var hdr: bool = false
## Gem and hazard colours from the colourblind palette (Palette.colourblind).
var colourblind: bool = false
## The player's buttons for the gameplay actions, by Bindings.key(action, device). Each value
## is a Bindings code. An action with no entry for a device has its default buttons there.
var bindings: Dictionary[String, String] = {}


## Puts every setting into the game. Call it after a change; Save calls it at start.
func apply() -> void:
	FollowCamera.shake_enabled = camera_shake
	Rumble.enabled = rumble
	InputHub.dead_zone = dead_zone
	PlayerSource.look_sensitivity = look_sensitivity
	PlayerSource.invert_y = invert_y
	if graphics_preset in PRESETS:
		Graphics.use(String(graphics_preset))
	AudioBuses.apply(self)
	Palette.use(colourblind)
	Bindings.apply(bindings)
	_apply_display()


## Returns the Window.Mode that window_mode names; windowed for a name that is not one.
func window_mode_id() -> Window.Mode:
	return WINDOW_MODES.get(window_mode, Window.MODE_WINDOWED)


## Returns the V-Sync mode that the vsync setting asks for.
func vsync_mode() -> DisplayServer.VSyncMode:
	return DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED


## Sets the window mode, the size of a window, the frame cap, V-Sync and HDR output. It
## changes the window only where it differs, so a change of another setting does not move it.
func _apply_display() -> void:
	var window: Window = (Engine.get_main_loop() as SceneTree).root
	var mode: Window.Mode = window_mode_id()
	if window.mode != mode:
		window.mode = mode
	if mode == Window.MODE_WINDOWED and resolution != Vector2i.ZERO and window.size != resolution:
		window.size = resolution
		window.move_to_center()
	Engine.max_fps = maxi(frame_cap, 0)
	if DisplayServer.window_get_vsync_mode() != vsync_mode():
		DisplayServer.window_set_vsync_mode(vsync_mode())
	window.hdr_output_requested = hdr and DisplayServer.window_is_hdr_output_supported()
