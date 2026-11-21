"""Runs one level script in an empty Blender scene and exports the scene as a .glb.

`tools/blender/build_levels.py` runs it for each level; to run it by hand:

    blender-5.2 -b --factory-startup --python-exit-code 1 \
        --python tools/blender/build_level.py -- levels/<tier>/<id>.py <out.glb>

The level id and tier come from the script path. They go into the `level` marker that the
script makes with `kit.level()`.
"""

import runpy
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    """Builds the level script given after `--` and writes the .glb given after it."""
    script, out = (Path(arg) for arg in sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sys.path.insert(0, str(ROOT))
    runpy.run_path(str(script), run_name="__main__")
    level = bpy.data.objects.get("level")
    if level is None:
        raise RuntimeError(f"{script}: call kit.level() to set the level data")
    level["orrery"]["id"] = script.stem
    level["orrery"]["tier"] = script.parent.name
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        export_format="GLB",
        export_extras=True,
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )


main()
