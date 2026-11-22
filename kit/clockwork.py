"""Clockwork: the pieces of the broken clock tower (Ascent zone 2, #32).

Play pieces (they collide):
- fragment(): a floating piece of broken masonry. Its top is a stone floor with a chamfered,
  dressed coping round the edge; under it hangs a broken mass of coursed ashlar.
- disc(): a round floor of any finish, with a rim band, for the barrel lid, the bob and the cap.

Decoration (no collision): numeral() lays the strokes of a Roman numeral, and rim() runs a
round band of any finish under a floor's edge.

place() moves objects built at the origin into their pose: build a tilted piece flat round
(0, 0, 0), then place it, as the clock face is built.

Every piece takes world positions and a town.Finish, or a kit material of kit/surfaces.py.
"""

import math
import random
from collections.abc import Iterable, Sequence

import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

import kit
from kit import town
from kit.outlines import turned

Point = tuple[float, float]
Vec3 = tuple[float, float, float]

# A fragment: the chamfer on its top edge, and the depth of its dressed coping, m.
CHAMFER = 0.05
COPING = 0.45
# The broken mass under a fragment: its points are this far apart round the edge, m.
BREAK_STEP = 1.1
# The mass starts this far inside the coping, m.
BREAK_INSET = 0.12


def fragment(
    name: str,
    outline: Sequence[Point],
    top: float,
    under: float = 2.5,
    floor: town.Finish = "limestone",
    coping: float = COPING,
    seed: int | None = None,
) -> bpy.types.Object:
    """Adds a floating piece of broken masonry whose flat top, of `floor` finish, has the
    plan `outline` at the height `top`. A dressed coping `coping` m deep runs round the edge,
    with a chamfer on top; under it a mass of coursed ashlar breaks off `under` m lower in a
    jagged point. The outline is convex or nearly so. seed: the shape of the break (the name
    when None). It collides."""
    rng = random.Random(seed if seed is not None else name)
    loop = _resample(turned(list(outline)), BREAK_STEP)
    c = _centroid(loop)
    parts = town.Parts()
    bm = parts.bm
    level = top - coping

    def ring(points: Sequence[Point], z: float | Sequence[float]) -> list:
        heights = [z] * len(points) if isinstance(z, float) else list(z)
        return [
            bm.verts.new((x, y, h)) for (x, y), h in zip(points, heights, strict=True)
        ]

    deck = ring(_inset(loop, CHAMFER), top)
    edge = ring(loop, top - CHAMFER)
    foot = ring(loop, level)
    inner = _inset(loop, BREAK_INSET)
    shelf = ring(inner, level)
    # Two jagged rings and a point: the break.
    near = [_toward(p, c, rng.uniform(0.05, 0.25)) for p in inner]
    near_z = [level - under * rng.uniform(0.15, 0.45) for _ in near]
    far = [_toward(p, c, rng.uniform(0.35, 0.6)) for p in inner]
    far_z = [level - under * rng.uniform(0.55, 0.9) for _ in far]
    near_v = ring(near, near_z)
    far_v = ring(far, far_z)
    tip = bm.verts.new((c[0], c[1], level - under))
    _cap(parts, deck, loop, floor, up=True)
    parts.faces(_bands(deck, edge) + _bands(edge, foot), "dressed")
    parts.faces(_bands(foot, shelf), "dressed")
    parts.faces(_bands(shelf, near_v) + _bands(near_v, far_v), "wall")
    n = len(far_v)
    parts.faces([[far_v[i], far_v[(i + 1) % n], tip] for i in range(n)], "wall")
    return parts.add(name)


def disc(
    name: str,
    at: Vec3,
    radius: float,
    depth: float = 0.6,
    finish: str = "polished_brass",
    clip: tuple[Point, Point] | None = None,
    segments: int = 96,
) -> bpy.types.Object:
    """Adds a round floor of `finish` (a kit material) whose top is at the height of `at`,
    `depth` m deep. clip: a point and a direction in plan; the disc keeps only the part to
    the left of that line, so a straight edge can meet a ramp's end flush. It collides."""
    outline = kit.arc((at[0], at[1]), radius, 0.0, 360.0, segments)
    if clip is not None:
        outline = _clip(outline, *clip)
    return kit.deck(outline, at[2], depth, name=name, material=finish)


