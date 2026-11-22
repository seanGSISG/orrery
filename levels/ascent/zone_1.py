"""Ascent 1 Clockmaker's Square (#31): the climb from a town square on the Earth at dawn up
the full height of the clock tower, 0 to 150 m. The brief and the map are
docs/levels/ascent-z1.md and ascent-z1.svg.

The script uses the coordinates of the climb (docs/design/ascent.md §2): x east, y north, z up,
the start pad at height 0. The tower stands on the north side of the square, 12 m square, with
its middle at TOWER. The start pad looks north at it, and the dawn sun stands in the
north-west. The market side (way A) is west of the square, the workshop side (way B) east.

Each section of the tower has a way inside and a way outside:

1. Town, 0 to +26: the market stalls, the bakery, the guildhall roof and the builder's hoist
   (or the crane beam); or the crates, the waterwheel gear, the workshop roof, the second gear,
   the loose planks and the spiral ramp in the tower base. Both reach the gallery.
2. Weight shaft, +26 to +50: the spiral ramp with two pendulums (or the counterweight); or the
   east scaffold with two vents.
3. Gear room, +50 to +80: three flat gears, two lift gears and two spiral ramps; or the three
   vents outside the west door.
4. Clock floor, +80 to +110: three bell weights; or the loose slate slopes outside the east door.
5. Belfry and crown, +110 to +150: the spiral ramp round the great bell to the bell floor, the
   stair fragments, a vent and the bell cradle; or the rafters; or the west hoist.
"""

import math
import random
from collections.abc import Sequence
from itertools import pairwise
from typing import Literal

import kit
from kit import town

Point = tuple[float, float]
Place = tuple[float, float, float]
# A route point and its actions, separated by ";" (route.gd), for example "jump; speed 4".
Leg = tuple[Place, str]

# --- The tower ---------------------------------------------------------------------------------

TOWER = (0.0, 39.0)
OUT = 6.0  # half its width outside
WALL = 0.6
IN = OUT - WALL
X0, X1 = TOWER[0] - OUT, TOWER[0] + OUT
Y0, Y1 = TOWER[1] - OUT, TOWER[1] + OUT
# The floors: the tops of the base, the gallery, the gear room, the clock floor, the belfry,
# the bell floor and the crown.
BASE = 13.9
GALLERY = 26.0
GEAR_ROOM = 50.0
CLOCK_FLOOR = 80.0
BELFRY = 110.0
BELL_FLOOR = 130.0
CROWN = 150.0
SLAB = 0.5
# The spiral ramps: the radii of their inner edge, outer edge and centre line, round TOWER.
R_IN, R_OUT, R_MID = 3.3, 5.3, 4.3
# A spiral ramp climbs this much for each degree: 4.8 m a half turn, 19.6 degrees at R_MID.
CLIMB = 4.8 / 180.0
# A gap in the inner kerb of a spiral ramp, degrees: 1.4 m at R_IN.
GAP = 24.0
# The route points on a spiral ramp: their radius, and the most degrees between two of them.
R_ROUTE, ROUTE_STEP = 4.75, 72.0
# How many degrees before a pendulum the route waits for it.
PENDULUM_WAIT = 45.0


def ring(radius: float, angle: float) -> Point:
    """Returns the plan point at radius and angle (degrees from east) round the tower."""
    a = math.radians(angle)
    return (TOWER[0] + radius * math.cos(a), TOWER[1] + radius * math.sin(a))


def sector(inner: float, outer: float, start: float, end: float) -> list[Point]:
    """Returns the outline of the ring between two radii and two angles round the tower."""
    count = max(2, math.ceil(abs(end - start) / 5.0))
    outer_arc = [
        ring(outer, start + (end - start) * i / count) for i in range(count + 1)
    ]
    inner_arc = [ring(inner, end - (end - start) * i / count) for i in range(count + 1)]
    return outer_arc + inner_arc


def spiral(
    name: str,
    bottom: float,
    start: float,
    turn: float,
    rise: float,
    gaps: Sequence[float] = (),
) -> None:
    """Adds a spiral ramp round the tower with a brass kerb on each edge. gaps: the angles
    (degrees along the ramp from its start) where the inner kerb has a gap of GAP degrees, a
    place to jump from into the middle of the tower."""
    centre = (*TOWER, bottom)
    town.helix(centre, R_IN, R_OUT, start, turn, rise, name=name)
    sign = 1.0 if turn > 0 else -1.0
    cuts = [0.0]
    for along in sorted(gaps):
        cuts += [along - GAP / 2, along + GAP / 2]
    cuts.append(abs(turn))
    for i in range(0, len(cuts), 2):
        town.helix_kerb(
            centre,
            R_IN,
            start,
            turn,
            rise,
            name=f"{name}_kerb_in_{i // 2}",
            span=(start + sign * cuts[i], start + sign * cuts[i + 1]),
        )
    kit.wall(
        [
            town.helix_point(centre, R_OUT, start, turn, rise, a)
            for a in _angles(start, turn)
        ],
        height=0.3,
        width=0.2,
        side="left" if turn > 0 else "right",
        bevel=0.03,
        name=f"{name}_kerb_out",
        material="brass",
    )


def on_spiral(
    bottom: float, start: float, turn: float, rise: float, angle: float
) -> Place:
    """Returns the route point on a spiral() at `angle` degrees. It lies outside the centre
    line, at R_ROUTE, so that a straight leg of up to ROUTE_STEP degrees clears the inner kerb:
    a route has at most 100 points (kit.marker), so a ramp gets few of them."""
    return town.helix_point((*TOWER, bottom), R_ROUTE, start, turn, rise, angle)


def along_spiral(end: float, waits: Sequence[float] = ()) -> list[float]:
    """Returns the angles along a spiral for its route points, from 5 degrees to `end`, at most
    ROUTE_STEP apart, with a point at each angle of `waits`."""
    marks = sorted({*waits, end})
    angles = [5.0]
    for mark in marks:
        count = math.ceil((mark - angles[-1]) / ROUTE_STEP)
        angles += [
            angles[-1] + (mark - angles[-1]) * (i + 1) / count for i in range(count)
        ]
    return angles


def _angles(start: float, turn: float) -> list[float]:
    count = max(1, math.ceil(abs(turn) / 5.0))
    return [start + turn * i / count for i in range(count + 1)]


def floor(name: str, top: float, holes: Sequence[Sequence[Point]] = ()) -> None:
    """Adds a floor slab inside the tower walls."""
    town.floor(name, kit.rect(X0, Y0, X1, Y1), top, SLAB, holes)


def storey(
    name: str,
    bottom: float,
    top: float,
    south: Sequence[town.Opening] = (),
    east: Sequence[town.Opening] = (),
    north: Sequence[town.Opening] = (),
    west: Sequence[town.Opening] = (),
) -> None:
    """Adds the four walls of the tower from bottom to top, each with its openings, measured
    along the wall: the south wall from its west end, the east wall from its south end, the
    north wall from its east end, the west wall from its north end."""
    corners = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    for i, (side, openings) in enumerate(
        (("south", south), ("east", east), ("north", north), ("west", west))
    ):
        town.facade(
            f"{name}_{side}",
            corners[i],
            corners[(i + 1) % 4],
            bottom,
            top,
            WALL,
            openings,
            side="left",
        )


def door(
    along: float, bottom: float, width: float = 2.4, height: float = 3.2
) -> town.Opening:
    """Returns a door opening on a tower wall."""
    return (along, width, bottom, bottom + height)


# --- Routes -------------------------------------------------------------------------------------

# The legs of each section: the first-run route and the expert route. Each leg starts where
# the last one ended.
FIRST: dict[int, list[Leg]] = {}
EXPERT: dict[int, list[Leg]] = {}
# The foot of each section above the town: the floor point where the routes of the section
# below end and its own routes start.
FOOT: dict[int, Place] = {}


kit.level(title="Clockmaker's Square", par=263.2, gold=119.7, sky="ground_dawn")

# --- The town ground ----------------------------------------------------------------------------

kit.deck(kit.rect(-60, -30, 60, 80), top=0.0, depth=1.0, name="ground")
# The square: a brass band round its edge.
SQUARE = kit.rect(-17, 0, 17, 32)
kit.inlay(
    SQUARE,
    holes=[kit.rect(-16.75, 0.25, 16.75, 31.75)],
    name="square_band",
    material="brass",
)
START: Place = (0.0, 23.5, 0.0)

# The fountain in the middle of the square, 4 m across: a low stone basin of still water, and
# in it the hero prop (2 m across) raised as the upper tier, with still water in its own basin.
# The rim and the prop's cylinder keep the marble out.
FOUNTAIN = (0.0, 15.0)
BASIN_R, BASIN_RIM, BASIN_TOP = 2.0, 0.22, 0.55
TIER = 0.3
town.floor(
    "fountain_rim",
    kit.arc(FOUNTAIN, BASIN_R, 0, 360),
    BASIN_TOP,
    BASIN_TOP,
    holes=[kit.arc(FOUNTAIN, BASIN_R - BASIN_RIM, 0, 360)],
    finish="dressed",
)
town.floor("fountain_floor", kit.arc(FOUNTAIN, BASIN_R - BASIN_RIM, 0, 360), 0.1, 0.1)
kit.prop("fountain", at=(*FOUNTAIN, TIER), collider="cylinder")
water = town.Parts()
water.solid(kit.arc(FOUNTAIN, BASIN_R - BASIN_RIM, 0, 360), 0.42, 0.44, "glass")
water.solid(kit.arc(FOUNTAIN, 0.86, 0, 360), 0.55 + TIER, 0.62 + TIER, "glass")
water.add("fountain_water", collide=False)

# --- 1. Town: the market side (way A) -----------------------------------------------------------

# Three stalls rise westward to the bakery: tables and booths whose boards are steps of 1 m.
STALL_Y = (9.5, 12.5)
town.stall("stall_1", (-10.5, STALL_Y[0]), (-7.5, STALL_Y[1]), 1.0, "canvas_cream")
town.stall("stall_2", (-14.0, STALL_Y[0]), (-11.0, STALL_Y[1]), 2.0, "canvas_ochre")
town.stall("stall_3", (-17.5, STALL_Y[0]), (-14.5, STALL_Y[1]), 3.0, "canvas_red")

