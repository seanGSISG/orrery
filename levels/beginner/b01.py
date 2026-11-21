"""B1 Dawn Plaza (#28): the first level. An open gem hunt on four floors round a clock face
that is set into a stone plaza. The brief and the map are docs/levels/b01.md and b01.svg.

The script uses the axes of the map: x east, y north, the middle of the plaza's south edge
at (0, 0). Heights: the plaza, the start terrace and the hand yard 0 m, the west terrace
+2 m, the garden -2 m, the upper court and the finish dais +4 m. The marble starts with the
camera along +y, so it looks north across the plaza. The dawn sun stands in the north-west.
"""

import math
from collections.abc import Sequence

import kit

Point = tuple[float, float]
Place = tuple[float, float, float]

# Every block goes down to this height. Out of bounds is 5 m below it.
BASE = -6.0
# The clock face: its centre, the radius of the dish and the sides of the dish's rim.
CLOCK = (0.0, 13.0)
DISH = 6.2
DISH_SIDES = 192
# The finish dais: a round end on the north side of the court. The finish is at its centre.
DAIS = (0.0, 53.0)
DAIS_RADIUS = 5.6
# The Minute Hand: a beam 1.2 m wide from the west terrace up to the court. It lies this
# many degrees east of north.
HAND_TURN = 31.6
HAND_HALF = 0.6


def block(
    name: str,
    outline: Sequence[Point],
    top: float,
    holes: Sequence[Sequence[Point]] = (),
) -> None:
    """Adds a floor at the height `top` on a block that goes down to BASE."""
    kit.deck(outline, top=top, depth=top - BASE, holes=holes, name=name)


def kerb(name: str, path: Sequence[Place]) -> None:
    """Adds the brass kerb of an outer edge, 0.3 m high, on the left of the path, and a row
    of gear teeth below it on the outer face."""
    kit.wall(path, height=0.3, width=0.3, bevel=0.03, name=name, material="brass")
    kit.teeth(path, name=f"{name}_teeth")


def parapet(name: str, path: Sequence[Place], height: float) -> None:
    """Adds a stone parapet with a brass cap on the left of the path, and gear teeth on the
    outer face. It stands where a kerb is too low: across the top of a ramp and below a
    drop, where the marble comes through the air."""
    kit.wall(path, height=height, width=0.4, name=name)
    cap = [(x, y, z + height) for x, y, z in path]
    kit.wall(
        cap, height=0.1, width=0.4, bevel=0.03, name=f"{name}_cap", material="brass"
    )
    kit.teeth(path, name=f"{name}_teeth")


def ring(name: str, centre: Point, inner: float, outer: float, top: float) -> None:
    """Adds a gold ring set into the floor at the height `top`."""
    kit.inlay(
        kit.arc(centre, outer, 0, 360),
        top=top,
        holes=[kit.arc(centre, inner, 0, 360)],
        name=name,
    )


def lifted(points: Sequence[Point], height: float) -> list[Place]:
    """Returns the points at one height."""
    return [(x, y, height) for x, y in points]


kit.level(title="Dawn Plaza", par=51.3, gold=25.6, sky="dawn")

# --- Floors ------------------------------------------------------------------------------

# The plaza level: the start terrace, the plaza, the landing of the garden ramp and the hand
# yard. The block also fills the space under the grand ramp and the west ramp.
block(
    "plaza",
    [
        (-8, -8),
        (8, -8),
        (8, 0),
        (17, 0),
        (17, 22),
        (22, 22),
        (22, 26),
        (6, 26),
        (6, 37),
        (-22, 37),
        (-22, 30),
        (-17, 30),
        (-17, 9),
        (-25, 9),
        (-25, 2),
        (-17, 2),
        (-17, 0),
        (-8, 0),
    ],
    top=0.0,
    holes=[kit.arc(CLOCK, DISH, 0, 360, DISH_SIDES)],
)
kit.dish(
    at=(*CLOCK, 0.0), radius=DISH, depth=0.6, flat=0.8, segments=DISH_SIDES, name="dish"
)
block(
    "terrace", [(-28, 2), (-25, 2), (-25, 9), (-17, 9), (-17, 30), (-28, 30)], top=2.0
)
# The garden: the south part, the east strip and the alley. Its block is also the floor of
# the vault and the ground under the garden ramp.
block(
    "garden",
    [
        (17, 0),
        (29, 0),
        (29, 37),
        (17, 37),
        (17, 43.8),
        (9.8, 43.8),
        (9.8, 32),
        (22, 32),
        (22, 22),
        (17, 22),
    ],
    top=-2.0,
)
# The upper court and the finish dais are one slab. The block under the court has a room in
# its south-east corner: the vault. An arch in its south wall opens to the alley, and two
# arches in its east wall let the light in.
COURT = [
    (-17, 37),
    (17, 37),
    (17, 48),
    (DAIS_RADIUS, 48),
    *kit.arc(DAIS, DAIS_RADIUS, 0, 180),
    (-DAIS_RADIUS, 48),
    (-17, 48),
]
kit.deck(COURT, top=4.0, depth=1.0, name="court")
block(
    "court_block",
    [
        (-17, 37),
        (11.5, 37),
        (11.5, 37.6),
        (10.4, 37.6),
        (10.4, 43.2),
        (17, 43.2),
        (17, 48),
        (-17, 48),
    ],
    top=3.0,
)
block("court_corner", kit.rect(15.5, 37, 17, 37.6), top=3.0)
block("dais_block", COURT[3:-1], top=3.0)
kit.arch(
    at=(13.5, 37, -2),
    width=2.6,
    height=3.0,
    span=4.0,
    top=5.0,
    depth=0.6,
    name="vault_arch",
)
for i, y in enumerate((39.0, 41.8)):
    kit.arch(
        at=(17, y, -2),
        width=2.0,
        height=3.0,
        span=2.8,
        top=5.0,
        depth=0.6,
        yaw=90,
        name=f"vault_window_{i}",
    )
