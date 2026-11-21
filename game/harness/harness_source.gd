class_name HarnessSource
extends InputSource
## The harness's InputSource. The `input` command calls hold(); the run reads the held input
## through InputHub like the player's input. When the hold ends, the source gives no move,
## jump or use, and keeps the last camera angles.

## Ticks of hold left; -1 holds until the next hold() call.
var _left: int = 0
var _held: MarbleInput = MarbleInput.new()


## Starts with no input and the player's start pitch, so the first frame looks the same.
func _init() -> void:
	_held.camera_pitch = PlayerSource.START_PITCH


## Holds input for frames ticks; frames < 0 holds it until the next call.
func hold(input: MarbleInput, frames: int) -> void:
	_held = input
	_left = frames


## The camera angles of the held input, for a command that leaves them out.
func camera() -> Vector2:
	return Vector2(_held.camera_yaw, _held.camera_pitch)


## Returns the held input and counts down the hold.
func next_input(_state: GameState) -> MarbleInput:
	if _left == 0:
		var rest: MarbleInput = MarbleInput.new()
		rest.camera_yaw = _held.camera_yaw
		rest.camera_pitch = _held.camera_pitch
		_held = rest
		_left = -1
	elif _left > 0:
		_left -= 1
	return _held
