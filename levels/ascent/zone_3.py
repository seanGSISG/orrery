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
# The fins of a ship with a deck on its back: no fin on top, where it would cross the deck.
LOW_FINS = (0.0, 180.0, 270.0)
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
FIN = harbour.fins(TENDER, root=5.0, span=4.0, floors=True, angles=LOW_FINS)
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
SAILMAKERS = (2.0, 61.6, 25.4, 78.0)
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
    gaps=[
        ("w", 64.4, 67.6),
        ("s", MAST_STEPS_X[0] - 0.1, SAILMAKERS[2]),
        ("n", 2.5, 5.7),
    ],
)

# --- Part 3: chimney field, +344 to +382 --------------------------------------------------------

# West way: three steps north from the Sailmakers' roof, then Roof 3, a slate slope of 20° up
# west to a ridge with a chimney vent.
P3_COL = 4.1
P3_STEPS = [(78.3, 80.6, 345.0), (80.9, 83.2, 346.0), (83.5, 85.8, 347.0)]
for i, (y0, y1, top) in enumerate(P3_STEPS):
    stack(f"field_step_{i + 1}", (P3_COL - 1.5, y0), (P3_COL + 1.5, y1), top)
ROOF_3 = (-15.5, 86.1, 6.0, 95.1)
R3_GUTTER = (2.0, 348.0)
R3_RIDGE = (-15.5, -12.1, 353.13)
r3x0, r3y0, r3x1, r3y1 = ROOF_3


def slope_roof(
    name: str,
    lo: Point,
    hi: Point,
    gutter: tuple[float, float, float],
    ridge: tuple[float, float, float],
    seed: int,
) -> None:
    """Adds a house with a roof that slopes along x: a flat gutter walk from gutter[0] to
    gutter[1] at gutter[2], a slate slope from gutter[0] to ridge's near end, and a flat ridge
    walk between ridge[0] and ridge[1] at ridge[2]. The storey under it is 4 m tall."""
    (x0, y0), (x1, y1) = lo, hi
    g0, _, gz = gutter
    k0, k1, kz = ridge
    near = k1 if g0 > k1 else k0
    base = gz - 0.25
    harbour.storey(
        name, (x0, y0), (x1, y1), base - 4.0, base, seed=seed, windows="nesw"
    )
    mass = town.Parts()
    mass.prism([(g0, base), (near, base), (near, kz - 0.3)], y0, y1, "y", "wall")
    mass.box((k0, y0, base), (k1, y1, kz - 0.25), "wall")
    mass.add(f"{name}_mass")
    for part, (a, b, z) in (("gutter", gutter), ("ridge", ridge)):
        harbour.slab(
            f"{name}_{part}", (a, y0 - EAVE, z - 0.25), (b, y1 + EAVE, z), "dressed"
        )
    mid = (y0 + y1) / 2
    harbour.slope(
        f"{name}_slope",
        (g0, mid, gz),
        (near, mid, kz),
        y1 - y0 + 2 * EAVE,
        "slate_turned",
    )
    for side, y in (("s", y0 - EAVE), ("n", y1 + EAVE)):
        harbour.kerb(
            f"{name}_kerb_{side}",
            [(g0, y, gz), (near, y, kz)],
            side="right" if (side == "s") == (near > g0) else "left",
        )


slope_roof(
    "roof_3", (r3x0, r3y0), (r3x1, r3y1), (R3_GUTTER[0], r3x1, 348.0), R3_RIDGE, 8
)
CHIMNEY_VENT = (-13.8, 93.6)
town.chimney("roof_3_stack", (-13.8, 87.6, 353.13), 1.1, 1.8)
vent("vent_chimney", (*CHIMNEY_VENT, R3_RIDGE[2]), 10.5)
for i, (x, y) in enumerate([(-4.0, 87.4), (-8.5, 93.8), (-1.0, 93.9)]):
    height = R3_GUTTER[1] + (R3_GUTTER[0] - x) * math.tan(math.radians(20.0))
    town.chimney(f"roof_3_chimney_{i}", (x, y, height - 0.3), 0.9, 1.8)