kit.wall(
    [(17, 37.6, -2), (17, 43.2, -2)],
    height=0.3,
    width=0.3,
    bevel=0.03,
    name="vault_sill",
    material="brass",
)

# An inverted cone with a brass finial hangs under each block, as under a tower top. The
# cones are out of reach, so they do not collide.
for name, (x, y), radius in (
    ("plaza", CLOCK, 14.0),
    ("terrace", (-22.5, 19.5), 5.2),
    ("garden", (25.5, 16.0), 3.3),
    ("court", (-4.0, 42.5), 5.2),
    ("dais", DAIS, 5.2),
):
    depth = 1.5 * radius
    kit.lathe(
        (x, y, BASE), [(0.0, -depth), (radius, 0.0)], name=f"keel_{name}", collide=False
    )
    kit.lathe(
        (x, y, BASE - depth),
        [(0.0, -0.14 * radius), (0.07 * radius, -0.07 * radius), (0.03 * radius, 0.0)],
        name=f"keel_{name}_finial",
        material="brass",
        collide=False,
    )

# --- Ramps -------------------------------------------------------------------------------

kit.ramp(at=(0, 26, 0), width=12, length=11, rise=4, fill=True, name="grand_ramp")
kit.ramp(
    at=(-17, 5.5, 0), width=7, length=8, rise=2, yaw=90, fill=True, name="west_ramp"
)
kit.ramp(
    at=(19.5, 22, 0),
    width=5,
    length=10,
    rise=-2,
    yaw=180,
    fill=True,
    name="garden_ramp",
    trim="",
)

# The Minute Hand: a fallen clock hand that lies from the edge of the terrace to the edge of
# the court. The slope has square ends. A level triangle joins each end to the edge of its
# floor, the heel at the terrace and the tip at the court, so the marble meets no step.
turn = math.radians(HAND_TURN)
along = (math.sin(turn), math.cos(turn))
right = (math.cos(turn), -math.sin(turn))
skew = HAND_HALF * math.sin(turn)
# The middle of the slope's top end. Its left corner is on the edge of the court, y = 37.
hand_end = (-15.2, 37.0 - skew)
# The middle of the slope's foot. Its right corner is on the edge of the terrace, y = 30.
hand_length = (hand_end[1] - (30.0 + skew)) / along[1]
hand_start = (hand_end[0] - hand_length * along[0], 30.0 + skew)
kit.ramp(
    at=(*hand_start, 2.0),
    width=2 * HAND_HALF,
    length=hand_length,
    rise=2,
    yaw=-HAND_TURN,
    name="minute_hand",
    material="gold",
)
# How far a side of the beam runs on from a square end to the edge of the floor.
reach = 2 * skew / along[1]
for name, middle, edge, side, top in (
    ("heel", hand_start, 30.0, -1, 2.0),
    ("tip", hand_end, 37.0, 1, 4.0),
):
    near = (middle[0] - side * HAND_HALF * right[0], edge)
    far = (
        middle[0] + side * HAND_HALF * right[0],
        middle[1] + side * HAND_HALF * right[1],
    )
    kit.deck(
        [near, far, (far[0] + side * reach * along[0], edge)],
        top=top,
        name=f"minute_hand_{name}",
        material="gold",
    )