# The bakery: a flat roof at +4 with a parapet on three sides; its chimney vent throws the
# marble north onto the guildhall roof.
BAKERY = (-25.0, 6.0, -18.0, 18.0)
BAKERY_TOP = 4.0
bx0, by0, bx1, by1 = BAKERY
town.block("bakery", (bx0, by0, 0.0), (bx1, by1, BAKERY_TOP))
kit.wall(
    [(bx1, by0, BAKERY_TOP), (bx0, by0, BAKERY_TOP), (bx0, by1, BAKERY_TOP)],
    height=0.9,
    width=0.35,
    side="right",
    name="bakery_parapet",
)
CHIMNEY_VENT = (-23.4, 17.0)
kit.marker("steam_vent", at=(*CHIMNEY_VENT, BAKERY_TOP), lift=9.0, name="vent_bakery")
town.chimney("bakery_chimney", (-20.2, 17.3, BAKERY_TOP), 1.0, 1.6)

# The guildhall: a hall with a roof that slopes up westward at 31.6 degrees from its east eave
# (+10) to a ridge walk (+14), and a north block with a flat terrace at +14.
GUILD = (-31.0, 20.0, -21.5, 40.0)
gx0, gy0, gx1, gy1 = GUILD
EAVE, RIDGE = 10.0, 14.0
RIDGE_X = (-30.8, -28.0)
TERRACE_Y = 33.0
# The hall walls, with a door to the square in the east wall.
for name, a, b, openings in (
    ("south", (gx0, gy0), (gx1, gy0), ()),
    ("east", (gx1, gy0), (gx1, TERRACE_Y), [(5.5, 2.4, 0.0, 3.0)]),
    ("west", (gx0, TERRACE_Y), (gx0, gy0), ()),
):
    town.facade(f"guildhall_{name}", a, b, 0.0, EAVE, 0.5, openings, side="left")
# The roof: the slope, the ridge walk and the west parapet.
kit.ramp(
    at=(gx1 + 0.0, (gy0 + TERRACE_Y) / 2, EAVE),
    width=TERRACE_Y - gy0,
    length=gx1 - RIDGE_X[1],
    rise=RIDGE - EAVE,
    yaw=90,
    fill=True,
    name="guildhall_roof",
    trim="",
)
FLUE = 1.3
DRY_CHIMNEY = (-29.4, 22.4)
town.floor(
    "guildhall_ridge",
    kit.rect(gx0, gy0, RIDGE_X[1], TERRACE_Y),
    RIDGE,
    RIDGE - EAVE + 0.5,
    holes=[
        kit.rect(
            DRY_CHIMNEY[0] - FLUE / 2,
            DRY_CHIMNEY[1] - FLUE / 2,
            DRY_CHIMNEY[0] + FLUE / 2,
            DRY_CHIMNEY[1] + FLUE / 2,
        )
    ],
)
# A brass gutter along the eave catches a marble that rolls back down the roof.
kit.wall(
    [(gx1, gy0, EAVE), (gx1, TERRACE_Y, EAVE)],
    height=0.4,
    width=0.25,
    side="left",
    bevel=0.03,
    name="guildhall_gutter",
    material="brass",
)
town.block(
    "guildhall_ridge_parapet", (gx0, gy0, RIDGE), (gx0 + 0.35, TERRACE_Y, RIDGE + 0.9)
)
# The north block and its terrace.
town.block("guildhall_north", (gx0, TERRACE_Y, 0.0), (gx1, gy1, RIDGE))
kit.wall(
    [
        (gx0, TERRACE_Y, RIDGE),
        (gx0, gy1, RIDGE),
        (gx1, gy1, RIDGE),
        (gx1, TERRACE_Y, RIDGE),
        (RIDGE_X[1], TERRACE_Y, RIDGE),
    ],
    height=0.9,
    width=0.35,
    side="right",
    name="guildhall_terrace_parapet",
)
# The ridge vent and its chimney; the dry chimney at the south end of the ridge walk.
RIDGE_VENT = (-28.4, 35.4)
kit.marker("steam_vent", at=(*RIDGE_VENT, RIDGE), lift=8.2, name="vent_ridge")
town.chimney("guildhall_chimney", (-30.2, 37.4, RIDGE), 1.0, 1.8)
town.chimney("guildhall_dry_chimney", (*DRY_CHIMNEY, RIDGE), 2.0, 0.7, flue=FLUE)
# The flue goes down to the hearth in the hall, where the egg is.
town.chimney("guildhall_flue", (*DRY_CHIMNEY, 1.2), 2.0, EAVE - 0.5 - 1.2, flue=FLUE)
town.block(
    "hearth_back",
    (DRY_CHIMNEY[0] - 1.0, DRY_CHIMNEY[1] - 1.0, 0.0),
    (DRY_CHIMNEY[0] - 0.65, DRY_CHIMNEY[1] + 1.0, 1.2),
)
# The hearth's cheeks stand flush with the flue walls, so the hearth is as wide as the flue
# and holds no ledge for a marble that drops in.
for side in (-1, 1):
    near, far = DRY_CHIMNEY[1] + side * FLUE / 2, DRY_CHIMNEY[1] + side * 1.0
    town.block(
        f"hearth_cheek_{(side + 1) // 2}",
        (DRY_CHIMNEY[0] - 1.0, min(near, far), 0.0),
        (DRY_CHIMNEY[0] + 1.0, max(near, far), 1.2),
    )
EGG: Place = (DRY_CHIMNEY[0] + 2.2, DRY_CHIMNEY[1], 0.0)
kit.marker("egg", at=EGG)

# The builder's crane: a beam from above the terrace to the gallery landing of the tower.
BEAM_Y = RIDGE_VENT[1]
BEAM_LOW = (-26.0, 21.2)
# The beam ends flush with the west edge of the gallery landing, so it makes no step.
LANDING_X = -9.0
BEAM_HIGH = (LANDING_X, GALLERY)
HEEL = 1.8
kit.track(
    at=(BEAM_LOW[0], BEAM_Y, BEAM_LOW[1]),
    width=0.8,
    length=HEEL,
    yaw=-90,
    name="crane_heel",
    material="brass",
    trim="gold",
)
kit.ramp(
    at=(BEAM_LOW[0] + HEEL, BEAM_Y, BEAM_LOW[1]),
    width=0.8,
    length=BEAM_HIGH[0] - BEAM_LOW[0] - HEEL,
    rise=BEAM_HIGH[1] - BEAM_LOW[1],
    yaw=-90,
    name="crane_beam",
    material="brass",
    trim="gold",
)
town.block(
    "crane_mast",
    (BEAM_LOW[0] + 0.7, BEAM_Y - 0.2, RIDGE),
    (BEAM_LOW[0] + 1.1, BEAM_Y + 0.2, BEAM_LOW[1] - 0.5),
    "iron",
)

# The builder's hoist: a deck from above the terrace to the gallery landing, 12 s a cycle.
HOIST_Y = 38.0
HOIST_LOW: Place = (-25.0, HOIST_Y, 19.8)
HOIST_HIGH: Place = (-10.5, HOIST_Y, GALLERY)
kit.marker(
    "moving_platform",
    at=HOIST_LOW,
    points=[HOIST_HIGH],
    period=12.0,
    stop=2.0,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="hoist",
)

# The gallery landing on the west face of the tower, with a parapet but where the hoist and the
# crane beam come.
LANDING = (LANDING_X, 33.6, X0, 40.4)
lx0, ly0, lx1, ly1 = LANDING
town.block("gallery_landing", (lx0, ly0, GALLERY - 1.0), (lx1, ly1, GALLERY))
for name, path in (
    (
        "south",
        [(lx1, ly0, GALLERY), (lx0, ly0, GALLERY), (lx0, BEAM_Y - 0.6, GALLERY)],
    ),
    (
        "north",
        [(lx0, HOIST_Y + 1.6, GALLERY), (lx0, ly1, GALLERY), (lx1, ly1, GALLERY)],
    ),
):
    kit.wall(path, height=1.0, width=0.3, side="right", name=f"gallery_landing_{name}")

# --- 1. Town: the workshop side (way B) ---------------------------------------------------------

# Two crates, +1 and +2, then the balcony on the south face of the workshop.
town.crate("crate_1", (7.5, 7.6, 0.0), (10.5, 10.4, 1.0))
town.crate("crate_2", (11.0, 7.6, 0.0), (14.0, 10.4, 1.0))
town.crate("crate_3", (11.15, 7.75, 1.0), (13.85, 10.25, 2.0))
# The second gear lifts from the workshop roof to the planks at the base top. Its axis is set
# so that its exit is level with BASE; the workshop roof is its boarding floor.
GEAR_2 = town.lift(
    "gear_town_2",
    (10.6, 36.5, BASE - 2.7 + 0.45),
    2.7,
    yaw=90,
    exit=1,
    period=10.0,
    teeth=10,
)
ROOF = GEAR_2.floor
# The waterwheel gear lifts from the balcony to the workshop roof.
WHEEL = town.lift(
    "gear_town_1", (25.6, 9.25, ROOF - 3.1 + 0.45), 3.1, yaw=0, exit=1, period=12.0
)
BALCONY = WHEEL.floor
WORKSHOP = (14.5, 10.0, 22.5, 28.0)
wx0, wy0, wx1, wy1 = WORKSHOP
town.block("workshop", (wx0, wy0, 0.0), (wx1, wy1, ROOF))
# The roof's parapet has a gap at the wheel's exit (south-east) and at the walk to the
# second gear (north-west).
kit.wall(
    [(wx1, wy0, ROOF), (wx0, wy0, ROOF), (wx0, wy1 - 2.0, ROOF)],
    height=0.9,
    width=0.35,
    side="right",
    name="workshop_parapet_sw",
)
kit.wall(
    [(wx0, wy1, ROOF), (wx1, wy1, ROOF), (wx1, wy0 + 2.6, ROOF)],
    height=0.9,
    width=0.35,
    side="right",
    name="workshop_parapet_ne",
)
town.block("balcony", (wx0, 7.5, BALCONY - 0.4), (21.4, wy0, BALCONY))
kit.wall(
    [(wx0 + 0.2, 7.5, BALCONY), (21.4, 7.5, BALCONY)],
    height=0.9,
    width=0.25,
    side="left",
    name="balcony_rail",
)
town.block(
    "wheel_lane", (21.4, 9.25 - 0.62, BALCONY - 0.4), (25.6, 9.25 + 0.62, BALCONY)
)
# The wheel's exit deck joins the roof at its south-east corner.
town.block("wheel_exit", (wx1, 9.9, ROOF - 0.4), (27.0, 12.6, ROOF))
# From the roof's north-west corner a walk leads to the second gear's lane.
town.block("gear_walk", (9.5, wy1 - 2.0, ROOF - 0.4), (wx0 + 0.01, wy1, ROOF))
town.block("gear_lane", (9.5, wy1, ROOF - 0.4), (11.7, 34.6, ROOF))
town.block("gear_lane_slot", (10.6 - 0.62, 34.6, ROOF - 0.4), (10.6 + 0.62, 36.5, ROOF))
kit.wall(
    [(9.5, wy1 - 2.0, ROOF), (9.5, 34.6, ROOF)],
    height=0.9,
    width=0.25,
    side="right",
    name="gear_walk_rail",
)
# The second gear lets the marble off west onto a ledge, then the loose planks to the door.
town.block("planks_ledge", (7.6, 35.3, BASE - 0.4), (10.6 - 0.66, 37.7, BASE))
kit.marker(
    "crumbling_tiles",
    at=(6.8, 36.5, BASE),
    width=1.6,
    depth=2.4,
    tile=0.8,
    name="planks",
)

