"""Analysis of a backing take: beat grid, downbeat, key, quality proxies and the loop cut.

`build.analyse_take` runs all of it on one take. The parts:

- `find_grid`: tempo and beat phase from a comb search over the onset envelope near the
  requested BPM, then a drift check across the take.
- `downbeat_phases`: which beat of four starts the bar (kick on 1 and 3, snare on 2 and
  4, harmony changing on 1), best first.
- `detect_key`: Krumhansl-Kessler key profiles against the mean chroma.
- `drum_punch`, `clip_runs_per_minute`, `quietest_window_db`: the listen-check proxies
  for mushy drums, clipping and silence.
- `loop_candidates`, `bake_loop`, `seam_test`: bar-aligned loops whose end bars match
  their start bars, the cut with its cross-fade, and the seam measured on the audio.
- `onset_lag`: how far the authored layer sits from the bed's own attacks.
"""

from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np
from scipy.signal import resample_poly

from orrery_music.synth import SR, Audio

AR = 22_050  # analysis sample rate
_KEYS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
FADE_S = 0.08  # loop-seam cross-fade


def to_analysis_rate(audio: Audio) -> np.ndarray:
    """Mono float at 22.05 kHz from 48 kHz stereo."""
    return resample_poly(audio.mean(axis=1), 147, 320).astype(np.float32)


@dataclass(frozen=True)
class Grid:
    period: float  # seconds per beat
    phase: float  # time of the first beat at or after 0 s
    drift_ms: float  # worst beat-phase shift between the thirds of the take
    # Comb score at the best grid over the median grid: the tempo confidence.
    peakiness: float

    @property
    def bpm(self) -> float:
        return 60.0 / self.period


def find_grid(y: np.ndarray, bpm_hint: float, spread: float = 0.08) -> Grid:
    """Fit a fixed beat grid within +-`spread` of the hint, then measure drift."""
    hop = 64
    env = librosa.onset.onset_strength(y=y, sr=AR, hop_length=hop)
    fps = AR / hop

    def comb(
        env_part: np.ndarray, periods: np.ndarray
    ) -> tuple[float, float, np.ndarray]:
        best = (-1.0, 0.0, 0.0)
        scores_all: list[float] = []
        n = env_part.size
        for p in periods:
            phases = np.arange(0.0, p, 1.0 / fps)
            k = np.arange(int((n / fps) / p))
            idx = np.rint((phases[:, None] + k[None, :] * p) * fps).astype(int)
            idx = np.clip(idx, 0, n - 1)
            scores = env_part[idx].mean(axis=1)
            j = int(np.argmax(scores))
            scores_all.extend(scores.tolist())
            if scores[j] > best[0]:
                best = (float(scores[j]), float(p), float(phases[j]))
        return best[1], best[2], np.array(scores_all)

    p0 = 60.0 / bpm_hint
    coarse = p0 / np.linspace(1 - spread, 1 + spread, 161)
    period, _, _ = comb(env, coarse)
    fine = period * np.linspace(0.996, 1.004, 81)
    period, phase, scores = comb(env, fine)
    peakiness = float(scores.max() / max(np.median(scores), 1e-9))
    thirds = np.array_split(np.arange(env.size), 3)
    shifts: list[float] = []
    for part in thirds:
        start = part[0] / fps
        _, ph, _ = comb(env[part], np.array([period]))
        # Phase of this third against the global grid, folded to +-period/4: a third whose
        # strongest pulse is the off-beat (hats, say) still sits on the same grid.
        half = period / 2
        rel = ((start + ph) - phase) % half
        shifts.append(rel if rel < half / 2 else rel - half)
    drift = (max(shifts) - min(shifts)) * 1000.0
    return Grid(period, phase, drift, peakiness)