# A gold ring on the terrace marks the way onto the hand.
hand_eye = (hand_start[0] - 1.9 * along[0], hand_start[1] - 1.9 * along[1])

# --- Kerbs and walls ---------------------------------------------------------------------

# Every outer edge has a kerb. An edge above another floor is open: the marble can drop.
# A parapet stands where the marble comes through the air: at the top of the west ramp and
# of the garden ramp, round the garden below the open plaza edge, and round the yard below
# the terrace.
kerb("kerb_terrace", [(-22, 30, 2), (-28, 30, 2), (-28, 13, 2)])
parapet("parapet_terrace", [(-28, 13, 2), (-28, 2, 2), (-25, 2, 2)], 1.2)
kerb(
    "kerb_south",
    [
        (-25, 2, 2),
        (-17, 2, 0),
        (-17, 0, 0),
        (-8, 0, 0),
        (-8, -8, 0),
        (8, -8, 0),
        (8, 0, 0),
        (17, 0, 0),
    ],
)
parapet("parapet_landing", [(22, 26, 0), (17, 26, 0)], 1.5)
kerb(
    "kerb_north",
    [
        (17, 26, 0),
        (6, 26, 0),
        (6, 37, 4),
        (17, 37, 4),
        (17, 48, 4),
        (DAIS_RADIUS, 48, 4),
        *lifted(kit.arc(DAIS, DAIS_RADIUS, 0, 180), 4.0),
        (-DAIS_RADIUS, 48, 4),
        (-17, 48, 4),
        (-17, 37, 4),
    ],
)
parapet("parapet_yard", [(-17, 37, 0), (-22, 37, 0), (-22, 30, 0)], 2.0)
parapet("parapet_garden", [(17, 0, -2), (29, 0, -2), (29, 37, -2), (17, 37, -2)], 1.0)
kerb("kerb_alley", [(9.8, 37, -2), (9.8, 32, -2), (17, 32, -2)])
# The garden wall hides the east strip and the alley from the ramp and from the plaza.
GARDEN_WALL = [(22, 12, -2), (22, 32, -2), (17, 32, -2)]
kit.wall(GARDEN_WALL, height=3.5, width=0.5, side="right", name="garden_wall")
kit.wall(
    [(x, y, z + 3.5) for x, y, z in GARDEN_WALL],
    height=0.1,
    width=0.5,
    side="right",
    bevel=0.03,
    name="garden_wall_cap",
    material="brass",
)

for i, (x, y) in enumerate(((-9.5, 3.5), (9.5, 3.5), (-9.5, 22.5), (9.5, 22.5))):
    kit.pillar(at=(x, y, 0), name=f"pillar_{i}")

# --- The clock face ----------------------------------------------------------------------

ring("clock_rim", CLOCK, 11.05, 11.35, 0.0)
ring("clock_dish_rim", CLOCK, DISH, DISH + 0.25, 0.0)
kit.inlay(kit.arc(CLOCK, 0.5, 0, 360), top=-0.6, name="clock_hub")
for hour in range(12):
    angle = 90 - 30 * hour
    wide = 0.5 if hour % 3 == 0 else 0.3
    foot = (
        CLOCK[0] + 8.9 * math.cos(math.radians(angle)),
        CLOCK[1] + 8.9 * math.sin(math.radians(angle)),
    )
    kit.inlay(kit.box(foot, wide, 1.6, yaw=angle - 90), name=f"clock_hour_{hour:02d}")
# The hour pointer shows six o'clock: dawn. The minute hand fell onto the terrace.
kit.inlay(
    [
        (0, CLOCK[1] - 8.6),
        (0.3, CLOCK[1] - 7.3),
        (0, CLOCK[1] - 6.8),
        (-0.3, CLOCK[1] - 7.3),
    ],
    name="clock_pointer",
)
ring("hand_eye", hand_eye, 1.0, 1.2, 2.0)
ring("start_ring", (0, -4.5), 0.6, 0.75, 0.0)
ring("finish_ring", DAIS, 1.3, 1.5, 4.0)

# A brass line marks each open edge.
for name, strip, top in (
    ("edge_plaza", kit.rect(16.86, 0.3, 17, 22), 0.0),
    ("edge_terrace_east", kit.rect(-17.14, 9, -17, 30), 2.0),
    ("edge_terrace_north", kit.rect(-22, 29.86, -17.14, 30), 2.0),
    ("edge_court", kit.rect(-16.7, 37, -6, 37.14), 4.0),
):
    kit.inlay(strip, top=top, name=name, material="brass")

# --- The armillary sphere over the finish ------------------------------------------------