# --- The tower base and the gallery ------------------------------------------------------------

kit.deck(kit.rect(X0, Y0, X1, Y1), top=BASE, depth=BASE + 1.0, name="tower_base")
EAST_DOOR_Y = 36.5
storey("tower_a", BASE, GALLERY - SLAB, east=[door(EAST_DOOR_Y - Y0, BASE)])
# The base ramp: from beside the east door up to the gallery, 2.5 half turns. It starts north
# of the door, so it passes the door well above its head.
BASE_START = 0.0
BASE_TURN = (GALLERY - BASE) / CLIMB
spiral("ramp_base", BASE, BASE_START, BASE_TURN, GALLERY - BASE)
BASE_END = BASE_START + BASE_TURN
floor("gallery", GALLERY, [sector(R_IN - 0.1, R_OUT + 0.15, BASE_END - 90.0, BASE_END)])
FOOT[2] = (*ring(1.5, 180.0), GALLERY)

# --- 2. Weight shaft ----------------------------------------------------------------------------

storey(
    "tower_b",
    GALLERY,
    GEAR_ROOM - SLAB,
    south=[door(9.6, GALLERY)],
    west=[(Y1 - 37.0, 5.6, GALLERY, GALLERY + 3.6)],
)
# The shaft ramp turns clockwise from the north-west, 5 half turns, so it passes over the
# west opening and the south door well above their heads.
SHAFT_START = 165.0
SHAFT_TURN = -(GEAR_ROOM - GALLERY) / CLIMB
spiral(
    "ramp_shaft", GALLERY, SHAFT_START, SHAFT_TURN, GEAR_ROOM - GALLERY, gaps=[180.0]
)
SHAFT_END = SHAFT_START + SHAFT_TURN


def shaft(angle: float) -> Place:
    """Returns the point on the shaft ramp `angle` degrees along it from its start."""
    return on_spiral(
        GALLERY, SHAFT_START, SHAFT_TURN, GEAR_ROOM - GALLERY, SHAFT_START - angle
    )


# The counterweight in the middle of the shaft.
COUNTER_LOW = GALLERY + 4.6
COUNTER_HIGH = GALLERY + 21.0
kit.marker(
    "moving_platform",
    at=(*TOWER, COUNTER_LOW),
    points=[(*TOWER, COUNTER_HIGH)],
    period=8.0,
    stop=1.0,
    width=2.4,
    depth=2.4,
    finish="wood",
    name="counterweight",
)
# Two pendulums hang from the ramp above and swing along the ramp.
PENDULUMS = {"pendulum_1": 300.0, "pendulum_2": 620.0}
for name, along in PENDULUMS.items():
    x, y, z = shaft(along)
    angle = SHAFT_START - along
    kit.marker(
        "pendulum",
        at=(x, y, z + 4.6),
        rotation=(0, 0, angle - 90.0),
        period=4.0,
        swing=40.0,
        name=name,
    )
floor(
    "gear_room",
    GEAR_ROOM,
    [sector(R_IN - 0.1, R_OUT + 0.15, SHAFT_END, SHAFT_END + 90.0)],
)

# The east scaffold, outside the gallery's south door: steps east to a vent, a deck with a
# bumper, steps back west to a second vent, and the balcony at the gear room's east door.
SCAFFOLD_Y = (30.4, 33.0)
town.block("scaffold_balcony", (1.5, SCAFFOLD_Y[0], GALLERY - 0.4), (6.8, Y0, GALLERY))
SCAFFOLD_STEPS = [(7.1, 9.4), (9.7, 12.0), (12.3, 14.6), (14.9, 18.6)]
for i, (x0, x1) in enumerate(SCAFFOLD_STEPS):
    town.block(
        f"scaffold_step_{i + 1}",
        (x0, SCAFFOLD_Y[0], GALLERY + 0.6 + i),
        (x1, SCAFFOLD_Y[1], GALLERY + 1.0 + i),
    )
SCAFFOLD_VENT_1 = (17.6, (SCAFFOLD_Y[0] + SCAFFOLD_Y[1]) / 2)
kit.marker(
    "steam_vent", at=(*SCAFFOLD_VENT_1, GALLERY + 4.0), lift=8.6, name="vent_scaffold_1"
)
SCAFFOLD_DECK = (19.8, 29.4, 24.6, 34.0, 37.0)
sx0, sy0, sx1, sy1, sz = SCAFFOLD_DECK
town.block("scaffold_deck", (sx0, sy0, sz - 0.4), (sx1, sy1, sz))
kit.marker("bumper", at=(23.8, 30.3, sz), name="bumper_scaffold_1")
SCAFFOLD_ROW_2 = (34.3, 36.6)
SCAFFOLD_STEPS_2 = [(19.8, 22.6), (16.9, 19.5), (12.6, 16.6)]
for i, (x0, x1) in enumerate(SCAFFOLD_STEPS_2):
    town.block(
        f"scaffold_step_{i + 5}",
        (x0, SCAFFOLD_ROW_2[0], sz + 0.6 + i),
        (x1, SCAFFOLD_ROW_2[1], sz + 1.0 + i),
    )
SCAFFOLD_VENT_2 = (13.6, (SCAFFOLD_ROW_2[0] + SCAFFOLD_ROW_2[1]) / 2)
kit.marker(
    "steam_vent", at=(*SCAFFOLD_VENT_2, sz + 3.0), lift=11.2, name="vent_scaffold_2"
)
town.block("gear_east_balcony", (X1, 33.6, GEAR_ROOM - 0.4), (10.0, 37.6, GEAR_ROOM))
kit.marker("bumper", at=(9.4, 37.0, GEAR_ROOM), name="bumper_scaffold_2")
# Iron stays hang the scaffold from the tower: from the outer corners of each deck and step up
# to the tower wall, 8 m higher. They do not collide.
stays = town.Parts()
for x0, y0, x1, y1, z in (
    *(
        (x0, SCAFFOLD_Y[0], x1, SCAFFOLD_Y[1], GALLERY + 0.6 + i)
        for i, (x0, x1) in enumerate(SCAFFOLD_STEPS)
    ),
    (sx0, sy0, sx1, sy1, sz - 0.4),
    *(
        (x0, SCAFFOLD_ROW_2[0], x1, SCAFFOLD_ROW_2[1], sz + 0.6 + i)
        for i, (x0, x1) in enumerate(SCAFFOLD_STEPS_2)
    ),
    (X1, 33.6, 10.0, 37.6, GEAR_ROOM - 0.4),
):
    anchor_y = min(max((y0 + y1) / 2, Y0 + 0.5), Y1 - 0.5)
    for corner in ((x1 - 0.1, y0 + 0.1), (x1 - 0.1, y1 - 0.1)):
        stays.bar((*corner, z), (X1 + 0.05, anchor_y, z + 8.0), 0.09, "iron")
stays.add("scaffold_stays", collide=False)

# --- 3. Gear room -------------------------------------------------------------------------------

WEST_DOOR = Y1 - TOWER[1]
GEAR_EAST_DOOR_Y = 35.5
storey(
    "tower_c",
    GEAR_ROOM,
    CLOCK_FLOOR - SLAB,
    east=[door(GEAR_EAST_DOOR_Y - Y0, GEAR_ROOM)],
    west=[door(WEST_DOOR, GEAR_ROOM)],
)
# Three flat gears are steps of 1 m from the floor to a ledge in the south-west corner.
FLAT_GEARS = {
    "gear_flat_1": (1.6, 35.2, 51.0),
    "gear_flat_2": (-0.9, 35.2, 52.0),
    "gear_flat_3": (-3.9, 35.0, 53.0),
}
for i, (name, (x, y, top)) in enumerate(FLAT_GEARS.items()):
    kit.marker(
        "turning_gear",
        at=(x, y, top),
        period=8.0,
        clockwise=i % 2 == 1,
        radius=1.2,
        teeth=10,
        name=name,
    )
    town.block(
        f"{name}_axle",
        (x - 0.15, y - 0.15, GEAR_ROOM),
        (x + 0.15, y + 0.15, top - 0.5),
        "iron",
    )
