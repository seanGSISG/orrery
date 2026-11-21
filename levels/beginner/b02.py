"""B2 Loose Hours (#29): the second level. It teaches jumps and checkpoints, with trapdoors
and crumbling tiles. A jump yard, a gate, a hall whose floor is a grid of loose and solid
panels over a room and the void, a terrace and three ways up to the finish. The brief and the
map are docs/levels/b02.md and b02.svg.

The script uses the axes of the map: x east, y north, the middle of the start court's south
edge at (0, 0). A map point (X, Y) in decimetres is (X / 10 - 30, 78 - Y / 10) here. Heights:
the start court, the jump yard, the gate and the hall 0 m, the channel -1 m, the undercroft
-4 m, the terrace +1 m, the landing +4 m and the finish deck +5 m. The marble starts with the
camera along +y, so it looks north. The dawn sun stands in the north-west.
"""

import math
from collections.abc import Sequence

import kit

Point = tuple[float, float]
Place = tuple[float, float, float]

# Every block goes down to this height. Out of bounds is 5 m below it.
BASE = -6.0
# The hall: a grid of CELL m cells, ten columns from west to east and one string per row
# from north to south. `.` is a solid panel, `T` a trapdoor, `C` crumbling tiles and `H` a
# hole. A cell is (column, row), counted from 0 at the north-west corner.
HALL_WEST = -20.0
HALL_NORTH = 44.0
CELL = 4.0
HALL_ROWS = (
    "T........H",
    "..T.CTH..T",
    ".T.CTHC.T.",
    "..........",
)
# Each loose cell and each hole is an opening of OPENING m in a frame of solid floor, so that
# an open trapdoor (OPENING long, DOOR thick) hangs clear of the undercroft floor.
FRAME = 0.2
OPENING = CELL - 2 * FRAME
DOOR = 0.3
# The undercroft: the room under the west half of the hall, and its alcove under the
# north-west trapdoor. Its floor is at -4 m and its ceiling, the hall's slab, at -1 m.
UNDERCROFT = [(-20, 32), (0, 32), (0, 40), (-16, 40), (-16, 44), (-20, 44)]
FLOOR = -4.0
CEILING = -1.0
# The trapdoor that drops the marble into the egg's nook. Its frame is gold.
EGG_DOOR = (4, 2)
# Trapdoors whose hinge is on the north side of the cell, so that the open door hangs
# against a wall of the undercroft. The others hinge on the south side.
NORTH_HINGES = {(0, 0), (2, 1), (5, 1), (9, 1)}
# The east sheet: crumbling tiles from the terrace (+1 m) up to the bridge (+4 m).
SHEET_FOOT = 49.0
SHEET_TOP = 59.0


def block(
    name: str,
    outline: Sequence[Point],
    top: float,
    holes: Sequence[Sequence[Point]] = (),
) -> None:
    """Adds a floor at the height `top` on a block that goes down to BASE. Its holes are
    shafts down through the block."""
    kit.deck(
        outline, top=top, depth=top - BASE, holes=holes, name=name, through=bool(holes)
    )


def kerb(name: str, path: Sequence[Place]) -> None:
    """Adds the brass kerb of an outer edge, 0.3 m high, on the left of the path, and a row
    of gear teeth below it on the outer face."""
    kit.wall(path, height=0.3, width=0.3, bevel=0.03, name=name, material="brass")
    kit.teeth(path, name=f"{name}_teeth")


def parapet(name: str, path: Sequence[Place], height: float) -> None:
    """Adds a stone parapet with a brass cap on the left of the path, and gear teeth on the
    outer face. It stands where a kerb is too low: where the marble comes through the air."""
    kit.wall(path, height=height, width=0.4, name=name)
    cap = [(x, y, z + height) for x, y, z in path]
    kit.wall(
        cap, height=0.1, width=0.4, bevel=0.03, name=f"{name}_cap", material="brass"
    )
    kit.teeth(path, name=f"{name}_teeth")


