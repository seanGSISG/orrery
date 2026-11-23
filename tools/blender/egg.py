"""Builds the jewelled brass Clockwork Egg and exports it as a .glb.

`just build-egg` runs it; to run it by hand:

    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 \
        --python tools/blender/egg.py -- <out.glb>

The egg is the hidden egg of each level (docs/plan.md §2.7). Lengths are metres. The origin is
on the floor below the egg, +z is up and +y is the back, where the hinge is. The .glb holds
three objects, which game/objects/egg/egg.gd moves:

- `shell`: the foot and the lower half, with ribs, a waist band, jewels and a clasp.
- `lid`: the upper half, with a trellis, jewels and a jewel on top. Its origin is the hinge.
- `gear`: the clockwork that rises when the egg opens: three wheels on one arbor. Its origin
  is the middle of the arbor.

The .glb holds no texture. The game gives the material `brass` its look
(game/objects/egg/brass.tres, named in egg.glb.import). The jewels are plain PBR materials,
which Godot imports as they are.
"""

import math
import sys
from itertools import pairwise
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

# The egg, as in game/objects/egg/egg.gd: the widest ring and its height, and the heights of
# the two halves.
RADIUS = 0.2
WAIST = 0.3
SHELL = 0.25
LID = 0.35
WALL = 0.006  # thickness of the two halves
# The axis of the hinge barrel: behind the widest ring. The lid turns about it.
HINGE = Vector((0.0, RADIUS + 0.012, WAIST))
GEAR_AT = Vector((0.0, 0.0, 0.2))
UP = Vector((0.0, 0.0, 1.0))
SEGMENTS = 48  # steps around the egg
# Material slots.
BRASS, BLUE, MAGENTA, GREEN = range(4)
# The jewels: the gem colours of the style board (docs/style/README.md), as linear RGB.
JEWELS = (
    ("jewel_blue", (0.01, 0.1, 0.55)),
    ("jewel_magenta", (0.6, 0.02, 0.28)),
    ("jewel_green", (0.0, 0.32, 0.1)),
)
# The foot from the floor to the cup that holds the egg: (radius, height).
FOOT = (
    (0.11, 0.0),
    (0.118, 0.006),
    (0.118, 0.014),
    (0.1, 0.02),
    (0.055, 0.034),
    (0.034, 0.05),
    (0.03, 0.062),
    (0.042, 0.074),
    (0.09, 0.082),
    (0.115, 0.088),
    (0.128, 0.1),
    (0.122, 0.104),
)
TRELLIS = 8  # ribs of the lid's trellis in each turn direction
TRELLIS_TOP = 1.2  # latitude where the trellis ends, under the collar of the top jewel


def egg_point(lat: float, lon: float, lift: float = 0.0) -> Vector:
    """Returns the point of the egg surface at latitude `lat` (-pi/2 is the bottom tip, 0 the
    widest ring, pi/2 the top tip) and longitude `lon`, `lift` metres outside the surface."""
    half = SHELL if lat < 0.0 else LID
    out = Vector((half * math.cos(lat), RADIUS * math.sin(lat))).normalized()
    ring = RADIUS * math.cos(lat) + lift * out.x
    return Vector(
        (
            math.cos(lon) * ring,
            math.sin(lon) * ring,
            WAIST + half * math.sin(lat) + lift * out.y,
        )
    )


def egg_normal(lat: float, lon: float) -> Vector:
    """Returns the unit normal of the egg surface, which points out of the egg."""
    return (egg_point(lat, lon, 1.0) - egg_point(lat, lon)).normalized()


