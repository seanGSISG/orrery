"""Ascent 3 Sky Harbour (#33): the roofs of the harbour quarter and its moored airships, 300 to
500 m of the climb. The brief and the map are docs/levels/ascent-z3.md and ascent-z3.svg.

The script uses the coordinates of the climb (docs/design/ascent.md §2): x east, y north, z up.
Zone 2 ends on the spire cap, a round floor 10 m across at +300 m round CAP. Zone 3 starts on
its own quay south of the cap and builds nothing else within 6 m of the cap's axis below
+312 m. Every airship points west, into the wind (kit/harbour.py).

Each part has two ways up:

1. First roofs, +300 to +322: the crate steps, Roof 1, its ridge vent, Roof 2, the dormer
   steps and gangway A (or the mooring rope from Roof 2); or the loose planks, the Tender's
   gondola, its deck vent, the fin, the stern steps and gangway B. All reach the Harbourmaster.
2. Courier and mast, +322 to +344: the tile steps, the Courier's gondola, three hull ramps with
   a pendulum, its top and gangplank C; or the roof vent, the loose shingles, the propeller
   gear, a vent, the mast platform and three steps. Both reach the Sailmakers' roof.
"""

import math
from collections.abc import Sequence

import kit
from kit import harbour, town
from kit.harbour import Ship

Point = tuple[float, float]
Place = tuple[float, float, float]
# A route point and its actions, separated by ";" (route.gd), for example "jump; speed 4".
Leg = tuple[Place, str]
# A gap in a parapet: the side (s, e, n or w) and the span, in world x on s and n, y on e and w.
Gap = tuple[str, float, float]

# The spire cap of zone 2: its middle and radius. Zone 3 does not build it.
CAP = (0.0, 39.0)
CAP_RADIUS = 5.0
# A floating house: the overhang of its terrace past its walls, and the terrace slab, m.
EAVE = 0.15
TERRACE = 0.25

FIRST: dict[int, list[Leg]] = {}
EXPERT: dict[int, list[Leg]] = {}

kit.level(title="Sky Harbour", par=400.0, gold=200.0, sky="ground_dawn")


def house(
    name: str,
    lo: Point,
    hi: Point,
    top: float,
    height: float = 4.0,
    seed: int = 0,
    gaps: Sequence[Gap] = (),
    windows: str = "nesw",
) -> None:
    """Adds a floating harbour house whose flat roof terrace spans the plan corners lo and hi
    at the height `top`: a storey `height` m tall under it, and a stone parapet round the
    terrace, open at the gaps."""
    (x0, y0), (x1, y1) = lo, hi
    harbour.storey(
        name,
        (x0 + EAVE, y0 + EAVE),
        (x1 - EAVE, y1 - EAVE),
        top - height,
        top - TERRACE,
        seed=seed,
        windows=windows,
    )
    harbour.slab(f"{name}_terrace", (x0, y0, top - TERRACE), (x1, y1, top), "dressed")
    harbour.parapet(f"{name}_parapet", lo, hi, top, along(lo, hi, gaps))


def along(lo: Point, hi: Point, gaps: Sequence[Gap]) -> list[Gap]:
    """Turns gaps in world x or y into spans along the sides of the box lo, hi as
    town.faces() runs them (s and e from the low corner, n and w from the high one)."""
    (x0, y0), (x1, y1) = lo, hi
    spans = []
    for side, a, b in gaps:
        a, b = min(a, b), max(a, b)
        start = {"s": x0, "e": y0}.get(side)
        if start is not None:
            spans.append((side, a - start, b - start))
        else:
            end = x1 if side == "n" else y1
            spans.append((side, end - b, end - a))
    return spans


def crate_step(name: str, lo: Point, hi: Point, top: float, bottom: float) -> None:
    """Adds a step of cargo: a crate between the plan corners lo and hi from `bottom` up to
    the height `top`."""
    town.crate(name, (*lo, bottom), (*hi, top))


def stack(name: str, lo: Point, hi: Point, top: float, height: float = 3.5) -> None:
    """Adds a step that is the top of a broken chimney stack: stone, with a dressed cap whose
    top is at `top`."""
    (x0, y0), (x1, y1) = lo, hi
    parts = town.Parts()
    parts.box(
        (x0 + 0.08, y0 + 0.08, top - height), (x1 - 0.08, y1 - 0.08, top - 0.2), "wall"
    )
    parts.box((x0, y0, top - 0.2), (x1, y1, top), "dressed")
    parts.add(name)


