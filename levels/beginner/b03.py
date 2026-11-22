"""B3 Spring Court (#30): the third level. It teaches the Coil Spring, with bumpers and moving
platforms. One spring in a safe start court lifts the marble over the Step, a gatehouse across
the whole court. Beyond it lies a wide walled court like a pinball table, with two balconies and
a clock tower round it. The player picks a way up to each: a spring, the gear stair or a
carriage. Two carriages circle the tower like the hands of a clock. The brief and the map are
docs/levels/b03.md and b03.svg.

The script uses the axes of the map: x east, y north, the middle of the start court's south
edge at (0, 0). A map point (X, Y) in decimetres is (X / 10 - 30, 78 - Y / 10) here. Heights:
the start court and the bumper court 0 m, the egg ledge +3 m, the Step +5 m, the balconies
+6 m and the tower +7 m. The marble starts with the camera along +y, so it looks north. The
dawn sun stands in the north-west, so the Step's south face is in shade: the Step is a gatehouse
on an arcade, and the sun shines through the grilles of its arches onto the start court.
"""

import math
from collections.abc import Sequence

import kit
from kit import town

Point = tuple[float, float]
Place = tuple[float, float, float]

# Every block goes down to this height. Out of bounds is 5 m below it.
BASE = -3.0
STEP = 5.0
LEDGE = 3.0
BALCONY = 6.0
TOWER = 7.0
# The Step's slab: its top and its underside, the crown of the arcade under it.
STEP_SLAB = 0.8
ARCADE = STEP - STEP_SLAB
# The arches of the Step's south face: their middles, the doorway and the panel.
ARCH_XS = (-12.5, -7.5, -2.5, 2.5, 7.5, 12.5)
ARCH_WIDTH = 3.6
ARCH_CROWN = 3.6
ARCH_SPAN = 5.0
ARCH_DEPTH = 0.6
# The carriage loop at +6 m round the tower, with a 2 s stop at each point: from the west
# balcony past the south dock to the east balcony, round the north-east corner to the north
# dock and round the north-west corner back. The balcony stops touch the balconies, the docks
# touch the tower, and the deck keeps 0.2 m from both. A straight leg from a balcony to the
# north dock would cut through the tower, so the loop turns at its two north corners.
CARRIAGE = 4.0
CARRIAGE_WEST = (-10.8, 50.8, BALCONY)
CARRIAGE_LOOP = [
    (0.0, 50.8, BALCONY),
    (10.8, 50.8, BALCONY),
    (10.8, 65.2, BALCONY),
    (0.0, 65.2, BALCONY),
    (-10.8, 65.2, BALCONY),
]
CARRIAGE_PERIOD = 28.0
CARRIAGE_STOP = 2.0
# The gear stair along the east wall: the middle of each gear and the height of its top face.
GEARS = [
    ((18.0, 18.8), 1.0),
    ((19.4, 23.6), 2.0),
    ((18.0, 28.4), 3.0),
    ((19.4, 33.2), 4.0),
    ((18.0, 38.0), 5.0),
    ((19.0, 42.6), 6.0),
]
GEAR_THICKNESS = 0.5
# The dial in the court floor: its middle is the middle bumper.
DIAL_CENTRE = (0.0, 29.8)
DIAL_RADIUS = 12.0


def block(name: str, outline: Sequence[Point], top: float) -> None:
    """Adds a floor at the height `top` on a block that goes down to BASE."""
    kit.deck(outline, top=top, depth=top - BASE, name=name)


def kerb(name: str, path: Sequence[Place]) -> None:
    """Adds the brass kerb of an outer edge, 0.3 m high, on the left of the path, and a row
    of gear teeth below it on the outer face."""
    kit.wall(path, height=0.3, width=0.3, bevel=0.03, name=name, material="brass")
    kit.teeth(path, name=f"{name}_teeth")