def rim(
    name: str,
    at: Vec3,
    radius: float,
    height: float,
    width: float = 0.25,
    finish: str = "polished_brass",
    span: tuple[float, float] = (0.0, 360.0),
) -> bpy.types.Object:
    """Adds a band of `finish` round the circle of `radius` about `at`, from the height of
    `at` down `height` m, `width` m thick outward, over the angles of `span` (degrees). It
    dresses the edge of a disc() and does not collide."""
    full = span[1] - span[0] >= 360.0
    points = kit.arc(
        (at[0], at[1]), radius, *span, max(8, int((span[1] - span[0]) / 4))
    )
    path = [(x, y, at[2] - height) for x, y in points]
    return kit.wall(
        path,
        height=height,
        width=width,
        side="right",
        closed=full,
        name=name,
        material=finish,
        collide=False,
    )


def numeral(
    name: str, text: str, at: Vec3, height: float, yaw: float, material: str = "gold"
) -> bpy.types.Object:
    """Lays the Roman numeral `text` (I, V and X) flat on a floor whose top is at the height
    of `at`, centred on `at`, `height` m tall, its foot toward the yaw angle + 180 degrees
    (yaw 0: it reads upright seen from -y). Each stroke is an inlay of `material` with two
    serifs on each I. It does not collide."""
    stroke = 0.12 * height
    cell = 0.62 * height
    gap = 0.16 * height
    width = len(text) * cell + (len(text) - 1) * gap
    a = math.radians(yaw)
    turn = Matrix.Rotation(a, 3, "Z")
    shapes: list[list[Point]] = []
    for i, letter in enumerate(text):
        mid = -width / 2 + cell / 2 + i * (cell + gap)
        if letter == "I":
            lines = [((mid, -height / 2), (mid, height / 2))]
        elif letter == "V":
            lines = [
                ((mid, -height / 2), (mid - 0.42 * cell, height / 2)),
                ((mid, -height / 2), (mid + 0.42 * cell, height / 2)),
            ]
        elif letter == "X":
            lines = [
                ((mid - 0.42 * cell, -height / 2), (mid + 0.42 * cell, height / 2)),
                ((mid + 0.42 * cell, -height / 2), (mid - 0.42 * cell, height / 2)),
            ]
        else:
            raise ValueError(f"clockwork.numeral: no stroke for {letter!r}")
        for foot, head in lines:
            shapes.append(_bar(foot, head, stroke))
        if letter == "I":
            for y in (-height / 2, height / 2):
                shapes.append(
                    _bar((mid - 0.28 * cell, y), (mid + 0.28 * cell, y), stroke * 0.7)
                )
    objects = []
    for k, shape in enumerate(shapes):
        world = [turn @ Vector((x, y, 0.0)) for x, y in shape]
        outline = [(at[0] + v.x, at[1] + v.y) for v in world]
        objects.append(
            kit.inlay(outline, at[2], name=f"{name}_{k:02d}", material=material)
        )
    for obj in objects[1:]:
        obj.parent = objects[0]
    return objects[0]


def union(
    polygon: Sequence[Point], centre: Point, radius: float, segments: int = 96
) -> list[Point]:
    """Returns the outline of a convex polygon joined with the circle of `radius` round
    centre. The two must overlap, and the polygon's middle must lie in the circle or the
    circle's middle in the polygon, so that the outline is star-shaped round that point."""
    poly = turned(list(polygon))
    circle = kit.arc(centre, radius, 0.0, 360.0, segments)
    inside_poly = _inside(poly)
    points = [p for p in poly if math.dist(p, centre) > radius]
    points += [p for p in circle if not inside_poly(p)]
    n = len(poly)
    for i in range(n):
        points += _crossings(poly[i], poly[(i + 1) % n], centre, radius)
    middle = _centroid(poly)
    hub = middle if math.dist(middle, centre) < radius else centre
    return sorted(points, key=lambda p: math.atan2(p[1] - hub[1], p[0] - hub[0]))


def place(objects: Iterable[bpy.types.Object], matrix: Matrix) -> None:
    """Moves each object (built round the origin) by matrix: its world matrix becomes
    matrix @ its world matrix. Children move with their parents, so pass only the roots."""
    for obj in objects:
        obj.matrix_world = matrix @ obj.matrix_world


def frame(at: Vec3, yaw: float, tilt: float) -> Matrix:
    """Returns the pose of a piece built flat round the origin: turned `yaw` degrees round z,
    then tipped `tilt` degrees round its own x axis (its +y side rises), at `at`."""
    return (
        Matrix.Translation(Vector(at))
        @ Matrix.Rotation(math.radians(yaw), 4, "Z")
        @ Matrix.Rotation(math.radians(tilt), 4, "X")
    )


def roots(before: set[str]) -> list[bpy.types.Object]:
    """Returns the objects added since `before` (a set of object names) that have no
    parent: the pieces to place()."""
    return [
        obj for obj in bpy.data.objects if obj.name not in before and obj.parent is None
    ]


def names() -> set[str]:
    """Returns the names of the objects in the level now, for roots()."""
    return {obj.name for obj in bpy.data.objects}