def kerbs(name: str, lo: Point, hi: Point, top: float, sides: str) -> None:
    """Adds a brass kerb on each side in `sides` (s, e, n, w) of the deck lo, hi at `top`,
    outside its edge."""
    for side, face in town.faces(lo, hi).items():
        if side in sides:
            a, b = face.at(0.0), face.at(face.length)
            harbour.kerb(f"{name}_{side}", [(*a, top), (*b, top)], side="right")


def deck(name: str, lo: Point, hi: Point, top: float, sides: str = "") -> None:
    """Adds a timber deck 0.3 m thick between the plan corners lo and hi, its top at `top`,
    with brass kerbs on the sides in `sides`."""
    harbour.slab(name, (*lo, top - harbour.PLANK), (*hi, top), "wood")
    if sides:
        kerbs(f"{name}_kerb", lo, hi, top, sides)


def vent(name: str, at: Place, lift: float, radius: float = 1.0) -> None:
    """Places a Steam Vent with its grate at `at`."""
    kit.marker("steam_vent", at=at, lift=lift, radius=radius, name=name)


# --- Part 1: first roofs, +300 to +322 ----------------------------------------------------------

# The quay: the zone start, flush with the south edge of the cap. A jetty runs west from it to
# the wall of Roof 1.
QUAY = (-7.0, 25.0, 5.5, 35.0)
qx0, qy0, qx1, qy1 = QUAY
START: Place = (0.0, 29.0, 300.0)
_rim = math.degrees(math.atan2(qy1 - CAP[1], 3.0))
town.floor(
    "quay",
    [
        (qx0, qy0),
        (qx1, qy0),
        (qx1, qy1),
        *kit.arc(CAP, CAP_RADIUS, _rim, -180.0 - _rim),
        (qx0, qy1),
    ],
    300.0,
    0.6,
    finish="wood",
)
JETTY_Y = (28.3, 31.7)
JETTY_ROW = (JETTY_Y[0] + JETTY_Y[1]) / 2
harbour.slab("jetty", (-12.65, JETTY_Y[0], 299.4), (qx0, JETTY_Y[1], 300.0), "wood")
# The planks to the Tender leave the east side; the crate steps leave the jetty.
PLANKS_Y = (32.8, 34.8)
harbour.parapet(
    "quay_parapet",
    (qx0, qy0),
    (qx1, qy1),
    300.0,
    along(
        (qx0, qy0),
        (qx1, qy1),
        [("n", qx0, qx1), ("w", *JETTY_Y), ("e", PLANKS_Y[0] - 0.3, qy1)],
    ),
)
# Iron girders under the quay: it hangs from the harbour like the houses.
_girders = town.Parts()
for _x in (-5.5, -1.5, 2.5):
    _girders.box((_x - 0.15, qy0 + 0.3, 298.9), (_x + 0.15, 33.0, 299.4), "iron")
_girders.add("quay_girders", collide=False)
for _at in ((-6.4, 25.6), (4.9, 25.6)):
    harbour.lamp(f"quay_lamp_{_at[0]:+.0f}", (*_at, 300.0))

# West way: two crates on the jetty, then Roof 1, a slate slope of 32° from its gutter walk
# (+303) to its ridge walk (+308).
CRATES = [(-9.6, -7.3, 301.0), (-12.2, -9.9, 302.0)]
for i, (x0, x1, top) in enumerate(CRATES):
    crate_step(f"crate_step_{i + 1}", (x0, 28.5), (x1, 31.5), top, 300.0)