LIFT_1_FLOOR = 54.0
# Lift gear 1 stands across x by the west wall and lets the marble off east, at the top, into
# the lane of lift gear 2.
LIFT_1 = town.lift(
    "gear_lift_1",
    (-3.9, 40.0, LIFT_1_FLOOR + 3.6 + town.LIFT_GAP),
    3.6,
    yaw=90,
    exit=-1,
)
town.block(
    "gear_lift_1_lane",
    (-3.9 - 0.62, 36.8, LIFT_1_FLOOR - 0.3),
    (-3.9 + 0.62, 40.0, LIFT_1_FLOOR),
)
LIFT_2 = town.lift(
    "gear_lift_2", (0.5, 40.0, LIFT_1.exit + 3.6 + town.LIFT_GAP), 3.6, yaw=0, exit=-1
)
town.block(
    "gear_lift_2_lane",
    (-1.5, 40.0 - 0.62, LIFT_1.exit - 0.3),
    (0.5, 40.0 + 0.62, LIFT_1.exit),
)
# Where lift gear 1 lets the marble off, the lane is wider than the gear's window.
town.block(
    "gear_lift_1_exit",
    (-3.9 + 0.65, 40.0 - 1.2, LIFT_1.exit - 0.3),
    (-1.5, 40.0 + 1.2, LIFT_1.exit),
)
# Lift gear 2 lets the marble off south onto a deck, and two spiral ramps climb clockwise from
# the west to the clock floor, with a level landing between them.
town.block(
    "gear_lift_2_deck", (X0 + WALL, 36.2, LIFT_2.exit - 0.3), (2.0, 39.15, LIFT_2.exit)
)
GEAR_RISE = (CLOCK_FLOOR - LIFT_2.exit) / 2
GEAR_TURN = -225.0
GEAR_RAMP_1 = 180.0
GEAR_RAMP_2 = GEAR_RAMP_1 + GEAR_TURN - 30.0
spiral("ramp_gears_1", LIFT_2.exit, GEAR_RAMP_1, GEAR_TURN, GEAR_RISE)
town.floor(
    "ramp_gears_landing",
    sector(R_IN, R_OUT, GEAR_RAMP_2, GEAR_RAMP_2 + 30.0),
    LIFT_2.exit + GEAR_RISE,
    SLAB,
)
spiral("ramp_gears_2", LIFT_2.exit + GEAR_RISE, GEAR_RAMP_2, GEAR_TURN, GEAR_RISE)
GEAR_RAMP_END = GEAR_RAMP_2 + GEAR_TURN


def gear_ramp(ramp: int, along: float) -> Place:
    """Returns the point on gear ramp 1 or 2, `along` degrees from its start."""
    start = GEAR_RAMP_1 if ramp == 1 else GEAR_RAMP_2
    bottom = LIFT_2.exit + (ramp - 1) * GEAR_RISE
    return on_spiral(bottom, start, GEAR_TURN, GEAR_RISE, start - along)


# Outside the west door: three vents in a line, each on the near end of a ledge, and five steps
# back to a balcony at the clock floor's west door.
VENT_Y = TOWER[1]
town.block(
    "gear_west_balcony",
    (X0 - 3.2, VENT_Y - 2.0, GEAR_ROOM - 0.4),
    (X0, VENT_Y + 2.0, GEAR_ROOM),
)
WEST_VENTS = {
    "vent_west_1": (-8.2, GEAR_ROOM),
    "vent_west_2": (-11.7, 58.0),
    "vent_west_3": (-15.2, 66.0),
}
for name, (x, z) in WEST_VENTS.items():
    kit.marker("steam_vent", at=(x, VENT_Y, z), lift=9.5, name=name)
for i, (x0, x1, z) in enumerate(
    ((-16.0, -10.6, 58.0), (-19.5, -14.1, 66.0), (-23.0, -17.6, 74.0))
):
    town.block(
        f"gear_west_ledge_{i + 1}", (x0, VENT_Y - 1.5, z - 0.5), (x1, VENT_Y + 1.5, z)
    )
# Each step is 1 m higher than the one before; the gaps of 0.3 m are narrower than the marble.
WEST_STEPS = [(-21.6 + 2.6 * i, -19.3 + 2.6 * i) for i in range(5)]
STEP_Y = (40.8, 43.0)
for i, (x0, x1) in enumerate(WEST_STEPS):
    town.block(
        f"gear_west_step_{i + 1}", (x0, STEP_Y[0], 74.5 + i), (x1, STEP_Y[1], 75.0 + i)
    )
town.block(
    "clock_west_balcony", (-8.6, 37.0, CLOCK_FLOOR - 0.4), (X0, STEP_Y[1], CLOCK_FLOOR)
)
FOOT[4] = (0.5, 41.0, CLOCK_FLOOR)

# --- 4. Clock floor -----------------------------------------------------------------------------

CLOCK_EAST_DOOR_Y = 42.5
BELL_X = 3.3
floor(
    "clock_floor",
    CLOCK_FLOOR,
    [
        sector(R_IN - 0.1, R_OUT + 0.15, GEAR_RAMP_END, GEAR_RAMP_END + 90.0),
        kit.rect(BELL_X - 1.6, TOWER[1] - 1.6, BELL_X + 1.6, TOWER[1] + 1.6),
    ],
)
storey(
    "tower_d",
    CLOCK_FLOOR,
    BELFRY - SLAB,
    east=[door(CLOCK_EAST_DOOR_Y - Y0, CLOCK_FLOOR)],
    west=[door(WEST_DOOR, CLOCK_FLOOR)],
)
# The clock: a dial on each face, no numerals. The hands show six o'clock: dawn.
DIAL_Z, DIAL_R = 95.0, 4.5
for name, at, yaw in (
    ("south", (TOWER[0], Y0, DIAL_Z), 0.0),
    ("east", (X1, TOWER[1], DIAL_Z), 90.0),
    ("north", (TOWER[0], Y1, DIAL_Z), 180.0),
    ("west", (X0, TOWER[1], DIAL_Z), -90.0),
):
    town.clock_face(f"clock_dial_{name}", at, yaw, DIAL_R, art="dial_tower")
# Three bell weights rise 10 m each, east, west and east, with a ledge between them.
BELL_WEIGHTS = {
    "bell_weight_1": (BELL_X, CLOCK_FLOOR, 0.0),
    "bell_weight_2": (-BELL_X, CLOCK_FLOOR + 10.0, 5.0),
    "bell_weight_3": (BELL_X, CLOCK_FLOOR + 20.0, 10.0),
}
for name, (x, z, offset) in BELL_WEIGHTS.items():
    kit.marker(
        "moving_platform",
        at=(x, TOWER[1], z),
        points=[(x, TOWER[1], z + 10.0)],
        period=12.0,
        stop=2.0,
        offset=offset,
        width=3.0,
        depth=3.0,
        finish="wood",
        name=name,
    )
for i, z in enumerate((CLOCK_FLOOR + 10.0, CLOCK_FLOOR + 20.0)):
    town.block(
        f"bell_ledge_{i + 1}",
        (-1.65, TOWER[1] - 1.5, z - 0.4),
        (1.65, TOWER[1] + 1.5, z),
    )
# Outside the east door: a loose slate slope up to a landing with a vent and a bumper, a ledge,
# a second loose slope west, a vent to a ledge north of the tower, and two steps to the belfry.
SLATE_Y = CLOCK_EAST_DOOR_Y
town.block(
    "clock_east_balcony",
    (X1, SLATE_Y - 2.0, CLOCK_FLOOR - 0.4),
    (9.0, SLATE_Y + 2.0, CLOCK_FLOOR),
)
SLOPE_1, SLOPE_1_ANGLE = 12.0, 31.0
s1 = math.radians(SLOPE_1_ANGLE)
SLOPE_1_TOP = (9.0 + SLOPE_1 * math.cos(s1), CLOCK_FLOOR + SLOPE_1 * math.sin(s1))
kit.marker(
    "crumbling_tiles",
    at=((9.0 + SLOPE_1_TOP[0]) / 2, SLATE_Y, (CLOCK_FLOOR + SLOPE_1_TOP[1]) / 2),
    rotation=(SLOPE_1_ANGLE, 0.0, -90.0),
    width=3.0,
    depth=SLOPE_1,
    tile=1.5,
    name="slates_1",
)
town.block(
    "slate_landing_1",
    (SLOPE_1_TOP[0], SLATE_Y - 2.5, SLOPE_1_TOP[1] - 0.5),
    (25.6, SLATE_Y + 2.5, SLOPE_1_TOP[1]),
)
SLATE_VENT_1 = (22.6, 44.0)
kit.marker(
    "steam_vent", at=(*SLATE_VENT_1, SLOPE_1_TOP[1]), lift=9.3, name="vent_slate_1"
)
kit.marker("bumper", at=(25.0, SLATE_Y - 1.6, SLOPE_1_TOP[1]), name="bumper_slate")
LEDGE_94 = 94.0
SLATE_ROW = 49.0
town.block("slate_ledge_94", (20.1, 46.6, LEDGE_94 - 0.5), (25.1, 51.0, LEDGE_94))
SLOPE_2, SLOPE_2_ANGLE = 10.5, 29.6
s2 = math.radians(SLOPE_2_ANGLE)
SLOPE_2_TOP = (20.1 - SLOPE_2 * math.cos(s2), LEDGE_94 + SLOPE_2 * math.sin(s2))
kit.marker(
    "crumbling_tiles",
    at=((20.1 + SLOPE_2_TOP[0]) / 2, SLATE_ROW, (LEDGE_94 + SLOPE_2_TOP[1]) / 2),
    rotation=(SLOPE_2_ANGLE, 0.0, 90.0),
    width=3.0,
    depth=SLOPE_2,
    tile=1.5,
    name="slates_2",
)
town.block(
    "slate_landing_2",
    (7.0, SLATE_ROW - 1.5, SLOPE_2_TOP[1] - 0.5),
    (SLOPE_2_TOP[0], SLATE_ROW + 1.5, SLOPE_2_TOP[1]),
)
SLATE_VENT_2 = (8.5, SLATE_ROW)
kit.marker(
    "steam_vent", at=(*SLATE_VENT_2, SLOPE_2_TOP[1]), lift=9.2, name="vent_slate_2"
)
town.block(
    "slate_ledge_107", (1.0, SLATE_ROW - 1.5, 106.5), (6.1, SLATE_ROW + 1.5, 107.0)
)
for i, (x0, x1) in enumerate(((-1.4, 0.7), (-3.9, -1.7))):
    town.block(
        f"slate_step_{i + 1}",
        (x0, SLATE_ROW - 1.5, 107.5 + i),
        (x1, SLATE_ROW + 1.5, 108.0 + i),
    )
NORTH_DOOR_X = -2.8
town.block(
    "belfry_bridge",
    (NORTH_DOOR_X - 1.5, Y1, BELFRY - 0.4),
    (NORTH_DOOR_X + 1.5, SLATE_ROW - 1.8, BELFRY),
)
FOOT[5] = (0.5, 39.0, BELFRY)

# --- 5. Belfry and crown ------------------------------------------------------------------------

