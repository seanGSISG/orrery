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
- Ascent maps are side views from the south, with a height axis in metres and a small plan. Zone 1 is 0 to 150 m, zone 2 is 150 to 300 m, zone 3 is 300 to 500 m.
- Solid white line: the route of a first run. Dashed pink line: the expert route. On the Ascent maps the expert line is drawn only where it leaves the first-run route. Where it is not drawn, the expert follows the white line.
- Where the expert line arcs over a ledge from one Steam Vent to the next, the marble does not land on that ledge.
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

## Object values

These are the `@export` defaults in `game/objects/<type>/<type>.gd`. A marker can set any of them for one object. The code wins over this table.

| Object | Default | Effect on the layouts |
|---|---|---|
| Coil Spring | `launch_speed` 20 m/s: a use raises the speed along up to 20 m/s (a marble that already rises faster keeps its speed). Apex 20² / (2 × 20) = 10 m. Air time 2.0 s. The pickup returns `respawn_delay` 5 s after it is taken, and at a restart. The pickup stays while the slot is full | B3 ledges are 5 to 7 m high |
| Bumper | `speed` 15 m/s: raises the speed away from the drum axis to 15 m/s. The drum is `radius` 0.5 m and `height` 1.0 m | Bumpers push across a floor, also from the top face. They do not lift the marble onto a ledge |
| Steam Vent | `lift` 8 m, column `radius` 1.0 m, `push` 60 m/s². The marble reaches `lift` m above the grate and hovers there while it stays in the column | The briefs set the `lift` of each vent |
| Trapdoor | `delay` 0.5 s after the first touch, then a 0.3 s swing open. The door starts to shut `close_after` 5 s after it starts to open. Panel 4 × 4 × 0.5 m | A 4 m trapdoor is safe at 8 m/s or more |
| Crumbling Tiles | Each tile breaks `delay` 0.5 s after its own first touch. A broken tile does not return by itself: a respawn or a restart brings the tiles back. Grid 4 × 4 m of 2 m `tile`, 0.5 m thick | Same rule as the trapdoor, for each tile. A tile that has gone does not come back until the next respawn |
| Moving platform | `period` 8 s for one cycle with the stops included, `stop` 1 s at each point, `loop` false (there and back), `offset` 0 s. Deck 4 × 4 × 0.5 m | The briefs set the path, period and stop of each platform |
| Pendulum | `period` 4 s, `swing` 60° to each side, `length` 4 m, bob `radius` 0.6 m, `offset` 0 s | The bob sweeps the track when the pivot is about `length` + `radius` above it |
| Turning gear | `period` 8 s for one turn, `radius` 2.1 m to the tooth tips, `teeth` 12, `thickness` 0.5 m, `clockwise` false | |

## Time estimates

Each level script carries two routes: the first-run route and the expert route. The route bot times both (`docs/plan.md` §4.6):

- **Par** = first-run route time × 1.5.
- **Gold** = expert route time × 1.15. Gold needs the expert line.

`just suggest-times <id>` prints both values from the bot's times. `just test-levels` checks that the first-run route finishes under par and the expert route under gold.

Until the bot runs, each brief estimates a route time T like this:

- T = route length ÷ cruise speed + 0.5 s for each sharp turn + the cost of each jump, wait and lift.
- Cruise speed: 12 m/s on open floor, 10 m/s between jumps, 8 to 9 m/s on a climb, 7 m/s on a spiral ramp.
- A jump onto a step costs 0.9 s in a stair and 0.4 s in a run.
- A Steam Vent lifts 8 m in 1.6 s. (The vent code reaches 8 m in about 1.1 s with the default `push`. The briefs keep 1.6 s, which includes the entry, until the route bot gives real times.)
- The wait for a moving platform is half its period.

B1 is built, so its row has the bot's times; the other rows are estimates. Ascent has no par time. Each zone script also carries both routes, and each zone brief gives both times as targets for the split timer.

| Level | First-run route | Expert route | Par | Gold |
|---|---|---|---|---|
| B1 (route bot, 2026-11-21) | 34.2 s | 22.2 s | 51.3 s | 25.6 s |
| B2 | 32 s | 17 s | 48 s | 20 s |
| B3 | 49 s | 23 s | 74 s | 26 s |
| Ascent 1 (0 to 150 m) | 122 s | 67 s | | |
| Ascent 2 (150 to 300 m) | 112 s | 59 s | | |
| Ascent 3 (300 to 500 m) | 152 s | 73 s | | |

## Rules from the first built level

B1 (`b01.md`, "As built") found these rules. They hold for every level.

- **North is +y.** The camera looks along +y at the start, and the dawn, noon and dusk suns all stand ahead of the start and on its left. A wall or a ramp that faces the start is in shade.
- **A kerb stops a marble that rolls.** A marble that comes through the air goes over a 0.3 m kerb: off the top of a ramp, after a drop of 2 m, or after a bounce. Put a parapet of 1 m or more there, or a floor behind the kerb.
- **A piece that lies across an edge makes a step.** Give a beam or a ramp a level end that follows the edge.
- **The route bot slows for each turn:** to 6.9 m/s at 30° and to 3.5 m/s at 90° or more (`RouteBot._turn_speed`). A sharp turn costs about half a second. On B1, curve points 2 to 3 m apart made the bot miss a point and turn back. So a fast route has few points, long legs and few turns.
- **Leave 0.5 m between a route line and a kerb or a pillar.**
- **Kit pieces for an open floor** are in `kit/masonry.py`: `deck` (a floor of any outline), `dish`, `wall` (also a kerb), `arch`, `lathe` and `pillar` collide; `inlay`, `teeth`, `gear`, `hoop` and `ball` are decoration and do not. `kit/outlines.py` has `rect`, `box` and `arc` for the outlines.
