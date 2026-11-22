# Ascent 1: Clockmaker's Square

Map: `ascent-z1.svg`. Ticket: #31. Shared numbers and rules: `README.md`. Heights: 0 to 150 m.

## Intent

The climb starts in a town square on Earth at dawn and goes up the full height of the clock tower. The zone teaches how Ascent works: there are several ways up, a fall costs height and not the run, and floors are places to rest. The square is open ground. The player can walk round it and look at both routes before the first jump. The tower has five floors, and every floor is a full rest ledge with a way up inside the tower and a way up outside it.

## Layout

The square is 34 × 32 m. The clock tower is 12 m wide. It is whole to +130 m and broken above that.

| Section | Heights | First way | Second way | Ends at |
|---|---|---|---|---|
| 1. Town | 0 to +26 m | **Market side (west):** three stall roofs, bakery roof (+4), chimney vent, guildhall roof (30° slope to +14), ridge vent, builder's hoist (period 12 s) | **Workshop side (east):** two crates, balcony (+3), waterwheel gear to the workshop roof (+9), second gear, loose planks, three ramps in the tower base | Gallery, +26 m |
| 2. Weight shaft | +26 to +50 m | **Inside:** spiral ramp, five half-turns of 17 m at 16°, two pendulums | **Outside east:** scaffold steps, vent, deck (+37), steps, vent, deck (+47), two bumpers | Gear room, +50 m |
| 3. Gear room | +50 to +80 m | **Inside:** three flat gears, two lift gears 7.2 m across (one turn in 16 s), two ramps | **Outside west:** three vents with ledges at +58, +66 and +74 m, five steps | Clock floor, +80 m |
| 4. Clock floor | +80 to +110 m | **Inside:** three bell weights, each a 3 m platform that rises 10 m (period 12 s), with a ledge between them | **Outside east:** loose-slate slope (31°), vent, ledge (+94), loose-slate slope, vent, ledge (+107), two steps, one bumper | Belfry, +110 m |
| 5. Belfry and crown | +110 to +150 m | **Inside:** spiral ramp round the great bell to the bell floor (+130). Then five stair fragments, a vent, and the bell cradle, a lift from +143 to +150 m (period 12 s) | **Outside west:** a second hoist from +110 to +130 m (period 16 s). No hazard | Crown, +150 m |

Also in the weight shaft: the clock's counterweight, a 2.4 m platform that moves in the middle of the shaft between +31 and +47 m, period 8 s. Also above the bell floor: two rafters, narrow beams 0.8 m wide and 21 m long at 25° and 29°, from the bell floor out over the east side and back to the crown.

## Routes

**First run (white).** Market side and the hoist. Then the inside of the tower all the way: spiral ramp, lift gears, bell weights, the ramp round the great bell, the stair fragments and the bell cradle. Every fall inside the tower ends on the floor below.

**Expert (dashed).**

1. From the top of the ridge vent, steer onto the low end of the crane beam (0.8 m wide, 21 m long, 16°). This skips the hoist.
2. In the weight shaft, climb one half-turn, jump the 2 m gap onto the counterweight and ride it to +47 m.
3. Leave the gear room by the west door and weave through the three vents without a landing.
4. Leave the clock floor by the east door and take both loose slopes at full speed.
5. Climb the ramp round the great bell, as on a first run. From the bell floor, take the two rafters to the crown.

## Gems

Ascent has no gems.

## Clockwork Egg (1 of 10)

The guildhall ridge has two chimneys. One steams: it is the vent. The other is dry. A marble that drops into the dry chimney falls 13 m into the hearth room of the guildhall, where the egg sits. A door leads back to the square. The egg costs the whole climb to the ridge, which is what makes it an Ascent secret.

## Hazards and objects

10 Steam Vents, 3 pendulums (two in the shaft, the great bell), 3 bumpers, 7 turning gears (2 in the town, 3 flat, 2 lift gears), 7 moving platforms (2 hoists, counterweight, 3 bell weights, bell cradle), 3 strips of Crumbling Tiles (planks, two slate slopes), 3 narrow beams, 1 egg. No carried power-ups.

