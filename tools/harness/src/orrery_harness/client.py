"""A typed client for the game harness (game/harness/harness.gd).

The harness speaks newline-delimited JSON-RPC 2.0 on 127.0.0.1. Use it like this:

    with Harness(port) as game:
        game.load_level("flat")
        game.input(move=(0.0, 1.0), frames=60)
        state = game.step(120)

Each method sends one command and returns its result as a model. An error response
raises HarnessError with the JSON-RPC code.
"""

import json
import socket
from types import TracebackType
from typing import Any, Self

from pydantic import BaseModel, ConfigDict

HOST = "127.0.0.1"

# Error codes that the harness adds to the JSON-RPC ones.
NO_RUN = -32000
NOT_FOUND = -32001
NOT_AVAILABLE = -32002
NO_FRAME = -32003
INVALID_REQUEST = -32600
INVALID_PARAMS = -32602
METHOD_NOT_FOUND = -32601
PARSE_ERROR = -32700

type Vector3 = tuple[float, float, float]


class GameState(BaseModel):
    """GameState.to_dict() (game/core/level/game_state.gd). Fields that later tickets add
    stay in the model as extra fields."""

    model_config = ConfigDict(extra="allow")

    tick: int
    level: str
    status: str
    screen: str
    input_device: str
    position: Vector3
    velocity: Vector3
    spin: Vector3
    up: Vector3
    on_ground: bool
    gems_collected: int
    gems_total: int
    timer: float
    medal: str
    power_up: str
    checkpoint: str
    egg_found: bool
    height: float


class Shot(BaseModel):
    """A saved screenshot. blank is true when the frame has almost one colour."""

    path: str
    width: int
    height: int
    blank: bool
    adapter: str


class LogLine(BaseModel):
    """One engine log line. seq counts up from 1; error is true for errors and warnings."""

    seq: int
    text: str
    error: bool


class _Logs(BaseModel):
    lines: list[LogLine]


class BotResult(BaseModel):
    """A route bot drive (game/harness/route_bot.gd): finished, the level clock in s and the
    falls out of bounds. When the bot gave up: stuck_at (world position), waypoint (the index
    of the point it headed for) and reason (stuck, fell, route_end or timeout)."""

    finished: bool
    time: float
    falls: int
    stuck_at: Vector3 | None = None
    waypoint: int | None = None
    reason: str | None = None


class _Error(BaseModel):
    code: int
    message: str


class _Response(BaseModel):
    id: int | str | None
    result: Any = None
    error: _Error | None = None


class HarnessError(Exception):
    """An error response from the harness."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"{message} (code {code})")
        self.code = code
        self.message = message


class Harness:
    """One connection to a running harness. Close it, or use it as a context manager."""

    def __init__(self, port: int, timeout: float = 60.0) -> None:
        self._socket = socket.create_connection((HOST, port), timeout=timeout)
        self._file = self._socket.makefile("rwb")
        self._next_id = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._file.close()
        self._socket.close()

    def call(self, method: str, **params: object) -> Any:
        """Sends one request and returns its result. None values are left out."""
        self._next_id += 1
        fields = {key: value for key, value in params.items() if value is not None}
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": method,
            "params": fields,
        }
        return self.send_line(json.dumps(request))

    def send_line(self, line: str) -> Any:
        """Sends one raw line and returns the result of its response."""
        self._file.write(line.encode() + b"\n")
        self._file.flush()
        reply = self._file.readline()
        if not reply:
            raise ConnectionError("the harness closed the connection")
        response = _Response.model_validate_json(reply)
        if response.error is not None:
            raise HarnessError(response.error.code, response.error.message)
        return response.result

    def ping(self) -> str:
        return self.call("ping")

    def quit(self) -> None:
        self.call("quit")

    def load_level(self, id: str) -> GameState:
        return GameState.model_validate(self.call("load_level", id=id))

    def load_mode(self, mode: str, zone: str | None = None) -> None:
        self.call("load_mode", mode=mode, zone=zone)

    def state(self) -> GameState:
        return GameState.model_validate(self.call("state"))

    def input(
        self,
        move: tuple[float, float] = (0.0, 0.0),
        jump: bool = False,
        use: bool = False,
        camera: tuple[float, float] | None = None,
        frames: int | None = None,
    ) -> None:
        """Holds the input for frames ticks, or until the next input when frames is None.
        move is (right, forward) relative to the camera; camera is (yaw, pitch) in radians."""
        self.call("input", move=move, jump=jump, use=use, camera=camera, frames=frames)

    def step(self, frames: int = 1) -> GameState:
        """Steps the run frames ticks at once, pauses it and returns the state."""
        return GameState.model_validate(self.call("step", frames=frames))

    def pause(self) -> None:
        self.call("pause")

    def resume(self) -> None:
        self.call("resume")

    def set_time_scale(self, scale: float) -> None:
        """Runs scale ticks per physics frame (0..64) while not paused."""
        self.call("set_time_scale", scale=scale)

    def teleport(self, position: Vector3, velocity: Vector3 | None = None) -> None:
        """Puts the marble at position with velocity; the state shows it at once."""
        self.call("teleport", position=position, velocity=velocity)

    def screenshot(self, path: str | None = None, shot: str | None = None) -> Shot:
        """Saves the next rendered frame as a PNG, from the level's Camera3D named shot
        when it is set."""
        return Shot.model_validate(self.call("screenshot", path=path, shot=shot))

    def logs(self, since: int = 0) -> list[LogLine]:
        return _Logs.model_validate(self.call("logs", since=since)).lines

    def run_bot(self, route: str | None = None) -> BotResult:
        """Restarts the level and lets the route bot play route (a kind, first_run by default,
        or a route name) to the end at full speed, then pauses the run."""
        return BotResult.model_validate(self.call("run_bot", route=route))

    def set_setting(self, key: str, value: object) -> object:
        """Sets an existing project setting and returns its new value."""
        return self.call("set_setting", key=key, value=value)["value"]
