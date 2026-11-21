class_name Surface
extends Resource
## The scales of one surface type (default, ice, sand ...). Keep one shared .tres file for each
## type, and give it to Solid.surface.

@export var id: StringName = &"default"
## Scales MarbleTuning.static_friction and kinetic_friction.
@export var friction: float = 1.0
## Scales MarbleTuning.restitution.
@export var restitution: float = 1.0
