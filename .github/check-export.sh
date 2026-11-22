#!/usr/bin/env bash
# Checks that an export holds every level and its baked lightmap. It plays each level of
# levels/*/*.py in the export for two frames, and Godot's verbose log must show the load of the
# built level and of each file of its bake in game/levels/lightmaps/. Run it from the repository
# root: .github/check-export.sh build/linux/orrery.x86_64
set -euo pipefail
shopt -s nullglob

exe=$1
data=$(mktemp -d)
trap 'rm -rf "$data"' EXIT
# An empty user:// that the trap deletes, so a check never writes the player's save.
export XDG_DATA_HOME=$data

levels=0 problems=0
for script in levels/*/*.py; do
    id=$(basename "$script" .py)
    want=("levels/built/$id.glb")
    for file in game/levels/lightmaps/"$id".* game/levels/lightmaps/"$id"_*; do
        [[ $file == *.import || $file == *.sha256 ]] || want+=("${file#game/}")
    done
    before=$problems status=0
    log=$("$exe" --headless --audio-driver Dummy --verbose --quit-after 2 -- --level "$id" 2>&1) || status=$?
    if (( status != 0 )); then
        echo "$id: the export exits with $status" >&2
        problems=$((problems + 1))
    fi
    for file in "${want[@]}"; do
        if ! grep -qF "Completed load for: 'res://$file'" <<<"$log"; then
            echo "$id: the export does not load res://$file" >&2
            problems=$((problems + 1))
        fi
    done
    levels=$((levels + 1))
    if (( problems == before )); then echo "$id: ${want[*]} load"; fi
done

if (( levels == 0 )); then echo "check-export: no level script in levels/" >&2; exit 1; fi
if (( problems > 0 )); then echo "check-export: $problems problems in $levels levels" >&2; exit 1; fi
echo "ORRERY levels ok: $levels levels"