def parapet(
    name: str, path: Sequence[Place], height: float, teeth: bool = True
) -> None:
    """Adds a stone parapet with a brass cap on the left of the path, and gear teeth on the
    outer face. It stands where a kerb is too low: where the marble comes through the air."""
    kit.wall(path, height=height, width=0.4, name=name)
    cap = [(x, y, z + height) for x, y, z in path]
    kit.wall(
        cap, height=0.1, width=0.4, bevel=0.03, name=f"{name}_cap", material="brass"
    )
    if teeth:
        kit.teeth(path, name=f"{name}_teeth")


def coping(name: str, x0: float, y0: float, x1: float, y1: float, top: float) -> None:
    """Adds a stone coping 0.16 m thick on the wall block from (x0, y0) to (x1, y1) whose top
    is at `top`. It reaches 0.08 m past the block on each side, and a brass strip runs along
    its middle."""
    kit.deck(
        kit.rect(x0 - 0.08, y0 - 0.08, x1 + 0.08, y1 + 0.08),
        top=top + 0.16,
        depth=0.16,
        name=name,
    )
    if x1 - x0 < y1 - y0:
        mid = (x0 + x1) / 2
        strip = kit.rect(mid - 0.05, y0, mid + 0.05, y1)
    else:
        mid = (y0 + y1) / 2
        strip = kit.rect(x0, mid - 0.05, x1, mid + 0.05)
    kit.inlay(strip, top=top + 0.16, name=f"{name}_strip", material="brass")


def pilaster(
    name: str, outline: Sequence[Point], top: float, foot: float = BASE
) -> None:
    """Adds a stone pilaster against a wall: a block from `foot` up to `top`, with a brass
    cap."""
    kit.deck(outline, top=top, depth=top - foot, name=name)
    kit.inlay(outline, top=top, name=f"{name}_cap", material="brass")


def ring(
    name: str,
    centre: Point,
    inner: float,
    outer: float,
    top: float,
    material: str = "brass",
) -> None:
    """Adds a ring of `material` set into the floor at the height `top`."""
    kit.inlay(
        kit.arc(centre, outer, 0, 360),
        top=top,
        holes=[kit.arc(centre, inner, 0, 360)],
        name=name,
        material=material,
    )


def dial_hand(name: str, towards: Point, length: float) -> None:
    """Adds a brass hand of the court dial, `length` m long, from the hub toward `towards`:
    a slim bar with a lozenge near its tip."""
    dx, dy = towards[0] - DIAL_CENTRE[0], towards[1] - DIAL_CENTRE[1]
    span = math.hypot(dx, dy)
    ux, uy = dx / span, dy / span
    shape = [
        (1.9, -0.22),
        (length - 1.4, -0.12),
        (length - 0.9, -0.36),
        (length, 0.0),
        (length - 0.9, 0.36),
        (length - 1.4, 0.12),
        (1.9, 0.22),
    ]
    kit.inlay(
        [
            (
                DIAL_CENTRE[0] + ux * along - uy * across,
                DIAL_CENTRE[1] + uy * along + ux * across,
            )
            for along, across in shape
        ],
        name=name,
        material="brass",
    )


def column(name: str, at: Place, height: float, radius: float) -> None:
    """Adds a round stone column that stands on the floor at `at`: a plinth, a shaft and a
    capital `height` m tall, whose top has the radius `radius` and carries a slab."""
    kit.lathe(
        at=at,
        profile=[
            (radius, 0.0),
            (radius, 0.3),
            (0.72 * radius, 0.45),
            (0.6 * radius, height - 0.45),
            (0.8 * radius, height - 0.25),
            (radius, height),
        ],
        name=name,
    )


kit.level(title="Spring Court", par=93.6, gold=27.8, sky="dawn")

# --- Start court, arcade and bumper court -------------------------------------------------

# One floor at 0 m: the start court, the arcade under the Step and the bumper court. The
# grilles of the arcade part the start court from the rest.
block(
    "floor",
    [
        (-10, 0),
        (10, 0),
        (10, 8),
        (15, 8),
        (15, 16),
        (22, 16),
        (22, 45),
        (-22, 45),
        (-22, 16),
        (-15, 16),
        (-15, 8),
        (-10, 8),
    ],
    top=0.0,
)
kerb("kerb_start", [(-10, 8, 0), (-10, 0, 0), (10, 0, 0), (10, 8, 0)])

