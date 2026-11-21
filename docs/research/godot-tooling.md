> **Research snapshot, 2026-11-20.** `docs/plan.md` records the decisions. Where this report and the plan differ, the plan wins.
> Superseded here: the plan uses **no third-party Godot MCP**. The project has its own harness MCP, and test runs render in `gamescope --backend headless`, with a windowed run as the fallback. Level tests run the route bot live and do not need exact physics repeats.

# Godot 4 agent tooling research (as of 2026-11-20)

Method: GitHub API (`gh api`), Godot source at tag 4.7.2-stable, godot-docs master RST (raw.githubusercontent.com), web search. Nothing installed. "UNVERIFIED" marks facts I could not confirm.

## 1. Version, 3D features, install, C#, typed GDScript

### Version
- Latest stable: **4.7.2-stable** (2026-08-18). 4.7 released 2026-06-18; 4.7.1 2026-07-14. Source: `gh api repos/godotengine/godot/releases`.
- 4.8 is in beta (beta 4 on 2026-11-18, "potentially the last beta", no RC or stable date given). Source: https://godotengine.org/download/archive and https://godotengine.org/article/dev-snapshot-godot-4-8-beta-2 ; beta 4 date from godotawesome.com blog (secondary). Do not use 4.8 for the project yet.
- 4.7 headline items: AreaLight3D, HDR output (Windows/macOS/iOS/visionOS/Linux Wayland), nearest-neighbor 3D resolution scale, Asset Store replaces Asset Library, VirtualJoystick, Tween.tween_await(). Source: web-search excerpt of the 4.7 release summary; https://godotengine.org/releases/4.7/ (page is client-rendered, I could not read it directly).

