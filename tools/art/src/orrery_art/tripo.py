"""Tripo tasks (API v3, developers.tripo3d.ai and docs/research/asset-prompting.md §2-3).

Every Tripo step is a task: `POST <endpoint>` with JSON options starts it, `GET /tasks/{id}`
polls it, and its `output` holds the result URLs. One `Task` describes any of them. A local
file anywhere in the options is a `Path`; `Tripo.start` uploads it (`POST /files`) and puts
its file_token in its place. To add a step (mesh/decimate, mesh/uv ...), write one more
function that returns its Task.

Every response is `{"code": 0, "data": {...}}`, or a non-zero code with `message` and
`suggestion`. HTTP 429 (rate limit 1007, or a full concurrency pool 2000: image tasks run
one at a time on an account) waits for `Retry-After` and tries again.
"""

import json
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import httpx2

from orrery_art.config import ModelSettings, out_path

TEXTURE_QUALITIES = ("standard", "detailed")
TEXTURE_TASK_QUALITIES = ("fast", "standard", "detailed", "extreme")
SERIES = ("p1", "p2", "h")
VIEWS = ("front", "left", "back", "right")
VIEW_KEYS = tuple(f"{view}_view_url" for view in VIEWS)
UPLOAD_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".glb": "model/gltf-binary",
}
# face_limit ranges by series (the P docs; H has no lower bound).
FACE_LIMITS = {"p1": (50, 20_000), "p2": (48, 50_000), "h": (1, 1_500_000)}
RUNNING = {"queued", "running", "unknown"}


class TripoError(Exception):
    """The API refused a request, or a task failed."""


@dataclass(frozen=True)
class Task:
    """One Tripo task. endpoint: the path under the API, for example
    `/generation/image-to-model`. body: its JSON options, with a Path for each local file.
    out: the output name under build/art/models/ (a .glb for a model task). credits: the
    estimated cost. model: the model id for the recipe. expects: the output keys that a
    successful task must return."""

    endpoint: str
    body: dict[str, Any]
    out: str
    credits: float
    model: str = ""
    expects: tuple[str, ...] = ("model_url",)

    @property
    def path(self) -> Path:
        return out_path("models", self.out)

    def shown(self) -> dict[str, Any]:
        """The body as a dry run and the recipe show it: each file as its path."""
        return _walk(self.body, str)


def _walk(value: Any, upload: Callable[[Path], str]) -> Any:
    """Returns value with each Path replaced by upload(path)."""
    if isinstance(value, Path):
        return upload(value)
    if isinstance(value, dict):
        return {key: _walk(item, upload) for key, item in value.items()}
    if isinstance(value, list):
        return [_walk(item, upload) for item in value]
    return value


def _file(path: Path, kinds: tuple[str, ...] = (".png", ".jpg", ".jpeg")) -> Path:
    if path.suffix.lower() not in kinds:
        raise ValueError(f"{path}: Tripo takes {' or '.join(kinds)} here")
    if not path.is_file():
        raise ValueError(f"{path}: no such file")
    return path


def _views(views: dict[str, Path]) -> list[dict[str, Path]]:
    """View-key inputs in the order front, left, back, right. Needs front and one more."""
    unknown = set(views) - set(VIEWS)
    if unknown or "front" not in views or len(views) < 2:
        raise ValueError(
            f"give the front view and at least one more of {', '.join(VIEWS)}"
        )
    return [{view: _file(views[view])} for view in VIEWS if view in views]


def _out(out: str, glb: bool) -> str:
    if glb and not out.endswith(".glb"):
        raise ValueError(f"{out}: a model output is a .glb")
    if not glb and Path(out).suffix:
        raise ValueError(f"{out}: give a name without an extension")
    out_path("models", out)
    return out


def image_to_multiview(settings: ModelSettings, image: Path, out: str) -> Task:
    """Front, left, back and right views of the object in one image (an image task: one at
    a time). The views are saved as `<out>.front.png` ..."""
    credits = settings.credits["image-to-multiview"]
    body = {"input": _file(image)}
    out = _out(out, False)
    return Task("/generation/image-to-multiview", body, out, credits, "", VIEW_KEYS)


