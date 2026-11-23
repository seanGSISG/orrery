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
##   and the marker's children become Marker3D children of the instance, in name order. A
##   Material export takes a kit material name: an unknown name fails the import.
## - Collision: a mesh named `<name>-col` collides and stays visible as `<name>`; a mesh named
##   `<name>-colonly` collides and goes away. Their faces are grouped by the `surface` extra of
##   each material ("default" when it has none). Each group becomes one Solid, `solid_<surface>`,
##   with the Surface res://core/level/<surface>_surface.tres.
## - Far scenery: a mesh named `<name>-far` stays visible as `<name>`, but it stays out of the
##   lightmap, gets no reflection probe and casts no shadow: scenery past the play space, such
##   as the far town round an Ascent zone. (Its shadows were soft blobs on the land.)
## - Lint: a level has exactly one `level`, one `start` and one `finish` marker. A level outside
##   levels/test/ (tier `test`) also has the gallery shots `overview`, `start`, `finish` and
##   `egg` (docs/design/visual-quality.md §7).
## - Route lint (#14): each `route` marker has the kind first_run or expert, a level has at most
##   one route of each kind, and a level outside levels/test/ has a first_run route.
## - Materials: a mesh surface whose material has the `material` extra (a kit material name,
##   kit/surfaces.py) gets the material that KitMaterials.find() returns for it.
## - Light: a level without its own WorldEnvironment and DirectionalLight3D gets them from a
##   SkyPreset, res://skies/<name>.tres: one sun with shadows, `sun`, and the sky, `sky`. The
##   level's `sky` names the preset; without one, the tier does (beginner dawn, intermediate
##   noon, advanced dusk, others dawn).
## - Reflections: static ReflectionProbes, `probe_<n>`, cover the level's meshes. Each is at
##   most PROBE_SIZE m on a side (docs/design/visual-quality.md §4).
## - Lightmap: every level gets one LightmapGI, `lightmap`, with the bake settings of
##   docs/design/visual-quality.md §4. When `just bake <id>` has written LIGHTMAP_DATA for the
##   level id, the LightmapGI uses it.
## Each error names the level id and the node.

const LEVEL_SCRIPT: Script = preload("res://core/level/level.gd")
const SOLID_SCRIPT: Script = preload("res://core/level/solid.gd")
const OBJECT_SCENE: String = "res://objects/%s/%s.tscn"
const SURFACE: String = "res://core/level/%s_surface.tres"
const ONE_EACH: Array[String] = ["level", "start", "finish"]
const GALLERY_SHOTS: Array[String] = ["overview", "start", "finish", "egg"]
## The baked lightmap of a level id. `just bake` writes it; the lightmap baker plugin uses it.
const LIGHTMAP_DATA: String = "res://levels/lightmaps/%s.lmbake"
## The sky preset of a name, and the name for each tier. Other tiers get DEFAULT_SKY.
const SKY: String = "res://skies/%s.tres"
const TIER_SKY: Dictionary[String, String] = {
	"beginner": "dawn",
	"intermediate": "noon",
	"advanced": "dusk",
}
const DEFAULT_SKY: String = "dawn"
## The longest side of a reflection probe, and how far the probes reach past the meshes, m.
const PROBE_SIZE: float = 30.0
const PROBE_MARGIN: float = 3.0
## How far above the highest mesh of its cell a reflection probe looks from, m.
const PROBE_HEIGHT: float = 2.0

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
	var visible: Array[MeshInstance3D] = _build_solids(meshes)
	_apply_materials(visible)
	_add_light_rig(level_data)
	_add_probes(visible.filter(_lit))
	_add_lightmap()
	scene.set_script(LEVEL_SCRIPT)
	_apply(scene, LEVEL_SCRIPT, level_data, "level")
	if not errors.is_empty():
		return null
	return scene as Level


## Collects the markers and the meshes under node. It does not look inside markers.
func _find(node: Node, markers: Array[Node3D], meshes: Array[MeshInstance3D]) -> void:
	for child: Node in node.get_children():
		if child is Node3D and not _marker_data(child as Node3D).is_empty():
			markers.append(child as Node3D)
			continue
		if child is MeshInstance3D:
			meshes.append(child as MeshInstance3D)
		_find(child, markers, meshes)


