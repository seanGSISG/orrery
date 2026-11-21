# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=11"]
# ///
"""Generate the style-board concept images with the local ComfyUI.

This file is the record of every concept image: model, sampler settings,
prompt and seed. Run it with ComfyUI up on 127.0.0.1:8188:

    uv run docs/style/concepts.py                 # all images, recorded seeds
    uv run docs/style/concepts.py zone-2 marble-a # only these
    uv run docs/style/concepts.py zone-2 --seed 7 --out /tmp/try  # explore

Model: Qwen-Image-2512 (Apache-2.0), see docs/licenses.md.
"""

from __future__ import annotations

import argparse
import io
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

COMFY_URL = "http://127.0.0.1:8188"
# The bf16 file, not the fp8 one: this ComfyUI runs with `--fast fp8_matrix_mult`,
# which turns the plain fp8 weights of this model into noise.
UNET = "qwen_image_2512_bf16.safetensors"
TEXT_ENCODER = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
STEPS = 50
CFG = 3.0  # below the model's default of 4: higher values push it toward a painted look
SAMPLER = "euler"
SCHEDULER = "simple"
SHIFT = 3.1
WIDE = (1664, 928)
SQUARE = (1328, 1328)
OUT_WIDTH = 1600
WEBP_QUALITY = 84

NEGATIVE = (
    "illustration, painting, digital art, CGI, 3D render, fantasy art, concept art, "
    "matte painting, oversaturated, vivid colours, bloom, lens flare, HDR, symmetrical "
    "composition, collage, candles, lanterns, lit windows, stairs, steps, staircase, "
    "stairway, text, letters, numerals, watermark, logo, people, tiled floor, checkerboard, "
    "grid pattern"
)

# Photographic language keeps the model away from a fantasy-art look.
PHOTO = (
    "Natural light from a single sun, consistent shadows, strong atmospheric perspective: "
    "distant things are paler, bluer and lower in contrast. Muted natural colours. "
    "Documentary photograph, full-frame camera, f/8, sharp focus, realistic exposure."
)

# Every world and zone image shows a space to play in, at marble scale (the marble is
# 0.4 m across), from the high three-quarter view of a level overview. A marble cannot
# climb steps, so tiers are joined by ramps. Gems are big pickups that float and glow.
VIEW = "Aerial photograph from a drone, a high three-quarter view that looks down at about forty degrees"
MARBLE = "A glass sphere forty centimetres across rests on the stone, small in the frame, and casts a shadow."
JEWELS = (
    "large glowing faceted jewels hovering in mid-air above the floor, each a little taller "
    "than the sphere, each casting a soft light, with a faint vertical beam of light rising "
    "from each jewel"
)
JEWEL_CUTS = (
    "One jewel is sapphire blue, cut as a tall double pyramid; one is amber orange, in a "
    "hexagonal cut; one is magenta, in a round brilliant cut."
)
BORDER = (
    "A low border of aged, slightly tarnished brass runs along every open edge; there are "
    "no walls and no railings."
)

