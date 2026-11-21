#!/usr/bin/env bash
# Installs every pinned tool for Orrery development on Arch/CachyOS, then runs the
# first-run checks (tools/setup/check.sh). Safe to repeat: each step skips work
# that is already done. Run it through `just setup`. Pins live in pins.env and
# mise.toml. Steps that need Sean are in the pre-setup wizard, not here.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
# shellcheck source=pins.env
source "$ROOT/tools/setup/pins.env"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/orrery"
DL="$CACHE/downloads"
OPT="$HOME/.local/opt"
BIN="$HOME/.local/bin"
COMFYUI_DIR="${COMFYUI_DIR:-$HOME/comfy/ComfyUI}"
UA='Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/140.0'
mkdir -p "$DL" "$OPT" "$BIN"

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
ok()   { printf '   ok    %s\n' "$1"; }
warn() { printf '   WARN  %s\n' "$1"; }
die()  { printf '   FAIL  %s\n' "$1" >&2; exit 1; }

# download DEST URL... : fetch DEST from the first URL that works (cached).
download() {
  local dest="$1"; shift
  [[ -f "$dest" ]] && return 0
  local url
  for url in "$@"; do
    curl -fsSL --retry 3 -A "$UA" -o "$dest.part" "$url" && { mv "$dest.part" "$dest"; return 0; }
  done
  rm -f "$dest.part"; die "download failed: $*"
}

# verify FILE SUM ALGO: checksum check; deletes the file on mismatch.
verify() {
  [[ -n "$2" ]] || die "no pinned checksum for $1 (sha: $("${3}sum" "$1" | cut -d' ' -f1))"
  echo "$2  $1" | "${3}sum" -c --quiet - || { rm -f "$1"; die "checksum mismatch: $1"; }
}

# hf_gate_open REPO: true when the hf CLI's account may download gated REPO.
hf_gate_open() {
  local tokfile="${HF_HOME:-$HOME/.cache/huggingface}/token" tok="${HF_TOKEN:-}" code
  [[ -z "$tok" && -r "$tokfile" ]] && tok=$(<"$tokfile")
  # Probe the weights the gate protects (README files stay open on gated repos).
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 15 -I -L \
    -H @<(printf 'Authorization: Bearer %s\n' "$tok") \
    "https://huggingface.co/$1/resolve/main/model.safetensors" || true)
  [[ "$code" == 200 ]]
}

