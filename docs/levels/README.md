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
| Moving platform | `period` 8 s for one cycle with the stops included, `stop` 1 s at each point of the path, `loop` false (there and back; true goes on from the last point to the first), `offset` 0 s (give a second deck on one loop `period` ÷ 2). Deck `width` 4 × `depth` 4 × `thickness` 0.5 m; its top face is at the marker and at each path point. Only `period` sets the speed: each leg eases out and in, so its top speed is π/2 × its average speed | A straight leg cannot go round a building, so a loop round a tower needs a stop at each corner (B3). The briefs set the path, period and stop of each platform |
| Pendulum | `period` 4 s, `swing` 60° to each side, `length` 4 m, bob `radius` 0.6 m, `offset` 0 s | The bob sweeps the track when the pivot is about `length` + `radius` above it |
| Turning gear | `period` 8 s for one turn, `radius` 2.1 m to the tooth tips, `teeth` 12, `thickness` 0.5 m, `clockwise` false. The top face is at the marker | B3's stair gears turn once in 10 s, every second one clockwise |
| Turning arm | `period` 8 s for one turn, `clockwise` false, `height` 0.25 m, `finish` brass (a kit material). The marker's points give the bar's outline in the marker's plane; the bar stands `height` up from it | Ascent 2's clock hands: 20 s, clockwise, blued steel, 0.05 m above the dial |

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

B1, B2, B3 and Ascent 1 are built, so their rows have the bot's times; the other rows are estimates. The estimate for Ascent 1 was 122 s and 67 s. Ascent has no par time. Each zone script also carries both routes, and each zone brief gives both times as targets for the split timer.

| Level | First-run route | Expert route | Par | Gold |
|---|---|---|---|---|
| B1 (route bot, 2026-11-21) | 34.2 s | 22.2 s | 51.3 s | 25.6 s |
| B2 (route bot, 2026-11-21) | 32.8 s | 24.2 s | 49.3 s | 27.9 s |
| B3 (route bot, 2026-11-21) | 62.4 s | 24.2 s | 93.6 s | 27.8 s |
| Ascent 1 (route bot, 2026-11-21) | 175.5 s | 104.0 s | | |
| Ascent 2 (150 to 300 m) | 112 s | 59 s | | |
| Ascent 3 (300 to 500 m) | 152 s | 73 s | | |

## Rules from B1 and B2

B1 and B2 (`b01.md` and `b02.md`, "As built") found these rules. They hold for every level.

- **North is +y.** The camera looks along +y at the start, and the dawn, noon and dusk suns all stand ahead of the start and on its left. A wall or a ramp that faces the start is in shade.
- **A kerb stops a marble that rolls.** A marble that comes through the air goes over a 0.3 m kerb: off the top of a ramp, after a drop of 2 m, or after a bounce. Put a parapet of 1 m or more there, or a floor behind the kerb.
- **A piece that lies across an edge makes a step.** Give a beam or a ramp a level end that follows the edge.
- **The route bot slows for each turn:** to 6.9 m/s at 30° and to 3.5 m/s at 90° or more (`RouteBot._turn_speed`). A sharp turn costs about half a second. On B1, curve points 2 to 3 m apart made the bot miss a point and turn back. So a fast route has few points, long legs and few turns.
- **Leave 0.5 m between a route line and a kerb or a pillar.**
- **Kit pieces for an open floor** are in `kit/masonry.py`: `deck` (a floor of any outline), `dish`, `wall` (also a kerb), `arch`, `grille` (bars in a doorway that the marble cannot pass), `lathe` and `pillar` collide; `inlay`, `teeth`, `gear`, `hoop` and `ball` are decoration and do not. `kit/outlines.py` has `rect`, `box` and `arc` for the outlines. `deck(..., holes=..., through=True)` makes each hole a shaft through the block, for a trapdoor or a gap to fall through.
- **An open trapdoor hangs its own length below its hinge**, from the bottom of the panel. Leave that room under it, or give the marker a shorter `depth` and a thinner `thickness`.
- **A gate needs a wall.** A gap of 3 m or less is a jump, not a barrier. To make one way in, close the sides with a wall higher than any jump reaches: 1.5 m from the floor, 2.5 m from a step of 1 m next to it.
- **A checkpoint pad catches a marble within 0.95 m of its middle.** Put it in a passage 2.3 to 3 m wide, or put one pad on each line that players take.
- **Loose tiles and slow turns.** A tile breaks 0.5 s after its first touch, so a marble must cross a tile of `tile` m in less than that: about (`tile` + 0.5) ÷ 0.5 m/s. The route bot slows to 3.5 m/s in a sharp turn, so a turn on loose tiles needs tiles of 1 m.
- **The route bot reaches a point within 0.45 m.** After a sharp turn it swings up to 0.8 m off its line. Give a gem on a trapdoor a straight run-up of 2 m or more, or a `wait 0` stop before it, so that the bot does not turn back onto the open door. Put a jump through a floating gem on a straight line.

