#!/usr/bin/env bash
# Reads changed paths, one per line, on stdin and prints the CI jobs they need as
# `<job>=true|false` lines for $GITHUB_OUTPUT. A path that no rule names needs every job, so
# feed it any such path (for example `everything`) to force a full run.
# Try it: git diff --name-only --no-renames origin/plan-1 | .github/pick-jobs.sh
set -euo pipefail

jobs=(lint test harness export music art)
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
        # The game and what it imports (the kit textures, the marble's core).
        game/* | assets/* | tools/blender/marble_core.py) run lint test harness export ;;
        # Level scripts and the level builder: only the tests load built levels.
        levels/* | kit/* | tools/blender/*) run lint test ;;
        # Tool projects: lint and their own tests.
        tools/harness/*) run lint harness ;;
        tools/audio/music/*) run lint music ;;
        tools/art/*) run lint art ;;
        # The other tool scripts and the ShellCheck config: lint.
        tools/* | .shellcheckrc) run lint ;;
        *) run "${jobs[@]}" ;;
    esac
done

# Lint, the tests, the harness and the export import the game, which needs the marble's core
# from the levels job. That job builds every level only when the tests need them.
levels=false
for job in lint test harness export; do [[ ${need[$job]} == true ]] && levels=true; done
echo "levels=$levels"
for job in "${jobs[@]}"; do echo "$job=${need[$job]}"; done
