"""Tests for the process-matching rule in perf.py."""

from perf import is_game


def test_is_game_counts_only_godot_games() -> None:
    commands = {
        "godot --path game res://test/perf/perf_run.tscn": True,
        "/home/u/.local/share/mise/installs/godot/4.7.2-stable/godot --audio-driver Dummy --path game": True,
        "Godot_v4.7.2-stable_linux.x86_64 --path game": True,
        "godot --headless --path game --import": False,
        "godot --path game --editor": False,
        "godot -e --path game": False,
        "godot --project-manager": False,
        "gamescope --backend headless -W 1920 -H 1080 -- godot --path game": False,
        "blender --background": False,
        "": False,
    }
    for line, expected in commands.items():
        assert is_game(line.split()) is expected, line
