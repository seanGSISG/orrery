class_name MarbleInput
extends RefCounted
## What the marble reads each tick. Every InputSource makes one per tick: the player, the
## route bot and the harness. Make one with MarbleInput.new() and set the fields you need.

## Roll direction relative to camera_yaw: x = right, y = forward. Length 0..1.
var move: Vector2 = Vector2.ZERO
## True while the jump button is held.
var jump: bool = false
## True while the use button is held.
var use: bool = false
## Camera heading in radians around up, absolute, measured in Marble.frame.
var camera_yaw: float = 0.0
## Camera pitch in radians, absolute. Negative looks down.
var camera_pitch: float = 0.0
