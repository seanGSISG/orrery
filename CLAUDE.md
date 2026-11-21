# Orrery

An original 3D marble platformer for Linux and Windows, built with Godot 4.7.2 and Blender 5.2.4 LTS. `docs/plan.md` holds every design decision, the architecture and the milestones. Read its relevant section before you add a feature, change the design, or start a milestone task. When a task conflicts with the plan, raise it with Sean before you build.

## Rules

- **Originality.** Every name, level, asset, melody and line of code in Orrery is our own. The projects in `docs/research/gameplay.md` are references for numbers and behaviour only. Write all code yourself from the documented behaviour.
- **Level scripts are the source of truth.** Change a level by editing `levels/<tier>/<id>.py` or `kit/`, then rebuild with `just build-levels <id>`. `.blend` and `.glb` files are build outputs. After live work in the Blender MCP, write the result back into the script.
- **Strict typing.** Type every GDScript variable, parameter and return. Project settings turn untyped declarations and unsafe calls into errors.
- **One input path.** The player, the route bot and the harness all feed `MarbleInput`. Test the marble through it.
- **Harness is debug-only.** Automation code lives in `game/harness/`, which the release export presets leave out.
- **Licenses.** Add a line to `docs/licenses.md` for every third-party asset, sample, font or AI model you use: source, license, where it is used.
- **Secrets.** Add every Easter egg and secret to `docs/secrets.md`.
- **File ownership** in parallel work follows `docs/plan.md` §7. Ask the owning agent for changes to its files.

## Done means

1. `just lint` and `just test` pass, and `just test` reports a non-zero test count.
2. For a level or object change: `just test-levels <id>` passes, so the route bot finishes under par.
3. For anything visible: you have looked at it in `just gallery <id>` or an `orrery` MCP `game_screenshot`, and the image shows the change.

## Seeing the game and the scene

- The `orrery` MCP server launches the game in `gamescope` with no window. It gives you game state, input, frame stepping, screenshots and the route bot.
- The `blender` MCP server runs code in a live Blender, takes viewport screenshots and searches the Blender 5.2 API docs. Search the docs before you use an unfamiliar `bpy` call. Its search matches whole words, so query `export_scene gltf`, not `export_scene.gltf`.
- Live Blender tools need a running Blender: start `just blender-agent` in the background (hidden, in gamescope), or ask Sean to run `just blender` for a window. The bridge listens on `localhost:9876`. The `_for_cli` tools and the doc search work without it.

## Gotchas

- `godot --headless` renders nothing, so its screenshots are blank. Use the harness for anything visual. Use `--headless` for imports, exports and logic tests.
- Godot and Jolt don't promise identical results from identical inputs. Assert with tolerances, and compare physics values only within one OS. Ghosts record transforms for this reason.
- Run the pinned official Blender (`blender-5.2`). The Arch `blender` package uses a different Python.
- GUT reports success when zero tests run, and it skips a test script that does not parse. Keep both checks in `just test`.
- With `unsafe_call_argument` an error, a Variant argument to a GUT assert (for example from `ProjectSettings.get_setting`) is a parse error. Put the value in a typed variable first.

## Workflow

Each spec is a GitHub issue with its own spec branch: M0 and M1 share `plan-1`, then M2 uses `plan-2`, and so on. Each task is a ticket PR into its spec branch, reviewed by Argus. A spec branch merges into `main` as a spec PR, reviewed by Argus and Devin. Run the `babysit` skill after you open or push a PR.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `seanGSISG/orrery`, through the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