### 3D features (verified in godot-docs master)
- **Jolt**: built into Godot since 4.4. Docs: "By default, new projects will use it as the physics engine." The ProjectSettings default string is `"DEFAULT"` and "is currently equivalent to GodotPhysics3D", so a new project.godot gets Jolt written by the editor. For an agent-created project, set it explicitly: `[physics] 3d/physics_engine="Jolt Physics"`. The old GDExtension is in maintenance mode. Sources: https://docs.godotengine.org/en/stable/tutorials/physics/using_jolt_physics.html ; ProjectSettings `physics/3d/physics_engine`. Jolt has known differences (joint properties, ray-cast face_index off by default, ghost-collision handling) on the same page.
- **Forward+ only**: SDFGI ("only supported when using the Forward+ renderer"), VoxelGI (Forward+ only), volumetric fog (Forward+ only), FSR2 (`Viewport.SCALING_3D_MODE_FSR2` exists; Forward+ only per Godot's long-standing behaviour, UNVERIFIED in this pass). LightmapGI works on all renderers (docs say it suits mobile). SSR and SSAO are Environment effects (Forward+). `Viewport.use_taa` default `false`. FSR1 and nearest-neighbor scaling modes also exist. Sources: docs `using_sdfgi.rst`, `using_voxel_gi.rst`, `volumetric_fog.rst`, `environment_and_post_processing.rst`, `class_viewport.rst`.
- Physics tick default 60/s (`physics/common/physics_ticks_per_second`).

### Install on Arch/CachyOS
- `pacman -Si godot` shows `extra/godot 4.7.2-2` (also `cachyos-extra-znver4/godot 4.7.2-2.1`) and `godot-mono 4.7.2-2`. Optional dep: pipewire-alsa. I could not list package files (`pacman -F` db not synced), so whether it bundles export templates is UNVERIFIED (Arch package normally does not).
- **mise has a Godot tool**: registry entry `godot` -> `backends = ["aqua:godotengine/godot"]` (https://github.com/jdx/mise/blob/main/registry/godot.toml). aqua registry has `pkgs/godotengine/godot`. mise latest is v2026.11.11. Alternative: `github:godotengine/godot` backend (needs `exe = "Godot"`-style option in mise.toml; from a blog excerpt, not tested). I did NOT run `mise ls-remote godot`; whether the aqua asset mapping selects the Linux zip and names the binary `godot` for 4.7.2 is UNVERIFIED.
- Official release assets for 4.7.2 (gh api): `Godot_v4.7.2-stable_linux.x86_64.zip`, `Godot_v4.7.2-stable_win64.exe.zip`, `Godot_v4.7.2-stable_export_templates.tpz`, mono variants, `SHA512-SUMS.txt`.
- **Recommendation**: mise-pinned official binary (version pin per project, same version in CI, templates match exactly). pacman `godot` is fine for the editor but version drift between machine and CI breaks template matching.
- **Export templates path (Linux)**: `$HOME/.local/share/godot/export_templates/<version>/` (docs compiling_for_linuxbsd.rst). `<version>` is `4.7.2.stable` (mono: `4.7.2.stable.mono`) - naming format from memory/Godot convention, not re-verified. Editor data path is `~/.local/share/godot/` (docs data_paths.rst, XDG_DATA_HOME honoured). Install: unzip the `.tpz` (it is a zip with a `templates/` dir) into that folder, or use the editor's Manage Export Templates. AUR also has `godot-export-templates-windows-bin`, `-linux-bin` etc. at 4.7.2-1 (0-2 votes; low trust).

### C# vs GDScript
- C# needs the `.NET` editor build (`godot-mono` / mono zip), dotnet SDK, mono export templates, and slower iteration. godot-ai MCP treats C# as text-only (no build, no compiler errors). Most MCP servers and GUT are GDScript-first. Windows export from Linux works for both, but typed GDScript is the simpler path. **Recommend typed GDScript.**

### Make untyped GDScript a hard error
Project settings (Advanced Settings on, section GDScript; in project.godot under `[debug]`). Values: 0 Ignore, 1 Warn, 2 Error (numeric mapping from Godot convention; docs say "Warn or Error"). Docs: "you can turn them into errors ... your game won't compile unless you fix all warnings."
```
[debug]
gdscript/warnings/untyped_declaration=2
gdscript/warnings/inferred_declaration=2   ; optional, docs: recommended together with untyped_declaration
gdscript/warnings/unsafe_call_argument=2
gdscript/warnings/unsafe_cast=2
gdscript/warnings/unsafe_method_access=2
gdscript/warnings/unsafe_property_access=2
```
Defaults: untyped_declaration=0, inferred_declaration=0, unsafe_*=0 (unsafe_void_return=1). Also `debug/gdscript/warnings/exclude_addons` exists (default true, UNVERIFIED value) so addons do not trip errors. Sources: https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/warning_system.html ; `class_projectsettings.rst`. Check: `godot --headless --path . --check-only --script res://x.gd` (flag exists in CLI docs) or `--import`; I did not run it.

## 2. Godot MCP servers (gh api, 2026-11-20)

| Repo | Stars | Last push | License | Runs/inputs/screenshots | Notes |
|---|---|---|---|---|---|
| Erodenn/godot-mcp-runtime | 101 | 2026-11-13 | MIT | Yes to all: run_project, screenshots (with pixel stats and `likelyBlank`), batched input sim, UI discovery, live GDScript, profiling, debug output, headless scene editing, `background:true` (window off-screen), `render_movie`, attach mode | npx, no addon, 43 tools, Node 20+, Godot 4.5+, v4.0.1. Created 2026-02. Small but active. Injects a temporary autoload bridge on localhost TCP. |
| hi-godot/godot-ai | 3628 | 2026-11-20 | MIT | Yes: `project_run`, `editor_screenshot` (viewport, cinematic cam, running game), `game_manage` input_key/mouse/gamepad/action and frame-timed `input_sequence`, `logs_read` (game/editor), `test_run` in-editor test framework, step/suspend | Needs Godot 4.7+, uv, addon in project, live editor (WS 9500 + HTTP 8000). 46 tools, v4.4.2 (2026-11-16). Commits daily. Signed releases, telemetry (opt-out env). Most popular live-editor option. |
| satelliteoflove/godot-mcp | 188 | 2026-11-16 | MIT | Yes: run frozen, deterministic time stepping (`step_until`), input injection, runtime state digest, screenshot_game, exec GDScript in game | Addon + npm package, Godot 4.5+, v4.3.0. Best for deterministic playtests; needs editor. |
| HaD0Yun/Doyunha-Gopeak | 274 | 2026-11-13 | MIT | Run/stop, debug output, screenshot capture, input injection, LSP, DAP, 95+ tools | Bun install from release tgz; recent security fix (shell injection) suggests audit before use. |
| Coding-Solo/godot-mcp | 6716 | 2026-04-16 | MIT | Launch editor, run project, debug output, stop, scene/node edits, UID tools. No screenshots, no input injection | `claude mcp add godot -- npx @coding-solo/godot-mcp`. Last commit is an RCE fix; stale 7 months. Popular but too thin for this goal. |
| tugcantopaloglu/godot-mcp | 521 | 2026-10-09 | MIT | 157 tools, full runtime (per Erodenn's table) | Committed autoload addon. Not examined in detail. |
| youichi-uda/godot-mcp-pro | 648 | 2026-09-24 | proprietary ($15) | play_scene, simulate_key, get_game_screenshot | Paid, per Ziva blog. |
| GDAI MCP (gdaimcp.com) | n/a (closed) | n/a | proprietary ($19) | Editor and game screenshots, simulate input | Closed source; site says Godot 4.2+. |
| IvanMurzak/Godot-MCP | 361 | 2026-11-20 | Apache-2.0 | not examined | |
| ee0pdt/Godot-MCP | 623 | 2025-03-19 | MIT | stale | do not use |
| bradypp/godot-mcp | 90 | 2025-05-31 | MIT | stale | do not use |
| godotengine org | - | - | - | none | No official Godot MCP found (`gh search repos mcp --owner godotengine` returned nothing). |

Blog comparing servers (vendor-authored, Ziva): https://ziva.sh/blogs/godot-mcp-server-claude-code-cursor (2026-11-16). Treat as biased.

Claude Code install commands:
- Erodenn: `claude mcp add godot --scope project -e GODOT_PATH=$(mise which godot) -- npx -y godot-mcp-runtime` (README shows JSON form with `npx -y godot-mcp-runtime` and `GODOT_PATH`; the CLI flags are my translation).
- godot-ai: addon from AssetLib or GitHub release into `addons/godot_ai/`, enable plugin, press "Configure" for Claude Code in the dock (writes the `claude mcp add` entry, pinned, via `godot-ai attach` stdio). Needs `uv`.
- satelliteoflove: `npx @satelliteoflove/godot-mcp --install-addon /path/to/project`, enable plugin, add MCP config.

**Recommendation**: Start with **Erodenn/godot-mcp-runtime** (no addon, works without an open editor, built-in blank-frame detection, off-screen window). If it proves too limited, add **hi-godot/godot-ai** (largest community, frame-timed input, in-editor tests) or satelliteoflove for frozen-clock stepping. Do not build a custom one first. A thin custom layer is only needed for game-specific state dumps; that is cheaper as an autoload that prints JSON, driven by `exec`.

## 3. Automated testing

### Frameworks
- **GUT** (bitwes/Gut): v9.7.1 (2026-07-10). Headless: `godot --headless --path . --import` once, then `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test -gexit`. Exit 0 pass, 1 fail (tested by Open Red Software, Godot 4.7, https://www.openredsoftware.com/blog/ , article 2026-11-10 "How to run Godot unit tests from the command line with GUT and GdUnit4"). `-gconfig=.gutconfig.json` for config. GitHub API shows license "none" detected (repo has MIT text historically; UNVERIFIED).
- **gdUnit4** (godot-gdunit-labs/gdUnit4, 1310 stars, MIT, v6.2.3 2026-11-01): `./addons/gdUnit4/runtest.sh --godot_binary $(which godot) --headless --ignoreHeadlessMode -a res://test`. Without `--ignoreHeadlessMode` v6.2.3 exits 103 "Headless mode is not supported!". Exit 0 pass, 100 test failure. Alt: `godot --headless --path . -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests/...`. Scene runner has `simulate_key_pressed`, `simulate_frames`, `await_millis`. Official action: godot-gdunit-labs/gdUnit4-action (63 stars, 2026-11-17).
- Both articles warn: CI can pass although zero tests ran (missing import, wrong dir). Check the test count in output. Also `simulate_frames` counts frames, not seconds: use time waits.
- Tests that need rendered Controls: drop `--headless`, use `xvfb-run`.

### CLI flags (verified in command_line_tutorial.rst and main.cpp)
- `--headless` = `--display-driver headless --audio-driver Dummy`.
- `--fixed-fps <fps>`: "Force a fixed number of frames per second. This setting disables real-time synchronization."
- `--write-movie <file>`: "usually with .avi or .png extension. `--fixed-fps` is forced when enabled ... `--quit-after` can be used to specify the number of frames to write." `--disable-vsync` speeds it up. Formats: AVI (MJPEG), OGV, PNG sequence + WAV (files named `name00000000.png`). Both flags work in exported projects. Source: https://docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html
- `--quit-after N` iterations; `--disable-render-loop`; `--script`, `--check-only`, `--import`, `--log-file`, `--rendering-driver`, `--display-driver`, `--resolution`.
- Screenshot from GDScript: `await RenderingServer.frame_post_draw; get_viewport().get_texture().get_image().save_png(path)`.

### Determinism
- Godot docs do not promise determinism. Godot Jolt extension README (https://github.com/godot-jolt/godot-jolt): "will not be making any guarantees about determinism, and will not support cross-platform determinism"; the extension had a `more_deterministic` setting. I found no such setting in the built-in Jolt module's ProjectSettings docs (UNVERIFIED that it was carried over).
- Practical: `--fixed-fps 60` with physics ticks 60 gives repeatable frame/physics step counts on the same machine and binary. Same inputs on same binary is likely repeatable, but assert on tolerances, not exact floats, and never across Linux vs Windows. Jolt vs Godot Physics: I found no authoritative comparison.
- Fixed-tick input replay: GodotInputRecorder (bitwes, 8 stars, 2026-04-22) records/replays input in tests; Erodenn `input` batches and godot-ai `input_sequence` (frame-timed) replace it for agents. godot-gdotmcp-style tools also list record/replay.

### Automation sockets for a running game
- hi-godot/godot-ai: editor WS (9500, authenticated, loopback) + Python server; game helper for input/screenshots.
- Erodenn: McpBridge autoload, localhost TCP, JSON.
- mrf/godot-stagehand (9 stars, MIT, 2026-11-16): in-game WebSocket JSON-RPC server addon + Go MCP server binary; "Playwright for games" (props, input press/hold/combo, waits, screenshots, record/replay). Small, young.
- Randroids-Dojo/PlayGodot (40 stars, MIT, 2026-02-24): "Playwright for Godot", headless automation.
- Godot's own remote debugger protocol (`--remote-debug tcp://...`) exists; I did not research it.

## 4. Real GPU frames without a visible window

- **`--headless` does NOT render.** `main.cpp` (4.7.2-stable): `--headless` sets `display_driver = "headless"` with comment "no audio, no rendering"; `DisplayServerHeadless::get_rendering_drivers_func()` returns only `"dummy"`; `RasterizerDummy` is used. Viewport textures have no image. Open Red Software confirms: "You can't take a screenshot with --headless ... a script that waits for a drawn frame never finishes" (https://www.openredsoftware.com/blog/godot-screenshot-command-line). A different blog claimed headless can still read the viewport; the source contradicts it. Use headless only for logic tests, imports and exports.
- **Simplest reliable way on this machine: run windowed on the KDE session.** Real RTX 5090 Vulkan, Forward+, no virtual display layer. Use `godot --path . --rendering-driver vulkan [--display-driver wayland|x11]` and either (a) a script that saves the viewport, or (b) Movie Maker: `godot --path . --write-movie /tmp/shot/f.png --fixed-fps 30 --quit-after 120` (deterministic frames, PNG sequence, quits by itself). Window flashes on screen; Erodenn's `background:true` moves it to (-9999,-9999) after start (not guaranteed to stop focus steal).
- Alternatives:
  - `xvfb-run` + NVIDIA: needs GPU-bound Xvfb. One agent-skill excerpt detects a display with `glxinfo | grep -i nvidia` else falls back to software lavapipe; also notes the separate render thread wrote no frames under Xvfb. Plain `xvfb-run` gives Mesa software GL (`--rendering-driver opengl3`), not Forward+/GPU. Not recommended for fidelity.
  - **gamescope**: source (src/main.cpp) has `--backend headless` "no window, no DRM output". Might give GPU Vulkan with no visible window; NVIDIA 5090 behaviour UNVERIFIED. Worth a 10-minute test: `gamescope --backend headless -W 1920 -H 1080 -- godot --path . ...`.
  - **cage / weston headless**: wlroots supports `WLR_BACKENDS=headless` and `WLR_RENDERER=vulkan|gles2` (wlroots docs/env_vars.md), so `WLR_BACKENDS=headless cage -- godot ...` is plausible. NVIDIA GPU rendering on wlroots headless UNVERIFIED; not tested. Weston headless not researched.
- Recommendation: windowed on KDE for screenshots now (via godot-mcp-runtime or Movie Maker); evaluate gamescope headless later if focus stealing hurts. Run unit tests with `--headless`.

## 5. Windows builds from Linux

- Export from Linux: install templates (see §1), define a "Windows Desktop" preset (creates `export_presets.cfg`), then `godot --headless --path . --export-release "Windows Desktop" build/win/game.exe`. Docs: "--headless is required on platforms without GPU access (CI); on platforms with GPU it prevents a window". Source: command_line_tutorial.rst, exporting_projects.rst.
- **rcedit/wine not needed for icons any more.** Docs: since 4.1 Godot creates the ICO from the preset icon (PNG/WebP/SVG); the icon page no longer mentions rcedit. Maintainer comment in a closed issue (2025-10-28): "as of 4.5 rcedit is not a requirement anymore to modify the icon" (https://github.com/godotengine/godot/issues/30830). Whether version/company metadata also works without rcedit: UNVERIFIED.
- Code signing on Linux: `osslsigncode` (docs exporting_for_windows.rst), env vars `GODOT_WINDOWS_CODESIGN_*`.
- Windows ARM64 templates exist. D3D12 export is optional (preset "Export D3D12").
- **Smoke test under Wine**: no authoritative source found; UNVERIFIED. Godot Windows builds default to Vulkan; Wine+DXVK/VKD3D on NVIDIA would need testing. Cheap smoke test: `wine game.exe --headless --quit-after 60` (starts engine, loads project, no GPU needed). For real validation use a `windows-latest` runner.
- **GitHub Actions**:
  - barichello/godot-ci (1158 stars, MIT, tag 4.7.2-stable 2026-08-18, Docker `barichello/godot-ci:4.7.2` and `:mono-4.7.2`): ready container with Godot and templates; Linux runner only. Its issue says Windows icon needed rcedit/wine (now obsolete).
  - firebelley/godot-export (655 stars, MIT, v8.0.0 2026-05-28): exports all presets, needs Linux headless Godot URL, optional `wine_path` for rcedit, node24. Run on ubuntu-latest.
  - chickensoft-games/setup-godot (188 stars, MIT, v2.4.3 2026-10-01): installs Godot (with or without .NET) and optionally templates on **ubuntu, macos and windows-latest** runners; version e.g. `4.7.2`, `include-templates: true`, caches. Best fit for running GUT/gdUnit4 on `windows-latest`: `uses: chickensoft-games/setup-godot@v2` then `godot --headless ...`.
  - gdUnit4-action for gdUnit4 tests.
- Recommended CI: matrix `[ubuntu-latest, windows-latest]` with setup-godot (templates on), run tests headless, then `--export-release` per OS; upload artifacts.

## 6. Unity / Unreal comparison (one paragraph)
Unity has a very active MCP ecosystem: CoplayDev/unity-mcp (16,089 stars, MIT, pushed 2026-11-17), IvanMurzak/Unity-MCP (4,674, Apache-2.0, 2026-11-19), and Unity now ships an official plugin and CLI/MCP mode for Claude Code (https://unity.com/features/ai). Unreal 5.8 (2026-06-23) has an official experimental Epic "Unreal MCP" plugin (HTTP MCP; `ModelContextProtocol.GenerateClientConfig` writes Claude Code config) plus community servers (ChiR24/Unreal_mcp, 1,053 stars, MIT). Linux editors: Unity officially supports only Ubuntu 22.04/24.04 on GNOME (Wayland with NVIDIA driver 550+ only on 24.04), anything else (Arch, KDE) is unsupported; Epic documents a Linux development quickstart and UE 5.8 Linux recommended specs (source build or installed build); I did not verify distro support or KDE Wayland behaviour for either editor, so "runs well on CachyOS" is UNVERIFIED. Both heavy compared with Godot's single binary and CLI.

## Unverified / gaps
- mise `godot` tool actually installing 4.7.2 correctly (not run, no install allowed).
- Arch `godot` package contents (templates not bundled?).
- Exact export template folder name for 4.7.2 (`4.7.2.stable`).
- gamescope headless and wlroots headless with NVIDIA 5090 for Vulkan frames.
- FSR2/SSR Forward+-only wording in 4.7 docs (long-standing; not re-read).
- Built-in Jolt determinism setting; any Jolt-vs-GodotPhysics determinism comparison.
- Windows smoke test under Wine/Proton.
- Erodenn runtime on this machine (Wayland off-screen window, focus behaviour).
- GUT license field (API says none).

## Key source URLs
- https://github.com/Erodenn/godot-mcp-runtime , https://github.com/hi-godot/godot-ai , https://github.com/satelliteoflove/godot-mcp , https://github.com/Coding-Solo/godot-mcp , https://github.com/HaD0Yun/Doyunha-Gopeak , https://github.com/mrf/godot-stagehand
- https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- https://docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html
- https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/warning_system.html
- https://docs.godotengine.org/en/stable/tutorials/physics/using_jolt_physics.html
- https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_windows.html
- https://github.com/godotengine/godot/blob/4.7.2-stable/main/main.cpp (lines ~813, 1505) and servers/display/display_server_headless.h
- https://github.com/jdx/mise/blob/main/registry/godot.toml
- https://www.openredsoftware.com/blog/godot-screenshot-command-line
- https://github.com/chickensoft-games/setup-godot , https://github.com/abarichello/godot-ci , https://github.com/firebelley/godot-export
- https://github.com/godot-gdunit-labs/gdUnit4 , https://github.com/bitwes/Gut
- https://github.com/ValveSoftware/gamescope (src/main.cpp `--backend headless`)
- https://unity.com/features/ai , https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available
