# Audio design

Status: built in #25. It follows `docs/plan.md` §2.12 and §4.8. Where this file and the plan differ, the plan wins.

Terms used in this file:

- **Group:** a folder `game/audio/music/<group>/` of music tracks that play together.
- **Sound:** one sound-effect file `game/audio/sfx/<sound>.ogg`.

## 1. Files

| Path | What it is |
|---|---|
| `game/audio/default_bus_layout.tres` | The buses Master, Music, SFX and UI. Music, SFX and UI send to Master. A hard limiter on Master (ceiling -0.5 dB) stops clipping. `project.godot` names this file in `audio/buses/default_bus_layout`. |
| `game/audio/audio_buses.gd` | `AudioBuses`: the bus names and the volume accessors. |
| `game/audio/music.gd` | The autoload `Music`: music groups, Ascent zones, menu sounds. It owns the `SfxPlayer`. |
| `game/audio/sfx_player.gd` | `SfxPlayer`: plays the sounds of one `LevelRun`. |
| `game/audio/sfx/` | The sounds, made by `tools/audio/sfx/synth_sfx.py`. They are small (about 220 KB in total), so git keeps them, not LFS. |
| `game/audio/music/` | The music groups. It is empty until the real tracks are imported. |
| `game/test/audio/loops/` | Two placeholder loops for the music tests (120 BPM, 4/4, 2 bars). |

## 2. Volumes

`Settings` (#21) stores the four volumes as linear values 0..1: `master_volume`, `music_volume`, `sfx_volume` and `ui_volume`. 0 is silent. At start, `Music` calls `AudioBuses.apply(Save.settings)`, which sets every bus. The settings menu (#23) reads `AudioBuses.volume(bus) -> float` and writes `AudioBuses.set_volume(bus, value, Save.settings)`, which sets the bus and the settings var. Then it calls `Save.write()` to keep the change. Use the constants `AudioBuses.MASTER`, `MUSIC`, `SFX` and `UI`.

## 3. Music

- **Which group plays:** a run plays the group in its level's `music` field. If that field is empty, it plays the group of the level's tier (`beginner`, `intermediate`, ...). With no run (the title and the menus), the group `title` plays. `Music` follows `Game.run` (when `Game` adds a run, and each frame for a change to null), so `Game` does not call it.
- **A normal group** plays as an `AudioStreamPlaylist`: shuffled, looped, with a 2 s fade from track to track (`Music.PLAYLIST_FADE`). The playlist moves to the next track after `beat_count` beats of the track, or at the end of the file when `beat_count` is 0.
- **The group `ascent`** plays as one `AudioStreamInteractive`. Each track is a clip, in file name order. `Music.set_zone(zone)` changes to clip `zone` (0 is the first; a larger zone keeps the last clip). The change waits for the next bar line of the playing track, then cross-fades over 4 beats into the start of the new track. The Ascent mode (#27) calls `set_zone` when the marble enters a zone.
- **A change of group** cross-fades over 1.5 s (`Music.FADE`). A group with no tracks fades out to silence.
- **Menu sounds:** `Music.play_ui(&"move")`, `&"select"` or `&"back"` plays on the UI bus.
- **Pause:** music plays on in pause. The sound effects pause with the game.

The API: `Music.play_group(group)`, `Music.play(stream)` (null fades out), `Music.set_zone(zone)`, `Music.play_ui(sound)`, `Music.group_of(run)`, `Music.load_tracks(dir)`, `Music.playlist(tracks)` and `Music.zones(tracks)`. `Music.group` is the group that plays now, and `Music.sfx` is the `SfxPlayer`.

## 4. Add a real track

1. Export the track as OGG Vorbis (quality 5 to 7), 44.1 or 48 kHz. Cut it on a bar line, so that it loops from its end to its start. The music pipeline (`tools/audio/music/`, §4.9 of the plan) checks the tempo, the loudness and the loop seam.
2. Put the file in `game/audio/music/<group>/`, for example `game/audio/music/beginner/brass_gears.ogg`. Ascent tracks go in `game/audio/music/ascent/`. Their file names set the zone order, so start them with `1_`, `2_`, `3_`.
3. Run `just import`. Godot writes `<file>.ogg.import` beside the track.
4. In that `.import` file, set these values in `[params]`, then run `just import` again:

   ```ini
   loop=true
   loop_offset=0      ; s where the loop starts again; 0 loops the whole file
   bpm=96             ; the tempo of the track
   beat_count=192     ; the beats in the loop: bars x beats per bar
   bar_beats=4        ; beats per bar
   ```

   `bpm`, `beat_count` and `bar_beats` give the bar lines for the Ascent changes and the track length for the playlists. Use whole bars: `beat_count` is a multiple of `bar_beats`.
5. Commit the `.ogg` and the `.ogg.import`, and add a row to `docs/licenses.md` (plan §4.9, step 5).

## 5. Sound effects

`SfxPlayer` connects to `LevelRun.feedback`. `SfxPlayer.SOUNDS` maps each feedback kind to a sound. A kind that is not a key falls back to its `<type>.` key, then to its `.<event>` key. A kind with no match plays nothing. So a new power-up `x.use` plays `powerup_use` before it gets its own sound.

| Feedback kind or state change | Sound | Where it plays |
|---|---|---|
| `marble.jump` | `jump` | flat |
| `marble.land`, strength under 0.6 | `land_soft` | flat |
| `marble.land`, strength 0.6 and more | `land_hard` | flat |
| `marble.bounce` | `bounce` | flat |
| `bumper.hit` | `bumper` | at the event |
| `steam_vent.blow` | `steam_vent` | at the event |
| `pendulum.hit` | `pendulum` | at the event |
| `trapdoor.*` | `trapdoor` | at the event |
| `tile.fall` | `tile_fall` | at the event |
| `tile.*` (for example `tile.crack`) | `tile_crack` | at the event |
| `gem.collect` | `gem` | flat |
| `egg.open` | `egg` | flat |
| `checkpoint.reach` | `checkpoint` | flat |
| `finish.open` | `finish_open` | flat |
| `finish.reach` | `finish_reach` | flat |
| `*.pickup` (for example `coil_spring.pickup`) | `powerup_pickup` | flat |
| `*.use` (for example `coil_spring.use`) | `powerup_use` | flat |
| status `respawning` to `playing`, or a restart | `respawn` | flat |
| the marble rolls on the ground | `roll` (loop) | flat |

- **Strength:** the strength 0..1 sets the volume (35 % to 100 %, linear) and the pitch (0.94 to 1.06, with ±3 % random change).
- **Voices:** each sound has 3 players of one voice each, used in turn, so each voice keeps its own volume, pitch and position. A sound does not start again within 4 ticks of its last start. A change of run stops every sound of the last run.
- **Roll:** the loop always plays while a run is attached. Its volume follows the rolling speed (spin × radius, over the top rolling speed) while the marble is on the ground. It is silent in the air. Its pitch goes from 0.7 to 1.4 with the speed.

### Make the sounds

`uv run --script tools/audio/sfx/synth_sfx.py` writes every sound and the placeholder loops, and checks each file: no clipping (peak under -1 dBFS), loudness in -30..-9 dBFS, a start within 15 ms, no cut-off end, and the length. `--montage <file.ogg>` also writes all sounds into one file to listen to. The sounds use no samples, so `docs/licenses.md` has no sample rows. To use a CC0 sample layer later, add its row there first.