class Part:
    """One object of the egg: a mesh that grows by faces. `origin` is the object's origin."""

    def __init__(self, name: str, origin: Vector) -> None:
        self.name = name
        self.origin = origin
        self.bm = bmesh.new()

    def face(
        self, corners: list[Vector], out: Vector, slot: int = BRASS, smooth: bool = True
    ) -> None:
        """Adds a face whose front looks along `out`. Corners that are one point count once."""
        ring: list[Vector] = []
        for corner in corners:
            if all((corner - other).length > 1e-6 for other in ring):
                ring.append(corner)
        if len(ring) < 3:
            return
        face = self.bm.faces.new(
            [self.bm.verts.new(corner - self.origin) for corner in ring]
        )
        face.normal_update()
        if face.normal.dot(out) < 0.0:
            face.normal_flip()
        face.material_index = slot
        face.smooth = smooth

    def lathe(
        self,
        profile: list[Vector],
        slot: int = BRASS,
        inward: bool = False,
        segments: int = SEGMENTS,
        smooth: bool = True,
    ) -> None:
        """Turns a profile round the z axis. Each profile point is (radius, 0, height). The
        faces look away from the axis, or toward it with `inward`. A flat end looks away from
        the middle height of the profile."""
        middle_height = (min(p.z for p in profile) + max(p.z for p in profile)) / 2
        for a, b in pairwise(profile):
            side = Vector((b.z - a.z, 0.0, a.x - b.x))
            if abs(side.x) < 1e-9:
                side = Vector((0.0, 0.0, 1.0 if a.z >= middle_height else -1.0))
            elif side.x < 0.0:
                side = -side
            for i in range(segments):
                turn0 = Matrix.Rotation(2 * math.pi * i / segments, 3, "Z")
                turn1 = Matrix.Rotation(2 * math.pi * (i + 1) / segments, 3, "Z")
                out = Matrix.Rotation(2 * math.pi * (i + 0.5) / segments, 3, "Z") @ side
                self.face(
                    [turn0 @ a, turn1 @ a, turn1 @ b, turn0 @ b],
                    -out if inward else out,
                    slot,
                    smooth,
                )

    def rod(
        self, start: Vector, end: Vector, radius: float, segments: int = 16
    ) -> None:
        """Adds a round rod with flat ends from `start` to `end`."""
        axis = (end - start).normalized()
        turn = UP.rotation_difference(axis).to_matrix()
        ring = [
            turn
            @ Vector(
                (
                    math.cos(2 * math.pi * i / segments),
                    math.sin(2 * math.pi * i / segments),
                    0.0,
                )
            )
            * radius
            for i in range(segments)
        ]
        for i in range(segments):
            j = (i + 1) % segments
            self.face(
                [start + ring[i], start + ring[j], end + ring[j], end + ring[i]],
                ring[i] + ring[j],
            )
        self.face([start + spot for spot in ring], -axis, BRASS, False)
        self.face([end + spot for spot in ring], axis, BRASS, False)

    def rib(
        self, points: list[Vector], normals: list[Vector], width: float, height: float
    ) -> None:
        """Adds a raised rib along a line on a surface: `points` on the surface, with the
        surface normal at each. The rib is `width` wide and stands `height` above the line."""
        rows: list[tuple[Vector, Vector, Vector, Vector]] = []
        for i, (point, normal) in enumerate(zip(points, normals, strict=True)):
            along = points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]
            across = along.cross(normal).normalized() * (width / 2)
            rise = normal * height
            sink = normal * -0.002  # the foot of the rib is inside the surface
            rows.append(
                (
                    point - across + sink,
                    point - across * 0.7 + rise,
                    point + across * 0.7 + rise,
                    point + across + sink,
                )
            )
        for i, (a, b) in enumerate(pairwise(rows)):
            across = (a[3] - a[0]).normalized()
            self.face([a[0], a[1], b[1], b[0]], -across)
            self.face([a[1], a[2], b[2], b[1]], normals[i])
            self.face([a[2], a[3], b[3], b[2]], across)
        self.face(list(rows[0]), points[0] - points[1])
        self.face(list(rows[-1]), points[-1] - points[-2])

    def ball(self, centre: Vector, radius: float, slot: int = BRASS) -> None:
        """Adds a small smooth ball."""
        steps, rings = 6, 4
        for j in range(rings):
            for i in range(steps):
                corners = []
                for dj, di in ((0, 0), (0, 1), (1, 1), (1, 0)):
                    lat = math.pi * ((j + dj) / rings - 0.5)
                    lon = 2 * math.pi * (i + di) / steps
                    corners.append(
                        centre
                        + radius
                        * Vector(
                            (
                                math.cos(lat) * math.cos(lon),
                                math.cos(lat) * math.sin(lon),
                                math.sin(lat),
                            )
                        )
                    )
                middle = sum(corners, Vector()) / 4
                self.face(corners, middle - centre, slot)

    def jewel(
        self,
        base: Vector,
        normal: Vector,
        radius: float,
        slot: int,
        tall: float = 0.75,
        point: bool = False,
    ) -> None:
        """Adds a faceted jewel in a brass setting. `base` is on the surface that holds it,
        `normal` points away from that surface, and the jewel stands `tall` radii high. Its
        top is a flat table, or a point with `point`."""
        normal = normal.normalized()
        turn = UP.rotation_difference(normal).to_matrix()

        def ring(share: float, height: float, sides: int, phase: float) -> list[Vector]:
            return [
                base
                + turn
                @ Vector(
                    (
                        math.cos(2 * math.pi * (i + phase) / sides) * radius * share,
                        math.sin(2 * math.pi * (i + phase) / sides) * radius * share,
                        height * radius,
                    )
                )
                for i in range(sides)
            ]

        # The setting: a collar round the foot of the jewel.
        low, high = ring(1.25, -0.25, 16, 0.0), ring(1.12, 0.22, 16, 0.0)
        lip = ring(0.98, 0.22, 16, 0.0)
        for i in range(16):
            j = (i + 1) % 16
            out = (low[i] + low[j]) / 2 - base
            self.face(
                [low[i], low[j], high[j], high[i]], out - normal * out.dot(normal)
            )
            self.face([high[i], high[j], lip[j], lip[i]], normal)
        # The jewel: a girdle, a ring of triangles, and a table or a point.
        sides = 8
        girdle = ring(1.0, 0.15, sides, 0.0)
        crown = ring(
            0.7 if point else 0.55, tall * (0.45 if point else 1.0), sides, 0.5
        )
        tip = base + normal * (tall * radius)
        for i in range(sides):
            j = (i + 1) % sides
            facets = [[girdle[i], girdle[j], crown[i]], [crown[i], crown[j], girdle[j]]]
            if point:
                facets.append([crown[i], crown[j], tip])
            for corners in facets:
                middle = sum(corners, Vector()) / 3
                self.face(corners, middle - base + normal * (radius * 0.5), slot, False)
        if not point:
            self.face(crown, normal, slot, False)

    def wheel(
        self,
        height: float,
        radius: float,
        teeth: int,
        thick: float,
        hub: float,
        spokes: int,
    ) -> None:
        """Adds a spur wheel round the z axis at `height`: `radius` is the tip of a tooth and
        `hub` the radius of the hub. Spokes join the hub to the toothed rim."""
        root = radius - 0.5 * (2 * math.pi * radius / teeth)
        inner = root - 0.35 * (root - hub) if spokes else hub
        outline: list[Vector] = []
        bore: list[Vector] = []
        for tooth in range(teeth):
            for share, reach in (
                (0.0, root),
                (0.2, radius),
                (0.5, radius),
                (0.7, root),
            ):
                angle = 2 * math.pi * (tooth + share) / teeth
                spot = Vector((math.cos(angle), math.sin(angle), 0.0))
                outline.append(spot * reach)
                bore.append(spot * inner)
        low = Vector((0.0, 0.0, height - thick / 2))
        high = Vector((0.0, 0.0, height + thick / 2))
        count = len(outline)
        for i in range(count):
            j = (i + 1) % count
            self.face(
                [outline[i] + high, outline[j] + high, bore[j] + high, bore[i] + high],
                UP,
                BRASS,
                False,
            )
            self.face(
                [outline[i] + low, outline[j] + low, bore[j] + low, bore[i] + low],
                -UP,
                BRASS,
                False,
            )
            edge = outline[j] - outline[i]
            self.face(
                [
                    outline[i] + low,
                    outline[j] + low,
                    outline[j] + high,
                    outline[i] + high,
                ],
                Vector((edge.y, -edge.x, 0.0)),
                BRASS,
                False,
            )
            if spokes:
                self.face(
                    [bore[i] + low, bore[j] + low, bore[j] + high, bore[i] + high],
                    -(bore[i] + bore[j]),
                    BRASS,
                    False,
                )
        if not spokes:
            return
        self.rod(low, high, hub, 24)
        wide = hub * 0.45
        for spoke in range(spokes):
            turn = Matrix.Rotation(2 * math.pi * spoke / spokes, 3, "Z")
            corners = [
                turn @ Vector((x, y, z))
                for x in (hub * 0.8, inner * 1.02)
                for y in (-wide, wide)
                for z in (low.z, high.z)
            ]
            x0y0z0, x0y0z1, x0y1z0, x0y1z1, x1y0z0, x1y0z1, x1y1z0, x1y1z1 = corners
            self.face([x0y0z1, x0y1z1, x1y1z1, x1y0z1], UP, BRASS, False)
            self.face([x0y0z0, x0y1z0, x1y1z0, x1y0z0], -UP, BRASS, False)
            self.face(
                [x0y0z0, x1y0z0, x1y0z1, x0y0z1],
                turn @ Vector((0, -1, 0)),
                BRASS,
                False,
            )
            self.face(
                [x0y1z0, x1y1z0, x1y1z1, x0y1z1], turn @ Vector((0, 1, 0)), BRASS, False
            )

    def finish(self, materials: list[bpy.types.Material]) -> None:
        """Makes the object. Edges sharper than 40 degrees stay sharp between smooth faces."""
        # face() gives each face its own points; smooth faces must share them.
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-5)
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for material in materials:
            mesh.materials.append(material)
        mesh.set_sharp_from_angle(angle=math.radians(40))
        item = bpy.data.objects.new(self.name, mesh)
        item.location = self.origin
        bpy.context.scene.collection.objects.link(item)


