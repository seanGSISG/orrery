"""The tracks of ticket #26 and the backing-track prompts built from the style brief.

The style brief is `docs/plan.md` 2.12. Prompts never name an artist or a song, ask for
an instrumental bed, and leave the lead melody to our own hook (hooks.py). ACE-Step
takes comma-separated tags plus BPM and key fields; Stable Audio 3 takes one caption
with the BPM and length written in it. `Track.requests` lists every take to render.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from orrery_music.comfy import TakeRequest
from orrery_music.hooks import HOOKS, Hook, Mode

TAKE_SECONDS = 180.0

# The shared part of the brief: early-2000s arcade electronica over modern hip-hop drums,
# with clockwork as the signature colour. Each track adds its own mood and tempo.
_ACE_CORE = (
    "instrumental, early 2000s arcade game electronica, groovy, funky bass line, "
    "bright synth stabs, light trance pads, modern hip-hop drums, punchy kick, crisp snare, "
    "808 sub bass, ticking clock percussion, metallic gear clicks, chimes, clean polished mix"
)
# Stable Audio 3 makes the beds: a steady groove on a simple vamp, so our hook carries the
# melody and the harmony stays easy to sit on. (Its first, busier prompts gave beds whose
# harmony wandered; every hook clashed with them.)
_SA3_CORE = (
    "instrumental groove bed with punchy modern hip-hop drums, a crisp snare and swung hi-hats, "
    "a deep 808 sub bass and a funky bass line on a simple two-chord vamp, light trance pads "
    "holding long chords, ticking clock percussion, metallic gear clicks and soft chimes, "
    "sparse arrangement with space on top"
)


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    bpm: int
    key: str
    mode: Mode
    # The hook's do in the music-box octave, before key detection moves it.
    tonic_midi: int
    hook_ids: tuple[str, ...]
    ace_moods: tuple[str, ...]
    sa3_moods: tuple[str, ...]
    # Allowed loop lengths in bars, each 1:30-2:30 at the track's tempo.
    loop_bars: tuple[int, ...]

    @property
    def hooks(self) -> tuple[Hook, ...]:
        return tuple(HOOKS[h] for h in self.hook_ids)

    def requests(self, ace_takes: int, sa3_takes: int) -> list[tuple[str, TakeRequest]]:
        """Every take for this track as (take id, request). Seeds are fixed per take id."""
        out: list[tuple[str, TakeRequest]] = []
        for i in range(ace_takes):
            mood = self.ace_moods[i % len(self.ace_moods)]
            take_id = f"{self.id}-ace-{i:02d}"
            prompt = f"{mood}, {_ACE_CORE}, {self.bpm} bpm"
            out.append(
                (
                    take_id,
                    TakeRequest(
                        "ace-step-1.5-xl-turbo",
                        prompt,
                        _seed(take_id),
                        TAKE_SECONDS,
                        self.bpm,
                        self.key,
                    ),
                )
            )
        for i in range(sa3_takes):
            mood = self.sa3_moods[i % len(self.sa3_moods)]
            take_id = f"{self.id}-sa3-{i:02d}"
            prompt = f"{mood} {_SA3_CORE}. Key: {self.key}. BPM: {self.bpm}. Length: {TAKE_SECONDS:.0f} seconds"
            out.append(
                (
                    take_id,
                    TakeRequest(
                        "stable-audio-3-medium",
                        prompt,
                        _seed(take_id),
                        TAKE_SECONDS,
                        self.bpm,
                        self.key,
                    ),
                )
            )
        return out


def mood_of(prompt: str) -> str:
    """The track-specific part of a prompt that `Track.requests` built."""
    return prompt.split(f", {_ACE_CORE}")[0].split(f" {_SA3_CORE}")[0]


def _seed(take_id: str) -> int:
    return int.from_bytes(hashlib.sha256(take_id.encode()).digest()[:6], "big")


TRACKS: dict[str, Track] = {
    t.id: t
    for t in (
        Track(
            id="title",
            name="Title theme",
            bpm=96,
            key="F major",
            mode="major",
            tonic_midi=77,  # F5
            hook_ids=("title-a", "title-b"),
            ace_moods=(
                "uplifting, cheerful, inviting title screen music, bouncy groove",
                "bright, sparkling, optimistic, boom-bap swing, warm major chords",
                "playful, wonder, light trance energy, half-time trap hi-hats",
            ),
            sa3_moods=(
                "Uplifting, bright early 2000s arcade electronica",
                "Bouncy, cheerful boom-bap electronica",
            ),
            loop_bars=(40, 48, 56),
        ),
        Track(
            id="beginner",
            name="Beginner track",
            bpm=90,
            key="A minor",
            mode="minor",
            tonic_midi=81,  # A5
            hook_ids=("beginner-a", "beginner-b"),
            ace_moods=(
                "upbeat, funky, relaxed groove, boom-bap swing, head-nodding",
                "playful, groovy, sunny, slap bass, half-time trap hi-hats",
                "laid-back, catchy, rolling groove, vinyl warmth, swung drums",
            ),
            sa3_moods=(
                "Funky, upbeat early 2000s arcade electronica",
                "Laid-back, groovy hip-hop electronica",
            ),
            loop_bars=(40, 48),
        ),
        Track(
            id="ascent",
            name="Ascent track",
            bpm=76,
            key="D minor",
            mode="minor",
            tonic_midi=74,  # D5
            hook_ids=("ascent-a", "ascent-b"),
            ace_moods=(
                "epic, soaring, mysterious, cinematic, slow half-time groove, wide reverb",
                "majestic, determined, climbing, big trance pads, slow trap drums, deep 808",
                "vast, starry, awe, heroic, slow boom-bap, glowing arpeggios",
            ),
            sa3_moods=(
                "Epic, slow cinematic electronica",
                "Majestic, slow half-time electronica",
            ),
            loop_bars=(32, 40),
        ),
    )
}
