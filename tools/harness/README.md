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
just harness quit
```

`launch` records the game in `build/harness/session.json`. Every other command, and the MCP server, talks to that game. Each command prints its result as JSON.

`--display` selects where the game renders:

| Display | What it does |
|---|---|
| `headless` (default) | `gamescope --backend headless` at the resolution. Real GPU frames, no window. Falls back to `window` |
| `window` | A desktop window at the resolution |
| `none` | `godot --headless`. Nothing renders, so `screenshot` fails. CI uses it |

## MCP tools

`game_launch {level, display, width, height}`, `game_state`, `game_input {move, jump, use, camera, frames}`, `game_step {frames}`, `game_screenshot {shot}` (returns the image), `game_logs {since}`, `game_quit`. The other harness commands (`teleport`, `pause`, `set_time_scale` and so on) are in the CLI.

## Protocol

One JSON-RPC 2.0 request or response per line on `127.0.0.1:<port>`. The game starts the harness only in a debug build with the user argument `--harness-port=<port>`. The harness owns time: the run steps only from the harness, at `set_time_scale` ticks per physics frame, or by exact counts with `step`. `step {frames}` counts ticks (1/120 s). The error codes are in `client.py`.

## Tests

`just test-harness` runs a contract test for each command against `godot --headless`. `just test-harness -m gpu` also runs the GPU screenshot test, on a machine with a GPU and gamescope.

## Add a command

1. Add a handler to `_commands` in `game/harness/harness.gd`. Read params with the typed `Params` getters and return a `Failure` for errors.
2. Add a typed method to `Harness` in `client.py`, a CLI subcommand in `cli.py` and, if agents need it often, a `game_*` tool in `mcp_server.py`.
3. Add a contract test in `tests/test_contract.py`.

For example, the route bot (#14) adds `run_bot {route?}`: the handler makes the bot's `InputSource` active with `InputHub.use_source()`, steps the run until it finishes or fails, makes the harness source active again and returns `{finished, time, falls, stuck_at?}`.