## Falls and rest ledges

| Fall from | Lands on | Height lost |
|---|---|---|
| Stalls, bakery or guildhall roof | The square | 1 to 14 m |
| Hoist or crane beam | Bakery roof or the square | 15 to 27 m |
| Inside the tower, any section | The floor below | 5 to 30 m |
| East scaffold | Workshop roof (+9 m) or the square | 18 to 47 m |
| West vents of the gear room | Guildhall roof (+14 m) | 36 to 66 m |
| East slopes of the clock floor | Scaffold deck (+47 m) | 33 to 60 m |
| Rafters | East ledge at +94 m | 36 to 45 m |
| Stair fragments of the crown | Bell floor (+130 m). West of the tower wall: the gear-room ledges or the guildhall roof | 1 to 121 m |

The inside way is always the safe way. The outside way is always faster and always costs more to miss. Rest ledges: bakery roof, guildhall ridge, workshop roof, and the five floors of the tower. No checkpoints. With Assist, one checkpoint on the start pad.

## Time targets

Ascent has no par time. The level script carries the first-run route and the expert route, and the bot times both.

| Section | First run | Arithmetic | Expert | Arithmetic |
|---|---|---|---|---|
| 1. Town | 22.2 s | stalls 4.4 + vents and roof 5.3 + hoist wait 6 and ride 6 + 0.5 | 12.6 s | 4.4 + 5.3 + beam 2.4 + 0.5 |
| 2. Weight shaft | 14.1 s | 85 m ÷ 7 + 2 pendulums × 1 | 10.8 s | 17 m ÷ 7 + wait 2 + ride 4 + 17 m ÷ 7 |
| 3. Gear room | 22.9 s | gears 3.7 + two rides of 8 + ledge 0.5 + ramps 23 m ÷ 8.5 | 10.3 s | three lifts 4.8 + five steps 4.5 + 1 |
| 4. Clock floor | 26.9 s | 3 × (wait 3.5 + ride 5) + 1.4 | 11.3 s | slopes 22 m ÷ 8 + two lifts 3.2 + ledges 2.5 + steps 1.8 + 1 |
| 5. Belfry and crown | 29.6 s | ramp 68 m ÷ 7 + bell 2 + steps 4.5 + vent 1.6 + cradle wait 5 and ride 5 + 1.8 | 16.2 s | ramp 9.7 + bell 1 + rafters 43 m ÷ 8.5 + 0.5 |
| Four floor crossings | 6 s | 4 × 1.5 | 6 s | 4 × 1.5 |
| **Zone** | **122 s** | | **67 s** | |

## Why it is fun

- The player picks a side of the square, and picks again on every floor of the tower.
- The first falls are short and land in the square, next to the other route.
- Each floor has its own machine: pendulums, lift gears, bell weights, the great bell. The tower never repeats a section.
- Every outside way is in plain view from the floor door. It tempts the player on every climb.
- The bell cradle is slow on purpose. It lifts the player out of the broken tower with the floating pieces of zone 2 in view.

## As built

Level script: `levels/ascent/zone_1.py`. Town kit: `kit/town.py`. The script follows the map and the plan inset, with the differences below. The map is a side view, so the script takes the north–south places from the inset. The tower stands north of the square, 12 m square, with its middle at (0, 39); x is east and y is north.

