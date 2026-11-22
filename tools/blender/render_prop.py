"""Renders the review sheet of a prop: one PNG that shows the prop from the front, the right,
the back and the left, beside the marble and a block of each kit material, in neutral light.

Run it with `just render-prop <id>`, or by hand:

    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 \
        --python tools/blender/render_prop.py -- <prop.glb> <out.png> [--samples 64] [--width 2400]

The four copies stand in a row on a grey floor, each turned 90 degrees more than the one
before. The marble (0.4 m glass with a brass core) and the blocks (0.4 m) stand at the left
end. The blocks and the prop's own kit-material faces use the game's kit materials: the
textures, tint, repeat, roughness scale and metallic of `game/materials/<set>/<name>.tres`,
mapped from three sides as the kit shader does. The light is a white sun and a grey sky, so
the colours read as they are. An orthographic camera looks from the front and 20 degrees up,
so every part of the row has the same scale. Cycles renders it on the CPU.
"""

import argparse
import math
import re
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kit.surfaces import MATERIALS

GAME = ROOT / "game"
TEXTURES = ROOT / "assets" / "textures"
MARBLE_RADIUS = 0.2
BLOCK = 0.4
# Space between the items of the row, as a part of the prop's largest width.
GAP = 0.35
ELEVATION = 20.0
# The kit shader keeps albedo inside these linear limits (game/materials/kit_surface.gdshader).
ALBEDO_MIN, ALBEDO_MAX_DIELECTRIC, ALBEDO_MAX_METAL = 0.013, 0.871, 0.956


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="render_prop.py")
    parser.add_argument("prop", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--width", type=int, default=2400, help="the image width, px")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if not args.prop.is_file():
        parser.error(f"no such prop: {args.prop}")
    return args


def tres(name: str) -> dict[str, str]:
    """Returns the shader parameters of the kit material name, with each texture as a file
    path. It reads the set from game/materials/kit_materials.gd, as KitMaterials.find does."""
    found = re.search(
        r'const SET: String = "(\w+)"',
        (GAME / "materials" / "kit_materials.gd").read_text(),
    )
    if found is None:
        raise RuntimeError("render_prop: no SET in game/materials/kit_materials.gd")
    folder = GAME / "materials"
    path = next(
        (
            p
            for p in (folder / found[1] / f"{name}.tres", folder / f"{name}.tres")
            if p.is_file()
        ),
        None,
    )
    if path is None:
        raise RuntimeError(f"render_prop: no kit material {name} in {folder}")
    text = path.read_text()
    textures = re.findall(r'path="res://materials/textures/([^"]+)" id="(\w+)"', text)
    by_id = {ident: file for file, ident in textures}
    params = dict(re.findall(r"^shader_parameter/(\w+) = (.+)$", text, re.MULTILINE))
    for key, value in params.items():
        if ref := re.fullmatch(r'ExtResource\("(\w+)"\)', value):
            params[key] = str(next(TEXTURES.glob(f"*/{by_id[ref[1]]}")))
    return params


def numbers(value: str) -> list[float]:
    """Returns the numbers of a .tres value: `0.7`, or `Vector3(1.0, 1.1, 1.4)`."""
    inside = re.search(r"\((.*)\)", value)
    return [float(x) for x in (inside[1] if inside else value).split(",")]


def kit_material(name: str) -> bpy.types.Material:
    """Returns a Blender copy of the kit material name: box-mapped textures in object space."""
    found = bpy.data.materials.get(f"kit_{name}")
    if found is not None:
        return found
    params = tres(name)
    material = bpy.data.materials.new(f"kit_{name}")
    tree = material.node_tree
    tree.nodes.clear()
    new = tree.nodes.new
    coord = new("ShaderNodeTexCoord")
    scale = new("ShaderNodeVectorMath")
    scale.operation = "SCALE"
    scale.inputs["Scale"].default_value = 1.0 / numbers(params.get("tile", "1"))[0]
    tree.links.new(coord.outputs["Object"], scale.inputs[0])

    def texture(key: str, data: bool) -> bpy.types.Node:
        node = new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(params[key], check_existing=True)
        if data:
            node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.3
        tree.links.new(scale.outputs["Vector"], node.inputs["Vector"])
        return node

    metallic = numbers(params.get("metallic", "0"))[0]
    bsdf = new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metallic
    tint = new("ShaderNodeVectorMath")
    tint.operation = "MULTIPLY"
    tint.inputs[1].default_value = numbers(params.get("tint", "(1, 1, 1)"))
    tree.links.new(texture("albedo_map", False).outputs["Color"], tint.inputs[0])
    low, high = new("ShaderNodeVectorMath"), new("ShaderNodeVectorMath")
    low.operation, high.operation = "MAXIMUM", "MINIMUM"
    low.inputs[1].default_value = (ALBEDO_MIN,) * 3
    top = ALBEDO_MAX_DIELECTRIC + (ALBEDO_MAX_METAL - ALBEDO_MAX_DIELECTRIC) * metallic
    high.inputs[1].default_value = (top,) * 3
    tree.links.new(tint.outputs["Vector"], low.inputs[0])
    tree.links.new(low.outputs["Vector"], high.inputs[0])
    tree.links.new(high.outputs["Vector"], bsdf.inputs["Base Color"])
    rough = new("ShaderNodeMath")
    rough.operation, rough.use_clamp = "MULTIPLY", True
    rough.inputs[1].default_value = numbers(params.get("roughness_scale", "1"))[0]
    tree.links.new(texture("roughness_map", True).outputs["Color"], rough.inputs[0])
    tree.links.new(rough.outputs["Value"], bsdf.inputs["Roughness"])
    if "normal_map" in params:
        bump = new("ShaderNodeNormalMap")
        bump.inputs["Strength"].default_value = numbers(
            params.get("normal_strength", "1")
        )[0]
        tree.links.new(
            texture("normal_map", True).outputs["Color"], bump.inputs["Color"]
        )
        tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    output = new("ShaderNodeOutputMaterial")
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material


def plain_material(
    name: str, color: tuple[float, float, float], inputs: dict[str, float]
) -> bpy.types.Material:
    """Returns a Principled BSDF material: color, and the other BSDF inputs by name."""
    material = bpy.data.materials.new(name)
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    for key, value in inputs.items():
        bsdf.inputs[key].default_value = value
    return material


def import_prop(path: Path) -> bpy.types.Mesh:
    """Imports the prop and returns its mesh, with its kit-material faces in the kit look."""
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(
            f"render_prop: {path} must hold one mesh; run `just prop-cleanup`"
        )
    mesh = meshes[0].data
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for i, material in enumerate(mesh.materials):
        if material is not None and "material" in material:
            mesh.materials[i] = kit_material(str(material["material"]))
    return mesh


def add(
    name: str, data: bpy.types.ID, at: Vector, yaw: float = 0.0
) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = Matrix.Translation(at) @ Matrix.Rotation(
        math.radians(yaw), 4, "Z"
    )
    return obj


def primitive(
    kind: str, material: bpy.types.Material, at: Vector, **size: float
) -> bpy.types.Object:
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=64, ring_count=32, location=at, **size
        )
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.mesh.primitive_cube_add(location=at, **size)
    obj = bpy.context.object
    obj.data.materials.append(material)
    return obj


