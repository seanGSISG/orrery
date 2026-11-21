"""GPT-Image: the cost estimate, the jobs file, live calls, edits, the alpha check and the
Batch API, against a mocked OpenAI API (the real openai client over an httpx2
MockTransport)."""

import base64
import io
import json
from collections.abc import Callable
from pathlib import Path

import httpx2
import openai
import pytest
from PIL import Image

from orrery_art import cli, images
from orrery_art.config import Config, record_spend

USAGE = {
    "input_tokens": 20,
    "output_tokens": 1449,
    "total_tokens": 1469,
    "input_tokens_details": {"image_tokens": 0, "text_tokens": 20},
}
Handler = Callable[[httpx2.Request], httpx2.Response]


def png(alpha: int) -> bytes:
    """A 4x4 RGBA PNG whose first pixel has the given alpha."""
    image = Image.new("RGBA", (4, 4), (200, 150, 50, 255))
    image.putpixel((0, 0), (0, 0, 0, alpha))
    data = io.BytesIO()
    image.save(data, "PNG")
    return data.getvalue()


CLEAR, OPAQUE = png(0), png(255)


def image_body(data: bytes = CLEAR) -> dict[str, object]:
    return {
        "created": 0,
        "data": [{"b64_json": base64.b64encode(data).decode()}],
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


def failed(
    argv: list[str], settings: Config, capsys: pytest.CaptureFixture[str]
) -> str:
    with pytest.raises(SystemExit):
        cli.main(argv, settings)
    return json.loads(capsys.readouterr().out)["error"]


def job(settings: Config, **fields: object) -> images.ImageJob:
    line = {"prompt": "a brass clock face", "out": "clock.png", **fields}
    return images.job_from_line(line, settings.image)


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
    assert images.output_tokens(width, height, quality, "gpt-image-2.6-flare") == tokens


def test_estimates(settings: Config, tmp_path: Path) -> None:
    plain = job(settings)
    live = images.estimate_usd(plain, settings.image, batch=False)
    assert live == pytest.approx(0.0435, abs=0.0005)
    assert images.estimate_usd(plain, settings.image, batch=True) == pytest.approx(
        live / 2
    )
    ref = tmp_path / "ref.png"
    ref.write_bytes(OPAQUE)
    with_ref = images.estimate_usd(
        job(settings, refs=[str(ref)]), settings.image, batch=False
    )
    assert with_ref == pytest.approx(live + 1500 * 8 / 1e6)


def test_the_default_model_is_flare_and_sunburst_is_named(settings: Config) -> None:
    assert job(settings).model == "gpt-image-2.6-flare"
    assert job(settings, model="sunburst").model == "gpt-image-2.6-sunburst"
    with pytest.raises(ValueError, match="flare, sunburst"):
        job(settings, model="gpt-image-2.6")


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
        {"prompt": None, "out": "g.png"},
        {"prompt": "h", "out": "h.png", "transparent": "false"},
        {"prompt": "i", "out": "k/i.png"},
        {"prompt": "j", "out": "k/i.png/j.png"},
    ]
    jobs.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    with pytest.raises(ValueError) as error:
        images.read_jobs(jobs, settings.image)
    message = str(error.value)
    for part in [
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "line 8",
        "two jobs write ./a.png",
    ]:
        assert part in message
    assert "k/i.png/j.png and another output are a file and its folder" in message


def test_image_sends_the_request_logs_usage_and_checks_alpha(
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
        "model": "gpt-image-2.6-flare",
        "prompt": "a brass clock face",
        "size": "1024x1024",
        "quality": "medium",
        "output_format": "webp",
        "background": "transparent",
    }
    path = isolated / "images" / "decals" / "clock.webp"
    assert result["ok"] and path.read_bytes() == CLEAR
    record = json.loads(path.with_name("clock.webp.json").read_text())
    assert (record["prompt"], record["mode"], record["ai_generated"]) == (
        "a brass clock face",
        "live",
        True,
    )
    assert record["settings"]["usage"]["output_tokens"] == 1449
    assert record["billed_usd"] == pytest.approx((20 * 5 + 1449 * 30) / 1e6, abs=1e-4)
    spend = (isolated / "spend.jsonl").read_text().splitlines()
    assert json.loads(spend[0])["service"] == "openai"


