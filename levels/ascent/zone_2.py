"""Ascent 2 The Broken Tower (#32): the climb through the pieces of the clock tower's broken
top, which float above the crown of zone 1, 150 to 300 m. The brief and the map are
docs/levels/ascent-z2.md and ascent-z2.svg.

The script uses the coordinates of the climb (docs/design/ascent.md §2): x east, y north, z up,
the climb start at height 0, the tower axis at AXIS as in zone 1. The zone starts on its own
floor south of zone 1's crown and ends on the spire cap, round AXIS at +300 m.

Each part has a west way and an east way:

1. Face and gears, +150 to +173: three stair fragments, the tilted clock face and its hands, a
   vent and five numeral stones; or three flat gears, the lift gear, a walkway with a
   pendulum and a weight lift. Both reach the bell ledge.
2. Mainspring, +173 to +200: a chain of three vents; or the mainspring ramp round a swinging
   bell. Both reach the barrel lid.
3. Shards and rod, +200 to +235: the stair shards with a lift and a vent; or the fallen
   pendulum rod, its bob and three vents. Both reach the Dial ring, on opposite sides.
4. Bells and slabs, +235 to +270: a chain of four vents; or the roof slabs, two bells and a
   weight lift. Both reach the roof slab.
5. The spire, +270 to +300: the loose slate slope and the fallen lightning rod; or the ramp
   round the spire and a vent. Both reach the cap.
"""

import math

from mathutils import Vector

import kit
from kit import clockwork, town

Point = tuple[float, float]
Place = tuple[float, float, float]
# A route point and its actions, separated by ";" (route.gd), for example "jump; speed 4".
Leg = tuple[Place, str]

AXIS = (0.0, 39.0)
CROWN = 150.0
# Zone 1's crown: a slab on top of the tower (levels/ascent/zone_1.py CROWN_RECT).
CROWN_RECT = (-8.0, 34.0, 6.0, 44.0)
# Steps: 2.3 m deep, with gaps of 0.3 m (docs/levels/README.md, rules from Ascent 1).
STEP = 2.3
STEP_GAP = 0.3
# The rest ledges.
BELL_LEDGE = 173.0
LID = 200.0
RING = 235.0
ROOF = 270.0
CAP = 300.0

# For work on one part: the start pad and both routes begin at the foot of this part (FOOT).
# Keep it at 1.
TEST_FROM = 1
FOOT: dict[int, Place] = {}
FIRST: dict[int, list[Leg]] = {}
EXPERT: dict[int, list[Leg]] = {}

kit.level(title="The Broken Tower", par=300.0, gold=200.0, sky="ground_dawn")


def ring(radius: float, angle: float, centre: Point = AXIS) -> Point:
    """Returns the plan point at `angle` degrees (from +x, counter-clockwise) on the circle of
    `radius` round centre."""
    a = math.radians(angle)
    return (centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a))


def step_row(
    name: str,
    start: Point,
    heading: float,
    first: float,
    count: int,
    width: float = 3.0,
    rise: float = 1.0,
    under: float = 1.6,
) -> list[Point]:
    """Adds `count` stone steps in a straight row: the first starts at the plan point `start`
    (the middle of its near edge), each runs STEP m along `heading` (degrees from +x), and each
    is `rise` m above the one before, from `first`. Returns the middle of each step."""
    a = math.radians(heading)
    u = (math.cos(a), math.sin(a))
    middles = []
    for i in range(count):
        near = (
            start[0] + u[0] * i * (STEP + STEP_GAP),
            start[1] + u[1] * i * (STEP + STEP_GAP),
        )
        mid = (near[0] + u[0] * STEP / 2, near[1] + u[1] * STEP / 2)
        clockwork.fragment(
            f"{name}_{i + 1}",
            block(mid, heading, width),
            first + rise * i,
            under=under,
        )
        middles.append(mid)
    return middles


