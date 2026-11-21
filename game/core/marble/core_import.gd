@tool
extends EditorScenePostImport
## The post-import script of the marble's brass core, res://core/marble/built/orrery_core.glb.
## The build (`just build-marble`) names it in the .glb.import file. The core casts no sun
## shadow and takes none: the shadow sphere of the glass skin casts the marble's shadow, and
## the core is inside that sphere.


## Returns scene with shadow casting off on each mesh and shadow receiving off on each
## material.
func _post_import(scene: Node) -> Object:
	for node: Node in scene.find_children("*", "MeshInstance3D", true, false):
		var instance: MeshInstance3D = node as MeshInstance3D
		instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for surface: int in instance.mesh.get_surface_count():
			var material: BaseMaterial3D = instance.mesh.surface_get_material(surface) as BaseMaterial3D
			material.disable_receive_shadows = true
	return scene
