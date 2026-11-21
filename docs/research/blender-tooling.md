> **Research snapshot, 2026-11-20.** `docs/plan.md` records the decisions. Where this report and the plan differ, the plan wins.
> Superseded here: the plan uses the **official Blender Lab MCP** (fallback: `ahujasid/mcp-for-blender`), and **level scripts are the source**, so `.blend` and `.glb` files are build outputs and are not committed.

# Blender tooling for Claude Code agents (research, 2026-11-20)

Host: CachyOS, KDE Wayland, RTX 5090. Blender is NOT installed on this host (`pacman -Q blender` fails), so nothing below was run locally. Nothing was installed.

## 1. Blender MCP servers

Stats from `gh api` / Gitea API on 2026-11-20.

| Candidate | Stars | Last commit | License | Blender | Transport | Notes |
|---|---|---|---|---|---|---|
| ahujasid/mcp-for-blender (renamed from blender-mcp; github.com/ahujasid/mcp-for-blender) | 35,164 | 2026-11-18 | MIT | 3.0+ (README) | stdio MCP server (`uvx mcp-for-blender`) <-> TCP/JSON socket <-> add-on | v2.3.1. Community; README: "not made by Blender". 68 open issues. |
| Blender Lab MCP, OFFICIAL (projects.blender.org/lab/blender_mcp) | 39 (Gitea) | 2026-09-29 | GPL-3.0-or-later | 5.1+ only | stdio MCP server <-> TCP socket <-> add-on; Streamable HTTP documented via llama.cpp wiki page | Releases: add-on v1.0.3 (2026-09-11), server pkg 1.0.2. 30 open issues. |
| HoldMyBeer-gg/blenderwright | 201 | 2026-11-20 | MIT | 5.2+ (per third-party comparison, unverified) | stdio + signed (HMAC) socket | 279 tools / 32 modules, mesh-quality analysis. Young repo. |
| nirholas/blender-mcp (npm @three-ws/blender-mcp) | 5 | 2026-11-10 | Apache-2.0 | 3.0+ | stdio | Headless, no add-on: inspect/convert/optimize/render/script files. Low adoption. |
| ifBars/blender-agent-studio | 122 | 2026-11-17 | MIT | not checked | Claude Code plugin (`claude plugin marketplace add ifBars/blender-agent-studio`) | Mostly headless; `blender_check_setup`; optional live-viewport add-on. Not evaluated in depth. |
| credoksopho1984/blender-ai-copilot-studio | 516 | 2026-11-15 | MIT | not checked | In-Blender copilot + HTTP endpoint | Runs its own LLM copilot inside Blender; not aimed at Claude Code. Not evaluated in depth. |
| dhakalnirajan/blender-open-mcp, djeada/blender-mcp-server, shefq/blendrelay-mcp, newo-ether/blender-mcp | 123 / 35 / 38 / 14 | 2026-10 to 11 | MIT | n/a | n/a | Not evaluated. |

Not verified: whether any of the smaller ones are safe or good. Only the top two were read in detail (README, source layout).

### ahujasid/mcp-for-blender (details)
- Nine tools: `execute_blender_code`, `look` (viewport/camera/multi-angle sheet/animation strip; solid/material/rendered/wireframe/xray; or show a render/image file), `get_scene_info`, `generate_3d` (Tripo/Hunyuan3D/Hyper3D/Meshy), `generate_gaussian_world` (World Labs, Blender 5.3+), `search_assets`/`import_asset` (Poly Haven, Sketchfab, Poly Pizza), `get_addon_status`, telemetry controls.
- Security: `execute_blender_code` = arbitrary Python in Blender (README: "ALWAYS save your work"). Add-on listens on localhost by default. Optional "Allow Remote Connections" has no auth or encryption (README says use SSH tunnel instead).
- Telemetry: a minimal anonymous usage record is ON by default (install ID, tool name, success, timing, versions, OS). Content (prompts, code, screenshots) only with opt-in. Disable fully with env `DISABLE_TELEMETRY=true`.
- Premium (paid) tier for AI generators exists; Poly Haven/Sketchfab need to be toggled in the add-on sidebar.
- Python: needs uv, Python 3.10+ for the server (runs outside Blender). README warns uv may pick a conda/pyenv Python that breaks install; pin with `--python 3.11` or `UV_PYTHON_PREFERENCE=only-managed`.
- Install (README, "Claude Code"):
  ```
  claude mcp add blender uvx mcp-for-blender
  uvx mcp-for-blender install-addon     # then Blender: Edit > Preferences > Add-ons > enable "Interface: MCP for Blender"
  ```
  One-liner alternative: `curl -LsSf https://www.mcp-for-blender.com/install.sh | sh` (pipes a script to sh; read it first). Suggested variant with telemetry off and user scope:
  `claude mcp add --scope user -e DISABLE_TELEMETRY=true blender -- uvx mcp-for-blender`
  Add-on server starts when Blender opens; otherwise N panel > "MCP for Blender" > Start MCP Server.