floor(
    "belfry",
    BELFRY,
    [kit.rect(BELL_X - 1.6, TOWER[1] - 1.6, BELL_X + 1.6, TOWER[1] + 1.6)],
)
storey(
    "tower_e",
    BELFRY,
    BELL_FLOOR - SLAB,
    north=[door(X1 - NORTH_DOOR_X, BELFRY, 2.6)],
    west=[door(WEST_DOOR, BELFRY)],
)
BELFRY_START = 260.0
BELFRY_TURN = (BELL_FLOOR - BELFRY) / CLIMB
spiral("ramp_belfry", BELFRY, BELFRY_START, BELFRY_TURN, BELL_FLOOR - BELFRY)
BELFRY_END = BELFRY_START + BELFRY_TURN


def belfry(along: float) -> Place:
    """Returns the point on the belfry ramp `along` degrees from its start."""
    return on_spiral(
        BELFRY, BELFRY_START, BELFRY_TURN, BELL_FLOOR - BELFRY, BELFRY_START + along
    )


# The great bell hangs still in the middle; its clapper is a long pendulum over the ramp.
kit.lathe(
    (*TOWER, BELL_FLOOR - 9.0),
    [
        (2.3, 0.0),
        (2.25, 0.35),
        (1.9, 1.2),
        (1.45, 3.4),
        (1.35, 6.0),
        (1.1, 7.3),
        (0.5, 8.0),
        (0.0, 8.2),
    ],
    name="great_bell",
    material="brass",
)
GREAT_BELL = 400.0
x, y, z = belfry(GREAT_BELL)
kit.marker(
    "pendulum",
    at=(x, y, z + 4.6),
    rotation=(0, 0, BELFRY_START + GREAT_BELL + 90.0),
    period=4.0,
    swing=40.0,
    name="great_bell_clapper",
)
floor(
    "bell_floor",
    BELL_FLOOR,
    [sector(R_IN - 0.1, R_OUT + 0.15, BELFRY_END - 90.0, BELFRY_END)],
)
# The broken top: stubs of the walls, the east wall up to the crown, and a gap where the
# first rafter leaves.
RAFTER_Y = 35.5
for name, lo, hi in (
    ("south", (X0, Y0, BELL_FLOOR), (X1 - WALL, Y0 + WALL, BELL_FLOOR + 1.4)),
    ("north", (X0, Y1 - WALL, BELL_FLOOR), (X1 - WALL, Y1, BELL_FLOOR + 1.8)),
    ("west_s", (X0, Y0, BELL_FLOOR), (X0 + WALL, TOWER[1] - 2.0, BELL_FLOOR + 1.8)),
    ("west_n", (X0, TOWER[1] + 2.0, BELL_FLOOR), (X0 + WALL, Y1, BELL_FLOOR + 1.2)),
    ("east_s", (X1 - WALL, Y0, BELL_FLOOR), (X1, RAFTER_Y - 1.2, CROWN - 1.0)),
    ("east_n", (X1 - WALL, RAFTER_Y + 1.2, BELL_FLOOR), (X1, Y1, CROWN - 1.0)),
    (
        "east_arch",
        (X1 - WALL, RAFTER_Y - 1.2, BELL_FLOOR + 3.4),
        (X1, RAFTER_Y + 1.2, CROWN - 1.0),
    ),
):
    town.block(f"tower_top_{name}", lo, hi)
# The west hoist: from a landing at the belfry's west door to one at the bell floor.
for name, z in (("belfry", BELFRY), ("bell", BELL_FLOOR)):
    town.block(
        f"hoist_west_landing_{name}",
        (X0 - 3.0, TOWER[1] - 2.0, z - 0.4),
        (X0, TOWER[1] + 2.0, z),
    )
kit.marker(
    "moving_platform",
    at=(X0 - 4.5, TOWER[1], BELFRY),
    points=[(X0 - 4.5, TOWER[1], BELL_FLOOR)],
    period=16.0,
    stop=2.0,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="hoist_west",
)
# The stair fragments: floating pieces of the broken stair, west from the bell floor, a
# platform with a vent, a fragment at +143 and the bell cradle up to the crown.
FRAGMENT_Y = (42.0, 44.2)
FRAGMENTS = [(2.1, 4.6), (-0.7, 1.8), (-3.5, -1.0), (-6.3, -3.8)]
for i, (x0, x1) in enumerate(FRAGMENTS):
    town.block(
        f"stair_fragment_{i + 1}",
        (x0, FRAGMENT_Y[0], BELL_FLOOR + 0.5 + i),
        (x1, FRAGMENT_Y[1], BELL_FLOOR + 1.0 + i),
    )
PLATFORM_135 = BELL_FLOOR + 5.0
town.block(
    "stair_platform", (-11.0, 37.6, PLATFORM_135 - 0.6), (-6.6, 45.0, PLATFORM_135)
)
CROWN_VENT = (-9.0, 38.8)
kit.marker("steam_vent", at=(*CROWN_VENT, PLATFORM_135), lift=9.5, name="vent_crown")
FRAGMENT_143 = 143.0
town.block(
    "stair_fragment_143", (-11.0, 31.0, FRAGMENT_143 - 0.6), (-7.5, 36.5, FRAGMENT_143)
)
CRADLE: Place = (-6.0, 32.5, FRAGMENT_143)
kit.marker(
    "moving_platform",
    at=CRADLE,
    points=[(CRADLE[0], CRADLE[1], CROWN)],
    period=12.0,
    stop=2.0,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="bell_cradle",
)
# The crown, on top of the east wall: the zone's top and its finish.
CROWN_RECT = (-8.0, 34.0, X1, Y1 - 1.0)
cx0, cy0, cx1, cy1 = CROWN_RECT
town.block("crown", (cx0, cy0, CROWN - 1.0), (cx1, cy1, CROWN))
FINISH: Place = (0.0, 39.0, CROWN)
# The rafters: two narrow beams from the bell floor out over the east side and back to the
# crown, with a cap where they meet.
RAFTER_1 = (19.0, 9.0, -20.0)  # length, rise, heading (degrees from east)
CAP = 1.6  # the radius of the round cap where the rafters meet
r1 = math.radians(RAFTER_1[2])
RAFTER_START: Place = (5.0, RAFTER_Y, BELL_FLOOR)
reach = RAFTER_1[0] + CAP
APEX: Place = (
    RAFTER_START[0] + reach * math.cos(r1),
    RAFTER_START[1] + reach * math.sin(r1),
    BELL_FLOOR + RAFTER_1[1],
)
RAFTER_END: Place = (X1, 39.0, CROWN)
kit.ramp(
    at=RAFTER_START,
    width=0.8,
    length=RAFTER_1[0],
    rise=RAFTER_1[1],
    yaw=RAFTER_1[2] - 90.0,
    name="rafter_1",
    material="brass",
    trim="gold",
)
town.floor("rafter_cap", kit.arc(APEX[:2], CAP, 0, 360), APEX[2], 0.5, finish="brass")
r2 = math.atan2(RAFTER_END[1] - APEX[1], RAFTER_END[0] - APEX[0])
kit.ramp(
    at=(APEX[0] + CAP * math.cos(r2), APEX[1] + CAP * math.sin(r2), APEX[2]),
    width=0.8,
    length=math.hypot(RAFTER_END[0] - APEX[0], RAFTER_END[1] - APEX[1]) - CAP,
    rise=CROWN - APEX[2],
    yaw=math.degrees(r2) - 90.0,
    name="rafter_2",
    material="brass",
    trim="gold",
)

# --- The tower's dress --------------------------------------------------------------------------

# A plinth, a cornice at each floor, a pilaster at each corner, glazed windows, the great door
# of the base and the louvres of the belfry. None of it collides: it stands at most 0.25 m
# proud of the walls.
dress = town.Parts()
dress.box((X0 - 0.25, Y0 - 0.25, 0.0), (X1 + 0.25, Y1 + 0.25, 0.9), "dressed")
# The solid base (a kit deck) gets a skin of coursed stone, like the walls above it.
dress.box((X0 - 0.02, Y0 - 0.02, 0.9), (X1 + 0.02, Y1 + 0.02, BASE - 0.5), "wall")
for z, finish in (
    (BASE, "dressed"),
    (GALLERY, "dressed"),
    (GEAR_ROOM, "dressed"),
    (CLOCK_FLOOR, "brass"),
    (BELFRY, "brass"),
    (BELL_FLOOR, "dressed"),
):
    for lo, hi in (
        ((X0 - 0.25, Y0 - 0.25), (X1 + 0.25, Y0)),
        ((X0 - 0.25, Y1), (X1 + 0.25, Y1 + 0.25)),
        ((X0 - 0.25, Y0), (X0, Y1)),
        ((X1, Y0), (X1 + 0.25, Y1)),
    ):
        dress.box((*lo, z - 0.5), (*hi, z), finish)
for cx, cy in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)):
    sx, sy = (1.0 if cx < 0 else -1.0), (1.0 if cy < TOWER[1] else -1.0)
    top = CROWN - 1.0 if cx > 0 else BELL_FLOOR - SLAB
    dress.box(
        (min(cx, cx + sx * 1.0), min(cy, cy - sy * 0.12), 0.9),
        (max(cx, cx + sx * 1.0), max(cy, cy - sy * 0.12), top),
        "wall",
    )
    dress.box(
        (min(cx, cx - sx * 0.12), min(cy, cy + sy * 1.0), 0.9),
        (max(cx, cx - sx * 0.12), max(cy, cy + sy * 1.0), top),
        "wall",
    )
TOWER_FACES = town.faces((X0, Y0), (X1, Y1))
# The light of each room of the tower (objects/room_probe): a warm ambient light, and
# reflections of the room, not of the sky.
for i, (bottom, top) in enumerate(
    pairwise((BASE, GALLERY, GEAR_ROOM, CLOCK_FLOOR, BELFRY, BELL_FLOOR, CROWN))
):
    kit.marker(
        "room_probe",
        at=(*TOWER, bottom),
        width=2 * IN,
        depth=2 * IN,
        height=top - SLAB - bottom,
        name=f"room_{i + 1}",
    )
# Two windows on each face of each storey, clear of the doors, the dials and the louvres.
for side, face in TOWER_FACES.items():
    for bottom, top in (
        (BASE + 4.0, GALLERY - 1.0),
        (GALLERY + 5.0, GEAR_ROOM - 1.0),
        (GEAR_ROOM + 5.0, CLOCK_FLOOR - 1.0),
    ):
        z = bottom
        while z + 3.0 < top:
            for along in (2.6, face.length - 2.6):
                town.window(dress, face, along, 1.1, z, z + 2.6)
            z += 6.0
    town.window(
        dress, face, face.length / 2, 3.2, BELFRY + 5.0, BELFRY + 13.0, pane="iron"
    )
