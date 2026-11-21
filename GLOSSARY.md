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