- Repo also has `.claude-plugin/` (Claude plugin; commit "vendor 2.3.1 wheel in the Claude plugin"). Not tested.
- Not verified: where `install-addon` writes on the Arch package vs tarball; behavior as a legacy (non-extension) add-on on Blender 5.3. Commits mention 5.3 features, so it is tracked against 5.3.

### Blender Lab MCP (official)
- Source: https://projects.blender.org/lab/blender_mcp ; docs https://www.blender.org/lab/mcp-server/ (Cloudflare blocks curl; read via a fetch tool).
- Blender 5.1 or newer. Add-on manifest id `mcp`, maintainer "Blender Lab", license GPL-3.0-or-later, permission "network: local TCP socket server".
- Architecture: `MCP client <-stdio-> blender-mcp (python pkg, uv) <-TCP-> Blender add-on`. Env `BLENDER_MCP_HOST`, `BLENDER_MCP_PORT`, `BLENDER_PATH` (for CLI tools).
- 26 tools (readme_tools.rst): `execute_blender_code`, `execute_blender_code_for_cli` (runs in a background Blender process), `get_blendfile_summary_*` (+ `_for_cli` variants that open a .blend headless), `get_objects_summary`, `get_object_detail_summary`, `get_python_api_docs`, `search_api_docs`, `search_manual_docs` (bundled API + manual RST, 5.2 refresh as of 2026-09-11), `get_screenshot_of_area_as_image`, `get_screenshot_of_window_as_image/json`, `jump_to_*`, `render_thumbnail_to_path`, `render_viewport_to_path`. No asset-library or AI-generation integrations. No glTF export tool (use `execute_blender_code`).
- Security: Blender's own warning: "will execute LLM generated code in Blender without any guards ... recommended to use a virtual machine, or a system without access to sensitive information." No socket auth found.
- Install for Claude Code (from official Setup wiki, Linux; `claude mcp add` form is my translation of its JSON, not quoted from the docs):
  1. Blender 5.1+ GUI: drag the install link on the lab page (add-on zip `mcp-1.0.3.zip` from the `lab.blender.org` extension repo); allow the "lab" repository; then Preferences > Add-ons > "MCP" > start server (auto-start is optional; the Anthropic-side tutorial text says to click Start each Blender launch).
  2. `git clone https://projects.blender.org/lab/blender_mcp.git ~/blender_mcp`
  3. `claude mcp add blender -- uv --directory $HOME/blender_mcp/mcp run blender-mcp` (use an absolute path instead of `$HOME` if the shell does not expand it)
- Anthropic also ships a "Blender" connector for Claude Desktop that uses this add-on (per a third-party guide; the same guide says the connector works with other MCP clients including Claude Code).
- Staleness: last commit 2026-09-29; bundled docs are for 5.2, Blender 5.3 shipped 2026-11-10. Small star count, but it is the Blender-run project.

### Recommendation
Primary: ahujasid/mcp-for-blender. Reasons: by far the most used and most actively maintained (daily commits), works on Blender 3.0+ (no lock to 5.1+), `look` gives multi-angle/wireframe/render views for agent self-checking, built-in Poly Haven/Sketchfab/Poly Pizza import, one-line `claude mcp add`. Set `DISABLE_TELEMETRY=true`, leave remote connections off, run it only against a scratch Blender you save often.
Runner-up / safer: Blender Lab MCP. Pick it if you prefer a Foundation-run, no-telemetry, no-network-integration server, or want its bundled API/manual search and `_for_cli` background tools. It is GPL, needs 5.1+, and has fewer features. Running both at once is possible (different add-ons, different sockets) but adds surface; I would not.
Both are "live GUI session" tools. For deterministic game-asset export, use headless scripts (section 3) and keep MCP for exploration and visual checks. This split is my judgment, not a documented practice.

## 2. Blender version and install on CachyOS/Arch

