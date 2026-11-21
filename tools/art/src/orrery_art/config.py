"""The committed settings (tools/art/config.toml), the output folder and the spend guard."""

import json
import math
import tomllib
from dataclasses import dataclass
from datetime import date
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
    """The GPT-Image defaults and live token prices. models: model ids by name (flare,
    sunburst); model: the default name."""

    model: str
    models: dict[str, str]
    quality: str
    size: str
    text_in_usd_per_m: float
    image_in_usd_per_m: float
    image_out_usd_per_m: float
    ref_image_tokens: int


@dataclass(frozen=True)
class ModelSettings:
    """The Tripo API. series: the geometry model id of p1, p2 and h. credits: the price
    table (config.toml names the keys)."""

    api: str
    usd_per_credit: float
    poll_seconds: float
    timeout_minutes: float
    retries: int
    texture_model: str
    series: dict[str, str]
    credits: dict[str, float]


@dataclass(frozen=True)
class Config:
    keys: Keys
    max_usd_per_run: float
    budget_usd: dict[str, float]
    image: ImageSettings
    model: ModelSettings


def load(path: Path = CONFIG) -> Config:
    """Reads the settings file."""
    data = tomllib.loads(path.read_text())
    spend = data["spend"]
    return Config(
        keys=Keys(**data["keys"]),
        max_usd_per_run=float(spend["max_usd_per_run"]),
        budget_usd={k: float(v) for k, v in spend["budget_usd"].items()},
        image=ImageSettings(**data["image"]),
        model=ModelSettings(**data["model"]),
    )


class SpendError(Exception):
    """A run costs more than its cap or its API's budget."""


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


def ledger() -> Path:
    """build/art/spend.jsonl: one line for each paid call, with its cost."""
    return OUT / "spend.jsonl"


def spent(service: str) -> float:
    """The running total in USD of one API (openai or tripo) in this checkout."""
    if not ledger().exists():
        return 0.0
    rows = [
        json.loads(line) for line in ledger().read_text().splitlines() if line.strip()
    ]
    return sum(float(row["usd"]) for row in rows if row["service"] == service)


def record_spend(service: str, usd: float, request_id: str, out: str) -> None:
    """Adds a paid call to the ledger, once per request id (a resumed task is not counted
    again)."""
    ledger().parent.mkdir(parents=True, exist_ok=True)
    if request_id and ledger().exists():
        for line in ledger().read_text().splitlines():
            if line.strip() and json.loads(line).get("id") == request_id:
                return
    row = {
        "date": date.today().isoformat(),
        "service": service,
        "usd": usd,
        "id": request_id,
        "out": out,
    }
    with ledger().open("a") as file:
        file.write(json.dumps(row) + "\n")


def check_budget(service: str, estimate_usd: float, config: Config) -> None:
    """Raises SpendError when the running total plus the estimate passes the budget."""
    total, budget = spent(service), config.budget_usd[service]
    if total + estimate_usd > budget:
        raise SpendError(
            f"{service}: USD {total:.2f} spent plus USD {estimate_usd:.2f} passes the budget "
            f"of USD {budget:.2f} in config.toml"
        )


def out_path(kind: str, name: str) -> Path:
    """Returns build/art/<kind>/<name>. name must be a relative path inside that folder, so
    that no output lands in a committed folder."""
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"{name!r}: give a relative path inside build/art/{kind}/")
    return OUT / kind / rel
