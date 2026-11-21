# /// script
# requires-python = ">=3.12"
# dependencies = ["evdev>=1.9"]
# ///
"""A virtual Xbox 360 controller on /dev/uinput, for tests.

The kernel presents it like a real wired controller (same vendor, product and
axes), so the game reads it through the same input path as real hardware.

A sequence is a list of steps separated by ";". It repeats until --seconds end.
Each step holds its input for its seconds, then lets go:

    press <button> <seconds>        for example: press a 0.2
    stick <left|right> <x> <y> <s>  x right, y up, -1..1; for example: stick left 0 1 0.8
    trigger <lt|rt> <value> <s>     value 0..1
    wait <seconds>

Run: uv run tools/pad/virtual_pad.py --seconds 15 --press a
     uv run tools/pad/virtual_pad.py --sequence "press a 0.2; stick left 0 1 0.8"
"""

import argparse
import time
from dataclasses import dataclass

from evdev import AbsInfo, UInput
from evdev import ecodes as e

BUTTONS: dict[str, int] = {
    "a": e.BTN_SOUTH,
    "b": e.BTN_EAST,
    "x": e.BTN_NORTH,
    "y": e.BTN_WEST,
    "lb": e.BTN_TL,
    "rb": e.BTN_TR,
    "view": e.BTN_SELECT,
    "menu": e.BTN_START,
    "guide": e.BTN_MODE,
    "ls": e.BTN_THUMBL,
    "rs": e.BTN_THUMBR,
}
# The x and y axis of each stick, in evdev's direction: y is positive down.
STICKS: dict[str, tuple[int, int]] = {
    "left": (e.ABS_X, e.ABS_Y),
    "right": (e.ABS_RX, e.ABS_RY),
}
TRIGGERS: dict[str, int] = {"lt": e.ABS_Z, "rt": e.ABS_RZ}
STICK = AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)
TRIGGER = AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)
HAT = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)


@dataclass(frozen=True)
class Hold:
    """One input that a step holds: an evdev event type, code and value."""

    type: int
    code: int
    value: int


@dataclass(frozen=True)
class Step:
    """Holds inputs for some seconds, then lets them go. No inputs is a wait."""

    holds: tuple[Hold, ...]
    seconds: float


def parse_step(text: str) -> Step:
    """Parse one step, for example "stick left 0 1 0.8"; raise ValueError when invalid."""
    words = text.split()
    match words:
        case ["press", button, seconds] if button in BUTTONS:
            return Step((Hold(e.EV_KEY, BUTTONS[button], 1),), float(seconds))
        case ["stick", stick, x, y, seconds] if stick in STICKS:
            ax, ay = STICKS[stick]
            holds = (
                Hold(e.EV_ABS, ax, round(_unit(x) * 32767)),
                Hold(e.EV_ABS, ay, round(-_unit(y) * 32767)),
            )
            return Step(holds, float(seconds))
        case ["trigger", trigger, value, seconds] if trigger in TRIGGERS:
            level = round(max(_unit(value), 0.0) * 255)
            return Step((Hold(e.EV_ABS, TRIGGERS[trigger], level),), float(seconds))
        case ["wait", seconds]:
            return Step((), float(seconds))
    raise ValueError(f"bad step: {text!r}")


def parse_sequence(text: str) -> list[Step]:
    """Parse steps separated by ";"."""
    return [parse_step(part) for part in text.split(";") if part.strip()]


def _unit(text: str) -> float:
    """Parse a number and clamp it to -1..1."""
    return min(max(float(text), -1.0), 1.0)


def make_pad() -> UInput:
    """Create the device with the Xbox 360 wired ids that SDL and Godot know."""
    caps = {
        e.EV_KEY: list(BUTTONS.values()),
        e.EV_ABS: [
            (e.ABS_X, STICK),
            (e.ABS_Y, STICK),
            (e.ABS_RX, STICK),
            (e.ABS_RY, STICK),
            (e.ABS_Z, TRIGGER),
            (e.ABS_RZ, TRIGGER),
            (e.ABS_HAT0X, HAT),
            (e.ABS_HAT0Y, HAT),
        ],
    }
    # evdev's hint allows only int codes, but its docs take (code, AbsInfo) for EV_ABS.
    return UInput(
        caps,  # ty: ignore[invalid-argument-type]
        name="Microsoft X-Box 360 pad",
        vendor=0x045E,
        product=0x028E,
        version=0x0114,
        bustype=e.BUS_USB,
    )


def play(pad: UInput, step: Step) -> None:
    """Hold the step's inputs for its seconds, then let go (buttons up, axes centred)."""
    for hold in step.holds:
        pad.write(hold.type, hold.code, hold.value)
    pad.syn()
    time.sleep(step.seconds)
    for hold in step.holds:
        pad.write(hold.type, hold.code, 0)
    pad.syn()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--seconds", type=float, default=10.0, help="how long the device exists"
    )
    parser.add_argument(
        "--press", choices=sorted(BUTTONS), help="tap this button twice a second"
    )
    parser.add_argument("--sequence", help="steps to repeat; see above")
    args = parser.parse_args()
    text = args.sequence or (f"press {args.press} 0.2; wait 0.3" if args.press else "")
    try:
        steps = parse_sequence(text) or [Step((), 0.1)]
    except ValueError as error:
        parser.error(str(error))
    with make_pad() as pad:
        print(f"virtual pad up: {pad.device.path}", flush=True)
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            for step in steps:
                play(pad, step)


if __name__ == "__main__":
    main()