def edit_multiview(
    settings: ModelSettings, task_id: str, edits: dict[str, str], out: str
) -> Task:
    """Edits views of an image_to_multiview task: one prompt (at most 1024 characters) for
    each view to change. Costs per edited view."""
    if not edits or set(edits) - set(VIEWS):
        raise ValueError(f"edit 1 to 4 views: {', '.join(VIEWS)}")
    for view, prompt in edits.items():
        if not prompt.strip() or len(prompt) > 1024:
            raise ValueError(f"{view}: the edit prompt must have 1 to 1024 characters")
    prompts = [{"view": view, "prompt": edits[view]} for view in VIEWS if view in edits]
    credits = settings.credits["edit-multiview"] * len(prompts)
    body = {"input": task_id, "prompts": prompts}
    out = _out(out, False)
    return Task("/generation/edit-multiview", body, out, credits, "", VIEW_KEYS)


def model(
    settings: ModelSettings,
    out: str,
    series: str = "p1",
    image: Path | None = None,
    views: dict[str, Path] | None = None,
    from_task: str = "",
    texture: bool = False,
    texture_quality: str = "standard",
    face_limit: int | None = None,
    seed: int | None = None,
) -> Task:
    """A 3D model from exactly one of: one image (image-to-model), 2 to 4 views
    (multiview-to-model), or the task id of an image_to_multiview or edit_multiview task.
    series: p1 (the default: low-poly), p2 or h. texture: off by default, so that the
    texture task runs after a look at the shape. A textured call sends the texture model
    and `delight: true`, so the texture holds no baked light."""
    if sum([image is not None, bool(views), bool(from_task)]) != 1:
        raise ValueError("give one image, 2 to 4 views, or the task id of the views")
    if series not in SERIES:
        raise ValueError(f"series must be one of {', '.join(SERIES)}")
    if texture_quality not in TEXTURE_QUALITIES:
        raise ValueError(
            f"texture quality must be one of {', '.join(TEXTURE_QUALITIES)}"
        )
    low, high = FACE_LIMITS[series]
    if face_limit is not None and not low <= face_limit <= high:
        raise ValueError(f"{series}: the face limit must be {low} to {high}")
    geometry = settings.series[series]
    body: dict[str, Any] = {"model": geometry, "texture": texture, "pbr": texture}
    if image is not None:
        endpoint = "/generation/image-to-model"
        body["input"] = _file(image)
    else:
        endpoint = "/generation/multiview-to-model"
        body["inputs"] = _views(views) if views else [{"task_id": from_task}]
    if face_limit is not None:
        body["face_limit"] = face_limit
    if seed is not None:
        body["model_seed"] = seed
    credits = settings.credits[f"{series}-textured" if texture else series]
    if texture:
        body["texture_quality"] = texture_quality
        body["texture_version"] = settings.texture_model
        body["delight"] = True
        if seed is not None:
            body["texture_seed"] = seed
        if texture_quality == "detailed":
            credits += settings.credits["detailed-texture"]
    return Task(endpoint, body, _out(out, True), credits, geometry)


def texture(
    settings: ModelSettings,
    source: str,
    out: str,
    refs: dict[str, Path] | None = None,
    quality: str = "standard",
    seed: int | None = None,
    bake: bool = True,
) -> Task:
    """New PBR texture maps for a model: source is a task id, or a local .glb. refs: the
    reference views (front alone, or front and more); resend them with every texture task.
    It sends the texture model and `delight: true`."""
    if quality not in TEXTURE_TASK_QUALITIES:
        raise ValueError(
            f"texture quality must be one of {', '.join(TEXTURE_TASK_QUALITIES)}"
        )
    glb = source.endswith(".glb")
    body: dict[str, Any] = {
        "input": _file(Path(source), (".glb",)) if glb else source,
        "model": settings.texture_model,
        "pbr": True,
        "delight": True,
        "bake": bake,
        "texture_quality": quality,
    }
    if refs:
        if set(refs) == {"front"}:
            body["texture_prompt"] = {"image": _file(refs["front"])}
        else:
            body["texture_prompt"] = {"images": _views(refs)}
    if seed is not None:
        body["texture_seed"] = seed
    credits = settings.credits[f"texture-{quality}"]
    return Task(
        "/models/texture", body, _out(out, True), credits, settings.texture_model
    )


def _urls(output: Any, key: str = "") -> Iterator[tuple[str, str]]:
    """Yields (key, url) for each URL in a task output, at any depth."""
    if isinstance(output, dict):
        for name, value in output.items():
            yield from _urls(value, name)
    elif isinstance(output, list):
        for i, value in enumerate(output):
            yield from _urls(value, f"{key}{i}")
    elif isinstance(output, str) and output.startswith(("http://", "https://")):
        yield key, output


