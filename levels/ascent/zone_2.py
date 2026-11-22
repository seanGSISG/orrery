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

kit.level(title="The Broken Tower", par=253.8, gold=84.1, sky="ground_dawn")


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
WIND_HOLE = 0.85
WIND_AT = (5.2 * math.sin(math.radians(120.0)), 5.2 * math.cos(math.radians(120.0)))
# The hands: name, dial angle at run time 0, blade and tail outlines as (along, across) from
# the hub, m. They turn on the hub (build_hands()): they push a marble, which can jump them.
HAND_PERIOD = 20.0
HAND_HEIGHT = 0.25
HAND_LIFT = 0.05
# The hands show ten past ten this many seconds into the run, when the expert route of the zone
# on its own comes to the face (EXPERT[1]).
HAND_START = 3.0
HANDS = [
    (
        "minute",
        60.0,
        [(0.7, 0.16), (5.4, 0.12), (5.9, 0.32), (6.4, 0.12), (8.1, 0.0)]
        + [(6.4, -0.12), (5.9, -0.32), (5.4, -0.12), (0.7, -0.16)],
        [(-0.7, -0.16), (-0.7, 0.16), (-1.9, 0.34), (-2.15, 0.0), (-1.9, -0.34)],
    ),
    (
        "hour",
        305.0,
        [(0.7, 0.24), (3.6, 0.2), (4.2, 0.55), (4.8, 0.2), (5.4, 0.0)]
        + [(4.8, -0.2), (4.2, -0.55), (3.6, -0.2), (0.7, -0.24)],
        [(-0.7, -0.2), (-0.7, 0.2), (-1.4, 0.36), (-1.6, 0.0), (-1.4, -0.36)],
    ),
]
# The bezel's gaps: at VI for the stairs and at XII for the vent landing, degrees of the dial
# (0 at XII, clockwise).
BEZEL_GAPS = {"vi": (180.0, 13.0), "xii": (0.0, 9.0)}


def dial_angle(clock: float) -> float:
    """Returns the plan angle (from +x, counter-clockwise, in the dial's own frame) of a dial
    angle `clock` (0 at XII, clockwise)."""
    return 90.0 - clock


def on_face(local: Point, lift: float = 0.0) -> Place:
    """Returns the world point of a point of the dial's own frame, `lift` m above the dial."""
    return clockwork.at(FACE_POSE, (local[0], local[1], lift))


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
            material="brass_polished",
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
            material="brass_polished" if hour else "gold",
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
        material="brass_polished",
    )
    kit.inlay(
        kit.arc(WIND_AT, WIND_HOLE + 0.22, 0.0, 360.0, 48),
        0.0,
        holes=[holes[1]],
        name="face_winding",
        material="brass_polished",
    )
    # The collar of the hands round the axle hole (the hands are turning arms: build_hands()).
    kit.inlay(
        kit.arc((0.0, 0.0), 0.85, 0.0, 360.0, 48),
        0.03,
        holes=[holes[0]],
        name="face_hand_collar",
        material="blued_steel",
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
            material="brass_polished",
        )
    clockwork.place(clockwork.roots(before), FACE_POSE)


build_face()


def build_hands() -> None:
    """Places the hands: each blade and each tail is a turning_arm of blued steel that stands
    HAND_HEIGHT m tall, HAND_LIFT m above the dial, and turns clockwise round the hub once in
    HAND_PERIOD s. They show ten past ten at HAND_START s. The two hands turn together, so the
    gap between them stays open; there is no hand over the hub hole."""
    for tag, clock, blade, tail in HANDS:
        a = math.radians(dial_angle(clock - 360.0 * HAND_START / HAND_PERIOD))
        c, s = math.cos(a), math.sin(a)
        for part, shape in (("blade", blade), ("tail", tail)):
            kit.marker(
                "turning_arm",
                at=on_face((0.0, 0.0), HAND_LIFT),
                rotation=(FACE_TILT, 0.0, FACE_YAW),
                points=[
                    on_face((u * c - v * s, u * s + v * c), HAND_LIFT) for u, v in shape
                ],
                name=f"face_hand_{tag}_{part}",
                period=HAND_PERIOD,
                clockwise=True,
                height=HAND_HEIGHT,
                finish="blued_steel",
            )


build_hands()

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
    """Builds the movement chamber: a stone floor and four walls of coursed ashlar whose tops
    follow the dial's underside, so that no light shows between them."""
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
        parts.faces([[n[j][0], n[i][0], n[i][1], n[j][1]]], "wall")
        parts.faces([[o[i][1], o[j][1], n[j][1], n[i][1]]], "dressed")
    parts.faces([[o[3][0], o[2][0], o[1][0], o[0][0]]], "wall")
    parts.faces([[n[0][0], n[1][0], n[2][0], n[3][0]]], "limestone")
    for i in range(4):
        j = (i + 1) % 4
        parts.faces([[o[i][0], n[i][0], n[j][0], o[j][0]]], "wall")
    parts.add("movement_chamber")


