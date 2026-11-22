"""Town: the pieces of the Ascent town and its clock tower (Ascent zone 1, #31).

Play pieces (they collide):
- helix(): a spiral ramp round a vertical axis; helix_point() gives a point on it and
  helix_kerb() a brass kerb along it.
- lift(): a lift gear: a gear that stands on its rim inside a brass casing and two side rings.
  It carries the marble from its bottom to its top, a half turn, and lets it off to one side.
- casing(): a curved band round a level axis; lift() is made of it.
- facade(): a straight wall with openings (doors, windows).
- block(): a box. stall(), crate() and chimney() are dressed boxes. house() adds a building
  to a Parts mesh, so that a street of them is one mesh; windows() and window() dress any wall
  face, and band() runs a string course or a cornice along it.

Decoration (no collision): sign(), clock_face() and decal(), a picture from assets/decals/.

Placeholders: spot() leaves a named empty where a prop model or a decal comes later. It shows
nothing in the game; docs/levels/ascent-z1.md lists the spots.

Every piece takes world positions. Each face has a Finish: the name of a game material.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Literal

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

import kit
from kit.scene import Vec3, add_object, default_name, pose
from kit.surfaces import surface as surface_material

Point = tuple[float, float]
# A wall opening: (centre along the wall, width, sill height, head height), m.
Opening = tuple[float, float, float, float]

# Decal art: PNG pictures with alpha (Git LFS), from the asset tools (tools/art/README.md).
DECALS = Path(__file__).resolve().parents[1] / "assets" / "decals"
# A curved piece gets one section for each this many degrees of its arc.
ARC_STEP = 5.0
# A lift gear: the gap from its tooth tips to the casing, the casing's thickness, the gap from
# the gear's faces to the side rings, and their thickness, m.
LIFT_GAP = 0.08
LIFT_CASING = 0.15
LIFT_SIDE_GAP = 0.05
LIFT_RING = 0.15
# The casing guards the rising side from the bottom (-90) up to this angle, degrees. Past it
# the notch holds the marble by itself.
LIFT_GUARD = 80.0
# The side ring of the exit side has a window round the top, from 90 - this to 90 + this.
LIFT_WINDOW = 14.0
# The gear thickness of a lift: room for the marble along the axis, m.
LIFT_THICKNESS = 1.2
# The width of a stripe of a stall's valance, m.
STRIPE = 0.32
# A window's stone frame: its width and depth, and the height of its lintel, m.
FRAME = 0.12
LINTEL = 0.22
# The finishes of town pieces. Each is a material of game/materials/ (KitMaterials.find):
# - limestone, brass, gold: the kit's materials (kit.surface()).
# - brass_polished: polished brass, for the casings and rings of the lift gears.
# - wall: limestone cut in courses of ashlar; wall_grey, wall_ochre and wall_pale: the same
#   stone in other tints, so that each house has its own (HOUSE_WALLS); dressed: limestone
#   with no joints, for frames, sills, string courses and cornices; wet_stone: dark wet stone
#   under water; gravel: a country road.
# - slate (slate_turned runs its courses along y), door, shutter, wood, canvas_*: CC0 texture
#   sets (docs/licenses.md).
# - glass: near-white panes that show the room behind; interior: that dark room; sash: painted
#   window bars; iron: black-painted iron; water: still water, dark, with a weak reflection.
Finish = Literal[
    "limestone",
    "brass",
    "gold",
    "brass_polished",
    "wall",
    "wall_grey",
    "wall_ochre",
    "wall_pale",
    "dressed",
    "wet_stone",
    "gravel",
    "slate",
    "slate_turned",
    "door",
    "shutter",
    "wood",
    "canvas_red",
    "canvas_ochre",
    "canvas_green",
    "canvas_cream",
    "glass",
    "interior",
    "sash",
    "iron",
    "water",
]
KIT_FINISHES = ("limestone", "brass", "gold")
# The walls of town houses: house() gives each house one of them, picked from its place, so
# that the houses of a street differ. The plain wall comes twice, so it stays the most common.
HOUSE_WALLS: tuple[Finish, ...] = (
    "wall",
    "wall",
    "wall_grey",
    "wall_ochre",
    "wall_pale",
)


def material(finish: Finish) -> bpy.types.Material:
    """Returns the material of a finish on surface type default, made once per level. The
    importer gives its faces the material of that name, so the look is set in the game."""
    if finish in KIT_FINISHES:
        return surface_material("default", finish)
    found = bpy.data.materials.get(f"{finish}_default")
    if found is None:
        found = bpy.data.materials.new(f"{finish}_default")
        found["surface"] = "default"
        found["material"] = finish
        found.use_backface_culling = True
    return found


# --- Meshes made of parts -------------------------------------------------------------------


class Parts:
    """One mesh built from parts of several materials. Add the parts, then call add() once."""

    def __init__(
        self, bm: bmesh.types.BMesh | None = None, finish: Finish | None = None
    ) -> None:
        self.bm = bm if bm is not None else bmesh.new()
        self.materials: list[Finish] = [finish] if finish else []
        # Single faces and the way each must face: add() keeps them so.
        self.flats: list[tuple[bmesh.types.BMFace, Vector]] = []

    def index(self, finish: Finish) -> int:
        """Returns the material slot of finish, made on first use."""
        if finish not in self.materials:
            self.materials.append(finish)
        return self.materials.index(finish)

    def faces(self, loops: list[list[bmesh.types.BMVert]], finish: Finish) -> None:
        """Adds a face on each loop of verts."""
        index = self.index(finish)
        for loop in loops:
            self.bm.faces.new(loop).material_index = index

    def flat(self, corners: Sequence[Vec3], facing: Vector, finish: Finish) -> None:
        """Adds one face on the corners, seen from the side `facing` (it has no back)."""
        face = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        face.material_index = self.index(finish)
        self.flats.append((face, facing))

    def solid(
        self, outline: Sequence[Point], bottom: float, top: float, finish: Finish
    ) -> None:
        """Adds a prism: a convex plan outline from the height bottom up to top."""
        low = [self.bm.verts.new((x, y, bottom)) for x, y in outline]
        high = [self.bm.verts.new((x, y, top)) for x, y in outline]
        self.faces([low, high, *_sides(low, high)], finish)

    def box(self, lo: Vec3, hi: Vec3, finish: Finish = "limestone") -> None:
        """Adds a box between the corners lo and hi."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        self.solid([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, finish)

    def slab(
        self,
        at: Point,
        along: Point,
        length: float,
        width: float,
        z: tuple[float, float],
        finish: Finish,
    ) -> None:
        """Adds a box `length` m along the unit direction `along` from the plan point `at` and
        `width` m to the left of it, between the heights z."""
        left = (-along[1], along[0])
        b = (at[0] + along[0] * length, at[1] + along[1] * length)
        c = (b[0] + left[0] * width, b[1] + left[1] * width)
        d = (at[0] + left[0] * width, at[1] + left[1] * width)
        self.solid([at, b, c, d], z[0], z[1], finish)

    def prism(
        self,
        section: Sequence[Point],
        start: float,
        end: float,
        axis: Literal["x", "y"],
        finish: Finish,
    ) -> None:
        """Adds a prism whose section runs along `axis` from start to end. A section point is
        (across, height): y and z for axis x, x and z for axis y."""

        def at(across: float, z: float, along: float) -> Vector:
            return (
                Vector((along, across, z))
                if axis == "x"
                else Vector((across, along, z))
            )

        first = [self.bm.verts.new(at(u, z, start)) for u, z in section]
        last = [self.bm.verts.new(at(u, z, end)) for u, z in section]
        self.faces([first, last, *_sides(first, last)], finish)

    def bar(self, a: Vec3, b: Vec3, width: float, finish: Finish) -> None:
        """Adds a square bar `width` m thick from the point a to b, for a strut or a rope."""
        axis = Vector(b) - Vector(a)
        side = axis.cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side = side.normalized() * width / 2
        up = axis.cross(side).normalized() * width / 2
        ring = [side + up, -side + up, -side - up, side - up]
        first = [self.bm.verts.new(Vector(a) + c) for c in ring]
        last = [self.bm.verts.new(Vector(b) + c) for c in ring]
        self.faces([first, last, *_sides(first, last)], finish)

    def mark(self) -> tuple[int, int]:
        """Returns a mark of the parts added so far, for turn()."""
        return len(self.bm.verts), len(self.flats)

    def turn(self, since: tuple[int, int], at: Point, yaw: float) -> None:
        """Turns the parts added after the mark `since` round the vertical axis through the
        plan point `at`, by `yaw` degrees counter-clockwise seen from above. Build a piece
        along x or y, then turn it to any heading."""
        rotation = Matrix.Rotation(math.radians(yaw), 3, "Z")
        self.bm.verts.ensure_lookup_table()
        verts = self.bm.verts[since[0] :]
        bmesh.ops.rotate(self.bm, verts=verts, cent=(*at, 0.0), matrix=rotation)
        self.flats[since[1] :] = [
            (face, rotation @ facing) for face, facing in self.flats[since[1] :]
        ]

    def add(self, name: str, collide: bool = True) -> bpy.types.Object:
        """Turns the parts into the object `name` (`<name>-col` when it collides)."""
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        for face, facing in self.flats:
            face.normal_update()
            if face.normal.dot(facing) < 0.0:
                face.normal_flip()
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for finish in self.materials:
            mesh.materials.append(material(finish))
        return add_object(f"{name}-col" if collide else name, mesh)


