"""GPT-Image jobs: the request, the cost estimate, live calls and the optional Batch API.

Live calls are the default (docs/research/asset-prompting.md §1.1: the sources disagree on
Batch for GPT-Image-2.6). A job with reference images goes to `/v1/images/edits` (multipart,
up to 16 images; give each one a numbered role in the prompt); one without goes to
`/v1/images/generations`. A dry run prints the same fields that a paid run sends.
"""

import base64
import hashlib
import json
import math
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import openai
from openai import omit
from openai.types import ImagesResponse
from openai.types.images_response import Usage
from PIL import Image

from orrery_art import manifest
from orrery_art.config import ImageSettings, out_path

GENERATIONS = "/v1/images/generations"
EDITS = "/v1/images/edits"
Quality = Literal["low", "medium", "high", "xhigh", "max"]
Complexity = Literal["low", "medium", "high"]
Format = Literal["png", "webp", "jpeg"]
QUALITIES: dict[str, Quality] = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
    "max": "max",
}
COMPLEXITIES: dict[str, Complexity] = {"low": "low", "medium": "medium", "high": "high"}
FORMATS: dict[str, Format] = {
    ".png": "png",
    ".webp": "webp",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
}
REF_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
MAX_REFS = 16
# The official token calculator (developers.openai.com/api/docs/guides/image-generation,
# GptImageTokenCalculator, checked 2026-11-21): a tile grid per quality on the long edge, and
# for GPT-Image-2.6 a factor on top. 1024x1024 medium on 2.6 gives 1449 output tokens.
GRID = {"low": 16, "medium": 24, "high": 48, "xhigh": 64, "max": 96}
SCALE_2_6 = {"low": 4.2, "medium": 3.3, "high": 1.0, "xhigh": 1.0, "max": 1.0}
MODEL_FAMILIES = ("gpt-image-2.5-", "gpt-image-2.6-")
BATCH_DONE = {"completed", "failed", "expired", "cancelled"}


@dataclass(frozen=True)
class ImageJob:
    """One image. out: the path under build/art/images/; its extension picks the format.
    model: the model id. size: WIDTHxHEIGHT. transparent: a real alpha background (.png or
    .webp). complexity: low, medium or high planning, None for the model default. refs:
    reference images, which make it an edit."""

    prompt: str
    out: str
    model: str
    size: str
    quality: str
    transparent: bool = False
    complexity: str | None = None
    refs: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError(f"{self.out}: the prompt is empty")
        out_path("images", self.out)
        if Path(self.out).suffix.lower() not in FORMATS:
            raise ValueError(f"{self.out}: use one of {', '.join(FORMATS)}")
        if self.quality not in QUALITIES:
            raise ValueError(
                f"{self.out}: quality must be one of {', '.join(QUALITIES)}"
            )
        if self.complexity is not None and self.complexity not in COMPLEXITIES:
            raise ValueError(
                f"{self.out}: complexity must be one of {', '.join(COMPLEXITIES)}"
            )
        if self.transparent and self.format == "jpeg":
            raise ValueError(f"{self.out}: a transparent image needs .png or .webp")
        if len(self.refs) > MAX_REFS:
            raise ValueError(f"{self.out}: at most {MAX_REFS} reference images")
        for ref in self.refs:
            if Path(ref).suffix.lower() not in REF_TYPES or not Path(ref).is_file():
                raise ValueError(f"{self.out}: no .png, .jpg or .webp reference {ref}")
        parse_size(self.size)

    @property
    def format(self) -> Format:
        return FORMATS[Path(self.out).suffix.lower()]

    @property
    def path(self) -> Path:
        return out_path("images", self.out)

    @property
    def endpoint(self) -> str:
        return EDITS if self.refs else GENERATIONS


def parse_size(size: str) -> tuple[int, int]:
    """Returns (width, height) of a WIDTHxHEIGHT size. Raises ValueError outside the model
    limits: both edges divisible by 16, an edge at most 3840, a ratio at most 3:1, and
    655,360 to 8,294,400 pixels (so the smallest is 1024x640)."""
    try:
        width, height = (int(n) for n in size.lower().split("x"))
    except ValueError:
        raise ValueError(
            f"size {size!r}: give WIDTHxHEIGHT, for example 1024x1024"
        ) from None
    problems = []
    if width % 16 or height % 16:
        problems.append("both edges must be divisible by 16")
    if max(width, height) > 3840:
        problems.append("an edge must be at most 3840")
    if min(width, height) <= 0 or max(width, height) / min(width, height) > 3:
        problems.append("the ratio must be at most 3:1")
    if not 655_360 <= width * height <= 8_294_400:
        problems.append("it must have 655,360 to 8,294,400 pixels")
    if problems:
        raise ValueError(f"size {size}: {'; '.join(problems)}")
    return width, height


