"""Contract tests: each harness command against a running debug build.

The tests start `godot --headless` (display none), so they run in CI. The screenshot test
needs a GPU and gamescope; run it locally with `uv run pytest -m gpu`.
"""

import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from orrery_harness import game
from orrery_harness.client import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    NO_FRAME,
    NOT_AVAILABLE,
    NOT_FOUND,
    PARSE_ERROR,
    Harness,
    HarnessError,
)


@pytest.fixture(scope="module")
def session() -> Iterator[game.Session]:
    session = game.start(game.LaunchOptions(level="flat", display="none"))
    yield session
    game.end(session)


@pytest.fixture
def harness(session: game.Session) -> Iterator[Harness]:
    """A connection to the game, with flat loaded fresh, paused at tick 0 and no input."""
    with session.connect() as harness:
        harness.pause()
        harness.set_time_scale(1.0)
        harness.input()
        harness.load_level("flat")
        yield harness


def test_ping(harness: Harness) -> None:
    assert harness.ping() == "pong"


def test_load_level(harness: Harness) -> None:
    state = harness.load_level("flat")
    assert (state.level, state.tick, state.status) == ("flat", 0, "playing")
    with pytest.raises(HarnessError) as missing:
        harness.load_level("no_such_level")
    assert missing.value.code == NOT_FOUND


def test_load_mode_is_a_stub(harness: Harness) -> None:
    with pytest.raises(HarnessError) as stub:
        harness.load_mode("ascent")
    assert stub.value.code == NOT_AVAILABLE


def test_state(harness: Harness) -> None:
    state = harness.state()
    assert (state.level, state.tick, state.gems_total) == ("flat", 0, 0)
    assert state.position[1] == pytest.approx(0.2, abs=0.01)  # on the start pad


def test_step_counts_ticks(harness: Harness) -> None:
    assert harness.step(10).tick == 10
    assert harness.step().tick == 11
    with pytest.raises(HarnessError) as bad:
        harness.step(0)
    assert bad.value.code == INVALID_PARAMS


def test_input_rolls_forward_for_its_frames(harness: Harness) -> None:
    harness.input(move=(0.0, 1.0), frames=60)
    rolling = harness.step(60)
    assert rolling.position[2] < -0.5  # forward at yaw 0 is -z
    coasting = harness.step(60)
    assert coasting.position[2] < rolling.position[2]
    assert abs(coasting.velocity[2]) < abs(rolling.velocity[2])


def test_pause_and_resume(harness: Harness) -> None:
    paused = harness.state().tick
    time.sleep(0.2)
    assert harness.state().tick == paused
    harness.resume()
    time.sleep(0.3)
    assert harness.state().tick > paused


def test_set_time_scale(harness: Harness) -> None:
    harness.set_time_scale(0.0)
    harness.resume()
    before = harness.state().tick
    time.sleep(0.2)
    assert harness.state().tick == before
    with pytest.raises(HarnessError) as bad:
        harness.set_time_scale(100.0)
    assert bad.value.code == INVALID_PARAMS


def test_teleport(harness: Harness) -> None:
    harness.teleport((3.0, 2.0, -1.0), (1.0, 0.0, 0.0))
    state = harness.step()
    assert state.position[0] == pytest.approx(3.0, abs=0.05)
    assert state.position[1] == pytest.approx(2.0, abs=0.05)
    assert state.velocity[0] == pytest.approx(1.0, abs=0.01)


def test_screenshot_without_a_display_fails(harness: Harness) -> None:
    with pytest.raises(HarnessError) as headless:
        harness.screenshot()
    assert headless.value.code == NO_FRAME


def test_logs(harness: Harness) -> None:
    lines = harness.logs()
    assert any("ORRERY harness listening" in line.text for line in lines)
    assert harness.logs(since=lines[-1].seq) == []


def test_run_bot_plays_each_route_to_the_finish(harness: Harness) -> None:
    harness.load_level("route_bot")
    first = harness.run_bot()
    assert (first.finished, first.falls, first.stuck_at) == (True, 0, None)
    assert harness.state().status == "finished"
    expert = harness.run_bot("expert")
    assert expert.finished
    assert 0.0 < expert.time < first.time
    with pytest.raises(HarnessError) as missing:
        harness.run_bot("no_such_route")
    assert missing.value.code == NOT_FOUND


def test_set_setting(harness: Harness) -> None:
    key = "physics/common/max_physics_steps_per_frame"
    assert harness.set_setting(key, 8) == 8
    with pytest.raises(HarnessError) as missing:
        harness.set_setting("no/such/setting", 1)
    assert missing.value.code == NOT_FOUND


def test_protocol_errors(harness: Harness) -> None:
    with pytest.raises(HarnessError) as unknown:
        harness.call("fly")
    assert unknown.value.code == METHOD_NOT_FOUND
    with pytest.raises(HarnessError) as garbled:
        harness.send_line("{not json")
    assert garbled.value.code == PARSE_ERROR
    with pytest.raises(HarnessError) as empty:
        harness.send_line("{}")
    assert empty.value.code == INVALID_REQUEST


def test_quit() -> None:
    session = game.start(game.LaunchOptions(display="none"))
    with session.connect() as harness:
        harness.quit()
    assert game._wait_exit(session, 10.0)


@pytest.mark.gpu
def test_screenshot_saves_a_gpu_frame(tmp_path: Path) -> None:
    session = game.start(game.LaunchOptions(level="flat", resolution=(640, 360)))
    try:
        with session.connect() as harness:
            harness.step(30)
            shot = harness.screenshot(str(tmp_path / "flat.png"))
            with pytest.raises(HarnessError) as missing:
                harness.screenshot(shot="no_such_shot")
            assert missing.value.code == NOT_FOUND
    finally:
        game.end(session)
    assert (shot.width, shot.height) == (640, 360)
    assert not shot.blank
    assert Path(shot.path).stat().st_size > 1000