def block(
    mid: Point, heading: float, width: float, length: float = STEP
) -> list[Point]:
    """Returns the outline of a box whose middle is `mid`, `length` m along `heading` (degrees
    from +x) and `width` m across it."""
    return kit.box(along(mid, heading, -length / 2), width, length, heading - 90.0)


def along(at: Point, heading: float, distance: float) -> Point:
    """Returns the plan point `distance` m from `at` along `heading` degrees."""
    a = math.radians(heading)
    return (at[0] + distance * math.cos(a), at[1] + distance * math.sin(a))


# --- 1. Face and gears ---------------------------------------------------------------------------

# The start floor: a broken piece of the tower's next storey, flush with the crown's south edge.
START_FLOOR = [
    (-4.2, 22.5),
    (6.0, 22.0),
    (6.6, 31.0),
    (6.0, 34.0),
    (-4.2, 34.0),
    (-4.8, 27.0),
]
clockwork.fragment("start_floor", START_FLOOR, CROWN, under=4.0)
START: Place = (0.9, 27.6, CROWN)

# The west way: three stair fragments west to the low rim of the clock face.
STAIR_Y = 28.8
STAIR_X = -4.95
STAIRS = step_row("face_stair", (STAIR_X, STAIR_Y), 180.0, CROWN + 1.0, 3, width=3.2)
STAIR_END = STAIR_X - 3 * STEP - 2 * STEP_GAP

# The clock face: a dial FACE_R m across the hub, tipped FACE_TILT degrees so that XII (the high
# rim) is to the north-west and VI (the low rim) to the south-east, where the stairs arrive.
FACE_R = 10.5
FACE_TILT = 16.0
FACE_YAW = 45.0
FACE_LOW = CROWN + 4.0
FACE_Z = FACE_LOW + FACE_R * math.sin(math.radians(FACE_TILT))
_low_plan = FACE_R * math.cos(math.radians(FACE_TILT))
FACE: Place = (
    STAIR_END - STEP_GAP - _low_plan * math.cos(math.radians(-45.0)),
    STAIR_Y - _low_plan * math.sin(math.radians(-45.0)),
    FACE_Z,
)
FACE_POSE = clockwork.frame(FACE, FACE_YAW, FACE_TILT)
# The holes in the dial: the hub, where the axle was, and the winding hole at four o'clock.
HUB_HOLE = 0.5
WIND_HOLE = 0.7
WIND_AT = (5.2 * math.sin(math.radians(120.0)), 5.2 * math.cos(math.radians(120.0)))
# The bezel's gaps: at VI for the stairs and at XII for the vent landing, degrees of the dial
# (0 at XII, clockwise).
BEZEL_GAPS = {"vi": (180.0, 13.0), "xii": (0.0, 9.0)}


def dial_angle(clock: float) -> float:
    """Returns the plan angle (from +x, counter-clockwise, in the dial's own frame) of a dial
    angle `clock` (0 at XII, clockwise)."""
    return 90.0 - clock


def on_face(local: Point, lift: float = 0.0) -> Place:
    """Returns the world point of a point of the dial's own frame, `lift` m above the dial."""
    p = FACE_POSE @ Vector((local[0], local[1], lift))
    return (p.x, p.y, p.z)