def half(part: Part, lower: bool) -> None:
    """Adds one half of the egg: the outside, the inside and the flat rim at the widest ring."""
    rings = 18
    sign = -1.0 if lower else 1.0
    outside = [egg_point(sign * math.pi / 2 * k / rings, 0.0) for k in range(rings + 1)]
    inside = [
        egg_point(sign * math.pi / 2 * k / rings, 0.0, -WALL) for k in range(rings + 1)
    ]
    part.lathe(outside)
    part.lathe(inside, inward=True)
    for i in range(SEGMENTS):
        turn0 = Matrix.Rotation(2 * math.pi * i / SEGMENTS, 3, "Z")
        turn1 = Matrix.Rotation(2 * math.pi * (i + 1) / SEGMENTS, 3, "Z")
        part.face(
            [
                turn0 @ inside[0],
                turn1 @ inside[0],
                turn1 @ outside[0],
                turn0 @ outside[0],
            ],
            UP if lower else -UP,
            BRASS,
            False,
        )


def moulding(part: Part, height: float, reach: float, bulge: float) -> None:
    """Adds a half-round band round the egg at the widest ring: `reach` tall, `bulge` deep."""
    steps = 6
    profile = []
    for k in range(steps + 1):
        angle = math.pi * (k / steps - 0.5)
        profile.append(
            Vector(
                (
                    RADIUS - 0.002 + bulge * math.cos(angle),
                    0,
                    height + reach / 2 * math.sin(angle),
                )
            )
        )
    part.lathe(
        [
            Vector((RADIUS - 0.004, 0, profile[0].z)),
            *profile,
            Vector((RADIUS - 0.004, 0, profile[-1].z)),
        ]
    )