# The campaign sky follows height: Beginner is near the Earth at dawn, Intermediate is
# high in thin air at noon, Advanced is at the edge of space at dusk. Only Advanced has a planet.
PLAZA = (
    f"{VIEW} onto a wide open plaza of weathered limestone that floats above a sea of "
    "clouds. The plaza is the subject and fills most of the frame: about fifteen metres "
    "across, paved with large limestone slabs laid in rings around a large clock face that "
    "is set flat into the middle of the floor, with plain brass bars for the hours and two "
    f"brass hands. {BORDER} At the back of the plaza a smooth sloped stone ramp, like a "
    "wheelchair ramp, rises to a second, smaller terrace one storey higher, and a few large "
    "brass gears are built into the wall under that terrace. Beside the plaza floats a "
    f"small round stone platform, joined to it by a short flat stone bridge. {MARBLE} "
    f"Three {JEWELS}: two above the plaza and one above the upper terrace. {JEWEL_CUTS}"
)
COURSE = (
    f"{VIEW} onto a course of floating limestone decks high above a sea of clouds. The "
    "course is the subject and fills most of the frame. It starts on a round stone platform "
    "in the foreground and splits into two routes. The safe route is a wide deck, about "
    "four metres wide, that winds away to the left in two broad banked curves. The shortcut "
    "goes straight ahead: two stone beams, each about one metre wide, cross an open gap "
    "side by side. Both routes end on one large platform in the distance. Beside the gap, a "
    "long arm of aged brass on a stone pier carries a small round stone platform out over "
    f"the clouds. {BORDER} {MARBLE} Three {JEWELS}: one above the wide route, one above "
    f"the beams and one above the far platform. {JEWEL_CUTS}"
)
STACK = (
    f"{VIEW} onto a cluster of floating limestone platforms at the edge of space. The "
    "platforms are the subject and fill most of the frame: five flat platforms of different "
    "sizes, each several metres across, at five different heights, joined by smooth sloped "
    "stone ramps; two of them are separated by a short open gap with no bridge. One "
    "platform is round and lies on a huge horizontal gear of aged brass, whose teeth show "
    "all around its rim. Three low round bumpers of brass, like wide domes, stand on the "
    f"largest platform. {BORDER} {MARBLE} Three {JEWELS}, each above a different platform. "
    f"{JEWEL_CUTS}"
)

MARBLE_SET = (
    "The marble rests on a smooth honed limestone surface with one curved inlaid line of "
    "aged brass. Low golden-hour sunlight from the left, a crisp highlight, soft sky-blue "
    "fill light, a softly blurred evening sky in the background. Macro product photograph, "
    "100mm lens, shallow depth of field, extremely sharp on the marble, natural colours."
)


@dataclass(frozen=True)
class Concept:
    """One concept image: its candidate name, output size, seed and prompt."""

    name: str
    size: tuple[int, int]
    seed: int
    prompt: str

    @property
    def file_name(self) -> str:
        return f"{self.name}.webp"


