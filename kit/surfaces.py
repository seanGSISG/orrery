"""Kit materials. Two custom properties tell the Godot importer what a face is: `material`
names its look and `surface` names its surface type."""

import bpy

# The looks in the game's material library (game/materials/kit_materials.gd).
MATERIALS = ("limestone", "brass", "gold")


def surface(id: str = "default", material: str = "limestone") -> bpy.types.Material:
    """Returns the kit material `material` on surface type `id`, made once per level.

    material: limestone (track decks), brass (trim and borders) or gold (inlays). The Godot
    importer gives the faces the look `game/materials/<set>/<material>.tres`. id: the importer
    gives the faces the Surface `game/core/level/<id>_surface.tres`, and it makes one Solid
    for each surface type.
    """
    if material not in MATERIALS:
        raise ValueError(
            f"kit.surface: no material {material!r}; use one of {MATERIALS}"
        )
    name = f"{material}_{id}"
    found = bpy.data.materials.get(name)
    if found is None:
        found = bpy.data.materials.new(name)
        found["surface"] = id
        found["material"] = material
        found.use_backface_culling = True
    return found
