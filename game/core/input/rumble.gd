class_name Rumble
extends RefCounted
## Controller rumble for the run's feedback (docs/plan.md §2.4): landings, bumpers and
## power-ups. InputHub calls play() for every feedback of every LevelRun while the player
## uses a pad. A power-up's feedback kind ends in `.use`, for example `coil_spring.use`.

## Rumble at feedback strength 1 for each kind: weak motor, strong motor (0..1), seconds.
const KINDS: Dictionary[StringName, Vector3] = {
	&"marble.land": Vector3(0.3, 0.7, 0.15),
	&"bumper.hit": Vector3(0.8, 0.4, 0.15),
}
## Rumble at strength 1 for a power-up's `.use` feedback.
const POWER_UP: Vector3 = Vector3(0.5, 0.8, 0.25)
## Feedback weaker than this does not rumble, so small bumps stay quiet.
const MIN_STRENGTH: float = 0.15

## Turn rumble off or on (the setting of docs/plan.md §2.4).
static var enabled: bool = true


## Returns the rumble for one feedback as weak motor, strong motor and seconds. The motors
## scale with strength; Vector3.ZERO means no rumble.
static func motors(kind: StringName, strength: float) -> Vector3:
	var full: Vector3 = KINDS.get(kind, Vector3.ZERO)
	if String(kind).ends_with(".use"):
		full = POWER_UP
	if strength < MIN_STRENGTH:
		return Vector3.ZERO
	var scale: float = clampf(strength, 0.0, 1.0)
	return Vector3(full.x * scale, full.y * scale, full.z)


## Rumbles pad for one feedback when rumble is on.
static func play(pad: int, kind: StringName, strength: float) -> void:
	var rumble: Vector3 = motors(kind, strength)
	if enabled and rumble.z > 0.0:
		Input.start_joy_vibration(pad, rumble.x, rumble.y, rumble.z)
