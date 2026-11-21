"""Tripo tasks against a mocked API and CDN: request shapes, uploads, polling, downloads,
recipes, resume, 429 back-off and the free account calls."""

import functools
import json
from pathlib import Path

import httpx2
import pytest

from orrery_art import cli, tripo
from orrery_art.config import Config

GLB = b"glTF fake model"
CDN = "https://cdn.tripo.test/out"
VIEWS = {f"{v}_view_url": f"{CDN}/{v}.png" for v in ("front", "left", "back", "right")}
MODEL = {"model_url": f"{CDN}/model.glb", "rendered_image_url": f"{CDN}/preview.webp"}


class Mock:
    """A mock Tripo API and CDN. statuses: the polled statuses; the last one repeats.
    output: the output of a successful task. busy: how many requests get HTTP 429."""

    def __init__(
        self, statuses: list[str], output: dict[str, object] | None = None
    ) -> None:
        self.seen: list[httpx2.Request] = []
        self.statuses = statuses
        self.output = output if output is not None else MODEL
        self.sleeps: list[float] = []
        self.busy = 0

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.seen.append(request)
        url = request.url
        if url.host == "cdn.tripo.test":
            return httpx2.Response(
                200, content=GLB if url.path.endswith(".glb") else b"png"
            )
        if self.busy:
            self.busy -= 1
            body = {"code": 2000, "message": "busy"}
            return httpx2.Response(429, json=body, headers={"Retry-After": "3"})
        match request.method, url.path:
            case "POST", "/v3/files":
                return ok({"file_token": f"file_{len(self.seen)}"})
            case "GET", "/v3/account/balance":
                return ok({"balance": 1999.5, "frozen": 0.0})
            case "GET", "/v3/account/usage":
                return ok([{"task_id": "task-0", "credits_consumed": 10.0}])
            case "GET", "/v3/tasks/task-1":
                status = (
                    self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
                )
                data: dict[str, object] = {
                    "task_id": "task-1",
                    "status": status,
                    "progress": 50,
                }
                if status == "success":
                    data |= {"output": self.output, "credits_consumed": 40.0}
                return ok(data)
            case "POST", _:
                return ok({"task_id": "task-1"})
        raise AssertionError(f"unexpected {request.method} {url}")

    def posted(self, path: str) -> dict[str, object]:
        request = next(r for r in self.seen if r.url.path == f"/v3{path}")
        return json.loads(request.content)


def ok(data: object) -> httpx2.Response:
    return httpx2.Response(200, json={"code": 0, "data": data})


@pytest.fixture
def image(tmp_path: Path) -> Path:
    path = tmp_path / "lamp.png"
    path.write_bytes(b"\x89PNG fake")
    return path


def use(monkeypatch: pytest.MonkeyPatch, mock: Mock) -> Mock:
    """Points the CLI's Tripo client at the mock."""
    transport = httpx2.MockTransport(mock.handler)
    connect = functools.partial(
        tripo.connect, transport=transport, sleep=mock.sleeps.append
    )
    monkeypatch.setattr(tripo, "connect", connect)
    monkeypatch.setenv("TRIPO_API_KEY", "tsk-test")
    return mock


def run(argv: list[str], settings: Config, capsys: pytest.CaptureFixture[str]) -> dict:
    cli.main(argv, settings)
    return json.loads(capsys.readouterr().out)