def block(
    name: str, lo: Vec3, hi: Vec3, finish: Finish = "wall", collide: bool = True
) -> bpy.types.Object:
    """Adds a box between the corners lo and hi."""
    parts = Parts()
    parts.box(lo, hi, finish)
    return parts.add(name, collide)


def floor(
    name: str,
    outline: Sequence[Point],
    top: float,
    depth: float,
    holes: Sequence[Sequence[Point]] = (),
    finish: Finish = "limestone",
) -> bpy.types.Object:
    """Adds a floor slab of any outline, `depth` m thick under the height `top`, with holes
    that go through it and have walls: a floor that a ramp or a lift comes up through."""
    loops = [
        _counter_clockwise(list(outline)),
        *(_counter_clockwise(list(hole))[::-1] for hole in holes),
    ]
    parts = Parts()
    bm = parts.bm
    index = parts.index(finish)
    high = [[bm.verts.new((x, y, top)) for x, y in loop] for loop in loops]
    low = [[bm.verts.new((x, y, top - depth)) for x, y in loop] for loop in loops]
    points = [point for loop in loops for point in loop]
    for verts, up in ((high, True), (low, False)):
        flat = [vert for loop in verts for vert in loop]
        for a, b, c in tessellate_polygon(
            [[(x, y, 0.0) for x, y in loop] for loop in loops]
        ):
            (ax, ay), (bx, by), (cx, cy) = points[a], points[b], points[c]
            counter = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay) > 0.0
            tri = (
                (flat[a], flat[b], flat[c])
                if counter == up
                else (flat[a], flat[c], flat[b])
            )
            bm.faces.new(tri).material_index = index
    for upper, lower in zip(high, low, strict=True):
        for side in _sides(lower, upper):
            bm.faces.new(side).material_index = index
    return parts.add(name)


# --- Walls ----------------------------------------------------------------------------------


