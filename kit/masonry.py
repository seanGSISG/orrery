"""Masonry: the pieces of an open play space. A level script draws its floors as outlines
(kit/outlines.py) and stands walls, kerbs and pillars on them.

- deck(): a floor of any outline. dish(): a round bowl that fills a round hole in a deck.
- wall(): a wall or a kerb along a path. arch(): a wall panel with a doorway. grille(): a
  row of bars that fills a doorway, too close for the marble and open to the light.
- teeth(): a row of gear teeth along the top of an outer wall. They do not collide.
- lathe() and pillar(): round pieces. They collide.
- hoop(), ball() and gear(): a round ring, a ball and a gear wheel against a wall. They do
  not collide.
- inlay(): a flat metal figure set into a floor. It does not collide.

A deck, a dish, a wall and an inlay take world positions and keep their origin at the world
origin, so the paving of the kit material runs on from one piece to the next. An arch, a
gear and a round piece have their origin at `at`. Each piece is `material` on the surface type
`surface`, as a track piece is (kit/pieces.py).
"""

import math
from collections.abc import Sequence
from itertools import pairwise
from typing import Literal

import bmesh
import bpy
from mathutils import Matrix
from mathutils.geometry import tessellate_polygon

from kit.outlines import Point, arc, turned
from kit.pieces import THICKNESS, TRIM_PROUD, TRIM_SUNK
from kit.scene import Vec3, add_mesh, default_name
from kit.surfaces import surface as surface_material

# Two faces that meet at less than this angle shade as one curved face, degrees.
SMOOTH_ANGLE = 30.0
# The rings of a dish are this far apart, m.
DISH_RING = 0.2
# Two outline points that are nearer than this are one point, m.
SAME_POINT = 1e-6
# A gear tooth: its size along the wall, out from the wall and down, and how far its top is
# below the top edge of the wall, m.
TOOTH_WIDTH = 0.32
TOOTH_DEPTH = 0.22
TOOTH_HEIGHT = 0.3
TOOTH_DROP = 0.12
# A gear wheel, as shares of its radius: the root of the teeth, the inner edge of the rim,
# the hub, the width of a spoke and how far the boss on the hub stands out.
GEAR_ROOT = 0.86
GEAR_RIM = 0.7
GEAR_HUB = 0.28
GEAR_SPOKE = 0.14
GEAR_BOSS = 0.05
GEAR_SPOKES = 6
# A grille: the width of a bar, the clear gap between two bars (below the marble's 0.4 m), the
# sides of a round bar, and the gap between the bars and the head of an arch, m.
GRILLE_BAR = 0.09
GRILLE_GAP = 0.26
GRILLE_SIDES = 6
GRILLE_CLEAR = 0.02


def deck(
    outline: Sequence[Point],
    top: float = 0.0,
    depth: float = THICKNESS,
    holes: Sequence[Sequence[Point]] = (),
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
    through: bool = False,
) -> bpy.types.Object:
    """Adds a floor of any outline: a block `depth` m deep whose flat top face is at the
    height `top`. Its sides are walls, so a deep deck is also the mass under the floor.
    holes: the outlines of openings in the top face, each for a piece that fills it, for
    example dish(). The block has no faces inside a hole. through: each hole goes down
    through the block and has walls: a shaft for a trapdoor, or a gap to fall through."""
    name = name or default_name("deck", "-col")
    bm = bmesh.new()
    _plate(bm, outline, holes, top, top - depth, through=through, closed=True)
    return add_mesh(bm, name, surface_material(surface, material), collide=True)


def inlay(
    outline: Sequence[Point],
    top: float = 0.0,
    holes: Sequence[Sequence[Point]] = (),
    name: str | None = None,
    material: str = "gold",
) -> bpy.types.Object:
    """Adds a flat figure of `material` set into a floor whose top is at the height `top`:
    a plate that stands TRIM_PROUD above the floor, as the edge trim of a track piece does.
    It does not collide, so it does not change how the marble rolls. holes: outlines cut out
    of the figure; a ring is a circle with a smaller circle as its hole."""
    name = name or default_name("inlay")
    bm = bmesh.new()
    _plate(
        bm,
        outline,
        holes,
        top + TRIM_PROUD,
        top - TRIM_SUNK,
        through=True,
        closed=False,
    )
    return add_mesh(bm, name, surface_material("default", material), collide=False)


