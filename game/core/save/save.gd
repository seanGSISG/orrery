extends SaveGame
## Autoload Save: the SaveGame of the game, in user://. At start it reads the file and puts
## the settings into the game. It puts a RunTracker into each run that Game loads, so that
## the egg, the finish and the ghost save themselves. It has no class_name, because a
## class_name would hide the autoload.


## Reads the save file, applies its settings and starts to watch Game for new runs. Writes
## nothing.
func _ready() -> void:
	read()
	# Deferred: the autoloads after Save (Graphics, Music) are not in the tree yet.
	_apply_settings.call_deferred()
	Game.child_entered_tree.connect(_on_game_child)


## Puts the settings that are loaded now into the game.
func _apply_settings() -> void:
	settings.apply()


## Adds a RunTracker to run when the run is ready, so that the run has its marble and objects.
func _on_game_child(node: Node) -> void:
	var run: LevelRun = node as LevelRun
	if run != null:
		run.ready.connect(RunTracker.attach.bind(run, self), CONNECT_ONE_SHOT)