def _band_flux(
    y: np.ndarray, lo: float, hi: float, hop: int = 256
) -> tuple[np.ndarray, float]:
    mel = librosa.feature.melspectrogram(
        y=y, sr=AR, hop_length=hop, n_mels=96, fmax=AR / 2
    )
    freqs = librosa.mel_frequencies(n_mels=96, fmax=AR / 2)
    band = librosa.power_to_db(mel[(freqs >= lo) & (freqs < hi)] + 1e-10)
    flux = np.maximum(0.0, np.diff(band, axis=1, prepend=band[:, :1])).mean(axis=0)
    return flux, AR / hop


def _at_beats(
    flux: np.ndarray, fps: float, times: np.ndarray, win: float = 0.03
) -> np.ndarray:
    w = max(1, int(win * fps))
    idx = np.rint(times * fps).astype(int)
    return np.array(
        [
            flux[max(0, i - w) : i + w + 1].max() if 0 <= i < flux.size else 0.0
            for i in idx
        ]
    )


def downbeat_phases(y: np.ndarray, grid: Grid) -> list[int]:
    """Rank the four beat offsets as the bar's first beat, best first."""
    kick, fps = _band_flux(y, 20, 150)
    snare, _ = _band_flux(y, 1500, 5000)
    beats = np.arange(grid.phase, y.size / AR - 0.05, grid.period)
    k_at = _at_beats(kick, fps, beats)
    s_at = _at_beats(snare, fps, beats)
    chroma = librosa.feature.chroma_cqt(y=y, sr=AR, hop_length=512)
    cfps = AR / 512
    seg = [
        chroma[:, int(t * cfps) : int((t + grid.period) * cfps) + 1].mean(axis=1)
        for t in beats
    ]
    novelty = np.array(
        [0.0] + [1.0 - _cos(seg[i - 1], seg[i]) for i in range(1, len(seg))]
    )

    def by_slot(v: np.ndarray) -> np.ndarray:
        return np.array([v[s::4].mean() if v[s::4].size else 0.0 for s in range(4)])

    ks, ss, ns = by_slot(k_at), by_slot(s_at), by_slot(novelty)
    scores = []
    for k in range(4):
        backbeat = (ks[k] + ks[(k + 2) % 4] - ks[(k + 1) % 4] - ks[(k + 3) % 4]) / (
            ks.mean() + 1e-9
        )
        backbeat += (ss[(k + 1) % 4] + ss[(k + 3) % 4] - ss[k] - ss[(k + 2) % 4]) / (
            ss.mean() + 1e-9
        )
        one_vs_three = (ks[k] - ks[(k + 2) % 4]) / (ks.mean() + 1e-9) + (
            ns[k] - ns[(k + 2) % 4]
        ) / (ns.mean() + 1e-9)
        scores.append(backbeat + 0.5 * one_vs_three)
    return [int(k) for k in np.argsort(scores)[::-1]]


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


@dataclass(frozen=True)
class Key:
    tonic: int  # pitch class, C = 0
    mode: str
    strength: float  # profile correlation

    @property
    def name(self) -> str:
        return f"{_KEYS[self.tonic]} {self.mode}"


def detect_key(y: np.ndarray) -> Key:
    chroma = librosa.feature.chroma_cqt(y=librosa.effects.harmonic(y), sr=AR).mean(
        axis=1
    )
    best = Key(0, "major", -2.0)
    for tonic in range(12):
        for mode, profile in (("major", _MAJOR), ("minor", _MINOR)):
            r = float(np.corrcoef(np.roll(profile, tonic), chroma)[0, 1])
            if r > best.strength:
                best = Key(tonic, mode, r)
    return best


def drum_punch(y: np.ndarray, grid: Grid) -> tuple[float, float]:
    """(percussive energy share, onset contrast at the beats). Low values mean mushy drums."""
    _harm, perc = librosa.effects.hpss(y)
    share = float(np.sum(perc**2) / (np.sum(y**2) + 1e-12))
    env = librosa.onset.onset_strength(y=perc, sr=AR, hop_length=256)
    fps = AR / 256
    beats = np.arange(grid.phase, y.size / AR - 0.05, grid.period / 2)
    contrast = float(_at_beats(env, fps, beats, 0.02).mean() / (np.median(env) + 1e-9))
    return share, contrast


