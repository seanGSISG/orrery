"""The material rules of a prop (docs/design/visual-quality.md §6), as pure functions on texture
pixels. `tools/blender/prop_cleanup.py` runs them in Blender; the tests run them on small arrays.

Every array holds floats from 0 to 1. A colour is sRGB (as an 8-bit file stores it), with the
channels on the last axis. A mask is a bool array: True is metal. Each rule is idempotent: a
second run of a rule on its own result changes nothing.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

type Pixels = NDArray[np.float32]
type Mask = NDArray[np.bool_]

# Albedo limits, sRGB: each channel of a dielectric, and the brightest channel of a metal.
DIELECTRIC_ALBEDO = (30 / 255, 240 / 255)
METAL_ALBEDO = (180 / 255, 250 / 255)
# Roughness limits: the dielectric rows of §6 (stone, polished to rough; glass is not a prop)
# and the metal rows (gold, and brass polished to aged).
DIELECTRIC_ROUGHNESS = (0.15, 0.95)
METAL_ROUGHNESS = (0.10, 0.55)
# Metallic at or above this becomes 1, below it 0. The zone 1 trial used it on every prop.
METAL_THRESHOLD = 0.6
# The stone rule. The kit limestone (set A: scuffed_cement x tint) has a saturation of 0.21 at
# its median and 0.34 at its 99th percentile. GPT-Image and Tripo give "honey limestone" about
# 0.6 to 0.9. A warm (hue 15 to 55 degrees), light pixel keeps at most STONE_SATURATION. Below
# STONE_LUMINANCE[0] (dark timber, joints) nothing changes; the cap fades in up to [1].
STONE_SATURATION = 0.34
STONE_HUE = (15.0, 55.0)
STONE_LUMINANCE = (0.34, 0.50)
# JPEG noise: after a clamp and one encode at quality 95, a rule moves at most about 0.3% of
# the pixels of a trial prop by more than 12 levels. So a JPEG map changes only when a rule
# moves more than JPEG_SHARE of its pixels further than JPEG_NOISE; a PNG map changes on any move.
JPEG_NOISE = 12 / 255
JPEG_SHARE = 0.01
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


@dataclass(frozen=True)
class PropClass:
    """A size class of docs/research/asset-prompting.md §3.2: the tallest prop of the class (m),
    its texture size (px) and its triangle budget."""

    up_to: float
    texture: int
    triangles: int


CLASSES = {
    "clutter": PropClass(up_to=0.7, texture=1024, triangles=2000),
    "medium": PropClass(up_to=2.5, texture=1024, triangles=6000),
    "hero": PropClass(up_to=float("inf"), texture=2048, triangles=15000),
}


def prop_class(height: float) -> str:
    """Returns the class of a prop that is height m tall. A prop in view at spawn is a hero
    whatever its height; the caller says so."""
    return next(name for name, spec in CLASSES.items() if height <= spec.up_to)


def fit_size(width: int, height: int, limit: int) -> tuple[int, int]:
    """Returns the image size with its longer edge at most limit px, in the same proportions.
    A smaller image keeps its size."""
    longest = max(width, height)
    if longest <= limit:
        return width, height
    return max(1, round(width * limit / longest)), max(
        1, round(height * limit / longest)
    )


def snap_metallic(metallic: Pixels) -> Pixels:
    """Returns metallic as 0 or 1."""
    return (metallic >= METAL_THRESHOLD).astype(np.float32)


def limit_roughness(roughness: Pixels, metal: Mask) -> Pixels:
    """Returns roughness inside the limits of its material: metal where metal is True."""
    low = np.where(metal, METAL_ROUGHNESS[0], DIELECTRIC_ROUGHNESS[0])
    high = np.where(metal, METAL_ROUGHNESS[1], DIELECTRIC_ROUGHNESS[1])
    return np.clip(roughness, low, high).astype(np.float32)


def limit_albedo(rgb: Pixels, metal: Mask, stone: bool = False) -> Pixels:
    """Returns the colours inside the albedo limits. A dielectric clamps each channel; a metal
    scales its colour, so its hue stays and its brightest channel is inside the limits.
    stone: then pull warm, light dielectric pixels toward the kit limestone (cap_stone). The
    cap comes after the clamp and keeps each colour between its own min and max channel, so
    the result stays inside the limits and a second run changes nothing."""
    dielectric = np.clip(rgb, *DIELECTRIC_ALBEDO)
    if stone:
        dielectric = cap_stone(dielectric)
    brightest = rgb.max(axis=-1, keepdims=True)
    scale = np.clip(brightest, *METAL_ALBEDO) / np.maximum(brightest, 1e-6)
    metal_rgb = np.where(brightest > 1e-6, rgb * scale, METAL_ALBEDO[0])
    return np.where(metal[..., None], metal_rgb, dielectric).astype(np.float32)


def cap_stone(rgb: Pixels) -> Pixels:
    """Returns the colours with each warm, light pixel at most STONE_SATURATION saturated.
    Saturation here is (max - min) / luminance. The change scales the colour about its own
    luminance, so the luminance and the hue stay and a second run changes nothing."""
    lum = (rgb @ LUMA)[..., None]
    chroma = rgb.max(axis=-1, keepdims=True) - rgb.min(axis=-1, keepdims=True)
    saturation = chroma / np.maximum(lum, 1e-6)
    low, high = STONE_LUMINANCE
    weight = np.clip((lum - low) / (high - low), 0.0, 1.0)
    hue = hue_degrees(rgb)[..., None]
    warm = (hue >= STONE_HUE[0]) & (hue <= STONE_HUE[1]) & (weight > 0)
    cap = STONE_SATURATION / np.maximum(weight, 1e-6)
    keep = np.where(warm & (saturation > cap), cap / np.maximum(saturation, 1e-6), 1.0)
    return (lum + (rgb - lum) * keep).astype(np.float32)


def hue_degrees(rgb: Pixels) -> Pixels:
    """Returns the HSV hue of each colour, 0 to 360 degrees (0 for a grey)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    high, low = rgb.max(axis=-1), rgb.min(axis=-1)
    chroma = np.maximum(high - low, 1e-6)
    hue = np.where(
        high == r,
        ((g - b) / chroma) % 6,
        np.where(high == g, (b - r) / chroma + 2, (r - g) / chroma + 4),
    )
    return np.where(high - low > 1e-6, hue * 60, 0.0).astype(np.float32)


