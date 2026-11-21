# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2.2", "soundfile>=0.13"]
# ///
"""Synthesises every Orrery sound effect and the placeholder music loops, then checks them.

Run: uv run --script tools/audio/sfx/synth_sfx.py [--montage PATH]

1. Each sound in SOUNDS is built from sines, inharmonic bells and filtered noise, in a
   clockwork style: ticks, ratchets, chimes and music-box notes. No samples are used.
2. Each sound is normalised to its loudness target (the loudest 50 ms window) with a peak
   cap, and written as mono OGG Vorbis to game/audio/sfx/<name>.ogg.
3. The placeholder music loops (120 BPM, 2 bars) go to game/test/audio/loops/. The music
   tests use them.
4. The check decodes every file again and fails on clipping, silence, a late start, a click
   at the end or a bad length. It prints one row per file.
5. --montage PATH also writes all sounds one after the other into one OGG file, to listen to.

The Godot import settings (loop, bpm, beat_count) live in the .ogg.import files beside the
sounds; this script does not write them. A random seed makes the audio the same on each run,
but the OGG container gets a new serial number, so the files change bytes each time.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt
import soundfile as sf

type Signal = npt.NDArray[np.float64]

RATE: int = 44100
ROOT: Path = Path(__file__).resolve().parents[3]
SFX_DIR: Path = ROOT / "game/audio/sfx"
LOOP_DIR: Path = ROOT / "game/test/audio/loops"
PEAK_CAP_DB: float = -1.5
WINDOW_S: float = 0.05


@dataclass(frozen=True)
class Sound:
    """One sound file: its name, how to render it, and its loudness target in dBFS."""

    name: str
    render: Callable[[np.random.Generator], Signal]
    loudness_db: float
    loop: bool = False


@dataclass(frozen=True)
class Report:
    """The measures of one decoded file, and the failed checks."""

    name: str
    seconds: float
    peak_db: float
    loudness_db: float
    onset_ms: float
    tail_db: float
    failures: list[str]


# --- Building blocks ---


def samples(seconds: float) -> int:
    """Returns the sample count of a duration."""
    return round(seconds * RATE)


def times(seconds: float) -> Signal:
    """Returns the time of each sample of a duration, s."""
    return np.arange(samples(seconds), dtype=np.float64) / RATE


def tone(freq: float | Signal, seconds: float) -> Signal:
    """Returns a sine; freq is a constant or one frequency per sample, Hz."""
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (samples(seconds),))
    return np.sin(2.0 * np.pi * np.cumsum(f) / RATE)


def sweep(start: float, end: float, seconds: float) -> Signal:
    """Returns a frequency per sample that glides from start to end on a log scale, Hz."""
    return start * (end / start) ** (times(seconds) / seconds)


def decay(seconds: float, time_constant: float, attack: float = 0.002) -> Signal:
    """Returns an envelope with a linear attack and an exponential decay."""
    t = times(seconds)
    return np.minimum(t / attack, 1.0) * np.exp(-t / time_constant)


def swell(seconds: float, rise: float, fall: float) -> Signal:
    """Returns an envelope that rises over rise seconds, then decays with fall."""
    t = times(seconds)
    return np.where(t < rise, (t / rise) ** 2, np.exp(-(t - rise) / fall))


def noise(seconds: float, rng: np.random.Generator) -> Signal:
    """Returns white noise."""
    return rng.standard_normal(samples(seconds))


def band(x: Signal, low: float, high: float) -> Signal:
    """Returns x through a zero-phase band-pass with soft (4th-order) edges, Hz."""
    n = 1 << int(np.ceil(np.log2(len(x) * 2)))
    spectrum = np.fft.rfft(x, n)
    f = np.maximum(np.fft.rfftfreq(n, 1.0 / RATE), 1e-6)
    gain = 1.0 / np.sqrt(1.0 + (low / f) ** 8) / np.sqrt(1.0 + (f / high) ** 8)
    return np.fft.irfft(spectrum * gain, n)[: len(x)]


def bell(
    freq: float, seconds: float, partials: Sequence[tuple[float, float, float]]
) -> Signal:
    """Returns a struck metal tone; each partial is (ratio, gain, decay time constant)."""
    out = np.zeros(samples(seconds))
    for ratio, gain, time_constant in partials:
        out += gain * tone(freq * ratio, seconds) * decay(seconds, time_constant, 0.001)
    return out


def music_box(freq: float, seconds: float = 0.6) -> Signal:
    """Returns one music-box (comb and pin) note."""
    return bell(freq, seconds, [(1.0, 1.0, 0.22), (3.0, 0.25, 0.07), (5.4, 0.12, 0.03)])


def click(
    rng: np.random.Generator, low: float = 1500.0, high: float = 9000.0
) -> Signal:
    """Returns one clockwork tick: a 6 ms burst of band-passed noise."""
    return band(noise(0.006, rng), low, high) * decay(0.006, 0.0012, 0.0003)


def thump(start: float, end: float, seconds: float, time_constant: float) -> Signal:
    """Returns a low body hit: a falling sine with a fast decay."""
    return tone(sweep(start, end, seconds), seconds) * decay(seconds, time_constant)


def mix(seconds: float, parts: Sequence[tuple[float, Signal]]) -> Signal:
    """Returns a buffer of seconds with each (start time, signal) part added in."""
    out = np.zeros(samples(seconds))
    for at, part in parts:
        start = samples(at)
        end = min(start + len(part), len(out))
        out[start:end] += part[: end - start]
    return out


def ratchet(
    rng: np.random.Generator, at: Sequence[float], low: float, high: float
) -> list[tuple[float, Signal]]:
    """Returns one tick for each time in at, as mix() parts."""
    return [(t, click(rng, low, high)) for t in at]


def periodic(
    seconds: float, low: float, high: float, rng: np.random.Generator
) -> Signal:
    """Returns band-limited noise that loops without a seam: random phases, one period."""
    n = samples(seconds)
    f = np.maximum(np.fft.rfftfreq(n, 1.0 / RATE), 1e-6)
    gain = 1.0 / np.sqrt(1.0 + (low / f) ** 4) / np.sqrt(1.0 + (f / high) ** 4)
    phase = rng.uniform(0.0, 2.0 * np.pi, len(f))
    return np.fft.irfft(gain * np.exp(1j * phase), n)


# --- The sounds ---


def roll(rng: np.random.Generator) -> Signal:
    """A 2 s seamless rumble with a little grit; the game sets its volume and pitch."""
    seconds = 2.0
    rumble = periodic(seconds, 50.0, 600.0, rng)
    grit = periodic(seconds, 1500.0, 4000.0, rng)
    wobble = 1.0 + 0.15 * np.sin(2.0 * np.pi * 7.0 * times(seconds))
    return (rumble / np.std(rumble) + 0.12 * grit / np.std(grit)) * wobble


def jump(rng: np.random.Generator) -> Signal:
    """A springy upward chirp with a release tick."""
    d = 0.28
    body = tone(sweep(260.0, 720.0, d), d) * decay(d, 0.07)
    spring = 0.3 * tone(sweep(900.0, 1500.0, d), d) * decay(d, 0.04)
    return mix(d, [(0.0, body + spring), (0.0, 0.5 * click(rng))])


def land_soft(rng: np.random.Generator) -> Signal:
    """A soft low thud and a short scuff."""
    d = 0.25
    scuff = 0.4 * band(noise(d, rng), 100.0, 1200.0) * decay(d, 0.02)
    return thump(120.0, 60.0, d, 0.05) + scuff


def land_hard(rng: np.random.Generator) -> Signal:
    """A heavy thud with a metal clank on top."""
    d = 0.5
    clank = 0.35 * bell(
        310.0, d, [(1.0, 1.0, 0.12), (2.76, 0.6, 0.08), (5.4, 0.35, 0.05)]
    )
    crash = 0.6 * band(noise(d, rng), 80.0, 3000.0) * decay(d, 0.03)
    return thump(140.0, 55.0, d, 0.09) + clank + crash


def bounce(rng: np.random.Generator) -> Signal:
    """A light tap with a short ring."""
    d = 0.22
    ring = 0.25 * bell(620.0, d, [(1.0, 1.0, 0.05), (2.76, 0.4, 0.03)])
    return mix(
        d,
        [
            (0.0, thump(200.0, 120.0, d, 0.035) + ring),
            (0.0, 0.3 * click(rng, 800.0, 5000.0)),
        ],
    )


def bumper(rng: np.random.Generator) -> Signal:
    """A bright ping with a springy boing."""
    d = 0.6
    ping = bell(520.0, d, [(1.0, 1.0, 0.18), (2.0, 0.5, 0.12), (3.0, 0.3, 0.08)])
    wobble = 1.0 + 0.03 * np.sin(2.0 * np.pi * 28.0 * times(d))
    boing = 0.6 * tone(sweep(700.0, 380.0, d) * wobble, d) * decay(d, 0.12)
    return mix(d, [(0.0, ping + boing), (0.0, 0.6 * click(rng))])


def steam_vent(rng: np.random.Generator) -> Signal:
    """A hiss of steam over a low puff."""
    d = 0.9
    hiss = band(noise(d, rng), 2500.0, 9000.0) * swell(d, 0.03, 0.35)
    puff = 0.7 * band(noise(d, rng), 80.0, 500.0) * decay(d, 0.08, 0.01)
    return hiss + puff


def pendulum(rng: np.random.Generator) -> Signal:
    """A heavy clang of a big bell weight, with a thud."""
    d = 1.3
    clang = bell(
        170.0,
        d,
        [(1.0, 1.0, 0.45), (2.76, 0.7, 0.3), (5.4, 0.45, 0.18), (8.93, 0.3, 0.1)],
    )
    hit = 0.5 * band(noise(0.05, rng), 200.0, 4000.0) * decay(0.05, 0.01, 0.0005)
    return mix(d, [(0.0, clang), (0.0, thump(110.0, 50.0, 0.4, 0.08)), (0.0, hit)])


def trapdoor(rng: np.random.Generator) -> Signal:
    """A latch ratchet, then the door drops open with a wooden thunk."""
    d = 0.7
    latch = ratchet(rng, [0.0, 0.04, 0.075, 0.105, 0.13], 600.0, 4000.0)
    knock = 0.6 * band(noise(0.2, rng), 100.0, 900.0) * decay(0.2, 0.03)
    return mix(d, [*latch, (0.18, thump(150.0, 70.0, 0.5, 0.06)), (0.18, knock)])


def tile_crack(rng: np.random.Generator) -> Signal:
    """Stone cracks: a few sharp snaps that come faster."""
    d = 0.45
    at = np.cumsum(np.linspace(0.06, 0.015, 9)) - 0.06
    parts = [(float(t), rng.uniform(0.4, 1.0) * click(rng, 800.0, 6000.0)) for t in at]
    return mix(d, [*parts, (0.0, 0.5 * thump(220.0, 120.0, 0.12, 0.02))])


def tile_fall(rng: np.random.Generator) -> Signal:
    """A tile breaks away: a crumble of rumble and falling bits."""
    d = 0.9
    rumble = band(noise(d, rng), 60.0, 700.0) * swell(d, 0.02, 0.3)
    bits = [
        (float(t), 0.6 * np.exp(-t / 0.4) * click(rng, 400.0, 3000.0))
        for t in np.sort(rng.uniform(0.0, 0.7, 12))
    ]
    return mix(d, [(0.0, rumble), *bits])


def gem(_rng: np.random.Generator) -> Signal:
    """Two quick music-box notes up a fifth."""
    return mix(0.7, [(0.0, music_box(1318.5)), (0.07, music_box(1975.5))])


def egg(_rng: np.random.Generator) -> Signal:
    """A rising music-box arpeggio: the egg opens."""
    notes = [1046.5, 1318.5, 1568.0, 2093.0, 2637.0]
    return mix(1.6, [(0.09 * i, music_box(f, 1.0)) for i, f in enumerate(notes)])


def powerup_pickup(rng: np.random.Generator) -> Signal:
    """A ratchet that winds up, then a chime."""
    at = 0.25 - np.cumsum(np.linspace(0.045, 0.02, 8))[::-1] + 0.02
    ticks = [
        (float(t), click(rng, 1000.0 + 300.0 * i, 8000.0)) for i, t in enumerate(at)
    ]
    chime = 0.8 * (music_box(1568.0) + 0.6 * music_box(2349.3))
    return mix(0.9, [*ticks, (0.27, chime)])


def powerup_use(rng: np.random.Generator) -> Signal:
    """A coil spring lets go: a wobbling sproing over a whoosh."""
    d = 0.6
    t = times(d)
    wobble = 1.0 + 0.25 * np.sin(2.0 * np.pi * 18.0 * t) * np.exp(-t / 0.2)
    sproing = tone(sweep(400.0, 900.0, d) * wobble, d) * decay(d, 0.18)
    whoosh = 0.5 * band(noise(d, rng), 600.0, 4000.0) * swell(d, 0.05, 0.12)
    return mix(d, [(0.0, sproing + whoosh), (0.0, click(rng))])


def checkpoint(rng: np.random.Generator) -> Signal:
    """A clock tick and a two-tone chime."""
    partials = [(1.0, 1.0, 0.5), (2.0, 0.4, 0.25), (3.0, 0.2, 0.12)]
    return mix(
        1.2,
        [
            (0.0, 0.6 * click(rng)),
            (0.03, bell(784.0, 1.1, partials)),
            (0.18, bell(1174.7, 1.0, partials)),
        ],
    )


def finish_open(rng: np.random.Generator) -> Signal:
    """Gears turn the gate open: steady ticks, then a rising chord."""
    ticks = ratchet(rng, [0.06 * i for i in range(10)], 700.0, 5000.0)
    chord = [
        (0.6 + 0.1 * i, 0.7 * music_box(f, 0.8))
        for i, f in enumerate([523.3, 659.3, 784.0])
    ]
    return mix(1.4, [*ticks, *chord])


def finish_reach(_rng: np.random.Generator) -> Signal:
    """A short bell fanfare: an arpeggio up into a held major chord."""
    partials = [(1.0, 1.0, 0.8), (2.0, 0.35, 0.4), (3.0, 0.15, 0.2)]
    notes = [(0.0, 1046.5), (0.1, 1318.5), (0.2, 1568.0)]
    chord = 0.5 * np.sum(
        [bell(f, 1.8, partials) for f in [1046.5, 1318.5, 1568.0, 2093.0]], axis=0
    )
    return mix(
        2.2, [*((t, 0.7 * bell(f, 0.6, partials)) for t, f in notes), (0.35, chord)]
    )


def respawn(rng: np.random.Generator) -> Signal:
    """A rising swell that lands on a tick and a chime: the marble is back."""
    d = 0.45
    rise = 0.5 * band(noise(d, rng), 800.0, 6000.0) * np.minimum(times(d) / d, 1.0) ** 2
    lift = 0.3 * tone(sweep(300.0, 900.0, d), d) * np.minimum(times(d) / d, 1.0)
    tick = 0.4 * click(rng)
    return mix(
        1.1,
        [
            (0.0, tick),
            (0.0, rise + lift),
            (0.45, click(rng)),
            (0.45, music_box(1760.0, 0.65)),
        ],
    )


def ui_move(rng: np.random.Generator) -> Signal:
    """A tiny clock tick for moving between menu items."""
    return mix(
        0.06,
        [
            (0.0, click(rng, 2000.0, 8000.0)),
            (0.0, 0.3 * tone(2400.0, 0.06) * decay(0.06, 0.01)),
        ],
    )


def ui_select(rng: np.random.Generator) -> Signal:
    """A tick and a soft chime for choosing a menu item."""
    return mix(0.5, [(0.0, click(rng)), (0.0, 0.6 * music_box(1760.0, 0.5))])


def ui_back(rng: np.random.Generator) -> Signal:
    """A lower tock for going back."""
    body = 0.5 * tone(sweep(600.0, 400.0, 0.15), 0.15) * decay(0.15, 0.02)
    return mix(0.15, [(0.0, click(rng, 500.0, 2500.0)), (0.0, body)])


SOUNDS: list[Sound] = [
    Sound("roll", roll, -16.0, loop=True),
    Sound("jump", jump, -15.0),
    Sound("land_soft", land_soft, -16.0),
    Sound("land_hard", land_hard, -12.0),
    Sound("bounce", bounce, -16.0),
    Sound("bumper", bumper, -12.0),
    Sound("steam_vent", steam_vent, -16.0),
    Sound("pendulum", pendulum, -12.0),
    Sound("trapdoor", trapdoor, -14.0),
    Sound("tile_crack", tile_crack, -16.0),
    Sound("tile_fall", tile_fall, -15.0),
    Sound("gem", gem, -15.0),
    Sound("egg", egg, -15.0),
    Sound("powerup_pickup", powerup_pickup, -15.0),
    Sound("powerup_use", powerup_use, -14.0),
    Sound("checkpoint", checkpoint, -15.0),
    Sound("finish_open", finish_open, -15.0),
    Sound("finish_reach", finish_reach, -13.0),
    Sound("respawn", respawn, -15.0),
    Sound("ui_move", ui_move, -24.0),
    Sound("ui_select", ui_select, -20.0),
    Sound("ui_back", ui_back, -22.0),
]


# --- Placeholder music loops ---

LOOP_BPM: float = 120.0
LOOP_BEATS: int = 8


def placeholder_loop(root: float, rng: np.random.Generator) -> Signal:
    """A 2-bar loop at LOOP_BPM: a held chord on root and a tick on each beat. It loops
    without a seam because every partial has a whole number of cycles in the loop."""
    seconds = LOOP_BEATS * 60.0 / LOOP_BPM
    pad = np.mean([tone(root * ratio, seconds) for ratio in (1.0, 1.5, 2.0)], axis=0)
    ticks = ratchet(
        rng, [i * 60.0 / LOOP_BPM for i in range(LOOP_BEATS)], 1500.0, 9000.0
    )
    return 0.3 * pad + mix(seconds, ticks)


LOOPS: dict[str, float] = {"zone_a": 220.0, "zone_b": 330.0}


# --- Output and checks ---


def loudness_db(x: Signal) -> float:
    """Returns the RMS of the loudest WINDOW_S window, dBFS."""
    w = samples(WINDOW_S)
    if len(x) < w:
        return to_db(float(np.sqrt(np.mean(x**2))))
    power = np.convolve(x**2, np.ones(w) / w, mode="valid")
    return to_db(float(np.sqrt(np.max(power))))


def to_db(value: float) -> float:
    """Returns an amplitude in dBFS; -inf for zero."""
    return float(20.0 * np.log10(value)) if value > 0.0 else float("-inf")


def finish(x: Signal, target_db: float, loop: bool) -> Signal:
    """Fades the edges of a one-shot, then sets the loudness to target_db, under the peak cap."""
    if not loop:
        fade = np.minimum(np.arange(len(x)) / samples(0.001), 1.0)
        fade *= np.minimum(np.arange(len(x))[::-1] / samples(0.015), 1.0)
        x = x * fade
    gain_db = min(
        target_db - loudness_db(x), PEAK_CAP_DB - to_db(float(np.max(np.abs(x))))
    )
    return x * 10.0 ** (gain_db / 20.0)


def write(path: Path, x: Signal) -> None:
    """Writes x as mono OGG Vorbis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, x.astype(np.float32), RATE, format="OGG", subtype="VORBIS")


