# Visual quality bar

Status: approved direction, 2026-11-20. Sean asked for "super crisp, photorealistic, very nice and modern looking graphics". This document turns that request into checks that agents can test. Every art ticket and every rendering ticket aims at this bar.

Engine: Godot 4.7.2, Forward+. Every setting name below comes from the 4.7.2-stable class reference (`doc/classes/*.xml` at tag `4.7.2-stable`) or the 4.7 manual (docs.godotengine.org/en/stable). Section 9 lists what we could not verify. A value that says "start" is a first value; tune it with the gallery, but stay inside the stated range.

Fixed decisions (`docs/plan.md` §4.7 and #38):

- Realism in M1 comes from baked lightmaps (`LightmapGI`), baked on the GPU at high quality.
- Real-time ray-traced reflections and shadows are a later, Ultra-only spike (#38). Nothing here depends on it.
- Sky by tier: Beginner is Earth sky clockwork at dawn. Intermediate is a high, bright sky. Advanced is the edge of space with one restrained planet. Section 10 gives the skies and the materials as built.
- Restraint and photographic realism come before spectacle.
- Performance target: 1080p at 60 fps on a GTX 1660-class GPU at Medium. Ultra can use everything on high-end GPUs.

## 1. The bar

A level meets the bar when all of these are true:

1. **Crisp edges.** Track edges, rails and gear teeth show no stair steps at 1080p or 4K, and the edges do not crawl when the camera moves.
2. **Crisp texture detail.** Within 3 m of the play camera, surfaces show their fine detail (stone pores, brass scratches) at 4K. The detail does not blur, show compression blocks or show an obvious repeat.
3. **Stable in motion.** A camera orbit causes no shimmer on specular highlights and no ghost trail behind the marble, the moving platforms or the particles.
4. **Believable light.** One sun gives one shadow direction. Contact shadows sit under every object. No light leaks through corners or under ledges. Baked light has no blotches or noise.
5. **Physically plausible materials.** Stone looks like stone, brass and gold look like metal with coloured reflections, and glass both reflects and refracts. No surface looks like plastic. No albedo is pure black or pure white.
6. **Modern HDR look.** The AgX tonemapper rolls off highlights softly. The sky is not blown out (the sun disc is the only exception). Shadows are not crushed to black. Glow appears only on real emitters and on the sun.
7. **Readable.** The track stands out from the sky, and the marble's blob shadow is always visible (`docs/plan.md` §2.1, §2.11).

## 2. Graphics presets

The settings menu (#23) applies one row of this table per preset. `game/` code applies each value at runtime through the property or `RenderingServer` method in the last column, so a preset change needs no restart. The exception is the reflection atlas: it is a project setting that Godot reads only at start, so it is the same in every preset.

| Setting | Low | Medium | High | Ultra | Runtime API |
|---|---|---|---|---|---|
| Anti-aliasing (section 3) | FXAA | MSAA 2× | FSR 2.2 at native resolution | FSR 2.2 at native resolution | `Viewport.screen_space_aa`, `msaa_3d`, `scaling_3d_mode`, `scaling_3d_scale` |
| 3D render scale | 1.0 | 1.0 | 1.0 | 1.0 | `Viewport.scaling_3d_scale` |
| Sharpening (`fsr_sharpness`, 0 is sharpest) | none | none | 0.2 | 0.2 | `Viewport.fsr_sharpness` |
| Texture mipmap bias | 0.0 | 0.0 | −0.5 | −0.5 | `Viewport.texture_mipmap_bias` |
| Anisotropic filtering | 4× | 16× | 16× | 16× | `Viewport.anisotropic_filtering_level` |
| Screen-space roughness limiter | on | on | on | on | `RenderingServer.screen_space_roughness_limiter_set_active` |
| Debanding | on | on | on | on | `Viewport.use_debanding` |
| Tonemapper | AgX | AgX | AgX | AgX | `Environment.tonemap_mode` |
| Glow | off | on | on | on | `Environment.glow_enabled` |
| SSAO | off | off | on, quality Medium, half size | on, quality High, full size | `Environment.ssao_enabled`, `RenderingServer.environment_set_ssao_quality` |
| SSIL | off | off | off | on, quality Medium | `Environment.ssil_enabled`, `RenderingServer.environment_set_ssil_quality` |
| SSR | off | off | on, half size | on, full size | `Environment.ssr_enabled`, `RenderingServer.environment_set_ssr_half_size` |
| Distance fog (exponential) | on | on | on | on | `Environment.fog_enabled`, `fog_mode` |
| Volumetric fog | off | off | on, 64 × 64 froxels | on, 96 × 96 froxels | `Environment.volumetric_fog_enabled`, `RenderingServer.environment_set_volumetric_fog_volume_size` |
| SDFGI (Ascent and Planetarium only) | off | off | off | on, 4 cascades, occlusion on, 16 rays | `Environment.sdfgi_enabled`, `RenderingServer.environment_set_sdfgi_ray_count` |
| Sun shadow atlas | 2048 | 4096 | 4096 | 8192 | `RenderingServer.directional_shadow_atlas_set_size` |
| Sun shadow filter | Soft Very Low | Soft Low | Soft Medium | Soft High | `RenderingServer.directional_soft_shadow_filter_set_quality` |
| Sun shadow splits | 2 | 4 | 4 | 4 | `DirectionalLight3D.directional_shadow_mode` |
| Sun shadow distance | 50 m | 80 m | 120 m | 160 m | `DirectionalLight3D.directional_shadow_max_distance` |
| Omni and spot shadow atlas | 2048 | 2048 | 4096 | 4096 | `Viewport.positional_shadow_atlas_size` |
| Lightmap bicubic sampling | off | on | on | on | `RenderingServer.lightmaps_set_bicubic_filter` |
| Mesh LOD threshold (pixels; higher is coarser) | 2.0 | 1.0 | 1.0 | 0.5 | `Viewport.mesh_lod_threshold` |
| Marble reflection probe (section 5) | off | off | off | on | `ReflectionProbe` node, `UPDATE_ALWAYS` |

Rules for the table:

- The level's `LightmapGI`, static reflection probes and baked shadowmask are the same in every preset. Presets change only real-time cost.
- Distance fog gives aerial perspective in every preset, so far geometry looks the same depth on Low and on Ultra. A sky preset gives one haze density. When volumetric fog is on, the volumetric fog shows half of the haze and the distance fog shows the other half (`GraphicsPreset.VOLUMETRIC_FOG_SHARE`), so the haze does not double. The fog does not change the sky (`fog_sky_affect = 0`).
- Texture quality is the anisotropic level and the mipmap bias. No preset changes the resolution of a texture (section 6).
- Not built yet: the SDFGI row comes with the Ascent mode. The marble reflection probe row comes with the marble look, because the marble needs its own render layer first.
- SDFGI never runs in a campaign level, because campaign levels use lightmaps. SDFGI runs only in Ascent and Planetarium on Ultra, where the sun moves.
- The sun has no size: no preset sets `Light3D.light_angular_distance`, so it keeps its default of 0° and no preset has PCSS soft shadows. A 0.5° sun matches the real sun ("approximately 0.5", `Light3D.light_angular_distance`), but in the Ascent 1 town (#31), with the low dawn sun, its PCSS made a cross-hatch dither in shade, stepped shadow edges from the tower, and a grainy sun patch that leaked into the shade of the square, on High and on Ultra alike. Test renders of the `egg`, `start` and `crown_down` shots with the sun at 0° and at 0.5°, and with the volumetric fog off, showed that the sun size alone made them. Godot also warns that PCSS has a "noticeable performance cost".
- Fixed project settings (all presets): `rendering/anti_aliasing/quality/use_debanding=true`, `rendering/reflections/reflection_atlas/reflection_size=256` (the default), `rendering/lightmapping/lightmap_gi/use_bicubic_filter=true`.

### Tonemapping, exposure and colour grading

- `Environment.tonemap_mode = TONE_MAPPER_AGX` in every environment. AgX is "better than other tonemappers at maintaining the hue of colors as they become brighter", and it works with HDR output. Filmic and ACES do not work with HDR output (manual, "HDR output").
- Start: `tonemap_agx_white = 16.29` (the default) and `tonemap_agx_contrast = 1.25` (the default). Range: white 6.0 to 16.29 ("at least 6.0" for photorealistic light), contrast 1.0 to 1.5.
- Exposure is fixed per sky preset (`Environment.tonemap_exposure`). Auto exposure stays off (`CameraAttributesPractical.auto_exposure_enabled = false`), so a level looks the same every run and gallery shots are comparable. In Ascent, a script sets the exposure from the same height curve that drives the time of day.
- Colour grading uses only `tonemap_agx_contrast` and `adjustment_saturation` (with `adjustment_enabled`). Do not use a colour-correction LUT (`adjustment_color_correction`) and do not use the Soft Light glow blend mode. Both are SDR-only and break HDR output.
- Glow: `glow_blend_mode = GLOW_BLEND_MODE_SCREEN` (the default), `glow_intensity` start 0.3, `glow_hdr_threshold` 1.5 (as built: stone in the low dawn sun reaches about 1.1, and at 1.0 it glowed), `glow_bloom = 0.0`. Glow must not make a haze over the whole image.

### HDR output

Godot 4.7 added HDR output. It is a display option in #23, separate from the presets. It is off by default and appears only when `DisplayServer.window_is_hdr_output_supported()` returns true.

- Turn it on with `Window.hdr_output_requested` (project setting `display/window/hdr/request_hdr_output`). This forces `Viewport.use_hdr_2d` on the main viewport.
- Linux: only on Wayland (`DisplayServer.FEATURE_HDR_OUTPUT`: "Linux (Wayland), macOS, iOS, visionOS, Windows"). The game must run with the Wayland display driver (`display/display_server/driver.linuxbsd="wayland"` or `--display-driver wayland`).
- Windows: only with the Direct3D 12 driver. In 4.7.2 the Vulkan driver reports no HDR support on Windows (`drivers/vulkan/rendering_device_driver_vulkan.cpp`, case `SUPPORTS_HDR_OUTPUT`). The project now uses Vulkan, so Windows HDR needs `rendering/rendering_device/driver.windows="d3d12"`, and that change needs its own test.
- Because of these driver limits, HDR output is not part of the M1 exit gate.

## 3. Anti-aliasing and sharpness

What Godot 4.7.2 offers (Viewport enums): MSAA 2×, 4× and 8× (`msaa_3d`); FXAA and SMAA 1x (`screen_space_aa`); TAA (`use_taa`); FSR 1.0 and FSR 2.2 (`scaling_3d_mode`); supersampling (bilinear scaling above 1.0); and the screen-space roughness limiter. MetalFX is Apple-only. DLSS and XeSS do not exist in Godot. Godot has no separate sharpening filter: sharpening exists only inside FSR (`fsr_sharpness`, the RCAS part of FSR).

| Method | Crisp | Stable in motion | Cost | Use |
|---|---|---|---|---|
| FXAA | Soft; blurs texture detail | No (edges crawl) | Lowest | Low only |
| SMAA 1x | Sharper than FXAA | No (edges crawl) | Low | Not used: MSAA 2× is a better fit for Medium |
| MSAA 2× | Sharp geometry edges, no blur | Edges are stable; specular and alpha aliasing remain | Medium | Medium |
| TAA | Adds blur, more in motion | Yes, but ghosts behind moving objects | Low | Not used: FSR 2.2 at native resolution is sharper |
| FSR 2.2 at scale 1.0 | Sharp; `fsr_sharpness` still works | Yes; "less blurriness compared to TAA, especially in motion" | High | High and Ultra |
| Supersampling (scale 1.5 to 2.0) | Sharpest | Yes | Very high (2.25× to 4× pixels) | Offline renders only (style board, store art) |

Reasons:

- The camera orbits fast, and the marble moves up to 15 m/s. TAA ghosts behind moving objects, so TAA would fail check 3 of the bar.
- FSR 2.2 at scale 1.0 gives temporal anti-aliasing with less blur than TAA, and its sharpening works at native resolution (manual, "Resolution scaling"). Godot turns TAA off when FSR 2.2 is on (`renderer_viewport.cpp`: "FSR 2 or MetalFX Temporal is not compatible with TAA").
- Medium cannot afford a temporal method on a GTX 1660 at 1080p60. MSAA 2× keeps geometry edges stable. The roughness limiter and the material rules in section 6 control specular shimmer, which MSAA cannot fix.
- Mipmap bias: Godot adds −0.5 automatically for TAA and −0.25 for FXAA, but adds nothing for FSR 2.2 at scale 1.0 (`texture_mipmap_bias` docs; `renderer_viewport.cpp` uses `log2(min(scale, 1.0))`). High and Ultra set −0.5 by hand, because temporal accumulation hides the extra grain. Range: 0.0 to −1.0.
- Alpha-scissor materials (foliage, grilles, if any) set `alpha_antialiasing_mode = ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE`, because MSAA does not smooth alpha edges.

## 4. Lightmaps and probes

### Lights

- Each level has exactly one key light: one `DirectionalLight3D` (the sun) with shadows on and `light_bake_mode = BAKE_DYNAMIC`. Its direct light and shadows stay real time, and its bounce light is baked.
  - Reason: with `BAKE_STATIC`, the light "doesn't display a specular lobe on static lightmapped meshes". Brass, gold and glass would lose their sun highlight. Shadowmasking also needs a directional light with the Dynamic bake mode (manual, "Using Lightmap GI"; `lightmapper_rd.cpp` warns "Shadowmask disabled: no directional light with their bake mode set to dynamic exists").
- Fill light comes from the sky and from baked bounce light. Do not add fill lights.
- Accent lights (lamps, emissive glass) use `BAKE_STATIC` and cast no real-time shadows.
  - Exception: the light below a gem and the light above the Clockwork Egg (section 11) are real time: `light_bake_mode = BAKE_DISABLED`, no shadows. Reason: they belong to objects, not to the level. A collected gem hides, and a lightmap would keep its light on the floor. The egg's light is there so that the room that hides the egg is not dark; it is the one light in a level that does the work of a fill light.
- `rendering/lights_and_shadows/use_physical_light_units` stays `false`. We do not need physical units to meet the bar.

### Bake settings (every level)

| Setting | Value | Reason |
|---|---|---|
| `LightmapGI.quality` | `BAKE_QUALITY_ULTRA` | The bake runs on the RTX 5090. Quality changes bake time, not file size |
| `bounces` | 4 (default 3) | Brighter, more natural bounce light from stone and gold |
| `bounce_indirect_energy` | 1.0 | Physically neutral |
| `directional` | `false` | The sun's direct light is real time, and baked indirect light is low frequency. Directional lightmaps store 4 layers (`lightmapper_rd.cpp`: `p_bake_sh ? 4 : 1`), so they are 4× the size |
| `supersampling` / `supersampling_factor` | `true` / 2.0 | Less noise, smoother shadows, better small contact shadows |
| `use_denoiser` | `true` | |
| Denoiser (`rendering/lightmapping/denoising/denoiser`) | JNLM (built in) | No extra tool. Change to OIDN only if the gallery shows blotches that JNLM cannot remove |
| `denoiser_strength` / `denoiser_range` | 0.1 / 10 (defaults) | Higher strength removes contact-shadow detail |
| `environment_mode` | `ENVIRONMENT_MODE_SCENE` | The level's sky lights the bake |
| `interior` | `false` | Open-air levels |
| `shadowmask_mode` | `SHADOWMASK_MODE_REPLACE` | Real-time sun shadows up close; baked shadows beyond `directional_shadow_max_distance`, so far islands keep their shadows on Low |
| `generate_probes_subdiv` | `GENERATE_PROBES_SUBDIV_8` (default) | Lightmap probes light the marble and the moving platforms |
| Lightmap texel size (import option `meshes/lightmap_texel_size`) | 0.1 m on level `.glb` files | Track, rails and props near the route |
| `GeometryInstance3D.gi_lightmap_texel_scale` | 0.25 on far scenery | Far scenery bakes at 0.4 m per texel |

Godot writes the lightmap as `.exr` and the shadowmask as `.png` (`scene/3d/lightmap_gi.cpp`). A bake must run in an editor with a real GPU, because `--headless` uses a dummy renderer. `LightmapGI.bake()` is not exposed to scripts in 4.7.2 (its binding is commented out in `scene/3d/lightmap_gi.cpp`); only the editor plugin bakes. The `just` bake command in #24 must work around this.

### Reflection probes

- Static probes: `ReflectionProbe` with `update_mode = UPDATE_ONCE` and `size` at most 30 m, placed so that each track section is inside one probe. They are the same in every preset.
  - `LevelConverter` adds them at import: a grid over the bounds of the level's meshes plus 3 m, with one probe for each grid cell that holds a mesh. Each probe looks from 2 m above the highest mesh of its cell.
  - `box_projection` is off. A level is in the open air, so most of a reflection is the sky, which is very far away. Box projection puts the sky on the walls of the box, and the reflection of the sky then slides as the camera moves along the track. Turn it on by hand only for a closed room.
  - `ambient_mode` is Disabled. The probes give reflections only; the lightmap and its probes give the ambient light.
  - A mesh named `<name>-far` is far scenery: it gets no probe and stays out of the lightmap.
- Room probes: a `room_probe` marker (`game/objects/room_probe/`) gives an indoor room an interior probe with box projection and a warm ambient colour. Godot's Forward+ renderer lets the first probe in a cluster take the whole weight, and a probe fades out over its blend distance at the edge of its box, so the room probe's box reaches 0.45 m into the walls, the floor and the ceiling.
- Marble probe (Ultra only): one `ReflectionProbe` follows the marble with `UPDATE_ALWAYS`. Its `cull_mask` leaves out the marble's layer, so the marble does not reflect itself. Its `reflection_mask` is only the marble's layer, so only the marble uses it. Godot recommends "only one ReflectionProbe with UPDATE_ALWAYS at most per scene", because of its "significant performance cost".
- SSR (High and Ultra) adds sharp reflections on opaque surfaces such as polished stone and brass. SSR does not reflect transparent materials and does not apply to them (manual, "Environment and post-processing").

## 5. The glass marble

The glass marble gets reflection and refraction without ray tracing. Its look is one skin scene, `game/core/marble/skins/glass_orrery.tscn` (marble A of the style board). `marble.tscn` puts the skin under `Ball`, the node that turns with the spin. A second skin is a second scene in `skins/`.

- **Core:** the brass orrery is an opaque mesh. `tools/blender/marble_core.py` builds it, and `just build-marble` exports it to `game/core/marble/built/` (a build output, like the levels). Because it is opaque, it is in the screen texture and the depth texture, and it has motion vectors for FSR 2.2.
- **Glass:** a sphere with the shader `skins/glass.gdshader`. The shader reads `hint_screen_texture` and `hint_depth_texture`, so the glass draws in the transparent pass.
  - Where the depth texture holds a point inside the ball, the pixel shows the core. The shader shows the screen texture at the same pixel, so the core is not sampled again and stays crisp. The glass does not magnify the core. The mesh has the sizes that the eye sees through glass with an index of refraction of 1.65.
  - Elsewhere the shader bends the view ray through a solid ball (index of refraction 1.65) and reads the screen texture where the ray points, outside the marble's own outline. The world shows upside down and small, as in a real glass ball. Only opaque objects appear in this picture.
  - The picture goes to `EMISSION` with `ALBEDO` black, `ROUGHNESS` 0.05 and `SPECULAR` 0.61 (F0 0.06, the value for an index of refraction of 1.65). The engine adds the sky, the probes and the sun as reflections.
  - Toward the outline, the glass has a cool tint. The outline itself is a thin dark line with no reflection. The tint and the line keep the marble visible on pale stone and on a bright sky.
- **Reflection:** the sky and the static probes on every preset, plus the marble probe on Ultra when the presets have it. Until a level has probes, the brass core reflects only the sky on Low and Medium; SSR adds the floor on High and Ultra.
- **Shadow:** the glass itself casts no shadow. The skin has a second sphere with `cast_shadow = SHADOW_CASTING_SETTING_SHADOWS_ONLY`, so the marble casts a sun shadow. The core casts no shadow and takes none (`game/core/marble/core_import.gd`), because it is inside the sphere. The crisp blob shadow straight down (`docs/plan.md` §2.11) stays in addition.
- **Ghost:** the ghost marble shows the shapes of the same skin in one pale, see-through look (`game/core/ghost/ghost.gdshader`). It does not read the screen texture.
- **Cost:** measured on the fixture at 1080p (RTX 5090, a shared GPU), the glass adds about 0.15 ms of GPU time on Low and Medium and less than 0.05 ms on High and Ultra. Most of it is the copy of the screen texture. A cheaper glass for Low needs a field in `GraphicsPreset`.
- **Later:** #38 can add ray-traced reflections on Ultra. This design does not depend on it.

## 6. Textures, materials and texel density

### Texel density

Assumption for these numbers: a 70° vertical field of view and the camera 1.5 m from the track deck. At 4K (2160 px high), the deck then takes about 2160 / (2 × 1.5 m × tan 35°) ≈ 1030 px per metre. At 1080p it takes about 515 px per metre.

| Zone | Target | In marble terms |
|---|---|---|
| Close (within 3 m of the play camera: track deck, rails, pads, gems, marble) | 1024 px/m (10.24 px/cm) | The 0.4 m marble diameter covers about 410 texels of deck |
| Middle (3 m to 20 m) | 512 px/m | |
| Far (more than 20 m) | 256 px/m | |
| Detail maps (close zone only) | 4096 px/m: a 1K detail map that repeats every 0.25 m | Gives the sub-centimetre grain that makes a 4K image look crisp |

A 2K texture that repeats every 2 m gives 1024 px/m. So 2K meets the close-zone target when the texture's real-world size is 2 m or less. (Poly Haven and ambientCG list a real-world size for each texture.)

### Texture policy

- **Default: 2K.** Every kit material is 2K or less.
- **4K exceptions** need a large repeat to hide tiling and still meet 1024 px/m. Only these qualify:
  - Track deck materials: at most 4 sets.
  - Rail and trim materials: at most 2 sets.
  - The Advanced-tier planet: 1 set. It fills a large part of the screen.
- **Marble skins stay at 2K.** The marble's equator is 1.26 m long, and in play it is about 200 px across at 1080p (about 400 px at 4K). 1K is already sharper than the screen, so 2K leaves margin for the skin-select close-up. A skin goes to 4K only if the 4K skin-select shot fails rubric check 2.
- **Detail maps:** 1K tileable detail normal maps (and optional detail albedo) for the close-zone materials. At most 6 sets.
  - `BaseMaterial3D` detail on UV1 uses the same UV scale as the base textures (`material.cpp`). Detail on UV2 rescales UV2, and UV2 is the lightmap UV. So every kit material uses one shader, `game/materials/kit_surface.gdshader`. Do not use `detail_uv_layer = DETAIL_UV_2` on lightmapped meshes.
  - As built: the kit shader maps the textures from three sides in the piece's own space, so a kit piece needs no UV1 and one repeat always covers `tile` metres. Its `detail_tile` uniform adds the material's own normal map again at 0.25 m per repeat. This gives the fine grain, so no separate detail set is in the repo yet.
- **Skies:** HDRIs at 4K. A tier sky may go to 8K only if its 4K gallery shot looks soft. (At 4K output with a 70° view, a 4K equirectangular sky is about 2.7× softer than the screen.) The tier skies import without compression (`compress/mode` Lossless) and with mipmaps: an HDR sky is one texture, and BC6H is slow to compress on a CI runner.
- **Where the files are:** `assets/textures/` holds each texture once, in Git LFS. Godot reads only `res://`, so `just import` copies the textures that the game uses into `game/materials/textures/` (not in git). A committed `game/materials/textures/<file>.import` adopts a texture and holds its import settings. The baked tier skies are in `game/skies/` (Git LFS).
- **Import settings:** `compress/mode` VRAM Compressed, `compress/high_quality = true` (BC7) for albedo, normal maps with RGTC (`compress/normal_map`), mipmaps on. Set `roughness/src_normal` on each roughness map, so the import filters roughness and reduces specular aliasing.
- **Source files:** use the OpenGL (Y+) normal-map variant (Poly Haven `nor_gl`, ambientCG `NormalGL`). Store albedo, roughness and AO as JPG (quality 90 or higher), and store normal maps as PNG, because lossy compression shows as blocky shading in normal maps. An 8-bit PNG is enough. Exception: the material sets B and C are not in use, so they keep the JPG normal maps of the style board. A set gets PNG normal maps when it becomes the set in use.
- **Filtering:** every kit material sets `texture_filter = TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC`. The default is `TEXTURE_FILTER_LINEAR_WITH_MIPMAPS`, and with it the anisotropic setting does nothing.
- Godot 4.7.2 has no texture streaming, so no preset changes texture resolution. Estimated VRAM for one level: about 12 2K sets and 3 4K sets, as BC7 with mipmaps, is about 0.5 GB. This fits a 6 GB GTX 1660.

### Git LFS estimate (whole 60-level scope)

Estimate from typical Poly Haven and ambientCG file sizes; not measured. One 2K set (JPG albedo, roughness and AO; PNG normal) is about 14 MB. One 4K set is about 55 MB.

| Item | Count | Each | Total |
|---|---|---|---|
| 2K kit material sets | 30 | 14 MB | 420 MB |
| 4K exception sets (deck 4, rail 2, planet 1) | 7 | 55 MB | 385 MB |
| 1K detail sets | 6 | 3 MB | 18 MB |
| 4K sky HDRIs (tiers, Ascent, Planetarium) | 6 | 25 MB | 150 MB |
| **Textures and skies** | | | **about 1.0 GB** |
| Optional: 8K upgrade for the 3 tier skies | 3 | +90 MB | +270 MB |
| Lightmaps, only if we commit them (60 levels, 3 secret, workshop, 8 Ascent zones) | 72 | about 5 MB | about 360 MB |

- The 4K exceptions add about 290 MB compared with a 2K-only policy.
- GitHub Free and Pro include 10 GiB of LFS storage and 10 GiB of LFS download bandwidth a month (docs.github.com, "About billing for Git Large File Storage"). Every version of a file counts toward storage. So replace a texture only for a real reason, and keep CI's LFS cache (`docs/plan.md` §5.3).
- Even with every option, the total stays under 2 GB.

### Material rules

| Material | Metallic | Roughness | Albedo (sRGB) |
|---|---|---|---|
| Stone, honed (track deck) | 0 | 0.45–0.70 | 50–220 |
| Stone, rough (cliffs, islands) | 0 | 0.70–0.95 | 40–200 |
| Stone, polished (accents only) | 0 | 0.15–0.30 | 50–220 |
| Brass, polished | 1 | 0.15–0.30 | Warm yellow; brightest channel 200–245 |
| Brass, aged or brushed | 1 (0.85 with tarnish) | 0.30–0.55 | Same hue, 10–20% darker |
| Gold | 1 | 0.10–0.45 | Warm yellow-orange; brightest channel 230–250 |
| Glass | 0 | 0.00–0.08 | Near white; tint comes from transparency |

These ranges are starting values from common PBR practice. We did not take them from a Godot source.

- No pure black or pure white albedo. Dielectrics stay between sRGB 30 and 240. Metals stay between sRGB 180 and 250 in their brightest channel.
- Metallic is 0 or 1. Use values between only for dust or dirt masks. The aged brass of set A is 0.85, as on the approved style board: the tarnish is a thin dielectric layer, and it keeps the brass golden where it reflects the blue sky.
- A flat metal under the open sky reflects mostly sky. Gold below roughness 0.4 looks olive where it reflects blue sky, so the gold inlay is 0.43.
- A roughness below 0.2 with a high-frequency normal map causes specular shimmer. Raise the roughness, or set `roughness/src_normal` on import.
- Use `anisotropy_enabled` only on brushed brass. Use `clearcoat_enabled` only on lacquered parts.

## 7. Review rubric

The gallery review agent and Sean use these checks on every level's gallery (#20). Each check is pass or fail. A level passes only when all checks pass.

| # | Check | How to check |
|---|---|---|
| 1 | Edges are crisp | In the 1080p `start` shot at 1:1, track edges and rails have no stair steps |
| 2 | Texture detail is crisp | In the 4K `start` shot at 1:1, the deck within 3 m shows fine grain. No blur, no compression blocks, no obvious repeat in `start` or `overview` |
| 3 | Motion is stable | The two `motion` frames (section 8) show no ghost trail behind the marble or the moving objects, and no highlight that flashes between the two frames |
| 4 | Light is believable | One shadow direction. Contact shadows under the marble and the props. No bright seams in corners, no light under ledges, no blotches or noise in the baked light, no unlit black faces |
| 5 | Materials are plausible | Stone, brass, gold and glass each read as their material. Metals show coloured reflections. The glass marble shows both reflection and refraction. No plastic look |
| 6 | Exposure is right | At most 1% of pixels are pure black (0, 0, 0) and at most 2% are pure white (255, 255, 255). A script measures this from the PNG. The sky is not blown out, except the sun disc |
| 7 | The look is restrained | Glow only on emitters and the sun. Fog does not wash out the track. The sky matches the tier (the fixed decisions at the top) |
| 8 | The level is readable | The track stands out from the sky in `overview`. The marble's blob shadow is visible in `start`. Gems and hazards are easy to see |

The gallery renders `start` at 1080p and at 4K, and every other shot at 1080p, on High. Sean also reviews one 4K Ultra page at each milestone.

## 8. Performance check

`just perf` (#20) flies the same fixed camera path through each level for each preset. It measures GPU frame time with `RenderingServer.viewport_set_measure_render_time` and `viewport_get_measured_render_time_gpu`, and it reads VRAM with `Performance.RENDER_VIDEO_MEM_USED`.

| Preset | Resolution | Measures | Fails when |
|---|---|---|---|
| Low | 1080p | GPU time (mean, 99th percentile), VRAM | Its VRAM is not lower than Medium's |
| Medium | 1080p | GPU time, VRAM | The 99th-percentile GPU time on the RTX 5090 is above the budget (`docs/plan.md` §4.7: start at 3 ms, calibrate in M1), or VRAM is above 4 GB |
| High | 1440p | GPU time | Report only |
| Ultra | 4K | GPU time | The 99th-percentile GPU time on the RTX 5090 is above 16.7 ms (60 fps) |

- The check also fails when Low, Medium, High and Ultra do not use more VRAM in that order at 1080p. This proves that the presets change real settings (#24). The check does not compare GPU time between presets: on a small level, the GPU time of Low and Medium changes by 2x from run to run on a shared GPU, and Medium and High cost about the same.
- The camera path includes one fast orbit around the marble. During that orbit, the check saves two frames 1/60 s apart as the `motion` pair for rubric check 3.

## 9. Not verified

- The Git LFS numbers for the whole scope are estimates. Section 10 has the numbers that #24 measured on the two fixture levels.
- Lightmap file size per level (about 5 MB) assumes about 5,000 m² of near surfaces at 0.1 m and 20,000 m² of far scenery at 0.4 m, so about 1 million texels with atlas padding. The first real level, B1, is 4.6 MB with every mesh at 0.1 m (section 10).
- The material ranges in section 6 are common PBR practice, not values from a Godot source.
- We did not test how much MSAA 2× costs on a real GTX 1660. The plan's 5090 budget stands in for it.
- We did not test HDR output on Sean's KDE Wayland session, or in `gamescope`.
- The −0.5 mipmap bias for FSR 2.2 at native resolution is our choice, not a Godot recommendation.

## 10. As built: kit materials and skies (#24)

Sean approved look A of the style board on 2026-11-21: honey limestone, aged brass and a golden dawn. He approved the noon sky and the dusk sky as rendered.

### Kit materials

A level script names a kit material, and the importer gives those faces the game's material of that name.

- Names: `limestone` (track decks), `brass` (trim and borders) and `gold` (inlays). `kit.surface(id, material)` makes the Blender material; `kit.track()` and `kit.ramp()` take `material="limestone"` and `trim="brass"`.
- The pieces of `kit/masonry.py` (`deck`, `wall`, `arch`, `lathe`, `inlay` and the others) take `material` in the same way. An inlay is gold; gear teeth, a gear, a hoop and a ball are brass unless the level script says otherwise.
- The trim is a brass angle section along the two long edges of a piece. It is a mesh of its own that does not collide, so it does not change how the marble rolls. Give `trim=""` for an edge that touches another piece.
- `KitMaterials.find(name)` (`game/materials/kit_materials.gd`) returns `res://materials/<set>/<name>.tres`, or else `res://materials/<name>.tres`. `LevelConverter` applies it at import. A level that names an unknown material fails the import.
- To add a kit material: add its name to `MATERIALS` in `kit/surfaces.py`, and add `<name>.tres` (a `ShaderMaterial` with `kit_surface.gdshader`) to each set folder, or once to `game/materials/` when the sets share it.
- A mesh whose material has no `material` property keeps its own material (for example the coloured stations of the feel course).
- Seven objects take their look from `KitMaterials.find()` at run time: the Trapdoor and Crumbling Tiles (#29), and the Bumper, Moving platform, Turning gear, Checkpoint and Finish (#30). Each has a test that checks its kit materials.
  - A Bumper is a band of enamel in the palette's hazard colour (roughness 0.5; a glossier band showed streaks of reflection) between a base and a cap of the kit brass. The cap covers the top face, and both pulse with the drum.
  - A Moving platform's deck is a copy of the kit limestone with no paving (a deck moves; see Crumbling Tiles), with a band of the kit brass round its top edge and one round its foot. A set `finish` (a kit material, for example `wood` in Ascent 1) replaces the stone; the brass bands stay.
  - A Turning gear's disc and teeth are the kit brass. The shader maps it in the gear's own space, so the texture turns with the gear.
  - A Checkpoint and a Finish share one look (`game/objects/pad_look.gd`): a round plate of stone (the kit limestone × 1.12, smoother, no paving) in a bevelled rim of the kit brass, with a glass lens in the middle. The plate stands 4.5 cm proud of the floor, so it reads as a raised pad; it does not collide. The lens is the pad's colour, pale while the pad is off and glowing while it is on. Before, an unlit pad was a dark disc that read as a hole (B2 style review).
  - These objects are built at run time and move or pulse, so they are not in the lightmap; the lightmap probes light them.
  - A Trapdoor's door is its own copy of the kit brass with one texture repeat across the door, so a large door shows no repeat.
  - Crumbling Tiles are a copy of the kit limestone: tint × 0.78, normal strength 1.8 and no paving (a tile moves, and the paving picks each slab's look from the piece's world position, so it would flicker). Each tile sits on a 4 cm tray of kit brass that shows as a brass line in the 5 cm gap round it. Each tile also lies at its own fixed tilt of up to 0.8° (its collider stays level) and shows its own patch of stone, both picked from its grid index. So loose tiles read apart from solid floor by shape, not by colour alone.
  - `crumbling_tiles.gd` is a tool script, so its tiles (meshes with lightmap UVs) exist in the editor and the lightmap bake lights them like the stone round them; a tile's baked light moves with it as it falls. Before, the tiles had only the probes, which over an empty frame see the sky: B2's east sheet in shade measured sRGB (55, 52, 47), and with the bake (73, 64, 52). The bake also closes the crumbling cells over B2's undercroft, as the tiles do in play, so that room is darker: the median luma of B2's `egg` shot went from 37 to 16 (pure black 0.05 %).

`KitMaterials.SET` picks the material set. It is the only setting to change:

| Set | Limestone | Tint, repeat | Brass | Tint, repeat, roughness scale |
|---|---|---|---|---|
| `a` (in use) | Poly Haven `scuffed_cement` | (2.6, 3.0, 3.5), 1.5 m | ambientCG `Metal007`, metallic 0.85, detail normal at 0.25 m | (1.0, 1.1, 1.4), 2.0 m, × 2.4 |
| `b` | Poly Haven `concrete_wall_008` | (2.3, 2.45, 3.0), 1.6 m | ambientCG `Metal048A` | (0.9, 0.8, 0.62), 1.0 m, × 3.0 |
| `c` | Poly Haven `dirty_concrete` | (1.6, 1.7, 1.9), 1.6 m | ambientCG `Metal008` | (1.0, 1.0, 1.0), 1.2 m, × 1.3 |

- The brass of set A repeats every 2 m: with the 2K maps that is 1024 px/m, the close-zone target (section 6). Before, it repeated every 0.7 m. A bar 0.09 m wide then showed a narrow strip of the map's dark blotches, which read as wood grain, and a dark pit fell every 0.7 m along a rail (B3 style review). The detail normal at 0.25 m gives the fine grain close to the camera.
- Gear teeth (`kit.teeth()`) and grille rails have 0.02 m chamfers on their edges, so each edge catches a highlight and the piece reads as cast metal, not as a sawn block. The teeth's chamfers are round, in two segments: with one flat segment, the small triangle at each corner caught the sun as a near-white point. The brass that objects build in code (turning-gear teeth, the carriage bands) gets the same 0.02 m chamfers from `Chamfer.box()` (`game/objects/chamfer.gd`); their colliders stay plain boxes.
- Gold is the same in every set: `Metal048A`, tint (1.0, 0.82, 0.5), 0.6 m, roughness × 5.
- Every limestone is paved: slabs of 1.0 m by 1.5 m in a running bond, joints 12 mm wide, the detail normal at 0.25 m.
- The tints are above 1 because the colour maps are darker than limestone. The shader keeps the result inside the albedo limits of section 6.
- To change the set: set `KitMaterials.SET`, then run `just build-levels` and `just bake`. Each set has its own dawn on the style board. To get it, set `SET` in `tools/blender/bake_skies.py` to the same letter, run `just bake-skies dawn`, and put these values into `game/skies/dawn.tres`. (`just bake-skies dawn --set b` bakes a set that is not in use into `build/skies/`, for a preview.)

| Dawn of set | `sky_energy` | `sun_elevation` | `sun_color` | `sun_energy` |
|---|---|---|---|---|
| A (in use) | 0.297 | 12 | (1, 0.84, 0.68) | 2.27 |
| B | 0.354 | 8 | (1, 0.80, 0.71) | 1.58 |
| C | 0.379 | 4.5 | (1, 0.77, 0.58) | 2.17 |

### Sky presets

A `SkyPreset` (`game/skies/<name>.tres`) is one baked sky and the light that goes with it. `LevelConverter` gives a level the preset that `kit.level(sky=...)` names. With no name, the tier picks it: Beginner `dawn`, Intermediate `noon`, Advanced `dusk`, every other tier `dawn`. An unknown name fails the import. A level that brings its own `WorldEnvironment` and `DirectionalLight3D` keeps them.

| Preset | Backdrop | Sun elevation | Sun colour (sRGB) | Sun energy | Sky energy | Fill | Haze (1/m) |
|---|---|---|---|---|---|---|---|
| `dawn` | A photographed dawn sky over a sea of clouds. No planets | 12° | (1, 0.84, 0.68) | 2.27 | 0.297 | none | 0.001 |
| `ground_dawn` | The same dawn sky on the ground: the photograph's far horizon over far land. No cloud sea, no planets. The Ascent climb starts in it | 12° | (1, 0.84, 0.68) | 2.27 | 0.297 | none | 0.001 |
| `noon` | The sky from 16 km: deep blue, clouds far below. No planets | 58° | (1, 0.99, 0.96) | 1.35 | 0.177 | none | 0.0005 |
| `dusk` | The sky from 80 km: the curve of the Earth, faint stars, one pale planet | 7° | (1, 0.77, 0.58) | 4.39 | 1.15 | half of the ambient light is a cool blue | 0.0003 |

- The sun stands at azimuth 135° in every sky: ahead of the start and on its left, when the level runs along the kit's +y.
- The energies hold the exposure of the style-board render (dawn −1.75 stops, noon −2.5, dusk +0.2), so `tonemap_exposure` stays 1.0 and a glowing object looks the same under every sky. A sun of S W/m² in the style-board script is `sun_energy` = S / π × 2^stops.
- A backdrop is one 4096×2048 panorama. It has no parallax, so it reads as far away. Its sun disc is cut down to a radiance of 16, because the `DirectionalLight3D` is the sun.
- The dusk sky is almost black, so the dusk preset mixes a cool blue colour into the ambient light. This is not a fill light: it comes from all directions and it is in the lightmap bake. The dusk panorama also has a faint airglow, so that space is not pure black.
- The ground dawn (#31) is the dawn of a town on the ground. Its sky is the same photograph as the dawn (Poly Haven `syferfontein_6d_clear`, strength 0.8), and so are its light and its energies. Its lower half is not a cloud sea:
  - Down to 0.7° below the horizon it is the photograph, with the photograph's far hills and plains. From 0.7° to 1.8° below the horizon it fades into far land, so the photograph's near rocks and grass do not show. From a tower they would look like giant rocks.
  - The bake draws the far land in the world shader: the view ray meets a plane 250 m below the camera. The land is dry grass with bushes and a few woods, and some fields in the farmed areas (`GRASS`, `BUSHES`, `FIELDS`). The sun lamp (24 W/m², 12°) and the sky light it. A haze with the colour of the photograph's far land, smoothed along the horizon, hides it with distance (visibility 6 km), so it meets the photograph with no seam.
  - The plane is lower than the climb. A panorama has no parallax, so the land shows its scale only by the size of its fields, and those look right from every height of zones 1 to 3.
- `just bake-skies [dawn|ground_dawn|noon|dusk]` renders the panoramas again with Blender Cycles (about 5 minutes for dawn, seconds for the others). `tools/blender/bake_skies.py` holds every number of the backdrops.
- The importer writes the sky and the sun into the level. After a change of a preset, `just test`, `just gallery` and `just bake` build the levels again by themselves.

### Measured (RTX 5090, 2026-11-21)

| Item | Value |
|---|---|
| Lightmap files, `fixture` (three 4 m by 8 m pieces) | 158 KB |
| Lightmap files, `core_loop` (four 8 m wide pieces) | 269 KB |
| Kit textures in Git LFS (sets A, B and C, and gold) | 47 MB |
| Tier skies in Git LFS (dawn, noon, dusk) | 35 MB |
| Sky sources in Git LFS (3 HDRIs, the planet map) | 14 MB |
| Lightmap files, `b01` (#28: 96 meshes, 83,300 triangles with the round 0.02 m chamfers of #30, every mesh at 0.1 m per texel; bake 39 s) | 4.7 MB |
| VRAM, `fixture`, Medium at 1080p | 875 MB |
| VRAM, `b01`, Medium at 1080p | 892 MB |
| GPU time, `b01`, mean / p99 at 1080p (three runs; see the note on clock speed below) | Low 0.22 to 0.54 / 0.27 to 0.78 ms, Medium 0.38 to 0.89 / 0.95 to 1.16 ms, High 0.83 to 0.90 / 0.94 to 3.00 ms, Ultra 1.30 to 1.33 / 1.60 to 1.62 ms |
| Lightmap files, `b02` (#29: 139 meshes and 102 crumbling tiles, 72,400 triangles in the level with the chamfers of #30; bake 39 s) | 5.1 MB |
| VRAM, `b02`, Medium at 1080p | 904 MB |
| GPU time, `b02`, mean / p99 (one run, with the object looks of #29) | Low 0.28 / 1.01 ms, Medium 0.37 / 0.50 ms, High 0.81 / 0.96 ms, Ultra 1.26 / 1.57 ms at 1080p; High 1.23 / 1.57 ms at 1440p; Ultra 3.95 / 5.14 ms at 4K |
| Lightmap files, `b03` (#30: 224 meshes, 64,600 triangles in the level; bake 40 s) | 5.2 MB |
| VRAM, `b03`, Medium at 1080p | 912 MB |
| GPU time, `b03`, mean / p99 (one run, with the round chamfers of the B3 style review) | Low 0.26 / 0.37 ms, Medium 0.39 / 0.54 ms, High 0.87 / 1.12 ms, Ultra 2.00 / 2.38 ms at 1080p; High 1.42 / 3.03 ms at 1440p; Ultra 4.98 / 11.92 ms at 4K |
| VRAM, `fixture`, Ultra at 4K | 2.3 GB |
| GPU time, `fixture`, mean / p99 at 1080p | Low 0.28 / 0.69 ms, Medium 0.39 / 0.95 ms, High 0.71 / 2.69 ms, Ultra 1.02 / 3.17 ms |
| GPU time, `fixture`, Ultra at 4K | 2.97 / 4.09 ms |

- With the stand-in light rig and no textures (#20), the same level used 222 MB at Medium.
- At these small loads the GPU changes its clock speed between runs: the same preset measured 0.19 ms in one run and 0.44 ms in the next. So the check "Low costs less than Medium" in `just perf` can fail by chance on a level this small. The two budgets passed in every run. Run the check again when only that order fails.

## 11. As built: gems and the Clockwork Egg

### Gems

One scene, `game/objects/gem/gem.tscn`, and four cuts. `GemCut` holds each cut as rings round the vertical axis and builds its mesh and the planes of its facets once; every gem of a cut shares them. A gem is 0.5 m across at its largest, and its lowest point is 0.3 m above its marker.

| Cut | Outline | Sides | Standard colour | Colourblind colour |
|---|---|---|---|---|
| 0 hexagon | flat at both ends | 6 | amber | orange |
| 1 double pyramid | pointed at both ends | 6 | deep blue | blue |
| 2 rose | pointed on top, flat below | 6 | emerald green | yellow |
| 3 brilliant | flat on top, pointed below | 12 | magenta | reddish purple |

- Cuts 0, 1 and 3 and their colours are the three gems of the style board, with its ring sizes. The game has four cuts, so cut 2 is new. Its outline is the one pair of ends that the board does not use. Its colour is a deep tone of the bluish green of the Okabe-Ito set, as the board's colours are deep tones of that set's orange, blue and reddish purple.
- `Palette` is the one place for the colours. The standard gems have one lightness, as on the board ("every colour emits the same luminance"). The colourblind gems keep the steps of lightness of their colours: `Palette.gem_lightness()` gives the jewel a factor from the luminance of its colour.

**Glass.** `game/objects/gem/gem.gdshader` draws the jewel in the opaque pass. The board's gem is clear glass (transmission 1); the game's gem does not show the level behind it. In exchange it has crisp edges with MSAA and with FSR 2.2, it writes motion vectors, and it needs no copy of the screen texture.

- The shader follows the view ray into the gem through the planes of the cut (index of refraction 2.2): the ray bends at the facet, the facets inside mirror it up to four times, and it leaves where it meets a facet at a steep angle. This needs a convex cut; a test checks each cut.
- The gem shows the sky and the probes in the direction of the ray that left. The engine reads them: the shader gives the engine a normal for that direction through `TANGENT` and `NORMAL_MAP`, and the colour as the tint of a metal. `NORMAL` stays the facet's own normal, so the clearcoat layer mirrors the surroundings in the outside of the glass.
- A long path through the glass gives a deep colour and a short path a pale one. The gem is dark where the camera looks straight through it and bright where it sends light back.
- `light()` adds two glints for each light: a coloured one where the path inside leaves toward the light, and a white one where a facet mirrors the light.
- A pale line marks each edge of the cut and each place where the path inside changes. That line hides the step between two pictures inside one facet, which no anti-aliasing mode smooths. A thin bright rim, at least 1.2 pixels wide, marks the outline.
- A far gem changes look: from 6 mm per pixel the picture of the inside fades, and from 2 cm per pixel the gem shows plain facets, glows about four times more, has no coloured glint from the path inside, and the sides that face the camera glint as the gem turns. Each gem starts at its own turn angle, so the gems of a level do not glint together.

**Round the gem.** The gem casts no shadow. An `OmniLight3D` 0.22 m above the marker (energy 0.25, range 1.2 m, no shadows, not baked) marks its place on the floor. The beam is 3.2 m tall and starts at the top of the jewel: `game/objects/gem/beam.gdshader`, additive, at least 0.2 % of the height of the view wide, so that it shows from far away. The finish uses the same shader with its old settings.

### Clockwork Egg

- `tools/blender/egg.py` builds the egg, and `just build-egg` writes `game/objects/egg/egg.glb` (21 266 triangles, 589 KB). The file is committed, like the baked skies, so that only a change to the script needs Blender. It is in plain git, not in Git LFS.
- The `.glb` holds three objects, which `egg.gd` moves: `shell`, `lid` with its origin on the hinge, and `gear` with its origin on its axis. It holds no texture. `egg.glb.import` gives the material `brass` the look of `game/objects/egg/brass.tres`: the kit shader with the Metal048A maps, tint (0.9, 0.76, 0.5), metallic 1. The jewels are plain PBR materials from the script: mirrors with the hue of the board's gem colours and a small glow.
- The light: one `OmniLight3D` 1 m above the marker, colour (1.0, 0.78, 0.5), energy 1.2, range 4 m, no shadows, not baked (the exception in section 4).

### Measured (RTX 5090, 2026-11-21)

GPU time is the median of three runs of the `just perf` scene. "Before" is one such set. "After" was measured in three sets: its mean repeated within 0.02 ms, its 99th percentile within 0.1 ms. The GPU also did other work, and at these loads it changes its clock speed between runs (section 10), so a difference below about 0.1 ms is not reliable.

| Run | Before: mean / p99 | After: mean / p99 | VRAM before / after |
|---|---|---|---|
| `core_loop`, Medium at 1080p | 0.75 / 0.89 ms | 0.78 / 0.92 ms | 872 / 882 MB |
| `core_loop`, Ultra at 4K | 3.34 / 4.12 ms | 3.39 / 4.23 ms | 2347 / 2357 MB |
| `fixture`, Medium at 1080p | 0.70 / 0.93 ms | 0.74 / 0.92 ms | 875 / 875 MB |
| `fixture`, Ultra at 4K | 3.03 / 3.91 ms | 3.07 / 3.94 ms | 2349 / 2349 MB |

- The budgets of section 8 hold: Medium at 1080p has a 99th percentile of 0.9 ms (limit 3 ms) and uses 882 MB (limit 4 GB); Ultra at 4K has a 99th percentile of 4.2 ms (limit 16.7 ms).
- One gem that fills about 40 % of the height of the view costs about 0.5 ms at Ultra 4K: 4.3 ms with the gem, 3.8 ms without it, in three runs each. The same test at 1080p gives no result, because the change of clock speed is larger than the cost.
- The style review of the B1 level (#28) found a median luma of about 20 of 255 in the vault that hides the egg. With a copy of that level (not part of this change) and the egg's light, one frame of its `egg` shot has a median luma of 58. The two numbers come from different runs, and the first one was not measured again here.
- Colourblind palette, mean luminance of the gem in one close view each: blue 0.08, reddish purple 0.13, orange 0.16, yellow 0.24. The step from reddish purple to orange is small. The standard gems are between 0.14 and 0.16.

### Not verified

- No check finds a shader that does not compile. `godot --headless` does not compile shaders, and `just gallery` fails only on a blank frame; a gem with a broken shader is a plain grey solid, not a blank frame. After a change to a shader, run the game on a GPU and search its log for `SHADER ERROR`.
- No level here uses the noon or the dusk sky. With the sky changed at run time in `core_loop` (the floor kept its dawn lightmap), the gems stay coloured at dusk but are darker: 0.10 to 0.12 mean luminance, against 0.14 to 0.16 at dawn. Look at the gems again in the first level with a dusk sky.
- The colourblind palette was not tested with a simulation of colour vision or with a player.
- The lightmaps of `core_loop` and `fixture` were baked with the old gem light, whose bounce light was baked. They were not baked again. The `.sha256` check does not see a change to an object scene.
- The finish beam was compared in one view on one GPU: the old and the new beam shader give the same picture there.
- Every frame here comes from one GPU and one driver. Two expressions that GLSL leaves undefined (a `smoothstep` with equal edges in the beam, a division by zero for opposite facets in the gem) drew correctly on it. They were found by reading and by review, and they are corrected; a frame did not show them.
