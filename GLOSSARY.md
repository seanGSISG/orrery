# Orrery

An original 3D marble platformer in Godot. These terms name the parts of the game runtime; `docs/design/core-runtime.md` has the full design.

## Language

**Tick**:
One physics step of the game, 1/120 s. One `LevelRun.step()` call advances one tick.
_Avoid_: frame (a frame is one rendered image)

**Sub-step**:
One part of a tick in the marble solver. The marble moves at most half its radius in one sub-step.

**MarbleInput**:
The value that the marble reads each tick: move direction, jump, use, camera yaw and pitch. The player, the route bot and the harness all make it.
_Avoid_: controls, input state

**InputSource**:
One producer of `MarbleInput`, for example the player's keyboard. The `InputHub` autoload holds the one active source.

**LevelRun**:
The node that plays one level and owns its time: the marble, the objects, the rules and the `GameState`.
_Avoid_: session, game

**GameState**:
The one observable snapshot of the game. Tests and the harness read it; nothing else is the test boundary.
_Avoid_: status, telemetry

**Solid**:
A collider that the marble can touch: level geometry or the solid part of an object. A mover moves it from code with `Solid.move()`.
_Avoid_: collider, body

**LevelObject**:
An object that a level marker places, such as a gem or a moving platform. It is a scene whose root script extends `LevelObject`, and the run calls its hooks.
_Avoid_: entity, prop

**Level script**:
The Python file `levels/<tier>/<id>.py` that builds one level with the kit (`kit/`). It is the source of truth; `just build-levels` turns it into `game/levels/built/<id>.glb`.
_Avoid_: map, level file

**Marker**:
A Blender empty that a level script places with `kit.marker(type, ...)`. Its custom property `orrery` holds the type and the settings. The importer puts an instance of `game/objects/<type>/<type>.tscn` in its place.
_Avoid_: spawn point, placeholder

**Route**:
A `route` marker: the points and actions that the route bot (`game/harness/route_bot.gd`) plays a level along. A level script places a `first_run` route and an `expert` route; `just test-levels` checks them against par and gold.
_Avoid_: path, track (a track is a level piece)

**Route bot**:
The program that plays a level along its routes with the same `MarbleInput` as a player. `just test-levels` and the harness `run_bot` command use it.
_Avoid_: AI, autoplay

**First-run route**:
The `route` of kind `first_run`: the line of a player who plays the level for the first time. The route bot must finish it under par.
_Avoid_: normal route, safe route

**Expert route**:
The `route` of kind `expert`: the fastest line, with shortcuts and skips. The route bot must finish it under gold.
_Avoid_: speedrun route, fast route

## Scoring and progress

**Par**:
The time to beat to qualify on a level and unlock the next one. It starts as the first-run route time × 1.5.
_Avoid_: target time, qualifying time

**Gold time**:
The harder time that earns the gold medal. It starts as the expert route time × 1.15.
_Avoid_: best time (a best time is the player's own record)

**Medal**:
The result of a finish: `none`, `qualified` (at or under par) or `gold` (at or under the gold time).
_Avoid_: rank, rating

**Rules**:
The level rules of one run: gems, the clock, the finish, checkpoints, out of bounds and the respawn.
_Avoid_: game logic, scoring

**Checkpoint**:
An object that sets where the marble comes back after it falls out of the level. Without one, the marble comes back on the start pad.
_Avoid_: save point, respawn point

**Power-up slot**:
The one place that holds a power-up. A pickup fills it when it is empty, and the use button empties it.
_Avoid_: inventory

**Feedback**:
An event that a `LevelObject` or the marble emits for sound and rumble. Its kind is named `<type>.<event>`, for example `bumper.hit`.
_Avoid_: signal event, effect

## Saves and ghosts

**Save**:
The autoload that keeps progress, best times, settings, the Ascent climb and ghosts in `user://`.
_Avoid_: profile, persistence

**Ghost**:
The recording of one run: the marble's position and rotation 30 times a second. The game plays the best ghost of a level back as a translucent marble. It does not re-simulate.
_Avoid_: replay, shadow

**RunTracker**:
The helper that `Save` adds to each run. It records the ghost, races the best ghost, and saves the egg and the finish.
_Avoid_: recorder, stats tracker

## Audio

**Music group**:
A folder of music tracks that play together, for example `beginner` or `ascent`. A level plays the group in its `music` field, or the group of its tier.
_Avoid_: playlist, soundtrack

## Tools

**Harness**:
The debug-only automation interface of the game. An agent or a test uses it to load a level, give input, step ticks and take screenshots.
_Avoid_: test server, remote control

**Shot**:
A named camera view that a level script places with `kit.shot()`. The screenshot gallery and the harness `screenshot` command render it.
_Avoid_: camera marker, viewpoint

**Feel course**:
The test level that is built for the feel review of the marble, the camera and the input. `just feel` plays it.
_Avoid_: test track, playground

**Tuning overlay**:
The on-screen panel of the feel course. It changes the marble, camera and input values while the game runs, and saves them into their default files.
_Avoid_: debug menu, cheat menu

**Lightmap bake**:
The GPU job that makes the baked lighting of one level. `just bake <id>` runs it, and the result is kept in Git LFS.
_Avoid_: light build, GI build