def build_face() -> None:
    """Builds the clock face flat round the origin, then tips it into FACE_POSE."""
    before = clockwork.names()
    holes = [
        kit.arc((0.0, 0.0), HUB_HOLE, 0.0, 360.0, 32),
        kit.arc(WIND_AT, WIND_HOLE, 0.0, 360.0, 32),
    ]
    outline = kit.arc((0.0, 0.0), FACE_R, 0.0, 360.0, 144)
    kit.deck(
        outline,
        0.0,
        0.6,
        holes=holes,
        through=True,
        name="face_dial",
        material="limestone",
    )
    # The chapter ring: two brass rings, hour bars, and black minute marks between them.
    for r0, r1, tag in ((8.35, 8.5, "inner"), (9.75, 9.9, "outer")):
        kit.inlay(
            kit.arc((0.0, 0.0), r1, 0.0, 360.0, 144),
            0.0,
            holes=[kit.arc((0.0, 0.0), r0, 0.0, 360.0, 144)],
            name=f"face_chapter_{tag}",
            material="polished_brass",
        )
    for minute in range(60):
        a = math.radians(dial_angle(minute * 6.0))
        hour = minute % 5 == 0
        r0, r1, w = (8.55, 9.7, 0.34) if hour else (9.25, 9.7, 0.07)
        c, s = math.cos(a), math.sin(a)
        n = (-s * w / 2, c * w / 2)
        kit.inlay(
            [
                (c * r0 + n[0], s * r0 + n[1]),
                (c * r0 - n[0], s * r0 - n[1]),
                (c * r1 - n[0], s * r1 - n[1]),
                (c * r1 + n[0], s * r1 + n[1]),
            ],
            0.0,
            name=f"face_mark_{minute:02d}",
            material="polished_brass" if hour else "gold",
        )
    # The numerals that stayed on the dial; the five near XII broke off and float as the
    # numeral stones.
    for hour, text in (
        (3, "III"),
        (4, "IIII"),
        (5, "V"),
        (6, "VI"),
        (7, "VII"),
        (8, "VIII"),
        (9, "IX"),
    ):
        clock = hour * 30.0
        x, y = ring(7.0, dial_angle(clock), (0.0, 0.0))
        clockwork.numeral(f"face_numeral_{hour}", text, (x, y, 0.0), 1.1, -clock)
    # The hub: a brass boss round the axle hole, and a brass ring round the winding hole.
    kit.inlay(
        kit.arc((0.0, 0.0), 1.25, 0.0, 360.0, 48),
        0.0,
        holes=[holes[0]],
        name="face_hub",
        material="polished_brass",
    )
    kit.inlay(
        kit.arc(WIND_AT, WIND_HOLE + 0.22, 0.0, 360.0, 48),
        0.0,
        holes=[holes[1]],
        name="face_winding",
        material="polished_brass",
    )
    # The bezel: a brass kerb round the rim, open at VI and at XII.
    gaps = sorted(
        (dial_angle(c) - w, dial_angle(c) + w) for c, w in BEZEL_GAPS.values()
    )
    spans = [(gaps[0][1], gaps[1][0]), (gaps[1][1], gaps[0][0] + 360.0)]
    for i, (a0, a1) in enumerate(spans):
        path = [(x, y, 0.0) for x, y in kit.arc((0.0, 0.0), FACE_R, a0, a1, 64)]
        kit.wall(
            path,
            0.35,
            width=0.4,
            side="right",
            bevel=0.08,
            name=f"face_bezel_{i + 1}",
            material="polished_brass",
        )
    clockwork.place(clockwork.roots(before), FACE_POSE)


build_face()

# The dial is tipped, so a level piece that meets it follows this plane: the height of the dial's
# top over a plan point.
_FACE_RISE = (
    -math.tan(math.radians(FACE_TILT)) * math.sin(math.radians(FACE_YAW)),
    math.tan(math.radians(FACE_TILT)) * math.cos(math.radians(FACE_YAW)),
)


def face_top(p: Point) -> float:
    """Returns the height of the dial's top plane over the plan point p."""
    return FACE[2] + (p[0] - FACE[0]) * _FACE_RISE[0] + (p[1] - FACE[1]) * _FACE_RISE[1]


# The XII landing: a level stone shelf past the gap in the bezel, with the vent to the numeral
# stones. Its edge on the dial side follows the rim.
XII = on_face((0.0, FACE_R))
_nw = (-math.sin(math.radians(FACE_YAW)), math.cos(math.radians(FACE_YAW)))
_rim = [
    on_face(ring(FACE_R, dial_angle(c), (0.0, 0.0)))
    for c in (12.0, 6.0, 0.0, -6.0, -12.0)
]
XII_LANDING = [
    *[(x, y) for x, y, _ in _rim],
    (_rim[-1][0] + _nw[0] * 3.8, _rim[-1][1] + _nw[1] * 3.8),
    (_rim[0][0] + _nw[0] * 3.8, _rim[0][1] + _nw[1] * 3.8),
]
clockwork.fragment("face_xii_landing", XII_LANDING, XII[2], under=2.2)
VENT_XII: Place = (XII[0] + _nw[0] * 1.7, XII[1] + _nw[1] * 1.7, XII[2])
kit.marker("steam_vent", at=VENT_XII, lift=9.5, name="vent_xii")

