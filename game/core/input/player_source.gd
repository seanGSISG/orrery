class_name PlayerSource
extends InputSource
## The player's keyboard and mouse: W A S D roll, Space jumps, left click uses. Click the
## game to capture the mouse, then the mouse turns the camera; Esc frees the mouse.
## InputHub uses this source by default. #18 adds the controller.

## Radians of camera turn per pixel of mouse motion.
const LOOK_SPEED: float = 0.003
## Pitch limits in radians. Negative looks down.
const PITCH_MIN: float = -1.4
const PITCH_MAX: float = 0.4
const START_PITCH: float = -0.45

var _yaw: float = 0.0
var _pitch: float = START_PITCH


## Returns the held keys and the camera angles as one MarbleInput.
func next_input(_state: GameState) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.move = Input.get_vector(&"roll_left", &"roll_right", &"roll_back", &"roll_forward")
	input.jump = Input.is_action_pressed(&"jump")
	input.use = Input.is_action_pressed(&"use")
	input.camera_yaw = _yaw
	input.camera_pitch = _pitch
	return input


## Turns the camera with the mouse while the mouse is captured.
func handle_event(event: InputEvent) -> void:
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw = wrapf(_yaw - motion.relative.x * LOOK_SPEED, -PI, PI)
		_pitch = clampf(_pitch - motion.relative.y * LOOK_SPEED, PITCH_MIN, PITCH_MAX)
	elif event is InputEventMouseButton and event.is_pressed():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event.is_action_pressed(&"ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