def clip_runs_per_minute(audio: Audio, level: float = 0.995, run: int = 3) -> float:
    """Runs of `run` or more consecutive samples at full scale (flat-topped clipping)."""
    hot = np.abs(audio).max(axis=1) >= level
    edges = np.diff(np.concatenate([[0], hot.astype(np.int8), [0]]))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    runs = int(np.sum((ends - starts) >= run))
    return runs / (audio.shape[0] / SR / 60.0)


def quietest_window_db(audio: Audio, window_s: float = 0.5) -> float:
    """Level of the quietest window against the whole clip, in dB (0 = no dip).

    Relative, so a quiet master does not count as silence; a drop-out or a dead stop shows
    as a dip of 35 dB or more.
    """
    n = int(window_s * SR)
    frames = audio[: audio.shape[0] // n * n].mean(axis=1).reshape(-1, n)
    rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-12)
    whole = np.sqrt(np.mean(frames**2) + 1e-12)
    return float(20 * np.log10(rms.min() / whole))


@dataclass(frozen=True)
class BarMap:
    """Per-bar features from a downbeat on: z-scored log-mel, chroma and level."""

    downbeat: float
    bar_s: float
    mel: np.ndarray  # (bars, bands)
    chroma: np.ndarray  # (bars, 12)
    level_db: np.ndarray  # (bars,)

    def sim(self, a: int, b: int) -> float:
        return 0.5 * _cos(self.mel[a], self.mel[b]) + 0.5 * _cos(
            self.chroma[a], self.chroma[b]
        )


def bar_map(y: np.ndarray, grid: Grid, first_beat: int) -> BarMap:
    downbeat = grid.phase + first_beat * grid.period
    bar_s = 4 * grid.period
    hop = 512
    fps = AR / hop
    mel = librosa.power_to_db(
        librosa.feature.melspectrogram(y=y, sr=AR, hop_length=hop, n_mels=48)
    )
    chroma = librosa.feature.chroma_cqt(y=y, sr=AR, hop_length=hop)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    bars = int((y.size / AR - downbeat) / bar_s)
    spans = [
        (int((downbeat + i * bar_s) * fps), int((downbeat + (i + 1) * bar_s) * fps))
        for i in range(bars)
    ]
    m = np.array([mel[:, a:b].mean(axis=1) for a, b in spans])
    m = (m - m.mean(axis=0)) / (m.std(axis=0) + 1e-6)
    c = np.array([chroma[:, a:b].mean(axis=1) for a, b in spans])
    lv = np.array(
        [20 * np.log10(np.sqrt(np.mean(rms[a:b] ** 2)) + 1e-9) for a, b in spans]
    )
    return BarMap(downbeat, bar_s, m, c, lv)


@dataclass(frozen=True)
class LoopCut:
    start_bar: int
    bars: int
    match: float  # mean bar similarity around the seam (1 = identical)
    start_s: float
    end_s: float


def loop_candidates(
    bm: BarMap, allowed_bars: tuple[int, ...], top: int = 6
) -> list[LoopCut]:
    """Bar-aligned loops ranked by how alike the bars around the end and the start are.

    Every bar in the loop must be within 12 dB of the median bar (no sparse intro or fade),
    and two full bars must follow the loop end (to compare and to cross-fade).
    """
    n = bm.level_db.size
    med = float(np.median(bm.level_db))
    found: list[LoopCut] = []
    for bars in allowed_bars:
        for s in range(2, n - bars - 1):
            e = s + bars
            if (
                bm.level_db[s : e + 2].min() < med - 12
                or bm.level_db[e : e + 2].min() < med - 6
            ):
                continue
            match = float(np.mean([bm.sim(s + j, e + j) for j in (-2, -1, 0, 1)]))
            found.append(
                LoopCut(
                    s,
                    bars,
                    match,
                    bm.downbeat + s * bm.bar_s,
                    bm.downbeat + e * bm.bar_s,
                )
            )
    found.sort(key=lambda c: c.match, reverse=True)
    return found[:top]


