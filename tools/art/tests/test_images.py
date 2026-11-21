"""GPT-Image: the cost estimate, the jobs file, and the live and Batch runs against a mocked
OpenAI API (the real openai client over an httpx2 MockTransport)."""

import base64
import json
from collections.abc import Callable
from pathlib import Path

import httpx2
import openai
import pytest

from orrery_art import cli, images
from orrery_art.config import Config

PNG = b"\x89PNG\r\n\x1a\n not a real image"
USAGE = {
    "input_tokens": 20,
    "output_tokens": 1449,
    "total_tokens": 1469,
    "input_tokens_details": {"image_tokens": 0, "text_tokens": 20},
}
Handler = Callable[[httpx2.Request], httpx2.Response]


def image_body() -> dict[str, object]:
    return {
        "created": 0,
        "data": [{"b64_json": base64.b64encode(PNG).decode()}],
        "usage": USAGE,
    }


def mock_openai(
    monkeypatch: pytest.MonkeyPatch, handler: Handler
) -> list[httpx2.Request]:
    """Makes the CLI use an OpenAI client whose requests go to handler. Returns the list
    that collects the requests."""
    seen: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    client = openai.OpenAI(
        api_key="test-key",
        base_url="https://api.test/v1",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(record)),
    )
    monkeypatch.setattr(cli, "openai_client", lambda config: client)
    return seen


def refuse(request: httpx2.Request) -> httpx2.Response:
    raise AssertionError(f"no request expected, got {request.method} {request.url}")


def run(argv: list[str], settings: Config, capsys: pytest.CaptureFixture[str]) -> dict:
    cli.main(argv, settings)
    return json.loads(capsys.readouterr().out)


@pytest.mark.parametrize(
    ("size", "quality", "tokens"),
    [
        ("1024x1024", "low", 823),
        ("1024x1024", "medium", 1449),
        ("1024x1024", "high", 1756),
    ],
)
def test_output_tokens_match_the_official_calculator(
    size: str, quality: str, tokens: int
) -> None:
    width, height = images.parse_size(size)
    assert (
        images.output_tokens(width, height, quality, "gpt-image-2.6-sunburst") == tokens
    )


def test_batch_halves_the_live_estimate(settings: Config) -> None:
    job = images.ImageJob("a brass clock face", "clock.png", "1024x1024", "medium")
    live = images.estimate_usd(job, settings.image, batch=False)
    assert images.estimate_usd(job, settings.image, batch=True) == pytest.approx(
        live / 2
    )
    assert live == pytest.approx(0.0435, abs=0.0005)


@pytest.mark.parametrize(
    "size", ["1000x1000", "512x512", "3840x1088", "4096x2048", "big"]
)
def test_parse_size_refuses_sizes_outside_the_limits(size: str) -> None:
    with pytest.raises(ValueError, match="size"):
        images.parse_size(size)


def test_read_jobs_names_each_bad_line(tmp_path: Path, settings: Config) -> None:
    jobs = tmp_path / "jobs.jsonl"
    lines = [
        {"prompt": "a", "out": "a.png"},
        {"prompt": "b", "out": "./a.png"},
        {"prompt": "c", "out": "../escape.png"},
        {"prompt": "d", "out": "d.png", "colour": "red"},
        {"out": "e.png"},
        {"prompt": "f", "out": "f.jpg", "transparent": True},
    ]
    jobs.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    with pytest.raises(ValueError) as error:
        images.read_jobs(jobs, settings.image)
    message = str(error.value)
    for part in ["line 3", "line 4", "line 5", "line 6", "two jobs write ./a.png"]:
        assert part in message


def test_image_sends_the_request_and_writes_a_manifest(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = mock_openai(
        monkeypatch, lambda request: httpx2.Response(200, json=image_body())
    )
    argv = [
        "image",
        "--prompt",
        "a brass clock face",
        "-o",
        "decals/clock.webp",
        "--transparent",
        "--yes",
    ]
    result = run(argv, settings, capsys)

    request = seen[0]
    assert (request.method, request.url.path) == ("POST", "/v1/images/generations")
    assert request.headers["Authorization"] == "Bearer test-key"
    assert json.loads(request.content) == {
        "model": "gpt-image-2.6-sunburst",
        "prompt": "a brass clock face",
        "size": "1024x1024",
        "quality": "medium",
        "output_format": "webp",
        "background": "transparent",
    }
    path = isolated / "images" / "decals" / "clock.webp"
    assert result["ok"] and path.read_bytes() == PNG
    record = json.loads(path.with_name("clock.webp.json").read_text())
    assert record["prompt"] == "a brass clock face"
    assert record["mode"] == "live"
    assert record["ai_generated"] is True
    assert record["settings"] == {
        "size": "1024x1024",
        "quality": "medium",
        "transparent": True,
    }
    assert record["billed_usd"] == pytest.approx((20 * 5 + 1449 * 30) / 1e6, abs=1e-4)


def test_dry_run_sends_nothing_and_needs_no_key(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli, "openai_client", lambda config: pytest.fail("no client in a dry run")
    )
    result = run(
        ["image", "--prompt", "a lamp", "-o", "lamp.png", "--dry-run"], settings, capsys
    )
    assert result["dry_run"] and result["within_cap"]
    assert result["requests"][0]["body"]["prompt"] == "a lamp"
    assert result["estimated_usd"] > 0


def test_a_paid_run_needs_yes(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_openai(monkeypatch, refuse)
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["image", "--prompt", "a lamp", "-o", "lamp.png"], settings)
    assert exit_info.value.code == cli.NEEDS_YES
    assert "--yes" in capsys.readouterr().err


def test_the_spend_guard_refuses_a_run_above_the_cap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_openai(monkeypatch, refuse)
    jobs = tmp_path / "set.jsonl"
    jobs.write_text(
        "".join(
            json.dumps({"prompt": f"icon {i}", "out": f"i{i}.png"}) + "\n"
            for i in range(5)
        )
    )
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["batch", str(jobs), "--yes", "--max-usd", "0.05"], settings)
    assert exit_info.value.code == 1
    assert "above the cap of USD 0.05" in json.loads(capsys.readouterr().out)["error"]


