"""orrery-art: GPT-Image art and Tripo props for Orrery. See tools/art/README.md.

    orrery-art image --prompt "..." -o decals/clock.png [--model sunburst] [--ref style.png]
    orrery-art set jobs.jsonl [--batch]
    orrery-art views concept.png -o lamp-views
    orrery-art edit-views <task id> --back "..." -o lamp-views-2
    orrery-art model --views <task id> -o lamp.glb --face-limit 4000 --seed 1
    orrery-art texture <task id> -o lamp-tex.glb --front a.png --back b.png
    orrery-art balance | check

Every paid command prints its estimate, refuses a run above the cap or past the API's
budget, and sends nothing without `--yes`. `--dry-run` prints the requests and the
estimate and sends nothing. Outputs and their recipes go to build/art/ (git-ignored). The
result is one JSON object on stdout; progress goes to stderr.
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx2
import openai

from orrery_art import images, manifest, tripo
from orrery_art.config import (
    Config,
    SpendError,
    check_budget,
    check_spend,
    load,
    out_path,
    record_spend,
    spent,
)
from orrery_art.keys import MissingKeyError, api_key

# Exit status when a paid run needs --yes.
NEEDS_YES = 2


class UsageError(Exception):
    """A bad argument or job."""


def emit(**fields: Any) -> None:
    """Prints the result object on stdout."""
    print(json.dumps(fields, indent=2))


def gate(
    args: argparse.Namespace,
    config: Config,
    service: str,
    estimate_usd: float,
    requests: list[Any],
) -> bool:
    """Runs the checks before a paid call. Returns True when the call may go ahead. A dry
    run prints the requests and the estimate and returns False. Raises SpendError above the
    cap or past the budget, and exits with NEEDS_YES without --yes."""
    cap = args.max_usd if args.max_usd is not None else config.max_usd_per_run
    estimate = round(estimate_usd, 4)
    if args.dry_run:
        emit(
            dry_run=True,
            requests=requests,
            estimated_usd=estimate,
            cap_usd=cap,
            within_cap=estimate_usd <= cap,
            spent_usd=round(spent(service), 4),
            budget_usd=config.budget_usd[service],
        )
        return False
    check_spend(estimate_usd, cap)
    check_budget(service, estimate_usd, config)
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


def tripo_client(config: Config) -> tripo.Tripo:
    return tripo.connect(config.model, api_key("TRIPO_API_KEY", config.keys.tripo))


def show(job: images.ImageJob) -> dict[str, Any]:
    return {"url": job.endpoint, "body": images.request_body(job)}


def run_live(
    client: openai.OpenAI, job: images.ImageJob, config: Config
) -> images.ImageResult:
    """Makes one image now and adds its cost to the ledger."""
    result = images.generate(client, job, config.image)
    usd = result.billed_usd
    if usd is None:
        usd = images.estimate_usd(job, config.image, batch=False)
    record_spend("openai", usd, "", job.out)
    return result


def cmd_image(args: argparse.Namespace, config: Config) -> None:
    job = images.ImageJob(
        prompt=args.prompt,
        out=args.output,
        model=images.model_id(config.image, args.model),
        size=args.size or config.image.size,
        quality=args.quality or config.image.quality,
        transparent=args.transparent,
        complexity=args.complexity,
        refs=tuple(args.ref),
    )
    estimate = images.estimate_usd(job, config.image, batch=False)
    if not gate(args, config, "openai", estimate, [show(job)]):
        return
    result = run_live(openai_client(config), job, config)
    emit(**asdict(result), path=str(job.path))
    if not result.ok:
        sys.exit(1)


def cmd_set(args: argparse.Namespace, config: Config) -> None:
    """A jobs file: live, one image at a time (the default), or through the Batch API."""
    jobs = images.read_jobs(Path(args.jobs), config.image)
    if args.batch:
        run_batch(args, config, jobs)
        return
    todo = [job for job in jobs if not made(job)]
    for job in jobs:
        if job not in todo:
            print(
                f"{job.out}: made before; delete it to make it again", file=sys.stderr
            )
    estimate = sum(images.estimate_usd(job, config.image, batch=False) for job in todo)
    if not todo or not gate(
        args, config, "openai", estimate, [show(job) for job in todo]
    ):
        if not todo:
            emit(ok=True, images=[], note="every image was made before")
        return
    client = openai_client(config)
    cap = args.max_usd if args.max_usd is not None else config.max_usd_per_run
    results, spent_here = [], 0.0
    for job in todo:
        # A dearer image than estimated must not let the next one pass a limit.
        next_usd = images.estimate_usd(job, config.image, batch=False)
        check_spend(spent_here + next_usd, cap)
        check_budget("openai", next_usd, config)
        result = run_live(client, job, config)
        spent_here += result.billed_usd if result.billed_usd is not None else next_usd
        results.append(result)
    emit_results(results)


def made(job: images.ImageJob) -> bool:
    """True when a job's image and recipe exist and a transparent image has clear pixels."""
    if not job.path.is_file() or not manifest.manifest_path(job.path).is_file():
        return False
    return not job.transparent or not images.alpha_problem(job.path)