def dish(
    at: Vec3,
    radius: float,
    depth: float,
    flat: float = 0.0,
    segments: int = 96,
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
) -> bpy.types.Object:
    """Adds a round bowl in a floor: its rim is a circle of `radius` around `at`, level with
    the floor, and its middle is `depth` m lower. The bowl is level out to the radius `flat`
    and at the rim, so the marble meets no edge. It collides. Cut its hole in the deck with
    `holes=[kit.arc(centre, radius, 0, 360, segments)]`: the same `segments` makes the rim
    fit the hole."""
    name = name or default_name("dish", "-col")
    if not 0.0 <= flat < radius:
        raise ValueError(f"kit.dish: flat must be from 0 to below the radius {radius}")
    rings = max(2, math.ceil((radius - flat) / DISH_RING))
    radii = [
        flat + (radius - flat) * k / rings
        for k in range(0 if flat > 0 else 1, rings + 1)
    ]
    bm = bmesh.new()
    middle = bm.verts.new((at[0], at[1], at[2] - depth))
    loops = []
    for r in radii:
        fall = 0.5 * depth * (1.0 + math.cos(math.pi * (r - flat) / (radius - flat)))
        loops.append(
            [
                bm.verts.new((x, y, at[2] - fall))
                for x, y in arc(at[:2], r, 0, 360, segments)
            ]
        )
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((middle, loops[0][i], loops[0][j])).smooth = True
        for inner, outer in pairwise(loops):
            bm.faces.new((inner[i], outer[i], outer[j], inner[j])).smooth = True
    return add_mesh(bm, name, surface_material(surface, material), collide=True)


def wall(
    path: Sequence[Vec3],
    height: float,
    width: float = 0.5,
    side: Literal["left", "right", "centre"] = "left",
    closed: bool = False,
    bevel: float = 0.0,
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
    collide: bool = True,
) -> bpy.types.Object:
    """Adds a wall, or a kerb when it is low: a bar `width` m wide and `height` m tall along
    the points of `path`, with mitred corners. Each point is the foot of the wall at a
    corner, so a path that climbs makes the kerb of a ramp. side: the side of the path that
    the wall stands on, seen along the path, so a wall on the `left` of a counter-clockwise
    outline stands inside it. closed: the path is a loop. bevel: the size of the chamfer on
    the two top edges."""
    name = name or default_name("wall", "-col" if collide else "")
    near = {"left": 0.0, "right": -width, "centre": -width / 2}[side]
    far = near + width
    section = [(near, 0.0), (far, 0.0), (far, height), (near, height)]
    if bevel > 0.0:
        section[2:] = [
            (far, height - bevel),
            (far - bevel, height),
            (near + bevel, height),
            (near, height - bevel),
        ]
    count = len(path)
    spans = count if closed else count - 1
    lefts = [_left(path[i], path[(i + 1) % count]) for i in range(spans)]
    bm = bmesh.new()
    rings = []
    turns = []
    for i, (x, y, z) in enumerate(path):
        before = lefts[i - 1] if closed or i > 0 else lefts[0]
        after = lefts[i] if closed or i < spans else lefts[-1]
        # The mitre: one step along it is one metre away from both segments.
        dot = before[0] * after[0] + before[1] * after[1]
        if dot < -0.999:
            raise ValueError(f"kit.wall: the path turns back on itself at point {i}")
        mitre = (
            (before[0] + after[0]) / (1.0 + dot),
            (before[1] + after[1]) / (1.0 + dot),
        )
        turns.append(math.degrees(math.acos(max(-1.0, min(1.0, dot)))))
        rings.append(
            [
                bm.verts.new((x + a * mitre[0], y + a * mitre[1], z + h))
                for a, h in section
            ]
        )
    for i in range(spans):
        here, there = rings[i], rings[(i + 1) % count]
        for k in range(len(section)):
            m = (k + 1) % len(section)
            bm.faces.new((here[k], here[m], there[m], there[k])).smooth = True
    if not closed:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
    # The faces shade as one round face along a curve of the path. The edges of the
    # section stay sharp, and so does the section at a corner of the path.
    for ring, turn in zip(rings, turns, strict=True):
        for k in range(len(section)):
            around = bm.edges.get((ring[k], ring[(k + 1) % len(section)]))
            if around is not None:
                around.smooth = turn < SMOOTH_ANGLE
    for i in range(spans):
        for k in range(len(section)):
            bm.edges.get((rings[i][k], rings[(i + 1) % count][k])).smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return add_mesh(bm, name, surface_material(surface, material), collide)


