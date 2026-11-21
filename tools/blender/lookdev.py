"""Look-dev renders for the style board: the look of the game, made with our own pipeline.

The script builds one small play space at true scale (the marble's radius is
0.2 m): a round tower-top plaza with a banked brass lip and a clock face set
into its floor, a wide banked route that climbs to an upper terrace, a narrow
shortcut beam that leaves the route at a fork, and a short bridge down to a
small second platform. Big cut gems hover over the floor. Nothing has steps.

Every game material is plain PBR (colour, roughness and normal maps, a metallic
value, a tint and a vertex colour, plus transmission for glass, emission for
gems and a clearcoat for the stone marble), so that it ports to a Godot
StandardMaterial3D. The textures and skies are the CC0 files under
assets/textures/ (see docs/licenses.md). Only the backdrop (sky, clouds, stars,
planet) uses Blender-only nodes; the game gets it as a baked sky.

Run from the repo root:

    blender-5.2 -b --factory-startup --python-exit-code 1 \
        --python tools/blender/lookdev.py -- [--only a noon gem] [--out DIR] \
        [--samples N] [--scale PERCENT] [--cpu]

Output: <out>/render-<shot>.webp at 1920x1080 (default out: docs/style/review).
Shots: a, b, c (dawn candidates), eye, noon, dusk, gem, marble-a, marble-b.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NamedTuple

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[2]
TEXTURES = REPO / "assets" / "textures"

MARBLE_RADIUS = 0.2  # docs/plan.md 4.2: all art is built to this scale
GEM_SIZE = 0.5  # the largest dimension of a gem: 1.25 x the marble's diameter
GEM_HOVER = 0.3  # the gap between the floor and the lowest point of a gem
PLAZA_RADIUS = 3.2
TERRACE_RADIUS = 2.2
ISLET_RADIUS = 1.4  # the small second platform
DECK_WIDTH = 2.4  # the safe route: six marble widths
BEAM_WIDTH = 0.8  # the shortcut: two marble widths
BRIDGE_WIDTH = 1.4
DECK_THICKNESS = 0.26
TERRACE_HEIGHT = 1.1  # the upper terrace is this much higher than the plaza
ISLET_DROP = 0.4  # the small platform is this much lower than the plaza
STRAIGHT_IN = 2.0  # the safe route: a straight, a banked right turn, a straight
ARC_RADIUS = 3.0
ARC_ANGLE = math.radians(110)
STRAIGHT_OUT = 1.5
BANK = math.radians(11)
FORK_AT = 0.95  # the beam leaves the safe route this far along it
BEAM_LANDING = math.radians(230)  # where the beam meets the terrace, counter-clockwise from +X at its centre
BRIDGE_ANGLE = math.radians(150)  # where the bridge leaves the plaza, counter-clockwise from +X
BRIDGE_LENGTH = 1.8
OVERLAP = 0.3  # a route reaches this far onto a pad
STEP = 0.002  # a route lies this much above the floor that it overlaps, so no two faces coincide
JOINT = 0.012  # the joint between two floor slabs
MORTAR = 0.5  # the joints are filled with stone that is this much darker
FLUSH = 0.0003  # the filling lies this far below the slab tops: a deeper joint shows a bright sunlit wall
SUN_AZIMUTH = 135.0  # degrees in the scene, counter-clockwise from +X: ahead of the overview camera, on its left
SKY_CAP = 40.0  # an HDRI's own sun is cut down to this; the sun lamp replaces it

UP = Vector((0.0, 0.0, 1.0))

MarbleLook = Literal["glass", "stone"]
GemCut = Literal["bipyramid", "hexagon", "brilliant"]
Color = tuple[float, float, float]
Point = tuple[float, float, float]
Profile = list[tuple[float, float]]

# Gem hues follow the blue, orange and reddish purple of the Okabe-Ito colour-blind-safe set.
# Each colour has its own cut, so that the outline alone tells the gems apart from any side:
# pointed at both ends, flat at both ends, or flat on top and pointed below.
# The rings are (radius, z) from top to bottom, in units of GEM_SIZE.
GEM_RINGS: dict[GemCut, list[tuple[float, float]]] = {
    "bipyramid": [(0.0, 0.5), (0.24, 0.19), (0.33, 0.025), (0.33, -0.025), (0.24, -0.19), (0.0, -0.5)],
    "hexagon": [(0.26, 0.44), (0.42, 0.32), (0.5, 0.16), (0.5, -0.16), (0.42, -0.32), (0.26, -0.44)],
    "brilliant": [(0.28, 0.24), (0.42, 0.17), (0.5, 0.05), (0.5, -0.01), (0.3, -0.3), (0.0, -0.58)],
}
GEM_COLORS: dict[GemCut, Color] = {
    "bipyramid": (0.01, 0.1, 0.55),
    "hexagon": (0.8, 0.3, 0.0),
    "brilliant": (0.6, 0.02, 0.28),
}


class Maps(NamedTuple):
    """The three files of a PBR texture set, under assets/textures."""

    color: str
    roughness: str
    normal: str  # OpenGL convention


def poly_haven(stem: str) -> Maps:
    """Return the maps of a Poly Haven texture set (2K JPG), for a stem like "stone/scuffed_cement"."""
    return Maps(f"{stem}_diff_2k.jpg", f"{stem}_rough_2k.jpg", f"{stem}_nor_gl_2k.jpg")


def ambient_cg(stem: str) -> Maps:
    """Return the maps of an ambientCG texture set (2K-JPG), for a stem like "metal/Metal007"."""
    return Maps(f"{stem}_2K-JPG_Color.jpg", f"{stem}_2K-JPG_Roughness.jpg", f"{stem}_2K-JPG_NormalGL.jpg")


@dataclass(frozen=True, kw_only=True)
class Surface:
    """One PBR material: a texture set and the constants of a Godot StandardMaterial3D."""

    name: str
    maps: Maps
    tile: float  # metres covered by one texture repeat
    tint: Color = (1.0, 1.0, 1.0)  # multiplies the colour map
    roughness_scale: float = 1.0  # multiplies the roughness map
    metallic: float = 0.0
    normal_strength: float = 1.0
    coat: float = 0.0  # clearcoat, for a polish


@dataclass(frozen=True, kw_only=True)
class HdriSky:
    """A photographed Earth sky with a sun lamp at the azimuth of the sky's own sun."""

    file: str  # Poly Haven asset id under assets/textures/sky
    strength: float
    sun_elevation: float  # degrees
    sun_color: Color
    sun_strength: float  # W/m2
    exposure: float


@dataclass(frozen=True, kw_only=True)
class PhysicalSky:
    """Blender's physical sky seen from high up, with a sun lamp and a cloud layer far below.

    `stars` and `planet` are for the edge of space. The lamp may stand higher
    than the sky model's sun, so that low light still reaches the floors.
    """

    altitude: float  # metres above sea level
    sky_sun_elevation: float  # degrees; drives the colours of the sky model
    strength: float  # 1/170 of the lamp's W/m2 is true to the sky model
    sun_elevation: float  # degrees; the lamp
    sun_color: Color
    sun_strength: float  # W/m2
    exposure: float
    cloud_drop: float  # km from the camera down to the cloud tops
    cloud_color: Color  # radiance of a sunlit cloud top
    stars: float = 0.0  # radiance of the brightest stars
    planet: bool = False


Sky = HdriSky | PhysicalSky


@dataclass(frozen=True, kw_only=True)
class Look:
    """One candidate look: the stone, the brass and the dawn light."""

    name: str
    stone: Surface  # floors and walls
    brass: Surface  # lips, borders and gears
    sky: HdriSky


@dataclass(frozen=True, kw_only=True)
class Shot:
    """One render: a look, a camera and where the marble rests. `sky` replaces the look's dawn sky."""

    name: str  # the file is render-<name>.webp
    look: str
    eye: Point
    target: Point
    lens: float  # mm on a 36 mm wide sensor
    marble_at: tuple[float, float] = (-1.0, -1.75)  # on the plaza
    marble: MarbleLook = "glass"
    sky: PhysicalSky | None = None
    fstop: float | None = None  # depth of field, focused on the marble


# Gold inlays: the clock face, the lines on the beam, and (polished) the marble's metal.
GOLD = Surface(name="gold", maps=ambient_cg("metal/Metal048A"), tile=0.6, metallic=1.0, tint=(1.0, 0.82, 0.5), roughness_scale=5.0)  # fmt: skip
POLISHED_GOLD = Surface(name="polished_gold", maps=ambient_cg("metal/Metal048A"), tile=0.2, metallic=1.0)
# Marble B: polished blue-black stone.
BLUE_STONE = Surface(name="blue_stone", maps=ambient_cg("stone/Marble023"), tile=1.0, tint=(0.55, 0.8, 1.5), roughness_scale=0.3, normal_strength=0.3, coat=1.0)  # fmt: skip

