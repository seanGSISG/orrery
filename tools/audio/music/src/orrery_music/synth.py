"""Sound sources for the authored layer.

- Clockwork one-shots (tick, tock, ratchet, chime) are synthesised here from damped
  sinusoids and noise, so they need no sample licence.
- Melodic parts (music box, celesta, glockenspiel, square lead) render through FluidSynth
  with the GeneralUser GS soundfont.

Every render is circular: sound that rings past the loop end wraps onto the loop start,
so the layer loops without a seam by construction.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import soundfile as sf

SR = 48_000

type Audio = np.ndarray  # float32, shape (samples, 2)

Clock = Literal["tick", "tock", "ratchet", "chime"]


@dataclass(frozen=True)
class Hit:
    """One clockwork one-shot at `time` seconds into the loop."""

    time: float
    sound: Clock
    gain: float
    pitch: int = 0  # MIDI note, used by the chime


def _modes(
    freqs: list[float], decays: list[float], amps: list[float], seconds: float
) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    out = np.zeros_like(t)
    for f, d, a in zip(freqs, decays, amps, strict=True):
        if f < SR / 2:
            out += a * np.exp(-t / d) * np.sin(2 * np.pi * f * t)
    return out


def _click(rng: np.random.Generator, base: float, body: float) -> np.ndarray:
    """A metallic escapement click: a 1.5 ms noise burst into a few inharmonic modes."""
    ring = _modes(
        [base, base * 1.47, base * 2.09, base * 2.56],
        [0.012, 0.008, 0.006, 0.004],
        [1, 0.6, 0.4, 0.25],
        0.08,
    )
    noise = rng.standard_normal(ring.size) * np.exp(
        -np.arange(ring.size) / (0.0015 * SR)
    )
    wood = _modes([body], [0.02], [0.5], 0.08)
    out = ring + 0.5 * noise + wood
    return out / np.max(np.abs(out))


def clockwork_sounds(seed: int = 7) -> dict[Clock, np.ndarray]:
    """The unpitched one-shots, mono, peak-normalised. Deterministic for a given seed."""
    rng = np.random.default_rng(seed)
    tick = _click(rng, 4200.0, 1900.0)
    tock = _click(rng, 2900.0, 1100.0)
    ratchet = np.zeros(int(0.2 * SR))
    pos = 0.0
    for i in range(11):  # a gear wheel clicking past its pawl, speeding up
        c = _click(rng, 3300.0 + 120.0 * (i % 3), 800.0) * (0.55 + 0.45 * i / 10)
        start = int(pos * SR)
        end = min(ratchet.size, start + c.size)
        ratchet[start:end] += c[: end - start]
        pos += 0.016 - 0.0008 * i
    ratchet /= np.max(np.abs(ratchet))
    return {"tick": tick, "tock": tock, "ratchet": ratchet}


def chime(pitch: int, seconds: float = 3.5) -> np.ndarray:
    """A small clock bell: hum, prime, minor third, fifth and nominal partials."""
    f = 440.0 * 2 ** ((pitch - 69) / 12)
    ratios = [0.5, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.2]
    decays = [2.4, 1.8, 1.2, 1.0, 0.9, 0.5, 0.35, 0.2]
    amps = [0.35, 1.0, 0.45, 0.25, 0.55, 0.2, 0.15, 0.08]
    out = _modes([f * r for r in ratios], decays, amps, seconds)
    attack = np.minimum(1.0, np.arange(out.size) / (0.002 * SR))
    out *= attack
    return out / np.max(np.abs(out))


def render_hits(hits: list[Hit], loop_samples: int, seed: int = 7) -> Audio:
    """Place the one-shots into a stereo loop of `loop_samples`, wrapping tails to the start."""
    sounds = clockwork_sounds(seed)
    out = np.zeros((loop_samples, 2), dtype=np.float64)
    pan = {"tick": 0.35, "tock": -0.35, "ratchet": 0.15, "chime": 0.0}
    for hit in hits:
        mono = chime(hit.pitch) if hit.sound == "chime" else sounds[hit.sound]
        p = pan[hit.sound]
        stereo = (
            np.stack(
                [mono * np.sqrt(0.5 * (1 - p)), mono * np.sqrt(0.5 * (1 + p))], axis=1
            )
            * hit.gain
        )
        idx = (round(hit.time * SR) + np.arange(mono.size)) % loop_samples
        np.add.at(out, idx, stereo)
    return out.astype(np.float32)


def render_midi(midi: Path, soundfont: Path, loop_samples: int) -> Audio:
    """Render a MIDI file through FluidSynth at 48 kHz and fold the tail onto the loop start."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "fluid.wav"
        subprocess.run(
            [
                "fluidsynth", "-ni", "-q",
                "-r", str(SR), "-g", "0.6",
                "-o", "audio.file.format=float",
                "-o", "synth.reverb.room-size=0.45",
                "-o", "synth.reverb.level=0.5",
                "-F", str(wav), str(soundfont), str(midi),
            ],
            check=True,
            capture_output=True,
        )  # fmt: skip
        data, sr = sf.read(wav, dtype="float32", always_2d=True)
    if sr != SR:
        raise RuntimeError(f"FluidSynth wrote {sr} Hz, want {SR}")
    return fold(data, loop_samples)


def fold(data: Audio, loop_samples: int) -> Audio:
    """Sum everything past `loop_samples` back onto the start (a circular render)."""
    out = np.zeros((loop_samples, data.shape[1]), dtype=np.float32)
    for start in range(0, data.shape[0], loop_samples):
        chunk = data[start : start + loop_samples]
        out[: chunk.shape[0]] += chunk
    return out
