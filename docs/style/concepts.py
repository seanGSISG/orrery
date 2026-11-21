# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=11"]
# ///
"""Generate the mood references of the style board with the local ComfyUI.

The mood references show atmosphere only. The look that Sean approves comes
from the Blender renders of tools/blender/lookdev.py. This file is the record
of each new mood image: model, sampler settings, prompt and seed. Run it with
ComfyUI up on 127.0.0.1:8188:

    uv run docs/style/concepts.py                    # all moods, recorded seeds
    uv run docs/style/concepts.py mood-dusk          # only this one
    uv run docs/style/concepts.py mood-dusk --seed 7 --out /tmp/try  # explore

ComfyUI also keeps each PNG under output/orrery_style_v2/.
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
SIZE = (1664, 928)
OUT_WIDTH = 1600
WEBP_QUALITY = 90
COMFY_FOLDER = "orrery_style_v2"

NEGATIVE = (
    "stairs, steps, staircase, stairway, illustration, painting, digital art, CGI, render, "
    "3D render, matte painting, fantasy art, oversaturated, glow, bloom, lens flare, collage, "
    "candles, lanterns, people, tiled floor, checkerboard, grid pattern, text, numerals, "
    "watermark, logo"
)

# Shared phrases. A marble cannot climb steps, so every link is a ramp. Gems are big
# pickups that hover. The marble is 0.4 m across and gives the scale.
RAMP = "a broad smooth stone ramp, one plain inclined slab like a wheelchair ramp"
MARBLE = "A clear glass sphere forty centimetres across rests on the stone floor and casts a shadow."
# "Large jewels hovering in mid-air" made jewels ten times the marble, lined up in the sky.
# The size and the height are now tied to the sphere and the floor.
JEWELS = (
    "Three cut gemstones float just above the floor, spread far apart across it. Each "
    "gemstone is about the size of the glass sphere, only slightly larger, and hovers a "
    "hand's width above the stone, right over its own shadow. A thin faint ray of light "
    "rises from each one. One is a sapphire-blue double pyramid, one an amber hexagonal "
    "cut, one a magenta round brilliant; each glows softly from inside."
)
# For noon, each gemstone also gets a named place on the course; that put them on the decks.
# The same wording made the dusk gems larger and higher, so dusk keeps JEWELS.
NOON_JEWELS = (
    "Three cut gemstones, each the size of a melon and only slightly larger than the glass "
    "sphere, float ankle-high above the paving, each right over its own shadow: one on the "
    "round platform beside the sphere, one on the wide curved deck and one on the stone "
    "beam. A thin faint ray of light rises from each one. One is a sapphire-blue double "
    "pyramid, one an amber hexagonal cut, one a magenta round brilliant; each glows softly "
    "from inside."
)
STONE = "weathered pale limestone with a low rim of aged, slightly tarnished brass"
CAMERA = "Shot on a full-frame camera with a 24mm lens at f/8, natural colours, realistic exposure, fine grain."


@dataclass(frozen=True)
class Mood:
    """One mood reference: its file name stem, seed and prompt."""

    name: str
    seed: int
    prompt: str

    @property
    def file_name(self) -> str:
        return f"{self.name}.webp"


MOODS: tuple[Mood, ...] = (
    # Beginner: near the Earth at dawn. No planet, moon or stars.
    Mood(
        "mood-dawn",
        5101,
        "Aerial photograph at sunrise, looking down at about forty degrees onto the flat "
        f"round top of an old stone tower that stands above a sea of clouds. The tower top is "
        f"a wide open plaza of {STONE}; a large clock face of plain brass bars and two brass "
        "hands is set flat into its floor. The plaza fills most of the frame. At the back, "
        f"{RAMP}, rises to a smaller upper terrace, and large brass gears are built into the "
        "wall below that terrace. On the right a short flat stone bridge leads to a second, "
        f"small round tower top. {MARBLE} {JEWELS} Low warm sunlight from the left, long soft "
        "shadows, thin haze, a pale blue sky with a soft peach band at the horizon. The sky "
        f"is empty. {CAMERA}",
    ),
    # Intermediate: high in thin air at noon. No planet.
    Mood(
        "mood-noon",
        5201,
        "Aerial photograph at midday from very high altitude, looking down at about forty "
        "degrees onto a course of floating stone decks far above a layer of clouds. The "
        f"course fills most of the frame and is made of {STONE}. From a round platform in "
        "the foreground the course forks: a wide deck curves away to the left in one broad "
        "banked turn, and a single straight stone beam, one metre wide, crosses the open gap "
        f"as a shortcut. Both end on a larger round platform that is reached by {RAMP}. "
        f"{MARBLE} {NOON_JEWELS} Hard white sunlight from high above, short crisp shadows, very "
        "clear thin air, a deep clean blue sky that pales to white haze at the horizon. The "
        f"sky is empty. {CAMERA}",
    ),
    # Advanced: the edge of space at dusk. One planet, veiled by haze.
    Mood(
        "mood-dusk",
        5301,
        "Photograph taken at dusk from the edge of space, looking down at about forty "
        "degrees onto five round stone platforms that float at different heights, stacked "
        f"like terraces. The platforms fill most of the frame and are made of {STONE}. Each "
        f"platform is joined to the next by {RAMP}; one pair is separated by a short open "
        "gap. One platform is a huge horizontal gear of aged brass with a stone deck on top. "
        "Two low dome-shaped brass bumpers stand on the largest platform. "
        f"{MARBLE} {JEWELS} Far below lies the curved horizon of the Earth, with a thin blue "
        "band of atmosphere and a faint orange line of sunset. Above it the sky is almost "
        "black, with a few faint stars. One large pale planet sits low on the horizon, half "
        "hidden by the haze of the atmosphere. The last warm sunlight comes from the left; "
        f"long shadows, cool blue fill light, no lamps. {CAMERA}",
    ),
)


def build_graph(mood: Mood, seed: int, cfg: float) -> dict[str, dict[str, object]]:
    """Return the ComfyUI API graph for one text-to-image run."""
    width, height = SIZE
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": UNET, "weight_dtype": "default"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": TEXT_ENCODER,
                "type": "qwen_image",
                "device": "default",
            },
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["1", 0], "shift": SHIFT},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": mood.prompt},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": NEGATIVE},
        },
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
        "9": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["8", 0], "vae": ["3", 0]},
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["9", 0],
                "filename_prefix": f"{COMFY_FOLDER}/{mood.name}_{seed}",
            },
        },
    }


def call(path: str, payload: dict[str, object] | None = None) -> bytes:
    """GET (or POST, when a payload is given) one ComfyUI endpoint."""
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(f"{COMFY_URL}{path}", data=data)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def generate(mood: Mood, seed: int, cfg: float) -> Image.Image:
    """Queue one image, wait for it and return it."""
    prompt_id: str = json.loads(
        call("/prompt", {"prompt": build_graph(mood, seed, cfg)})
    )["prompt_id"]
    while True:
        history = json.loads(call(f"/history/{prompt_id}"))
        if prompt_id in history:
            break
        time.sleep(2)
    entry = history[prompt_id]
    if entry["status"]["status_str"] != "success":
        raise RuntimeError(f"{mood.name}: ComfyUI run failed: {entry['status']}")
    saved = entry["outputs"]["10"]["images"][0]
    query = urllib.parse.urlencode(
        {
            "filename": saved["filename"],
            "subfolder": saved["subfolder"],
            "type": saved["type"],
        }
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
    names = [mood.name for mood in MOODS]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "names", nargs="*", help=f"images to make (default: all of {', '.join(names)})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        action="append",
        help="try this seed, not the recorded one (repeatable)",
    )
    parser.add_argument(
        "--cfg", type=float, default=CFG, help="try this guidance scale"
    )
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "review")
    args = parser.parse_args()
    if unknown := set(args.names) - set(names):
        parser.error(f"unknown image name: {', '.join(sorted(unknown))}")
    for mood in MOODS:
        if args.names and mood.name not in args.names:
            continue
        for seed in args.seed or [mood.seed]:
            started = time.monotonic()
            image = generate(mood, seed, args.cfg)
            file_name = mood.file_name if not args.seed else f"{mood.name}_{seed}.webp"
            save_webp(image, args.out / file_name)
            print(
                f"{args.out / file_name}  seed={seed}  cfg={args.cfg}  {time.monotonic() - started:.0f}s"
            )


if __name__ == "__main__":
    main()
