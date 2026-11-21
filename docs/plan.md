# Orrery: project plan

Status: approved design, 2026-11-20. Codename and repo name: `orrery` (`seanGSISG/orrery`, private). The store title is chosen before any public release, because small games named "Orrery" already exist.

This file records every design decision and how the project is built, tested and delivered. The research behind it is in `docs/research/`. Where a research report and this plan differ, this plan wins.

## 1. Summary

- Orrery is an **original 3D marble platformer** in the genre of Marble Blast: roll, jump, collect gems, beat the clock, use power-ups. It has its own name, levels, art, music and look. It copies no level, asset, melody or code from any other game.
- It runs **natively on Linux and Windows**, plays fully with an **Xbox controller** (USB or Bluetooth) or keyboard and mouse, and is single-player.
- Content: **60 campaign levels** in 3 tiers, 3 secret levels and a hidden workshop level, plus two bonus modes: **Ascent** (a long climb from Earth to space with no checkpoints) and **Planetarium** (small planets with their own gravity on the arms of a giant orrery).
- Engine: **Godot 4.7.2**, strictly typed GDScript, and our own marble physics. Levels are **Blender 5.2.4 LTS Python scripts** that build into `.glb` files.
- Agents build, test, play and screenshot the game through a **built-in automation interface** (the *harness*) and a project MCP server. A *route bot* proves that each level can be finished under par.
- Delivery: milestones M0–M4. M1 contains 3 levels and the first 3 zones of Ascent. M2 (12 levels, all of Ascent) is the first full release.

## 2. Game design

### 2.1 Pillars

1. **Responsive marble feel.** The marble is a spinning sphere. Input sets a target spin; the marble does not get pushed like a box.
2. **Fast retries.** Hazards push the marble; they never kill it. Respawn takes under 2 seconds. Restart is one button.
3. **Readable levels.** The track stands out clearly against the sky. Each mechanic is taught on its own before levels combine mechanics.
4. **Layered goals.** Qualify (par time), gold time, a hidden Clockwork Egg in every level, ghosts of your best runs.
5. **Depth for experts.** Speedrun routes, shortcuts and skips are welcome when they take skill.

### 2.2 Modes

| Mode | Content | Unlock |
|---|---|---|
| Campaign | 60 levels: 20 Beginner, 20 Intermediate, 20 Advanced. Plus 3 secret levels and the workshop level | Beginner level 1 is open; the rest unlock by progression (2.3) |
| Ascent | One continuous climb in 8 zones from Earth to space (2.9) | Open from the start |
| Planetarium | 3 systems of 5 small planets each (2.10) | Clear the Beginner tier |

### 2.3 Core loop, scoring and progression

- A level runs: start pad → collect all gems → finish pad. The finish pad opens only when all gems are collected.
- Each level has a **par time** (beat it to qualify and unlock the next level) and a harder **gold time**.
- A tier unlocks when you qualify on the last level of the tier before it.
- Each level hides one **Clockwork Egg** off the main route (2.7).
- **Gold times** unlock cosmetic marble skins (8 in total).
- The level-select screen shows best time, medals and eggs per level.
- Local best times only. No online leaderboards in v1.
- **Ghosts:** the game records your best run of each level and can show it as a translucent marble while you play.

### 2.4 Controls and camera

| Action | Xbox controller | Keyboard + mouse |
|---|---|---|
| Roll (relative to the camera) | Left stick | W A S D |
| Camera | Right stick | Mouse |
| Jump | A | Space |
| Use power-up | X or RT | Left click |
| Restart | View | R |
| Pause | Menu | Esc |

- The controller works for everything: gameplay, menus, settings and rebinding.
- On-screen button icons follow the last input used (Xbox icons or keyboard icons). Hot-plugging works.
- Rumble on landings, bumpers and power-ups, with an on/off setting.
- Settings: stick dead zone, camera sensitivity, invert Y, full key and button rebinding.
- Camera: third-person orbit around the marble. It pulls in when a wall is in the way, follows the current "up" direction (for gravity changes and planets) and shakes on hard landings (setting to turn off).

### 2.5 Power-ups

The marble holds one power-up at a time and uses it with one button.