def rail(name: str, path: Sequence[Place], height: float) -> None:
    """Adds a brass rail on the right of the path, from 0.5 m below it to `height` above it:
    the frame of a loose floor, which stays when the tiles fall."""
    low = [(x, y, z - 0.5) for x, y, z in path]
    kit.wall(
        low,
        height=height + 0.5,
        width=0.3,
        side="right",
        bevel=0.03,
        name=name,
        material="brass",
    )


def ring(
    name: str,
    centre: Point,
    inner: float,
    outer: float,
    top: float,
    material: str = "gold",
) -> None:
    """Adds a ring of `material` set into the floor at the height `top`."""
    kit.inlay(
        kit.arc(centre, outer, 0, 360),
        top=top,
        holes=[kit.arc(centre, inner, 0, 360)],
        name=name,
        material=material,
    )


def cog(
    name: str, centre: Point, radius: float, teeth: int, inner: float, top: float
) -> None:
    """Adds a gold cog set into the floor at the height `top`: a ring with `teeth` teeth
    out to `radius`, round a hole of radius `inner`."""
    pitch = 360.0 / teeth
    root = radius - 0.3
    outline: list[Point] = []
    for i in range(teeth):
        for share, reach in (
            (-0.25, root),
            (-0.15, radius),
            (0.15, radius),
            (0.25, root),
        ):
            angle = math.radians((i + share) * pitch)
            outline.append(
                (
                    centre[0] + reach * math.cos(angle),
                    centre[1] + reach * math.sin(angle),
                )
            )
    kit.inlay(outline, top=top, holes=[kit.arc(centre, inner, 0, 360)], name=name)


def column(name: str, at: Point, top: float, radius: float) -> None:
    """Adds a round stone column from BASE up to `top`. Its flat top has the radius
    `radius`, for the marble to land on, and a gold ring."""
    height = top - BASE
    kit.lathe(
        at=(*at, BASE),
        profile=[
            (0.72 * radius, 0.0),
            (0.72 * radius, height - 1.1),
            (0.8 * radius, height - 0.8),
            (radius, height - 0.4),
            (radius, height),
        ],
        name=name,
    )
    ring(f"{name}_ring", at, radius - 0.3, radius - 0.18, top)


def post(name: str, at: Point, top: float = 0.48) -> None:
    """Adds a stone post of the undercroft, from its floor to its ceiling. `top` is the
    radius of its cap; stand the cap under solid floor, so that a marble that falls through
    an opening does not land on it."""
    room = CEILING - FLOOR
    k = top / 0.48
    kit.lathe(
        at=(*at, FLOOR),
        profile=[
            (0.5 * k, 0.0),
            (0.5 * k, 0.3),
            (0.32 * k, 0.45),
            (0.28 * k, room - 0.5),
            (0.42 * k, room - 0.2),
            (top, room),
        ],
        name=name,
    )


def cell_box(c: int, r: int, inset: float) -> list[Point]:
    """Returns the outline of the hall cell (c, r), `inset` m inside its edges."""
    x0 = HALL_WEST + CELL * c
    y0 = HALL_NORTH - CELL * (r + 1)
    return kit.rect(x0 + inset, y0 + inset, x0 + CELL - inset, y0 + CELL - inset)


def cell_centre(c: int, r: int) -> Point:
    """Returns the middle of the hall cell (c, r)."""
    return (HALL_WEST + CELL * (c + 0.5), HALL_NORTH - CELL * (r + 0.5))


def in_undercroft(c: int, r: int) -> bool:
    """True when the hall cell (c, r) is over the undercroft: the west five cells of the two
    middle rows, and the north-west cell over the alcove."""
    return (c <= 4 and r in (1, 2)) or (c, r) == (0, 0)


kit.level(title="Loose Hours", par=49.3, gold=27.9, sky="dawn")

# --- Start court and jump yard ----------------------------------------------------------

# The start court and the south half of the yard are one block. A channel 3 m wide and 1 m
# deep crosses the yard. A ramp at each end of it leads back up, so a missed jump costs a
# short roll.
block(
    "yard_south",
    [(-10, 0), (10, 0), (10, 8), (19, 8), (19, 15), (-19, 15), (-19, 8), (-10, 8)],
    top=0.0,
)
block("channel", kit.rect(-19, 15, 19, 18), top=-1.0)
for name, x, yaw in (("east", 15.0, -90), ("west", -15.0, 90)):
    kit.ramp(
        at=(x, 16.5, -1.0),
        width=3,
        length=4,
        rise=1,
        yaw=yaw,
        fill=True,
        trim="",
        name=f"channel_ramp_{name}",
    )
