"""Markers: empties that the Godot importer swaps for objects (game/levels/level_converter.gd).

A marker is an empty with the custom property `orrery = {"type": <type>, <setting>: <value>, ...}`.
The importer puts an instance of `game/objects/<type>/<type>.tscn` in its place, with the
marker's name and transform, and writes each setting into the `@export` var of the same name.
"""

from collections.abc import Sequence

import bpy
from mathutils import Vector

from kit.scene import Vec3, add_object, default_name, pose

Setting = bool | int | float | str


def marker(
    type: str,
    at: Vec3,
    rotation: Vec3 = (0.0, 0.0, 0.0),
    points: Sequence[Vec3] = (),
    name: str | None = None,
    **settings: Setting,
) -> bpy.types.Object:
    """Places a marker for the object `type` and returns its empty.

    at: the object origin. rotation: XYZ angles in degrees. points: world positions that the
    object reads as Marker3D children, in this order (for example a platform path). name: the
    Godot node name; the default is `<type>_00`, `<type>_01` ... settings: the object's
    `@export` values, as bool, int, float or str. Give positions and directions as points or
    as the rotation, never as settings: the export does not turn vector settings into Godot's
    axes.
    """
    for key, value in settings.items():
        if not isinstance(value, Setting):
            raise TypeError(
                f"kit.marker({type!r}): setting {key!r} must be bool, int, float or str, "
                f"got {value!r}; give positions as points"
            )
    obj = add_object(name or default_name(type))
    obj.empty_display_type = "PLAIN_AXES"
    obj.matrix_world = pose(at, rotation)
    obj["orrery"] = {"type": type, **settings}
    world_to_local = obj.matrix_world.inverted()
    # Point names end in two or more digits, all of one width, so that their name order is
    # the order of `points`.
    digits = max(2, len(str(len(points) - 1)))
    for i, point in enumerate(points):
        child = add_object(f"{obj.name}_p{i:0{digits}d}")
        child.empty_display_type = "PLAIN_AXES"
        child.empty_display_size = 0.25
        child.parent = obj
        child.location = world_to_local @ Vector(point)
    return obj


def level(
    title: str, par: float, gold: float, music: str = "", sky: str = ""
) -> bpy.types.Object:
    """Sets the level data: the title, the par and gold times in seconds, the music track and
    the sky preset (dawn, noon or dusk: `game/skies/<sky>.tres`). With no sky, the tier picks
    it: beginner dawn, intermediate noon, advanced dusk. Call it once in each level script.
    The build adds the id and the tier from the script path `levels/<tier>/<id>.py`."""
    return marker(
        "level",
        at=(0.0, 0.0, 0.0),
        name="level",
        title=title,
        par=par,
        gold=gold,
        music=music,
        sky=sky,
    )


def shot(name: str, at: Vec3, rotation: Vec3 = (0.0, 0.0, 0.0)) -> bpy.types.Object:
    """Places a named camera view (for example overview, start, finish, egg) for the gallery
    and the harness `screenshot {shot}` command. With rotation (0, 0, 0) it looks along +y;
    a positive x angle tilts it up."""
    return marker("shot", at=at, rotation=rotation, name=name)