# The stone maps are darker than limestone, so each tint is above 1. Bake the tint into the
# colour map when a look is approved; Godot's albedo colour should stay at or below 1.
LOOKS: tuple[Look, ...] = (
    # Warm honey limestone, lightly weathered, and aged brass in a golden dawn.
    Look(
        name="A",
        stone=Surface(name="limestone_a", maps=poly_haven("stone/scuffed_cement"), tile=1.5, tint=(2.6, 3.0, 3.5)),
        brass=Surface(name="brass_a", maps=ambient_cg("metal/Metal007"), tile=0.7, metallic=0.85, tint=(1.0, 1.1, 1.4), roughness_scale=2.4),
        sky=HdriSky(file="syferfontein_6d_clear_puresky", strength=0.8, sun_elevation=12.0, sun_color=(1.0, 0.68, 0.42), sun_strength=24.0, exposure=-1.75),
    ),
    # Pale cream limestone, clean, and satin brass in a soft pink dawn.
    Look(
        name="B",
        stone=Surface(name="limestone_b", maps=poly_haven("stone/concrete_wall_008"), tile=1.6, tint=(2.3, 2.45, 3.0)),
        brass=Surface(name="brass_b", maps=ambient_cg("metal/Metal048A"), tile=1.0, metallic=1.0, tint=(0.9, 0.8, 0.62), roughness_scale=3.0),
        sky=HdriSky(file="qwantani_dusk_2_puresky", strength=0.9, sun_elevation=8.0, sun_color=(1.0, 0.6, 0.46), sun_strength=14.0, exposure=-1.5),
    ),
    # Grey limestone, heavily weathered, and dark bronze at first light, with the sun on the horizon.
    Look(
        name="C",
        stone=Surface(name="limestone_c", maps=poly_haven("stone/dirty_concrete"), tile=1.6, tint=(1.6, 1.7, 1.9)),
        brass=Surface(name="brass_c", maps=ambient_cg("metal/Metal008"), tile=1.2, metallic=1.0, roughness_scale=1.3),
        sky=HdriSky(file="syferfontein_1d_clear_puresky", strength=1.6, sun_elevation=4.5, sun_color=(1.0, 0.56, 0.3), sun_strength=18.0, exposure=-1.4),
    ),
)  # fmt: skip
BEST = "A"  # the look of every shot that is not a candidate

# Intermediate tier: high in thin air at noon. Deep blue sky, a hint of the Earth's curve, no planet.
NOON = PhysicalSky(
    altitude=16000.0, sky_sun_elevation=58.0, strength=0.2, sun_elevation=58.0, sun_color=(1.0, 0.97, 0.92),
    sun_strength=24.0, exposure=-2.5, cloud_drop=7.0, cloud_color=(5.6, 5.6, 5.7),
)  # fmt: skip
# Advanced tier: the edge of space at dusk. One planet low on the horizon behind the haze, faint stars.
DUSK = PhysicalSky(
    altitude=80000.0, sky_sun_elevation=-5.5, strength=0.6, sun_elevation=7.0, sun_color=(1.0, 0.56, 0.3),
    sun_strength=12.0, exposure=0.2, cloud_drop=70.0, cloud_color=(0.035, 0.05, 0.085), stars=4.0, planet=True,
)  # fmt: skip

OVERVIEW_EYE: Point = (-1.0, -8.8, 4.2)  # a high three-quarter view, like a level overview
OVERVIEW_TARGET: Point = (1.7, 3.9, 0.3)
OVERVIEW_LENS = 24.0
GEM_AT = (1.95, -0.85)  # the plaza gem, between the clock face and the lip

SHOTS: tuple[Shot, ...] = (
    Shot(name="a", look="A", eye=OVERVIEW_EYE, target=OVERVIEW_TARGET, lens=OVERVIEW_LENS),
    Shot(name="b", look="B", eye=OVERVIEW_EYE, target=OVERVIEW_TARGET, lens=OVERVIEW_LENS),
    Shot(name="c", look="C", eye=OVERVIEW_EYE, target=OVERVIEW_TARGET, lens=OVERVIEW_LENS),
    # The view of the player: low, close behind the marble, toward the fork; a gem and the brass lip beside it.
    Shot(name="eye", look=BEST, eye=(0.91, -2.85, 0.55), target=(1.56, -0.43, 0.2), lens=26.0, marble_at=(1.3, -1.4), fstop=5.6),
    Shot(name="noon", look=BEST, eye=OVERVIEW_EYE, target=OVERVIEW_TARGET, lens=OVERVIEW_LENS, sky=NOON),
    Shot(name="dusk", look=BEST, eye=OVERVIEW_EYE, target=OVERVIEW_TARGET, lens=OVERVIEW_LENS, sky=DUSK),
    Shot(name="gem", look=BEST, eye=(1.75, -2.74, 0.5), target=(1.64, -0.87, 0.45), lens=35.0, marble_at=(1.32, -0.885), fstop=5.6),
    Shot(name="marble-a", look=BEST, eye=(-0.99, 0.55, 0.3), target=(-0.6, -0.9, 0.21), lens=50.0, marble_at=(-0.6, -0.9), fstop=5.6),
    Shot(name="marble-b", look=BEST, eye=(-0.99, 0.55, 0.3), target=(-0.6, -0.9, 0.21), lens=50.0, marble_at=(-0.6, -0.9), fstop=5.6, marble="stone"),
)  # fmt: skip


@dataclass(frozen=True)
class Frame:
    """A cross-section plane on a path: origin, right and up axes, distance along the path."""

    origin: Vector
    right: Vector
    up: Vector
    distance: float

    def at(self, x: float, z: float) -> Vector:
        return self.origin + self.right * x + self.up * z

    @property
    def forward(self) -> Vector:
        return self.up.cross(self.right)

    def matrix(self, x: float = 0.0, z: float = 0.0) -> Matrix:
        """Return a transform whose X, Y, Z axes are right, forward, up at the point (x, z)."""
        rotation = Matrix((self.right, self.forward, self.up)).transposed().to_4x4()
        return Matrix.Translation(self.at(x, z)) @ rotation

    def moved(self, along: float) -> Frame:
        """Return this frame moved `along` the path direction."""
        return Frame(self.origin + self.forward * along, self.right, self.up, self.distance + along)


def direction(azimuth: float, elevation: float) -> Vector:
    """Return the unit vector for an azimuth (degrees from +X, counter-clockwise) and an elevation."""
    a, e = math.radians(azimuth), math.radians(elevation)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def polar(radius: float, angle: float, z: float = 0.0) -> Vector:
    return Vector((radius * math.cos(angle), radius * math.sin(angle), z))


