# Asset tools

GPT-Image makes 2D art: decals, signage, clock faces, emblems, key art, icons and concept boards. Tripo makes decorative 3D props from a concept image. A Blender clean-up step and `kit.prop` put a prop into a level. Every output is AI-generated: record it in `docs/licenses.md`, and the Steam AI disclosure cites the recipes. `docs/research/asset-prompting.md` holds the prompt rules, the templates and the prop pipeline; this file tells how to run the tools.

## Keys

The tools read `OPENAI_API_KEY` and `TRIPO_API_KEY` from the environment, else from `.env` at the repo root (git-ignored). In a git worktree without its own `.env`, they read the main checkout's `.env`. A real environment variable wins over `.env`.

1. Copy `.env.example` to `.env`.
2. Fill in each key from Bitwarden: `OPENAI_API_KEY` is the password field of the item `openai-api-key`, and `TRIPO_API_KEY` is the password field of the item `tripo-api-key`.
3. Run `just art check`. It loads both keys and calls free endpoints (the two OpenAI models, the Tripo balance).

The tools load a key only just before a call to the API, so a dry run needs no key. They never print or save a key. When a key is missing, the error names the variable, the `.env` path and the Bitwarden item.

## Costs and the spend guards

| Call | Price |
|---|---|
| GPT-Image-2.6 Flare or Sunburst, live | USD 30 per 1M image output tokens, USD 8 per 1M image input, USD 5 per 1M text input. 1024x1024: low USD 0.025, medium USD 0.044, high USD 0.053 |
| GPT-Image-2.6, Batch API (`set --batch`) | Half the live price, if the API accepts it for 2.6 |
| Tripo `views` (image-to-multiview) | 10 credits (1 credit = USD 0.01) |
| Tripo `edit-views` | 5 credits per edited view |
| Tripo `model`, P1 / P2 / H | 40 / 100 / 20 credits without texture, 50 / 110 / 30 with it; detailed texture +20 |
| Tripo `texture` | fast or standard 10, detailed 20, extreme 30 credits |

`tools/art/config.toml` holds the prices (with their source date), the caps and the budgets. The image estimate uses the formula of OpenAI's token calculator; a reference image adds a guessed 1,500 input tokens. After a call, the recipe records the billed cost, from the token usage or Tripo's `credits_consumed`.

- A paid command prints its estimate and sends nothing without `--yes`. `--dry-run` prints the requests and the estimate and sends nothing.
- A run estimated above `max_usd_per_run` (USD 5) stops. `--max-usd` sets another cap for one run.
- `build/art/spend.jsonl` keeps the running total of each API in this checkout. A call that would take the total past its budget (USD 20 each) stops.
- `just art balance` shows the Tripo balance and usage and the running totals. It costs nothing.

## Images

Draft in Flare (the default), then make the final in Sunburst with the same prompt (`--model sunburst`). Calls are live, one at a time.

```sh
just art image --prompt "..." -o decals/clock.png --transparent --quality low --dry-run
just art image --prompt "..." -o decals/clock.png --transparent --model sunburst --yes
just art image --prompt "Image 1 sets the material look only. ..." --ref build/art/images/style.png -o props/cart.png --yes
just art set tools/art/examples/decals.jsonl --yes          # live, one job at a time
just art set tools/art/examples/decals.jsonl --batch --yes  # Batch API (untested for 2.6)
```

- `--ref` (repeat, up to 16) makes it an edit (`/v1/images/edits`). Give each image a numbered role in the prompt.
- `--transparent` asks for a transparent background. The tool then checks that the PNG or WebP has clear pixels, and fails the job if not (the file stays for a look).
- A jobs file has one JSON object for each line: `prompt` and `out`, and optionally `model` (`flare`, `sunburst`), `size` (`WIDTHxHEIGHT`, edges divisible by 16, 1024x640 at least), `quality` (`low` to `max`), `complexity` (`low`, `medium`, `high`), `transparent` (`true` or `false`) and `refs` (a list of paths). A wrong type stops the whole file before any call.
- A live `set` skips the images that it made before. A `--batch` run keeps its state in `build/art/batches/<jobs file name>-<hash of its path>.json`, and a rerun resumes the batch and never pays twice. The OpenAI sources disagree on Batch for GPT-Image-2.6; if a batch fails validation, the result says so and nothing is billed.

## Props: concept image, views, model, texture, clean-up, `kit.prop`

These are the steps of `docs/research/asset-prompting.md` §3.1. Each Tripo command waits for its task, downloads the results at once (the URLs are short-lived) and writes a recipe beside them.

