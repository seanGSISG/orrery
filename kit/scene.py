"""Helpers that add objects to the level scene. Kit modules use them; level scripts do not."""

import math

import bpy
from mathutils import Euler, Matrix, Vector

Vec3 = tuple[float, float, float]

_counts: dict[str, int] = {}


def default_name(prefix: str, suffix: str = "") -> str:
    """Returns the next name `<prefix>_00`, `<prefix>_01` ... for an object with no name. The
    object name `<name><suffix>` is free."""
    while True:
        n = _counts.get(prefix, 0)
        _counts[prefix] = n + 1
        name = f"{prefix}_{n:02d}"
        if f"{name}{suffix}" not in bpy.data.objects:
            return name


def add_object(name: str, data: bpy.types.Mesh | None = None) -> bpy.types.Object:
    """Adds an object (an empty when data is None) to the scene. Raises when the name is taken,
    because Blender would rename it and the Godot node name would change."""
    if name in bpy.data.objects:
        raise ValueError(f"kit: the name {name!r} is already used in this level")
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def pose(at: Vec3, rotation: Vec3) -> Matrix:
    """Returns the world matrix for a position and an XYZ rotation in degrees."""
    return Matrix.LocRotScale(
        Vector(at), Euler([math.radians(a) for a in rotation]), None
    )
