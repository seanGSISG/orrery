class_name InputSource
extends RefCounted
## One producer of MarbleInput: the player, the route bot or the harness. Extend it and
## override next_input(); give it to InputHub.use_source() to make it the active source.


## Returns the input for the next tick. The hub calls it once per tick; state is the latest
## snapshot. This base source returns no input.
func next_input(_state: GameState) -> MarbleInput:
	return MarbleInput.new()


## Receives the unhandled input events that the hub forwards. This base source ignores them.
func handle_event(_event: InputEvent) -> void:
	pass
