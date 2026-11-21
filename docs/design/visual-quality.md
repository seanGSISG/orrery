# Visual quality bar

Status: approved direction, 2026-11-20. Sean asked for "super crisp, photorealistic, very nice and modern looking graphics". This document turns that request into checks that agents can test. Every art ticket and every rendering ticket aims at this bar.

Engine: Godot 4.7.2, Forward+. Every setting name below comes from the 4.7.2-stable class reference (`doc/classes/*.xml` at tag `4.7.2-stable`) or the 4.7 manual (docs.godotengine.org/en/stable). Section 9 lists what we could not verify. A value that says "start" is a first value; tune it with the gallery, but stay inside the stated range.

Fixed decisions (`docs/plan.md` §4.7 and #38):

- Realism in M1 comes from baked lightmaps (`LightmapGI`), baked on the GPU at high quality.
- Real-time ray-traced reflections and shadows are a later, Ultra-only spike (#38). Nothing here depends on it.
- Sky by tier: Beginner is Earth sky clockwork at dawn. Intermediate is a high, bright sky. Advanced is the edge of space with one restrained planet.
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
| Sun angular size (PCSS soft shadows) | 0° | 0° | 0.5° | 0.5° | `Light3D.light_angular_distance` |
| Omni and spot shadow atlas | 2048 | 2048 | 4096 | 4096 | `Viewport.positional_shadow_atlas_size` |
| Lightmap bicubic sampling | off | on | on | on | `RenderingServer.lightmaps_set_bicubic_filter` |
| Mesh LOD threshold (pixels; higher is coarser) | 2.0 | 1.0 | 1.0 | 0.5 | `Viewport.mesh_lod_threshold` |
| Marble reflection probe (section 5) | off | off | off | on | `ReflectionProbe` node, `UPDATE_ALWAYS` |

Rules for the table:

- The level's `LightmapGI`, static reflection probes and baked shadowmask are the same in every preset. Presets change only real-time cost.
- Distance fog gives aerial perspective in every preset, so the cloud sea looks the same depth on Low and on Ultra. When volumetric fog is on, the preset code lowers the distance-fog density so the haze does not double.
- SDFGI never runs in a campaign level, because campaign levels use lightmaps. SDFGI runs only in Ascent and Planetarium on Ultra, where the sun moves.
- The 0.5° sun matches the real sun ("approximately 0.5", `Light3D.light_angular_distance`). Godot warns that PCSS has a "noticeable performance cost", so Low and Medium use 0°.
- Fixed project settings (all presets): `rendering/anti_aliasing/quality/use_debanding=true`, `rendering/reflections/reflection_atlas/reflection_size=256` (the default), `rendering/lightmapping/lightmap_gi/use_bicubic_filter=true`.

### Tonemapping, exposure and colour grading

- `Environment.tonemap_mode = TONE_MAPPER_AGX` in every environment. AgX is "better than other tonemappers at maintaining the hue of colors as they become brighter", and it works with HDR output. Filmic and ACES do not work with HDR output (manual, "HDR output").
- Start: `tonemap_agx_white = 16.29` (the default) and `tonemap_agx_contrast = 1.25` (the default). Range: white 6.0 to 16.29 ("at least 6.0" for photorealistic light), contrast 1.0 to 1.5.
- Exposure is fixed per sky preset (`Environment.tonemap_exposure`). Auto exposure stays off (`CameraAttributesPractical.auto_exposure_enabled = false`), so a level looks the same every run and gallery shots are comparable. In Ascent, a script sets the exposure from the same height curve that drives the time of day.
- Colour grading uses only `tonemap_agx_contrast` and `adjustment_saturation` (with `adjustment_enabled`). Do not use a colour-correction LUT (`adjustment_color_correction`) and do not use the Soft Light glow blend mode. Both are SDR-only and break HDR output.
- Glow: `glow_blend_mode = GLOW_BLEND_MODE_SCREEN` (the default), `glow_intensity` start 0.3, `glow_hdr_threshold` 1.0 or higher, `glow_bloom = 0.0`. Glow must not make a haze over the whole image.

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

- Static probes: `ReflectionProbe` with `update_mode = UPDATE_ONCE`, `box_projection = true` and `size` at most 30 m, placed along the track so that each track section is inside one probe. They are the same in every preset.
- Marble probe (Ultra only): one `ReflectionProbe` follows the marble with `UPDATE_ALWAYS`. Its `cull_mask` leaves out the marble's layer, so the marble does not reflect itself. Its `reflection_mask` is only the marble's layer, so only the marble uses it. Godot recommends "only one ReflectionProbe with UPDATE_ALWAYS at most per scene", because of its "significant performance cost".
- SSR (High and Ultra) adds sharp reflections on opaque surfaces such as polished stone and brass. SSR does not reflect transparent materials and does not apply to them (manual, "Environment and post-processing").

## 5. The glass marble

The glass marble (and the translucent ghost) gets reflection and refraction without ray tracing:

- **Material:** `BaseMaterial3D` with `transparency = TRANSPARENCY_ALPHA`, `metallic = 0`, `metallic_specular = 0.5` (F0 about 0.04, the value for glass with an index of refraction near 1.5), `roughness` 0.02 to 0.05, and `refraction_enabled = true`.
- **Refraction:** `refraction_enabled` distorts the screen texture behind the marble along its normal. Only opaque objects appear in the refraction. This is correct for the tiny orrery inside the glass marble: it is an opaque mesh inside the sphere, so the glass bends it like a lens. Start `refraction_scale` at 0.05 (the default). If the result does not look like a solid glass ball, write a small spatial shader that bends the view ray through the sphere and reads `hint_screen_texture`. Do this only if the gallery shows the need.
- **Reflection:** the static probes on every preset, plus the marble probe on Ultra. Fresnel from the PBR model makes the rim brighter at grazing angles.
- **Shadow:** `TRANSPARENCY_ALPHA` "disables shadow casting". Add a child sphere with `cast_shadow = SHADOW_CASTING_SETTING_SHADOWS_ONLY`, so the marble casts a sun shadow. The crisp blob shadow straight down (`docs/plan.md` §2.11) stays in addition.
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
  - `BaseMaterial3D` detail on UV1 uses the same UV scale as the base textures (`material.cpp`). Detail on UV2 rescales UV2, and UV2 is the lightmap UV. So close-zone materials use one kit `ShaderMaterial` (a `BaseMaterial3D` converted to a shader, plus a `detail_scale` uniform on UV1). Do not use `detail_uv_layer = DETAIL_UV_2` on lightmapped meshes.
- **Skies:** HDRIs at 4K. A tier sky may go to 8K only if its 4K gallery shot looks soft. (At 4K output with a 70° view, a 4K equirectangular sky is about 2.7× softer than the screen.)
- **Import settings:** `compress/mode` VRAM Compressed, `compress/high_quality = true` (BC7) for albedo, normal maps with RGTC (`compress/normal_map`), mipmaps on. Set `roughness/src_normal` on each roughness map, so the import filters roughness and reduces specular aliasing.
- **Source files:** use the OpenGL (Y+) normal-map variant (Poly Haven `nor_gl`, ambientCG `NormalGL`). Store albedo, roughness and AO as JPG (quality 90 or higher), and store normal maps as PNG, because lossy compression shows as blocky shading in normal maps.
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
| Brass, aged or brushed | 1 | 0.30–0.55 | Same hue, 10–20% darker |
| Gold | 1 | 0.10–0.35 | Warm yellow-orange; brightest channel 230–250 |
| Glass | 0 | 0.00–0.08 | Near white; tint comes from transparency |

These ranges are starting values from common PBR practice. We did not take them from a Godot source.

- No pure black or pure white albedo. Dielectrics stay between sRGB 30 and 240. Metals stay between sRGB 180 and 250 in their brightest channel.
- Metallic is 0 or 1. Use values between only for dust or dirt masks.
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
| Low | 1080p | GPU time (mean, 99th percentile) | Its GPU time is higher than Medium's |
| Medium | 1080p | GPU time, VRAM | The 99th-percentile GPU time on the RTX 5090 is above the budget (`docs/plan.md` §4.7: start at 3 ms, calibrate in M1), or VRAM is above 4 GB |
| High | 1440p | GPU time | Report only |
| Ultra | 4K | GPU time | The 99th-percentile GPU time on the RTX 5090 is above 16.7 ms (60 fps) |

- The check also fails when Low, Medium, High and Ultra do not cost more in that order at 1080p. This proves that the presets change real settings (#24).
- The camera path includes one fast orbit around the marble. During that orbit, the check saves two frames 1/60 s apart as the `motion` pair for rubric check 3.

## 9. Not verified

- The VRAM, bake-size and Git LFS numbers are estimates. #20 and #24 must measure them and replace the estimates.
- Lightmap file size per level (about 5 MB) assumes about 5,000 m² of near surfaces at 0.1 m and 20,000 m² of far scenery at 0.4 m, so about 1 million texels with atlas padding. We have not baked a level.
- The material ranges in section 6 are common PBR practice, not values from a Godot source.
- We did not test how much MSAA 2× costs on a real GTX 1660. The plan's 5090 budget stands in for it.
- We did not check whether a script can call the editor plugin's bound `_bake` method from a running editor. #24 must prove the bake command.
- We did not test HDR output on Sean's KDE Wayland session, or in `gamescope`.
- The −0.5 mipmap bias for FSR 2.2 at native resolution is our choice, not a Godot recommendation.
