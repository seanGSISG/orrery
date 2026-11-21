# Style board

The style board sets the look of Orrery: materials, light, sky and scale. Sean approves it before any final art (ticket #5, `docs/plan.md` 2.11). Level layouts come from the level briefs, not from this board.

Open `review/index.html` to see the board.

**Status: not approved yet.** When Sean decides, write the choices into "Approved choices" below.

## Open choices

| Choice | Recommendation |
|---|---|
| Materials and light: candidate A, B or C | A. Honey limestone and aged brass match the art direction. B is cleaner and reads as new gold. C is the most weathered; its stains read as dirt. |
| Marble: A (glass, brass core) or B (blue stone, gold inlay) | A. The brass core shows the marble's roll, and the glass picks up each sky. B contrasts more with pale stone. |
| Gem look | Three cuts, one per colour, as rendered. |
| Noon and dusk skies | As rendered. The dusk scene is dark away from the sun; a level at dusk needs fill light for play. |

## Approved choices

None yet.

## The game look: Blender renders

`tools/blender/lookdev.py` builds one small play space at true scale and renders it with Cycles (OptiX, denoised, 1920x1080, 384 samples, AgX). Run from the repo root:

```sh
blender-5.2 -b --factory-startup --python-exit-code 1 --python tools/blender/lookdev.py
blender-5.2 -b --factory-startup --python-exit-code 1 --python tools/blender/lookdev.py -- --only a gem --samples 64 --scale 50
```

The second line is a quick preview of two shots. All nine shots take about 20 minutes on the RTX 5090; the cloud volume is the slow part.

### The play space

All sizes are in metres. The marble's radius is 0.2.

| Piece | Size | Notes |
|---|---|---|
| Plaza | radius 3.2 | Round tower top. Slabs laid in rings, a gold clock face set flush into the floor, a banked brass lip 0.44 wide and 0.16 high. |
| Safe route | 2.4 wide | Six marble widths. A straight, a 110 degree right turn banked up to 11 degrees, a straight. It climbs 1.1 to the terrace. Banked brass borders. |
| Shortcut beam | 0.8 wide | Two marble widths, no borders, a gold line along each edge. It leaves the safe route at the fork, 0.95 from the plaza, and climbs straight to the terrace. |
| Terrace | radius 2.2 | 1.1 above the plaza. |
| Bridge and small platform | 1.4 wide, radius 1.4 | The bridge drops 0.4 to the platform. |
| Gems | 0.5 across | 1.25 x the marble's diameter. The lowest point is 0.3 above the floor. |

Nothing has steps. Each route lies 2 mm above the floor that it overlaps.

### Materials

Every game material is plain PBR, so that it ports to a Godot `StandardMaterial3D`: colour, roughness and normal maps, a metallic value, a tint and a roughness factor. Floor slabs also carry a vertex colour (0.84 to 1.0) so that no two slabs match; the joints between them are filled flush with stone at 0.5. The stone tints are above 1 because the maps are darker than limestone; bake the tint into the colour map when a look is approved.

| Look | Stone (Poly Haven) | Brass (ambientCG) | Sky (Poly Haven) | Sun |
|---|---|---|---|---|
| A | `scuffed_cement`, tint (2.6, 3.0, 3.5), 1.5 m per repeat | `Metal007`, tint (1.0, 1.1, 1.4), metallic 0.85, roughness x 2.4 | `syferfontein_6d_clear_puresky`, strength 0.8 | 12 degrees, (1.0, 0.68, 0.42), 24 W/m2, exposure -1.75 |
| B | `concrete_wall_008`, tint (2.3, 2.45, 3.0), 1.6 m | `Metal048A`, tint (0.9, 0.8, 0.62), roughness x 3.0 | `qwantani_dusk_2_puresky`, strength 0.9 | 8 degrees, (1.0, 0.6, 0.46), 14 W/m2, exposure -1.5 |
| C | `dirty_concrete`, tint (1.6, 1.7, 1.9), 1.6 m | `Metal008`, roughness x 1.3 | `syferfontein_1d_clear_puresky`, strength 1.6 | 4.5 degrees, (1.0, 0.56, 0.3), 18 W/m2, exposure -1.4 |

- Gold inlays (all looks): `Metal048A`, tint (1.0, 0.82, 0.5), roughness x 5.
- Marble A: glass with a pale cool tint (0.74, 0.9, 1.0), IOR 1.65 and transmission 1, around a bold polished `Metal048A` orrery (a ball, three rings, three planets). The tint, the strong rim and the core make it stand out on warm stone from far away. Marble B: `Marble023`, tint (0.55, 0.8, 1.5), roughness x 0.3, clearcoat 1, with `Metal048A` orbit lines.
- Gems: glass with a colour, IOR 2.2, transmission 1, and a subtle emission in the same colour, so that the facets still catch the light. Every colour emits the same luminance. The hues follow the blue, orange and reddish purple of the Okabe-Ito colour-blind-safe set, and each colour has its own outline from any side: blue double pyramid (0.01, 0.1, 0.55), pointed at both ends; amber hexagon (0.8, 0.3, 0.0), flat at both ends; magenta brilliant (0.6, 0.02, 0.28), flat on top and pointed below. A point light 0.22 above the floor marks the spot below each gem. Gems cast no shadow.
- Gem beam: an additive cylinder, 3.2 high, that fades toward its top and its sides. In Godot: an unshaded additive material with a vertical gradient and a rim fade.
- Blob shadow: a dark disc with a crisp edge, 1.2 x the marble's radius, straight below the marble.

The backdrop is not a game material. The dawn cloud sea is a Cycles volume. The noon and dusk skies are Blender's multiple-scattering sky seen from 16 km and 80 km, with a cloud layer and stars made in the world shader, and one planet on a far sphere. The game gets each backdrop as a baked sky.

### Shots

| File | Subject | Look and sky |
|---|---|---|
| `render-a.webp`, `render-b.webp`, `render-c.webp` | High three-quarter view of the play space | Looks A, B, C, each with its dawn sky |
| `render-eye.webp` | Player's view: the marble close in the foreground, a gem and the brass lip beside it | A, dawn |
| `render-noon.webp` | Same view as the candidates | A; sky at 16 km, sun at 58 degrees, 24 W/m2, exposure -2.5 |
| `render-dusk.webp` | Same view as the candidates | A; sky at 80 km with its sun at -5.5 degrees, lamp at 7 degrees, (1.0, 0.56, 0.3), 12 W/m2, exposure 0.2; stars; one planet |
| `render-gem.webp` | Blue gem next to the marble | A, dawn |
| `render-marble-a.webp`, `render-marble-b.webp` | Marble candidates | A, dawn |

## Mood references: AI images

The mood references show atmosphere only. They are not the game look, and each one breaks at least one rule of the art direction (see "Known faults").

- Model: Qwen-Image-2512 (`qwen_image_2512_bf16.safetensors`, Apache-2.0, see `docs/licenses.md`), in the local ComfyUI.
- Settings for every image: 1664x928, 50 steps, guidance 3.0, sampler `euler`, scheduler `simple`, shift 3.1.
- `concepts.py` makes the three `mood-*` images again from the recorded prompts and seeds. The four `ref-*` images come from an earlier run; their prompts are recorded only here.
- Each tier got at most three attempts. What helped: tie the size and height of the gems to the glass sphere and the floor, give each gem a named place, and describe a ramp as "one plain inclined slab".
- Krea 2 is installed and may give more photographic images, but its license allows commercial use only below USD 1 million of yearly company revenue. It was not used.

### `mood-dawn.webp`: Dawn (Beginner): tower-top plaza

- Seed: `5101`. ComfyUI file: `output/orrery_style_v2/mood-dawn_5101_00002_.png`.
- Known faults: The gems stand in a group and hover about one marble height up. Numerals on the clock face.

<details><summary>Prompt</summary>

Aerial photograph at sunrise, looking down at about forty degrees onto the flat round top of an old stone tower that stands above a sea of clouds. The tower top is a wide open plaza of weathered pale limestone with a low rim of aged, slightly tarnished brass; a large clock face of plain brass bars and two brass hands is set flat into its floor. The plaza fills most of the frame. At the back, a broad smooth stone ramp, one plain inclined slab like a wheelchair ramp, rises to a smaller upper terrace, and large brass gears are built into the wall below that terrace. On the right a short flat stone bridge leads to a second, small round tower top. A clear glass sphere forty centimetres across rests on the stone floor and casts a shadow. Three cut gemstones float just above the floor, spread far apart across it. Each gemstone is about the size of the glass sphere, only slightly larger, and hovers a hand's width above the stone, right over its own shadow. A thin faint ray of light rises from each one. One is a sapphire-blue double pyramid, one an amber hexagonal cut, one a magenta round brilliant; each glows softly from inside. Low warm sunlight from the left, long soft shadows, thin haze, a pale blue sky with a soft peach band at the horizon. The sky is empty. Shot on a full-frame camera with a 24mm lens at f/8, natural colours, realistic exposure, fine grain.

Negative: stairs, steps, staircase, stairway, illustration, painting, digital art, CGI, render, 3D render, matte painting, fantasy art, oversaturated, glow, bloom, lens flare, collage, candles, lanterns, people, tiled floor, checkerboard, grid pattern, text, numerals, watermark, logo

</details>

### `mood-noon.webp`: Noon (Intermediate): fork course

- Seed: `5201`. ComfyUI file: `output/orrery_style_v2/mood-noon_5201_00003_.png`.
- Known faults: The amber gem hangs over the gap. The beam is as wide as a bridge.

<details><summary>Prompt</summary>

Aerial photograph at midday from very high altitude, looking down at about forty degrees onto a course of floating stone decks far above a layer of clouds. The course fills most of the frame and is made of weathered pale limestone with a low rim of aged, slightly tarnished brass. From a round platform in the foreground the course forks: a wide deck curves away to the left in one broad banked turn, and a single straight stone beam, one metre wide, crosses the open gap as a shortcut. Both end on a larger round platform that is reached by a broad smooth stone ramp, one plain inclined slab like a wheelchair ramp. A clear glass sphere forty centimetres across rests on the stone floor and casts a shadow. Three cut gemstones, each the size of a melon and only slightly larger than the glass sphere, float ankle-high above the paving, each right over its own shadow: one on the round platform beside the sphere, one on the wide curved deck and one on the stone beam. A thin faint ray of light rises from each one. One is a sapphire-blue double pyramid, one an amber hexagonal cut, one a magenta round brilliant; each glows softly from inside. Hard white sunlight from high above, short crisp shadows, very clear thin air, a deep clean blue sky that pales to white haze at the horizon. The sky is empty. Shot on a full-frame camera with a 24mm lens at f/8, natural colours, realistic exposure, fine grain.

Negative: stairs, steps, staircase, stairway, illustration, painting, digital art, CGI, render, 3D render, matte painting, fantasy art, oversaturated, glow, bloom, lens flare, collage, candles, lanterns, people, tiled floor, checkerboard, grid pattern, text, numerals, watermark, logo

</details>

### `mood-dusk.webp`: Dusk (Advanced): stacked platforms

- Seed: `5301`. ComfyUI file: `output/orrery_style_v2/mood-dusk_5301_00002_.png`.
- Known faults: The gems hover about two marble heights up, over the bumpers. The ramps are rough slabs.

<details><summary>Prompt</summary>

Photograph taken at dusk from the edge of space, looking down at about forty degrees onto five round stone platforms that float at different heights, stacked like terraces. The platforms fill most of the frame and are made of weathered pale limestone with a low rim of aged, slightly tarnished brass. Each platform is joined to the next by a broad smooth stone ramp, one plain inclined slab like a wheelchair ramp; one pair is separated by a short open gap. One platform is a huge horizontal gear of aged brass with a stone deck on top. Two low dome-shaped brass bumpers stand on the largest platform. A clear glass sphere forty centimetres across rests on the stone floor and casts a shadow. Three cut gemstones float just above the floor, spread far apart across it. Each gemstone is about the size of the glass sphere, only slightly larger, and hovers a hand's width above the stone, right over its own shadow. A thin faint ray of light rises from each one. One is a sapphire-blue double pyramid, one an amber hexagonal cut, one a magenta round brilliant; each glows softly from inside. Far below lies the curved horizon of the Earth, with a thin blue band of atmosphere and a faint orange line of sunset. Above it the sky is almost black, with a few faint stars. One large pale planet sits low on the horizon, half hidden by the haze of the atmosphere. The last warm sunlight comes from the left; long shadows, cool blue fill light, no lamps. Shot on a full-frame camera with a 24mm lens at f/8, natural colours, realistic exposure, fine grain.

Negative: stairs, steps, staircase, stairway, illustration, painting, digital art, CGI, render, 3D render, matte painting, fantasy art, oversaturated, glow, bloom, lens flare, collage, candles, lanterns, people, tiled floor, checkerboard, grid pattern, text, numerals, watermark, logo

</details>

### `ref-plaza.webp`: Plaza with a banked brass lip (earlier run)

- Seed: `1301`. ComfyUI file: `output/orrery_style/world-dawn_1301_00001_.png`.
- Known faults: Stairs. Small gems on the floor.

<details><summary>Prompt</summary>

Aerial photograph from a drone, a high three-quarter view that looks down at about forty degrees onto a wide open plaza of weathered limestone that floats above a sea of clouds. The plaza is the subject and fills most of the frame: about fifteen metres across, paved with large limestone slabs laid in rings around a large clock face that is set flat into the middle of the floor, with plain brass bars for the hours and two brass hands. A low border of aged, slightly tarnished brass runs along every open edge; there are no walls and no railings. At the back of the plaza a broad, smooth stone ramp with no steps rises to a second, smaller terrace one storey higher, and a few large brass gears are built into the wall under that terrace. A glass sphere forty centimetres across rests on the stone, small in the frame, and casts a shadow. Seven small faceted gems, red, blue and green, each half the size of the sphere, lie far apart on the plaza and the terrace. Early morning, just after sunrise: low warm sunlight from the left, long soft shadows, and at the top of the frame a pale blue sky with a soft peach band along the horizon. The sky is empty. Natural light from a single sun, consistent shadows, strong atmospheric perspective: distant things are paler, bluer and lower in contrast. Muted natural colours. Documentary photograph, full-frame camera, f/8, sharp focus, realistic exposure.

Negative: illustration, painting, digital art, CGI, 3D render, fantasy art, concept art, matte painting, oversaturated, vivid colours, glow, bloom, lens flare, light rays, HDR, symmetrical composition, collage, candles, lanterns, lit windows, text, letters, numerals, watermark, logo, people, tiled floor, checkerboard, grid pattern

</details>

### `ref-fork.webp`: Fork course (earlier run)

- Seed: `1101`. ComfyUI file: `output/orrery_style/world-noon-b_1101_00003_.png`.
- Known faults: Small gems on the floor.

<details><summary>Prompt</summary>

Aerial photograph from a drone, a high three-quarter view that looks down at about forty degrees onto a course of floating limestone decks high above a sea of clouds. The course is the subject and fills most of the frame. It starts on a round stone platform in the foreground and splits into two routes. The safe route is a wide deck, about four metres wide, that winds away to the left in two broad banked curves. The shortcut goes straight ahead: two narrow stone beams, each barely wider than the sphere, cross an open gap side by side. Both routes end on one large platform in the distance. Beside the gap, a long arm of aged brass on a stone pier carries a small round stone platform out over the clouds. A low border of aged, slightly tarnished brass runs along every open edge; there are no walls and no railings. A glass sphere forty centimetres across rests on the stone, small in the frame, and casts a shadow. A few small faceted gems, red, blue and green, each half the size of the sphere, lie along both routes. Midday in the stratosphere, thirty kilometres up, like a photograph from a high-altitude balloon: the sky at the top of the frame is a very dark blue and pales to a thin bright band of haze along the horizon, and the horizon is visibly curved. The cloud layer lies very far below, its shapes small. Hard white sunlight, short crisp shadows. The sky is empty, with no stars. Natural light from a single sun, consistent shadows, strong atmospheric perspective: distant things are paler, bluer and lower in contrast. Muted natural colours. Documentary photograph, full-frame camera, f/8, sharp focus, realistic exposure.

Negative: illustration, painting, digital art, CGI, 3D render, fantasy art, concept art, matte painting, oversaturated, vivid colours, glow, bloom, lens flare, light rays, HDR, symmetrical composition, collage, candles, lanterns, lit windows, text, letters, numerals, watermark, logo, people, tiled floor, checkerboard, grid pattern

</details>

### `ref-zone-2.webp`: Ascent zone 2: broken clock tower (earlier run)

- Seed: `2201`. ComfyUI file: `output/orrery_style/zone-2_2201_00002_.png`.
- Known faults: Spiral stairs, not a ramp. No gem.

<details><summary>Prompt</summary>

Photograph of a tall stack of floating stonework against a clear morning sky, seen from the side and a little from above. The pieces of a broken limestone clock tower hang motionless in the air at many heights, one above another, and form a climb with several ways up: ring-shaped stone floors, flat slabs several metres across, curved wall segments, and three very large gears of aged brass lying flat as platforms. Stone ramps, short flights of stairs and narrow stone beams link each level to the next in two or three places; some levels are separated by short open gaps. One long brass pendulum hangs below the highest piece. A glass sphere forty centimetres across rests on the stone, small in the frame, and casts a shadow. Far below, the slate roofs of a small town are pale in the morning haze. Clear early-morning sunlight from the right, soft blue shadows. Natural light from a single sun, consistent shadows, strong atmospheric perspective: distant things are paler, bluer and lower in contrast. Muted natural colours. Documentary photograph, full-frame camera, f/8, sharp focus, realistic exposure.

Negative: illustration, painting, digital art, CGI, 3D render, fantasy art, concept art, matte painting, oversaturated, vivid colours, glow, bloom, lens flare, light rays, HDR, symmetrical composition, collage, candles, lanterns, lit windows, text, letters, numerals, watermark, logo, people, tiled floor, checkerboard, grid pattern

</details>

### `ref-zone-3.webp`: Ascent zone 3: roofs and airships (earlier run)

- Seed: `2301`. ComfyUI file: `output/orrery_style/zone-3_2301_00002_.png`.
- Known faults: Stairs on the roofs. The airships are not joined to the roofs.

<details><summary>Prompt</summary>

Aerial photograph from a drone, a high three-quarter view that looks down at about forty degrees over the rooftops of an old town in mid-morning: steep slate and copper-green roofs, brick chimneys and a few brass weathervanes. Laid across the roofs is a network of flat stone decks and terraces at different heights, each about three metres wide, with a low border of aged brass and no railings. Stone ramps, plank bridges and steps link them; the routes fork and rejoin and climb from roof to roof. Two airships float moored above the highest roofs: long cream fabric envelopes, wooden gondolas with flat open decks, aged-brass fittings. Two separate gangways rise from the roof decks to the airships. A glass sphere forty centimetres across rests on the stone, small in the frame, and casts a shadow. Blue sky with a few large white clouds, light haze over the town. Natural light from a single sun, consistent shadows, strong atmospheric perspective: distant things are paler, bluer and lower in contrast. Muted natural colours. Documentary photograph, full-frame camera, f/8, sharp focus, realistic exposure.

Negative: illustration, painting, digital art, CGI, 3D render, fantasy art, concept art, matte painting, oversaturated, vivid colours, glow, bloom, lens flare, light rays, HDR, symmetrical composition, collage, candles, lanterns, lit windows, text, letters, numerals, watermark, logo, people, tiled floor, checkerboard, grid pattern

</details>
