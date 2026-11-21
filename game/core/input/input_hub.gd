extends Node
## Autoload InputHub. Holds the one active InputSource; the player source is the default.
## The run calls next_input() once per tick. The harness and the route bot call use_source().
## It has no class_name, because a class_name would hide the autoload.

## The last physical device used: &"keyboard" or &"pad".
var device: StringName = &"keyboard"

var _source: InputSource = PlayerSource.new()


## Makes source the only active source.
func use_source(source: InputSource) -> void:
	_source = source


## Returns the active source's input for the next tick.
func next_input(state: GameState) -> MarbleInput:
	return _source.next_input(state)


## Tracks the last physical device from every event, also the ones the UI uses.
func _input(event: InputEvent) -> void:
	var axis: InputEventJoypadMotion = event as InputEventJoypadMotion
	if event is InputEventJoypadButton or (axis != null and absf(axis.axis_value) > 0.5):
		device = &"pad"
	elif event is InputEventKey or event is InputEventMouseButton:
		device = &"keyboard"


## Forwards the events that nothing else handled to the active source.
func _unhandled_input(event: InputEvent) -> void:
	_source.handle_event(event)
