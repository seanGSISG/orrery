"""Harbour: the pieces of the Ascent sky harbour (Ascent zone 3, #33): moored airships, the
floating tops of harbour houses, lattice masts and mooring ropes.

Play pieces (they collide):
- slab() and slope(): a level or a sloped plate of any finish between two points, for decks,
  steps, roofs and gangways. rope(): a narrow beam with level ends, the walk of a mooring rope.
- Ship: an airship. envelope() is its hull of fabric gores, gondola() its car with an open
  deck, promenade() a deck along its back and fins() its tail.
- storey(): the top storey of a floating house, broken off below; gable() a slate roof on it.
- mast(): a lattice mast of iron.

Decoration (no collision): engine(), propeller(), line(), rigging() and lamp().

Every piece takes world positions. A face has a finish: a material of game/materials/ (the
town finishes of kit/town.py and the harbour finishes below). Every ship points west, into
the wind: its nose is at its low x.
"""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

import bmesh
import bpy
from mathutils import Vector

import kit
from kit import town
from kit.scene import Vec3

Point = tuple[float, float]
# The finishes of the harbour, besides those of kit/town.py (whose brass_polished, the brass
# of the lift casings, is also the brass of the big harbour fittings):
# - envelope: the doped cream canvas of an airship; varnish: the varnished timber of a
#   gondola, a propeller or a fin frame; rope: tarred hemp; seam: the lighter cord of the
#   envelope seams.
Finish = str

# An envelope: the share of its length that the round nose takes, and the radius of its tail
# end as a share of its widest radius.
NOSE = 0.3
TAIL = 0.07
# The fabric gores round an envelope, and how far the middle of a gore stands out of the
# polygon of its girders (a share of the radius): gas pressure.
GORES = 24
BULGE = 0.025
# The ring frames along an envelope: their spacing, m, and how far the fabric sags between two
# frames, as a share of the radius. The fabric is taut over each frame, so it creases there.
BAY = 3.2
SAG = 0.02
# A seam of cord runs along each girder and round each ring frame: SEAM m wide, but at
# most SEAM_SHARE of a gore's width where the gores narrow to the nose and the tail.
SEAM = 0.1
SEAM_SHARE = 0.3
# The spacing of the iron posts under a deck on the back of a ship, m.
TRESTLE = 4.8
# A deck plank, a kerb and a rope beam: thickness, kerb height and width, m.
PLANK = 0.3
KERB = 0.3
KERB_WIDTH = 0.16
# The level end of a rope beam, m.
HEEL = 0.9


def material(finish: Finish) -> bpy.types.Material:
    """Returns the material of a finish on surface type default (town.material())."""
    return town.material(finish)  # ty: ignore[invalid-argument-type]


# --- Plates ---------------------------------------------------------------------------------


def slab(
    name: str,
    lo: Vec3,
    hi: Vec3,
    finish: Finish = "wood",
    collide: bool = True,
) -> bpy.types.Object:
    """Adds a box between the corners lo and hi: a deck, a step or a floor whose top is hi's
    height."""
    parts = town.Parts()
    parts.box(lo, hi, finish)  # ty: ignore[invalid-argument-type]
    return parts.add(name, collide)


def slope(
    name: str,
    a: Vec3,
    b: Vec3,
    width: float,
    finish: Finish = "wood",
    depth: float = PLANK,
    collide: bool = True,
) -> bpy.types.Object:
    """Adds a plate whose top face runs straight from the point a to the point b and is
    `width` m wide across that line: a ramp, a roof slope or a gangway. It is `depth` m
    thick, straight down."""
    parts = town.Parts()
    _plate(parts, a, b, width, depth, finish)
    return parts.add(name, collide)


