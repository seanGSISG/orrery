"""Orrery kit: the Blender library that level scripts call (docs/plan.md §4.3).

A level script `levels/<tier>/<id>.py` imports kit and builds its level in the empty scene that
`tools/blender/build_level.py` gives it. Rebuild with `just build-levels <id>`.

Units and axes are Blender's: metres, x right, y forward, z up. Angles are in degrees. The glTF
export turns positions into Godot's y-up axes: Blender (x, y, z) is Godot (x, z, -y).
"""

from kit.markers import level, marker, shot
from kit.masonry import (
    arch,
    ball,
    deck,
    dish,
    gear,
    hoop,
    inlay,
    lathe,
    pillar,
    teeth,
    wall,
)
from kit.outlines import arc, box, rect
from kit.pieces import ramp, track
from kit.surfaces import surface

__all__ = [
    "arc",
    "arch",
    "ball",
    "box",
    "deck",
    "dish",
    "gear",
    "hoop",
    "inlay",
    "lathe",
    "level",
    "marker",
    "pillar",
    "ramp",
    "rect",
    "shot",
    "surface",
    "teeth",
    "track",
    "wall",
]