# The square's name plaque over the great door, clear of the door's lintel (5.6 m).
town.decal(
    "plaque_square", "plaque_square", (TOWER[0], Y0 - 0.02, 6.7), 0.0, (2.4, 1.6)
)
dress.add("tower_dress", collide=False)
# The great door of the tower base: a hero prop 4 m wide on the plinth, its back in the wall.
kit.prop("great_door", at=(TOWER[0], Y0, 0.9))
# The broken crown: merlons at the corners.
for i, (mx, my) in enumerate(
    ((cx0, cy0), (cx1 - 1.0, cy0), (cx1 - 1.0, cy1 - 1.0), (cx0, cy1 - 1.0))
):
    town.block(
        f"crown_merlon_{i + 1}", (mx, my, CROWN), (mx + 1.0, my + 1.0, CROWN + 0.8)
    )
    kit.ball((mx + 0.5, my + 0.5, CROWN + 1.05), 0.25, name=f"crown_finial_{i + 1}")

# --- The town round the square ------------------------------------------------------------------


# A house of a street: plan corners, eave height, the sides with no windows.
House = tuple[Point, Point, float, str]


def street(
    name: str, houses: Sequence[House], along: Literal["x", "y"], door: str
) -> None:
    """Adds a row of houses as one mesh: each house is (lo, hi, eave, blind sides), with its
    ridge 3.4 m above the eave."""
    parts = town.Parts()
    for lo, hi, eave, blind in houses:
        town.house(parts, lo, hi, eave, eave + 3.4, along, door, blind)
    parts.add(name)


def row(
    start: float,
    widths: Sequence[float],
    eaves: Sequence[float],
    other: tuple[float, float],
    along: Literal["x", "y"],
) -> list[House]:
    """Returns the houses of a row whose fronts follow `along` (x or y) from `start`, each
    `width` wide, between the two cross coordinates of `other`. The houses between the ends
    have no windows on their shared sides."""
    out = []
    at = start
    blind_inner = "ew" if along == "x" else "ns"
    for i, (width, eave) in enumerate(zip(widths, eaves, strict=True)):
        if along == "x":
            lo, hi = (at, other[0]), (at + width, other[1])
        else:
            lo, hi = (other[0], at), (other[1], at + width)
        ends = blind_inner
        if i == 0:
            ends = ends.replace("w" if along == "x" else "s", "")
        if i == len(widths) - 1:
            ends = ends.replace("e" if along == "x" else "n", "")
        out.append((lo, hi, eave, ends))
        at += width
    return out


# The south side of the square, with a street going south from its middle.
street(
    "town_south_w",
    row(-40.0, [7, 6, 8, 6.5, 8.5], [9, 7.5, 10, 8, 9.5], (-9.0, -1.0), "x"),
    "x",
    "n",
)
street(
    "town_south_e",
    row(4.0, [8, 6, 7.5, 7, 7.5], [8.5, 10, 7.5, 9, 8], (-9.0, -1.0), "x"),
    "x",
    "n",
)
# West of the bakery and the guildhall, across a lane.
street(
    "town_west",
    row(
        -1.0, [7, 8, 6, 7, 8, 6, 6], [8, 9.5, 7.5, 10, 8.5, 9, 7.5], (-42.0, -33.0), "y"
    ),
    "y",
    "e",
)
street("town_west_inner", [((-31.5, 4.0), (-25.6, 18.8), 7.0, "")], "y", "e")
# North-west and north of the tower, across a street from it.
street("town_north_w", row(-40.0, [9, 9], [8, 9.5], (41.0, 49.0), "x"), "x", "s")
street(
    "town_north",
    row(-40.0, [8, 7, 9, 6, 7, 6], [9, 8, 10, 7.5, 9.5, 8], (51.0, 59.0), "x"),
    "x",
    "s",
)
street(
    "town_north_e",
    row(6.0, [7, 8, 6, 9, 7], [8.5, 9.5, 7.5, 10, 8], (51.0, 59.0), "x"),
    "x",
    "s",
)
street(
    "town_north_e_inner",
    [
        ((14.0, 41.0), (21.0, 48.0), 8.0, ""),
        ((22.0, 41.0), (29.0, 48.0), 9.0, ""),
    ],
    "x",
    "s",
)
# East of the waterwheel, and a low house under the scaffold.
street(
    "town_east",
    row(-1.0, [8, 7, 9, 6, 8, 7], [9, 7.5, 10, 8, 9.5, 8.5], (31.0, 40.0), "y"),
    "y",
    "w",
)
street("town_east_inner", [((19.5, -1.0), (27.5, 6.5), 8.0, "")], "x", "s")
# The outer ring: streets of plainer houses out to the edge of the ground.
street(
    "town_ring_s",
    row(
        -52.0,
        [9, 8, 10, 9, 8, 10, 9, 8, 10, 9, 8, 10],
        [7, 8, 9, 7.5, 8.5, 7, 9, 8, 7.5, 9, 8, 7],
        (-24.0, -15.0),
        "x",
    ),
    "x",
    "n",
)
street(
    "town_ring_w",
    row(
        -15.0,
        [10, 9, 10, 8, 10, 9, 10, 9, 10],
        [8, 7, 9, 8, 7.5, 9, 8, 7, 8.5],
        (-56.0, -47.0),
        "y",
    ),
    "y",
    "e",
)
street(
    "town_ring_e",
    row(
        -15.0,
        [10, 9, 10, 8, 10, 9, 10, 9, 10],
        [7.5, 9, 8, 7, 9, 8.5, 7, 8, 9],
        (47.0, 56.0),
        "y",
    ),
    "y",
    "w",
)
street(
    "town_ring_n",
    row(
        -47.0,
        [9, 10, 8, 9, 10, 9, 8, 10, 9, 10],
        [8, 9, 7, 8.5, 9, 7.5, 8, 9, 7, 8],
        (66.0, 75.0),
        "x",
    ),
    "x",
    "s",
)

# Open country round the town (objects/land), just under the town's ground.
kit.marker("land", at=(0.0, 20.0, -0.03), name="land")


def far_town() -> None:
    """Adds the far town round the ground: short rows of plain houses on a jittered grid, out
    to a ragged edge 150 to 260 m from the square. It is far scenery (`-far`): no collision,
    no lightmap and no reflection probe."""
    rng = random.Random(31)
    parts = town.Parts()
    for gx in range(-288, 289, 36):
        for gy in range(-250, 311, 30):
            along: Literal["x", "y"] = "x" if rng.random() < 0.6 else "y"
            length = rng.uniform(14.0, 28.0 if along == "x" else 22.0)
            deep = rng.uniform(7.0, 9.0)
            x0 = gx + rng.uniform(-5.0, 5.0) - (length if along == "x" else deep) / 2
            y0 = gy + rng.uniform(-4.0, 4.0) - (deep if along == "x" else length) / 2
            x1 = x0 + (length if along == "x" else deep)
            y1 = y0 + (deep if along == "x" else length)
            reach = math.hypot((x0 + x1) / 2, (y0 + y1) / 2 - 20.0)
            if reach > 150.0 + 110.0 * rng.random():
                continue
            if x1 > -72.0 and x0 < 72.0 and y1 > -44.0 and y0 < 94.0:
                continue
            at = x0 if along == "x" else y0
            end = x1 if along == "x" else y1
            while end - at > 5.0:
                width = min(rng.uniform(6.0, 9.0), end - at)
                if along == "x":
                    lo, hi = (at, y0), (at + width, y1)
                else:
                    lo, hi = (x0, at), (x1, at + width)
                eave = rng.uniform(6.0, 9.5)
                town.house(parts, lo, hi, eave, eave + 3.4, along, plain=True)
                at += width
    parts.add("far_town-far", collide=False)


far_town()

# Street lamps round the square, off the ways up. A cylinder makes each post solid.
LAMPS = [
    (-12.0, 1.0),
    (12.0, 1.0),
    (-16.2, 22.0),
    (13.4, 30.0),
    (-7.0, 29.6),
    (7.0, 29.6),
    (-3.5, 0.6),
    (3.5, 0.6),
    (-16.4, 5.0),
    (16.0, 5.5),
]
for at in LAMPS:
    kit.prop("lamp_post", at=(*at, 0.0), collider="cylinder")

# The windows and doors of the bakery, the workshop and the guildhall. They do not collide.
fronts = town.Parts()
# The shop fronts: the bakery's and the clockmaker's shop windows show their shops.
bakery_front = town.faces((bx0, by0), (bx1, by1))["e"]
town.window(fronts, bakery_front, 2.4, 1.0, 0.9, 2.2, room="window_room_a")
town.window(fronts, bakery_front, 7.2, 1.4, 0.0, 2.4, door=True)
town.window(fronts, bakery_front, 10.2, 2.0, 0.6, 2.3, room="window_bakery")
town.windows(fronts, town.faces((bx0, by0), (bx1, by1))["s"], BAKERY_TOP)
workshop_faces = town.faces((wx0, wy0), (wx1, wy1))
town.windows(fronts, workshop_faces["w"], ROOF, bottom=3.0)
town.window(fronts, workshop_faces["w"], 3.5, 2.0, 0.6, 2.3, room="window_clockmaker")
town.window(fronts, workshop_faces["w"], 8.0, 1.4, 0.0, 2.4, door=True)
for along, room in ((11.5, "window_room_b"), (15.0, "window_room_a")):
    town.window(fronts, workshop_faces["w"], along, 1.0, 0.9, 2.2, room=room)
town.windows(fronts, workshop_faces["n"], ROOF)
town.windows(fronts, workshop_faces["s"], ROOF, bottom=BALCONY)
hall = town.Face((gx1, gy0), (0.0, 1.0), (1.0, 0.0), TERRACE_Y - gy0)
for along in (2.0, 9.0, 11.4):
    town.window(fronts, hall, along, 1.3, 1.6, 6.8)
town.windows(
    fronts,
    town.Face((gx1, TERRACE_Y), (0.0, 1.0), (1.0, 0.0), gy1 - TERRACE_Y),
    RIDGE,
    storey=3.5,
)
for along in (3.0, 6.5):
    town.window(
        fronts,
        town.Face((gx1, gy0), (-1.0, 0.0), (0.0, -1.0), gx1 - gx0),
        along,
        1.3,
        1.6,
        6.8,
    )
