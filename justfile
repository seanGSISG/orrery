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

# Import the Godot project headless (fills game/.godot)
import:
    "{{ godot }}" --headless --path game --import

# Play a level in a window (default: the flat test level). Click to turn the camera with the mouse
run level="flat": import
    "{{ godot }}" --path game -- --level {{ level }}

# Run the GUT tests headless. Fails when a test fails, a script does not load, or zero tests ran
[script("bash")]
test: import
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
        tools+=("$f")
        grep -q '^# /// script' "$f" && deps+=(--with-requirements "$f")
    done
    uvx "${deps[@]}" "ty@$TY_VERSION" check "${tools[@]}"
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
