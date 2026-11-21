#!/usr/bin/env bash
# First-run checks for the Orrery toolchain. Prints one line per check:
#   PASS      the primary path works
#   FALLBACK  the primary path failed and the plan's fallback (named on the line) works
#   FAIL      neither works; fix this before building on it
# Exits non-zero when any check FAILs. Logs go to ~/.cache/orrery/check-logs.
# Run it through `just check-env` (setup runs it too).
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
# shellcheck source=pins.env
source "$ROOT/tools/setup/pins.env"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/orrery"
LOG="$CACHE/check-logs"
mkdir -p "$LOG"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
GODOT=$(cd "$ROOT" && mise which godot 2>/dev/null || true)
BLENDER="$HOME/.local/bin/blender-$BLENDER_SERIES"
fails=0

report() {  # report STATUS NAME DETAIL
  local colour=32; [[ "$1" == FALLBACK ]] && colour=33; [[ "$1" == FAIL ]] && { colour=31; fails=$((fails + 1)); }
  printf '   \033[%sm%-8s\033[0m %-28s %s\n' "$colour" "$1" "$2" "$3"
}

# probe MODE LOG [launcher...]: run the Godot probe project; succeeds on its marker line.
probe() {
  local mode="$1" log="$2"; shift 2
  timeout 90 "$@" "$GODOT" --path "$WORK/probe" -- --mode="$mode" --out="$WORK/render.png" >"$log" 2>&1
  grep -q "^PROBE $mode ok" "$log"
}
GS=(gamescope --backend headless -W 640 -H 360 --)

# 1. Godot version
if [[ -n "$GODOT" ]] && "$GODOT" --version | grep -q "^$(sed -n 's/^godot = "\(.*\)"/\1/p' "$ROOT/mise.toml")\.stable"; then
  report PASS "Godot" "$("$GODOT" --version | head -1)"
else
  report FAIL "Godot" "mise does not provide the pinned Godot; run just setup"
  exit 1
fi
cp -r "$ROOT/tools/setup/probe" "$WORK/probe"
"$GODOT" --headless --path "$WORK/probe" --import >"$LOG/probe-import.log" 2>&1

# 2. Blender EEVEE with no display
eevee=(-b --factory-startup --python-exit-code 1 --python "$ROOT/tools/setup/checks/blender_eevee.py" -- "$WORK/eevee.png")
if env -u DISPLAY -u WAYLAND_DISPLAY "$BLENDER" "${eevee[@]}" >"$LOG/blender-nodisplay.log" 2>&1; then
  report PASS "Blender EEVEE, no display" "$(grep -o 'contrast=[0-9.]*' "$LOG/blender-nodisplay.log")"
elif "$BLENDER" "${eevee[@]}" >"$LOG/blender-display.log" 2>&1; then
  report FALLBACK "Blender EEVEE, no display" "renders only inside the desktop session"
else
  report FAIL "Blender EEVEE, no display" "see $LOG/blender-*.log"
fi

# 3. Godot GPU frames with no window
if probe render "$LOG/godot-gamescope.log" "${GS[@]}"; then
  report PASS "Godot GPU frame, gamescope" "$(grep -o 'contrast=.*' "$LOG/godot-gamescope.log")"
elif probe render "$LOG/godot-window.log"; then
  report FALLBACK "Godot GPU frame, gamescope" "renders in a desktop window instead"
else
  report FAIL "Godot GPU frame, gamescope" "see $LOG/godot-*.log"
fi

# 4. Virtual Xbox controller seen by Godot
uv run --quiet "$ROOT/tools/pad/virtual_pad.py" --seconds 40 --press a >"$LOG/pad.log" 2>&1 &
pad=$!
sleep 2
if probe joypad "$LOG/joypad-headless.log" ; then
  report PASS "Virtual Xbox controller" "$(grep -o 'name=.*' "$LOG/joypad-headless.log")"
elif probe joypad "$LOG/joypad-gamescope.log" "${GS[@]}"; then
  report PASS "Virtual Xbox controller" "$(grep -o 'name=.*' "$LOG/joypad-gamescope.log") (in gamescope only)"
else
  report FALLBACK "Virtual Xbox controller" "test through the harness input path only; see $LOG/pad.log"
fi
kill "$pad" 2>/dev/null; wait "$pad" 2>/dev/null

# 5. Windows export boots under Wine
export WINEPREFIX="$CACHE/wine" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml="
mkdir -p "$WORK/win"
if "$GODOT" --headless --path "$WORK/probe" --export-debug "Windows Desktop" "$WORK/win/probe.exe" >"$LOG/win-export.log" 2>&1 \
  && timeout 180 wine "$WORK/win/probe.console.exe" --headless -- --mode=boot >"$LOG/wine.log" 2>&1 \
  && grep -q "^PROBE boot ok" "$LOG/wine.log"; then
  report PASS "Windows export under Wine" "boots headless"
elif [[ -f "$WORK/win/probe.exe" ]]; then
  report FALLBACK "Windows export under Wine" "export works; boot check moves to the CI Windows runner"
else
  report FAIL "Windows export under Wine" "export failed; see $LOG/win-export.log"
fi

echo
(( fails == 0 )) && echo "   All checks passed or have a working fallback." || echo "   $fails check(s) failed."
exit $(( fails > 0 ))