def needs_change(before: Pixels, after: Pixels, jpeg: bool) -> bool:
    """Tells whether a map must take the result of a rule. For a JPEG map, a move as small as
    the encoder's own noise does not count (JPEG_NOISE, JPEG_SHARE); otherwise any move counts."""
    moved = np.abs(after - before)
    if moved.ndim == 3:
        moved = moved.max(axis=-1)
    if not jpeg:
        return bool((moved > 0.5 / 255).any())
    return float((moved > JPEG_NOISE).mean()) > JPEG_SHARE


def resample(mask: Mask, shape: tuple[int, int]) -> Mask:
    """Returns the mask at another size (height, width), nearest pixel, so a metallic map of
    one size can steer a colour map of another."""
    rows = np.arange(shape[0]) * mask.shape[0] // shape[0]
    cols = np.arange(shape[1]) * mask.shape[1] // shape[1]
    return mask[np.ix_(rows, cols)]


def to_srgb(linear: Pixels) -> Pixels:
    """Returns linear colour values as sRGB (a material's colour value is linear in Blender)."""
    return np.where(
        linear <= 0.0031308, linear * 12.92, 1.055 * np.power(linear, 1 / 2.4) - 0.055
    ).astype(np.float32)


def to_linear(srgb: Pixels) -> Pixels:
    """Returns sRGB colour values as linear."""
    return np.where(
        srgb <= 0.04045, srgb / 12.92, np.power((srgb + 0.055) / 1.055, 2.4)
    ).astype(np.float32)
