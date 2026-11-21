"""The prop path in headless Blender: tools/blender/prop_cleanup.py on a built-in primitive,
then `kit.prop` in a tiny level built by tools/blender/build_level.py. Skipped when
blender-5.2 is missing."""

import json
import os
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

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


def blender(*args: str) -> str:
    result = subprocess.run(
        [BLENDER, *FLAGS, *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def read_glb(path: Path) -> dict:
    """Returns the JSON chunk of a .glb."""
    data = path.read_bytes()
    length, kind = struct.unpack_from("<I4s", data, 12)
    assert data[:4] == b"glTF" and kind == b"JSON"
    return json.loads(data[20 : 20 + length])


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
