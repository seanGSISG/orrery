class_name WorldQuery
extends RefCounted
## The only code that asks Jolt about the level. It is read-only, and it works outside
## physics frames, so a run can step many ticks in one frame. LevelRun makes one and gives
## it to Marble.step(). Positions are world positions.

## Physics layer masks; project.godot names layer 1 `solid` and layer 2 `trigger`.
const SOLID_MASK: int = 1
const TRIGGER_MASK: int = 2
## Two contacts are one when their normals agree this closely.
const SAME_NORMAL: float = 0.9998

var _space: PhysicsDirectSpaceState3D
var _radius: float
var _margin: float
var _query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()


## Queries space with a sphere of radius; contacts count up to margin outside the surface.
func _init(space: PhysicsDirectSpaceState3D, radius: float, margin: float) -> void:
	_space = space
	_radius = radius
	_margin = margin
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = radius
	_query.shape = sphere


## Returns the contacts of the sphere at center with every Solid, one per distinct normal of
## each Solid. So a flush object keeps its own contact beside the floor's.
func contacts(center: Vector3) -> Array[Contact]:
	_set_query(center, _margin, Vector3.ZERO, SOLID_MASK, false)
	var solids: Array[Solid] = []
	var rids: Array[RID] = []
	# One body can fill several entries (F4), so ask for more than the Solids we expect.
	for hit: Dictionary in _space.intersect_shape(_query, 32):
		var rid: RID = hit["rid"]
		if rids.has(rid):
			continue
		rids.append(rid)
		var collider: Object = hit["collider"]
		var solid: Solid = collider as Solid
		if solid != null:
			solids.append(solid)
	var out: Array[Contact] = []
	# collide_shape gives points only (F1), so query each Solid alone, with every other body
	# excluded (also a body that is not a Solid), to know its owner.
	for solid: Solid in solids:
		var others: Array[RID] = rids.duplicate()
		others.erase(solid.get_rid())
		_query.exclude = others
		var pairs: Array[Vector3] = _space.collide_shape(_query, 16)
		var own: Array[Contact] = []
		for k: int in range(0, pairs.size(), 2):
			_add_contact(own, center, pairs[k], pairs[k + 1], solid)
		out.append_array(own)
	_query.exclude = []
	return out


## Returns the safe fraction (0..1) of motion before the sphere at center hits a Solid.
## A Solid that the sphere already overlaps does not stop it.
func sweep(center: Vector3, motion: Vector3) -> float:
	_set_query(center, 0.0, motion, SOLID_MASK, false)
	return _space.cast_motion(_query)[0]


## Returns the objects whose triggers overlap the sphere at center.
func overlaps(center: Vector3) -> Array[LevelObject]:
	_set_query(center, 0.0, Vector3.ZERO, TRIGGER_MASK, true)
	var out: Array[LevelObject] = []
	for hit: Dictionary in _space.intersect_shape(_query, 16):
		var collider: Object = hit["collider"]
		var area: Area3D = collider as Area3D
		var object: LevelObject = area.owner as LevelObject if area != null else null
		if object != null and not out.has(object):
			out.append(object)
	return out


func _set_query(center: Vector3, margin: float, motion: Vector3, mask: int, areas: bool) -> void:
	_query.transform = Transform3D(Basis.IDENTITY, center)
	_query.margin = margin
	_query.motion = motion
	_query.collision_mask = mask
	_query.collide_with_areas = areas
	_query.collide_with_bodies = not areas


## Adds the contact at point on solid to out, which holds only that Solid's contacts. deepest
## is the pair's other point: the point of the sphere, grown by the margin, that lies deepest
## past the surface. Of two contacts with almost the same normal, only the deeper one stays:
## within about 2 mm of an internal edge, Jolt also gives the neighbour triangle's edge point,
## with a normal tilted by up to 0.01 rad.
func _add_contact(
	out: Array[Contact], center: Vector3, deepest: Vector3, point: Vector3, solid: Solid
) -> void:
	var offset: Vector3 = center - point
	var distance: float = offset.length()
	if distance < 0.000001:
		return
	var normal: Vector3 = offset / distance
	var depth: float = _radius - distance
	# A mover can push a convex Solid over the centre. Then deepest lies on the far side of the
	# surface from the centre, and the way out is from the centre toward point (F23).
	if (point - deepest).dot(normal) < -0.5 * _radius:
		normal = -normal
		depth = _radius + distance
	var contact: Contact = null
	for known: Contact in out:
		if known.normal.dot(normal) > SAME_NORMAL:
			if depth <= known.depth:
				return
			contact = known
	if contact == null:
		contact = Contact.new()
		out.append(contact)
	contact.point = point
	contact.normal = normal
	contact.depth = depth
	contact.velocity = solid.velocity_at(point)
	contact.surface = solid.surface if solid.surface != null else Solid.DEFAULT_SURFACE
	contact.object = solid.owner as LevelObject
