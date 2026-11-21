"""Write `out/review/index.html`: one dark, phone-friendly page with every kept candidate.

Each card has the full loop and a 20 s preview (both under `out/`, not committed),
the tempo, key and length, and one line on what makes it catchy. The "Hear the seam"
button jumps to 5 s before the loop end with looping on, so the wrap is easy to judge.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from orrery_music.brief import TRACKS

_CSS = """
:root { color-scheme: dark; --bg: #0d1017; --card: #161b26; --line: #263044; --text: #e7ebf3;
  --dim: #9aa6bd; --accent: #f2c14e; --pass: #6fd3a8; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 760px; margin: 0 auto; padding: 20px 16px 48px; }
h1 { font-size: 1.5rem; margin: 0 0 4px; }
h2 { font-size: 1.15rem; margin: 32px 0 12px; color: var(--accent); }
.note { color: var(--dim); font-size: .9rem; margin: 0 0 8px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 14px; margin: 0 0 12px; }
.card h3 { margin: 0 0 6px; font-size: 1rem; display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }
.pick { font-size: .75rem; color: var(--bg); background: var(--pass); border-radius: 999px; padding: 1px 8px; }
.facts { color: var(--dim); font-size: .85rem; margin: 0 0 8px; }
.catchy { margin: 0 0 10px; }
audio { width: 100%; margin: 4px 0; }
.row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.label { font-size: .8rem; color: var(--dim); min-width: 52px; }
button { background: transparent; color: var(--text); border: 1px solid var(--line);
  border-radius: 8px; padding: 6px 10px; font: inherit; font-size: .85rem; cursor: pointer; }
button:hover { border-color: var(--accent); }
"""

_JS = """
for (const b of document.querySelectorAll('button[data-seam]')) {
  b.addEventListener('click', () => {
    const a = document.getElementById(b.dataset.seam);
    const go = () => { a.currentTime = Math.max(0, a.duration - 5); a.play(); };
    a.loop = true;
    if (Number.isFinite(a.duration)) go(); else a.addEventListener('loadedmetadata', go, { once: true });
  });
}
for (const a of document.querySelectorAll('audio')) {
  a.addEventListener('play', () => {
    for (const other of document.querySelectorAll('audio')) if (other !== a) other.pause();
  });
}
"""


def write_review(root: Path) -> Path:
    sections: list[str] = []
    for track_id, track in TRACKS.items():
        manifest = root / "manifest" / f"{track_id}.json"
        if not manifest.exists():
            continue
        data = json.loads(manifest.read_text())
        kept = sorted(
            (c for c in data["candidates"] if c["kept"]), key=lambda c: -c["score"]
        )
        cards: list[str] = []
        for i, c in enumerate(kept):
            full = html.escape(f"../../{c['file']}")
            prev = html.escape(f"../../{c['preview']}")
            aid = html.escape(f"a-{c['id']}")
            minutes, seconds = divmod(round(c["seconds"]), 60)
            model = (
                "ACE-Step 1.5 XL" if c["model"].startswith("ace") else "Stable Audio 3"
            )
            badge = '<span class="pick">top pick</span>' if i == 0 else ""
            cards.append(
                f"""<div class="card">
<h3>{html.escape(c["id"])} {badge}</h3>
<p class="facts">{c["bpm"]:.1f} BPM · {html.escape(c["hook_key"])} · {minutes}:{seconds:02d} ({c["bars"]} bars) · {model} bed · hook “{html.escape(c["hook_name"])}”</p>
<p class="catchy">{html.escape(c["catchy"])}</p>
<div class="row"><span class="label">Loop</span><button data-seam="{aid}">Hear the seam</button></div>
<audio id="{aid}" controls loop preload="none" src="{full}"></audio>
<div class="row"><span class="label">Preview</span></div>
<audio controls preload="none" src="{prev}"></audio>
</div>"""
            )
        bad_takes = sum(1 for t in data["takes"] if t["rejects"])
        bad_mixes = sum(1 for c in data["candidates"] if c["rejects"])
        sections.append(
            f"<h2>{html.escape(track.name)}</h2>\n"
            f'<p class="note">{len(kept)} kept. {bad_takes} of {len(data["takes"])} takes and '
            f"{bad_mixes} of {len(data['candidates'])} mixes failed a check "
            f"(manifest/{track_id}.json says why).</p>\n" + "\n".join(cards)
        )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Orrery music review</title>
<style>{_CSS}</style>
</head>
<body>
<main>
<h1>Orrery music review</h1>
<p class="note">Pick one per track. Every file is normalised to -16 LUFS and loops on a bar line.</p>
{"".join(sections)}
</main>
<script>{_JS}</script>
</body>
</html>
"""
    dest = root / "out" / "review" / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    return dest
