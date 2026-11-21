"""Tripo tasks (API v3, developers.tripo3d.ai, checked 2026-11-21).

Every Tripo step is a task: `POST <endpoint>` with JSON options starts it, `GET /tasks/{id}`
polls it, and its `output` holds the result URLs. One `Task` describes any of them. A local
image anywhere in the options is a `Path`; `Tripo.start` uploads it (`POST /files`) and puts
its file_token in its place. To add a step, write a function that returns its Task, like
`image_to_model` and `multiview_to_model`.

Every response is `{"code": 0, "data": {...}}`, or a non-zero code with `message` and
`suggestion`.
"""

import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import httpx2

from orrery_art.config import ModelSettings, out_path

TEXTURE_QUALITIES = ("standard", "detailed")
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
VIEWS = ("front", "left", "back", "right")
RUNNING = {"queued", "running", "unknown"}


class TripoError(Exception):
    """The API refused a request, or a task failed."""


@dataclass(frozen=True)
class Task:
    """One Tripo task. endpoint: the path under the API, for example
    `/generation/image-to-model`. body: its JSON options, with a Path for each local image.
    out: the main output path under build/art/models/ (the `model_url` result). credits: the
    estimated cost."""

    endpoint: str
    body: dict[str, Any]
    out: str
    credits: int

    @property
    def path(self) -> Path:
        return out_path("models", self.out)

    def shown(self) -> dict[str, Any]:
        """The body as a dry run shows it: each image as `<upload of PATH>`."""
        return _walk(self.body, lambda path: f"<file_token of the upload of {path}>")


def _walk(value: Any, upload: Callable[[Path], str]) -> Any:
    """Returns value with each Path replaced by upload(path)."""
    if isinstance(value, Path):
        return upload(value)
    if isinstance(value, dict):
        return {key: _walk(item, upload) for key, item in value.items()}
    if isinstance(value, list):
        return [_walk(item, upload) for item in value]
    return value


def _image(path: Path) -> Path:
    if path.suffix.lower() not in IMAGE_TYPES:
        raise ValueError(f"{path}: Tripo takes a .png or .jpg image")
    if not path.is_file():
        raise ValueError(f"{path}: no such image")
    return path


def _model_options(
    settings: ModelSettings,
    texture_quality: str,
    face_limit: int | None,
    seed: int | None,
) -> dict[str, Any]:
    """The options that image-to-model and multiview-to-model share: a textured PBR model.
    Blender clean-up sets the real size later, so `auto_size` stays off."""
    if texture_quality not in TEXTURE_QUALITIES:
        raise ValueError(
            f"texture quality must be one of {', '.join(TEXTURE_QUALITIES)}"
        )
    if face_limit is not None and face_limit <= 0:
        raise ValueError("the face limit must be positive")
    body: dict[str, Any] = {
        "model": settings.version,
        "texture": True,
        "pbr": True,
        "texture_quality": texture_quality,
    }
    if face_limit is not None:
        body["face_limit"] = face_limit
    if seed is not None:
        body["model_seed"] = seed
        body["texture_seed"] = seed
    return body


def _credits(settings: ModelSettings, kind: str, texture_quality: str) -> int:
    extra = settings.detailed_texture_credits if texture_quality == "detailed" else 0
    return settings.credits[kind] + extra


def _glb(out: str) -> str:
    if not out.endswith(".glb"):
        raise ValueError(f"{out}: the model output is a .glb")
    out_path("models", out)
    return out


def image_to_model(
    settings: ModelSettings,
    image: Path,
    out: str,
    texture_quality: str = "standard",
    face_limit: int | None = None,
    seed: int | None = None,
) -> Task:
    """A textured model from one image, best a single object on a plain background.
    face_limit: the most faces, None for adaptive. seed: the geometry and texture seed."""
    body = {
        "input": _image(image),
        **_model_options(settings, texture_quality, face_limit, seed),
    }
    credits = _credits(settings, "image-to-model", texture_quality)
    return Task("/generation/image-to-model", body, _glb(out), credits)


def multiview_to_model(
    settings: ModelSettings,
    views: dict[str, Path],
    out: str,
    texture_quality: str = "standard",
    face_limit: int | None = None,
    seed: int | None = None,
) -> Task:
    """A textured model from 2 to 4 views of one object (front, left, back, right) in the
    same light. The front view is required."""
    unknown = set(views) - set(VIEWS)
    if unknown or "front" not in views or len(views) < 2:
        raise ValueError(
            f"give the front view and at least one more of {', '.join(VIEWS)}"
        )
    inputs = [{view: _image(views[view])} for view in VIEWS if view in views]
    body = {
        "inputs": inputs,
        **_model_options(settings, texture_quality, face_limit, seed),
    }
    credits = _credits(settings, "multiview-to-model", texture_quality)
    return Task("/generation/multiview-to-model", body, _glb(out), credits)


