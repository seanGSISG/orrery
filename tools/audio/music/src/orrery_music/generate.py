"""Render backing-track takes through ComfyUI and record how each one was made.

Each take lands in `out/takes/<track>/<take id>.flac` with a JSON record next to it
(model, prompt, seed, settings, the exact ComfyUI workflow). Existing takes are skipped,
so the command is safe to re-run after an interruption.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

from orrery_music.brief import Track
from orrery_music.comfy import ComfyError, comfy_version, run_take, workflow


def generate(track: Track, out: Path, ace_takes: int, sa3_takes: int) -> list[Path]:
    """Render the track's missing takes one at a time and return every take file."""
    files: list[Path] = []
    for take_id, req in track.requests(ace_takes, sa3_takes):
        flac = out / "takes" / track.id / f"{take_id}.flac"
        record = flac.with_suffix(".json")
        if flac.exists() and record.exists():
            files.append(flac)
            continue
        start = time.monotonic()
        try:
            run_take(req, flac)
        except ComfyError as err:
            print(f"{take_id}: ComfyUI failed: {err}")
            continue
        record.write_text(
            json.dumps(
                {
                    "take": take_id,
                    "track": track.id,
                    **asdict(req),
                    "render_seconds": round(time.monotonic() - start, 1),
                    "comfyui": comfy_version(),
                    "workflow": workflow(req, f"orrery/{take_id}"),
                },
                indent=2,
            )
        )
        print(f"{take_id}: {time.monotonic() - start:.0f} s")
        files.append(flac)
    return files
