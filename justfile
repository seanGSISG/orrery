# Orrery tasks. Run `just` to list them. CI runs them too, on Linux and Windows (Git Bash).
set shell := ["bash", "-euo", "pipefail", "-c"]
export PATH := if os_family() == "windows" { env("PATH") } else { env("HOME") + "/.local/bin:" + env("PATH") }

# The mise-pinned Godot, else the `godot` on PATH (CI installs it with setup-godot).
godot := `mise which godot 2>/dev/null || command -v godot || echo godot`

# List the tasks
default:
    @just --list

# Install and check every pinned tool (safe to repeat)
setup:
    tools/setup/setup.sh

# Run the first-run checks only
check-env:
    tools/setup/check.sh

# Open Blender 5.2 with the MCP bridge on localhost:9876 (a window on the desktop)
[positional-arguments]
blender *args:
    blender-5.2 --online-mode "$@"

# Blender with the MCP bridge in a hidden gamescope display; run it in the background
blender-agent:
    gamescope --backend headless -W 1920 -H 1080 -- blender-5.2 --online-mode

# Build the marble's brass core (tools/blender/marble_core.py) into game/core/marble/built/
[script("bash")]
build-marble:
    set -euo pipefail
    out=game/core/marble/built
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT
    if ! "${BLENDER:-blender-5.2}" -b --factory-startup -noaudio --python-exit-code 1 \
        --python tools/blender/marble_core.py -- "$tmp/orrery_core.glb" >"$tmp/log" 2>&1; then
        cat "$tmp/log" >&2
        echo "just build-marble: Blender failed" >&2
        exit 1
    fi
    "${GLTF_VALIDATOR:-gltf_validator}" "$tmp/orrery_core.glb"
    # The .import file names the post-import script before Godot can see the new .glb.
    mkdir -p "$out"
    printf '[remap]\n\nimporter="scene"\n\n[params]\n\nimport_script/path="res://core/marble/core_import.gd"\ngltf/embedded_image_handling=2\n' \
        >"$out/orrery_core.glb.import"
    mv "$tmp/orrery_core.glb" "$out/orrery_core.glb"

# Build the marble's core when its .glb is missing or older than its script or its texture
[private]
[script("bash")]
fresh-marble:
    set -euo pipefail
    glb=game/core/marble/built/orrery_core.glb
    for input in tools/blender/marble_core.py assets/textures/metal/Metal048A_2K-JPG_Color.jpg; do
        if [[ ! -f $glb || $input -nt $glb ]]; then just build-marble; break; fi
    done

# Copy the kit textures that the game uses from assets/textures/ into the Godot project, which
# reads only res://. A committed game/materials/textures/<file>.import adopts <file>
[private]
[script("bash")]
kit-textures:
    set -euo pipefail
    for import in game/materials/textures/*.import; do
        name=$(basename "$import" .import)
        sources=(assets/textures/*/"$name")
        if [[ ! -f ${sources[0]} ]]; then echo "just kit-textures: assets/textures/ has no $name" >&2; exit 1; fi
        cp -u "${sources[0]}" "game/materials/textures/$name"
    done

# Import the Godot project headless (fills game/.godot)
import: fresh-marble kit-textures
    "{{ godot }}" --headless --path game --import

# Play a level in a window (default: the flat test level). Click to turn the camera with the mouse
[positional-arguments]
run level="flat": import
    "{{ godot }}" --path game -- --level "$1"

# Build level scripts (all, or the given ids) into game/levels/built/ and check that they import
[positional-arguments]
build-levels *ids: fresh-marble kit-textures
    GODOT="{{ godot }}" uv run --script tools/blender/build_levels.py "$@"

# Build the feel-review course and play it in a window with the tuning overlay (LB+Y or F1)
feel: (build-levels "feel")
    "{{ godot }}" --path game res://debug/feel.tscn

