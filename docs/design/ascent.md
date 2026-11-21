# Ascent mode design

Status: built in #27. It follows `docs/plan.md` §2.9. Where this file and the plan differ, the plan wins.

Terms used in this file:

- **Climb:** one play of Ascent, from the climb start to the gate. A climb can have many sessions.
- **Zone:** one part of the climb. Each zone is a level script of its own.
- **Climb start:** the start pad of the first zone. Heights are in metres above it.
- **Gate:** the "to be continued" gate. It stands on the finish pad of the last built zone.
- **Spot:** the saved place of a climb that is not finished.
- **Fall:** a drop of more than 3 m below the floor that the marble was on.

## 1. Files

| Path | What it is |
|---|---|
| `game/modes/ascent/ascent.gd` | `Ascent`: the mode. `Ascent.start()` builds the climb and plays it; one `Ascent` node is in the run. |
| `game/modes/ascent/ascent_falls.gd` | `AscentFalls`: counts the falls and the metres fallen. |
| `game/modes/ascent/ascent_sky.gd`, `ascent_sky.gdshader` | `AscentSky`: the sun and the sky of the climb, set by the height. The shader blends the panoramas of two sky presets. |
| `game/modes/ascent/ascent_flag.gd` | `AscentFlag`: the flag at the best height. |
| `game/modes/ascent/ascent_gate.gd` | `AscentGate`: the gate. |
| `game/ui/hud/height_meter.gd`, `game/ui/widgets/height_scale.gd` | The height meter of the HUD. |
| `game/ui/screens/ascent_screen.gd` | The Ascent menu: Continue, New climb, Assist. |
| `game/ui/screens/ascent_stats_screen.gd` | The stats screen at the gate. |
| `levels/test/ascent_fixture_<n>.py` | Three fixture zones, 12 m each, for the tests. |

## 2. How a zone plugs in

A zone is a level like any other: `levels/ascent/zone_<n>.py`, built to `zone_<n>.glb`. `Ascent.ZONES` lists the zone ids from the bottom. The game climbs the built zones from the bottom up to the first one that is not built (`Ascent.zones()`), so the climb works while only some zones exist. A zone above a gap waits for the zone below it. While none is built, New climb in the Ascent menu is off. The game never climbs the fixture zones: its save is of its own zones.

Rules for a zone script:

1. **Coordinates.** Use the coordinates of the climb, not of the zone. Zone 2 has its floors at 150 m to 300 m. The mode loads every zone at the origin and does not move it.
2. **Start pad.** Put the `start` marker on a floor of the zone itself. It is the zone start: the marble is in the zone from the height of this pad up, and Assist puts its checkpoint here. In zone 1 it is the climb start.
3. **Finish pad.** Put the `finish` marker at the top of the zone, on a floor of the zone. The zone above starts beside it, on its own floor, flush with this one. Do not build the same floor in two zones.
4. **Routes.** Carry a `first_run` route and an `expert` route from the start pad to the finish pad, as every level does. `just test-levels zone_<n>` drives them on the zone alone.
5. **Par and gold.** Ascent has no par time, but `just test-levels` compares each route with the level's `par` and `gold`. Set them with `just suggest-times zone_<n>`.
6. **No carried power-ups** (plan §2.9). The HUD of a climb has no power-up slot.
7. **Light.** Do not rely on the zone's own sun or sky. In the climb, the mode removes each zone's `WorldEnvironment`, `DirectionalLight3D`, `LightmapGI` and `ReflectionProbe` nodes: the light changes with the height, and a probe that looks once would keep the light of the start. The sky lights the reflections.

What the mode does with the zones:

- It removes every checkpoint of a zone: the climb has no checkpoints but those of Assist.
- It removes every finish pad but the last. So the marble rolls from the top floor of a zone onto the start floor of the next zone. The last finish pad gets the gate and ends the run.
- It gives every mesh a visibility range: `Ascent.FAR` (300 m) from the nearest side of the mesh, with a fade over the last 40 m. A zone must be made of many meshes for this to help. One mesh for a whole tower is drawn as a whole.
- A zone that has no scene, or no start pad, is left out with a warning.

Object names must be different in every zone only when a bot drives the whole climb: a `wait_until <object>` action finds the first object of that name in the run.

## 3. What the mode does in a climb

**Height.** `GameState.height` is the marble's height above the climb start, along the up of the climb start. The mode writes it each tick. `Ascent.zone_heights` has the height of each zone start, and `Ascent.top` the height of the gate.