ROOF_1 = (-29.5, 26.0, -12.65, 36.0)
r1x0, r1y0, r1x1, r1y1 = ROOF_1
GUTTER = (-14.5, -12.5, 303.0)
RIDGE = (-25.5, -22.5, 308.0)
harbour.storey(
    "roof_1", (r1x0, r1y0), (r1x1, r1y1), 299.0, 302.75, seed=1, windows="sew"
)
_roof = town.Parts()
_roof.prism(
    [(GUTTER[0], 302.75), (RIDGE[1], 302.75), (RIDGE[1], RIDGE[2] - 0.3)],
    r1y0,
    r1y1,
    "y",
    "wall",
)
_roof.prism(
    [(RIDGE[0], 302.75), (r1x0, 302.75), (r1x0, 305.2), (RIDGE[0], RIDGE[2] - 0.3)],
    r1y0,
    r1y1,
    "y",
    "wall",
)
_roof.box((RIDGE[0], r1y0, 302.75), (RIDGE[1], r1y1, RIDGE[2] - 0.25), "wall")
_roof.add("roof_1_mass")
harbour.slab(
    "roof_1_gutter",
    (GUTTER[0], r1y0 - EAVE, 302.75),
    (GUTTER[1], r1y1 + EAVE, 303.0),
    "dressed",
)
harbour.slab(
    "roof_1_ridge",
    (RIDGE[0], r1y0 - EAVE, 307.75),
    (RIDGE[1], r1y1 + EAVE, 308.0),
    "dressed",
)
_mid = (r1y0 + r1y1) / 2
harbour.slope(
    "roof_1_slope",
    (GUTTER[0], _mid, GUTTER[2]),
    (RIDGE[1], _mid, RIDGE[2]),
    r1y1 - r1y0 + 2 * EAVE,
    "slate_turned",
)
harbour.slope(
    "roof_1_back",
    (RIDGE[0], _mid, RIDGE[2]),
    (r1x0 - 0.3, _mid, 305.0),
    r1y1 - r1y0 + 2 * EAVE,
    "slate_turned",
)
town.chimney("roof_1_chimney", (-27.6, 27.4, 305.9), 0.9, 1.6)
RIDGE_VENT = (-24.0, 34.0)
vent("vent_ridge", (*RIDGE_VENT, RIDGE[2]), 9.5)

# Roof 2 (+315): a wide terrace with two bumpers, and a wing to the north where the mooring
# rope leaves.
ROOF_2 = (-30.0, 37.5, -21.2, 52.0)
WING = (-30.0, 52.0, -24.0, 56.5)
DORMER_Y = (43.3, 46.3)
DORMER_ROW = (DORMER_Y[0] + DORMER_Y[1]) / 2
ROPE_Y = 54.2
house(
    "roof_2",
    ROOF_2[:2],
    ROOF_2[2:],
    315.0,
    seed=2,
    gaps=[
        ("s", -26.0, -22.0),
        ("e", DORMER_Y[0] - 0.3, DORMER_Y[1] + 0.3),
        ("n", -30.0, -24.0),
    ],
)
house(
    "roof_2_wing",
    WING[:2],
    WING[2:],
    315.0,
    height=3.2,
    seed=3,
    gaps=[("s", -30.0, -24.0), ("e", ROPE_Y - 0.9, ROPE_Y + 0.9)],
    windows="nw",
)
kit.marker("bumper", at=(-28.0, 45.5, 315.0), name="bumper_roof_2_1")
kit.marker("bumper", at=(-23.0, 49.5, 315.0), name="bumper_roof_2_2")
town.chimney("roof_2_chimney", (-28.9, 38.6, 315.0), 0.9, 1.4)

# The dormer steps (+316 to +318) stand out of the slate roof of a lower house.
DORMERS = [(-20.9, -18.6, 316.0), (-18.3, -16.0, 317.0), (-15.7, -13.4, 318.0)]
harbour.storey(
    "dormer_house", (-20.9, 41.9), (-13.5, 47.7), 309.4, 313.0, seed=4, windows="ns"
)
harbour.gable(
    "dormer_house_roof", (-20.9, 41.9), (-13.5, 47.7), 313.0, 315.0, along="x"
)
for i, (x0, x1, top) in enumerate(DORMERS):
    stack(f"dormer_{i + 1}", (x0, DORMER_Y[0]), (x1, DORMER_Y[1]), top, top - 313.0)

# Gangway A: from the last dormer to the Harbourmaster, 8 s a cycle.
GANGWAY_A_LOW: Place = (-11.75, DORMER_ROW, 318.0)
GANGWAY_A_HIGH: Place = (-8.6, 47.7, 322.0)
kit.marker(
    "moving_platform",
    at=GANGWAY_A_LOW,
    points=[GANGWAY_A_HIGH],
    period=8.0,
    stop=1.0,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="gangway_a",
)

