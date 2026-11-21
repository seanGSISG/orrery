"""Cleans a generated model (for example a Tripo GLB) into a prop that `kit.prop` can place.

Run it with `just prop-cleanup`, or by hand:

    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 \
        --python tools/blender/prop_cleanup.py -- <in.glb> <out.glb> --height 1.5 \
        [--triangles 5000] [--material brass]

It imports the model, joins its meshes into one object named after <out>, scales it so that
decimates it to at most --triangles triangles, scales it so that it is --height m tall, puts
the origin at the centre of its base (on the ground, z = 0), and exports a clean .glb. --material gives
every face that kit material (kit/surfaces.py), so the Godot importer uses our look.
"""

import argparse
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kit.surfaces import MATERIALS, surface

DEFAULT_TRIANGLES = 5000
# Vertices closer than this weld into one. glTF splits vertices at UV and normal seams, and a
# split mesh does not decimate well.
WELD_DISTANCE = 1e-5
# Edges between faces at more than this angle (radians, 30 degrees) stay sharp.
SHARP_ANGLE = 0.5236


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="prop_cleanup.py")
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument(
        "--height", type=float, required=True, help="the prop height, m"
    )
    parser.add_argument("--triangles", type=int, default=DEFAULT_TRIANGLES)
    parser.add_argument("--material", choices=MATERIALS)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if args.height <= 0 or args.triangles < 12:
        parser.error("--height must be positive and --triangles at least 12")
    return args


def triangles(mesh: bpy.types.Mesh) -> int:
    return sum(len(polygon.vertices) - 2 for polygon in mesh.polygons)


def joined_mesh(name: str) -> bpy.types.Object:
    """Bakes the world transform into every imported mesh, joins them into one new object
    at the origin and deletes everything else."""
    parts = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if not parts:
        raise RuntimeError("prop_cleanup: the model has no mesh")
    for obj in parts:
        obj.data = obj.data.copy()
        obj.data.transform(obj.matrix_world)
        obj.data.update()
    target = parts[0]
    with bpy.context.temp_override(
        active_object=target,
        selected_editable_objects=parts,
        selected_objects=parts,
    ):
        bpy.ops.object.join()
    for obj in list(bpy.data.objects):
        if obj != target:
            bpy.data.objects.remove(obj)
    target.parent = None
    target.matrix_world = Matrix.Identity(4)
    target.name = name
    target.data.name = name
    return target


def weld(mesh: bpy.types.Mesh) -> None:
    """Welds split vertices, deletes loose ones, and replaces the imported custom normals
    with smooth shading that keeps the edges sharper than SHARP_ANGLE."""
    shape = bmesh.new()
    shape.from_mesh(mesh)
    bmesh.ops.remove_doubles(shape, verts=shape.verts, dist=WELD_DISTANCE)
    loose = [v for v in shape.verts if not v.link_faces]
    bmesh.ops.delete(shape, geom=loose, context="VERTS")
    shape.to_mesh(mesh)
    shape.free()
    if "custom_normal" in mesh.attributes:
        mesh.attributes.remove(mesh.attributes["custom_normal"])
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=SHARP_ANGLE)
    mesh.update()


def fit(obj: bpy.types.Object, height: float) -> None:
    """Scales the mesh to height and moves the centre of its base to the origin."""
    points = [v.co for v in obj.data.vertices]
    low = Vector(min(p[i] for p in points) for i in range(3))
    high = Vector(max(p[i] for p in points) for i in range(3))
    size = high.z - low.z
    if size <= 0:
        raise RuntimeError("prop_cleanup: the model is flat")
    base = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    scale = height / size
    obj.data.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(-base))
    obj.data.update()


def decimate(obj: bpy.types.Object, budget: int) -> None:
    """Collapses edges until the mesh has at most budget triangles."""
    ratio = 1.0
    for _ in range(8):
        count = triangles(obj.data)
        if count <= budget:
            return
        ratio = min(ratio, budget / count) * 0.98
        modifier = obj.modifiers.new("decimate", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = ratio
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = bpy.data.meshes.new_from_object(evaluated)
        obj.modifiers.remove(modifier)
        old = obj.data
        obj.data = mesh
        mesh.name = old.name
        bpy.data.meshes.remove(old)
    raise RuntimeError(f"prop_cleanup: could not decimate to {budget} triangles")


def main() -> None:
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.source))
    obj = joined_mesh(args.out.stem)
    weld(obj.data)
    # Decimate first: a collapse moves vertices, so the size and the base come after it.
    decimate(obj, args.triangles)
    weld(obj.data)
    fit(obj, args.height)
    if args.material:
        obj.data.materials.clear()
        obj.data.materials.append(surface("default", args.material))
    bpy.context.view_layer.update()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(args.out),
        export_format="GLB",
        export_extras=True,
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    size = obj.dimensions
    print(
        f"prop-cleanup: {args.out.name}: {triangles(obj.data)} triangles, "
        f"{size.x:.2f} x {size.y:.2f} x {size.z:.2f} m"
    )


main()