def model_id(settings: ImageSettings, name: str | None) -> str:
    """Returns the model id for a name in config.toml (flare, sunburst), or the default."""
    key = name or settings.model
    if key not in settings.models:
        raise ValueError(f"model must be one of {', '.join(settings.models)}")
    return settings.models[key]


def job_from_line(line: dict[str, Any], settings: ImageSettings) -> ImageJob:
    """Makes a job from one JSONL object: `prompt` and `out` (strings), and optionally
    `model` (flare, sunburst), `size`, `quality`, `complexity`, `transparent` (a JSON
    boolean) and `refs` (a list of image paths). Raises TypeError on a wrong type and
    ValueError on an unknown key, so that a typo never becomes a paid prompt."""
    known = {
        "prompt",
        "out",
        "model",
        "size",
        "quality",
        "complexity",
        "transparent",
        "refs",
    }
    unknown = set(line) - known
    if unknown:
        raise ValueError(f"unknown keys {', '.join(sorted(unknown))}")
    for key in ("prompt", "out", "model", "size", "quality", "complexity"):
        if key in line and not isinstance(line[key], str):
            raise TypeError(f"{key} must be a string")
    if not isinstance(line.get("transparent", False), bool):
        raise TypeError("transparent must be true or false")
    refs = line.get("refs", [])
    if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
        raise TypeError("refs must be a list of paths")
    return ImageJob(
        prompt=line["prompt"],
        out=line["out"],
        model=model_id(settings, line.get("model")),
        size=line.get("size", settings.size),
        quality=line.get("quality", settings.quality),
        transparent=line.get("transparent", False),
        complexity=line.get("complexity"),
        refs=tuple(refs),
    )


def read_jobs(path: Path, settings: ImageSettings) -> list[ImageJob]:
    """Reads a JSONL file of jobs. Raises ValueError that names each bad line, and each
    pair of jobs whose outputs collide (the same path, or one inside the other)."""
    try:
        lines = path.read_text().splitlines()
    except OSError as error:
        raise ValueError(
            f"{path}: cannot read the jobs file ({error.strerror})"
        ) from None
    jobs: list[ImageJob] = []
    problems: list[str] = []
    for number, text in enumerate(lines, 1):
        if not text.strip():
            continue
        try:
            jobs.append(job_from_line(json.loads(text), settings))
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            problems.append(f"line {number}: {error}")
    # Each job writes its image and its recipe; no two may be one path, or a file and a
    # folder of each other.
    seen: set[Path] = set()
    for job in jobs:
        mine = {job.path, manifest.manifest_path(job.path)}
        parents = {parent for p in mine for parent in p.parents}
        if job.path in seen:
            problems.append(f"two jobs write {job.out}")
        elif seen & (mine | parents) or any(p in o.parents for p in mine for o in seen):
            problems.append(f"{job.out} and another output are a file and its folder")
        seen |= mine
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    if not jobs:
        raise ValueError(f"{path}: no jobs")
    return jobs


def output_tokens(width: int, height: int, quality: str, model: str) -> int:
    """The output tokens of one image, by the official calculator."""
    if not model.startswith(MODEL_FAMILIES):
        raise ValueError(f"{model}: the estimate knows only GPT-Image-2.5 and 2.6")
    tiles = GRID[quality]
    long_edge, short_edge = max(width, height), min(width, height)
    s = tiles / (long_edge / short_edge)
    c = math.floor(s)
    short_tiles = c + c % 2 if s - c == 0.5 else math.floor(s + 0.5)
    tokens = math.ceil(tiles * short_tiles * (2e6 + width * height) / 4e6)
    scale = SCALE_2_6[quality] if model.startswith("gpt-image-2.6-") else 1.0
    return math.floor(tokens * scale + 0.5)


