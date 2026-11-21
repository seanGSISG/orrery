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
# Vendor + product of the virtual Xbox 360 pad (tools/pad/virtual_pad.py), as they
# appear in an SDL/Godot joypad GUID.
PAD_ID=5e0400008e020000
fails=0

report() {  # report STATUS NAME DETAIL
  local colour=32; [[ "$1" == FALLBACK ]] && colour=33; [[ "$1" == FAIL ]] && { colour=31; fails=$((fails + 1)); }
  printf '   \033[%sm%-8s\033[0m %-28s %s\n' "$colour" "$1" "$2" "$3"
}

# probe MODE LOG [launcher...]: run the Godot probe project (with --headless when
# HEADLESS is set). Succeeds when the run exits 0 (gamescope exits 0 unless the
# timeout kills it) and prints its marker line.
probe() {
  local mode="$1" log="$2"; shift 2
  timeout 90 "$@" "$GODOT" ${HEADLESS:+"--headless"} --path "$WORK/probe" -- --mode="$mode" --out="$WORK/render.png" --match="$PAD_ID" >"$log" 2>&1 \
    && grep -q "^PROBE $mode ok" "$log"
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

# 4. Virtual Xbox controller seen by Godot. Only an A press from the virtual pad
# counts, so a real controller cannot pass this check. There is no fallback to
# verify here: without it, controller tests drop to the harness input path.
uv run --quiet "$ROOT/tools/pad/virtual_pad.py" --seconds 240 --press a >"$LOG/pad.log" 2>&1 &
pad=$!
for _ in $(seq 1 90); do
  grep -q '^virtual pad up:' "$LOG/pad.log" || ! kill -0 "$pad" 2>/dev/null && break
  sleep 1
done
if ! grep -q '^virtual pad up:' "$LOG/pad.log"; then
  report FAIL "Virtual Xbox controller" "the virtual pad did not start; see $LOG/pad.log"
elif HEADLESS=1 probe joypad "$LOG/joypad-headless.log"; then
  report PASS "Virtual Xbox controller" "$(grep -o 'name=.*' "$LOG/joypad-headless.log")"
elif probe joypad "$LOG/joypad-gamescope.log" "${GS[@]}"; then
  report PASS "Virtual Xbox controller" "$(grep -o 'name=.*' "$LOG/joypad-gamescope.log") (in gamescope only)"
else
  report FAIL "Virtual Xbox controller" "Godot did not read the virtual pad; see $LOG/joypad-*.log"
fi
kill "$pad" 2>/dev/null; wait "$pad" 2>/dev/null

# 5. Windows export boots under Wine
export WINEPREFIX="$CACHE/wine" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml="
mkdir -p "$WORK/win"
if "$GODOT" --headless --path "$WORK/probe" --export-debug "Windows Desktop" "$WORK/win/probe.exe" >"$LOG/win-export.log" 2>&1 \
  && [[ -s "$WORK/win/probe.exe" ]]; then
  if timeout 180 wine "$WORK/win/probe.console.exe" --headless -- --mode=boot >"$LOG/wine.log" 2>&1 \
    && grep -q "^PROBE boot ok" "$LOG/wine.log"; then
    report PASS "Windows export under Wine" "boots headless"
  else
    report FAIL "Windows export under Wine" "export works but Wine cannot boot it; see $LOG/wine.log"
  fi
else
  report FAIL "Windows export under Wine" "export failed; see $LOG/win-export.log"
fi

# 6. Blender MCP: run code, take a window screenshot and search the API docs through
# the official server, against a Blender in a hidden gamescope display.
gamescope --backend headless -W 1600 -H 900 -- "$BLENDER" --online-mode >"$LOG/blender-mcp-ui.log" 2>&1 &
bl=$!
for _ in $(seq 1 60); do (exec 3<>/dev/tcp/127.0.0.1/9876) 2>/dev/null && break; sleep 1; done
if BLENDER_PATH="$BLENDER" timeout 120 uv run --quiet "$ROOT/tools/setup/checks/blender_mcp_check.py" \
  "$HOME/.local/share/orrery/blender_mcp/mcp" >"$LOG/blender-mcp.log" 2>&1 \
  && grep -q '^BLENDER-MCP ok' "$LOG/blender-mcp.log"; then
  report PASS "Blender MCP" "$(grep -o 'blender=.*' "$LOG/blender-mcp.log")"
else
  report FAIL "Blender MCP" "see $LOG/blender-mcp*.log; the plan's fallback is ahujasid/mcp-for-blender"
fi
kill "$bl" 2>/dev/null; wait "$bl" 2>/dev/null

echo
(( fails == 0 )) && echo "   All checks passed or have a working fallback." || echo "   $fails check(s) failed."
exit $(( fails > 0 ))
