@tool
class_name LevelConverter
extends RefCounted
## Turns an imported level scene (a built .glb) into a Level. level_import.gd runs it after each
## import; tests run it on scenes built in code. Use it like this:
##     var converter: LevelConverter = LevelConverter.new()
##     var level: Level = converter.convert(scene)   # null when converter.errors is not empty
##
## The rules (docs/plan.md §4.3, docs/design/core-runtime.md §5):
## - Markers: a node whose "extras" metadata holds `orrery = {"type": T, ...}`. The marker of
##   type `level` sets the root's Level vars and goes away. A marker of any other type becomes an
##   instance of res://objects/T/T.tscn with the marker's name and transform. Each other key
##   sets the @export var of that name on the instance root, and the marker's children become
##   Marker3D children of the instance, in name order.
## - Collision: a mesh named `<name>-col` collides and stays visible as `<name>`; a mesh named
##   `<name>-colonly` collides and goes away. Their faces are grouped by the `surface` extra of
##   each material ("default" when it has none). Each group becomes one Solid, `solid_<surface>`,
##   with the Surface res://core/level/<surface>_surface.tres.
## - Lint: a level has exactly one `level`, one `start` and one `finish` marker.
## Each error names the level id and the node.

const LEVEL_SCRIPT: Script = preload("res://core/level/level.gd")
const SOLID_SCRIPT: Script = preload("res://core/level/solid.gd")
const OBJECT_SCENE: String = "res://objects/%s/%s.tscn"
const SURFACE: String = "res://core/level/%s_surface.tres"
const ONE_EACH: Array[String] = ["level", "start", "finish"]

## The problems of the last convert() call.
var errors: PackedStringArray = []

var _root: Node3D
var _id: String = ""


## Converts scene in place and returns it as a Level, or returns null and fills errors. The
## caller keeps ownership of scene in both cases.
func convert(scene: Node3D) -> Level:
	errors.clear()
	_root = scene
	_id = String(scene.name)
	var markers: Array[Node3D] = []
	var meshes: Array[MeshInstance3D] = []
	_find(scene, markers, meshes)
	var level_data: Dictionary = {}
	var counts: Dictionary[String, int] = {}
	for marker: Node3D in markers:
		var data: Dictionary = _marker_data(marker)
		var type: String = str(data.get("type", ""))
		var count: int = counts.get(type, 0)
		counts[type] = count + 1
		if type == "level":
			level_data = data
			_id = str(data.get("id", _id))
	for type: String in ONE_EACH:
		var count: int = counts.get(type, 0)
		if count != 1:
			_fail(scene, "needs exactly one `%s` marker, found %d" % [type, count])
	for marker: Node3D in markers:
		var data: Dictionary = _marker_data(marker)
		if str(data.get("type", "")) == "level":
			_remove(marker)
		else:
			_place(marker, data)
	_build_solids(meshes)
	scene.set_script(LEVEL_SCRIPT)
	_apply(scene, LEVEL_SCRIPT, level_data, "level")
	if not errors.is_empty():
		return null
	return scene as Level


## Collects the markers and the hinted meshes under node. It does not look inside markers.
func _find(node: Node, markers: Array[Node3D], meshes: Array[MeshInstance3D]) -> void:
	for child: Node in node.get_children():
		if child is Node3D and not _marker_data(child as Node3D).is_empty():
			markers.append(child as Node3D)
			continue
		if child is MeshInstance3D and _hint(child) != "":
			meshes.append(child as MeshInstance3D)
		_find(child, markers, meshes)


## Returns the `orrery` dictionary of a marker, or an empty one for other nodes.
func _marker_data(node: Node3D) -> Dictionary:
	var extras: Dictionary = node.get_meta(&"extras", {})
	var data: Variant = extras.get("orrery")
	if data is Dictionary:
		return data
	return {}


## Returns "-col" or "-colonly" when the node name ends with that hint, else "".
func _hint(node: Node) -> String:
	for hint: String in ["-colonly", "-col"]:
		if String(node.name).ends_with(hint):
			return hint
	return ""


## Puts an instance of the marker's object scene in the marker's place.
func _place(marker: Node3D, data: Dictionary) -> void:
	var type: String = str(data.get("type", ""))
	var path: String = OBJECT_SCENE % [type, type]
	if not ResourceLoader.exists(path):
		_fail(marker, "unknown marker type `%s`: %s does not exist" % [type, path])
		return
	var scene: PackedScene = load(path) as PackedScene
	var root: Node = scene.instantiate() if scene != null else null
	var object: Node3D = root as Node3D
	var script: Script = object.get_script() if object != null else null
	if script == null:
		_fail(marker, "%s must have a Node3D root with a LevelObject script" % path)
		if root != null:
			root.free()
		return
	_apply(object, script, data, String(marker.name))
	var parent: Node = marker.get_parent()
	var index: int = marker.get_index()
	parent.remove_child(marker)
	object.name = marker.name
	object.transform = marker.transform
	parent.add_child(object)
	parent.move_child(object, index)
	object.owner = _root
	var children: Array[Node] = marker.get_children()
	children.sort_custom(func(a: Node, b: Node) -> bool: return String(a.name) < String(b.name))
	for child: Node in children:
		var point: Marker3D = Marker3D.new()
		point.name = child.name
		point.transform = (child as Node3D).transform
		object.add_child(point)
		point.owner = _root
	marker.free()