# The numeral stones: five numerals that broke off near XII float in an arc round the face, each
# 1 m above the one before, from +168 to +172. The bell ledge comes next.
STONE_R = 14.65
STONE_FIRST = 135.0
STONE_PITCH = math.degrees((STEP + STEP_GAP) / STONE_R)
STONES = []
for i, text in enumerate(("X", "XI", "XII", "I", "II")):
    angle = STONE_FIRST - i * STONE_PITCH
    mid = ring(STONE_R, angle, (FACE[0], FACE[1]))
    top = 168.0 + i
    clockwork.fragment(
        f"numeral_stone_{i + 1}", block(mid, angle - 90.0, 3.0), top, under=2.4
    )
    clockwork.numeral(
        f"numeral_stone_{i + 1}_mark", text, (*mid, top), 1.0, angle - 90.0
    )
    STONES.append((mid, top, angle))

# The movement chamber under the hub: the marble that drops through the hub hole lands by the
# egg; a small vent under the winding hole lifts it back onto the face.
HUB: Place = FACE
WIND = on_face(WIND_AT)
CHAMBER_FLOOR = CROWN + 2.0
_cu = (WIND[0] - HUB[0], WIND[1] - HUB[1])
_cl = math.hypot(*_cu)
_cu = (_cu[0] / _cl, _cu[1] / _cl)
_cv = (-_cu[1], _cu[0])


def chamber_point(u: float, v: float) -> Point:
    """Returns the plan point at u m from the hub toward the winding hole and v m to its left."""
    return (HUB[0] + _cu[0] * u + _cv[0] * v, HUB[1] + _cu[1] * u + _cv[1] * v)


CHAMBER = (-2.2, _cl + 2.0, -2.2, 2.2)  # u0, u1, v0, v1: the inside