@pytest.mark.parametrize("cap", ["nan", "-1", "inf"])
def test_the_spend_guard_refuses_a_cap_that_is_not_a_finite_amount(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
    cap: str,
) -> None:
    mock_openai(monkeypatch, refuse)
    with pytest.raises(SystemExit):
        cli.main(
            ["image", "--prompt", "a", "-o", "a.png", "--yes", "--max-usd", cap],
            settings,
        )
    assert "finite" in json.loads(capsys.readouterr().out)["error"]


def test_a_batch_dry_run_ignores_saved_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_openai(monkeypatch, refuse)
    jobs = tmp_path / "set.jsonl"
    jobs.write_text(json.dumps({"prompt": "icon", "out": "icon.png"}) + "\n")
    images.BatchState("other-hash", "batch-9").write(images.state_path(jobs))
    result = run(["batch", str(jobs), "--dry-run"], settings, capsys)
    assert result["dry_run"] and len(result["requests"]) == 1


def test_jobs_files_with_one_name_keep_their_own_state(tmp_path: Path) -> None:
    first, second = tmp_path / "a" / "decals.jsonl", tmp_path / "b" / "decals.jsonl"
    assert images.state_path(first) != images.state_path(second)
    assert images.state_path(first) == images.state_path(first)


def test_a_missing_jobs_file_gives_the_json_error(
    tmp_path: Path, settings: Config, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        cli.main(["batch", str(tmp_path / "typo.jsonl"), "--dry-run"], settings)
    assert "cannot read the jobs file" in json.loads(capsys.readouterr().out)["error"]


def test_the_default_cap_comes_from_the_config(settings: Config) -> None:
    assert settings.max_usd_per_run == 5.0


def test_batch_submits_polls_collects_and_resumes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    batch = {
        "id": "batch-1",
        "object": "batch",
        "endpoint": "/v1/images/generations",
        "input_file_id": "file-in",
        "completion_window": "24h",
        "created_at": 0,
    }
    polls = iter(["in_progress", "completed"])
    output = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": "1",
                    "response": {"status_code": 200, "body": image_body()},
                }
            ),
            json.dumps(
                {
                    "custom_id": "0",
                    "response": {
                        "status_code": 400,
                        "body": {"error": {"message": "refused"}},
                    },
                }
            ),
        ]
    )

    def handler(request: httpx2.Request) -> httpx2.Response:
        match request.method, request.url.path:
            case "POST", "/v1/files":
                return httpx2.Response(
                    200,
                    json={
                        "id": "file-in",
                        "object": "file",
                        "bytes": 1,
                        "created_at": 0,
                        "filename": "f",
                        "purpose": "batch",
                        "status": "processed",
                    },
                )
            case "POST", "/v1/batches":
                return httpx2.Response(200, json={**batch, "status": "validating"})
            case "GET", "/v1/batches/batch-1":
                return httpx2.Response(
                    200,
                    json={**batch, "status": next(polls), "output_file_id": "file-out"},
                )
            case "GET", "/v1/files/file-out/content":
                return httpx2.Response(200, text=output)
        raise AssertionError(f"unexpected {request.method} {request.url}")

    seen = mock_openai(monkeypatch, handler)
    jobs = tmp_path / "decals.jsonl"
    jobs.write_text(
        json.dumps({"prompt": "a gear emblem", "out": "gear.png"})
        + "\n"
        + json.dumps({"prompt": "a sign", "out": "sign.png", "quality": "low"})
        + "\n"
    )
    # One image fails, so the run exits 1.
    with pytest.raises(SystemExit):
        cli.main(["batch", str(jobs), "--yes", "--poll", "0"], settings)
    result = json.loads(capsys.readouterr().out)

    upload = seen[0].content
    assert (
        b'"custom_id": "0"' in upload and b'"url": "/v1/images/generations"' in upload
    )
    assert json.loads(seen[1].content) == {
        "input_file_id": "file-in",
        "endpoint": "/v1/images/generations",
        "completion_window": "24h",
    }
    assert [r["ok"] for r in result["images"]] == [False, True]
    assert result["images"][0]["error"] == "refused"
    sign = isolated / "images" / "sign.png"
    assert sign.read_bytes() == PNG
    assert json.loads(sign.with_name("sign.png.json").read_text())["mode"] == "batch"

    # A rerun reports the collected set and sends nothing.
    count = len(seen)
    with pytest.raises(SystemExit):
        cli.main(["batch", str(jobs), "--yes"], settings)
    assert len(seen) == count
    assert "Already collected" in capsys.readouterr().err
