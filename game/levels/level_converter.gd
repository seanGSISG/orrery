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
##   type `level` sets the root's Level vars and goes away. A marker of type `shot` becomes a
##   Camera3D with the marker's name and transform, for the harness `screenshot {shot}` command.
##   A marker of any other type becomes an instance of res://objects/T/T.tscn with the marker's
##   name and transform. Each other key sets the @export var of that name on the instance root,
##   and the marker's children become Marker3D children of the instance, in name order.
## - Collision: a mesh named `<name>-col` collides and stays visible as `<name>`; a mesh named
##   `<name>-colonly` collides and goes away. Their faces are grouped by the `surface` extra of
##   each material ("default" when it has none). Each group becomes one Solid, `solid_<surface>`,
##   with the Surface res://core/level/<surface>_surface.tres.
## - Lint: a level has exactly one `level`, one `start` and one `finish` marker. A level outside
##   levels/test/ (tier `test`) also has the gallery shots `overview`, `start`, `finish` and
##   `egg` (docs/design/visual-quality.md §7).
## - Route lint (#14): each `route` marker has the kind first_run or expert, a level has at most
##   one route of each kind, and a level outside levels/test/ has a first_run route.
## - Light: a level without its own WorldEnvironment and DirectionalLight3D gets a stand-in
##   rig: one sun with shadows and a procedural sky with AgX tonemapping. The level's `sky`
##   picks dawn, noon or dusk; without one, the tier does (beginner dawn, intermediate noon,
##   advanced dusk, others noon). The look baseline (#24) replaces it with the real skies.
## Each error names the level id and the node.

const LEVEL_SCRIPT: Script = preload("res://core/level/level.gd")
const SOLID_SCRIPT: Script = preload("res://core/level/solid.gd")
const OBJECT_SCENE: String = "res://objects/%s/%s.tscn"
const SURFACE: String = "res://core/level/%s_surface.tres"
const ONE_EACH: Array[String] = ["level", "start", "finish"]
const GALLERY_SHOTS: Array[String] = ["overview", "start", "finish", "egg"]
## The stand-in light rigs by name: sun elevation in degrees, sun colour and sky colours.
const SUN_ELEVATION: Dictionary[String, float] = {"dawn": 20.0, "noon": 60.0, "dusk": 25.0}
const SUN_COLOR: Dictionary[String, Color] = {
	"dawn": Color(1.0, 0.82, 0.66),
	"noon": Color(1.0, 0.97, 0.92),
	"dusk": Color(1.0, 0.68, 0.48),
}
const SKY_TOP: Dictionary[String, Color] = {
	"dawn": Color(0.3, 0.42, 0.65),
	"noon": Color(0.24, 0.45, 0.82),
	"dusk": Color(0.1, 0.13, 0.3),
}
const SKY_HORIZON: Dictionary[String, Color] = {
	"dawn": Color(0.92, 0.74, 0.6),
	"noon": Color(0.7, 0.8, 0.9),
	"dusk": Color(0.85, 0.55, 0.45),
}
const TIER_RIG: Dictionary[String, String] = {
	"beginner": "dawn",
	"intermediate": "noon",
	"advanced": "dusk",
}

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
	var shots: Array[String] = []
	for marker: Node3D in markers:
		var data: Dictionary = _marker_data(marker)
		var type: String = str(data.get("type", ""))
		var count: int = counts.get(type, 0)
		counts[type] = count + 1
		if type == "level":
			level_data = data
			_id = str(data.get("id", _id))
		elif type == "shot":
			shots.append(String(marker.name))
	for type: String in ONE_EACH:
		var count: int = counts.get(type, 0)
		if count != 1:
			_fail(scene, "needs exactly one `%s` marker, found %d" % [type, count])
	if str(level_data.get("tier", "")) != "test":
		for shot: String in GALLERY_SHOTS:
			if shot not in shots:
				_fail(scene, "needs the gallery shot `%s`" % shot)
	_check_routes(markers, str(level_data.get("tier", "")))
	for marker: Node3D in markers:
		var data: Dictionary = _marker_data(marker)
		var type: String = str(data.get("type", ""))
		if type == "level":
			_remove(marker)
		elif type == "shot":
			_place_shot(marker, data)
		else:
			_place(marker, data)
	_build_solids(meshes)
	_add_light_rig(level_data)
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


## The route lint (#14) on the markers of a level of tier.
func _check_routes(markers: Array[Node3D], tier: String) -> void:
	var kinds: Array[StringName] = []
	for marker: Node3D in markers:
		var data: Dictionary = _marker_data(marker)
		if str(data.get("type", "")) != "route":
			continue
		var kind: StringName = StringName(str(data.get("kind", "")))
		if kind not in Route.KINDS:
			_fail(marker, "a `route` needs the kind first_run or expert, got `%s`" % kind)
		elif kind in kinds:
			_fail(marker, "a second `%s` route" % kind)
		kinds.append(kind)
	if tier != "test" and &"first_run" not in kinds:
		_fail(_root, "needs a `route` marker of kind first_run (objects/route/route.gd)")


## Puts a Camera3D with the marker's name and transform in the marker's place. It looks along
## the marker's -z axis in Godot, which is the marker's +y axis in Blender.
func _place_shot(marker: Node3D, data: Dictionary) -> void:
	if data.size() > 1:
		_fail(marker, "a `shot` marker has no settings")
	var camera: Camera3D = Camera3D.new()
	var parent: Node = marker.get_parent()
	var index: int = marker.get_index()
	parent.remove_child(marker)
	camera.name = marker.name
	camera.transform = marker.transform
	parent.add_child(camera)
	parent.move_child(camera, index)
	camera.owner = _root
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


## Adds the stand-in sun and sky when the level has no WorldEnvironment and no
## DirectionalLight3D of its own.
func _add_light_rig(level_data: Dictionary) -> void:
	for type: String in ["WorldEnvironment", "DirectionalLight3D"]:
		if not _root.find_children("*", type, true, false).is_empty():
			return
	var rig: String = str(level_data.get("sky", ""))
	if not SUN_ELEVATION.has(rig):
		rig = TIER_RIG.get(str(level_data.get("tier", "")), "noon")
	var material: ProceduralSkyMaterial = ProceduralSkyMaterial.new()
	material.sky_top_color = SKY_TOP[rig]
	material.sky_horizon_color = SKY_HORIZON[rig]
	material.ground_horizon_color = SKY_HORIZON[rig]
	var sky: Sky = Sky.new()
	sky.sky_material = material
	var environment: Environment = Environment.new()
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky
	environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	# A light haze for the presets that turn volumetric fog on; the default washes out the sky.
	environment.volumetric_fog_density = 0.002
	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = "sky"
	world.environment = environment
	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.name = "sun"
	sun.shadow_enabled = true
	sun.light_color = SUN_COLOR[rig]
	sun.rotation_degrees = Vector3(-SUN_ELEVATION[rig], 35.0, 0.0)
	for node: Node in [world, sun]:
		_root.add_child(node)
		node.owner = _root
