# /// script
# requires-python = ">=3.12"
# dependencies = ["evdev>=1.9"]
# ///
"""A virtual Xbox 360 controller on /dev/uinput, for tests.

The kernel presents it like a real wired controller (same vendor, product and
axes), so the game reads it through the same input path as real hardware.

Run: uv run tools/pad/virtual_pad.py --seconds 15 --press a
"""

import argparse
import time

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
STICK = AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)
TRIGGER = AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)
HAT = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seconds", type=float, default=10.0, help="how long the device exists"
    )
    parser.add_argument(
        "--press", choices=sorted(BUTTONS), help="tap this button twice a second"
    )
    args = parser.parse_args()
    with make_pad() as pad:
        print(f"virtual pad up: {pad.device.path}", flush=True)
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            if args.press:
                pad.write(e.EV_KEY, BUTTONS[args.press], 1)
                pad.syn()
                time.sleep(0.2)
                pad.write(e.EV_KEY, BUTTONS[args.press], 0)
                pad.syn()
            time.sleep(0.3)


if __name__ == "__main__":
    main()