def _plate(
    parts: town.Parts, a: Vec3, b: Vec3, width: float, depth: float, finish: Finish
) -> None:
    """Adds to parts a plate from a to b, as slope() does."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = math.hypot(dx, dy)
    left = Vector((-dy / run, dx / run, 0.0)) * (width / 2)
    top = [Vector(a) - left, Vector(b) - left, Vector(b) + left, Vector(a) + left]
    low = [p - Vector((0.0, 0.0, depth)) for p in top]
    bm = parts.bm
    high_v = [bm.verts.new(p) for p in top]
    low_v = [bm.verts.new(p) for p in low]
    parts.faces([high_v, low_v[::-1], *town._sides(low_v, high_v)], finish)  # ty: ignore[invalid-argument-type]


def rope(
    name: str, a: Vec3, b: Vec3, width: float = 0.6, heel: float = HEEL
) -> list[Vec3]:
    """Adds the walk of a mooring rope from the floor point a to the floor point b: a narrow
    timber beam `width` m wide, level for `heel` m at each end (a level end follows the edge
    it starts from), and the hawser it is lashed to. Returns the route points: the foot and
    the top of its slope."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = math.hypot(dx, dy)
    ux, uy = dx / run, dy / run
    foot = (a[0] + ux * heel, a[1] + uy * heel, a[2])
    top = (b[0] - ux * heel, b[1] - uy * heel, b[2])
    parts = town.Parts()
    for p, q in ((a, foot), (foot, top), (top, b)):
        _plate(parts, p, q, width, 0.22, "wood")
    parts.add(name)
    # The hawser runs under the walk, with an iron lashing every 1.5 m.
    under = town.Parts()
    sink = Vector((0.0, 0.0, 0.32))
    under.bar(Vector(a) - sink, Vector(b) - sink, 0.24, "rope")
    length = math.dist(a, b)
    for k in range(1, int(length / 1.5)):
        t = k / int(length / 1.5)
        p = Vector(a).lerp(Vector(b), t)
        side = Vector((-uy, ux, 0.0)) * (width / 2 + 0.02)
        under.bar(p - side - sink * 1.3, p - side + Vector((0, 0, 0.02)), 0.07, "iron")
        under.bar(p + side - sink * 1.3, p + side + Vector((0, 0, 0.02)), 0.07, "iron")
    under.add(f"{name}_hawser", collide=False)
    return [foot, top]


def kerb(
    name: str,
    path: Sequence[Vec3],
    side: str = "left",
    height: float = KERB,
    closed: bool = False,
) -> bpy.types.Object:
    """Adds a brass kerb `height` m tall on the `side` of the path, seen along it."""
    return kit.wall(
        path,
        height=height,
        width=KERB_WIDTH,
        side=side,  # ty: ignore[invalid-argument-type]
        closed=closed,
        bevel=0.03,
        material="brass",
        name=name,
    )


# --- Airships -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Ship:
    """An airship. Its axis runs along +x from the nose tip `nose` (x, y, z) for `length` m;
    `radius` is its widest radius, NOSE × length behind the nose."""

    name: str
    nose: Vec3
    length: float
    radius: float

    @property
    def tail(self) -> float:
        """The x of the tail end."""
        return self.nose[0] + self.length

    @property
    def widest(self) -> float:
        """The x of the widest ring."""
        return self.nose[0] + NOSE * self.length

    def r(self, x: float) -> float:
        """The radius of the envelope at its girders at x (0 beyond its ends): the shape of the
        hull, less the sag of the fabric between two ring frames. A point at this radius is on
        the fabric or just inside it."""
        along = x - self.nose[0]
        u = along / self.length
        if u < 0.0 or u > 1.0:
            return 0.0
        sag = SAG * abs(math.sin(math.pi * along / BAY))
        return self.radius * _shape(u) * (1.0 - sag)

    def top(self, x: float) -> float:
        """The height of the top of the envelope at x."""
        return self.nose[2] + self.r(x)

    def bottom(self, x: float) -> float:
        """The height of the bottom of the envelope at x."""
        return self.nose[2] - self.r(x)

    def point(self, x: float, angle: float, out: float = 0.0) -> Vector:
        """The point on the envelope at x and `angle` degrees round the axis (0 north, 90 up,
        180 south, 270 down), `out` m outside it."""
        a = math.radians(angle)
        r = self.r(x) + out
        return Vector(
            (x, self.nose[1] + r * math.cos(a), self.nose[2] + r * math.sin(a))
        )


def _shape(u: float) -> float:
    """The radius of an envelope at the share u of its length from the nose, as a share of
    its widest radius: a round nose and a long tail that narrows to TAIL."""
    if u <= NOSE:
        t = (NOSE - u) / NOSE
        return math.sqrt(max(0.0, 1.0 - t * t))
    t = (u - NOSE) / (1.0 - NOSE)
    return 1.0 - (1.0 - TAIL) * t * t


