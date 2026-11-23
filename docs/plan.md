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
| Movers | Platforms on paths, turning gears, turning arms | M1 |
| | Turntables | M3 |
| Travel | Cannon (fires the marble on an arc) | M2 |
| | Pneumatic Tube, Gravity Arrow (changes which way is down) | M3 |
| Environment (Ascent and Planetarium) | Wind gusts, low-gravity zones | M2 |
| | Point gravity (planets) | M3 |

Each object and power-up is introduced in a level that focuses on it, before any level combines it with others.

The turning arm (`turning_arm`, a flat bar that turns round its marker's axis and pushes the marble) came into M1 for the turning clock hands of Ascent 2 (#32). It is the base of the M3 Clock Hands.

Two markers have no gameplay of their own. A `land` marker (`game/objects/land/`) gives an Ascent town open country out to the horizon; the marble that touches it is out of bounds. A `room_probe` marker (`game/objects/room_probe/`) gives an indoor room its own warm ambient light and reflections.

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
- **Falls:** no checkpoints by default. A fall can drop the marble several zones. The game saves the exact spot on quit and continues from there. **Assist** adds a checkpoint at each zone start, and the stats mark an assisted climb. An assisted climb never replaces a record: it saves no best time, no ghost and no best height (Sean, 2026-11-21).
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

- **Sky clockwork:** stone and brass clockwork architecture in a warm golden-hour light, with glass and gold details and realistic PBR materials.
- **Sky by height** (Sean, 2026-11-20). The sky of a tier shows how high its levels are:
  - Beginner: dawn. The levels stand on the Earth. The clockwork theme lives in the architecture. No planets.
  - Intermediate: noon, in the high sky about 16 km up. No planet.
  - Advanced: dusk at the edge of space, about 80 km up. Faint stars and one restrained planet.
  - Ascent: zones 1 to 3 are on the Earth only. Time of day follows height (2.9).
- **Style board** (Sean, 2026-11-21; ticket #5; `docs/style/README.md`):
  - Material and light set A: honey limestone, aged brass, golden dawn.
  - Marble A is the default: clear glass with a turning brass orrery core. Marble B (blue stone, gold inlay) becomes an unlockable skin later.
  - Gems are 0.5 m wide and float 0.3 m above the floor. Each colour has its own cut. A faint beam shows each gem across the level.
- **HUD and menus** (Sean, 2026-11-21; ticket #6; `docs/ui-mockups/README.md`): direction B (glass and light) for the in-level HUD and the Ascent HUD; direction C (orrery chart) for the title, level select, pause, settings and results screens. The HUD takes the coral accent and the numerals of C.
- The marble always casts a crisp blob shadow straight down, so the player can judge jumps.
- Geometry comes from Blender scripts (`bpy` and geometry nodes). Base tiling materials start from CC0 libraries (Poly Haven, ambientCG). The tier skies are our own Cycles renders (`just bake-skies`) of CC0 HDRIs or Blender's sky model. Textures are 2K by default, with a short list of 4K exceptions (`docs/design/visual-quality.md` §6). 2D art (logo, menu art) comes from the local ComfyUI or from GPT-Image.
- **AI art** (Sean, 2026-11-21): AI art is allowed where it looks better than a CC0 or scripted piece. GPT-Image makes decals, signage and concept images. Tripo makes decorative props from an image. Both run through `tools/art` (4.3). Every AI asset gets a row in `docs/licenses.md`. Prompts never name games, brands, characters or living artists (`docs/research/asset-prompting.md`).
- **Look review:** before any final art, Sean approves a style board (ComfyUI concept images of the world, the M1 Ascent zones and the marble, plus 3 Blender test renders of a piece of track in final materials and lighting). The HUD and each menu get 3 distinct static mockups for Sean to pick from. Both are done (2026-11-21): see above, `docs/style/README.md` and `docs/ui-mockups/README.md`.

### 2.12 Audio and music

- **Style brief:** upbeat, groovy electronic music in the spirit of early-2000s arcade games (funky bass lines, bright synth leads, light trance pads), blended with modern hip-hop drums (boom-bap swing, half-time trap hi-hats, 808 bass). Orrery's signature sound is clockwork as instruments: clock ticks as hi-hats, music-box and celesta melodies, chimes, gear-ratchet percussion. Every track has a 4–8 bar hook that keeps coming back.
- **Tempo:** Beginner and Intermediate 85–100 BPM, Advanced up to 140 BPM, Ascent and Planetarium slower and more epic.
- **Loops:** 1:30–2:30, cut on bar lines. Much longer than the genre's old 30–70 second loops, to avoid repetition.
- **Track list:** 16 tracks: title theme, 3 Beginner, 3 Intermediate, 3 Advanced, 2 Planetarium, 3 Ascent (they change by zone, on bar lines), 1 credits song. Stingers: level complete, gold time, new record, egg found, big fall.
- **Vocals:** gameplay music is instrumental with short vocal chops. One full vocal theme song plays on the title screen and in the credits.
- **Rules:** no melody copied from any song. Prompts never name an artist or a song.
- **Production:** see 4.9. Sean picks every final track.
- **Picked so far** (M1): the title theme "Wind-up", the Beginner track "Roll call" and the first Ascent track "Spiral stair". Each is an ACE-Step 1.5 XL instrumental bed with our own hook and clockwork layer on top (`docs/research/music.md`; the pipeline and its README are in `tools/audio/music/`, ticket #26, PR #67).
- **Sound effects:** synthesised (sfxr-style) and layered with CC0 samples. Agents check them; Sean does not need to review them.

### 2.13 Settings and defaults

- English only. All text goes through Godot's translation system so other languages can come later.
- No analytics, telemetry or network access in the game.
- Accessibility: gem and hazard colours that colourblind players can tell apart (the colourblind palette), plus shape cues (each gem colour has its own cut); a camera shake toggle. A motion blur toggle and a reduced-flashing option are deferred: M1 has neither (#23, 2026-11-20). Add the reduced-flashing option with the first effect that flashes (for example the Spark Mine, M2).
- Saves and settings live in Godot's `user://` folder (standard per OS).
- Display: windowed, borderless or fullscreen; any resolution; ultrawide; frame-rate cap or uncapped; V-Sync toggle; HDR output where the display supports it; high-refresh monitors.
- Graphics presets Low, Medium, High, Ultra (4.7).
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
| Art models | GPT-Image-2.6 (2D art) and Tripo (decorative 3D props), through `tools/art` | — |

No third-party Godot MCP. The harness MCP covers running the game, screenshots, input and game state; the Godot command line covers imports, exports and tests; agents edit scene files as text. If agents struggle with menu or UI scene work, add `hi-godot/godot-ai` then.

## 4. Architecture

### 4.1 Repo layout

```
orrery/
├── README.md              the front page for players (media in docs/media/)
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
│   ├── style/             approved style board
│   ├── ui-mockups/        approved HUD and menu mockups
│   ├── design/            runtime, audio and visual quality designs
│   ├── media/             README screenshots and clips (not in Git LFS)
│   ├── secrets.md         every Easter egg and secret
│   └── licenses.md        source and license of every third-party asset and model
├── game/                  the Godot project
│   ├── project.godot
│   ├── addons/            gut, lightmap_baker (the bake plugin, 4.7)
│   ├── core/              marble solver, camera, input, gravity fields, save data, ghosts
│   ├── objects/           one folder per object or power-up (scene + script)
│   ├── modes/             ascent (campaign and planetarium come later)
│   ├── ui/                menus and HUD
│   ├── audio/             buses, music players, sound effects
│   ├── debug/             feel-review course support and the live tuning overlay
│   ├── settings/          graphics presets
│   ├── skies/             sky presets and their baked skies
│   ├── materials/         kit materials and the kit surface shader
│   ├── harness/           automation interface and route bot (left out of release exports)
│   ├── levels/built/      built .glb files (generated, ignored by git)
│   └── test/              GUT tests; object tests in test/objects/<type>/
├── levels/                level scripts, the source of truth
│   ├── beginner/  intermediate/  advanced/  secret/
│   ├── ascent/            zone_1.py … zone_8.py
│   └── planetarium/
├── kit/                   shared Blender library: track pieces, props, materials, marker helpers
├── assets/                Git LFS: textures/, decals/, props/ (the sounds and the music are in game/audio/)
├── tools/
│   ├── blender/           build_level.py, look-dev renders
│   ├── harness/           uv project: harness MCP server + CLI
│   ├── art/               GPT-Image and Tripo art tools (4.3)
│   ├── audio/             sfx synth, music pipeline, review page
│   ├── gallery/           screenshot gallery
│   ├── perf/              GPU frame-time check
│   ├── setup/             install and first-run checks
│   └── pad/               virtual Xbox controller for tests
└── scripts/               one-off scripts
```

Never committed: `.blend` and `.glb` build outputs, `game/.godot/`, `build/`. The exception is `game/objects/egg/egg.glb`: `just build-egg` writes it, and it is committed, like the baked skies.

Object tests live in `game/test/objects/<type>/`, not beside the object: the release exports leave out only `test/*`, and GUT scans only `res://test/`. The runtime design is in `docs/design/core-runtime.md`.

### 4.2 Marble physics

Every serious marble game writes its own marble physics (`docs/research/gameplay.md` §6). Orrery does too. The solver is our own code, written from the documented behaviour. No code comes from reference projects.

- **State:** position, linear velocity, angular velocity, radius, mass, current gravity vector, held power-up effects.
- **Tick:** Godot physics runs at 120 Hz. Each tick splits into sub-steps so that the marble moves at most half its radius per sub-step.
- **Contacts:** a sphere query against the level's collision shapes (`PhysicsDirectSpaceState3D.collide_shape` for contact points, `cast_motion` for the sweep). Static level geometry is a trimesh. Every collider is a `Solid` (a `StaticBody3D`). A moving object moves its `Solid` from code each tick with `Solid.move()`, which sets the physics transform at once and records the surface velocity; the solver reads that velocity at the contact point. Movers are not `AnimatableBody3D`: its transform reaches shape queries only at the next physics frame, and `LevelRun.step()` runs ticks outside physics frames (`docs/design/core-runtime.md` §1 and §2). The contact normal comes from the marble centre to the closest point, which avoids catching on the inner edges between triangles.
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
   - `route`: ordered waypoints for the route bot, with actions (`jump`, `use`, `wait`, `wait_until`, `speed`), in the kind `first_run` or `expert` (4.6).
   - `shot`: named camera views for the screenshot gallery (at least `overview`, `start`, `finish`, `egg`).
3. **Build:** `just build-levels` runs `blender -b --factory-startup --python-exit-code 1 --python tools/blender/build_level.py -- <script> <out.glb>` for each level, in parallel. The export keeps custom properties (`export_extras=True`). Collision meshes use Godot's import name hints (`-col`, `-colonly`, `-convcolonly`); surface type comes from a material custom property. A mesh named `<name>-far` is far scenery: it is drawn, but it has no collision, no lightmap, no probe and no shadow.
4. **Import:** a Godot post-import script reads the extras from each node's `extras` metadata and swaps every marker for the matching scene from `game/objects/`. A setting that is a `Material` takes the name of a kit material (an unknown name fails the import). Godot generates the lightmap UVs itself on import, so Blender does not author them.
5. **Checks:** `gltf-validator` on each `.glb`. A level lint in the importer (`game/levels/level_converter.gd`) requires exactly one `level`, one `start` and one `finish` marker, the four gallery shots (`overview`, `start`, `finish`, `egg`), and a `first_run` route (at most one route of each kind). Levels in `levels/test/` skip the shots and the route. The route bot fails a route that does not reach every gem (4.6). No check for the egg exists yet.

Hero props that are impractical to script may be `.blend` files in `kit/` (Git LFS). Every level stays a script.

**Generated art and props.** `tools/art/` makes 2D art with GPT-Image-2.6 (Flare drafts, Sunburst finals) and decorative 3D props with Tripo (concept image, views, P1 geometry, a separate de-lit texture), with a dry run, spend caps and budgets, and a recipe for each file. `just prop-cleanup` turns a generated model into `assets/props/<name>.glb` (Git LFS), and a level script places it with `kit.prop(name, at=..., rotation=..., collider="none"|"box"|"cylinder")`. A prop is decoration: only its optional box or cylinder collides, and the marble rolls only on kit pieces. See `tools/art/README.md` and `docs/research/asset-prompting.md`.

### 4.4 Game runtime

- **Autoloads:** `Game` (mode and level flow), `Save` (progress, best times, ghosts, settings), `InputHub` (one input source at a time: player, route bot or harness), `Graphics` (the graphics preset), `Music`.
- **Settings:** `Save.settings` (`Settings`, a `SaveRecord`) holds every player setting. `Save.change_settings({key: value})` sets them, calls `Settings.apply()` and writes the save file; the settings menu and the harness `set_setting` use it. `Settings.apply()` puts each value into the game: the camera, rumble, input, graphics preset, bus volumes, display, `Palette` (the standard or colourblind colours) and `Bindings` (the player's buttons in the input map). The save file has a format version (2) and `read()` migrates an older file (`docs/design/core-runtime.md` §4).
- **Input sources:** the marble reads a small `MarbleInput` value each tick (move vector, jump, use, camera yaw and pitch). The player, the route bot and the harness all produce it, so tests drive the exact path the player uses.
- **Objects:** each object is one scene with one typed script and its own GUT test.
- **Ghosts:** the marble's position and rotation, recorded 30 times a second of level clock by the `RunTracker` that `Save` adds to each run. `RunTracker` follows the signal `LevelRun.stepped`, which `step()` emits at the end of every tick (`docs/design/core-runtime.md` §4). They play back the same on any PC because they do not re-simulate.

### 4.5 The harness (automation interface)

- Debug builds only. It lives in `game/harness/`, starts only with the `--harness-port=<port>` user argument, binds to `127.0.0.1` only, and the release export presets leave the folder out.
- Protocol: newline-delimited JSON-RPC 2.0 over TCP.
- Commands (`game/harness/harness.gd`):
  - `ping`, `quit`
  - `load_level {id}`. `load_mode {mode, zones?, zone?, resume?, assist?}` starts a mode; `ascent` is the only mode. It starts a new climb, or continues the saved spot when `resume` is true. `zones` are the zone level ids from the bottom, `zone` (1 is the first) puts the marble on the start pad of that zone, and `assist` sets Assist first. Until a zone is built, it climbs the fixture zones (`docs/design/ascent.md`).
  - `state`: the `GameState` as JSON (`docs/design/core-runtime.md` §6): marble position, velocity, spin, up, on-ground, gems collected and total, timer, medal, held power-up, last checkpoint, egg found, height (Ascent), level status, input device
  - `input {move, jump, use, camera, frames}`: `camera` is `[yaw, pitch]`; with no `frames` the input holds until the next `input`
  - `step {frames}`: runs the ticks (120 per second) at once, at most 36000 per request, and pauses. `pause`, `resume`, `set_time_scale {scale}` (ticks per physics frame, 0 to 64)
  - `teleport {position, velocity?}`
  - `screenshot {path?, shot?}`: saves the real rendered frame, optionally from a named camera shot. It returns `{path, width, height, blank, adapter}`. It fails with `NO_FRAME` under `godot --headless`, which renders nothing. With a `shot`, the harness first draws 30 frames from that camera, so the image has settled when it saves.
  - `run_bot {route?}`: restarts the level, plays a route to the end at full speed, pauses, and returns `{finished, time, falls}` (plus `{stuck_at, waypoint, reason}` when the bot gave up). `route` is `first_run` (default), `expert` or a route node name.
  - `logs {since}`
  - `set_setting {key, value}`: a key of `Settings` (such as `graphics_preset`) goes through `Save.change_settings()`, as the settings menu does: it applies the value and writes the save file. It returns the error `NOT_SAVED` when the value changed but the file could not be written. Any other key sets the project setting of that name. An unknown key gives `NOT_FOUND`.
- **Harness MCP** (`tools/harness/`): Python server that launches the game and wraps the socket. Tools: `game_launch {level = "flat", display = headless|window|none, width = 1920, height = 1080}`, `game_state`, `game_input {move, jump, use, camera, frames}`, `game_step {frames}`, `game_screenshot {shot?}` (returns the image), `game_run_bot {route?}`, `game_load_mode {mode = ascent, zone?, zones?, resume?, assist?}`, `game_logs {since}`, `game_quit`. `display` is `headless` (gamescope, no window; falls back to `window`), `window` (a desktop window) or `none` (`godot --headless`: no frames, no screenshots; CI uses it). `game_launch` has no `mode` parameter: start a mode with `game_load_mode` after the launch. The same package has a CLI (`uv run orrery-harness …`, or `just harness …`) with one subcommand for every harness command, so there is one implementation. `teleport`, `pause`, `resume`, `set_time_scale`, `load_level` and `set_setting` are in the CLI only. See `tools/harness/README.md`.
- **Session isolation:** each launch gets its own empty `user://` folder, `build/harness/user-<port>-<random>/` (set through `XDG_DATA_HOME`). The folder is deleted when the session ends, so a harness session never reads or writes the player's saves and ghosts. Every automated launch (harness, gallery, perf, bake) is silent (`--audio-driver Dummy`). `just run` and `just feel` keep the sound.
- Launch (`display = headless`): `gamescope --backend headless -W <width> -H <height> -- godot --path game --resolution <width>x<height> -- --harness-port=<port> [--level <id>]`. Fallback: a window on the KDE desktop.

### 4.6 The route bot

Built in #14 (`game/harness/route_bot.gd`, `game/objects/route/route.gd`).

- Reads the level's `route` markers and steers the marble with the same `MarbleInput` as a player: it aims at the next waypoint from the marble's current position and speed, and it does each waypoint's action.
- Because it steers from the current state, small physics differences between runs or between Linux and Windows do not break it. Level tests do not need exact physics repeats.
- **Route markers:** a level script places one `route` marker of kind `first_run` (the line of a player on a first run) and one of kind `expert` (the fastest line). `kit.marker("route", at=…, name=…, kind="first_run", points=[…], actions="…")`. The `points` are positions on the floor, in order. Put a point on each gem and on the finish pad.
- **Action syntax:** `actions` is a text of entries `<point> <action> [values]`, separated by `;`. `<point>` is the 0-based index in `points`.
  - `jump`: jump at the point. `use`: use the held power-up at the point.
  - `wait <s>`: stop and wait s seconds.
  - `wait_until <object> <from> <to>`: stop and wait until the cycle time of the named mover is in [from, to).
  - `speed <m/s>`: the top speed on the way to the point.
  - At one point the bot first waits, then uses, then jumps.
- **In a climb:** the bot comes to rest on the last point of its route and stays there until the run finishes. A test can give one bot to each zone in turn: the next bot starts from a still marble, and each bot counts its 300 s from its own first input (`docs/design/ascent.md` §8).
- **Result:** `{finished, time, falls}`. The bot gives up with `reason` `stuck`, `fell` (3 falls), `route_end` (the last point is reached but the run did not finish: a gem is missing) or `timeout` (300 s after its first input).
- **`just test-levels [id]`:** runs both routes of each built level, headless, in-process (so it runs on Windows too). The `first_run` route must finish under par and the `expert` route under gold, with no fall. With no ids it tests every built level and fails when none has a route.
- **`just suggest-times <id>`:** prints the times from the bot's run: par = `first_run` time × 1.5 and gold = `expert` time × 1.15, rounded up to 0.1 s. A person tunes them after playing.
- From M3, a search program tries many input sequences per level to find unintended shortcuts. Agents fix the shortcuts or keep them as intended skips.

### 4.7 Rendering and performance

- Renderer: Forward+ (Vulkan).
- Campaign levels: baked `LightmapGI`, reflection probes, volumetric fog, SSR and SSAO on High and above, a dynamic sun shadow for moving objects.
- Ascent and Planetarium: dynamic sky and sun (time of day follows height in Ascent), SDFGI on Ultra only.
- **Lightmap bake** (#24): the importer gives every level one `LightmapGI` with the bake settings of `docs/design/visual-quality.md` §4. `just bake <id>` bakes it on the GPU in a hidden gamescope display and writes `game/levels/lightmaps/<id>.lmbake` (Git LFS). Godot 4.7.2 does not expose `LightmapGI.bake()` to scripts, so the add-on `game/addons/lightmap_baker/` calls the bound `_bake` method of the built-in `LightmapGIEditorPlugin`. That is an internal call; see the risk in 9.
- Presets: **Low** (no GI or fog, lower shadow resolution), **Medium**, **High**, **Ultra** (4K-ready, SDFGI, full volumetrics).
- **Targets:** 1080p at 60 fps on a GTX 1660 / RX 5600-class GPU at Medium. Agents can't test that GPU directly, so the performance check fails when GPU frame time at Medium on the RTX 5090 goes over a budget (start at 3 ms; calibrate in M1 against a known-good scene). High-refresh monitors work.
- **Measured (#20, RTX 5090, idle GPU, `just perf fixture` with the stand-in light rig):** GPU mean/p99 ms Low 0.10/0.13, Medium 0.21/0.24, High 0.56/0.61, Ultra 0.84/0.96 at 1080p; High 1440p 0.82/0.90; Ultra 4K 2.7/3.3. VRAM Medium 222 MB, Ultra 4K 1.7 GB. The fixture is too small to calibrate the 3 ms budget, so it stays until the first real level (M1).
- **Visual quality bar:** `docs/design/visual-quality.md` turns "crisp and photorealistic" into checks. It holds the preset table, the anti-aliasing choice, the lightmap bake settings, the glass-marble approach, the texture policy (2K default with a short list of 4K exceptions, which replaces the 2K cap in 2.11 and 9), the material rules, the gallery review rubric and what `just perf` measures per preset. Every art and rendering ticket meets it.

### 4.8 Audio implementation

Built in #25. `docs/design/audio.md` is the design: the buses, the volume settings, the music groups, the zone changes, the sound table and how to add a track.

- Music files: OGG Vorbis with loop points, BPM and beat counts set in the import settings. The music `.ogg` files are in Git LFS (`game/audio/music/**/*.ogg`); the small sound effects are not.
- The autoload `Music` plays one *group* of tracks (a folder `game/audio/music/<group>/`). A normal group is an `AudioStreamPlaylist` (shuffled, looped, 2 s fade between tracks). The group `ascent` is one `AudioStreamInteractive`: `Music.set_zone(zone)` changes the clip on the next bar line. The level's `music` field picks the group, then the tier, and the title and menus play `title`.
- Buses: Master (with a hard limiter), Music, SFX, UI, each with a volume setting in `Save.settings`.
- Sound effects: `SfxPlayer` plays one sound per `LevelRun.feedback` kind. The sounds come from `tools/audio/sfx/synth_sfx.py`.

### 4.9 Music production pipeline

1. **Backing tracks:** a script calls the local ComfyUI API with ACE-Step 1.5 XL and Stable Audio 3 workflows, using prompts built from the style brief (2.12). ACE-Step also sings the vocal theme song from original lyrics that agents write.
2. **Melody and clockwork layer:** agents write the hooks and clockwork percussion as MIDI from Python, render them through CC0 or free-licensed samples (FluidSynth with the GeneralUser GS soundfont, plus CC0 one-shots), and mix them over the backing track.
3. **Checks:** a script measures tempo, loudness (normalised to a set target with `ffmpeg loudnorm`) and the loop seam.
4. **Review:** agents make 3–5 candidates per track and build one review page. Sean listens and picks the keeper.
5. **Records:** `docs/licenses.md` lists the model, prompt and human-written layer for each track. A store release must disclose the AI-made music and 2D art (Steam requires this).

US copyright protects only the human-written parts of a track, which is why the melody layer is written by agents and reviewed by Sean rather than generated whole.

## 5. Testing and agent playtesting

### 5.1 Commands

`just --list` is the source of truth. CI runs these tasks too.

| Command | What it does |
|---|---|
| `just setup` | Installs and checks every pinned tool (6.2). Safe to repeat |
| `just check-env` | Runs the first-run checks (6.3) only |
| `just blender` / `just blender-agent` | Opens Blender 5.2 with the MCP bridge on `localhost:9876`: in a window, or hidden in gamescope |
| `just import` | `godot --headless --path game --import` |
| `just build-levels [id…]` | Builds level scripts into `game/levels/built/*.glb` and checks that they import |
| `just lint` | `just lint-game` (`gdlint` from gdtoolkit, and a Godot compile check of every game script) and `just lint-scripts` (Ruff check and format, ty, shellcheck; no Godot). Tool versions come from `tools/setup/pins.env`. The level lint runs in the importer, in `just build-levels` |
| `just test` | GUT unit tests, headless. Fails if a test fails, a test script does not load, or zero tests ran. It runs with an empty `user://` that it deletes, so tests never touch the player's save (#73) |
| `just test-levels [id…]` | Runs the route bot on each built level, headless (4.6). Fails if `first_run` is not under par or `expert` not under gold. Like `just test`, it uses an empty `user://` (#73) |
| `just suggest-times <id>` | Prints par and gold from the route bot's times (4.6) |
| `just harness …` | Drives a debug build through the harness CLI (4.5) |
| `just test-harness [-m gpu]` | Harness contract tests on a headless debug build. `-m gpu` adds the GPU screenshot test |
| `just gallery [id…]` | Renders every level's camera shots on High into `build/gallery/index.html`. Fails on a shader compile error |
| `just perf [id…]` | Flies a fixed camera path through each level per graphics preset and checks GPU frame time and VRAM. It waits for a quiet GPU and repeats a disturbed run (`docs/design/visual-quality.md` §8). Fails on a shader compile error |
| `just test-perf` | The tests of the perf tool (no Godot) |
| `just bake [id…]` | Bakes the lightmaps of levels on this GPU (4.7). Close every Godot editor on the project first |
| `just test-pad` | Plays a short sequence on a virtual Xbox controller and checks the game's response (local only) |
| `just ui-shots` | Saves a screenshot of each HUD and menu screen at 1080p and 4K into `build/ui/<height>/`. Fails on a shader compile error |
| `just build-sfx [--montage PATH]` | Synthesises the sound effects and the test music loops, and checks them. `--montage` also joins the sounds into one OGG |
| `just art …` / `just model …` / `just prop-cleanup <source> <name>` | GPT-Image art and Tripo props through `tools/art`; paid calls need `--yes`, `--dry-run` sends nothing. `prop-cleanup` turns a generated model into `assets/props/<name>.glb` (4.3) |
| `just render-prop <name>` | Renders the review sheet of `assets/props/<name>.glb` into `build/props/<name>.png`: four views of the prop beside the marble and the kit materials (headless Cycles on the CPU) |
| `just test-music` / `just test-art` | The tests of the music pipeline and of the asset tools (mocked APIs, no paid call) |
| `just bake-skies [name…]` | Bakes the tier skies into `game/skies/<name>.hdr` with Cycles on this GPU |
| `just build-marble` / `just build-egg` | Builds the marble's brass core (`game/core/marble/built/`, ignored by git) and the Clockwork Egg (`game/objects/egg/egg.glb`, committed) from `tools/blender/` |
| `just feel` | Builds the feel-review course and plays it in a window with the tuning overlay (`docs/feel-review.md`) |
| `just run [level]` | Plays a level in a window (default: `flat`) |
| `just export` | Builds Linux and Windows release exports into `build/` |
| `just export-debug` | Builds the Linux debug export (harness and test levels included) |
| `just smoke-wine` | Exports, starts the Windows export under Wine, headless, and checks its boot marker |

There is no `just ci` task. CI runs the tasks in 5.3 as separate jobs.

### 5.2 Test layers

1. **Unit tests (GUT):** the marble solver (rolling, friction, bounce, slide, gravity fields), every object and power-up, scoring, progression, saves.
2. **Level tests:** every level builds, imports, passes the level lint, and the route bot finishes both routes: `first_run` under par and `expert` under gold. The bot needs physics, not rendering, so this runs headless on Linux and Windows.
3. **Screenshot gallery:** each level's named shots, rendered on the GPU in `gamescope`. Agents review the gallery with vision; Sean reviews it at each milestone. No pixel-exact image comparisons, because lighting noise and anti-aliasing make them fail at random.
4. **Performance check:** GPU frame time along a fixed camera path, against the budget in 4.7.
5. **Controller test:** `tools/pad/` creates a virtual Xbox controller through `/dev/uinput` (the same kernel path as a real controller). The test checks that Godot sees it, that A makes the marble jump and that the stick rolls it.
6. **Manual:** Sean plays each milestone with a real controller on Linux and on a real Windows PC.

Tests stay focused: one test per behaviour, no broad smoke tests, no tests kept for removed features.

### 5.3 CI (GitHub Actions)

CI runs only the jobs that a change needs, on pull requests, on pushes to `main` and `plan-*`, and on version tags (`v*`). The `changes` job lists the changed files and `.github/pick-jobs.sh` maps them to jobs: docs (`*.md`, `docs/`) run no job; `game/`, `assets/` and the marble's core script run both lints, the tests, the harness and the export; `levels/`, `kit/` and `tools/blender/` run the script lint, the tests and the export; each tool project under `tools/` runs the script lint and its own tests (`tools/harness` the harness job, `tools/audio/music` and `tools/art` the tool tests), and other `tools/` files run only the script lint; `.github/`, `justfile`, `mise.toml`, `tools/setup/pins.env`, `.gitattributes` and any path that no rule names run every job. A manual run (`workflow_dispatch`), a new branch or a new tag also runs every job.

- **`changes` job** (ubuntu): picks the jobs, and writes the changed files and the picked jobs to the run summary.
- **`lint-game` job** (ubuntu): runs `just lint-game`, which imports the game.
- **`lint-scripts` job** (ubuntu): runs `just lint-scripts`. It has no Godot and no LFS files, so a tool change lints in about a minute.
- **`levels` job** (ubuntu): installs Blender 5.2.4 (cached), runs `just build-levels` when the tests or the export run (else only `just build-marble`), uploads the built files. When the level cache has the .glb files, it runs `just build-levels --reuse`, which skips Blender but imports and checks the levels as before. When the core cache has the core and the levels are not needed, it skips Blender and Godot.
- **`test` job** (matrix: `ubuntu-latest`, `windows-latest`): Git LFS checkout (cached), `setup-godot@v2` with the Godot version from `mise.toml`, downloads the built levels, runs import, GUT tests and the headless level tests.
- **`harness` job** (ubuntu): `just test-harness`, the harness contract tests on a headless debug build.
- **`export` job** (ubuntu): `setup-godot@v2` with export templates, downloads the built levels, `just export`, boots the Linux export, plays every level in it (`.github/check-export.sh`), uploads both exports as artifacts. The check fails when the export does not load a built level or a file of its baked lightmap.
- **`windows-boot` job** (`windows-latest`): downloads the Windows export from the `export` job, boots it headless, checks its boot marker, and plays every level in it with the same check.
- **`tools` job** (ubuntu): `just test-music` and `just test-art`, each when its tool changed.
- **`release` job** (ubuntu, version tags only): runs after every other job passes. It downloads the two exports that the `export` job made and the boot checks passed, and publishes them as `orrery-<tag>-linux-x86_64.tar.gz` and `orrery-<tag>-windows-x86_64.zip` on a GitHub release with generated notes. A tag with a hyphen (`v0.1.0-rc.1`) makes a prerelease. Only this job has `contents: write`.
- GPU work (gallery, performance check) runs on Sean's machine only, because GitHub runners have no GPU.

CI caches (`actions/cache`; a cache made on a branch serves that branch and its pull requests, one made on `main` serves all):

| Cache | Path | Key | Restore |
|---|---|---|---|
| Git LFS objects | `.git/lfs` | `lfs-` + hash of the LFS object list | exact key |
| Godot import | `game/.godot` | `godot-import-<os>-<godot pin>-` + `hashFiles` of `game/**` (less `.godot/`, `*.gd`, `*.uid`, `*.tscn`, `*.tres`, `*.gdshader`, and the built core and levels, so all jobs on one OS share one key) and `assets/textures/**` | the newest cache with the `godot-import-<os>-<godot pin>-` prefix |
| Marble core | `game/core/marble/built/` | `marble-<blender pin>-<validator pin>-` + `hashFiles` of `tools/blender/marble_core.py`, its texture `Metal048A_2K-JPG_Color.jpg`, `game/core/marble/core_import.gd` and `justfile` (the recipe writes the `.import` file) | exact key |
| Level .glb files | `game/levels/built/*.glb` | `levels-<blender pin>-<validator pin>-` + `hashFiles` of `levels/**`, `kit/**`, `tools/blender/**`, `assets/props/**`, `assets/decals/**` and `game/skies/*.tres` (every file that the Blender export reads) | exact key |
| Blender and glTF-Validator | `~/.local/opt` | the two pins | exact key |

A partial hit of the import cache is safe: Godot imports a file again only when the MD5 of the file or of its `.import` file differs from the stored one. The level cache holds the Blender output only. `--reuse` writes fresh `.import` files (each import gives them a new UID), so every job that has the levels imports them again with the current `LevelConverter`. A change to one input of a Blender build misses its cache and builds again.

To cut a release, tag a commit that CI passed on, and push the tag:

```sh
git fetch origin
git tag -a v0.1.0-rc.1 -m "M1 playtest build 1" origin/plan-1
git push origin v0.1.0-rc.1
gh run watch -R seanGSISG/orrery   # then: gh release view v0.1.0-rc.1 -R seanGSISG/orrery
```

If the tag run fails, fix the cause, delete the tag (`git push origin :refs/tags/<tag>` and `git tag -d <tag>`), and tag the new commit. The exe is not signed, so Windows SmartScreen warns on its first start (More info, then Run anyway).

## 6. Dev environment

### 6.1 Already done (pre-setup, 2026-11-20)

- Installed: `xpadneo-dkms` 0.10.5 (Xbox Bluetooth driver), `evtest`, `shellcheck`.
- Created the private repo `seanGSISG/orrery` with the five triage labels. The local branch is `main`; `origin` points to the repo. Nothing pushed yet.
- `scripts/presetup-wizard.sh` walks Sean through the Stable Audio 3 license, review-bot access, and the USB and Bluetooth controller checks.
- Already present: `uv`, `just`, `bun`, `node`, `gh` (scopes `repo`, `workflow`, `project`), `hf` (logged in), `gamescope` 3.17, `wine` 11.22, `ffmpeg`, `docker`. `sudo` needs no password.

### 6.2 M0 install steps (`just setup` automates them)

1. **System packages:** `sudo pacman -S --needed mise git-lfs`, then `git lfs install`.
2. **Godot:** `mise use godot@4.7.2` (writes `mise.toml`), then confirm `mise which godot` runs 4.7.2. Export templates: download `Godot_v4.7.2-stable_export_templates.tpz` from the GitHub release, check it against `SHA512-SUMS.txt`, unzip its `templates/` into `~/.local/share/godot/export_templates/4.7.2.stable/`.
3. **Blender 5.2.4 LTS:** download the official Linux tarball from an official Blender mirror (`download.blender.org` refuses scripted downloads), check it against the SHA-256 pinned in `tools/setup/pins.env`, extract to `~/.local/opt/blender-5.2.4/`, link `~/.local/bin/blender-5.2`.
4. **Blender Lab MCP:** clone `https://projects.blender.org/lab/blender_mcp.git` at the commit pinned in `pins.env` into `~/.local/share/orrery/blender_mcp/`, build its add-on and install it into Blender 5.2.4 with `blender --command extension`, and `uv sync` its server. The add-on starts its bridge (`localhost:9876`) by itself when Blender runs with `--online-mode`: `just blender` (a window) or `just blender-agent` (hidden, in gamescope).
5. **Godot add-ons:** vendor GUT 9.7.1 into `game/addons/gut/`.
6. **Python tools:** `uv sync` in `tools/harness/` (MCP SDK, `evdev` for the virtual controller). `gdtoolkit` runs through `uvx`.
7. **glTF tools:** Khronos `glTF-Validator` release binary into `~/.local/bin/`; `@gltf-transform/cli` through `bunx`.
8. **Music models:** `tools/setup/comfy-models.txt` lists the ComfyUI files for ACE-Step 1.5 XL and Stable Audio 3 Medium (with its T5Gemma and Qwen text encoders). `hf download` puts them in the Hugging Face cache and setup links them into ComfyUI's models folder. Stable Audio 3 files wait until Sean accepts its license in the wizard.

Pins: Godot in `mise.toml`; everything else in `tools/setup/pins.env`. `just check-env` reruns the first-run checks (6.3) alone.

`.mcp.json` (project scope):

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "${HOME}/.local/share/orrery/blender_mcp/mcp", "run", "--quiet", "blender-mcp"],
      "env": { "BLENDER_PATH": "${HOME}/.local/bin/blender-5.2" }
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
| Blender Lab MCP | Runs code, returns a window screenshot and finds a `bpy` call in the API docs | `ahujasid/mcp-for-blender` with telemetry off |
| `gamescope --backend headless` | Godot renders a non-blank screenshot through it on the RTX 5090 | A small window on the KDE desktop |
| Virtual Xbox controller | Godot lists it as a joypad and reads A | Test through the harness input path only |
| Windows export under Wine | Boots headless and exits cleanly | CI Windows runner only |
| CI | A minimal project passes on both runners | — |
| ComfyUI music workflows | One ACE-Step and one Stable Audio 3 sample render | ElevenLabs Music (paid) for backing tracks |

## 7. Workflow

- **Specs and branches:** each spec is one GitHub issue with one spec branch. M0 and M1 share the first spec and the branch `plan-1`; M2, M3 and M4 each get their own spec (`plan-2`, `plan-3`, `plan-4`) when they start. Each task is a ticket PR into its spec branch, reviewed by Argus. A spec branch merges into `main` as a spec PR, reviewed by Argus and Devin through the babysit flow.
- **Merges into `main`** (Sean, 2026-11-20): a spec branch merges into `main` at checkpoints only. There are two: M0, after the Argus and Devin gate and with no playtest; and the end of M1, after Sean's playtest sign-off.
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
| **M1** | Marble solver and tuning; camera; input (keyboard, mouse, Xbox controller, button icons, rumble); harness and harness MCP; route bot; level pipeline and kit v1; objects: core set and the Clockwork Egg, Bumper, Steam Vent, Pendulum, Trapdoor, Crumbling Tiles, moving platforms, turning gears, turning arms; Coil Spring; HUD; menus; saves; ghosts; 3 Beginner levels; Ascent zones 1–3; title theme, 1 Beginner track, 1 Ascent track; first sound effects | All tests pass on Linux and Windows. The route bot finishes all 3 levels and Ascent zones 1–3. Sean has played it with a real controller on Linux and Windows |
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
| Git LFS quota on GitHub | Textures at 2K by default, with a short list of 4K exceptions (`docs/design/visual-quality.md` §6); cache LFS objects in CI |
| The lightmap bake calls Godot's internal `LightmapGIEditorPlugin._bake` through the `lightmap_baker` add-on (#24). Godot does not promise that this stays | Recheck the bake on every Godot upgrade (run `just bake` on a level and read its `BAKE done` line). The add-on's header says the same |
| Windows save rename atomicity is untested. `SaveGame` writes `save.json.tmp` and renames it over `save.json`; on Windows a crash between the two steps may leave only the `.tmp` file | `read()` falls back to the `.tmp` file. Check the rename on a real Windows PC at the M1 playtest |
| The ray-tracing spike (#38) uses Godot 4.7's experimental `RenderingDevice` ray-tracing API, which may change | Ultra-only option, built after M1 as a prototype. Keep, change or drop after the write-up; every other preset renders as before |
| Name conflict with existing "Orrery" games | `orrery` stays the codename; the store title is chosen before any public release |

## 10. Things only Sean does

- Run `scripts/presetup-wizard.sh`: the Stable Audio 3 license, review-bot access, the controller over USB and Bluetooth.
- Approve the style board; pick the HUD and menu mockups.
- Feel-review the marble physics early in M1.
- Pick the final music tracks.
- Play each milestone with a real controller on Linux and on a real Windows PC.
- Choose the store title before any public release.
