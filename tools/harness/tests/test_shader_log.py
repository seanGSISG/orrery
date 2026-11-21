"""The shader compile check on a game log, with the text that Godot 4.7 prints."""

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
