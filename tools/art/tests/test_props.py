"""The prop path in headless Blender: tools/blender/prop_cleanup.py on a built-in primitive,
then `kit.prop` in a tiny level built by tools/blender/build_level.py. Skipped when
blender-5.2 is missing."""

import io
import json
import os
import shutil
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
BLENDER = os.environ.get("BLENDER", "blender-5.2")
FLAGS = ["-b", "--factory-startup", "-noaudio", "--python-exit-code", "1"]

pytestmark = pytest.mark.skipif(
    shutil.which(BLENDER) is None, reason=f"needs {BLENDER}"
)

# Two parts away from the origin, as a generated model might be: a stretched UV sphere (960
# triangles, z -0.5 to 2.5) and a 1 m cube on top of it (z 3.5 to 4.5). Both are 1 m wide, so
# a clean 2 m prop is 0.4 m wide (give or take what the decimation moves).
PRIMITIVE = """
import sys, bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.5, location=(3, 2, 1))
bpy.context.object.scale = (1, 1, 3)
bpy.ops.mesh.primitive_cube_add(size=1, location=(3, 2, 4))
bpy.ops.export_scene.gltf(filepath=sys.argv[-1], export_format="GLB")
"""


def blender(*args: str, code: int = 0) -> str:
    """Runs Blender, checks its exit code and returns its output."""
    result = subprocess.run(
        [BLENDER, *FLAGS, *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == code, result.stdout + result.stderr
    return result.stdout + result.stderr


def cleanup(source: Path, out: Path, *args: str, code: int = 0) -> str:
    """Runs prop_cleanup.py on source and returns its output."""
    script = str(ROOT / "tools" / "blender" / "prop_cleanup.py")
    return blender("--python", script, "--", str(source), str(out), *args, code=code)


def read_glb(path: Path) -> dict:
    """Returns the JSON chunk of a .glb."""
    data = path.read_bytes()
    length, kind = struct.unpack_from("<I4s", data, 12)
    assert data[:4] == b"glTF" and kind == b"JSON"
    return json.loads(data[20 : 20 + length])


def glb_images(path: Path) -> dict[str, tuple[str, bytes]]:
    """Returns the images of a .glb by the BSDF input they feed (base, packed, normal): the
    MIME type and the file bytes."""
    data = path.read_bytes()
    gltf = read_glb(path)
    length = struct.unpack_from("<I", data, 12)[0]
    blob = data[20 + length + 8 :]
    material = gltf["materials"][0]
    pbr = material["pbrMetallicRoughness"]
    textures = {
        "base": pbr["baseColorTexture"]["index"],
        "packed": pbr["metallicRoughnessTexture"]["index"],
        "normal": material["normalTexture"]["index"],
    }
    out = {}
    for role, texture in textures.items():
        image = gltf["images"][gltf["textures"][texture]["source"]]
        view = gltf["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        out[role] = (image["mimeType"], blob[start : start + view["byteLength"]])
    return out


def validator_errors(path: Path) -> int:
    validator = os.environ.get("GLTF_VALIDATOR", "gltf_validator")
    if shutil.which(validator) is None:
        return 0
    result = subprocess.run(
        [validator, "-o", str(path)], capture_output=True, text=True, check=False
    )
    return json.loads(result.stdout)["issues"]["numErrors"]


@pytest.fixture(scope="module")
def lamp(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A cleaned prop: 2 m tall, at most 200 triangles, brass."""
    folder = tmp_path_factory.mktemp("props")
    source = folder / "source.glb"
    blender("--python-expr", PRIMITIVE, "--", str(source))
    out = folder / "lamp.glb"
    script = str(ROOT / "tools" / "blender" / "prop_cleanup.py")
    log = blender(
        "--python",
        script,
        "--",
        str(source),
        str(out),
        "--height",
        "2",
        "--triangles",
        "200",
        "--material",
        "brass",
    )
    assert "prop-cleanup: lamp.glb:" in log
    return out


def test_prop_cleanup_scales_centres_decimates_and_sets_the_kit_material(
    lamp: Path,
) -> None:
    gltf = read_glb(lamp)
    assert [node["name"] for node in gltf["nodes"]] == ["lamp"]
    primitive = gltf["meshes"][0]["primitives"][0]
    position = gltf["accessors"][primitive["attributes"]["POSITION"]]
    # glTF is y-up: the height is y, and the base sits on y = 0.
    low, high = position["min"], position["max"]
    assert low[1] == pytest.approx(0, abs=1e-4) and high[1] == pytest.approx(
        2, abs=1e-3
    )
    assert low[0] == pytest.approx(-0.2, abs=0.01) and high[0] == pytest.approx(
        0.2, abs=0.01
    )
    assert low[2] == pytest.approx(-0.2, abs=0.01) and high[2] == pytest.approx(
        0.2, abs=0.01
    )
    assert gltf["accessors"][primitive["indices"]]["count"] // 3 <= 200
    assert gltf["materials"][primitive["material"]]["extras"] == {
        "surface": "default",
        "material": "brass",
    }
    assert validator_errors(lamp) == 0


def test_render_prop_writes_one_review_sheet(lamp: Path, tmp_path: Path) -> None:
    out = tmp_path / "lamp.png"
    script = str(ROOT / "tools" / "blender" / "render_prop.py")
    args = ("--samples", "1", "--width", "480")
    assert f"render-prop: {out}" in blender(
        "--python", script, "--", str(lamp), str(out), *args
    )
    with Image.open(out) as sheet:
        assert sheet.width == 480 and 120 <= sheet.height < 480


def test_kit_prop_places_shared_meshes_and_simple_colliders(
    lamp: Path, tmp_path: Path
) -> None:
    script = tmp_path / "test" / "props.py"
    script.parent.mkdir()
    script.write_text(
        "from pathlib import Path\n"
        "import kit\n"
        "import kit.props\n"
        f"kit.props.PROPS = Path({str(lamp.parent)!r})\n"
        "kit.level(title='Props', par=10.0, gold=5.0)\n"
        "kit.track(at=(0.0, 0.0, 0.0))\n"
        "kit.prop('lamp', at=(1.0, 2.0, 0.0), rotation=(0.0, 0.0, 90.0), collider='box')\n"
        "kit.prop('lamp', at=(-1.0, 2.0, 0.0), collider='cylinder')\n"
        "kit.prop('lamp', at=(0.0, 6.0, 0.0))\n"
    )
    out = tmp_path / "props.glb"
    blender(
        "--python",
        str(ROOT / "tools" / "blender" / "build_level.py"),
        "--",
        str(script),
        str(out),
    )
    gltf = read_glb(out)
    nodes = {node["name"]: node for node in gltf["nodes"]}
    props = [nodes[f"prop_lamp_0{i}"] for i in range(3)]
    assert len({node["mesh"] for node in props}) == 1
    # Blender (1, 2, 0) is glTF (1, 0, -2).
    assert props[0]["translation"] == pytest.approx([1, 0, -2], abs=1e-5)
    assert "children" not in props[2]
    box = gltf["nodes"][props[0]["children"][0]]
    cylinder = gltf["nodes"][props[1]["children"][0]]
    assert box["name"] == "prop_lamp_00_collider-colonly"
    assert cylinder["name"] == "prop_lamp_01_collider-colonly"
    triangles = {
        name: gltf["accessors"][
            gltf["meshes"][node["mesh"]]["primitives"][0]["indices"]
        ]["count"]
        // 3
        for name, node in (("box", box), ("cylinder", cylinder))
    }
    assert triangles == {"box": 12, "cylinder": 16 * 2 + 2 * 14}
    material = gltf["materials"][
        gltf["meshes"][props[0]["mesh"]]["primitives"][0]["material"]
    ]
    assert material["name"] == "brass_default"
    assert validator_errors(out) == 0


# A cube mirrored on x (scale -1), and a check that prints how many faces of the cleaned
# model point inwards.
MIRRORED = """
import sys, bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1, location=(2, 0, 1))
bpy.context.object.scale = (-1, 1, 1)
bpy.ops.export_scene.gltf(filepath=sys.argv[-1], export_format="GLB")
"""
INWARD = """
import sys, bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
mesh = next(o for o in bpy.data.objects if o.type == "MESH").data
centre = sum((v.co for v in mesh.vertices), mesh.vertices[0].co * 0) / len(mesh.vertices)
inward = sum(1 for p in mesh.polygons if p.normal.dot(p.center - centre) < 0)
print(f"inward faces: {inward}")
"""


def test_prop_cleanup_keeps_a_mirrored_part_outward(tmp_path: Path) -> None:
    source, out = tmp_path / "mirrored.glb", tmp_path / "box.glb"
    blender("--python-expr", MIRRORED, "--", str(source))
    script = str(ROOT / "tools" / "blender" / "prop_cleanup.py")
    blender("--python", script, "--", str(source), str(out), "--height", "1")
    assert "inward faces: 0" in blender("--python-expr", INWARD, "--", str(out))


# A cube with the material graph that the glTF importer makes for a Tripo model: base colour,
# packed metallic-roughness and normal map, each an image file. sys.argv: the three images, the
# out .glb, and "no-uv" to export it without UVs.
TEXTURED = """
import sys, bpy
base, packed, normal, out, uv = sys.argv[sys.argv.index("--") + 1 :]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1)
cube = bpy.context.object
if uv == "no-uv":
    cube.data.uv_layers.remove(cube.data.uv_layers[0])
material = bpy.data.materials.new("tripo")
cube.data.materials.append(material)
tree = material.node_tree
bsdf = tree.nodes["Principled BSDF"]
def image(path, data):
    node = tree.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(path)
    if data:
        node.image.colorspace_settings.name = "Non-Color"
    return node
tree.links.new(image(base, False).outputs["Color"], bsdf.inputs["Base Color"])
split = tree.nodes.new("ShaderNodeSeparateColor")
tree.links.new(image(packed, True).outputs["Color"], split.inputs["Color"])
tree.links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
tree.links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
bump = tree.nodes.new("ShaderNodeNormalMap")
tree.links.new(image(normal, True).outputs["Color"], bump.inputs["Color"])
tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB")
"""


def textured_model(folder: Path, uv: str = "uv") -> Path:
    """Writes a Tripo-like model: 2048 x 1024 maps, a JPEG normal map, a dielectric left half
    (pure white above pure black, metallic 0.3, roughness 0.02) and a metal right half (dark
    brass, metallic 0.8, roughness 0.9)."""
    base = Image.new("RGB", (2048, 1024), (0, 0, 0))
    base.paste((255, 255, 255), (0, 0, 1024, 512))
    base.paste((100, 80, 40), (1024, 0, 2048, 1024))
    packed = Image.new("RGB", (2048, 1024), (255, 5, 77))
    packed.paste((255, 230, 204), (1024, 0, 2048, 1024))
    paths = [folder / "base.jpg", folder / "packed.png", folder / "normal.jpg"]
    base.save(paths[0], quality=95)
    packed.save(paths[1])
    Image.new("RGB", (2048, 1024), (128, 128, 255)).save(paths[2], quality=95)
    out = folder / f"tripo-{uv}.glb"
    blender("--python-expr", TEXTURED, "--", *map(str, paths), str(out), uv)
    return out


def test_prop_cleanup_makes_tripo_materials_game_ready_and_a_rerun_changes_nothing(
    tmp_path: Path,
) -> None:
    first, second = tmp_path / "crate.glb", tmp_path / "again" / "crate.glb"
    log = cleanup(textured_model(tmp_path), first, "--height", "0.5")
    assert "prop-cleanup: crate.glb: clutter" in log
    assert read_glb(first)["materials"][0]["name"] == "orrery_crate"
    images = glb_images(first)
    assert [mime for mime, _ in images.values()] == [
        "image/jpeg",
        "image/png",
        "image/png",
    ]
    maps = {
        role: np.asarray(Image.open(io.BytesIO(data)).convert("RGB")).astype(int)
        for role, (_, data) in images.items()
    }
    assert all(pixels.shape == (512, 1024, 3) for pixels in maps.values())
    packed, base = maps["packed"], maps["base"]
    # Metallic 0 or 1; roughness 0.15 (38) and 0.55 (140). Far from the edge between halves.
    assert packed[:, :500, 2].max() == 0 and packed[:, 524:, 2].min() == 255
    assert np.unique(packed[:, :500, 1]).tolist() == [38]
    assert np.unique(packed[:, 524:, 1]).tolist() == [140]
    # Albedo: white and black clamp to 240 and 30; the dark brass scales to 180 (JPEG noise).
    assert np.abs(base[20:230, 20:480] - 240).max() <= 2
    assert np.abs(base[280:500, 20:480] - 30).max() <= 2
    assert np.abs(base[20:490, 544:1000] - [180, 144, 72]).max() <= 3
    cleanup(first, second, "--height", "0.5")
    assert glb_images(second) == images


def test_prop_cleanup_stops_on_textures_without_uvs(tmp_path: Path) -> None:
    source = textured_model(tmp_path, "no-uv")
    log = cleanup(source, tmp_path / "x.glb", "--height", "1", code=1)
    assert (
        "prop-cleanup: error: tripo-no-uv.glb: the model has textures but no UV map"
        in log
    )


def test_prop_cleanup_gives_a_kit_material_to_chosen_parts(tmp_path: Path) -> None:
    source, out = tmp_path / "source.glb", tmp_path / "post.glb"
    blender("--python-expr", PRIMITIVE, "--", str(source))
    log = cleanup(source, out, "--height", "2", "--material", "brass:1", "--parts")
    # Part 0 is the sphere (most faces), part 1 the cube on top of it. glTF has triangles only.
    assert "prop-cleanup: part 0: 960 faces, centre (0.00, 0.00, 0.60) m" in log
    assert "prop-cleanup: part 1: 12 faces, centre (0.00, 0.00, 1.80) m" in log
    gltf = read_glb(out)
    brass = [
        primitive
        for primitive in gltf["meshes"][0]["primitives"]
        if gltf["materials"][primitive["material"]].get("extras", {}).get("material")
        == "brass"
    ]
    assert len(brass) == 1
    assert gltf["accessors"][brass[0]["indices"]]["count"] // 3 == 12