# --- The Step: a gatehouse across the court ----------------------------------------------

# The slab of the Step rests on an arcade. Each south arch has a brass grille: a jump cannot
# climb the Step and the marble cannot pass the bars, but the sun and the view pass through.
kit.deck(kit.rect(-15, 8, 15, 16), top=STEP, depth=STEP_SLAB, name="step")
for i, x in enumerate(ARCH_XS):
    kit.arch(
        at=(x, 8, 0),
        width=ARCH_WIDTH,
        height=ARCH_CROWN,
        span=ARCH_SPAN,
        top=ARCADE,
        depth=ARCH_DEPTH,
        name=f"step_arch_{i}",
    )
    kit.grille(
        at=(x, 8 + ARCH_DEPTH / 2, 0),
        width=ARCH_WIDTH,
        height=ARCH_CROWN,
        arched=True,
        rails=(1.3,),
        name=f"step_grille_{i}",
    )
# The ends of the arcade, and columns under the north edge of the slab. The court runs on
# under the slab as a covered walk.
for name, x0, x1 in (("west", -15.0, -14.4), ("east", 14.4, 15.0)):
    kit.deck(
        kit.rect(x0, 8 + ARCH_DEPTH, x1, 16),
        top=ARCADE,
        depth=ARCADE,
        name=f"step_end_{name}",
    )
for i, x in enumerate((-9.0, -3.0, 3.0, 9.0)):
    column(f"step_column_{i}", (x, 15.4, 0), ARCADE, 0.5)
kerb("kerb_step", [(-15, 16, STEP), (-15, 8, STEP), (15, 8, STEP), (15, 16, STEP)])
kit.teeth([(15, 16, STEP), (-15, 16, STEP)], name="step_north_teeth")

# The court floor is a dial: a brass ring round the middle bumper with twelve hour bars, and
# two brass hands that point at the two court springs (see Objects).
ring("court_dial", DIAL_CENTRE, DIAL_RADIUS - 0.22, DIAL_RADIUS, 0.0)
ring("court_dial_hub", DIAL_CENTRE, 1.5, 1.68, 0.0)
for hour in range(12):
    angle = math.radians(90 - 30 * hour)
    long = 1.6 if hour % 3 == 0 else 0.9
    out = DIAL_RADIUS - 0.5
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy * 0.16, ux * 0.16
    a = (DIAL_CENTRE[0] + ux * (out - long), DIAL_CENTRE[1] + uy * (out - long))
    b = (DIAL_CENTRE[0] + ux * out, DIAL_CENTRE[1] + uy * out)
    kit.inlay(
        [
            (a[0] - vx, a[1] - vy),
            (b[0] - vx, b[1] - vy),
            (b[0] + vx, b[1] + vy),
            (a[0] + vx, a[1] + vy),
        ],
        name=f"court_dial_hour_{hour:02d}",
        material="brass",
    )

# --- Court walls -------------------------------------------------------------------------

# The west wall is low, so its shadow keeps to the edge of the court. The east wall is as high
# as the east balcony and backs the gear stair; its face takes the morning sun.
block("wall_west", kit.rect(-22.8, 16, -22, 45), top=1.5)
coping("wall_west_coping", -22.8, 15.4, -22, 45, 1.5)
block("wall_south_west", kit.rect(-22.8, 15.4, -15, 16), top=1.5)
coping("wall_south_west_coping", -21.84, 15.4, -15, 16, 1.5)
block("wall_east", kit.rect(22, 16, 22.8, 45), top=BALCONY)
coping("wall_east_coping", 22, 16, 22.8, 44.92, BALCONY)
block("wall_south_east", kit.rect(15, 15.4, 22.8, 16), top=STEP)
coping("wall_south_east_coping", 15, 15.4, 21.92, 16, STEP)
kit.teeth(
    [(22.8, 45, BALCONY), (22.8, 16, BALCONY)], side="left", name="wall_east_teeth"
)
# Pilasters between the stair gears and a brass string course give the sunlit east wall its
# rhythm. The pilasters keep 0.2 m from the tips of the gear teeth.
for i, y in enumerate((16.6, 21.2, 26.0, 30.8, 35.6, 40.3, 44.4)):
    pilaster(
        f"wall_east_pilaster_{i}",
        kit.rect(21.72, y - 0.3, 22.0, y + 0.3),
        BALCONY,
        foot=0.0,
    )