# Roof 4 (+361 to +366): a slate slope of 20° up east, with a bumper; a vent on its ridge.
ROOF_4 = (-17.0, 97.3, 7.5, 107.3)
r4x0, r4y0, r4x1, r4y1 = ROOF_4
R4_GUTTER = (-17.0, -10.0, 361.0)
R4_RIDGE = (4.1, 7.5, 366.13)
slope_roof("roof_4", (r4x0, r4y0), (r4x1, r4y1), R4_GUTTER, R4_RIDGE, 9)
kit.marker("bumper", at=(-2.0, 104.6, 363.9), name="bumper_roof_4")
ROOF_4_VENT = (5.8, 105.6)
vent("vent_roof_4", (*ROOF_4_VENT, R4_RIDGE[2]), 10.5)
for i, (x, y) in enumerate([(-6.0, 98.3), (1.0, 98.4), (-14.5, 106.3)]):
    height = 361.0 + max(0.0, x + 10.0) * math.tan(math.radians(20.0))
    town.chimney(f"roof_4_chimney_{i}", (x, y, height - 0.3), 0.9, 1.6)

# Roof 5 (+374), then gangway D to the Signal roof, 12 s a cycle.
ROOF_5 = (0.0, 109.0, 10.0, 117.0)
SIGNAL = (16.6, 99.0, 27.6, 110.0)
SIGNAL_TOP = 382.0
GANGWAY_D_LOW: Place = (11.6, 113.0, 374.0)
GANGWAY_D_HIGH: Place = (SIGNAL[0] - 1.6, 109.4 - 0.5, SIGNAL_TOP)
house(
    "roof_5",
    ROOF_5[:2],
    ROOF_5[2:],
    374.0,
    seed=10,
    gaps=[("s", 3.8, 7.8), ("e", 111.4, 114.6)],
)
kit.marker(
    "moving_platform",
    at=GANGWAY_D_LOW,
    points=[GANGWAY_D_HIGH],
    period=12.0,
    stop=1.5,
    width=3.0,
    depth=3.0,
    finish="wood",
    name="gangway_d",
)

# East way: the Lamplighter. A vent on the Sailmakers' roof throws the marble to its gondola
# (+351); a vent on a sponson throws it to the stern gallery (+359.5); the flying gangway runs
# along the ship up to the bow gallery (+365.5); a vent, a platform (+374) and a vent.
LAMPLIGHTER = Ship("lamplighter", (8.0, 82.0, 360.0), 26.0, 6.0)
LAMP_DECK = 351.0
harbour.envelope(LAMPLIGHTER)
harbour.fins(LAMPLIGHTER, root=6.0, span=2.6)
harbour.gondola(
    LAMPLIGHTER,
    17.0,
    31.0,
    LAMP_DECK,
    3.6,
    kerbs=[("s", 17.0, 19.4), ("s", 22.6, 31.0), ("n", 17.0, 27.3)],
)
harbour.engine("lamplighter_engine_1", (14.0, 74.6, 356.0))
harbour.engine("lamplighter_engine_2", (24.0, 76.6, 357.5))
SAIL_VENT = (21.0, 76.8)
vent("vent_sailmakers", (*SAIL_VENT, SAILMAKERS_TOP), 10.0)
deck("lamplighter_sponson", (27.5, 83.8), (31.0, 91.2), LAMP_DECK, "en")
LAMP_VENT = (29.25, 90.0)
vent("vent_lamplighter", (*LAMP_VENT, LAMP_DECK), 11.2)
STERN_GALLERY = (27.5, 93.2, 33.0, 97.6)
GALLERY_TOP = 359.5
deck("stern_gallery", STERN_GALLERY[:2], STERN_GALLERY[2:], GALLERY_TOP, "en")
FLYING_ROW = 95.4
BOW_TOP = 365.5
BOW_GALLERY = (8.0, 92.6, 12.5, 99.0)
harbour.slope(
    "flying_gangway",
    (STERN_GALLERY[0], FLYING_ROW, GALLERY_TOP),
    (BOW_GALLERY[2], FLYING_ROW, BOW_TOP),
    2.4,
    "wood",
)
for edge, side in ((FLYING_ROW - 1.2, "left"), (FLYING_ROW + 1.2, "right")):
    harbour.kerb(
        f"flying_gangway_{side}",
        [(STERN_GALLERY[0], edge, GALLERY_TOP), (BOW_GALLERY[2], edge, BOW_TOP)],
        side=side,
    )
