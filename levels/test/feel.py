"""Feel-review course (#19): one loop of numbered stations for tuning the marble by feel.
`just feel` plays it with the live tuning overlay; docs/feel-review.md says what to try at
each station. Each station has a floating sign with its number and name, so a report can
say "station 2 feels icy".

The loop runs counter-clockwise, seen from above:
- north (+y): 1 flat runway with 5 m stripes, 2-4 hills of 10, 20 and 30 degrees;
- east (+x): 5-7 walls of 90, 60 and 45 degrees, 8 a thin wall, 9 a V seam;
- south (-y): 10 gaps of 1 to 6 m, 11 steps of 0.5 to 1.2 m, then a ramp down;
- west (-x): 12 a moving platform, 13 a turning gear, 14 bumpers, then back onto the
  runway.
The finish is on a side pad west of the start, out of the loop.

Kit has only flat tracks and ramps, so the walls, the V seam and the steps are prisms made
by _prism() below. M1 has one surface type (default), so every piece uses it; the stations
differ only in colour.
"""

import math
from collections.abc import Sequence

import bmesh
import bpy

import kit

WIDTH = 8.0
HALF = WIDTH / 2
# A prism goes this far below the track top, so that it closes against the track slab.
EMBED = 0.3


def _material(name: str, rgb: tuple[float, float, float]) -> bpy.types.Material:
    """Returns a material of colour rgb on the default surface, made once."""
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material["surface"] = "default"
        material.use_backface_culling = True
        material.diffuse_color = (*rgb, 1.0)
        nodes = material.node_tree.nodes if material.node_tree else None
        bsdf = nodes.get("Principled BSDF") if nodes else None
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    return material


LIGHT = _material("feel_light", (0.78, 0.78, 0.74))
DARK = _material("feel_dark", (0.22, 0.24, 0.27))
WALL = _material("feel_wall", (0.62, 0.36, 0.28))
SIGN = _material("feel_sign", (1.0, 0.78, 0.18))


def _paint(obj: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Object:
    """Gives every face of a kit piece the material."""
    obj.data.materials[0] = material
    return obj


def _prism(
    name: str,
    at: tuple[float, float, float],
    profile: Sequence[tuple[float, float]],
    length: float,
    yaw: float = 0.0,
    material: bpy.types.Material = WALL,
) -> bpy.types.Object:
    """Adds a colliding prism: the closed polygon profile of (across, up) points, in m from
    `at`, swept `length` m forward. Like a kit piece, it runs along +y turned by `yaw`
    degrees, and +across is the right side."""
    bm = bmesh.new()
    front = [bm.verts.new((u, 0.0, z)) for u, z in profile]
    back = [bm.verts.new((u, length, z)) for u, z in profile]
    bm.faces.new(front)
    bm.faces.new(back)
    for i in range(len(profile)):
        j = (i + 1) % len(profile)
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(f"{name}-col", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw))
    return obj


def _wall(name: str, at: tuple[float, float, float], angle: float, yaw: float) -> None:
    """Adds a 1.5 m wall along the left side of the lane whose face leans back to `angle`
    degrees from the floor, 12 m long."""
    height = 1.5
    lean = height / math.tan(math.radians(angle))
    foot = -HALF + 1.5
    below = EMBED / math.tan(math.radians(angle))
    profile = [
        (foot + below, -EMBED),
        (foot - lean, height),
        (foot - lean - 0.5, height),
        (foot - lean - 0.5, -EMBED),
    ]
    _prism(name, at, profile, 12.0, yaw)