1. **Concept image.** One object, front view, plain background, even light: `just art image --prompt "..." -o props/lamp.png --quality high --yes`.
2. **Views.** `just art views build/art/images/props/lamp.png -o lamp-views --yes` saves `lamp-views.front.png`, `.left.png`, `.back.png` and `.right.png`, and prints the task id. Skip this step for a simple symmetric prop and give the image to `model`.
3. **Fix a view** (optional). `just art edit-views <views task id> --back "the back has a flat panel" -o lamp-views-2 --yes`.
4. **Geometry.** `just model --views <views task id> -o lamp-shape.glb --face-limit 4000 --seed 1 --yes`. The default series is P1 (low-poly) and there is no texture yet. `--series p2` or `h` compares; `--texture` textures in the same call; an image path instead of `--views` (with `--back` ...) sends your own views.
5. **Look at the shape** in Blender before you pay for the texture.
6. **Texture.** `just art texture <model task id> -o lamp.glb --front build/art/models/lamp-views.front.png --back build/art/models/lamp-views.back.png --seed 1 --yes`. It sends the texture model `v3.5-20260815` and `delight: true`, so the texture holds no baked light. `--no-bake` sends `bake: false`.
7. **Clean-up.** `just prop-cleanup build/art/models/lamp.glb lamp --height 3.2`. Headless Blender writes `assets/props/lamp.glb` (Git LFS) with the recipe beside it. It does all of these:
   - It welds the mesh, decimates it to the triangle budget, scales it to the height in metres and puts the origin on the centre of its base.
   - It names the material `orrery_lamp`.
   - It reduces each map to the texture size of the class: 1K for clutter (up to 0.7 m) and medium (up to 2.5 m), 2K for hero (taller).
   - It sets metallic to 0 or 1. It clamps roughness to 0.10–0.55 on metal and 0.15–0.95 on dielectric. It clamps albedo: each channel of a dielectric to sRGB 30–240, and the brightest channel of a metal to 180–250, with the hue kept.
   - It writes the normal map as PNG. The colour map stays JPEG (quality 95).
   - It changes a map only when a rule moves it, so a second run on a clean prop changes nothing.

   Options:
   - `--class hero` gives a prop in view at spawn the hero texture size. `--triangles N` replaces the class budget (clutter 2,000, medium 6,000, hero 15,000).
   - `--stone` pulls warm, light colours to the saturation of the kit limestone. Use it for a stone prop that came out ochre. It does not change dark timber or colours that are not warm.
   - `--material brass` gives every face a kit material (`limestone`, `brass`, `gold`). `--parts` prints the connected parts of the model, largest first; `--material brass:1,2` then gives the kit material to parts 1 and 2 only.

   The clean-up stops with `prop-cleanup: error:` and exit code 1 when it cannot fix the model: the triangle budget is out of reach, the model has textures but no UVs, or a material graph is not the one that the glTF importer makes. The rules are in `src/orrery_art/materials.py`.
8. **Review.** `just render-prop lamp` writes `build/props/lamp.png`: the prop from the front, the right, the back and the left, beside the marble and a block of each kit material, in neutral light. Look at the size, the shape and the colours against the kit blocks. Then look at the prop in `just gallery`.
9. **Level.** In a level script: `kit.prop("lamp", at=(4.0, 2.0, 0.0), rotation=(0.0, 0.0, 90.0), collider="box")`. A prop is decoration: it does not collide unless `collider` is `box` or `cylinder`, and then only that simple shape collides. The marble rolls only on our own kit pieces.

A rerun of a Tripo command after a time-out waits for the same task (its task file is `<output>.task.json`), even if the inputs have moved. Tripo runs one image task at a time on an account (views, edit-views); a busy account answers HTTP 429, and the tool waits for `Retry-After` and tries again.

A prop is not a LevelObject: it has no script and no marker. It is a mesh in the level `.glb`.

## Outputs and recipes

Everything goes to `build/art/` (git-ignored): `images/`, `models/`, `batches/` and `spend.jsonl`. Each output has a recipe, `<file>.json`: the service and endpoint, the model, the prompt or the inputs, every request field, the seed, the token usage, the estimated and billed cost, the batch or task id, the date and `"ai_generated": true`. Only the cleaned props in `assets/props/` are committed.

## Tests and code

`just test-art` runs the tests with mocked OpenAI and Tripo APIs. They make no paid call. The material rule tests need no Blender. The prop tests run `prop_cleanup.py`, `render_prop.py` and `kit.prop` in headless `blender-5.2`, and they skip when it is missing.

The Tripo client in `src/orrery_art/tripo.py` runs any task type: a `Task` is an endpoint, its JSON options (local files as `Path`s, which it uploads) and its outputs. `image_to_multiview`, `edit_multiview`, `model` and `texture` are thin functions that return a `Task`; a later step (`mesh/decimate`, `mesh/uv`, `mesh/segment` ...) is one more.