def envelope(ship: Ship) -> bpy.types.Object:
    """Adds the envelope of a ship: fabric gores that stand out between longitudinal girders
    and sag between the ring frames, a seam of cord (finish seam) along each girder and round
    each frame, a brass mooring cone on the nose and a brass cap on the tail. It collides."""
    xs, frames = _stations(ship)
    parts = town.Parts()
    bm = parts.bm
    fabric = parts.index("envelope")  # ty: ignore[invalid-argument-type]
    seam = parts.index("seam")  # ty: ignore[invalid-argument-type]
    gore = math.tau / GORES

    def ring(x: float) -> list[bmesh.types.BMVert]:
        # Three points a gore: the two edges of the seam on its first girder, then its middle.
        r = ship.r(x)
        half = min(SEAM / 2 / max(r, 0.01), SEAM_SHARE * gore / 2)
        middle = r * math.cos(gore / 2) * (1.0 + BULGE)
        verts = []
        for k in range(GORES):
            for angle, reach in (
                (gore * k - half, r),
                (gore * k + half, r),
                (gore * (k + 0.5), middle),
            ):
                verts.append(
                    bm.verts.new(
                        (
                            x,
                            ship.nose[1] + reach * math.cos(angle),
                            ship.nose[2] + reach * math.sin(angle),
                        )
                    )
                )
        return verts

    def face(verts: list[bmesh.types.BMVert], finish: int) -> None:
        made = bm.faces.new(verts)
        made.material_index = finish
        made.smooth = True

    rings = [ring(x) for x in xs]
    around = len(rings[0])
    nose = bm.verts.new(ship.nose)
    tail = bm.verts.new((ship.tail + 0.02, ship.nose[1], ship.nose[2]))
    for k in range(around):
        j = (k + 1) % around
        finish = seam if k % 3 == 0 else fabric
        face([nose, rings[0][j], rings[0][k]], finish)
        face([tail, rings[-1][k], rings[-1][j]], finish)
    for i, (a, b) in enumerate(pairwise(rings)):
        for k in range(around):
            j = (k + 1) % around
            finish = seam if i in frames or k % 3 == 0 else fabric
            face([a[k], a[j], b[j], b[k]], finish)
    # The edges of the seams stay sharp, so each gore and each bay shades round on its own.
    for i, (a, b) in enumerate(pairwise(rings)):
        for k in range(around):
            if k % 3 != 2:
                bm.edges.get((a[k], b[k])).smooth = False
            if i in frames:
                for verts in (a, b):
                    bm.edges.get((verts[k], verts[(k + 1) % around])).smooth = False
    obj = parts.add(ship.name)
    _caps(ship)
    return obj


def _stations(ship: Ship) -> tuple[list[float], set[int]]:
    """Returns the x of the rings of an envelope, and the indices of the rings from which a
    ring frame's seam runs to the next ring. A frame stands every BAY m from the nose tip.
    The rings stand close together round the nose, a quarter BAY apart along the rest and on
    both edges of each frame's seam, and never at the nose tip itself."""
    x0, length = ship.nose[0], ship.length
    frames = [x0 + BAY * j for j in range(1, math.ceil(length / BAY))]
    frames = [x for x in frames if x < ship.tail - BAY / 2]
    marks = [(x + side * SEAM / 2, side < 0) for x in frames for side in (-1, 1)]
    nose = [
        x0 + NOSE * length * (1.0 - math.cos(math.pi / 2 * k / 9)) for k in range(1, 10)
    ]
    quarters = [x0 + BAY * q / 4 for q in range(1, math.ceil(4 * length / BAY))]
    for x in nose + quarters:
        if x < ship.tail - 0.2 and all(abs(x - m) > 0.2 for m, _ in marks):
            marks.append((x, False))
    marks.sort()
    return [x for x, _ in marks], {i for i, (_, starts) in enumerate(marks) if starts}


def _caps(ship: Ship) -> None:
    """Adds the brass mooring cone on the nose and the cap on the tail of a ship."""
    parts = town.Parts()
    x0, y, z = ship.nose
    cone = ship.length * 0.012
    tip = [
        Vector((x0 - 0.35, y, z)),
        *[
            Vector((x0 + cone, y + 0.22 * math.cos(a), z + 0.22 * math.sin(a)))
            for a in (math.tau * k / 12 for k in range(12))
        ],
    ]
    _fan(parts, tip, "brass_polished")
    t = ship.tail
    r = ship.r(t - 0.3) + 0.05
    cap = [
        Vector((t + 0.5, y, z)),
        *[
            Vector((t - 0.3, y + r * math.cos(a), z + r * math.sin(a)))
            for a in (-math.tau * k / 12 for k in range(12))
        ],
    ]
    _fan(parts, cap, "brass_polished")
    parts.add(f"{ship.name}_caps", collide=False)


