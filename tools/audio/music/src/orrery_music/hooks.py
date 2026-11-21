"""The authored hooks: original 4-8 bar melodies, one or two per track.

Agents wrote every note here by hand (the human-written layer for the copyright record in
`docs/licenses.md`). Pitches are semitones above the track's tonic, so a hook follows the
key that the analysis detects in a backing take. Beats count from the first beat of the
hook in 4/4. `check_hook` holds the rules a hook must pass before it is used.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Literal

Mode = Literal["major", "minor"]


@dataclass(frozen=True)
class Note:
    beat: float
    length: float
    pitch: int  # semitones above the tonic


@dataclass(frozen=True)
class Hook:
    id: str
    name: str
    mode: Mode
    bars: int
    notes: tuple[Note, ...]
    why_catchy: str


def _n(*spec: tuple[float, float, int]) -> tuple[Note, ...]:
    return tuple(Note(b, length, p) for b, length, p in spec)


# Major scale degrees: do 0, re 2, mi 4, sol 7, la 9, do' 12, re' 14, mi' 16, sol' 19, la' 21.
_TITLE_A_CALL = (
    (0, 0.5, 7),
    (0.5, 0.5, 12),
    (1, 0.25, 14),
    (1.25, 0.75, 16),
    (2.5, 0.5, 14),
    (3, 1, 12),
)

TITLE_A = Hook(
    id="title-a",
    name="Wind-up",
    mode="major",
    bars=8,
    notes=_n(
        *_TITLE_A_CALL,
        (4, 0.5, 9),
        (4.5, 0.5, 12),
        (5, 0.25, 14),
        (5.25, 0.75, 16),
        (6.5, 0.5, 19),
        (7, 1, 16),
        *((b + 8, n, p) for b, n, p in _TITLE_A_CALL),
        (12, 0.5, 14),
        (12.5, 0.5, 12),
        (13, 0.5, 9),
        (13.5, 1.5, 7),
        *((b + 16, n, p) for b, n, p in _TITLE_A_CALL),
        (20, 0.5, 9),
        (20.5, 0.5, 12),
        (21, 0.25, 14),
        (21.25, 0.75, 16),
        (22.5, 0.5, 19),
        (23, 1, 16),
        (24, 0.5, 9),
        (24.5, 0.5, 12),
        (25, 0.25, 14),
        (25.25, 0.75, 16),
        (26, 0.5, 14),
        (26.5, 0.5, 12),
        (27, 0.5, 9),
        (27.5, 0.5, 14),
        (28, 3, 12),
    ),
    why_catchy="A rising sol-do-re-mi pickup with a 16th-note hiccup, answered one step higher, then resolved home: a call and response on five notes.",
)

_TITLE_B_HALF = (
    (0, 0.75, 16),
    (0.75, 0.75, 14),
    (1.5, 0.5, 12),
    (2, 0.5, 14),
    (2.5, 0.5, 16),
)

TITLE_B = Hook(
    id="title-b",
    name="Planet song",
    mode="major",
    bars=4,
    notes=_n(
        *_TITLE_B_HALF,
        (3, 0.5, 19),
        (3.5, 0.5, 16),
        (4, 0.75, 14),
        (4.75, 0.75, 12),
        (5.5, 0.5, 9),
        (6, 1.5, 12),
        *((b + 8, n, p) for b, n, p in _TITLE_B_HALF),
        (11, 0.5, 21),
        (11.5, 0.5, 19),
        (12, 0.5, 16),
        (12.5, 0.5, 14),
        (13, 2, 12),
    ),
    why_catchy="A 3-3-2 dotted-eighth bounce that falls mi-re-do, then climbs to a new top note on the repeat: easy to hum after one loop.",
)

# Minor scale degrees: do 0, re 2, me 3, fa 5, sol 7, le 8, te 10, do' 12, re' 14, me' 15, fa' 17, sol' 19.
_BEG_A_BAR0 = (
    (0, 0.25, 12),
    (0.5, 0.25, 12),
    (0.75, 0.25, 10),
    (1, 0.5, 12),
    (1.75, 0.75, 7),
    (2.75, 0.25, 3),
    (3, 0.5, 5),
    (3.5, 0.5, 7),
)
_BEG_A_BAR1 = (
    (4, 0.5, 10),
    (4.5, 0.25, 7),
    (4.75, 0.75, 5),
    (5.5, 0.5, 3),
    (6, 1, 0),
    (7, 0.25, 5),
    (7.25, 0.25, 3),
    (7.5, 0.5, 0),
)

BEGINNER_A = Hook(
    id="beginner-a",
    name="Roll call",
    mode="minor",
    bars=8,
    notes=_n(
        *_BEG_A_BAR0,
        *_BEG_A_BAR1,
        *((b + 8, n, p) for b, n, p in _BEG_A_BAR0),
        (12, 0.5, 10),
        (12.5, 0.25, 12),
        (12.75, 0.75, 15),
        (13.5, 0.5, 12),
        (14, 0.5, 10),
        (14.5, 1.5, 7),
        *((b + 16, n, p) for b, n, p in _BEG_A_BAR0),
        *((b + 16, n, p) for b, n, p in _BEG_A_BAR1),
        *((b + 24, n, p) for b, n, p in _BEG_A_BAR0),
        (28, 0.5, 10),
        (28.5, 0.25, 12),
        (28.75, 0.75, 15),
        (29.5, 0.5, 17),
        (30, 0.25, 15),
        (30.25, 1.75, 12),
    ),
    why_catchy="A funky double-tap on the top note that tumbles down five notes in 16ths, repeated four times with a lift to the top on bar 8.",
)

_BEG_B_BAR0 = (
    (0, 0.5, 0),
    (0.5, 0.5, 12),
    (1, 0.5, 10),
    (1.5, 0.5, 7),
    (2, 0.25, 5),
    (2.25, 0.5, 7),
    (2.75, 0.75, 10),
)

BEGINNER_B = Hook(
    id="beginner-b",
    name="Marble bounce",
    mode="minor",
    bars=4,
    notes=_n(
        *_BEG_B_BAR0,
        (3.5, 0.5, 12),
        (4, 1.5, 7),
        (5.5, 0.25, 5),
        (5.75, 0.25, 3),
        (6, 1, 0),
        *((b + 8, n, p) for b, n, p in _BEG_B_BAR0),
        (11.5, 0.5, 15),
        (12, 1.5, 12),
        (13.5, 0.5, 10),
        (14, 2, 7),
    ),
    why_catchy="An octave jump like a bounce, then a slide back down; the repeat lands one note higher, so the four bars ask and answer.",
)

_ASC_A_RISE = (
    (0, 0.5, 0),
    (0.5, 0.5, 7),
    (1, 1, 12),
    (2, 0.5, 10),
    (2.5, 0.5, 12),
    (3, 1, 14),
)

ASCENT_A = Hook(
    id="ascent-a",
    name="Spiral stair",
    mode="minor",
    bars=8,
    notes=_n(
        *_ASC_A_RISE,
        (4, 1.5, 15),
        (5.5, 0.5, 14),
        (6, 2, 12),
        (8, 0.5, 3),
        (8.5, 0.5, 10),
        (9, 1, 15),
        (10, 0.5, 14),
        (10.5, 0.5, 15),
        (11, 1, 17),
        (12, 1.5, 19),
        (13.5, 0.5, 17),
        (14, 2, 15),
        *((b + 16, n, p) for b, n, p in _ASC_A_RISE),
        (20, 1.5, 15),
        (21.5, 0.5, 14),
        (22, 2, 12),
        (24, 0.5, 8),
        (24.5, 0.5, 12),
        (25, 1, 15),
        (26, 0.5, 14),
        (26.5, 0.5, 12),
        (27, 1, 10),
        (28, 4, 12),
    ),
    why_catchy="Open fifths that climb like a staircase, the same rising figure sequenced up a third, so the melody itself sounds like the climb.",
)

ASCENT_B = Hook(
    id="ascent-b",
    name="Lantern",
    mode="minor",
    bars=4,
    notes=_n(
        (0, 1.5, 7),
        (1.5, 0.5, 12),
        (2, 1, 14),
        (3, 1, 15),
        (4, 1.5, 14),
        (5.5, 0.5, 10),
        (6, 2, 12),
        (8, 1.5, 7),
        (9.5, 0.5, 12),
        (10, 1, 14),
        (11, 1, 19),
        (12, 1, 17),
        (13, 1, 15),
        (14, 0.5, 14),
        (14.5, 1.5, 12),
    ),
    why_catchy="A slow sol-do-re-me call that answers itself, and on the repeat leaps to the high sol before it settles: broad and singable at a slow tempo.",
)

HOOKS: dict[str, Hook] = {
    h.id: h for h in (TITLE_A, TITLE_B, BEGINNER_A, BEGINNER_B, ASCENT_A, ASCENT_B)
}

_STABLE = {"major": {0, 4, 7}, "minor": {0, 3, 7}}
_SCALE = {"major": {0, 2, 4, 5, 7, 9, 11}, "minor": {0, 2, 3, 5, 7, 8, 10}}


def check_hook(hook: Hook) -> list[str]:
    """Return the rules the hook breaks (empty when it is good to use).

    A hook spans 4-8 bars, stays in its scale, keeps a range of at most an octave and a
    sixth, has no overlapping notes, brings back the rhythm of its opening bar (the motif
    that makes it stick) and ends long on a stable note (do, mi/me or sol).
    """
    errors: list[str] = []
    notes = sorted(hook.notes, key=lambda n: n.beat)
    if not 4 <= hook.bars <= 8:
        errors.append(f"{hook.bars} bars, want 4-8")
    if not notes:
        return [*errors, "no notes"]
    if notes[-1].beat + notes[-1].length > hook.bars * 4 + 1e-6:
        errors.append("notes run past the last bar")
    off_scale = sorted({n.pitch % 12 for n in notes} - _SCALE[hook.mode])
    if off_scale:
        errors.append(f"off-scale pitches {off_scale}")
    pitches = [n.pitch for n in notes]
    if max(pitches) - min(pitches) > 21:
        errors.append(f"range {max(pitches) - min(pitches)} semitones, want <= 21")
    for a, b in itertools.pairwise(notes):
        if a.beat + a.length > b.beat + 1e-6:
            errors.append(f"notes overlap at beat {b.beat}")
    first_bar = [n.beat for n in notes if n.beat < 4]
    repeats = any(
        [n.beat - 4 * bar for n in notes if 4 * bar <= n.beat < 4 * bar + 4]
        == first_bar
        for bar in range(1, hook.bars)
    )
    if not repeats:
        errors.append("the rhythm of the opening bar never comes back")
    last = notes[-1]
    if last.pitch % 12 not in _STABLE[hook.mode] or last.length < 1.5:
        errors.append("does not end long on a stable note")
    return errors
