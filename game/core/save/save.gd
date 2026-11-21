extends SaveGame
## Autoload Save: the SaveGame of the game, in user://. At start it only reads the file. It
## puts a RunTracker into each run that Game loads, so that the egg, the finish and the ghost
## save themselves. It has no class_name, because a class_name would hide the autoload.


## Reads the save file and starts to watch Game for new runs. Writes nothing.
func _ready() -> void:
	read()
	Game.child_entered_tree.connect(_on_game_child)


## Adds a RunTracker to run when the run is ready, so that the run has its marble and objects.
func _on_game_child(node: Node) -> void:
	var run: LevelRun = node as LevelRun
	if run != null:
		run.ready.connect(RunTracker.attach.bind(run, self), CONNECT_ONE_SHOT)