deck("bow_gallery", BOW_GALLERY[:2], BOW_GALLERY[2:], BOW_TOP, "ws")
# Ropes from the envelope hold the gangway and the galleries.
_hangers = town.Parts()
for x in (31.0, 25.0, 19.0, 13.0, 10.0):
    hull = LAMPLIGHTER.point(x, 45.0)
    z = GALLERY_TOP + (STERN_GALLERY[0] - min(x, STERN_GALLERY[0])) * (
        BOW_TOP - GALLERY_TOP
    ) / (STERN_GALLERY[0] - BOW_GALLERY[2])
    for y in (FLYING_ROW - 1.1, FLYING_ROW + 1.1):
        harbour.line(_hangers, (x, y, z), (hull.x, hull.y, hull.z), 0.05)
_hangers.add("flying_gangway_hangers", collide=False)
BOW_VENT = (10.25, 97.6)
vent("vent_bow", (*BOW_VENT, BOW_TOP), 11.0)
LAMP_PLATFORM = (7.5, 100.8, 15.0, 106.8)
LAMP_PLATFORM_TOP = 374.0
deck("lamp_platform", LAMP_PLATFORM[:2], LAMP_PLATFORM[2:], LAMP_PLATFORM_TOP, "wn")
harbour.mast("lamp_platform_mast", (11.25, 103.8, 352.0), LAMP_PLATFORM_TOP - 0.3)
PLATFORM_VENT = (13.4, 104.0)
vent("vent_platform", (*PLATFORM_VENT, LAMP_PLATFORM_TOP), 10.8)

# The Signal roof (+382): the third rest ledge.
house(
    "signal",
    SIGNAL[:2],
    SIGNAL[2:],
    SIGNAL_TOP,
    height=4.5,
    seed=11,
    gaps=[("w", 100.5, 110.0), ("n", 20.8, 22.2), ("n", 24.2, 27.4)],
)
harbour.lamp("signal_lamp", (26.9, 99.7, SIGNAL_TOP))

# --- Part 4: the flotilla, +382 to +419 ---------------------------------------------------------


def span(length: float, angle: float) -> tuple[float, float]:
    """Returns the plan distance between the two floor edges that a rope of `length` m at
    `angle` degrees joins (its slope and both heels), and its rise."""
    a = math.radians(angle)
    return length * math.cos(a) + 2 * harbour.HEEL, length * math.sin(a)


def gangplank(name: str, low: Place, high: Place) -> None:
    """Places a gangplank: a moving deck 3 m square from low to high, 10 s a cycle."""
    kit.marker(
        "moving_platform",
        at=low,
        points=[high],
        period=10.0,
        stop=1.0,
        width=3.0,
        depth=3.0,
        finish="wood",
        name=name,
    )


def skiff(ship: Ship, deck_x: tuple[float, float], width: float, top: float) -> None:
    """Adds an airship whose back carries a flat deck of `width` m at `top` from deck_x[0] to
    deck_x[1], with brass kerbs along both sides, and a gondola and two engines under it."""
    harbour.envelope(ship)
    harbour.fins(ship, root=ship.length * 0.22, span=ship.radius * 0.6, angles=LOW_FINS)
    harbour.promenade(ship, [(deck_x[0], top), (deck_x[1], top)], width)
    x0 = ship.nose[0] + ship.length * 0.25
    x1 = ship.nose[0] + ship.length * 0.6
    harbour.gondola(ship, x0, x1, ship.bottom(ship.widest) - 1.2, 2.4, windows=True)
    for side in (-1.0, 1.0):
        y = ship.nose[1] + side * (ship.radius + 0.7)
        harbour.engine(
            f"{ship.name}_engine_{int(side + 1)}", (x1 - 1.0, y, ship.nose[2] - 1.0)
        )


