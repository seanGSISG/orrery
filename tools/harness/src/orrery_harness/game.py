"""Launch and stop a debug build of the game with the harness on.

launch() starts `godot --path game -- --harness-port=<port>` on a free port and waits
until the harness answers. The display decides where it renders:

- headless: inside `gamescope --backend headless` at the set resolution. The GPU renders
  real frames, and no window opens. When gamescope is missing or the game does not come
  up in it, launch falls back to window.
- window: a normal desktop window at the set resolution.
- none: `godot --headless`. It renders nothing, so screenshots fail; tests and CI use it.

launch() records the running game in build/harness/session.json, so that every later CLI
command and the MCP server reach the same game.
"""

import os
import shutil
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from orrery_harness.client import Harness

type Display = Literal["headless", "window", "none"]

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "game/project.godot").exists()
)
GAME = ROOT / "game"
RUNS = ROOT / "build/harness"
SESSION = RUNS / "session.json"

# The game gets only these variables from the caller's environment, plus the GPU driver
# variables that start with a prefix below.
_ENV_KEYS = {
    "PATH",
    "HOME",
    "USER",
    "LANG",
    "LC_ALL",
    "XDG_RUNTIME_DIR",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_CACHE_HOME",
    "DISPLAY",
    "WAYLAND_DISPLAY",
    "XAUTHORITY",
    "DBUS_SESSION_BUS_ADDRESS",
}
_ENV_PREFIXES = ("VK_", "MESA_", "__GLX_", "__NV_", "DRI_")


class Session(BaseModel):
    """A running game: its harness port, process id, display and log file."""

    port: int
    pid: int
    display: Display
    log: str

    def connect(self) -> Harness:
        return Harness(self.port)


@dataclass(frozen=True)
class LaunchOptions:
    """What launch() starts. resolution is (width, height)."""

    level: str | None = None
    display: Display = "headless"
    resolution: tuple[int, int] = (1920, 1080)
    timeout: float = 60.0


class LaunchError(RuntimeError):
    """The game did not start, or its harness did not answer in time."""


def godot() -> str:
    """The Godot binary: $ORRERY_GODOT, else the mise pin, else `godot` on PATH."""
    if path := os.environ.get("ORRERY_GODOT"):
        return path
    if shutil.which("mise"):
        found = subprocess.run(
            ["mise", "which", "godot"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if found.returncode == 0 and found.stdout.strip():
            return found.stdout.strip()
    return shutil.which("godot") or "godot"


def launch(options: LaunchOptions) -> Session:
    """Stops the recorded game, starts a new one and records it."""
    stop()
    session = start(options)
    SESSION.write_text(session.model_dump_json())
    return session


def start(options: LaunchOptions) -> Session:
    """Starts a game and waits until its harness answers, without recording it. Stop it
    with end()."""
    RUNS.mkdir(parents=True, exist_ok=True)
    binary = godot()
    if not (GAME / ".godot").exists():
        subprocess.run(
            [binary, "--headless", "--path", str(GAME), "--import"], check=True
        )
    displays: list[Display] = [options.display]
    if options.display == "headless":
        if shutil.which("gamescope"):
            displays.append("window")
        else:
            displays = ["window"]
    errors: list[str] = []
    for display in displays:
        try:
            return _start(binary, display, options)
        except LaunchError as error:
            errors.append(f"{display}: {error}")
    raise LaunchError("; ".join(errors))


def current() -> Session:
    """The recorded game. Raises LaunchError when no game is recorded."""
    if not SESSION.exists():
        raise LaunchError("no game is running; launch one first")
    return Session.model_validate_json(SESSION.read_text())


def stop() -> None:
    """Ends the recorded game and forgets it."""
    if SESSION.exists():
        session = current()
        SESSION.unlink()
        end(session)


def end(session: Session) -> None:
    """Quits the game, and kills it when it does not quit within 10 s. A game that no longer
    runs gets no quit, because another game may have its port now."""
    if not running(session):
        return
    try:
        with session.connect() as game:
            game.quit()
    except OSError:
        pass
    if not _wait_exit(session, 10.0):
        _kill(session)


def _start(binary: str, display: Display, options: LaunchOptions) -> Session:
    port = _free_port()
    width, height = options.resolution
    args = ["--", f"--harness-port={port}"]
    if options.level:
        args += ["--level", options.level]
    size = ["--resolution", f"{width}x{height}"]
    command = {
        "headless": [
            *(
                "gamescope",
                "--backend",
                "headless",
                "-W",
                str(width),
                "-H",
                str(height),
                "--",
            ),
            *(binary, "--path", str(GAME), *size, *args),
        ],
        "window": [binary, "--path", str(GAME), *size, *args],
        "none": [binary, "--headless", "--path", str(GAME), *args],
    }[display]
    log = RUNS / f"game-{port}.log"
    with log.open("wb") as out:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            env=_game_env(),
            start_new_session=True,
        )
    session = Session(port=port, pid=process.pid, display=display, log=str(log))
    deadline = time.monotonic() + options.timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise LaunchError(f"the game exited with {process.returncode}; see {log}")
        try:
            with session.connect() as game:
                game.ping()
            return session
        except OSError:
            time.sleep(0.2)
    _kill(session)
    raise LaunchError(f"no harness answer in {options.timeout:.0f} s; see {log}")


def _game_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if value and (key in _ENV_KEYS or key.startswith(_ENV_PREFIXES))
    }


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def running(session: Session) -> bool:
    """True while the session's process runs and is still that game: its command line has
    the session's harness port. A reused process id is not the game."""
    # A child that exited stays a zombie until it is reaped; reap it when it is ours.
    try:
        os.waitpid(session.pid, os.WNOHANG)
    except ChildProcessError:
        pass
    try:
        command = Path(f"/proc/{session.pid}/cmdline").read_bytes()
    except OSError:
        return False
    return f"--harness-port={session.port}".encode() in command


def _wait_exit(session: Session, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not running(session):
            return True
        time.sleep(0.1)
    return False


def _kill(session: Session) -> None:
    """Kills the game's process group (gamescope and Godot) while it is still the game."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if not running(session):
            return
        try:
            os.killpg(session.pid, sig)
        except ProcessLookupError:
            return
        if _wait_exit(session, 5.0):
            return
