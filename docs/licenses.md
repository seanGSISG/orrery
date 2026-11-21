# Licenses

Every third-party asset, sample, font, add-on and AI model in Orrery. Each line gives the source, the license and where we use it.

| Item | Source | License | Used in |
|---|---|---|---|
| GUT 9.7.1 (Godot Unit Test) | Tag archive `https://github.com/bitwes/Gut/archive/refs/tags/v9.7.1.tar.gz` (SHA-256 `6da99c4e9228d9bec3fb4bd1730a487770a989f0f511dac82a2897a964613385`), vendored unchanged | MIT (`game/addons/gut/LICENSE.md`). Its bundled fonts (Anonymous Pro, Courier Prime, Lobster Two) are SIL OFL 1.1 fonts; `game/addons/gut/fonts/OFL.txt` holds the license text | `game/addons/gut/`: the unit-test runner. Release exports leave it out |
| Sound effects and placeholder music loops | Our own work: `tools/audio/sfx/synth_sfx.py` synthesises them from sines and noise. No samples. The script runs with numpy (BSD-3-Clause) and soundfile (BSD-3-Clause, with libsndfile, LGPL-2.1), which are build tools only and do not ship | Ours | `game/audio/sfx/`; `game/test/audio/loops/` (tests only) |
| Scuffed Cement, PBR texture, 2K | [Poly Haven](https://polyhaven.com/a/scuffed_cement). The normal map is the PNG download, reduced to 8 bits | CC0 1.0 | `assets/textures/stone/`; the limestone of material set A (`game/materials/a/`) |
| Concrete Wall 008, PBR texture, 2K | [Poly Haven](https://polyhaven.com/a/concrete_wall_008) | CC0 1.0 | `assets/textures/stone/`; the limestone of material set B (`game/materials/b/`) |
| Dirty Concrete, PBR texture, 2K | [Poly Haven](https://polyhaven.com/a/dirty_concrete) | CC0 1.0 | `assets/textures/stone/`; the stone of material set C (`game/materials/c/`) |
| Metal007, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Metal007). The normal map is from the PNG download, reduced to 8 bits | CC0 1.0 | `assets/textures/metal/`; the aged brass of material set A |
| Metal008, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Metal008) | CC0 1.0 | `assets/textures/metal/`; the dark bronze of material set C |
| Metal048A, PBR texture, 2K | [ambientCG](https://ambientcg.com/a/Metal048A) | CC0 1.0 | `assets/textures/metal/`; the gold (`game/materials/gold.tres`) and the satin brass of material set B |
| Syferfontein 6d Clear (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/syferfontein_6d_clear_puresky) | CC0 1.0 | `assets/textures/sky/`; the source of the dawn sky (`tools/blender/bake_skies.py`) |
| Qwantani Dusk 2 (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/qwantani_dusk_2_puresky) | CC0 1.0 | `assets/textures/sky/`; the source of the dawn sky of look B (`bake_skies.py --look b`). Not in the game |
| Syferfontein 1d Clear (Pure Sky), HDRI sky, 2K | [Poly Haven](https://polyhaven.com/a/syferfontein_1d_clear_puresky) | CC0 1.0 | `assets/textures/sky/`; the source of the dawn sky of look C (`bake_skies.py --look c`). Not in the game |
| Cassini cylindrical map of Jupiter, PIA07782 | [NASA Photojournal](https://photojournal.jpl.nasa.gov/catalog/PIA07782), file from `assets.science.nasa.gov`. Credit: NASA/JPL/Space Science Institute | Public domain (NASA) | `assets/textures/planet/`; the planet of the dusk sky, with colour and contrast turned down |
| Tier skies: dawn, noon, dusk (4096×2048 HDR) | Our own renders: `tools/blender/bake_skies.py` path-traces them in Blender Cycles from the sky sources above, Blender's sky model and our own cloud and star shaders | Ours | `game/skies/` |