def _sign(
    text: str, at: tuple[float, float, float], yaw: float, size: float = 0.9
) -> None:
    """Adds an upright text sign centred on `at`, readable when you travel along `yaw` (the
    kit yaw of the piece it labels). It does not collide."""
    curve = bpy.data.curves.new(f"sign {text}", type="FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.size = size
    curve.extrude = 0.04
    source = bpy.data.objects.new(f"sign {text} source", curve)
    bpy.context.scene.collection.objects.link(source)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph))
    bpy.data.objects.remove(source)
    mesh.materials.clear()
    mesh.materials.append(SIGN)
    obj = bpy.data.objects.new(f"sign {text}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    obj.rotation_euler = (math.radians(90), 0.0, math.radians(yaw))


kit.level(title="Feel review", par=300.0, gold=150.0)

# --- North leg, +y (yaw 0) ---------------------------------------------------------------

# 1: a 60 m runway in 5 m stripes, to judge top speed and braking distance.
for i in range(12):
    _paint(kit.track(at=(0, i * 5, 0), length=5), LIGHT if i % 2 == 0 else DARK)
kit.marker("start", at=(0, 2, 0))
_sign("1 FLAT", (0, 8, 1.8), 0)

# 2-4: hills that climb and drop at 10, 20 and 30 degrees, each with a 4 m top.
y = 60.0
for number, angle, length, colour in (
    (2, 10, 12, LIGHT),
    (3, 20, 8, DARK),
    (4, 30, 6, LIGHT),
):
    rise = length * math.tan(math.radians(angle))
    _sign(f"{number} SLOPE {angle}", (0, y + 1, 1.8), 0)
    _paint(kit.ramp(at=(0, y, 0), length=length, rise=rise), colour)
    _paint(kit.track(at=(0, y + length, rise), length=4), colour)
    _paint(kit.ramp(at=(0, y + length + 4, rise), length=length, rise=-rise), colour)
    _paint(kit.track(at=(0, y + 2 * length + 4, 0), length=4), colour)
    y += 2 * length + 8
# The flat after the last hill (y 132..136) and this track make the corner pad: x -4..4,
# y 132..140.
_paint(kit.track(at=(0, 136, 0), length=4), DARK)

# --- East leg, +x (yaw -90); the lane centre is y = 136 ---------------------------------

EAST = -90.0
kit.marker("checkpoint", at=(7, 136, 0))
for number, angle, x in ((5, 90, 4), (6, 60, 18), (7, 45, 32)):
    _paint(
        kit.track(at=(x, 136, 0), length=14, yaw=EAST), LIGHT if number % 2 else DARK
    )
    _wall(f"wall_{angle}", (x + 1, 136, 0), angle, EAST)
    _sign(f"{number} WALL {angle}", (x + 2, 136, 1.8), EAST)

# 8: a free-standing wall 0.2 m thick in the middle of the lane, for the camera case of #11.
_paint(kit.track(at=(46, 136, 0), length=14, yaw=EAST), DARK)
_prism(
    "thin_wall",
    (48, 136, 0),
    [(-0.1, -EMBED), (0.1, -EMBED), (0.1, 2), (-0.1, 2)],
    10,
    EAST,
)
_sign("8 THIN WALL", (47, 136, 2.9), EAST)

# 9: a V seam: two 30 degree faces that meet along the lane centre.
side = HALF * math.tan(math.radians(30))
_prism(
    "v_seam",
    (60, 136, 0),
    [(-HALF, side), (0, 0), (HALF, side), (HALF, -0.5), (-HALF, -0.5)],
    14,
    EAST,
    LIGHT,
)
_sign("9 V SEAM", (61, 136, 3.0), EAST)
# The corner pad spans x 74..82, y 132..140.
_paint(kit.track(at=(74, 136, 0), length=8, yaw=EAST), DARK)

# --- South leg, -y (yaw 180); the lane centre is x = 78 ---------------------------------

SOUTH = 180.0
kit.marker("checkpoint", at=(78, 129, 0))
_paint(kit.track(at=(78, 132, 0), length=12, yaw=SOUTH), LIGHT)
_sign("10 GAPS", (78, 128, 1.8), SOUTH)

# 10: pads with gaps of 1, 2, 3, 4 and 6 m between them.
y = 120.0
for i, gap in enumerate((1, 2, 3, 4, 6)):
    y -= gap
    _sign(f"{gap} m", (78, y + gap / 2, 1.4), SOUTH, size=0.6)
    _paint(
        kit.track(at=(78, y, 0), length=6 if i < 4 else 8, yaw=SOUTH),
        DARK if i % 2 else LIGHT,
    )
    y -= 6 if i < 4 else 8
# y is 72 here: the last pad ends at y 72.

# 11: steps that rise 0.5, 0.8, 1.0 and 1.2 m, each 5 m deep, then a ramp back down.
kit.marker("checkpoint", at=(78, 76, 0))
_sign("11 STEPS", (78, 75, 1.8), SOUTH)
top = 0.0
for i, step in enumerate((0.5, 0.8, 1.0, 1.2)):
    top += step
    box = [(-HALF, -EMBED), (HALF, -EMBED), (HALF, top), (-HALF, top)]
    _prism(f"step_{i}", (78, y, 0), box, 5, SOUTH, LIGHT if i % 2 else DARK)
    _sign(f"{step:.1f} m", (78, y - 0.5, top + 1.3), SOUTH, size=0.6)
    y -= 5
_paint(kit.ramp(at=(78, y, top), length=12, rise=-top, yaw=SOUTH), LIGHT)
_paint(kit.track(at=(78, y - 12, 0), length=4, yaw=SOUTH), DARK)
# y - 16 is 36: the corner pad spans x 74..82, y 28..36.
_paint(kit.track(at=(78, 36, 0), length=8, yaw=SOUTH), LIGHT)

# --- West leg, -x (yaw 90); the lane centre is y = 32 -----------------------------------

WEST = 90.0
kit.marker("checkpoint", at=(71, 32, 0))
_paint(kit.track(at=(74, 32, 0), length=8, yaw=WEST), DARK)

# 12 and 13: the mover fixture of levels/test/movers.py, along -x. The deck (4 x 4 m)
# starts flush with the track end and stops flush with the gear.
_sign("12 PLATFORM", (68, 32, 1.8), WEST)
kit.marker(
    "moving_platform", at=(64, 32, 0), points=[(52, 32, 0)], period=9.0, stop=1.5
)
kit.marker("turning_gear", at=(47.9, 32, 0), period=6.0, radius=2.1, teeth=10)
_sign("13 GEAR", (47.9, 32, 1.8), WEST)

# Back to the runway: the track ends at its right edge, x = 4.
_paint(kit.track(at=(45.8, 32, 0), length=41.8, yaw=WEST), LIGHT)

# 14: three bumpers to roll into, off the lane centre so that you can also pass them.
_sign("14 BUMPERS", (36, 32, 1.8), WEST)
for x, y in ((30, 30.5), (24, 33.5), (18, 30.5)):
    kit.marker("bumper", at=(x, y, 0))

# The finish: a side pad off the left edge of the runway, out of the loop.
_paint(kit.track(at=(-4, 4, 0), width=4, length=6, yaw=WEST), DARK)
kit.marker("finish", at=(-8, 4, 0))
_sign("FINISH", (-8, 4, 2.0), WEST, size=0.6)

kit.shot("overview", at=(38, 10, 105), rotation=(-62, 0, 0))
kit.shot("runway", at=(0, -4, 2.2), rotation=(-8, 0, 0))
kit.shot("hills", at=(9, 52, 6), rotation=(-18, 0, 30))
kit.shot("walls", at=(-4, 128, 4), rotation=(-14, 0, -70))
kit.shot("thin_wall", at=(44, 133, 1.4), rotation=(-6, 0, -80))
kit.shot("gaps", at=(84, 136, 5), rotation=(-20, 0, 160))
kit.shot("steps", at=(85, 82, 6), rotation=(-18, 0, 155))
kit.shot("movers", at=(66, 22, 7), rotation=(-25, 0, 48))
