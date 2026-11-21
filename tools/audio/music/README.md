# Music pipeline (ticket #26)

Makes loop candidates for Orrery's music: an AI backing take, our own hook and clockwork
layer on top, checks, and a review page. `docs/plan.md` 2.12 is the style brief and 4.9
the pipeline.

## Commands

Run from this folder. ComfyUI must be up at `http://127.0.0.1:8188` with the ACE-Step 1.5
XL turbo and Stable Audio 3 Medium files from `tools/setup/comfy-models.txt`.

```sh
# Once: the GeneralUser GS soundfont (licence in docs/licenses.md)
mkdir -p out/sf && curl -L -o out/sf/GeneralUser-GS.sf2 \
  https://github.com/mrbumpy409/GeneralUser-GS/raw/main/GeneralUser-GS.sf2

uv run orrery-music generate          # backing takes, one ComfyUI job at a time
uv run orrery-music build             # analyse, mix, check, keep 3-5 per track
uv run orrery-music review            # review/index.html
uv run orrery-music all --track title # all three steps for one track
uv run pytest
```

System tools: `fluidsynth`, `ffmpeg`, `oggenc` (vorbis-tools).

## What each step does

1. **Generate** (`brief.py`, `comfy.py`, `generate.py`). Prompts come from the style brief
   and never name an artist or a song. ACE-Step takes are full instrumental arrangements;
   Stable Audio 3 takes are instrumental beds. Each take is `out/takes/<track>/<id>.flac`
   with a JSON record: model, prompt, seed, settings and the exact ComfyUI workflow.
2. **Layer** (`hooks.py`, `score.py`, `synth.py`). Each track has two original hooks,
   written note by note. `score.py` lays the hook over 8-bar phrases (intro, lift, break,
   full) with clock-tick hats, gear ratchets and chimes, and writes MIDI. FluidSynth
   renders the music box, celesta, glockenspiel and square lead; the clockwork one-shots are
   synthesised in numpy, so they need no sample licence.
3. **Fit and mix** (`build.py`). The take's beat grid, downbeat and key are detected, the
   hook is moved to the key that fits the take's harmony best, and the layer is aligned to
   the take's own attacks. The loop is cut on bar lines where the bars around the end match
   the bars around the start, with an 80 ms cross-fade baked into the head.
4. **Master and check** (`master.py`). -16 LUFS integrated, -1 dBTP (reasons in
   `master.py`). The final OGG is decoded again and checked for length (1:30-2:30), tempo,
   loudness, clipping, silence and the loop seam. Take-level proxies reject clipping,
   silence, drifting tempo and mushy drums; hook-level proxies reject a hook that clashes
   with the bed or sits under it.
5. **Review** (`review.py`). `out/review/index.html` plays the kept candidates.

## Outputs

| Path | Committed | What |
|---|---|---|
| `out/` | no | takes, work files, full candidate OGGs and the review page with 20 s previews |
| `out/midi/<candidate>.mid` | no | the written layer of every kept candidate |
| `midi/<candidate>.mid` | yes | the written layer of each shipped track, copied from `out/midi/` when Sean picks it |
| `manifest/<track>.json` | yes | prompts, seeds, settings, metrics and every rejection |

The full OGGs carry Vorbis comments `BPM`, `BEATS`, `BAR_BEATS`, `LOOPSTART=0` and
`LOOPLENGTH` (samples) for the Godot import (#25): the whole file is the loop, so
`loop_offset` is 0.

## Ship a pick

1. Copy `out/candidates/<track>/<id>.ogg` to `game/audio/music/<group>/<name>.ogg` and
   follow `docs/design/audio.md` §4. Its `BPM` and `BEATS` comments give `bpm` and
   `beat_count`; round `bpm` up in the last decimal, so `beat_count` beats never run past
   the end of the file.
2. Copy `out/midi/<id>.mid` to `midi/`.
3. Add the track's row (prompt, seed, written layer) to `docs/licenses.md`.

Shipped so far: title `title-ace-03-a` (Wind-up), Beginner `beginner-ace-07-a` (Roll
call), Ascent zone 1 `ascent-ace-06-a` (Spiral stair).