fronts.add("town_fronts", collide=False)
# Shop signs: art on the hanging boards of the bakery and the clockmaker; the inn's board waits
# for its art. Signs and a shop dial on the walls.
town.sign("sign_bakery", (bx1, 16.2, 3.4), (1.0, 0.0), art="sign_bakery")
town.sign(
    "sign_clockmaker",
    (wx0, 20.0, 4.6),
    (-1.0, 0.0),
    width=1.2,
    height=0.8,
    art="sign_clockmaker",
)
town.sign("sign_inn", (-8.0, -1.0, 3.6), (0.0, 1.0), art="sign_inn")
town.decal(
    "sign_guildhall", "sign_guildhall", (gx1 + 0.02, 25.5, 3.85), 90.0, (2.4, 0.9)
)
town.decal("sign_workshop", "sign_workshop", (18.5, wy0 - 0.02, 6.1), 0.0, (1.65, 1.1))
town.decal("dial_shop", "dial_shop", (wx0 - 0.02, 16.0, 6.4), -90.0, (1.2, 1.2))
# Street name plates, between the ground floor's lintels and the first floor's sills.
town.decal(
    "street_name_south",
    "street_name_south",
    (4.55, -1.0 + 0.02, 3.5),
    180.0,
    (1.0, 0.32),
)
town.decal(
    "street_name_east", "street_name_east", (wx0 - 0.02, 13.0, 3.0), -90.0, (1.0, 0.28)
)
# Notices: a market bill by the guildhall's door, and the clockmaker's notice by his door.
town.decal("notice_market", "notice_market", (gx1 + 0.02, 27.0, 1.5), 90.0, (0.6, 0.8))
town.decal("notice_clock", "notice_clock", (wx0 - 0.02, 22.2, 1.5), -90.0, (0.6, 0.8))
# Grime: damp at the foot of the walls round the square, and rain streaks under sills.
GRIME_BASE = [
    ((bx1 + 0.015, 9.0, 0.4), 90.0),
    ((bx1 + 0.015, 12.0, 0.4), 90.0),
    ((bx1 + 0.015, 15.0, 0.4), 90.0),
    ((wx0 - 0.015, 26.5, 0.4), -90.0),
    ((wx0 - 0.015, 17.0, 0.4), -90.0),
    ((wx0 - 0.015, 12.0, 0.4), -90.0),
    ((gx1 + 0.015, 22.0, 0.4), 90.0),
    ((gx1 + 0.015, 29.5, 0.4), 90.0),
]
for i, (at, yaw) in enumerate(GRIME_BASE):
    town.decal(f"grime_base_{i}", "grime_base", at, yaw, (3.0, 0.8), soft=True)
GRIME_STREAKS = [
    ((wx0 - 0.015, 17.5, 3.35), -90.0),
    ((wx0 - 0.015, 11.5, 3.35), -90.0),
    ((gx1 + 0.015, 29.0, 1.05), 90.0),
]
for i, (at, yaw) in enumerate(GRIME_STREAKS):
    town.decal(f"grime_streaks_{i}", "grime_streaks", at, yaw, (1.2, 1.0), soft=True)
# Props: decoration from the art trial (#96). Each has a simple collider, so the marble meets it
# as it looks; none stands on a way up.
PROPS: list[tuple[str, Place, float, str]] = [
    ("bread_cart", (6.0, 3.0, 0.0), 30.0, "box"),
    ("barrels", (-17.3, 19.0, 0.0), 0.0, "cylinder"),
    ("barrels", (13.6, 25.6, 0.0), 0.0, "cylinder"),
    ("barrels", (-10.2, -0.3, 0.0), 0.0, "cylinder"),
    ("barrels", (24.2, 15.6, 0.0), 0.0, "cylinder"),
    ("flower_trough", (-3.3, FOUNTAIN[1], 0.0), 0.0, "box"),
    ("flower_trough", (3.3, FOUNTAIN[1], 0.0), 0.0, "box"),
    ("flower_trough", (-2.6, Y0 - 0.6, 0.0), 90.0, "box"),
    ("flower_trough", (2.6, Y0 - 0.6, 0.0), 90.0, "box"),
    ("flower_trough", (-14.0, -0.35, 0.0), 90.0, "box"),
    ("flower_trough", (14.0, -0.35, 0.0), 90.0, "box"),
    ("flower_trough", (gx1 + 0.35, 22.0, 0.0), 0.0, "box"),
]
for name, at, yaw, collider in PROPS:
    kit.prop(name, at=at, rotation=(0.0, 0.0, yaw), collider=collider)
# The props of the art pass: benches with their backs to the tower, goods on the counters of
# the bakery's and the fruit seller's stalls, a crate of clock parts by the workshop, a hay
# cart in the south street and an anvil by the waterwheel. None is on a way up.
ART_PROPS: list[tuple[str, Place, float, str]] = [
    ("bench", (-10.5, 30.8, 0.0), 180.0, "box"),
    ("bench", (10.5, 29.6, 0.0), 180.0, "box"),
    ("bench", (-15.8, 26.0, 0.0), 90.0, "box"),
    ("stall_bread", (-12.5, 9.95, 0.95), 0.0, "none"),
    ("stall_fruit", (-16.0, 9.95, 0.95), 0.0, "none"),
    ("clock_parts", (13.8, 22.5, 0.0), -90.0, "box"),
    ("hay_cart", (0.0, -5.0, 0.0), 0.0, "box"),
    ("anvil", (25.0, 14.0, 0.0), 0.0, "box"),
]
for name, at, yaw, collider in ART_PROPS:
    kit.prop(name, at=at, rotation=(0.0, 0.0, yaw), collider=collider)

# --- Routes: section 1 -------------------------------------------------------------------------

STALL_ROW = 11.0
FIRST[1] = [
    ((-6.5, STALL_ROW, 0.0), "jump; speed 4"),
    ((-9.2, STALL_ROW, 1.0), "speed 4"),
    ((-10.0, STALL_ROW, 1.0), "jump; speed 4"),
    ((-12.6, STALL_ROW, 2.0), "speed 4"),
    ((-13.5, STALL_ROW, 2.0), "jump; speed 4"),
    ((-16.1, STALL_ROW, 3.0), "speed 4"),
    ((-17.0, STALL_ROW, 3.0), "jump; speed 4"),
    ((-19.6, STALL_ROW, BAKERY_TOP), "speed 4"),
    ((CHIMNEY_VENT[0], 15.8, BAKERY_TOP), "speed 3"),
    (
        (
            CHIMNEY_VENT[0],
            22.4,
            EAVE + (gx1 - CHIMNEY_VENT[0]) * (RIDGE - EAVE) / (gx1 - RIDGE_X[1]),
        ),
        "speed 3",
    ),
    ((-29.4, 25.4, RIDGE), ""),
    ((-29.4, 32.6, RIDGE), ""),
]
# The hoist leaves from the vent's flight: from a stop west of the vent, wait for the deck.
_hoist_dir = (HOIST_LOW[0] - RIDGE_VENT[0], HOIST_LOW[1] - RIDGE_VENT[1])
_hoist_len = math.hypot(*_hoist_dir)
_hoist_unit = (_hoist_dir[0] / _hoist_len, _hoist_dir[1] / _hoist_len)
FIRST[1] += [
    (
        (
            RIDGE_VENT[0] - 2.0 * _hoist_unit[0],
            RIDGE_VENT[1] - 2.0 * _hoist_unit[1],
            RIDGE,
        ),
        "wait_until hoist 10.4 11.6",
    ),
    (
        (
            RIDGE_VENT[0] - 1.15 * _hoist_unit[0],
            RIDGE_VENT[1] - 1.15 * _hoist_unit[1],
            RIDGE,
        ),
        "speed 3",
    ),
    (HOIST_LOW, "speed 3; wait_until hoist 6.0 7.8"),
    ((lx0 + 1.5, HOIST_Y, GALLERY), ""),
    (FOOT[2], ""),
]
EXPERT[1] = FIRST[1][:11] + [
    ((RIDGE_VENT[0] - 2.0, BEAM_Y, RIDGE), "wait 0.3"),
    ((RIDGE_VENT[0] - 1.15, BEAM_Y, RIDGE), "speed 3"),
    ((BEAM_LOW[0] + 1.0, BEAM_Y, BEAM_LOW[1]), "speed 3"),
    ((BEAM_HIGH[0] - 2.0, BEAM_Y, BEAM_HIGH[1] - 0.7), "speed 6"),
    ((lx0 + 1.6, BEAM_Y, GALLERY), "speed 6"),
    (FOOT[2], ""),
]

# --- Routes: section 2 -------------------------------------------------------------------------

FOOT[3] = (*ring(1.5, 0.0), GEAR_ROOM)
_waits = {at - PENDULUM_WAIT: name for name, at in PENDULUMS.items()}
FIRST[2] = [(shaft(-10.0), "")] + [
    (shaft(along), f"wait_until {_waits[along]} 1.4 1.8" if along in _waits else "")
    for along in along_spiral(895.0, list(_waits))
]
FIRST[2] += [((*ring(R_MID, SHAFT_END - 14.0), GEAR_ROOM), ""), (FOOT[3], "")]
_cw_at = SHAFT_START - 180.0
EXPERT[2] = [
    (shaft(-10.0), ""),
    (shaft(5.0), ""),
    (shaft(47.5), ""),
    (shaft(90.0), ""),
    (shaft(160.0), ""),
]
EXPERT[2] += [
    ((*ring(4.85, _cw_at), shaft(180.0)[2]), "wait_until counterweight 7.2 7.8"),
    ((*ring(3.95, _cw_at), shaft(180.0)[2]), "jump; speed 4.8"),
    ((*TOWER, COUNTER_LOW), "speed 4.8; wait_until counterweight 4.0 4.6"),
]
_cw_out = shaft(800.0)
_cw_dir = (_cw_out[0] - TOWER[0], _cw_out[1] - TOWER[1])
_cw_len = math.hypot(*_cw_dir)
EXPERT[2] += [
    (
        (
            TOWER[0] + _cw_dir[0] / _cw_len * 0.9,
            TOWER[1] + _cw_dir[1] / _cw_len * 0.9,
            COUNTER_HIGH,
        ),
        "jump; speed 4.5",
    ),
    ((_cw_out[0], _cw_out[1], _cw_out[2]), "speed 4.5"),
    (shaft(845.0), ""),
    (shaft(895.0), ""),
    ((*ring(R_MID, SHAFT_END - 14.0), GEAR_ROOM), ""),
    (FOOT[3], ""),
]