def build_row(mesh: bpy.types.Mesh) -> list[bpy.types.Object]:
    """Places the marble, the kit blocks and four turned copies of the prop in a row along x.
    Returns every object of the row."""
    points = [v.co for v in mesh.vertices]
    low = Vector(min(p[i] for p in points) for i in range(3))
    high = Vector(max(p[i] for p in points) for i in range(3))
    reach = max(
        Vector((max(abs(low.x), abs(high.x)), max(abs(low.y), abs(high.y)), 0)).length,
        BLOCK,
    )
    gap = GAP * max(reach, BLOCK)
    x = 0.0
    glass = plain_material(
        "glass",
        (1.0, 1.0, 1.0),
        {"Roughness": 0.0, "IOR": 1.5, "Transmission Weight": 1.0},
    )
    centre = Vector((x, 0, MARBLE_RADIUS))
    row = [
        primitive("sphere", glass, centre, radius=MARBLE_RADIUS),
        primitive("sphere", kit_material("brass"), centre, radius=MARBLE_RADIUS / 2),
    ]
    for look in MATERIALS:
        x += BLOCK + gap / 2
        row.append(
            primitive("cube", kit_material(look), Vector((x, 0, BLOCK / 2)), size=BLOCK)
        )
    x += BLOCK / 2 + gap + reach
    for yaw in (0.0, 90.0, 180.0, 270.0):
        row.append(add(f"prop_{int(yaw)}", mesh, Vector((x, 0, 0)), yaw))
        x += 2 * reach + gap
    return row


def build_stage(row: list[bpy.types.Object], width: int) -> None:
    """Adds the floor, the light and an orthographic camera that frames the row."""
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=1000)
    floor = plain_material("floor", (0.18, 0.18, 0.18), {"Roughness": 0.8})
    bpy.context.object.data.materials.append(floor)
    world = bpy.data.worlds.new("grey")
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    background.inputs["Strength"].default_value = 0.6
    scene.world = world
    sun = add("sun", bpy.data.lights.new("sun", "SUN"), Vector())
    sun.data.energy = 2.5
    sun.data.angle = math.radians(2.0)
    sun.rotation_euler = (math.radians(45.0), 0.0, math.radians(-35.0))
    camera = add("camera", bpy.data.cameras.new("camera"), Vector())
    camera.data.type = "ORTHO"
    camera.rotation_euler = (math.radians(90.0 - ELEVATION), 0.0, 0.0)
    scene.camera = camera
    bpy.context.view_layer.update()
    # Frame the row: its corners in camera space give the centre and the size.
    view = camera.matrix_world.inverted()
    corners = [
        view @ (obj.matrix_world @ Vector(c)) for obj in row for c in obj.bound_box
    ]
    low = Vector(min(p[i] for p in corners) for i in range(2))
    high = Vector(max(p[i] for p in corners) for i in range(2))
    size = (high - low) * 1.08
    centre = camera.matrix_world @ Vector(
        ((low.x + high.x) / 2, (low.y + high.y) / 2, 0.0)
    )
    camera.location = centre - camera.matrix_world.to_3x3() @ Vector((0, 0, -100.0))
    camera.data.clip_end = 1000.0
    height = max(round(width * size.y / size.x), width // 4)
    camera.data.ortho_scale = max(size.x, size.y * width / height)
    scene.render.resolution_x, scene.render.resolution_y = width, height


def configure(samples: int) -> None:
    """Cycles on the CPU (a few seconds; it needs no free GPU memory), with the denoiser."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"


def main() -> None:
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure(args.samples)
    row = build_row(import_prop(args.prop))
    build_stage(row, args.width)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(args.out)
    bpy.ops.render.render(write_still=True)
    print(f"render-prop: {args.out}")


main()