# --- Helpers ------------------------------------------------------------------------------


def _bar(a: Point, b: Point, width: float) -> list[Point]:
    """Returns the outline of a bar `width` m wide from the point a to b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    return [
        (a[0] + nx, a[1] + ny),
        (a[0] - nx, a[1] - ny),
        (b[0] - nx, b[1] - ny),
        (b[0] + nx, b[1] + ny),
    ]


def _resample(loop: Sequence[Point], step: float) -> list[Point]:
    """Returns the closed loop with points added on each side, at most `step` m apart."""
    out: list[Point] = []
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        count = max(1, math.ceil(math.dist(a, b) / step))
        out += [
            (a[0] + (b[0] - a[0]) * k / count, a[1] + (b[1] - a[1]) * k / count)
            for k in range(count)
        ]
    return out


def _centroid(loop: Sequence[Point]) -> Point:
    """Returns the middle of the area of a closed loop."""
    area = cx = cy = 0.0
    n = len(loop)
    for i in range(n):
        (x0, y0), (x1, y1) = loop[i], loop[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    return (cx / (3 * area), cy / (3 * area))


def _toward(p: Point, c: Point, share: float) -> Point:
    """Returns the point `share` of the way from p to c."""
    return (p[0] + (c[0] - p[0]) * share, p[1] + (c[1] - p[1]) * share)


def _inset(loop: Sequence[Point], d: float) -> list[Point]:
    """Returns the counter-clockwise loop moved `d` m inward, with mitred corners."""
    n = len(loop)
    out: list[Point] = []
    for i in range(n):
        p0, p1, p2 = loop[i - 1], loop[i], loop[(i + 1) % n]
        e0 = Vector((p1[0] - p0[0], p1[1] - p0[1])).normalized()
        e1 = Vector((p2[0] - p1[0], p2[1] - p1[1])).normalized()
        n0, n1 = Vector((-e0.y, e0.x)), Vector((-e1.y, e1.x))
        bisect = n0 + n1
        if bisect.length < 1e-6:
            bisect = n0
        bisect.normalize()
        scale = d / max(0.2, bisect.dot(n0))
        out.append((p1[0] + bisect.x * scale, p1[1] + bisect.y * scale))
    return out


def _bands(upper: Sequence, lower: Sequence) -> list[list]:
    """Returns the quads between two rings of verts of the same count."""
    n = len(upper)
    return [
        [upper[i], lower[i], lower[(i + 1) % n], upper[(i + 1) % n]] for i in range(n)
    ]


def _cap(
    parts: town.Parts,
    verts: Sequence,
    loop: Sequence[Point],
    finish: town.Finish,
    up: bool,
) -> None:
    """Fills a ring of verts (on the plan loop) with triangles of finish that face up or down."""
    index = parts.index(finish)
    for a, b, c in tessellate_polygon([[(x, y, 0.0) for x, y in loop]]):
        (ax, ay), (bx, by), (cx, cy) = loop[a], loop[b], loop[c]
        counter = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay) > 0.0
        tri = (
            (verts[a], verts[b], verts[c])
            if counter == up
            else (verts[a], verts[c], verts[b])
        )
        parts.bm.faces.new(tri).material_index = index


def _inside(poly: Sequence[Point]):
    """Returns a test for points inside the counter-clockwise convex polygon."""

    def test(p: Point) -> bool:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < 0.0:
                return False
        return True

    return test


def _crossings(a: Point, b: Point, centre: Point, radius: float) -> list[Point]:
    """Returns the points where the segment from a to b crosses the circle."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    fx, fy = a[0] - centre[0], a[1] - centre[1]
    qa = dx * dx + dy * dy
    qb = 2.0 * (fx * dx + fy * dy)
    qc = fx * fx + fy * fy - radius * radius
    disc = qb * qb - 4.0 * qa * qc
    if disc <= 0.0:
        return []
    root = math.sqrt(disc)
    ts = [(-qb - root) / (2.0 * qa), (-qb + root) / (2.0 * qa)]
    return [(a[0] + dx * t, a[1] + dy * t) for t in ts if 0.0 < t < 1.0]


def _clip(outline: Sequence[Point], at: Point, along: Point) -> list[Point]:
    """Returns the part of a closed outline to the left of the line through `at` along
    `along` (one pass of Sutherland-Hodgman)."""

    def side(p: Point) -> float:
        return along[0] * (p[1] - at[1]) - along[1] * (p[0] - at[0])

    out: list[Point] = []
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        sa, sb = side(a), side(b)
        if sa >= 0.0:
            out.append(a)
        if (sa >= 0.0) != (sb >= 0.0):
            t = sa / (sa - sb)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out
