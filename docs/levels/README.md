# Level briefs

One brief and one map per level. The brief is the design; the level script follows it. `review/index.html` shows all M1 maps on one page.

| Level | Brief | Map |
|---|---|---|
| B1 Dawn Plaza | `b01.md` | `b01.svg` |
| B2 Loose Hours | `b02.md` | `b02.svg` |
| B3 Spring Court | `b03.md` | `b03.svg` |
| Ascent 1 Clockmaker's Square | `ascent-z1.md` | `ascent-z1.svg` |
| Ascent 2 The Broken Tower | `ascent-z2.md` | `ascent-z2.svg` |
| Ascent 3 Sky Harbour | `ascent-z3.md` | `ascent-z3.svg` |

## Map rules

- Scale: 10 SVG units = 1 m on every map. The coordinates in each SVG are the design positions in decimetres.
- Beginner maps are plans with north up. Colour shows height in 2 m bands. Numbers on the map are spot heights in metres.
- Ascent maps are side views from the south, with a height axis in metres and a small plan.
- Solid white line: the route of a first run. Dashed pink line: the expert route.
- Symbols are larger than life. A gem is 0.5 m wide in the game.

## Sizing numbers

These come from the starting values in `docs/plan.md` §4.2: radius 0.2 m, gravity 20 m/s², top rolling speed 15 m/s, jump impulse 7.5 m/s.

| Quantity | Arithmetic | Result | Design rule |
|---|---|---|---|
| Jump height | 7.5² / (2 × 20) | 1.41 m | Normal step: 1.0 m or less. Expert step: 1.2 to 1.3 m |
| Jump air time on flat ground | 2 × 7.5 / 20 | 0.75 s | |
| Longest flat gap | speed × 0.75 s | 11.2 m at 15 m/s, 6.0 m at 8 m/s | Normal gap: 3 m or less. Expert gap: 4 to 6 m |
| Window to land on a 1.0 m step | 7.5 t − 10 t² = 1.0 | t = 0.17 s to 0.58 s | A 2 m gap with a 1 m step needs 3.5 m/s or more |
| Time to top speed | 15 m/s ÷ 15 m/s² (75 rad/s² × 0.2 m) | 1.0 s over 7.5 m | Give 8 m of run-up before a speed test |
| Steepest ramp that the marble climbs easily | 20 × sin(angle) is well below 15 m/s² | 20° gives 6.8 m/s² | Normal ramp: 20° or less |

## Assumptions about objects

The plan does not give these values. The briefs use the values below. The owner of each object must confirm them.

| Object | Assumed value | Effect on the layouts |
|---|---|---|
| Coil Spring | Adds 20 m/s upward. Apex 20² / (2 × 20) = 10 m. Air time 2.0 s. The pickup returns after 5 s | B3 ledges are 5 to 7 m high |
| Bumper | Pushes at 15 m/s along the contact normal | Bumpers push across a floor. They do not lift the marble onto a ledge |
| Steam Vent | Each vent has a `lift` setting: the height the marble reaches | The briefs give the lift of each vent |
| Trapdoor | Opens 0.5 s after the first touch. Resets after 5 s | A 4 m trapdoor is safe at 8 m/s or more |
| Crumbling Tiles | Fall 0.5 s after the first touch. Return after 5 s | Same rule as the trapdoor |
| Moving platform | Path, period and stop times are settings | The briefs give them |

## Time estimates

The route bot sets the final par and gold times (`docs/plan.md` §4.6): par = bot time × 1.5, gold = bot time × 1.15. Until the bot runs, each brief estimates the bot time T like this:

- T = route length ÷ cruise speed + 0.5 s for each sharp turn + the cost of each jump, wait and lift.
- Cruise speed: 12 m/s on open floor, 10 m/s between jumps, 8 to 9 m/s on a climb.
- A jump onto a step costs 0.9 s in a stair and 0.4 s in a run.

Ascent has no par time. Each zone brief gives a clean climb time and an expert time as targets for the split timer.
