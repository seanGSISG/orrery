# Licenses

Every third-party asset, sample, font, add-on and AI model in Orrery. Each line gives the source, the license and where we use it.

| Item | Source | License | Used in |
|---|---|---|---|
| GUT 9.7.1 (Godot Unit Test) | Tag archive `https://github.com/bitwes/Gut/archive/refs/tags/v9.7.1.tar.gz` (SHA-256 `6da99c4e9228d9bec3fb4bd1730a487770a989f0f511dac82a2897a964613385`), vendored unchanged | MIT (`game/addons/gut/LICENSE.md`). Its bundled fonts (Anonymous Pro, Courier Prime, Lobster Two) are SIL OFL 1.1 fonts; `game/addons/gut/fonts/OFL.txt` holds the license text | `game/addons/gut/`: the unit-test runner. Release exports leave it out |
| Sound effects and placeholder music loops | Our own work: `tools/audio/sfx/synth_sfx.py` synthesises them from sines and noise. No samples. The script runs with numpy (BSD-3-Clause) and soundfile (BSD-3-Clause, with libsndfile, LGPL-2.1), which are build tools only and do not ship | Ours | `game/audio/sfx/`; `game/test/audio/loops/` (tests only) |
| Instrument Serif (Regular, Italic) | `https://github.com/google/fonts/tree/main/ofl/instrumentserif`, unchanged. SHA-256: Regular `498efd461f6ddfcb7a111bf9a565709d2085d48201d501ead960d93e84ffbb88`, Italic `08939b8bdf534afec24ae0ef5e03f948940cd9a8fe08e7fecbad040e62327385`. Copyright 2022 The Instrument Serif Project Authors | SIL OFL 1.1 (`game/ui/fonts/InstrumentSerif-OFL.txt`) | `game/ui/fonts/`: titles, level names and menu items |
| IBM Plex Mono (Regular, Medium) | `https://github.com/google/fonts/tree/main/ofl/ibmplexmono`, unchanged. SHA-256: Regular `6a3412f058c7d8dfd9170c41e85ade48e5156ecb89356110ca57a0a27734af46`, Medium `a9b4c49bb299e05b5f6c481e7fb5e78943d2793249a0c8874ab574a2d1ea6755`. Copyright 2017 IBM Corp., with Reserved Font Name "Plex" | SIL OFL 1.1 (`game/ui/fonts/IBMPlexMono-OFL.txt`) | `game/ui/fonts/`: numbers, small labels and button glyphs of the HUD and the menus |