def run_batch(
    args: argparse.Namespace, config: Config, jobs: list[images.ImageJob]
) -> None:
    """The jobs through the Batch API at half price. A rerun resumes the batch."""
    jobs_file = Path(args.jobs)
    digest = images.jobs_hash(jobs)
    state_file = images.state_path(jobs_file)
    # A dry run ignores the saved state, so it never talks to the API.
    state = None if args.dry_run else images.BatchState.read(state_file)
    if state is not None and state.jobs_hash == digest and state.results is not None:
        print(
            f"Already collected; delete {state_file} to make the set again",
            file=sys.stderr,
        )
        missing = [
            r.out
            for r in state.results
            if r.ok and not out_path("images", r.out).exists()
        ]
        if missing:
            raise UsageError(
                f"collected files are gone: {', '.join(missing)}; delete {state_file} to make them again"
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
        if any(job.refs for job in jobs):
            raise UsageError("a batch takes no reference images; run the set live")
        estimate = sum(
            images.estimate_usd(job, config.image, batch=True) for job in jobs
        )
        requests = [{"custom_id": str(i), **show(job)} for i, job in enumerate(jobs)]
        if not gate(args, config, "openai", estimate, requests):
            return
        client = client or openai_client(config)
        state = images.BatchState(digest, images.submit(client, jobs))
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
            note=f"rerun `set {args.jobs} --batch` to collect",
        )
        return
    state.results = images.collect(client, batch, jobs, config.image)
    for job, result in zip(jobs, state.results, strict=True):
        # A returned image is billed even when it fails the alpha check.
        usd = result.billed_usd
        if usd is None and job.path.is_file():
            usd = images.estimate_usd(job, config.image, batch=True)
        if usd is not None:
            record_spend("openai", usd, f"{state.batch_id}/{job.out}", result.out)
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


def views_of(args: argparse.Namespace, *names: str) -> dict[str, Path]:
    return {name: Path(value) for name in names if (value := getattr(args, name, None))}


def cmd_views(args: argparse.Namespace, config: Config) -> None:
    run_task(
        args,
        config,
        args.output,
        lambda: tripo.image_to_multiview(config.model, Path(args.image), args.output),
    )


def cmd_edit_views(args: argparse.Namespace, config: Config) -> None:
    edits = {view: text for view in tripo.VIEWS if (text := getattr(args, view))}
    run_task(
        args,
        config,
        args.output,
        lambda: tripo.edit_multiview(config.model, args.task, edits, args.output),
    )


def cmd_model(args: argparse.Namespace, config: Config) -> None:
    """Image-to-model from one image; multiview-to-model from --views (a task id) or from
    the image as the front plus --left, --back or --right."""
    side_views = views_of(args, "left", "back", "right")
    image = Path(args.image) if args.image else None
    if args.views and (image or side_views):
        raise UsageError("give --views or local images, not both")

    def make() -> tripo.Task:
        options: dict[str, Any] = {
            "series": args.series,
            "texture": args.texture,
            "texture_quality": args.texture_quality,
            "face_limit": args.face_limit,
            "seed": args.seed,
        }
        if side_views:
            if image is None:
                raise UsageError("--left, --back and --right need the front image")
            return tripo.model(
                config.model,
                args.output,
                views={"front": image, **side_views},
                **options,
            )
        return tripo.model(
            config.model,
            args.output,
            image=image,
            from_task=args.views or "",
            **options,
        )

    run_task(args, config, args.output, make)


