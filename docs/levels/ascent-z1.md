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
5. From the bell floor, take the two rafters to the crown.

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
