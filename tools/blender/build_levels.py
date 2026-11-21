# /// script
# requires-python = ">=3.13"
# ///
"""Builds level scripts into game/levels/built/<id>.glb and checks them.

Usage: `just build-levels [id ...]`, which runs `uv run --script tools/blender/build_levels.py`.
With no ids it builds every `levels/<tier>/<id>.py`.

1. In parallel, for each level: headless Blender runs tools/blender/build_level.py to export the
   .glb, and glTF-Validator checks it. A level that fails loses its old .glb.
2. Godot imports the project once. Each built level gets a `.glb.import` file that names the
   post-import script game/levels/level_import.gd. Its LevelConverter swaps the markers for
   objects, builds the collision and runs the level lint. The file also sets the meshes to
   Static Lightmaps, so Godot generates their UV2 at 0.1 m per texel for `just bake`.
3. game/levels/check_levels.gd checks that each built level loads as a Level.

Environment: BLENDER (default blender-5.2), GLTF_VALIDATOR (default gltf_validator) and GODOT
(default godot) override the tool commands.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS = ROOT / "levels"
BUILT = ROOT / "game" / "levels" / "built"
BUILD_LEVEL = ROOT / "tools" / "blender" / "build_level.py"
IMPORT_SETTINGS = """[remap]

importer="scene"

[params]

nodes/use_node_type_suffixes=false
meshes/light_baking=2
meshes/lightmap_texel_size=0.1
import_script/path="res://levels/level_import.gd"
"""


@dataclass(frozen=True)
class Level:
    """One level script and its build output."""

    id: str
    script: Path

    @property
    def out(self) -> Path:
        return BUILT / f"{self.id}.glb"


def find_levels(ids: list[str]) -> list[Level]:
    """Returns the levels with the given ids (all levels when ids is empty), sorted by id.
    Exits when an id is unknown or two scripts share an id."""
    found: dict[str, Level] = {}
    for script in sorted(LEVELS.glob("*/*.py")):
        if script.stem in found:
            sys.exit(f"build-levels: two level scripts have the id {script.stem!r}")
        found[script.stem] = Level(script.stem, script)
    unknown = sorted(set(ids) - found.keys())
    if unknown:
        sys.exit(f"build-levels: no level script for {', '.join(unknown)}")
    return [found[i] for i in sorted(ids or found)]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Runs a command and captures its output as text."""
    return subprocess.run(command, capture_output=True, text=True, check=False)


def validation_errors(glb: Path) -> list[str]:
    """Returns the glTF-Validator errors for a .glb file."""
    result = run([os.environ.get("GLTF_VALIDATOR", "gltf_validator"), "-o", str(glb)])
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [f"gltf_validator gave no report: {result.stderr.strip()}"]
    messages = report["issues"]["messages"]
    return [
        f"{m['code']} at {m.get('pointer', '?')}: {m['message']}"
        for m in messages
        if m["severity"] == 0
    ]


def build(level: Level) -> list[str]:
    """Exports and validates one level. Returns its problems; when there are none, the .glb
    and its .glb.import file are in game/levels/built/."""
    level.out.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        glb = Path(tmp) / level.out.name
        blender = os.environ.get("BLENDER", "blender-5.2")
        flags = ["-b", "--factory-startup", "-noaudio", "--python-exit-code", "1"]
        script = ["--python", str(BUILD_LEVEL), "--", str(level.script), str(glb)]
        result = run([blender, *flags, *script])
        if result.returncode != 0 or not glb.exists():
            return [f"Blender failed:\n{result.stdout}{result.stderr}".rstrip()]
        errors = validation_errors(glb)
        if errors:
            return errors
        # Name the post-import script before Godot can see the .glb. A fresh file also makes
        # Godot import the level again, so a changed LevelConverter runs on every build.
        level.out.with_name(level.out.name + ".import").write_text(IMPORT_SETTINGS)
        shutil.move(glb, level.out)
    return []


def import_and_check(levels: list[Level]) -> list[str]:
    """Imports the Godot project and checks that each level loads as a Level. Returns the
    problems: the importer's errors, then one line for each level that does not load."""
    godot = [
        os.environ.get("GODOT", "godot"),
        "--headless",
        "--path",
        str(ROOT / "game"),
    ]
    imported = run([*godot, "--import"])
    ids = [level.id for level in levels]
    checked = run([*godot, "--script", "res://levels/check_levels.gd", "--", *ids])
    # LevelConverter errors start with "level <id>:"; SCRIPT ERROR means a bug in a script.
    ours = ("ERROR: level ", "SCRIPT ERROR")
    log = (imported.stdout + imported.stderr).splitlines()
    errors = [line.removeprefix("ERROR: ") for line in log if line.startswith(ours)]
    unloaded = [
        line for line in checked.stderr.splitlines() if line.startswith("level ")
    ]
    problems = [*errors, *unloaded]
    if not problems and (imported.returncode != 0 or checked.returncode != 0):
        problems = [f"Godot failed:\n{imported.stderr}{checked.stderr}"]
    return problems


def remove_stale(levels: list[Level]) -> None:
    """Deletes the built files of levels whose script is gone, so Godot does not import them."""
    ids = {level.id for level in levels}
    for path in [*BUILT.glob("*.glb"), *BUILT.glob("*.glb.import")]:
        if path.name.removesuffix(".import").removesuffix(".glb") not in ids:
            path.unlink()


def main() -> None:
    """Builds the levels named on the command line (all when none) and exits 1 on a problem."""
    levels = find_levels(sys.argv[1:])
    BUILT.mkdir(parents=True, exist_ok=True)
    if not sys.argv[1:]:
        remove_stale(levels)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
        problems = dict(zip(levels, pool.map(build, levels), strict=True))
    for level, errors in problems.items():
        print(f"{level.id}: {'FAILED' if errors else 'built'}")
        for error in errors:
            print(f"  {error}")
    built = [level for level, errors in problems.items() if not errors]
    failed = len(built) < len(levels)
    if built:
        errors = import_and_check(built)
        print("Godot import: " + ("FAILED" if errors else f"{len(built)} levels load"))
        for error in errors:
            print(f"  {error}")
        failed = failed or bool(errors)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
