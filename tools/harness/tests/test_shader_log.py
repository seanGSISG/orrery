"""The shader compile check on a game log, with the text that Godot 4.7 prints."""

import subprocess
from pathlib import Path

import pytest

from orrery_harness import game

BROKEN = """\
--res://core/marble/marble.gdshader--
E  16->  ROUGHNESS = nonexistent_value;
SHADER ERROR: Unknown identifier in expression: 'nonexistent_value'.
          at: (null) (res://core/marble/marble.gdshader:16)
ERROR: Shader compilation failed.
   at: set_code (servers/rendering/renderer_rd/forward_clustered/scene_shader_forward_clustered.cpp:185)
ORRERY harness listening on 127.0.0.1:49851
"""


def test_a_clean_log_passes() -> None:
    game.check_log(
        "ORRERY harness listening on 127.0.0.1:1\nERROR: 4 resources still in use\n",
        "x",
    )


def test_a_shader_error_names_the_shader_and_the_line() -> None:
    with pytest.raises(game.ShaderError) as error:
        game.check_log(BROKEN, "game.log")
    text = str(error.value)
    assert "game.log" in text
    assert "Unknown identifier in expression: 'nonexistent_value'" in text
    assert "res://core/marble/marble.gdshader:16" in text
    assert "ORRERY harness" not in text


def test_a_log_with_many_errors_shows_the_first_few() -> None:
    assert len(game.shader_errors(BROKEN * 10)) == 6


def test_stop_ends_the_game_then_fails_on_a_shader_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """quit is the check that `just gallery` relies on: the session is forgotten and its data
    deleted before the error is raised."""
    finished = subprocess.Popen(["true"])
    finished.wait()  # its process id no longer runs
    log = tmp_path / "game.log"
    log.write_text(BROKEN)
    data = tmp_path / "user"
    data.mkdir()
    session = game.Session(
        port=1, pid=finished.pid, display="none", log=str(log), data=str(data)
    )
    monkeypatch.setattr(game, "SESSION", tmp_path / "session.json")
    game.SESSION.write_text(session.model_dump_json())
    with pytest.raises(game.ShaderError, match="marble.gdshader:16"):
        game.stop()
    assert not game.SESSION.exists()
    assert not data.exists()