build_chamber()
# Two wheels of the movement on the chamber's side walls, above the marble's reach. A wheel
# faces -y before its yaw, so this yaw turns its face away from the wall at v = +2.2 m.
_wall_yaw = math.degrees(math.atan2(-_cv[0], _cv[1]))
for _name, (_u, _v, _up, _r, _teeth, _yaw) in {
    "chamber_wheel_1": (1.4, CHAMBER[3] - 0.05, 1.7, 0.9, 18, _wall_yaw),
    "chamber_wheel_2": (3.1, CHAMBER[2] + 0.05, 1.5, 0.65, 14, _wall_yaw + 180.0),
}.items():
    kit.gear(
        (*chamber_point(_u, _v), CHAMBER_FLOOR + _up),
        _r,
        teeth=_teeth,
        depth=0.25,
        yaw=_yaw,
        name=_name,
        material="brass_polished",
    )
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
# The probe's box reaches RoomProbe.REACH (0.45 m) past this height. Its top, +154.75 m, stays
# below the dial's top over the whole box (lowest +155.2 m), so no room light shows on the face.
CHAMBER_PROBE = 2.3
kit.marker(
    "room_probe",
    at=(*_cm, CHAMBER_FLOOR),
    rotation=(0.0, 0.0, math.degrees(math.atan2(_cu[1], _cu[0])) - 90.0),
    width=CHAMBER[3] - CHAMBER[2],
    depth=CHAMBER[1] - CHAMBER[0],
    height=CHAMBER_PROBE,
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
        material="brass_polished",
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
# The foot of the mainspring barrel, set into the floor: a ring of the kit's brass.
kit.inlay(
    kit.arc((COIL[0], COIL[1]), BARREL_R - 0.4, 0.0, 360.0, 96),
    BELL_LEDGE,
    holes=[kit.arc((COIL[0], COIL[1]), BARREL_R - 0.85, 0.0, 360.0, 96)],
    name="barrel_foot",
    material="brass",
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
# The barrel lid: a stone disc 13 m across, cut straight where the ramp's end meets it, with the
# polished brass teeth of the barrel's great wheel round its edge.
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
    material="brass_polished",
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


# --- 3. Shards and rod ---------------------------------------------------------------------------

# The Dial ring: the brass rim of a second dial, flat in the air round the axis, 50 m across.
RING_IN, RING_OUT = 23.0, 27.0
RING_MID = (RING_IN + RING_OUT) / 2
# Where the two ways of part 3 arrive, degrees round the axis: the west way (and the vent chain
# of part 4) at RING_WEST, the east way (and the roof slabs of part 4) at RING_EAST.
RING_WEST, RING_EAST = 156.0, -25.0

# The west way: six steps south from the lid, a lift, five steps west, a vent ledge, a ledge,
# and six steps that follow the ring's outside round to RING_WEST.
SHARD_X = -9.0
SHARDS_1 = step_row("shard_a", (SHARD_X, COIL[1] - STEP_GAP), 270.0, LID + 1.0, 6)
SHARD_LIFT: Place = (SHARD_X, SHARDS_1[-1][1] - STEP / 2 - 0.15 - 1.5, LID + 6.0)
kit.marker(
    "moving_platform",
    at=SHARD_LIFT,
    points=[(SHARD_LIFT[0], SHARD_LIFT[1], LID + 14.0)],
    period=10.0,
    stop=1.5,
    width=3.0,
    depth=3.0,
    name="lift_shards",
)
SHARD_Y = SHARD_LIFT[1]
SHARDS_2 = step_row("shard_b", (SHARD_X - 1.5 - 0.15, SHARD_Y), 180.0, LID + 15.0, 5)
SHARD_VENT_LEDGE = LID + 20.0
_vl_east = SHARDS_2[-1][0] - STEP / 2 - STEP_GAP
clockwork.fragment(
    "shard_vent_ledge",
    kit.rect(-29.4, 27.0, _vl_east, SHARD_Y + 1.5),
    SHARD_VENT_LEDGE,
    under=2.0,
)
SHARD_VENT_AT = 196.5
SHARD_VENT: Place = (*ring(28.8, SHARD_VENT_AT), SHARD_VENT_LEDGE)
kit.marker("steam_vent", at=SHARD_VENT, lift=9.5, name="vent_shards")
SHARD_TOP = LID + 28.0
clockwork.fragment(
    "shard_landing",
    clockwork.sector(AXIS, 27.3, 30.3, 185.0, 193.6),
    SHARD_TOP,
    under=1.8,
)
_s3_step = math.degrees(STEP / 28.8)
_s3_gap = math.degrees(STEP_GAP / 28.8)
SHARDS_3 = []
for i in range(6):
    a0 = 185.0 - _s3_gap - i * (_s3_step + _s3_gap)
    clockwork.fragment(
        f"shard_c_{i + 1}",
        clockwork.sector(AXIS, 27.3, 30.3, a0 - _s3_step, a0),
        SHARD_TOP + 1.0 + i,
        under=1.6,
    )
    SHARDS_3.append(a0 - _s3_step / 2)

# The east way: the fallen pendulum rod, a beam of the kit's brass with a stone top (a long flat
# of brass that faces the sky mirrors the sun), from the lid's rim up to its bob, then a
# straight chain of three vents and three steps round the ring's inside to RING_EAST.
BOB_CENTRE: Place = (17.46, 49.0, LID + 7.0)
_rod_u = (BOB_CENTRE[0] - LID_CENTRE[0], BOB_CENTRE[1] - LID_CENTRE[1])
_rod_len = math.hypot(*_rod_u)
_rod_u = (_rod_u[0] / _rod_len, _rod_u[1] / _rod_len)
ROD_HEADING = math.degrees(math.atan2(_rod_u[1], _rod_u[0]))
ROD_LENGTH = 17.5
ROD_RISE = BOB_CENTRE[2] - LID
ROD_RUN = math.sqrt(ROD_LENGTH**2 - ROD_RISE**2)
ROD_FOOT: Place = (
    LID_CENTRE[0] + _rod_u[0] * LID_R,
    LID_CENTRE[1] + _rod_u[1] * LID_R,
    LID,
)
BOB_R = 3.0
_bob = along(ROD_FOOT[:2], ROD_HEADING, ROD_RUN + BOB_R)
BOB: Place = (*_bob, BOB_CENTRE[2])
clockwork.retop(
    kit.ramp(
        at=ROD_FOOT,
        width=1.2,
        length=ROD_RUN,
        rise=ROD_RISE,
        yaw=ROD_HEADING - 90.0,
        name="pendulum_rod",
        material="brass",
        trim="",
    ),
    "limestone",
)
clockwork.disc("pendulum_bob", BOB, BOB_R, depth=0.9)
clockwork.rim("pendulum_bob_rim", BOB, BOB_R, 0.9, width=0.1)
ROD_VENT_HEADING = -75.0
_rd = (
    math.cos(math.radians(ROD_VENT_HEADING)),
    math.sin(math.radians(ROD_VENT_HEADING)),
)
ROD_VENTS: list[Place] = []
for i, z in enumerate((BOB[2], LID + 15.0, LID + 23.0)):
    at = (BOB[0] + _rd[0] * (1.5 + 3.5 * i), BOB[1] + _rd[1] * (1.5 + 3.5 * i))
    kit.marker("steam_vent", at=(*at, z), lift=9.5, name=f"vent_rod_{i + 1}")
    ROD_VENTS.append((*at, z))
    if i > 0:
        clockwork.fragment(
            f"rod_ledge_{i}",
            block(along(at, ROD_VENT_HEADING, 1.6), ROD_VENT_HEADING, 3.0, 5.4),
            z,
            under=1.5,
        )
ROD_TOP = LID + 31.0
_rod_land = along(ROD_VENTS[-1][:2], ROD_VENT_HEADING, 3.0)
_land_angle = math.degrees(math.atan2(_rod_land[1] - AXIS[1], _rod_land[0] - AXIS[0]))
clockwork.fragment(
    "rod_landing",
    clockwork.sector(AXIS, 18.7, 21.7, _land_angle - 4.5, _land_angle + 4.5),
    ROD_TOP,
    under=1.8,
)
_e_step = math.degrees(STEP / 21.2)
_e_gap = math.degrees(STEP_GAP / 21.2)
ROD_STEPS = []
for i in range(3):
    a0 = _land_angle - 4.5 - _e_gap - i * (_e_step + _e_gap)
    clockwork.fragment(
        f"rod_step_{i + 1}",
        clockwork.sector(AXIS, 19.7, RING_IN - STEP_GAP, a0 - _e_step, a0),
        ROD_TOP + 1.0 + i,
        under=1.6,
    )
    ROD_STEPS.append(a0 - _e_step / 2)

# The ring: a stone chapter ring 4 m wide, with a polished brass bead on each edge, open where
# the ways meet it.
kit.deck(
    kit.arc(AXIS, RING_OUT, 0.0, 360.0, 240),
    RING,
    0.8,
    holes=[kit.arc(AXIS, RING_IN, 0.0, 360.0, 240)],
    through=True,
    name="dial_ring",
)
RING_GAPS = [(RING_WEST, 9.0), (RING_EAST, 9.0)]
for edge, r, side in (("outer", RING_OUT, "right"), ("inner", RING_IN, "left")):
    spans = [
        (RING_EAST + 9.0, RING_WEST - 9.0),
        (RING_WEST + 9.0, RING_EAST + 360.0 - 9.0),
    ]
    for k, (a0, a1) in enumerate(spans):
        kit.wall(
            [(x, y, RING) for x, y in kit.arc(AXIS, r, a0, a1, int((a1 - a0) / 2))],
            0.28,
            width=0.3,
            side="left" if side == "right" else "right",
            bevel=0.06,
            name=f"dial_ring_bead_{edge}_{k + 1}",
            material="brass_polished",
        )
for hour in range(12):
    a = 90.0 - hour * 30.0
    c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
    kit.inlay(
        block(
            (AXIS[0] + c * RING_MID, AXIS[1] + s_ * RING_MID),
            a,
            0.5 if hour % 3 else 0.9,
            2.6,
        ),
        RING,
        name=f"dial_ring_hour_{hour:02d}",
        material="blued_steel",
    )

# --- 4. Bells and slabs --------------------------------------------------------------------------

# The roof slab: the broken top of the belfry roof at +270, round the axis, with a wing to the
# west-south-west where the vent chain and the weight lift arrive.
ROOF_WING_X = -12.6
# The west edge of the wing, and the east edge of the floor west of it.
ROOF_WEST_X = -24.6
ROOF_CORE = [
    (12.4, 35.0),
    (12.9, 41.5),
    (10.0, 48.6),
    (4.0, 51.8),
    (-4.2, 51.4),
    (-10.2, 47.8),
    (ROOF_WING_X, 41.0),
    (ROOF_WING_X, 29.0),
    (-9.4, 27.0),
    (-3.8, 26.0),
    (4.2, 26.4),
    (10.2, 29.6),
]
clockwork.fragment("roof_slab", ROOF_CORE, ROOF, under=6.0)

# The west way: four vents in a row south above the ring's west side; the strongest throws the
# marble onto the roof slab's wing.
CHAIN2_X = -22.2
CHAIN2 = [
    (*ring(24.3, RING_WEST), RING, 9.5),
]
for i, z in enumerate((243.0, 251.0, 259.0)):
    CHAIN2.append((CHAIN2_X, CHAIN2[0][1] - 3.5 * (i + 1), z, 9.5 if i < 2 else 12.5))
CHAIN2[0] = (CHAIN2_X, CHAIN2[0][1], RING, 9.5)
for i, (x, y, z, lift) in enumerate(CHAIN2):
    kit.marker("steam_vent", at=(x, y, z), lift=lift, name=f"vent_bells_{i + 1}")
    if i > 0:
        clockwork.fragment(
            f"bells_ledge_{i}",
            kit.rect(x - 1.5, y - 4.3, x + 1.5, y + 1.1),
            z,
            under=1.3,
        )

# The east way: four roof slabs of slate that climb clockwise round above the ring from
# RING_EAST, with a flat ridge stone after each, and two bells that swing along the middle two.
# The slabs have no trim, so each reads as a piece of roof; the slate's courses run across the
# slope (along the ramp's x).
SLAB_R = 25.2
SLAB_RUN = 11.0
SLAB_RISE = 4.0
SLAB_SPAN = 2.0 * math.degrees(math.asin(SLAB_RUN / 2.0 / SLAB_R))
RIDGE_SPAN = 5.6
SLABS: list[tuple[Place, Place]] = []
# The angle where each slab ends and its ridge stone starts.
SLAB_ANGLES: list[float] = []
_a = RING_EAST - 6.0
for i in range(4):
    z0 = RING + SLAB_RISE * i
    p0, p1 = ring(SLAB_R, _a), ring(SLAB_R, _a - SLAB_SPAN)
    heading = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    clockwork.refinish(
        kit.ramp(
            at=(*p0, z0),
            width=3.4,
            length=SLAB_RUN,
            rise=SLAB_RISE,
            yaw=heading - 90.0,
            name=f"roof_slab_{i + 1}",
            trim="",
        ),
        "slate",
    )
    SLABS.append(((*p0, z0), (*p1, z0 + SLAB_RISE)))
    _a -= SLAB_SPAN
    clockwork.fragment(
        f"roof_ridge_{i + 1}",
        clockwork.sector(AXIS, SLAB_R - 1.9, SLAB_R + 1.5, _a - RIDGE_SPAN, _a),
        z0 + SLAB_RISE,
        under=1.0,
    )
    if i in (1, 2):
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        kit.marker(
            "pendulum",
            at=(*mid, z0 + SLAB_RISE / 2 + 4.6),
            rotation=(0.0, 0.0, heading),
            period=4.0,
            swing=45.0,
            name=f"pendulum_slab_{i}",
        )
    SLAB_ANGLES.append(_a)
    _a -= RIDGE_SPAN
# The weight lift: from the last ridge stone up beside the roof slab's wing. The deck's near side
# runs along the ridge stone's end, 0.05 m off, because a gap as wide as the marble catches it.
# The wing's edge follows the deck's inner side. _wr points out from the axis, _wt clockwise.
WEIGHT_2_R = 24.0
_wr = (math.cos(math.radians(_a)), math.sin(math.radians(_a)))
_wt = (_wr[1], -_wr[0])
_w = ring(WEIGHT_2_R, _a)
WEIGHT_2_LOW: Place = (
    _w[0] + _wt[0] * 1.55,
    _w[1] + _wt[1] * 1.55,
    RING + 4 * SLAB_RISE,
)
kit.marker(
    "moving_platform",
    at=WEIGHT_2_LOW,
    rotation=(0.0, 0.0, _a - 90.0),
    points=[(*WEIGHT_2_LOW[:2], ROOF)],
    period=16.0,
    stop=3.0,
    width=3.0,
    depth=3.0,
    name="weight_lift_2",
)
_inner = [
    (
        WEIGHT_2_LOW[0] - _wr[0] * 1.6 + _wt[0] * k * 1.5,
        WEIGHT_2_LOW[1] - _wr[1] * 1.6 + _wt[1] * k * 1.5,
    )
    for k in (1.0, -1.0)
]
# Near the last vent the wing's north edge stays 2.8 m south of it: a marble that the vent
# throws south at 3 m/s is still below the roof's top 2 m from the vent.
ROOF_WING_Y = CHAIN2[-1][1] - 2.8
ROOF_WING = [
    *_inner,
    (ROOF_WING_X, 29.0),
    (ROOF_WING_X, 40.0),
    (-21.0, ROOF_WING_Y),
    (ROOF_WEST_X, ROOF_WING_Y),
    (ROOF_WEST_X, 31.3),
]
clockwork.fragment("roof_slab_wing", ROOF_WING, ROOF, under=2.0)

# --- 5. The spire --------------------------------------------------------------------------------

# The spire: eight sides of slate round the axis, broken off flat under the cap. The cap is the
# round floor at the top of the climb, where zone 3 starts (docs/levels/ascent-z2.md, As built).
CAP_R = 5.0
CAP_DEPTH = 0.7
clockwork.spire("spire", (*AXIS, ROOF - 0.5), 4.0, 3.2, CAP - CAP_DEPTH - ROOF + 0.5)
clockwork.disc("spire_cap", (*AXIS, CAP), CAP_R, depth=CAP_DEPTH, finish="limestone")
# The rim leaves out the cap's south edge, where zone 3's quay meets the cap at +300 m: its
# outer edge stays north of y = 35.0 (Handover to zone 3).
clockwork.rim(
    "spire_cap_rim", (*AXIS, CAP), CAP_R, CAP_DEPTH, width=0.12, span=(-50.0, 230.0)
)

# The spire ramp: a slate band that winds four half turns clockwise round the spire, from the
# north point of the roof slab up to the north point of the balcony.
SPIRE_IN, SPIRE_OUT = 4.3, 6.8
SPIRE_START = 90.0
SPIRE_TURN = -720.0
BALCONY = 292.0
SPIRE_AT: Place = (*AXIS, ROOF)
clockwork.refinish(
    town.helix(
        SPIRE_AT,
        SPIRE_IN,
        SPIRE_OUT,
        SPIRE_START,
        SPIRE_TURN,
        BALCONY - ROOF,
        name="spire_ramp",
    ),
    "slate",
)
for radius, inside in ((SPIRE_IN, False), (SPIRE_OUT, True)):
    clockwork.helix_wall(
        SPIRE_AT,
        radius,
        SPIRE_START,
        SPIRE_TURN,
        BALCONY - ROOF,
        inside=inside,
        name=f"spire_ramp_kerb_{'in' if not inside else 'out'}",
    )


def spire_ramp(along: float, radius: float = 6.0) -> Place:
    """Returns the point `along` degrees up the spire ramp from its foot, at `radius`."""
    return town.helix_point(
        SPIRE_AT, radius, SPIRE_START, SPIRE_TURN, BALCONY - ROOF, SPIRE_START - along
    )


# The balcony: a broken floor east of the spire at the ramp's top. The marble rolls round the
# spire vent and into it westward, and the vent throws it onto the cap's east half.
clockwork.fragment(
    "spire_balcony",
    clockwork.sector(AXIS, 3.1, 13.0, -45.0, 90.0),
    BALCONY,
    under=1.0,
)
SPIRE_VENT: Place = (8.0, AXIS[1], BALCONY)
kit.marker("steam_vent", at=SPIRE_VENT, lift=11.5, name="vent_spire")

# The lightning rod way: a vent west off the roof slab's wing, a loose slope of slate north, a
# vent east, then the fallen lightning rod, 0.8 m wide, from its ledge up to the cap's west
# edge at ROD_ANGLE round the axis. Floors at +270 under the way catch a fall.
ROOF_WEST = [(-37.0, 30.8), (ROOF_WEST_X, 31.3), (ROOF_WEST_X, 50.5), (-36.5, 50.5)]
clockwork.fragment("roof_slab_west", ROOF_WEST, ROOF, under=3.0)
clockwork.fragment(
    "roof_slab_north",
    [
        (ROOF_WEST_X, 41.6),
        (ROOF_WING_X, 41.0),
        (-10.2, 47.8),
        (-16.0, 50.5),
        (ROOF_WEST_X, 50.5),
    ],
    ROOF,
    under=3.0,
)
BOLT_1: Place = (-26.6, 33.4, ROOF)
kit.marker("steam_vent", at=BOLT_1, lift=11.5, name="vent_lightning_1")
BOLT_LEDGE = 280.0
clockwork.fragment("lightning_ledge_1", kit.rect(-37.0, 31.0, -29.5, 36.5), BOLT_LEDGE)
BOLT_X = -33.7
BOLT_RISE = 4.0
BOLT_SLOPE = 34.0
_slope_run = BOLT_RISE / math.tan(math.radians(BOLT_SLOPE))
# Tiles 1.2 m long that break 0.7 s after a touch: a marble that climbs at 1.7 m/s or more gets
# up, and one that stops on the slope drops to the floor below.
kit.marker(
    "crumbling_tiles",
    at=(BOLT_X, 36.5 + _slope_run / 2, BOLT_LEDGE + BOLT_RISE / 2),
    rotation=(BOLT_SLOPE, 0.0, 0.0),
    width=3.6,
    depth=BOLT_RISE / math.sin(math.radians(BOLT_SLOPE)),
    tile=1.2,
    delay=0.7,
    name="lightning_slope",
)
BOLT_TOP = BOLT_LEDGE + BOLT_RISE
BOLT_TOP_Y = 36.5 + _slope_run
clockwork.fragment(
    "lightning_ledge_2", kit.rect(-37.0, BOLT_TOP_Y, -27.9, 50.2), BOLT_TOP
)
ROD_ANGLE = 160.0
_rod = ring(CAP_R + 19.0, ROD_ANGLE)
ROD_FOOT_2: Place = (*_rod, BALCONY)
ROD_TOP_2: Place = (*ring(CAP_R, ROD_ANGLE), CAP)
_rod_d = ((ROD_TOP_2[0] - _rod[0]) / 19.0, (ROD_TOP_2[1] - _rod[1]) / 19.0)
# The marble lands 2.8 m before the rod's foot, on the rod's line; the second vent throws it
# east from 4.1 m west of there.
BOLT_LAND: Place = (_rod[0] - _rod_d[0] * 2.8, _rod[1] - _rod_d[1] * 2.8, BALCONY)
BOLT_2: Place = (BOLT_LAND[0] - 4.1, BOLT_LAND[1], BOLT_TOP)
kit.marker("steam_vent", at=BOLT_2, lift=9.5, name="vent_lightning_2")
clockwork.fragment(
    "lightning_ledge_3",
    kit.rect(BOLT_2[0] + 1.9, BOLT_LAND[1] - 2.9, _rod[0] + 0.6, BOLT_LAND[1] + 2.1),
    BALCONY,
)
clockwork.retop(
    kit.ramp(
        at=ROD_FOOT_2,
        width=0.8,
        length=19.0,
        rise=CAP - BALCONY,
        yaw=ROD_ANGLE + 180.0 - 90.0,
        name="lightning_rod",
        material="brass",
        trim="",
    ),
    "limestone",
)

# A brass kerb round the balcony's outer edge.
kit.wall(
    [(*ring(13.0, a), BALCONY) for a in range(-45, 91, 5)],
    0.35,
    width=0.25,
    name="spire_balcony_kerb",
    material="brass_polished",
)

# --- Decoration -----------------------------------------------------------------------------------

# Pieces of the old tower that float round the climb, 30 m or more from the axis and clear of
# every route: wall panels with a belfry arch, and big wheels of the clockwork.
TOWER_WALLS = [  # angle round the axis, radius, height of the foot, roll
    (75.0, 33.0, 188.0, 8.0),
    (20.0, 35.0, 232.0, -10.0),
    (-40.0, 34.0, 205.0, 6.0),
    (-110.0, 33.0, 262.0, -7.0),
    (110.0, 36.0, 248.0, 9.0),
    (-150.0, 40.0, 222.0, -5.0),
    (160.0, 42.0, 180.0, 7.0),
    (-75.0, 36.0, 238.0, 11.0),
]
for i, (angle, radius, z, roll) in enumerate(TOWER_WALLS):
    wall = kit.arch(
        (*ring(radius, angle), z),
        width=3.2,
        height=7.0,
        span=9.0,
        top=12.0,
        depth=1.4,
        yaw=angle + 90.0,
        name=f"tower_wall_{i + 1}",
    )
    clockwork.refinish(wall, "wall")
    clockwork.tilt(wall, roll, 4.0)
TOWER_GEARS = [  # angle, radius, height of the middle, wheel radius, teeth, roll
    (45.0, 31.0, 214.0, 4.5, 24, 15.0),
    (-75.0, 31.0, 186.0, 3.2, 18, -20.0),
    (140.0, 34.0, 205.0, 3.8, 20, 10.0),
    (0.0, 30.0, 262.0, 2.6, 16, 25.0),
]
for i, (angle, radius, z, size, teeth, roll) in enumerate(TOWER_GEARS):
    gear = kit.gear(
        (*ring(radius, angle), z),
        size,
        teeth=teeth,
        depth=0.5,
        yaw=angle + 90.0,
        name=f"tower_gear_{i + 1}",
        material="brass_polished",
    )
    clockwork.tilt(gear, roll, -8.0)

FINISH: Place = (*AXIS, CAP)
FOOT[2] = (-8.0, 49.5, BELL_LEDGE)
FOOT[3] = (-5.6, 51.2, LID)
FOOT[4] = (*ring(RING_MID, RING_EAST + 4.0), RING)
FOOT[5] = (CHAIN2_X, CHAIN2[-1][1] - 4.8, ROOF)
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
# On the last stair the bot waits for the hands. From VI it passes HAND_GAP m from the hub on
# the IX side, where it moves the way the hands turn. It reaches VI 1 to 1.5 s after it leaves.
# When it reaches VI from 0.7 to 5.3 s after the hands show ten past ten, its line up the face
# stays 0.7 m or more clear of them, also for a crossing 30 % slower or faster.
HAND_GAP = 3.5
HAND_WAIT = f"wait_until face_hand_minute_blade {HAND_START + 1.0} {HAND_START + 2.5}"
for i, (x, y) in enumerate(STAIRS):
    EXPERT[1] += [
        ((x, y, CROWN + 1.0 + i), "speed 3" if i < 2 else f"speed 3; {HAND_WAIT}"),
        ((x - 0.25, y, CROWN + 1.0 + i), "jump; speed 3"),
    ]
_vi = (FACE[0] + _se[0] * (_low_plan - 0.8), FACE[1] + _se[1] * (_low_plan - 0.8))
_by = (FACE[0] - _ne[0] * HAND_GAP, FACE[1] - _ne[1] * HAND_GAP)
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
# Up the coil the points lie 70 degrees apart. Past the bell they lie 45 degrees apart in the
# outer lane, so the line between them stays clear of the bell's lane on the inner half; the bot
# waits for the bell 45 degrees before it.
_bell_lane = (BELL_ALONG - 45.0, BELL_ALONG, BELL_ALONG + 45.0)
FIRST[2] += [(coil(a), "speed 7") for a in range(60, int(_bell_lane[0]) - 30, 70)]
FIRST[2] += [
    (
        coil(a, 5.35),
        "speed 7; wait_until pendulum_spring 0.1 0.4" if i == 0 else "speed 7",
    )
    for i, a in enumerate(_bell_lane)
]
FIRST[2] += [(coil(a), "speed 7") for a in range(int(_bell_lane[-1]) + 65, 960, 70)]
FIRST[2] += [(coil(975.0), ""), ((-5.6, 51.2, LID), "")]
EXPERT[2] = [
    ((CHAIN_X - 0.6, 46.3, BELL_LEDGE), "speed 3"),
    ((CHAIN_X, 47.3, BELL_LEDGE), "speed 3"),
    ((CHAIN_X, 58.6, CHAIN_TOP), "speed 3"),
    ((CHAIN_X + 1.6, 58.9, CHAIN_TOP), "jump; speed 3"),
    ((-10.5, 58.4, LID), "speed 3"),
]


# --- Routes: part 3 -------------------------------------------------------------------------------


def on_ring(radius: float, angle: float, z: float) -> Place:
    """Returns the point at `angle` degrees round the axis at `radius`, at the height z."""
    return (*ring(radius, angle), z)


FIRST[3] = [
    ((SHARD_X, COIL[1] + 2.4, LID), "speed 3"),
    ((SHARD_X, COIL[1] + 0.9, LID), "jump; speed 3"),
]
# On the stairs the bot jumps where it crosses each step's jump point, and a jump that it
# reaches in the air goes off at the landing; so a step needs no point of its own.
FIRST[3] += [
    ((x, y - 0.25, LID + 1.0 + i), "jump; speed 3")
    for i, (x, y) in enumerate(SHARDS_1[:-1])
]
FIRST[3] += [
    (
        (SHARD_X, SHARDS_1[-1][1] - 0.6, LID + 6.0),
        "speed 2; wait_until lift_shards 9.6 0.3",
    ),
    (SHARD_LIFT, "speed 2; wait_until lift_shards 5.0 6.2"),
    ((SHARD_X - 0.6, SHARD_Y, LID + 14.0), "jump; speed 3"),
]
FIRST[3] += [
    ((x - 0.25, y, LID + 15.0 + i), "jump; speed 3")
    for i, (x, y) in enumerate(SHARDS_2)
]
_t = (math.sin(math.radians(SHARD_VENT_AT)), -math.cos(math.radians(SHARD_VENT_AT)))
FIRST[3] += [
    ((_vl_east - 1.2, SHARD_Y, SHARD_VENT_LEDGE), "speed 3"),
    (
        (SHARD_VENT[0] - _t[0] * 3.4, SHARD_VENT[1] - _t[1] * 3.4, SHARD_VENT_LEDGE),
        "speed 2.5",
    ),
    (
        (SHARD_VENT[0] - _t[0] * 1.8, SHARD_VENT[1] - _t[1] * 1.8, SHARD_VENT_LEDGE),
        "speed 3",
    ),
    (on_ring(28.8, 189.0, SHARD_TOP), "speed 3"),
    (on_ring(28.8, 186.2, SHARD_TOP), "jump; speed 2.5"),
]
FIRST[3] += [
    (on_ring(28.8, a - 1.1, SHARD_TOP + 1.0 + i), "jump; speed 2.5")
    for i, a in enumerate(SHARDS_3[:-1])
]
FIRST[3] += [
    (on_ring(28.8, SHARDS_3[-1], SHARD_TOP + 6.0), "speed 1.5"),
    (on_ring(28.0, SHARDS_3[-1], SHARD_TOP + 6.0), "jump; speed 2.5"),
]
# The last shard step ends beside vent_bells_1, so the first run lands on the ring's outer half,
# clear of the vent. Then it rolls clockwise round the north half to RING_EAST: the roof slabs
# climb over the south half, and the first slab starts at the ring's own height.
FIRST[3] += [(on_ring(26.0, SHARDS_3[-1], RING), "speed 2")]
for a in range(int(SHARDS_3[-1]) - 20, int(RING_EAST), -33):
    FIRST[3].append((on_ring(RING_MID, a, RING), "speed 12"))
EXPERT[3] = [
    ((ROD_FOOT[0] - _rod_u[0] * 2.0, ROD_FOOT[1] - _rod_u[1] * 2.0, LID), "speed 4"),
    (
        (ROD_FOOT[0] + _rod_u[0] * ROD_RUN, ROD_FOOT[1] + _rod_u[1] * ROD_RUN, BOB[2]),
        "speed 5",
    ),
    ((BOB[0] - _rd[0] * 1.1, BOB[1] - _rd[1] * 1.1, BOB[2]), "speed 2; wait 0.2"),
    (
        (ROD_VENTS[0][0] - _rd[0] * 1.8, ROD_VENTS[0][1] - _rd[1] * 1.8, BOB[2]),
        "speed 3",
    ),
    ((*_rod_land, ROD_TOP), "speed 3"),
    (on_ring(20.2, _land_angle - 3.0, ROD_TOP), "jump; speed 2.5"),
]
for i, a in enumerate(ROD_STEPS):
    last = i == len(ROD_STEPS) - 1
    EXPERT[3] += [
        (on_ring(21.2, a, ROD_TOP + 1.0 + i), "speed 2.5" if not last else "speed 1.5"),
        (
            on_ring(21.2, a - 1.5, ROD_TOP + 1.0 + i)
            if not last
            else on_ring(21.6, a, ROD_TOP + 3.0),
            "jump; speed 2.5",
        ),
    ]
EXPERT[3] += [(on_ring(RING_MID, ROD_STEPS[-1], RING), "speed 3")]
for a in range(int(ROD_STEPS[-1]) + 20, int(RING_WEST) - 5, 22):
    EXPERT[3].append((on_ring(RING_MID, a, RING), "speed 12"))


# --- Routes: part 4 -------------------------------------------------------------------------------

FIRST[4] = []
for i, (p0, p1) in enumerate(SLABS):
    pre = ""
    if i in (1, 2):
        pre = f"speed 3; wait_until pendulum_slab_{i} 1.4 1.8"
    FIRST[4] += [
        (p0, pre or "speed 5"),
        (
            (p1[0] + (p1[0] - p0[0]) * 0.06, p1[1] + (p1[1] - p0[1]) * 0.06, p1[2]),
            "speed 5",
        ),
    ]
_ridge_end = ring(WEIGHT_2_R, SLAB_ANGLES[-1] - RIDGE_SPAN + 1.6)
FIRST[4] += [
    ((*_ridge_end, RING + 4 * SLAB_RISE), "speed 2; wait_until weight_lift_2 0.1 0.8"),
    (WEIGHT_2_LOW, "speed 2; wait_until weight_lift_2 8.2 10.5"),
    ((WEIGHT_2_LOW[0] - _wr[0] * 3.2, WEIGHT_2_LOW[1] - _wr[1] * 3.2, ROOF), "speed 3"),
]
EXPERT[4] = [
    ((CHAIN2_X + 0.6, CHAIN2[0][1] + 3.4, RING), "speed 3"),
    ((CHAIN2_X, CHAIN2[0][1] + 1.8, RING), "speed 3"),
    ((CHAIN2_X, CHAIN2[-1][1] - 4.8, ROOF), "speed 3"),
]


# --- Routes: part 5 -------------------------------------------------------------------------------

FIRST[5] = [((-4.0, spire_ramp(0.0)[1], ROOF), "speed 4")]
FIRST[5] += [(spire_ramp(a), "") for a in range(0, 721, 72)]
FIRST[5] += [
    ((9.5, 43.6, BALCONY), "speed 3"),
    ((11.8, 41.0, BALCONY), "speed 3"),
    ((11.6, AXIS[1], BALCONY), "speed 2.5"),
    ((SPIRE_VENT[0] + 2.3, AXIS[1], BALCONY), "speed 3"),
    ((3.0, AXIS[1], CAP), "speed 3"),
]
EXPERT[5] = [
    ((BOLT_1[0] + 2.0, BOLT_1[1], ROOF), "speed 3"),
    ((BOLT_1[0] - 4.7, BOLT_1[1], BOLT_LEDGE), "speed 3"),
    ((BOLT_X, 35.6, BOLT_LEDGE), "speed 4"),
    ((BOLT_X, BOLT_TOP_Y + 0.8, BOLT_TOP), "speed 6"),
    ((BOLT_2[0] - 2.9, BOLT_2[1], BOLT_TOP), "speed 3"),
    (BOLT_LAND, "speed 3"),
    (ROD_FOOT_2, "speed 4"),
    (ROD_TOP_2, "speed 8"),
]


def route(kind: str, legs: list[Leg]) -> None:
    """Places the route of `kind` through the legs, from the start pad to the finish pad. In
    the climb the marble comes from zone 1's finish, so the route first goes to the pad: the
    way from there to the first jump is then the same as in the zone on its own."""
    first = START if TEST_FROM == 1 else FOOT[TEST_FROM]
    legs = [(first, "speed 3"), *legs]
    actions = [
        f"{i} {action.strip()}"
        for i, (_, text) in enumerate(legs)
        for action in text.split(";")
        if action.strip()
    ]
    legs = [*legs, (FINISH, "")]
    kit.marker(
        "route",
        at=first,
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

# The overview looks south-east from the north-west, with the dawn sun (azimuth 135°) behind it.
kit.shot("overview", at=(-85.0, 125.0, 262.0), rotation=(-21.0, 0.0, -136.0))
kit.shot("start", at=(START[0], START[1] - 3.0, CROWN + 1.6), rotation=(8.0, 0.0, 0.0))
kit.shot(
    "finish",
    at=(FINISH[0] + 12.0, FINISH[1] - 15.0, CAP + 6.0),
    rotation=(-16.0, 0.0, 38.7),
)
# The egg shot stands between the chamber's vent and the egg, so the vent is behind it.
_egg_eye = chamber_point(_cl - 0.8, -1.0)
kit.shot(
    "egg",
    at=(*_egg_eye, CHAMBER_FLOOR + 1.3),
    rotation=(
        -12.0,
        0.0,
        math.degrees(math.atan2(_egg_eye[0] - EGG[0], EGG[1] - _egg_eye[1])),
    ),
)
kit.shot("face", at=(2.0, 14.0, 162.0), rotation=(-12.0, 0.0, 40.0))
kit.shot("gears", at=(6.0, 18.0, 156.0), rotation=(-2.0, 0.0, -30.0))
kit.shot("mainspring", at=(14.0, 34.0, 190.0), rotation=(-11.0, 0.0, 45.0))
kit.shot("ring", at=(30.0, 10.0, 245.0), rotation=(-17.0, 0.0, 46.0))
kit.shot("slabs", at=(8.0, 2.0, 258.0), rotation=(-27.0, 0.0, 45.0))
kit.shot("spire", at=(18.0, 30.0, 285.0), rotation=(-3.0, 0.0, 63.0))
kit.shot("rod", at=(-40.0, 22.0, 290.0), rotation=(-11.0, 0.0, -37.0))