def teeth(
    path: Sequence[Vec3],
    side: Literal["left", "right"] = "right",
    closed: bool = False,
    pitch: float = 0.64,
    name: str | None = None,
    material: str = "brass",
) -> bpy.types.Object:
    """Adds a row of gear teeth on the face of a wall: blocks of `material`, TOOTH_WIDTH
    wide, one every `pitch` m along the points of `path`, which is the top edge of the wall.
    The teeth hang TOOTH_DROP below the path and stand out to the `side` of it, seen along
    the path. A corner of the path gets no tooth. They do not collide: put them on outer
    faces only, where the marble does not go."""
    name = name or default_name("teeth")
    count = len(path)
    spans = count if closed else count - 1
    out = -1.0 if side == "right" else 1.0
    lengths = [
        math.hypot(
            path[(i + 1) % count][0] - path[i][0], path[(i + 1) % count][1] - path[i][1]
        )
        for i in range(spans)
    ]
    total = sum(lengths)
    number = int(total // pitch)
    half = TOOTH_WIDTH / 2
    bm = bmesh.new()
    travelled = 0.0
    for i in range(spans):
        start, end = path[i], path[(i + 1) % count]
        length = lengths[i]
        left = _left(start, end)
        ahead = (left[1], -left[0])
        normal = (out * left[0], out * left[1])
        # The middle of a tooth is on this span. A tooth keeps clear of a corner and of an
        # end of the path; on a curve it reaches a little past the end of its span.
        clear = []
        for j in (i, (i + 1) % count):
            if not closed and j in (0, count - 1):
                clear.append(half)
            elif (
                _bend(path[j - 1][:2], path[j][:2], path[(j + 1) % count][:2])
                < SMOOTH_ANGLE
            ):
                clear.append(0.0)
            else:
                clear.append(half + TOOTH_DEPTH)
        for k in range(number):
            along = (total - number * pitch) / 2 + pitch * (k + 0.5) - travelled
            if not clear[0] <= along < length - clear[1]:
                continue
            ends = []
            for step in (along - half, along + half):
                x = start[0] + ahead[0] * step
                y = start[1] + ahead[1] * step
                top = start[2] + (end[2] - start[2]) * step / length - TOOTH_DROP
                ends.append(
                    [
                        bm.verts.new((x + normal[0] * d, y + normal[1] * d, top - h))
                        for d, h in (
                            (-TRIM_SUNK, 0.0),
                            (TOOTH_DEPTH, 0.0),
                            (TOOTH_DEPTH, TOOTH_HEIGHT),
                            (-TRIM_SUNK, TOOTH_HEIGHT),
                        )
                    ]
                )
            bm.faces.new(ends[0])
            bm.faces.new(ends[1])
            for a in range(4):
                b = (a + 1) % 4
                bm.faces.new((ends[0][a], ends[0][b], ends[1][b], ends[1][a]))
        travelled += length
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return add_mesh(bm, name, surface_material("default", material), collide=False)


def lathe(
    at: Vec3,
    profile: Sequence[Point],
    segments: int = 0,
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
    collide: bool = True,
) -> bpy.types.Object:
    """Adds a round piece that stands at `at`: the `profile` of (radius, height) points,
    from its bottom to its top, turned around the vertical axis through `at`. A radius of 0
    at an end closes it in a point; any other end gets a flat cap. A profile that ends
    where it starts makes a ring with no caps. With no `segments`, it gets as many sides as
    its widest ring needs to look round. The piece has its origin at `at`, so a level
    script can turn it, for example to stand a ring on its edge."""
    name = name or default_name("lathe", "-col" if collide else "")
    loop = len(profile) > 2 and profile[0] == profile[-1]
    points = list(profile[:-1] if loop else profile)
    widest = max(radius for radius, _ in points)
    sides = segments or len(arc((0.0, 0.0), widest, 0, 360))
    bm = bmesh.new()
    rings = [
        [
            bm.verts.new((x, y, height))
            for x, y in arc((0.0, 0.0), radius, 0, 360, sides)
        ]
        if radius > 0.0
        else [bm.verts.new((0.0, 0.0, height))]
        for radius, height in points
    ]
    for low, high in pairwise([*rings, rings[0]] if loop else rings):
        for i in range(sides):
            j = (i + 1) % sides
            corners = [low[i % len(low)], low[j % len(low)]]
            corners += [high[j % len(high)], high[i % len(high)]]
            # A ring of one point is the tip of a cone: its faces are triangles.
            face = list(dict.fromkeys(corners))
            if len(face) >= 3:
                bm.faces.new(face).smooth = True
    if not loop:
        for ring in (rings[0], rings[-1]):
            if len(ring) > 1:
                bm.faces.new(ring)
    count = len(points)
    for k in range(count) if loop else range(1, count - 1):
        bend = _bend(points[k - 1], points[k], points[(k + 1) % count])
        ring = rings[k]
        for i in range(len(ring)):
            around = bm.edges.get((ring[i], ring[(i + 1) % len(ring)]))
            if around is not None:
                around.smooth = bend < SMOOTH_ANGLE
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = add_mesh(bm, name, surface_material(surface, material), collide)
    obj.location = at
    return obj


def hoop(
    at: Vec3,
    radius: float,
    thickness: float = 0.25,
    rotation: Vec3 = (0.0, 0.0, 0.0),
    name: str | None = None,
    material: str = "brass",
) -> bpy.types.Object:
    """Adds a round ring of round section, for example a ring of an armillary sphere. Its
    middle is at `at`, its centre line has the radius `radius`, and it is `thickness` m
    thick. It lies flat; `rotation`, XYZ angles in degrees, turns it. It does not collide:
    keep it out of the marble's way."""
    name = name or default_name("hoop")
    steps = 16
    section = [
        (
            radius + thickness / 2 * math.cos(math.tau * k / steps),
            thickness / 2 * math.sin(math.tau * k / steps),
        )
        for k in range(steps)
    ]
    obj = lathe(at, [*section, section[0]], name=name, material=material, collide=False)
    obj.rotation_euler = [math.radians(angle) for angle in rotation]
    return obj


def pillar(
    at: Vec3, radius: float = 0.8, height: float = 3.5, name: str | None = None
) -> bpy.types.Object:
    """Adds a round limestone pillar that stands on the floor at `at`: a plinth of `radius`,
    a slim shaft and a capital, `height` m tall, with a brass ball on top. The stone
    collides; the ball is out of the marble's reach and does not."""
    name = name or default_name("pillar", "-col")
    shaft = 0.38 * radius
    stone = [
        (radius, 0.0),
        (radius, 0.4),
        (0.6 * radius, 0.55),
        (shaft, 0.75),
        (0.9 * shaft, height - 0.5),
        (0.55 * radius, height - 0.25),
        (0.55 * radius, height),
    ]
    obj = lathe(at, stone, name=name)
    finial = 0.45 * radius
    # The ball sits a little into the capital.
    top = ball((0.0, 0.0, height + 0.8 * finial), finial, name=f"{name}_ball")
    top.parent = obj
    return obj


def ball(
    at: Vec3, radius: float, name: str | None = None, material: str = "brass"
) -> bpy.types.Object:
    """Adds a ball of `material` whose middle is at `at`: a finial, or the pivot of a ring.
    It does not collide: keep it out of the marble's way."""
    name = name or default_name("ball")
    steps = 12
    half = [
        (
            radius * math.sin(math.pi * k / steps),
            -radius * math.cos(math.pi * k / steps),
        )
        for k in range(1, steps)
    ]
    profile = [(0.0, -radius), *half, (0.0, radius)]
    return lathe(at, profile, name=name, material=material, collide=False)


def gear(
    at: Vec3,
    radius: float,
    teeth: int = 14,
    depth: float = 0.25,
    yaw: float = 0.0,
    name: str | None = None,
    material: str = "brass",
) -> bpy.types.Object:
    """Adds a gear wheel that stands upright, flat against a wall: a rim with `teeth` teeth
    out to `radius`, six spokes and a hub. `at` is the middle of its front face. Like an
    arch, it faces -y and runs back `depth` m along +y, turned by `yaw` degrees, so a part
    of `depth` can be inside the wall. It does not collide: put it above the marble's reach
    or on a wall that the marble does not touch."""
    name = name or default_name("gear")
    pitch = 360.0 / teeth
    root = GEAR_ROOT * radius
    rim: list[Point] = []
    for i in range(teeth):
        middle = i * pitch
        # A tooth with sloped flanks, then the root of the gap to the next tooth.
        for share, reach in (
            (-0.25, root),
            (-0.15, radius),
            (0.15, radius),
            (0.25, root),
            (0.5, root),
        ):
            angle = math.radians(middle + share * pitch)
            rim.append((reach * math.cos(angle), reach * math.sin(angle)))
    # A window between each two spokes. The spokes have parallel sides.
    inner, outer = GEAR_HUB * radius, GEAR_RIM * radius
    windows = []
    for i in range(GEAR_SPOKES):
        middle = (i + 0.5) * 360.0 / GEAR_SPOKES
        spans = [
            180.0 / GEAR_SPOKES
            - math.degrees(math.asin(GEAR_SPOKE * radius / 2 / reach))
            for reach in (inner, outer)
        ]
        windows.append(
            [
                *arc((0.0, 0.0), inner, middle - spans[0], middle + spans[0]),
                *arc((0.0, 0.0), outer, middle + spans[1], middle - spans[1]),
            ]
        )
    bm = bmesh.new()
    _plate(bm, rim, windows, 0.0, -depth, through=True, closed=True)
    # The boss on the hub stands proud of the wheel.
    boss = arc((0.0, 0.0), 0.6 * inner, 0, 360)
    _plate(bm, boss, (), GEAR_BOSS * radius, 0.0, through=False, closed=False)
    # The wheel lies flat; stand it up, so that its top face is its front.
    bmesh.ops.rotate(
        bm,
        verts=bm.verts[:],
        cent=(0.0, 0.0, 0.0),
        matrix=Matrix.Rotation(math.pi / 2, 3, "X"),
    )
    obj = add_mesh(bm, name, surface_material("default", material), collide=False)
    obj.location = at
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw))
    return obj


