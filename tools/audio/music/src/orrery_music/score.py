"""Arrange a hook and the clockwork percussion over a loop, and write it as MIDI.

The loop is cut into 8-bar phrases. The hook plays in every phrase in one of four
settings (`PhraseKind`), so it keeps coming back:

- intro: music box hook over tick-tock eighths.
- lift: celesta with a glockenspiel octave above, trap-style tick rolls at bars 4 and 8.
- break: the hook's first half on music box, then its opening bars echo on glockenspiel,
  over quarter ticks and gear ratchets.
- full: music box, celesta an octave down and a quiet square lead two octaves down.

`arrange` returns the full MIDI (the record of the human-written layer, clockwork on the
drum channel), the melodic-only MIDI that FluidSynth renders, and the clockwork hits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import mido
import numpy as np

from orrery_music.hooks import Hook
from orrery_music.synth import Clock, Hit

PPQ = 480
PhraseKind = Literal["intro", "lift", "break", "full"]

# Part name -> (MIDI channel, GM program, octave shift from the hook, velocity).
PARTS: dict[str, tuple[int, int, int, int]] = {
    "music box": (0, 10, 0, 104),
    "celesta": (1, 8, 0, 96),
    "glockenspiel": (2, 9, 12, 62),
    "celesta low": (3, 8, -12, 80),
    "square lead": (4, 80, -24, 46),
}
_SETTINGS: dict[PhraseKind, tuple[str, ...]] = {
    "intro": ("music box",),
    "lift": ("celesta", "glockenspiel"),
    "break": ("music box",),
    "full": ("music box", "celesta low", "square lead"),
}
_CLOCK_NOTES: dict[Clock, int] = {"tick": 42, "tock": 44, "ratchet": 39}
_CHIME_CHANNEL = 5


def phrase_kinds(phrases: int) -> list[PhraseKind]:
    """intro, lift, break, full, then lift and full alternate (a break every fourth phrase)."""
    base: list[PhraseKind] = ["intro", "lift", "break", "full"]
    kinds = base[:phrases]
    while len(kinds) < phrases:
        kinds.append(
            "break"
            if len(kinds) % 4 == 2
            else ("lift" if len(kinds) % 2 == 0 else "full")
        )
    return kinds


@dataclass(frozen=True)
class Layer:
    full_midi: mido.MidiFile
    melodic_midi: mido.MidiFile
    hits: list[Hit]
    hook_notes: list[
        tuple[float, float, int]
    ]  # (start s, end s, MIDI pitch) of every hook note
    kinds: list[PhraseKind]


def _hook_events(
    hook: Hook, start_beat: float, bars: tuple[int, int]
) -> list[tuple[float, float, int]]:
    """The hook's notes in bars [a, b) of the hook, shifted to `start_beat`, repeating short hooks."""
    a, b = bars
    out: list[tuple[float, float, int]] = []
    for bar in range(a, b):
        hb = bar % hook.bars
        for n in hook.notes:
            if 4 * hb <= n.beat < 4 * hb + 4:
                out.append(
                    (start_beat + 4 * (bar - a) + n.beat - 4 * hb, n.length, n.pitch)
                )
    return out