# The north half of the yard and the forecourt of the gate.
block(
    "yard_north",
    [
        (-19, 18),
        (19, 18),
        (19, 25),
        (8, 25),
        (8, 27.4),
        (-8, 27.4),
        (-8, 25),
        (-19, 25),
    ],
    top=0.0,
)
# The block: a step of 1 m with a gem on top.
kit.deck(kit.rect(-13, 19.5, -9, 23.5), top=1.0, depth=1.0, name="block")

# --- Trapdoor hall and undercroft -------------------------------------------------------

loose: dict[tuple[int, int], str] = {
    (c, r): kind
    for r, line in enumerate(HALL_ROWS)
    for c, kind in enumerate(line)
    if kind != "."
}
openings = {key: cell_box(*key, FRAME) for key in loose}
# The hall block goes down to BASE, except where the undercroft is under it. Its south strip
# carries the hall's south wall. Each opening east of the undercroft is a shaft to the void.
block(
    "hall",
    [
        (-20, 27.4),
        (20, 27.4),
        (20, 44),
        (-16, 44),
        (-16, 40),
        (0, 40),
        (0, 32),
        (-20, 32),
    ],
    top=0.0,
    holes=[shape for key, shape in openings.items() if not in_undercroft(*key)],
)
# The hall's slab over the undercroft is its ceiling.
kit.deck(
    UNDERCROFT,
    top=0.0,
    depth=-CEILING,
    holes=[shape for key, shape in openings.items() if in_undercroft(*key)],
    name="undercroft_ceiling",
    through=True,
)
block("undercroft", UNDERCROFT, top=FLOOR)
# The north wall of the alcove, which carries the end of the hall's north kerb.
block("undercroft_wall", kit.rect(-20, 44, -14, 44.5), top=0.0)
# Posts hold the ceiling, under solid panels. A slim post hides the egg's nook from the
# west: it stands under the strip of floor between the crumbling cell and the egg's door.
for i, at in enumerate(((-18, 38), (-14, 38), (-10, 34), (-6, 38))):
    post(f"undercroft_post_{i}", at)
post("undercroft_post_nook", (HALL_WEST + CELL * EGG_DOOR[0], 34.0), FRAME - 0.02)

for (c, r), kind in loose.items():
    centre = cell_centre(c, r)
    name = f"cell_{c}{r}"
    frame = "gold" if (c, r) == EGG_DOOR else "brass"
    kit.inlay(
        cell_box(c, r, 0.06),
        holes=[cell_box(c, r, FRAME - 0.02)],
        name=f"{name}_frame",
        material=frame,
    )
    if kind == "T":
        kit.marker(
            "trapdoor",
            at=(*centre, 0.0),
            rotation=(0, 0, 180 if (c, r) in NORTH_HINGES else 0),
            name=f"trapdoor_{c}{r}",
            width=OPENING,
            depth=OPENING,
            thickness=DOOR,
        )
    elif kind == "C":
        kit.marker(
            "crumbling_tiles",
            at=(*centre, 0.0),
            name=f"tiles_{c}{r}",
            width=OPENING,
            depth=OPENING,
            tile=OPENING / 2,
        )

# The hall's south wall is too high to jump. The gate is the one way in.
for name, x0, x1 in (("west", -20.0, -3.0), ("east", 3.0, 20.0)):
    path = [(x0, 27.4, 0.0), (x1, 27.4, 0.0)]
    kit.wall(path, height=2.6, width=0.6, name=f"hall_wall_{name}")
    kit.wall(
        [(x0, 27.4, 2.6), (x1, 27.4, 2.6)],
        height=0.12,
        width=0.6,
        bevel=0.03,
        name=f"hall_wall_{name}_cap",
        material="brass",
    )
    kit.teeth(path, name=f"hall_wall_{name}_teeth")