# The Harbourmaster (+322): the first rest ledge.
HARBOURMASTER = (-7.0, 46.0, 3.0, 56.0)
TILE_X = (-6.8, -3.8)
TILE_COL = (TILE_X[0] + TILE_X[1]) / 2
GANGWAY_B_HIGH: Place = (1.5, 44.4, 322.0)
house(
    "harbourmaster",
    HARBOURMASTER[:2],
    HARBOURMASTER[2:],
    322.0,
    height=4.5,
    seed=5,
    gaps=[
        ("w", 46.0, 49.4),
        ("w", ROPE_Y - 0.9, ROPE_Y + 0.9),
        ("s", 0.0, 3.0),
        ("n", TILE_X[0] - 0.1, TILE_X[1] + 0.1),
    ],
)
harbour.lamp("harbourmaster_lamp", (2.4, 55.4, 322.0))

# The first mooring rope (expert): 0.6 m wide, 25°, from the wing to the Harbourmaster.
ROPE_1 = harbour.rope(
    "rope_1", (WING[2], ROPE_Y, 315.0), (HARBOURMASTER[0], ROPE_Y, 322.0)
)

# East way: the loose planks, then the Tender.
kit.marker(
    "crumbling_tiles",
    at=(7.6, (PLANKS_Y[0] + PLANKS_Y[1]) / 2, 300.0),
    width=4.0,
    depth=2.0,
    tile=1.0,
    name="planks",
)
TENDER = Ship("tender", (7.5, 34.5, 308.5), 19.0, 4.4)
TENDER_DECK = 301.0
SPONSON = (17.0, 28.0, 21.0, 32.7)
harbour.envelope(TENDER)
harbour.gondola(
    TENDER,
    10.0,
    23.0,
    TENDER_DECK,
    3.6,
    kerbs=[("n", 10.0, 23.0), ("s", 11.6, SPONSON[0]), ("s", SPONSON[2], 23.0)],
)
deck("tender_sponson", SPONSON[:2], (SPONSON[2], 32.8), TENDER_DECK, "sw")
TENDER_VENT = (19.2, 29.8)
vent("vent_tender", (*TENDER_VENT, TENDER_DECK), 10.8)
FIN = harbour.fins(TENDER, root=5.0, span=4.0, floors=True)
# Brass kerbs on the trailing edge and the tip of the south fin: the vent throws the marble
# east along it.
harbour.kerb(
    "tender_fin_kerb",
    [(23.75, 27.7, FIN), (27.1, 27.7, FIN), (27.1, 33.6, FIN)],
    side="right",
)
harbour.engine("tender_engine_n", (14.5, 40.2, 305.6))
harbour.engine("tender_engine_s", (14.5, 28.8, 305.6))
# The stern steps: a deckhouse on the fin, then three decks up over the tail to the top.
crate_step("tender_deckhouse", (25.0, 30.8), (27.1, 33.2), FIN + 0.86, FIN)
TENDER_TOP = 313.4
STERN = [(24.6, 26.6, 310.45), (22.3, 24.3, 311.45), (19.7, 22.0, 312.45)]
_legs = town.Parts()
for i, (x0, x1, top) in enumerate(STERN):
    deck(f"tender_stern_{i + 1}", (x0, 33.5), (x1, 35.5), top, "n")
    for x in (x0 + 0.3, x1 - 0.3):
        _legs.bar((x, 34.5, top - 0.3), (x, 34.5, TENDER.top(x) - 0.1), 0.12, "iron")
_legs.add("tender_stern_legs", collide=False)
harbour.promenade(
    TENDER,
    [(9.0, TENDER_TOP), (19.4, TENDER_TOP)],
    2.0,
    kerbs=[("n", 9.0, 19.4), ("s", 9.0, 19.4)],
)
# Gangway B: from the top of the Tender to the Harbourmaster, 10 s a cycle.
kit.marker(
    "moving_platform",
    at=(7.4, 34.5, TENDER_TOP),
    points=[GANGWAY_B_HIGH],
    period=10.0,
    stop=1.5,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="gangway_b",
)

# Egg 1: a cargo crate under the Tender, below the zone start. A vent on it throws the marble
# north, back up to the gondola deck.
CRATE = (7.5, 29.0, 11.5, 32.4, 297.8)
town.crate(
    "cargo_crate", (CRATE[0], CRATE[1], CRATE[4] - 1.4), (CRATE[2], CRATE[3], CRATE[4])
)
_davit = town.Parts()
for _x in (CRATE[0] + 0.4, CRATE[2] - 0.4):
    harbour.line(_davit, (_x, 30.7, CRATE[4]), (_x, 32.4, 300.6), 0.06)