def arch(
    at: Vec3,
    width: float,
    height: float,
    span: float,
    top: float,
    depth: float = 0.5,
    yaw: float = 0.0,
    surface: str = "default",
    name: str | None = None,
    material: str = "limestone",
) -> bpy.types.Object:
    """Adds a wall panel with a round-headed doorway. `at` is the middle of the threshold,
    on the front face of the panel. The doorway is `width` m wide and `height` m high at
    its crown. The panel is `span` m wide, `top` m tall and `depth` m thick. Like a track
    piece, it runs back from `at` along +y, turned by `yaw` degrees. It collides."""
    name = name or default_name("arch", "-col")
    half = width / 2
    spring = height - half
    if spring < 0.0 or top <= height or span <= width:
        raise ValueError("kit.arch: the doorway does not fit in the panel")
    head = [(x, y) for x, y in arc((0.0, spring), half, 180, 0)]
    outline = [
        (-span / 2, 0.0),
        (-half, 0.0),
        *head,
        (half, 0.0),
        (span / 2, 0.0),
        (span / 2, top),
        (-span / 2, top),
    ]
    bm = bmesh.new()
    _plate(bm, outline, (), 0.0, -depth, through=False, closed=True)
    # The plate lies flat with the doorway toward +y; stand it up, so that its top face is
    # the front of the panel.
    bmesh.ops.rotate(
        bm,
        verts=bm.verts[:],
        cent=(0.0, 0.0, 0.0),
        matrix=Matrix.Rotation(math.pi / 2, 3, "X"),
    )
    obj = add_mesh(bm, name, surface_material(surface, material), collide=True)
    obj.location = at
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw))
    return obj


