# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright>=1.49", "pillow>=11"]
# ///
"""Render the UI mockups to PNG and make the thumbnails that index.html shows.

Usage: uv run docs/ui-mockups/render.py [filter ...]
A filter keeps the shots whose name contains it, for example `b-` or `hud`.
The loading screens (#138) are direction C only. Each also renders as `#climb` (the Ascent
climb) and at 4K, into png/4k/.
Needs Google Chrome on this machine and network access to Google Fonts.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
DIRECTIONS = ("a-brass", "b-glass", "c-chart")
SCREENS = ("hud", "ascent", "title", "levels", "pause", "settings", "results")
# Extra shots: output suffix -> page and URL fragment.
VARIANTS = {"hud-keys": "hud.html#keys"}
LOADING = ("loading-dial", "loading-horizon", "loading-limb")
SIZE = (1920, 1080)
THUMB_WIDTH = 1280


@dataclass(frozen=True)
class Shot:
    """One screen of one direction: its page URL and its output name."""

    name: str
    url: str
    # Device pixels per CSS pixel: 2 renders the 1920 x 1080 page at 3840 x 2160.
    scale: int = 1


def shots() -> list[Shot]:
    """List every shot: 7 screens and the variants for each direction, then the loading
    screens of direction C at both sizes."""
    result: list[Shot] = []
    for direction in DIRECTIONS:
        letter = direction.split("-")[0]
        pages = {screen: f"{screen}.html" for screen in SCREENS} | VARIANTS
        for suffix, page in pages.items():
            result.append(
                Shot(f"{letter}-{suffix}", f"{(ROOT / direction).as_uri()}/{page}")
            )
    chart = (ROOT / "c-chart").as_uri()
    for scale in (1, 2):
        for screen in LOADING:
            for suffix, fragment in (("", ""), ("-climb", "#climb")):
                url = f"{chart}/{screen}.html{fragment}"
                result.append(Shot(f"c-{screen}{suffix}", url, scale))
    return result


def main() -> None:
    filters = sys.argv[1:]
    wanted = [s for s in shots() if not filters or any(f in s.name for f in filters)]
    (ROOT / "png").mkdir(exist_ok=True)
    (ROOT / "thumbs").mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        pages = {
            scale: browser.new_page(
                viewport={"width": SIZE[0], "height": SIZE[1]},
                device_scale_factor=scale,
            )
            for scale in (1, 2)
        }
        for shot in wanted:
            page = pages[shot.scale]
            # A fragment-only change does not reload the page, so start from a blank page.
            page.goto("about:blank")
            page.goto(shot.url, wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            folder = ROOT / "png" / ("4k" if shot.scale == 2 else "")
            folder.mkdir(exist_ok=True)
            png = folder / f"{shot.name}.png"
            # An animation shows its first pose, so a shot is the same at every run.
            page.screenshot(path=png, animations="disabled")
            print(png.relative_to(ROOT))
            if shot.scale != 1:
                continue
            with Image.open(png) as image:
                height = round(image.height * THUMB_WIDTH / image.width)
                thumb = image.convert("RGB").resize(
                    (THUMB_WIDTH, height), Image.Resampling.LANCZOS
                )
                thumb.save(ROOT / "thumbs" / f"{shot.name}.webp", quality=82, method=6)
        browser.close()


if __name__ == "__main__":
    main()