def build_shell() -> Part:
    """Builds the foot and the lower half."""
    part = Part("shell", Vector())
    half(part, lower=True)
    part.lathe([Vector((radius, 0, height)) for radius, height in FOOT])
    band = WAIST - 0.014
    moulding(part, band, 0.02, 0.008)
    # Ribs from the cup of the foot up to the band.
    for i in range(12):
        lon = 2 * math.pi * (i + 0.5) / 12
        lats = [-1.0 + (1.0 - 0.1) * k / 14 for k in range(15)]
        part.rib(
            [egg_point(lat, lon) for lat in lats],
            [egg_normal(lat, lon) for lat in lats],
            0.008,
            0.003,
        )
    # Jewels on the band. The hinge takes the place of the jewel at the back, and the clasp
    # at the front is a large jewel on a plate.
    for i in range(12):
        lon = 2 * math.pi * i / 12
        out = Vector((math.cos(lon), math.sin(lon), 0.0))
        at = out * (RADIUS + 0.005) + UP * band
        if i == 3:
            continue
        if i == 9:
            part.jewel(at + out * 0.004, out, 0.021, GREEN, 0.7)
        else:
            part.jewel(at, out, 0.013, MAGENTA if i % 2 else BLUE)
    # The hinge: two knuckles of the barrel across the back. The lid has the middle one.
    for sign in (-1.0, 1.0):
        part.rod(
            HINGE + Vector((0.015 * sign, 0.0, 0.0)),
            HINGE + Vector((0.045 * sign, 0.0, 0.0)),
            0.011,
        )
    return part