CONCEPTS: tuple[Concept, ...] = (
    Concept(
        "world-dawn",
        WIDE,
        1301,
        f"{PLAZA} Early morning, just after sunrise: low warm sunlight from the left, long "
        "soft shadows, and at the top of the frame a pale blue sky with a soft peach band "
        f"along the horizon. The sky is empty. {PHOTO}",
    ),
    # Two sky directions for noon: bright high-altitude blue, or the deep blue stratosphere.
    Concept(
        "world-noon-a",
        WIDE,
        1101,
        f"{COURSE} Midday at high altitude: the sun is high, the air is thin and very "
        "clear, the sky at the top of the frame is a bright clean blue, the cloud layer "
        "lies far below and fades into haze at the horizon. Short crisp shadows. The sky "
        f"is empty. {PHOTO}",
    ),
    Concept(
        "world-noon-b",
        WIDE,
        1101,
        f"{COURSE} Midday in the stratosphere, thirty kilometres up, like a photograph "
        "from a high-altitude balloon: the sky at the top of the frame is a very dark blue "
        "and pales to a thin bright band of haze along the horizon, and the horizon is a "
        "clear curved arc, like the edge of a globe. The cloud layer lies very far below, "
        "its shapes small. Hard white sunlight, short crisp shadows. The sky is empty, "
        f"with no stars. {PHOTO}",
    ),
    Concept(
        "world-dusk",
        WIDE,
        1101,
        f"{STACK} Dusk at the edge of space: at the top of the frame a dark blue-violet sky "
        "with a few faint stars and a thin band of soft orange along the gently curved "
        "horizon; the cloud layer lies very far below. One large ringed planet hangs low "
        f"over the horizon, partly veiled by haze. Cool, soft light, no lamps. {PHOTO}",
    ),
    Concept(
        "zone-1",
        WIDE,
        2101,
        f"{VIEW} onto the cobbled market square of a small old town at golden dawn. Low "
        "warm sunlight from the right, long shadows, light mist only in the far distance. "
        "Stone and timber houses with slate roofs and low porches stand around the "
        "square; a few market stalls with canvas awnings stand on the cobbles. At the far "
        "side rises the stone base of a tall clock tower; only its lower storeys are in "
        "the frame. A route for the sphere climbs out of the square: wide wooden planks "
        "and smooth sloped stone ramps lean from the cobbles up onto the flat porch "
        "roofs, more planks lead from there up to the roof ridges, and from the ridges a "
        "ramp reaches a broad stone ledge on the base of the clock tower. There are "
        "ledges at several heights, and two separate ways up are in view, one on the "
        f"left side of the square and one on the right. Everything stands on the ground; "
        f"nothing floats except the jewels. {MARBLE} Two {JEWELS}: one above a porch roof "
        f"and one above the tower ledge. {PHOTO}",
    ),
    Concept(
        "zone-2",
        WIDE,
        2201,
        "Photograph of a tall stack of floating stonework against a clear morning sky, "
        "seen from the side and a little from above. The pieces of a broken limestone "
        "clock tower hang motionless in the air at many heights, one above another: "
        "round stone floor discs several metres across, and very large gears of aged "
        "brass lying flat as platforms. A smooth spiral stone ramp with a low brass lip "
        "winds up around the stack from disc to disc; it is the safe way up. The second "
        "way up is shorter: the discs and one slowly turning gear hang close enough "
        "above one another for a jump from each to the next. One long brass pendulum "
        f"hangs below the highest piece. {MARBLE} One of the {JEWELS}, sapphire blue and "
        "cut as a tall double pyramid, hovers above a disc at mid height. Far below, the "
        "slate roofs of a small town are pale in the morning haze. Clear early-morning "
        f"sunlight from the right, soft blue shadows. {PHOTO}",
    ),
    Concept(
        "zone-3",
        WIDE,
        2301,
        f"{VIEW} over the rooftops of an old town in mid-morning: steep slate and "
        "copper-green roofs, brick chimneys and a few brass weathervanes. Narrow flat "
        "stone decks with a low border of aged brass run along the roof ridges, across "
        "the flat tops of dormers and around the ledges of chimney stacks, and smooth "
        "sloped ramps and plank bridges link them, so that two separate routes climb "
        "from the nearest roof to the highest ridge. Two small airships are moored low "
        "over the roofs, their open wooden decks only a little above the ridges: long "
        "cream fabric envelopes, wooden gondolas about three metres wide, aged-brass "
        "fittings. A wooden gangplank rises from the highest roof ridge to the deck of "
        "the nearer, lower airship, and a second gangplank rises from that deck to the "
        f"deck of the higher airship behind it. {MARBLE} One of the {JEWELS}, amber "
        "orange in a hexagonal cut, hovers above the deck of the lower airship. Blue sky "
        f"with a few large white clouds, light haze over the town. {PHOTO}",
    ),
    Concept(
        "gem",
        WIDE,
        4101,
        "Close-up photograph from a low angle. A large cut jewel hovers thirty "
        "centimetres above a floor of weathered limestone, next to a clear glass sphere "
        "forty centimetres across that rests on the floor. The jewel is fifty centimetres "
        "tall, a little taller than the sphere: a deep sapphire-blue gem, cut as a tall "
        "double pyramid with crisp facets. It glows softly from inside and throws a soft "
        "blue light on the stone below it, and a faint, thin vertical beam of pale light "
        "rises from the jewel straight up into the sky. A flat strip of aged brass is set "
        "into the floor. Early morning, low warm sun, long soft shadows; a sea of clouds "
        "and a pale sky, softly blurred, in the background. Photograph, 50mm lens, f/4, "
        "natural colours, realistic exposure.",
    ),
    Concept(
        "marble-a",
        SQUARE,
        3101,
        "A single marble: a perfect sphere of clear flawless glass about four "
        "centimetres across. At its centre floats a tiny brass orrery: a small polished "
        "brass ball ringed by three thin interlocking brass rings and a few minute "
        "gears, sharply visible through the glass with realistic refraction. A warm "
        f"patch of focused light falls on the stone beside the marble. {MARBLE_SET}",
    ),
    Concept(
        "marble-b",
        SQUARE,
        3201,
        "A single marble: a perfect polished sphere of deep midnight-blue stone with "
        "faint darker veins, about four centimetres across. Fine lines of gold are "
        "inlaid flush into its surface: three thin orbit rings that cross at different "
        "angles, with a few tiny gold dots on the rings like planets. High-gloss "
        f"polish with crisp reflections of the evening sky. {MARBLE_SET}",
    ),
)