kit.wall(
    [(22, 16, 3.0), (22, 45, 3.0)],
    height=0.14,
    width=0.05,
    name="wall_east_course",
    material="brass",
    collide=False,
)
# Between the balconies the court ends at the gap round the tower. A bumper throws the marble
# fast, so this edge has a parapet.
parapet("parapet_court_north", [(13, 45, 0), (-13, 45, 0)], 1.2)

# --- Balconies -----------------------------------------------------------------------------

block("balcony_west", kit.rect(-26, 45, -13, 55), top=BALCONY)
block("balcony_east", kit.rect(13, 45, 26, 55), top=BALCONY)
# A spring lands the marble on a balcony from the court, so the far edges have parapets. The
# inner edges have kerbs, with a gap where a carriage stops.
parapet(
    "parapet_balcony_west",
    [(-13, 55, BALCONY), (-26, 55, BALCONY), (-26, 45, BALCONY)],
    1.0,
)
parapet(
    "parapet_balcony_east",
    [(26, 45, BALCONY), (26, 55, BALCONY), (13, 55, BALCONY)],
    1.0,
)
kerb("kerb_balcony_west_south", [(-26, 45, BALCONY), (-22, 45, BALCONY)])
kerb("kerb_balcony_east_south", [(22, 45, BALCONY), (26, 45, BALCONY)])
kerb("kerb_balcony_west_inner_south", [(-13, 45, BALCONY), (-13, 48.6, BALCONY)])
kerb("kerb_balcony_west_inner_north", [(-13, 53, BALCONY), (-13, 55, BALCONY)])
kerb("kerb_balcony_east_inner_south", [(13, 48.6, BALCONY), (13, 45, BALCONY)])
kerb("kerb_balcony_east_inner_north", [(13, 55, BALCONY), (13, 53, BALCONY)])
# A brass gear wheel in the face of each balcony over the court, above the marble's reach,
# and a row of gear teeth under each balcony's edge.
for name, x in (("west", -17.5), ("east", 15.6)):
    kit.gear(
        at=(x, 44.97, 3.6),
        radius=1.5,
        teeth=16,
        depth=0.25,
        name=f"balcony_{name}_gear",
    )
kit.teeth([(-13, 45, BALCONY), (-22, 45, BALCONY)], name="balcony_west_teeth")
kit.teeth([(22, 45, BALCONY), (13, 45, BALCONY)], name="balcony_east_teeth")

# --- Tower and egg ledge -------------------------------------------------------------------

block("tower", kit.rect(-5, 53, 5, 63), top=TOWER)
# Parapets on the tower top where a spring leap lands, with a gap at the south dock for the
# jump up from a carriage. The north edge has kerbs and the north dock's gap: a marble that
# rolls off it drops onto the egg ledge, whose spring brings it back.
parapet("parapet_tower_east", [(2.2, 53, TOWER), (5, 53, TOWER), (5, 63, TOWER)], 1.0)
parapet(
    "parapet_tower_west", [(-5, 63, TOWER), (-5, 53, TOWER), (-2.2, 53, TOWER)], 1.0
)
kerb("kerb_tower_north_east", [(4.6, 63, TOWER), (2.2, 63, TOWER)])
kerb("kerb_tower_north_west", [(-2.2, 63, TOWER), (-4.6, 63, TOWER)])
for name, x, y in (
    ("south_west", -4.2, 53.8),
    ("south_east", 4.2, 53.8),
    ("north_west", -4.2, 62.2),
    ("north_east", 4.2, 62.2),
):
    kit.pillar(at=(x, y, TOWER), radius=0.55, height=2.8, name=f"tower_pinnacle_{name}")
