"""Tripo image-to-3D against a mocked API: upload, start, poll, download, manifest, resume."""

import functools
import json
from pathlib import Path

import httpx2
import pytest

from orrery_art import cli, tripo
from orrery_art.config import Config

GLB = b"glTF fake model"


@pytest.fixture
def image(tmp_path: Path) -> Path:
    path = tmp_path / "lamp.png"
    path.write_bytes(b"\x89PNG fake")
    return path


def mock_tripo(
    monkeypatch: pytest.MonkeyPatch, statuses: list[str]
) -> list[httpx2.Request]:
    """Points tripo.connect at a mock API and CDN. Returns the list of requests."""
    seen: list[httpx2.Request] = []
    polls = iter(statuses)

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        match request.method, request.url.host, request.url.path:
            case "POST", "openapi.tripo3d.ai", "/v3/files":
                return httpx2.Response(
                    200, json={"code": 0, "data": {"file_token": "file_abc"}}
                )
            case "POST", "openapi.tripo3d.ai", (
                "/v3/generation/image-to-model" | "/v3/generation/multiview-to-model"
            ):
                return httpx2.Response(
                    200, json={"code": 0, "data": {"task_id": "task-1"}}
                )
            case "GET", "openapi.tripo3d.ai", "/v3/tasks/task-1":
                data = {"task_id": "task-1", "status": next(polls), "progress": 50}
                if data["status"] == "success":
                    data["output"] = {
                        "model_url": "https://cdn.tripo.test/out/model.glb",
                        "rendered_image_url": "https://cdn.tripo.test/out/preview.webp",
                    }
                    data["credits_consumed"] = 30.0
                return httpx2.Response(200, json={"code": 0, "data": data})
            case "GET", "cdn.tripo.test", "/out/model.glb":
                return httpx2.Response(200, content=GLB)
            case "GET", "cdn.tripo.test", "/out/preview.webp":
                return httpx2.Response(200, content=b"preview")
        raise AssertionError(f"unexpected {request.method} {request.url}")

    connect = functools.partial(tripo.connect, transport=httpx2.MockTransport(handler))
    monkeypatch.setattr(tripo, "connect", connect)
    monkeypatch.setenv("TRIPO_API_KEY", "tsk-test")
    return seen


def test_model_runs_a_task_and_writes_the_glb(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = mock_tripo(monkeypatch, ["queued", "running", "success"])
    argv = [
        "model",
        str(image),
        "-o",
        "lamp.glb",
        "--texture-quality",
        "detailed",
        "--seed",
        "7",
        "--yes",
    ]
    cli.main(argv, settings)
    result = json.loads(capsys.readouterr().out)

    upload, start = seen[0], seen[1]
    assert upload.headers["Authorization"] == "Bearer tsk-test"
    assert b'name="file"; filename="lamp.png"' in upload.content
    assert json.loads(start.content) == {
        "input": "file_abc",
        "model": "v3.1-20260211",
        "texture": True,
        "pbr": True,
        "texture_quality": "detailed",
        "model_seed": 7,
        "texture_seed": 7,
    }
    cdn = seen[-1]
    assert cdn.url.host == "cdn.tripo.test" and "Authorization" not in cdn.headers
    glb = isolated / "models" / "lamp.glb"
    assert glb.read_bytes() == GLB
    preview = glb.with_name("lamp.rendered_image_url.webp")
    assert preview.read_bytes() == b"preview"
    assert result == {
        "ok": True,
        "files": [str(glb), str(preview)],
        "task_id": "task-1",
        "billed_usd": 0.3,
    }
    record = json.loads(glb.with_name("lamp.glb.json").read_text())
    assert (record["service"], record["seed"], record["estimated_usd"]) == (
        "Tripo API /generation/image-to-model",
        7,
        0.4,
    )
    assert record["settings"]["texture_quality"] == "detailed"
    assert not glb.with_name("lamp.glb.task.json").exists()


def test_a_rerun_resumes_the_task_instead_of_paying_again(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = mock_tripo(monkeypatch, ["success"])
    task_file = isolated / "models" / "lamp.glb.task.json"
    task_file.parent.mkdir(parents=True)
    task_file.write_text(json.dumps({"task_id": "task-1"}))
    cli.main(["model", str(image), "-o", "lamp.glb"], settings)
    paths = [r.url.path for r in seen]
    assert paths == ["/v3/tasks/task-1", "/out/model.glb", "/out/preview.webp"]
    assert "Resuming task task-1" in capsys.readouterr().err


def test_a_failed_task_reports_the_reason(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_tripo(monkeypatch, ["failed"])
    with pytest.raises(SystemExit):
        cli.main(["model", str(image), "-o", "lamp.glb", "--yes"], settings)
    assert "task task-1 failed" in json.loads(capsys.readouterr().out)["error"]


def test_an_api_error_shows_the_message_and_the_suggestion(settings: Config) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        body = {
            "code": 2010,
            "message": "not enough credit",
            "suggestion": "buy credit",
        }
        return httpx2.Response(403, json=body)

    client = tripo.connect(settings.model, "k", httpx2.MockTransport(handler))
    with pytest.raises(
        tripo.TripoError, match=r"code 2010: not enough credit \(buy credit\)"
    ):
        client.balance()


def test_model_dry_run_shows_the_requests_and_the_cost(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = mock_tripo(monkeypatch, [])
    monkeypatch.delenv("TRIPO_API_KEY")
    cli.main(["model", str(image), "-o", "lamp.glb", "--dry-run"], settings)
    result = json.loads(capsys.readouterr().out)
    assert seen == []
    assert result["estimated_usd"] == 0.3
    body = result["requests"][0]["body"]
    assert body["texture_quality"] == "standard"
    assert body["input"] == f"<file_token of the upload of {image}>"


def test_model_needs_yes(
    monkeypatch: pytest.MonkeyPatch, image: Path, settings: Config
) -> None:
    seen = mock_tripo(monkeypatch, [])
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["model", str(image), "-o", "lamp.glb"], settings)
    assert exit_info.value.code == cli.NEEDS_YES and seen == []


def test_multiview_uploads_each_view_in_order(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    tmp_path: Path,
    settings: Config,
) -> None:
    seen = mock_tripo(monkeypatch, ["success"])
    back = tmp_path / "back.png"
    back.write_bytes(b"\x89PNG back")
    cli.main(
        ["model", str(image), "--back", str(back), "-o", "lamp.glb", "--yes"], settings
    )
    uploads = [r for r in seen if r.url.path == "/v3/files"]
    assert [b'filename="lamp.png"' in r.content for r in uploads] == [True, False]
    start = next(r for r in seen if r.url.path == "/v3/generation/multiview-to-model")
    body = json.loads(start.content)
    assert body["inputs"] == [{"front": "file_abc"}, {"back": "file_abc"}]


def test_multiview_needs_the_front_and_one_more_view(
    settings: Config, image: Path
) -> None:
    with pytest.raises(ValueError, match="front view"):
        tripo.multiview_to_model(settings.model, {"back": image}, "x.glb")
    with pytest.raises(ValueError, match="front view"):
        tripo.multiview_to_model(settings.model, {"front": image}, "x.glb")
