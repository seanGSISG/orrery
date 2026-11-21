# /// script
# requires-python = ">=3.13"
# dependencies = ["pillow>=11"]
# ///
"""Renders each level's camera shots into build/gallery/index.html for the visual review.

Usage: `just gallery [id ...]`. With no ids it renders every level script `levels/<tier>/<id>.py`.

For each level it launches the debug game through the harness (tools/harness) in gamescope with
no window, on the High graphics preset (docs/design/visual-quality.md §7). It saves every shot
at 1920x1080 as build/gallery/<id>/<shot>.png, and `start` again at 3840x2160 in <id>/4k/. It
reads each PNG for the exposure check (rubric check 6) and writes one page with a section per
level: the shots, the `motion` pair from `just perf` when it exists, and the 8-check rubric from
the doc as a checklist. It exits 1 when a frame is blank or a screenshot fails.
"""

import html
import json
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "gallery"
BUILT = ROOT / "game" / "levels" / "built"
RUBRIC_DOC = ROOT / "docs" / "design" / "visual-quality.md"
PRESET = "high"
# The shots that the level lint requires (game/levels/level_converter.gd), in page order.
REQUIRED = ["overview", "start", "finish", "egg"]
HD = (1920, 1080)
UHD = (3840, 2160)
# Ticks to step after a level loads, so the marble rests on the start pad.
SETTLE_TICKS = 60
# Rubric check 6: the most pure black and pure white pixels a shot may have.
MAX_BLACK = 0.01
MAX_WHITE = 0.02


class GalleryError(RuntimeError):
    """A harness command failed."""


@dataclass(frozen=True)
class Shot:
    """One saved screenshot and what the checks found in it."""

    name: str
    path: Path
    blank: bool
    black: float
    white: float

    @property
    def exposed(self) -> bool:
        return self.black <= MAX_BLACK and self.white <= MAX_WHITE