# The back ledge in a niche behind the tower, 3 m below the north dock. Two buttresses close
# the niche at the sides, under the carriage loop, so only a carriage rider sees the ledge.
block("ledge", kit.rect(-4.5, 63, 4.5, 72.2), top=LEDGE)
block("buttress_west", kit.rect(-5.5, 63, -4.5, 72.2), top=STEP)
block("buttress_east", kit.rect(4.5, 63, 5.5, 72.2), top=STEP)
coping("buttress_west_coping", -5.5, 63.08, -4.5, 72.2, STEP)
coping("buttress_east_coping", 4.5, 63.08, 5.5, 72.2, STEP)
# Pilasters on the east and west faces of the tower and a brass string course under its
# parapets. The carriages pass the south and north faces 0.2 m away, so those stay flat.
for side in (-1, 1):
    for i, y in enumerate((53.7, 58.0, 62.3)):
        x0, x1 = sorted((side * 5.0, side * 5.4))
        pilaster(
            f"tower_pilaster_{'west' if side < 0 else 'east'}_{i}",
            kit.rect(x0, y - 0.35, x1, y + 0.35),
            TOWER,
        )
kit.wall(
    [(-5, 53, 6.3), (5, 53, 6.3), (5, 63, 6.3), (-5, 63, 6.3)],
    height=0.14,
    width=0.05,
    side="right",
    closed=True,
    name="tower_course",
    material="brass",
    collide=False,
)
parapet("parapet_ledge", [(4.5, 72.2, LEDGE), (-4.5, 72.2, LEDGE)], 1.0)

# The clock on the tower's south face, seen from the start through the grilles: the brass
# dial of Ascent 1 (assets/decals/dial_tower.png) with gold hands at ten past ten. A hand
# turns from twelve toward three by its angle. The carriages are its other hands.
DIAL = (0.0, 52.98, 3.2)
DIAL_SIZE = 4.6
town.decal("tower_dial", "dial_tower", DIAL, 0.0, (DIAL_SIZE, DIAL_SIZE))
kit.ball((DIAL[0], DIAL[1] - 0.12, DIAL[2]), 0.18, name="tower_dial_hub")
for name, length, turn in (("hour", 1.15, -55.0), ("minute", 1.85, 60.0)):
    hand = kit.lathe(
        at=(DIAL[0], DIAL[1] - 0.08, DIAL[2]),
        profile=[(0.07, 0.0), (0.07, length - 0.3), (0.0, length)],
        name=f"tower_dial_hand_{name}",
        material="gold",
        collide=False,
    )
    hand.rotation_euler = (0.0, math.radians(turn), 0.0)

# A brass line marks each open edge that the marble drops from or steps onto a carriage from.
for name, strip, top in (
    ("edge_step_north", kit.rect(-15, 15.86, 15, 16), STEP),
    ("edge_balcony_west_south", kit.rect(-22, 45, -13, 45.14), BALCONY),
    ("edge_balcony_east_south", kit.rect(13, 45, 22, 45.14), BALCONY),
    ("edge_balcony_west_stop", kit.rect(-13.14, 48.6, -13, 53), BALCONY),
    ("edge_balcony_east_stop", kit.rect(13, 48.6, 13.14, 53), BALCONY),
    ("edge_tower_south_dock", kit.rect(-2.2, 53, 2.2, 53.14), TOWER),
    ("edge_tower_north_dock", kit.rect(-2.2, 62.86, 2.2, 63), TOWER),
):
    kit.inlay(strip, top=top, name=name, material="brass")

# --- Gear stair ----------------------------------------------------------------------------

for i, ((x, y), top) in enumerate(GEARS):
    kit.marker(
        "turning_gear",
        at=(x, y, top),
        name=f"stair_gear_{i}",
        period=10.0,
        clockwise=i % 2 == 1,
        thickness=GEAR_THICKNESS,
    )
    # The brass axle that holds the gear, from the court floor to its underside. The shoulder
    # stays below the neck, so the profile rises all the way on the shortest axle too.
    kit.lathe(
        at=(x, y, 0.0),
        profile=[
            (0.55, 0.0),
            (0.55, 0.25),
            (0.3, min(0.4, top - GEAR_THICKNESS - 0.2)),
            (0.26, top - GEAR_THICKNESS - 0.15),
            (0.4, top - GEAR_THICKNESS),
        ],
        name=f"stair_axle_{i}",
        material="brass",
    )