kit.arch(
    at=(0, 27.4, 0), width=3.0, height=3.6, span=6.0, top=5.6, depth=0.6, name="gate"
)
kit.wall(
    [(-3, 27.4, 5.6), (3, 27.4, 5.6)],
    height=0.12,
    width=0.6,
    bevel=0.03,
    name="gate_cap",
    material="brass",
)
kit.gear(at=(0, 27.36, 4.55), radius=0.8, depth=0.2, name="gate_gear_south")
kit.gear(at=(0, 28.04, 4.55), radius=0.8, depth=0.2, yaw=180, name="gate_gear_north")
# Two pillars stand before the gate. A brass gear wheel is set into the hall wall on each
# side of the gate, over the gap below the wall, out of the marble's reach.
for name, side in (("west", -1), ("east", 1)):
    kit.pillar(
        at=(side * 4.4, 26.2, 0), radius=0.6, height=3.6, name=f"gate_pillar_{name}"
    )
    kit.gear(at=(side * 12, 27.36, 1.35), radius=1.1, name=f"hall_wall_gear_{name}")
# A gear wheel set into the east wall of the egg's nook. The egg's light falls on it.
kit.gear(at=(-0.03, 34, -2.5), radius=0.8, depth=0.2, yaw=-90, name="nook_gear")

# --- Undercroft steps --------------------------------------------------------------------

# A stair of three steps of 1 m leads from the undercroft's open west side back up to the
# yard: west onto step 3, south up steps 2 and 1, east up onto the yard.
block("step_3", kit.rect(-24, 29, -20, 35), top=-3.0)
block("step_2", kit.rect(-24, 25, -20, 29), top=-2.0)
block("step_1", kit.rect(-23, 21, -19, 25), top=-1.0)

# --- Terrace and the three ways up ------------------------------------------------------

block("terrace", kit.rect(-14, 44, 16, 49), top=1.0)
# West stair: three pads at +2, +3 and +4 m, then a bridge to the landing.
block("stair_a", kit.rect(-14, 51, -10, 55), top=2.0)
block("stair_b", kit.rect(-20, 51, -16, 55), top=3.0)
block("stair_c", kit.rect(-20, 57, -16, 61), top=4.0)
kit.deck(kit.rect(-16, 59, -6, 61), top=4.0, depth=0.8, name="stair_bridge")
# Centre pillars: three precise jumps.
column("pillar_low", (0, 51.6), 2.2, 1.0)
column("pillar_high", (0, 55.2), 3.3, 1.0)
# East sheet: crumbling tiles from the terrace up to a crumbling bridge to the landing, in a
# brass frame that stays when the tiles fall. The marble turns west onto the bridge at the
# top of the sheet. The tiles are 1 m, so a marble that keeps rolling at 3 m/s or more stays
# up, also in the turn.
sheet_slope = math.degrees(math.atan2(4.0 - 1.0, SHEET_TOP - SHEET_FOOT))
kit.marker(
    "crumbling_tiles",
    at=(13, (SHEET_FOOT + SHEET_TOP) / 2, 2.5),
    rotation=(sheet_slope, 0, 0),
    name="tiles_sheet",
    width=6.0,
    depth=math.hypot(SHEET_TOP - SHEET_FOOT, 3.0),
    tile=1.0,
)
kit.marker(
    "crumbling_tiles",
    at=(11, SHEET_TOP + 1.5, 4.0),
    name="tiles_sheet_bridge",
    width=10.0,
    depth=3.0,
    tile=1.0,
)
rail("sheet_rail_west", [(10, SHEET_TOP, 4.0), (10, SHEET_FOOT, 1.0)], 0.3)
rail("sheet_rail_east", [(16, SHEET_FOOT, 1.0), (16, SHEET_TOP, 4.0)], 0.3)
rail("sheet_bridge_rail", [(6, SHEET_TOP, 4.0), (10, SHEET_TOP, 4.0)], 0.3)
# A fast marble leaves the top of the sheet through the air.
rail(
    "sheet_parapet",
    [(16, SHEET_TOP, 4.0), (16, SHEET_TOP + 3, 4.0), (7, SHEET_TOP + 3, 4.0)],
    1.2,
)