def harness(*args: str) -> object:
    """Runs one harness CLI command and returns its JSON result."""
    command = ["uv", "run", "--quiet", "--project", str(ROOT / "tools/harness")]
    result = subprocess.run(
        [*command, "orrery-harness", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GalleryError(f"harness {' '.join(args)}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def level_ids(ids: list[str]) -> list[str]:
    """Returns the given ids, or every level script's id when there are none."""
    return ids or sorted(script.stem for script in ROOT.glob("levels/*/*.py"))


def shot_names(level: str) -> list[str]:
    """Returns the names of the `shot` markers in the built level's glTF JSON: the
    lint-required shots first, in REQUIRED order, then the others by name."""
    data = (BUILT / f"{level}.glb").read_bytes()
    length, kind = struct.unpack_from("<II", data, 12)
    if kind != 0x4E4F534A:  # "JSON"
        raise GalleryError(f"{level}.glb: the first chunk is not JSON")
    gltf = json.loads(data[20 : 20 + length])
    names = [
        node["name"]
        for node in gltf.get("nodes", [])
        if node.get("extras", {}).get("orrery", {}).get("type") == "shot"
    ]
    rank = {name: i for i, name in enumerate(REQUIRED)}
    return sorted(names, key=lambda name: (rank.get(name, len(REQUIRED)), name))


def exposure(path: Path) -> tuple[float, float]:
    """Returns the shares of pure black and pure white pixels in a PNG."""
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        total = rgb.width * rgb.height
        colors = {color: count for count, color in rgb.getcolors(total) or []}
    return colors.get((0, 0, 0), 0) / total, colors.get((255, 255, 255), 0) / total


def capture(
    level: str, size: tuple[int, int], shots: list[str], suffix: str = ""
) -> list[Shot]:
    """Launches the level at size on the gallery preset and saves the shots into
    build/gallery/<level>/ (<level>/4k/ for a suffix), named after the shot."""
    harness("launch", "--level", level, "--resolution", f"{size[0]}x{size[1]}")
    try:
        harness("set_setting", "orrery/graphics/preset", PRESET)
        harness("step", str(SETTLE_TICKS))
        saved: list[Shot] = []
        for name in shots:
            path = OUT / level / suffix.removeprefix("-") / f"{name}.png"
            result = harness("screenshot", "--shot", name, "--path", str(path))
            blank = isinstance(result, dict) and bool(result.get("blank"))
            black, white = exposure(path)
            saved.append(Shot(f"{name}{suffix}", path, blank, black, white))
        return saved
    finally:
        harness("quit")


def rubric() -> list[tuple[str, str]]:
    """Returns the (check, how to check) rows of the review rubric table in RUBRIC_DOC §7."""
    section = (
        RUBRIC_DOC.read_text().split("## 7. Review rubric", 1)[1].split("\n## ", 1)[0]
    )
    rows = re.findall(r"^\| (\d+) \| (.+?) \| (.+?) \|$", section, re.MULTILINE)
    if len(rows) != 8:
        raise GalleryError(
            f"{RUBRIC_DOC.name} §7: expected 8 rubric rows, found {len(rows)}"
        )
    return [(check, how) for _, check, how in rows]


def inline(text: str) -> str:
    """Escapes Markdown text for HTML and turns `code` spans into <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text, quote=False))


def figure(name: str, path: Path, flags: str = "") -> str:
    """Returns the HTML for one image, linked to the full-size file, with a caption."""
    src = html.escape(quote(path.relative_to(OUT).as_posix()))
    name = html.escape(name)
    return (
        f'<figure><a href="{src}"><img src="{src}" alt="{name}" loading="lazy"></a>'
        f"<figcaption><b>{name}</b> {flags}</figcaption></figure>"
    )


def shot_figure(shot: Shot) -> str:
    """Returns the HTML for one screenshot with its blank and exposure flags."""
    mark = "ok" if shot.exposed else "bad"
    flags = (
        f'<span class="{mark}">black {shot.black:.2%}, white {shot.white:.2%}</span>'
    )
    if shot.blank:
        flags = '<span class="bad">BLANK</span> ' + flags
    return figure(shot.name, shot.path, flags)


def section(level: str, shots: list[Shot], checks: list[tuple[str, str]]) -> str:
    """Returns the HTML section for one level: shots, motion pair and rubric checklist."""
    motion = [OUT / level / "motion" / f"motion-{i}.png" for i in (1, 2)]
    if all(path.exists() for path in motion):
        pair = "".join(figure(path.stem, path) for path in motion)
    else:
        pair = f"<p>No motion pair yet: run <code>just perf {html.escape(level)}</code>.</p>"
    exposed = bool(shots) and all(shot.exposed for shot in shots)
    verdict = "no shots" if not shots else "pass" if exposed else "FAIL"
    items = []
    for number, (check, how) in enumerate(checks, 1):
        checked, note = "", ""
        if number == 6:
            checked = " checked" if exposed else ""
            note = f" <em>(script: {verdict})</em>"
        items.append(
            f'<li><label><input type="checkbox"{checked}> <b>{number}. {inline(check)}</b>'
            f"</label><br><span>{inline(how)}{note}</span></li>"
        )
    return (
        f'<section id="{html.escape(level)}"><h2>{html.escape(level)}</h2>'
        f'<div class="shots">{"".join(shot_figure(shot) for shot in shots)}</div>'
        f'<h3>Motion</h3><div class="shots">{pair}</div>'
        f'<h3>Rubric</h3><ol class="rubric">{"".join(items)}</ol></section>'
    )


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Orrery gallery</title>
<style>
:root {{ color-scheme: dark; --bg: #0e1116; --panel: #171b22; --text: #d8dee9;
  --muted: #8b95a5; --ok: #7fd18b; --bad: #ff6b6b; }}
body {{ margin: 0; padding: 24px; background: var(--bg); color: var(--text);
  font: 15px/1.5 system-ui, sans-serif; }}
h1 {{ margin: 0 0 8px; }} h2 {{ margin: 0 0 12px; }} h3 {{ color: var(--muted); }}
section {{ background: var(--panel); border-radius: 8px; padding: 20px; margin: 24px 0; }}
.shots {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 16px; }}
figure {{ margin: 0; }} img {{ width: 100%; border-radius: 4px; display: block; }}
figcaption {{ color: var(--muted); font-size: 13px; padding-top: 4px; }}
.ok {{ color: var(--ok); }} .bad {{ color: var(--bad); font-weight: 600; }}
.rubric {{ list-style: none; padding: 0; }} .rubric li {{ margin: 8px 0; }} .rubric span {{ color: var(--muted); }}
code {{ background: #232936; padding: 0 4px; border-radius: 3px; }}
</style></head><body>
<h1>Orrery gallery</h1>
<p>Preset {preset}. Every shot at 1920x1080, <code>start</code> also at 3840x2160.</p>
{sections}
</body></html>
"""


def main() -> None:
    """Renders the gallery for the levels on the command line (all when none)."""
    checks = rubric()
    sections = []
    problems = []
    for level in level_ids(sys.argv[1:]):
        try:
            names = shot_names(level)
            shots = capture(level, HD, names)
            if "start" in names:
                shots += capture(level, UHD, ["start"], "-4k")
        except (GalleryError, OSError) as error:
            problems.append(f"{level}: {error}")
            continue
        problems += [f"{level}: {shot.name} is blank" for shot in shots if shot.blank]
        sections.append(section(level, shots, checks))
        print(f"{level}: {len(shots)} shots")
    OUT.mkdir(parents=True, exist_ok=True)
    page = OUT / "index.html"
    page.write_text(PAGE.format(preset=PRESET.title(), sections="\n".join(sections)))
    print(f"Gallery: {page}")
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