# --- Objects -------------------------------------------------------------------------------

START = (0.0, 3.0, 0.0)
FINISH = (0.0, 58.4, TOWER)
kit.marker("start", at=START)
kit.marker("finish", at=FINISH)
ring("start_ring", START[:2], 0.62, 0.74, 0.0)
ring("finish_ring", FINISH[:2], 1.3, 1.45, TOWER)

GEMS = {
    "step": (0.0, 12.4, STEP),
    "court_south": (0.0, 23.2, 0.0),
    "court_east": (10.0, 31.0, 0.0),
    "court_north": (0.2, 38.0, 0.0),
    "sky": (-14.8, 41.4, 8.5),
    "balcony_west": (-20.4, 50.8, BALCONY),
    "balcony_east": (21.2, 49.8, BALCONY),
}
for name, at in GEMS.items():
    kit.marker("gem", at=at, name=f"gem_{name}")

SPRINGS = {
    "start": (0.0, 6.6, 0.0),
    "court_west": (-10.2, 30.8, 0.0),
    "court_east": (11.0, 39.4, 0.0),
    "balcony_east": (16.6, 52.8, BALCONY),
    "ledge": (2.4, 70.0, LEDGE),
}
for name, at in SPRINGS.items():
    kit.marker("coil_spring", at=at, name=f"spring_{name}")
    ring(f"spring_ring_{name}", at[:2], 0.5, 0.6, at[2])
# The hands of the court dial: the hour hand points at the west spring, the minute hand at the
# east spring.
dial_hand("court_dial_hand_hour", SPRINGS["court_west"][:2], 6.4)
dial_hand("court_dial_hand_minute", SPRINGS["court_east"][:2], 10.4)

BUMPERS = [
    (0.0, 29.8),
    (-5.6, 25.2),
    (5.6, 25.2),
    (-6.4, 38.2),
    (6.8, 36.8),
    (-16.0, 22.0),
    (12.0, 19.0),
]
for i, at in enumerate(BUMPERS):
    kit.marker("bumper", at=(*at, 0.0), name=f"bumper_{i}")
    ring(f"bumper_ring_{i}", at, 0.78, 0.9, 0.0)

for name, offset in (("a", 0.0), ("b", CARRIAGE_PERIOD / 2)):
    kit.marker(
        "moving_platform",
        at=CARRIAGE_WEST,
        points=CARRIAGE_LOOP,
        name=f"carriage_{name}",
        period=CARRIAGE_PERIOD,
        stop=CARRIAGE_STOP,
        loop=True,
        offset=offset,
        width=CARRIAGE,
        depth=CARRIAGE,
    )

# The Clockwork Egg: on the back ledge behind the tower.
kit.marker("egg", at=(-1.8, 70.0, LEDGE))
# Checkpoint 1 on the Step, on the line from the spring to the drop into the court. 2 and 3
# on the balconies, on the line between the gem and the carriage stop.
kit.marker("checkpoint", at=(0.0, 14.4, STEP), name="checkpoint_step")
kit.marker("checkpoint", at=(-17.4, 50.8, BALCONY), name="checkpoint_balcony_west")
kit.marker("checkpoint", at=(17.6, 50.2, BALCONY), name="checkpoint_balcony_east")

# --- Routes --------------------------------------------------------------------------------

# A route is a list of steps: a point and its actions ("use; speed 6"), or "" for none. A
# `speed` caps the way into its point. The bot keeps its speed in the air, so the speed at a
# `use` point sets the length of the spring's arc: 1.63 s onto a balcony, 1.95 s from a balcony
# to the tower. A carriage's cycle starts at the west stop; it waits there from 0 to 2 s, at the
# south dock from 4.4 to 6.4 s, at the east stop from 8.8 to 10.8 s and at the north dock from
# 18.4 to 20.4 s. The second carriage is half a cycle behind the first.
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