| Name | Effect | First milestone |
|---|---|---|
| Coil Spring | High jump | M1 |
| Mainspring | Speed burst in the camera's direction | M2 |
| Rubber Shell | Extra bouncy for 5 s | M2 |
| Damper | No bounce, landings stick, for 5 s | M2 |
| Ornithopter | Slow fall and strong air control for 5 s | M2 |
| Pocket Watch | The level clock stops for 5 s | M2 |
| Brass Weight | Marble is 2× size and 5× mass for 10 s; pushes through fans and bumpers | M3 |
| Rewind Gear | Puts the marble back where it was 3 s ago, with the speed it had then | M3 |
| Tether | Fires a magnetic line to a nearby brass ring so the marble can swing (Advanced tier) | M3 |

There is no charge-meter "blast" ability. Gravity changes come from objects in the world, not from a power-up.

### 2.6 Hazards and level objects

| Group | Objects | First milestone |
|---|---|---|
| Core | Start pad, finish pad, gems, checkpoints | M1 |
| Pushers | Bumper, Steam Vent, Pendulum | M1 |
| | Spark Mine | M2 |
| | Boiler Bomb, Cyclone, Electromagnet, Piston, Clock Hands | M3 |
| Floors | Trapdoor (drops, resets after 5 s), Crumbling Tiles | M1 |
| | Conveyor; surfaces: oil, glass-ice | M2 |
| | Surfaces: sand, rubber | M3 |
| Movers | Platforms on paths, turning gears | M1 |
| | Turntables | M3 |
| Travel | Cannon (fires the marble on an arc) | M2 |
| | Pneumatic Tube, Gravity Arrow (changes which way is down) | M3 |
| Environment (Ascent and Planetarium) | Wind gusts, low-gravity zones | M2 |
| | Point gravity (planets) | M3 |

Each object and power-up is introduced in a level that focuses on it, before any level combines it with others.

### 2.7 Clockwork Eggs and secrets

- Every campaign level hides one jewelled **Clockwork Egg** off the main route. When found, it opens and shows a tiny clockwork surprise.
- All eggs of a tier unlock that tier's **secret level** (3 in total).
- All 60 campaign eggs unlock the **glass marble** with a tiny orrery inside and the hidden **workshop level**.
- Ascent hides 10 eggs along the climb. Planetarium hides one egg per system.
- Untracked secrets: hidden rooms, a gear with a face, a marble-sized model of one level hidden inside another. `docs/secrets.md` lists every secret so agents keep them consistent.

### 2.8 Level design by tier

- **Beginner:** introduces the core mechanics and common objects, one focus per level. Wide tracks, gentle par times.
- **Intermediate:** combines mechanics. Moving platforms, narrow paths, optional shortcuts.
- **Advanced:** precision platforming, gravity puzzles, long multi-gem routes, tight par times that reward speedrun routes and skips.
- Level types across tiers: race tracks, open gem hunts, mazes and puzzles.
- Every level has a short design brief in `docs/levels/<level-id>.md`: intent, mechanic taught, route sketch, egg location, target par.

### 2.9 Ascent

- **Concept:** start in a clockmaker's town square on Earth at dawn. Climb through the pieces of a broken clock tower, rooftops and airships, the cloud sea, the sky-clockwork world, thin air with strong wind gusts, and finally space with low gravity and stars, where the Orrery's gate waits.
- **Structure:** one continuous, hand-designed climb in 8 zones, each zone its own level script. A first climb takes about 60 minutes; a skilled run takes about 10–12 minutes.
- **Light:** the time of day follows height, from dawn through day and sunset to the starfield.
- **Falls:** no checkpoints by default. A fall can drop the marble several zones. The game saves the exact spot on quit and continues from there. **Assist** adds a checkpoint at each zone start, and stats mark assisted runs.
- **Stats:** height meter on screen, a flag in the world at your best height, time to the top, falls, total meters fallen, a stats screen at the end, and a ghost of your best climb.
- **Objects:** no carried power-ups. Only objects built into the world (bumpers, steam vents, cannons, gears, wind, low gravity).
- **Loading:** start simple. Load all zones at the start and use Godot's visibility ranges for far geometry. Add zone streaming only if the memory or performance checks fail.
- **Milestones:** zones 1–3 (Earth town, broken clock tower, rooftops and airships) ship in M1 and end at a "to be continued" gate. Zones 4–8 ship in M2.

### 2.10 Planetarium

- A giant brass orrery turns in the sky. Each arm carries a small planet with its own point gravity. The marble can roll all the way around a planet, and the camera turns with it.
- The arms turn on a clock, and the planets line up from time to time. A jump at the right moment lets the next planet's gravity catch the marble. A miss drops it into the clouds.
- Goal per system: collect a star core on each planet, then dive into the sun. Gold time and an egg per system.
- 3 systems of 5 planets. Built after M2, ships with M3.