def cmd_texture(args: argparse.Namespace, config: Config) -> None:
    refs = views_of(args, *tripo.VIEWS)
    run_task(
        args,
        config,
        args.output,
        lambda: tripo.texture(
            config.model,
            args.source,
            args.output,
            refs,
            args.quality,
            args.seed,
            not args.no_bake,
        ),
    )


def run_task(
    args: argparse.Namespace, config: Config, out: str, make: Callable[[], tripo.Task]
) -> None:
    """Runs a Tripo task through the paid-call gate, waits for it, downloads its results at
    once and writes its recipe (inputs, every option, task id, credits). A task file
    beside the output records a started task and its recipe, so a rerun waits for that
    task instead of paying again, even when its inputs have moved. A dry run ignores the
    task file."""
    settings = config.model
    path = out_path("models", out)
    task_file = path.with_name(path.name + ".task.json")
    record: dict[str, Any]
    task: tripo.Task | None = None
    if task_file.exists() and not args.dry_run:
        started = json.loads(task_file.read_text())
        task_id, record = started["task_id"], started["record"]
        print(
            f"Resuming task {task_id}; delete {task_file} to start a new one",
            file=sys.stderr,
        )
        expects = started.get("expects", ["model_url"])
    else:
        task = make()
        usd = task.credits * settings.usd_per_credit
        print(f"Estimated credits: {task.credits:g}", file=sys.stderr)
        request = {"url": settings.api + task.endpoint, "body": task.shown()}
        if not gate(args, config, "tripo", usd, [request]):
            return
        task_id = ""
        record = {
            "service": f"Tripo API {task.endpoint}",
            "model": task.model,
            "prompt": json.dumps(
                task.shown().get("input") or task.shown().get("inputs")
            ),
            "settings": task.shown(),
            "estimated_usd": round(usd, 4),
            "seed": getattr(args, "seed", None),
        }
        expects = list(task.expects)
    client = tripo_client(config)
    if task is not None:
        task_id = client.start(task)
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text(
            json.dumps({"task_id": task_id, "record": record, "expects": expects})
            + "\n"
        )
        print(f"Started task {task_id}", file=sys.stderr)
    data = client.wait(task_id, settings.poll_seconds, settings.timeout_minutes * 60)
    output = data.get("output") or {}
    consumed = data.get("credits_consumed")
    billed = (
        None
        if consumed is None
        else round(float(consumed) * settings.usd_per_credit, 4)
    )
    # Count the charge before the output check and the download, which can fail; the
    # ledger keeps one row per task.
    record_spend(
        "tripo", billed if billed is not None else record["estimated_usd"], task_id, out
    )
    absent = tripo.missing(output, expects)
    if absent:
        raise tripo.TripoError(
            f"task {task_id} succeeded but returned no {', '.join(absent)}"
        )
    files = client.download(output, path)
    manifest.write(
        path,
        manifest.Manifest(**record, mode="task", billed_usd=billed, request_id=task_id),
    )
    task_file.unlink()
    emit(ok=True, files=[str(f) for f in files], task_id=task_id, billed_usd=billed)


def cmd_balance(args: argparse.Namespace, config: Config) -> None:
    """The Tripo balance and usage, and this checkout's running totals. It costs nothing."""
    client = tripo_client(config)
    credits = client.balance()
    emit(
        tripo_credits=credits,
        tripo_usd=round(credits * config.model.usd_per_credit, 2),
        tripo_usage=client.usage(),
        spent_usd={service: round(spent(service), 4) for service in config.budget_usd},
        budget_usd=config.budget_usd,
    )


