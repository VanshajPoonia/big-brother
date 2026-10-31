import argparse
import os
import sys
from pathlib import Path

from bigbrother import __version__
from bigbrother.schema import Label, Report

DEFAULT_CACHE = Path(os.environ.get("BIGBROTHER_CACHE", Path.home() / ".cache" / "bigbrother" / "repos"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bigbrother",
        description="Check the claims in an issue or pull request against the code.",
    )
    parser.add_argument("--version", action="version", version=f"bigbrother {__version__}")
    commands = parser.add_subparsers(dest="command")

    check = commands.add_parser("check", help="label one issue with evidence")
    check.add_argument("issue", help="a GitHub issue URL, or a JSON file in the shape of tests/fixtures/issues/")
    check.add_argument("--repo", type=Path, help="a local clone of the issue's repo (default: clone it into the cache)")
    check.add_argument("--out", type=Path, default=Path("bigbrother-out"), help="folder for report.json and report.md")
    check.add_argument("--json", action="store_true", help="print the report as JSON instead of a summary")
    check.add_argument("--replay", type=Path, metavar="REPORT_JSON",
                       help="reuse the model answers saved in an earlier report.json, so no model is needed")
    check.add_argument(
        "--blocked-label",
        choices=[label.value for label in Label],
        default=Label.CANNOT_REPRODUCE.value,
        help="label to use when nothing could run (rule 5)",
    )

    commands.add_parser("doctor", help="say what this machine can run: tests, Docker runs, the model")

    evaluate = commands.add_parser("eval", help="score the tool on hand-checked issues")
    evaluate.add_argument("cases", nargs="?", type=Path, default=Path("eval/cases.yaml"))
    evaluate.add_argument("--out", type=Path, default=Path("eval/runs/latest"), help="folder for each report and results.md")
    evaluate.add_argument("--only", nargs="*", help="run only these case ids")
    evaluate.add_argument(
        "--blocked-label",
        choices=[label.value for label in Label],
        default=Label.CANNOT_REPRODUCE.value,
        help="label to use when nothing could run (rule 5)",
    )
    return parser


def summary(report: Report) -> str:
    """Plain Markdown a maintainer can read. The proof lane's richer report replaces it when it lands."""
    v = report.verdict
    lines = [
        f"# {report.issue.title}",
        "",
        f"{report.issue.url}",
        "",
        f"**{v.label.value}** ({v.confidence.value} confidence, rule {v.rule}, basis {v.basis.value})",
        "",
        "## Why",
        *[f"- {reason}" for reason in v.reasons],
    ]
    if report.premises:
        lines += ["", "## What the report relies on"]
        for r in report.premises:
            where = f" at {r.excerpt.path}:{r.excerpt.line}: `{r.excerpt.text.strip()}`" if r.excerpt else ""
            lines.append(f"- {r.premise.kind} `{r.premise.value}`: {r.state.value}{where}")
    if report.run:
        lines += ["", "## What ran", f"- status: {report.run.status.value}"]
        if report.run.exception_type:
            lines.append(f"- exception: {report.run.exception_type}")
        lines += [f"- `{c}`" for c in report.run.commands]
    if report.notes:
        lines += ["", "## Notes", *[f"- {n}" for n in report.notes]]
    model = report.model_calls[0].model if report.model_calls else "none (not reachable)"
    lines += ["", f"bigbrother {report.tool_version}, model {model}"]
    return "\n".join(lines) + "\n"


def _load_issue(source: str):
    from bigbrother.ingest import fetch_issue, load_issue_file

    if source.startswith(("http://", "https://")):
        return fetch_issue(source)
    return load_issue_file(source)


def run_check(args: argparse.Namespace) -> int:
    from bigbrother import pipeline
    from bigbrother.extract.model import ModelError, default_model
    from bigbrother.ingest import ensure_clone
    from bigbrother.premises import check_premises, resolve_revision
    from bigbrother.sandbox import reproduce

    try:
        issue = _load_issue(args.issue)
    except (OSError, ValueError) as error:
        print(f"bigbrother: can't read the issue: {error}", file=sys.stderr)
        return 2
    try:
        if args.replay is not None:
            from bigbrother.extract.model import ReplayModel

            model = ReplayModel(Report.model_validate_json(args.replay.read_text(encoding="utf-8")).model_calls)
        else:
            model = default_model()
    except (OSError, ValueError, ModelError) as error:
        print(f"bigbrother: {error}", file=sys.stderr)
        return 2

    if args.repo is not None:
        if not (args.repo / ".git").exists():
            print(f"bigbrother: {args.repo} isn't a git clone", file=sys.stderr)
            return 2
        repo_dir = args.repo
    else:
        try:
            repo_dir = ensure_clone(issue.repo, DEFAULT_CACHE)
        except Exception as error:  # noqa: BLE001
            print(f"bigbrother: couldn't clone {issue.repo}: {error}", file=sys.stderr)
            return 2

    report = pipeline.check(
        issue,
        repo_dir,
        model,
        resolve_revision=resolve_revision,
        check_premises=check_premises,
        reproduce=reproduce,
        blocked_label=Label(args.blocked_label),
    )

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (args.out / "report.md").write_text(summary(report), encoding="utf-8")

    print(report.model_dump_json(indent=2) if args.json else summary(report))
    return 0


def run_eval(args: argparse.Namespace) -> int:
    import time

    from bigbrother import pipeline
    from bigbrother.evaluate import load_cases, render, score
    from bigbrother.extract.model import ModelError, default_model
    from bigbrother.ingest import ensure_clone, fetch_issue
    from bigbrother.premises import check_premises, resolve_revision
    from bigbrother.sandbox import reproduce

    try:
        cases = load_cases(args.cases)
        model = default_model()
    except (OSError, ValueError, ModelError) as error:
        print(f"bigbrother: {error}", file=sys.stderr)
        return 2
    if args.only:
        cases = [case for case in cases if case.id in args.only]

    reports, seconds = [], []
    for n, case in enumerate(cases, 1):
        started = time.monotonic()
        print(f"[{n}/{len(cases)}] {case.id} ...", file=sys.stderr, flush=True)
        try:
            issue = fetch_issue(case.issue_url)
            repo_dir = ensure_clone(issue.repo, DEFAULT_CACHE)
            report = pipeline.check(issue, repo_dir, model, resolve_revision=resolve_revision,
                                    check_premises=check_premises, reproduce=reproduce,
                                    blocked_label=Label(args.blocked_label))
            folder = args.out / case.id
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "report.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
            (folder / "report.md").write_text(summary(report), encoding="utf-8")
        except Exception as error:  # noqa: BLE001  one bad case must not stop the run
            print(f"    crashed: {error}", file=sys.stderr)
            report = None
        reports.append(report)
        seconds.append(round(time.monotonic() - started, 1))
        said = report.verdict.label.value if report else "crashed"
        print(f"    expected {case.expected.value}, said {said} ({seconds[-1]}s)", file=sys.stderr)

    results = render(score(cases, reports, seconds), list(zip(cases, reports)))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.md").write_text(results, encoding="utf-8")
    print(results)
    return 0


def run_doctor() -> int:
    import shutil
    import subprocess

    import httpx

    from bigbrother.extract.model import DEFAULT_MODEL, ModelError, local_only, ollama_host

    def ok(command: list[str]) -> bool:
        try:
            return subprocess.run(command, capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    have_git = shutil.which("git") is not None
    have_docker = ok(["docker", "info"])
    wanted = os.environ.get("BIGBROTHER_MODEL", DEFAULT_MODEL)
    model_line = f"model: {wanted} not found at {ollama_host()}, run `ollama pull {wanted}`"
    have_model = False
    try:
        with httpx.Client(base_url=local_only(ollama_host()), timeout=5, trust_env=False) as client:
            names = {m["name"] for m in client.get("/api/tags").json().get("models", [])}
        have_model = wanted in names or f"{wanted}:latest" in names
        if have_model:
            model_line = f"model: {wanted} ready at {ollama_host()}"
    except ModelError as error:
        model_line = f"model: {error}"
    except (httpx.HTTPError, ValueError):
        model_line = f"model: Ollama isn't answering at {ollama_host()}"

    print(f"python: {sys.version.split()[0]}")
    print(f"git: {'yes' if have_git else 'missing, needed to read repos'}")
    print("docker: " + ("running" if have_docker else "not running, needed to run the reporter's code"))
    print(model_line)
    layer = 0 if not have_git else 1 + have_docker + (have_docker and have_model)
    what = {0: "read the saved reports in examples/ and eval/runs/",
            1: "tests, premise checks and --replay, without running anything",
            2: "--replay with real Docker runs",
            3: "everything: bigbrother check and bigbrother eval"}
    print(f"layer {layer}: {what[layer]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check":
        return run_check(args)
    if args.command == "eval":
        return run_eval(args)
    if args.command == "doctor":
        return run_doctor()
    return 0