_davit.bar((CRATE[0] + 0.2, 32.5, 300.6), (CRATE[2] + 0.4, 32.5, 300.6), 0.12, "iron")
_davit.add("cargo_crate_davit", collide=False)
EGG_CRATE: Place = (8.4, 30.6, CRATE[4])
kit.marker("egg", at=EGG_CRATE, name="egg_crate")
vent("vent_crate", (10.6, 30.8, CRATE[4]), 6.5)

# --- Part 2: Courier and mast, +322 to +344 -----------------------------------------------------

# West way: three tile steps north from the Harbourmaster to the Courier's gondola (+326).
TILES = [(56.3, 58.6, 323.0), (58.9, 61.2, 324.0), (61.5, 63.8, 325.0)]
for i, (y0, y1, top) in enumerate(TILES):
    stack(f"tile_step_{i + 1}", (TILE_X[0], y0), (TILE_X[1], y1), top)
COURIER = Ship("courier", (-26.0, 66.0, 334.0), 28.0, 5.6)
COURIER_DECK = 326.0
harbour.envelope(COURIER)
harbour.gondola(
    COURIER,
    -24.5,
    -3.5,
    COURIER_DECK,
    3.8,
    kerbs=[("s", -24.5, TILE_X[0] - 0.2), ("n", -22.0, -3.5)],
)
harbour.fins(COURIER, root=6.0, span=2.4)
harbour.engine("courier_engine_1", (-18.0, 59.4, 331.0))
harbour.engine("courier_engine_2", (-9.0, 60.6, 332.0))
# The hull ramps: a switchback of three timber ramps of 20° on the north flank, on iron
# brackets. Ramps 1 and 3 run east in row A, ramp 2 west in row B, outside it.
RAMP_X = (-22.0, -9.5)
ROW_A, ROW_B = 73.2, 76.0
RAMP_W = 2.4
RISE = 4.7
LEVELS = [COURIER_DECK + RISE * k for k in range(4)]
COURIER_TOP = LEVELS[3]
deck(
    "courier_bridge", (-24.5, 67.9), (RAMP_X[0], ROW_A + RAMP_W / 2), COURIER_DECK, "w"
)
for i, (row, a, b) in enumerate(
    [
        (ROW_A, RAMP_X[0], RAMP_X[1]),
        (ROW_B, RAMP_X[1], RAMP_X[0]),
        (ROW_A, RAMP_X[0], RAMP_X[1]),
    ]
):
    low, high = LEVELS[i], LEVELS[i + 1]
    harbour.slope(
        f"courier_ramp_{i + 1}", (a, row, low), (b, row, high), RAMP_W, "wood"
    )
    for edge, side in ((row + RAMP_W / 2, "left"), (row - RAMP_W / 2, "right")):
        if a > b:
            side = "right" if side == "left" else "left"
        harbour.kerb(
            f"courier_ramp_{i + 1}_{side}", [(a, edge, low), (b, edge, high)], side=side
        )
LANDING_Y = (ROW_A - RAMP_W / 2, ROW_B + RAMP_W / 2)
deck(
    "courier_landing_1",
    (RAMP_X[1], LANDING_Y[0]),
    (-6.5, LANDING_Y[1]),
    LEVELS[1],
    "sen",
)
deck(
    "courier_landing_2",
    (-25.0, LANDING_Y[0]),
    (RAMP_X[0], LANDING_Y[1]),
    LEVELS[2],
    "swn",
)
deck(
    "courier_landing_3",
    (RAMP_X[1], 67.2),
    (-6.5, LANDING_Y[0] + RAMP_W),
    COURIER_TOP,
    "en",
)
harbour.kerb(
    "courier_landing_3_w",
    [(RAMP_X[1], LANDING_Y[0], COURIER_TOP), (RAMP_X[1], 67.2, COURIER_TOP)],
)
# Iron brackets from the hull to the underside of each ramp.
_brackets = town.Parts()
for x in (-19.0, -12.5):
    t = (x - RAMP_X[0]) / (RAMP_X[1] - RAMP_X[0])
    for i, row in enumerate((ROW_A, ROW_B, ROW_A)):
        ramp = LEVELS[i] + RISE * (t if row == ROW_A else 1.0 - t)
        hull = COURIER.point(x, 0.0)
        _brackets.bar(
            (x, row, ramp - 0.35), (hull.x, hull.y - 0.1, hull.z), 0.1, "iron"
        )
