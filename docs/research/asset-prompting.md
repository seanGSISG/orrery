> **Research snapshot, 2026-11-21.** No API was called and no money was spent. `docs/plan.md` records the decisions. Where this report and the plan differ, the plan wins.
> Sources: Tripo API docs (`developers.tripo3d.ai/en/docs/*` for text-to-image, image-to-image, image-to-multiview, edit-multiview, image-to-model, multiview-to-model, text-to-model, models-texture, mesh-segment, mesh-smartsegment, mesh-complete, mesh-decimate, mesh-uv, models-convert, files, task-query, rate-limits, billing, changelog) and `developers.tripo3d.ai/en/pricing`; OpenAI `developers.openai.com/api/docs/guides/image-prompting`, `.../guides/image-generation`, `.../guides/batch`, `.../pricing`, `.../models/gpt-image-2.6-sunburst` and `-flare`, `.../api/reference/resources/images/methods/generate` and `edit`; OpenArt `openart.ai/blog/gpt-image-2-6-prompt-guide/` (2026-11-20). Licensing and Steam: Tripo help and terms excerpts, `openai.com/policies/services-agreement/`, `partner.steamgames.com/doc/gettingstarted/contentsurvey`.

# Asset prompting and tool chains: GPT-Image-2.6 and Tripo

Legend: **[P]** = primary source (official docs, read in full). **[S]** = secondary (blog, search excerpt). **[I]** = our inference. **[U]** = could not verify.

Scope: GPT-Image makes 2D art (decals, signs, clock faces, plaques, concept boards, key art, icons). Tripo makes decorative 3D props. Nothing the marble rolls on comes from Tripo. A prop gets a simple collider at most (the task brief; `CLAUDE.md` rules).

## 0. Summary

**GPT-Image-2.6, top rules**

1. The model IDs are `gpt-image-2.6-flare` (fast, for drafts) and `gpt-image-2.6-sunburst` (detail and precise edits, for finals). There is no ID `gpt-image-2.6`. [P]
2. Write the prompt in labeled blocks in a fixed order: use, subject, composition, style, constraints. Start with what the image is for. [P]
3. Name things a camera can see: materials, light direction, 2 to 4 colours. Do not use mood words alone. [P]
4. Quote exact text, say how often it appears, where it sits and in what letters. Spell odd words letter by letter. Check every word. [P]
5. For a decal, ask for transparency twice: in the prompt, and with `background: "transparent"` and `output_format: "png"`. Then check the decoded alpha channel. [P]
6. Edit one thing at a time. Write "change only X" and a keep list. Number each reference image and give it one role. [P]
7. Put exclusions in a constraints block. The API has no negative-prompt field. [P]
8. Draft with Flare at `quality: "medium"`. Finish with Sunburst at `quality: "high"`. Keep the prompt and settings the same when you switch. [P]

**Tripo, top rules**

1. The API is v3: `https://openapi.tripo3d.ai/v3`. Use the P series (`P1-20260311`) for props. It makes low-poly meshes straight from `face_limit` (50 to 20,000 triangles). [P]
2. Feed it one clean concept image: one object, whole in frame, plain light backdrop, soft shadowless light. [P: "clean background, minimal occlusion"; I: the lighting advice]
3. Send `texture_version: "v3.5-20260815"` and `delight: true` explicitly. If you omit `delight`, it is `false`. [P]
4. Make the geometry without texture first (40 credits), then texture it (10 credits). The total is the same as one textured call (50). Re-texturing then costs 10, not 50. [P prices; I: the workflow]
5. Skip segment, complete, decimate and UV for normal props. P-series output is already low-poly and UV-wrapped. [P for the claim that the generation call can export UVs; I: that it is enough]
6. Fix scale, origin, materials and texture size in our own Blender script. It costs nothing.

**Cost per prop** (P1, multiview path): about 70 credits = **USD 0.70**, plus a retry allowance of USD 0.70. Section 4 has the table.

**Tripo endpoints the tooling must support:** see section 3.7.

## 1. GPT-Image-2.6

### 1.1 Facts

| Item | Fact | Source |
|---|---|---|
| Models | `gpt-image-2.6-flare` (speed), `gpt-image-2.6-sunburst` (detail, edit accuracy). Both do generation, edits and transparent backgrounds. | [P] image-prompting, model pages |
| Endpoints | `POST /v1/images/generations`, `POST /v1/images/edits` (Image API). The model pages list Responses and Chat Completions as "Not supported". | [P] |
| `quality` | `low`, `medium`, `high`, `xhigh`, `max`, `auto`. It sets how much visual detail renders, such as texture and small lettering. | [P] guide. The API reference text lists `xhigh` and `max` only for 2.5 models. The guide says 2.6 supports them. Test before relying on it. |
| `complexity` | `low`, `medium`, `high`. Default `high`. It sets how much the model plans before it renders. No separate fee. Use `low` for small edits. | [P] |
| `size` | `auto`, `1024x1024`, `1536x1024`, `1024x1536`, or any `WIDTHxHEIGHT`: both sides a multiple of 16, ratio 1:3 to 3:1, longest side at most 3840, total pixels 655,360 to 8,294,400. | [P] guide |
| `background` | `auto`, `opaque`, `transparent`. Use `png` or `webp` for transparent. | [P] |
| `output_format` | `png`, `jpeg`, `webp`, `svg`, `gif`. Only JPEG and WebP take `output_compression`. SVG: `n` must be 1, no edit endpoint. | [P] |
| `n` | 1 to 10. | [P] reference |
| Edits | Up to 16 input images (`images[]`, each at most 20 MB). `markup`: a transparent PNG overlay, same pixel size as image 1, at most 16,777,216 pixels and 50 MB, cannot combine with `mask`. Do not send `input_fidelity`. | [P] reference and guide |
| Prompt length | At most 32,000 characters. | [P] reference |
| Latency | Complex prompts can take up to 2 minutes. | [P] guide |
| Access | Image models may need API Organization Verification. | [P] guide |
| Moderation | `moderation: "low"` or `"auto"`. All prompts and images are filtered. | [P] |
| Price | Image output USD 30 per 1M tokens. Image input USD 8, text input USD 5 per 1M. The number of output tokens per image depends on size and quality. The guide only gives a JS calculator, so we could not read per-image costs for 2.6. | [P] pricing, guide |
| Batch | The pricing page lists a Batch rate for 2.6 (output USD 15 per 1M). The batch guide names only the 2.5 models for images. The 2.6 model pages say `v1/batch` is "Not supported". The sources disagree. Our volume is small, so do not plan on Batch. | [P], conflict |
| Ownership | OpenAI Services Agreement 4.1: the customer owns all Output, and OpenAI assigns its rights, if any. | [S] excerpt of `openai.com/policies/services-agreement/` (effective 2026-01-01) |
| Provenance | OpenAI adds C2PA content credentials to images from its image models. Keep the original files unedited in the art source folder. | [S] OpenAI posts, 2025-04 and 2026-05 |