def facade(
    name: str,
    a: Point,
    b: Point,
    bottom: float,
    top: float,
    thickness: float,
    openings: Sequence[Opening] = (),
    side: Literal["left", "right"] = "right",
    finish: Finish = "wall",
) -> bpy.types.Object:
    """Adds a straight wall from the plan point a to b, `thickness` m thick on the `side` of
    the line seen from a to b, from the height bottom to top. openings: holes, as (centre,
    width, sill, head); they must not overlap along the wall."""
    length = math.dist(a, b)
    along = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    left = (-along[1], along[0])
    shift = 0.0 if side == "left" else -thickness
    origin = (a[0] + left[0] * shift, a[1] + left[1] * shift)
    parts = Parts()

    def piece(s0: float, s1: float, z0: float, z1: float) -> None:
        if s1 - s0 > 1e-6 and z1 - z0 > 1e-6:
            start = (origin[0] + along[0] * s0, origin[1] + along[1] * s0)
            parts.slab(start, along, s1 - s0, thickness, (z0, z1), finish)

    done = 0.0
    for centre, width, sill, head in sorted(openings):
        s0, s1 = centre - width / 2, centre + width / 2
        piece(done, s0, bottom, top)
        piece(s0, s1, bottom, sill)
        piece(s0, s1, head, top)
        done = s1
    piece(done, length, bottom, top)
    return parts.add(name)


# --- Curved pieces --------------------------------------------------------------------------


def casing(
    at: Vec3,
    radius: float,
    start: float,
    end: float,
    width: float,
    thickness: float = LIFT_CASING,
    yaw: float = 0.0,
    name: str | None = None,
    finish: Finish = "brass",
) -> bpy.types.Object:
    """Adds a curved band round a level axis: the part of a tube from the angle `start` to
    `end`, degrees, whose inner face is `radius` m from the axis. `at` is the middle of the
    axis. With yaw 0 the axis runs along +y and the angles go from +x (0) to +z (90), as a
    gear that stands on its rim turns seen from -y; yaw turns the piece round z. The band is
    `width` m along the axis and `thickness` m thick, out from the inner face."""
    sections = []
    for angle in _arc_angles(start, end):
        a = math.radians(angle)
        ring = [
            _turn(Vector((r * math.cos(a), y, r * math.sin(a))), yaw) + Vector(at)
            for r, y in (
                (radius, -width / 2),
                (radius, width / 2),
                (radius + thickness, width / 2),
                (radius + thickness, -width / 2),
            )
        ]
        sections.append(ring)
    return Parts(_loft(sections), finish).add(name or default_name("casing", "-col"))


def helix(
    at: Vec3,
    inner: float,
    outer: float,
    start: float,
    turn: float,
    rise: float,
    thickness: float = 0.5,
    name: str | None = None,
    finish: Finish = "limestone",
) -> bpy.types.Object:
    """Adds a spiral ramp round the vertical axis through `at`: a slab between the radii
    `inner` and `outer`, from the angle `start` (degrees from +x, counter-clockwise seen from
    above) through `turn` degrees (negative turns clockwise). Its top face starts at the
    height of `at` and climbs `rise` m, and the slab is `thickness` m thick."""
    sections = []
    for angle in _arc_angles(start, start + turn):
        top = at[2] + rise * (angle - start) / turn
        a = math.radians(angle)
        sections.append(
            [
                Vector((at[0] + r * math.cos(a), at[1] + r * math.sin(a), z))
                for r, z in (
                    (inner, top),
                    (outer, top),
                    (outer, top - thickness),
                    (inner, top - thickness),
                )
            ]
        )
    return Parts(_loft(sections), finish).add(name or default_name("helix", "-col"))


def helix_point(
    at: Vec3, radius: float, start: float, turn: float, rise: float, angle: float
) -> Vec3:
    """Returns the point at `angle` degrees on the circle of `radius` round a helix() with
    these settings, on its top face."""
    a = math.radians(angle)
    return (
        at[0] + radius * math.cos(a),
        at[1] + radius * math.sin(a),
        at[2] + rise * (angle - start) / turn,
    )


def helix_kerb(
    at: Vec3,
    radius: float,
    start: float,
    turn: float,
    rise: float,
    height: float = 0.3,
    name: str | None = None,
    span: tuple[float, float] | None = None,
) -> bpy.types.Object:
    """Adds a brass kerb that stands on a helix() along the circle of `radius`, on its outer
    side: the kerb of the ramp's inner edge. span: the part of the helix from one angle to
    another, in the helix's direction; the whole helix when None."""
    first, last = span if span is not None else (start, start + turn)
    path = [
        helix_point(at, radius, start, turn, rise, angle)
        for angle in _arc_angles(first, last)
    ]
    return kit.wall(
        path,
        height=height,
        width=0.25,
        side="right" if turn > 0 else "left",
        bevel=0.03,
        name=name,
        material="brass",
    )


# --- Lift gears -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Lift:
    """Where a lift() takes the marble. floor: the top of the floor under the gear, where
    the marble boards; exit: the top of the floor beside the gear's top, where it leaves.
    board, side and out are route points: under the gear just past its lowest point, on
    the rising side at the axis height, and on the exit floor beside the top."""

    floor: float
    exit: float
    board: Vec3
    side: Vec3
    out: Vec3