**Zones and music.** The marble enters a zone 0.5 m below its start and leaves it 3 m below. On a change, the mode calls `Music.set_zone(zone)` and emits `Ascent.zone_changed`.

**Falls** (`AscentFalls`). The stats are `falls` and `fallen` (total metres).

| Number | Value | Why |
|---|---|---|
| `FALL_HEIGHT` | 3 m | A jump is 1.4 m high, and the highest step that a level asks for is 1.3 m. So a normal move is never a fall. |
| `FLOOR_MEMORY` | 2 s | On lower ground, the marble forgets the old floor after this time. So a slow way down is not a fall. |
| `SETTLE` | 0.25 s | A fall ends when the marble stays on the ground this long and gets no lower. So bounces and slides are part of one fall. |
| `TELEPORT` | 3 m in one tick | A larger move is a teleport (a respawn, a continued climb, the harness). It is not a fall, and it ends a fall in progress. |

- The floor is the highest height at which the marble stood on a floor. A floor is a contact whose normal is within 60° of up.
- A fall starts when the marble is more than `FALL_HEIGHT` below the floor. `fallen` grows by the way from the floor to the lowest point of the fall.
- A fast slide down a slope is a fall too.
- The spot keeps the floor and the lowest point, so a fall with a quit in it is still one fall.

**Best height and flag.** The best height is the highest floor of the level geometry that the marble stood on, in any climb. The floor of an object (a lift, a trapdoor) does not count, because it can move away. `AscentFlag` stands at that place. It moves only when a fall starts, so it is never under a marble that climbs past its best. A best height below 3 m has no flag.

**Assist.** `Save.ascent.assist` is the switch. It is in the Ascent menu and counts from the next start of the climb. With Assist:

- the climb has a `Checkpoint` on the start pad of each zone (`assist_1`, `assist_2`, ...);
- a fall of `ASSIST_DROP` (10 m) below the last checkpoint puts the marble back on it, through the out-of-bounds rule of `Rules`;
- `Save.ascent.assisted` marks the climb. The mark stays when the player turns Assist off again. The stats screen shows it.
- An assisted climb never replaces a record (Sean, 2026-11-21): it writes no best time, no ghost and no best height. The mode sets `LevelRun.keeps_records` to false, and `RunTracker` then saves no finish. The stats screen still shows the time of the climb, with the best time as it was.

**The spot.** `Ascent.save_spot()` writes the place, the velocity, the clock, the run's tick, the height, the zone ids of the climb, the last Assist checkpoint, the state of the fall counter, the falls, the metres fallen and the best height to `Save.ascent`. It also keeps the ghost recording of the climb so far under the ghost id `ascent_climb`. It runs:

- when the game pauses, so a crash in the pause menu loses nothing;
- when the run leaves the tree (Save and quit, a new level, the end of the game);
- when the player closes the window.

The next `Ascent.start()` continues the spot with `LevelRun.resume()`. The run starts at the saved tick, so every mover has the pose that it had. The clock runs on, and the last Assist checkpoint is the one that the marble reached. The spot counts only in a climb that starts with the zones of the spot: more zones on top are fine, and a climb of other zones starts at the bottom (`Ascent.has_spot()`; the Ascent menu shows Continue by the same rule). While the marble waits for a respawn, the spot is the place of that respawn. Objects with a state of their own (a trapdoor, crumbling tiles) start again in their first state.

**The gate.** The last finish pad ends the run. The mode removes the spot. `RunTracker` saves the time and the ghost with `Save.finish()` under the level id of the climb, as for any level. The ghost of the best climb plays in the next climb when `Settings.ghost` is on.

**Records.** The level id of a climb is `Ascent.record_id(ids)`: `ascent:` and the zone ids with a `+` between them, for example `ascent:zone_1+zone_2+zone_3`. `GameState.level` reports it, and the best time and the ghost are kept under it. So each set of zones has a record of its own: a best time from a build with fewer zones never stands for the full climb. The tier and the music group of every climb are `ascent`.

**Eggs.** The save keeps the found eggs of a level as a set of egg ids (`LevelRecord.eggs`); the id of an egg is its node name, which is its marker name in the level script. A level has every egg found when each of its egg ids is in the set, so an egg that gets a new name must be found again. An egg of a climb saves under the id of its zone (`zone_3`), not of the climb, so it stays found when the climb gets more zones, and it is the same egg when the zone is played alone. Give each egg of a zone its own marker name. After a continue, an egg is closed again; to find it again changes nothing.