### 2.11 Art direction

- **Sky clockwork:** floating stone and brass architecture above a sea of clouds, warm golden-hour light, glass and gold details, realistic PBR materials.
- Each tier shifts the time of day: Beginner at dawn, Intermediate at noon, Advanced at dusk.
- The marble always casts a crisp blob shadow straight down, so the player can judge jumps.
- Geometry comes from Blender scripts (`bpy` and geometry nodes). Textures and skies come from CC0 libraries (Poly Haven, ambientCG), at 2K at most. 2D art (logo, UI icons, menu art) comes from the local ComfyUI.
- No paid AI 3D generators.
- **Look review:** before any final art, Sean approves a style board (ComfyUI concept images of the world, the M1 Ascent zones and the marble, plus 3 Blender test renders of a piece of track in final materials and lighting). The HUD and each menu get 3 distinct static mockups for Sean to pick from.

### 2.12 Audio and music

- **Style brief:** upbeat, groovy electronic music in the spirit of early-2000s arcade games (funky bass lines, bright synth leads, light trance pads), blended with modern hip-hop drums (boom-bap swing, half-time trap hi-hats, 808 bass). Orrery's signature sound is clockwork as instruments: clock ticks as hi-hats, music-box and celesta melodies, chimes, gear-ratchet percussion. Every track has a 4–8 bar hook that keeps coming back.
- **Tempo:** Beginner and Intermediate 85–100 BPM, Advanced up to 140 BPM, Ascent and Planetarium slower and more epic.
- **Loops:** 1:30–2:30, cut on bar lines. Much longer than the genre's old 30–70 second loops, to avoid repetition.
- **Track list:** 16 tracks: title theme, 3 Beginner, 3 Intermediate, 3 Advanced, 2 Planetarium, 3 Ascent (they change by zone, on bar lines), 1 credits song. Stingers: level complete, gold time, new record, egg found, big fall.
- **Vocals:** gameplay music is instrumental with short vocal chops. One full vocal theme song plays on the title screen and in the credits.
- **Rules:** no melody copied from any song. Prompts never name an artist or a song.
- **Production:** see 4.10. Sean picks every final track.
- **Sound effects:** synthesised (sfxr-style) and layered with CC0 samples. Agents check them; Sean does not need to review them.

### 2.13 Settings and defaults

- English only. All text goes through Godot's translation system so other languages can come later.
- No analytics, telemetry or network access in the game.
- Accessibility: gem and hazard colours that colourblind players can tell apart, plus shape cues; camera shake and motion blur toggles; a reduced-flashing setting.
- Saves and settings live in Godot's `user://` folder (standard per OS).
- Display: windowed, borderless or fullscreen; any resolution; ultrawide; frame-rate cap or uncapped; V-Sync toggle; high-refresh monitors.
- Graphics presets Low, Medium, High, Ultra (4.9).
- Steam Deck: no special work in v1.

## 3. Tech stack

| Part | Choice | Pin |
|---|---|---|
| Engine | Godot (official build via `mise`, `aqua:godotengine/godot`) | 4.7.2-stable. Move to 4.8 only when it is stable and our tests pass |
| Game language | GDScript with strict typing. Untyped declarations and unsafe calls are errors | — |
| Physics | Our own marble solver. Godot's collision system (Jolt, set explicitly) only finds contacts | — |
| Unit tests | GUT, vendored in `game/addons/gut/` | 9.7.1 |
| 3D tool | Blender, official blender.org build, not the Arch package | 5.2.4 LTS |
| Blender MCP | Official Blender Lab MCP (`projects.blender.org/lab/blender_mcp`), pinned commit. Fallback: `ahujasid/mcp-for-blender` with `DISABLE_TELEMETRY=true` | — |
| Project MCP | Orrery harness MCP (Python, `uv`, official MCP SDK) | — |
| Tool scripts | Python via `uv` (Ruff, ty). Blender scripts run in Blender's own Python | — |
| Task runner | `just` | — |
| Runtimes | `mise` (`mise.toml` pins Godot) | — |
| Binary assets | Git LFS | — |
| Test display | `gamescope --backend headless` (fallback: a small window on the KDE desktop) | — |
| CI | GitHub Actions on `ubuntu-latest` and `windows-latest`, `chickensoft-games/setup-godot@v2` | — |
| Music models | ACE-Step 1.5 XL (MIT), Stable Audio 3 Medium (Stability Community License) in the local ComfyUI | — |

