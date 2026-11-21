"""orrery-art: GPT-Image art and Tripo props for Orrery. See tools/art/README.md.

    orrery-art image --prompt "..." -o decals/clock.png [--size 1024x1024] [--quality medium]
    orrery-art batch jobs.jsonl [--no-wait]
    orrery-art model build/art/images/lamp.png -o lamp.glb [--texture-quality detailed]
    orrery-art check

`image`, `batch` and `model` are paid. Each one prints its estimate, refuses a run above the
spend cap, and sends nothing without `--yes`. `--dry-run` prints the requests and the
estimate and sends nothing. Outputs and their manifests go to build/art/ (git-ignored).
The result is one JSON object on stdout; progress goes to stderr.
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import openai

from orrery_art import images, manifest, tripo
from orrery_art.config import Config, SpendError, check_spend, load
from orrery_art.keys import MissingKeyError, api_key

# Exit status when a paid run needs --yes.
NEEDS_YES = 2


class UsageError(Exception):
    """A bad argument or job."""


def emit(**fields: Any) -> None:
    """Prints the result object on stdout."""
    print(json.dumps(fields, indent=2))


def gate(
    args: argparse.Namespace, config: Config, estimate_usd: float, requests: list[Any]
) -> bool:
    """Runs the checks before a paid call. Returns True when the call may go ahead. A dry
    run prints the requests and the estimate and returns False. Raises SpendError above the
    cap, and exits with NEEDS_YES without --yes."""
    cap = args.max_usd if args.max_usd is not None else config.max_usd_per_run
    estimate = round(estimate_usd, 4)
    if args.dry_run:
        emit(
            dry_run=True,
            requests=requests,
            estimated_usd=estimate,
            cap_usd=cap,
            within_cap=estimate <= cap,
        )
        return False
    check_spend(estimate, cap)
    print(f"Estimated cost: USD {estimate:.4f} (cap USD {cap:.2f})", file=sys.stderr)
    if not args.yes:
        print(
            "This call is paid. Add --yes to send it, or --dry-run to see it.",
            file=sys.stderr,
        )
        sys.exit(NEEDS_YES)
    return True


def openai_client(config: Config) -> openai.OpenAI:
    return openai.OpenAI(api_key=api_key("OPENAI_API_KEY", config.keys.openai))


def cmd_image(args: argparse.Namespace, config: Config) -> None:
    job = images.ImageJob(
        prompt=args.prompt,
        out=args.output,
        size=args.size or config.image.size,
        quality=args.quality or config.image.quality,
        transparent=args.transparent,
    )
    estimate = images.estimate_usd(job, config.image, batch=False)
    body = {
        "url": images.ENDPOINT,
        "body": images.request_body(job, config.image.model),
    }
    if not gate(args, config, estimate, [body]):
        return
    result = images.generate(openai_client(config), job, config.image)
    emit(**asdict(result), path=str(job.path))
    if not result.ok:
        sys.exit(1)


def cmd_batch(args: argparse.Namespace, config: Config) -> None:
    jobs_file = Path(args.jobs)
    jobs = images.read_jobs(jobs_file, config.image)
    digest = images.jobs_hash(jobs, config.image.model)
    state_file = images.state_path(jobs_file)
    state = images.BatchState.read(state_file)
    if state is not None and state.jobs_hash == digest and state.results is not None:
        print(
            f"Already collected; delete {state_file} to make the set again",
            file=sys.stderr,
        )
        emit_results(state.results)
        return
    client: openai.OpenAI | None = None
    if state is not None and state.jobs_hash != digest:
        client = openai_client(config)
        status = client.batches.retrieve(state.batch_id).status
        if status not in images.BATCH_DONE:
            raise UsageError(
                f"{jobs_file} changed while batch {state.batch_id} is {status}: rerun "
                f"with the old file, or cancel the batch, before you send a new one"
            )
        state = None
    if state is None:
        estimate = sum(
            images.estimate_usd(job, config.image, batch=True) for job in jobs
        )
        requests = [
            {
                "custom_id": str(i),
                "url": images.ENDPOINT,
                "body": images.request_body(job, config.image.model),
            }
            for i, job in enumerate(jobs)
        ]
        if not gate(args, config, estimate, requests):
            return
        client = client or openai_client(config)
        state = images.BatchState(digest, images.submit(client, jobs, config.image))
        state.write(state_file)
        print(f"Submitted {state.batch_id}: {len(jobs)} images", file=sys.stderr)
    client = client or openai_client(config)
    batch = images.wait(
        client, state.batch_id, args.poll, keep_waiting=not args.no_wait
    )
    state.status = batch.status
    if batch.status not in images.BATCH_DONE:
        state.write(state_file)
        emit(
            ok=True,
            batch_id=state.batch_id,
            status=batch.status,
            note=f"rerun `batch {args.jobs}` to collect",
        )
        return
    state.results = images.collect(client, batch, jobs, config.image)
    state.write(state_file)
    emit_results(state.results)


def emit_results(results: list[images.ImageResult]) -> None:
    billed = sum(r.billed_usd or 0.0 for r in results)
    emit(
        ok=all(r.ok for r in results),
        billed_usd=round(billed, 4),
        images=[asdict(r) for r in results],
    )
    if not all(r.ok for r in results):
        sys.exit(1)


def cmd_model(args: argparse.Namespace, config: Config) -> None:
    """Image-to-model from one image, or multiview-to-model when --left, --back or --right
    gives more views (the image is then the front)."""
    options = {
        "texture_quality": args.texture_quality,
        "face_limit": args.face_limit,
        "seed": args.seed,
    }
    image = Path(args.image)
    views = {
        view: Path(p)
        for view in ("left", "back", "right")
        if (p := getattr(args, view))
    }
    if views:
        task = tripo.multiview_to_model(
            config.model, {"front": image, **views}, args.output, **options
        )
    else:
        task = tripo.image_to_model(config.model, image, args.output, **options)
    run_task(
        args, config, task, prompt=" ".join(str(p) for p in [image, *views.values()])
    )


def run_task(
    args: argparse.Namespace, config: Config, task: tripo.Task, prompt: str
) -> None:
    """Runs any Tripo task through the paid-call gate, waits for it, downloads its results
    and writes the manifest of the main one. A task file beside the output records a
    started task, so a rerun waits for it instead of paying again."""
    settings = config.model
    usd = task.credits * settings.usd_per_credit
    task_file = task.path.with_name(task.path.name + ".task.json")
    if task_file.exists():
        task_id = json.loads(task_file.read_text())["task_id"]
        print(
            f"Resuming task {task_id}; delete {task_file} to start a new one",
            file=sys.stderr,
        )
    else:
        print(f"Estimated credits: {task.credits}", file=sys.stderr)
        request = {"url": settings.api + task.endpoint, "body": task.shown()}
        if not gate(args, config, usd, [request]):
            return
        task_id = ""
    client = tripo.connect(settings, api_key("TRIPO_API_KEY", config.keys.tripo))
    if not task_id:
        task_id = client.start(task)
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text(
            json.dumps({"task_id": task_id, "endpoint": task.endpoint}) + "\n"
        )
        print(f"Started task {task_id}", file=sys.stderr)
    data = client.wait(task_id, settings.poll_seconds, settings.timeout_minutes * 60)
    files = client.download(data.get("output") or {}, task.path)
    consumed = data.get("credits_consumed")
    billed = (
        None
        if consumed is None
        else round(float(consumed) * settings.usd_per_credit, 4)
    )
    shown = {
        k: v for k, v in task.shown().items() if isinstance(v, str | int | float | bool)
    }
    manifest.write(
        task.path,
        manifest.Manifest(
            service=f"Tripo API {task.endpoint}",
            model=settings.version,
            mode="task",
            prompt=prompt,
            settings=shown,
            estimated_usd=round(usd, 4),
            billed_usd=billed,
            request_id=task_id,
            seed=args.seed,
        ),
    )
    task_file.unlink()
    emit(ok=True, files=[str(f) for f in files], task_id=task_id, billed_usd=billed)


def cmd_check(args: argparse.Namespace, config: Config) -> None:
    """Checks that both keys load and that the APIs accept them. It costs nothing."""
    model = openai_client(config).models.retrieve(config.image.model)
    client = tripo.connect(config.model, api_key("TRIPO_API_KEY", config.keys.tripo))
    credits = client.balance()
    emit(
        ok=True,
        openai_model=model.id,
        tripo_credits=credits,
        tripo_usd=round(credits * config.model.usd_per_credit, 2),
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="orrery-art", description=__doc__.split("\n\n")[0]
    )
    sub = root.add_subparsers(dest="command", required=True)

    def paid(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="print the requests and the estimate; send nothing",
        )
        p.add_argument("--yes", action="store_true", help="send the paid call")
        p.add_argument(
            "--max-usd",
            type=float,
            help="the spend cap for this run (default: config.toml)",
        )

    image = sub.add_parser("image", help="one image now, at the live price")
    image.add_argument("--prompt", required=True)
    image.add_argument(
        "-o",
        "--output",
        required=True,
        help="path under build/art/images/ (.png, .webp, .jpg)",
    )
    image.add_argument("--size", help="WIDTHxHEIGHT, edges divisible by 16")
    image.add_argument("--quality", choices=list(images.GRID))
    image.add_argument("--transparent", action="store_true")
    paid(image)

    batch = sub.add_parser(
        "batch", help="a JSONL file of images through the Batch API, at half price"
    )
    batch.add_argument(
        "jobs", help="JSONL: one {prompt, out, size?, quality?, transparent?} per line"
    )
    batch.add_argument(
        "--no-wait", action="store_true", help="submit or check once, then return"
    )
    batch.add_argument(
        "--poll", type=float, default=60.0, help="seconds between status checks"
    )
    paid(batch)

    model = sub.add_parser(
        "model", help="a textured GLB from an image or 2-4 views (Tripo)"
    )
    model.add_argument(
        "image",
        help="a .png or .jpg of one object on a plain background (the front view)",
    )
    for view in ("left", "back", "right"):
        model.add_argument(
            f"--{view}", help=f"the {view} view: makes it a multiview task"
        )
    model.add_argument(
        "-o", "--output", required=True, help="path under build/art/models/ (.glb)"
    )
    model.add_argument(
        "--texture-quality", choices=tripo.TEXTURE_QUALITIES, default="standard"
    )
    model.add_argument("--face-limit", type=int)
    model.add_argument("--seed", type=int)
    paid(model)

    sub.add_parser("check", help="check both API keys with free calls")
    return root


COMMANDS = {
    "image": cmd_image,
    "batch": cmd_batch,
    "model": cmd_model,
    "check": cmd_check,
}


def main(argv: list[str] | None = None, config: Config | None = None) -> None:
    args = parser().parse_args(argv)
    try:
        COMMANDS[args.command](args, config or load())
    except (
        UsageError,
        ValueError,
        SpendError,
        MissingKeyError,
        tripo.TripoError,
        openai.APIError,
    ) as error:
        emit(ok=False, error=str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