## Returns the `orrery` dictionary of a marker, or an empty one for other nodes.
func _marker_data(node: Node3D) -> Dictionary:
	var extras: Dictionary = node.get_meta(&"extras", {})
	var data: Variant = extras.get("orrery")
	if data is Dictionary:
		return data
	return {}


## Returns "-col", "-colonly" or "-far" when the node name ends with that hint, else "".
func _hint(node: Node) -> String:
	for hint: String in ["-colonly", "-col", "-far"]:
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
## the marker's -z axis in Godot, which is the marker's +y axis in Blender, as far as the play
## camera sees (FollowCamera.FAR).
func _place_shot(marker: Node3D, data: Dictionary) -> void:
	if data.size() > 1:
		_fail(marker, "a `shot` marker has no settings")
	var camera: Camera3D = Camera3D.new()
	camera.far = FollowCamera.FAR
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
			var expected: String = (
				"a kit material name" if types[name] == TYPE_OBJECT else type_string(types[name])
			)
			_error(node, "setting `%s` must be %s, got %s" % [name, expected, settings[key]])
			continue
		target.set(name, value)


## Returns value converted to the Variant type, or null when it does not convert. Numbers
## arrive from glTF as floats, so a whole float converts to int too. A String converts to an
## Object (a Material export) as the kit material of that name, or null when there is none.
func _converted(value: Variant, type: int) -> Variant:
	var number: bool = value is float or value is int
	if type == TYPE_FLOAT and number:
		var real: float = value
		return real
	if type == TYPE_INT and number:
		var whole: float = value
		if whole == roundf(whole):
			return int(whole)
	if type == TYPE_OBJECT and value is String:
		var kit_name: String = value
		return KitMaterials.find(kit_name)
	var strings: bool = value is String and type in [TYPE_STRING, TYPE_STRING_NAME]
	if strings or (type == TYPE_BOOL and value is bool):
		return type_convert(value, type)
	return null


## Makes one Solid for each surface type from the faces of the hinted meshes. Returns the
## meshes that stay in the level.
func _build_solids(meshes: Array[MeshInstance3D]) -> Array[MeshInstance3D]:
	var visible: Array[MeshInstance3D] = []
	var faces: Dictionary[String, PackedVector3Array] = {}
	for mesh_node: MeshInstance3D in meshes:
		var hint: String = _hint(mesh_node)
		if hint == "":
			visible.append(mesh_node)
			continue
		if hint == "-far":
			mesh_node.name = String(mesh_node.name).trim_suffix(hint)
			mesh_node.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
			mesh_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			visible.append(mesh_node)
			continue
		_add_faces(mesh_node, faces)
		if hint == "-col":
			mesh_node.name = String(mesh_node.name).trim_suffix(hint)
			visible.append(mesh_node)
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
	return visible


## Returns true for a mesh in the lit play space: every mesh but far scenery.
func _lit(mesh_node: MeshInstance3D) -> bool:
	return mesh_node.gi_mode != GeometryInstance3D.GI_MODE_DISABLED


## Adds the faces of each mesh surface, in root space, to the group of its material's surface.
func _add_faces(mesh_node: MeshInstance3D, faces: Dictionary[String, PackedVector3Array]) -> void:
	var to_root: Transform3D = _to_root(mesh_node)
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


## Returns the transform from the space of node to the space of the level root.
func _to_root(node: Node3D) -> Transform3D:
	var to_root: Transform3D = Transform3D.IDENTITY
	var above: Node = node
	while above != _root and above is Node3D:
		to_root = (above as Node3D).transform * to_root
		above = above.get_parent()
	return to_root


## Returns the `surface` extra of material, or "default".
func _surface_id(material: Material) -> String:
	return _extra(material, "surface", "default")


## Returns the extra `key` of material as text, or fallback when it has none.
func _extra(material: Material, key: String, fallback: String) -> String:
	if material == null:
		return fallback
	var extras: Dictionary = material.get_meta(&"extras", {})
	return str(extras.get(key, fallback))


## Gives each mesh surface with a kit material name the material of the library.
func _apply_materials(meshes: Array[MeshInstance3D]) -> void:
	for mesh_node: MeshInstance3D in meshes:
		var mesh: Mesh = mesh_node.mesh
		if mesh == null:
			continue
		for i: int in mesh.get_surface_count():
			var kit_name: String = _extra(mesh.surface_get_material(i), "material", "")
			if kit_name == "":
				continue
			var material: Material = KitMaterials.find(kit_name)
			if material == null:
				_fail(mesh_node, "unknown kit material `%s` (game/materials/)" % kit_name)
				continue
			mesh.surface_set_material(i, material)


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