def estimate_usd(job: ImageJob, settings: ImageSettings, batch: bool) -> float:
    """The estimated cost of a job: its output tokens, about one token for each four
    characters of the prompt, and ref_image_tokens for each reference (a guess: OpenAI
    gives no formula for input images). The Batch API bills half."""
    width, height = parse_size(job.size)
    out_tokens = output_tokens(width, height, job.quality, job.model)
    text_tokens = math.ceil(len(job.prompt) / 4)
    image_tokens = len(job.refs) * settings.ref_image_tokens
    usd = (
        text_tokens * settings.text_in_usd_per_m
        + image_tokens * settings.image_in_usd_per_m
        + out_tokens * settings.image_out_usd_per_m
    ) / 1e6
    return usd / 2 if batch else usd


def billed_usd(
    usage: Usage | None, settings: ImageSettings, batch: bool
) -> float | None:
    """The cost from the token usage that the API returns, or None without usage."""
    if usage is None:
        return None
    images_in = usage.input_tokens_details.image_tokens
    text_in = usage.input_tokens - images_in
    usd = (
        text_in * settings.text_in_usd_per_m
        + images_in * settings.image_in_usd_per_m
        + usage.output_tokens * settings.image_out_usd_per_m
    ) / 1e6
    return round(usd / 2 if batch else usd, 4)


def request_body(job: ImageJob) -> dict[str, Any]:
    """The fields of the request for a job. An edit sends the `image` files as multipart."""
    body: dict[str, Any] = {
        "model": job.model,
        "prompt": job.prompt,
        "size": job.size,
        "quality": job.quality,
        "output_format": job.format,
    }
    if job.transparent:
        body["background"] = "transparent"
    if job.complexity:
        body["complexity"] = job.complexity
    if job.refs:
        body["image"] = list(job.refs)
    return body


@dataclass(frozen=True)
class ImageResult:
    out: str
    ok: bool
    billed_usd: float | None = None
    error: str = ""


def alpha_problem(path: Path) -> str:
    """Returns "" when an image has a fully clear pixel, else why not. It reads the decoded
    alpha, so an indexed PNG with a transparency chunk counts too."""
    with Image.open(path) as image:
        low, _ = image.convert("RGBA").getchannel("A").getextrema()
    return "" if low == 0 else "the image has no transparent pixel"


def _save(
    job: ImageJob,
    response: ImagesResponse,
    settings: ImageSettings,
    batch: bool,
    request_id: str,
) -> ImageResult:
    """Writes the image of a response unedited, its manifest, and checks its alpha."""
    data = response.data[0].b64_json if response.data else None
    if not data:
        return ImageResult(job.out, False, error="the response holds no image")
    job.path.parent.mkdir(parents=True, exist_ok=True)
    job.path.write_bytes(base64.b64decode(data))
    billed = billed_usd(response.usage, settings, batch)
    usage = response.usage.model_dump() if response.usage else None
    manifest.write(
        job.path,
        manifest.Manifest(
            service=f"OpenAI Images API {job.endpoint}",
            model=job.model,
            mode="batch" if batch else "live",
            prompt=job.prompt,
            settings={**request_body(job), "usage": usage},
            estimated_usd=round(estimate_usd(job, settings, batch), 4),
            billed_usd=billed,
            request_id=request_id,
        ),
    )
    problem = alpha_problem(job.path) if job.transparent else ""
    return ImageResult(job.out, not problem, billed, problem)


def generate(
    client: openai.OpenAI, job: ImageJob, settings: ImageSettings
) -> ImageResult:
    """Makes one image now, at the live price."""
    background: Literal["transparent", "auto"] = (
        "transparent" if job.transparent else "auto"
    )
    complexity = COMPLEXITIES[job.complexity] if job.complexity else omit
    if job.refs:
        files = [
            (Path(r).name, Path(r).read_bytes(), REF_TYPES[Path(r).suffix.lower()])
            for r in job.refs
        ]
        response = client.images.edit(
            image=files,
            model=job.model,
            prompt=job.prompt,
            size=job.size,
            quality=QUALITIES[job.quality],
            output_format=job.format,
            background=background,
            complexity=complexity,
        )
    else:
        response = client.images.generate(
            model=job.model,
            prompt=job.prompt,
            size=job.size,
            quality=QUALITIES[job.quality],
            output_format=job.format,
            background=background,
            complexity=complexity,
        )
    return _save(job, response, settings, batch=False, request_id="")