- Current stable: Blender 5.3.0, released 2026-11-10. Blender 5.2 LTS (released 2026-07-14, supported to July 2028) is at 5.2.4 (2026-11-10). Blender 5.4 is alpha. Source: https://www.blender.org/download/ and https://www.blender.org/releases/ (via search excerpts).
- Arch `extra/blender` = `17:5.3.0-1`, built 2026-11-11 (verified with `pacman -Si`). Its PKGBUILD builds against OptiX headers (`_optix_version=9.1.0`) and `cuda`, depends on system `python`, `python-numpy`, `python-requests`. Optional `cuda` for Cycles CUDA. Host system Python is 3.14.10.
- Bundled Python in official builds: 5.0 = 3.11.13, 5.1 = 3.13.9, 5.2 = 3.13.13 (StackExchange table); 5.3 stays 3.13 (Japanese-language release summary, and the VFX Platform table). Add-ons with compiled wheels need cp313 for 5.1+.
- Issue (my inference, not tested): the Arch package uses system Python 3.14, so pip-installed or bundled cp313 wheels will not load, and extension packages built for 3.13 may misbehave. The official tarball has an isolated, known Python.
- Godot's manual says (docs 4.7, `available_formats`): "strongly recommended to use an official Blender release downloaded from blender.org, as opposed to a Linux distribution package or Flatpak" for direct `.blend` import (packaging/sandbox issues).
- Install options:
  - Official tarball (`blender-5.x.y-linux-x64.tar.xz`, ~367 MB): recommended. Extract to e.g. `~/opt/blender-5.2.4`, symlink `~/.local/bin/blender`, set `BLENDER_PATH`. Pin the version per project. Bundled Python, no distro drift.
  - `pacman -S blender`: works, always newest (5.3.0), has OptiX. Risk: system Python 3.14 mismatch above; rolling updates change the version under the agent.
  - AUR `blender-bin` 5.3.0-1 repackages the tarball (15 votes). `blender-git` is a nightly build. Not needed.
  - Flatpak: avoid (sandbox: file paths, headless, and Godot warns against it).
  - Snap exists on blender.org; not relevant on Arch.
- Version choice (judgment): 5.2.4 LTS tarball for a long-lived game project; 5.3.0 if you want the newest. One reason to prefer 5.2: per FOSSLinux (2026-11-11, secondary source) Blender 5.3 switches the default GPU backend on Linux to Vulkan, while 5.2 LTS defaults to OpenGL. A Blender tracker comment (March 2026) reports black node previews in Blender 5.0.1 on Vulkan with NVIDIA driver 595.45.04 on Linux; switching to OpenGL or driver 590.48.01 fixed it. Not verified for 5.3 or the 5090.

## 3. Headless Blender

- Basic: `blender --background --factory-startup --python script.py -- <args>`. Useful flags (Blender 5.3 manual): `--python-exit-code <1..255>` exits non-zero when the script raises; `--factory-startup` skips user startup file; `--python-use-system-env` / `--python-use-user-env` weaken Python isolation; `--addons a,b` enables add-ons; `--gpu-backend vulkan|opengl|metal`; `--gpu-device`. Source: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html.
- Use the data API in scripts; many `bpy.ops` need UI context and fail in background mode (Voyager guide, 2026-11-06).
- EEVEE in background on Linux: NOT verified on this machine (no Blender installed; I did not install). What sources say:
  - EEVEE needs a GPU context even with `-b`. A headless OpenGL/EGL path on Linux was added in Blender 3.4 (commit 3195a38120 "Introduce headless OpenGL rendering on Linux"; cited in the Voyager guide).
  - An NVIDIA-container write-up (c.pgdm.ch, 2023) needs `libEGL_nvidia` registered in `/usr/share/glvnd/egl_vendor.d/10_nvidia.json` and `NVIDIA_DRIVER_CAPABILITIES=all`; on a normal Arch host with the NVIDIA driver this should already exist. Fallback if EGL fails: run under Xvfb (xvfb-run) or on the real Wayland/X session.
  - 5.3 changed the Linux default backend to Vulkan (secondary source). Whether background mode with Vulkan needs a display is unknown to me. Force with `--gpu-backend opengl` or `--gpu-backend vulkan` and test both.
  - Recommended 10-line smoke test once Blender is installed: render a cube with EEVEE under `env -u DISPLAY -u WAYLAND_DISPLAY blender -b --factory-startup --gpu-backend opengl --python test.py`, check the PNG is not black.
