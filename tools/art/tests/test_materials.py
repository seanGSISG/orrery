"""The prop material rules (orrery_art.materials) on small arrays. They need no Blender."""

import numpy as np
import pytest

from orrery_art import materials as m


def srgb(*levels: tuple[int, int, int]) -> np.ndarray:
    """Returns one row of sRGB colours from 8-bit levels."""
    return np.array([levels], dtype=np.float32) / 255


def test_metallic_snaps_to_0_or_1() -> None:
    snapped = m.snap_metallic(
        np.array([0.0, 0.3, 0.59, 0.6, 0.85, 1.0], dtype=np.float32)
    )
    assert snapped.tolist() == [0, 0, 0, 1, 1, 1]


def test_roughness_stays_inside_the_limits_of_its_material() -> None:
    roughness = np.array([0.0, 0.5, 1.0, 0.0, 0.3, 1.0], dtype=np.float32)
    metal = np.array([False, False, False, True, True, True])
    assert m.limit_roughness(roughness, metal).tolist() == pytest.approx(
        [0.15, 0.5, 0.95, 0.10, 0.3, 0.55]
    )


def test_a_dielectric_clamps_each_channel() -> None:
    out = m.limit_albedo(
        srgb((0, 0, 0), (255, 255, 255), (250, 120, 10)), np.zeros((1, 3), bool)
    )
    assert np.round(out * 255).tolist() == [
        [[30, 30, 30], [240, 240, 240], [240, 120, 30]]
    ]


def test_a_metal_keeps_its_hue_and_brings_its_brightest_channel_into_range() -> None:
    out = m.limit_albedo(
        srgb((100, 80, 40), (255, 204, 102), (0, 0, 0)), np.ones((1, 3), bool)
    )
    dark, bright, black = np.round(out[0] * 255).tolist()
    assert dark == [180, 144, 72]
    assert bright == [250, 200, 100]
    assert black == [180, 180, 180]


def test_stone_pulls_light_warm_colours_to_the_kit_limestone() -> None:
    # Honey limestone (light ochre), dark timber, a light green, and the kit limestone itself.
    colours = srgb((222, 178, 96), (90, 60, 30), (120, 200, 120), (190, 176, 150))
    out = m.limit_albedo(colours, np.zeros((1, 4), bool), stone=True)
    lum = colours @ m.LUMA
    stone = out[0, 0]
    assert (stone.max() - stone.min()) / (stone @ m.LUMA) == pytest.approx(
        m.STONE_SATURATION, abs=1e-4
    )
    assert stone @ m.LUMA == pytest.approx(lum[0, 0], abs=1e-5)
    assert np.allclose(out[0, 1:], colours[0, 1:], atol=1e-6)


def test_every_rule_changes_nothing_on_its_own_result() -> None:
    rng = np.random.default_rng(1)
    rgb = rng.random((64, 64, 3), dtype=np.float32)
    metal = rng.random((64, 64)) > 0.7
    once = m.limit_albedo(rgb, metal, stone=True)
    assert np.abs(m.limit_albedo(once, metal, stone=True) - once).max() < 1e-5
    rough = m.limit_roughness(rgb[..., 0], metal)
    assert np.array_equal(m.limit_roughness(rough, metal), rough)
    snapped = m.snap_metallic(rgb[..., 1])
    assert np.array_equal(m.snap_metallic(snapped), snapped)


def test_texture_size_follows_the_class() -> None:
    assert m.prop_class(0.5) == "clutter"
    assert m.prop_class(1.8) == "medium"
    assert m.prop_class(3.2) == "hero"
    assert m.CLASSES["medium"].texture == 1024 and m.CLASSES["hero"].texture == 2048
    assert m.fit_size(4096, 4096, 1024) == (1024, 1024)
    assert m.fit_size(4096, 2048, 2048) == (2048, 1024)
    assert m.fit_size(512, 512, 1024) == (512, 512)


def test_a_jpeg_map_changes_only_beyond_the_encoder_noise() -> None:
    before = np.full((100, 100, 3), 0.5, dtype=np.float32)
    noise = before.copy()
    noise[:1, :50] += 20 / 255  # 0.5% of the pixels move far: encoder noise
    assert not m.needs_change(before, noise, jpeg=True)
    assert m.needs_change(before, noise, jpeg=False)
    real = before.copy()
    real[:5] += 20 / 255  # 5% of the pixels move far
    assert m.needs_change(before, real, jpeg=True)


def test_a_metal_mask_steers_a_map_of_another_size() -> None:
    mask = np.array([[True, False], [False, True]])
    assert m.resample(mask, (4, 4)).tolist() == [
        [True, True, False, False],
        [True, True, False, False],
        [False, False, True, True],
        [False, False, True, True],
    ]
