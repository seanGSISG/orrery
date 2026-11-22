"""Cleans a generated model (for example a Tripo GLB) into a prop that `kit.prop` can place.

Run it with `just prop-cleanup`, or by hand:

    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 \
        --python tools/blender/prop_cleanup.py -- <in.glb> <out.glb> --height 1.5 \
        [--class hero] [--triangles 5000] [--stone] [--material brass[:1,2]] [--parts]

It imports the model and joins its meshes into one object named after <out>. It decimates the
mesh to at most --triangles triangles, scales it to --height m, puts the origin at the centre
of its base (z = 0) and exports a clean .glb. Then it makes each of the model's own materials
obey docs/design/visual-quality.md §6 (the rules are in tools/art/src/orrery_art/materials.py):

- the material is named `orrery_<out>`;
- every map is at most the texture size of the class (clutter and medium 1K, hero 2K);
- metallic is 0 or 1, and roughness and albedo are inside the limits of metal or dielectric;
- the normal map and the metallic-roughness map are PNG (lossless);
- --stone pulls warm, light colours to the saturation of the kit limestone.

The class comes from the height (asset-prompting.md §3.2); give --class hero for a prop in view
at spawn. --material brass gives every face that kit material (kit/surfaces.py), and
--material brass:1,2 gives it only to parts 1 and 2 of the list that --parts prints. The Godot
importer then uses our look on those faces.

A map changes only when a rule moves it, so a second run on a clean prop changes nothing. A
model that breaks a rule the script cannot fix (a triangle budget out of reach, textures
without UVs, a material graph it cannot read) stops the run with a `prop-cleanup: error:` line
and exit code 1.
"""

import argparse
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "art" / "src"))

from orrery_art import materials as rules

from kit.surfaces import MATERIALS, surface

# Vertices closer than this weld into one. glTF splits vertices at UV and normal seams, and a
# split mesh does not decimate well.
WELD_DISTANCE = 1e-5
# Edges between faces at more than this angle (radians, 30 degrees) stay sharp.
SHARP_ANGLE = 0.5236
# docs/design/visual-quality.md §6 asks for 90 or higher.
JPEG_QUALITY = 95
JPEG, PNG = b"\xff\xd8\xff", b"\x89PNG"


class PropError(Exception):
    """A rule that the clean-up cannot fix. main() prints it and exits with code 1."""


def kit_material(text: str) -> tuple[str, list[int] | None]:
    """Reads --material: a kit material, optionally with the parts that take it."""
    look, colon, parts = text.partition(":")
    if look not in MATERIALS:
        raise argparse.ArgumentTypeError(f"{look!r} is not one of {MATERIALS}")
    try:
        return look, [int(part) for part in parts.split(",")] if colon else None
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"{text!r}: parts are numbers, as in brass:1,2"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="prop_cleanup.py")
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument(
        "--height", type=float, required=True, help="the prop height, m"
    )
    parser.add_argument(
        "--class",
        dest="size_class",
        choices=rules.CLASSES,
        help="the size class (default: from --height)",
    )
    parser.add_argument(
        "--triangles", type=int, help="the budget (default: the class budget)"
    )
    parser.add_argument("--stone", action="store_true")
    parser.add_argument("--material", type=kit_material)
    parser.add_argument("--parts", action="store_true", help="print the parts")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if not args.source.is_file():
        parser.error(f"no such model: {args.source}")
    if not 0 < args.height < float("inf"):
        parser.error("--height must be a positive number")
    args.size_class = args.size_class or rules.prop_class(args.height)
    if args.triangles is None:
        args.triangles = rules.CLASSES[args.size_class].triangles
    if args.triangles < 12:
        parser.error("--triangles must be at least 12")
    return args


def triangles(mesh: bpy.types.Mesh) -> int:
    return sum(len(polygon.vertices) - 2 for polygon in mesh.polygons)


def joined_mesh(name: str) -> bpy.types.Object:
    """Bakes the world transform into every imported mesh, joins them into one new object
    at the origin and deletes everything else."""
    parts = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if not parts:
        raise PropError("the model has no mesh")
    # Read every world matrix first: clearing a parent changes its children's.
    worlds = [obj.matrix_world.copy() for obj in parts]
    for obj, world in zip(parts, worlds, strict=True):
        obj.data = obj.data.copy()
        obj.data.transform(world)
        # A mirrored node (negative scale) turns its faces inside out once it is baked.
        if world.determinant() < 0:
            obj.data.flip_normals()
        obj.data.update()
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
    # The join places each part by its transform, which is now the identity.
    bpy.context.view_layer.update()
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


def bounds(points: list[Vector]) -> tuple[Vector, Vector]:
    low = Vector(min(p[i] for p in points) for i in range(3))
    high = Vector(max(p[i] for p in points) for i in range(3))
    return low, high


