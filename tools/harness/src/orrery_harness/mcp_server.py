"""The `orrery` MCP server: game_* tools over the same launcher and client as the CLI.

.mcp.json starts it with `uv run --directory tools/harness orrery-harness-mcp` (stdio).
game_launch records the game in build/harness/session.json, so the CLI reaches the same
game. A game that this server launched quits when the server exits.
"""

import atexit
from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Literal

from mcp.server.mcpserver import Image, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from orrery_harness import game
from orrery_harness.client import BotResult, GameState, Harness, HarnessError, LogLine

server = MCPServer(
    name="orrery",
    instructions=(
        "Play the Orrery debug build. Call game_launch first. The run steps itself in real "
        "time until game_step, which steps exact ticks and pauses it. game_input holds an "
        "input that the next ticks read."
    ),
)
SHOTS = game.RUNS / "shots"
# The game that this server launched, if any.
_launched: game.Session | None = None


@contextmanager
def _errors() -> Generator[None]:
    """Shows launch, harness and socket errors to the agent as tool errors."""
    try:
        yield
    except (game.LaunchError, game.ShaderError, HarnessError, OSError) as error:
        raise ToolError(str(error)) from error


@contextmanager
def _game() -> Generator[Harness]:
    """A connection to the recorded game."""
    with _errors(), game.current().connect() as harness:
        yield harness


@server.tool()
def game_launch(
    level: str | None = "flat",
    display: Literal["headless", "window", "none"] = "headless",
    width: int = 1920,
    height: int = 1080,
) -> GameState:
    """Start the game with the harness, replacing a running one, and return the state.
    headless renders on the GPU in gamescope without a window (falls back to a window);
    none renders nothing (no screenshots)."""
    global _launched
    with _errors():
        _launched = game.launch(game.LaunchOptions(level, display, (width, height)))
    with _game() as harness:
        return harness.state()


@server.tool()
def game_load_mode(
    mode: Literal["ascent"] = "ascent",
    zone: int | None = None,
    zones: list[str] | None = None,
    resume: bool = False,
    assist: bool | None = None,
) -> GameState:
    """Start a mode in the launched game and return the state. ascent starts a new climb of
    every built zone, or continues the saved spot when resume is true. zone (1 is the first)
    puts the marble on the start pad of that zone; zones are the zone level ids from the
    bottom; assist turns Assist on or off first. state.height is m above the climb start."""
    with _game() as harness:
        return harness.load_mode(mode, zone, zones, resume, assist)


@server.tool()
def game_state() -> GameState:
    """Return the GameState: tick, level, status, marble position, velocity, gems, timer."""
    with _game() as harness:
        return harness.state()


@server.tool()
def game_input(
    move: tuple[float, float] = (0.0, 0.0),
    jump: bool = False,
    use: bool = False,
    camera: tuple[float, float] | None = None,
    frames: int | None = None,
) -> str:
    """Hold an input for `frames` ticks (default: until the next game_input). move is
    (right, forward) relative to the camera, length 0..1; camera is (yaw, pitch) in radians."""
    with _game() as harness:
        harness.input(move, jump, use, camera, frames)
    return "held"


@server.tool()
def game_step(frames: int = 1) -> GameState:
    """Step the run `frames` ticks (120 per second) at once, pause it, return the state."""
    with _game() as harness:
        return harness.step(frames)


@server.tool()
def game_screenshot(shot: str | None = None) -> list[Image | str]:
    """Render the next frame and return it as an image. shot names a level camera."""
    with _game() as harness:
        tick = harness.state().tick
        path = SHOTS / f"{shot or 'frame'}-{tick}.png"
        saved = harness.screenshot(str(path), shot)
    note = f"{saved.width}x{saved.height} on {saved.adapter}, saved to {saved.path}"
    return [Image(path=saved.path), f"BLANK FRAME: {note}" if saved.blank else note]


@server.tool()
def game_run_bot(route: str | None = None) -> BotResult:
    """Restart the level and let the route bot play a route to the end at full speed, then
    pause. route is first_run (default), expert or a route name. Returns finished, time (s)
    and falls; when the bot gave up, also stuck_at, waypoint and reason."""
    with _game() as harness:
        return harness.run_bot(route)


@server.tool()
def game_logs(since: int = 0) -> list[LogLine]:
    """Return the engine log lines after sequence number `since`."""
    with _game() as harness:
        return harness.logs(since)


@server.tool()
def game_quit() -> str:
    """Quit the game."""
    with _errors():
        game.stop()
    return "quit"


def _stop_launched() -> None:
    """Stops the game this server launched, unless another launch replaced it."""
    if _launched is not None and game.SESSION.exists() and game.current() == _launched:
        # The exit cannot report a shader error; game_quit does.
        with suppress(game.ShaderError):
            game.stop()


def main() -> None:
    atexit.register(_stop_launched)
    server.run()


if __name__ == "__main__":
    main()
