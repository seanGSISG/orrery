"""Command line: `orrery-music generate|build|review|all [--track ID]`.

- generate: render backing takes through ComfyUI (one job at a time).
- build: analyse every take, mix the hook and clockwork layer over it, run the checks,
  and keep the best 3-5 passing candidates per track.
- review: write out/review/index.html from the kept candidates.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from orrery_music.brief import TRACKS
from orrery_music.generate import generate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"


def main() -> None:
    parser = argparse.ArgumentParser(prog="orrery-music")
    parser.add_argument("command", choices=["generate", "build", "review", "all"])
    parser.add_argument(
        "--track", choices=sorted(TRACKS), action="append", help="default: every track"
    )
    parser.add_argument("--ace", type=int, default=14, help="ACE-Step takes per track")
    parser.add_argument(
        "--sa3", type=int, default=8, help="Stable Audio 3 takes per track"
    )
    args = parser.parse_args()
    tracks = [TRACKS[t] for t in (args.track or sorted(TRACKS))]
    if args.command in ("generate", "all"):
        for track in tracks:
            generate(track, OUT, args.ace, args.sa3)
    if args.command in ("build", "all"):
        from orrery_music.build import build

        for track in tracks:
            build(track, OUT, ROOT)
    if args.command in ("review", "all"):
        from orrery_music.review import write_review

        write_review(ROOT)