def sky(at: Place) -> Place:
    """Returns the middle of the gem whose marker is at `at`, where the marble meets it."""
    return (at[0], at[1], at[2] + 0.55)


# Both routes start the same: the start spring at a walk, over the Step through its gem, and
# off the north edge of the Step into the court.
STEP_UP: list[Step] = [
    ((0.0, 5.4, 0.0), "speed 3"),
    (SPRINGS["start"], "use; speed 3"),
    (GEMS["step"], ""),
    ((0.0, 15.2, STEP), ""),
]

# First run: the three court gems, the west spring straight up through the sky gem and back
# into the court, the west spring again onto the west balcony. A carriage past the south dock
# to the east balcony and its gem, the next carriage round to the north dock, a jump up to the
# tower.
route(
    "first_run",
    [
        *STEP_UP,
        (GEMS["court_south"], ""),
        (GEMS["court_east"], ""),
        (GEMS["court_north"], ""),
        (SPRINGS["court_west"], ""),
        ((-14.8, 41.4, 0.0), "wait 0; use"),
        (sky(GEMS["sky"]), ""),
        ((-14.8, 41.4, 0.0), ""),
        (SPRINGS["court_west"], ""),
        ((-11.4, 33.4, 0.0), ""),
        ((-15.0, 39.6, 0.0), "use; speed 5"),
        (GEMS["balcony_west"], ""),
        ((-14.2, 50.8, BALCONY), "wait_until carriage_a 27.4 0.6"),
        (CARRIAGE_WEST, "wait_until carriage_a 9.0 10.6"),
        ((14.6, 50.4, BALCONY), ""),
        (GEMS["balcony_east"], ""),
        ((14.2, 50.8, BALCONY), "wait_until carriage_b 8.2 9.2"),
        ((10.8, 50.8, BALCONY), "wait_until carriage_b 18.6 20.2"),
        ((0.0, 63.8, BALCONY), "jump; speed 3"),
        ((0.0, 61.4, TOWER), ""),
        (FINISH, ""),
    ],
)

# Expert: the south court gem and a straight run at the west spring, one arc through the sky
# gem onto the west balcony, back down across the court through the north and east gems to
# the east spring and onto the east balcony, its gem and spring, and a leap over the gap to
# the tower. No carriage.
route(
    "expert",
    [
        *STEP_UP,
        (GEMS["court_south"], ""),
        (SPRINGS["court_west"], "speed 12"),
        ((-11.66, 34.16, 0.0), "use; speed 12"),
        (sky(GEMS["sky"]), ""),
        ((-19.5, 52.1, BALCONY), ""),
        (GEMS["balcony_west"], ""),
        ((-16.6, 46.0, BALCONY), ""),
        (GEMS["court_north"], ""),
        (GEMS["court_east"], ""),
        (SPRINGS["court_east"], ""),
        ((11.8, 40.2, 0.0), "use; speed 6"),
        (GEMS["balcony_east"], ""),
        (SPRINGS["balcony_east"], ""),
        ((15.0, 53.4, BALCONY), "use; speed 6"),
        (FINISH, ""),
    ],
)

# --- Shots ---------------------------------------------------------------------------------

# The sun stands in the north-west, so every shot looks away from it.
kit.shot("overview", at=(-30, 2, 24), rotation=(-30, 0, -46))
kit.shot("start", at=(0, 0.6, 1.6), rotation=(-2, 0, 0))
kit.shot("finish", at=(-11, 70, 13), rotation=(-21, 0, -137))
kit.shot("egg", at=(0.5, 64.5, 7.6), rotation=(-38, 0, 23))
kit.shot("court", at=(-18, 18, 9), rotation=(-22, 0, -50))
kit.shot("gears", at=(6, 20, 4.5), rotation=(-4, 0, -40))
kit.shot("carriage", at=(-20, 48, 9), rotation=(-12, 0, -80))
kit.shot("bumpers", at=(-4, 20.5, 1.6), rotation=(-8, 0, -41))
kit.shot("pad", at=(-1.5, 17.2, 6.6), rotation=(-27, 0, -152))
