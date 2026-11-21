"""The manifest: one `<output>.json` next to each generated file. It records how the file was
made, so that docs/licenses.md and the Steam AI-content disclosure can cite it."""

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

Setting = str | int | float | bool


@dataclass(frozen=True)
class Manifest:
    """service: the API (OpenAI Images, Tripo). mode: live, batch or task. prompt: the text
    prompt, or the source image of a model. request_id: the batch or task id."""

    service: str
    model: str
    mode: str
    prompt: str
    settings: dict[str, Setting]
    estimated_usd: float
    billed_usd: float | None
    request_id: str = ""
    seed: int | None = None
    date: str = field(default_factory=lambda: date.today().isoformat())
    ai_generated: bool = True


def manifest_path(output: Path) -> Path:
    """Returns the manifest path of an output file: `<name>.<ext>.json`."""
    return output.with_name(output.name + ".json")


def write(output: Path, manifest: Manifest) -> Path:
    """Writes the manifest of output and returns its path."""
    path = manifest_path(output)
    path.write_text(json.dumps(asdict(manifest), indent=2) + "\n")
    return path