# --- Landing and finish deck -------------------------------------------------------------

block("landing", kit.rect(-6, 58, 6, 62), top=4.0)
block("finish_deck", kit.rect(-7, 62, 7, 69), top=5.0)
# A large gear wheel is set into the face of the landing, behind the centre pillars.
kit.gear(at=(0, 57.97, 0.6), radius=2.4, teeth=20, name="landing_gear")

# --- Kerbs and parapets ------------------------------------------------------------------

kerb(
    "kerb_yard",
    [
        (-19, 21, 0),
        (-19, 8, 0),
        (-10, 8, 0),
        (-10, 0, 0),
        (10, 0, 0),
        (10, 8, 0),
        (19, 8, 0),
        (19, 25, 0),
    ],
)
# The marble reaches the north edge of the yard through the air, after the channel.
parapet("parapet_yard_east", [(19, 25, 0), (8, 25, 0)], 1.2)
parapet("parapet_yard_west", [(-8, 25, 0), (-19, 25, 0)], 1.2)
kerb("kerb_gate_east", [(8, 25, 0), (8, 27.4, 0)])
kerb("kerb_gate_west", [(-8, 27.4, 0), (-8, 25, 0)])
kerb("kerb_hall_east", [(20, 28, 0), (20, 44, 0), (16, 44, 0)])
kerb("kerb_hall_west", [(-14, 44.5, 0), (-20, 44.5, 0), (-20, 28, 0)])
kerb("kerb_terrace_west", [(-14, 49, 1), (-14, 44, 1)])
kerb("kerb_terrace_east", [(16, 44, 1), (16, 49, 1)])
kerb("kerb_terrace_north_west", [(-2, 49, 1), (-9.5, 49, 1)])
kerb("kerb_terrace_north_east", [(9.5, 49, 1), (2, 49, 1)])
kerb("kerb_undercroft", [(-20, 44, -4), (-20, 35, -4)])
kerb("kerb_step_3", [(-20, 35, -3), (-24, 35, -3), (-24, 29, -3)])
kerb("kerb_step_2", [(-24, 29, -2), (-24, 25, -2)])
kerb("kerb_step_2_gap", [(-20, 25, -2), (-20, 27.4, -2)])
kerb("kerb_step_1", [(-23, 25, -1), (-23, 21, -1), (-19, 21, -1)])
kerb("kerb_step_1_gap", [(-19, 25, -1), (-20, 25, -1)])
kerb("kerb_stair", [(-6, 61, 4), (-20, 61, 4), (-20, 57, 4)])
kerb("kerb_stair_bridge", [(-16, 59, 4), (-6, 59, 4)])
kerb("kerb_finish", [(7, 62, 5), (7, 69, 5), (-7, 69, 5), (-7, 62, 5)])

# A brass line marks each open edge that the marble drops from or jumps up to.
for name, strip, top in (
    ("edge_channel_south", kit.rect(-15, 14.86, 15, 15), 0.0),
    ("edge_channel_north", kit.rect(-15, 18, 15, 18.14), 0.0),
    ("edge_yard_west", kit.rect(-19, 21, -18.86, 25), 0.0),
    ("edge_terrace_south", kit.rect(-14, 44, 16, 44.14), 1.0),
    ("edge_terrace_west_way", kit.rect(-14, 48.86, -9.5, 49), 1.0),
    ("edge_terrace_pillars", kit.rect(-2, 48.86, 2, 49), 1.0),
    ("edge_landing", kit.rect(-6, 58, 6, 58.14), 4.0),
    ("edge_finish", kit.rect(-7, 62, 7, 62.14), 5.0),
):
    kit.inlay(strip, top=top, name=name, material="brass")

# --- The clock over the finish -----------------------------------------------------------

# A brass wheel in a brass ring between two stone piers, seen from the start. Three of its
# twelve hour balls are missing: the loose hours.
DIAL = (0.0, 68.2, 11.6)
DIAL_RADIUS = 4.35
for name, side in (("west", -1), ("east", 1)):
    kit.pillar(
        at=(side * 5.4, 68.0, 5.0), radius=0.7, height=6.8, name=f"dial_pier_{name}"
    )
    kit.ball((side * 4.85, DIAL[1], DIAL[2]), 0.3, name=f"dial_pivot_{name}")