def test_views_uploads_the_image_and_saves_each_view(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock = use(
        monkeypatch, Mock(["queued", "success"], {"generate_multiview_image": VIEWS})
    )
    result = run(["views", str(image), "-o", "lamp-views", "--yes"], settings, capsys)

    upload = mock.seen[0]
    assert upload.headers["Authorization"] == "Bearer tsk-test"
    assert b'name="file"; filename="lamp.png"' in upload.content
    assert mock.posted("/generation/image-to-multiview") == {"input": "file_1"}
    names = sorted(Path(f).name for f in result["files"])
    assert names == [f"lamp-views.{v}.png" for v in ("back", "front", "left", "right")]
    cdn = [r for r in mock.seen if r.url.host == "cdn.tripo.test"]
    assert cdn and all("Authorization" not in r.headers for r in cdn)
    recipe = json.loads((isolated / "models" / "lamp-views.json").read_text())
    assert recipe["service"] == "Tripo API /generation/image-to-multiview"
    assert (recipe["request_id"], recipe["estimated_usd"], recipe["billed_usd"]) == (
        "task-1",
        0.1,
        0.4,
    )
    assert recipe["settings"] == {"input": str(image)}
    ledger = json.loads((isolated / "spend.jsonl").read_text())
    assert (ledger["service"], ledger["id"]) == ("tripo", "task-1")


def test_edit_views_sends_one_prompt_per_view(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock = use(monkeypatch, Mock(["success"]))
    argv = ["edit-views", "task-0", "--back", "add a handle", "--left", "no wheel"]
    result = run([*argv, "-o", "v2", "--dry-run"], settings, capsys)
    assert mock.seen == [] and result["estimated_usd"] == 0.1
    assert result["requests"][0]["body"] == {
        "input": "task-0",
        "prompts": [
            {"view": "left", "prompt": "no wheel"},
            {"view": "back", "prompt": "add a handle"},
        ],
    }


def test_model_from_a_views_task_is_p1_without_texture(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock = use(monkeypatch, Mock(["running", "success"]))
    argv = ["model", "--views", "task-0", "-o", "lamp.glb", "--face-limit", "4000"]
    result = run([*argv, "--seed", "7", "--yes"], settings, capsys)
    assert mock.posted("/generation/multiview-to-model") == {
        "model": "P1-20260311",
        "texture": False,
        "pbr": False,
        "inputs": [{"task_id": "task-0"}],
        "face_limit": 4000,
        "model_seed": 7,
    }
    glb = isolated / "models" / "lamp.glb"
    assert glb.read_bytes() == GLB
    assert result["files"] == [str(glb), str(glb.with_name("lamp.rendered_image.webp"))]
    recipe = json.loads(glb.with_name("lamp.glb.json").read_text())
    assert (recipe["model"], recipe["seed"], recipe["estimated_usd"]) == (
        "P1-20260311",
        7,
        0.4,
    )
    assert not glb.with_name("lamp.glb.task.json").exists()


def test_a_textured_model_sends_the_texture_model_and_delight(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    tmp_path: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use(monkeypatch, Mock(["success"]))
    back = tmp_path / "back.png"
    back.write_bytes(b"\x89PNG back")
    argv = [
        "model",
        str(image),
        "--back",
        str(back),
        "-o",
        "lamp.glb",
        "--series",
        "p2",
    ]
    argv += ["--texture", "--texture-quality", "detailed", "--seed", "3", "--dry-run"]
    result = run(argv, settings, capsys)
    request = result["requests"][0]
    body = request["body"]
    assert request["url"].endswith("/generation/multiview-to-model")
    assert body["inputs"] == [{"front": str(image)}, {"back": str(back)}]
    assert (body["model"], body["texture_version"], body["delight"]) == (
        "P2-20260801",
        "v3.5-20260815",
        True,
    )
    assert (body["texture_seed"], body["pbr"]) == (3, True)
    assert result["estimated_usd"] == pytest.approx(1.3)


def test_texture_resends_the_views_and_uploads_a_local_glb(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    tmp_path: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock = use(monkeypatch, Mock(["success"]))
    model = tmp_path / "shape.glb"
    model.write_bytes(GLB)
    back = tmp_path / "back.png"
    back.write_bytes(b"\x89PNG back")
    argv = ["texture", str(model), "--front", str(image), "--back", str(back)]
    run(
        [*argv, "-o", "lamp-tex.glb", "--seed", "5", "--no-bake", "--yes"],
        settings,
        capsys,
    )
    uploads = [r for r in mock.seen if r.url.path == "/v3/files"]
    assert b"model/gltf-binary" in uploads[0].content
    assert mock.posted("/models/texture") == {
        "input": "file_1",
        "model": "v3.5-20260815",
        "pbr": True,
        "delight": True,
        "bake": False,
        "texture_quality": "standard",
        "texture_prompt": {"images": [{"front": "file_2"}, {"back": "file_3"}]},
        "texture_seed": 5,
    }


def test_a_rerun_resumes_with_the_saved_recipe_even_when_inputs_moved(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock = use(monkeypatch, Mock(["success"]))
    record = {
        "service": "Tripo API /generation/image-to-model",
        "model": "P1-20260311",
        "prompt": "first.png",
        "settings": {"input": "first.png"},
        "estimated_usd": 0.4,
        "seed": 3,
    }
    task_file = isolated / "models" / "lamp.glb.task.json"
    task_file.parent.mkdir(parents=True)
    task_file.write_text(json.dumps({"task_id": "task-1", "record": record}))
    cli.main(["model", "moved-away.png", "-o", "lamp.glb", "--seed", "9"], settings)
    paths = [r.url.path for r in mock.seen]
    assert paths == ["/v3/tasks/task-1", "/out/model.glb", "/out/preview.webp"]
    assert "Resuming task task-1" in capsys.readouterr().err
    written = json.loads((isolated / "models" / "lamp.glb.json").read_text())
    assert (written["prompt"], written["seed"]) == ("first.png", 3)


def test_a_dry_run_ignores_a_started_task(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock = use(monkeypatch, Mock(["success"]))
    task_file = isolated / "models" / "lamp.glb.task.json"
    task_file.parent.mkdir(parents=True)
    task_file.write_text(json.dumps({"task_id": "task-1", "record": {}}))
    result = run(["model", str(image), "-o", "lamp.glb", "--dry-run"], settings, capsys)
    assert mock.seen == [] and result["dry_run"]
    assert result["requests"][0]["body"]["input"] == str(image)
    assert result["estimated_usd"] == 0.4


def test_a_model_task_without_a_model_keeps_its_task_file(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use(monkeypatch, Mock(["success"], {"rendered_image_url": f"{CDN}/preview.webp"}))
    with pytest.raises(SystemExit):
        cli.main(["model", str(image), "-o", "lamp.glb", "--yes"], settings)
    assert "no model_url" in json.loads(capsys.readouterr().out)["error"]
    assert (isolated / "models" / "lamp.glb.task.json").exists()


def test_a_failed_task_reports_the_reason(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use(monkeypatch, Mock(["failed"]))
    with pytest.raises(SystemExit):
        cli.main(["model", str(image), "-o", "lamp.glb", "--yes"], settings)
    assert "task task-1 failed" in json.loads(capsys.readouterr().out)["error"]


def test_http_429_waits_for_retry_after(settings: Config) -> None:
    mock = Mock(["success"])
    mock.busy = 2
    transport = httpx2.MockTransport(mock.handler)
    client = tripo.connect(settings.model, "k", transport, mock.sleeps.append)
    assert client.balance() == 1999.5
    assert mock.sleeps == [3.0, 3.0]


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


def test_balance_shows_credits_usage_and_the_running_totals(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use(monkeypatch, Mock(["success"]))
    result = run(["balance"], settings, capsys)
    assert (result["tripo_credits"], result["tripo_usd"]) == (1999.5, 20.0)
    assert result["tripo_usage"][0]["credits_consumed"] == 10.0
    assert result["spent_usd"] == {"openai": 0, "tripo": 0}


def test_a_model_needs_yes(
    monkeypatch: pytest.MonkeyPatch, image: Path, settings: Config
) -> None:
    mock = use(monkeypatch, Mock(["success"]))
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["model", str(image), "-o", "lamp.glb"], settings)
    assert exit_info.value.code == cli.NEEDS_YES and mock.seen == []


def test_bad_inputs_are_refused(settings: Config, image: Path) -> None:
    with pytest.raises(ValueError, match="front view"):
        tripo.model(settings.model, "x.glb", views={"back": image})
    with pytest.raises(ValueError, match="one image"):
        tripo.model(settings.model, "x.glb")
    with pytest.raises(ValueError, match="50 to 20000"):
        tripo.model(settings.model, "x.glb", image=image, face_limit=30_000)
    with pytest.raises(ValueError, match="1 to 4 views"):
        tripo.edit_multiview(settings.model, "t", {}, "v")


def test_views_without_all_four_views_fail_and_keep_the_task(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    isolated: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    three = {k: v for k, v in VIEWS.items() if not k.startswith("back")}
    use(monkeypatch, Mock(["success"], {"generate_multiview_image": three}))
    with pytest.raises(SystemExit):
        cli.main(["views", str(image), "-o", "v", "--yes"], settings)
    assert "no back_view_url" in json.loads(capsys.readouterr().out)["error"]
    assert (isolated / "models" / "v.task.json").exists()


def test_model_refuses_views_and_local_images_together(
    monkeypatch: pytest.MonkeyPatch,
    image: Path,
    settings: Config,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use(monkeypatch, Mock(["success"]))
    with pytest.raises(SystemExit):
        cli.main(
            ["model", str(image), "--views", "t", "-o", "x.glb", "--dry-run"], settings
        )
    assert "not both" in json.loads(capsys.readouterr().out)["error"]


def test_a_task_is_counted_once_when_its_download_is_retried(
    monkeypatch: pytest.MonkeyPatch,
    settings: Config,
    isolated: Path,
) -> None:
    use(monkeypatch, Mock(["success"]))
    record = {
        "service": "s",
        "model": "m",
        "prompt": "p",
        "settings": {},
        "estimated_usd": 0.4,
    }
    task_file = isolated / "models" / "lamp.glb.task.json"
    task_file.parent.mkdir(parents=True)
    for _ in range(2):
        task_file.write_text(json.dumps({"task_id": "task-1", "record": record}))
        cli.main(["model", "x.png", "-o", "lamp.glb"], settings)
    assert len((isolated / "spend.jsonl").read_text().splitlines()) == 1