# Rope 1 and gangplank 1: from the Signal roof north to Skiff 1.
ROPE_COL_1 = 21.5
_plan_1, _rise_1 = span(24.0, 30.0)
SKIFF_1_TOP = SIGNAL_TOP + _rise_1
SKIFF_1_Y = (SIGNAL[3] + _plan_1, SIGNAL[3] + _plan_1 + 6.0)
SKIFF_1 = Ship("skiff_1", (14.5, sum(SKIFF_1_Y) / 2, SKIFF_1_TOP - 3.85), 19.0, 3.4)
skiff(SKIFF_1, (17.0, 31.0), 6.0, SKIFF_1_TOP)
ROPE_2_FLOOR = harbour.rope(
    "rope_2",
    (ROPE_COL_1, SIGNAL[3], SIGNAL_TOP),
    (ROPE_COL_1, SKIFF_1_Y[0], SKIFF_1_TOP),
)
GANGPLANK_1 = (25.8, (SIGNAL[3] + 1.6, SIGNAL_TOP), (SKIFF_1_Y[0] - 1.6, SKIFF_1_TOP))
gangplank(
    "gangplank_1",
    (GANGPLANK_1[0], *GANGPLANK_1[1]),
    (GANGPLANK_1[0], *GANGPLANK_1[2]),
)
# Rope 2 and gangplank 2: from Skiff 1 west to Skiff 2.
ROPE_ROW_2 = SKIFF_1_Y[0] + 1.35
GANGPLANK_ROW_2 = SKIFF_1_Y[1] - 1.25
_plan_2, _rise_2 = span(22.5, 32.0)
SKIFF_2_TOP = SKIFF_1_TOP + _rise_2
SKIFF_2_X = (17.0 - _plan_2 - 14.0, 17.0 - _plan_2)
SKIFF_2_Y = (ROPE_ROW_2 - 2.1, GANGPLANK_ROW_2 + 2.1)
SKIFF_2 = Ship(
    "skiff_2", (SKIFF_2_X[0] - 2.6, sum(SKIFF_2_Y) / 2, SKIFF_2_TOP - 4.25), 19.0, 3.8
)
skiff(SKIFF_2, SKIFF_2_X, SKIFF_2_Y[1] - SKIFF_2_Y[0], SKIFF_2_TOP)
ROPE_3_FLOOR = harbour.rope(
    "rope_3", (17.0, ROPE_ROW_2, SKIFF_1_TOP), (SKIFF_2_X[1], ROPE_ROW_2, SKIFF_2_TOP)
)
gangplank(
    "gangplank_2",
    (17.0 - 1.6, GANGPLANK_ROW_2, SKIFF_1_TOP),
    (SKIFF_2_X[1] + 1.6, GANGPLANK_ROW_2, SKIFF_2_TOP),
)
# Rope 3 and gangplank 3: from Skiff 2 on west to the Tanker. The rope needs a run-up: the deck
# of Skiff 2 gives 14 m in line with it.
# The brief asks for 35°: the marble stalls about 20 m up a beam of 32° or more, so this rope is
# as long and as steep as rope 3.
_plan_3, _rise_3 = span(22.5, 32.0)
TANKER_TOP = SKIFF_2_TOP + _rise_3
TANKER_DECK = (
    SKIFF_2_X[0] - _plan_3 - 24.0,
    ROPE_ROW_2 - 5.0,
    SKIFF_2_X[0] - _plan_3,
    ROPE_ROW_2 + 5.0,
)
TANKER = Ship(
    "tanker", (TANKER_DECK[0] - 4.0, ROPE_ROW_2, TANKER_TOP - 6.45), 32.0, 6.0
)
harbour.envelope(TANKER)
harbour.fins(TANKER, root=7.0, span=3.6, angles=LOW_FINS)
harbour.promenade(
    TANKER,
    [(TANKER_DECK[0], TANKER_TOP), (TANKER_DECK[2], TANKER_TOP)],
    TANKER_DECK[3] - TANKER_DECK[1],
    kerbs=[("s", TANKER_DECK[0], TANKER_DECK[2] - 4.0)],
)
_tx = TANKER.nose[0]
harbour.gondola(TANKER, _tx + 9.0, _tx + 23.0, TANKER.bottom(TANKER.widest) - 1.4, 3.2)
for i, x in enumerate((_tx + 15.0, _tx + 25.0)):
    harbour.engine(
        f"tanker_engine_{i}", (x, TANKER.nose[1] - 7.0, TANKER.nose[2] - 2.0)
    )