def decode(path: Path) -> tuple[Signal, int]:
    """Reads the first channel of an audio file, and its sample rate."""
    data, rate = sf.read(path, dtype="float64", always_2d=True)
    return np.asarray(data[:, 0], dtype=np.float64), int(rate)


def check(path: Path, loop: bool, length_s: float | None = None) -> Report:
    """Decodes path and measures it. Fails on a peak over -1 dBFS (clipping), loudness under
    -30 dBFS (silence) or over -9 dBFS, a start later than 15 ms, a one-shot whose last 10 ms
    are less than 24 dB under its loudness (cut off while loud), a length over 2.5 s, or a loop whose length is not length_s."""
    x, rate = decode(path)
    seconds = len(x) / rate
    peak = float(np.max(np.abs(x)))
    loud = loudness_db(x)
    onset = int(np.argmax(np.abs(x) > peak * 0.1)) / rate * 1000.0
    tail = to_db(float(np.sqrt(np.mean(x[-samples(0.01) :] ** 2))))
    failures: list[str] = []
    if to_db(peak) > -1.0:
        failures.append("peak over -1 dBFS")
    if not -30.0 <= loud <= -9.0:
        failures.append("loudness outside -30..-9 dBFS")
    if onset > 15.0:
        failures.append("starts late")
    if not loop and tail > loud - 24.0:
        failures.append("cut off while loud")
    if length_s is not None and abs(seconds - length_s) > 1.0 / rate:
        failures.append(f"length is not {length_s} s")
    if length_s is None and seconds > 2.5:
        failures.append("longer than 2.5 s")
    return Report(path.stem, seconds, to_db(peak), loud, onset, tail, failures)


