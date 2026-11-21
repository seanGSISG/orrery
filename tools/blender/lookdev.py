"""Look-dev renders for the style board: one small piece of a level, three candidates.

The script builds a small play space at the 0.2 m marble scale: a plaza, then
a fork of a wide banked route and a narrow shortcut beam that both climb to a
goal pad. It floats above a sea of clouds under an Earth sky at dawn (the
Beginner look). The script renders candidates A, B and C, which differ in
stone, metal, marble look and light. All geometry is built here; the stone
textures and the skies are the CC0 files under assets/textures/ (see
docs/licenses.md).

Run from the repo root:

    blender-5.2 -b --factory-startup --python-exit-code 1 \
        --python tools/blender/lookdev.py -- [--only A C] [--out DIR] \
        [--samples N] [--scale PERCENT] [--cpu]

Output: <out>/render-a.webp, render-b.webp, render-c.webp at 1920x1080
(default out: docs/style/review).
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[2]
STONE_DIR = REPO / "assets" / "textures" / "stone"
SKY_DIR = REPO / "assets" / "textures" / "sky"

MARBLE_RADIUS = 0.2  # docs/plan.md 4.2: all art is built to this scale
DECK_WIDTH = 2.4  # the wide route: six marble widths
BEAM_WIDTH = 0.5  # the shortcut: barely wider than the marble
DECK_THICKNESS = 0.2
PLAZA_RADIUS = 3.0
GOAL_RADIUS = 1.7
DECK_START = Vector((-1.0, 2.6, 0.0))  # the wide route leaves the plaza here, heading +Y
STRAIGHT = 3.0
ARC_RADIUS = 6.5
ARC_ANGLE = math.radians(62)
CLIMB = 1.1  # the goal pad is this much higher than the plaza
BANK = math.radians(7)
MARBLE_AT = Vector((0.4, 1.0, 0.0))  # on the plaza, in front of the fork
MARBLE_HOP = 0.3  # the marble is in mid-hop, so the blob shadow shows on its own
GEM_RADIUS = 0.16
CAMERA_AT = Vector((-8.5, -4.2, 4.8))  # a high three-quarter view, like a level overview
CAMERA_TARGET = Vector((1.5, 4.3, 0.1))
SUN_AZIMUTH = 90.0  # degrees in the scene, counter-clockwise from +X: ahead and left
SKY_CAP = 40.0  # the sky file's own sun is cut down to this; the sun lamp replaces it

UP = Vector((0.0, 0.0, 1.0))
BRASS = (0.78, 0.55, 0.19)
GOLD = (1.0, 0.74, 0.31)

MarbleLook = Literal["glass", "stone"]
Color = tuple[float, float, float]


@dataclass(frozen=True, kw_only=True)
class Candidate:
    """One render candidate: the stone, the metal, the marble look, the light and the sky."""

    name: str
    stone: str  # ambientCG asset id under assets/textures/stone
    stone_tile: float  # metres covered by one texture repeat
    stone_tint: Color  # multiplied with the stone colour; above 1 lightens it
    stone_roughness: float  # added to the (very glossy) roughness map
    metal_color: Color  # linear RGB of rails and trims
    metal_roughness: float
    marble: MarbleLook
    sky: str  # Poly Haven asset id under assets/textures/sky
    sky_strength: float
    sun_elevation: float  # degrees
    sun_color: Color
    sun_strength: float  # W/m2
    exposure: float


CANDIDATES: tuple[Candidate, ...] = (
    # Weathered honey limestone and aged brass in a warm dawn with cloud bands.
    Candidate(
        name="A", stone="Marble007", stone_tile=2.0, stone_tint=(1.7, 1.6, 1.4), stone_roughness=0.42,
        metal_color=BRASS, metal_roughness=0.34, marble="glass",
        sky="qwantani_sunset_puresky", sky_strength=0.8,
        sun_elevation=13.0, sun_color=(1.0, 0.70, 0.42), sun_strength=18.0, exposure=-1.7,
    ),
    # Polished white marble and gold in a soft pink dawn.
    Candidate(
        name="B", stone="Marble012", stone_tile=2.2, stone_tint=(1.0, 1.0, 1.0), stone_roughness=0.2,
        metal_color=GOLD, metal_roughness=0.24, marble="stone",
        sky="belfast_sunset_puresky", sky_strength=0.7,
        sun_elevation=8.0, sun_color=(1.0, 0.62, 0.48), sun_strength=12.0, exposure=-1.6,
    ),
    # Polished blue-black marble and aged brass in a clear dawn with a low sun.
    Candidate(
        name="C", stone="Marble023", stone_tile=2.2, stone_tint=(0.75, 0.84, 1.0), stone_roughness=0.22,
        metal_color=BRASS, metal_roughness=0.26, marble="glass",
        sky="syferfontein_1d_clear_puresky", sky_strength=1.5,
        sun_elevation=10.0, sun_color=(1.0, 0.62, 0.34), sun_strength=18.0, exposure=-1.6,
    ),
)  # fmt: skip


@dataclass(frozen=True)
class Frame:
    """A cross-section plane on a path: origin, right and up axes, distance along the path."""

    origin: Vector
    right: Vector
    up: Vector
    distance: float

    def at(self, x: float, z: float) -> Vector:
        return self.origin + self.right * x + self.up * z

    @property
    def forward(self) -> Vector:
        return self.up.cross(self.right)

    def matrix(self, x: float = 0.0, z: float = 0.0) -> Matrix:
        """Return a transform whose X, Y, Z axes are right, forward, up at the point (x, z)."""
        rotation = Matrix((self.right, self.forward, self.up)).transposed().to_4x4()
        return Matrix.Translation(self.at(x, z)) @ rotation


def direction(azimuth: float, elevation: float) -> Vector:
    """Return the unit vector for an azimuth (degrees from +X, counter-clockwise) and an elevation."""
    a, e = math.radians(azimuth), math.radians(elevation)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def deck_frames(step: float = 0.1) -> list[Frame]:
    """Return the frames of the wide route's centre line: a straight, then a banked climbing right turn."""
    arc_length = ARC_RADIUS * ARC_ANGLE
    total = STRAIGHT + arc_length
    count = round(total / step)
    frames: list[Frame] = []
    for index in range(count + 1):
        distance = total * index / count
        t = max(0.0, (distance - STRAIGHT) / arc_length)  # 0..1 along the turn
        heading = t * ARC_ANGLE
        origin = DECK_START + Vector((
            ARC_RADIUS * (1 - math.cos(heading)),
            min(distance, STRAIGHT) + ARC_RADIUS * math.sin(heading),
            CLIMB * t * t * (3 - 2 * t),
        ))  # fmt: skip
        slope = CLIMB * 6 * t * (1 - t) / arc_length
        forward = Vector((math.sin(heading), math.cos(heading), slope)).normalized()
        flat_right = forward.cross(UP).normalized()
        flat_up = flat_right.cross(forward)
        bank = BANK * math.sin(math.pi * t)
        right = flat_right * math.cos(bank) - flat_up * math.sin(bank)
        frames.append(Frame(origin, right, right.cross(forward), distance))
    return frames


