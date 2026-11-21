class_name Contact
extends RefCounted
## One touch between the marble and a Solid. WorldQuery.contacts() makes them; the solver and
## LevelObject.on_touch() read them. At the edge of a flush Solid, a contact copies the point,
## normal, depth and velocity of the surface that the edge continues, and keeps its own surface
## and object (WorldQuery).

## The touched point, on the surface.
var point: Vector3
## Unit vector from point toward the marble centre.
var normal: Vector3
## Radius minus distance. Negative when the surface is inside the contact margin only.
var depth: float
## Surface velocity at point.
var velocity: Vector3
## The Solid's surface type. Never null.
var surface: Surface
## The object that owns the Solid. Null for plain level geometry.
var object: LevelObject
