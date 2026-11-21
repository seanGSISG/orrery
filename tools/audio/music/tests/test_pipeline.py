"""Focused tests for the parts that must be exact: hooks, grid, loop seam, layer, loudness."""

from __future__ import annotations

import numpy as np
import pytest

from orrery_music import analysis as an
from orrery_music import master
from orrery_music.build import remode
from orrery_music.hooks import HOOKS, Hook, Note, check_hook
from orrery_music.score import arrange, phrase_kinds
from orrery_music.synth import SR, fold, render_hits


@pytest.mark.parametrize("hook", list(HOOKS.values()), ids=list(HOOKS))
def test_every_hook_passes_the_rules(hook: Hook) -> None:
    assert check_hook(hook) == []


def test_a_hook_without_a_motif_or_resolution_fails() -> None:
    bad = Hook(
        "bad", "Bad", "major", 4, (Note(0, 1, 0), Note(5, 1, 2), Note(10, 0.5, 6)), ""
    )
    errors = check_hook(bad)
    assert any("off-scale" in e for e in errors)
    assert any("opening bar" in e for e in errors)
    assert any("stable note" in e for e in errors)


def test_remode_round_trips() -> None:
    hook = HOOKS["ascent-a"]
    assert remode(remode(hook)) == hook
    assert remode(hook).mode == "major"


def _drum_loop(bpm: float, seconds: float, first_downbeat: float) -> np.ndarray:
    """Kick on beats 1 and 3, snare on 2 and 4, at 22.05 kHz."""
    y = np.zeros(int(seconds * an.AR), dtype=np.float32)
    period = 60.0 / bpm
    rng = np.random.default_rng(0)
    t = np.arange(int(0.12 * an.AR)) / an.AR
    kick = np.sin(2 * np.pi * 60 * t) * np.exp(-t / 0.05)
    snare = rng.standard_normal(t.size) * np.exp(-t / 0.03) * 0.5
    for i in range(int((seconds - first_downbeat) / period)):
        at = int((first_downbeat + i * period) * an.AR)
        hit = kick if i % 2 == 0 else snare
        end = min(y.size, at + hit.size)
        y[at:end] += hit[: end - at]
    return y


def test_grid_and_downbeat_on_a_drum_loop() -> None:
    y = _drum_loop(
        93.0, 40.0, first_downbeat=0.4 + 60 / 93
    )  # the first bar starts on beat 2 of the grid
    grid = an.find_grid(y, 90)
    assert grid.bpm == pytest.approx(93.0, abs=0.1)
    assert grid.drift_ms < 10
    phases = an.downbeat_phases(y, grid)
    downbeat = grid.phase + phases[0] * grid.period
    # Kick on 1 and 3 looks the same at half-bar resolution, so 1 or 3 both count here.
    assert (
        min(
            abs((downbeat - (0.4 + 60 / 93)) % (2 * grid.period) - d)
            for d in (0, 2 * grid.period)
        )
        < 0.02
    )


def test_baked_loop_wraps_without_a_jump() -> None:
    t = np.arange(10 * SR) / SR
    tone = (0.5 * np.sin(2 * np.pi * 110.3 * t)).astype(np.float32)
    audio = np.stack([tone, tone], axis=1)
    loop = an.bake_loop(audio, 1.0, 7.0)
    assert loop.shape[0] == 6 * SR
    wrap_step = abs(float(loop[0, 0] - loop[-1, 0]))
    typical = float(np.abs(np.diff(loop[:, 0])).max())
    assert wrap_step <= typical * 1.01


def test_seam_test_flags_a_hard_cut() -> None:
    bar = 2.5
    t = np.arange(int(8 * bar * SR)) / SR
    pad = 0.2 * np.sin(2 * np.pi * 220 * t)
    for i in range(0, t.size, int(bar / 4 * SR)):
        pad[i : i + 200] += 0.5
    good = np.stack([pad, pad], axis=1).astype(np.float32)
    seam = an.seam_test(good, bar)
    assert seam.flux_ratio < 1.5 and seam.spectral_jump < 1.5
    bad = good.copy()
    tail = t[-int(bar * SR) :]
    bad[-int(bar * SR) :] = (0.2 * np.sin(2 * np.pi * 1760 * tail))[
        :, None
    ]  # a new section at the end
    assert an.seam_test(bad, bar).spectral_jump > 1.5


def test_layer_fills_every_phrase_and_stays_inside_the_loop() -> None:
    period = 60 / 96
    layer = arrange(HOOKS["title-b"], 40, period, 77)
    assert layer.kinds == phrase_kinds(5) == ["intro", "lift", "break", "full", "lift"]
    loop_s = 40 * 4 * period
    starts = [a for a, _, _ in layer.hook_notes]
    for p in range(5):  # the hook comes back in every 8-bar phrase
        assert any(32 * p * period <= s < 32 * (p + 1) * period for s in starts)
    assert all(0 <= h.time < loop_s for h in layer.hits)
    assert layer.melodic_midi.ticks_per_beat == 480


def test_fold_and_hits_wrap_round() -> None:
    n = SR
    data = np.ones((n + 100, 2), dtype=np.float32)
    assert fold(data, n)[:100, 0] == pytest.approx(2.0)
    from orrery_music.synth import Hit

    out = render_hits([Hit(time=n / SR - 0.001, sound="tick", gain=1.0)], n)
    assert np.abs(out[:500]).max() > 0.01  # the tail rang on past the end and wrapped


def test_limiter_and_normalise_hit_the_target() -> None:
    rng = np.random.default_rng(1)
    noise = rng.standard_normal((20 * SR, 2)).astype(np.float32) * 0.3
    limited = master.limit(noise)
    assert master.true_peak_db(limited) <= -1.4
    out, loud = master.normalise(noise)
    assert loud.integrated == pytest.approx(master.TARGET_LUFS, abs=0.3)
    assert loud.true_peak <= master.TARGET_TP
    assert out.shape == noise.shape