def line_frames(start: Vector, end: Vector, step: float = 0.25) -> list[Frame]:
    """Return the frames of a straight path from `start` to `end`."""
    forward = (end - start).normalized()
    right = forward.cross(UP).normalized()
    count = max(1, round((end - start).length / step))
    return [Frame(start.lerp(end, i / count), right, right.cross(forward), (end - start).length * i / count) for i in range(count + 1)]


def clear_runs(ring: list[Frame], mouths: list[tuple[Vector, float]]) -> list[list[Frame]]:
    """Split a closed ring of frames into the runs that stay clear of every mouth.

    A mouth is a point on the ring and a half-width: the place where a route
    joins a pad, which the pad's border must leave open.
    """
    blocked = [any((frame.origin - point).length < half for point, half in mouths) for frame in ring]
    first = blocked.index(True)
    runs: list[list[Frame]] = [[]]
    for frame, is_blocked in zip(ring[first:] + ring[:first], blocked[first:] + blocked[:first], strict=True):
        if is_blocked:
            runs.append([])
        else:
            runs[-1].append(frame)
    return [run for run in runs if len(run) >= 6]


def ring_frames(centre: Vector, radius: float, axis: Vector = UP, segments: int = 96) -> list[Frame]:
    """Return the frames of a closed circle around `axis`; frame.right points outward."""
    axis = axis.normalized()
    side = axis.orthogonal().normalized()
    other = axis.cross(side)
    frames: list[Frame] = []
    for index in range(segments):
        angle = 2 * math.pi * index / segments
        outward = side * math.cos(angle) + other * math.sin(angle)
        frames.append(Frame(centre + outward * radius, outward, axis, radius * angle))
    return frames


def circle_profile(radius: float, segments: int = 10) -> list[tuple[float, float]]:
    return [
        (radius * math.cos(2 * math.pi * i / segments), radius * math.sin(2 * math.pi * i / segments))
        for i in range(segments)
    ]


def rect_profile(x0: float, x1: float, z0: float, z1: float, bevel: float = 0.0) -> list[tuple[float, float]]:
    """Return a rectangle cross-section, with its four corners cut by `bevel`."""
    if bevel == 0.0:
        return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    b = bevel
    return [(x0 + b, z0), (x1 - b, z0), (x1, z0 + b), (x1, z1 - b), (x1 - b, z1), (x0 + b, z1), (x0, z1 - b), (x0, z0 + b)]  # fmt: skip


