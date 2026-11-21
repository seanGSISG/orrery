"""The orrery-harness CLI: one subcommand per harness command, plus launch.

    uv run orrery-harness launch --level flat --resolution 1280x720
    uv run orrery-harness input --move 0 1 --frames 60
    uv run orrery-harness step 120
    uv run orrery-harness screenshot --path build/harness/flat.png
    uv run orrery-harness quit

launch records the game in build/harness/session.json; the other commands talk to that
game. Each command prints its result as JSON. An error prints to stderr and exits 1.
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from orrery_harness import game
from orrery_harness.client import Harness, HarnessError

type Command = Callable[[Harness, argparse.Namespace], object]


def _resolution(text: str) -> tuple[int, int]:
    width, _, height = text.partition("x")
    return int(width), int(height)


def _vector(parts: list[float]) -> tuple[float, float, float]:
    return parts[0], parts[1], parts[2]


def _json(text: str) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _parser() -> tuple[argparse.ArgumentParser, dict[str, Command]]:
    parser = argparse.ArgumentParser(
        prog="orrery-harness", description=__doc__.split("\n")[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)
    commands: dict[str, Command] = {}

    def add(name: str, run: Command, help: str) -> argparse.ArgumentParser:
        commands[name] = run
        return sub.add_parser(name, help=help)

    launch = sub.add_parser("launch", help="start the game with the harness on")
    launch.add_argument("--level", help="level id to play, for example flat")
    launch.add_argument(
        "--display", choices=["headless", "window", "none"], default="headless"
    )
    launch.add_argument(
        "--resolution", type=_resolution, default=(1920, 1080), help="WxH"
    )

    add("ping", lambda g, a: g.ping(), "check that the harness answers")
    sub.add_parser("quit", help="quit the game")
    add("state", lambda g, a: g.state(), "print the GameState")
    add("load_level", lambda g, a: g.load_level(a.id), "load a level").add_argument(
        "id"
    )
    mode = add(
        "load_mode",
        lambda g, a: g.load_mode(a.mode, a.zone, a.zones, a.resume, a.assist),
        "start a mode: ascent",
    )
    mode.add_argument("mode")
    mode.add_argument("--zone", type=int, help="start on this zone; 1 is the first")
    mode.add_argument("--zones", nargs="+", help="zone level ids, from the bottom")
    mode.add_argument(
        "--resume", action="store_true", default=None, help="continue the saved spot"
    )
    mode.add_argument(
        "--assist", action=argparse.BooleanOptionalAction, help="turn Assist on or off"
    )
    held = add(
        "input",
        lambda g, a: g.input(
            move=(a.move[0], a.move[1]),
            jump=a.jump,
            use=a.use,
            camera=(a.camera[0], a.camera[1]) if a.camera else None,
            frames=a.frames,
        ),
        "hold an input",
    )
    held.add_argument(
        "--move", nargs=2, type=float, default=[0.0, 0.0], metavar=("X", "Y")
    )
    held.add_argument("--jump", action="store_true")
    held.add_argument("--use", action="store_true")
    held.add_argument("--camera", nargs=2, type=float, metavar=("YAW", "PITCH"))
    held.add_argument(
        "--frames", type=int, help="ticks to hold (default: until next input)"
    )
    add("step", lambda g, a: g.step(a.frames), "step ticks and pause").add_argument(
        "frames", type=int, nargs="?", default=1
    )
    add("pause", lambda g, a: g.pause(), "pause the run")
    add("resume", lambda g, a: g.resume(), "resume the run")
    add(
        "set_time_scale",
        lambda g, a: g.set_time_scale(a.scale),
        "ticks per physics frame",
    ).add_argument("scale", type=float)
    tp = add(
        "teleport",
        lambda g, a: g.teleport(
            _vector(a.position), _vector(a.velocity) if a.velocity else None
        ),
        "move the marble",
    )
    tp.add_argument("position", nargs=3, type=float)
    tp.add_argument("--velocity", nargs=3, type=float)
    shot = add(
        "screenshot",
        lambda g, a: g.screenshot(
            str(Path(a.path).resolve()) if a.path else None, a.shot
        ),
        "save a rendered frame",
    )
    shot.add_argument(
        "--path",
        help="PNG path (default: in build/harness/user-<port>-*/, deleted at the next launch)",
    )
    shot.add_argument("--shot", help="the level's Camera3D to render from")
    add("logs", lambda g, a: g.logs(a.since), "print engine log lines").add_argument(
        "--since", type=int, default=0
    )
    add(
        "run_bot", lambda g, a: g.run_bot(a.route), "play a route to the end"
    ).add_argument("--route", help="first_run (default), expert or a route name")
    setting = add(
        "set_setting",
        lambda g, a: g.set_setting(a.key, _json(a.value)),
        "set a setting",
    )
    setting.add_argument("key")
    setting.add_argument("value", help="a JSON value, or plain text")
    return parser, commands


def _plain(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser, commands = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "launch":
            options = game.LaunchOptions(args.level, args.display, args.resolution)
            result: object = game.launch(options)
        elif args.command == "quit":
            game.stop()
            result = None
        else:
            with game.current().connect() as harness:
                result = commands[args.command](harness, args)
    except (HarnessError, game.LaunchError, OSError) as error:
        print(f"orrery-harness: {error}", file=sys.stderr)
        return 1
    print(json.dumps(_plain(result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