| Difference | Reason |
|---|---|
| The start pad is 9.5 m south of the tower wall, not 2.6 m | The camera looks north at the start. Close to the wall, the first view was the wall. Now it shows the square, the tower base and the two sides |
| The circle in the middle of the inset is a fountain | It has no vent symbol, and a square needs a middle |
| The bakery vent throws the marble north onto the south end of the guildhall roof, not west onto the eave | On the inset the guildhall stands north of the bakery. A vent throws the marble the way it enters |
| A brass gutter runs along the guildhall eave | A marble that landed near the eave rolled back down and off |
| The north part of the guildhall is a flat terrace at +14 m with a parapet. The ridge vent stands on it, and the hoist and the crane leave from it | The vent throws the marble the way it enters, so a player needs room to line up with the hoist or with the beam. The 2.8 m ridge walk gave no room |
| The crane beam is 17.5° and 17 m, with a level heel at its low end, and it ends flush with the gallery landing (map: 16°, 21 m) | The heel must be 3 m past the vent, where the marble is at the top of its throw, and the beam must end flush with the landing: a step of 0.12 m stopped the marble |
| The hoist runs from above the terrace (+19.8 m) to the gallery landing (+26 m) and stops flush with it (map: +19.5 to +27 m) | The marble rolls straight off the deck onto the landing |
| The crates and the balcony are on the south face of the workshop | The waterwheel stands at the workshop's south-east corner |
| Every lift gear (the waterwheel, the second gear and the two lift gears of the gear room) carries the marble from its bottom to its top inside a brass casing and two side rings, and lets it off sideways through a window in one ring | In a prototype, a marble that rode a notch over the top fell out too late to reach any floor beyond the gear. The casing also lets the marble board at the bottom, so a gear 7.2 m across lifts 7.2 m |
| The second gear stands north of the workshop and lets the marble off west at +13.9 m onto a ledge, the loose planks and the tower's east door. The tower base top is +13.9 m (map: +14) | The gear's exit sets the height |
| The tower base climb is a spiral ramp of 2.5 half turns, not three straight ramps | At 12 m wide, three straight ramps of 4 m rise are steeper than 20° and leave no room for landings |
| The weight shaft ramp is 5 half turns of 13.5 m at 19.6° (map: 17 m at 16°) | A ramp 2 m wide fits round a 12 m tower only at 4.3 m from its middle |
| Each spiral ramp has a brass kerb on both edges. The shaft ramp's inner kerb has a gap where the expert jumps to the counterweight | The kerbs stop a fall into the middle of the tower or into its corners. Without the gap, the jump clipped the kerb |
| The counterweight runs from +30.6 m to +47 m | A landing 0.2 m below the take-off lets a run-up of 0.9 m reach it |
| The pendulums swing along the ramp, not across it | Across the ramp, the bob would go through the tower wall |
| The east scaffold: steps +27 to +30 m east, a vent to a deck at +37 m beyond the steps, steps +38 to +40 m west, and a vent to the gear room's east balcony at +50 m. No deck at +47 m and no steps at +48 and +49 m | The tower wall leaves no room for two more steps between the second vent and the door. The two bumpers stand on the +37 m deck and on the +50 m balcony |
| The scaffold hangs from the tower on iron stays | Posts from the ground made a cage in front of the start |
| Gear room: three flat gears along the south wall (+51, +52, +53 m), lift gear 1 by the west wall, lift gear 2 across the room, and two spiral ramps of 225° with a level landing between them | Lift gear 1 lets the marble off straight into the lane of lift gear 2. The two ramps climb the 12.3 m that are left |
| The three west vents stand in one line west from the west door, each at the near end of its ledge (+58, +66, +74 m). Five steps lead back east to the clock floor's west balcony | A marble that keeps its speed crosses all three steam columns without a landing: the expert's weave. A marble that slows down lands on a ledge |
| Steps and stair fragments have gaps of 0.3 m | A gap narrower than the marble cannot drop it. Wider gaps dropped the route bot after a short jump |
| The clock floor's east way goes from the second slate slope through a vent onto a ledge at +107 m north of the tower, two steps and a bridge into the belfry's north door | A door in the east wall would be in the way of the belfry ramp's first turn |
| The great bell hangs still. Its clapper is the third pendulum: it swings along the belfry ramp | The pendulum object has a ball for a bob, so the bell itself cannot swing |
| The crown vent stands on a platform at +135 m and throws the marble south onto the fragment at +143 m. The bell cradle rises beside it to the crown | The cradle must arrive flush with the crown's edge |
| The rafters are 19 m at 25.3° and 19.6 m at 29.3°, and meet on a round brass cap 3.2 m across | Two beams that meet in a point make the marble turn 170° on a beam 0.8 m wide |
| The crown is a slab 14 × 10 m at +150 m on top of the east wall, with a merlon at each corner. The finish is in its middle | Zone 2 starts beside it, on its own floor |

