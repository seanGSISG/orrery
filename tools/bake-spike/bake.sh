#!/usr/bin/env bash
# Bakes the LightmapGI of the given imported scenes in a hidden gamescope display, the shape of
# a `just bake` recipe. Usage: bake.sh <project dir> res://level/a.glb [res://level/b.glb ...]
# gamescope always exits 0 (or dumps core on teardown), so success is the plugin's summary line.
set -euo pipefail
godot=${GODOT:-$(cd /home/adminuser/orca/projects/marble-blast-game && mise which godot)}
project=$1
shift
"$godot" --headless --path "$project" --import >/dev/null 2>&1
log=$(mktemp)
trap 'rm -f "$log"' EXIT
gamescope --backend headless -W 1280 -H 720 -- \
    "$godot" --editor --path "$project" -- --bake-lightmaps "$@" >"$log" 2>&1 || true
grep -E '^(BAKE|Done baking|ERROR|SCRIPT ERROR)' "$log" || true
if ! grep -qx "BAKE done: $# of $# baked" "$log"; then
    echo "bake.sh: not every scene baked" >&2
    exit 1
fi
