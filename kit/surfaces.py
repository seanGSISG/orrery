"""Surface materials. The material custom property `surface` names the surface type."""

import bpy


def surface(id: str = "default") -> bpy.types.Material:
    """Returns the material for surface type `id`, made once per level. The Godot importer
    gives faces with this material the Surface `game/core/level/<id>_surface.tres`, and it
    makes one Solid for each surface type."""
    name = f"surface_{id}"
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material["surface"] = id
        material.use_backface_culling = True
    return material