Decoration that the map does not show: a town round the square (about 70 houses in streets of one mesh each, out to 56 m from the square), street lamps, shop signs, a plinth, a cornice at each floor, quoins at the corners, glazed windows, the great door of the tower base, a dial on each face of the clock floor (no numerals, six o'clock), and louvres in the belfry. The windows, the dials, the signs, the stays and the tower's dress do not collide.

The look follows a concept board of the square at dawn (GPT-Image, not in the game). Every face has a `town.Finish`, a material in `game/materials/`:

- Walls are `wall`: the limestone of the deck, cut in courses of ashlar 0.95 × 0.42 m (`wall_size` of `kit_surface.gdshader`). Frames, sills, lintels, string courses and cornices are `dressed` limestone with no joints.
- Roofs are `slate` (CC0); `slate_turned` turns the courses for a ridge along y. Doors, shutters, timber and stall canvas are CC0 texture sets too (`docs/licenses.md`). Iron is black paint (metallic 0).
- A window has a stone frame 0.12 m wide and deep, a sill and a lintel. In the frame, 0.09 m back, near-white glass (`glass.gdshader`) shows a dark room behind it, under a cross of painted sash bars. About one storey in three has open shutters.
- A house (`town.house()`) has a string course at each storey and a cornice under the eaves, a chimney stack with two pots, and an iron ridge.
- The fountain is 4 m across: a low stone basin of still water, with the trial fountain raised in its middle as the upper tier.
- Moving decks are timber (`finish="wood"` of `moving_platform`).

Past the town: a `land` marker (`game/objects/land/`) gives 12 km of flat country just under the town's ground: grass at its true size, then fields of several crops with hedges between them, faded by the sky's distance fog into the horizon. A far town of plain houses (`town.house(plain=True)`) stands round the ground out to a ragged edge 150 to 260 m from the square: one mesh, `far_town-far`, with no collision, no lightmap and no probe.

### Routes and times

The route bot drives both routes (`just test-levels zone_1`, 2026-11-21): first run **175.5 s**, expert **104.0 s**. Par 263.2 s and gold 119.7 s come from `just suggest-times zone_1`. Ascent has no par time; the two values only let `just test-levels` check the routes. The bot is slower than the estimates (122 s and 67 s): it slows to 3.5 m/s at each sharp turn, it waits for each mover's window, and it climbs the spiral ramps on legs of 72°, because a route has at most 100 points (`kit.marker`).

The other ways up were driven with routes that were not kept: the workshop side with the base ramp, the east scaffold, and the west hoist of the belfry. The expert route drives the crane beam, the counterweight, the west vents, the slate slopes and the rafters. The route bot also climbed the zone in the Ascent mode (`load_mode ascent`) to the gate at 150 m.

### Light

The zone has no lightmap bake: in the climb, the mode removes each zone's lightmap (`docs/design/ascent.md` §2). Played alone, the zone has the `ground_dawn` sky (`kit.level(sky="ground_dawn")`). At dawn the guildhall and the west houses put much of the square in shade. A warm fill (`ground_dawn.tres`: `sky_share` 0.8, `fill_color` a warm stone colour) stands in for the light that sunlit walls throw into the shade, so the shade reads as dawn, not as a cold blue. It lights the zone played alone and the climb start alike.

Each room of the tower has a `room_probe` marker (`game/objects/room_probe/`): a warm ambient light and an interior probe, so the rooms look lit by lamps and warm stone, not by the cold sky. The climb keeps these probes.

The start view faces north into the shade of the tower and the square, and the sun (azimuth 135°) is ahead and to the left. Every level starts with the camera to the north (`MarbleInput.camera_yaw` 0), so a turned start camera would need a start heading in the core input for the player, the bot and the harness alike. Turned round, the zone would put the tower behind the start. The faces that the start looks at stay in shade; the warm fill and the sunlit west faces of the workshop side carry the view.

### Clockwork Egg as built

The dry chimney stands at the south end of the ridge walk (+14 m). Its flue, 1.3 m wide, goes down 15 m to the hearth of the guildhall's hall. The egg stands in front of the hearth. A door 2.4 m wide in the hall's east wall opens to the street beside the square.

### Props, decals and placeholders

The art of the zone-1 trial (#96; `assets/props/`, `assets/decals/`, `docs/licenses.md`) is in place. Every play surface is still kit geometry; a prop is decoration with a simple collider where the marble could otherwise roll through it.

| Prop | Instances | Where | Collider |
|---|---|---|---|
| `fountain` | 1 | The middle of the square, with still water in its basin (a glass disc that does not collide) | cylinder |
| `lamp_post` | 10 | Round the square, off the ways up | cylinder |
| `bread_cart` | 1 | South-east of the fountain | box |
| `barrels` | 4 | By the bakery door, by the workshop door, by the inn, by the waterwheel | cylinder |
| `flower_trough` | 7 | Beside the fountain, beside the tower's great door, in front of the south houses, by the guildhall door | box |

| Decal | Where |
|---|---|
| `dial_tower` | The four dials of the clock floor, 8.8 m across, under the brass hands at six o'clock |
| `dial_shop` | The workshop's west wall, beside the clockmaker's sign |
| `sign_bakery`, `sign_clockmaker` | Both faces of the hanging boards of the bakery and the clockmaker |
| `sign_guildhall` | Over the hall door of the guildhall |
| `sign_workshop` | The workshop's south wall, over the balcony |
| `plaque_square` | Over the great door of the tower |

`town.decal(name, art, at, yaw, size)` puts a picture of `assets/decals/` on an upright quad. Its alpha cuts the outline at 0.5 (glTF alpha mode MASK), and it does not collide.

The props and decals that wait for their art have a placeholder: an empty with the custom property `town_spot` = {kind, size, note}, from `town.spot()`. It shows nothing in the game. To put a model in, change its `town.spot("prop", name, at, rotation, ...)` line to `kit.prop(name, at=..., rotation=..., collider=...)` at the same place. No spot stands on a way up.

| Prop spot | Place (x, y, z) | Size (w × d × h, m) | To make |
|---|---|---|---|
| `prop_bench_1`, `prop_bench_2` | (−10.5, 30.8, 0), (10.5, 29.6, 0) | 1.8 × 0.6 × 0.9 | Benches with their backs to the tower |
| `prop_bench_3` | (−15.8, 26.0, 0) | 1.8 × 0.6 × 0.9 | Bench by the guildhall lane |
| `prop_goods_stall_2`, `prop_goods_stall_3` | (−12.5, 9.95, 0.95), (−16.0, 9.95, 0.95) | 2.6 × 0.6 × 0.5 | Bread and fruit on the stall counters |
| `prop_clock_parts` | (13.8, 22.5, 0) | 1.2 × 0.8 × 1.0 | A crate of clock parts by the workshop door |
| `prop_hay_cart` | (0.0, −5.0, 0) | 1.8 × 3.2 × 1.6 | Hay cart in the south street |
| `prop_anvil` | (25.0, 14.0, 0) | 0.8 × 0.5 × 0.8 | Anvil by the waterwheel |

| Decal spot | Where | Art to make |
|---|---|---|
| `decal_sign_inn` | The board of the inn's hanging sign, south side of the square | Sign art on both faces |
| `decal_street_name_south`, `decal_street_name_east` | The corner house of the south street, and the workshop's west wall | Street name plates |