class Builder:
    """Collects geometry in one bmesh and turns it into one object with one material.

    Every `add_*` method appends geometry. Lengths are metres. Sweeps write UVs in
    metres (U along the path, V around the profile); `finish` scales them by 1/tile.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.verify()

    def add_sweep(self, frames: list[Frame], profile: list[tuple[float, float]], *, closed: bool = False) -> None:
        """Sweep a closed cross-section along the frames. `closed` joins the last frame to the first."""
        rings = [[self.bm.verts.new(frame.at(x, z)) for x, z in profile] for frame in frames]
        girth = [0.0]
        for (x0, z0), (x1, z1) in zip(profile, [*profile[1:], profile[0]], strict=True):
            girth.append(girth[-1] + math.hypot(x1 - x0, z1 - z0))
        pairs = list(zip(range(len(frames) - 1), range(1, len(frames)), strict=True))
        if closed:
            pairs.append((len(frames) - 1, 0))
        for a, b in pairs:
            u0 = frames[a].distance
            u1 = frames[b].distance if b else u0 + (frames[1].distance - frames[0].distance)
            for j in range(len(profile)):
                k = (j + 1) % len(profile)
                face = self.bm.faces.new((rings[a][j], rings[a][k], rings[b][k], rings[b][j]))
                for loop, uv in zip(face.loops, ((u0, girth[j]), (u0, girth[j + 1]), (u1, girth[j + 1]), (u1, girth[j])), strict=True):
                    loop[self.uv].uv = uv
        if not closed:
            for ring in (rings[0], rings[-1]):
                face = self.bm.faces.new(ring)
                for loop, uv in zip(face.loops, profile, strict=True):
                    loop[self.uv].uv = uv

    def add_cylinder(self, base: Vector, axis: Vector, height: float, radius: float, top_radius: float | None = None, segments: int = 32) -> None:
        """Add a capped cylinder or cone that stands on `base` and points along `axis`."""
        axis = axis.normalized()
        rotation = axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
        matrix = Matrix.Translation(base + axis * height / 2) @ rotation
        bmesh.ops.create_cone(
            self.bm, cap_ends=True, segments=segments, radius1=radius,
            radius2=radius if top_radius is None else top_radius, depth=height, matrix=matrix, calc_uvs=True,
        )  # fmt: skip

    def add_sphere(self, centre: Vector, radius: float, segments: int = 48) -> None:
        bmesh.ops.create_uvsphere(
            self.bm, u_segments=segments, v_segments=segments // 2, radius=radius,
            matrix=Matrix.Translation(centre), calc_uvs=True,
        )  # fmt: skip

    def add_box(self, matrix: Matrix, size: tuple[float, float, float]) -> None:
        """Add a box of `size` centred on `matrix`."""
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=matrix @ Matrix.Diagonal((*size, 1.0)), calc_uvs=True)

    def add_disc(self, centre: Vector, radius: float, thickness: float, segments: int = 128) -> None:
        """Add a flat stone disc whose top face is at `centre`, with UVs in metres."""
        start = len(self.bm.faces)
        self.add_cylinder(centre - UP * thickness, UP, thickness, radius, segments=segments)
        self.bm.faces.ensure_lookup_table()
        for face in self.bm.faces[start:]:
            flat = abs(face.normal.z) > 0.5
            for loop in face.loops:
                co = loop.vert.co
                angle = math.atan2(co.y - centre.y, co.x - centre.x)
                loop[self.uv].uv = (co.x, co.y) if flat else (radius * angle, co.z)

    def add_gem(self, centre: Vector, radius: float) -> None:
        """Add a small cut gem: a flat-topped crown above a pointed lower half."""
        self.add_cylinder(centre, UP, radius * 0.4, radius, radius * 0.55, segments=8)
        self.add_cylinder(centre - UP * radius * 0.9, UP, radius * 0.9, 0.0, radius, segments=8)

    def add_gear(self, matrix: Matrix, radius: float, teeth: int, thickness: float, bore: float) -> None:
        """Add a spur gear in the XY plane of `matrix`: `radius` is the tooth tip, `bore` the hole."""
        root = radius - 0.55 * (2 * math.pi * radius / teeth)
        outline: list[tuple[float, float]] = []
        for tooth in range(teeth):
            for fraction, r in ((0.0, root), (0.18, radius), (0.5, radius), (0.68, root)):
                angle = 2 * math.pi * (tooth + fraction) / teeth
                outline.append((r * math.cos(angle), r * math.sin(angle)))
        layers = []
        for z in (-thickness / 2, thickness / 2):
            outer = [self.bm.verts.new(matrix @ Vector((x, y, z))) for x, y in outline]
            inner = [self.bm.verts.new(matrix @ Vector((x * bore / math.hypot(x, y), y * bore / math.hypot(x, y), z))) for x, y in outline]
            layers.append((outer, inner))
        count = len(outline)
        (outer0, inner0), (outer1, inner1) = layers
        for i in range(count):
            j = (i + 1) % count
            self.bm.faces.new((outer0[i], outer0[j], inner0[j], inner0[i]))
            self.bm.faces.new((outer1[i], outer1[j], inner1[j], inner1[i]))
            self.bm.faces.new((outer0[i], outer0[j], outer1[j], outer1[i]))
            self.bm.faces.new((inner0[i], inner0[j], inner1[j], inner1[i]))

    def finish(self, material: bpy.types.Material, parent: bpy.types.Object, *, tile: float = 1.0, sharp_angle: float = 40.0) -> bpy.types.Object:
        """Create the object: fix normals, scale UVs to `tile` metres per repeat, shade smooth."""
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        for face in self.bm.faces:
            face.smooth = True
            for loop in face.loops:
                loop[self.uv].uv = loop[self.uv].uv / tile
        mesh = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        mesh.set_sharp_from_angle(angle=math.radians(sharp_angle))
        mesh.materials.append(material)
        obj = bpy.data.objects.new(self.name, mesh)
        obj.parent = parent
        bpy.context.scene.collection.objects.link(obj)
        return obj


def new_material(name: str) -> tuple[bpy.types.Material, bpy.types.NodeTree, bpy.types.Node]:
    """Return a material with an empty node tree and its output node."""
    material = bpy.data.materials.new(name)
    tree = material.node_tree
    tree.nodes.clear()
    return material, tree, tree.nodes.new("ShaderNodeOutputMaterial")


def node(tree: bpy.types.NodeTree, kind: str, /, **settings: object) -> bpy.types.Node:
    """Add a node. A keyword that names a node property sets it; any other sets that input socket.

    Write a socket name with `_` for a space ("From_Min"). A socket value can be a
    constant or another node's output socket, which is then linked.
    """
    new = tree.nodes.new(kind)
    for key, value in settings.items():
        if hasattr(new, key):
            setattr(new, key, value)
        elif isinstance(value, bpy.types.NodeSocket):
            tree.links.new(value, new.inputs[key.replace("_", " ")])
        else:
            new.inputs[key.replace("_", " ")].default_value = value
    return new


def load_image(path: Path, *, data: bool) -> bpy.types.Image:
    image = bpy.data.images.load(str(path), check_existing=True)
    if data:
        image.colorspace_settings.name = "Non-Color"
    return image


def stone_material(candidate: Candidate) -> bpy.types.Material:
    """Return a PBR stone from an ambientCG texture set (colour, roughness, OpenGL normal), UV-mapped."""
    material, tree, output = new_material(f"stone_{candidate.stone}")

    def texture(suffix: str, *, data: bool) -> bpy.types.NodeSocket:
        path = STONE_DIR / f"{candidate.stone}_2K-JPG_{suffix}.jpg"
        return node(tree, "ShaderNodeTexImage", image=load_image(path, data=data)).outputs["Color"]

    tint = node(tree, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY", Factor=1.0, A=texture("Color", data=False), B=(*candidate.stone_tint, 1.0))  # fmt: skip
    roughness = node(tree, "ShaderNodeMath", operation="ADD")
    tree.links.new(texture("Roughness", data=True), roughness.inputs[0])
    roughness.inputs[1].default_value = candidate.stone_roughness
    normal = node(tree, "ShaderNodeNormalMap", Color=texture("NormalGL", data=True))
    shader = node(tree, "ShaderNodeBsdfPrincipled", Base_Color=tint.outputs["Result"], Roughness=roughness.outputs["Value"], Normal=normal.outputs["Normal"])  # fmt: skip
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def metal_material(name: str, color: Color, roughness: float, *, tarnish: float = 0.0) -> bpy.types.Material:
    """Return a procedural metal. `tarnish` (0..1) adds darker, duller patches, like aged brass."""
    material, tree, output = new_material(name)
    coords = node(tree, "ShaderNodeTexCoord")
    noise = node(tree, "ShaderNodeTexNoise", Vector=coords.outputs["Object"], Scale=9.0, Detail=8.0, Roughness=0.65)
    patches = node(tree, "ShaderNodeMapRange", Value=noise.outputs["Factor"], From_Min=0.4, From_Max=0.68, To_Min=0.0, To_Max=tarnish)  # fmt: skip
    dull = tuple(channel * factor for channel, factor in zip(color, (0.42, 0.40, 0.36), strict=True))
    aged = node(tree, "ShaderNodeMix", data_type="RGBA", Factor=patches.outputs["Result"], A=(*color, 1.0), B=(*dull, 1.0))
    spread = node(tree, "ShaderNodeMapRange", Value=noise.outputs["Factor"], From_Min=0.3, From_Max=0.7, To_Min=roughness * 0.7, To_Max=roughness * (1.4 + tarnish))  # fmt: skip
    shader = node(tree, "ShaderNodeBsdfPrincipled", Base_Color=aged.outputs["Result"], Metallic=1.0, Roughness=spread.outputs["Result"])  # fmt: skip
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def glass_material(name: str) -> bpy.types.Material:
    material, tree, output = new_material(name)
    shader = node(tree, "ShaderNodeBsdfPrincipled", Roughness=0.0, IOR=1.5, Transmission_Weight=1.0)
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def gem_material(name: str, color: Color) -> bpy.types.Material:
    """Return a cut gem: deep colour under a hard polish, so that it reads from far away."""
    material, tree, output = new_material(name)
    shader = node(tree, "ShaderNodeBsdfPrincipled", Base_Color=(*color, 1.0), Roughness=0.03, IOR=1.7, Transmission_Weight=0.3, Coat_Weight=1.0)  # fmt: skip
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def marble_stone_material() -> bpy.types.Material:
    """Return the polished blue-black stone of marble look B (box-projected, so it has no seam)."""
    material, tree, output = new_material("marble_stone")
    coords = node(tree, "ShaderNodeTexCoord")
    mapping = node(tree, "ShaderNodeMapping", Vector=coords.outputs["Object"], Scale=(1.4, 1.4, 1.4))
    image = node(tree, "ShaderNodeTexImage", image=load_image(STONE_DIR / "Marble023_2K-JPG_Color.jpg", data=False), projection="BOX", projection_blend=0.25, Vector=mapping.outputs["Vector"])  # fmt: skip
    tint = node(tree, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY", Factor=1.0, A=image.outputs["Color"], B=(0.45, 0.62, 1.0, 1.0))  # fmt: skip
    shader = node(tree, "ShaderNodeBsdfPrincipled", Base_Color=tint.outputs["Result"], Roughness=0.06, Coat_Weight=1.0, Coat_Roughness=0.02)  # fmt: skip
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def blob_shadow_material() -> bpy.types.Material:
    """Return the blob shadow: a dark disc with a crisp edge, see-through outside it."""
    material, tree, output = new_material("blob_shadow")
    coords = node(tree, "ShaderNodeTexCoord")
    length = node(tree, "ShaderNodeVectorMath", operation="LENGTH")
    tree.links.new(coords.outputs["Object"], length.inputs[0])
    edge = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=length.outputs["Value"], From_Min=0.8, From_Max=1.0, To_Min=0.62, To_Max=0.0)  # fmt: skip
    clear = node(tree, "ShaderNodeBsdfTransparent")
    dark = node(tree, "ShaderNodeBsdfDiffuse", Color=(0.0, 0.0, 0.0, 1.0))
    mix = node(tree, "ShaderNodeMixShader", Factor=edge.outputs["Result"])
    tree.links.new(clear.outputs["BSDF"], mix.inputs[1])
    tree.links.new(dark.outputs["BSDF"], mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], output.inputs["Surface"])
    return material


def cloud_material(top: float, depth: float) -> bpy.types.Material:
    """Return the cloud-sea volume: noise that thins out toward `top` (world Z, metres)."""
    material, tree, output = new_material("cloud_sea")
    position = node(tree, "ShaderNodeNewGeometry").outputs["Position"]
    noise = node(tree, "ShaderNodeTexNoise", Vector=position, Scale=0.011, Detail=7.0, Roughness=0.58)
    split = node(tree, "ShaderNodeSeparateXYZ", Vector=position)
    # The cover threshold rises with height, so only the strongest noise reaches the top: cloud heaps.
    threshold = node(tree, "ShaderNodeMapRange", Value=split.outputs["Z"], From_Min=top - depth, From_Max=top, To_Min=0.36, To_Max=0.72)  # fmt: skip
    cover = node(tree, "ShaderNodeMath", operation="SUBTRACT")
    tree.links.new(noise.outputs["Factor"], cover.inputs[0])
    tree.links.new(threshold.outputs["Result"], cover.inputs[1])
    density = node(tree, "ShaderNodeMapRange", Value=cover.outputs["Value"], From_Min=0.0, From_Max=0.08, To_Min=0.0, To_Max=0.22)  # fmt: skip
    volume = node(tree, "ShaderNodeVolumePrincipled", Color=(1.0, 1.0, 1.0, 1.0), Anisotropy=0.35, Density=density.outputs["Result"])
    tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return material


def add_pad(stone: Builder, trim: Builder, centre: Vector, radius: float, teeth: int, mouths: list[tuple[Vector, float]]) -> None:
    """Add a round stone pad on a large gear, with a low brass border that is open at each mouth."""
    stone.add_disc(centre - UP * 0.002, radius, DECK_THICKNESS)
    for run in clear_runs(ring_frames(centre, radius, segments=192), mouths):
        trim.add_sweep(run, rect_profile(-0.07, 0.03, -0.09, 0.055, bevel=0.015))
    trim.add_gear(Matrix.Translation(centre - UP * (DECK_THICKNESS + 0.07)), radius + 0.33, teeth, 0.12, radius - 0.5)


def build_course(candidate: Candidate, root: bpy.types.Object) -> None:
    """Build the play space: a plaza, then a fork of two routes that climb to a goal pad.

    The wide route is a banked curve with low brass borders. The shortcut is a
    narrow straight beam with no border. Gems hover over both.
    """
    frames = deck_frames()
    metal = metal_material("metal", candidate.metal_color, candidate.metal_roughness, tarnish=0.55)
    half = DECK_WIDTH / 2
    plaza = Vector((0.0, 0.0, 0.0))
    goal = frames[-1].origin + frames[-1].forward * (GOAL_RADIUS - 0.15)
    toward_goal = Vector((goal.x, goal.y, 0.0)).normalized()
    beam = line_frames(toward_goal * (PLAZA_RADIUS - 0.1), goal - toward_goal * (GOAL_RADIUS - 0.1))
    plaza_mouths = [(Vector((DECK_START.x, math.sqrt(PLAZA_RADIUS**2 - DECK_START.x**2), 0.0)), half), (toward_goal * PLAZA_RADIUS, BEAM_WIDTH / 2 + 0.06)]  # fmt: skip
    goal_mouths = [(goal - frames[-1].forward * GOAL_RADIUS, half), (goal - toward_goal * GOAL_RADIUS, BEAM_WIDTH / 2 + 0.06)]

    stone = Builder("stone")
    trim = Builder("metal_parts")
    add_pad(stone, trim, plaza, PLAZA_RADIUS, 72, plaza_mouths)
    add_pad(stone, trim, goal, GOAL_RADIUS, 44, goal_mouths)
    stone.add_sweep(frames, rect_profile(-half, half, -DECK_THICKNESS, 0.0, bevel=0.025))
    stone.add_sweep(beam, rect_profile(-BEAM_WIDTH / 2, BEAM_WIDTH / 2, -0.16, 0.0, bevel=0.02))
    stone.finish(stone_material(candidate), root, tile=candidate.stone_tile)

    # The wide route: a low border on each edge, a band on each side face, two inlaid lines.
    for side in (-1, 1):
        edge = side * (half - 0.05)
        trim.add_sweep(frames, [(edge + x, z) for x, z in rect_profile(-0.045, 0.045, -0.01, 0.055, bevel=0.015)])
        trim.add_sweep(frames, [(side * half + x, z) for x, z in rect_profile(-0.012, 0.012, -0.13, -0.07)])
        trim.add_sweep(frames, [(side * 0.8 + x, z) for x, z in rect_profile(-0.018, 0.018, -0.01, 0.003)])
        trim.add_sweep(beam, [(side * (BEAM_WIDTH / 2 - 0.03) + x, z) for x, z in rect_profile(-0.015, 0.015, -0.01, 0.003)])
    # Scale marks between each inlaid line and the border, like the marks on a dial: a long one every metre.
    for index, frame in enumerate(frames[5:-2:5]):
        length = 0.26 if index % 2 == 0 else 0.13
        for side in (-1, 1):
            trim.add_box(frame.matrix(side * (half - 0.11 - length / 2), 0.0015), (length, 0.022, 0.003))
    # Under the routes: a keel, ribs that reach out to the edges, and gears whose teeth show past the edges.
    trim.add_sweep(frames, rect_profile(-0.09, 0.09, -DECK_THICKNESS - 0.16, -DECK_THICKNESS + 0.01, bevel=0.03))
    trim.add_sweep(beam, rect_profile(-0.06, 0.06, -0.28, -0.15, bevel=0.02))
    for frame in frames[8:-2:12]:
        trim.add_box(frame.matrix(0.0, -DECK_THICKNESS - 0.04), (DECK_WIDTH - 0.1, 0.07, 0.08))
    for frame in (frames[44], frames[88]):
        trim.add_gear(frame.matrix(0.0, -DECK_THICKNESS - 0.14), half + 0.36, 36, 0.1, half - 0.25)
    # The plaza floor is a clock dial: two inlaid rings, twelve hour marks and a hub.
    for radius in (0.42, PLAZA_RADIUS - 0.5):
        trim.add_sweep(ring_frames(plaza, radius, segments=192), rect_profile(-0.016, 0.016, -0.01, 0.001), closed=True)
    for hour in range(12):
        length = 0.42 if hour % 3 == 0 else 0.24
        spin = Matrix.Rotation(2 * math.pi * hour / 12, 4, "Z")
        mark = spin @ Vector((PLAZA_RADIUS - 0.16 - length / 2, 0.0, 0.0))
        if all((mark - point).length > reach + length for point, reach in plaza_mouths):
            trim.add_box(spin @ Matrix.Translation((PLAZA_RADIUS - 0.16 - length / 2, 0.0, 0.0)), (length, 0.04, 0.002))
    trim.add_cylinder(Vector((0.0, 0.0, -0.01)), UP, 0.012, 0.13, segments=48)
    # Marker posts with a clear glass globe: a pair at the start of the wide route, then along the outside of the turn.
    glass = Builder("post_glass")
    for index, side in ((4, -1), (4, 1), (50, -1), (92, -1)):
        foot = frames[index].at(side * (half - 0.05), 0.05)
        trim.add_cylinder(foot, UP, 0.05, 0.07, 0.035)
        trim.add_cylinder(foot, UP, 0.36, 0.022)
        trim.add_cylinder(foot + UP * 0.34, UP, 0.045, 0.028, 0.065)
        globe = foot + UP * 0.47
        glass.add_sphere(globe, 0.1)
        trim.add_sweep(ring_frames(globe, 0.103, segments=48), circle_profile(0.007, 8), closed=True)
        trim.add_cylinder(globe + UP * 0.092, UP, 0.055, 0.055, 0.0)
    trim.finish(metal, root)
    glass.finish(glass_material("post_glass"), root)

    # Gems hover over the plaza, both routes and the goal.
    spots = [Vector((-1.7, -0.5, 0.0)), Vector((1.6, -1.3, 0.0)), frames[32].origin, frames[72].origin, beam[len(beam) // 2].origin, goal]  # fmt: skip
    for index, (name, tint) in enumerate((("ruby", (0.8, 0.03, 0.06)), ("sapphire", (0.04, 0.2, 0.9)), ("emerald", (0.02, 0.6, 0.2)))):
        gems = Builder(f"gem_{name}")
        for spot in spots[index::3]:
            gems.add_gem(spot + UP * 0.34, GEM_RADIUS)
        gems.finish(gem_material(f"gem_{name}", tint), root)


def build_marble(look: MarbleLook, root: bpy.types.Object) -> None:
    """Build the marble in mid-hop above the plaza, and its blob shadow straight below it."""
    centre = MARBLE_AT + UP * (MARBLE_RADIUS + MARBLE_HOP)
    tilts = (Vector((0.35, 0.2, 1.0)), Vector((1.0, 0.3, 0.45)), Vector((-0.4, 1.0, 0.3)))
    shell = Builder("marble")
    shell.add_sphere(centre, MARBLE_RADIUS, segments=96)
    detail = Builder("marble_detail")
    if look == "glass":
        # Clear glass around a small brass orrery: a ball, three rings and three planets.
        shell.finish(glass_material("marble_glass"), root)
        detail.add_sphere(centre, 0.055, segments=32)
        for index, (axis, radius) in enumerate(zip(tilts, (0.095, 0.122, 0.15), strict=True)):
            ring = ring_frames(centre, radius, axis, segments=64)
            detail.add_sweep(ring, circle_profile(0.0065, 8), closed=True)
            detail.add_sphere(ring[index * 23 % 64].origin, 0.016, segments=16)
        detail.finish(metal_material("marble_core", BRASS, 0.16), root)
    else:
        # Polished blue-black stone with three gold orbit lines and gold dots set into the surface.
        shell.finish(marble_stone_material(), root)
        for index, axis in enumerate(tilts):
            ring = ring_frames(centre, MARBLE_RADIUS - 0.001, axis, segments=96)
            detail.add_sweep(ring, circle_profile(0.0045, 8), closed=True)
            for step in (index * 31 % 96, (index * 31 + 40) % 96):
                detail.add_sphere(ring[step].origin, 0.012, segments=16)
        detail.finish(metal_material("marble_gold", GOLD, 0.12), root)

    blob = Builder("blob_shadow")
    bmesh.ops.create_circle(blob.bm, cap_ends=True, segments=64, radius=1.0)
    shadow = blob.finish(blob_shadow_material(), root)
    shadow.location = MARBLE_AT + UP * 0.004
    shadow.scale = (MARBLE_RADIUS * 1.05,) * 3
    shadow.visible_shadow = False


def build_cloud_sea(root: bpy.types.Object) -> None:
    """Build the sea of clouds far below the course as one large volume."""
    top, depth, half_size = -22.0, 45.0, 20000.0
    box = Builder("cloud_sea")
    box.add_box(Matrix.Translation((0.0, 0.0, top - depth / 2)), (2 * half_size, 2 * half_size, depth))
    box.finish(cloud_material(top, depth), root)


def sky_sun_azimuth(image: bpy.types.Image) -> float:
    """Return the azimuth (degrees, world) of the brightest spot of an equirectangular sky."""
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    luminance = pixels.reshape(height, width, 4)[..., :3] @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    _, columns = np.nonzero(luminance >= np.quantile(luminance, 0.9997))
    u = (float(np.median(columns)) + 0.5) / width
    return (0.5 - u) * 360.0  # Cycles maps a direction to u = 0.5 - atan2(y, x) / 2pi


def build_light(candidate: Candidate) -> Vector:
    """Set the sky and the sun lamp. Return the world direction to the sun.

    The sky is a photographed Earth sky. The sun lamp stands at the azimuth of
    the sky file's own sun, at the candidate's elevation.
    """
    scene = bpy.context.scene
    world = bpy.data.worlds.new("sky")
    tree = world.node_tree
    tree.nodes.clear()
    image = load_image(SKY_DIR / f"{candidate.sky}_2k.hdr", data=False)
    sky = node(tree, "ShaderNodeTexEnvironment", image=image)
    capped = node(tree, "ShaderNodeVectorMath", operation="MINIMUM")
    tree.links.new(sky.outputs["Color"], capped.inputs[0])
    capped.inputs[1].default_value = (SKY_CAP,) * 3
    background = node(tree, "ShaderNodeBackground", Color=capped.outputs["Vector"], Strength=candidate.sky_strength)
    output = tree.nodes.new("ShaderNodeOutputWorld")
    tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    scene.world = world

    to_sun = direction(sky_sun_azimuth(image), candidate.sun_elevation)
    light = bpy.data.lights.new("sun", "SUN")
    light.energy = candidate.sun_strength
    light.color = candidate.sun_color
    light.angle = math.radians(1.2)
    sun = bpy.data.objects.new("sun", light)
    sun.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(sun)
    return to_sun


def build_camera(root: bpy.types.Object) -> None:
    """Place the camera high behind the plaza, looking down the course."""
    scene = bpy.context.scene
    data = bpy.data.cameras.new("camera")
    data.lens = 24.0
    data.sensor_width = 36.0
    data.clip_end = 500000.0
    camera = bpy.data.objects.new("camera", data)
    camera.location = CAMERA_AT
    camera.rotation_euler = (CAMERA_TARGET - CAMERA_AT).to_track_quat("-Z", "Y").to_euler()
    camera.parent = root
    scene.collection.objects.link(camera)
    scene.camera = camera


def configure_render(samples: int, scale: int, use_gpu: bool) -> None:
    """Set Cycles (OptiX on the GPU, or the CPU), 1920x1080, AgX, WebP output."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    if use_gpu:
        preferences = bpy.context.preferences.addons["cycles"].preferences
        preferences.compute_device_type = "OPTIX"
        preferences.get_devices()
        for device in preferences.devices:
            device.use = device.type == "OPTIX"
        scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 12
    scene.cycles.glossy_bounces = 8
    scene.cycles.volume_bounces = 5
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = scale
    scene.render.image_settings.file_format = "WEBP"
    scene.render.image_settings.quality = 90
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def render_candidate(candidate: Candidate, out: Path, samples: int, scale: int, use_gpu: bool) -> Path:
    """Build the whole scene for one candidate from an empty file and render it."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    to_sun = build_light(candidate)
    # The scene turns as one piece, so that its sun direction (SUN_AZIMUTH) meets the sky's sun.
    root = bpy.data.objects.new("root", None)
    root.rotation_euler.z = math.atan2(to_sun.y, to_sun.x) - math.radians(SUN_AZIMUTH)
    scene.collection.objects.link(root)
    build_course(candidate, root)
    build_marble(candidate.marble, root)
    build_cloud_sea(root)
    build_camera(root)
    configure_render(samples, scale, use_gpu)
    scene.view_settings.exposure = candidate.exposure
    path = out / f"render-{candidate.name.lower()}.webp"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", choices=[c.name for c in CANDIDATES], help="candidates to render (default: all)")
    parser.add_argument("--out", type=Path, default=REPO / "docs" / "style" / "review")
    parser.add_argument("--samples", type=int, default=384)
    parser.add_argument("--scale", type=int, default=100, help="resolution in percent, for quick previews")
    parser.add_argument("--cpu", action="store_true", help="render on the CPU, for when ComfyUI holds the GPU memory")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    args.out.mkdir(parents=True, exist_ok=True)
    for candidate in CANDIDATES:
        if args.only is None or candidate.name in args.only:
            path = render_candidate(candidate, args.out.resolve(), args.samples, args.scale, not args.cpu)
            print(f"lookdev: wrote {path}")


if __name__ == "__main__":
    main()
