# Orrery harness client

This package launches a debug build of the game and drives it through the harness in `game/harness/harness.gd` (plan §4.5). It has two front-ends over one client (`client.py`) and one launcher (`game.py`):

- the CLI `orrery-harness` (`just harness …` from the repo root), and
- the MCP server `orrery-harness-mcp`, registered as `orrery` in `.mcp.json`.

## CLI

```sh
just harness launch --level flat --resolution 1280x720   # gamescope, no window
just harness input --move 0 1 --frames 90                # hold "forward" for 90 ticks
just harness step 150                                    # step 150 ticks, then pause
just harness screenshot --path build/harness/flat.png
just harness run_bot --route expert                      # the route bot plays a route
just harness quit
```

`launch` records the game in `build/harness/session.json`. Every other command, and the MCP server, talks to that game. Each command prints its result as JSON.

`quit` (and `game_quit`) fails with the shader path and the first error lines when the game's log shows a shader compile error. `--headless` compiles no shaders, so only a rendering display (`headless` gamescope or `window`) can show one. `check-log [PATH]` runs the same check on any log (stdin by default).

Each game starts with its own empty `user://` in a new `build/harness/user-<port>-<random>/` folder, so harness sessions and tests never read or write the player's saves, ghosts or settings, nor each other's. The folder goes when the game ends (the next `launch`, or `game_quit`), with any screenshot saved there without `--path`.

`--display` selects where the game renders:

| Display | What it does |
|---|---|
| `headless` (default) | `gamescope --backend headless` at the resolution. Real GPU frames, no window. Falls back to `window` |
| `window` | A desktop window at the resolution |
| `none` | `godot --headless`. Nothing renders, so `screenshot` fails. CI uses it |

## MCP tools

`game_launch {level, display, width, height}`, `game_load_mode {mode, zone, zones, resume, assist}`, `game_state`, `game_input {move, jump, use, camera, frames}`, `game_step {frames}`, `game_screenshot {shot}` (returns the image), `game_run_bot {route}`, `game_logs {since}`, `game_quit`. The other harness commands (`teleport`, `pause`, `set_time_scale` and so on) are in the CLI.

## Protocol

One JSON-RPC 2.0 request or response per line on `127.0.0.1:<port>`. The game starts the harness only in a debug build with the user argument `--harness-port=<port>`. The harness owns time: the run steps only from the harness, at `set_time_scale` ticks per physics frame, or by exact counts with `step`. `step {frames}` counts ticks (1/120 s). The error codes are in `client.py`.

## Tests

`just test-harness` runs a contract test for each command against `godot --headless`. `just test-harness -m gpu` also runs the GPU screenshot test, on a machine with a GPU and gamescope.

## Add a command

1. Add a handler to `_commands` in `game/harness/harness.gd`. Read params with the typed `Params` getters and return a `Failure` for errors.
2. Add a typed method to `Harness` in `client.py`, a CLI subcommand in `cli.py` and, if agents need it often, a `game_*` tool in `mcp_server.py`.
3. Add a contract test in `tests/test_contract.py`.

## Modes

`load_mode {mode, zone?, zones?, resume?, assist?}` starts a mode. `ascent` is the only one (`game/modes/ascent/ascent.gd`): it starts a new climb of every built zone and returns the state, in which `height` is the marble's height above the climb start in m. While no zone of the game is built, it climbs the fixture zones (`levels/test/ascent_fixture_<n>.py`). A request with an unknown mode, no built zone or a zone number above the number of zone scenes fails before the start, and keeps the run and Assist as they were. `resume` continues the saved spot. `zones` gives the zone level ids from the bottom, for a climb of some zones or of test levels. `assist` turns Assist on or off first. `zone` (1 is the first) puts the marble on the start pad of that zone.

```sh
just harness load_mode ascent --zone 2          # a new climb, with the marble at the start of zone 2
just harness load_mode ascent --resume          # continue where the last climb of this game ended
```

## Route bot

`run_bot {route?}` restarts the level and lets the route bot (`game/harness/route_bot.gd`) play one of its routes to the end at full speed, then pauses the run. `route` is a route kind (`first_run`, the default, or `expert`) or a route node name. The result is `{finished, time, falls}`, and `{stuck_at, waypoint, reason}` when the bot gave up. `game/objects/route/route.gd` describes how a level script places a route. `just test-levels` runs the same bot in-process, without the harness, so it runs on Windows too.