def lift(
    name: str,
    at: Vec3,
    radius: float,
    yaw: float = 0.0,
    exit: Literal[1, -1] = 1,
    period: float = 16.0,
    teeth: int = 12,
) -> Lift:
    """Adds a lift gear whose level axis goes through `at`. With yaw 0 the gear stands across
    y: the marble rolls in under it along +x, a tooth pushes it up the +x side inside the
    casing of polished brass, and at the top it rolls off sideways, through a window in the side ring, to
    +y (exit 1) or -y (exit -1). yaw turns the lift round z. The gear turns once in `period`
    s, so the ride takes half of it. Build the boarding floor up to the axis line at `floor`,
    as a lane between the side rings, and the exit floor beside the top at `exit`, clear of
    the gear's face. The gear marker is `name`."""
    a = math.radians(yaw)
    u = (math.cos(a), math.sin(a))
    v = (-math.sin(a), math.cos(a))
    x, y, z = at
    kit.marker(
        "turning_gear",
        at=(x - v[0] * LIFT_THICKNESS / 2, y - v[1] * LIFT_THICKNESS / 2, z),
        rotation=(90.0, 0.0, yaw),
        period=period,
        radius=radius,
        thickness=LIFT_THICKNESS,
        teeth=teeth,
        name=name,
    )
    ring_at = LIFT_THICKNESS / 2 + LIFT_SIDE_GAP + LIFT_RING / 2
    casing(
        at,
        radius + LIFT_GAP,
        -90.0,
        LIFT_GUARD,
        2 * (ring_at + LIFT_RING / 2),
        yaw=yaw,
        name=f"{name}_casing",
        finish="brass_polished",
    )
    for side in (1, -1):
        window = side == exit
        casing(
            (x + v[0] * side * ring_at, y + v[1] * side * ring_at, z),
            radius - 0.6,
            90.0 + LIFT_WINDOW if window else 0.0,
            450.0 - LIFT_WINDOW if window else 360.0,
            LIFT_RING,
            thickness=0.9,
            yaw=yaw,
            name=f"{name}_ring_{'exit' if window else 'back'}",
            finish="brass_polished",
        )
    floor = z - radius - LIFT_GAP
    top = z + radius - 0.45
    out = LIFT_THICKNESS / 2 + 1.2
    return Lift(
        floor=floor,
        exit=top,
        board=(x + u[0] * 0.4, y + u[1] * 0.4, floor),
        side=(x + u[0] * (radius - 0.2), y + u[1] * (radius - 0.2), z),
        out=(x + v[0] * exit * out, y + v[1] * exit * out, top),
    )


# --- Dressed boxes --------------------------------------------------------------------------


def stall(
    name: str, lo: Point, hi: Point, top: float, canvas: Finish = "canvas_red"
) -> bpy.types.Object:
    """Adds a market stall on the floor at height 0 between the plan corners lo and hi, whose
    flat roof of boards is at the height `top`: four posts, a counter at the front (low y) and
    a valance round the roof in stripes of the canvas and cream. A low stall is a covered
    table. The roof is a step."""
    (x0, y0), (x1, y1) = lo, hi
    board = 0.14
    under = top - board
    parts = Parts()
    parts.box((x0, y0, under), (x1, y1, top), "wood")
    post = 0.14
    for px in (x0 + 0.05, x1 - 0.05 - post):
        for py in (y0 + 0.05, y1 - 0.05 - post):
            parts.box((px, py, 0.0), (px + post, py + post, under), "wood")
    counter = min(0.9, under - 0.3)
    if counter > 0.4:
        parts.box((x0 + 0.1, y0 + 0.1, 0.0), (x1 - 0.1, y0 + 0.8, counter), "wood")
        parts.box(
            (x0 + 0.05, y0 + 0.05, counter),
            (x1 - 0.05, y0 + 0.85, counter + 0.05),
            "wood",
        )
    else:
        parts.box((x0 + 0.1, y0 + 0.1, 0.0), (x1 - 0.1, y1 - 0.1, under), "wood")
    drop = min(0.35, under - 0.1)
    skirt = 0.03
    # The valance: its stripes are a mesh of their own that does not collide, and one plain
    # slab a side collides, so the marble meets no seam between two stripes.
    z = (under - drop, under)
    stripes, shell = Parts(), Parts()
    for at, along, length in (
        ((x0 - skirt, y0 - skirt), (1.0, 0.0), x1 - x0 + 2 * skirt),
        ((x1 + skirt, y1 + skirt), (-1.0, 0.0), x1 - x0 + 2 * skirt),
        ((x0 - skirt, y1), (0.0, -1.0), y1 - y0),
        ((x1 + skirt, y0), (0.0, 1.0), y1 - y0),
    ):
        shell.slab(at, along, length, skirt, z, canvas)
        count = max(1, round(length / STRIPE))
        step = length / count
        for i in range(count):
            start = (at[0] + along[0] * step * i, at[1] + along[1] * step * i)
            finish = canvas if i % 2 == 0 else "canvas_cream"
            stripes.slab(start, along, step, skirt, z, finish)
    stripes.add(f"{name}_valance", collide=False)
    shell.add(f"{name}_valance-colonly", collide=False)
    return parts.add(name)