- Cycles GPU/OptiX in background: Cycles GPU does not need OpenGL or X in `-b` mode (Blender devtalk answer, 2019; old but consistent with the design). Select device in the script: `prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices(); for d in prefs.devices: d.use = d.type != "CPU"; scene.cycles.device = "GPU"`. OptiX needs the NVIDIA driver; official builds ship OptiX support; the Arch build links OptiX 9.1.0 headers. Not tested on a 5090. For a marble game, bakes (AO, lightmaps) may matter more than final renders; Cycles OptiX is the fast path.
- glTF/GLB export from script, with custom properties:
  ```python
  bpy.ops.export_scene.gltf(
      filepath="/abs/out.glb", export_format='GLB',
      export_extras=True,        # custom properties -> glTF extras
      export_yup=True, export_apply=True,   # apply modifiers (warning: drops shape keys)
      use_selection=False, export_cameras=False, export_lights=False)
  ```
  `export_extras` ("Custom Properties, Export custom properties as glTF extras") confirmed in the Blender 5.1/5.3 Python API docs and the 5.2 manual (https://docs.blender.org/api/current/bpy.ops.export_scene.html). Blender 5.x also has meshopt compression (`export_meshopt_compression_enable`, extension EXT_ or KHR_meshopt_compression) plus Draco. Do NOT enable meshopt/Draco for Godot unless you verify Godot's glTF importer supports it (I did not verify). Custom property values must be JSON-serializable types (int, float, str, arrays); object, mesh-data and material custom properties go to node, mesh and material extras respectively (from the Godot side description below).
- Running `bpy` as a module (`uv add bpy`) is another option; not researched (wheel needs a matching Python; 5.x wheels are cp313).

## 4. Blender -> Godot 4

- Current Godot: 4.7.2-stable (2026-08-18). 4.7-stable 2026-06-18. (3.6.3 also released 2026-08-22, old line.) Source: `gh api repos/godotengine/godot/releases`. I did not check for a 4.8 beta.
- Two routes (docs: https://docs.godotengine.org/en/4.7/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html):
  - Direct `.blend`: Godot calls Blender to export glTF transparently, then uses its normal glTF import. Needs Blender 3.0+ (3.5+ recommended); set Editor Settings > Filesystem > Import > Blender > Blender Path (auto-detected at default locations); Blender must be installed before opening the project. Disable via "Blender > Enabled". Official tarball recommended, not distro/Flatpak. Team note in docs: `.blend` in the repo means every contributor needs Blender.
  - `.glb` export: explicit and reproducible; Godot needs no Blender. Docs recommend glTF for complex scenes and animations.
- Recommendation (judgment): keep `.blend` as source, export `.glb` with a headless script into the Godot project, commit both. Agents can then run the export, then `godot --headless --import` without any Blender path setup in the editor. Direct `.blend` import is fine for quick prototyping.
- Import hints = name suffixes (docs: node_type_customization):
  - `-noimp`: node/animation removed on import. `-col`: adds StaticBody3D + trimesh collision child. `-convcol`: convex. `-colonly`: removes the mesh, keeps a StaticBody3D with trimesh. `-convcolonly`: same with a convex shape. `-rigid`: imports as RigidBody3D. `-occ`/`-occonly` occluder, `-navmesh` navigation mesh, `-vehicle`/`-wheel`, `-loop`/`-cycle` on animation names, `-vcol` on material names.
  - Options `nodes/use_node_type_suffixes=false` or `nodes/use_name_suffixes=false` disable them; `-noimp`, `-vcol`, `-loop` still apply when only node type suffixes are off.
- glTF extras / custom properties in Godot:
  - Blender: set `export_extras=True`. Godot import dock (Blender import options): "Nodes > Custom Properties: imports custom properties from Blender as glTF extras" (docs: import_configuration).
  - Per DeepWiki on godotengine/godot (not verified against source line by line): node extras land as node metadata under the single key `"extras"` (a Dictionary), only when non-empty. Mesh and material extras land as `mesh.get_meta("extras")` and `material.get_meta("extras")`. Extras are not split into one meta entry per property.
  - Hooks: `EditorScenePostImport._post_import(scene)` (set per scene in the Import dock; can walk nodes and convert `extras` into node groups, scripts, collision layers etc.) or `GLTFDocumentExtension` (`_import_post_parse(state)`, `_import_node(state, gltf_node, json, node)`, `_import_post(state, root)`), registered via `GLTFDocument.register_gltf_document_extension()` from an editor plugin. The docs recommend `GLTFDocumentExtension` for predictable, runtime-compatible behavior.
- Lightmap UV2:
  - Import dock "Meshes > Light Baking = Static Lightmaps" sets GI mode Static and generates UV2 on import (Lightmap Texel Size controls density). Docs: import_configuration.
  - Per DeepWiki, this unwrap replaces any UV2 already imported (glTF `TEXCOORD_1` maps to UV2). So: do not author a lightmap UV in Blender for Godot; let Godot unwrap. Only keep a second Blender UV map if you set Light Baking to something other than Static Lightmaps. Whether Blender exports its 2nd UV map as `TEXCOORD_1`: not verified.

## 5. Other useful tools (short)

- Poly Haven API: https://api.polyhaven.com (`/types` returns hdris, textures, models; `/assets?t=textures` returned 871 entries when I called it). CC0. Already wired into ahujasid MCP; for agents, plain `curl` + `jq` is simpler than another MCP. API terms: attribution requested, no key. (Terms not re-read.)
- ambientCG API v2: `https://ambientcg.com/api/v2/full_json?type=Material&limit=1` works without a key (2043 results total on 2026-11-20). CC0. Downloads are zip with PBR maps.
- glTF-Transform: github.com/donmccurdy/glTF-Transform, 2,090 stars, MIT, pushed 2026-10-20; CLI `@gltf-transform/cli` 4.5.1 (npm modified 2026-09-28). Use: `npx @gltf-transform/cli inspect model.glb`, optimize/resize/prune/dedup/texture compress.
- glTF-Validator: github.com/KhronosGroup/glTF-Validator, 481 stars, Apache-2.0, pushed 2026-10-06. The npm `gltf-validator` package was last published 2024-10-22 (2.0.0-dev.3.10); the official CLI binaries are on GitHub releases. Use after export in CI.
- Godot MCP servers exist (Coding-Solo/godot-mcp 6.7k stars, MIT, pushed 2026-04-16; yurineko73/Godot-MCP-Native 882; tugcantopaloglu/godot-mcp 521, pushed 2026-10-09). Out of scope here; not evaluated.
- No Poly Haven MCP of note found (only 0-star repos).

## Could not verify
- Anything running on this host: EEVEE headless (EGL/Vulkan), OptiX on the 5090, Arch package Python mismatch, add-on install path with `uvx mcp-for-blender install-addon`.
- Blender 5.3 Vulkan-default claim comes from FOSSLinux (secondary); not confirmed on the official 5.3 release notes (fetch returned only a partial page).
- Blender 5.3 bundled Python = 3.13: inferred from a secondary summary and the VFX Platform 2026 table.
- blenderwright's Blender version floor and its tool count come from a third-party comparison and its README, not tested.
- Godot extras/UV2 behavior comes from DeepWiki summaries plus docs, not from running Godot.

## Sources
- https://github.com/ahujasid/mcp-for-blender (README, `gh api`)
- https://projects.blender.org/lab/blender_mcp (shallow clone: readme.md, readme_tools.rst, addon manifest, wiki Setup.md; Gitea API)
- https://www.blender.org/lab/mcp-server/
- https://www.blender.org/download/ , https://www.blender.org/releases/
- https://gitlab.archlinux.org/archlinux/packaging/packages/blender/-/raw/main/PKGBUILD ; https://archlinux.org/packages/extra/x86_64/blender/
- https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- https://docs.blender.org/api/current/bpy.ops.export_scene.html ; https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html
- https://www.fosslinux.com/163781/blender-5-3-vulkan-default-linux.htm
- https://c.pgdm.ch/notes/eevee-docker-gpu ; https://voyager.so/blog/headless-3d-rendering
- https://docs.godotengine.org/en/4.7/tutorials/assets_pipeline/importing_3d_scenes/ (pages: available_formats, import_configuration, node_type_customization) via github.com/godotengine/godot-docs
- https://deepwiki.com/search/2b2f6cbf-4b7b-40b1-8e03-2b0de456f494 ; https://deepwiki.com/search/00d13175-029d-4d08-ba31-9ef7b29fec74
- https://api.polyhaven.com ; https://ambientcg.com/api/v2/full_json
- https://github.com/donmccurdy/glTF-Transform ; https://github.com/KhronosGroup/glTF-Validator