No third-party Godot MCP. The harness MCP covers running the game, screenshots, input and game state; the Godot command line covers imports, exports and tests; agents edit scene files as text. If agents struggle with menu or UI scene work, add `hi-godot/godot-ai` then.

## 4. Architecture

### 4.1 Repo layout

```
orrery/
├── CLAUDE.md              agent rules and commands
├── justfile               every task (see 5.1)
├── mise.toml              pins Godot
├── .mcp.json              Blender MCP + Orrery harness MCP
├── .gitattributes         Git LFS patterns
├── .github/workflows/     CI
├── docs/
│   ├── plan.md            this file
│   ├── research/          research snapshots
│   ├── agents/            issue tracker, labels, domain-doc rules
│   ├── levels/            one design brief per level
│   ├── style/             approved style board and UI mockup choices
│   ├── secrets.md         every Easter egg and secret
│   └── licenses.md        source and license of every third-party asset and model
├── game/                  the Godot project
│   ├── project.godot
│   ├── addons/gut/
│   ├── core/              marble solver, camera, input, gravity fields, save data
│   ├── objects/           one folder per object or power-up (scene + script + test)
│   ├── modes/             campaign, ascent, planetarium
│   ├── ui/                menus and HUD
│   ├── audio/             buses, music players
│   ├── harness/           automation interface and route bot (left out of release exports)
│   ├── levels/built/      built .glb files (generated, ignored by git)
│   └── test/              GUT tests
├── levels/                level scripts, the source of truth
│   ├── beginner/  intermediate/  advanced/  secret/
│   ├── ascent/            zone_1.py … zone_8.py
│   └── planetarium/
├── kit/                   shared Blender library: track pieces, props, materials, marker helpers
├── assets/                Git LFS: textures/, audio/sfx/, audio/music/, ui/
├── tools/
│   ├── blender/           build_level.py, look-dev renders
│   ├── harness/           uv project: harness MCP server + CLI
│   ├── audio/             sfx synth, music pipeline, review page
│   └── pad/               virtual Xbox controller for tests
└── scripts/               one-off scripts
```

Never committed: `.blend` and `.glb` build outputs, `game/.godot/`, `build/`.

### 4.2 Marble physics

Every serious marble game writes its own marble physics (`docs/research/gameplay.md` §6). Orrery does too. The solver is our own code, written from the documented behaviour. No code comes from reference projects.

- **State:** position, linear velocity, angular velocity, radius, mass, current gravity vector, held power-up effects.
- **Tick:** Godot physics runs at 120 Hz. Each tick splits into sub-steps so that the marble moves at most half its radius per sub-step.
- **Contacts:** a sphere query against the level's collision shapes (`PhysicsDirectSpaceState3D.collide_shape` for contact points, `cast_motion` for the sweep). Static level geometry is a trimesh; moving objects are `AnimatableBody3D`, and the solver reads their velocity at the contact point. The contact normal comes from the marble centre to the closest point, which avoids catching on the inner edges between triangles.
- **Motion model:**
  - Input sets a target angular velocity around the axis perpendicular to the move direction and the surface normal. Spin approaches the target at the angular acceleration limit; with no input, braking pulls spin toward zero.
  - Friction at the contact couples spin and linear velocity: static friction, then kinetic friction when the contact slips. Each surface type scales the friction.
  - Impacts: above the minimum bounce speed, the marble bounces with the restitution value. Glancing impacts (below the slide angle) slide instead of bounce.
  - In the air, input gives a small direct acceleration (air control).
  - Gravity comes from the gravity field the marble is in: uniform direction (normal, Gravity Arrow, low-gravity zones) or toward a point (planets). "Up" is always the opposite of gravity, for the camera and for jumps.
- **Feel rules:** input never slows the marble below its current speed. Glancing hits slide. Hazards push, never kill. Falling out of the level respawns at the last checkpoint in under 2 seconds and the clock keeps running.
- **Starting numbers** (genre values; we tune them by feel):

| Value | Start |
|---|---|
| Marble radius | 0.2 m (all art is built to this scale) |
| Gravity | 20 m/s² |
| Top rolling speed from input | 15 m/s |
| Angular acceleration / braking | 75 / 30 rad/s² |
| Air acceleration | 5 m/s² |
| Jump impulse | 7.5 m/s along the contact normal |
| Friction static / kinetic / at bounce | 1.1 / 0.7 / 0.2 |
| Restitution | 0.5 |
| Slide threshold (dot of velocity and normal) | 0.5 |
| Minimum bounce speed | 0.1 m/s |