ROPE_4_FLOOR = harbour.rope(
    "rope_4",
    (SKIFF_2_X[0], ROPE_ROW_2, SKIFF_2_TOP),
    (TANKER_DECK[2], ROPE_ROW_2, TANKER_TOP),
)
gangplank(
    "gangplank_3",
    (SKIFF_2_X[0] - 1.6, GANGPLANK_ROW_2, SKIFF_2_TOP),
    (TANKER_DECK[2] + 1.6, GANGPLANK_ROW_2, TANKER_TOP),
)

# --- Part 5: rigging, +417.8 to +460 ------------------------------------------------------------

# The Flagship, the biggest ship of the harbour, lies west of the Tanker. Its gondola deck
# (+460) is the last rest ledge; both ways of part 5 climb to its east end, the crow's nests on
# NEST_ROW and the cargo lifts on CARGO_ROW.
FLAG_DECK_TOP = 460.0
NEST_ROW = ROPE_ROW_2 - 2.9
CARGO_ROW = GANGPLANK_ROW_2
FLAG_ROW = (NEST_ROW + CARGO_ROW) / 2
# A vent stands 1.6 m from the west end of its floor and throws the marble NEST_RISE m up onto
# the next floor, whose east end is THROW m west of the vent.
NEST_RISE = 9.5
THROW = 3.2
NEST_LENGTH = 8.0
NEST_HALF = 1.75
VENT_1 = TANKER_DECK[2] - 6.5
vent("vent_tanker", (VENT_1, NEST_ROW, TANKER_TOP), NEST_RISE + 2.8)
# Nests 1 and 2 stand on masts on the Tanker; the yardarm joins nest 2 to nest 3.
NESTS: list[tuple[float, float, float]] = []
_east, _top = VENT_1 - THROW, TANKER_TOP
for i in range(4):
    if i == 2:
        _plan_y, _rise_y = span(9.8, 24.0)
        _east, _top = _east - _plan_y, _top + _rise_y
    else:
        _top += NEST_RISE
    NESTS.append((_east - NEST_LENGTH, _east, _top))
    _east -= NEST_LENGTH if i == 1 else NEST_LENGTH - 1.6 + THROW
for i, (x0, x1, top) in enumerate(NESTS):
    deck(
        f"nest_{i + 1}",
        (x0, NEST_ROW - NEST_HALF),
        (x1, NEST_ROW + NEST_HALF),
        top,
        "ns",
    )
    if i != 1:
        rise = NEST_RISE if i < 3 else FLAG_DECK_TOP - top
        vent(f"vent_nest_{i + 1}", (x0 + 1.6, NEST_ROW, top), rise + 2.8)
for i in (0, 1):
    x0, x1, top = NESTS[i]
    harbour.mast(f"nest_{i + 1}_mast", (x1 - 3.0, NEST_ROW, TANKER_TOP), top - 0.3)
YARDARM = harbour.rope(
    "yardarm",
    (NESTS[1][0], NEST_ROW, NESTS[1][2]),
    (NESTS[2][1], NEST_ROW, NESTS[2][2]),
)
FLAG_E = NESTS[3][0] + 1.6 - THROW
FLAGSHIP = Ship(
    "flagship", (FLAG_E - 10.0 - 25.2, FLAG_ROW, FLAG_DECK_TOP + 14.0), 84.0, 9.0
)
harbour.envelope(FLAGSHIP)
harbour.gondola(
    FLAGSHIP,
    FLAG_E - 20.0,
    FLAG_E,
    FLAG_DECK_TOP,
    10.0,
    kerbs=[("s", FLAG_E - 20.0, FLAG_E)],
)