def cmd_check(args: argparse.Namespace, config: Config) -> None:
    """Checks that both keys load and that the APIs accept them. It costs nothing."""
    models = [
        openai_client(config).models.retrieve(m).id
        for m in config.image.models.values()
    ]
    credits = tripo_client(config).balance()
    emit(
        ok=True,
        openai_models=models,
        tripo_credits=credits,
        tripo_usd=round(credits * config.model.usd_per_credit, 2),
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="orrery-art", description=__doc__.split("\n\n")[0]
    )
    sub = root.add_subparsers(dest="command", required=True)

    def paid(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
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
        return p

    def out(p: argparse.ArgumentParser, help: str) -> None:
        p.add_argument("-o", "--output", required=True, help=help)

    image = paid(
        sub.add_parser("image", help="one image now (generations, or edits with --ref)")
    )
    image.add_argument("--prompt", required=True)
    out(image, "path under build/art/images/ (.png, .webp, .jpg)")
    image.add_argument(
        "--model", help="flare (drafts, the default) or sunburst (finals)"
    )
    image.add_argument("--size", help="WIDTHxHEIGHT, edges divisible by 16")
    image.add_argument("--quality", choices=list(images.QUALITIES))
    image.add_argument("--complexity", choices=list(images.COMPLEXITIES))
    image.add_argument("--transparent", action="store_true")
    image.add_argument(
        "--ref",
        action="append",
        default=[],
        help="a reference image (repeat, up to 16)",
    )

    jobs = paid(
        sub.add_parser("set", help="a JSONL file of images, live one at a time")
    )
    jobs.add_argument(
        "jobs",
        help="JSONL: one {prompt, out, model?, size?, quality?, complexity?, transparent?, refs?} per line",
    )
    jobs.add_argument(
        "--batch",
        action="store_true",
        help="use the Batch API (half price; untested for 2.6)",
    )
    jobs.add_argument(
        "--no-wait",
        action="store_true",
        help="with --batch: submit or check once, then return",
    )
    jobs.add_argument(
        "--poll",
        type=float,
        default=60.0,
        help="with --batch: seconds between status checks",
    )

    views = paid(
        sub.add_parser(
            "views", help="front, left, back and right views from one image (Tripo)"
        )
    )
    views.add_argument(
        "image", help="a .png or .jpg of one object on a plain background"
    )
    out(
        views,
        "a name under build/art/models/, no extension: views are <name>.front.png ...",
    )

    edit = paid(
        sub.add_parser("edit-views", help="edit views of a `views` task (Tripo)")
    )
    edit.add_argument("task", help="the task id of the views")
    for view in tripo.VIEWS:
        edit.add_argument(f"--{view}", help=f"the edit prompt for the {view} view")
    out(edit, "a name under build/art/models/, no extension")

    model = paid(
        sub.add_parser(
            "model", help="a GLB from an image, views or a views task (Tripo)"
        )
    )
    model.add_argument(
        "image", nargs="?", help="a .png or .jpg: the image, or the front view"
    )
    for view in ("left", "back", "right"):
        model.add_argument(
            f"--{view}", help=f"the {view} view: makes it a multiview task"
        )
    model.add_argument("--views", help="the task id of a views or edit-views task")
    out(model, "path under build/art/models/ (.glb)")
    model.add_argument("--series", choices=tripo.SERIES, default="p1")
    model.add_argument(
        "--texture", action="store_true", help="texture it in the same task"
    )
    model.add_argument(
        "--texture-quality", choices=tripo.TEXTURE_QUALITIES, default="standard"
    )
    model.add_argument("--face-limit", type=int)
    model.add_argument("--seed", type=int)

    tex = paid(sub.add_parser("texture", help="new texture maps for a model (Tripo)"))
    tex.add_argument("source", help="the task id of a model task, or a local .glb")
    for view in tripo.VIEWS:
        tex.add_argument(f"--{view}", help=f"the {view} reference view")
    out(tex, "path under build/art/models/ (.glb)")
    tex.add_argument(
        "--quality", choices=tripo.TEXTURE_TASK_QUALITIES, default="standard"
    )
    tex.add_argument("--seed", type=int)
    tex.add_argument("--no-bake", action="store_true", help="send bake: false")

    sub.add_parser(
        "balance", help="the Tripo balance and usage, and the running totals"
    )
    sub.add_parser("check", help="check both API keys with free calls")
    return root


COMMANDS = {
    "image": cmd_image,
    "set": cmd_set,
    "views": cmd_views,
    "edit-views": cmd_edit_views,
    "model": cmd_model,
    "texture": cmd_texture,
    "balance": cmd_balance,
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
        httpx2.HTTPError,
    ) as error:
        emit(ok=False, error=str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