def jobs_hash(jobs: list[ImageJob]) -> str:
    """A short hash of the jobs, which ties a batch state file to its jobs."""
    text = json.dumps([asdict(job) for job in jobs], sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass
class BatchState:
    """The batch state file (see state_path). A rerun with the same jobs resumes the batch
    instead of paying for a new one."""

    jobs_hash: str
    batch_id: str
    status: str = "submitted"
    results: list[ImageResult] | None = None

    @staticmethod
    def read(path: Path) -> "BatchState | None":
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        results = data.get("results")
        return BatchState(
            jobs_hash=data["jobs_hash"],
            batch_id=data["batch_id"],
            status=data.get("status", "submitted"),
            results=None if results is None else [ImageResult(**r) for r in results],
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write a new file and swap it in, so an interrupted write never loses the batch id.
        partial = path.with_name(path.name + ".partial")
        partial.write_text(json.dumps(asdict(self), indent=2) + "\n")
        partial.replace(path)


def state_path(jobs_file: Path) -> Path:
    """build/art/batches/<name>-<hash of the full path>.json, so that two jobs files with one
    name in two folders keep their own state."""
    source = jobs_file.resolve()
    digest = hashlib.sha256(str(source).encode()).hexdigest()[:8]
    return out_path("batches", f"{source.stem}-{digest}.json")


def submit(client: openai.OpenAI, jobs: list[ImageJob]) -> str:
    """Uploads the jobs as a Batch input file, starts the batch and returns its id. The
    custom_id of each line is the job index. Edits (jobs with refs) cannot go in a batch."""
    if any(job.refs for job in jobs):
        raise ValueError("a batch takes no reference images; run the set live")
    lines = [
        json.dumps(
            {
                "custom_id": str(i),
                "method": "POST",
                "url": GENERATIONS,
                "body": request_body(job),
            }
        )
        for i, job in enumerate(jobs)
    ]
    upload = client.files.create(
        file=("orrery-art-batch.jsonl", ("\n".join(lines) + "\n").encode()),
        purpose="batch",
    )
    batch = client.batches.create(
        input_file_id=upload.id, endpoint=GENERATIONS, completion_window="24h"
    )
    return batch.id


def wait(
    client: openai.OpenAI,
    batch_id: str,
    poll_seconds: float,
    keep_waiting: bool,
    sleep: Callable[[float], None] = time.sleep,
) -> openai.types.Batch:
    """Polls the batch until it is done (or once, when keep_waiting is False) and prints each
    new status to stderr. Returns the last Batch."""
    last = ""
    while True:
        try:
            batch = client.batches.retrieve(batch_id)
        except (openai.APIConnectionError, openai.InternalServerError) as error:
            if not keep_waiting:
                raise
            print(
                f"{batch_id}: status check failed, retrying: {error}", file=sys.stderr
            )
            sleep(poll_seconds)
            continue
        counts = batch.request_counts
        status = batch.status
        if counts is not None:
            status += f" {counts.completed + counts.failed}/{counts.total}"
        if status != last:
            print(f"{batch_id}: {status}", file=sys.stderr)
            last = status
        if batch.status in BATCH_DONE or not keep_waiting:
            return batch
        sleep(poll_seconds)


def collect(
    client: openai.OpenAI,
    batch: openai.types.Batch,
    jobs: list[ImageJob],
    settings: ImageSettings,
) -> list[ImageResult]:
    """Saves the images of a finished batch. Returns one result for each job, in order."""
    results: dict[int, ImageResult] = {}
    for file_id in (batch.output_file_id, batch.error_file_id):
        if not file_id:
            continue
        for text in client.files.content(file_id).text.splitlines():
            if not text.strip():
                continue
            row = json.loads(text)
            i = int(row["custom_id"])
            response = row.get("response") or {}
            body = response.get("body") or {}
            if response.get("status_code") == 200 and body.get("data"):
                parsed = ImagesResponse.model_validate(body)
                results[i] = _save(
                    jobs[i], parsed, settings, batch=True, request_id=batch.id
                )
            else:
                error = body.get("error") or row.get("error") or {}
                message = error.get("message", "no image returned")
                results[i] = ImageResult(jobs[i].out, False, error=message)
    reason = f"batch {batch.status}"
    if batch.errors is not None and batch.errors.data:
        reason += ": " + "; ".join(e.message or "" for e in batch.errors.data)
    return [
        results.get(i, ImageResult(job.out, False, error=reason))
        for i, job in enumerate(jobs)
    ]
