# /// script
# requires-python = ">=3.13"
# dependencies = ["pillow>=11", "numpy>=2"]
# ///
"""Brass look study: shoots brass material variants at fixed cameras and measures the brass
pixels in shade. It is a study tool on the brass-study branch, not part of the game.

Usage (from the repo root, after `just build-levels b01 b02 b03 zone_1` and `just import`):
  uv run --script tools/brass_study/study.py shoot [variant ...]   # default: every variant
  uv run --script tools/brass_study/study.py polished               # the two polished brasses
  uv run --script tools/brass_study/study.py measure                # writes build/brass_study/stats.json
  uv run --script tools/brass_study/study.py export <folder>         # page images and stats

`shoot` copies tools/brass_study/variants/<variant>.tres over the kit brass
(game/materials/a/brass.tres), launches each level through the harness on the High preset,
saves the views as build/brass_study/<variant>/<level>-<shot>.png, and puts the kit brass back.
No rebake: every variant uses the lightmaps baked with the control brass.

Two variants are for measurement only: `mask` (flat magenta) finds the brass pixels by
comparison with `control`, and `light` (white matte, sun only) is black where the brass is in
shade. `measure` reads those frames and gives, for each variant and view, the median colour of
the brass in shade, its CIE LCh hue and chroma, and how far it sits from wood and cork tones.
"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "tools" / "brass_study"
OUT = ROOT / "build" / "brass_study"
KIT_BRASS = ROOT / "game" / "materials" / "a" / "brass.tres"
POLISHED = ROOT / "game" / "materials" / "brass_polished.tres"
PRESET = "high"
SIZE = "1920x1080"
# Ticks after the level loads, as the gallery (tools/gallery/gallery.py).
SETTLE_TICKS = 60
# The views of the study: level -> shots.
VIEWS: dict[str, list[str]] = {
    "b01": ["start"],
    "b02": ["start"],
    "b03": ["start", "gears"],
    "zone_1": ["shaft"],
}
# The zone 1 views that show the polished brass of the lift casings.
POLISHED_VIEWS: dict[str, list[str]] = {"zone_1": ["start", "workshop", "gear_room"]}
# Close-up corners for the polished views, where the most changed pixels are not the casing.
POLISHED_CROPS: dict[str, tuple[int, int]] = {
    "zone_1-start": (1000, 40),
    "zone_1-workshop": (168, 184),
}
MEASURE_ONLY = ("mask", "light")
# A brass pixel is in shade when the sun-only frame is darker than this (sRGB luma, 0-255).
SHADE_LUMA = 12.0
# A brass pixel is in sun when the sun-only frame is brighter than this.
SUN_LUMA = 40.0
# Reference tones: the median sRGB albedo of the game's wood (Poly Haven weathered_planks x the
# tint of game/materials/wood.tres) and of ambientCG Cork002 (CC0, 1K colour map).
REFERENCES: dict[str, tuple[float, float, float]] = {
    "wood": (89.0, 73.0, 62.0),
    "cork": (175.0, 130.0, 101.0),
}


class StudyError(RuntimeError):
    """A harness command failed."""


def harness(*args: str) -> object:
    """Runs one harness CLI command and returns its JSON result."""
    command = [
        "uv",
        "run",
        "--quiet",
        "--project",
        str(ROOT / "tools/harness"),
        "orrery-harness",
    ]
    result = subprocess.run(
        [*command, *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise StudyError(f"harness {' '.join(args)}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def shoot_views(folder: Path, views: dict[str, list[str]]) -> None:
    """Launches each level of views and saves its shots as folder/<level>-<shot>.png."""
    for level, shots in views.items():
        harness("launch", "--level", level, "--resolution", SIZE)
        try:
            harness("set_setting", "orrery/graphics/preset", PRESET)
            harness("step", str(SETTLE_TICKS))
            for shot in shots:
                path = folder / f"{level}-{shot}.png"
                result = harness("screenshot", "--shot", shot, "--path", str(path))
                if isinstance(result, dict) and result.get("blank"):
                    raise StudyError(f"{path} is blank")
                print(f"  {path.relative_to(ROOT)}", flush=True)
        finally:
            harness("quit")


def swap_and_shoot(
    target: Path, source: Path, folder: Path, views: dict[str, list[str]]
) -> None:
    """Puts source in place of target, shoots views into folder, and puts target back."""
    original = target.read_bytes()
    try:
        target.write_bytes(source.read_bytes())
        shoot_views(folder, views)
    finally:
        target.write_bytes(original)


def shoot(names: list[str]) -> None:
    """Shoots each named variant (default: every file in variants/)."""
    variants = names or sorted(
        path.stem for path in (STUDY / "variants").glob("*.tres")
    )
    for name in variants:
        print(f"variant {name}", flush=True)
        swap_and_shoot(
            KIT_BRASS, STUDY / "variants" / f"{name}.tres", OUT / name, VIEWS
        )


def polished() -> None:
    """Shoots the zone 1 casings with each polished brass in polished/."""
    for source in sorted((STUDY / "polished").glob("*.tres")):
        print(f"polished {source.stem}", flush=True)
        swap_and_shoot(POLISHED, source, OUT / "polished" / source.stem, POLISHED_VIEWS)


def to_linear(srgb: np.ndarray) -> np.ndarray:
    """sRGB 0-255 to linear 0-1."""
    c = srgb / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_lab(srgb: np.ndarray) -> np.ndarray:
    """sRGB 0-255 (..., 3) to CIE L*a*b* (D65)."""
    m = np.array(
        [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]
    )
    xyz = to_linear(srgb) @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack(
        [
            116 * f[..., 1] - 16,
            500 * (f[..., 0] - f[..., 1]),
            200 * (f[..., 1] - f[..., 2]),
        ],
        -1,
    )


def luma(srgb: np.ndarray) -> np.ndarray:
    """Rec. 709 luma of sRGB 0-255 values."""
    return srgb @ np.array([0.2126, 0.7152, 0.0722])


def load(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float64)


@dataclass(frozen=True)
class Stats:
    """The brass pixels of one variant in one view, in one light (shade or sun)."""

    pixels: int
    median: tuple[int, int, int]
    luma: float
    luma_p10: float
    luma_p90: float
    lightness: float
    chroma: float
    hue: float
    # Lab distance to each reference tone scaled to the same luma ("wood as bright as this").
    delta_wood: float
    delta_cork: float
    # Hue angle difference to each reference, degrees.
    hue_from_wood: float
    hue_from_cork: float


def same_luma(reference: tuple[float, float, float], target: float) -> np.ndarray:
    """The reference tone scaled in linear light to the given sRGB luma."""
    lin = to_linear(np.array(reference))
    lum = float(lin @ np.array([0.2126, 0.7152, 0.0722]))
    want = float(to_linear(np.array([target]))[0])
    scaled = np.clip(lin * want / lum, 0.0, 1.0)
    return 255 * np.where(
        scaled <= 0.0031308, scaled * 12.92, 1.055 * scaled ** (1 / 2.4) - 0.055
    )


def hue_gap(a: float, b: float) -> float:
    return float(abs((a - b + 180) % 360 - 180))


def stats(pixels: np.ndarray) -> Stats | None:
    """Stats of an (n, 3) array of sRGB pixels, or None when there are too few."""
    if len(pixels) < 200:
        return None
    median = np.median(pixels, axis=0)
    lum = luma(pixels)
    lab = to_lab(median)
    chroma = float(np.hypot(lab[1], lab[2]))
    hue = float(np.degrees(np.arctan2(lab[2], lab[1])) % 360)
    deltas: dict[str, float] = {}
    hues: dict[str, float] = {}
    for name, tone in REFERENCES.items():
        ref = to_lab(same_luma(tone, float(np.median(lum))))
        deltas[name] = float(np.linalg.norm(lab - ref))
        hues[name] = hue_gap(hue, float(np.degrees(np.arctan2(ref[2], ref[1])) % 360))
    return Stats(
        pixels=len(pixels),
        median=(int(median[0]), int(median[1]), int(median[2])),
        luma=round(float(np.median(lum)), 1),
        luma_p10=round(float(np.percentile(lum, 10)), 1),
        luma_p90=round(float(np.percentile(lum, 90)), 1),
        lightness=round(float(lab[0]), 1),
        chroma=round(chroma, 1),
        hue=round(hue, 1),
        delta_wood=round(deltas["wood"], 1),
        delta_cork=round(deltas["cork"], 1),
        hue_from_wood=round(hues["wood"], 1),
        hue_from_cork=round(hues["cork"], 1),
    )


def masks(view: str) -> tuple[np.ndarray, np.ndarray]:
    """The brass pixels in shade and in sun of a view, from the mask and light frames."""
    mask = load(OUT / "mask" / f"{view}.png")
    control = load(OUT / "control" / f"{view}.png")
    light = luma(load(OUT / "light" / f"{view}.png"))
    r, g, b = mask[..., 0], mask[..., 1], mask[..., 2]
    magenta = (r > g + 80) & (b > g + 80) & (np.abs(r - b) < 60)
    changed = np.abs(mask - control).max(axis=-1) > 40
    brass = magenta & changed
    # Drop the edge pixels: anti-aliasing mixes them with their neighbours.
    eroded = Image.fromarray((brass * 255).astype(np.uint8)).filter(
        ImageFilter.MinFilter(3)
    )
    inner = np.asarray(eroded) > 0
    return inner & (light < SHADE_LUMA), inner & (light > SUN_LUMA)


def mottle(frame: np.ndarray, shade: np.ndarray) -> float:
    """How blotchy the brass in shade is: the spread of its luma after a 6 px blur is taken
    away, against its median luma. Wood grain and cork pits raise it. The mask loses two more
    pixels at each edge, so the edges of a bar do not count."""
    inner = Image.fromarray((shade * 255).astype(np.uint8)).filter(
        ImageFilter.MinFilter(5)
    )
    keep = np.asarray(inner) > 0
    lum = luma(frame)
    lum8 = Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8), mode="L")
    blur = np.asarray(lum8.filter(ImageFilter.GaussianBlur(6)), dtype=np.float64)
    return round(float(np.std((lum - blur)[keep]) / np.median(lum[keep])), 3)


def measure() -> None:
    """Writes build/brass_study/stats.json and prints a table of the shade stats."""
    variants = sorted(
        path.name
        for path in OUT.iterdir()
        if path.is_dir() and path.name not in (*MEASURE_ONLY, "polished", "explore")
    )
    views = [f"{level}-{shot}" for level, shots in VIEWS.items() for shot in shots]
    result: dict[str, object] = {
        "references": REFERENCES,
        "shade_luma": SHADE_LUMA,
        "views": {},
    }
    for view in views:
        shade, sun = masks(view)
        entry: dict[str, object] = {
            "shade_pixels": int(shade.sum()),
            "sun_pixels": int(sun.sum()),
            "variants": {},
        }
        for variant in variants:
            frame = load(OUT / variant / f"{view}.png")
            in_shade = stats(frame[shade])
            in_sun = stats(frame[sun])
            entry["variants"][variant] = {
                "shade": asdict(in_shade) if in_shade else None,
                "sun": asdict(in_sun) if in_sun else None,
                "mottle": mottle(frame, shade),
            }
            if in_shade:
                print(
                    f"{view:16} {variant:10} shade n={in_shade.pixels:6} median={in_shade.median} "
                    f"L={in_shade.lightness:5} C={in_shade.chroma:5} h={in_shade.hue:5} "
                    f"dWood={in_shade.delta_wood:5} dCork={in_shade.delta_cork:5} "
                    f"luma p10/50/90={in_shade.luma_p10}/{in_shade.luma}/{in_shade.luma_p90}"
                )
        result["views"][view] = entry
        # The shade mask, for a look by eye.
        Image.fromarray((shade * 255).astype(np.uint8)).save(OUT / f"shade-{view}.png")
    (OUT / "stats.json").write_text(json.dumps(result, indent=2))


CROP = (768, 432)


def best_crop(weight: np.ndarray) -> tuple[int, int]:
    """The top-left corner of the CROP window that holds the most weight."""
    total = np.pad(weight.astype(np.float64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    w, h = CROP
    sums = total[h:, w:] - total[:-h, w:] - total[h:, :-w] + total[:-h, :-w]
    y, x = np.unravel_index(int(np.argmax(sums)), sums.shape)
    return int(x), int(y)


def save_pair(frame: Path, corner: tuple[int, int], out: Path, stem: str) -> None:
    """Saves a frame as <stem>.webp (1280 wide) and its CROP at 1:1 as <stem>-crop.webp."""
    with Image.open(frame) as image:
        rgb = image.convert("RGB")
        rgb.resize((1280, 720), Image.Resampling.LANCZOS).save(
            out / f"{stem}.webp", quality=84
        )
        x, y = corner
        rgb.crop((x, y, x + CROP[0], y + CROP[1])).save(
            out / f"{stem}-crop.webp", quality=88
        )


def export(out: Path) -> None:
    """Writes the page images into out/img/ and the stats into out/stats.json."""
    images = out / "img"
    images.mkdir(parents=True, exist_ok=True)
    stats_json = json.loads((OUT / "stats.json").read_text())
    crops: dict[str, tuple[int, int]] = {}
    for view, entry in stats_json["views"].items():
        shade, _ = masks(view)
        crops[view] = best_crop(shade)
        for variant in entry["variants"]:
            save_pair(
                OUT / variant / f"{view}.png", crops[view], images, f"{variant}-{view}"
            )
    for level, shots in POLISHED_VIEWS.items():
        for shot in shots:
            view = f"{level}-{shot}"
            folders = sorted((OUT / "polished").iterdir())
            frames = [load(folder / f"{view}.png") for folder in folders]
            differs = np.abs(frames[0] - frames[1]).max(axis=-1) > 30
            crops[f"polished-{view}"] = POLISHED_CROPS.get(view) or best_crop(differs)
            for folder in folders:
                save_pair(
                    folder / f"{view}.png",
                    crops[f"polished-{view}"],
                    images,
                    f"{folder.name}-{view}",
                )
    stats_json["crops"] = crops
    (out / "stats.json").write_text(json.dumps(stats_json, indent=1))


def main() -> None:
    command, *args = sys.argv[1:] or ["help"]
    match command:
        case "shoot":
            shoot(args)
        case "polished":
            polished()
        case "measure":
            measure()
        case "export" if args:
            export(Path(args[0]))
        case _:
            print(__doc__)
            sys.exit(2)


if __name__ == "__main__":
    main()
