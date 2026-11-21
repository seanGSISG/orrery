class_name CrumblingTiles
extends LevelObject
## The `crumbling_tiles` marker: a flat grid of loose tiles, `width` by `depth` m, with the top
## face at the marker and centred on it. Each tile shakes from the marble's first touch, breaks
## and falls away `delay` s later, and stays gone until a respawn or a restart. Tilt the marker
## for a ramp or a slope. Each tile is its own Solid; a broken tile leaves the solid layer.

const LOOK: Material = preload("res://objects/crumbling_tiles/tile.tres")
## Gap between the tiles that shows on screen, m. The colliders have no gap.
const GAP: float = 0.02
## Largest shake offset of a cracked tile, m.
const SHAKE: float = 0.03
## Shakes per second of a cracked tile.
const SHAKE_RATE: float = 25.0
## Fall acceleration of a broken tile on screen, m/s².
const FALL: float = 9.8
## Seconds that a broken tile shows as it falls, before it hides.
const FALL_TIME: float = 1.0

## Seconds from a tile's first touch until it breaks.
@export var delay: float = 0.5
## Grid size along the marker's x axis, m.
@export var width: float = 4.0
## Grid size along the marker's forward axis (Blender y), m.
@export var depth: float = 4.0
## Edge of one tile, m. The grid rounds it so that whole tiles fill width and depth.
@export var tile: float = 2.0
## Tile size down from the top face, m.
@export var thickness: float = 0.5

var _columns: int = 1
var _rows: int = 1
## Size of one tile, m.
var _size: Vector3 = Vector3.ZERO
## The tiles in row order: index row * _columns + column.
var _solids: Array[Solid] = []
var _looks: Array[MeshInstance3D] = []
## Run time of each tile's first touch; INF while the tile is whole.
var _touched_at: PackedFloat64Array = []
## Run time of the current tick, from advance().
var _now: float = 0.0


## Builds one Solid with a box shape and a mesh for each tile of the grid.
func _ready() -> void:
	if delay < 0.0 or tile <= 0.0:
		push_error("crumbling_tiles %s: needs delay >= 0 and tile > 0" % name)
		delay = maxf(delay, 0.0)
		tile = width if tile <= 0.0 else tile
	_columns = maxi(1, roundi(width / tile))
	_rows = maxi(1, roundi(depth / tile))
	_size = Vector3(width / _columns, thickness, depth / _rows)
	var box: BoxShape3D = BoxShape3D.new()
	box.size = _size
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = _size - Vector3(GAP, 0, GAP)
	for row: int in _rows:
		for column: int in _columns:
			var solid: Solid = Solid.new()
			solid.name = "Tile%02d_%02d" % [row, column]
			solid.position = Vector3(
				(column + 0.5) * _size.x - width / 2.0, 0, (row + 0.5) * _size.z - depth / 2.0
			)
			add_child(solid)
			solid.owner = self
			var shape: CollisionShape3D = CollisionShape3D.new()
			shape.shape = box
			shape.position.y = -thickness / 2.0
			solid.add_child(shape)
			var look: MeshInstance3D = MeshInstance3D.new()
			look.mesh = mesh
			look.material_override = LOOK
			solid.add_child(look)
			_solids.append(solid)
			_looks.append(look)
	_touched_at.resize(_solids.size())
	reset(true)


## Brings every tile back whole.
func reset(_restart: bool) -> void:
	_touched_at.fill(INF)
	for i: int in _solids.size():
		_solids[i].collision_layer = WorldQuery.SOLID_MASK
		_looks[i].visible = true
		_looks[i].position = Vector3(0, -thickness / 2.0, 0)
	reset_physics_interpolation()


## Shakes each cracked tile, breaks it `delay` s after its touch with tile.fall, and lets it
## fall on screen.
func advance(_run: LevelRun, t: float) -> void:
	_now = t
	for i: int in _solids.size():
		var age: float = t - _touched_at[i]
		if age < 0.0:
			continue
		var look: MeshInstance3D = _looks[i]
		var rest: Vector3 = Vector3(0, -thickness / 2.0, 0)
		if age < delay:
			var phase: float = TAU * SHAKE_RATE * age
			look.position = rest + Vector3(sin(phase), 0, cos(phase * 1.3)) * SHAKE
			continue
		var solid: Solid = _solids[i]
		if solid.collision_layer != 0:
			solid.collision_layer = 0
			feedback.emit(&"tile.fall", 0.5, solid.global_position)
		var fall: float = age - delay
		look.visible = fall < FALL_TIME
		if look.visible:
			var drop: float = 0.5 * FALL * fall * fall
			look.global_position = solid.global_transform * rest + Vector3.DOWN * drop


## Cracks each whole tile that the marble touches, with tile.crack. The contact gives the
## marble centre, and every tile within the marble's contact reach of it cracks, so a marble on
## a seam cracks the tiles on both sides.
func on_touch(run: LevelRun, contact: Contact) -> void:
	var tuning: MarbleTuning = run.marble.tuning
	var reach: float = tuning.radius + tuning.contact_margin
	var centre: Vector3 = to_local(contact.point + contact.normal * (tuning.radius - contact.depth))
	var half: Vector3 = _size / 2.0
	for i: int in _solids.size():
		if _touched_at[i] != INF:
			continue
		var offset: Vector3 = centre - (_solids[i].position + Vector3(0, -half.y, 0))
		if (offset - offset.clamp(-half, half)).length() <= reach:
			_touched_at[i] = _now
			feedback.emit(&"tile.crack", 0.3, _solids[i].global_position)
