"""Mix, loudness and encoding.

Loudness target: -16 LUFS integrated, -1 dBTP. Game music plays under SFX and dialogue
through the Music bus, so the files only need to be consistent with each other and loud
enough to keep resolution; -16 LUFS is the common streaming/mobile reference (AES TD1008)
and what most PC game soundtracks master near, and the 1 dB true-peak margin absorbs the
overshoot of Vorbis encoding. The Music bus volume, not the file, sets the in-game level.

ffmpeg `loudnorm` measures loudness (EBU R128 / BS.1770). The gain itself is applied
here, with a circular true-peak limiter, because `loudnorm`'s normalising pass resamples
to 192 kHz and its dynamic mode changes gain over time, and either would break a
sample-exact loop. All filters here run circularly for the same reason.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, resample_poly, sosfilt

from orrery_music.synth import SR, Audio

TARGET_LUFS = -16.0
TARGET_TP = -1.0
_LIMIT_CEILING_DB = -2.0  # leave room for the encoder's overshoot


@dataclass(frozen=True)
class Loudness:
    integrated: float
    true_peak: float
    lra: float


def measure(audio: Audio) -> Loudness:
    """EBU R128 loudness of `audio` played once, measured by ffmpeg loudnorm."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "m.wav"
        sf.write(wav, audio, SR, subtype="FLOAT")
        return measure_file(wav)


def measure_file(path: Path) -> Loudness:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
         f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    text = proc.stderr
    data = json.loads(text[text.rindex("{") : text.rindex("}") + 1])
    return Loudness(
        float(data["input_i"]), float(data["input_tp"]), float(data["input_lra"])
    )


def circular_sos(sos: np.ndarray, audio: Audio, pad_s: float = 1.0) -> Audio:
    """IIR filter a loop as if it repeats: warm the filter on the loop's own tail."""
    pad = min(audio.shape[0], int(pad_s * SR))
    ext = np.concatenate([audio[-pad:], audio], axis=0)
    return sosfilt(sos, ext, axis=0)[pad:].astype(np.float32)


def peaking(f0: float, gain_db: float, q: float) -> np.ndarray:
    """RBJ peaking EQ as one second-order section."""
    a = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    alpha = np.sin(w) / (2 * q)
    b = np.array([1 + alpha * a, -2 * np.cos(w), 1 - alpha * a])
    den = np.array([1 + alpha / a, -2 * np.cos(w), 1 - alpha / a])
    return np.concatenate([b / den[0], den / den[0]])[None, :]


def band_rms_db(audio: Audio, lo: float, hi: float) -> float:
    sos = butter(4, [lo, hi], btype="bandpass", fs=SR, output="sos")
    y = sosfilt(sos, audio.mean(axis=1))
    return float(10 * np.log10(np.mean(y**2) + 1e-12))


def rms_db(audio: Audio) -> float:
    return float(10 * np.log10(np.mean(audio.mean(axis=1) ** 2) + 1e-12))


def true_peak_db(audio: Audio) -> float:
    up = resample_poly(audio, 4, 1, axis=0)
    return float(20 * np.log10(np.abs(up).max() + 1e-12))


def limit(
    audio: Audio, ceiling_db: float = _LIMIT_CEILING_DB, window_s: float = 0.008
) -> Audio:
    """Circular look-ahead peak limiter on the 4x-oversampled peak; no gain change at the wrap."""
    ceiling = 10 ** (ceiling_db / 20)
    up = np.abs(resample_poly(audio, 4, 1, axis=0)).max(axis=1)
    peak = up.reshape(-1, 4).max(axis=1)[: audio.shape[0]]
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    w = max(1, int(window_s * SR))
    # Each smoothed value averages minima over windows that all contain the sample, so it
    # never exceeds the gain the sample needs.
    gain = uniform_filter1d(
        minimum_filter1d(need, size=2 * w + 1, mode="wrap"), size=w, mode="wrap"
    )
    return (audio * gain[:, None]).astype(np.float32)


def normalise(audio: Audio) -> tuple[Audio, Loudness]:
    """Gain to TARGET_LUFS, then limit peaks; returns the result and its measured loudness."""
    before = measure(audio)
    out = audio * np.float32(10 ** ((TARGET_LUFS - before.integrated) / 20))
    out = limit(out)
    after = measure(out)
    # The limiter lowers loudness a little; one gain trim brings it back on target.
    trim = TARGET_LUFS - after.integrated
    if abs(trim) > 0.1:
        out = limit(out * np.float32(10 ** (trim / 20)))
        after = measure(out)
    return out, after


def encode_ogg(audio: Audio, dest: Path, quality: int, tags: dict[str, str]) -> Path:
    """Write OGG Vorbis with oggenc; loop facts go into Vorbis comments."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "e.wav"
        sf.write(wav, np.clip(audio, -1.0, 1.0), SR, subtype="PCM_24")
        cmd = ["oggenc", "-Q", "-q", str(quality), "-o", str(dest)]
        for k, v in tags.items():
            cmd += ["-c", f"{k}={v}"]
        subprocess.run([*cmd, str(wav)], check=True)
    return dest


def preview(audio: Audio, start_s: float, seconds: float = 20.0) -> Audio:
    """A short excerpt with half-second fades, wrapping round the loop if needed."""
    n = int(seconds * SR)
    idx = (int(start_s * SR) + np.arange(n)) % audio.shape[0]
    clip = audio[idx].copy()
    f = SR // 2
    ramp = np.linspace(0.0, 1.0, f, dtype=np.float32)[:, None]
    clip[:f] *= ramp
    clip[-f:] *= ramp[::-1]
    return clip
