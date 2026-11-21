class_name FollowCamera
extends Camera3D
## Basic third-person camera (#7). Each frame it sits behind the marble at the input's camera
## yaw and pitch and looks at the marble, so rolling forward rolls away from the camera. Set
## run and add the camera to the tree. #11 replaces it with the orbit camera.

## Distance from the marble centre, m.
@export var distance: float = 2.5

## The run to follow.
var run: LevelRun


func _process(delta: float) -> void:
	if run != null:
		follow(run.state, run.last_input, delta)


## Places the camera for one frame from the state and the input of the last tick. This
## camera does not smooth, so it ignores _dt.
func follow(state: GameState, input: MarbleInput, _dt: float) -> void:
	var yaw: Basis = Basis(Vector3.UP, input.camera_yaw)
	var look: Basis = yaw * Basis(Vector3.RIGHT, input.camera_pitch)
	global_transform = Transform3D(look, state.position + look * Vector3(0.0, 0.0, distance))