def build_graph(concept: Concept, seed: int, cfg: float) -> dict[str, dict[str, object]]:
    """Return the ComfyUI API graph for one text-to-image run."""
    width, height = concept.size
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": TEXT_ENCODER, "type": "qwen_image", "device": "default"},
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": SHIFT}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": concept.prompt}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": NEGATIVE}},
        "7": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["7", 0],
                "seed": seed,
                "steps": STEPS,
                "cfg": cfg,
                "sampler_name": SAMPLER,
                "scheduler": SCHEDULER,
                "denoise": 1.0,
            },
        },
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {
            "class_type": "SaveImage",
            "inputs": {"images": ["9", 0], "filename_prefix": f"orrery_style/{concept.name}_{seed}"},
        },
    }


def call(path: str, payload: dict[str, object] | None = None) -> bytes:
    """GET (or POST, when a payload is given) one ComfyUI endpoint."""
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(f"{COMFY_URL}{path}", data=data)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def generate(concept: Concept, seed: int, cfg: float) -> Image.Image:
    """Queue one image, wait for it and return it."""
    prompt_id: str = json.loads(call("/prompt", {"prompt": build_graph(concept, seed, cfg)}))["prompt_id"]
    while True:
        history = json.loads(call(f"/history/{prompt_id}"))
        if prompt_id in history:
            break
        time.sleep(2)
    entry = history[prompt_id]
    if entry["status"]["status_str"] != "success":
        raise RuntimeError(f"{concept.name}: ComfyUI run failed: {entry['status']}")
    saved = entry["outputs"]["10"]["images"][0]
    query = urllib.parse.urlencode(
        {"filename": saved["filename"], "subfolder": saved["subfolder"], "type": saved["type"]}
    )
    return Image.open(io.BytesIO(call(f"/view?{query}"))).convert("RGB")


def save_webp(image: Image.Image, path: Path) -> None:
    """Scale the image down to OUT_WIDTH (never up) and save it as WebP."""
    if image.width > OUT_WIDTH:
        height = round(image.height * OUT_WIDTH / image.width)
        image = image.resize((OUT_WIDTH, height), Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=WEBP_QUALITY, method=6)


def main() -> None:
    names = [concept.name for concept in CONCEPTS]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*", help=f"images to make (default: all of {', '.join(names)})")
    parser.add_argument("--seed", type=int, action="append", help="try this seed, not the recorded one (repeatable)")
    parser.add_argument("--cfg", type=float, default=CFG, help="try this guidance scale")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "review")
    args = parser.parse_args()
    if unknown := set(args.names) - set(names):
        parser.error(f"unknown image name: {', '.join(sorted(unknown))}")
    for concept in CONCEPTS:
        if args.names and concept.name not in args.names:
            continue
        for seed in args.seed or [concept.seed]:
            started = time.monotonic()
            image = generate(concept, seed, args.cfg)
            file_name = concept.file_name if not args.seed else f"{concept.name}_{seed}.webp"
            save_webp(image, args.out / file_name)
            print(f"{args.out / file_name}  seed={seed}  cfg={args.cfg}  {time.monotonic() - started:.0f}s")


if __name__ == "__main__":
    main()