_brackets.add("courier_brackets", collide=False)
# The pendulum swings across ramp 2 from an arm under the edge of ramp 3.
PENDULUM_X = -15.75
_ramp_2 = LEVELS[1] + RISE * (RAMP_X[1] - PENDULUM_X) / (RAMP_X[1] - RAMP_X[0])
PIVOT: Place = (PENDULUM_X, ROW_B, _ramp_2 + 4.6)
kit.marker(
    "pendulum",
    at=PIVOT,
    rotation=(0, 0, -90.0),
    period=4.0,
    swing=45.0,
    name="courier_hook",
)
_arm = town.Parts()
_arm.bar(
    (PENDULUM_X, ROW_A + 1.4, PIVOT[2]),
    (PENDULUM_X, ROW_B + 0.2, PIVOT[2]),
    0.16,
    "iron",
)
_arm.bar(
    (PENDULUM_X, ROW_A + 1.4, PIVOT[2] - 1.2),
    (PENDULUM_X, ROW_B - 0.5, PIVOT[2]),
    0.1,
    "iron",
)
_arm.add("courier_hook_arm", collide=False)
# The top of the Courier (+340.1), then gangplank C to the Sailmakers' roof, 10 s a cycle.
harbour.promenade(
    COURIER,
    [(-24.0, COURIER_TOP), (-6.5, COURIER_TOP)],
    2.4,
    kerbs=[("s", -24.0, -6.5), ("n", -24.0, RAMP_X[1])],
)
SAILMAKERS = (2.0, 61.6, 25.4, 71.6)
SAILMAKERS_TOP = 344.0
GANGPLANK_C_LOW: Place = (-4.9, 66.0, COURIER_TOP)
GANGPLANK_C_HIGH: Place = (SAILMAKERS[0] - 1.6, 66.0, SAILMAKERS_TOP)
kit.marker(
    "moving_platform",
    at=GANGPLANK_C_LOW,
    points=[GANGPLANK_C_HIGH],
    period=10.0,
    stop=1.5,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="gangplank_c",
)

# East way: a roof vent on the Harbourmaster, the loose shingles (+328.5), two stacks, the
# propeller gear (+331.5), a vent, the mast platform (+340) and three steps.
MAST_ROW = 51.0
HM_VENT = (0.0, MAST_ROW)
vent("vent_harbourmaster", (*HM_VENT, 322.0), 9.6)
SHINGLES = (3.4, 7.4)
harbour.storey(
    "shingle_house", (3.5, 49.6), (7.3, 52.4), 324.2, 328.0, seed=6, windows="ns"
)
kit.marker(
    "crumbling_tiles",
    at=((SHINGLES[0] + SHINGLES[1]) / 2, MAST_ROW, 328.5),
    width=4.0,
    depth=3.0,
    tile=1.0,
    name="shingles",
)
MAST_STACKS = [(7.7, 10.0, 329.5), (10.3, 12.6, 330.5)]
for i, (x0, x1, top) in enumerate(MAST_STACKS):
    stack(f"mast_stack_{i + 1}", (x0, MAST_ROW - 1.2), (x1, MAST_ROW + 1.2), top)
GEAR: Place = (14.95, MAST_ROW, 331.5)
kit.marker(
    "turning_gear", at=GEAR, period=8.0, radius=2.1, teeth=12, name="propeller_gear"
)
harbour.propeller("propeller_gear_blades", (GEAR[0], GEAR[1], GEAR[2] - 2.7), 1.5)
town.block(
    "propeller_gear_axle",
    (GEAR[0] - 0.2, GEAR[1] - 0.2, 324.0),
    (GEAR[0] + 0.2, GEAR[1] + 0.2, GEAR[2] - 0.5),
    "iron",
    collide=False,
)
MAST_LEDGE = (17.15, 20.0)
deck(
    "mast_ledge",
    (MAST_LEDGE[0], MAST_ROW - 1.5),
    (MAST_LEDGE[1], MAST_ROW + 1.5),
    GEAR[2],
    "sn",
)
MAST_VENT = (18.6, MAST_ROW)
vent("vent_mast", (*MAST_VENT, GEAR[2]), 11.0)
MAST_TOP = 340.0
MAST_DECK = (21.8, 48.5, 26.8, 53.5)
deck("mast_platform", MAST_DECK[:2], MAST_DECK[2:], MAST_TOP, "se")
harbour.mast("mast", (24.3, MAST_ROW, 316.0), MAST_TOP - 0.3, width=2.4, head=1.4)
MAST_STEPS_X = (22.4, 25.4)
MAST_COL = (MAST_STEPS_X[0] + MAST_STEPS_X[1]) / 2
MAST_STEPS = [(53.8, 56.1, 341.0), (56.4, 58.7, 342.0), (59.0, 61.3, 343.0)]
for i, (y0, y1, top) in enumerate(MAST_STEPS):
    crate_step(
        f"mast_step_{i + 1}",
        (MAST_STEPS_X[0], y0),
        (MAST_STEPS_X[1], y1),
        top,
        top - 1.2,
    )

