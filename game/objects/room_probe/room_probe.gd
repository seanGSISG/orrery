class_name RoomProbe
extends LevelObject
## The `room_probe` marker: the light of a room, such as one floor of a tower. The room is
## `width` x `depth` x `height` m inside its walls: the marker is the middle of its floor, and
## width runs along the marker's x, depth along its forward axis (Blender y). In the room the
## sky's cold ambient light gives way to a warm AMBIENT, and the reflections show the room, not
## the sky (an interior probe). The Ascent climb keeps these probes (ascent.gd).

## The ambient light of a room: warm, as from lamps and sunlit stone.
const AMBIENT: Color = Color(1.0, 0.86, 0.7)
## The probe's box reaches this far into the walls, the floor and the ceiling, m. A probe fades
## out over its blend distance at its edge, so a box the size of the room would give the room's
## own faces no light. Keep it less than the walls are thick, so their outer faces stay out.
const REACH: float = 0.45

## Room size along the marker's x axis, m.
@export var width: float = 10.0
## Room size along the marker's forward axis (Blender y), m.
@export var depth: float = 10.0
## Room height from the marker up, m.
@export var height: float = 6.0
## Strength of the ambient light.
@export var energy: float = 0.2


## Sizes the probe to the room and sets its light.
func _ready() -> void:
	var probe: ReflectionProbe = $Probe
	probe.size = Vector3(width, height, depth) + Vector3.ONE * 2.0 * REACH
	probe.position = Vector3(0.0, height / 2.0, 0.0)
	probe.blend_distance = REACH * 0.5
	probe.ambient_color = AMBIENT
	probe.ambient_color_energy = energy
