"""The committed settings (tools/art/config.toml), the output folder and the spend guard."""

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "tools" / "art" / "config.toml"
# Every generated file goes here. `build/` is git-ignored.
OUT = ROOT / "build" / "art"


@dataclass(frozen=True)
class Keys:
    """The Bitwarden item names of the API keys."""

    openai: str
    tripo: str


@dataclass(frozen=True)
class ImageSettings:
    """The GPT-Image defaults and live token prices."""

    model: str
    quality: str
    size: str
    text_in_usd_per_m: float
    image_out_usd_per_m: float


@dataclass(frozen=True)
class ModelSettings:
    """The Tripo API, its model version and the credit prices. credits: the estimate for each
    task type, by endpoint name (image-to-model ...)."""

    api: str
    version: str
    usd_per_credit: float
    credits: dict[str, int]
    detailed_texture_credits: int
    poll_seconds: float
    timeout_minutes: float


@dataclass(frozen=True)
class Config:
    keys: Keys
    max_usd_per_run: float
    image: ImageSettings
    model: ModelSettings


def load(path: Path = CONFIG) -> Config:
    """Reads the settings file."""
    data = tomllib.loads(path.read_text())
    return Config(
        keys=Keys(**data["keys"]),
        max_usd_per_run=float(data["spend"]["max_usd_per_run"]),
        image=ImageSettings(**data["image"]),
        model=ModelSettings(**data["model"]),
    )


class SpendError(Exception):
    """A run costs more than its cap."""


def check_spend(estimate_usd: float, cap_usd: float) -> None:
    """Raises SpendError when the estimate is above the cap, or the cap is not a finite
    amount of zero or more (`--max-usd nan` must not open the gate)."""
    if not 0 <= cap_usd < math.inf:
        raise SpendError(
            f"the cap must be a finite amount of USD 0 or more, not {cap_usd}"
        )
    if not estimate_usd <= cap_usd:
        raise SpendError(
            f"the estimate USD {estimate_usd:.2f} is above the cap of USD {cap_usd:.2f}. "
            f"Run fewer jobs, or raise the cap for this run with --max-usd {estimate_usd:.2f}"
        )


def out_path(kind: str, name: str) -> Path:
    """Returns build/art/<kind>/<name>. name must be a relative path inside that folder, so
    that no output lands in a committed folder."""
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"{name!r}: give a relative path inside build/art/{kind}/")
    return OUT / kind / rel