# The cargo way: three lifts (moving platforms) west and up, a walkway with two cargo hooks
# (pendulums) between lifts 1 and 2, and a pallet deck between lifts 2 and 3.
WALK_LENGTH = 15.5
PALLET_LENGTH = 4.5
CARGO_RISE = (13.0, 12.5)
WALK_TOP = TANKER_TOP + CARGO_RISE[0]
PALLET_TOP = WALK_TOP + CARGO_RISE[1]
_drift = (TANKER_DECK[0] - FLAG_E - WALK_LENGTH - PALLET_LENGTH) / 3 - 3.2
LIFTS: list[float] = []  # the x of each lift's low end


def cargo_lift(i: int, west: float, low: float, high: float) -> float:
    """Places cargo lift i from beside the west end `west` of a floor at `low` up to `high`,
    _drift m further west. Returns the x of the east end of the floor it serves above."""
    x = west - 1.6
    LIFTS.append(x)
    gangplank(f"cargo_lift_{i}", (x, CARGO_ROW, low), (x - _drift, CARGO_ROW, high))
    return x - _drift - 1.6


_walk_e = cargo_lift(1, TANKER_DECK[0], TANKER_TOP, WALK_TOP)
WALK = (_walk_e - WALK_LENGTH, _walk_e)
_pallet_e = cargo_lift(2, WALK[0], WALK_TOP, PALLET_TOP)
PALLETS = (_pallet_e - PALLET_LENGTH, _pallet_e)
cargo_lift(3, PALLETS[0], PALLET_TOP, FLAG_DECK_TOP)
for name, (x0, x1), top in (
    ("cargo_walk", WALK, WALK_TOP),
    ("pallets", PALLETS, PALLET_TOP),
):
    deck(name, (x0, CARGO_ROW - 1.5), (x1, CARGO_ROW + 1.5), top, "ns")
HOOKS = (WALK[1] - 5.5, WALK[1] - 11.5)
_gantry = town.Parts()
for i, x in enumerate(HOOKS):
    kit.marker(
        "pendulum",
        at=(x, CARGO_ROW, WALK_TOP + 4.6),
        rotation=(0, 0, -90.0),
        period=4.0,
        swing=45.0,
        name=f"cargo_hook_{i + 1}",
    )
    for side in (-1.0, 1.0):
        y = CARGO_ROW + side * 1.75
        _gantry.bar((x, y, WALK_TOP - 0.3), (x, y, WALK_TOP + 4.8), 0.1, "iron")
    _gantry.bar(
        (x, CARGO_ROW - 1.75, WALK_TOP + 4.8),
        (x, CARGO_ROW + 1.75, WALK_TOP + 4.8),
        0.12,
        "iron",
    )
# The rigging: ropes from the corners of the hanging floors up to the keel of the Flagship.
_floors = [(x0, x1, NEST_ROW, NEST_HALF, top) for x0, x1, top in NESTS[2:]] + [
    (*WALK, CARGO_ROW, 1.5, WALK_TOP),
    (*PALLETS, CARGO_ROW, 1.5, PALLET_TOP),
]
for x0, x1, row, half, top in _floors:
    for x in (x0 + 0.3, x1 - 0.3):
        keel = FLAGSHIP.point(x, 270.0)
        for y in (row - half + 0.1, row + half - 0.1):
            harbour.line(_gantry, (x, y, top - 0.3), (x, keel.y, keel.z + 0.2), 0.04)
_gantry.add("rigging", collide=False)

# --- Routes ----------------------------------------------------------------------------------------

FINISH: Place = (FLAG_E - 10.0, FLAG_ROW, FLAG_DECK_TOP)

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

# Part 3, first run: the steps, Roof 3, the chimney vent, Roof 4, its vent, Roof 5, gangway D.
FIRST[3] = [((P3_COL, 76.0, SAILMAKERS_TOP), "speed 4")]
_tops = [SAILMAKERS_TOP] + [top for _, _, top in P3_STEPS]
_edges = [y0 for y0, _, _ in P3_STEPS] + [r3y0]
for i, edge in enumerate(_edges):
    FIRST[3].append(((P3_COL, edge - 0.9, _tops[i]), "jump; speed 3"))
    FIRST[3].append(((P3_COL, edge + 0.8, _tops[i] + 1.0), "speed 3"))
