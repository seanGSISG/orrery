class_name Ui
extends CanvasLayer
## The HUD and the menus. It shows the screen that Game.screen names: one of `screens`, or
## the HUD for &"play". main.tscn has one; a test adds its own.
##
## - With no run and no menu (the start of the game), it shows the title.
## - The `pause` action (Menu or Esc) pauses a level and resumes it.
## - When the run finishes, it stops the marble on the finish and shows the results.
## - Under a menu with no run, it shows the Backdrop.
## - It plays the menu sounds: a move of the focus here, select in the items, back in Screen.
## - The HUD shows only through the run's FollowCamera, so a screenshot from a level's shot
##   camera has no HUD.
##
## The look is UiLook; UiTheme builds the Theme from it, and `_root` gives it to every
## control. All text is a key of res://ui/text/en.po.

var hud: Hud = Hud.new()
var title: TitleScreen = TitleScreen.new()
var level_select: LevelSelectScreen = LevelSelectScreen.new()
var settings: SettingsScreen = SettingsScreen.new()
var pause: PauseScreen = PauseScreen.new()
var results: ResultsScreen = ResultsScreen.new()
## The screens by their name in Game.screen. &"play" is not here: it shows the HUD.
var screens: Dictionary[StringName, Screen] = {
	&"title": title,
	&"level_select": level_select,
	&"settings": settings,
	&"pause": pause,
	&"results": results,
}

var _root: Control = Control.new()
var _backdrop: Backdrop
## The screen that shows now.
var _shown: StringName = &""
## The best time of the run's level before this attempt; the results compare with it.
var _best_before: float = -1.0
## True while a screen opens, so that its first focus makes no sound.
var _quiet: bool = false
## True when the mouse turned the camera before a menu took it.
var _mouse_was_captured: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 5
	_root.theme = UiTheme.build()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_root.add_child(hud)
	for screen: Screen in screens.values():
		screen.visible = false
		_root.add_child(screen)
	if Game.run == null and Game.screen == &"play":
		Game.screen = &"title"
	Game.screen_changed.connect(_show)
	Game.child_entered_tree.connect(_on_game_child)
	get_viewport().gui_focus_changed.connect(_on_focus_changed)
	_show(Game.screen)


## Updates the HUD, and follows the run to the results and back.
func _process(_delta: float) -> void:
	var run: LevelRun = Game.run
	if run == null:
		return
	var finished: bool = run.state.status == &"finished"
	if Game.screen == &"play" and finished:
		# The marble stays on the finish, and the run stops (Game), under the results.
		run.teleport(run.state.position, Vector3.ZERO)
		Game.screen = &"results"
	elif Game.screen == &"results" and not finished:
		# The harness or a bot restarted the run.
		Game.screen = &"play"
	elif Game.screen == &"play":
		hud.show_state(run.state, run.level)
		hud.visible = get_viewport().get_camera_3d() is FollowCamera


## Pauses and resumes with the `pause` action.
func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed(&"pause"):
		return
	var run: LevelRun = Game.run
	if Game.screen == &"play" and run != null and run.state.status != &"finished":
		Game.screen = &"pause"
	elif Game.screen == &"pause":
		Music.play_ui(&"back")
		Game.screen = &"play"
	else:
		return
	get_viewport().set_input_as_handled()


## Shows screen: its Screen, or the HUD for &"play".
func _show(screen: StringName) -> void:
	var before: StringName = _shown
	_shown = screen
	var run: LevelRun = Game.run
	if screen == &"settings" and before != &"settings":
		settings.return_to = before
	if screen == &"results":
		results.catalog = level_select.catalog
		results.previous_best = _best_before
	if screen == &"play" and run != null:
		_begin_attempt(run)
		hud.show_state(run.state, run.level)
	_take_mouse(screen != &"play")
	hud.visible = screen == &"play" and run != null
	for id: StringName in screens:
		screens[id].visible = id == screen
	_quiet = true
	if screens.has(screen):
		screens[screen].open()
	else:
		get_viewport().gui_release_focus()
	_quiet = false
	# Deferred, so that a level that loads in this frame (`--level`) never makes a backdrop.
	_sync_backdrop.call_deferred()


## Keeps what the results and the level select need of the attempt that starts on run: the
## best time of its level before the attempt, and the level. _show() calls it for a retry.
func _begin_attempt(run: LevelRun) -> void:
	_best_before = Save.level(run.level.id).best_time
	level_select.last_level = run.level.id


## Begins the attempt of a run when Game adds it, before its first tick. The harness can load
## and finish a level in one frame, with no change of screen in between.
func _on_game_child(node: Node) -> void:
	var run: LevelRun = node as LevelRun
	if run != null:
		_begin_attempt(run)


## Adds the Backdrop while there is no run, and frees it when there is one.
func _sync_backdrop() -> void:
	if Game.run == null and _backdrop == null:
		_backdrop = Backdrop.new()
		add_child(_backdrop)
	elif Game.run != null and _backdrop != null:
		remove_child(_backdrop)
		_backdrop.queue_free()
		_backdrop = null


## With menu true, frees the mouse for the menu. With menu false, gives the mouse back to the
## camera when it had it before the menu.
func _take_mouse(menu: bool) -> void:
	if menu:
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			_mouse_was_captured = true
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif _mouse_was_captured:
		_mouse_was_captured = false
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


## Plays the move sound when the focus moves inside a screen.
func _on_focus_changed(_control: Control) -> void:
	if not _quiet:
		Music.play_ui(&"move")