## Writes each setting except `type` into the @export var of the same name on target. script
## is target's script; it lists the vars and their types.
func _apply(target: Object, script: Script, settings: Dictionary, node: String) -> void:
	var types: Dictionary[String, int] = {}
	for property: Dictionary in script.get_script_property_list():
		var usage: int = property["usage"]
		var property_name: String = property["name"]
		var type: int = property["type"]
		if usage & PROPERTY_USAGE_EDITOR:
			types[property_name] = type
	for key: Variant in settings:
		var name: String = str(key)
		if name == "type":
			continue
		if not types.has(name):
			_error(node, "unknown setting `%s`" % name)
			continue
		var value: Variant = _converted(settings[key], types[name])
		if value == null:
			var expected: String = type_string(types[name])
			_error(node, "setting `%s` must be %s, got %s" % [name, expected, settings[key]])
			continue
		target.set(name, value)


## Returns value converted to the Variant type, or null when it does not convert. Numbers
## arrive from glTF as floats, so a whole float converts to int too.
func _converted(value: Variant, type: int) -> Variant:
	var number: bool = value is float or value is int
	if type == TYPE_FLOAT and number:
		var real: float = value
		return real
	if type == TYPE_INT and number:
		var whole: float = value
		if whole == roundf(whole):
			return int(whole)
	if type == TYPE_BOOL and value is bool:
		return value
	if type == TYPE_STRING and value is String:
		return value
	if type == TYPE_STRING_NAME and value is String:
		var text: String = value
		return StringName(text)
	return null


## Makes one Solid for each surface type from the faces of the hinted meshes.
func _build_solids(meshes: Array[MeshInstance3D]) -> void:
	var faces: Dictionary[String, PackedVector3Array] = {}
	for mesh_node: MeshInstance3D in meshes:
		var hint: String = _hint(mesh_node)
		_add_faces(mesh_node, faces)
		if hint == "-col":
			mesh_node.name = String(mesh_node.name).trim_suffix(hint)
		elif mesh_node.get_child_count() > 0:
			_fail(mesh_node, "a -colonly mesh must not have children")
		else:
			_remove(mesh_node)
	for surface_id: String in faces:
		var path: String = SURFACE % surface_id
		if not ResourceLoader.exists(path):
			_fail(_root, "unknown surface `%s`: %s does not exist" % [surface_id, path])
			continue
		var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
		shape.set_faces(faces[surface_id])
		var collision: CollisionShape3D = CollisionShape3D.new()
		collision.name = "shape"
		collision.shape = shape
		var solid: StaticBody3D = StaticBody3D.new()
		solid.name = "solid_%s" % surface_id
		solid.set_script(SOLID_SCRIPT)
		solid.set("surface", load(path))
		solid.add_child(collision)
		_root.add_child(solid)
		solid.owner = _root
		collision.owner = _root


## Adds the faces of each mesh surface, in root space, to the group of its material's surface.
func _add_faces(mesh_node: MeshInstance3D, faces: Dictionary[String, PackedVector3Array]) -> void:
	var to_root: Transform3D = Transform3D.IDENTITY
	var node: Node = mesh_node
	while node != _root and node is Node3D:
		to_root = (node as Node3D).transform * to_root
		node = node.get_parent()
	var mesh: Mesh = mesh_node.mesh
	for i: int in mesh.get_surface_count():
		var arrays: Array = mesh.surface_get_arrays(i)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = PackedInt32Array()
		if arrays[Mesh.ARRAY_INDEX] != null:
			indices = arrays[Mesh.ARRAY_INDEX]
		var surface_id: String = _surface_id(mesh.surface_get_material(i))
		var group: PackedVector3Array = faces.get(surface_id, PackedVector3Array())
		if indices.is_empty():
			for vertex: Vector3 in vertices:
				group.append(to_root * vertex)
		else:
			for index: int in indices:
				group.append(to_root * vertices[index])
		faces[surface_id] = group


## Returns the `surface` extra of material, or "default".
func _surface_id(material: Material) -> String:
	if material == null:
		return "default"
	var extras: Dictionary = material.get_meta(&"extras", {})
	return str(extras.get("surface", "default"))


## Takes node out of the scene and frees it.
func _remove(node: Node) -> void:
	node.get_parent().remove_child(node)
	node.free()


## Records an error about node.
func _fail(node: Node, message: String) -> void:
	_error(String(node.name), message)


## Records an error about the node named node.
func _error(node: String, message: String) -> void:
	errors.append("level %s: node %s: %s" % [_id, node, message])