FIRST[3] += [
    ((R3_GUTTER[0] + 0.8, 90.6, R3_GUTTER[1]), "speed 3"),
    ((R3_RIDGE[1] - 0.5, 90.6, R3_RIDGE[2]), ""),
    ((CHIMNEY_VENT[0], CHIMNEY_VENT[1] - 1.2, R3_RIDGE[2]), "speed 3"),
    ((CHIMNEY_VENT[0], r4y0 + 1.7, R4_GUTTER[2]), "speed 3"),
    ((R4_GUTTER[1] - 1.0, 101.5, R4_GUTTER[2]), "speed 4"),
    ((R4_RIDGE[0] + 0.5, 101.5, R4_RIDGE[2]), ""),
    ((ROOF_4_VENT[0], ROOF_4_VENT[1] - 1.2, R4_RIDGE[2]), "speed 3"),
    ((ROOF_4_VENT[0], ROOF_5[1] + 2.0, 374.0), "speed 3"),
    ((8.8, GANGWAY_D_LOW[1], 374.0), "wait_until gangway_d 11.2 11.8"),
    (GANGWAY_D_LOW, "speed 3; wait_until gangway_d 6.2 7.2"),
    ((SIGNAL[0] + 2.4, GANGWAY_D_HIGH[1], SIGNAL_TOP), "speed 3"),
]
# Part 3, expert: four vents and the flying gangway of the Lamplighter.
EXPERT[3] = [
    ((SAIL_VENT[0], SAIL_VENT[1] - 2.8, SAILMAKERS_TOP), "speed 4"),
    ((SAIL_VENT[0], SAIL_VENT[1] - 1.2, SAILMAKERS_TOP), "speed 3"),
    ((SAIL_VENT[0], LAMPLIGHTER.nose[1], LAMP_DECK), "speed 3"),
    ((LAMP_VENT[0], LAMPLIGHTER.nose[1] + 0.6, LAMP_DECK), "speed 3"),
    ((LAMP_VENT[0], LAMP_VENT[1] - 1.2, LAMP_DECK), "speed 3"),
    ((LAMP_VENT[0], FLYING_ROW, GALLERY_TOP), "speed 3"),
    ((BOW_GALLERY[2] - 0.5, FLYING_ROW, BOW_TOP), ""),
    ((BOW_VENT[0] + 0.9, FLYING_ROW, BOW_TOP), "speed 3"),
    ((BOW_VENT[0], BOW_VENT[1] - 1.2, BOW_TOP), "speed 3"),
    ((BOW_VENT[0], 103.4, LAMP_PLATFORM_TOP), "speed 3"),
    ((PLATFORM_VENT[0] - 1.2, PLATFORM_VENT[1], LAMP_PLATFORM_TOP), "speed 3"),
    ((SIGNAL[0] + 2.4, PLATFORM_VENT[1], SIGNAL_TOP), "speed 3"),
]

