"""Shared fixtures. Every test writes to a temporary build/art/ and sees no real key: the
`.env` lookup points at an empty temporary file, and the key variables are unset."""

import dataclasses
from pathlib import Path

import pytest

from orrery_art import config, keys


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Returns the temporary build/art/ folder."""
    out = tmp_path / "build-art"
    monkeypatch.setattr(config, "OUT", out)
    monkeypatch.setattr(keys, "env_files", lambda: [tmp_path / ".env"])
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TRIPO_API_KEY", raising=False)
    return out


@pytest.fixture
def settings() -> config.Config:
    """The committed settings, with no wait between polls."""
    loaded = config.load()
    return dataclasses.replace(
        loaded, model=dataclasses.replace(loaded.model, poll_seconds=0)
    )