# The Sailmakers' roof (+344): the second rest ledge.
house(
    "sailmakers",
    SAILMAKERS[:2],
    SAILMAKERS[2:],
    SAILMAKERS_TOP,
    height=4.5,
    seed=7,
    gaps=[("w", 64.4, 67.6), ("s", MAST_STEPS_X[0] - 0.1, SAILMAKERS[2])],
)

# --- Routes ----------------------------------------------------------------------------------------

FINISH: Place = (14.0, 66.6, SAILMAKERS_TOP)

# Part 1, first run: the crates, Roof 1 and its vent, Roof 2, the dormers and gangway A.
FIRST[1] = [
    ((-5.0, JETTY_ROW, 300.0), "speed 4"),
    ((-6.4, JETTY_ROW, 300.0), "jump; speed 3"),
    ((-8.1, JETTY_ROW, 301.0), "speed 3"),
    ((-9.0, JETTY_ROW, 301.0), "jump; speed 3"),
    ((-10.7, JETTY_ROW, 302.0), "speed 3"),
    ((-11.6, JETTY_ROW, 302.0), "jump; speed 3"),
    ((-13.4, JETTY_ROW, 303.0), "speed 3"),
    ((-23.3, JETTY_ROW, RIDGE[2]), ""),
    ((RIDGE_VENT[0], RIDGE_VENT[1] - 1.2, RIDGE[2]), "speed 3"),
    ((RIDGE_VENT[0], 39.6, 315.0), "speed 3"),
]
EXPERT[1] = FIRST[1][:]
FIRST[1] += [
    ((-22.6, DORMER_ROW, 315.0), "speed 3"),
    ((-21.8, DORMER_ROW, 315.0), "jump; speed 3"),
]
for i, (x0, x1, top) in enumerate(DORMERS):
    FIRST[1].append(((x0 + 0.8, DORMER_ROW, top), "speed 3"))
    if i < len(DORMERS) - 1:
        FIRST[1].append(((DORMERS[i + 1][0] - 0.9, DORMER_ROW, top), "jump; speed 3"))
FIRST[1] += [
    ((-14.3, DORMER_ROW, 318.0), "wait_until gangway_a 7.2 7.8"),
    (GANGWAY_A_LOW, "speed 3; wait_until gangway_a 4.1 4.9"),
    ((-5.8, GANGWAY_A_HIGH[1], 322.0), "speed 3"),
]
# Expert: from the landing on Roof 2 to the wing, then up the rope.
EXPERT[1] += [
    ((-26.5, ROPE_Y, 315.0), "speed 4"),
    (ROPE_1[0], ""),
    (ROPE_1[1], ""),
    ((-5.5, ROPE_Y, 322.0), "speed 4"),
]

# Part 2, first run: the tile steps, the Courier's ramps and gangplank C.
FIRST[2] = [((TILE_COL, 54.0, 322.0), "speed 3")]
_edges = [56.3] + [y0 for y0, _, _ in TILES[1:]] + [64.1]
_tops = [322.0] + [top for _, _, top in TILES]
for i, edge in enumerate(_edges):
    FIRST[2].append(((TILE_COL, edge - 0.9, _tops[i]), "jump; speed 3"))
    FIRST[2].append(
        ((TILE_COL, edge + 0.8 if i < 3 else 65.6, _tops[i] + 1.0), "speed 3")
    )