def smoothstep(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def path_frame(origin: Vector, heading: float, slope: float, bank: float, distance: float) -> Frame:
    """Return the frame of a path that points along `heading` (radians, clockwise from +Y) and climbs at `slope`."""
    forward = Vector((math.sin(heading), math.cos(heading), slope)).normalized()
    flat_right = forward.cross(UP).normalized()
    flat_up = flat_right.cross(forward)
    right = flat_right * math.cos(bank) - flat_up * math.sin(bank)
    return Frame(origin, right, right.cross(forward), distance)


def route_frames(step: float = 0.1) -> list[Frame]:
    """Return the centre line of the safe route: out of the plaza, round a banked right turn, up to the terrace."""
    arc = ARC_RADIUS * ARC_ANGLE
    total = STRAIGHT_IN + arc + STRAIGHT_OUT
    climb_from, climb_to = STRAIGHT_IN - 0.2, total - 0.5
    count = round(total / step)
    frames: list[Frame] = []
    for index in range(count + 1):
        distance = total * index / count
        on_arc = min(max(distance - STRAIGHT_IN, 0.0), arc)
        after = max(distance - STRAIGHT_IN - arc, 0.0)
        heading = on_arc / ARC_RADIUS
        t = min(max((distance - climb_from) / (climb_to - climb_from), 0.0), 1.0)
        origin = Vector((
            ARC_RADIUS * (1 - math.cos(heading)) + after * math.sin(ARC_ANGLE),
            PLAZA_RADIUS - OVERLAP + min(distance, STRAIGHT_IN) + ARC_RADIUS * math.sin(heading) + after * math.cos(ARC_ANGLE),
            TERRACE_HEIGHT * smoothstep(t),
        ))  # fmt: skip
        slope = TERRACE_HEIGHT * 6 * t * (1 - t) / (climb_to - climb_from)
        bank = BANK * math.sin(math.pi * on_arc / arc) ** 2
        frames.append(path_frame(origin, heading, slope, bank, distance))
    return frames


def line_frames(start: Vector, end: Vector, rise: Callable[[float], float], step: float = 0.1) -> list[Frame]:
    """Return the frames of a path that is straight in plan from `start` to `end`.

    `rise(t)` is the height above `start` at the fraction t of the plan length.
    """
    plan = (end - start).to_2d()
    length = plan.length
    heading = math.atan2(plan.x, plan.y)
    count = max(1, round(length / step))
    frames: list[Frame] = []
    for index in range(count + 1):
        t = index / count
        slope = (rise(min(t + 0.5 / count, 1.0)) - rise(max(t - 0.5 / count, 0.0))) / (length / count)
        origin = Vector((start.x + plan.x * t, start.y + plan.y * t, start.z + rise(t)))
        frames.append(path_frame(origin, heading, slope, 0.0, length * t))
    return frames


def ring_frames(centre: Vector, radius: float, axis: Vector = UP, segments: int = 192, girth: float | None = None) -> list[Frame]:  # fmt: skip
    """Return the frames of a closed circle around `axis`; frame.right points outward.

    With radius 0 the frames turn on the axis, for a profile given in absolute
    radii; `girth` is then the radius at which the texture is laid around it.
    """
    axis = axis.normalized()
    side = Vector((1.0, 0.0, 0.0)) if abs(axis.z) > 0.99 else axis.orthogonal().normalized()
    other = axis.cross(side)
    frames: list[Frame] = []
    for index in range(segments):
        angle = 2 * math.pi * index / segments
        outward = side * math.cos(angle) + other * math.sin(angle)
        frames.append(Frame(centre + outward * radius, outward, axis, (radius if girth is None else girth) * angle))
    return frames


def open_runs(frames: list[Frame], blocked: Callable[[Frame], bool]) -> list[list[Frame]]:
    """Split a path into the runs of frames that are not blocked."""
    runs: list[list[Frame]] = [[]]
    for frame in frames:
        if blocked(frame):
            runs.append([])
        else:
            runs[-1].append(frame)
    return [run for run in runs if len(run) >= 3]


def ring_runs(ring: list[Frame], mouths: list[tuple[Vector, float]]) -> list[list[Frame]]:
    """Split a closed ring into the runs that stay clear of every mouth.

    A mouth is a point on the ring and a half-width: the place where a route
    joins a pad, which the pad's lip must leave open.
    """

    def blocked(frame: Frame) -> bool:
        return any((frame.origin - point).to_2d().length < half for point, half in mouths)

    first = next(index for index, frame in enumerate(ring) if blocked(frame))
    return open_runs(ring[first:] + ring[:first], blocked)


def circle_profile(radius: float, segments: int = 10) -> Profile:
    return [(radius * math.cos(2 * math.pi * i / segments), radius * math.sin(2 * math.pi * i / segments)) for i in range(segments)]  # fmt: skip


def rect_profile(x0: float, x1: float, z0: float, z1: float, bevel: float = 0.0) -> Profile:
    """Return a rectangle cross-section, with its four corners cut by `bevel`."""
    if bevel == 0.0:
        return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    b = bevel
    return [(x0 + b, z0), (x1 - b, z0), (x1, z0 + b), (x1, z1 - b), (x1 - b, z1), (x0 + b, z1), (x0, z1 - b), (x0, z0 + b)]  # fmt: skip


def lip_profile(width: float, height: float, drop: float) -> Profile:
    """Return the cross-section of a banked lip: a concave slope that rises outward from the floor.

    X is 0 at the outer edge of the floor and negative inward. The slope starts
    flush with the floor at -width, so a marble rolls up it and back.
    """
    points: Profile = [(0.045, -drop), (0.045, height - 0.02), (0.025, height), (-0.03, height)]
    steps = 10
    for index in range(1, steps + 1):
        t = index / steps
        points.append((-0.03 - (width - 0.03) * t, STEP + (height - STEP) * (1 - t) ** 2))
    return [*points, (-width, -0.012), (-0.06, -0.012), (-0.06, -drop)]


def offset_profile(profile: Profile, x: float, mirror: bool = False) -> Profile:
    """Move a profile sideways by `x`; `mirror` flips it first, for the left edge of a path."""
    return [((-px if mirror else px) + x, pz) for px, pz in profile]


class Builder:
    """Collects geometry in one bmesh and turns it into one object with one material.

    Every `add_*` method appends geometry. Lengths are metres. UVs are metres
    too; `finish` scales them by 1/tile.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.verify()
        self.shade = self.bm.faces.layers.float.new("shade")  # per face: how much darker than the material

    def darken(self, first: int, amount: float) -> None:
        """Darken the faces added since the face count `first` by `amount` (0..1), as a vertex colour."""
        self.bm.faces.ensure_lookup_table()
        for face in self.bm.faces[first:]:
            face[self.shade] = amount

    def add_sweep(self, frames: list[Frame], profile: Profile, *, closed: bool = False, shift: tuple[float, float] = (0.0, 0.0)) -> None:  # fmt: skip
        """Sweep a closed cross-section along the frames. `closed` joins the last frame to the first.

        UVs run along the path (U) and around the profile (V), moved by `shift`.
        """
        rings = [[self.bm.verts.new(frame.at(x, z)) for x, z in profile] for frame in frames]
        girth = [0.0]
        for (x0, z0), (x1, z1) in zip(profile, [*profile[1:], profile[0]], strict=True):
            girth.append(girth[-1] + math.hypot(x1 - x0, z1 - z0))
        pairs = list(zip(range(len(frames) - 1), range(1, len(frames)), strict=True))
        if closed:
            pairs.append((len(frames) - 1, 0))
        for a, b in pairs:
            u0 = frames[a].distance + shift[0]
            u1 = (frames[b].distance if b else frames[a].distance + frames[1].distance - frames[0].distance) + shift[0]
            for j in range(len(profile)):
                k = (j + 1) % len(profile)
                face = self.bm.faces.new((rings[a][j], rings[a][k], rings[b][k], rings[b][j]))
                v0, v1 = girth[j] + shift[1], girth[j + 1] + shift[1]
                for loop, uv in zip(face.loops, ((u0, v0), (u0, v1), (u1, v1), (u1, v0)), strict=True):
                    loop[self.uv].uv = uv
        if not closed:
            for ring in (rings[0], rings[-1]):
                face = self.bm.faces.new(ring)
                for loop, uv in zip(face.loops, profile, strict=True):
                    loop[self.uv].uv = uv

    def add_sector(self, centre: Vector, r0: float, r1: float, a0: float, a1: float, thickness: float, uv: Matrix) -> None:  # fmt: skip
        """Add one floor slab: a ring sector whose top face is at `centre`. `uv` maps world XY to UV."""
        count = max(2, math.ceil((a1 - a0) / math.radians(2.0)))
        rows = []
        for index in range(count + 1):
            out = polar(1.0, a0 + (a1 - a0) * index / count)
            rows.append([self.bm.verts.new(centre + out * r - UP * d) for r in (r0, r1) for d in (0.0, thickness)])
        quads = [(rows[0][0], rows[0][1], rows[0][3], rows[0][2]), (rows[-1][0], rows[-1][2], rows[-1][3], rows[-1][1])]
        for a, b in zip(rows, rows[1:], strict=False):
            quads += [(a[0], a[2], b[2], b[0]), (a[1], b[1], b[3], a[3]), (a[0], b[0], b[1], a[1]), (a[2], a[3], b[3], b[2])]
        for quad in quads:
            face = self.bm.faces.new(quad)
            for loop in face.loops:
                loop[self.uv].uv = (uv @ loop.vert.co).to_2d()

    def add_cylinder(self, base: Vector, axis: Vector, height: float, radius: float, top_radius: float | None = None, segments: int = 32) -> None:  # fmt: skip
        """Add a capped cylinder or cone that stands on `base` and points along `axis`."""
        axis = axis.normalized()
        rotation = axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
        matrix = Matrix.Translation(base + axis * height / 2) @ rotation
        bmesh.ops.create_cone(
            self.bm, cap_ends=True, segments=segments, radius1=radius,
            radius2=radius if top_radius is None else top_radius, depth=height, matrix=matrix, calc_uvs=True,
        )  # fmt: skip

    def add_sphere(self, centre: Vector, radius: float, segments: int = 48) -> None:
        bmesh.ops.create_uvsphere(
            self.bm, u_segments=segments, v_segments=segments // 2, radius=radius,
            matrix=Matrix.Translation(centre), calc_uvs=True,
        )  # fmt: skip

    def add_box(self, matrix: Matrix, size: tuple[float, float, float]) -> None:
        """Add a box of `size` centred on `matrix`, with UVs in metres."""
        start = len(self.bm.faces)
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=matrix @ Matrix.Diagonal((*size, 1.0)), calc_uvs=False)
        self.bm.faces.ensure_lookup_table()
        inverse = matrix.inverted()
        for face in self.bm.faces[start:]:
            for loop in face.loops:
                local = inverse @ loop.vert.co
                loop[self.uv].uv = (local.x + local.z, local.y + local.z)

    def add_disc(self, centre: Vector, radius: float, thickness: float, uv: Matrix, segments: int = 64) -> None:
        """Add a round floor slab whose top face is at `centre`. `uv` maps world XY to UV."""
        start = len(self.bm.faces)
        self.add_cylinder(centre - UP * thickness, UP, thickness, radius, segments=segments)
        self.bm.faces.ensure_lookup_table()
        for face in self.bm.faces[start:]:
            for loop in face.loops:
                loop[self.uv].uv = (uv @ loop.vert.co).to_2d()

    def add_spindle(self, centre: Vector, rings: list[tuple[float, float]], sides: int) -> None:
        """Add a faceted solid of revolution: `rings` are (radius, z) from top to bottom; radius 0 is a point."""
        loops: list[list[bmesh.types.BMVert]] = []
        for radius, z in rings:
            if radius == 0.0:
                loops.append([self.bm.verts.new(centre + UP * z)])
            else:
                loops.append([self.bm.verts.new(centre + polar(radius, 2 * math.pi * i / sides, z)) for i in range(sides)])
        if len(loops[0]) > 1:
            self.bm.faces.new(loops[0])
        if len(loops[-1]) > 1:
            self.bm.faces.new(loops[-1])
        for upper, lower in zip(loops, loops[1:], strict=False):
            for i in range(sides):
                j = (i + 1) % sides
                if len(upper) == 1:
                    self.bm.faces.new((upper[0], lower[i], lower[j]))
                elif len(lower) == 1:
                    self.bm.faces.new((upper[i], lower[0], upper[j]))
                else:
                    self.bm.faces.new((upper[i], lower[i], lower[j], upper[j]))

    def add_gem(self, centre: Vector, cut: GemCut, size: float) -> None:
        """Add a cut gem whose largest dimension is `size`, centred on `centre`."""
        self.add_spindle(centre, [(r * size, z * size) for r, z in GEM_RINGS[cut]], 12 if cut == "brilliant" else 6)

    def add_gear(self, matrix: Matrix, radius: float, teeth: int, thickness: float, bore: float) -> None:
        """Add a spur gear in the XY plane of `matrix`: `radius` is the tooth tip, `bore` the hole."""
        root = radius - 0.55 * (2 * math.pi * radius / teeth)
        outline: Profile = []
        for tooth in range(teeth):
            for fraction, r in ((0.0, root), (0.18, radius), (0.5, radius), (0.68, root)):
                angle = 2 * math.pi * (tooth + fraction) / teeth
                outline.append((r * math.cos(angle), r * math.sin(angle)))
        layers = []
        for z in (-thickness / 2, thickness / 2):
            outer = [Vector((x, y, z)) for x, y in outline]
            inner = [Vector((x * bore / math.hypot(x, y), y * bore / math.hypot(x, y), z)) for x, y in outline]
            layers.append((outer, inner))
        (outer0, inner0), (outer1, inner1) = layers
        count = len(outline)
        for i in range(count):
            j = (i + 1) % count
            around = 2 * math.pi * radius * i / count
            for corners, flat in (
                ((outer0[i], outer0[j], inner0[j], inner0[i]), True),
                ((outer1[i], outer1[j], inner1[j], inner1[i]), True),
                ((outer0[i], outer0[j], outer1[j], outer1[i]), False),
                ((inner0[i], inner0[j], inner1[j], inner1[i]), False),
            ):
                face = self.bm.faces.new([self.bm.verts.new(matrix @ corner) for corner in corners])
                for loop, corner in zip(face.loops, corners, strict=True):
                    loop[self.uv].uv = (corner.x, corner.y) if flat else (around + (corner - corners[0]).length, corner.z)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-5)

    def finish(self, material: bpy.types.Material, parent: bpy.types.Object, *, tile: float = 1.0, sharp_angle: float = 40.0, flat: bool = False) -> bpy.types.Object:  # fmt: skip
        """Create the object: fix normals, scale UVs to `tile` metres per repeat, shade smooth (or `flat`)."""
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        tint = self.bm.loops.layers.float_color.new("tint")
        for face in self.bm.faces:
            face.smooth = not flat
            value = 1.0 - face[self.shade]
            for loop in face.loops:
                loop[self.uv].uv = loop[self.uv].uv / tile
                loop[tint] = (value, value, value, 1.0)
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        if not flat:
            mesh.set_sharp_from_angle(angle=math.radians(sharp_angle))
        mesh.materials.append(material)
        obj = bpy.data.objects.new(self.name, mesh)
        obj.parent = parent
        bpy.context.scene.collection.objects.link(obj)
        return obj


def new_material(name: str) -> tuple[bpy.types.Material, bpy.types.NodeTree, bpy.types.Node]:
    """Return a material with an empty node tree and its output node."""
    material = bpy.data.materials.new(name)
    tree = material.node_tree
    tree.nodes.clear()
    return material, tree, tree.nodes.new("ShaderNodeOutputMaterial")


def node(tree: bpy.types.NodeTree, kind: str, /, **settings: object) -> bpy.types.Node:
    """Add a node. A keyword that names a node property sets it; any other sets that input socket.

    Write a socket name with `_` for a space ("From_Min"). A socket value can be a
    constant or another node's output socket, which is then linked.
    """
    new = tree.nodes.new(kind)
    for key, value in settings.items():
        if hasattr(new, key):
            setattr(new, key, value)
        elif isinstance(value, bpy.types.NodeSocket):
            tree.links.new(value, new.inputs[key.replace("_", " ")])
        else:
            new.inputs[key.replace("_", " ")].default_value = value
    return new


def math_node(tree: bpy.types.NodeTree, operation: str, *values: object) -> bpy.types.NodeSocket:
    """Add a Math node on constants or sockets and return its result socket."""
    new = tree.nodes.new("ShaderNodeMath")
    new.operation = operation
    for index, value in enumerate(values):
        if isinstance(value, bpy.types.NodeSocket):
            tree.links.new(value, new.inputs[index])
        else:
            new.inputs[index].default_value = value
    return new.outputs["Value"]


def load_image(path: Path, *, data: bool) -> bpy.types.Image:
    image = bpy.data.images.load(str(path), check_existing=True)
    if data:
        image.colorspace_settings.name = "Non-Color"
    return image


def pbr_material(surface: Surface, *, box: float | None = None) -> bpy.types.Material:
    """Return the PBR material of a surface, UV-mapped. `box` projects it from three sides at that scale (no seam on a sphere)."""
    material, tree, output = new_material(surface.name)
    settings: dict[str, object] = {}
    if box is not None:
        coords = node(tree, "ShaderNodeTexCoord")
        mapping = node(tree, "ShaderNodeMapping", Vector=coords.outputs["Object"], Scale=(box, box, box))
        settings = {"projection": "BOX", "projection_blend": 0.25, "Vector": mapping.outputs["Vector"]}

    def texture(file: str, *, data: bool) -> bpy.types.NodeSocket:
        return node(tree, "ShaderNodeTexImage", image=load_image(TEXTURES / file, data=data), **settings).outputs["Color"]

    # Colour = map x tint x vertex colour, as in Godot with "vertex colour as albedo" on.
    tint = node(tree, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY", Factor=1.0, A=texture(surface.maps.color, data=False), B=(*surface.tint, 1.0))  # fmt: skip
    if box is None:
        vertex = node(tree, "ShaderNodeVertexColor", layer_name="tint")
        tint = node(tree, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY", Factor=1.0, A=tint.outputs["Result"], B=vertex.outputs["Color"])  # fmt: skip
    roughness = math_node(tree, "MULTIPLY", texture(surface.maps.roughness, data=True), surface.roughness_scale)
    normal = node(tree, "ShaderNodeNormalMap", Strength=surface.normal_strength, Color=texture(surface.maps.normal, data=True))
    shader = node(
        tree, "ShaderNodeBsdfPrincipled", Base_Color=tint.outputs["Result"], Roughness=roughness,
        Metallic=surface.metallic, Normal=normal.outputs["Normal"], Coat_Weight=surface.coat, Coat_Roughness=0.03,
    )  # fmt: skip
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def glass_material(name: str) -> bpy.types.Material:
    """Return the glass of the marble: clear, with a pale cool tint and a strong rim, so that it stands out on warm stone."""
    material, tree, output = new_material(name)
    shader = node(tree, "ShaderNodeBsdfPrincipled", Base_Color=(0.74, 0.9, 1.0, 1.0), Roughness=0.0, IOR=1.65, Transmission_Weight=1.0)
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def gem_material(name: str, color: Color, glow: float) -> bpy.types.Material:
    """Return a cut gem: deeply coloured glass that also glows a little in its own colour."""
    material, tree, output = new_material(name)
    shader = node(
        tree, "ShaderNodeBsdfPrincipled", Base_Color=(*color, 1.0), Roughness=0.0, IOR=2.2, Transmission_Weight=1.0,
        Emission_Color=(*color, 1.0), Emission_Strength=glow,
    )  # fmt: skip
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def beam_material(name: str, color: Color, strength: float) -> bpy.types.Material:
    """Return the light beam above a gem: additive, soft at its sides, fading out toward its top.

    In Godot this is an unshaded additive material with a vertical gradient and a rim fade.
    """
    material, tree, output = new_material(name)
    height = node(tree, "ShaderNodeSeparateXYZ", Vector=node(tree, "ShaderNodeTexCoord").outputs["Generated"]).outputs["Z"]
    fade = math_node(tree, "POWER", math_node(tree, "SUBTRACT", 1.0, height), 1.6)
    facing = node(tree, "ShaderNodeLayerWeight", Blend=0.5).outputs["Facing"]
    core = math_node(tree, "POWER", math_node(tree, "SUBTRACT", 1.0, facing), 2.5)
    glow = node(tree, "ShaderNodeEmission", Color=(*color, 1.0), Strength=math_node(tree, "MULTIPLY", math_node(tree, "MULTIPLY", fade, core), strength))  # fmt: skip
    add = node(tree, "ShaderNodeAddShader")
    tree.links.new(node(tree, "ShaderNodeBsdfTransparent").outputs["BSDF"], add.inputs[0])
    tree.links.new(glow.outputs["Emission"], add.inputs[1])
    tree.links.new(add.outputs["Shader"], output.inputs["Surface"])
    return material


def blob_shadow_material() -> bpy.types.Material:
    """Return the blob shadow: a dark disc with a crisp edge, see-through outside it."""
    material, tree, output = new_material("blob_shadow")
    coords = node(tree, "ShaderNodeTexCoord")
    length = node(tree, "ShaderNodeVectorMath", operation="LENGTH")
    tree.links.new(coords.outputs["Object"], length.inputs[0])
    edge = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=length.outputs["Value"], From_Min=0.88, From_Max=1.0, To_Min=0.72, To_Max=0.0)  # fmt: skip
    clear = node(tree, "ShaderNodeBsdfTransparent")
    dark = node(tree, "ShaderNodeBsdfDiffuse", Color=(0.0, 0.0, 0.0, 1.0))
    mix = node(tree, "ShaderNodeMixShader", Factor=edge.outputs["Result"])
    tree.links.new(clear.outputs["BSDF"], mix.inputs[1])
    tree.links.new(dark.outputs["BSDF"], mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], output.inputs["Surface"])
    return material


def cloud_material(top: float, depth: float) -> bpy.types.Material:
    """Return the cloud-sea volume: noise that thins out toward `top` (world Z, metres)."""
    material, tree, output = new_material("cloud_sea")
    position = node(tree, "ShaderNodeNewGeometry").outputs["Position"]
    noise = node(tree, "ShaderNodeTexNoise", Vector=position, Scale=0.0045, Detail=6.0, Roughness=0.55)
    split = node(tree, "ShaderNodeSeparateXYZ", Vector=position)
    # The cover threshold rises with height, so only the strongest noise reaches the top: cloud heaps.
    threshold = node(tree, "ShaderNodeMapRange", Value=split.outputs["Z"], From_Min=top - 40.0, From_Max=top, To_Min=0.3, To_Max=0.6)  # fmt: skip
    cover = math_node(tree, "SUBTRACT", noise.outputs["Factor"], threshold.outputs["Result"])
    density = node(tree, "ShaderNodeMapRange", Value=cover, From_Min=0.0, From_Max=0.08, To_Min=0.0, To_Max=0.3)
    volume = node(tree, "ShaderNodeVolumePrincipled", Color=(1.0, 1.0, 1.0, 1.0), Anisotropy=0.35, Density=density.outputs["Result"])
    tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return material


@dataclass
class Parts:
    """The builders of the play space, one per material."""

    stone: Builder
    brass: Builder
    gold: Builder
    rng: random.Random

    def slab_uv(self) -> Matrix:
        """Return a random placement of the stone texture, so that no two slabs look alike."""
        turn = Matrix.Rotation(self.rng.choice((0.0, 0.5, 1.0, 1.5)) * math.pi, 4, "Z")
        return Matrix.Translation((self.rng.uniform(0.0, 8.0), self.rng.uniform(0.0, 8.0), 0.0)) @ turn

    def slab_shade(self) -> float:
        """Return how much darker one slab is than the stone: real slabs differ a little."""
        return self.rng.uniform(0.0, 0.16)


def add_pad(parts: Parts, centre: Vector, radius: float, mouths: list[tuple[Vector, float]], rings: list[tuple[float, int, float]], *, lip: tuple[float, float], depth: float) -> None:  # fmt: skip
    """Add a round tower top: a floor of slabs laid in rings, a banked brass lip, a gear band and a stone drum.

    `rings` lists the slab rings from the centre outward as (outer radius, slab
    count, first joint angle). `lip` is the (width, height) of the brass lip,
    which stays open at each mouth. `depth` is the height of the drum.
    """
    floor = centre - UP * STEP
    inner = 0.0
    for outer, count, phase in rings:
        if inner == 0.0:
            parts.stone.add_disc(floor, outer - JOINT / 2, 0.1, parts.slab_uv())
        for index in range(count if inner > 0.0 else 0):
            gap = JOINT / (inner + outer)  # half the joint, as an angle at the middle radius
            a0, a1 = phase + 2 * math.pi * index / count, phase + 2 * math.pi * (index + 1) / count
            first = len(parts.stone.bm.faces)
            parts.stone.add_sector(floor, inner + JOINT / 2, outer - JOINT / 2, a0 + gap, a1 - gap, 0.1, parts.slab_uv())
            parts.stone.darken(first, parts.slab_shade())
        inner = outer
    first = len(parts.stone.bm.faces)
    parts.stone.add_disc(floor - UP * FLUSH, inner, 0.03, parts.slab_uv())
    parts.stone.darken(first, MORTAR)

    # The body, as one turned profile: bed under the slabs, cornice, recess for the gear, banded drum, bowl.
    drum = radius - 0.16
    profile: Profile = [
        (0.01, -0.014), (radius - 0.02, -0.014), (radius - 0.02, -0.2), (radius + 0.06, -0.2), (radius + 0.06, -0.27),
        (radius - 0.02, -0.34), (radius - 0.12, -0.36), (radius - 0.12, -0.6), (radius, -0.62), (radius, -0.68), (drum, -0.76),
    ]  # fmt: skip
    z = -1.15
    while z > -depth + 0.2:
        profile += [(drum, z + 0.025), (drum - 0.03, z), (drum, z - 0.025)]
        z -= 0.5
    bowl = 0.9 * radius
    profile += [(drum, -depth), (drum - 0.09, -depth - 0.07), (drum - 0.09, -depth - 0.18), (0.3, -depth - bowl), (0.01, -depth - bowl)]
    parts.stone.add_sweep(ring_frames(centre, 0.0, girth=radius), profile, closed=True)
    parts.brass.add_gear(Matrix.Translation(centre - UP * 0.48), radius + 0.1, round(2 * math.pi * radius / 0.36), 0.2, radius - 0.4)
    parts.brass.add_cylinder(centre - UP * (depth + bowl + 0.55), UP, 0.62, 0.0, 0.3)
    parts.brass.add_sphere(centre - UP * (depth + bowl + 0.62), 0.14, segments=24)

    width, height = lip
    for run in ring_runs(ring_frames(centre, radius), mouths):
        parts.brass.add_sweep(run, lip_profile(width, height, 0.19))
        for end in (run[0], run[-1]):  # a low bollard closes each end of the lip
            foot = end.at(-width * 0.45, 0.0)
            parts.brass.add_cylinder(foot, UP, height + 0.04, width * 0.4, width * 0.34, segments=24)
            parts.brass.add_cylinder(foot + UP * (height + 0.04), UP, 0.05, width * 0.2, width * 0.16, segments=24)
            parts.brass.add_sphere(foot + UP * (height + 0.08 + width * 0.3), width * 0.32, segments=32)


def add_deck(parts: Parts, frames: list[Frame], width: float, *, slab: float, kerb: tuple[float, float] | None, blocked: Callable[[Frame, int], bool] | None = None) -> None:  # fmt: skip
    """Add a stone route: a body, a top of slabs with dark joints, a brass keel and (with `kerb`) banked brass borders.

    `kerb` is the (width, height) of the borders. `blocked(frame, side)` leaves
    a border open where another route crosses it; side is -1 (left) or 1 (right).
    """
    half = width / 2
    parts.stone.add_sweep(frames, rect_profile(-half + 0.01, half - 0.01, -DECK_THICKNESS, -0.014, bevel=0.01))
    parts.brass.add_sweep(frames, rect_profile(-0.09, 0.09, -DECK_THICKNESS - 0.14, -DECK_THICKNESS + 0.01, bevel=0.03))
    first = len(parts.stone.bm.faces)
    parts.stone.add_sweep(frames, rect_profile(-half + 0.02, half - 0.02, -0.03, -FLUSH))
    parts.stone.darken(first, MORTAR)
    per_slab = max(2, round(slab / (frames[1].distance - frames[0].distance)))
    for start in range(0, len(frames) - 1, per_slab):
        run = frames[start : start + per_slab + 1]
        if len(run) < 2:
            continue
        run = [run[0].moved(JOINT / 2), *run[1:-1], run[-1].moved(-JOINT / 2)]
        shift = (parts.rng.uniform(0.0, 8.0), parts.rng.uniform(0.0, 8.0))
        first = len(parts.stone.bm.faces)
        parts.stone.add_sweep(run, rect_profile(-half, half, -0.1, 0.0), shift=shift)
        parts.stone.darken(first, parts.slab_shade())
    if kerb is not None:
        for side in (-1, 1):
            profile = offset_profile(lip_profile(kerb[0], kerb[1], 0.1), side * half, mirror=side < 0)
            for run in open_runs(frames, lambda frame, side=side: blocked is not None and blocked(frame, side)):
                parts.brass.add_sweep(run, profile)


def add_clock_face(parts: Parts, radius: float, ring: float) -> None:
    """Set a clock face of gold into the plaza floor: two rings, twelve hour bars, two hands and a hub.

    Twelve o'clock points along +Y, toward the safe route. All of it is flush
    with the floor to within a few millimetres, so the marble rolls over it.
    """
    low, high = -0.012, 0.004
    for r in (ring, radius):
        parts.gold.add_sweep(ring_frames(Vector((0.0, 0.0, 0.0)), r), rect_profile(-0.03, 0.03, low, high), closed=True)
    for hour in range(12):
        spin = Matrix.Rotation(-2 * math.pi * hour / 12, 4, "Z")
        wide = 0.14 if hour % 3 == 0 else 0.075
        parts.gold.add_box(spin @ Matrix.Translation((0.0, (ring + radius) / 2, (low + high) / 2)), (wide, radius - ring - 0.3, high - low))
    for hour_angle, length, wide in ((-2 * math.pi * 10.17 / 12, ring * 0.7, 0.13), (-2 * math.pi * 2 / 12, ring * 0.97, 0.09)):
        spin = Matrix.Rotation(hour_angle, 4, "Z")
        tip, tail = Vector((0.0, length, 0.0)), Vector((0.0, -0.28, 0.0))
        corners = [Vector((-wide / 2, 0.0, 0.0)), tail, Vector((wide / 2, 0.0, 0.0)), tip]
        lower = [parts.gold.bm.verts.new(spin @ (corner + UP * low)) for corner in corners]
        upper = [parts.gold.bm.verts.new(spin @ (corner + UP * (high + 0.002))) for corner in corners]
        parts.gold.bm.faces.new(lower)
        parts.gold.bm.faces.new(upper)
        for i in range(4):
            parts.gold.bm.faces.new((lower[i], lower[(i + 1) % 4], upper[(i + 1) % 4], upper[i]))
    parts.gold.add_cylinder(Vector((0.0, 0.0, low)), UP, high + 0.008 - low, 0.17, segments=48)


@dataclass(frozen=True)
class Gem:
    """A gem pickup: its cut and the point on the floor below it."""

    cut: GemCut
    floor: Vector


def gem_centre(gem: Gem) -> Vector:
    """Return the centre of a gem that hovers GEM_HOVER above its floor point."""
    return gem.floor + UP * (GEM_HOVER - GEM_RINGS[gem.cut][-1][1] * GEM_SIZE)


def build_gems(gems: list[Gem], root: bpy.types.Object, glow: float) -> None:
    """Build the gems: cut, glowing, coloured glass, a soft light on the floor below and a faint beam above.

    `glow` scales the emission to the exposure of the shot. Every colour emits
    the same luminance, so that no gem outshines another.
    """
    for cut, color in GEM_COLORS.items():
        level = 0.2 / (0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2])  # brings this colour to one luminance
        mine = [gem for gem in gems if gem.cut == cut]
        if not mine:
            continue
        shell, beam = Builder(f"gem_{cut}"), Builder(f"gem_beam_{cut}")
        for gem in mine:
            centre = gem_centre(gem)
            shell.add_gem(centre, cut, GEM_SIZE)
            beam.add_cylinder(centre, UP, 3.2, 0.065, 0.05, segments=24)
            light = bpy.data.lights.new(f"gem_light_{cut}", "POINT")
            light.color = color
            light.energy = 14.0 * glow * level
            light.shadow_soft_size = 0.1
            lamp = bpy.data.objects.new(light.name, light)
            lamp.location = gem.floor + UP * (GEM_HOVER * 0.75)
            lamp.parent = root
            bpy.context.scene.collection.objects.link(lamp)
        jewel = shell.finish(gem_material(f"gem_{cut}", color, 0.22 * glow * level), root, flat=True)
        jewel.visible_shadow = False  # the light on the floor marks the spot below a gem
        rays = beam.finish(beam_material(f"gem_beam_{cut}", tuple(0.12 + channel * level for channel in color), 0.5 * glow), root)
        rays.visible_shadow = False
        rays.visible_diffuse = False
        rays.visible_glossy = False


def build_course(look: Look, root: bpy.types.Object, *, caustics: bool) -> list[Gem]:
    """Build the play space and return its gems.

    `caustics` lets the floor show the sunlight that the glass marble focuses;
    it is slow, so only the close-ups use it.

    The plaza is at the origin. The safe route leaves it along +Y and turns
    right, up to the terrace. The beam leaves the route at the fork and climbs
    straight to the terrace. The bridge drops to the islet.
    """
    parts = Parts(Builder("stone"), Builder("brass"), Builder("gold"), random.Random(5))
    route = route_frames()
    half = DECK_WIDTH / 2
    plaza = Vector((0.0, 0.0, 0.0))
    last = route[-1]
    terrace = last.origin + Vector((math.sin(ARC_ANGLE), math.cos(ARC_ANGLE), 0.0)) * (TERRACE_RADIUS - OVERLAP)
    islet = polar(PLAZA_RADIUS + BRIDGE_LENGTH + ISLET_RADIUS - 2 * OVERLAP, BRIDGE_ANGLE, -ISLET_DROP)

    # The beam: level while it lies on the route, then one smooth climb to the terrace.
    fork = next(frame for frame in route if frame.distance >= FORK_AT)
    beam_start = fork.at(0.25, STEP)
    landing = Vector((terrace.x, terrace.y, STEP)) + polar(TERRACE_RADIUS, BEAM_LANDING)
    toward = (landing - beam_start).to_2d().normalized().to_3d()
    beam_end = landing + toward * OVERLAP
    level = 1.7 / (beam_end - beam_start).length
    beam = line_frames(beam_start, beam_end, lambda t: TERRACE_HEIGHT * smoothstep((t - level) / (0.94 - level)))

    def beam_crosses(frame: Frame, side: int) -> bool:
        edge = frame.at(side * (half - 0.1), 0.0) - beam_start
        along = edge.dot(toward)
        return side > 0 and along > 0.0 and (edge - toward * along).to_2d().length < BEAM_WIDTH / 2 + 0.08

    add_deck(parts, route, DECK_WIDTH, slab=1.2, kerb=(0.24, 0.08), blocked=beam_crosses)
    add_deck(parts, beam, BEAM_WIDTH, slab=1.15, kerb=None)
    for side in (-1, 1):  # a gold line along each edge marks the shortcut
        parts.gold.add_sweep(beam, rect_profile(side * (BEAM_WIDTH / 2 - 0.07) - 0.02, side * (BEAM_WIDTH / 2 - 0.07) + 0.02, -0.01, 0.004))
    bridge_start = polar(PLAZA_RADIUS - OVERLAP, BRIDGE_ANGLE, STEP)
    bridge_end = polar(PLAZA_RADIUS + BRIDGE_LENGTH - OVERLAP, BRIDGE_ANGLE, STEP)
    bridge = line_frames(bridge_start, bridge_end, lambda t: -ISLET_DROP * smoothstep((t - 0.2) / 0.6))
    add_deck(parts, bridge, BRIDGE_WIDTH, slab=1.1, kerb=(0.2, 0.07))

    clock, ring = 2.1, 1.45
    add_pad(
        parts, plaza, PLAZA_RADIUS,
        [(Vector((0.0, PLAZA_RADIUS, 0.0)), half + 0.3), (polar(PLAZA_RADIUS, BRIDGE_ANGLE), BRIDGE_WIDTH / 2 + 0.28)],
        [(0.5, 1, 0.0), (ring, 8, 0.0), (clock, 12, math.pi / 12), (PLAZA_RADIUS - 0.4, 18, 0.0)],
        lip=(0.44, 0.16), depth=2.0,
    )  # fmt: skip
    add_clock_face(parts, clock, ring)
    add_pad(
        parts, terrace, TERRACE_RADIUS,
        [(terrace - last.forward.to_2d().normalized().to_3d() * TERRACE_RADIUS, half + 0.26), (terrace + polar(TERRACE_RADIUS, BEAM_LANDING), BEAM_WIDTH / 2 + 0.3)],
        [(0.5, 1, 0.0), (1.25, 8, 0.2), (TERRACE_RADIUS - 0.32, 13, 0.0)],
        lip=(0.34, 0.13), depth=1.25,
    )  # fmt: skip
    add_pad(
        parts, islet, ISLET_RADIUS,
        [(islet - polar(ISLET_RADIUS, BRIDGE_ANGLE), BRIDGE_WIDTH / 2 + 0.22)],
        [(0.45, 1, 0.0), (ISLET_RADIUS - 0.27, 8, 0.3)],
        lip=(0.28, 0.11), depth=0.95,
    )  # fmt: skip

    floor = parts.stone.finish(pbr_material(look.stone), root, tile=look.stone.tile)
    floor.cycles.is_caustics_receiver = caustics
    parts.brass.finish(pbr_material(look.brass), root, tile=look.brass.tile)
    parts.gold.finish(pbr_material(GOLD), root, tile=GOLD.tile)

    arc_middle = next(frame for frame in route if frame.distance >= STRAIGHT_IN + ARC_RADIUS * ARC_ANGLE * 0.5)
    return [
        Gem("bipyramid", Vector((*GEM_AT, 0.0))),
        Gem("bipyramid", terrace + Vector((0.5, -0.2, 0.0))),
        Gem("hexagon", arc_middle.origin.copy()),
        Gem("hexagon", islet.copy()),
        Gem("brilliant", beam[round(len(beam) * 0.56)].origin.copy()),  # the reward for the risky route
    ]


def build_marble(look: MarbleLook, at: tuple[float, float], root: bpy.types.Object) -> None:
    """Build the marble at rest on the plaza, and its blob shadow straight below it."""
    centre = Vector((*at, MARBLE_RADIUS))
    tilts = (Vector((0.35, 0.2, 1.0)), Vector((1.0, 0.3, 0.45)), Vector((-0.4, 1.0, 0.3)))
    shell = Builder("marble")
    shell.add_sphere(centre, MARBLE_RADIUS, segments=96)
    detail = Builder("marble_detail")
    if look == "glass":
        # Clear glass around a small brass orrery: a ball, three rings and three planets.
        ball = shell.finish(glass_material("marble_glass"), root)
        ball.cycles.is_caustics_caster = True
        detail.add_sphere(centre, 0.075, segments=32)
        for index, (axis, radius) in enumerate(zip(tilts, (0.105, 0.13, 0.155), strict=True)):
            ring = ring_frames(centre, radius, axis, segments=64)
            detail.add_sweep(ring, circle_profile(0.011, 8), closed=True)
            detail.add_sphere(ring[index * 23 % 64].origin, 0.022, segments=16)
        detail.finish(pbr_material(POLISHED_GOLD), root, tile=POLISHED_GOLD.tile)
    else:
        # Polished blue-black stone with three gold orbit lines and gold dots set into the surface.
        shell.finish(pbr_material(BLUE_STONE, box=1.4), root)
        for index, axis in enumerate(tilts):
            ring = ring_frames(centre, MARBLE_RADIUS - 0.001, axis, segments=96)
            detail.add_sweep(ring, circle_profile(0.0045, 8), closed=True)
            for step in (index * 31 % 96, (index * 31 + 40) % 96):
                detail.add_sphere(ring[step].origin, 0.012, segments=16)
        detail.finish(pbr_material(POLISHED_GOLD), root, tile=POLISHED_GOLD.tile)

    blob = Builder("blob_shadow")
    bmesh.ops.create_circle(blob.bm, cap_ends=True, segments=64, radius=1.0)
    shadow = blob.finish(blob_shadow_material(), root)
    shadow.location = Vector((*at, 0.006))
    shadow.scale = (MARBLE_RADIUS * 1.2,) * 3
    shadow.visible_shadow = False


def build_cloud_sea(root: bpy.types.Object) -> None:
    """Build the sea of clouds close below the course as one large volume (the dawn backdrop)."""
    top, depth, half_size = -50.0, 100.0, 30000.0
    box = Builder("cloud_sea")
    box.add_box(Matrix.Translation((0.0, 0.0, top - depth / 2)), (2 * half_size, 2 * half_size, depth))
    box.finish(cloud_material(top, depth), root)


def sky_sun_azimuth(image: bpy.types.Image) -> float:
    """Return the azimuth (degrees, world) of the brightest spot of an equirectangular sky."""
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    luminance = pixels.reshape(height, width, 4)[..., :3] @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    _, columns = np.nonzero(luminance >= np.quantile(luminance, 0.9997))
    u = (float(np.median(columns)) + 0.5) / width
    return (0.5 - u) * 360.0  # Cycles maps a direction to u = 0.5 - atan2(y, x) / 2pi


def hdri_world(sky: HdriSky) -> tuple[bpy.types.World, float]:
    """Return the world of a photographed sky and the azimuth of its sun."""
    world = bpy.data.worlds.new("sky")
    tree = world.node_tree
    tree.nodes.clear()
    image = load_image(TEXTURES / "sky" / f"{sky.file}_2k.hdr", data=False)
    picture = node(tree, "ShaderNodeTexEnvironment", image=image)
    capped = node(tree, "ShaderNodeVectorMath", operation="MINIMUM")
    tree.links.new(picture.outputs["Color"], capped.inputs[0])
    capped.inputs[1].default_value = (SKY_CAP,) * 3
    background = node(tree, "ShaderNodeBackground", Color=capped.outputs["Vector"], Strength=sky.strength)
    tree.links.new(background.outputs["Background"], tree.nodes.new("ShaderNodeOutputWorld").inputs["Surface"])
    return world, sky_sun_azimuth(image)


def physical_world(sky: PhysicalSky) -> bpy.types.World:
    """Return the world of the physical sky: the sky model, a cloud layer far below and (for dusk) faint stars.

    The clouds are noise on a sphere `cloud_drop` km below the camera, found
    from the view direction alone, and fade into the haze with distance.
    """
    world = bpy.data.worlds.new("sky")
    tree = world.node_tree
    tree.nodes.clear()
    view = node(tree, "ShaderNodeTexCoord").outputs["Generated"]
    model = node(
        tree, "ShaderNodeTexSky", sky_type="MULTIPLE_SCATTERING", sun_disc=False, altitude=sky.altitude,
        sun_elevation=math.radians(sky.sky_sun_elevation), sun_rotation=math.radians(90.0 - SUN_AZIMUTH),
    )  # fmt: skip
    air = node(tree, "ShaderNodeVectorMath", operation="SCALE", Scale=sky.strength)
    tree.links.new(model.outputs["Color"], air.inputs[0])
    split = node(tree, "ShaderNodeSeparateXYZ", Vector=view)

    # Where the view ray meets the cloud sphere: t = -b - sqrt(b2 - c), in km.
    earth, drop = 6371.0, sky.cloud_drop
    b = math_node(tree, "MULTIPLY", split.outputs["Z"], earth + drop)
    inside = math_node(tree, "SUBTRACT", math_node(tree, "MULTIPLY", b, b), 2 * earth * drop + drop * drop)
    reach = math_node(tree, "SUBTRACT", math_node(tree, "MULTIPLY", b, -1.0), math_node(tree, "SQRT", math_node(tree, "MAXIMUM", inside, 0.0)))
    ground = node(tree, "ShaderNodeVectorMath", operation="SCALE", Scale=reach)
    tree.links.new(view, ground.inputs[0])
    flat = node(tree, "ShaderNodeVectorMath", operation="MULTIPLY")
    tree.links.new(ground.outputs["Vector"], flat.inputs[0])
    flat.inputs[1].default_value = (1.0, 1.0, 0.0)
    fields = node(tree, "ShaderNodeTexNoise", Vector=flat.outputs["Vector"], Scale=0.035, Detail=9.0, Roughness=0.62)
    puffs = node(tree, "ShaderNodeTexNoise", Vector=flat.outputs["Vector"], Scale=0.4, Detail=6.0, Roughness=0.6)
    both = math_node(tree, "ADD", fields.outputs["Factor"], math_node(tree, "MULTIPLY", puffs.outputs["Factor"], 0.35))
    cover = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=both, From_Min=0.62, From_Max=0.8)
    below = node(tree, "ShaderNodeMapRange", Value=inside, From_Min=0.0, From_Max=2 * earth * drop * 0.02)
    looking_down = math_node(tree, "LESS_THAN", split.outputs["Z"], 0.0)
    haze = math_node(tree, "POWER", 2.718, math_node(tree, "DIVIDE", reach, -28.0 * drop))  # e^(-distance / visibility)
    amount = math_node(tree, "MULTIPLY", math_node(tree, "MULTIPLY", cover.outputs["Result"], below.outputs["Result"]), math_node(tree, "MULTIPLY", looking_down, haze))  # fmt: skip
    clouded = node(tree, "ShaderNodeMix", data_type="RGBA", Factor=math_node(tree, "MULTIPLY", amount, 0.9), A=air.outputs["Vector"], B=(*sky.cloud_color, 1.0))  # fmt: skip
    color = clouded.outputs["Result"]

    if sky.stars > 0.0:
        cells = node(tree, "ShaderNodeTexVoronoi", Vector=view, Scale=170.0)
        point = node(tree, "ShaderNodeMapRange", Value=cells.outputs["Distance"], From_Min=0.0, From_Max=0.045, To_Min=1.0, To_Max=0.0)
        size = math_node(tree, "POWER", node(tree, "ShaderNodeSeparateColor", Color=cells.outputs["Color"]).outputs["Red"], 6.0)
        above = node(tree, "ShaderNodeMapRange", Value=split.outputs["Z"], From_Min=-0.1, From_Max=0.05)
        star = math_node(tree, "MULTIPLY", math_node(tree, "MULTIPLY", point.outputs["Result"], size), math_node(tree, "MULTIPLY", above.outputs["Result"], sky.stars))  # fmt: skip
        lit = node(tree, "ShaderNodeVectorMath", operation="ADD")
        tree.links.new(color, lit.inputs[0])
        tree.links.new(node(tree, "ShaderNodeCombineXYZ", X=star, Y=star, Z=star).outputs["Vector"], lit.inputs[1])
        color = lit.outputs["Vector"]

    background = node(tree, "ShaderNodeBackground", Color=color, Strength=1.0)
    tree.links.new(background.outputs["Background"], tree.nodes.new("ShaderNodeOutputWorld").inputs["Surface"])
    return world


def build_planet(sky: PhysicalSky, to_sun: Vector) -> None:
    """Hang one pale banded planet low over the horizon, half sunk into the haze of the atmosphere.

    The map is NASA's Cassini map of Jupiter (public domain), with its colour
    and contrast turned down. The shader lights the planet from the sun's
    direction by itself, and lets it fade out toward the Earth's horizon.
    """
    distance, half_angle = 20000.0, math.radians(5.0)
    horizon = -math.acos(6371.0 / (6371.0 + sky.altitude / 1000.0))  # the dip of the Earth's edge
    ball = Builder("planet")
    ball.add_sphere(Vector((0.0, 0.0, 0.0)), distance * math.tan(half_angle), segments=96)
    material, tree, output = new_material("planet")
    image = node(tree, "ShaderNodeTexImage", image=load_image(TEXTURES / "planet" / "PIA07782.jpg", data=False))
    pale = node(tree, "ShaderNodeHueSaturation", Saturation=0.3, Value=1.0, Color=image.outputs["Color"])
    soft = node(tree, "ShaderNodeMix", data_type="RGBA", Factor=0.45, A=pale.outputs["Color"], B=(0.5, 0.47, 0.43, 1.0))
    geometry = node(tree, "ShaderNodeNewGeometry")
    facing = node(tree, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
    tree.links.new(geometry.outputs["Normal"], facing.inputs[0])
    facing.inputs[1].default_value = to_sun
    lit = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=facing.outputs["Value"], From_Min=-0.08, From_Max=0.9, To_Min=0.0, To_Max=sky.sun_strength * 0.12)  # fmt: skip
    surface = node(tree, "ShaderNodeEmission", Color=soft.outputs["Result"], Strength=lit.outputs["Result"])
    incoming = node(tree, "ShaderNodeSeparateXYZ", Vector=geometry.outputs["Incoming"])
    rise = math_node(tree, "MULTIPLY", incoming.outputs["Z"], -1.0)  # the sine of the view ray's elevation
    veil = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=rise, From_Min=math.sin(horizon + math.radians(0.6)), From_Max=math.sin(horizon + math.radians(6.5)), To_Min=0.0, To_Max=0.9)  # fmt: skip
    mix = node(tree, "ShaderNodeMixShader", Factor=veil.outputs["Result"])
    tree.links.new(node(tree, "ShaderNodeBsdfTransparent").outputs["BSDF"], mix.inputs[1])
    tree.links.new(surface.outputs["Emission"], mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], output.inputs["Surface"])
    planet = ball.finish(material, None)
    planet.location = direction(SUN_AZIMUTH - 76.0, math.degrees(horizon) + 3.4) * distance
    planet.rotation_euler = (math.radians(14.0), math.radians(-20.0), math.radians(200.0))
    planet.visible_shadow = False
    planet.visible_diffuse = False
    planet.visible_glossy = False


def build_light(sky: Sky) -> tuple[Vector, float]:
    """Set the world and the sun lamp. Return the world direction to the sun and the turn of the scene.

    The scene turns as one piece, so that its sun direction (SUN_AZIMUTH) meets the sky's sun.
    """
    scene = bpy.context.scene
    if isinstance(sky, HdriSky):
        scene.world, azimuth = hdri_world(sky)
    else:
        scene.world, azimuth = physical_world(sky), SUN_AZIMUTH
    to_sun = direction(azimuth, sky.sun_elevation)
    light = bpy.data.lights.new("sun", "SUN")
    light.energy = sky.sun_strength
    light.color = sky.sun_color
    light.angle = math.radians(1.0)
    light.cycles.is_caustics_light = True
    sun = bpy.data.objects.new("sun", light)
    sun.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(sun)
    return to_sun, math.radians(azimuth - SUN_AZIMUTH)


def build_camera(shot: Shot, root: bpy.types.Object) -> None:
    scene = bpy.context.scene
    data = bpy.data.cameras.new("camera")
    data.lens = shot.lens
    data.sensor_width = 36.0
    data.clip_start = 0.05
    data.clip_end = 500000.0
    eye, target = Vector(shot.eye), Vector(shot.target)
    if shot.fstop is not None:
        data.dof.use_dof = True
        data.dof.focus_distance = (Vector((*shot.marble_at, MARBLE_RADIUS)) - eye).length
        data.dof.aperture_fstop = shot.fstop
    camera = bpy.data.objects.new("camera", data)
    camera.location = eye
    camera.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    camera.parent = root
    scene.collection.objects.link(camera)
    scene.camera = camera


def configure_render(samples: int, scale: int, use_gpu: bool) -> None:
    """Set Cycles (OptiX on the GPU, or the CPU), 1920x1080, denoised, AgX, WebP output."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    if use_gpu:
        preferences = bpy.context.preferences.addons["cycles"].preferences
        preferences.compute_device_type = "OPTIX"
        preferences.get_devices()
        for device in preferences.devices:
            device.use = device.type == "OPTIX"
        scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 12
    scene.cycles.glossy_bounces = 8
    scene.cycles.volume_bounces = 12
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = scale
    scene.render.image_settings.file_format = "WEBP"
    scene.render.image_settings.quality = 92
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def render_shot(shot: Shot, out: Path, samples: int, scale: int, use_gpu: bool) -> Path:
    """Build the whole scene for one shot from an empty file and render it."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    look = next(candidate for candidate in LOOKS if candidate.name == shot.look)
    sky: Sky = shot.sky or look.sky
    to_sun, turn = build_light(sky)
    root = bpy.data.objects.new("root", None)
    root.rotation_euler.z = turn
    scene.collection.objects.link(root)
    gems = build_course(look, root, caustics=shot.fstop is not None)
    # Gems glow at a fixed brightness on screen: the emission follows the exposure of the shot.
    build_gems(gems, root, glow=2.0 ** (-1.7 - sky.exposure))
    build_marble(shot.marble, shot.marble_at, root)
    if isinstance(sky, HdriSky):
        build_cloud_sea(root)
    elif sky.planet:
        build_planet(sky, to_sun)
    build_camera(shot, root)
    configure_render(samples, scale, use_gpu)
    scene.view_settings.exposure = sky.exposure
    path = out / f"render-{shot.name}.webp"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", choices=[shot.name for shot in SHOTS], help="shots to render (default: all)")
    parser.add_argument("--out", type=Path, default=REPO / "docs" / "style" / "review")
    parser.add_argument("--samples", type=int, default=384)
    parser.add_argument("--scale", type=int, default=100, help="resolution in percent, for quick previews")
    parser.add_argument("--cpu", action="store_true", help="render on the CPU, for when ComfyUI holds the GPU memory")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    args.out.mkdir(parents=True, exist_ok=True)
    for shot in SHOTS:
        if args.only is None or shot.name in args.only:
            path = render_shot(shot, args.out.resolve(), args.samples, args.scale, not args.cpu)
            print(f"lookdev: wrote {path}")


if __name__ == "__main__":
    main()
