# /// script
# requires-python = ">=3.13"
# ///
"""Checks GPU frame time and VRAM per graphics preset (docs/design/visual-quality.md §8).

Usage: `just perf [id ...]`. With no ids it checks every level script `levels/<tier>/<id>.py`.

For each level it runs game/test/perf/perf_run.tscn once per run below, each in its own
`gamescope --backend headless` at the run's resolution. The scene flies a camera along the
level's shots and once around the marble, and reports the GPU time per frame
(RenderingServer.viewport_get_measured_render_time_gpu: the GPU time of the game window's
viewport, without the compositor) and the VRAM (Performance.RENDER_VIDEO_MEM_USED). The High
run at 1080p also saves the `motion` pair into build/gallery/<id>/motion/ for `just gallery`.

It fails when:
- Medium at 1080p has a 99th percentile above MEDIUM_P99_MS, or uses more than MAX_VRAM_MB,
- Ultra at 4K has a 99th percentile above ULTRA_4K_P99_MS,
- the mean GPU time at 1080p does not rise from Low to Medium to High to Ultra.
The two GPU time budgets are for the RTX 5090; on another GPU they only report. Run it on an
idle GPU: other GPU work (a Blender render, ComfyUI) inflates the times and can fail the gates.

Environment: GODOT (default godot) is the Godot binary.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "perf"
GALLERY = ROOT / "build" / "gallery"
SCENE = "res://test/perf/perf_run.tscn"
BUDGET_GPU = "RTX 5090"
MEDIUM_P99_MS = 3.0
ULTRA_4K_P99_MS = 16.7
MAX_VRAM_MB = 4096.0
ORDER = ["low", "medium", "high", "ultra"]


@dataclass(frozen=True)
class Run:
    """One preset at one resolution."""

    preset: str
    width: int
    height: int
    motion: bool = False

    @property
    def name(self) -> str:
        return f"{self.preset} {self.height}p"


RUNS = [
    Run("low", 1920, 1080),
    Run("medium", 1920, 1080),
    Run("high", 1920, 1080, motion=True),
    Run("ultra", 1920, 1080),
    Run("high", 2560, 1440),
    Run("ultra", 3840, 2160),
]


@dataclass(frozen=True)
class Result:
    """What one run measured: GPU ms (mean, p50, p99) and VRAM in MB."""

    run: Run
    adapter: str
    mean: float
    p50: float
    p99: float
    vram_mb: float


def level_ids(ids: list[str]) -> list[str]:
    """Returns the given ids, or every level script's id when there are none."""
    return ids or sorted(script.stem for script in ROOT.glob("levels/*/*.py"))


def check_shaders(log: str, name: str) -> None:
    """Raises RuntimeError with the first shader compile errors in the game log (the harness
    CLI holds the one check that `just gallery` and `just ui-shots` also use)."""
    command = ["uv", "run", "--quiet", "--project", str(ROOT / "tools/harness")]
    check = subprocess.run(
        [*command, "orrery-harness", "check-log"],
        input=log,
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        raise RuntimeError(f"{name}: {check.stderr.strip()}")


def measure(level: str, run: Run) -> Result:
    """Runs the perf scene for one level and one run, and returns its report."""
    out = OUT / f"{level}-{run.preset}-{run.height}.json"
    out.unlink(missing_ok=True)
    size = ["-W", str(run.width), "-H", str(run.height)]
    godot = os.environ.get("GODOT", "godot")
    args = ["--level", level, "--preset", run.preset, "--out", str(out)]
    if run.motion:
        args += ["--motion", str(GALLERY / level / "motion")]
    command = [
        *("gamescope", "--backend", "headless", *size, "--"),
        *(
            godot,
            # Silent: automated runs play no sound on the speakers.
            "--audio-driver",
            "Dummy",
            "--path",
            str(ROOT / "game"),
            "--resolution",
            f"{run.width}x{run.height}",
        ),
        *(SCENE, "--", *args),
    ]
    done = subprocess.run(
        command, capture_output=True, text=True, timeout=300, check=False
    )
    if done.returncode != 0 or not out.exists():
        log = f"{done.stdout}{done.stderr}"
        raise RuntimeError(
            f"{level} {run.name}: failed (exit {done.returncode})\n{log}"
        )
    check_shaders(f"{done.stdout}{done.stderr}", f"{level} {run.name}")
    report = json.loads(out.read_text())
    if (report["width"], report["height"]) != (run.width, run.height):
        size = f"{report['width']}x{report['height']}"
        raise RuntimeError(f"{level} {run.name}: rendered at {size}")
    gpu = report["gpu_ms"]
    if not all(gpu[key] > 0.0 for key in ("mean", "p50", "p99")):
        raise RuntimeError(f"{level} {run.name}: no GPU time measured: {gpu}")
    return Result(
        run,
        report["adapter"],
        gpu["mean"],
        gpu["p50"],
        gpu["p99"],
        report["vram_mb"],
    )


def problems(level: str, results: list[Result]) -> list[str]:
    """Returns the failed gates for one level's results."""
    found: list[str] = []
    calibrated = BUDGET_GPU in results[0].adapter
    hd = {r.run.preset: r for r in results if r.run.height == 1080}
    medium = hd["medium"]
    if calibrated and medium.p99 > MEDIUM_P99_MS:
        found.append(f"Medium 1080p p99 {medium.p99:.2f} ms > {MEDIUM_P99_MS} ms")
    if medium.vram_mb > MAX_VRAM_MB:
        found.append(f"Medium VRAM {medium.vram_mb:.0f} MB > {MAX_VRAM_MB:.0f} MB")
    ultra = next(r for r in results if r.run == Run("ultra", 3840, 2160))
    if calibrated and ultra.p99 > ULTRA_4K_P99_MS:
        found.append(f"Ultra 4K p99 {ultra.p99:.2f} ms > {ULTRA_4K_P99_MS} ms")
    costs = [hd[preset].mean for preset in ORDER]
    if any(a >= b for a, b in pairwise(costs)):
        order = ", ".join(f"{p} {c:.3f}" for p, c in zip(ORDER, costs, strict=True))
        found.append(f"1080p mean GPU ms do not rise from Low to Ultra: {order}")
    return [f"{level}: {problem}" for problem in found]


def main() -> None:
    """Measures the levels on the command line (all when none) and exits 1 on a failed gate."""
    OUT.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []
    for level in level_ids(sys.argv[1:]):
        try:
            results = [measure(level, run) for run in RUNS]
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            failed.append(f"{level}: {error}")
            continue
        print(f"{level} on {results[0].adapter}: GPU ms mean / p50 / p99, VRAM MB")
        for r in results:
            print(
                f"  {r.run.name:12} {r.mean:6.3f} {r.p50:6.3f} {r.p99:6.3f} {r.vram_mb:7.0f}"
            )
        failed += problems(level, results)
    for problem in failed:
        print(f"FAIL {problem}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