FIRST[2] += [
    ((-23.2, 66.4, COURIER_DECK), "speed 6"),
    ((-23.2, ROW_A, COURIER_DECK), "speed 3"),
    ((RAMP_X[1] + 0.4, ROW_A, LEVELS[1]), ""),
    ((-8.0, ROW_A, LEVELS[1]), "speed 3"),
    ((-8.0, ROW_B, LEVELS[1]), "speed 3"),
    (
        (-12.5, ROW_B, LEVELS[1] + RISE * 3.0 / 12.5),
        "speed 3; wait_until courier_hook 1.6 2.0",
    ),
    ((RAMP_X[0] - 0.4, ROW_B, LEVELS[2]), ""),
    ((-23.5, ROW_B, LEVELS[2]), "speed 3"),
    ((-23.5, ROW_A, LEVELS[2]), "speed 3"),
    ((RAMP_X[1] + 0.4, ROW_A, LEVELS[3]), ""),
    ((-8.0, ROW_A, LEVELS[3]), "speed 3"),
    ((-8.0, 66.0, COURIER_TOP), "speed 3; wait_until gangplank_c 9.0 9.8"),
    (GANGPLANK_C_LOW, "speed 3; wait_until gangplank_c 5.2 6.2"),
    ((SAILMAKERS[0] + 1.5, 66.0, SAILMAKERS_TOP), "speed 3"),
]
# Part 2, expert: the roof vent, the shingles, the stacks, the gear, a vent and the mast.
EXPERT[2] = [
    ((HM_VENT[0] - 3.0, MAST_ROW, 322.0), "speed 3"),
    ((SHINGLES[0] + 1.2, MAST_ROW, 328.5), "speed 3"),
    ((MAST_STACKS[0][0] - 0.9, MAST_ROW, 328.5), "jump; speed 3"),
    ((MAST_STACKS[0][0] + 0.8, MAST_ROW, 329.5), "speed 3"),
    ((MAST_STACKS[1][0] - 0.9, MAST_ROW, 329.5), "jump; speed 3"),
    ((MAST_STACKS[1][0] + 0.8, MAST_ROW, 330.5), "speed 3"),
    ((GEAR[0] - 3.0, MAST_ROW, 330.5), "jump; speed 3"),
    ((GEAR[0], MAST_ROW, GEAR[2]), "speed 3"),
    ((MAST_VENT[0] - 1.2, MAST_ROW, GEAR[2]), "speed 3"),
    ((MAST_VENT[0] + 5.0, MAST_ROW, MAST_TOP), "speed 3"),
    ((MAST_COL, MAST_STEPS[0][0] - 0.9, MAST_TOP), "jump; speed 3"),
]
for i, (y0, _, top) in enumerate(MAST_STEPS):
    EXPERT[2].append(((MAST_COL, y0 + 0.8, top), "speed 3"))
    edge = MAST_STEPS[i + 1][0] if i < len(MAST_STEPS) - 1 else SAILMAKERS[1]
    EXPERT[2].append(((MAST_COL, edge - 0.9, top), "jump; speed 3"))
EXPERT[2].append(((MAST_COL, SAILMAKERS[1] + 1.2, SAILMAKERS_TOP), "speed 3"))

# --- Start, finish, routes ------------------------------------------------------------------------

kit.marker("start", at=START)
kit.marker("finish", at=FINISH)


def route(kind: str, legs: list[Leg]) -> None:
    """Places the route of `kind` through the legs, ending on the finish pad."""
    legs = [*legs, (FINISH, "")]
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


route("first_run", [leg for part in sorted(FIRST) for leg in FIRST[part]])
route("expert", [leg for part in sorted(EXPERT) for leg in EXPERT[part]])

# --- Shots ----------------------------------------------------------------------------------------

kit.shot("overview", at=(48.0, -10.0, 352.0), rotation=(-22, 0, 40))
kit.shot("start", at=(0.0, 24.0, 301.6), rotation=(6, 0, 0))
kit.shot("egg", at=(4.0, 26.0, 299.5), rotation=(-12, 0, -50))
kit.shot("first_roofs", at=(-4.0, 22.0, 309.0), rotation=(4, 0, 40))
kit.shot("tender", at=(30.0, 18.0, 312.0), rotation=(-6, 0, 30))
kit.shot("courier", at=(-6.0, 90.0, 338.0), rotation=(-4, 0, 160))
kit.shot("finish", at=(4.0, 58.0, 346.0), rotation=(-6, 0, -30))