kit.gear(
    at=(DIAL[0], DIAL[1] + 0.15, DIAL[2]),
    radius=3.9,
    teeth=36,
    depth=0.2,
    name="dial_wheel",
)
kit.hoop(DIAL, DIAL_RADIUS, 0.32, rotation=(90, 0, 0), name="dial_ring")
for hour in range(12):
    if hour in (2, 7, 10):
        continue
    angle = math.radians(90 - 30 * hour)
    kit.ball(
        (
            DIAL[0] + DIAL_RADIUS * math.cos(angle),
            DIAL[1] - 0.05,
            DIAL[2] + DIAL_RADIUS * math.sin(angle),
        ),
        0.3,
        name=f"dial_hour_{hour:02d}",
    )
kit.ball((DIAL[0], DIAL[1] - 0.3, DIAL[2]), 0.38, name="dial_hub")
for name, length, turn in (("hour", 2.3, 128.0), ("minute", 3.4, -24.0)):
    hand = kit.lathe(
        at=(DIAL[0], DIAL[1] - 0.25, DIAL[2]),
        profile=[(0.14, 0.0), (0.14, length - 0.5), (0.0, length)],
        name=f"dial_hand_{name}",
        material="gold",
        collide=False,
    )
    hand.rotation_euler = (0.0, math.radians(turn), 0.0)

# --- Objects -----------------------------------------------------------------------------

START = (0.0, 3.0, 0.0)
FINISH = (0.0, 66.0, 5.0)
kit.marker("start", at=START)
kit.marker("finish", at=FINISH)
ring("start_ring", START[:2], 0.6, 0.75, 0.0)
cog("start_cog", START[:2], 2.6, 18, 2.0, 0.0)
ring("finish_ring", FINISH[:2], 1.3, 1.5, 5.0)
GEMS = {
    "channel": (6.0, 16.5, 0.6),
    "block": (-11.0, 21.5, 1.0),
    "trapdoor": (-14.0, 34.0, 0.0),
    "tiles": (-2.9, 39.3, 0.0),
    "island": (14.0, 38.8, 0.0),
    "landing": (0.0, 60.3, 5.2),
}
for name, at in GEMS.items():
    kit.marker("gem", at=at, name=f"gem_{name}")
for name in ("block", "island"):
    at = GEMS[name]
    ring(f"gem_ring_{name}", at[:2], 0.45, 0.55, at[2])
# The Clockwork Egg: in the nook at the east end of the undercroft, under the gold-framed
# trapdoor straight ahead of the gate.
kit.marker("egg", at=(*cell_centre(*EGG_DOOR), -4.0))
# Checkpoint 1 is in the gate. Checkpoint 2 is a pad at the foot of each way up.
kit.marker("checkpoint", at=(0, 27.7, 0), name="checkpoint_gate")
for name, x in (("west", -12.0), ("centre", 0.0), ("east", 13.0)):
    kit.marker("checkpoint", at=(x, 46.6, 1.0), name=f"checkpoint_terrace_{name}")

# --- Routes ------------------------------------------------------------------------------

# A route is a list of steps: a point and its actions ("jump; speed 6"), or "" for none. A
# `speed` caps the way into its point, so a capped point has a free point a few metres before
# it.
Step = tuple[Place, str]


def route(kind: str, steps: Sequence[Step]) -> None:
    """Places the route marker of `kind` from the start pad along `steps`."""
    kit.marker(
        "route",
        at=START,
        points=[point for point, _ in steps],
        name=f"route_{kind}",
        kind=kind,
        actions="; ".join(
            f"{i} {action.strip()}"
            for i, (_, text) in enumerate(steps)
            for action in text.split(";")
            if action.strip()
        ),
    )