class Tripo:
    """A client for the Tripo API; make it with `connect`. http has the API base_url and the
    key; transport, for tests, also carries the downloads."""

    def __init__(
        self, http: httpx2.Client, transport: httpx2.BaseTransport | None = None
    ) -> None:
        self.http = http
        self.transport = transport

    def upload(self, image: Path) -> str:
        """Uploads an image and returns its file_token."""
        files = {
            "file": (image.name, image.read_bytes(), IMAGE_TYPES[image.suffix.lower()])
        }
        return str(self._data(self.http.post("/files", files=files))["file_token"])

    def start(self, task: Task) -> str:
        """Uploads the task's images, starts it and returns its task_id."""
        body = _walk(task.body, self.upload)
        return str(self._data(self.http.post(task.endpoint, json=body))["task_id"])

    def balance(self) -> float:
        """Returns the available credits. It costs nothing."""
        return float(self._data(self.http.get("/account/balance"))["balance"])

    def task(self, task_id: str) -> dict[str, Any]:
        """Returns the task data: status, progress, output, credits_consumed ..."""
        return self._data(self.http.get(f"/tasks/{task_id}"))

    def wait(
        self,
        task_id: str,
        poll_seconds: float,
        timeout_seconds: float,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> dict[str, Any]:
        """Polls a task until it succeeds and returns its data. Raises TripoError when the
        task fails or the timeout ends (the task keeps running; rerun to resume)."""
        end = clock() + timeout_seconds
        last = ""
        while True:
            data = self.task(task_id)
            status = str(data.get("status", "unknown"))
            line = f"{status} {data.get('progress', 0)}%"
            if line != last:
                print(f"{task_id}: {line}", file=sys.stderr)
                last = line
            if status == "success":
                return data
            if status not in RUNNING:
                reason = data.get("error_message") or data.get("error_code") or status
                raise TripoError(f"task {task_id} {status}: {reason}")
            if clock() >= end:
                raise TripoError(
                    f"task {task_id} is still {status}; rerun to wait for it"
                )
            sleep(poll_seconds)

    def download(self, output: dict[str, Any], path: Path) -> list[Path]:
        """Downloads each result URL of a task output. `model_url` goes to path; any other
        URL goes to `<path stem>.<key><n><ext>` beside it. The client has no API key, so the
        key never goes to the CDN. Returns the files."""
        urls = [
            (key, i, url)
            for key, value in output.items()
            for i, url in enumerate(value if isinstance(value, list) else [value])
            if isinstance(url, str) and url.startswith(("http://", "https://"))
        ]
        saved: list[Path] = []
        path.parent.mkdir(parents=True, exist_ok=True)
        with httpx2.Client(
            timeout=300, follow_redirects=True, transport=self.transport
        ) as cdn:
            for key, i, url in urls:
                ext = PurePosixPath(urlparse(url).path).suffix
                many = isinstance(output[key], list)
                target = (
                    path
                    if key == "model_url"
                    else path.with_name(f"{path.stem}.{key}{i if many else ''}{ext}")
                )
                response = cdn.get(url)
                response.raise_for_status()
                target.write_bytes(response.content)
                saved.append(target)
        return saved

    @staticmethod
    def _data(response: httpx2.Response) -> dict[str, Any]:
        """Returns the `data` of a response, or raises TripoError with the API's message."""
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {}
        if response.is_error or payload.get("code") != 0:
            message = payload.get("message") or response.reason_phrase
            suggestion = payload.get("suggestion")
            raise TripoError(
                f"{response.request.method} {response.request.url.path}: HTTP "
                f"{response.status_code}, code {payload.get('code')}: {message}"
                + (f" ({suggestion})" if suggestion else "")
            )
        return payload["data"]


def connect(
    settings: ModelSettings, key: str, transport: httpx2.BaseTransport | None = None
) -> Tripo:
    """Returns a client for the API with the key in its Authorization header. transport:
    for tests."""
    http = httpx2.Client(
        base_url=settings.api,
        headers={"Authorization": f"Bearer {key}"},
        timeout=120,
        transport=transport,
    )
    return Tripo(http, transport)
