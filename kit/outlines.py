"""Outlines: lists of (x, y) points, in metres, that say where a deck, an inlay or a wall
goes. A level script joins them into the outline of a floor:

    court = [(-17, 37), (17, 37), (17, 48), *kit.arc((0, 53), 5.6, -30, 210), (-17, 48)]

The point order of a closed outline does not matter; the pieces turn it as they need.
"""

import math
from collections.abc import Sequence

Point = tuple[float, float]

# An arc with no segment count has segments this flat: the gap between the arc and a
# segment's middle, m.
ARC_SAG = 0.001
MIN_SEGMENTS = 12


def rect(x0: float, y0: float, x1: float, y1: float) -> list[Point]:
    """Returns the rectangle with the opposite corners (x0, y0) and (x1, y1)."""
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def box(at: Point, width: float, length: float, yaw: float = 0.0) -> list[Point]:
    """Returns a rectangle that lies like a track piece: it starts at `at`, the centre of
    its front edge, and runs `length` m along +y, turned by `yaw` degrees."""
    turn = math.radians(yaw)
    across = (math.cos(turn), math.sin(turn))
    along = (-math.sin(turn), math.cos(turn))
    half = width / 2
    corners = ((-half, 0.0), (half, 0.0), (half, length), (-half, length))
    return [
        (at[0] + u * across[0] + v * along[0], at[1] + u * across[1] + v * along[1])
        for u, v in corners
    ]


def arc(
    centre: Point, radius: float, start: float, end: float, segments: int = 0
) -> list[Point]:
    """Returns the points of a circle arc from the angle `start` to `end`, in degrees
    counter-clockwise from +x. `end` below `start` goes clockwise. A sweep of 360 is a full
    circle of `segments` points; any other arc has `segments` + 1 points, with both ends.
    With no `segments`, the arc gets as many as it needs to look round."""
    sweep = math.radians(end - start)
    if segments <= 0:
        step = 2.0 * math.acos(max(0.0, 1.0 - ARC_SAG / radius))
        segments = max(MIN_SEGMENTS, math.ceil(abs(sweep) / step))
    full = math.isclose(abs(sweep), math.tau)
    count = segments if full else segments + 1
    first = math.radians(start)
    return [
        (
            centre[0] + radius * math.cos(first + sweep * i / segments),
            centre[1] + radius * math.sin(first + sweep * i / segments),
        )
        for i in range(count)
    ]


def signed_area(outline: Sequence[Point]) -> float:
    """Returns the area of a closed outline: positive when its points turn
    counter-clockwise."""
    total = 0.0
    for i, (x0, y0) in enumerate(outline):
        x1, y1 = outline[(i + 1) % len(outline)]
        total += x0 * y1 - x1 * y0
    return total / 2


def turned(outline: Sequence[Point], clockwise: bool = False) -> list[Point]:
    """Returns the closed outline with its points in counter-clockwise order, or clockwise."""
    points = list(outline)
    if (signed_area(points) < 0.0) != clockwise:
        points.reverse()
    return points
