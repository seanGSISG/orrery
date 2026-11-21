# Licenses

Every third-party asset, sample, font, add-on and AI model in Orrery. Each line gives the source, the license and where we use it.

| Item | Source | License | Used in |
|---|---|---|---|
| GUT 9.7.1 (Godot Unit Test) | Tag archive `https://github.com/bitwes/Gut/archive/refs/tags/v9.7.1.tar.gz` (SHA-256 `6da99c4e9228d9bec3fb4bd1730a487770a989f0f511dac82a2897a964613385`), vendored unchanged | MIT (`game/addons/gut/LICENSE.md`). Its bundled fonts (Anonymous Pro, Courier Prime, Lobster Two) are SIL OFL 1.1 fonts; `game/addons/gut/fonts/OFL.txt` holds the license text | `game/addons/gut/`: the unit-test runner. Release exports leave it out |
| Sound effects and placeholder music loops | Our own work: `tools/audio/sfx/synth_sfx.py` synthesises them from sines and noise. No samples. The script runs with numpy (BSD-3-Clause) and soundfile (BSD-3-Clause, with libsndfile, LGPL-2.1), which are build tools only and do not ship | Ours | `game/audio/sfx/`; `game/test/audio/loops/` (tests only) |
| Qwen-Image-2512, image model (`qwen_image_2512_bf16.safetensors`) | [Comfy-Org/Qwen-Image](https://huggingface.co/Comfy-Org/Qwen-Image) at `1f12b17`, repackaged from [Qwen/Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512) | Apache-2.0 | Mood references of the style board: `docs/style/review/mood-*.webp` and `ref-*.webp` |
| Qwen2.5-VL-7B, text encoder (`qwen_2.5_vl_7b_fp8_scaled.safetensors`) | Comfy-Org/Qwen-Image at `1f12b17`, from [Qwen/Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | Apache-2.0 | Text encoder of Qwen-Image-2512 |
| Qwen-Image VAE (`qwen_image_vae.safetensors`) | Comfy-Org/Qwen-Image at `1f12b17` | Apache-2.0 | Image decoder of Qwen-Image-2512 |
| Scuffed Cement, PBR texture, 2K | [Poly Haven](https://polyhaven.com/a/scuffed_cement) | CC0 1.0 | `assets/textures/stone/`; limestone of look A (`tools/blender/lookdev.py`) |
| Concrete Wall 008, PBR texture, 2K | [Poly Haven](https://polyhaven.com/a/concrete_wall_008) | CC0 1.0 | `assets/textures/stone/`; limestone of look B |
| Dirty Concrete, PBR texture, 2K | [Poly Haven](https://polyhaven.com/a/dirty_concrete) | CC0 1.0 | `assets/textures/stone/`; limestone of look C |
| Marble023, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Marble023) | CC0 1.0 | `assets/textures/stone/`; the stone marble (Marble B) |
| Metal007, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Metal007) | CC0 1.0 | `assets/textures/metal/`; aged brass of look A |
| Metal008, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Metal008) | CC0 1.0 | `assets/textures/metal/`; dark bronze of look C |
| Metal048A, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Metal048A) | CC0 1.0 | `assets/textures/metal/`; gold inlays, satin brass of look B, the marble's brass core and gold lines |
| Syferfontein 6d Clear (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/syferfontein_6d_clear_puresky) | CC0 1.0 | `assets/textures/sky/`; dawn sky of look A |
| Qwantani Dusk 2 (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/qwantani_dusk_2_puresky) | CC0 1.0 | `assets/textures/sky/`; dawn sky of look B |
| Syferfontein 1d Clear (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/syferfontein_1d_clear_puresky) | CC0 1.0 | `assets/textures/sky/`; dawn sky of look C |
| Cassini cylindrical map of Jupiter, PIA07782 | [NASA Photojournal](https://photojournal.jpl.nasa.gov/catalog/PIA07782), file from `assets.science.nasa.gov`. Credit: NASA/JPL/Space Science Institute | Public domain (NASA) | `assets/textures/planet/`; the planet of the dusk sky, with colour and contrast turned down |

## Image models that Orrery must not use

These models are installed in the local ComfyUI, but their licenses do not allow commercial use of the outputs without a condition. Checked on 2026-11-20.

| Model | License | Reason |
|---|---|---|
| Qwen-Image-2.1 | Qwen Research License | Non-commercial use only. A commercial license must be requested from the vendor. |
| FLUX.2 klein 9B | FLUX Non-Commercial License | Non-commercial use only. |
| Krea 2 (Turbo, Raw and their fine-tunes) | [Krea 2 Community License](https://www.krea.ai/krea-2-licensing) | Section 2.3 permits commercial use of the model, its derivatives and its outputs only while the total revenue of the company and its affiliates is below USD 1 million per year. The license is revocable. Orrery can use Krea 2 only if Sean confirms that this condition holds and accepts it. |
