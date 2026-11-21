"""Turn backing takes into checked candidates and keep the best 3-5 per track.

For each take: analyse it (grid, downbeat, key, drums, clipping, loop cut), and reject it
if a listen-check proxy fails. For each surviving take and each of the track's hooks:
fit the hook to the take's harmony, arrange and render the layer, mix, normalise, encode
OGG Vorbis, decode it again and run the final checks on the file a player would load.

Writes `out/candidates/<track>/<candidate>.ogg`, `review/previews/<candidate>.ogg`,
`midi/<candidate>.mid` (the human-written layer) and `manifest/<track>.json` (prompts,
seeds, settings, every metric and every rejection reason).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from orrery_music import analysis as an
from orrery_music import master
from orrery_music.brief import Track, mood_of
from orrery_music.hooks import Hook, Note, check_hook
from orrery_music.score import arrange
from orrery_music.synth import SR, Audio, render_hits, render_midi


@dataclass(frozen=True)
class Limits:
    """Thresholds for the checks and listen-check proxies.

    Set from the spread over the first 66 takes. Onset contrast: ACE-Step takes 18-65,
    Stable Audio 3 takes 10-15, and the takes under 8 also had the weakest beat grids.
    Loop match: about 0.9-1.0 for ACE-Step, 0.5-0.7 for Stable Audio 3, which evolves more.
    Hook fit (chroma lift, see `fit_hook`): the best hook-bed pairs reach 0.3-0.45, a random
    melody scores about 0. Seam ratios compare the wrap with the loop's own 4-bar lines.
    """

    tempo_error_pct: float = 3.0  # detected tempo against the requested one
    drift_ms: float = 25.0  # beat-phase shift across the take
    clip_runs_per_min: float = 6.0
    quietest_db: float = -35.0  # quietest half second against the whole loop
    drum_contrast: float = 8.0
    loop_match: float = 0.5
    seam_flux: float = 1.5
    seam_jump: float = 1.5
    hook_fit: float = 0.25
    hook_over_bed_db: float = -1.5  # hook against the bed, 1.2-6 kHz presence band
    loudness_lu: float = 0.5
    min_s: float = 90.0
    max_s: float = 150.0


LIMITS = Limits()
KEEP = 5


@dataclass
class TakeReport:
    take: str
    model: str
    prompt: str
    seed: int
    bpm: float
    drift_ms: float
    downbeat_beat: int
    key: str
    key_strength: float
    drum_share: float
    drum_contrast: float
    clip_runs_per_min: float
    loop_start_bar: int = 0
    loop_bars: int = 0
    loop_start_s: float = 0.0
    loop_end_s: float = 0.0
    loop_match: float = 0.0
    seam_flux: float = 0.0
    seam_jump: float = 0.0
    quietest_db: float = 0.0
    rejects: list[str] = field(default_factory=list)


@dataclass
class Candidate:
    id: str
    track: str
    take: str
    model: str
    hook: str
    hook_name: str
    hook_key: str
    bars: int
    bpm: float
    seconds: float
    loudness_lufs: float
    true_peak_db: float
    hook_fit: float
    hook_over_bed_db: float
    layer_shift_ms: float
    seam_flux: float
    seam_jump: float
    final_bpm: float
    file: str
    preview: str
    midi: str
    catchy: str
    score: float = 0.0
    rejects: list[str] = field(default_factory=list)
    kept: bool = False


def load(path: Path) -> Audio:
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr == 44_100:
        data = resample_poly(data, 160, 147, axis=0).astype(np.float32)
    elif sr != SR:
        raise ValueError(f"{path}: unexpected rate {sr}")
    return data


def analyse_take(
    track: Track, flac: Path
) -> tuple[TakeReport, Audio, an.Grid, an.BarMap | None]:
    record = json.loads(flac.with_suffix(".json").read_text())
    audio = load(flac)
    y = an.to_analysis_rate(audio)
    grid = an.find_grid(y, track.bpm)
    phases = an.downbeat_phases(y, grid)
    key = an.detect_key(y)
    share, contrast = an.drum_punch(y, grid)
    report = TakeReport(
        take=flac.stem,
        model=record["model"],
        prompt=record["prompt"],
        seed=record["seed"],
        bpm=round(grid.bpm, 2),
        drift_ms=round(grid.drift_ms, 1),
        downbeat_beat=phases[0],
        key=key.name,
        key_strength=round(key.strength, 2),
        drum_share=round(share, 2),
        drum_contrast=round(contrast, 1),
        clip_runs_per_min=0.0,
    )
    err = abs(grid.bpm - track.bpm) / track.bpm * 100
    if err > LIMITS.tempo_error_pct:
        report.rejects.append(
            f"tempo {grid.bpm:.1f} is {err:.1f}% off the requested {track.bpm}"
        )
    if grid.drift_ms > LIMITS.drift_ms:
        report.rejects.append(f"tempo drifts {grid.drift_ms:.0f} ms across the take")
    if contrast < LIMITS.drum_contrast:
        report.rejects.append(f"mushy drums (onset contrast {contrast:.1f})")
    best: tuple[float, an.LoopCut, an.Seam, an.BarMap] | None = None
    for phase in phases[:2]:
        bm = an.bar_map(y, grid, phase)
        for cut in an.loop_candidates(bm, track.loop_bars):
            seam = an.seam_test(an.bake_loop(audio, cut.start_s, cut.end_s), bm.bar_s)
            # Prefer the first-ranked downbeat; take the second only for a clearly better seam.
            rank = (
                cut.match
                - 0.3 * max(0.0, seam.flux_ratio - 1)
                - 0.3 * max(0.0, seam.spectral_jump - 1)
            )
            rank -= 0.05 * (phase != phases[0])
            if best is None or rank > best[0]:
                best = (rank, cut, seam, bm)
    if best is None:
        report.rejects.append(
            "no loop of an allowed length without a sparse or fading bar"
        )
        return report, audio, grid, None
    _, cut, seam, bm = best
    report.downbeat_beat = round((bm.downbeat - grid.phase) / grid.period)
    report.loop_start_bar, report.loop_bars = cut.start_bar, cut.bars
    report.loop_start_s, report.loop_end_s = round(cut.start_s, 4), round(cut.end_s, 4)
    report.loop_match = round(cut.match, 3)
    report.seam_flux, report.seam_jump = (
        round(seam.flux_ratio, 2),
        round(seam.spectral_jump, 2),
    )
    segment = audio[int(cut.start_s * SR) : int(cut.end_s * SR)]
    report.clip_runs_per_min = round(an.clip_runs_per_minute(segment), 1)
    report.quietest_db = round(an.quietest_window_db(segment), 1)
    if report.clip_runs_per_min > LIMITS.clip_runs_per_min:
        report.rejects.append(
            f"clipping ({report.clip_runs_per_min:.0f} flat-topped runs a minute)"
        )
    if report.quietest_db < LIMITS.quietest_db:
        report.rejects.append(
            f"silence or drop-out (a {-report.quietest_db:.0f} dB dip)"
        )
    if cut.match < LIMITS.loop_match:
        report.rejects.append(f"loop end and start differ (match {cut.match:.2f})")
    if seam.flux_ratio > LIMITS.seam_flux or seam.spectral_jump > LIMITS.seam_jump:
        report.rejects.append(
            f"audible seam (flux {seam.flux_ratio:.2f}, jump {seam.spectral_jump:.2f})"
        )
    return report, audio, grid, bm


_TO_MAJOR = {3: 4, 8: 9, 10: 11}
_TO_MINOR = {v: k for k, v in _TO_MAJOR.items()}


def remode(hook: Hook) -> Hook:
    """The same hook in the parallel mode (minor me/le/te become mi/la/ti, and back)."""
    table = _TO_MAJOR if hook.mode == "minor" else _TO_MINOR
    notes = tuple(
        Note(
            n.beat,
            n.length,
            n.pitch - n.pitch % 12 + table.get(n.pitch % 12, n.pitch % 12),
        )
        for n in hook.notes
    )
    return replace(hook, mode="major" if hook.mode == "minor" else "minor", notes=notes)


def fit_hook(
    hook: Hook, loop: Audio, bars: int, period: float, near: int
) -> tuple[Hook, int, float]:
    """Pick the hook's mode and tonic that sit best on the backing's harmony.

    Fit is the chroma lift under the hook's notes, weighted by note length: per frame,
    1 means the note is the strongest pitch class in the bed, 0 an average one, below 0 a
    weak one. Lift, not raw chroma, so a bed with flat (noisy) chroma does not score well
    by default. Searched over all 12 tonics and both modes. Returns (hook, tonic MIDI, fit).
    """
    y = an.to_analysis_rate(loop)
    chroma = librosa.feature.chroma_cqt(y=y, sr=an.AR, hop_length=512)
    mean = chroma.mean(axis=0, keepdims=True)
    chroma = (chroma - mean) / (chroma.max(axis=0, keepdims=True) - mean + 1e-9)
    fps = an.AR / 512
    best: tuple[float, Hook, int] = (-9.0, hook, near)
    for variant in (hook, remode(hook)):
        spans = arrange(variant, bars, period, 60).hook_notes
        frames = [
            (int(a * fps), max(int(a * fps) + 1, int(b * fps)), p - 60)
            for a, b, p in spans
        ]
        weights = np.array([b - a for a, b, _ in frames], dtype=float)
        # A 0.02 handicap keeps the hook's own mode unless the other one is clearly better.
        handicap = 0.0 if variant is hook else 0.02
        for tonic in range(12):
            vals = np.array(
                [chroma[(tonic + p) % 12, a:b].mean() for a, b, p in frames]
            )
            fit = float(np.sum(vals * weights) / weights.sum())
            if fit - handicap > best[0] - (0.0 if best[1] is hook else 0.02):
                best = (fit, variant, tonic)
    fit, variant, pc = best
    tonic = near + ((pc - near) % 12)
    if tonic - near > 6:
        tonic -= 12
    return variant, tonic, round(fit, 3)


def build_candidate(
    track: Track,
    report: TakeReport,
    audio: Audio,
    grid: an.Grid,
    hook: Hook,
    root: Path,
    out: Path,
    sf2: Path,
) -> Candidate:
    cid = f"{report.take}-{hook.id.split('-')[1]}"
    loop = an.bake_loop(audio, report.loop_start_s, report.loop_end_s)
    n = loop.shape[0]
    period = (report.loop_end_s - report.loop_start_s) / (report.loop_bars * 4)
    played, tonic, fit = fit_hook(
        hook, loop, report.loop_bars, period, track.tonic_midi
    )
    layer = arrange(played, report.loop_bars, period, tonic)
    midi_path = root / "midi" / f"{cid}.mid"
    midi_path.parent.mkdir(parents=True, exist_ok=True)
    layer.full_midi.save(midi_path)
    work = out / "work" / track.id
    work.mkdir(parents=True, exist_ok=True)
    layer.melodic_midi.save(work / f"{cid}-melodic.mid")
    melody = render_midi(work / f"{cid}-melodic.mid", sf2, n)
    clock = render_hits(layer.hits, n)
    # Line the layer up with the bed's own attacks (a few ms); the loop is circular.
    lag = an.onset_lag(loop, clock)
    shift = round(lag * SR)
    melody, clock = np.roll(melody, -shift, axis=0), np.roll(clock, -shift, axis=0)

    bed = master.circular_sos(master.peaking(2800.0, -2.5, 0.9), loop)
    bed_band = master.band_rms_db(bed, 1200, 6000)
    gain_db = bed_band + 1.0 - master.band_rms_db(melody, 1200, 6000)
    gain_db = min(gain_db, master.rms_db(bed) - 2.0 - master.rms_db(melody))
    melody = melody * np.float32(10 ** (gain_db / 20))
    over_bed = master.band_rms_db(melody, 1200, 6000) - bed_band
    clock_db = (
        master.band_rms_db(bed, 3000, 10000)
        - 5.0
        - master.band_rms_db(clock, 3000, 10000)
    )
    clock_db = min(clock_db, master.rms_db(bed) - 10.0 - master.rms_db(clock))
    mix = bed + melody + clock * np.float32(10 ** (clock_db / 20))
    final, _ = master.normalise(mix)

    seconds = n / SR
    tags = {
        "TITLE": f"Orrery {track.name} candidate {cid}",
        "BPM": f"{60 / period:.3f}",
        "BEATS": str(report.loop_bars * 4),
        "BAR_BEATS": "4",
        "LOOPSTART": "0",
        "LOOPLENGTH": str(n),
        "KEY": _key_of(played, tonic),
    }
    ogg = master.encode_ogg(
        final, out / "candidates" / track.id / f"{cid}.ogg", 6, tags
    )
    prev = master.encode_ogg(
        master.preview(final, 8 * 4 * period),
        root / "review" / "previews" / f"{cid}.ogg",
        1,
        {},
    )

    decoded, sr = sf.read(ogg, dtype="float32", always_2d=True)
    if sr != SR:
        raise RuntimeError(f"{ogg}: decoded at {sr} Hz")
    loud = master.measure_file(ogg)
    seam = an.seam_test(decoded, 4 * period)
    regrid = an.find_grid(an.to_analysis_rate(decoded), 60 / period, spread=0.02)
    cand = Candidate(
        id=cid,
        track=track.id,
        take=report.take,
        model=report.model,
        hook=hook.id,
        hook_name=hook.name,
        hook_key=_key_of(played, tonic),
        bars=report.loop_bars,
        bpm=round(60 / period, 2),
        seconds=round(decoded.shape[0] / SR, 2),
        loudness_lufs=loud.integrated,
        true_peak_db=loud.true_peak,
        hook_fit=fit,
        hook_over_bed_db=round(over_bed, 1),
        layer_shift_ms=round(-lag * 1000, 1),
        seam_flux=round(seam.flux_ratio, 2),
        seam_jump=round(seam.spectral_jump, 2),
        final_bpm=round(regrid.bpm, 2),
        file=str(ogg.relative_to(root)),
        preview=str(prev.relative_to(root)),
        midi=str(midi_path.relative_to(root)),
        catchy=" ".join(
            [
                hook.why_catchy,
                *(
                    [f"Played in {played.mode} to fit the bed."]
                    if played.mode != hook.mode
                    else []
                ),
                f"Bed: {mood_of(report.prompt).lower()}.",
            ]
        ),
    )
    lo, hi = LIMITS.min_s, LIMITS.max_s
    if not lo <= seconds <= hi:
        cand.rejects.append(f"length {seconds:.0f} s outside {lo:.0f}-{hi:.0f} s")
    if (
        abs(loud.integrated - master.TARGET_LUFS) > LIMITS.loudness_lu
        or loud.true_peak > master.TARGET_TP
    ):
        cand.rejects.append(
            f"loudness {loud.integrated:.1f} LUFS / {loud.true_peak:.1f} dBTP off target"
        )
    if abs(regrid.bpm - 60 / period) / (60 / period) > 0.005:
        cand.rejects.append(
            f"final tempo {regrid.bpm:.2f} differs from the grid {60 / period:.2f}"
        )
    if seam.flux_ratio > LIMITS.seam_flux or seam.spectral_jump > LIMITS.seam_jump:
        cand.rejects.append(
            f"audible seam in the OGG (flux {seam.flux_ratio:.2f}, jump {seam.spectral_jump:.2f})"
        )
    if an.clip_runs_per_minute(decoded) > 0:
        cand.rejects.append("clipping in the OGG")
    if an.quietest_window_db(decoded) < LIMITS.quietest_db:
        cand.rejects.append("silence in the OGG")
    if fit < LIMITS.hook_fit:
        cand.rejects.append(
            f"weak hook: clashes with the bed's harmony (fit {fit:.2f})"
        )
    if over_bed < LIMITS.hook_over_bed_db:
        cand.rejects.append(f"weak hook: buried {over_bed:.1f} dB under the bed")
    cand.rejects += [f"hook rule: {e}" for e in check_hook(played)]
    cand.score = round(
        2.0 * fit
        + min(report.drum_contrast / 40.0, 1.0)
        + report.loop_match
        - 0.3 * max(0.0, cand.seam_flux - 1.0)
        - 0.3 * max(0.0, cand.seam_jump - 1.0),
        3,
    )
    return cand


def _key_of(hook: Hook, tonic: int) -> str:
    return an.Key(tonic % 12, hook.mode, 1.0).name


def select(cands: list[Candidate]) -> list[Candidate]:
    """Up to KEEP passing candidates, one per take, best score first.

    Each hook and each model gets a place first when it has a passing candidate, so Sean
    hears both hooks and both kinds of bed.
    """
    passing = sorted(
        (c for c in cands if not c.rejects), key=lambda c: c.score, reverse=True
    )
    kept: list[Candidate] = []

    def free(c: Candidate) -> bool:
        return c not in kept and c.take not in {k.take for k in kept}

    for group in [
        *dict.fromkeys(c.hook for c in passing),
        *dict.fromkeys(c.model for c in passing),
    ]:
        if not any(group in (k.hook, k.model) for k in kept):
            first = next(
                (c for c in passing if group in (c.hook, c.model) and free(c)), None
            )
            if first:
                kept.append(first)
    for c in passing:
        if len(kept) < KEEP and free(c):
            kept.append(c)
    for c in kept:
        c.kept = True
    return sorted(kept, key=lambda c: c.score, reverse=True)


def build(track: Track, out: Path, root: Path) -> list[Candidate]:
    sf2 = out / "sf" / "GeneralUser-GS.sf2"
    if not sf2.exists():
        raise FileNotFoundError(f"{sf2}: download GeneralUser GS first (see README.md)")
    reports: list[TakeReport] = []
    cands: list[Candidate] = []
    for flac in sorted((out / "takes" / track.id).glob("*.flac")):
        report, audio, grid, _ = analyse_take(track, flac)
        reports.append(report)
        print(f"{report.take}: {'; '.join(report.rejects) or 'ok'}", flush=True)
        if report.rejects:
            continue
        for hook in track.hooks:
            cand = build_candidate(track, report, audio, grid, hook, root, out, sf2)
            print(
                f"  {cand.id}: score {cand.score:.2f} {'; '.join(cand.rejects) or 'pass'}",
                flush=True,
            )
            cands.append(cand)
    kept = select(cands)
    manifest = root / "manifest" / f"{track.id}.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "track": asdict(track) | {"hooks": [asdict(h) for h in track.hooks]},
                "limits": asdict(LIMITS),
                "loudness_target": {
                    "lufs": master.TARGET_LUFS,
                    "true_peak_db": master.TARGET_TP,
                },
                "takes": [asdict(r) for r in reports],
                "candidates": [asdict(c) for c in cands],
            },
            indent=1,
        )
    )
    # Only the kept candidates' files stay; the manifest keeps the metrics of the rest.
    keep_ids = {c.id for c in kept}
    for c in cands:
        if c.id not in keep_ids:
            for path in (c.file, c.midi, c.preview):
                (root / path).unlink(missing_ok=True)
    return kept
