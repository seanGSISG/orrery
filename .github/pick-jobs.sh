#!/usr/bin/env bash
# Reads changed paths, one per line, on stdin and prints the CI jobs they need as
# `<job>=true|false` lines for $GITHUB_OUTPUT. A path that no rule names needs every job, so
# feed it any such path (for example `everything`) to force a full run.
# Try it: git diff --name-only --no-renames origin/plan-1 | .github/pick-jobs.sh
set -euo pipefail

jobs=(lint-game lint-scripts test harness export music art perf)
declare -A need
for job in "${jobs[@]}"; do need[$job]=false; done
run() { for job in "$@"; do need[$job]=true; done; }

while IFS= read -r path; do
    case $path in
        "") ;;
        # Docs: no job reads them.
        *.md | docs/* | LICENSE*) ;;
        # The workflow, the task runner and the version pins: every job.
        .github/* | justfile | mise.toml | tools/setup/pins.env | .gitattributes) run "${jobs[@]}" ;;
        # The game and what it imports (the kit textures, the marble's core). The script lint
        # checks any Python or shell script in them.
        game/* | assets/* | tools/blender/marble_core.py) run lint-game lint-scripts test harness export ;;
        # Level scripts and the level builder: the tests and the export load the built levels.
        levels/* | kit/* | tools/blender/*) run lint-scripts test export ;;
        # Tool projects: the script lint and their own tests.
        tools/harness/*) run lint-scripts harness ;;
        tools/audio/music/*) run lint-scripts music ;;
        tools/art/*) run lint-scripts art ;;
        tools/perf/*) run lint-scripts perf ;;
        # The other tool scripts and the ShellCheck config: the script lint.
        tools/* | .shellcheckrc) run lint-scripts ;;
        *) run "${jobs[@]}" ;;
    esac
done

# The levels job: `all` builds every level and the marble's core, for the tests and the export;
# `core` builds only the core, which lint-game and the harness need to import the game.
levels=false
for job in lint-game harness; do [[ ${need[$job]} == true ]] && levels=core; done
for job in test export; do [[ ${need[$job]} == true ]] && levels=all; done
echo "levels=$levels"
for job in "${jobs[@]}"; do echo "$job=${need[$job]}"; done