# Both routes start the same: a jump over the channel through the first gem, a jump onto the
# block, then the gate.
YARD: list[Step] = [
    ((5.2, 14.4, 0), "jump; speed 9"),
    (GEMS["channel"], ""),
    ((6.9, 20.6, 0), "speed 6"),
    ((-3.6, 21.4, 0), ""),
    ((-7.4, 21.5, 0), "jump; speed 6"),
    (GEMS["block"], ""),
    ((-1.0, 25.2, 0), ""),
    ((0, 29.2, 0), ""),
]


def landing(side: int) -> list[Step]:
    """Returns the end of a route that comes off a bridge onto the landing, from the west
    (`side` -1) or the east (1): a jump along the bridge's line through the last gem, then a
    hop north onto the finish deck."""
    gem = GEMS["landing"]
    return [
        ((side * 3.8, gem[1] - 0.05, 4), ""),
        ((side * 1.5, gem[1] - 0.1, 4), "jump; speed 4.5"),
        (gem, ""),
        ((-side * 2.6, 60.9, 4), ""),
        ((-side * 2.6, 61.3, 4), "jump"),
        (FINISH, ""),
    ]


# First run: west along the solid south row and fast over the west trapdoor through its gem,
# east along the solid north row with a cut over the corner of the crumbling tiles, round
# the east island, up to the terrace and the west stair. The bot stops before the trapdoor,
# as a first-time player does.
route(
    "first_run",
    [
        *YARD,
        ((-14, 29.8, 0), "wait 0"),
        (GEMS["trapdoor"], ""),
        ((-14, 41.8, 0), ""),
        ((-8.6, 41.6, 0), ""),
        ((-5.6, 37.0, 0), ""),
        (GEMS["tiles"], ""),
        ((-0.2, 41.6, 0), ""),
        ((10, 41.8, 0), ""),
        ((10, 38.8, 0), ""),
        (GEMS["island"], ""),
        ((14, 42.6, 0), "jump; speed 6"),
        ((12.6, 46.4, 1), ""),
        ((-12, 46.6, 1), ""),
        ((-12, 48.6, 1), "jump; speed 6"),
        ((-12, 53, 2), ""),
        ((-13.6, 53, 2), "jump; speed 6"),
        ((-18, 53, 3), ""),
        ((-18, 54.4, 3), "jump; speed 6"),
        ((-18, 59.6, 4), ""),
        ((-6, 60, 4), ""),
        *landing(-1),
    ],
)
# Expert: through the west trapdoor gem, then east along the middle row in one line: the
# crumbling gem, a trapdoor, a jump over a hole, the island gem. Up the east sheet and over
# its crumbling bridge.
route(
    "expert",
    [
        *YARD,
        ((-10.0, 29.7, 0), ""),
        ((-13.4, 29.9, 0), "speed 3.5"),
        (GEMS["trapdoor"], ""),
        ((-14, 38.4, 0), ""),
        ((-6, 39.3, 0), ""),
        (GEMS["tiles"], ""),
        ((2.8, 39.3, 0), "jump; speed 10"),
        ((10.4, 39.2, 0), "speed 10"),
        (GEMS["island"], ""),
        ((14, 42.8, 0), "jump; speed 6"),
        ((13.6, 46.6, 1), ""),
        ((14, 57.4, 3.52), ""),
        ((13.0, 60.2, 4), ""),
        ((6.4, 60.5, 4), ""),
        *landing(1),
    ],
)

# --- Shots -------------------------------------------------------------------------------

kit.shot("overview", at=(-40, 28, 30), rotation=(-36, 0, -76))
kit.shot("start", at=(0, 0.2, 1.6), rotation=(-6, 0, 0))
kit.shot("finish", at=(-9, 57, 7.5), rotation=(-8, 0, -40))
kit.shot("egg", at=(-9, 35.5, -2.6), rotation=(-12, 0, -104))
kit.shot("gate", at=(-5, 21, 2.2), rotation=(2, 0, -18))
kit.shot("hall", at=(0, 28.4, 3.6), rotation=(-24, 0, 0))
kit.shot("climbs", at=(4, 41, 4.5), rotation=(-2, 0, 0))
kit.shot("undercroft", at=(-23, 31.5, -1.6), rotation=(-12, 0, -64))
kit.shot("sheet", at=(22, 45, 6), rotation=(-12, 0, 38))
