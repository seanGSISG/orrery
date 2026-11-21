"""Bakes the tier skies into game/skies/<name>.hdr: the backdrop that the game shows.

Usage: `just bake-skies [name ...]` bakes dawn, noon and dusk (all when no name is given).
`--look b` or `--look c` bakes the dawn of another look candidate (docs/design/visual-quality.md
§10). `--scale 25` makes a quick preview in build/skies/, so it does not replace a game sky.

Each sky is one equirectangular image, 4096x2048, scene-linear Radiance HDR, path-traced with
Cycles on the GPU. The game's SkyPreset (game/skies/<name>.tres) shows it and adds the sun as a
DirectionalLight3D, so the image holds no full-strength sun: the sun disc is cut down to SUN_CAP.

- dawn (Beginner): a photographed Earth sky (Poly Haven, CC0) over a sea of clouds. No planets.
- noon (Intermediate): Blender's physical sky seen from 16 km, with a cloud layer far below.
- dusk (Advanced): the same sky model from 80 km: the curve of the Earth, faint stars and one
  pale planet (NASA's Cassini map of Jupiter, public domain) low in the haze.

Axes: the image centre looks along Blender -y, which is Godot +z, and the sun stands at
SUN_AZIMUTH. The script prints where the sun is in each image; SkyPreset.sun_azimuth and
sun_elevation must match it.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "assets" / "textures"
OUT = ROOT / "game" / "skies"
PREVIEWS = ROOT / "build" / "skies"  # where a bake below full size goes
WIDTH, HEIGHT = 4096, 2048
SUN_AZIMUTH = 135.0  # degrees, counter-clockwise from +x seen from above: ahead of the start, on its left
SUN_CAP = 16.0  # the brightest radiance a sky pixel keeps; the game's sun light replaces the rest
EARTH_RADIUS = 6371.0  # km

Color = tuple[float, float, float]


@dataclass(frozen=True, kw_only=True)
class HdriSky:
    """A photographed sky over a sea of clouds, with a sun lamp that lights the clouds."""

    file: str  # Poly Haven asset id under assets/textures/sky
    strength: float
    sun_elevation: float  # degrees; the lamp
    sun_color: Color
    sun_strength: float  # W/m2


@dataclass(frozen=True, kw_only=True)
class PhysicalSky:
    """Blender's physical sky from high up, with a cloud layer far below.

    `stars` and `planet` are for the edge of space.
    """

    altitude: float  # metres above sea level
    sun_elevation: float  # degrees; drives the colours of the sky model
    strength: float
    cloud_drop: float  # km from the camera down to the cloud tops
    cloud_color: Color  # radiance of a sunlit cloud top
    sun_disc: bool = False
    stars: float = 0.0  # radiance of the brightest stars
    planet: float = 0.0  # radiance of the planet's sunlit side; 0 is no planet
    # Added to every direction, so that space is not pure black.
    airglow: Color = (0.0, 0.0, 0.0)


Sky = HdriSky | PhysicalSky

# The dawn of each look candidate (the style board, #5). `a` is the provisional choice.
DAWNS: dict[str, HdriSky] = {
    "a": HdriSky(file="syferfontein_6d_clear_puresky", strength=0.8, sun_elevation=12.0, sun_color=(1.0, 0.68, 0.42), sun_strength=24.0),
    "b": HdriSky(file="qwantani_dusk_2_puresky", strength=0.9, sun_elevation=8.0, sun_color=(1.0, 0.6, 0.46), sun_strength=14.0),
    "c": HdriSky(file="syferfontein_1d_clear_puresky", strength=1.6, sun_elevation=4.5, sun_color=(1.0, 0.56, 0.3), sun_strength=18.0),
}  # fmt: skip
NOON = PhysicalSky(altitude=16000.0, sun_elevation=58.0, strength=0.2, cloud_drop=7.0, cloud_color=(5.6, 5.6, 5.7), sun_disc=True)  # fmt: skip
DUSK = PhysicalSky(altitude=80000.0, sun_elevation=-5.5, strength=0.6, cloud_drop=70.0, cloud_color=(0.035, 0.05, 0.085), stars=4.0, planet=1.45, airglow=(0.0025, 0.0035, 0.006))  # fmt: skip


def direction(azimuth: float, elevation: float) -> Vector:
    """Returns the unit vector at an azimuth and an elevation in degrees."""
    a, e = math.radians(azimuth), math.radians(elevation)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def node(tree: bpy.types.NodeTree, kind: str, /, **settings: object) -> bpy.types.Node:
    """Adds a node. A keyword that names a node property sets it; any other sets that input
    socket (write `_` for a space). A socket value can be a constant or an output socket."""
    new = tree.nodes.new(kind)
    for key, value in settings.items():
        if hasattr(new, key):
            setattr(new, key, value)
        elif isinstance(value, bpy.types.NodeSocket):
            tree.links.new(value, new.inputs[key.replace("_", " ")])
        else:
            new.inputs[key.replace("_", " ")].default_value = value
    return new


def math_node(
    tree: bpy.types.NodeTree, operation: str, *values: object
) -> bpy.types.NodeSocket:
    """Adds a Math node on constants or sockets and returns its result socket."""
    new = tree.nodes.new("ShaderNodeMath")
    new.operation = operation
    for index, value in enumerate(values):
        if isinstance(value, bpy.types.NodeSocket):
            tree.links.new(value, new.inputs[index])
        else:
            new.inputs[index].default_value = value
    return new.outputs["Value"]


def capped(
    tree: bpy.types.NodeTree, color: bpy.types.NodeSocket, cap: float
) -> bpy.types.NodeSocket:
    """Returns color with each channel cut down to cap."""
    limit = node(tree, "ShaderNodeVectorMath", operation="MINIMUM")
    tree.links.new(color, limit.inputs[0])
    limit.inputs[1].default_value = (cap, cap, cap)
    return limit.outputs["Vector"]


def new_world() -> bpy.types.NodeTree:
    """Makes an empty world for the scene and returns its node tree."""
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.node_tree.nodes.clear()
    return world.node_tree


def finish_world(tree: bpy.types.NodeTree, color: bpy.types.NodeSocket) -> None:
    """Connects color to the world output as the background."""
    background = node(tree, "ShaderNodeBackground", Color=color, Strength=1.0)
    tree.links.new(
        background.outputs["Background"],
        tree.nodes.new("ShaderNodeOutputWorld").inputs["Surface"],
    )


def image_sun(pixels: np.ndarray) -> tuple[float, float]:
    """Returns (u, v) of the brightest spot of an equirectangular image, v from the bottom."""
    luminance = pixels[..., :3] @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    rows, columns = np.nonzero(luminance >= np.quantile(luminance, 0.9997))
    height, width = luminance.shape
    return (float(np.median(columns)) + 0.5) / width, (
        float(np.median(rows)) + 0.5
    ) / height


def image_pixels(image: bpy.types.Image) -> np.ndarray:
    """Returns the pixels of an image as rows from the bottom, RGBA floats."""
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape(height, width, 4)


def build_hdri(sky: HdriSky) -> float:
    """Builds the photographed sky, its sun lamp and the cloud sea. Returns the azimuth of the sun."""
    tree = new_world()
    image = bpy.data.images.load(str(SOURCES / "sky" / f"{sky.file}_2k.hdr"))
    picture = node(tree, "ShaderNodeTexEnvironment", image=image)
    scaled = node(tree, "ShaderNodeVectorMath", operation="SCALE", Scale=sky.strength)
    tree.links.new(capped(tree, picture.outputs["Color"], SUN_CAP), scaled.inputs[0])
    finish_world(tree, scaled.outputs["Vector"])
    u, _ = image_sun(image_pixels(image))
    azimuth = (
        0.5 - u
    ) * 360.0  # Cycles maps a direction to u = 0.5 - atan2(y, x) / 2pi
    add_sun(direction(azimuth, sky.sun_elevation), sky.sun_color, sky.sun_strength)
    add_cloud_sea()
    return azimuth


def add_sun(to_sun: Vector, color: Color, strength: float) -> None:
    """Adds the sun lamp. It lights the clouds; the camera does not see it."""
    light = bpy.data.lights.new("sun", "SUN")
    light.energy = strength
    light.color = color
    light.angle = math.radians(1.0)
    sun = bpy.data.objects.new("sun", light)
    sun.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
    sun.visible_camera = False
    bpy.context.scene.collection.objects.link(sun)


def add_cloud_sea() -> None:
    """Adds the sea of clouds below the level as one large volume: noise that thins out toward its top."""
    top, depth, half_size = -50.0, 100.0, 8000.0
    # Cycles splits a volume at the middle of its box, and a split can show as a faint line in
    # the clouds. The box is off-centre, so that no split runs through the view straight down.
    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(1900.0, 2600.0, top - depth / 2)
    )
    box = bpy.context.object
    box.scale = (2 * half_size, 2 * half_size, depth)
    material = bpy.data.materials.new("cloud_sea")
    tree = material.node_tree
    tree.nodes.clear()
    position = node(tree, "ShaderNodeNewGeometry").outputs["Position"]
    noise = node(
        tree,
        "ShaderNodeTexNoise",
        Vector=position,
        Scale=0.0045,
        Detail=6.0,
        Roughness=0.55,
    )
    split = node(tree, "ShaderNodeSeparateXYZ", Vector=position)
    # The cover threshold rises with height, so only the strongest noise reaches the top: cloud heaps.
    threshold = node(tree, "ShaderNodeMapRange", Value=split.outputs["Z"], From_Min=top - 40.0, From_Max=top, To_Min=0.3, To_Max=0.6)  # fmt: skip
    cover = math_node(
        tree, "SUBTRACT", noise.outputs["Factor"], threshold.outputs["Result"]
    )
    density = node(
        tree,
        "ShaderNodeMapRange",
        Value=cover,
        From_Min=0.0,
        From_Max=0.08,
        To_Min=0.0,
        To_Max=0.3,
    )
    volume = node(tree, "ShaderNodeVolumePrincipled", Color=(1.0, 1.0, 1.0, 1.0), Anisotropy=0.35, Density=density.outputs["Result"])  # fmt: skip
    tree.links.new(
        volume.outputs["Volume"],
        tree.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"],
    )
    box.data.materials.append(material)


def build_physical(sky: PhysicalSky) -> float:
    """Builds the physical sky: the sky model, a cloud layer far below and (for dusk) faint stars
    and the planet. Returns the azimuth of the sun.

    The clouds are noise on a sphere `cloud_drop` km below the camera, found from the view
    direction alone, and they fade into the haze with distance.
    """
    tree = new_world()
    view = node(tree, "ShaderNodeTexCoord").outputs["Generated"]
    model = node(
        tree, "ShaderNodeTexSky", sky_type="MULTIPLE_SCATTERING", sun_disc=sky.sun_disc, altitude=sky.altitude,
        sun_elevation=math.radians(sky.sun_elevation), sun_rotation=math.radians(90.0 - SUN_AZIMUTH),
    )  # fmt: skip
    air = node(tree, "ShaderNodeVectorMath", operation="SCALE", Scale=sky.strength)
    tree.links.new(model.outputs["Color"], air.inputs[0])
    split = node(tree, "ShaderNodeSeparateXYZ", Vector=view)

    # Where the view ray meets the cloud sphere: t = -b - sqrt(b2 - c), in km.
    drop = sky.cloud_drop
    b = math_node(tree, "MULTIPLY", split.outputs["Z"], EARTH_RADIUS + drop)
    inside = math_node(
        tree,
        "SUBTRACT",
        math_node(tree, "MULTIPLY", b, b),
        2 * EARTH_RADIUS * drop + drop * drop,
    )
    reach = math_node(tree, "SUBTRACT", math_node(tree, "MULTIPLY", b, -1.0), math_node(tree, "SQRT", math_node(tree, "MAXIMUM", inside, 0.0)))  # fmt: skip
    ground = node(tree, "ShaderNodeVectorMath", operation="SCALE", Scale=reach)
    tree.links.new(view, ground.inputs[0])
    flat = node(tree, "ShaderNodeVectorMath", operation="MULTIPLY")
    tree.links.new(ground.outputs["Vector"], flat.inputs[0])
    flat.inputs[1].default_value = (1.0, 1.0, 0.0)
    fields = node(
        tree,
        "ShaderNodeTexNoise",
        Vector=flat.outputs["Vector"],
        Scale=0.035,
        Detail=9.0,
        Roughness=0.62,
    )
    puffs = node(
        tree,
        "ShaderNodeTexNoise",
        Vector=flat.outputs["Vector"],
        Scale=0.4,
        Detail=6.0,
        Roughness=0.6,
    )
    both = math_node(
        tree,
        "ADD",
        fields.outputs["Factor"],
        math_node(tree, "MULTIPLY", puffs.outputs["Factor"], 0.35),
    )
    cover = node(
        tree,
        "ShaderNodeMapRange",
        interpolation_type="SMOOTHSTEP",
        Value=both,
        From_Min=0.62,
        From_Max=0.8,
    )
    below = node(
        tree,
        "ShaderNodeMapRange",
        Value=inside,
        From_Min=0.0,
        From_Max=2 * EARTH_RADIUS * drop * 0.02,
    )
    looking_down = math_node(tree, "LESS_THAN", split.outputs["Z"], 0.0)
    haze = math_node(
        tree, "POWER", 2.718, math_node(tree, "DIVIDE", reach, -28.0 * drop)
    )  # e^(-distance / visibility)
    amount = math_node(tree, "MULTIPLY", math_node(tree, "MULTIPLY", cover.outputs["Result"], below.outputs["Result"]), math_node(tree, "MULTIPLY", looking_down, haze))  # fmt: skip
    clouded = node(tree, "ShaderNodeMix", data_type="RGBA", Factor=math_node(tree, "MULTIPLY", amount, 0.9), A=capped(tree, air.outputs["Vector"], SUN_CAP), B=(*sky.cloud_color, 1.0))  # fmt: skip
    color = clouded.outputs["Result"]

    if sky.stars > 0.0:
        cells = node(tree, "ShaderNodeTexVoronoi", Vector=view, Scale=170.0)
        point = node(tree, "ShaderNodeMapRange", Value=cells.outputs["Distance"], From_Min=0.0, From_Max=0.045, To_Min=1.0, To_Max=0.0)  # fmt: skip
        size = math_node(
            tree,
            "POWER",
            node(tree, "ShaderNodeSeparateColor", Color=cells.outputs["Color"]).outputs[
                "Red"
            ],
            6.0,
        )
        above = node(
            tree,
            "ShaderNodeMapRange",
            Value=split.outputs["Z"],
            From_Min=-0.1,
            From_Max=0.05,
        )
        star = math_node(tree, "MULTIPLY", math_node(tree, "MULTIPLY", point.outputs["Result"], size), math_node(tree, "MULTIPLY", above.outputs["Result"], sky.stars))  # fmt: skip
        lit = node(tree, "ShaderNodeVectorMath", operation="ADD")
        tree.links.new(color, lit.inputs[0])
        tree.links.new(
            node(tree, "ShaderNodeCombineXYZ", X=star, Y=star, Z=star).outputs[
                "Vector"
            ],
            lit.inputs[1],
        )
        color = lit.outputs["Vector"]
    glow = node(tree, "ShaderNodeVectorMath", operation="ADD")
    tree.links.new(color, glow.inputs[0])
    glow.inputs[1].default_value = sky.airglow
    finish_world(tree, glow.outputs["Vector"])
    if sky.planet > 0.0:
        add_planet(sky)
    return SUN_AZIMUTH


def add_planet(sky: PhysicalSky) -> None:
    """Hangs one pale banded planet low over the horizon, half sunk into the haze of the atmosphere.

    The shader lights the planet from the sun's side by itself and lets it fade out toward the
    Earth's horizon. The planet's colour and contrast are turned down, so it stays restrained.
    """
    distance, half_angle = 20000.0, math.radians(5.0)
    horizon = -math.acos(
        EARTH_RADIUS / (EARTH_RADIUS + sky.altitude / 1000.0)
    )  # the dip of the Earth's edge
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=96, ring_count=48, radius=distance * math.tan(half_angle)
    )
    planet = bpy.context.object
    bpy.ops.object.shade_smooth()
    material = bpy.data.materials.new("planet")
    tree = material.node_tree
    tree.nodes.clear()
    image = bpy.data.images.load(str(SOURCES / "planet" / "PIA07782.jpg"))
    picture = node(tree, "ShaderNodeTexImage", image=image)
    pale = node(
        tree,
        "ShaderNodeHueSaturation",
        Saturation=0.3,
        Value=1.0,
        Color=picture.outputs["Color"],
    )
    soft = node(
        tree,
        "ShaderNodeMix",
        data_type="RGBA",
        Factor=0.45,
        A=pale.outputs["Color"],
        B=(0.5, 0.47, 0.43, 1.0),
    )
    geometry = node(tree, "ShaderNodeNewGeometry")
    facing = node(tree, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
    tree.links.new(geometry.outputs["Normal"], facing.inputs[0])
    # The planet's light comes from where the game's sun lamp stands, a little above the horizon.
    facing.inputs[1].default_value = direction(SUN_AZIMUTH, 7.0)
    lit = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=facing.outputs["Value"], From_Min=-0.08, From_Max=0.9, To_Min=0.0, To_Max=sky.planet)  # fmt: skip
    surface = node(
        tree,
        "ShaderNodeEmission",
        Color=soft.outputs["Result"],
        Strength=lit.outputs["Result"],
    )
    incoming = node(tree, "ShaderNodeSeparateXYZ", Vector=geometry.outputs["Incoming"])
    rise = math_node(
        tree, "MULTIPLY", incoming.outputs["Z"], -1.0
    )  # the sine of the view ray's elevation
    veil = node(tree, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", Value=rise, From_Min=math.sin(horizon + math.radians(0.6)), From_Max=math.sin(horizon + math.radians(6.5)), To_Min=0.0, To_Max=0.9)  # fmt: skip
    mix = node(tree, "ShaderNodeMixShader", Factor=veil.outputs["Result"])
    tree.links.new(
        node(tree, "ShaderNodeBsdfTransparent").outputs["BSDF"], mix.inputs[1]
    )
    tree.links.new(surface.outputs["Emission"], mix.inputs[2])
    tree.links.new(
        mix.outputs["Shader"],
        tree.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"],
    )
    planet.data.materials.append(material)
    planet.location = (
        direction(SUN_AZIMUTH - 76.0, math.degrees(horizon) + 3.4) * distance
    )
    planet.rotation_euler = (
        math.radians(14.0),
        math.radians(-20.0),
        math.radians(200.0),
    )


def add_camera(sun_azimuth: float) -> None:
    """Adds the panorama camera at the level origin. It turns so that the sun lands at SUN_AZIMUTH
    in the image: the image centre is then the level's -y direction."""
    data = bpy.data.cameras.new("camera")
    data.type = "PANO"
    data.panorama_type = "EQUIRECTANGULAR"
    data.clip_start = 0.05
    data.clip_end = 500000.0
    camera = bpy.data.objects.new("camera", data)
    camera.rotation_euler = (math.radians(90.0), 0.0, math.radians(sun_azimuth + 45.0))
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera


def configure_render(samples: int, scale: int, use_gpu: bool) -> None:
    """Sets Cycles (OptiX on the GPU, or the CPU), denoised, scene-linear Radiance HDR output."""
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
    scene.cycles.volume_bounces = 12
    scene.cycles.use_auto_tile = False  # one tile: the denoiser leaves no seam
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = scale
    scene.render.image_settings.file_format = "HDR"


def bake(
    name: str, sky: Sky, out: Path, samples: int, scale: int, use_gpu: bool
) -> None:
    """Builds one sky in an empty file, renders it and prints where its sun is."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    azimuth = build_hdri(sky) if isinstance(sky, HdriSky) else build_physical(sky)
    add_camera(azimuth)
    configure_render(samples, scale, use_gpu)
    path = out / f"{name}.hdr"
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    u, v = image_sun(image_pixels(bpy.data.images.load(str(path))))
    # The image centre (u = 0.5) looks along -y, azimuth 270; u grows to the right, toward -x.
    print(f"bake-skies: wrote {path}; brightest spot at azimuth {(270.0 - (u - 0.5) * 360.0) % 360.0:.1f}, elevation {(v - 0.5) * 180.0:.1f}")  # fmt: skip


def main() -> None:
    """Bakes the skies named after `--` (all when none)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "names",
        nargs="*",
        choices=["dawn", "noon", "dusk", []],
        help="skies to bake (default: all)",
    )
    parser.add_argument(
        "--look",
        choices=sorted(DAWNS),
        default="a",
        help="the look candidate whose dawn to bake",
    )
    parser.add_argument(
        "--out", type=Path, help="default: game/skies, or build/skies below --scale 100"
    )
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument(
        "--scale",
        type=int,
        default=100,
        help="resolution in percent, for quick previews",
    )
    parser.add_argument("--cpu", action="store_true", help="render on the CPU")
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    skies: dict[str, Sky] = {"dawn": DAWNS[args.look], "noon": NOON, "dusk": DUSK}
    out: Path = args.out or (OUT if args.scale == 100 else PREVIEWS)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.names or skies:
        bake(
            name,
            skies[name],
            out.resolve(),
            args.samples,
            args.scale,
            not args.cpu,
        )


if __name__ == "__main__":
    main()
