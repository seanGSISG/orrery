"""Props: decoration meshes from `assets/props/<name>.glb` (Git LFS).

A prop is a model that `just prop-cleanup` has made real-size, with its origin at the centre
of its base. It does not collide, so it never changes how the marble rolls; the marble rolls
only on our own kit pieces. A prop can have a simple collider: a box or a cylinder around it,
a `-colonly` mesh that the Godot importer turns into collision and then removes.
"""

from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

from kit.scene import Vec3, add_object, default_name, pose
from kit.surfaces import surface

# Level scripts read props from here; tests point it at a temporary folder.
PROPS = Path(__file__).resolve().parents[1] / "assets" / "props"
COLLIDERS = ("none", "box", "cylinder")
CYLINDER_SIDES = 16


def prop(
    name: str,
    at: Vec3,
    rotation: Vec3 = (0.0, 0.0, 0.0),
    collider: str = "none",
) -> bpy.types.Object:
    """Places the prop `assets/props/<name>.glb` with its base centre at `at` and returns its
    object, `prop_<name>_00`, `prop_<name>_01` ... rotation: XYZ angles in degrees.
    collider: none, box or cylinder (around the prop's bounds; it collides on surface type
    default). Props of one name share one mesh."""
    if collider not in COLLIDERS:
        raise ValueError(f"kit.prop({name!r}): collider must be one of {COLLIDERS}")
    mesh = _mesh(name)
    obj = add_object(default_name(f"prop_{name}"), mesh)
    obj.matrix_world = pose(at, rotation)
    if collider != "none":
        shape = add_object(f"{obj.name}_collider-colonly", _collider(mesh, collider))
        shape.parent = obj
    return obj


def _mesh(name: str) -> bpy.types.Mesh:
    """Returns the mesh `prop_<name>`, imported from its .glb the first time. Its kit
    materials (the `material` and `surface` extras that prop-cleanup writes) become the
    level's kit materials."""
    mesh_name = f"prop_{name}"
    found = bpy.data.meshes.get(mesh_name)
    if found is not None:
        return found
    path = PROPS / f"{name}.glb"
    if not path.is_file():
        raise FileNotFoundError(
            f"kit.prop: no {path}; make it with `just prop-cleanup` (tools/art/README.md)"
        )
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in new if obj.type == "MESH"]
    if len(meshes) != 1 or meshes[0].matrix_world != Matrix.Identity(4):
        for obj in new:
            bpy.data.objects.remove(obj)
        raise ValueError(
            f"kit.prop: {path} must hold one mesh at the origin; run `just prop-cleanup` on it"
        )
    mesh = meshes[0].data
    for obj in new:
        bpy.data.objects.remove(obj)
    mesh.name = mesh_name
    for i, material in enumerate(mesh.materials):
        if material is not None and "material" in material:
            look = str(material["material"])
            mesh.materials[i] = surface(str(material.get("surface", "default")), look)
    return mesh


def _collider(mesh: bpy.types.Mesh, kind: str) -> bpy.types.Mesh:
    """Returns a box or a cylinder mesh around the bounds of mesh."""
    points = [v.co for v in mesh.vertices]
    low = Vector(min(p[i] for p in points) for i in range(3))
    high = Vector(max(p[i] for p in points) for i in range(3))
    size = high - low
    centre = (low + high) / 2
    shape = bmesh.new()
    if kind == "box":
        bmesh.ops.create_cube(
            shape,
            size=1.0,
            matrix=Matrix.Translation(centre) @ Matrix.Diagonal((*size, 1.0)),
        )
    else:
        bmesh.ops.create_cone(
            shape,
            cap_ends=True,
            segments=CYLINDER_SIDES,
            radius1=max(size.x, size.y) / 2,
            radius2=max(size.x, size.y) / 2,
            depth=size.z,
            matrix=Matrix.Translation(centre),
        )
    out = bpy.data.meshes.new(f"{mesh.name}_{kind}")
    shape.to_mesh(out)
    shape.free()
    return out