**Restart.** A climb is not restartable (`LevelRun.restartable` is false): the `restart` action does nothing, so one press cannot lose a long climb. New climb in the Ascent menu starts at the bottom. `LevelRun.restart()` itself (the route bot, the harness) starts a new climb with new stats.

## 4. Light

`AscentSky` has one sun and one sky. They come from the tier skies of the look baseline (`game/skies/*.tres`, `SkyPreset`): `dawn.tres` at the climb start and `noon.tres` at `NOON_HEIGHT` (500 m, the top of zone 3). Zones 1 to 3 are on the Earth only. M2 adds the skies of the higher zones (sunset, the stars).

| Value | Dawn, 0 m | Noon, 500 m |
|---|---|---|
| Sun elevation | 12° | 58° |
| Sun energy | 2.27 | 1.35 |
| Sky energy | 0.297 | 0.177 |
| Haze density | 0.001 /m | 0.0005 /m |

- The environment and the sun are those that `SkyPreset.environment()` and `sun()` make for dawn. So the tonemap, the glow and the haze are as in a level.
- `show_height()` gives `_apply()` a weight: the height over `NOON_HEIGHT`, from 0 to 1. `_apply()` is the one place that blends the values of the two presets: the panoramas (in `ascent_sky.gdshader`), the sun's elevation, turn, colour and energy, the fill light, the exposure and the haze. To change the light, change the presets.
- The light changes in steps of 1 m of height, because each change makes Godot draw the light of the sky again. The step that reaches dawn or noon is never left out, and outside the two ends nothing changes.
- `GraphicsPreset` says that SDFGI comes with the Ascent mode (Ultra only). It is not built yet.

## 5. HUD and menus

- **Title.** Ascent opens the Ascent menu.
- **Ascent menu** (`Game.screen` `ascent`). Continue (only with a spot), New climb (off while no zone is built), and the Assist switch. Above them: the saved climb, the best height and the best time, each only when it exists.
- **HUD.** A climb shows the clock and the height meter: the height in whole metres over a scale with a tick at each zone start, a ring for the gate, a gold pennant at the best height and the accent ring at the marble. It has no gems, no target times and no power-up slot.
- **Pause.** Resume, Settings, Save and quit. Save and quit opens the Ascent menu.
- **Stats** (`Game.screen` `ascent_stats`). Time, new record or best time, height, falls, metres fallen and the Assist mark. Done opens the Ascent menu.

## 6. Harness

`load_mode {mode: "ascent", zone?, zones?, resume?, assist?}` starts a climb and returns the state (`tools/harness/README.md`). The MCP tool is `game_load_mode`. Until the first zone is built, the harness climbs the fixture zones. `LevelRun.teleported` lets the mode write the height after a teleport, so the state is whole with no step.

## 7. Tests

- `game/test/modes/ascent/` drives the fixture climb through `MarbleInput` and `LevelRun.teleport()`, and reads `GameState`, the `Ascent` node and the save. `AscentTest` (`game/test/support/ascent_test.gd`) is the base.
- `test_route_bot_climbs_to_the_gate` lets the route bot play the first-run route of each zone in turn, from the climb start through the gate.
- `game/test/ui/test_ascent_screens.gd` drives the menus with the pad.
- `just test-levels ascent_fixture_1 ascent_fixture_2 ascent_fixture_3` drives both routes of each fixture zone.
- `just ui-shots` saves the Ascent menu, the HUD of a climb, its pause menu and the stats screen.

## 8. Open points

1. **Eggs in the menus.** The save keeps every egg of every zone, but no screen of Ascent shows them yet (the Ascent menu or the stats screen can count them: 10 in all).
2. **Whole-climb bot.** The harness `run_bot` drives only the route of the first zone. A test can chain the zone routes, as `test_route_bot_climbs_to_the_gate` does. For this, the last point of a zone route must be a stop, or the top floor must be long enough to stop on.
3. **SDFGI.** Ascent has no SDFGI on Ultra yet (plan §4.7).
4. **Two sun glows.** Each sky panorama holds the glow of its own sun. Between dawn and noon the sky shows both glows, each weaker, and the sun light comes from between them. One sun that moves needs panoramas with no glow and a sun that the sky shader draws.
5. **Failed saves.** A save that cannot be written gives a warning in the log only, as everywhere in the game. The ghost recording of the climb and the spot are two files; after a crash between the two writes the recording can be a few seconds ahead of the spot.
6. **Streaming.** All zones load at the start. Add zone streaming only if the memory or performance checks fail (plan §2.9).
