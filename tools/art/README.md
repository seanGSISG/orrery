# Asset tools

GPT-Image makes 2D art: decals, signage, clock faces, emblems, key art, icons and concept boards. Tripo makes decorative 3D props from an image. A Blender clean-up step and `kit.prop` put a prop into a level. Every output is AI-generated: record it in `docs/licenses.md`, and the Steam AI disclosure cites the manifests.

## Keys

The tools read `OPENAI_API_KEY` and `TRIPO_API_KEY` from the environment, else from `.env` at the repo root (git-ignored). In a git worktree without its own `.env`, they read the main checkout's `.env`. A real environment variable wins over `.env`.

1. Copy `.env.example` to `.env`.
2. Fill in each key from Bitwarden: `OPENAI_API_KEY` is the password field of the item `openai-api-key`, and `TRIPO_API_KEY` is the password field of the item `tripo-api-key`.
3. Run `just art check`. It loads both keys and calls two free endpoints (the OpenAI model, the Tripo balance).

The tools load a key only just before a call to the API, so a dry run needs no key. They never print or save a key. When a key is missing, the error names the variable, the `.env` path and the Bitwarden item.

## Costs and the spend guard

| Call | Price | Example |
|---|---|---|
| GPT-Image-2.6 Sunburst, live | USD 30 per 1M image output tokens, USD 5 per 1M text input tokens | 1024x1024: low USD 0.025, medium USD 0.044, high USD 0.053 |
| GPT-Image-2.6 Sunburst, batch | Half the live price | 1024x1024 medium: USD 0.022 |
| Tripo image-to-model or multiview-to-model | 20-30 credits (1 credit = USD 0.01); detailed texture about 10 more | Standard texture: USD 0.30; detailed: USD 0.40 |

`tools/art/config.toml` holds these prices and the cap. The image estimate uses the formula of OpenAI's token calculator. After a call, the manifest also records the billed cost, from the token usage or the Tripo `credits_consumed`.

- A paid command (`image`, `batch`, `model`) prints its estimate and sends nothing without `--yes`.
- `--dry-run` prints the requests and the estimate and sends nothing.
- A run estimated above `max_usd_per_run` (USD 5) stops. `--max-usd` sets another cap for one run.

## Images: batch or live

Use `batch` for sets. It costs half, but OpenAI can take up to 24 h (often 30-60 min). Use `image` only when the next step waits for the picture, for example the concept image of a prop.

```sh
just art image --prompt "A brass clock-face decal, no background" -o decals/clock.png --transparent --yes
just art batch tools/art/examples/decals.jsonl --dry-run
just art batch tools/art/examples/decals.jsonl --yes          # submits, waits, saves
just art batch tools/art/examples/decals.jsonl --yes --no-wait  # submits and returns; rerun to collect
```

A jobs file has one JSON object for each line: `prompt` and `out`, and optionally `size` (`WIDTHxHEIGHT`, edges divisible by 16, 1024x640 at least), `quality` (`low`, `medium`, `high`, `xhigh`, `max`) and `transparent` (`.png` or `.webp` only). The model, quality and size defaults are in `config.toml`.

A batch keeps its state in `build/art/batches/<jobs file>.json`. A rerun of the same file resumes the batch and never pays twice. After the images are saved, a rerun only reports them. OpenAI's model page for GPT-Image-2.6 shows the Batch endpoint as not available, but its pricing page lists a Batch price. If a batch fails validation, the result says so and nothing is billed: use `image` instead.

## Props: concept image, 3D, clean-up, `kit.prop`

1. **Concept image.** One object, front view, plain background, even light: `just art image --prompt "..." -o props/lamp.png --quality high --yes`.
2. **3D model.** `just model build/art/images/props/lamp.png -o lamp.glb --yes`. Add `--back`, `--left` or `--right` images to send a multiview task. `--texture-quality detailed` gives an HD texture; `--face-limit` caps the faces. A rerun after a time-out waits for the same task.
3. **Clean-up.** `just prop-cleanup build/art/models/lamp.glb lamp --height 1.8 --triangles 4000 [--material brass]`. Headless Blender welds and decimates the mesh, scales it to the height in metres, puts the origin on the centre of its base, and writes `assets/props/lamp.glb` (Git LFS) with the manifest beside it. `--material` replaces the model's own texture with a kit material (`limestone`, `brass`, `gold`).
4. **Level.** In a level script: `kit.prop("lamp", at=(4.0, 2.0, 0.0), rotation=(0.0, 0.0, 90.0), collider="box")`. A prop is decoration: it does not collide unless `collider` is `box` or `cylinder`, and then only that simple shape collides. The marble rolls only on our own kit pieces.

A prop is not a LevelObject: it has no script and no marker. It is a mesh in the level `.glb`.

## Outputs

Everything goes to `build/art/` (git-ignored): `images/`, `models/` and `batches/`. Each output has a manifest, `<file>.json`: the service, model, mode, prompt (or source images), settings, seed, estimated and billed cost, request id, date and `"ai_generated": true`. Only the cleaned props in `assets/props/` are committed.

## Tests

`just test-art` runs the tests with mocked OpenAI and Tripo APIs. They make no paid call. The prop tests run `prop_cleanup.py` and `kit.prop` in headless `blender-5.2`, and they skip when it is missing.

The Tripo client in `src/orrery_art/tripo.py` runs any task type: a `Task` is an endpoint, its JSON options (local images as `Path`s, which it uploads) and its outputs. `image_to_model` and `multiview_to_model` are the first two; a new step is one more function that returns a `Task`.