def arrange(hook: Hook, bars: int, period: float, tonic: int, seed: int = 1) -> Layer:
    """Lay out `bars` bars (a multiple of 8) at `period` seconds per beat with the hook on `tonic`."""
    if bars % 8:
        raise ValueError("loop length must be a whole number of 8-bar phrases")
    rng = np.random.default_rng(seed)
    kinds = phrase_kinds(bars // 8)
    notes: dict[str, list[tuple[float, float, int, int]]] = {p: [] for p in PARTS}
    hits: list[Hit] = []
    chimes: list[tuple[float, int]] = []
    hook_notes: list[tuple[float, float, int]] = []

    def tick(beat: float, sound: Clock, gain: float) -> None:
        hits.append(Hit(beat * period, sound, gain * float(rng.uniform(0.9, 1.0))))

    for p, kind in enumerate(kinds):
        b0 = 32.0 * p
        if kind == "break":
            melody = [(*e, "music box") for e in _hook_events(hook, b0, (0, 4))]
            melody += [
                (*e, "glockenspiel") for e in _hook_events(hook, b0 + 16, (0, 2))
            ]
            melody += [
                (*e, "glockenspiel") for e in _hook_events(hook, b0 + 24, (0, 2))
            ]
        else:
            melody = [
                (*e, part)
                for e in _hook_events(hook, b0, (0, 8))
                for part in _SETTINGS[kind]
            ]
        for beat, length, pitch, part in melody:
            channel, _, shift, vel = PARTS[part]
            v = int(np.clip(vel + rng.integers(-6, 7), 1, 127))
            notes[part].append((beat, length * 0.95, tonic + pitch + shift, v))
            if part in ("music box", "celesta"):
                hook_notes.append(
                    (beat * period, (beat + length) * period, tonic + pitch)
                )
        chimes.append((b0, tonic - 12))
        chimes.append((b0, tonic - 5))
        if kind == "break":
            chimes.append((b0 + 16, tonic - 12))
        for bar in range(8):
            bb = b0 + 4 * bar
            last_of_four = bar % 4 == 3
            if kind == "break":
                for beat in range(4):
                    tick(
                        bb + beat,
                        "tick" if beat % 2 == 0 else "tock",
                        0.7 if beat % 2 == 0 else 0.55,
                    )
                tick(bb + 3.5, "ratchet", 0.5)
                continue
            for e in range(8):
                beat = bb + e / 2
                if kind == "lift" and last_of_four and e >= 6:
                    continue  # the roll below replaces beat 4
                tick(
                    beat, "tick" if e % 2 == 0 else "tock", 0.62 if e % 4 == 0 else 0.42
                )
            if kind == "full":
                tick(bb + 3.75, "tock", 0.3)
            if kind == "lift" and last_of_four:
                step = (
                    1 / 4 if bar == 3 else 1 / 6
                )  # sixteenths, then a triplet roll into the next phrase
                for i in range(round(1 / step)):
                    tick(bb + 3 + i * step, "tick", 0.3 + 0.3 * i * step)
            if bar == 7:
                tick(bb + 3.5, "ratchet", 0.55)

    for beat, pitch in chimes:
        hits.append(Hit(beat * period, "chime", 0.5, pitch))

    tempo = mido.bpm2tempo(60.0 / period)
    full = mido.MidiFile(ticks_per_beat=PPQ)
    melodic = mido.MidiFile(ticks_per_beat=PPQ)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=round(tempo), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    meta.append(
        mido.MetaMessage("track_name", name=f"Orrery {hook.id}, {bars} bars", time=0)
    )
    end_tick = bars * 4 * PPQ
    meta.append(mido.MetaMessage("end_of_track", time=end_tick))
    full.tracks.append(meta)
    melodic.tracks.append(meta.copy())
    for part, part_notes in notes.items():
        if not part_notes:
            continue
        channel, program, _, _ = PARTS[part]
        events = [(0, mido.Message("program_change", channel=channel, program=program))]
        for beat, length, pitch, vel in part_notes:
            events.append(
                (
                    round(beat * PPQ),
                    mido.Message("note_on", channel=channel, note=pitch, velocity=vel),
                )
            )
            events.append(
                (
                    round((beat + length) * PPQ),
                    mido.Message("note_off", channel=channel, note=pitch),
                )
            )
        # A silent controller 3 s after the loop end keeps FluidSynth rendering the release tails.
        tail = end_tick + round(3.0 / period * PPQ)
        events.append(
            (
                tail,
                mido.Message("control_change", channel=channel, control=110, value=0),
            )
        )
        track = _track(part, events)
        full.tracks.append(track)
        melodic.tracks.append(track.copy())
    clock_events: list[tuple[int, mido.Message]] = []
    for hit in hits:
        t = round(hit.time / period * PPQ)
        if hit.sound == "chime":
            msg = mido.Message(
                "note_on",
                channel=_CHIME_CHANNEL,
                note=hit.pitch,
                velocity=int(hit.gain * 127),
            )
            off = mido.Message("note_off", channel=_CHIME_CHANNEL, note=hit.pitch)
        else:
            note = _CLOCK_NOTES[hit.sound]
            msg = mido.Message(
                "note_on", channel=9, note=note, velocity=int(hit.gain * 127)
            )
            off = mido.Message("note_off", channel=9, note=note)
        clock_events += [(t, msg), (t + PPQ // 8, off)]
    full.tracks.append(
        _track("clockwork (synthesised, not rendered by FluidSynth)", clock_events)
    )
    return Layer(full, melodic, hits, sorted(hook_notes), kinds)


def _track(name: str, events: list[tuple[int, mido.Message]]) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=name, time=0))
    now = 0
    # note_off sorts before note_on at the same tick, so repeated notes retrigger cleanly.
    for t, msg in sorted(
        events, key=lambda e: (e[0], e[1].dict()["type"] != "note_off")
    ):
        track.append(msg.copy(time=t - now))
        now = t
    return track