def grille(
    at: Vec3,
    width: float,
    height: float,
    yaw: float = 0.0,
    arched: bool = False,
    rails: Sequence[float] = (),
    name: str | None = None,
    material: str = "brass",
) -> bpy.types.Object:
    """Adds a grille that fills a doorway: round upright bars GRILLE_BAR m thick with gaps of
    at most GRILLE_GAP m, also at the sides, which the marble cannot pass, and a level rail at
    each height in `rails`. `at` is the middle of the threshold, on the middle line of the
    grille. Like an arch, the
    grille lies across the way along +y, turned by `yaw` degrees. The bars stand `height` m
    tall; with `arched`, they stop under the round head of a kit.arch() doorway of the same
    width and height. It collides, and the sun shines through it."""
    name = name or default_name("grille", "-col")
    half = width / 2
    spring = height - half
    if arched and spring < 0.0:
        raise ValueError(
            "kit.grille: an arched doorway is at least half its width high"
        )

    def top(x: float) -> float:
        """The height of the doorway at x across it."""
        if not arched or abs(x) >= half:
            return height
        return spring + math.sqrt(half * half - x * x) - GRILLE_CLEAR

    # Enough bars that the gap at each side of the row is no wider than the gap between bars,
    # and one bar in a doorway narrower than a gap.
    pitch = GRILLE_BAR + GRILLE_GAP
    count = max(1, math.ceil((width - GRILLE_GAP) / pitch))
    first = -(count - 1) * pitch / 2
    bm = bmesh.new()
    for i in range(count):
        x = first + i * pitch
        reach = top(abs(x) + GRILLE_BAR / 2)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            segments=GRILLE_SIDES,
            radius1=GRILLE_BAR / 2,
            radius2=GRILLE_BAR / 2,
            depth=reach,
            matrix=Matrix.Translation((x, 0.0, reach / 2)),
        )
    # The sides of a bar shade round; its ends are its only faces that are not quads.
    for face in bm.faces:
        face.smooth = len(face.verts) == 4
    for z in rails:
        # A rail reaches across the doorway at its height, under the head of an arch.
        across = (
            half
            if z <= spring or not arched
            else math.sqrt(half * half - (z - spring) ** 2)
        )
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation((0.0, 0.0, z))
            @ Matrix.Diagonal(
                (2 * across - GRILLE_CLEAR, 1.6 * GRILLE_BAR, 2 * GRILLE_BAR, 1.0)
            ),
        )
    obj = add_mesh(bm, name, surface_material("default", material), collide=True)
    obj.location = at
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw))
    return obj


