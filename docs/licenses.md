# Licenses

Every third-party asset, sample, font, add-on and AI model in Orrery. Each line gives the source, the license and where we use it.

| Item | Source | License | Used in |
|---|---|---|---|
| GUT 9.7.1 (Godot Unit Test) | Tag archive `https://github.com/bitwes/Gut/archive/refs/tags/v9.7.1.tar.gz` (SHA-256 `6da99c4e9228d9bec3fb4bd1730a487770a989f0f511dac82a2897a964613385`), vendored unchanged | MIT (`game/addons/gut/LICENSE.md`). Its bundled fonts (Anonymous Pro, Courier Prime, Lobster Two) are SIL OFL 1.1 fonts; `game/addons/gut/fonts/OFL.txt` holds the license text | `game/addons/gut/`: the unit-test runner. Release exports leave it out |
| Sound effects and placeholder music loops | Our own work: `tools/audio/sfx/synth_sfx.py` synthesises them from sines and noise. No samples. The script runs with numpy (BSD-3-Clause) and soundfile (BSD-3-Clause, with libsndfile, LGPL-2.1), which are build tools only and do not ship | Ours | `game/audio/sfx/`; `game/test/audio/loops/` (tests only) |
