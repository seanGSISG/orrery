# Licenses

Every third-party asset, sample, font and AI model used in Orrery. Add one row per item.

| Item | Source | License | Used for |
|---|---|---|---|
| Qwen-Image-2512, image model (`qwen_image_2512_bf16.safetensors`) | [Comfy-Org/Qwen-Image](https://huggingface.co/Comfy-Org/Qwen-Image) at `1f12b17`, repackaged from [Qwen/Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512) | Apache-2.0 | Concept images of the style board: `docs/style/review/world-*.webp`, `zone-*.webp`, `marble-*.webp` |
| Qwen2.5-VL-7B, text encoder (`qwen_2.5_vl_7b_fp8_scaled.safetensors`) | Comfy-Org/Qwen-Image at `1f12b17`, from [Qwen/Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | Apache-2.0 | Text encoder of Qwen-Image-2512 |
| Qwen-Image VAE (`qwen_image_vae.safetensors`) | Comfy-Org/Qwen-Image at `1f12b17` | Apache-2.0 | Image decoder of Qwen-Image-2512 |
| Marble007, PBR stone texture, 2K | [ambientCG](https://ambientcg.com/a/Marble007) | CC0 1.0 | `assets/textures/stone/`; look-dev render A (`tools/blender/lookdev.py`) |
| Marble012, PBR stone texture, 2K | [ambientCG](https://ambientcg.com/a/Marble012) | CC0 1.0 | `assets/textures/stone/`; look-dev render B |
| Marble023, PBR stone texture, 2K | [ambientCG](https://ambientcg.com/a/Marble023) | CC0 1.0 | `assets/textures/stone/`; look-dev render C and the stone marble |
| Qwantani Sunset (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/qwantani_sunset_puresky) | CC0 1.0 | `assets/textures/sky/`; look-dev render A |
| Belfast Sunset (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/belfast_sunset_puresky) | CC0 1.0 | `assets/textures/sky/`; look-dev render B |
| Syferfontein 1d Clear (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/syferfontein_1d_clear_puresky) | CC0 1.0 | `assets/textures/sky/`; look-dev render C |

## Image models that Orrery must not use

These models are installed in the local ComfyUI, but their licenses do not allow commercial use of the outputs without a condition. Checked on 2026-11-20.

| Model | License | Reason |
|---|---|---|
| Qwen-Image-2.1 | Qwen Research License | Non-commercial use only. A commercial license must be requested from the vendor. |
| FLUX.2 klein 9B | FLUX Non-Commercial License | Non-commercial use only. |
| Krea 2 (Turbo, Raw and their fine-tunes) | Krea 2 Community License | Commercial use only while company revenue is below USD 1 million per year; the license is revocable. |
