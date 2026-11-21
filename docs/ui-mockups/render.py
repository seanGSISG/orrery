# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright>=1.49", "pillow>=11"]
# ///
"""Render the UI mockups to PNG and make the thumbnails that index.html shows.

Usage: uv run docs/ui-mockups/render.py [filter ...]
A filter keeps the shots whose name contains it, for example `b-` or `hud`.
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
SIZE = (1920, 1080)
THUMB_WIDTH = 1280


@dataclass(frozen=True)
class Shot:
    """One screen of one direction: its page URL and its output name."""

    name: str
    url: str


def shots() -> list[Shot]:
    """List every shot: 7 screens and the variants, for each direction."""
    result: list[Shot] = []
    for direction in DIRECTIONS:
        letter = direction.split("-")[0]
        pages = {screen: f"{screen}.html" for screen in SCREENS} | VARIANTS
        for suffix, page in pages.items():
            result.append(
                Shot(f"{letter}-{suffix}", f"{(ROOT / direction).as_uri()}/{page}")
            )
    return result


def main() -> None:
    filters = sys.argv[1:]
    wanted = [s for s in shots() if not filters or any(f in s.name for f in filters)]
    (ROOT / "png").mkdir(exist_ok=True)
    (ROOT / "thumbs").mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(
            viewport={"width": SIZE[0], "height": SIZE[1]}, device_scale_factor=1
        )
        for shot in wanted:
            # A fragment-only change does not reload the page, so start from a blank page.
            page.goto("about:blank")
            page.goto(shot.url, wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            png = ROOT / "png" / f"{shot.name}.png"
            page.screenshot(path=png)
            with Image.open(png) as image:
                height = round(image.height * THUMB_WIDTH / image.width)
                thumb = image.convert("RGB").resize(
                    (THUMB_WIDTH, height), Image.Resampling.LANCZOS
                )
                thumb.save(ROOT / "thumbs" / f"{shot.name}.webp", quality=82, method=6)
            print(png.relative_to(ROOT))
        browser.close()


if __name__ == "__main__":
    main()