def crate(name: str, lo: Vec3, hi: Vec3) -> bpy.types.Object:
    """Adds a wooden crate between the corners lo and hi, with two iron bands round it."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    parts = Parts()
    parts.box(lo, hi, "wood")
    band = 0.06
    for z in (z0 + 0.15, z1 - 0.15 - band):
        parts.box((x0 - 0.01, y0 - 0.01, z), (x1 + 0.01, y1 + 0.01, z + band), "iron")
    return parts.add(name)


def chimney(
    name: str, at: Vec3, width: float, height: float, flue: float = 0.0
) -> bpy.types.Object:
    """Adds a stone chimney stack with its foot's middle at `at`, `width` m square and
    `height` m tall, with a brass cap. flue > 0 leaves an open flue of that width down through
    the stack and no cap: a marble that drops in falls on down."""
    x, y, z = at
    h = width / 2
    parts = Parts()
    if flue <= 0.0:
        parts.box((x - h, y - h, z - 0.3), (x + h, y + h, z + height), "wall")
        c = h + 0.06
        parts.box((x - c, y - c, z + height - 0.2), (x + c, y + c, z + height), "brass")
    else:
        f = flue / 2
        for (ax, ay), (bx, by) in (
            ((x - h, y - h), (x + h, y - f)),
            ((x - h, y + f), (x + h, y + h)),
            ((x - h, y - f), (x - f, y + f)),
            ((x + f, y - f), (x + h, y + f)),
        ):
            parts.box((ax, ay, z - 0.3), (bx, by, z + height), "wall")
    return parts.add(name)


# --- Buildings ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Face:
    """A wall face in plan: it starts at `start` and runs `length` m along the unit direction
    `along`; `out` is the unit direction out of the wall."""

    start: Point
    along: Point
    out: Point
    length: float

    def at(self, s: float, o: float = 0.0) -> Point:
        """Returns the plan point `s` m along the face and `o` m out from it."""
        return (
            self.start[0] + self.along[0] * s + self.out[0] * o,
            self.start[1] + self.along[1] * s + self.out[1] * o,
        )


def faces(lo: Point, hi: Point) -> dict[str, Face]:
    """Returns the four faces of a box between the plan corners lo and hi, by side: s (low y),
    e, n and w, each running counter-clockwise round the box."""
    (x0, y0), (x1, y1) = lo, hi
    return {
        "s": Face((x0, y0), (1.0, 0.0), (0.0, -1.0), x1 - x0),
        "e": Face((x1, y0), (0.0, 1.0), (1.0, 0.0), y1 - y0),
        "n": Face((x1, y1), (-1.0, 0.0), (0.0, 1.0), x1 - x0),
        "w": Face((x0, y1), (0.0, -1.0), (-1.0, 0.0), y1 - y0),
    }


def house(
    parts: Parts,
    lo: Point,
    hi: Point,
    eave: float,
    ridge: float,
    along: Literal["x", "y"] = "x",
    door: str = "s",
    blind: str = "",
    storey: float = 3.0,
    plain: bool = False,
) -> None:
    """Adds a town house to parts between the plan corners lo and hi, on the floor at height
    0: coursed stone walls up to `eave`, a slate gable roof up to `ridge`, whose ridge runs
    along `along`, and a chimney stack on the ridge. The walls take one of HOUSE_WALLS, picked
    from lo. blind: the sides with no windows, for example "ew" for a house between two
    others. A house that is not plain also gets a door on the side `door` (s, e, n or w; ""
    for none), framed windows, a string course at each storey, a cornice under the eaves and
    an iron ridge. A plain house is for the far town: its windows are flat dark panes with no
    frame, and it has no door, bands or ridge."""
    (x0, y0), (x1, y1) = lo, hi
    wall = HOUSE_WALLS[_pick(lo, 0) % len(HOUSE_WALLS)]
    parts.box((x0, y0, 0.0), (x1, y1, eave), wall)
    over = 0.35
    if along == "x":
        mid, ends, low, high = (y0 + y1) / 2, (x0, x1), y0, y1
    else:
        mid, ends, low, high = (x0 + x1) / 2, (y0, y1), x0, x1
    slate: Finish = "slate" if along == "x" else "slate_turned"
    parts.prism([(low, eave), (high, eave), (mid, ridge - 0.3)], *ends, along, wall)
    parts.prism(
        [(low - over, eave - 0.25), (high + over, eave - 0.25), (mid, ridge)],
        ends[0] - 0.15,
        ends[1] + 0.15,
        along,
        slate,
    )
    if not plain:
        cap = [(mid - 0.12, ridge - 0.1), (mid + 0.12, ridge - 0.1)]
        cap += [(mid + 0.12, ridge + 0.08), (mid - 0.12, ridge + 0.08)]
        parts.prism(cap, ends[0] - 0.2, ends[1] + 0.2, along, "iron")
    # A chimney stack on the ridge, a quarter of the way along, with a cap and two pots.
    at = ends[0] + (ends[1] - ends[0]) * 0.25
    lo_c, hi_c = (at - 0.45, mid - 0.3), (at + 0.45, mid + 0.3)
    if along == "y":
        lo_c, hi_c = (mid - 0.3, at - 0.45), (mid + 0.3, at + 0.45)
    parts.box((*lo_c, ridge - 1.0), (*hi_c, ridge + 1.1), wall)
    parts.box(
        (lo_c[0] - 0.06, lo_c[1] - 0.06, ridge + 1.1),
        (hi_c[0] + 0.06, hi_c[1] + 0.06, ridge + 1.22),
        "dressed",
    )
    sides = faces(lo, hi)
    shown = {key: face for key, face in sides.items() if key not in blind}
    if plain:
        for face in shown.values():
            panes(parts, face, eave - 0.55, storey)
        return
    for t in (0.3, 0.7):
        px = lo_c[0] + (hi_c[0] - lo_c[0]) * (t if along == "x" else 0.5)
        py = lo_c[1] + (hi_c[1] - lo_c[1]) * (0.5 if along == "x" else t)
        parts.solid(_octagon((px, py), 0.11), ridge + 1.22, ridge + 1.6, "iron")
    # A string course at each storey and a cornice under the eaves. Each runs only along the
    # shown faces, and stops flush at a blind side, so that two houses in a row meet flush.
    for k in range(1, math.ceil((eave - 0.9) / storey)):
        band(parts, shown, sides, k * storey - 0.09, k * storey + 0.09, 0.07)
    band(parts, shown, sides, eave - 0.5, eave - 0.38, 0.08)
    band(parts, shown, sides, eave - 0.38, eave - 0.25, 0.18)
    for key, face in shown.items():
        windows(parts, face, eave - 0.55, storey, door=key == door)


def panes(
    parts: Parts, face: Face, top: float, storey: float = 3.0, spacing: float = 2.6
) -> None:
    """Adds the windows of a far house on a wall face: flat dark panes 2 cm proud of the wall,
    with no frame, in the rows and places of windows() up to the height top."""
    count = max(1, int((face.length - 1.2) // spacing))
    step = face.length / count
    out = Vector((*face.out, 0.0))
    for floor in range(int(top // storey) + 1):
        sill = floor * storey + (0.9 if floor == 0 else 0.8)
        head = floor * storey + 2.2
        if head + LINTEL > top:
            continue
        for i in range(count):
            a = face.at(step * (i + 0.5) - 0.5, 0.02)
            b = face.at(step * (i + 0.5) + 0.5, 0.02)
            corners = [(*a, sill), (*b, sill), (*b, head), (*a, head)]
            parts.flat(corners, out, "interior")


def band(
    parts: Parts,
    shown: dict[str, Face],
    sides: dict[str, Face],
    bottom: float,
    top: float,
    out: float,
) -> None:
    """Adds a stone band `out` m proud of each shown face of a box, between the heights
    bottom and top. At a corner between two shown faces, the band of the later face (in the
    order of faces()) fills the corner, so the two do not overlap."""
    order = list(sides)
    for key, face in shown.items():
        before = order[order.index(key) - 1]
        s0 = -out if before in shown else 0.0
        corners = [face.at(s0), face.at(face.length), face.at(face.length, out)]
        corners.append(face.at(s0, out))
        parts.solid(_counter_clockwise(corners), bottom, top, "dressed")


def windows(
    parts: Parts,
    face: Face,
    top: float,
    storey: float = 3.0,
    bottom: float = 0.0,
    door: bool = False,
    spacing: float = 2.6,
) -> None:
    """Adds a row of windows on each storey of a wall face from the height bottom up to top
    (the top of the highest lintel), about `spacing` m apart, and a door in the middle of the
    lowest row when `door`. About one storey in three has shutters."""
    count = max(1, int((face.length - 1.2) // spacing))
    step = face.length / count
    for floor in range(int((top - bottom) // storey) + 1):
        base = bottom + floor * storey
        shutters = _pick(face.start, floor) % 3 == 0
        for i in range(count):
            door_here = door and floor == 0 and i == count // 2
            sill = base + (0.0 if door_here else 0.9 if floor == 0 else 0.8)
            head = base + (2.4 if door_here else 2.2)
            if head + LINTEL <= top:
                width = 1.4 if door_here else 1.0
                window(
                    parts,
                    face,
                    step * (i + 0.5),
                    width,
                    sill,
                    head,
                    door_here,
                    shutters=shutters and not door_here,
                )


def window(
    parts: Parts,
    face: Face,
    centre: float,
    width: float,
    sill: float,
    head: float,
    door: bool = False,
    pane: Finish | None = None,
    shutters: bool = False,
    room: str = "",
) -> None:
    """Adds one window or door on a wall face, `centre` m along it, from the height sill to
    head. A stone frame FRAME m wide and deep stands round it, with a lintel above and, under a
    window, a sill. Inside the frame: a door leaf; or the panel `pane` (for example iron
    louvres); or a window: a dark room behind near-white glass with a cross of sash bars, so
    the glass sits back in the frame. shutters: two shutter leaves open flat beside it.
    room: the decal art of the room behind the glass (a shop window), in place of the dark
    room; it is its own object, so give it to a few windows only."""

    def piece(
        s0: float, s1: float, o0: float, o1: float, z0: float, z1: float, finish: Finish
    ) -> None:
        corners = [face.at(s0, o0), face.at(s1, o0), face.at(s1, o1), face.at(s0, o1)]
        parts.solid(_counter_clockwise(corners), z0, z1, finish)

    def panel(o: float, finish: Finish) -> None:
        a, b = face.at(s0, o), face.at(s1, o)
        corners = [(*a, sill), (*b, sill), (*b, head), (*a, head)]
        parts.flat(corners, Vector((*face.out, 0.0)), finish)

    half = width / 2
    s0, s1 = centre - half, centre + half
    if door:
        piece(s0, s1, 0.0, 0.05, sill, head, "door")
    elif pane is not None:
        piece(s0, s1, 0.0, 0.04, sill, head, pane)
    else:
        if room:
            x, y = face.at(centre, 0.006)
            yaw = math.degrees(math.atan2(face.out[0], -face.out[1]))
            decal(
                f"room_{room}_{x:.0f}_{y:.0f}",
                room,
                (x, y, (sill + head) / 2),
                yaw,
                (width, head - sill),
            )
        else:
            panel(0.005, "interior")
        panel(0.03, "glass")
        bar = 0.025
        piece(centre - bar, centre + bar, 0.0, 0.06, sill, head, "sash")
        transom = sill + (head - sill) * 0.62
        piece(s0, s1, 0.0, 0.06, transom - bar, transom + bar, "sash")
    piece(s0 - FRAME, s0, 0.0, FRAME, sill, head, "dressed")
    piece(s1, s1 + FRAME, 0.0, FRAME, sill, head, "dressed")
    piece(
        s0 - FRAME - 0.06,
        s1 + FRAME + 0.06,
        0.0,
        FRAME + 0.02,
        head,
        head + LINTEL,
        "dressed",
    )
    if not door:
        piece(
            s0 - FRAME - 0.05,
            s1 + FRAME + 0.05,
            0.0,
            FRAME + 0.06,
            sill - 0.1,
            sill,
            "dressed",
        )
    if shutters:
        leaf = half
        for side in (-1, 1):
            near = centre + side * (half + FRAME + 0.02)
            far = near + side * leaf
            piece(min(near, far), max(near, far), 0.0, 0.04, sill, head, "shutter")


def _pick(at: Point, n: int) -> int:
    """Returns a whole number that a plan point and a count always give the same: a stable
    choice with no random state."""
    return int(abs(at[0] * 7.0 + at[1] * 13.0)) + n * 5


# --- Decoration -----------------------------------------------------------------------------


def sign(
    name: str,
    at: Vec3,
    out: Point,
    width: float = 1.0,
    height: float = 0.7,
    art: str = "",
) -> bpy.types.Object:
    """Adds a hanging shop sign: an iron bracket from the wall point `at` along the unit
    direction `out`, and a board below it, side on to the street. art: the decal on both
    faces of the board (decal()); without it, the decal spot `decal_<name>` marks the board
    for its art."""
    x, y, z = at
    left = (-out[1], out[0])
    reach = width + 0.3
    parts = Parts()
    parts.slab(
        (x - left[0] * 0.03, y - left[1] * 0.03),
        out,
        reach,
        0.06,
        (z - 0.06, z),
        "iron",
    )
    near = (x + out[0] * 0.2 - left[0] * 0.03, y + out[1] * 0.2 - left[1] * 0.03)
    board = (z - 0.1 - height, z - 0.1)
    parts.slab(near, out, width, 0.06, board, "wood")
    middle = (x + out[0] * (0.2 + width / 2), y + out[1] * (0.2 + width / 2))
    facing = math.degrees(math.atan2(out[1], out[0]))
    if not art:
        spot(
            "decal",
            name,
            (*middle, (board[0] + board[1]) / 2),
            (90.0, 0.0, facing),
            (width, 0.06, height),
            "shop sign art, on both faces of the board",
        )
    for side in (1, -1):
        # The board is 0.06 m thick round the line `left` 0.03 m from the bracket.
        face = (middle[0] + left[0] * side * 0.035, middle[1] + left[1] * side * 0.035)
        if art:
            decal(
                f"{name}_{'a' if side > 0 else 'b'}",
                art,
                (*face, (board[0] + board[1]) / 2),
                facing + (180.0 if side > 0 else 0.0),
                (width, height),
            )
    return parts.add(name, collide=False)


def clock_face(
    name: str,
    at: Vec3,
    yaw: float,
    radius: float,
    hour: float = 6.0,
    minute: float = 0.0,
    art: str = "",
) -> bpy.types.Object:
    """Adds a clock dial on a wall: `at` is the dial's middle on the wall face, and yaw turns
    the dial from facing -y. A stone dial plate, a gold rim, the hour marks and two brass
    hands at hour:minute. art: the decal of a dial with no hands, which gives the marks;
    without it, twelve brass hour bars (no numerals) and a decal spot `decal_<name>`."""
    a = math.radians(yaw)
    right = (math.cos(a), math.sin(a))
    out = (math.sin(a), -math.cos(a))
    parts = Parts()
    _dial_ring(parts, at, right, out, 0.0, radius, (0.0, 0.12), "limestone")
    _dial_ring(parts, at, right, out, radius - 0.25, radius + 0.1, (0.0, 0.2), "gold")
    for h in range(0 if art else 12):
        bar = 0.18 if h % 3 == 0 else 0.11
        angle = math.radians(90.0 - 30.0 * h)
        _dial_bar(
            parts,
            at,
            right,
            out,
            angle,
            (radius * 0.72, radius * 0.88),
            bar,
            (0.12, 0.17),
        )
    hour_angle = math.radians(90.0 - 30.0 * (hour + minute / 60.0))
    _dial_bar(
        parts, at, right, out, hour_angle, (-0.3, radius * 0.5), 0.22, (0.17, 0.24)
    )
    minute_angle = math.radians(90.0 - 6.0 * minute)
    _dial_bar(
        parts, at, right, out, minute_angle, (-0.4, radius * 0.75), 0.14, (0.24, 0.3)
    )
    middle = (at[0] + out[0] * 0.125, at[1] + out[1] * 0.125, at[2])
    if art:
        decal(f"{name}_art", art, middle, yaw, (2 * radius - 0.2, 2 * radius - 0.2))
    else:
        size = (2 * radius, 0.02, 2 * radius)
        spot(
            "decal", name, middle, (90.0, 0.0, yaw), size, "clock dial art, no numerals"
        )
    return parts.add(name, collide=False)


def decal(
    name: str,
    art: str,
    at: Vec3,
    yaw: float,
    size: tuple[float, float],
    soft: bool = False,
) -> bpy.types.Object:
    """Adds a flat picture: the art `assets/decals/<art>.png` on an upright quad `size`
    (width, height) m whose middle is `at`, facing -y turned by yaw degrees, as a clock dial
    does. Put it a few millimetres proud of its wall. Its alpha cuts the outline at 0.5; a
    soft decal (grime, stains) blends by its alpha instead. It does not collide; decals of one
    art share one material."""
    a = math.radians(yaw)
    right = Vector((math.cos(a), math.sin(a), 0.0))
    up = Vector((0.0, 0.0, 1.0))
    middle = Vector(at)
    w, h = size[0] / 2, size[1] / 2
    bm = bmesh.new()
    corners = [middle - right * w - up * h, middle + right * w - up * h]
    corners += [middle + right * w + up * h, middle - right * w + up * h]
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    uv = bm.loops.layers.uv.new("UVMap")
    for loop, coord in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1)), strict=True):
        loop[uv].uv = coord
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(_decal_material(art, soft))
    return add_object(name, mesh)


def _decal_material(art: str, soft: bool = False) -> bpy.types.Material:
    """Returns the material of a decal art, made once per level: its picture as the colour,
    and its alpha cut at 0.5 (a Round node, which the glTF export writes as alpha mode MASK),
    or for a soft decal its alpha as it is (alpha mode BLEND)."""
    key = f"decal_{art}_soft" if soft else f"decal_{art}"
    found = bpy.data.materials.get(key)
    if found is not None:
        return found
    found = bpy.data.materials.new(key)
    found.use_backface_culling = True
    tree = found.node_tree
    bsdf = tree.nodes["Principled BSDF"]
    picture = tree.nodes.new("ShaderNodeTexImage")
    picture.image = bpy.data.images.load(str(DECALS / f"{art}.png"))
    tree.links.new(picture.outputs["Color"], bsdf.inputs["Base Color"])
    if soft:
        found.surface_render_method = "BLENDED"
        tree.links.new(picture.outputs["Alpha"], bsdf.inputs["Alpha"])
    else:
        cut = tree.nodes.new("ShaderNodeMath")
        cut.operation = "ROUND"
        tree.links.new(picture.outputs["Alpha"], cut.inputs[0])
        tree.links.new(cut.outputs["Value"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.65
    return found


def _dial(
    at: Vec3, right: Point, out: Point, r: float, angle: float, depth: float
) -> Vector:
    """Returns the point at radius r and angle (radians from the dial's right) on a dial,
    `depth` m out from the wall."""
    return Vector(
        (
            at[0] + right[0] * r * math.cos(angle) + out[0] * depth,
            at[1] + right[1] * r * math.cos(angle) + out[1] * depth,
            at[2] + r * math.sin(angle),
        )
    )


def _dial_ring(
    parts: Parts,
    at: Vec3,
    right: Point,
    out: Point,
    inner: float,
    outer: float,
    depth: tuple[float, float],
    finish: Finish,
    sides: int = 64,
) -> None:
    """Adds a flat ring (a disc when inner is 0) on a dial, between two depths."""
    angles = [math.tau * i / sides for i in range(sides)]
    if inner <= 0.0:
        for d0, d1 in (depth,):
            back = [
                parts.bm.verts.new(_dial(at, right, out, outer, t, d0)) for t in angles
            ]
            front = [
                parts.bm.verts.new(_dial(at, right, out, outer, t, d1)) for t in angles
            ]
            parts.faces([back, front, *_sides(back, front)], finish)
        return
    rings = [
        [parts.bm.verts.new(_dial(at, right, out, r, t, d)) for t in angles]
        for r, d in (
            (inner, depth[0]),
            (outer, depth[0]),
            (outer, depth[1]),
            (inner, depth[1]),
        )
    ]
    for k in range(4):
        here, there = rings[k], rings[(k + 1) % 4]
        parts.faces(
            [
                [here[i], here[(i + 1) % sides], there[(i + 1) % sides], there[i]]
                for i in range(sides)
            ],
            finish,
        )


def _dial_bar(
    parts: Parts,
    at: Vec3,
    right: Point,
    out: Point,
    angle: float,
    span: tuple[float, float],
    width: float,
    depth: tuple[float, float],
) -> None:
    """Adds a brass bar on a dial along `angle` (radians), over the radii of span, `width` m
    wide, between two depths."""
    across = angle + math.pi / 2
    corners = []
    for r, w in ((span[0], -1), (span[1], -1), (span[1], 1), (span[0], 1)):
        side = r * math.cos(angle) + w * width / 2 * math.cos(across)
        up = r * math.sin(angle) + w * width / 2 * math.sin(across)
        corners.append((side, up))
    loops = [
        [
            parts.bm.verts.new(
                (
                    at[0] + right[0] * side + out[0] * d,
                    at[1] + right[1] * side + out[1] * d,
                    at[2] + up,
                )
            )
            for side, up in corners
        ]
        for d in depth
    ]
    parts.faces([loops[0], loops[1], *_sides(loops[0], loops[1])], "brass")


# --- Placeholders ---------------------------------------------------------------------------


def spot(
    kind: Literal["prop", "decal"],
    name: str,
    at: Vec3,
    rotation: Vec3 = (0.0, 0.0, 0.0),
    size: Vec3 = (1.0, 1.0, 1.0),
    note: str = "",
) -> bpy.types.Object:
    """Leaves an empty named `<kind>_<name>` where a prop model (kit.prop) or a decal comes
    later, with its size (width, depth, height in m) and a note as custom properties. It
    shows nothing in the game. A prop spot stands at the middle of the prop's base, off every
    play surface, so the prop can come in without a change to how the zone plays."""
    obj = add_object(f"{kind}_{name}")
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.5
    obj.matrix_world = pose(at, rotation)
    obj["town_spot"] = {"kind": kind, "size": list(size), "note": note}
    return obj


# --- Helpers --------------------------------------------------------------------------------


def _sides(
    low: list[bmesh.types.BMVert], high: list[bmesh.types.BMVert]
) -> list[list[bmesh.types.BMVert]]:
    """Returns the side quads between two loops of verts."""
    count = len(low)
    return [
        [low[i], low[(i + 1) % count], high[(i + 1) % count], high[i]]
        for i in range(count)
    ]


def _octagon(at: Point, radius: float) -> list[Point]:
    """Returns the plan outline of an octagon round `at`."""
    return [
        (
            at[0] + radius * math.cos(math.tau * i / 8),
            at[1] + radius * math.sin(math.tau * i / 8),
        )
        for i in range(8)
    ]


def _counter_clockwise(points: list[Point]) -> list[Point]:
    """Returns a plan outline with its points in counter-clockwise order."""
    count = len(points)
    area = sum(
        points[i][0] * points[(i + 1) % count][1]
        - points[(i + 1) % count][0] * points[i][1]
        for i in range(count)
    )
    return points if area > 0 else points[::-1]


def _arc_angles(start: float, end: float) -> list[float]:
    """Returns the angles from start to end, at most ARC_STEP degrees apart."""
    count = max(1, math.ceil(abs(end - start) / ARC_STEP))
    return [start + (end - start) * i / count for i in range(count + 1)]


def _turn(v: Vector, yaw: float) -> Vector:
    """Returns v turned by yaw degrees round z."""
    a = math.radians(yaw)
    return Vector(
        (
            v.x * math.cos(a) - v.y * math.sin(a),
            v.x * math.sin(a) + v.y * math.cos(a),
            v.z,
        )
    )


def _loft(sections: Sequence[Sequence[Vector]]) -> bmesh.types.BMesh:
    """Returns a closed solid through the sections, in order: each section is a loop of
    points, and every section has the same number. The two end sections are its caps. The
    faces shade smooth along the run and keep sharp corners across it."""
    bm = bmesh.new()
    loops = [[bm.verts.new(p) for p in ring] for ring in sections]
    count = len(sections[0])
    for a, b in pairwise(loops):
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new((a[i], a[j], b[j], b[i])).smooth = True
            bm.edges.get((a[i], b[i])).smooth = False
    bm.faces.new(loops[0])
    bm.faces.new(loops[-1])
    return bm
