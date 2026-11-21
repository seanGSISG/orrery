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
import: kit-textures
    "{{ godot }}" --headless --path game --import

# Play a level in a window (default: the flat test level). Click to turn the camera with the mouse
[positional-arguments]
run level="flat": import
    "{{ godot }}" --path game -- --level "$1"

# Build level scripts (all, or the given ids) into game/levels/built/ and check that they import
[positional-arguments]
build-levels *ids: kit-textures
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

# Run the GUT tests headless. Fails when a test fails, a script does not load, or zero tests ran
[script("bash")]
test: fresh-levels import
    set -euo pipefail
    log=$(mktemp)
    trap 'rm -f "$log"' EXIT
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
        [[ $f == tools/harness/* ]] && continue
        tools+=("$f")
        grep -q '^# /// script' "$f" && deps+=(--with-requirements "$f")
    done
    uvx "${deps[@]}" "ty@$TY_VERSION" check "${tools[@]}"
    # The harness is a uv project; ty checks it with its locked dependencies.
    uv run --quiet --project tools/harness --with "ty==$TY_VERSION" ty check tools/harness
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

# Build the Linux debug export (harness and test levels included) into build/linux-debug/
export-debug: import
    mkdir -p build/linux-debug
    "{{ godot }}" --headless --path game --export-debug "Linux Debug" ../build/linux-debug/orrery.x86_64

# --- Route bot (#14) ---

# Run the route bot on built levels (all, or the given ids): first_run under par, expert under gold
[positional-arguments]
[script("bash")]
test-levels *ids: fresh-levels import
    set -euo pipefail
    log=$(mktemp)
    trap 'rm -f "$log"' EXIT
    # --quit-after stops a run whose test script did not load; it would wait forever.
    status=0
    "{{ godot }}" --headless --path game --quit-after 100 res://harness/route_bot_levels.tscn \
        -- "$@" 2>&1 | tee "$log" || status=$?
    if grep -q 'SCRIPT ERROR' "$log" || ! grep -q '^test-levels: ' "$log"; then
        echo "just test-levels: the level test did not run to the end" >&2
        exit 1
    fi
    exit "$status"

# Print the par (first_run time × 1.5) and gold (expert time × 1.15) from route bot times
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

# Render every shot of each level (all, or the given ids) on High into build/gallery/index.html
[positional-arguments]
gallery *ids: fresh-levels import
    uv run --quiet --script tools/gallery/gallery.py "$@"

# Fly each level's camera path per graphics preset and check the GPU time and VRAM budgets
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
    timeout 3600 gamescope --backend headless -W 1280 -H 720 -- \
        "{{ godot }}" --editor --path game -- --bake-lightmaps "${scenes[@]}" >"$log" 2>&1 || true
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

# --- Skies (#24) ---

# Bake the tier skies (all, or dawn, noon, dusk) into game/skies/<name>.hdr with Cycles on this GPU
[positional-arguments]
bake-skies *args:
    blender-5.2 -b --factory-startup -noaudio --python-exit-code 1 --python tools/blender/bake_skies.py -- "$@"
