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
- the VRAM at 1080p does not rise from Low to Medium to High to Ultra. VRAM proves that the
  presets change real settings; the GPU time of a small level is too noisy for that.
The two GPU time budgets are for the RTX 5090; on another GPU they only report. Other GPU work
(a Blender render, ComfyUI) inflates the times and can fail the gates, so run it on an idle GPU.

Other agents' games share the GPU. Before each run the tool waits until no other Godot game runs
(QUIET_TIMEOUT_S, then it gives up). During a run it checks every WATCH_S seconds; a game that
starts marks the run as disturbed, and the tool repeats the run, at most MAX_REPEATS times. The
report and the run's JSON say how many runs were disturbed. A run that is still disturbed after
the last try fails with a message of its own: its numbers are not reliable.

Environment: GODOT (default godot) is the Godot binary.
"""

import json
import os
import signal
import subprocess
import sys
import time
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
QUIET_TIMEOUT_S = 20 * 60
QUIET_POLL_S = 5.0
WATCH_S = 1.0
RUN_TIMEOUT_S = 300.0
MAX_REPEATS = 2


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
    disturbed: int = 0
    clean: bool = True


class GpuBusyError(RuntimeError):
    """Another Godot game kept the GPU busy until QUIET_TIMEOUT_S."""


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


def is_game(argv: list[str]) -> bool:
    """Tells whether a command line is a Godot game that uses the GPU. The binary name starts
    with `godot`. An editor, the project manager and `--headless` runs (imports, exports, tests)
    use no real GPU time, so they do not count."""
    if not argv or not Path(argv[0]).name.lower().startswith("godot"):
        return False
    skipped = {"--headless", "--editor", "-e", "--project-manager", "-p"}
    return skipped.isdisjoint(argv[1:])


def other_games() -> list[int]:
    """Returns the pids of Godot games that this tool did not start (reads /proc, Linux only)."""
    parent: dict[int, int] = {}
    games: list[int] = []
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            # The stat line is `pid (comm) state ppid ...`; comm can hold spaces and brackets.
            ppid = int(entry.joinpath("stat").read_text().rpartition(")")[2].split()[1])
            cmdline = entry.joinpath("cmdline").read_bytes()
        except (OSError, ValueError, IndexError):  # the process ended while we read it
            continue
        parent[int(entry.name)] = ppid
        if is_game(cmdline.decode(errors="replace").split("\0")):
            games.append(int(entry.name))

    def is_ours(pid: int) -> bool:
        while pid > 1:
            if pid == os.getpid():
                return True
            pid = parent.get(pid, 0)
        return False

    return [pid for pid in games if not is_ours(pid)]


def wait_for_quiet(label: str) -> None:
    """Blocks until no other Godot game runs. Prints one line when it has to wait. Raises
    GpuBusyError after QUIET_TIMEOUT_S."""
    deadline = time.monotonic() + QUIET_TIMEOUT_S
    waiting = False
    while games := other_games():
        if time.monotonic() > deadline:
            raise GpuBusyError(
                f"{label}: other Godot games (pids {games}) still ran after "
                f"{QUIET_TIMEOUT_S / 60:.0f} min; run it when the GPU is quiet"
            )
        if not waiting:
            print(
                f"waiting for other Godot games (pids {games}) before {label}",
                flush=True,
            )
            waiting = True
        time.sleep(QUIET_POLL_S)


def run_watched(command: list[str]) -> tuple[subprocess.CompletedProcess[str], bool]:
    """Runs a command (timeout RUN_TIMEOUT_S) and returns it with whether another Godot game
    started while it ran. Checks every WATCH_S seconds. The command runs in its own process
    group, so a timeout kills gamescope and the game it started."""
    start = time.monotonic()
    disturbed = False
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        while True:
            try:
                stdout, stderr = process.communicate(timeout=WATCH_S)
                break
            except subprocess.TimeoutExpired as error:
                if time.monotonic() - start > RUN_TIMEOUT_S:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    raise subprocess.TimeoutExpired(command, RUN_TIMEOUT_S) from error
                disturbed = disturbed or bool(other_games())
    done = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    return done, disturbed or bool(other_games())


def measure(level: str, run: Run) -> Result:
    """Runs the perf scene for one level and one run, and returns its report."""
    out = OUT / f"{level}-{run.preset}-{run.height}.json"
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
    disturbed = 0
    while True:
        wait_for_quiet(f"{level} {run.name}")
        out.unlink(missing_ok=True)
        done, was_disturbed = run_watched(command)
        if not was_disturbed:
            break
        disturbed += 1
        if disturbed > MAX_REPEATS:
            break
        print(f"{level} {run.name}: another game started; repeating", flush=True)
    clean = disturbed <= MAX_REPEATS
    if done.returncode != 0 or not out.exists():
        log = f"{done.stdout}{done.stderr}"
        raise RuntimeError(
            f"{level} {run.name}: failed (exit {done.returncode})\n{log}"
        )
    check_shaders(f"{done.stdout}\n{done.stderr}", f"{level} {run.name}")
    report = json.loads(out.read_text())
    if (report["width"], report["height"]) != (run.width, run.height):
        size = f"{report['width']}x{report['height']}"
        raise RuntimeError(f"{level} {run.name}: rendered at {size}")
    report["disturbed_runs"] = disturbed
    report["clean"] = clean
    out.write_text(json.dumps(report, indent=2))
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
        disturbed,
        clean,
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
    vram = [hd[preset].vram_mb for preset in ORDER]
    if any(a >= b for a, b in pairwise(vram)):
        order = ", ".join(f"{p} {v:.0f}" for p, v in zip(ORDER, vram, strict=True))
        found.append(f"1080p VRAM MB does not rise from Low to Ultra: {order}")
    for r in results:
        if not r.clean:
            found.append(
                f"{r.run.name} was disturbed by another game in all {r.disturbed} tries; "
                "its numbers are not reliable. Run again when no game runs"
            )
    return [f"{level}: {problem}" for problem in found]


def main() -> None:
    """Measures the levels on the command line (all when none) and exits 1 on a failed gate."""
    OUT.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []
    for level in level_ids(sys.argv[1:]):
        try:
            results = [measure(level, run) for run in RUNS]
        except GpuBusyError as error:
            failed.append(str(error))
            break
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            failed.append(f"{level}: {error}")
            continue
        print(f"{level} on {results[0].adapter}: GPU ms mean / p50 / p99, VRAM MB")
        for r in results:
            note = f"  disturbed {r.disturbed}x" if r.disturbed else ""
            print(
                f"  {r.run.name:12} {r.mean:6.3f} {r.p50:6.3f} {r.p99:6.3f} {r.vram_mb:7.0f}{note}"
            )
        print(
            f"  disturbed runs: {sum(r.disturbed for r in results)} of {len(results)}"
        )
        failed += problems(level, results)
    for problem in failed:
        print(f"FAIL {problem}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