def _plate(
    bm: bmesh.types.BMesh,
    outline: Sequence[Point],
    holes: Sequence[Sequence[Point]],
    top: float,
    bottom: float,
    through: bool,
    closed: bool,
) -> None:
    """Adds a block to bm: the outline, minus the holes, from the height `top` down to
    `bottom`, with outward faces. through: a hole goes down through the block and has
    walls; else it is an opening in the top face only. closed: the block has a bottom face.
    A point that repeats the point before it is left out, so an outline can join an arc to
    the point where the arc ends."""
    loops = [
        _distinct(turned(outline)),
        *(_distinct(turned(hole, clockwise=True)) for hole in holes),
    ]
    upper = [[bm.verts.new((x, y, top)) for x, y in loop] for loop in loops]
    _fill(bm, loops, upper, up=True)
    walled = loops if through else loops[:1]
    lower = [[bm.verts.new((x, y, bottom)) for x, y in loop] for loop in walled]
    if closed:
        _fill(bm, walled, lower, up=False)
    for loop, high, low in zip(walled, upper, lower, strict=False):
        count = len(loop)
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new((high[i], low[i], low[j], high[j])).smooth = True
        for i in range(count):
            bend = _bend(loop[i - 1], loop[i], loop[(i + 1) % count])
            bm.edges.get((high[i], low[i])).smooth = bend < SMOOTH_ANGLE


def _fill(
    bm: bmesh.types.BMesh,
    loops: Sequence[Sequence[Point]],
    verts: Sequence[Sequence[bmesh.types.BMVert]],
    up: bool,
) -> None:
    """Fills the area inside the first loop and outside the others with flat triangles on
    verts, which face up or down."""
    points = [point for loop in loops for point in loop]
    flat = [vert for loop in verts for vert in loop]
    for a, b, c in tessellate_polygon(
        [[(x, y, 0.0) for x, y in loop] for loop in loops]
    ):
        (ax, ay), (bx, by), (cx, cy) = points[a], points[b], points[c]
        counter = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay) > 0.0
        bm.faces.new(
            (flat[a], flat[b], flat[c])
            if counter == up
            else (flat[a], flat[c], flat[b])
        )


def _distinct(outline: Sequence[Point]) -> list[Point]:
    """Returns the closed outline without each point that repeats the point before it."""
    return [
        point
        for i, point in enumerate(outline)
        if math.dist(point, outline[i - 1]) > SAME_POINT
    ]


def _left(start: Vec3, end: Vec3) -> Point:
    """Returns the unit vector to the left of the way from start to end, seen from above."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0.0:
        raise ValueError(f"kit.wall: two path points are at the same place, {start}")
    return (-dy / length, dx / length)


def _bend(before: Point, at: Point, after: Point) -> float:
    """Returns the angle in degrees by which a line turns at the point `at`."""
    first = math.atan2(at[1] - before[1], at[0] - before[0])
    second = math.atan2(after[1] - at[1], after[0] - at[0])
    return abs(math.degrees((second - first + math.pi) % math.tau - math.pi))