def build_lid() -> Part:
    """Builds the upper half: a rim with beads, a trellis with jewels and the top jewel."""
    part = Part("lid", HINGE)
    half(part, lower=False)
    moulding(part, WAIST + 0.009, 0.012, 0.005)
    part.rod(
        HINGE + Vector((-0.013, 0.0, 0.0)), HINGE + Vector((0.013, 0.0, 0.0)), 0.011
    )
    for i in range(60):
        lon = 2 * math.pi * i / 60
        part.ball(
            Vector((math.cos(lon), math.sin(lon), 0.0)) * (RADIUS + 0.0015)
            + UP * (WAIST + 0.0185),
            0.0042,
        )
    # The trellis: ribs that climb the lid in both turn directions and cross.
    turn = math.pi / 2
    steps = 28
    for i in range(TRELLIS):
        for way in (-1.0, 1.0):
            lats = [0.07 + (TRELLIS_TOP - 0.07) * k / steps for k in range(steps + 1)]
            lons = [
                2 * math.pi * i / TRELLIS + way * turn * k / steps
                for k in range(steps + 1)
            ]
            part.rib(
                [egg_point(lat, lon) for lat, lon in zip(lats, lons, strict=True)],
                [egg_normal(lat, lon) for lat, lon in zip(lats, lons, strict=True)],
                0.007,
                0.003,
            )
    # A jewel where the ribs cross, in two rows.
    for share, size, slot in ((0.25, 0.0085, BLUE), (0.5, 0.0075, MAGENTA)):
        lat = 0.07 + (TRELLIS_TOP - 0.07) * share
        for i in range(TRELLIS):
            lon = 2 * math.pi * i / TRELLIS + turn * share
            part.jewel(egg_point(lat, lon, 0.002), egg_normal(lat, lon), size, slot)
    # The collar that ends the trellis, with beads, and the jewel on top.
    top = egg_point(TRELLIS_TOP, 0.0)
    collar = top.z - 0.004
    part.lathe(
        [
            Vector((top.x + 0.004, 0, collar - 0.004)),
            Vector((top.x + 0.008, 0, collar + 0.002)),
            Vector((top.x + 0.002, 0, collar + 0.01)),
            Vector((0.03, 0, WAIST + LID + 0.004)),
            Vector((0.024, 0, WAIST + LID + 0.012)),
            Vector((0.0, 0, WAIST + LID + 0.012)),
        ]
    )
    for i in range(24):
        lon = 2 * math.pi * i / 24
        part.ball(
            Vector((math.cos(lon), math.sin(lon), 0.0)) * (top.x + 0.007)
            + UP * (collar + 0.003),
            0.0036,
        )
    crown = Vector((0.0, 0.0, WAIST + LID + 0.012))
    part.jewel(crown, UP, 0.026, BLUE, 2.4, point=True)
    return part


def build_gear() -> Part:
    """Builds the clockwork: three wheels and a jewel on one arbor."""
    part = Part("gear", GEAR_AT)
    part.rod(Vector((0.0, 0.0, 0.04)), Vector((0.0, 0.0, 0.29)), 0.007, 12)
    part.wheel(0.165, 0.125, 24, 0.014, 0.024, 5)
    part.wheel(0.215, 0.08, 16, 0.012, 0.018, 4)
    part.wheel(0.255, 0.045, 10, 0.01, 0.007, 0)
    part.jewel(Vector((0.0, 0.0, 0.288)), UP, 0.016, MAGENTA, 2.0, point=True)
    return part


def materials() -> list[bpy.types.Material]:
    """Returns the materials in slot order. The game replaces `brass` by its own material. A
    jewel is a mirror with the colour's hue, which shows the sky in each facet, and it glows a
    little in its colour, so that it shows in a dark room."""
    made = []
    looks = [("brass", (0.9, 0.62, 0.3), 0.25, 0.0)]
    for name, colour in JEWELS:
        looks.append((name, colour, 0.08, 0.5))
    for name, colour, roughness, glow in looks:
        material = bpy.data.materials.new(name)
        material.use_backface_culling = True
        tree = material.node_tree
        tree.nodes.clear()
        shader = tree.nodes.new("ShaderNodeBsdfPrincipled")
        hue = [channel / max(colour) for channel in colour] if glow else colour
        shader.inputs["Base Color"].default_value = (*hue, 1.0)
        shader.inputs["Metallic"].default_value = 1.0
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Emission Color"].default_value = (*colour, 1.0)
        shader.inputs["Emission Strength"].default_value = glow
        output = tree.nodes.new("ShaderNodeOutputMaterial")
        tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        made.append(material)
    return made


def main() -> None:
    """Builds the three objects and writes the .glb given after `--`."""
    out = Path(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    looks = materials()
    for part in (build_shell(), build_lid(), build_gear()):
        part.finish(looks)
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )


main()
