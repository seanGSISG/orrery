"""Track pieces. Each piece is a mesh named `<name>-col`, so the Godot importer makes it collide.

A piece starts at `at`, the centre of its front top edge, and runs `length` m forward along +y,
turned by `yaw` degrees around z. To chain pieces, start the next piece where the last one ends.
"""

import math

import bmesh
import bpy

from kit.scene import Vec3, add_object, default_name
from kit.surfaces import surface as surface_material

THICKNESS = 0.5


def track(
    at: Vec3,
    width: float = 4.0,
    length: float = 8.0,
    yaw: float = 0.0,
    surface: str = "default",
    name: str | None = None,
) -> bpy.types.Object:
    """Adds a flat track piece: a slab THICKNESS m thick whose top face is at the height of
    `at`. surface: the surface type of all its faces."""
    return _slab(
        name or default_name("track", "-col"), at, width, length, 0.0, yaw, surface
    )


def ramp(
    at: Vec3,
    width: float = 4.0,
    length: float = 8.0,
    rise: float = 2.0,
    yaw: float = 0.0,
    surface: str = "default",
    name: str | None = None,
) -> bpy.types.Object:
    """Adds a ramp: a slab THICKNESS m thick whose top face climbs `rise` m (down when
    negative) over `length` m. The next piece starts at `at` + (0, length, rise) for yaw 0."""
    return _slab(
        name or default_name("ramp", "-col"), at, width, length, rise, yaw, surface
    )


def _slab(
    name: str,
    at: Vec3,
    width: float,
    length: float,
    rise: float,
    yaw: float,
    surface: str,
) -> bpy.types.Object:
    """Builds a closed slab mesh with outward faces, so that the trimesh collides on top."""
    bm = bmesh.new()
    half = width / 2
    profile = [
        (0.0, 0.0),
        (length, rise),
        (length, rise - THICKNESS),
        (0.0, -THICKNESS),
    ]
    left = [bm.verts.new((-half, y, z)) for y, z in profile]
    right = [bm.verts.new((half, y, z)) for y, z in profile]
    bm.faces.new(left)
    bm.faces.new(right)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((left[i], left[j], right[j], right[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(surface_material(surface))
    obj = add_object(f"{name}-col", mesh)
    obj.location = at
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw))
    return obj
