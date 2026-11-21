"""Builds the brass orrery core of the glass marble and exports it as a .glb.

`just build-marble` runs it; to run it by hand:

    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 \
        --python tools/blender/marble_core.py -- <out.glb>

The core is the inside of marble A of the style board (docs/style/README.md): a ball, three
tilted rings and one planet on each ring, in polished brass. Lengths are metres. The origin
is the centre of the marble, whose radius is 0.2.

The sizes are the sizes that the eye sees in the look-dev render (`build_marble` in
tools/blender/lookdev.py). There, solid glass with an index of refraction of 1.65 magnifies
the parts near the centre. The game's glass does not magnify the core, so this mesh carries
the magnified sizes.

The material is plain PBR, so Godot imports it as a StandardMaterial3D: the colour map of
ambientCG Metal048A (assets/textures/metal/, docs/licenses.md) with a tint, one roughness
and a metallic value of 1. The .glb holds the map.
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

TEXTURES = Path(__file__).resolve().parents[2] / "assets" / "textures" / "metal"
TILE = 0.2  # metres covered by one texture repeat
# The colour map is a pale gold (sRGB 254, 227, 157). The tint makes it polished brass by
# the material rules of docs/design/visual-quality.md §6.
TINT = (0.9, 0.76, 0.5)  # linear; multiplies the colour map
# The roughness map is flat: 0.09, give or take 0.004. glTF has no roughness factor above 1 to
# scale it with, so the brass has one roughness: the map's mean × 2.4.
ROUGHNESS = 0.22
BALL_RADIUS = 0.105
PLANET_RADIUS = 0.024
TUBE_RADIUS = 0.012
# One ring per row: its axis, its radius and where its planet sits on it, in degrees.
RINGS = (
    (Vector((0.35, 0.2, 1.0)), 0.128, 0.0),
    (Vector((1.0, 0.3, 0.45)), 0.148, 130.0),
    (Vector((-0.4, 1.0, 0.3)), 0.168, 260.0),
)


def add_sphere(
    bm: bmesh.types.BMesh, centre: Vector, radius: float, segments: int
) -> None:
    """Adds a sphere. Its UVs repeat the texture each TILE metres along the equator."""
    uv = bm.loops.layers.uv.verify()
    made = bmesh.ops.create_uvsphere(
        bm,
        u_segments=segments,
        v_segments=segments // 2,
        radius=radius,
        matrix=Matrix.Translation(centre),
        calc_uvs=True,
    )
    repeats = Vector((2 * math.pi * radius / TILE, math.pi * radius / TILE))
    for face in {face for vert in made["verts"] for face in vert.link_faces}:
        for loop in face.loops:
            loop[uv].uv *= repeats


def add_ring(
    bm: bmesh.types.BMesh, turn: Matrix, radius: float, segments: int, sides: int
) -> None:
    """Adds a ring around the origin: a tube of TUBE_RADIUS along a circle of `radius` in the
    XY plane, turned by `turn`. Its UVs repeat the texture each TILE metres along the ring."""
    uv = bm.loops.layers.uv.verify()
    rows = []
    for i in range(segments):
        along = 2 * math.pi * i / segments
        outward = Vector((math.cos(along), math.sin(along), 0.0))
        row = []
        for j in range(sides):
            around = 2 * math.pi * j / sides
            reach = radius + TUBE_RADIUS * math.cos(around)
            height = Vector((0.0, 0.0, TUBE_RADIUS * math.sin(around)))
            row.append(bm.verts.new(turn @ (outward * reach + height)))
        rows.append(row)
    length = 2 * math.pi * radius / TILE
    girth = 2 * math.pi * TUBE_RADIUS / TILE
    for i in range(segments):
        for j in range(sides):
            a, b = rows[i], rows[(i + 1) % segments]
            k = (j + 1) % sides
            face = bm.faces.new((a[j], b[j], b[k], a[k]))
            u0, u1 = length * i / segments, length * (i + 1) / segments
            v0, v1 = girth * j / sides, girth * (j + 1) / sides
            corners = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
            for loop, corner in zip(face.loops, corners, strict=True):
                loop[uv].uv = corner


def brass() -> bpy.types.Material:
    """Returns the polished brass: the Metal048A colour map × TINT, ROUGHNESS and metallic 1."""
    material = bpy.data.materials.new("brass")
    material.use_backface_culling = True
    tree = material.node_tree
    tree.nodes.clear()
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(TEXTURES / "Metal048A_2K-JPG_Color.jpg"))
    # The glTF exporter writes a multiply with a constant as a factor of the map.
    colour = tree.nodes.new("ShaderNodeMix")
    colour.data_type = "RGBA"
    colour.blend_type = "MULTIPLY"
    colour.inputs["Factor"].default_value = 1.0
    tree.links.new(texture.outputs["Color"], colour.inputs["A"])
    colour.inputs["B"].default_value = (*TINT, 1.0)
    shader = tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = ROUGHNESS
    tree.links.new(colour.outputs["Result"], shader.inputs["Base Color"])
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def main() -> None:
    """Builds the core as one object, `core`, and writes the .glb given after `--`."""
    out = Path(sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    add_sphere(bm, Vector(), BALL_RADIUS, segments=64)
    for axis, radius, planet_at in RINGS:
        turn = Vector((0.0, 0.0, 1.0)).rotation_difference(axis).to_matrix()
        add_ring(bm, turn, radius, segments=96, sides=12)
        at = math.radians(planet_at)
        planet = turn @ Vector((math.cos(at), math.sin(at), 0.0)) * radius
        add_sphere(bm, planet, PLANET_RADIUS, segments=24)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for face in bm.faces:
        face.smooth = True
    mesh = bpy.data.meshes.new("core")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(brass())
    bpy.context.scene.collection.objects.link(bpy.data.objects.new("core", mesh))
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )


main()
