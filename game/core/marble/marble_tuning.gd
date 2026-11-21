class_name MarbleTuning
extends Resource
## Every marble physics value (docs/plan.md §4.2). The one instance is
## res://core/marble_tuning.tres; tune the marble there, not in code.

## Marble radius, m. All art is built to this scale.
@export var radius: float = 0.2
@export var mass: float = 1.0
## Gravity when no GravityField applies, m/s², straight down.
@export var gravity: float = 20.0
## Top rolling speed from input, m/s. Input never slows a faster marble to this speed.
@export var max_roll_speed: float = 15.0
## How fast input changes the spin, rad/s².
@export var angular_acceleration: float = 75.0
## How fast the spin goes to zero with no input, rad/s².
@export var braking_acceleration: float = 30.0
## Air control: how fast input changes the velocity in the air, m/s².
@export var air_acceleration: float = 5.0
## A jump raises the speed away from the ground to this value, m/s, along the contact normal.
@export var jump_impulse: float = 7.5
## A jump needs ground whose normal has at least this dot with up. So a wall or a ceiling
## gives no jump; 0.1 allows slopes up to 84°.
@export var jump_min_up: float = 0.1
## Friction coefficients on the ground. Each Surface scales them.
@export var static_friction: float = 1.1
@export var kinetic_friction: float = 0.7
## Friction coefficient at a bounce, times the Surface friction.
@export var bounce_friction: float = 0.2
## Part of the speed into a surface that a bounce gives back, times the Surface restitution.
@export var restitution: float = 0.5
## A hit slides along the surface instead of bouncing when the speed into the surface is less
## than this part of the speed (the dot of the velocity direction and the normal).
@export var slide_threshold: float = 0.5
## A hit slower than this speed into the surface, m/s, stops without a bounce.
@export var min_bounce_speed: float = 0.1
## Speed into the surface, m/s, at which land and bounce feedback reach strength 1.
@export var hard_impact_speed: float = 20.0
## Longest move in one sub-step, in radii.
@export var max_substep_move: float = 0.5
@export var max_substeps: int = 16
## Contacts this far outside the surface still count, m.
@export var contact_margin: float = 0.01
