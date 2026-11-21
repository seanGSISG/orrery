@tool
class_name CrumblingTiles
extends LevelObject
## The `crumbling_tiles` marker: a flat grid of loose tiles, `width` by `depth` m, with the top
## face at the marker and centred on it. Each tile shakes from the marble's first touch, breaks
## and falls away `delay` s later, and stays gone until a respawn or a restart. Tilt the marker
## for a ramp or a slope. Each tile is its own Solid; a broken tile leaves the solid layer.
## A tile is worn stone, the kit's limestone (KitMaterials) darker and more worn than the floor
## round it, on a thin brass tray that shows as a brass line in the gap round the tile. Each
## tile lies at its own small tilt and shows its own patch of stone, so loose tiles read apart
## from solid floor. The tray falls with its tile.
## It is a tool script, so that the tiles also exist in the editor: the lightmap bake lights
## them like the stone round them, and their baked light moves with a tile as it falls.

## The worn look against the kit limestone: its tint is this much darker, and its normal map
## has this strength (the kit limestone keeps the shader's 1.0).
const WORN_SHADE: float = 0.78
const WORN_RELIEF: float = 1.8
## Gap between the tiles that shows on screen, m. The colliders have no gap.
const GAP: float = 0.05
## The brass tray under a tile: as wide as the tile's collider, this thick, its top this far
## below the tile's top, m.
const TRAY: float = 0.04
const TRAY_DROP: float = 0.01
## A tile lies tilted by up to this angle round a level axis, rad. Its collider stays level.
const TILT: float = deg_to_rad(0.8)
## A tile's stone shows a patch of the texture moved by up to this far along each axis: one
## texture repeat of the kit limestone, m.
const PATCH: float = 1.5
## Largest shake offset of a cracked tile, m.
const SHAKE: float = 0.03
## Shakes per second of a cracked tile.
const SHAKE_RATE: float = 25.0
## Fall acceleration of a broken tile on screen, m/s².
const FALL: float = 9.8
## Seconds that a broken tile shows as it falls, before it hides.
const FALL_TIME: float = 1.0

## The worn look of every tile; worn_look() makes it once.
static var _worn: ShaderMaterial = null

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
## Where each tile's look rests in its Solid: below the top, and back by its stone's patch.
var _rests: PackedVector3Array = []
## Run time of each tile's first touch; INF while the tile is whole.
var _touched_at: PackedFloat64Array = []
## Run time of the current tick, from advance().
var _now: float = 0.0


## Builds one Solid with a box shape, a stone mesh and a brass tray for each tile of the grid.
func _ready() -> void:
	# In the editor, build the tiles only inside a level, for the lightmap bake. In the
	# object's own scene they would be saved with it, and built twice at run time.
	if Engine.is_editor_hint() and get_tree().edited_scene_root == self:
		return
	if delay < 0.0 or tile <= 0.0:
		push_error("crumbling_tiles %s: needs delay >= 0 and tile > 0" % name)
		delay = maxf(delay, 0.0)
		tile = width if tile <= 0.0 else tile
	_columns = maxi(1, roundi(width / tile))
	_rows = maxi(1, roundi(depth / tile))
	_size = Vector3(width / _columns, thickness, depth / _rows)
	var box: BoxShape3D = BoxShape3D.new()
	box.size = _size
	var stone: BoxMesh = BoxMesh.new()
	stone.size = _size - Vector3(GAP, 0, GAP)
	stone.add_uv2 = true
	var arrays: Array = stone.surface_get_arrays(0)
	var tray: BoxMesh = BoxMesh.new()
	tray.size = Vector3(_size.x, TRAY, _size.z)
	var brass: Material = KitMaterials.find("brass")
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
			var dice: RandomNumberGenerator = RandomNumberGenerator.new()
			dice.seed = hash(Vector2i(column, row))
			var patch: Vector3 = Vector3(dice.randf(), 0, dice.randf()) * PATCH
			var turn: float = dice.randf() * TAU
			var tilt: Basis = Basis(Vector3(cos(turn), 0, sin(turn)), dice.randf() * TILT)
			var look: MeshInstance3D = MeshInstance3D.new()
			look.name = "Look"
			look.mesh = _stone(arrays, tilt, patch, stone.lightmap_size_hint)
			look.material_override = worn_look()
			solid.add_child(look)
			# The lightmap bake skips a node with no owner.
			look.owner = self
			var under: MeshInstance3D = MeshInstance3D.new()
			under.name = "Tray"
			under.mesh = tray
			under.material_override = brass
			under.gi_mode = GeometryInstance3D.GI_MODE_DYNAMIC
			under.position = patch + Vector3(0, thickness / 2.0 - TRAY_DROP - TRAY / 2.0, 0)
			look.add_child(under)
			_solids.append(solid)
			_looks.append(look)
			_rests.append(Vector3(0, -thickness / 2.0, 0) - patch)
	_touched_at.resize(_solids.size())
	reset(true)


## Returns the tiles' look: a copy of the kit limestone, darker, with a stronger normal map and
## no paving. A tile moves as it shakes and falls, and the paving picks each slab's look from
## the piece's world position, so it would flicker on a tile.
static func worn_look() -> ShaderMaterial:
	if _worn == null:
		var stone: ShaderMaterial = KitMaterials.find("limestone").duplicate() as ShaderMaterial
		var tint: Vector3 = stone.get_shader_parameter("tint")
		stone.set_shader_parameter("tint", tint * WORN_SHADE)
		stone.set_shader_parameter("normal_strength", WORN_RELIEF)
		stone.set_shader_parameter("slab_size", Vector2.ZERO)
		_worn = stone
	return _worn


## Returns the stone box `arrays` turned by `tilt` round its middle and moved by `patch`, with
## its lightmap UVs. The kit shader maps the texture in the mesh's own space, so the move shows
## another patch of stone; the look sits back by `patch`, so the tile stays in place.
static func _stone(arrays: Array, tilt: Basis, patch: Vector3, hint: Vector2i) -> ArrayMesh:
	# Packed arrays pass by reference: change copies, not the shared box.
	var box_points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var box_normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	var points: PackedVector3Array = box_points.duplicate()
	var normals: PackedVector3Array = box_normals.duplicate()
	for i: int in points.size():
		points[i] = tilt * points[i] + patch
		normals[i] = tilt * normals[i]
	var surface: Array = arrays.duplicate()
	surface[Mesh.ARRAY_VERTEX] = points
	surface[Mesh.ARRAY_NORMAL] = normals
	var mesh: ArrayMesh = ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, surface)
	mesh.lightmap_size_hint = hint
	return mesh


## Brings every tile back whole.
func reset(_restart: bool) -> void:
	_touched_at.fill(INF)
	for i: int in _solids.size():
		_solids[i].collision_layer = WorldQuery.SOLID_MASK
		_looks[i].visible = true
		_looks[i].position = _rests[i]
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
		var rest: Vector3 = _rests[i]
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
