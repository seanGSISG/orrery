"""Keys: the environment wins over `.env`, a worktree falls back to the main checkout, and a
missing key names the variable, the file and the Bitwarden item."""

import subprocess
from pathlib import Path

import pytest

from orrery_art import keys

# The real lookup; the autouse fixture replaces keys.env_files for every other test.
from orrery_art.keys import env_files


def test_read_env_parses_quotes_export_and_comments(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "# keys\nexport OPENAI_API_KEY=\"sk-a#b\"\nTRIPO_API_KEY='tsk-1'\n\nBROKEN\n"
    )
    assert keys.read_env(env) == {"OPENAI_API_KEY": "sk-a#b", "TRIPO_API_KEY": "tsk-1"}


def test_the_environment_wins_over_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = tmp_path / ".env"
    env.write_text("TRIPO_API_KEY=from-file\n")
    assert keys.api_key("TRIPO_API_KEY", "tripo-api-key", [env]) == "from-file"
    monkeypatch.setenv("TRIPO_API_KEY", "from-env")
    assert keys.api_key("TRIPO_API_KEY", "tripo-api-key", [env]) == "from-env"


def test_an_empty_value_falls_through_to_the_next_file(tmp_path: Path) -> None:
    (tmp_path / "a").write_text("OPENAI_API_KEY=\n")
    (tmp_path / "b").write_text("OPENAI_API_KEY=sk-main\n")
    files = [tmp_path / "a", tmp_path / "b"]
    assert keys.api_key("OPENAI_API_KEY", "openai-api-key", files) == "sk-main"


def test_a_missing_key_names_the_variable_the_file_and_the_item(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    with pytest.raises(keys.MissingKeyError) as error:
        keys.api_key("OPENAI_API_KEY", "openai-api-key", [env])
    message = str(error.value)
    assert "OPENAI_API_KEY" in message and str(env) in message
    assert "'openai-api-key'" in message and "password" in message


def test_a_worktree_falls_back_to_the_main_checkout(tmp_path: Path) -> None:
    main = tmp_path / "main"
    main.mkdir()

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(main), *args], check=True, capture_output=True)

    git("init", "-q")
    git(
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "x",
    )
    git("worktree", "add", "-q", str(tmp_path / "wt"))
    assert env_files(tmp_path / "wt") == [tmp_path / "wt" / ".env", main / ".env"]
    assert env_files(main) == [main / ".env"]