def build_chamber() -> None:
    """Builds the movement chamber: a stone floor and four walls whose tops follow the dial's
    underside, so that no light shows between them."""
    u0, u1, v0, v1 = CHAMBER
    wall = 0.45
    parts = town.Parts()
    bm = parts.bm
    under = 0.6 / math.cos(math.radians(FACE_TILT))

    def column(p: Point, bottom: float) -> tuple:
        return (
            bm.verts.new((p[0], p[1], bottom)),
            bm.verts.new((p[0], p[1], face_top(p) - under + 0.02)),
        )

    outer = [
        chamber_point(u, v)
        for u, v in (
            (u0 - wall, v0 - wall),
            (u1 + wall, v0 - wall),
            (u1 + wall, v1 + wall),
            (u0 - wall, v1 + wall),
        )
    ]
    inner = [chamber_point(u, v) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
    bottom = CHAMBER_FLOOR - 0.6
    o = [column(p, bottom) for p in outer]
    n = [column(p, CHAMBER_FLOOR) for p in inner]
    for i in range(4):
        j = (i + 1) % 4
        parts.faces([[o[i][0], o[j][0], o[j][1], o[i][1]]], "wall")
        parts.faces([[n[j][0], n[i][0], n[i][1], n[j][1]]], "dressed")
        parts.faces([[o[i][1], o[j][1], n[j][1], n[i][1]]], "dressed")
    parts.faces([[o[3][0], o[2][0], o[1][0], o[0][0]]], "wall")
    parts.faces([[n[0][0], n[1][0], n[2][0], n[3][0]]], "limestone")
    for i in range(4):
        j = (i + 1) % 4
        parts.faces([[o[i][0], n[i][0], n[j][0], o[j][0]]], "wall")
    parts.add("movement_chamber")


build_chamber()
EGG: Place = (*chamber_point(-0.9, 0.0), CHAMBER_FLOOR)
kit.marker("egg", at=EGG)
CHAMBER_VENT: Place = (WIND[0], WIND[1], CHAMBER_FLOOR)
kit.marker(
    "steam_vent",
    at=CHAMBER_VENT,
    lift=WIND[2] - CHAMBER_FLOOR + 1.6,
    radius=0.5,
    name="vent_chamber",
)
_cm = chamber_point((CHAMBER[0] + CHAMBER[1]) / 2, 0.0)
kit.marker(
    "room_probe",
    at=(*_cm, CHAMBER_FLOOR),
    rotation=(0.0, 0.0, math.degrees(math.atan2(_cu[1], _cu[0])) - 90.0),
    width=CHAMBER[3] - CHAMBER[2],
    depth=CHAMBER[1] - CHAMBER[0],
    height=3.4,
    name="movement_chamber_probe",
)

# The east way: three flat gears east of the start floor, a landing, and the lift gear, which
# lets the marble off west at the top onto the walkway.
GEAR_Y = 29.0
FLAT_GEARS = {
    "gear_flat_1": (8.9, CROWN + 1.0),
    "gear_flat_2": (14.4, CROWN + 2.0),
    "gear_flat_3": (19.9, CROWN + 3.0),
}
FLAT_R = 2.6
for i, (name, (x, top)) in enumerate(FLAT_GEARS.items()):
    kit.marker(
        "turning_gear",
        at=(x, GEAR_Y, top),
        period=14.0,
        clockwise=i % 2 == 1,
        radius=FLAT_R,
        teeth=16,
        name=name,
    )
    kit.lathe(
        (x, GEAR_Y, top - 4.0),
        [(0.0, 0.0), (0.22, 0.0), (0.22, 3.45), (0.34, 3.5), (0.0, 3.5)],
        name=f"{name}_arbor",
        material="polished_brass",
        collide=False,
    )
LIFT_X = 24.0
GEAR_LANDING = CROWN + 4.0
clockwork.fragment(
    "gear_landing", kit.rect(22.8, 26.6, 25.6, 31.4), GEAR_LANDING, under=2.0
)
LIFT = town.lift(
    "gear_lift",
    (LIFT_X, 34.0, GEAR_LANDING + 3.8 + town.LIFT_GAP),
    3.8,
    yaw=90.0,
    exit=1,
    period=16.0,
    teeth=20,
)
town.block(
    "gear_lift_lane",
    (LIFT_X - 0.62, 31.4, GEAR_LANDING - 0.4),
    (LIFT_X + 0.62, 34.0, GEAR_LANDING),
    "limestone",
)
WALK = LIFT.exit
WALK_Y = (32.8, 35.2)
WALK_TURN_X = (2.6, 5.0)
clockwork.fragment(
    "walkway",
    [
        (LIFT_X - 0.65, WALK_Y[0]),
        (LIFT_X - 0.65, WALK_Y[1]),
        (WALK_TURN_X[1], WALK_Y[1]),
        (WALK_TURN_X[1], 41.0),
        (WALK_TURN_X[0], 41.0),
        (WALK_TURN_X[0], WALK_Y[0]),
    ],
    WALK,
    under=1.2,
    coping=0.35,
)
PENDULUM_WALK_X = 13.0
kit.marker(
    "pendulum",
    at=(PENDULUM_WALK_X, sum(WALK_Y) / 2, WALK + 4.6),
    period=4.0,
    swing=50.0,
    name="pendulum_walk",
)
# The weight lift: a clock weight that rides from the walkway's north end up to the bell ledge.
WEIGHT_X = sum(WALK_TURN_X) / 2
WEIGHT_LOW: Place = (WEIGHT_X, 42.7, WALK)
kit.marker(
    "moving_platform",
    at=WEIGHT_LOW,
    points=[(WEIGHT_X, 42.7, BELL_LEDGE)],
    period=8.0,
    stop=1.5,
    width=3.0,
    depth=3.0,
    name="weight_lift_1",
)

# The bell ledge: a broken piece of the bell floor at +173, and the brass floor of the mainspring
# barrel on its east side.
COIL: Place = (-1.0, 49.0, BELL_LEDGE)
_stone_end = ring(STONE_R, STONE_FIRST - 5 * STONE_PITCH, (FACE[0], FACE[1]))
BARREL_R = 6.2
BELL_LEDGE_OUTLINE = clockwork.union(
    [
        (_stone_end[0] - 1.2, 47.0),
        (-12.0, 44.4),
        (WALK_TURN_X[1] + 0.4, 44.4),
        (WALK_TURN_X[1] + 0.4, 47.5),
        (-3.0, 55.6),
        (-14.0, 56.2),
        (_stone_end[0] - 1.6, 52.8),
    ],
    (COIL[0], COIL[1]),
    BARREL_R,
)
clockwork.fragment("bell_ledge", BELL_LEDGE_OUTLINE, BELL_LEDGE, under=5.0)
# The foot of the mainspring barrel, set into the floor: a brass ring.
kit.inlay(
    kit.arc((COIL[0], COIL[1]), BARREL_R - 0.4, 0.0, 360.0, 96),
    BELL_LEDGE,
    holes=[kit.arc((COIL[0], COIL[1]), BARREL_R - 0.85, 0.0, 360.0, 96)],
    name="barrel_foot",
    material="polished_brass",
)


# --- 2. Mainspring -------------------------------------------------------------------------------

# The mainspring ramp: a band of blued steel that coils 5.5 half turns clockwise round COIL, from
# the north point of the barrel floor up to its west point at the barrel lid.
COIL_IN, COIL_OUT = 3.35, 5.85
COIL_MID = (COIL_IN + COIL_OUT) / 2
COIL_START = 90.0
COIL_TURN = -990.0
COIL_RISE = LID - BELL_LEDGE
clockwork.refinish(
    town.helix(
        COIL, COIL_IN, COIL_OUT, COIL_START, COIL_TURN, COIL_RISE, name="mainspring"
    ),
    "blued_steel",
)
clockwork.helix_wall(
    COIL,
    COIL_OUT,
    COIL_START,
    COIL_TURN,
    COIL_RISE,
    inside=True,
    name="mainspring_kerb",
)


def coil(along: float, radius: float = 4.75) -> Place:
    """Returns the point `along` degrees up the mainspring ramp from its start, at `radius`."""
    return town.helix_point(
        COIL, radius, COIL_START, COIL_TURN, COIL_RISE, COIL_START - along
    )


# The bell: it hangs inside the coil and swings along the ramp's inner half on the second turn,
# at the east point.
BELL_ALONG = 450.0
_bell = coil(BELL_ALONG, 4.0)
kit.marker(
    "pendulum",
    at=(_bell[0], _bell[1], _bell[2] + 4.6),
    rotation=(0.0, 0.0, 90.0),
    period=4.0,
    swing=50.0,
    name="pendulum_spring",
)
# The barrel lid: a brass disc 13 m across, cut straight where the ramp's end meets it, with the
# teeth of the barrel's great wheel round its edge.
LID_CENTRE: Place = (-7.0, 54.6, LID)
LID_R = 6.5
clockwork.disc(
    "barrel_lid", LID_CENTRE, LID_R, depth=0.7, clip=((0.0, COIL[1]), (1.0, 0.0))
)
_lid_cut = math.degrees(math.asin((COIL[1] - LID_CENTRE[1]) / LID_R))
_lid_arc = (180.0 - _lid_cut, 360.0 + _lid_cut)
kit.teeth(
    [
        (x, y, LID - 0.12)
        for x, y in kit.arc(LID_CENTRE[:2], LID_R, _lid_arc[1], _lid_arc[0], 120)
    ],
    side="left",
    pitch=0.7,
    name="barrel_lid_teeth",
    material="polished_brass",
)

# The west way: three vents in a row north from the bell ledge. Each lifts the marble over the
# next, and the last one onto a fragment beside the lid.
CHAIN_X = -15.0
CHAIN_VENTS = {
    "vent_chain_1": (48.5, BELL_LEDGE, 9.5),
    "vent_chain_2": (52.0, 181.0, 9.5),
    "vent_chain_3": (55.5, 189.0, 11.5),
}
for name, (y, z, lift) in CHAIN_VENTS.items():
    kit.marker("steam_vent", at=(CHAIN_X, y, z), lift=lift, name=name)
for i, (y, z, _) in enumerate(list(CHAIN_VENTS.values())[1:]):
    clockwork.fragment(
        f"chain_fragment_{i + 1}",
        kit.rect(CHAIN_X - 1.5, y - 1.1, CHAIN_X + 1.5, y + 4.3),
        z,
        under=1.4,
    )
CHAIN_TOP = LID - 1.0
_lid_side = kit.arc(LID_CENTRE[:2], LID_R + STEP_GAP, 155.5, 124.6, 8)
clockwork.fragment(
    "chain_fragment_3",
    [
        (CHAIN_X - 1.6, _lid_side[0][1] - 0.1),
        *_lid_side,
        (CHAIN_X - 1.6, _lid_side[-1][1]),
    ],
    CHAIN_TOP,
    under=2.2,
)

FINISH: Place = (-3.0, 56.5, LID)
FOOT[2] = (-8.0, 49.5, BELL_LEDGE)
kit.marker("start", at=START if TEST_FROM == 1 else FOOT[TEST_FROM])
kit.marker("finish", at=FINISH)

# --- Routes: part 1 -------------------------------------------------------------------------------

FIRST[1] = [
    ((5.5, GEAR_Y, CROWN), "jump; speed 3"),
]
for name, (x, top) in FLAT_GEARS.items():
    FIRST[1] += [
        ((x, GEAR_Y, top), "speed 3"),
        ((x + 1.7, GEAR_Y, top), "jump; speed 3"),
    ]
FIRST[1].append(((23.6, GEAR_Y, GEAR_LANDING), "speed 3"))
FIRST[1] += [
    ((LIFT_X, 30.4, GEAR_LANDING), "speed 2"),
    (LIFT.board, "speed 2"),
    (LIFT.side, "speed 1.5"),
    (LIFT.out, ""),
    ((PENDULUM_WALK_X + 5.5, 34.0, WALK), "speed 3; wait_until pendulum_walk 1.4 1.7"),
    ((sum(WALK_TURN_X) / 2, 34.0, WALK), "speed 6"),
    ((WEIGHT_X, 40.3, WALK), "speed 3; wait_until weight_lift_1 7.7 0.3"),
    (WEIGHT_LOW, "speed 2; wait_until weight_lift_1 4.0 5.2"),
    ((WEIGHT_X, 46.0, BELL_LEDGE), "speed 3"),
]
_se = (math.cos(math.radians(-45.0)), math.sin(math.radians(-45.0)))
_ne = (math.cos(math.radians(45.0)), math.sin(math.radians(45.0)))
EXPERT[1] = [
    ((STAIR_X + 0.95, STAIR_Y, CROWN), "jump; speed 3"),
]
for i, (x, y) in enumerate(STAIRS):
    EXPERT[1] += [
        ((x, y, CROWN + 1.0 + i), "speed 3"),
        ((x - 0.25, y, CROWN + 1.0 + i), "jump; speed 3"),
    ]
_vi = (FACE[0] + _se[0] * (_low_plan - 0.8), FACE[1] + _se[1] * (_low_plan - 0.8))
_by = (FACE[0] + _ne[0] * 2.0, FACE[1] + _ne[1] * 2.0)
_xi = (XII[0] - _nw[0] * 1.0, XII[1] - _nw[1] * 1.0)
EXPERT[1] += [
    ((*_vi, face_top(_vi)), "speed 4"),
    ((*_by, face_top(_by)), "speed 8"),
    ((*_xi, face_top(_xi)), "speed 4"),
    ((XII[0] + _nw[0] * 0.3, XII[1] + _nw[1] * 0.3, XII[2]), "speed 3"),
]
for i, (mid, top, angle) in enumerate(STONES):
    heading = angle - 90.0
    EXPERT[1].append(((*mid, top), "speed 1.5; wait 0.3" if i == 0 else "speed 2.5"))
    EXPERT[1].append(((*along(mid, heading, 0.55), top), "jump; speed 2.5"))
EXPERT[1] += [
    (
        (*ring(STONE_R, STONE_FIRST - 5 * STONE_PITCH, (FACE[0], FACE[1])), BELL_LEDGE),
        "speed 3",
    ),
]


# --- Routes: part 2 -------------------------------------------------------------------------------

FIRST[2] = [
    ((1.2, 49.0, BELL_LEDGE), "speed 3"),
    ((-3.6, 53.6, BELL_LEDGE), "speed 3"),
    (coil(5.0), "speed 5"),
]
_coil_points = [a for a in range(60, 990, 66) if abs(a - (BELL_ALONG - 45.0)) > 20.0]
_coil_points.append(int(BELL_ALONG - 45.0))
for a in sorted(_coil_points):
    FIRST[2].append(
        (
            coil(a),
            "wait_until pendulum_spring 0.1 0.4" if a == BELL_ALONG - 45.0 else "",
        )
    )
FIRST[2] += [(coil(975.0), ""), ((-5.6, 51.2, LID), "")]
EXPERT[2] = [
    ((CHAIN_X - 0.6, 46.3, BELL_LEDGE), "speed 3"),
    ((CHAIN_X, 47.3, BELL_LEDGE), "speed 3"),
    ((CHAIN_X, 58.6, CHAIN_TOP), "speed 3"),
    ((CHAIN_X + 1.6, 58.9, CHAIN_TOP), "jump; speed 3"),
    ((-10.5, 58.4, LID), "speed 3"),
]


def route(kind: str, legs: list[Leg]) -> None:
    """Places the route of `kind` through the legs, ending on the finish pad."""
    actions = [
        f"{i} {action.strip()}"
        for i, (_, text) in enumerate(legs)
        for action in text.split(";")
        if action.strip()
    ]
    legs = [*legs, (FINISH, "")]
    kit.marker(
        "route",
        at=START if TEST_FROM == 1 else FOOT[TEST_FROM],
        points=[point for point, _ in legs],
        name=f"route_{kind}",
        kind=kind,
        actions="; ".join(actions),
    )


# --- Both routes ---------------------------------------------------------------------------------

route(
    "first_run",
    [leg for part in sorted(FIRST) if part >= TEST_FROM for leg in FIRST[part]],
)
route(
    "expert",
    [leg for part in sorted(EXPERT) if part >= TEST_FROM for leg in EXPERT[part]],
)

# --- Shots ----------------------------------------------------------------------------------------

kit.shot("overview", at=(48.0, -30.0, 230.0), rotation=(-22.0, 0.0, 40.0))
kit.shot("start", at=(START[0], START[1] - 3.0, CROWN + 1.6), rotation=(8.0, 0.0, 0.0))
kit.shot(
    "finish",
    at=(FINISH[0] + 8.0, FINISH[1] - 8.0, BELL_LEDGE + 5.0),
    rotation=(-18.0, 0.0, 45.0),
)
kit.shot(
    "egg",
    at=(*chamber_point(CHAMBER[1] - 0.6, 0.0), CHAMBER_FLOOR + 1.3),
    rotation=(-12.0, 0.0, math.degrees(math.atan2(_cu[1], _cu[0])) + 90.0),
)
kit.shot("face", at=(2.0, 14.0, 162.0), rotation=(-12.0, 0.0, 40.0))
kit.shot("gears", at=(6.0, 18.0, 156.0), rotation=(-2.0, 0.0, -30.0))
kit.shot("debug_plan", at=(-4.0, 46.0, 215.0), rotation=(-90.0, 0.0, 0.0))
kit.shot("debug_ledge", at=(-4.0, 30.0, 182.0), rotation=(-20.0, 0.0, 0.0))
