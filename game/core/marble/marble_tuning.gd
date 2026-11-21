class_name MarbleTuning
extends Resource
## Every marble physics value (docs/plan.md §4.2). The one instance is
## res://core/marble_tuning.tres; tune the marble there, not in code.

## Marble radius, m. All art is built to this scale.
@export var radius: float = 0.2
@export var mass: float = 1.0
## Gravity when no gravity field applies, m/s².
@export var gravity: float = 20.0
## Top rolling speed from input, m/s. Input never slows a faster marble to this speed.
@export var max_roll_speed: float = 15.0
## How fast input changes the spin, rad/s².
@export var angular_acceleration: float = 75.0
## How fast the spin goes to zero with no input, rad/s².
@export var braking_acceleration: float = 30.0
@export var air_acceleration: float = 5.0
@export var jump_impulse: float = 7.5
## Friction coefficients. Each Surface scales them.
@export var static_friction: float = 1.1
@export var kinetic_friction: float = 0.7
@export var bounce_friction: float = 0.2
@export var restitution: float = 0.5
## Dot of velocity and normal below which an impact slides instead of bouncing.
@export var slide_threshold: float = 0.5
@export var min_bounce_speed: float = 0.1
## Longest move in one sub-step, in radii.
@export var max_substep_move: float = 0.5
@export var max_substeps: int = 16
## Contacts this far outside the surface still count, m.
@export var contact_margin: float = 0.01
