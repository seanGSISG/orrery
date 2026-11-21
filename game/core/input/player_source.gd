class_name PlayerSource
extends InputSource
## The player's keyboard, mouse and controller (docs/plan.md §2.4). W A S D or the left stick
## roll, Space or A jumps, left click, X or RT uses. Click the game to capture the mouse,
## then the mouse turns the camera; Esc frees the mouse. The right stick turns the camera at
## any time. Stick roll stays analog: half a push rolls at half strength. InputHub uses this
## source by default.
##
## The static vars are the player's camera settings; a settings menu sets them, and they
## apply at once. The stick dead zone setting is InputHub.dead_zone.

## Radians of camera turn per pixel of mouse motion, at look_sensitivity 1.
const LOOK_SPEED: float = 0.003
## Camera turn rates at full right-stick push and look_sensitivity 1, radians per second.
const STICK_YAW_RATE: float = 3.0
const STICK_PITCH_RATE: float = 2.0
## Pitch limits in radians. Negative looks down.
const PITCH_MIN: float = -1.4
const PITCH_MAX: float = 0.4
const START_PITCH: float = -0.45

## Multiplies the camera turn of the mouse and the right stick.
static var look_sensitivity: float = 1.0
## True: pushing the right stick up or moving the mouse up looks down.
static var invert_y: bool = false

var _yaw: float = 0.0
var _pitch: float = START_PITCH


## Returns the held roll, jump and use inputs and the camera angles as one MarbleInput.
## Each call is one tick, so the right stick turns the camera by one tick's worth.
func next_input(_state: GameState) -> MarbleInput:
	var input: MarbleInput = MarbleInput.new()
	input.move = Input.get_vector(
		&"roll_left", &"roll_right", &"roll_back", &"roll_forward", InputHub.dead_zone
	)
	input.jump = Input.is_action_pressed(&"jump")
	input.use = Input.is_action_pressed(&"use")
	var look: Vector2 = Input.get_vector(
		&"look_left", &"look_right", &"look_down", &"look_up", InputHub.dead_zone
	)
	# The square curve gives fine aim near the centre and full speed at the rim.
	look *= look.length() * look_sensitivity / Engine.physics_ticks_per_second
	_turn(-look.x * STICK_YAW_RATE, look.y * STICK_PITCH_RATE)
	input.camera_yaw = _yaw
	input.camera_pitch = _pitch
	return input


## Turns the camera with the mouse while the mouse is captured.
func handle_event(event: InputEvent) -> void:
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var turn: Vector2 = -motion.relative * LOOK_SPEED * look_sensitivity
		_turn(turn.x, turn.y)
	elif event is InputEventMouseButton and event.is_pressed():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event.is_action_pressed(&"ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


## Turns the camera by yaw and pitch radians; pitch > 0 looks up unless invert_y is on.
func _turn(yaw: float, pitch: float) -> void:
	_yaw = wrapf(_yaw + yaw, -PI, PI)
	_pitch = clampf(_pitch + (-pitch if invert_y else pitch), PITCH_MIN, PITCH_MAX)
