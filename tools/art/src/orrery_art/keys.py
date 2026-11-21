"""API keys: from the environment, else from the git-ignored `.env` at the repo root.

In a git worktree without its own `.env`, the main checkout's `.env` is used. A real
environment variable wins over `.env`. The tools ask for a key only just before a call to
the API, so a dry run needs no key. They never print a key or write it to a file.
"""

import os
import subprocess
from pathlib import Path

from orrery_art.config import ROOT


class MissingKeyError(Exception):
    """No key in the environment and none in `.env`."""


def env_files(root: Path = ROOT) -> list[Path]:
    """Returns the `.env` files to read, first match first: the checkout's own, then the
    main checkout's (found from `git rev-parse --git-common-dir`)."""
    files = [root / ".env"]
    try:
        common = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return files
    main = Path(common).parent / ".env"
    if common and main not in files:
        files.append(main)
    return files


def read_env(path: Path) -> dict[str, str]:
    """Parses `NAME=value` lines. It skips blank lines and `#` comments, takes an optional
    `export ` and strips one pair of quotes. A `#` inside a value stays part of it."""
    values: dict[str, str] = {}
    try:
        text = path.read_text()
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.removeprefix("export ").split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[name.strip()] = value
    return values


def api_key(name: str, item: str, files: list[Path] | None = None) -> str:
    """Returns the key `name` from the environment, else from the first `.env` that sets it.
    Raises MissingKeyError that names the variable, the `.env` path and the Bitwarden item
    `item` that holds the key in its password field."""
    key = os.environ.get(name, "").strip()
    paths = env_files() if files is None else files
    for path in paths:
        if key:
            break
        key = read_env(path).get(name, "").strip()
    if not key:
        raise MissingKeyError(
            f"no {name}: set it in {' or '.join(map(str, paths))} (copy .env.example). "
            f"The key is the password "
            f"field of the Bitwarden item {item!r}."
        )
    return key