def _fan(parts: town.Parts, points: list[Vector], finish: Finish) -> None:
    """Adds a closed cone: the first point is the tip, the rest its base ring."""
    bm = parts.bm
    tip = bm.verts.new(points[0])
    base = [bm.verts.new(p) for p in points[1:]]
    loops = [[tip, base[k], base[(k + 1) % len(base)]] for k in range(len(base))]
    parts.faces([*loops, base[::-1]], finish)  # ty: ignore[invalid-argument-type]


def promenade(
    ship: Ship,
    profile: Sequence[Point],
    width: float,
    kerbs: Sequence[tuple[str, float, float]] = (),
    name: str = "",
) -> bpy.types.Object:
    """Adds a timber deck along the back of a ship, on iron posts: its top face follows
    the profile of (x, height) points along the axis and is `width` m wide. kerbs: the brass
    kerbs along its edges, each (side n or s, x0, x1). Keep the profile above the envelope."""
    name = name or f"{ship.name}_deck"
    y = ship.nose[1]
    half = width / 2
    parts = town.Parts()
    for (xa, za), (xb, zb) in pairwise(profile):
        _plate(parts, (xa, y, za), (xb, y, zb), width, PLANK, "wood")
    obj = parts.add(name)
    for i, (side, x0, x1) in enumerate(kerbs):
        edge = y + (half if side == "n" else -half)
        path = [(x, edge, _height(profile, x)) for x in _cuts(profile, x0, x1)]
        kerb(f"{name}_kerb_{i}", path, side="right" if side == "n" else "left")
    # Trestles: an iron post from under each edge of the deck down to the envelope every
    # TRESTLE m. Where the envelope is narrower than the deck, the posts stand further in, so
    # that each one ends in the fabric; where it is much narrower, the deck has no post.
    legs = town.Parts()
    x_first, x_last = profile[0][0], profile[-1][0]
    count = max(1, round((x_last - x_first) / TRESTLE))
    for k in range(count + 1):
        x = x_first + (x_last - x_first) * k / count
        r = ship.r(x)
        if r < half * 0.6:
            continue
        reach = min(half - 0.25, 0.85 * r)
        foot = ship.nose[2] + math.sqrt(r * r - reach * reach) - 0.1
        deck = _height(profile, x) - PLANK
        if deck - foot < 0.25:
            continue
        for side in (-1.0, 1.0):
            y_leg = y + side * reach
            legs.bar(Vector((x, y_leg, deck)), Vector((x, y_leg, foot)), 0.1, "iron")
    if legs.bm.faces:
        legs.add(f"{name}_trestles", collide=False)
    else:
        legs.bm.free()
    return obj


def _height(profile: Sequence[Point], x: float) -> float:
    """The height of a profile of (x, height) points at x, straight between the points."""
    for (xa, za), (xb, zb) in pairwise(profile):
        if xa <= x <= xb or xb <= x <= xa:
            t = 0.0 if xb == xa else (x - xa) / (xb - xa)
            return za + (zb - za) * t
    return profile[0][1] if x < profile[0][0] else profile[-1][1]


def _cuts(profile: Sequence[Point], x0: float, x1: float) -> list[float]:
    """The x from x0 to x1 with every profile point between them: the corners of a kerb."""
    inner = [x for x, _ in profile if x0 < x < x1]
    return [x0, *inner, x1]