# Four pillars carry the horizon ring. The other two rings hang inside it, above the
# marble's reach. The marble sees the rings from the start: they mark the finish. The
# pillars stand clear of the two ways in: from the south and from the last gem.
for i in range(4):
    angle = math.radians(68.5 + 90 * i)
    kit.pillar(
        at=(DAIS[0] + 3.9 * math.cos(angle), DAIS[1] + 3.9 * math.sin(angle), 4),
        radius=0.5,
        height=2.8,
        name=f"dais_pillar_{i}",
    )
SPHERE = (*DAIS, 7.33)
kit.hoop(SPHERE, 3.9, name="armillary_horizon")
kit.hoop(SPHERE, 2.5, rotation=(90, 0, 0), name="armillary_meridian")
kit.hoop(SPHERE, 3.1, rotation=(55, 0, 40), name="armillary_ecliptic")

# --- Objects -----------------------------------------------------------------------------

START = (0.0, -4.5, 0.0)
FINISH = (*DAIS, 4.0)
kit.marker("start", at=START)
kit.marker("finish", at=FINISH)
GEMS = {
    "clock_centre": (0, 13, -0.6),
    "clock_nine": (-9.8, 13, 0),
    "clock_three": (9.8, 13, 0),
    "terrace_south": (-23, 14, 2),
    "terrace_north": (-23, 26.4, 2),
    "garden_south": (20.2, 4.4, -2),
    "garden_east": (25.6, 17.8, -2),
    "court": (-9.8, 42.4, 4),
}
for name, at in GEMS.items():
    kit.marker("gem", at=at, name=f"gem_{name}")
    # A gold ring marks the place of each gem that is not on the clock face.
    if not name.startswith("clock"):
        ring(f"gem_ring_{name}", at[:2], 0.45, 0.55, at[2])
# The Clockwork Egg: in the vault under the court, at the west end of the alley.
kit.marker("egg", at=(13.4, 40.4, -2))

# --- Routes ------------------------------------------------------------------------------

# First run: the clock face, the west terrace and back, the garden and back, the grand ramp.
# The turns are sharp, as on a first run.
kit.marker(
    "route",
    at=START,
    points=[
        GEMS["clock_centre"],
        GEMS["clock_nine"],
        (-16, 5.5, 0),
        (-26.2, 5.5, 2),
        (-25.8, 9.5, 2),
        GEMS["terrace_south"],
        GEMS["terrace_north"],
        (-26.3, 8, 2),
        (-18, 5.5, 0.25),
        GEMS["clock_three"],
        (19.5, 23.5, 0),
        (19.5, 13, -1.8),
        GEMS["garden_south"],
        GEMS["garden_east"],
        (23.6, 10.6, -2),
        (19.5, 11, -2),
        (19.5, 23.5, 0),
        (2, 25, 0),
        (0, 36, 3.6),
        GEMS["court"],
        (0, 48.5, 4),
        FINISH,
    ],
    name="route_first_run",
    kind="first_run",
)
# Expert: one loop with no way back. The drop off the open east edge into the garden, round
# the end of the garden wall, up the garden ramp, across the clock face, up the west ramp
# and over the Minute Hand to the court. The marble lands on the first garden gem, so the
# drop has a speed limit.
kit.marker(
    "route",
    at=START,
    points=[
        (5.6, -0.2, 0),
        (9.5, 1.6, 0),
        (14.6, 2.93, 0),
        GEMS["garden_south"],
        GEMS["garden_east"],
        (22.25, 8.0, -2),
        (19.3, 23.2, 0),
        GEMS["clock_three"],
        GEMS["clock_centre"],
        GEMS["clock_nine"],
        (-25.7, 3.3, 2),
        (-25.7, 9.6, 2),
        GEMS["terrace_south"],
        GEMS["terrace_north"],
        (*hand_start, 2),
        (*hand_end, 4),
        GEMS["court"],
        FINISH,
    ],
    name="route_expert",
    kind="expert",
    actions="3 speed 7.2; 14 speed 10; 15 speed 10",
)

# --- Shots -------------------------------------------------------------------------------

kit.shot("overview", at=(-24, -20, 25), rotation=(-34, 0, -31))
kit.shot("start", at=(0, -7.3, 1.5), rotation=(-10, 0, 0))
kit.shot("finish", at=(-7, 42.5, 5.6), rotation=(4, 0, -34))
kit.shot("egg", at=(10.9, 40.3, -0.8), rotation=(-5, 0, -90))
kit.shot("clock", at=(0, 1, 8), rotation=(-38, 0, 0))
kit.shot("hand", at=(-23.2, 24.2, 3.7), rotation=(-10, 0, -31.6))
kit.shot("garden", at=(26, 3, -0.5), rotation=(-8, 0, 12))
