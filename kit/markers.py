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
# Point names end in two digits, so that their name order is the order of `points`.
MAX_POINTS = 100


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
    if len(points) > MAX_POINTS:
        raise ValueError(f"kit.marker({type!r}): at most {MAX_POINTS} points")
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
    for i, point in enumerate(points):
        child = add_object(f"{obj.name}_p{i:02d}")
        child.empty_display_type = "PLAIN_AXES"
        child.empty_display_size = 0.25
        child.parent = obj
        child.location = world_to_local @ Vector(point)
    return obj


def level(
    title: str, par: float, gold: float, music: str = "", sky: str = ""
) -> bpy.types.Object:
    """Sets the level data: the title, the par and gold times in seconds, the music track and
    the sky preset. Call it once in each level script. The build adds the id and the tier from
    the script path `levels/<tier>/<id>.py`."""
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