def gondola(
    ship: Ship,
    x0: float,
    x1: float,
    deck: float,
    width: float,
    depth: float = 2.4,
    kerbs: Sequence[tuple[str, float, float]] = (),
    windows: bool = True,
) -> bpy.types.Object:
    """Adds the gondola of a ship from x0 to x1 under its axis: a cabin of varnished timber
    whose roof is an open deck at the height `deck`, `width` m wide, with rounded ends and a
    keel `depth` m below the deck; a row of windows on each side; iron struts from its sides to
    the envelope. kerbs as for promenade(). The deck and the hull collide."""
    name = f"{ship.name}_gondola"
    y = ship.nose[1]
    half = width / 2
    deck_parts = town.Parts()
    deck_parts.box((x0, y - half, deck - PLANK), (x1, y + half, deck), "wood")
    obj = deck_parts.add(f"{name}_deck")

    def rounding(x: float) -> float:
        """The share of the full width and depth that the hull has at x: 1 in the middle,
        0.55 at the ends, where the hull rounds off."""
        t = (x - x0) / (x1 - x0)
        return 0.55 + 0.45 * (1.0 - (2.0 * t - 1.0) ** 6)

    # The hull: sections across the gondola, square at the top and narrowing to the keel;
    # the ends round off in plan.
    sections = []
    steps = 16
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i / steps
        w = half * rounding(x)
        keel = depth * rounding(x)
        top = deck - PLANK
        sections.append(
            [
                Vector((x, y - w, top)),
                Vector((x, y - w * 0.96, top - keel * 0.6)),
                Vector((x, y - w * 0.55, top - keel)),
                Vector((x, y + w * 0.55, top - keel)),
                Vector((x, y + w * 0.96, top - keel * 0.6)),
                Vector((x, y + w, top)),
            ]
        )
    town.Parts(town._loft(sections), "varnish").add(f"{name}_hull")  # ty: ignore[invalid-argument-type]
    for i, (side, ka, kb) in enumerate(kerbs):
        edge = y + (half if side == "n" else -half)
        kerb(
            f"{name}_kerb_{i}",
            [(ka, edge, deck), (kb, edge, deck)],
            side="right" if side == "n" else "left",
        )
    dress = town.Parts()
    if windows:
        # The windows sit on the middle 70 % of the sides, where the hull is nearly straight,
        # each one on the hull at its x.
        span = (x1 - x0) * 0.7
        count = max(1, int(span // 1.3))
        for side in (-1.0, 1.0):
            for k in range(count):
                x = (x0 + x1 - span) / 2 + span * (k + 0.5) / count
                yy = y + side * (half * rounding(x) * 0.985 + 0.01)
                lo, hi = deck - PLANK - 0.85, deck - PLANK - 0.25
                _window(dress, x, yy, side, lo, hi)
        # A brass band under the deck edge.
        for side in (-1.0, 1.0):
            yy = y + side * half
            dress.box(
                (x0 + 0.6, min(yy, yy + side * 0.04), deck - PLANK - 0.12),
                (x1 - 0.6, max(yy, yy + side * 0.04), deck - PLANK),
                "brass_polished",
            )
    # Struts from the hull sides up to the envelope, outside the deck.
    for x in (x0 + 1.2, (x0 + x1) / 2, x1 - 1.2):
        r = ship.r(x)
        if r <= 0.0:
            continue
        for side in (-1.0, 1.0):
            low = Vector((x, y + side * (half + 0.08), deck - PLANK - 0.4))
            # The strut meets the envelope 40 degrees round from its bottom, on its side.
            high = ship.point(x, 270.0 + side * 40.0)
            dress.bar(low, high, 0.09, "iron")
    dress.add(f"{name}_dress", collide=False)
    return obj


def _window(
    parts: town.Parts, x: float, y: float, side: float, lo: float, hi: float
) -> None:
    """Adds a small cabin window on a gondola side facing `side` (+1 north, -1 south): a dark
    room behind glass in a brass frame."""
    w = 0.32
    out = Vector((0.0, side, 0.0))
    for finish, o in (("interior", 0.0), ("glass", 0.015)):
        yy = y + side * o
        parts.flat(
            [(x - w, yy, lo), (x + w, yy, lo), (x + w, yy, hi), (x - w, yy, hi)],
            out,
            finish,  # ty: ignore[invalid-argument-type]
        )
    f = 0.05
    for (ax, az), (bx, bz) in (
        ((x - w - f, lo - f), (x + w + f, lo)),
        ((x - w - f, hi), (x + w + f, hi + f)),
        ((x - w - f, lo), (x - w, hi)),
        ((x + w, lo), (x + w + f, hi)),
    ):
        parts.box(
            (ax, min(y, y + side * 0.05), az),
            (bx, max(y, y + side * 0.05), bz),
            "brass_polished",
        )


def fins(
    ship: Ship,
    root: float,
    span: float,
    floors: bool = False,
    angles: Sequence[float] = (0.0, 90.0, 180.0, 270.0),
) -> float:
    """Adds the tail fins of a ship at the given angles (Ship.point()): flat plates of canvas
    on a varnished frame, from `root` m in front of the tail to past it, reaching `span` m out
    of the envelope. floors: the level fins (angles 0 and 180) have a flat top that the marble
    rolls on. Returns the height of that top."""
    thickness = 0.24
    xa = ship.tail - root
    xb = ship.tail + 0.6
    floor = ship.nose[2] + thickness / 2
    for angle in angles:
        level = angle % 180.0 == 0.0
        name = f"{ship.name}_fin_{int(angle)}"
        a = math.radians(angle)
        out = Vector((0.0, math.cos(a), math.sin(a)))
        across = Vector((0.0, -math.sin(a), math.cos(a))) * (thickness / 2)
        base = Vector((0.0, ship.nose[1], ship.nose[2]))
        lead_root = base + Vector((xa, 0, 0)) + out * max(ship.r(xa) - 0.2, 0.0)
        trail_root = base + Vector((xb, 0, 0))
        lead_tip = base + Vector((xa + root * 0.45, 0, 0)) + out * (ship.r(xa) + span)
        trail_tip = base + Vector((xb, 0, 0)) + out * (ship.r(xa) + span)
        outline = [lead_root, trail_root, trail_tip, lead_tip]
        parts = town.Parts()
        bm = parts.bm
        top = [bm.verts.new(p + across) for p in outline]
        low = [bm.verts.new(p - across) for p in outline]
        parts.faces([top, low[::-1], *town._sides(low, top)], "envelope")  # ty: ignore[invalid-argument-type]
        # A varnished frame round the plate.
        # On a fin that the marble rolls on, the frame is flush with the plate.
        frame = thickness if level and floors else thickness + 0.06
        for p, q in pairwise([*outline[1:], outline[0]]):
            parts.bar(p, q, frame, "varnish")  # ty: ignore[invalid-argument-type]
        parts.add(name, collide=floors or not level)
    return floor


def engine(name: str, at: Vec3, length: float = 2.2, radius: float = 0.45) -> None:
    """Adds an engine car pointing west from `at` (its middle): a varnished nacelle with a
    brass nose and a four-bladed propeller behind it, east. It does not collide."""
    x, y, z = at
    parts = town.Parts()
    rings = []
    for k in range(9):
        t = k / 8
        r = radius * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.6
        xx = x - length / 2 + length * t
        rings.append(
            [Vector((xx, y + r * math.cos(a), z + r * math.sin(a))) for a in _ring(12)]
        )
    town.Parts(town._loft(rings), "varnish").add(f"{name}_car", collide=False)  # ty: ignore[invalid-argument-type]
    _fan(
        parts,
        [Vector((x - length / 2 - 0.25, y, z))]
        + [
            Vector(
                (x - length / 2 + 0.05, y + 0.18 * math.cos(a), z + 0.18 * math.sin(a))
            )
            for a in _ring(12)
        ],
        "brass_polished",
    )
    parts.add(f"{name}_spinner", collide=False)
    propeller(f"{name}_propeller", (x + length / 2 + 0.12, y, z), radius * 3.2)


def propeller(
    name: str, at: Vec3, radius: float, blades: int = 4, axis: Literal["x", "z"] = "x"
) -> None:
    """Adds a still propeller of varnished timber with a brass hub, its shaft along `axis`:
    x for the propeller of an engine, z for one on an upright axle."""
    middle = Vector(at)
    shaft = Vector((1.0, 0.0, 0.0)) if axis == "x" else Vector((0.0, 0.0, 1.0))
    # Two directions across the shaft; (u, v, shaft) is right-handed, so the faces keep their
    # winding.
    u = Vector((0.0, 1.0, 0.0)) if axis == "x" else Vector((1.0, 0.0, 0.0))
    v = shaft.cross(u)
    parts = town.Parts()
    hub = [
        [
            middle + shaft * dx + u * 0.16 * math.cos(a) + v * 0.16 * math.sin(a)
            for a in _ring(10)
        ]
        for dx in (-0.12, 0.12)
    ]
    parts.bm.free()
    parts = town.Parts(town._loft(hub), "brass_polished")
    timber = parts.index("varnish")  # ty: ignore[invalid-argument-type]
    for b in range(blades):
        a0 = math.tau * b / blades + 0.3
        sections = []
        for k in range(6):
            t = k / 5
            r = 0.14 + (radius - 0.14) * t
            chord = 0.22 * (1.0 - 0.6 * t) + 0.04
            twist = 0.9 - 0.6 * t
            a = a0
            centre = middle + u * r * math.cos(a) + v * r * math.sin(a)
            along = -u * math.sin(a) + v * math.cos(a)
            pitch = shaft
            lead = along * math.cos(twist) + pitch * math.sin(twist)
            thick = pitch * math.cos(twist) * 0.04 - along * math.sin(twist) * 0.04
            sections.append(
                [
                    centre + lead * chord,
                    centre + thick,
                    centre - lead * chord,
                    centre - thick,
                ]
            )
        blade = town._loft(sections)
        for face in blade.faces:
            face.material_index = timber
        tmp = bpy.data.meshes.new("tmp_blade")
        blade.to_mesh(tmp)
        blade.free()
        parts.bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    parts.add(name, collide=False)


def _ring(count: int) -> list[float]:
    """Returns count angles evenly round a circle, radians."""
    return [math.tau * k / count for k in range(count)]


def line(
    parts: town.Parts, a: Vec3, b: Vec3, width: float = 0.07, finish: Finish = "rope"
) -> None:
    """Adds a straight rope or cable from a to b to parts. Keep it 0.07 m or wider: a thinner
    line breaks into dots at range."""
    parts.bar(Vector(a), Vector(b), width, finish)  # ty: ignore[invalid-argument-type]


# --- Floating houses ------------------------------------------------------------------------


def storey(
    name: str,
    lo: Point,
    hi: Point,
    floor: float,
    eave: float,
    seed: int = 0,
    windows: str = "nesw",
    cornice: bool = True,
) -> bpy.types.Object:
    """Adds the top storey of a harbour house between the plan corners lo and hi, broken off
    below: walls of coursed stone from the height `floor` up to `eave`, with windows on the
    sides in `windows` and a cornice, and under the floor the stubs of the walls of the storey
    below, broken off at uneven heights. The walls collide; the stubs do not."""
    (x0, y0), (x1, y1) = lo, hi
    parts = town.Parts()
    parts.box((x0, y0, floor), (x1, y1, eave), "wall")
    sides = town.faces(lo, hi)
    shown = {key: face for key, face in sides.items() if key in windows}
    if cornice:
        town.band(parts, sides, sides, eave - 0.5, eave - 0.38, 0.08)
        town.band(parts, sides, sides, eave - 0.38, eave - 0.25, 0.18)
    town.band(parts, sides, sides, floor - 0.02, floor + 0.2, 0.1)
    for face in shown.values():
        if eave - floor > 2.4:
            town.windows(parts, face, eave - 0.55, bottom=floor - 0.8)
    obj = parts.add(name)
    # The stubs: the break runs up and down along each wall in a jagged line.
    broken = town.Parts()
    rng = random.Random(seed)
    for face in sides.values():
        s, drop = 0.0, rng.uniform(0.3, 2.1)
        while s < face.length - 0.05:
            step = min(face.length - s, rng.uniform(0.7, 1.6))
            after = rng.uniform(0.3, 2.1)
            corners = [face.at(s, 0.0), face.at(s + step, 0.0)]
            corners += [face.at(s + step, -0.5), face.at(s, -0.5)]
            drops = [drop, after, after * 0.8, drop * 0.8]
            bm = broken.bm
            low = [
                bm.verts.new((*c, floor - d))
                for c, d in zip(corners, drops, strict=True)
            ]
            high = [bm.verts.new((*c, floor)) for c in corners]
            broken.faces([low[::-1], high, *town._sides(low, high)], "wall")
            s, drop = s + step, after
    # The broken floor: a slab of rough stone under the storey.
    broken.box(
        (x0 + 0.5, y0 + 0.5, floor - 0.45), (x1 - 0.5, y1 - 0.5, floor), "dressed"
    )
    broken.add(f"{name}_broken", collide=False)
    return obj


def parapet(
    name: str,
    lo: Point,
    hi: Point,
    top: float,
    gaps: Sequence[tuple[str, float, float]] = (),
) -> None:
    """Adds a stone parapet 0.9 m tall round a flat roof between lo and hi, whose floor is at
    `top`, with gaps: (side s, e, n or w, from, to) in m along that side as faces() runs it."""
    sides = town.faces(lo, hi)
    for key, face in sides.items():
        cuts = sorted((a, b) for s, a, b in gaps if s == key)
        spans = []
        start = 0.0
        for a, b in cuts:
            if a > start:
                spans.append((start, a))
            start = max(start, b)
        if start < face.length:
            spans.append((start, face.length))
        for i, (a, b) in enumerate(spans):
            if b - a < 0.2:
                continue
            p, q = face.at(a), face.at(b)
            kit.wall(
                [(*p, top), (*q, top)],
                height=0.9,
                width=0.35,
                side="right",
                bevel=0.04,
                name=f"{name}_{key}_{i}",
            )


def gable(
    name: str,
    lo: Point,
    hi: Point,
    eave: float,
    ridge: float,
    along: str = "x",
    collide: bool = True,
) -> bpy.types.Object:
    """Adds a slate gable roof on a storey between lo and hi: two slopes from the eaves at
    `eave` up to the ridge at `ridge`, the ridge along `along`, with stone gable ends and an
    iron ridge."""
    (x0, y0), (x1, y1) = lo, hi
    parts = town.Parts()
    over = 0.3
    if along == "x":
        mid, ends, low, high = (y0 + y1) / 2, (x0, x1), y0, y1
    else:
        mid, ends, low, high = (x0 + x1) / 2, (y0, y1), x0, x1
    slate = "slate" if along == "x" else "slate_turned"
    parts.prism([(low, eave), (high, eave), (mid, ridge - 0.3)], *ends, along, "wall")  # ty: ignore[invalid-argument-type]
    parts.prism(
        [(low - over, eave - 0.2), (high + over, eave - 0.2), (mid, ridge)],
        ends[0] - 0.15,
        ends[1] + 0.15,
        along,  # ty: ignore[invalid-argument-type]
        slate,  # ty: ignore[invalid-argument-type]
    )
    cap = [(mid - 0.12, ridge - 0.1), (mid + 0.12, ridge - 0.1)]
    cap += [(mid + 0.12, ridge + 0.08), (mid - 0.12, ridge + 0.08)]
    parts.prism(cap, ends[0] - 0.2, ends[1] + 0.2, along, "iron")  # ty: ignore[invalid-argument-type]
    return parts.add(name, collide)


def chimneys(name: str, spots: Sequence[Vec3], height: float = 1.6) -> None:
    """Adds a brick-red chimney stack with two pots at each foot point of spots. They
    collide."""
    for i, (x, y, z) in enumerate(spots):
        town.chimney(f"{name}_{i}", (x, y, z), 0.9, height)


# --- Masts ----------------------------------------------------------------------------------


def mast(
    name: str,
    foot: Vec3,
    top: float,
    width: float = 1.6,
    head: float = 0.9,
    bay: float = 2.4,
    hanging: bool = False,
) -> None:
    """Adds a lattice mast of iron from the foot point up to the height `top`: four corner
    posts that taper from `width` to `head` m apart, with a cross brace in each bay of about
    `bay` m. hanging: the mast hangs in the air, so a frame closes its foot and its posts meet
    in a point `width` m below it. It collides."""
    x, y, z = foot
    parts = town.Parts()
    count = max(1, round((top - z) / bay))

    def corner(k: int, h: float) -> Vector:
        t = (h - z) / (top - z)
        half = (width + (head - width) * t) / 2
        sx = -1.0 if k in (0, 3) else 1.0
        sy = -1.0 if k in (0, 1) else 1.0
        return Vector((x + sx * half, y + sy * half, h))

    for k in range(4):
        parts.bar(corner(k, z), corner(k, top), 0.12, "iron")
        if hanging:
            parts.bar(corner(k, z), corner((k + 1) % 4, z), 0.07, "iron")
            parts.bar(corner(k, z), Vector((x, y, z - width)), 0.12, "iron")
    for i in range(count):
        h0 = z + (top - z) * i / count
        h1 = z + (top - z) * (i + 1) / count
        for k in range(4):
            j = (k + 1) % 4
            parts.bar(corner(k, h0), corner(j, h1), 0.07, "iron")
            parts.bar(corner(j, h0), corner(k, h1), 0.07, "iron")
            parts.bar(corner(k, h1), corner(j, h1), 0.07, "iron")
    parts.add(name)


def lamp(name: str, at: Vec3) -> None:
    """Adds a harbour lamp on a short iron post standing at `at`. It does not collide."""
    kit.prop("lamp_post", at=at)