Per-image cost proxy [I]. `gpt-image-2` has the same USD 30 per 1M output rate. Its documented per-image prices are: 1024x1024 low 0.006, medium 0.053, high 0.211; 1024x1536 and 1536x1024 low 0.005, medium 0.041, high 0.165. Token counts for 2.6 may differ, and `xhigh` and `max` cost more. We scale by pixel count for other sizes. This is a rough guess. Log `usage` from the first real call and re-plan.

### 1.2 Rules

These rules follow the OpenAI guide [P] and the OpenArt guide [S], and the lessons in `docs/style/README.md` (mood images).

1. **Order.** Write use, subject, composition, style, constraints. For long prompts use labeled blocks (`USE:`, `SUBJECT:`, `STYLE:`, `CONSTRAINTS:`). Change one block per retry. [P, S]
2. **State the use.** "A flat decal for a clock face" or "key art with space for a logo on the left" changes the layout the model picks. [S]
3. **Describe what the camera sees.** Name materials ("weathered honey-coloured limestone", "aged brass with warm tarnish"), light (direction, strength, colour), and 2 to 4 colours. Say "photorealistic" or "real photograph" when you want it. Camera words (35mm, 24mm, f/8) are cues, not physics. [P, S]
4. **Size things against known objects.** The style board learned that gems hover or shrink unless the prompt ties them to the 0.4 m glass sphere and the floor, and that a ramp must be "one plain inclined slab". Do the same for every scale-critical item. [P: docs/style/README.md, Qwen runs; I: applies to GPT-Image]
5. **Text.** Quote the exact words. Say how many times each appears, where, how big, and in what letters. Spell rare words letter by letter. Add "no other text". Use `quality: "high"` for small or dense text. Read every word of the result. Fix a typo with an edit, not a new image. [P, S]
6. **No numerals on clock faces.** `docs/style/README.md` lists numerals on the clock face as a known fault of the `mood-dawn` image. Our faces use plain brass bars. [P: repo]
7. **Transparency.** Ask in the prompt ("isolated on a fully transparent background, no shadow, no checkerboard") and set `background: "transparent"` with `png` or `webp`. Do not set `output_compression` for PNG. Open the file and check that the alpha channel has transparent pixels. Test the edge on a white page and a black page. Repeat the transparency line in every follow-up edit. [P, S]
8. **Flat decals.** Ask for a straight-on orthographic view, even light, no cast shadow, no reflection of the environment. Light is added by Godot. [I]
9. **Edits.** One change per edit. Write the change, then "Keep: ..." and list what must not move. Paste the same keep list into each edit. If part of an image must stay pixel-identical, composite the approved region into the original. [P, S]
10. **References.** Number each image and give it one role: "Image 1 sets the material look and the light only. Draw a new subject." A reference with no role gets mixed in. [P, S]
11. **Exclusions.** Put them in `CONSTRAINTS:` ("No text, no people, no logos, no watermarks. Original design only."). Do not stack keywords such as "4k, ultra detailed". [P, S]
12. **Quality and complexity.** `quality` is detail. `complexity` is planning. Change one at a time and keep the other fixed. Use `low` complexity for small edits. Use explicit values: `auto` hides the cost. [P]
13. **Sizes.** Draft at 1024x1024 or 1536x1024. Make finals at the target size. Use 16:9 sizes that are multiples of 16 (`1536x864`, `2048x1152`, `3840x2160`). Square is typically fastest on `gpt-image-2` [P]; we did not verify it for 2.6.
14. **Draft, then finish.** Iterate in Flare, then run the same prompt in Sunburst. [S, P]
15. **A set must match.** Reuse the shared style blocks (1.3) word for word. After the first approved image, pass it as image 1 for the next ones. [P: reference roles; I: set consistency]
16. **Originality.** Prompts describe the look in our words. They never name existing games, brands, characters or living artists. End each prompt with "Original design only." [P: OpenAI examples use the same line; repo rule]
17. **Icons.** For flat icons, try `output_format: "svg"` with simple shapes and few flat colours. The API paints a reference image first, then writes the SVG. [P]

### 1.3 Shared style blocks

Paste them word for word.

`SCENE_STYLE` (look in the level, golden dawn):

```
STYLE: Photographic realism with restraint. Materials: weathered honey-coloured limestone with fine pores and soft edge wear; aged brass with a warm tarnish and fine scratches; dark oiled timber. Light: low golden sunrise from the left, long soft shadows, thin haze, a pale blue sky with a soft peach band at the horizon. Natural colours, fine grain. No glow, no bloom, no lens flare.
```