def montage(paths: Sequence[Path], out: Path) -> None:
    """Writes every file in paths one after the other, with 0.4 s gaps, into out. The roll
    loop plays three times, quiet to loud, as the game does at three speeds."""
    gap = np.zeros(samples(0.4))
    parts: list[Signal] = []
    for path in paths:
        x, _ = decode(path)
        if path.stem == "roll":
            x = np.concatenate([x[: samples(1.5)] * g for g in (0.3, 0.6, 1.0)])
        parts += [x, gap]
    write(out, np.concatenate(parts))


def main(argv: Sequence[str]) -> int:
    """Renders and checks every sound and loop. Returns 1 when a check fails."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--montage", type=Path, help="also write all sounds into this OGG file"
    )
    args = parser.parse_args(argv)
    rng = np.random.default_rng(25)
    reports: list[Report] = []
    paths: list[Path] = []
    for sound in SOUNDS:
        path = SFX_DIR / f"{sound.name}.ogg"
        write(path, finish(sound.render(rng), sound.loudness_db, sound.loop))
        reports.append(check(path, sound.loop))
        paths.append(path)
    loop_seconds = LOOP_BEATS * 60.0 / LOOP_BPM
    for name, root in LOOPS.items():
        path = LOOP_DIR / f"{name}.ogg"
        write(path, finish(placeholder_loop(root, rng), -16.0, True))
        reports.append(check(path, True, loop_seconds))
    print(f"{'file':<16}{'s':>6}{'peak':>8}{'loud':>8}{'onset':>7}{'tail':>8}  result")
    for r in reports:
        result = ", ".join(r.failures) or "ok"
        print(
            f"{r.name:<16}{r.seconds:6.2f}{r.peak_db:8.1f}{r.loudness_db:8.1f}{r.onset_ms:7.1f}{r.tail_db:8.1f}  {result}"
        )
    if args.montage is not None:
        montage(paths, args.montage)
        print(f"montage: {args.montage}")
    return 1 if any(r.failures for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