def test_a_transparent_image_without_clear_pixels_fails(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_openai(
        monkeypatch, lambda request: httpx2.Response(200, json=image_body(OPAQUE))
    )
    argv = ["image", "--prompt", "a decal", "-o", "decal.png", "--transparent", "--yes"]
    with pytest.raises(SystemExit):
        cli.main(argv, settings)
    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "the alpha channel has no transparent pixel"
    assert (isolated / "images" / "decal.png").exists()


def test_references_make_an_edit_with_each_image(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = mock_openai(
        monkeypatch, lambda request: httpx2.Response(200, json=image_body())
    )
    first, second = tmp_path / "style.png", tmp_path / "shape.png"
    first.write_bytes(OPAQUE)
    second.write_bytes(OPAQUE)
    argv = ["image", "--prompt", "Image 1 sets the look only.", "-o", "a.png"]
    argv += [
        "--ref",
        str(first),
        "--ref",
        str(second),
        "--model",
        "sunburst",
        "--complexity",
        "low",
        "--yes",
    ]
    run(argv, settings, capsys)
    request = seen[0]
    assert request.url.path == "/v1/images/edits"
    assert request.headers["Content-Type"].startswith("multipart/form-data")
    assert (
        b'filename="style.png"' in request.content
        and b'filename="shape.png"' in request.content
    )
    assert (
        b"gpt-image-2.6-sunburst" in request.content
        and b'name="complexity"' in request.content
    )


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
    assert (result["spent_usd"], result["budget_usd"]) == (0, 20.0)


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
    error = failed(["set", str(jobs), "--yes", "--max-usd", "0.05"], settings, capsys)
    assert "above the cap of USD 0.05" in error


@pytest.mark.parametrize("cap", ["nan", "-1", "inf"])
def test_the_spend_guard_refuses_a_cap_that_is_not_a_finite_amount(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
    cap: str,
) -> None:
    mock_openai(monkeypatch, refuse)
    error = failed(
        ["image", "--prompt", "a", "-o", "a.png", "--yes", "--max-usd", cap],
        settings,
        capsys,
    )
    assert "finite" in error


def test_the_budget_counts_earlier_spend(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_openai(monkeypatch, refuse)
    record_spend("openai", 19.98, "", "earlier.png")
    error = failed(["image", "--prompt", "a", "-o", "a.png", "--yes"], settings, capsys)
    assert "passes the budget of USD 20.00" in error


def test_a_live_set_runs_each_job_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = mock_openai(
        monkeypatch, lambda request: httpx2.Response(200, json=image_body())
    )
    jobs = tmp_path / "set.jsonl"
    jobs.write_text(
        "".join(
            json.dumps({"prompt": f"icon {i}", "out": f"i{i}.png"}) + "\n"
            for i in range(2)
        )
    )
    result = run(["set", str(jobs), "--yes"], settings, capsys)
    assert [r["ok"] for r in result["images"]] == [True, True] and len(seen) == 2
    again = run(["set", str(jobs), "--yes"], settings, capsys)
    assert again["images"] == [] and len(seen) == 2


def test_a_missing_jobs_file_gives_the_json_error(
    tmp_path: Path, settings: Config, capsys: pytest.CaptureFixture[str]
) -> None:
    error = failed(["set", str(tmp_path / "typo.jsonl"), "--dry-run"], settings, capsys)
    assert "cannot read the jobs file" in error


def test_jobs_files_with_one_name_keep_their_own_state(tmp_path: Path) -> None:
    first, second = tmp_path / "a" / "decals.jsonl", tmp_path / "b" / "decals.jsonl"
    assert images.state_path(first) != images.state_path(second)


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
    result = run(["set", str(jobs), "--batch", "--dry-run"], settings, capsys)
    assert result["dry_run"] and len(result["requests"]) == 1


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
    refused = {"status_code": 400, "body": {"error": {"message": "refused"}}}
    output = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": "1",
                    "response": {"status_code": 200, "body": image_body()},
                }
            ),
            json.dumps({"custom_id": "0", "response": refused}),
        ]
    )
    uploaded = {"id": "file-in", "object": "file", "bytes": 1, "created_at": 0}
    uploaded |= {"filename": "f", "purpose": "batch", "status": "processed"}

    def handler(request: httpx2.Request) -> httpx2.Response:
        match request.method, request.url.path:
            case "POST", "/v1/files":
                return httpx2.Response(200, json=uploaded)
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
        cli.main(["set", str(jobs), "--batch", "--yes", "--poll", "0"], settings)
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
    assert sign.read_bytes() == CLEAR
    assert json.loads(sign.with_name("sign.png.json").read_text())["mode"] == "batch"

    # A rerun reports the collected set and sends nothing.
    count = len(seen)
    with pytest.raises(SystemExit):
        cli.main(["set", str(jobs), "--batch", "--yes"], settings)
    assert len(seen) == count
    assert "Already collected" in capsys.readouterr().err

    # A collected file that is gone is reported, not counted as made.
    sign.unlink()
    assert "collected files are gone: sign.png" in failed(
        ["set", str(jobs), "--batch"], settings, capsys
    )