- All values live in one resource file, `game/core/marble_tuning.tres`, so agents tune them without code changes.
- If profiling shows the GDScript solver is too slow, move only its inner loop to a GDExtension. Do not do this before a profile shows the need.

### 4.3 Level pipeline

The level script is the source of truth. Blender and Godot files are build outputs.

1. **Kit:** `kit/` is a Python library for Blender. It builds track pieces, props and materials, and it places *markers*: Blender empties with a custom property `orrery` (a small dictionary such as `{"type": "gem"}`).
2. **Level script:** `levels/<tier>/<id>.py` calls the kit. It sets level data on the root (id, name, tier, par, gold, music track, sky preset) and places markers:
   - Gameplay objects: `gem`, `start`, `finish`, `checkpoint`, `egg`, each power-up, each hazard, with its settings (for example a platform's path and period).
   - `route`: ordered waypoints for the route bot, with actions (`jump`, `use`, `wait_until`).
   - `shot`: named camera views for the screenshot gallery (at least `overview`, `start`, `finish`, `egg`).
3. **Build:** `just build-levels` runs `blender -b --factory-startup --python-exit-code 1 --python tools/blender/build_level.py -- <script> <out.glb>` for each level, in parallel. The export keeps custom properties (`export_extras=True`). Collision meshes use Godot's import name hints (`-col`, `-colonly`, `-convcolonly`); surface type comes from a material custom property.
4. **Import:** a Godot post-import script reads the extras from each node's `extras` metadata and swaps every marker for the matching scene from `game/objects/`. Godot generates the lightmap UVs itself on import, so Blender does not author them.
5. **Checks:** `gltf-validator` on each `.glb`; a level lint that requires one start, one finish, at least one route, the required shots, an egg, and gems that the route reaches.

Hero props that are impractical to script may be `.blend` files in `kit/` (Git LFS). Every level stays a script.

### 4.4 Game runtime

- **Autoloads:** `Game` (mode and level flow), `Save` (progress, best times, ghosts, settings), `InputHub` (one input source at a time: player, route bot or harness), `Music`.
- **Input sources:** the marble reads a small `MarbleInput` value each tick (move vector, jump, use, camera yaw and pitch). The player, the route bot and the harness all produce it, so tests drive the exact path the player uses.
- **Objects:** each object is one scene with one typed script and its own GUT test.
- **Ghosts:** the marble's position and rotation, recorded 30 times a second. They play back the same on any PC because they do not re-simulate.

### 4.5 The harness (automation interface)

- Debug builds only. It lives in `game/harness/`, starts only with the `--harness-port=<port>` user argument, binds to `127.0.0.1` only, and the release export presets leave the folder out.
- Protocol: newline-delimited JSON-RPC 2.0 over TCP.
- Commands:
  - `ping`, `quit`
  - `load_level {id}` and `load_mode {mode, zone?}`
  - `state`: marble position, velocity, spin, on-ground, gems collected and total, timer, held power-up, last checkpoint, height (Ascent), level status, input device
  - `input {move, jump, use, camera, frames}`
  - `step {frames}`, `pause`, `resume`, `set_time_scale {scale}`
  - `teleport {position, velocity?}`
  - `screenshot {path, shot?}`: saves the real rendered frame, optionally from a named camera shot
  - `run_bot {route?}`: runs the route bot to the end and returns `{finished, time, falls, stuck_at?}`
  - `logs {since}`, `set_setting {key, value}`
- **Harness MCP** (`tools/harness/`): Python server that launches the game and wraps the socket. Tools: `game_launch {level?, mode?, display: headless|window, resolution}`, `game_state`, `game_input`, `game_step`, `game_screenshot` (returns the image), `game_run_bot`, `game_logs`, `game_quit`. The same package also has a CLI (`uv run orrery-harness …`) for `just` tasks and CI, so there is one implementation.
- Launch: `gamescope --backend headless -W 1920 -H 1080 -- godot --path game -- --harness-port=<port>`. Fallback: a small window on the KDE desktop.

### 4.6 The route bot

- Reads the level's `route` markers and steers the marble with the same `MarbleInput` as a player: it aims at the next waypoint from the marble's current position and speed, and it does each waypoint's action (jump, use power-up, wait until a platform arrives).
- Because it steers from the current state, small physics differences between runs or between Linux and Windows do not break it. Level tests do not need exact physics repeats.
- **Par and gold:** start as the bot's time × 1.5 (par) and × 1.15 (gold). A person tunes them after playing.
- From M3, a search program tries many input sequences per level to find unintended shortcuts. Agents fix the shortcuts or keep them as intended skips.

### 4.7 Rendering and performance

- Renderer: Forward+ (Vulkan).
- Campaign levels: baked `LightmapGI`, reflection probes, volumetric fog, SSR and SSAO on High and above, a dynamic sun shadow for moving objects.
- Ascent and Planetarium: dynamic sky and sun (time of day follows height in Ascent), SDFGI on Ultra only.
- Presets: **Low** (no GI or fog, lower shadow resolution), **Medium**, **High**, **Ultra** (4K-ready, SDFGI, full volumetrics).
- **Targets:** 1080p at 60 fps on a GTX 1660 / RX 5600-class GPU at Medium. Agents can't test that GPU directly, so the performance check fails when GPU frame time at Medium on the RTX 5090 goes over a budget (start at 3 ms; calibrate in M1 against a known-good scene). High-refresh monitors work.

### 4.8 Audio implementation

- Music files: OGG Vorbis with loop points, BPM and beat counts set in the import settings.
- `AudioStreamPlaylist` shuffles a tier's tracks. `AudioStreamInteractive` changes Ascent tracks by zone group on bar lines and handles title and menu transitions.
- Buses: Master, Music, SFX, UI, each with a volume setting.

### 4.9 Music production pipeline

1. **Backing tracks:** a script calls the local ComfyUI API with ACE-Step 1.5 XL and Stable Audio 3 workflows, using prompts built from the style brief (2.12). ACE-Step also sings the vocal theme song from original lyrics that agents write.
2. **Melody and clockwork layer:** agents write the hooks and clockwork percussion as MIDI from Python, render them through CC0 or free-licensed samples (FluidSynth with the GeneralUser GS soundfont, plus CC0 one-shots), and mix them over the backing track.
3. **Checks:** a script measures tempo, loudness (normalised to a set target with `ffmpeg loudnorm`) and the loop seam.
4. **Review:** agents make 3–5 candidates per track and build one review page. Sean listens and picks the keeper.
5. **Records:** `docs/licenses.md` lists the model, prompt and human-written layer for each track. A store release must disclose the AI-made music and 2D art (Steam requires this).

US copyright protects only the human-written parts of a track, which is why the melody layer is written by agents and reviewed by Sean rather than generated whole.

## 5. Testing and agent playtesting

### 5.1 Commands

| Command | What it does |
|---|---|
| `just setup` | Installs and checks every pinned tool (6.2). Safe to repeat |
| `just build-levels [id]` | Builds level scripts into `.glb` files |
| `just import` | `godot --headless --path game --import` |
| `just lint` | `gdlint` (gdtoolkit), Ruff, ty, shellcheck, level lint |
| `just test` | GUT unit tests, headless. Fails if zero tests ran |
| `just test-levels [id]` | Runs the route bot on each level, headless. Fails if the bot does not finish under par |
| `just gallery [id]` | Renders every level's camera shots into `build/gallery/index.html` |
| `just perf [id]` | Flies a fixed camera path through each level and checks GPU frame time |
| `just test-pad` | Plays a short sequence on a virtual Xbox controller and checks the game's response |
| `just export` | Builds Linux and Windows release exports into `build/` |
| `just smoke-wine` | Starts the Windows export under Wine, headless, and checks that it boots |
| `just run [level]` | Plays the game |
| `just ci` | Everything CI runs, locally |

### 5.2 Test layers

1. **Unit tests (GUT):** the marble solver (rolling, friction, bounce, slide, gravity fields), every object and power-up, scoring, progression, saves.
2. **Level tests:** every level builds, imports, passes the level lint, and the route bot finishes it under par. The bot needs physics, not rendering, so this runs headless on Linux and Windows.
3. **Screenshot gallery:** each level's named shots, rendered on the GPU in `gamescope`. Agents review the gallery with vision; Sean reviews it at each milestone. No pixel-exact image comparisons, because lighting noise and anti-aliasing make them fail at random.
4. **Performance check:** GPU frame time along a fixed camera path, against the budget in 4.7.
5. **Controller test:** `tools/pad/` creates a virtual Xbox controller through `/dev/uinput` (the same kernel path as a real controller). The test checks that Godot sees it, that A makes the marble jump and that the stick rolls it.
6. **Manual:** Sean plays each milestone with a real controller on Linux and on a real Windows PC.

Tests stay focused: one test per behaviour, no broad smoke tests, no tests kept for removed features.

### 5.3 CI (GitHub Actions)

- **`levels` job** (ubuntu): installs Blender 5.2.4 (cached), runs `just build-levels`, uploads the built files.
- **`test` job** (matrix: `ubuntu-latest`, `windows-latest`): Git LFS checkout (cached), `setup-godot@v2` with 4.7.2 and templates, downloads the built levels, runs import, GUT tests and the headless level tests.
- **`export` job:** Linux and Windows release exports as artifacts.
- GPU work (gallery, performance check) runs on Sean's machine only, because GitHub runners have no GPU.

## 6. Dev environment

### 6.1 Already done (pre-setup, 2026-11-20)

- Installed: `xpadneo-dkms` 0.10.5 (Xbox Bluetooth driver), `evtest`, `shellcheck`.
- Created the private repo `seanGSISG/orrery` with the five triage labels. The local branch is `main`; `origin` points to the repo. Nothing pushed yet.
- `scripts/presetup-wizard.sh` walks Sean through the Stable Audio 3 license, review-bot access, and the USB and Bluetooth controller checks.
- Already present: `uv`, `just`, `bun`, `node`, `gh` (scopes `repo`, `workflow`, `project`), `hf` (logged in), `gamescope` 3.17, `wine` 11.22, `ffmpeg`, `docker`. `sudo` needs no password.

### 6.2 M0 install steps (`just setup` automates them)

1. **System packages:** `sudo pacman -S --needed mise git-lfs`, then `git lfs install`.
2. **Godot:** `mise use godot@4.7.2` (writes `mise.toml`), then confirm `mise which godot` runs 4.7.2. Export templates: download `Godot_v4.7.2-stable_export_templates.tpz` from the GitHub release, check it against `SHA512-SUMS.txt`, unzip its `templates/` into `~/.local/share/godot/export_templates/4.7.2.stable/`.
3. **Blender 5.2.4 LTS:** download the official Linux tarball from `download.blender.org`, check its SHA-256, extract to `~/.local/opt/blender-5.2.4/`, link `~/.local/bin/blender-5.2`. `just setup` first tries `mise` (HTTP backend) and falls back to this script.
4. **Blender Lab MCP:** clone `https://projects.blender.org/lab/blender_mcp.git` at a pinned commit into `~/.local/share/orrery/blender_mcp/`, install its add-on into Blender 5.2.4 from the command line, and register it in `.mcp.json`.
5. **Godot add-ons:** vendor GUT 9.7.1 into `game/addons/gut/`.
6. **Python tools:** `uv sync` in `tools/harness/` (MCP SDK, `evdev` for the virtual controller). `gdtoolkit` runs through `uvx`.
7. **glTF tools:** Khronos `glTF-Validator` release binary into `~/.local/bin/`; `@gltf-transform/cli` through `bunx`.
8. **Music models:** download ACE-Step 1.5 XL and Stable Audio 3 Medium (plus its T5Gemma and Qwen text encoders) into the local ComfyUI with `hf download`, following the docs.comfy.org tutorials. Stable Audio 3 needs the license click from the wizard first.

`.mcp.json` (project scope):

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "${HOME}/.local/share/orrery/blender_mcp/mcp", "run", "blender-mcp"]
    },
    "orrery": {
      "command": "uv",
      "args": ["--directory", "tools/harness", "run", "orrery-harness-mcp"]
    }
  }
}
```

### 6.3 First-run checks (M0 exit gate)

Each check has a fallback, so a failure changes the plan, not the schedule.

| Check | Pass | Fallback |
|---|---|---|
| `mise` installs Godot 4.7.2 | `godot --version` prints 4.7.2.stable | Official zip pinned by the setup script |
| Blender EEVEE renders with no display | A cube renders to a non-black PNG under `blender -b` with `DISPLAY` and `WAYLAND_DISPLAY` unset | `xvfb-run`, or a window on the desktop |
| Blender Lab MCP | Runs code and returns a viewport screenshot | `ahujasid/mcp-for-blender` with telemetry off |
| `gamescope --backend headless` | Godot renders a non-blank screenshot through it on the RTX 5090 | A small window on the KDE desktop |
| Virtual Xbox controller | Godot lists it as a joypad and reads A | Test through the harness input path only |
| Windows export under Wine | Boots headless and exits cleanly | CI Windows runner only |
| CI | A minimal project passes on both runners | — |
| ComfyUI music workflows | One ACE-Step and one Stable Audio 3 sample render | ElevenLabs Music (paid) for backing tracks |

## 7. Workflow

- **Specs and branches:** each spec is one GitHub issue with one spec branch. M0 and M1 share the first spec and the branch `plan-1`; M2, M3 and M4 each get their own spec (`plan-2`, `plan-3`, `plan-4`) when they start. Each task is a ticket PR into its spec branch, reviewed by Argus. A spec branch merges into `main` as a spec PR, reviewed by Argus and Devin through the babysit flow.
- **Tracking:** GitHub Issues on `seanGSISG/orrery` (`docs/agents/issue-tracker.md`). `waypoint track` creates the project's card on Sean's Board in M0.
- **Phase 1 (core, M0–M1):** one agent works in order: tools, Godot project, marble physics, harness, level pipeline, controller support, menus and HUD, then the M1 levels and Ascent zones 1–3.
- **Phase 2 (content, M2 on):** parallel agents run as Orca workers, each in its own git worktree. File ownership:
  - Each level agent owns one level script and its brief (`levels/<tier>/<id>.py`, `docs/levels/<id>.md`).
  - One kit agent owns `kit/` and shared materials. Other agents request kit changes through it.
  - One agent owns each new object or power-up (`game/objects/<name>/`).
  - The core agent owns `game/core/` and `game/harness/`.
- **Review gate:** a review agent checks each level's gallery, route-bot result and performance before merge.
- **Models:** Fable 5.2 for orchestration, the marble solver and complex reviews; Opus 5.5 for ordinary implementation; Sonnet 5.5 for well-specified tasks such as level scripts from a brief; Haiku 5.5 for search and bulk extraction.

## 8. Milestones

| Milestone | Contents | Exit criteria |
|---|---|---|
| **M0 Setup** | Install the tools (6.2); first-run checks (6.3); Godot project skeleton with strict typing; `justfile`; CI on both runners; `.mcp.json`; `waypoint` card; style board and UI mockups approved | Every check in 6.3 passes or has its fallback in place. CI green. Sean has approved the style board and picked the HUD and menu mockups |
| **M1** | Marble solver and tuning; camera; input (keyboard, mouse, Xbox controller, button icons, rumble); harness and harness MCP; route bot; level pipeline and kit v1; objects: core set and the Clockwork Egg, Bumper, Steam Vent, Pendulum, Trapdoor, Crumbling Tiles, moving platforms, turning gears; Coil Spring; HUD; menus; saves; ghosts; 3 Beginner levels; Ascent zones 1–3; title theme, 1 Beginner track, 1 Ascent track; first sound effects | All tests pass on Linux and Windows. The route bot finishes all 3 levels and Ascent zones 1–3. Sean has played it with a real controller on Linux and Windows |
| **M2** (first full release) | 12 levels (4 per tier); Ascent zones 4–8; M2 power-ups and objects (2.5, 2.6); about 8 music tracks; zip builds on a private GitHub Release | As M1, for all content. Gallery reviewed by Sean |
| **M3** | 36 levels (12 per tier); Planetarium; the remaining power-ups and objects; shortcut search | As M2. Shortcut search reports reviewed |
| **M4** | 60 levels (20 per tier); 3 secret levels and the workshop level; the 8 marble skins and the glass marble; full soundtrack with stingers and the vocal theme; final store title | As M2, plus a full playthrough by Sean |

## 9. Risks

| Risk | Mitigation |
|---|---|
| The GDScript solver is too slow | Profile in M1; move only the inner loop to a GDExtension if needed |
| Marble feel is wrong | One tuning file; feel review by Sean early in M1, before levels are built on it |
| 60 levels become filler | A brief per level; each level must have a clear intent; gallery and play reviews per milestone |
| `gamescope` headless fails on NVIDIA | Windowed fallback on the KDE desktop |
| AI music quality is low | Many candidates per track; Sean picks; the option to hire a composer for the title theme stays open |
| Git LFS quota on GitHub | Textures at 2K or less; cache LFS objects in CI |
| Name conflict with existing "Orrery" games | `orrery` stays the codename; the store title is chosen before any public release |

## 10. Things only Sean does

- Run `scripts/presetup-wizard.sh`: the Stable Audio 3 license, review-bot access, the controller over USB and Bluetooth.
- Approve the style board; pick the HUD and menu mockups.
- Feel-review the marble physics early in M1.
- Pick the final music tracks.
- Play each milestone with a real controller on Linux and on a real Windows PC.
- Choose the store title before any public release.