def missing(output: dict[str, Any], expects: list[str] | tuple[str, ...]) -> list[str]:
    """The expected output keys that hold no URL in a task output. `model_url` must be at
    the top level, where `Tripo.download` takes the main model from."""
    found = {key for key, _ in _urls(output) if key != "model_url"}
    if isinstance(output.get("model_url"), str):
        found |= {key for key, _ in _urls({"model_url": output["model_url"]})}
    return [key for key in expects if key not in found]


def _label(key: str) -> str:
    """front_view_url -> front, rendered_image_url -> rendered_image."""
    return key.removesuffix("_url").removesuffix("_view")


def _dict(data: dict[str, Any] | list[Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TripoError(f"expected an object from the API, got {type(data).__name__}")
    return data


class Tripo:
    """A client for the Tripo API; make it with `connect`. http has the API base_url and the
    key; transport, for tests, also carries the downloads."""

    def __init__(
        self,
        http: httpx2.Client,
        transport: httpx2.BaseTransport | None = None,
        retries: int = 6,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.http = http
        self.transport = transport
        self.retries = retries
        self.sleep = sleep

    def _send(
        self, method: str, path: str, **options: Any
    ) -> dict[str, Any] | list[Any]:
        """Sends a request and returns its `data`. On HTTP 429 it waits for Retry-After (or
        2, 4, 8 ... s) and tries again, up to `retries` times."""
        attempt = 0
        while True:
            response = self.http.request(method, path, **options)
            if response.status_code != 429 or attempt >= self.retries:
                return self._data(response)
            attempt += 1
            try:
                wait = float(response.headers.get("Retry-After", ""))
            except ValueError:
                wait = min(2.0**attempt, 60.0)
            print(f"Tripo: busy (HTTP 429), waiting {wait:.0f} s", file=sys.stderr)
            self.sleep(wait)

    def upload(self, path: Path) -> str:
        """Uploads an image or a .glb and returns its file_token."""
        files = {
            "file": (path.name, path.read_bytes(), UPLOAD_TYPES[path.suffix.lower()])
        }
        return str(_dict(self._send("POST", "/files", files=files))["file_token"])

    def start(self, task: Task) -> str:
        """Uploads the task's files, starts it and returns its task_id."""
        body = _walk(task.body, self.upload)
        return str(_dict(self._send("POST", task.endpoint, json=body))["task_id"])

    def balance(self) -> float:
        """Returns the available credits. It costs nothing."""
        return float(_dict(self._send("GET", "/account/balance"))["balance"])

    def usage(self) -> dict[str, Any] | list[Any]:
        """Returns the account's usage records (task id, type, credits). It costs nothing."""
        return self._send("GET", "/account/usage")

    def task(self, task_id: str) -> dict[str, Any]:
        """Returns the task data: status, progress, output, credits_consumed ..."""
        return _dict(self._send("GET", f"/tasks/{task_id}"))

    def wait(
        self,
        task_id: str,
        poll_seconds: float,
        timeout_seconds: float,
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
            self.sleep(poll_seconds)

    def download(self, output: dict[str, Any], path: Path) -> list[Path]:
        """Downloads each result URL of a task output at once (the URLs are short-lived).
        `model_url` goes to path; any other URL goes to `<path stem>.<label><ext>` beside
        it, for example `lamp.front.png`. The client has no API key, so the key never goes
        to the CDN. Returns the files."""
        saved: list[Path] = []
        path.parent.mkdir(parents=True, exist_ok=True)
        primary = output.get("model_url")
        client = httpx2.Client(
            timeout=300, follow_redirects=True, transport=self.transport
        )
        with client as cdn:
            for key, url in _urls(output):
                ext = PurePosixPath(urlparse(url).path).suffix
                if key == "model_url" and url == primary and path not in saved:
                    target = path
                else:
                    # Two results with one key name never overwrite each other.
                    target, n = path.with_name(f"{path.stem}.{_label(key)}{ext}"), 1
                    while target in saved or target == path:
                        n += 1
                        target = path.with_name(f"{path.stem}.{_label(key)}{n}{ext}")
                response = cdn.get(url)
                response.raise_for_status()
                target.write_bytes(response.content)
                saved.append(target)
        return saved

    @staticmethod
    def _data(response: httpx2.Response) -> dict[str, Any] | list[Any]:
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
    settings: ModelSettings,
    key: str,
    transport: httpx2.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Tripo:
    """Returns a client for the API with the key in its Authorization header. transport
    and sleep: for tests."""
    http = httpx2.Client(
        base_url=settings.api,
        headers={"Authorization": f"Bearer {key}"},
        timeout=120,
        transport=transport,
    )
    return Tripo(http, transport, settings.retries, sleep)