step "System packages"
pkgs=(mise git-lfs gamescope wine evtest shellcheck unzip)
missing=()
for p in "${pkgs[@]}"; do pacman -Q "$p" >/dev/null 2>&1 || missing+=("$p"); done
(( ${#missing[@]} )) && sudo pacman -S --needed --noconfirm "${missing[@]}"
ok "${pkgs[*]}"
if pacman -Q xpadneo-dkms >/dev/null 2>&1 || sudo pacman -S --needed --noconfirm xpadneo-dkms >/dev/null 2>&1; then
  ok "xpadneo-dkms (Xbox controller over Bluetooth)"
else
  warn "xpadneo-dkms is not in your repos; install it from the AUR for Bluetooth controllers"
fi
git lfs install >/dev/null && ok "git lfs"

step "Godot (mise)"
(cd "$ROOT" && mise trust -q && mise install -q)
GODOT=$(cd "$ROOT" && mise which godot)
gver=$("$GODOT" --version | head -1)               # e.g. 4.7.2.stable.official.<hash>
gnum=${gver%%.stable*}                             # 4.7.2 (or 4.8 for a release with no patch number)
tdir="${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/$gnum.stable"
ok "godot $gver"
if [[ ! -f "$tdir/version.txt" ]]; then
  gtag="$gnum-stable"
  tpz="$DL/Godot_v${gtag}_export_templates.tpz"
  download "$tpz" "https://github.com/godotengine/godot/releases/download/$gtag/Godot_v${gtag}_export_templates.tpz"
  verify "$tpz" "$GODOT_TEMPLATES_SHA512" sha512
  # Unpack beside the target, then rename: an interrupted install never looks complete.
  rm -rf "$tdir.partial"
  mkdir -p "$tdir.partial"
  unzip -q "$tpz" -d "$tdir.partial"
  rm -rf "$tdir"
  mv "$tdir.partial/templates" "$tdir"
  rm -rf "$tdir.partial" "$tpz"
fi
ok "export templates in $tdir"

step "Blender $BLENDER_VERSION"
bdir="$OPT/blender-$BLENDER_VERSION"
if [[ ! -x "$bdir/blender" ]]; then
  tar="blender-$BLENDER_VERSION-linux-x64.tar.xz"
  urls=(); for m in $BLENDER_MIRRORS; do urls+=("$m/release/Blender$BLENDER_SERIES/$tar"); done
  download "$DL/$tar" "${urls[@]}"
  verify "$DL/$tar" "$BLENDER_SHA256" sha256
  rm -rf "$bdir" "$OPT/blender-$BLENDER_VERSION-linux-x64"   # clear a partial install
  tar -xJf "$DL/$tar" -C "$OPT"
  mv "$OPT/blender-$BLENDER_VERSION-linux-x64" "$bdir"
  rm -f "$DL/$tar"
fi
ln -sfn "$bdir/blender" "$BIN/blender-$BLENDER_SERIES"
"$BIN/blender-$BLENDER_SERIES" --version 2>/dev/null | grep -q "^Blender $BLENDER_VERSION" || die "blender-$BLENDER_SERIES does not report $BLENDER_VERSION"
ok "blender-$BLENDER_SERIES -> $bdir"

step "Blender MCP (official Blender Lab)"
mdir="$HOME/.local/share/orrery/blender_mcp"
[[ -d "$mdir/.git" ]] || git clone -q "$BLENDER_MCP_REPO" "$mdir"
if [[ "$(cat "$mdir/.orrery-installed" 2>/dev/null)" != "$BLENDER_MCP_COMMIT" ]]; then
  git -C "$mdir" fetch -q origin
  git -C "$mdir" checkout -q "$BLENDER_MCP_COMMIT"
  zdir=$(mktemp -d)
  "$BIN/blender-$BLENDER_SERIES" --command extension build --source-dir "$mdir/addon/blender_mcp_addon" --output-dir "$zdir" >/dev/null
  "$BIN/blender-$BLENDER_SERIES" --command extension install-file -r user_default --enable "$zdir"/*.zip >/dev/null
  rm -rf "$zdir"
  (cd "$mdir/mcp" && uv sync -q)
  echo "$BLENDER_MCP_COMMIT" >"$mdir/.orrery-installed"
fi
ok "blender_mcp ${BLENDER_MCP_COMMIT:0:7}, add-on enabled in Blender $BLENDER_SERIES"

step "glTF tools"
vdir="$OPT/gltf_validator-$GLTF_VALIDATOR_VERSION"
if [[ ! -x "$vdir/gltf_validator" ]]; then
  f="gltf_validator-$GLTF_VALIDATOR_VERSION-linux64.tar.xz"
  download "$DL/$f" "https://github.com/KhronosGroup/glTF-Validator/releases/download/$GLTF_VALIDATOR_VERSION/$f"
  verify "$DL/$f" "$GLTF_VALIDATOR_SHA256" sha256
  rm -rf "$vdir.partial"
  mkdir -p "$vdir.partial"
  tar -xJf "$DL/$f" -C "$vdir.partial"
  [[ -x "$vdir.partial/gltf_validator" ]] || die "$f has no gltf_validator"
  rm -rf "$vdir"
  mv "$vdir.partial" "$vdir"
  rm -f "$DL/$f"
fi
ln -sfn "$vdir/gltf_validator" "$BIN/gltf_validator"
ok "gltf_validator $GLTF_VALIDATOR_VERSION"
bunx "@gltf-transform/cli@$GLTF_TRANSFORM_VERSION" --version >/dev/null
ok "gltf-transform $GLTF_TRANSFORM_VERSION (bunx)"
uvx --from "gdtoolkit==$GDTOOLKIT_VERSION" gdlint --version >/dev/null
ok "gdtoolkit $GDTOOLKIT_VERSION (uvx)"

step "ComfyUI music models"
if [[ ! -d "$COMFYUI_DIR/models" ]]; then
  warn "ComfyUI not found at $COMFYUI_DIR (set COMFYUI_DIR); skipping music models"
else
  while read -r repo file sub gate; do
    [[ -z "$repo" || "$repo" == \#* ]] && continue
    name=$(basename "$file")
    link="$COMFYUI_DIR/models/$sub/$name"
    if [[ -e "$link" && ! -L "$link" ]]; then
      warn "$sub/$name is a real file, not a setup link; leaving it alone"
      continue
    fi
    if [[ -n "${gate:-}" ]] && ! hf_gate_open "$gate"; then
      warn "$name waits for the license: accept it at https://huggingface.co/$gate, then rerun just setup"
      continue
    fi
    path=$(hf download "$repo" "$file" --quiet)
    mkdir -p "$COMFYUI_DIR/models/$sub"
    ln -sfn "$path" "$link"
    ok "$sub/$name"
  done < "$ROOT/tools/setup/comfy-models.txt"
fi

step "First-run checks"
exec "$ROOT/tools/setup/check.sh"