## Rules from Ascent 1

Ascent 1 (`ascent-z1.md`, "As built") found these rules for tall levels and for the route bot.

- **A Steam Vent throws the marble the way it enters.** Put the landing ahead of the vent, 2.5 to 3 m past the column at 3 m/s, and give the player room to line up before the vent. In the air the bot only steers and brakes, so a route enters each vent toward its landing.
- **The bot cannot climb a steep slope on a short leg.** Its push is in proportion to the speed that it wants, and near a point it wants little. On a slope over 25°, give it one long leg from the foot to the top.
- **A jump point is about 0.9 m before the next edge.** Steps of 1 m are 2.3 m deep with gaps of 0.3 m, and the jump legs have a speed of 2.5 to 3 m/s.
- **Two pieces that the marble rolls across meet flush.** A step of 0.12 m stopped the marble at the end of a beam. Moving decks stop flush with their floors, and the gap beside a moving deck is 0.2 m or less.
- **A route has at most 100 points** (`kit.marker`). On a spiral ramp 2 m wide, points 72° apart at 4.75 m from the middle keep each leg clear of the inner kerb.
- **A lift gear needs a casing.** `town.lift()` carries the marble from the bottom of the gear to its top and lets it off sideways.
- **Give each indoor room a `room_probe`.** Without it, a room has the cold ambient light of the sky. The marker is the middle of the room's floor, with the room's inside size; its probe reaches 0.45 m into the walls, so keep the walls thicker than that.
- **Put land round a town.** A `land` marker just under the town's ground gives open country out to the haze. The land holds the marble, and its touch puts the marble out of bounds, so close the town's edge with houses: a marble on the ground must not roll out by accident. Far scenery (houses past the play space) is one mesh named `<name>-far`: no collision, no lightmap and no probe.
- **Town finishes.** Walls take `wall` (coursed ashlar), frames and bands `dressed` (no joints), roofs `slate`. `town.Finish` lists every finish; each is a material in `game/materials/`.

## Rules from B3

B3 (`b03.md`, "As built") found these rules.

- **A wall that faces the start puts the start in shade.** The dawn sun is 12° high, so a wall 5 m high throws a shadow 23 m long. Where a wall must stand across the way, give it arches with grilles: the sun and the view pass through, the marble does not.
- **A moving platform goes straight from stop to stop.** A loop round a tower needs a stop at each corner, and the deck sweeps half its width, and more at its corners, on each side of the line between stops.
- **A spring lands the marble with a bounce.** After a drop of 4 m the marble bounces about 1 m high and settles about 4 m further on. Put a gem 4 m past the landing, or on the arc itself.
- **The bot only steers and brakes in the air.** Its speed at a `use` point sets the length of the arc: about 5 m/s from the court onto a balcony, 12 m/s for a long arc. The point after a `use` must be past the landing, or the bot turns back on the balcony and rolls off its edge.
- **A rolling marble goes over a parapet when it falls 6 m.** A marble that leaves a carriage fast clears the court's 1.2 m parapet 6 m below and lands in the court.