# Part 4, first run: the three gangplanks.
FIRST[4] = [
    ((GANGPLANK_1[0], SIGNAL[3] - 1.5, SIGNAL_TOP), "wait_until gangplank_1 9.0 9.8"),
    ((GANGPLANK_1[0], *GANGPLANK_1[1]), "speed 3; wait_until gangplank_1 5.2 5.9"),
    ((GANGPLANK_1[0], SKIFF_1_Y[0] + 1.4, SKIFF_1_TOP), "speed 3"),
    ((17.0 + 1.4, GANGPLANK_ROW_2, SKIFF_1_TOP), "wait_until gangplank_2 9.0 9.8"),
    (
        (17.0 - 1.6, GANGPLANK_ROW_2, SKIFF_1_TOP),
        "speed 3; wait_until gangplank_2 5.2 5.9",
    ),
    ((SKIFF_2_X[1] - 1.4, GANGPLANK_ROW_2, SKIFF_2_TOP), "speed 3"),
    (
        (SKIFF_2_X[0] + 1.4, GANGPLANK_ROW_2, SKIFF_2_TOP),
        "wait_until gangplank_3 9.0 9.8",
    ),
    (
        (SKIFF_2_X[0] - 1.6, GANGPLANK_ROW_2, SKIFF_2_TOP),
        "speed 3; wait_until gangplank_3 5.2 5.9",
    ),
    ((TANKER_DECK[2] - 1.4, GANGPLANK_ROW_2, TANKER_TOP), "speed 3"),
]
# Part 4, expert: the three mooring ropes.
EXPERT[4] = [
    ((ROPE_COL_1, SIGNAL[3] - 4.0, SIGNAL_TOP), "speed 5"),
    (ROPE_2_FLOOR[0], ""),
    (ROPE_2_FLOOR[1], ""),
    ((ROPE_COL_1, ROPE_ROW_2, SKIFF_1_TOP), "speed 2.5"),
    ((19.5, ROPE_ROW_2, SKIFF_1_TOP), "speed 3"),
    (ROPE_3_FLOOR[0], ""),
    (ROPE_3_FLOOR[1], ""),
    (ROPE_4_FLOOR[0], ""),
    (ROPE_4_FLOOR[1], ""),
    ((TANKER_DECK[2] - 2.0, ROPE_ROW_2, TANKER_TOP), "speed 3"),
]

# Part 5, first run: the three cargo lifts, the walkway with its two hooks and the pallets.
FIRST[5] = [
    ((TANKER_DECK[0] + 1.4, CARGO_ROW, TANKER_TOP), "wait_until cargo_lift_1 9.0 9.8"),
    ((LIFTS[0], CARGO_ROW, TANKER_TOP), "speed 3; wait_until cargo_lift_1 5.2 5.9"),
    ((WALK[1] - 1.4, CARGO_ROW, WALK_TOP), "speed 3"),
    (
        (HOOKS[0] + 3.25, CARGO_ROW, WALK_TOP),
        "speed 3; wait_until cargo_hook_1 1.6 2.0",
    ),
    (
        (HOOKS[1] + 3.25, CARGO_ROW, WALK_TOP),
        "speed 3; wait_until cargo_hook_2 1.6 2.0",
    ),
    ((WALK[0] + 1.4, CARGO_ROW, WALK_TOP), "speed 3; wait_until cargo_lift_2 9.0 9.8"),
    ((LIFTS[1], CARGO_ROW, WALK_TOP), "speed 3; wait_until cargo_lift_2 5.2 5.9"),
    ((PALLETS[1] - 1.4, CARGO_ROW, PALLET_TOP), "speed 3"),
    ((PALLETS[0] + 1.4, CARGO_ROW, PALLET_TOP), "wait_until cargo_lift_3 9.0 9.8"),
    ((LIFTS[2], CARGO_ROW, PALLET_TOP), "speed 3; wait_until cargo_lift_3 5.2 5.9"),
    ((FLAG_E - 1.4, CARGO_ROW, FLAG_DECK_TOP), "speed 3"),
]
# Part 5, expert: four vents, the nests and the yardarm.
EXPERT[5] = [
    ((VENT_1 + 3.4, NEST_ROW, TANKER_TOP), "speed 3"),
    ((VENT_1 + 1.2, NEST_ROW, TANKER_TOP), "speed 3"),
    ((VENT_1 - 5.6, NEST_ROW, NESTS[0][2]), "speed 3"),
    ((NESTS[0][0] + 2.8, NEST_ROW, NESTS[0][2]), "speed 3"),
    ((NESTS[0][0] - 4.0, NEST_ROW, NESTS[1][2]), "speed 4"),
    (YARDARM[0], ""),
    (YARDARM[1], ""),
]
for x0, _, top in NESTS[2:]:
    EXPERT[5] += [
        ((x0 + 2.8, NEST_ROW, top), "speed 3"),
        ((x0 - 4.0, NEST_ROW, top + NEST_RISE), "speed 3"),
    ]
EXPERT[5][-1] = ((FLAG_E - 2.4, NEST_ROW, FLAG_DECK_TOP), "speed 3")

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
