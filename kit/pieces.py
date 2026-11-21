"""Track pieces. Each piece is a mesh named `<name>-col`, so the Godot importer makes it collide.

A piece starts at `at`, the centre of its front top edge, and runs `length` m forward along +y,
turned by `yaw` degrees around z. To chain pieces, start the next piece where the last one ends.

A piece is `material` (limestone) with an edge trim of `trim` (brass) along its two long edges.
The trim is a second mesh, `<name>_trim`. It does not collide, so it does not change how the
marble rolls. Give `trim=""` for an edge that touches another piece.
"""

import math

import bmesh
import bpy

from kit.scene import Vec3, add_object, default_name
from kit.surfaces import surface as surface_material

THICKNESS = 0.5
# The edge trim: an angle section that covers TRIM_WIDTH of the top and TRIM_DROP of the side.
# It stands TRIM_PROUD above the stone, and its outer corner has a TRIM_BEVEL chamfer.
TRIM_WIDTH = 0.14
TRIM_DROP = 0.12
TRIM_PROUD = 0.003
TRIM_BEVEL = 0.01
# The hidden faces of the trim lie this deep in the stone.
TRIM_SUNK = 0.01


def track(
    at: Vec3,
    width: float = 4.0,
    length: float = 8.0,
    yaw: float = 0.0,
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
    trim: str = "brass",
) -> bpy.types.Object:
    """Adds a flat track piece: a slab THICKNESS m thick whose top face is at the height of
    `at`. surface: the surface type of all its faces. material, trim: the kit materials of
    the slab and of its edge trim; `trim=""` leaves the trim out."""
    name = name or default_name("track", "-col")
    return _slab(name, at, width, length, 0.0, yaw, surface, material, trim)


def ramp(
    at: Vec3,
    width: float = 4.0,
    length: float = 8.0,
    rise: float = 2.0,
    yaw: float = 0.0,
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
    trim: str = "brass",
) -> bpy.types.Object:
    """Adds a ramp: a slab THICKNESS m thick whose top face climbs `rise` m (down when
    negative) over `length` m. The next piece starts at `at` + (0, length, rise) for yaw 0.
    surface, material and trim are as for track()."""
    name = name or default_name("ramp", "-col")
    return _slab(name, at, width, length, rise, yaw, surface, material, trim)


def _slab(
    name: str,
    at: Vec3,
    width: float,
    length: float,
    rise: float,
    yaw: float,
    surface: str,
    material: str,
    trim: str,
) -> bpy.types.Object:
    """Builds a closed slab mesh with outward faces, so that the trimesh collides on top, and
    its edge trim."""
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
    obj = _finish(bm, name, f"{name}-col", surface_material(surface, material))
    obj.location = at
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw))
    if trim:
        edge = _trim(
            f"{name}_trim", half, length, rise, surface_material("default", trim)
        )
        edge.location = at
        edge.rotation_euler = obj.rotation_euler
    return obj


def _trim(
    name: str, half: float, length: float, rise: float, material: bpy.types.Material
) -> bpy.types.Object:
    """Builds the edge trim of a slab: one angle section along each long edge, from the
    front of the slab to its back. The section caps the top corner of the slab."""
    out = half + TRIM_PROUD
    section = [
        (half - TRIM_WIDTH, TRIM_PROUD),
        (out - TRIM_BEVEL, TRIM_PROUD),
        (out, TRIM_PROUD - TRIM_BEVEL),
        (out, -TRIM_DROP),
        (half - TRIM_SUNK, -TRIM_DROP),
        (half - TRIM_SUNK, -TRIM_SUNK),
        (half - TRIM_WIDTH, -TRIM_SUNK),
    ]
    bm = bmesh.new()
    for side in (-1.0, 1.0):
        front = [bm.verts.new((side * x, 0.0, z)) for x, z in section]
        back = [bm.verts.new((side * x, length, z + rise)) for x, z in section]
        bm.faces.new(front)
        bm.faces.new(back)
        for i in range(len(section)):
            j = (i + 1) % len(section)
            bm.faces.new((front[i], front[j], back[j], back[i]))
    return _finish(bm, name, name, material)


def _finish(
    bm: bmesh.types.BMesh, mesh_name: str, name: str, material: bpy.types.Material
) -> bpy.types.Object:
    """Turns bm into the object `name` with outward faces and one material, and frees bm."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    return add_object(name, mesh)