## Adds the sun and the sky of the level's SkyPreset when the level has no WorldEnvironment
## and no DirectionalLight3D of its own.
func _add_light_rig(level_data: Dictionary) -> void:
	for type: String in ["WorldEnvironment", "DirectionalLight3D"]:
		if not _root.find_children("*", type, true, false).is_empty():
			return
	var sky_name: String = str(level_data.get("sky", ""))
	if sky_name == "":
		sky_name = TIER_SKY.get(str(level_data.get("tier", "")), DEFAULT_SKY)
	var path: String = SKY % sky_name
	var preset: SkyPreset = load(path) as SkyPreset if ResourceLoader.exists(path) else null
	if preset == null:
		_fail(_root, "unknown sky `%s`: %s is not a SkyPreset" % [sky_name, path])
		return
	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = "sky"
	world.environment = preset.environment()
	var sun: DirectionalLight3D = preset.sun()
	sun.name = "sun"
	for node: Node in [world, sun]:
		_root.add_child(node)
		node.owner = _root


## Adds static reflection probes in a grid over the bounds of the meshes. A grid cell with no
## mesh in it gets no probe. A probe looks from PROBE_HEIGHT m above the highest mesh of its
## cell, so that it sees the track from above and the open sky.
func _add_probes(meshes: Array[MeshInstance3D]) -> void:
	var boxes: Array[AABB] = []
	for mesh_node: MeshInstance3D in meshes:
		boxes.append(_to_root(mesh_node) * mesh_node.get_aabb())
	if boxes.is_empty():
		return
	var bounds: AABB = boxes[0]
	for box: AABB in boxes:
		bounds = bounds.merge(box)
	bounds = bounds.grow(PROBE_MARGIN)
	var counts: Vector3i = Vector3i((bounds.size / PROBE_SIZE).ceil()).maxi(1)
	var cell: Vector3 = bounds.size / Vector3(counts)
	var number: int = 0
	for x: int in counts.x:
		for y: int in counts.y:
			for z: int in counts.z:
				var area: AABB = AABB(bounds.position + cell * Vector3(x, y, z), cell)
				var inside: Array[AABB] = boxes.filter(area.intersects)
				if inside.is_empty():
					continue
				var top: float = area.position.y
				for box: AABB in inside:
					top = maxf(top, minf(box.end.y, area.end.y))
				var probe: ReflectionProbe = ReflectionProbe.new()
				probe.name = "probe_%d" % number
				probe.update_mode = ReflectionProbe.UPDATE_ONCE
				# Reflections only: the lightmap and its probes give the ambient light.
				probe.ambient_mode = ReflectionProbe.AMBIENT_DISABLED
				probe.size = cell
				probe.position = area.get_center()
				var eye: float = minf(top + PROBE_HEIGHT, area.end.y - 0.1)
				probe.origin_offset = Vector3(0.0, eye - probe.position.y, 0.0)
				_root.add_child(probe)
				probe.owner = _root
				number += 1


## Adds the LightmapGI with the bake settings, and its committed bake when one exists.
func _add_lightmap() -> void:
	var lightmap: LightmapGI = LightmapGI.new()
	lightmap.name = "lightmap"
	lightmap.quality = LightmapGI.BAKE_QUALITY_ULTRA
	lightmap.bounces = 4
	lightmap.bounce_indirect_energy = 1.0
	lightmap.directional = false
	lightmap.supersampling = true
	lightmap.supersampling_factor = 2.0
	lightmap.use_denoiser = true
	lightmap.denoiser_strength = 0.1
	lightmap.denoiser_range = 10
	lightmap.environment_mode = LightmapGI.ENVIRONMENT_MODE_SCENE
	lightmap.interior = false
	lightmap.shadowmask_mode = LightmapGIData.SHADOWMASK_MODE_REPLACE
	lightmap.generate_probes_subdiv = LightmapGI.GENERATE_PROBES_SUBDIV_8
	var data_path: String = LIGHTMAP_DATA % _id
	if ResourceLoader.exists(data_path):
		lightmap.light_data = load(data_path) as LightmapGIData
	_root.add_child(lightmap)
	lightmap.owner = _root
