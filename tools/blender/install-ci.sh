#!/usr/bin/env bash
# Installs the pinned Blender and glTF-Validator (tools/setup/pins.env) on an Ubuntu CI runner:
# the files go to ~/.local/opt and the commands to ~/.local/bin, where `just build-levels`
# finds them. A tool that is already in ~/.local/opt (from the CI cache) is not downloaded again.
# On a dev machine, `just setup` installs the same tools.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
# shellcheck source=../setup/pins.env
source "$ROOT/tools/setup/pins.env"
OPT="$HOME/.local/opt"
BIN="$HOME/.local/bin"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$OPT" "$BIN"

# Libraries that Blender links and the runner image may not have.
sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends \
  libvulkan1 libx11-6 libxi6 libxfixes3 libxrender1 libxkbcommon0 libsm6 libgl1 libegl1 >/dev/null

blender="$OPT/blender-$BLENDER_VERSION"
if [[ ! -x "$blender/blender" ]]; then
  tar="blender-$BLENDER_VERSION-linux-x64.tar.xz"
  for mirror in $BLENDER_MIRRORS; do
    curl -fsSL --retry 3 -o "$TMP/$tar" "$mirror/release/Blender$BLENDER_SERIES/$tar" && break
  done
  echo "$BLENDER_SHA256  $TMP/$tar" | sha256sum -c --quiet -
  tar -xJf "$TMP/$tar" -C "$TMP"
  mv "$TMP/blender-$BLENDER_VERSION-linux-x64" "$blender"
fi
ln -sfn "$blender/blender" "$BIN/blender-$BLENDER_SERIES"

validator="$OPT/gltf_validator-$GLTF_VALIDATOR_VERSION"
if [[ ! -x "$validator/gltf_validator" ]]; then
  tar="gltf_validator-$GLTF_VALIDATOR_VERSION-linux64.tar.xz"
  curl -fsSL --retry 3 -o "$TMP/$tar" \
    "https://github.com/KhronosGroup/glTF-Validator/releases/download/$GLTF_VALIDATOR_VERSION/$tar"
  echo "$GLTF_VALIDATOR_SHA256  $TMP/$tar" | sha256sum -c --quiet -
  mkdir -p "$validator"
  tar -xJf "$TMP/$tar" -C "$validator"
fi
ln -sfn "$validator/gltf_validator" "$BIN/gltf_validator"

"$BIN/blender-$BLENDER_SERIES" --version | sed -n 1p