def fit(obj: bpy.types.Object, height: float) -> None:
    """Scales the mesh to height and moves the centre of its base to the origin."""
    low, high = bounds([v.co for v in obj.data.vertices])
    size = high.z - low.z
    if size <= 0:
        raise PropError("the model is flat")
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
    raise PropError(
        f"could not decimate to {budget} triangles ({triangles(obj.data)} left); "
        "give a larger --triangles or a lower Tripo face_limit"
    )


def parts(mesh: bpy.types.Mesh) -> list[list[int]]:
    """Returns the connected parts of the welded mesh as lists of face indices, the part with
    the most faces first (ties: the lower base first)."""
    shape = bmesh.new()
    shape.from_mesh(mesh)
    shape.faces.ensure_lookup_table()
    seen: set[int] = set()
    found: list[tuple[int, float, list[int]]] = []
    for start in shape.faces:
        if start.index in seen:
            continue
        seen.add(start.index)
        group, stack = [], [start]
        while stack:
            face = stack.pop()
            group.append(face.index)
            for edge in face.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        low_z = min(v.co.z for i in group for v in shape.faces[i].verts)
        found.append((len(group), low_z, group))
    shape.free()
    found.sort(key=lambda part: (-part[0], part[1]))
    return [group for _, _, group in found]


def print_parts(mesh: bpy.types.Mesh, groups: list[list[int]], height: float) -> None:
    """Prints each part: its faces, and its centre and size in metres of the clean prop."""
    low, high = bounds([v.co for v in mesh.vertices])
    scale = height / max(high.z - low.z, 1e-9)
    base = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for i, group in enumerate(groups):
        points = [
            (mesh.vertices[v].co - base) * scale
            for f in group
            for v in mesh.polygons[f].vertices
        ]
        a, b = bounds(points)
        c, s = (a + b) / 2, b - a
        print(
            f"prop-cleanup: part {i}: {len(group)} faces, centre ({c.x:.2f}, {c.y:.2f}, "
            f"{c.z:.2f}) m, size {s.x:.2f} x {s.y:.2f} x {s.z:.2f} m"
        )


def give_kit_material(
    obj: bpy.types.Object, look: str, chosen: list[int] | None, groups: list[list[int]]
) -> None:
    """Gives the kit material look to every face, or to the chosen parts only."""
    mesh = obj.data
    if chosen is None:
        mesh.materials.clear()
        mesh.materials.append(surface("default", look))
        return
    if bad := [i for i in chosen if not 0 <= i < len(groups)]:
        raise PropError(f"no part {bad}: the model has parts 0 to {len(groups) - 1}")
    if not mesh.materials:
        # The other faces keep a plain material of their own.
        mesh.materials.append(bpy.data.materials.new(obj.name))
    mesh.materials.append(surface("default", look))
    slot = len(mesh.materials) - 1
    for i in chosen:
        for face in groups[i]:
            mesh.polygons[face].material_index = slot


def pixels(image: bpy.types.Image) -> np.ndarray:
    """Returns the image as an array (height, width, channels), sRGB for a colour map."""
    width, height = image.size
    data = np.empty(width * height * image.channels, dtype=np.float32)
    image.pixels.foreach_get(data)
    return data.reshape(height, width, image.channels)


def magic(image: bpy.types.Image) -> bytes:
    """Returns the first bytes of the image's file (empty for an image made in Blender)."""
    return image.packed_file.data[:4] if image.packed_file is not None else b""


def is_jpeg(image: bpy.types.Image) -> bool:
    return magic(image).startswith(JPEG)


def store(image: bpy.types.Image, before: np.ndarray, after: np.ndarray) -> bool:
    """Writes after into the image when the rules moved it (rules.needs_change). Returns
    whether it did. A changed image is encoded again on export, in its own format."""
    if not rules.needs_change(before, after, is_jpeg(image)):
        return False
    image.pixels.foreach_set(after.ravel())
    image.update()
    return True


def as_png(image: bpy.types.Image) -> bpy.types.Image:
    """Replaces the image with a copy that exports as PNG, and returns the copy. For a normal
    map: a lossy normal map shows as blocky shading (visual-quality.md §6)."""
    width, height = image.size
    png = bpy.data.images.new(image.name, width, height, alpha=image.channels == 4)
    png.colorspace_settings.name = "Non-Color"
    png.pixels.foreach_set(pixels(image).ravel())
    png.update()
    image.user_remap(png)
    name = image.name
    bpy.data.images.remove(image)
    png.name = name
    return png


def linked(
    socket: bpy.types.NodeSocket, kind: str, material: str
) -> bpy.types.Node | None:
    """Returns the node of type kind that feeds socket, or None when nothing feeds it."""
    if not socket.links:
        return None
    node = socket.links[0].from_node
    if node.type != kind:
        raise PropError(
            f"material {material}: {socket.name} comes from a {node.type} node, not from "
            f"{kind}; the clean-up reads only the graph that the glTF importer makes"
        )
    return node