def bake_loop(
    audio: Audio, start_s: float, end_s: float, fade_s: float = FADE_S
) -> Audio:
    """Cut [start, end) and cross-fade the audio that follows `end` into the loop's head.

    The wrap from the loop's last sample to its first is then the take's own continuation,
    so the seam has no click; the cross-fade hides the change back to the start material.
    """
    s, e, f = round(start_s * SR), round(end_s * SR), round(fade_s * SR)
    loop = audio[s:e].copy()
    theta = np.linspace(0.0, np.pi / 2, f, dtype=np.float32)[:, None]
    loop[:f] = audio[e : e + f] * np.cos(theta) + audio[s : s + f] * np.sin(theta)
    return loop


@dataclass(frozen=True)
class Seam:
    """How the loop's wrap compares with its own bar lines (1.0 = like any bar line).

    flux_ratio: spectral flux at the wrap over the median flux at the loop's 4-bar lines.
    spectral_jump: mel distance between the beat before and the beat after the wrap, over
    the same distance at those lines. A change of section or level at the wrap shows here.
    """

    flux_ratio: float
    spectral_jump: float


def seam_test(loop: Audio, bar_s: float) -> Seam:
    """Play the wrap (last 3 s then first 3 s) and compare it with the loop's own bar lines."""
    y = to_analysis_rate(np.concatenate([loop[-3 * SR :], loop, loop[: 3 * SR]]))
    hop = 64
    fps = AR / hop
    # A short FFT keeps the flux peak of an attack sharp, so its frame alignment matters less.
    mel = librosa.power_to_db(
        librosa.feature.melspectrogram(
            y=y, sr=AR, n_fft=1024, hop_length=hop, n_mels=64
        )
        + 1e-10
    )
    flux = np.maximum(0.0, np.diff(mel, axis=1, prepend=mel[:, :1])).mean(axis=0)
    loop_s = loop.shape[0] / SR
    # The wrap is a phrase boundary, so compare it with the loop's other 4-bar boundaries.
    lines = 3.0 + np.arange(4, round(loop_s / bar_s), 4) * bar_s
    wraps = np.array([3.0, 3.0 + loop_s])
    f_lines, f_wrap = _at_beats(flux, fps, lines), _at_beats(flux, fps, wraps)

    def jump(t: float) -> float:
        # 1.5 beats each side, a quarter beat clear of the line: each window then holds one
        # beat attack at the same place, and the attack on the line itself is left out.
        i, beat = round(t * fps), bar_s / 4 * fps
        a, b = round(0.25 * beat), round(1.75 * beat)
        before = mel[:, i - b : i - a].mean(axis=1)
        after = mel[:, i + a : i + b].mean(axis=1)
        return float(np.linalg.norm(before - after))

    j_lines = np.array([jump(t) for t in lines])
    j_wrap = np.array([jump(t) for t in wraps])
    return Seam(
        float(f_wrap.max() / (np.median(f_lines) + 1e-9)),
        float(j_wrap.max() / (np.median(j_lines) + 1e-9)),
    )


def onset_lag(bed: Audio, layer: Audio, max_s: float = 0.025) -> float:
    """Seconds by which the layer's onsets trail the bed's (negative: the layer is early).

    The beat grid comes from the bed's onset envelope, whose peaks sit a few ms off the
    true attack for soft kicks; aligning the layer's own clicks to the bed fixes that.
    """
    hop = 32
    e_bed = librosa.onset.onset_strength(y=to_analysis_rate(bed), sr=AR, hop_length=hop)
    e_lay = librosa.onset.onset_strength(
        y=to_analysis_rate(layer), sr=AR, hop_length=hop
    )
    n = min(e_bed.size, e_lay.size)
    e_bed, e_lay = e_bed[:n], e_lay[:n]
    m = int(max_s * AR / hop)
    lags = np.arange(-m, m + 1)
    xc = [float(np.dot(np.roll(e_lay, -k), e_bed)) for k in lags]
    return float(lags[int(np.argmax(xc))] * hop / AR)