`ASSET_STYLE` (for decals and for images that feed Tripo; neutral light so that Godot's light is the only light):

```
STYLE: Photographic realism with restraint. True-colour matte and satin materials as seen under neutral light. Soft, even, shadowless light from all sides, like inside a light tent. No cast shadow, no hard highlights, no mirror reflections, no glow. Backdrop: plain seamless light grey with nothing else in the frame.
```

### 1.4 Prompt templates

Each template lists its API settings. Fill the `[slots]`.

**T1. Brass clock-face decal, transparent.** Settings: Sunburst, `1024x1024`, `quality: high`, `background: transparent`, `output_format: png`. Godot gives the roughness and metallic values from the kit brass material. The image sets albedo, and its alpha cuts the shape.

```
USE: A flat game decal for the face of a street clock. Straight-on orthographic view, no perspective.
SUBJECT: A circular clock face centred in a square frame, filling 92 percent of the width. A thin aged-brass rim. Inside it, a satin-brass dial with twelve plain raised bars for the hours, longer at the 12, 3, 6 and 9 positions, and a fine track of small minute bars. Two slim brass hands: a short hour hand and a long minute hand, set to ten past ten. A small round brass boss at the centre. No numerals and no letters.
STYLE: Photographic realism with restraint. Aged brass with soft warm tarnish, fine brushed grain and a few hairline scratches. Soft, even, shadowless light from all sides. No mirror reflections, no glow, so the colours read as base colour.
CONSTRAINTS: Fully transparent background outside the rim, with a crisp edge and no halo. Do not draw a checkerboard, a backdrop, a wall or a drop shadow. No text of any kind, no logos, no watermarks. Original design only.
```

**T2. Shop sign for the town square.** Settings: Sunburst, `1536x1024`, `quality: high`, `background: opaque`. The shop name is invented. Search it once before you ship it.

```
USE: A front-on texture for a hanging shop sign in a clockmaker's town square, for a game prop. Flat orthographic view. The sign fills the frame with a thin margin of plain light grey.
SUBJECT: A rectangular sign board of dark oiled timber with a gently arched top, a narrow aged-brass frame and two brass hanging rings at the top corners. Hand-lettered gold-leaf capitals in two lines, centred. Line 1: "OSWIN & DAUGHTER" in large letters. Line 2: "CLOCKMAKERS" in smaller letters. Under line 2, a small brass cog-wheel between two short rules.
TEXT RULES: Draw exactly these two lines, once each, and no other text. Spelling: O-S-W-I-N, D-A-U-G-H-T-E-R, C-L-O-C-K-M-A-K-E-R-S.
STYLE: [ASSET_STYLE] The paint is old and slightly worn at the edges. The gold leaf shows fine cracks.
CONSTRAINTS: No people, no extra signs, no watermark, no logo. Original design only.
```

**T3. Engraved brass plaque, transparent.** Settings: Sunburst, `1536x1024`, `quality: high`, `background: transparent`, `png`. Follow-up edit for a height map (an untested idea [I]): pass T3's output as image 1 and ask "Make a greyscale height map of image 1, same layout, white is raised, black is recessed, no other change." If it fails, build the normal map from the albedo in Blender.

```
USE: A flat game decal for a plaque on a stone wall. Straight-on orthographic view.
SUBJECT: A rectangular aged-brass plaque with rounded corners and four small round screw heads. Engraved capital letters, dark with age in the grooves, centred in two lines. Line 1: "CLOCKMAKERS' SQUARE". Line 2: "Set in stone, kept in brass." A fine engraved line border runs inside the edge.
TEXT RULES: Exactly these two lines, once each. No other text. Spelling of line 1: C-L-O-C-K-M-A-K-E-R-S, apostrophe, S-Q-U-A-R-E.
STYLE: [ASSET_STYLE] Soft warm tarnish, fine scratches, no mirror reflections.
CONSTRAINTS: Fully transparent background outside the plaque, crisp edge, no halo, no shadow, no checkerboard. No logos, no watermark. Original design only.
```

**T4. Zone concept board (one view per image).** Models place inset panels badly [I]. Make one image per view and compose the board in our tooling. Keep `SCENE_STYLE` identical. Settings: Flare draft `1536x864`, `quality: medium`; Sunburst final `2048x1152`, `quality: high`.

```
USE: Concept art for a new game zone, [VIEW: wide establishing view from the marble's height | macro of the main floor material | one hero landmark].
SUBJECT: [ZONE, for example: the sky-clockwork world above the cloud sea.] A course of broad weathered limestone decks with a low rim of aged brass and no railings. Ramps are one plain inclined slab with no steps. [KEY PLACES: name each one, with its size against a clear glass sphere 0.4 m across that rests on the stone floor and casts a shadow.] [HERO LANDMARK: for example, a huge horizontal brass gear carrying a stone deck.]
COMPOSITION: High three-quarter view looking down about forty degrees. The course fills most of the frame. The sky is empty.
[SCENE_STYLE]
CONSTRAINTS: No text, no numerals, no people, no stairs, no lit windows, no watermark. Original design only.
```

**T5. Store capsule key art, no text.** Settings: Flare draft `1536x864`, `quality: medium`; Sunburst final `3840x2160`, `quality: high` (the largest allowed size [P]). We add the title in our own type. Steam art sizes and safe areas were not read here [U]: check Steamworks art specs before the final crop.

```
USE: Key art for a game's store page, with a calm area on the left third for a title logo that we add later.
SUBJECT: A clear glass marble forty centimetres across, with a turning brass orrery of three rings and three small planets inside it, in the lower right foreground on a pale limestone ledge. Behind it, a climb of floating clock-tower stonework rises through thin cloud toward a pale sky.
COMPOSITION: Landscape, the marble about one fifth of the frame width, the climb leading the eye up and to the left, the left third of the frame quiet.
[SCENE_STYLE]
CONSTRAINTS: No text, no logo, no people, no watermark. Original design only.
```

**T6. Prop concept image that feeds Tripo.** Settings: Flare drafts `1024x1024`, `quality: medium`; Sunburst final `1024x1024`, `quality: high`, `background: opaque`. Use a plain light backdrop. Ask for the whole object.

```
USE: A single prop for a game, to be turned into a 3D model.
SUBJECT: [PROP, with real size and parts, for example: a wooden market handcart, 1.2 m long, two spoked wheels, a flat bed holding three rough linen sacks and one small crate, a pair of long wooden handles.] The whole object is visible, centred, nothing cut off, with space around it.
COMPOSITION: Three-quarter view from slightly above, the object filling about 80 percent of the frame. One object only.
[ASSET_STYLE] Materials: [for example: weathered oiled timber, dark iron tyres, coarse linen.]
CONSTRAINTS: No people, no hands, no text, no extra objects, no ground shadow, no environment. Original design only.
```

### 1.5 Cost estimate for the trial

Prices are proxies from section 1.1 [I]. All numbers are USD.

| Item | Count | Settings | Each | Total |
|---|---|---|---|---|
| Prop concept drafts (Flare) | 15 | 1024², medium | 0.053 | 0.80 |
| Prop concept finals (Sunburst) | 10 | 1024², high | 0.211 | 2.11 |
| Decals and sign (T1 to T3): 2 drafts + 2 finals each | 3 sets | 1536x1024 | 0.41 per set | 1.24 |
| Zone concept (T4): 3 views, 2 drafts + 2 finals each | 3 sets | 1536x864 / 2048x1152 | 0.57 per set | 1.71 |
| Store capsule (T5): 3 drafts + 2 finals | 1 set | 2048x1152 / 3840x2160 | 1.92 per set | 1.92 |
| Fix-up edits | 6 | 1536x1024, high | 0.15 | 0.90 |
| **Sum** | | | | **8.68** |
| With a 1.5x allowance | | | | **13.0** |

This fits in USD 20. Stop rule: after the first Sunburst `high` 1024x1024 call, read `usage`. If it costs more than twice the proxy (above USD 0.42), re-plan before you run the rest.

## 2. Tripo API v3: what each call does

### 2.1 Basics [P]

- Base URL `https://openapi.tripo3d.ai/v3`. Header `Authorization: Bearer <key>`.
- All generation and processing calls are asynchronous. A call returns `{"code":0,"data":{"task_id":...}}`. Poll `GET /v3/tasks/{task_id}` or use a webhook. Status is `queued`, `running`, `success`, `failed` or `cancelled`. Treat `banned` and `expired` as terminal. A bounded wait is needed for unknown values. `output` has `model_url` (a GLB) and `rendered_image_url`. `credits_consumed` can have 2 decimals: parse it as a float.
- Credits are frozen when a task starts and returned when it fails or is cancelled. Failed and cancelled tasks cost nothing. 1 credit = USD 0.01.
- Inputs: a public URL, a `file_token` from `POST /v3/files` (images JPEG or PNG at most 20 MB; models at most 150 MB), or the `task_id` of an earlier task.
- Limits: rate limit gives HTTP 429 with code `1007`. A full concurrency pool gives 429 with code `2000` and a `Retry-After` header. Default concurrency per category: H-series generation 10, **P-series generation 5**, **image generation 1** (text-to-image, image-to-image, image-to-multiview, edit-multiview), model processing 5 (texture, convert, refine), mesh operations 10 (segment, complete, retopology). The tooling must run image tasks one at a time.
- Balance and usage: `GET /v3/account/balance` and `/v3/account/usage`. A usage history call (`/v3/account/usage/history`, up to 31 days) exists for reconciliation.
- Output URLs: the docs give no lifetime [U]. Download at once.
- Do not set `export_orientation` on generation if you will post-process. Convert at the end (docs advice). [P]

### 2.2 Prices [P]

Pricing page, 2026-11-21. The P-series tab loads only after a click, so we rendered it in a headless browser. The P2 numbers match the changelog (100 / 110 / 120 / 130).

| Operation | Credits | USD |
|---|---|---|
| **P1 multiview-to-3D**, no texture / standard texture | 40 / 50 | 0.40 / 0.50 |
| P1 text-to-3D, no texture / standard | 30 / 40 | 0.30 / 0.40 |
| **P2 multiview-to-3D**, no texture / standard texture | 100 / 110 | 1.00 / 1.10 |
| H series image or multiview to 3D, no texture / standard | 20 / 30 | 0.20 / 0.30 |
| H add-ons: HD texture +10, 8K texture +20, HD geometry +20, quad +5, smart low-poly +10, parts +20 | | |
| Texture task: fast 10, standard 10, HD 20, 8K 30 | | 0.10 to 0.30 |
| Image to multiview | 10 | 0.10 |
| Edit multiview | 5 per edited image | 0.05 |
| Retopology: v1 10, v2 30, v3 triangle 35, v3 quad 40 | | |
| Smart UV | 20 | 0.20 |
| Segmentation | 40 | 0.40 |
| Smart segmentation: model 55, image 85 | | |
| Part completion: default 50, quick cap 30 | | |
| Format convert: basic 5, advanced 10 | | |
| Image generation (text or image to image) | seedream 5; banana 5; banana2 10 to 15; banana_pro 15 to 20; chat_image_2 10 (15 at 4K), `high` quality 20 / 25 / 40 for 1K / 2K / 4K | |

The "advanced" convert price applies when you set `quadface_limit`, `flatten_bottom`, `flatten_bottom_threshold`, `texture_size`, `texture_format`, `pivot_to_center_bottom` or `scale_factor`.

A P-series texture add-on: P2 standard +10, detailed +20, extreme +30 (changelog). The P1 numbers for detailed and extreme are not listed [U]. Texture resolution for `standard` is not stated [U]. `extreme` is 8K. The convert call defaults to a 4096 px diffuse map.

### 2.3 Endpoints

| Endpoint | What it does | Key inputs and options | When to use it |
|---|---|---|---|
| `POST /generation/text-to-image` | Makes an image from text. | `prompt` (at most about 600 English words, key items first, `--no` for exclusions), `model` (`seedream_v5`, `seedream_v4`, `banana`, `banana_pro`, `banana2`, `chat_image_2`, `chat_image_2.5_flare`, `chat_image_2.5_sunburst`), `size`, `quality` (`chat_image` only), `background` (2.5 models only), `output_format`, `template`. | Not our default: GPT-Image makes the concept images. Use it only if OpenAI access fails. The docs do not say that `chat_image_*` is OpenAI's model [U]. |
| `POST /generation/image-to-image` | Edits or restyles from reference images. | `input` or `inputs` (up to 4 seedream, 10 banana, 16 chat_image), `prompt`, `template` (`3d_enhance`, `variants`, ...), `size`, `quality`. | `template: "3d_enhance"` may clean a concept image for 3D. Untested [I]. |
| `POST /generation/image-to-multiview` | Makes front, left, back and right views of one object from one image. | `input` only. Output `generate_multiview_image.{front,left,back,right}_view_url`. | **Default step** before the 3D call. It shows you the hidden sides for 10 credits, before the 40-credit call. |
| `POST /generation/edit-multiview` | Edits views of an `image_to_multiview` task. | `input` = that task ID. `prompts[]`: 1 to 4 items `{view, prompt}`, each prompt at most 1024 characters. | Fix a bad view (a wrong back, a missing wheel). 5 credits per edited view. Skip if the views are fine. |
| `POST /generation/image-to-model` | One image to a 3D model. | H: `model v3.1-20260211`, `face_limit`, `texture`, `pbr`, `texture_quality`, `texture_version`, `delight`, `geometry_quality`, `quad`, `smart_low_poly` (face_limit 500 to 20,000), `generate_parts`, `auto_size`, `model_seed`, `texture_seed`, `export_uv`. P: `P1-20260311` (`face_limit` 50 to 20,000) or `P2-20260801` (triangles 48 to 50,000; quads to 25,000, `quad`). | Simple props: skip multiview and send the image. Same price as multiview-to-model. |
| `POST /generation/multiview-to-model` | 2 to 4 views to a 3D model. Same options as above. | `inputs`: view-key objects `{front|left|back|right: url|file_token}` (front needed, at least 2 views), or `[{task_id}]` of an `image_to_multiview` or `edit_multiview` task. | **Default model step.** |
| `POST /generation/text-to-model` | Text to 3D. | As above. | Not used. We want control of the look through the concept image. |
| `POST /models/texture` | Makes new texture maps for an existing model. | `input` (task ID, token or URL; GLB, GLTF, FBX, OBJ, STL), `model` (`v3.5-20260815` default), `texture_prompt` (`text`, `image`, or `images` by view; one only; `style_image` with `text`), `pbr` (default true), `texture_quality` (`fast`, `standard`, `detailed`, `extreme`), `texture_seed`, `texture_alignment`, `delight`, `bake` (default true), `part_names`. | **Default texture step** after a no-texture geometry call. Also a 10-credit fix for a bad texture. Send the reference images again (the docs say this is "strongly recommended"). |
| `POST /mesh/segment` | Splits a model into parts named `tripo_part_N`. | `model` v1 (geometry) or v2 beta (semantic; `segmentation_granularity`, `split_by_connectivity`, `ref_image`). | Only for a prop with a moving part. Not for the trial. |
| `POST /mesh/smartsegment` | Segmentation plus modelling in one call. | `seg_type` `image` or `model` (GLB, needs `transform`), `granularity`, `hint`. | Same as segment. More expensive. Not for the trial. |
| `POST /mesh/complete` | Fills holes in segmented parts. | `input` = a `mesh/segment` task, `completion_mode` `ai_completion` or `quick_cap`, `part_names`. | After segment, only. |
| `POST /mesh/decimate` (retopology) | Reduces the triangle count. | `model` v1 basic, v2 smart (default), v3 newest. `face_limit` (v3: 500 to 20,000 triangles), `quad`, `smart_uv` (v3 only, no extra cost), `bake` (default true), `part_names`. | Only if a model is over budget. P-series meshes are already at the `face_limit`. |
| `POST /mesh/uv` | New UV layout, remaps the texture. | `input` at most 80,000 triangles, `bake`. Returns a UV atlas preview (`uv_render_url`). | Only if the UVs stretch or overlap. |
| `POST /models/convert` | Changes format and applies simple changes. | `format` (GLTF, FBX, USDZ, OBJ, STL, 3MF), `face_limit`, `texture_size` (default 4096), `texture_format`, `pivot_to_center_bottom`, `scale_factor`, `export_orientation`. | Skip. Blender does it for free. |

### 2.4 Which model series

| Series | Result | Cost (multiview, no texture, then texture) | Use |
|---|---|---|---|
| P1 | Low-poly with clean topology. `face_limit` 50 to 20,000. Docs: start at 150 triangles for simple props and 250 for complex ones. | 40 + 10 | **Default.** |
| P2 | Same idea, newer. Triangles up to 50,000, optional quads. | 100 + 10 | One comparison run on the first prop. Use for a hero prop only if P1 fails. |
| H3.1 + `smart_low_poly` | "Hand-crafted clean topology style." The docs say it suits simple inputs and may fail on complex ones. Faces 500 to 20,000. | 20 + 10 + 10 = 40 | One comparison run on the first prop. |
| H3.1 plain | Up to 1.5M triangles. Docs call 50,000 to 100,000 "game-ready". That is too heavy for our props. | 20 + 10 | Not used. |

## 3. The prop pipeline

### 3.1 Recommended steps

| # | Step | Tool | Credits | Skip when |
|---|---|---|---|---|
| 1 | Concept image (T6). Check it by eye: whole object, even light, right materials. | GPT-Image (OpenAI USD, section 1.5) | 0 | never |
| 2 | `image-to-multiview` | Tripo | 10 | A simple symmetric prop (barrel, crate): send the image to `image-to-model` instead. |
| 3 | `edit-multiview` on any bad view | Tripo | 5 per view | Views are fine. |
| 4 | `multiview-to-model`, `model: P1-20260311`, `texture: false`, `pbr: false`, `face_limit` from 3.2, `model_seed` set | Tripo | 40 | never |
| 5 | Look at the untextured GLB in Blender: shape, thickness, holes, scale. If bad, repeat step 4 (new seed) or step 3. | Blender | 0 | never |
| 6 | `models/texture`: `input` = step 4 task, `texture_version: v3.5-20260815`, `delight: true`, `pbr: true`, `texture_quality: standard`, `texture_seed` set, `texture_prompt.images` = the 4 views | Tripo | 10 | never |
| 7 | Segment, complete, decimate, UV | Tripo | 0 | skip by default (see 3.2) |
| 8 | Blender clean-up script (3.5) and export of GLB into `kit/` | Blender | 0 | never |
| 9 | Checks (section 5) in `just gallery` | Godot | 0 | never |

Steps 4 and 6 together cost 50 credits, the same as one textured call (P1 standard texture 50). So the split costs nothing extra and makes a bad texture cost 10 to fix. We did not verify that the texture task gives the same quality as the in-call texture [U]. The trial tests it (section 4).

Use `texture_quality: detailed` (HD, +10) only for a hero prop that shows within 3 m of the play camera.

### 3.2 Triangle and texture budget

The gates: Medium 1080p p99 GPU time at most 3 ms, VRAM at most 4 GB (`docs/design/visual-quality.md` §8, `docs/plan.md` §4.7). The measured test fixture is far under that (Medium p99 0.24 ms, 222 MB, `docs/plan.md` §4.7), so the fixture does not tell us the prop budget. The numbers below are our own **starting values [I]**. Calibrate with `just perf` once props sit in `ascent-z1`.

| Class | Size | `face_limit` start | Texture set | Example |
|---|---|---|---|---|
| Clutter | under 0.7 m | 800 to 2,000 | 1K | barrel, sack, crate |
| Medium | 0.7 to 2.5 m | 2,000 to 6,000 | 1K | handcart, fountain |
| Tall or hero | over 2.5 m, or in view at spawn | 6,000 to 15,000 | 2K | street clock, lamp post |

- Level cap [I]: at most 150 prop instances, at most 20 unique meshes, at most 300,000 prop triangles in view. Average 2,000 triangles times 150 is exactly 300,000. Shadow cascades draw the geometry again (the Medium preset has 4 sun splits), so keep the margin.
- Reuse the same mesh and material resources for repeats. Use `MultiMeshInstance3D` for large repeats, and set a visibility range for small props [I].
- Textures: a 1K BC7 map with mipmaps is about 1.4 MB. A 2K map is about 5.6 MB (arithmetic [I]). A prop with 3 maps (albedo, normal, packed occlusion-roughness-metal) is about 4 MB at 1K and 17 MB at 2K. 17 props at 1K and 3 at 2K come to about 120 MB. That fits the 4 GB gate and the level texture estimate of 0.5 GB in `docs/design/visual-quality.md` §6.
- The texel targets in `docs/design/visual-quality.md` §6 apply: 1024 px/m close, 512 px/m middle, 256 px/m far. A 1 m prop in the middle zone needs 512 px, so 1K is enough.
- Tripo's native texture size is not documented [U]. Check the maps in the first GLB. Down-sample to the class size in Blender.
- Godot makes mesh LODs on import for static meshes (`visual-quality.md` §2 lists a mesh LOD threshold), so a 6,000-triangle prop should be cheap far away [I].

### 3.3 Skip rules

- **Segment, smart segment, complete:** only for a prop with a part that moves (clock hands, a wheel). The path costs 40 + 50 = 90 credits and needs a texture re-run. Cheaper: make the moving part in Blender, or use the kit. Not for the trial, except one optional test on the street clock.
- **Decimate (retopology v3.0, 35 credits):** only for an H-series result or an over-budget mesh. P-series meshes stop at `face_limit`.
- **Smart UV (20 credits):** only if the UV atlas stretches or overlaps. Generation exports UVs by default (`export_uv: true`) [P]. We expect the texture to sit on those UVs [I].
- **Convert:** never. Blender does scale, origin and format for free.
- **Multiview:** skip for simple props (3.1 step 2).

### 3.4 Keeping lighting out of the textures

The level is lit by Godot (baked `LightmapGI`, one sun). A texture with baked shadow or a baked highlight gives two shadow directions and fails rubric check 4 (`docs/design/visual-quality.md` §7).

1. **In the concept image:** use `ASSET_STYLE` (neutral, shadowless, no mirror reflections, no ground shadow). Do not put dawn light in a prop image. [I]
2. **In the Tripo calls:** send `texture_version: "v3.5-20260815"` and `delight: true` explicitly. The docs say that if you omit `delight` the default is `false`, and that it becomes `true` only if you name `v3.5-20260815` yourself. An explicit value always wins. [P]
3. **Re-send the reference images** in `texture_prompt.images` with every texture call. [P]
4. **Check `bake`.** The default is `true`: "Bake advanced material effects into base textures." We do not know whether this bakes light [U]. The trial compares `bake: true` and `false` on one prop (10 credits each).
5. **Measure in Blender** (script, 3.5): albedo sRGB between 30 and 240 for dielectrics and 180 to 250 for metals (`visual-quality.md` §6); metallic only 0 or 1; no pixel run above 240 in a smooth highlight shape; mean luminance of the lit side and the shadow side of the UV islands about equal.
6. **Look at it in the gallery** under the dawn sun and a second sun angle. The shade on the prop must follow the sun, not the texture.
7. **Fix:** re-run the texture with a new `texture_seed` (10 credits); clamp levels in Blender; or assign the kit brass or stone material to that part.

### 3.5 Blender clean-up (our script, no cost)

An asset script in `tools/blender/` should do this for each GLB [I]:

1. Import. Delete tiny loose islands. Merge by distance. Recalculate normals. Report non-manifold edges and the triangle count.
2. Scale to the real height from the prop spec (the marble is 0.4 m across; `auto_size` is not trusted [I]). Set the origin to the bottom centre. Apply transforms. The up axis is Y for glTF, and Godot matches it.
3. Materials: name `orrery_<prop>`. Snap metallic to 0 or 1. Clamp albedo into the allowed range. Set roughness limits per `visual-quality.md` §6 (brass 0.15 to 0.55, stone 0.45 to 0.95).
4. Down-sample the textures to the class size, as JPG (albedo, roughness) and PNG (normal), per `visual-quality.md` §6 (source files).
5. Add a hidden simple collider (box or convex hull). No trimesh from Tripo.
6. Put the GLB in `kit/props/` (Git LFS). `docs/plan.md` §4.3 allows hero props as `.blend` in `kit/`. Store a recipe file beside it: prompt, concept image path, task IDs, seeds, parameters, credits used, date. The same seed and the same input give the same mesh (docs: `model_seed`, `texture_seed`) [P], so the recipe makes the asset repeatable [I].
7. Write one line in `docs/licenses.md` for the AI model, as the repo rule says.

### 3.6 Orrery fit for the 5-prop trial

The three stall roofs, crates, planks and ramps of Ascent 1 are part of the route (`docs/levels/ascent-z1.md`). They must come from `kit/`, not from Tripo. The trial props below are decoration only. They sit beside the routes, and the marble may touch them only through a simple collider.

| # | Prop | Size | Class | Why it tests something |
|---|---|---|---|---|
| 1 | Wooden market handcart with sacks and a crate | 1.2 m | Medium | Mixed materials, spoked wheels (thin parts) |
| 2 | Street lamp post, aged brass and dark iron | 3.2 m | Hero | Thin tall metal, brass look |
| 3 | Stone drinking trough with a brass spout | 1.4 m | Medium | Stone and brass together, no water |
| 4 | Three strapped barrels | 0.9 m | Clutter | Cheap repeatable clutter, tight budget |
| 5 | Street clock: stone pedestal and brass housing, with the face from the T1 decal added in Blender | 4 m | Hero | The chain from GPT-Image decal to 3D, and no numerals |

Sean owns the final choice of props.

### 3.7 Endpoints the tooling must support

**Tripo, required for the trial**

- `POST /v3/files` (upload an image, get a `file_token`)
- `POST /v3/generation/image-to-multiview`
- `POST /v3/generation/edit-multiview`
- `POST /v3/generation/multiview-to-model` (P1 and P2, and H for the one comparison) with `inputs` as view-key objects or `[{task_id}]`
- `POST /v3/generation/image-to-model` (the skip-multiview path)
- `POST /v3/models/texture` (with `texture_prompt.images`, `texture_version`, `delight`, `bake`, `texture_seed`, `part_names`)
- `GET /v3/tasks/{task_id}` (poll, read `credits_consumed`, read `output.model_url`)
- `GET /v3/account/balance`, and `GET /v3/account/usage` for reconciliation
- A download of `output.model_url` and `rendered_image_url` to disk at once

**Tripo, add after the trial, only if it proves useful**

- `POST /v3/mesh/decimate` (v3.0, `face_limit`, `smart_uv`, `bake`)
- `POST /v3/mesh/uv`
- `POST /v3/mesh/segment`, `/v3/mesh/smartsegment`, `/v3/mesh/complete`
- `POST /v3/generation/text-to-image` and `/v3/generation/image-to-image`
- `POST /v3/models/convert`
- Webhooks (polling is enough for us)

**Tooling behaviour** [I, from the docs above]

- Run image-category tasks one at a time (concurrency 1). Cap P-series tasks at 5.
- On HTTP 429, read `Retry-After`. Use backoff for code `1007`.
- Parse credits as floats. Keep a running total. Refuse to start a call when the total plus the call's known price passes the budget. Keep the price table in code, with its source date.
- A `--dry-run` mode that prints the plan and the cost and sends nothing.
- Write the recipe file (3.5 step 6) for every task.
- Never print or log the API key. Do not send project or personal text in prompts.

**OpenAI**

- `POST /v1/images/generations` and `POST /v1/images/edits` (multipart, up to 16 `images`). Parameters: `model`, `prompt`, `size`, `quality`, `complexity`, `background`, `output_format`, `n`, and `moderation`. Edits also take `markup`.
- Save the base64 result to disk, unedited. Log `usage` per call. Check that a transparent PNG really has transparent pixels.
- Organization Verification may be needed before the first call [P].

## 4. Cost table for the 5-prop trial

Budget: USD 20 on each API. Tripo prices are from section 2.2 [P]. OpenAI is in section 1.5.

**Tripo, per prop (P1 multiview path)**

| Step | Credits | USD |
|---|---|---|
| image-to-multiview | 10 | 0.10 |
| edit-multiview, 2 views on average | 10 | 0.10 |
| multiview-to-model P1, no texture, `face_limit` set | 40 | 0.40 |
| models/texture standard, `delight: true` | 10 | 0.10 |
| **Subtotal per prop** | **70** | **0.70** |
| Retry allowance: 1 new multiview (10), 1 new geometry (40), 2 new textures (20) | 70 | 0.70 |
| **Maximum per prop** | **140** | **1.40** |

**Tripo, trial total**

| Item | Credits | USD |
|---|---|---|
| 5 props, base | 350 | 3.50 |
| 5 props, full retry allowance | 350 | 3.50 |
| P2 comparison on prop 1 (100 + 10) | 110 | 1.10 |
| H3.1 + `smart_low_poly` comparison on prop 1 (20 + 10 + 10) | 40 | 0.40 |
| Texture `bake` true vs false, and `delight` true vs false, on prop 1 (4 texture runs) | 40 | 0.40 |
| HD texture on prop 5 (instead of standard) | 20 | 0.20 |
| Retopology v3.0 on the H result (35) and Smart UV (20) | 55 | 0.55 |
| Segment + complete on the street clock (40 + 50) | 90 | 0.90 |
| **Worst case** | **1,015** | **10.15** |
| **Left of USD 20** | | **9.85** |

Likely spend is about USD 4 to 6. Skip the optional lines if the first props look good.

**OpenAI:** about USD 8.7, or USD 13 with a 1.5x allowance (section 1.5).

## 5. Risks and checks

| Risk | Check or control |
|---|---|
| **Style mismatch.** Tripo textures and GPT images may differ from set A (honey limestone, aged brass, golden dawn). | Compare each prop in `just gallery ascent-z1` against `docs/style/review/` renders. Use identical `ASSET_STYLE`. Pass the first approved image as a style reference for the others. Fix hue and value in Blender, or assign the kit stone and brass materials. |
| **Baked lighting.** | Section 3.4. Rubric check 4 and 6 in `visual-quality.md` §7. |
| **Metal looks like flat yellow paint, or plastic.** | Check metallic is 0 or 1 and roughness is in range. Rubric check 5. Fall back to the kit brass for brass parts. |
| **Scale and pivot.** | The Blender script sets the real size and bottom-centre origin. Check the prop against the 0.4 m marble in the gallery. |
| **Topology and holes.** Thin parts (spokes, lamp arms) may break or merge. | View the untextured GLB before spending 10 credits on texture (step 5). Report non-manifold edges. Give thin items a larger `face_limit`. |
| **Texture stretch or seams.** | Look at the UV atlas. Run Smart UV (20 credits) only if needed. |
| **Hidden sides wrong** (back of the cart). | Look at the 4 views. Fix with `edit-multiview`. |
| **Text and numerals in 3D.** AI 3D text is unreliable [I]. | Keep text off Tripo props. Add signs, plaques and faces as decals from GPT-Image (T1 to T3). |
| **Text errors in GPT images.** | Read every word. Fix with an edit. |
| **Transparency fails** (white fringe, drawn checkerboard). | Check alpha. Test on white and black. |
| **Perf.** | `just perf` with props in place. Gates: Medium 1080p p99 at most 3 ms, VRAM at most 4 GB. |
| **Collision.** | Props get a hidden box or convex shape. Nothing from Tripo is a `Solid` the marble rolls on. |
| **Originality.** | Prompts never name games, brands, characters or living artists. Review each image for accidental logos or lookalikes. Search any invented shop name once. |
| **Licensing, Tripo.** The Tripo help page says paid users have full rights to use, modify, distribute and sell their models, and free users' outputs belong to Tripo [S]. The terms (read through secondary excerpts, last updated 2025-07-11 and an archive copy from 2026-11-18) say "Paid Users generally have all rights" (5.2.2) and give Tripo a licence to use and display content to run the service. They bar using outputs to build competing models. One summary says to keep AI labels or watermarks that Tripo adds [S]. We could not open `tripo3d.ai/terms` (HTTP 403). It is not stated that purchased API credits count as a "paid" account [U]. | Before the trial: Sean reads the terms in his logged-in Tripo account, confirms that bought API credits give commercial rights, and saves a dated copy. Record it in `docs/licenses.md`. |
| **Licensing, OpenAI.** Customer owns Output (Services Agreement 4.1) [S]. | Record the model ID and date. |
| **Steam disclosure.** The Steamworks content survey asks for "pre-generated" AI content that ships with the game and is consumed by players: artwork, sound, narrative, localization. It says efficiency tools used behind the scenes are not the focus. Store capsule and marketing art made with a generator also count in secondary summaries [S]. `docs/plan.md` §4.9 already says a store release must disclose AI-made music and 2D art. | Add 3D props and decals to that list. In `docs/licenses.md` record for each AI asset: tool, model ID, date, prompt or recipe path, task ID or `usage`, where it is used, and whether it ships. Generate the Steam disclosure from that file. |
| **Provenance data.** OpenAI images carry C2PA metadata [S]. | Keep unedited originals in the art source folder. |

## 6. Gaps and conflicts

- Per-image cost for 2.6 at each size and quality is unknown. Section 1.5 uses `gpt-image-2` prices as a proxy [I].
- Batch for 2.6: the pricing page lists a Batch rate, but the model pages say "Not supported" and the batch guide names only 2.5. We do not plan on Batch.
- `xhigh` and `max` quality: the guide says 2.6 supports them. The API reference text lists them for 2.5 only.
- Tripo P1 prices for detailed and extreme texture are not listed. The standard texture native resolution is not documented. The lifetime of output URLs is not documented.
- Tripo does not say what `chat_image_*` models are.
- Whether the split flow (geometry, then texture) matches the quality of an in-call texture, whether `bake` bakes light, and how well `delight` works on aged brass are all untested. Section 4 includes the tests.
- The 2.6 Flare and Sunburst quality gap on small text and on thin brass details is untested. The OpenArt guide says to use Sunburst for finals and close-up detail [S].
- Tripo licence text is read only through secondary excerpts.
- Steam art sizes and safe areas were not read.