# Build the levels whose .glb is missing or older than its script, the kit, the importer, the
# material set or a sky preset (the importer writes the sky and the sun into the level)
[private]
[script("bash")]
fresh-levels:
    set -euo pipefail
    inputs=(kit/*.py tools/blender/build_level.py tools/blender/build_levels.py game/levels/level_converter.gd game/materials/kit_materials.gd game/skies/sky_preset.gd game/skies/*.tres)
    stale=()
    for script in levels/*/*.py; do
        id=$(basename "$script" .py)
        glb="game/levels/built/$id.glb"
        for input in "$script" "${inputs[@]}"; do
            if [[ ! -f $glb || $input -nt $glb ]]; then stale+=("$id"); break; fi
        done
    done
    if (( ${#stale[@]} > 0 )); then just build-levels "${stale[@]}"; fi

# Run the GUT tests headless. Fails when a test fails, a script does not load, or zero tests ran.
# XDG_DATA_HOME points Godot at an empty user:// that the recipe deletes, so tests never touch the
# player's save. Windows (CI) has no XDG_DATA_HOME: Godot writes to APPDATA there, which is harmless.
[script("bash")]
test: fresh-levels import
    set -euo pipefail
    log=$(mktemp) data=$(mktemp -d)
    trap 'rm -rf "$log" "$data"' EXIT
    export XDG_DATA_HOME="$data"
    "{{ godot }}" --headless --path game -s res://addons/gut/gut_cmdln.gd -gdisable_colors 2>&1 | tee "$log"
    # GUT skips a test script that does not parse, and it exits 0 when zero tests ran.
    if grep -q 'Parse Error' "$log"; then echo "just test: a script did not load" >&2; exit 1; fi
    count=$(grep -oE '^Tests +[0-9]+' "$log" | grep -oE '[0-9]+' || true)
    if (( ${count:-0} == 0 )); then echo "just test: zero tests ran" >&2; exit 1; fi

# Lint GDScript (gdlint, and a Godot compile check), Python (Ruff; ty outside Blender
# scripts) and shell scripts (shellcheck). Tool versions come from tools/setup/pins.env
[script("bash")]
lint: import
    set -euo pipefail
    source tools/setup/pins.env
    files() { git ls-files --cached --others --exclude-standard "$@"; }
    mapfile -t gd < <(files 'game/*.gd' ':!game/addons/*')
    uvx --from "gdtoolkit==$GDTOOLKIT_VERSION" gdlint "${gd[@]}"
    # Compile every game script, also the ones that no test loads. Load them from a running
    # SceneTree, not with --check-only, so that references to autoloads resolve.
    check=$(mktemp --suffix=.gd)
    trap 'rm -f "$check"' EXIT
    cat > "$check" <<'GDSCRIPT'
    extends SceneTree

    func _initialize() -> void:
        for path: String in OS.get_cmdline_user_args():
            load("res://" + path.trim_prefix("game/"))
        quit()
    GDSCRIPT
    status=0
    log=$("{{ godot }}" --headless --path game --script "$check" -- "${gd[@]}" 2>&1) || status=$?
    if (( status != 0 )) || grep -q 'SCRIPT ERROR' <<<"$log"; then
        echo "$log" >&2
        echo "just lint: a game script does not compile" >&2
        exit 1
    fi
    mapfile -t py < <(files '*.py')
    uvx "ruff@$RUFF_VERSION" check "${py[@]}"
    uvx "ruff@$RUFF_VERSION" format --check "${py[@]}"
    # Blender scripts import bpy, which exists only inside Blender. Tool scripts declare
    # their dependencies inline (PEP 723); ty checks them with those dependencies.
    tools=() deps=()
    for f in "${py[@]}"; do
        grep -qE '^(import|from) bpy' "$f" && continue
        [[ $f == tools/harness/* || $f == tools/audio/music/* ]] && continue
        tools+=("$f")
        grep -q '^# /// script' "$f" && deps+=(--with-requirements "$f")
    done
    uvx "${deps[@]}" "ty@$TY_VERSION" check "${tools[@]}"
    # The harness and the music pipeline are uv projects; ty checks each with its locked dependencies.
    uv run --quiet --project tools/harness --with "ty==$TY_VERSION" ty check tools/harness
    uv run --quiet --project tools/audio/music --with "ty==$TY_VERSION" ty check tools/audio/music
    mapfile -t sh < <(files '*.sh')
    shellcheck "${sh[@]}"

# Build the Linux and Windows release exports into build/
export: import
    mkdir -p build/linux build/windows
    "{{ godot }}" --headless --path game --export-release "Linux" ../build/linux/orrery.x86_64
    "{{ godot }}" --headless --path game --export-release "Windows Desktop" ../build/windows/orrery.exe

# Boot the Windows export headless under Wine and check its boot marker
[script("bash")]
smoke-wine: export
    set -euo pipefail
    export WINEPREFIX="${XDG_CACHE_HOME:-$HOME/.cache}/orrery/wine" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml="
    status=0
    log=$(timeout 180 wine build/windows/orrery.exe --headless -- --smoke 2>&1) || status=$?
    if (( status != 0 )) || ! grep -q '^ORRERY boot ok' <<<"$log"; then
        echo "$log" >&2
        echo "just smoke-wine: no boot marker (exit $status)" >&2
        exit 1
    fi
    echo "Windows export boots under Wine."

# --- Harness (#9) ---

# Drive a debug build through the harness CLI, for example `just harness launch --level flat`
[positional-arguments]
harness *args:
    uv run --quiet --project tools/harness orrery-harness "$@"

# Run the harness contract tests on a headless debug build. `-m gpu` runs the GPU screenshot test
[positional-arguments]
test-harness *args: import
    uv run --quiet --project tools/harness pytest tools/harness "$@"

# --- Music pipeline (#26) ---

# Run the music pipeline tests (needs ffmpeg for the loudness test)
[positional-arguments]
test-music *args:
    uv run --quiet --project tools/audio/music pytest tools/audio/music "$@"

# Build the Linux debug export (harness and test levels included) into build/linux-debug/
export-debug: import
    mkdir -p build/linux-debug
    "{{ godot }}" --headless --path game --export-debug "Linux Debug" ../build/linux-debug/orrery.x86_64

# --- Route bot (#14) ---

# Run the route bot on built levels (all, or the given ids): first_run under par, expert under gold.
# Like `test`, it runs with an empty user:// (XDG_DATA_HOME) that the recipe deletes, so the bot's
# finishes never write the player's save or ghosts.
[positional-arguments]
[script("bash")]
test-levels *ids: fresh-levels import
    set -euo pipefail
    log=$(mktemp) data=$(mktemp -d)
    trap 'rm -rf "$log" "$data"' EXIT
    export XDG_DATA_HOME="$data"
    # --quit-after stops a run whose test script did not load; it would wait forever.
    status=0
    "{{ godot }}" --headless --path game --quit-after 100 res://harness/route_bot_levels.tscn \
        -- "$@" 2>&1 | tee "$log" || status=$?
    if grep -q 'SCRIPT ERROR' "$log" || ! grep -q '^test-levels: ' "$log"; then
        echo "just test-levels: the level test did not run to the end" >&2
        exit 1
    fi
    exit "$status"

# Print the par (first_run time × 1.5) and gold (expert time × 1.15) from route bot times. It runs
# test-levels, so it also leaves the player's save alone
suggest-times id: (test-levels "--suggest" id)

# --- Controller (#18) ---

# Drive a virtual Xbox pad on /dev/uinput (local only). The pad plugs in while the game runs;
# the test checks that Godot sees it, A makes the marble jump and the left stick rolls it
[script("bash")]
test-pad: import
    set -euo pipefail
    if [[ ! -w /dev/uinput ]]; then echo "just test-pad: /dev/uinput is not writable" >&2; exit 1; fi
    log=$(mktemp) padlog=$(mktemp)
    steps="press a 0.3; wait 0.7; stick left 0 1 0.6; stick left 0 -1 0.6; wait 0.3"
    (sleep 3; exec uv run --quiet tools/pad/virtual_pad.py --seconds 60 --sequence "$steps") >"$padlog" 2>&1 &
    pad=$!
    trap 'pkill -P "$pad" || true; kill "$pad" 2>/dev/null || true; rm -f "$log" "$padlog"' EXIT
    status=0
    ORRERY_VIRTUAL_PAD=1 "{{ godot }}" --headless --path game -s res://addons/gut/gut_cmdln.gd \
        -gdisable_colors -gunit_test_name=test_virtual_pad 2>&1 | tee "$log" || status=$?
    # A failed Godot run falls through to here, so the pad log explains it before cleanup.
    if (( status != 0 )) || ! grep -qE '^Passing Tests +1$' "$log" || grep -qE '^(Failing|Risky)' "$log"; then
        cat "$padlog" >&2
        echo "just test-pad: the virtual pad test did not pass" >&2
        exit 1
    fi

# --- Gallery and performance (#20) ---

# Render every shot of each level (all, or the given ids) on High into build/gallery/index.html. Fails on a shader compile error
[positional-arguments]
gallery *ids: fresh-levels import
    uv run --quiet --script tools/gallery/gallery.py "$@"

# Fly each level's camera path per graphics preset and check the GPU time and VRAM budgets. Fails on a shader compile error
[positional-arguments]
perf *ids: fresh-levels import
    GODOT="{{ godot }}" uv run --quiet --script tools/perf/perf.py "$@"

# --- Lightmaps (#24) ---

# Bake the lightmaps of levels (all, or the given ids) on this GPU. Close every Godot editor on this project first
[positional-arguments]
[script("bash")]
bake *ids: fresh-levels import
    set -euo pipefail
    if (( $# == 0 )); then mapfile -t ids < <(basename -s .py levels/*/*.py); set -- "${ids[@]}"; fi
    out=game/levels/lightmaps
    # The editor scans the project at start; the bake can import its files only into a known folder.
    mkdir -p "$out"
    scenes=()
    for id in "$@"; do
        glb="game/levels/built/$id.glb"
        if [[ ! -f $glb ]]; then echo "just bake: $glb is missing" >&2; exit 1; fi
        scenes+=("res://levels/built/$id.glb")
    done
    log=$(mktemp) settings=$(mktemp)
    # The editor rewrites project.godot on exit and drops the settings that equal the defaults.
    cp game/project.godot "$settings"
    trap 'cp "$settings" game/project.godot; rm -f "$log" "$settings"' EXIT
    # A bake needs a real GPU, so the editor runs in a hidden gamescope display. gamescope's exit
    # code does not follow Godot's, so the plugin's summary line is the only success check.
    # The Dummy audio driver keeps the editor silent.
    timeout 3600 gamescope --backend headless -W 1280 -H 720 -- \
        "{{ godot }}" --audio-driver Dummy --editor --path game -- --bake-lightmaps "${scenes[@]}" >"$log" 2>&1 || true
    # The sidecar records the level each new bake belongs to; `just test` warns when they differ.
    for id in "$@"; do
        if grep -q "^BAKE ok res://levels/built/$id.glb " "$log"; then
            sha256sum "game/levels/built/$id.glb" | cut -d' ' -f1 >"$out/$id.sha256"
        fi
    done
    if ! grep -qx "BAKE done: $# of $# baked" "$log"; then
        grep -E '^(BAKE|ERROR|SCRIPT ERROR)' "$log" >&2 || true
        echo "just bake: not every level baked" >&2
        exit 1
    fi
    grep -E '^BAKE' "$log"

# --- Audio (#25) ---

# Synthesise the sound effects (game/audio/sfx/) and the test music loops, and check them. `--montage PATH` also joins the sounds into one OGG
[positional-arguments]
build-sfx *args:
    uv run --script tools/audio/sfx/synth_sfx.py "$@"

# --- HUD and menus (#22) ---

# Save a screenshot of each UI screen at 1080p and 4K into build/ui/<height>/ (GPU, gamescope).
# The Dummy audio driver keeps the run silent. It fails on a shader compile error in the log
[script("bash")]
ui-shots: fresh-levels import
    set -euo pipefail
    log=$(mktemp)
    trap 'rm -f "$log"' EXIT
    for size in "1920 1080" "3840 2160"; do
        read -r width height <<<"$size"
        # --quit-after stops a run whose script failed before its end; it would wait forever.
        gamescope --backend headless -W "$width" -H "$height" -- "{{ godot }}" \
            --audio-driver Dummy --path game --resolution "${width}x${height}" --quit-after 3000 \
            res://test/ui/ui_shots.tscn -- --out "$PWD/build/ui/$height" >"$log" 2>&1 || true
        # gamescope's exit code does not follow Godot's, so the script's last line is the check.
        if ! grep -qx 'ui-shots: done' "$log"; then
            grep -E '^(ui-shots|ERROR|SCRIPT ERROR)' "$log" >&2 || true
            echo "just ui-shots: not every screenshot was saved at ${width}x${height}" >&2
            exit 1
        fi
        # A shader that does not compile draws as a grey solid, and the screenshots still save.
        uv run --quiet --project tools/harness orrery-harness check-log "$log"
        grep '^ui-shots: /' "$log"
    done

# --- Skies (#24) ---

# Bake the tier skies (all, or dawn, noon, dusk) into game/skies/<name>.hdr with Cycles on this GPU
[positional-arguments]
bake-skies *args:
    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 --python tools/blender/bake_skies.py -- "$@"
