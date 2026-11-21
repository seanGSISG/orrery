extends Node
## Autoload InputHub. Holds the one active InputSource; the player source is the default.
## The run calls next_input() once per tick. The harness and the route bot call use_source().
## It also tracks the device used last (for GameState and the button glyphs) and rumbles
## that pad for the feedback of every LevelRun. It has no class_name, because a class_name
## would hide the autoload.

## Emitted when the device used last changes, for example to redraw button glyphs.
signal device_changed(device: StringName)

## The stick push from which a stick or trigger counts as pad use.
const PAD_AXIS_USE: float = 0.5

## The last physical device used: &"keyboard" or &"pad".
var device: StringName = &"keyboard"
## Godot's device id of the pad used last; -1 before any pad input. Rumble goes to it.
var pad: int = -1

var _source: InputSource = PlayerSource.new()


## Watches pad hot-plug and every LevelRun that enters the tree.
func _ready() -> void:
	Input.joy_connection_changed.connect(_on_joy_connection_changed)
	get_tree().node_added.connect(_on_node_added)


## Makes source the only active source.
func use_source(source: InputSource) -> void:
	_source = source


## Returns the active source's input for the next tick.
func next_input(state: GameState) -> MarbleInput:
	return _source.next_input(state)


## Tracks the last physical device from every event, also the ones the UI uses.
func _input(event: InputEvent) -> void:
	var axis: InputEventJoypadMotion = event as InputEventJoypadMotion
	if event is InputEventJoypadButton or (axis != null and absf(axis.axis_value) > PAD_AXIS_USE):
		pad = event.device
		_set_device(&"pad")
	elif event is InputEventKey or event is InputEventMouseButton:
		_set_device(&"keyboard")


## Forwards the events that nothing else handled to the active source.
func _unhandled_input(event: InputEvent) -> void:
	_source.handle_event(event)


## Sets device and emits device_changed when it changes.
func _set_device(next: StringName) -> void:
	if next != device:
		device = next
		device_changed.emit(device)


## Falls back to the keyboard when the active pad is unplugged. A pad that is plugged in
## becomes active on its first input.
func _on_joy_connection_changed(id: int, connected: bool) -> void:
	if not connected and id == pad:
		pad = -1
		_set_device(&"keyboard")


## Connects rumble to the feedback of each LevelRun.
func _on_node_added(node: Node) -> void:
	var run: LevelRun = node as LevelRun
	if run != null and not run.feedback.is_connected(_on_feedback):
		run.feedback.connect(_on_feedback)


## Rumbles the active pad for one feedback while the player uses a pad.
func _on_feedback(kind: StringName, strength: float, _at: Vector3) -> void:
	if device == &"pad":
		Rumble.play(pad, kind, strength)
