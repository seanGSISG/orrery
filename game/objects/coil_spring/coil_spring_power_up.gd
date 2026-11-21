class_name CoilSpringPowerUp
extends PowerUp
## The held Coil Spring: a high jump. The use raises the marble's speed along up to
## launch_speed and keeps the speed across up, so at 20 m/s and gravity 20 m/s² the marble
## rises 10 m. A marble that already rises faster keeps its speed.

## Speed along up after the use, m/s.
var launch_speed: float


## Makes a Coil Spring that launches at speed m/s.
func _init(speed: float) -> void:
	super(&"coil_spring")
	launch_speed = speed


## Launches the marble along up.
func use(run: LevelRun) -> void:
	var marble: Marble = run.marble
	var rise: float = launch_speed - marble.velocity.dot(marble.up)
	if rise > 0.0:
		marble.add_velocity(marble.up * rise)