# --- Routes: section 3 -------------------------------------------------------------------------

FIRST[3] = [
    ((5.1, 35.2, GEAR_ROOM), ""),
    ((4.1, 35.2, GEAR_ROOM), "jump; speed 3"),
    ((1.6, 35.2, 51.0), "speed 3"),
    ((1.5, 35.2, 51.0), "jump; speed 3"),
    ((-0.9, 35.2, 52.0), "speed 3"),
    ((-1.0, 35.2, 52.0), "jump; speed 3"),
    ((-3.9, 35.0, 53.0), "speed 3"),
    ((-3.9, 35.6, 53.0), "jump; speed 3"),
    ((-3.9, 37.6, LIFT_1_FLOOR), "speed 3"),
    (LIFT_1.board, "speed 2"),
    (LIFT_1.side, "speed 1.5"),
    (LIFT_1.out, ""),
    (LIFT_2.board, "speed 2"),
    (LIFT_2.side, "speed 1.5"),
    (LIFT_2.out, ""),
    ((-4.3, 37.4, LIFT_2.exit), ""),
]
for ramp in (1, 2):
    for along in (10.0, 82.0, 154.0, 222.0):
        FIRST[3].append((gear_ramp(ramp, along), ""))
    if ramp == 1:
        FIRST[3].append(
            ((*ring(R_MID, GEAR_RAMP_2 + 15.0), LIFT_2.exit + GEAR_RISE), "")
        )
FIRST[3] += [((*ring(R_MID, GEAR_RAMP_END - 14.0), CLOCK_FLOOR), ""), (FOOT[4], "")]
EXPERT[3] = [
    ((-2.0, VENT_Y, GEAR_ROOM), ""),
    ((X0 - 1.0, VENT_Y, GEAR_ROOM), "speed 3"),
    ((-20.6, 38.2, 74.0), "speed 3"),
    ((-20.6, 39.9, 74.0), "jump; speed 3"),
]
STEP_ROW = (STEP_Y[0] + STEP_Y[1]) / 2
for i, (x0, x1) in enumerate(WEST_STEPS):
    EXPERT[3].append((((x0 + x1) / 2, STEP_ROW, 75.0 + i), "speed 2.5"))
    EXPERT[3].append(((x1 - 0.6, STEP_ROW, 75.0 + i), "jump; speed 2.5"))
EXPERT[3] += [
    ((-7.3, STEP_ROW, CLOCK_FLOOR), "speed 3.5"),
    ((-7.3, VENT_Y, CLOCK_FLOOR), ""),
    ((-4.0, VENT_Y, CLOCK_FLOOR), ""),
    (FOOT[4], ""),
]

# --- Routes: section 4 -------------------------------------------------------------------------

# On each floor or ledge the route waits beside the next bell weight for it to come down, rides
# it up, and steps off toward the next one.
FIRST[4] = []
for name, (x, z, _) in BELL_WEIGHTS.items():
    side = 1.0 if x > 0 else -1.0
    FIRST[4] += [
        ((side * 0.9, TOWER[1], z), f"speed 3; wait_until {name} 0.3 1.2"),
        ((x, TOWER[1], z), f"speed 3; wait_until {name} 6.0 7.5"),
    ]
FIRST[4] += [(FOOT[5], "")]
EXPERT[4] = [
    ((4.5, 41.6, CLOCK_FLOOR), ""),
    ((8.4, SLATE_Y, CLOCK_FLOOR), ""),
    ((SLOPE_1_TOP[0] + 0.6, SLATE_Y, SLOPE_1_TOP[1]), "speed 8"),
    ((SLATE_VENT_1[0] - 0.6, 41.9, SLOPE_1_TOP[1]), "speed 4"),
    ((SLATE_VENT_1[0], 42.8, SLOPE_1_TOP[1]), "speed 3"),
    ((SLATE_VENT_1[0], SLATE_ROW - 0.6, LEDGE_94), "speed 3"),
    ((20.7, SLATE_ROW, LEDGE_94), ""),
    ((SLOPE_2_TOP[0] - 0.4, SLATE_ROW, SLOPE_2_TOP[1]), "speed 7"),
    ((SLATE_VENT_2[0] + 1.3, SLATE_ROW, SLOPE_2_TOP[1]), "speed 3"),
    ((3.6, SLATE_ROW, 107.0), "speed 3"),
    ((1.6, SLATE_ROW, 107.0), "jump; speed 3"),
    ((-0.4, SLATE_ROW, 108.0), "speed 3"),
    ((-0.8, SLATE_ROW, 108.0), "jump; speed 3"),
    ((NORTH_DOOR_X, 49.6, 109.0), "speed 2.5"),
    ((NORTH_DOOR_X, 48.1, 109.0), "jump; speed 2.5"),
    ((NORTH_DOOR_X, 46.2, BELFRY), "speed 2.5"),
    ((NORTH_DOOR_X, Y1 - 1.0, BELFRY), ""),
    (FOOT[5], ""),
]

# --- Routes: section 5 -------------------------------------------------------------------------

BELL_START: list[Leg] = [((-2.6, 35.3, BELFRY), "")]
for along in along_spiral(745.0, [GREAT_BELL - PENDULUM_WAIT]):
    action = (
        "wait_until great_bell_clapper 1.4 1.8"
        if along == GREAT_BELL - PENDULUM_WAIT
        else ""
    )
    BELL_START.append((belfry(along), action))
BELL_START += [
    ((*ring(R_MID, BELFRY_END + 14.0), BELL_FLOOR), ""),
]
FIRST[5] = BELL_START + [((3.4, 39.6, BELL_FLOOR), "")]
FRAGMENT_ROW = (FRAGMENT_Y[0] + FRAGMENT_Y[1]) / 2
FIRST[5].append(((3.4, 41.1, BELL_FLOOR), "jump; speed 2.5"))
for i, (x0, x1) in enumerate(FRAGMENTS):
    FIRST[5].append((((x0 + x1) / 2, FRAGMENT_ROW, BELL_FLOOR + 1.0 + i), "speed 2.5"))
    FIRST[5].append(((x0 + 0.6, FRAGMENT_ROW, BELL_FLOOR + 1.0 + i), "jump; speed 2.5"))
FIRST[5] += [
    ((CROWN_VENT[0], 41.8, PLATFORM_135), "speed 2.5"),
    ((CROWN_VENT[0], 40.6, PLATFORM_135), "speed 3"),
    ((CROWN_VENT[0], 34.6, FRAGMENT_143), "speed 3"),
    ((-9.3, 32.6, FRAGMENT_143), "wait_until bell_cradle 10.8 11.6"),
    (CRADLE, "speed 3; wait_until bell_cradle 6.0 7.6"),
    ((CRADLE[0], 35.6, CROWN), ""),
    (FINISH, ""),
]
EXPERT[5] = BELL_START + [
    ((3.6, RAFTER_Y, BELL_FLOOR), ""),
    (
        (
            RAFTER_START[0] + 0.6 * math.cos(r1),
            RAFTER_Y + 0.6 * math.sin(r1),
            BELL_FLOOR + 0.3,
        ),
        "speed 5",
    ),
    (APEX, ""),
    (
        (RAFTER_END[0] - 0.8 * math.cos(r2), RAFTER_END[1] - 0.8 * math.sin(r2), CROWN),
        "",
    ),
    (FINISH, ""),
]

# --- Start, finish, routes ------------------------------------------------------------------------

kit.marker("start", at=START)
kit.marker("finish", at=FINISH)


def route(kind: str, legs: list[Leg]) -> None:
    """Places the route of `kind` through the legs, ending on the finish pad."""
    actions = [
        f"{i} {action.strip()}"
        for i, (_, text) in enumerate(legs)
        for action in text.split(";")
        if action.strip()
    ]
    kit.marker(
        "route",
        at=START,
        points=[point for point, _ in legs],
        name=f"route_{kind}",
        kind=kind,
        actions="; ".join(actions),
    )


route("first_run", [leg for section in sorted(FIRST) for leg in FIRST[section]])
route("expert", [leg for section in sorted(EXPERT) for leg in EXPERT[section]])

# --- Shots ----------------------------------------------------------------------------------------

kit.shot("overview", at=(-46, -30, 62), rotation=(-24, 0, -36))
kit.shot("start", at=(0, 19.5, 1.6), rotation=(10, 0, 0))
kit.shot("square", at=(0.0, -6.5, 2.2), rotation=(14, 0, 0))
kit.shot("market", at=(4.0, 3.0, 3.0), rotation=(4, 0, 58))
kit.shot("workshop", at=(-2.0, 4.0, 3.0), rotation=(6, 0, -52))
kit.shot("tower", at=(26, -26, 30), rotation=(16, 0, 34))
kit.shot("crown_down", at=(0.0, 30.0, 156.0), rotation=(-80, 0, 180))
kit.shot("finish", at=(14, 20, 158), rotation=(-22, 0, 35))
kit.shot("egg", at=(EGG[0] + 3.5, EGG[1] - 1.5, 1.6), rotation=(-12, 0, 70))
kit.shot("shaft", at=(-4.2, 37.0, 33.0), rotation=(-25, 0, -60))
kit.shot("gear_room", at=(4.6, 34.2, 59.0), rotation=(-12, 0, 45))
kit.shot("clock_floor", at=(-4.6, 34.2, 84.0), rotation=(8, 0, -40))
kit.shot("belfry", at=(4.6, 43.6, 118.0), rotation=(-15, 0, 140))
kit.shot("clock", at=(16.0, 37.5, 95.0), rotation=(0, 0, 82))
# The fork of each floor of the tower: its way inside and the door to its way outside.
kit.shot("fork_gallery", at=(4.4, 43.8, 27.8), rotation=(-4, 0, 147))
kit.shot("fork_gear_room", at=(4.8, 35.0, 53.5), rotation=(-10, 0, 70))
kit.shot("fork_clock_floor", at=(-4.8, 36.0, 82.2), rotation=(4, 0, -59))
kit.shot("fork_belfry", at=(4.8, 34.0, 113.5), rotation=(-10, 0, 35))