def clean_material(material: bpy.types.Material, size: int, stone: bool) -> list[str]:
    """Applies the §6 rules to one material of the model. Returns what it did, for the log."""
    name = material.name
    nodes = [n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
    if len(nodes) != 1:
        raise PropError(f"material {name}: {len(nodes)} Principled BSDF nodes, not 1")
    bsdf = nodes[0]
    base = linked(bsdf.inputs["Base Color"], "TEX_IMAGE", name)
    # Both come straight from one split of the packed map; a factor node in between stops it.
    splits = {
        linked(bsdf.inputs[key], "SEPARATE_COLOR", name)
        for key in ("Metallic", "Roughness")
    } - {None}
    if len(splits) > 1:
        raise PropError(f"material {name}: metallic and roughness come from two maps")
    split = next(iter(splits), None)
    packed = linked(split.inputs["Color"], "TEX_IMAGE", name) if split else None
    bump = linked(bsdf.inputs["Normal"], "NORMAL_MAP", name)
    normal = linked(bump.inputs["Color"], "TEX_IMAGE", name) if bump else None
    done = []
    images = {n.image for n in material.node_tree.nodes if n.type == "TEX_IMAGE"}
    for image in images - {None}:
        width, height = image.size
        new = rules.fit_size(width, height, size)
        if new != (width, height):
            image.scale(*new)
            done.append(f"{image.name} {width}x{height} -> {new[0]}x{new[1]}")
    # The data maps are lossless, so metallic stays exactly 0 or 1 and the normals unblocked.
    for node in (packed, normal):
        if node is not None and node.image and magic(node.image) != PNG:
            node.image = as_png(node.image)
            done.append(f"{node.image.name}: PNG")

    # Metallic and roughness: the blue and green channels of the packed map (glTF), else
    # the BSDF values.
    metallic = bsdf.inputs["Metallic"]
    roughness = bsdf.inputs["Roughness"]
    metallic.default_value = float(
        rules.snap_metallic(np.float32(metallic.default_value))
    )
    scalar_metal = np.array([[metallic.default_value > 0.5]])
    roughness.default_value = float(
        rules.limit_roughness(np.float32(roughness.default_value), scalar_metal)[0, 0]
    )
    metal = scalar_metal
    if packed is not None and packed.image is not None:
        before = pixels(packed.image)
        after = before.copy()
        if metallic.is_linked:
            after[..., 2] = rules.snap_metallic(before[..., 2])
            metal = after[..., 2] > 0.5
        if roughness.is_linked:
            after[..., 1] = rules.limit_roughness(before[..., 1], metal)
        if store(packed.image, before, after):
            done.append(f"{packed.image.name}: metallic 0 or 1, roughness in limits")

    # Albedo, steered by the metal mask.
    color = bsdf.inputs["Base Color"]
    srgb = rules.to_srgb(np.array(color.default_value[:3], dtype=np.float32))
    fixed = rules.limit_albedo(srgb[None, None], np.array([[metal.any()]]), stone)
    color.default_value = (*rules.to_linear(fixed[0, 0]), color.default_value[3])
    if base is not None and base.image is not None:
        before = pixels(base.image)
        after = before.copy()
        mask = rules.resample(metal, before.shape[:2])
        after[..., :3] = rules.limit_albedo(before[..., :3], mask, stone)
        if store(base.image, before, after):
            done.append(f"{base.image.name}: albedo in limits")
    return done


def textured(mesh: bpy.types.Mesh) -> bool:
    return any(
        node.type == "TEX_IMAGE"
        for material in mesh.materials
        if material is not None and "material" not in material and material.node_tree
        for node in material.node_tree.nodes
    )


def run(args: argparse.Namespace) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.source))
    name = args.out.stem
    obj = joined_mesh(name)
    weld(obj.data)
    if textured(obj.data) and not obj.data.uv_layers:
        raise PropError("the model has textures but no UV map; ask Tripo for UVs")
    groups = parts(obj.data) if args.parts or args.material else []
    if args.parts:
        print_parts(obj.data, groups, args.height)
    if args.material:
        give_kit_material(obj, *args.material, groups)
    # Decimate first: a collapse moves vertices, so the size and the base come after it.
    decimate(obj, args.triangles)
    weld(obj.data)
    fit(obj, args.height)
    size = rules.CLASSES[args.size_class].texture
    own = [m for m in obj.data.materials if m is not None and "material" not in m]
    for i, material in enumerate(own):
        material.name = f"orrery_{name}" if i == 0 else f"orrery_{name}_{i + 1}"
        for line in clean_material(material, size, args.stone):
            print(f"prop-cleanup: {line}")
    bpy.context.view_layer.update()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(args.out),
        export_format="GLB",
        export_image_format="AUTO",
        export_jpeg_quality=JPEG_QUALITY,
        export_extras=True,
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    dims = obj.dimensions
    print(
        f"prop-cleanup: {args.out.name}: {args.size_class}, {triangles(obj.data)} triangles, "
        f"{dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} m, textures at most {size} px"
    )


def main() -> None:
    args = parse_args()
    try:
        run(args)
    except PropError as error:
        print(f"prop-cleanup: error: {args.source.name}: {error}", file=sys.stderr)
        sys.exit(1)


main()
