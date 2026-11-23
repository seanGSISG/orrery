class_name MovingPlatform
extends LevelObject
## The `moving_platform` marker: a box deck that rides a path. The path starts at the marker
## and goes through the marker's points in order (kit.marker(points=...)). The deck waits
## `stop` s at each point, and each move eases out and in, so a marble that rests on the deck
## rides along through friction. One cycle takes `period` s, stops included: there and back
## along the path, or once round it when `loop` is true. The top face of the deck is at the
## path point, and the deck keeps the marker's rotation. With no points the deck stays still.
## The deck is a slab of the kit's stone in a frame of the kit's brass (KitMaterials): a band
## round its top edge and one round its foot. A set `finish` replaces the stone; the bands stay.

## The brass bands: their height, how far they stand out from the stone, and how far each band
## keeps from the deck's top face and underside, m.
const BAND: float = 0.14
const BAND_PROUD: float = 0.025
const BAND_DROP: float = 0.02

## The deck's stone of every platform; stone() makes it once.
static var _stone: ShaderMaterial = null

## Seconds for one cycle, stops included.
@export var period: float = 8.0
## Seconds that the deck waits at each point.
@export var stop: float = 1.0
## False: there and back along the path. True: from the last point on to the first.
@export var loop: bool = false
## Seconds into the cycle at t = 0. For two decks on one loop, give the second period / 2.
@export var offset: float = 0.0
## Deck size along the marker's x axis, m.
@export var width: float = 4.0
## Deck size along the marker's forward axis (Blender y), m.
@export var depth: float = 4.0
## Deck size down from the top face, m.
@export var thickness: float = 0.5
## The deck's material in place of the stone; the brass bands stay. A level script names a kit
## material, for example finish="wood", and the importer sets it (an unknown name fails the
## import). Null keeps the stone.
@export var finish: Material = null

## World positions where the deck stops, in cycle order. Leg i runs from stop i to stop i + 1,
## and the last leg runs back to stop 0.
var _stops: PackedVector3Array = []
## Move time of each leg, s.
var _times: PackedFloat64Array = []

@onready var _solid: Solid = $Solid


## Sizes the deck and its brass bands and works out the path from the marker's points. The
## bands are nodes of the scene, so that a mode that sets a range on every mesh of a level
## before the level's _ready (Ascent) finds them.
func _ready() -> void:
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(width, thickness, depth)
	var shape: CollisionShape3D = $Solid/Shape
	shape.shape = box
	shape.position.y = -thickness / 2.0
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = box.size
	var look: MeshInstance3D = $Solid/Mesh
	look.mesh = mesh
	look.material_override = finish if finish != null else stone()
	look.position = shape.position
	var tall: float = minf(BAND, thickness / 3.0)
	# Chamfered edges catch a highlight, so the bands read as brass and not as paint.
	var band: ArrayMesh = Chamfer.box(
		Vector3(width + 2.0 * BAND_PROUD, tall, depth + 2.0 * BAND_PROUD)
	)
	# The top band's top is BAND_DROP below the deck's top face, and the foot band's bottom is
	# BAND_DROP above the deck's underside, so no face of a band lies on a face of the stone.
	var top: MeshInstance3D = $Solid/Mesh/TopBand
	var foot: MeshInstance3D = $Solid/Mesh/FootBand
	top.position.y = thickness / 2.0 - BAND_DROP - tall / 2.0
	foot.position.y = BAND_DROP + (tall - thickness) / 2.0
	for frame: MeshInstance3D in [top, foot]:
		frame.mesh = band
		frame.material_override = KitMaterials.find("brass")
	_plan()


## Returns the deck's stone: a copy of the kit limestone with no paving. A deck moves, and the
## paving picks each slab's look from the piece's world position, so it would flicker.
static func stone() -> ShaderMaterial:
	if _stone == null:
		var slab: ShaderMaterial = KitMaterials.find("limestone").duplicate() as ShaderMaterial
		slab.set_shader_parameter("slab_size", Vector2.ZERO)
		_stone = slab
	return _stone


## Puts the deck at its start pose. A checkpoint respawn does not change it, because the clock
## runs on.
func reset(restart: bool) -> void:
	if restart:
		_place(0.0)
		_solid.reset_physics_interpolation()


## Moves the deck to its pose at run time t.
func advance(_run: LevelRun, t: float) -> void:
	_place(t)


## Fills _stops and _times. A path with no length, a negative stop, or a period too short for
## its stops keeps the deck at the marker.
func _plan() -> void:
	var points: PackedVector3Array = [global_position]
	for child: Node in get_children():
		var point: Marker3D = child as Marker3D
		if point != null:
			points.append(point.global_position)
	_stops = points.duplicate()
	if not loop:
		for i: int in range(points.size() - 2, 0, -1):
			_stops.append(points[i])
	var lengths: PackedFloat64Array = []
	var total: float = 0.0
	for i: int in _stops.size():
		lengths.append(_stops[i].distance_to(_stops[(i + 1) % _stops.size()]))
		total += lengths[i]
	var moving: float = period - stop * _stops.size()
	var valid: bool = moving > 0.0 and stop >= 0.0
	if total > 0.0 and not valid:
		var stops: String = "%d stops of %.2f s" % [_stops.size(), stop]
		push_error("moving_platform %s: needs stop >= 0 and period > %s" % [name, stops])
	if total <= 0.0 or not valid:
		_stops = [global_position]
		_times = [0.0]
		return
	_times.clear()
	for length: float in lengths:
		_times.append(moving * length / total)


## Moves the Solid to the deck pose at run time t, with the deck velocity at that time.
func _place(t: float) -> void:
	var at: Vector3 = _stops[0]
	var velocity: Vector3 = Vector3.ZERO
	var phase: float = fposmod(t + offset, period) if _stops.size() > 1 else 0.0
	for i: int in _stops.size():
		if phase < stop:
			at = _stops[i]
			break
		phase -= stop
		if phase < _times[i]:
			var from: Vector3 = _stops[i]
			var to: Vector3 = _stops[(i + 1) % _stops.size()]
			var u: float = phase / _times[i]
			at = from.lerp(to, 0.5 - 0.5 * cos(PI * u))
			velocity = (to - from) * (0.5 * PI / _times[i] * sin(PI * u))
			break
		phase -= _times[i]
	_solid.move(Transform3D(global_basis, at), velocity, Vector3.ZERO)
