import argparse
import os
import subprocess
import sys
from pathlib import Path

from bigbrother import __version__
from bigbrother.schema import Label, Report

DEFAULT_CACHE = Path(os.environ.get("BIGBROTHER_CACHE", Path.home() / ".cache" / "bigbrother" / "repos"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bigbrother",
        description="Check the claims in an issue, or the tests in a pull request, against the code.",
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

    check.add_argument("--comment", action="store_true",
                       help="post the report on the issue and label it (only on our demo repo)")

    pr = commands.add_parser("pr", help="say whether any test names the code a pull request changes")
    pr.add_argument("url", help="a GitHub pull request URL")
    pr.add_argument("--repo", type=Path, help="a local clone of the PR's repo (default: clone it into the cache)")
    pr.add_argument("--out", type=Path, default=Path("bigbrother-out"), help="folder for pr.json and pr.md")
    pr.add_argument("--comment", action="store_true", help="post the report on the PR and label it (only on our demo repo)")

    watch = commands.add_parser("watch", help="act as the bot on our demo repo: check every new issue and PR and comment")
    watch.add_argument("--repo", default="VanshajPoonia/big-brother-demo", help="owner/name, must be our demo repo")
    watch.add_argument("--every", type=int, default=30, help="seconds between looks (default 30)")
    watch.add_argument("--once", action="store_true", help="handle what's open now, then stop")
    watch.add_argument("--out", type=Path, default=Path("bigbrother-out/watch"), help="folder for each report")

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


def _link(report: Report, path: str, line: int) -> str:
    """path:line, linked to that exact line on GitHub when we know the commit."""
    if report.revision is None:
        return f"{path}:{line}"
    return f"[{path}:{line}](https://github.com/{report.issue.repo}/blob/{report.revision.sha}/{path}#L{line})"


def _tail(text: str, lines: int = 12) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def summary(report: Report, heading: bool = True) -> str:
    """Plain Markdown a maintainer can read, as report.md or as the bot's comment (no heading)."""
    v = report.verdict
    lines = [f"# {report.issue.title}", "", f"{report.issue.url}", ""] if heading else []
    lines += [
        f"**{v.label.value}** ({v.confidence.value} confidence, rule {v.rule}, basis {v.basis.value})",
        "",
        "## Why",
        *[f"- {reason}" for reason in v.reasons],
    ]
    if report.premises:
        lines += ["", "## What the report relies on"]
        for r in report.premises:
            where = f" at {_link(report, r.excerpt.path, r.excerpt.line)}: `{r.excerpt.text.strip()}`" if r.excerpt else ""
            lines.append(f"- {r.premise.kind} `{r.premise.value}`: {r.state.value}{where}")
    if report.old_install:
        o = report.old_install
        lines += ["", "## Where the missing name is", f"- `{o.owner}.{o.name}` at {_link(report, o.path, o.line)}, first in {o.added_in}"]
    if report.run:
        lines += ["", "## What ran", f"- status: {report.run.status.value}"]
        if report.run.exception_type:
            lines.append(f"- exception: {report.run.exception_type}")
        if report.repro:
            who = "the reporter's own" if report.repro.origin == "reporter" else "written by Qwen"
            lines += ["", f"<details><summary>The script ({who})</summary>", "", "```python",
                      report.repro.code.rstrip(), "```", "</details>"]
        if report.run.commands:
            lines += ["", "<details><summary>Every command it ran</summary>", "",
                      *[f"- `{c}`" for c in report.run.commands], "</details>"]
        if report.run.stderr.strip():
            lines += ["", "<details><summary>Last lines of its output</summary>", "", "```",
                      _tail(report.run.stderr), "```", "</details>"]
    if report.notes:
        lines += ["", "## Notes", *[f"- {n}" for n in report.notes]]
    model = report.model_calls[0].model if report.model_calls else "none (not reachable)"
    lines += ["", f"Rerun: `bigbrother check {report.issue.url}`", "", f"bigbrother {report.tool_version}, model {model}"]
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
    if args.comment:
        from bigbrother.bot import require_demo

        try:
            require_demo(issue.repo)
        except ValueError as error:
            print(f"bigbrother: not commenting: {error}", file=sys.stderr)
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
    if args.comment:
        return _post(issue.repo, issue.number, summary(report, heading=False), report.verdict.label.value)
    return 0


def _post(repo: str, number: int, markdown: str, label: str) -> int:
    import httpx

    from bigbrother.bot import post

    try:
        link = post(repo, number, markdown, label)
    except (ValueError, httpx.HTTPError) as error:
        print(f"bigbrother: couldn't comment: {error}", file=sys.stderr)
        return 2
    print(f"bigbrother: commented {label} on {link}", file=sys.stderr)
    return 0


def _clone(repo: str, local: Path | None) -> Path:
    from bigbrother.ingest import ensure_clone

    if local is not None:
        if not (local / ".git").exists():
            raise ValueError(f"{local} isn't a git clone")
        return local
    return ensure_clone(repo, DEFAULT_CACHE)


def run_pr(args: argparse.Namespace) -> int:
    import httpx

    from bigbrother.pullrequest import check_pr, fetch_commits, fetch_pr, parse_pr_url
    from bigbrother.pullrequest import summary as pr_summary

    try:
        repo, number = parse_pr_url(args.url)
        if args.comment:
            from bigbrother.bot import require_demo

            require_demo(repo)
        pr = fetch_pr(args.url)
        repo_dir = _clone(repo, args.repo)
        fetch_commits(repo_dir, pr)
        report = check_pr(pr, repo_dir)
    except (OSError, ValueError, httpx.HTTPError, subprocess.SubprocessError) as error:
        print(f"bigbrother: {error}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pr.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (args.out / "pr.md").write_text(pr_summary(report), encoding="utf-8")
    print(pr_summary(report))
    if args.comment:
        return _post(repo, number, pr_summary(report, heading=False), report.label.value)
    return 0


def run_watch(args: argparse.Namespace) -> int:
    """Poll the demo repo and comment on each new issue and PR, like a GitHub App would on a webhook."""
    import time

    import httpx

    from bigbrother.bot import pending, require_demo

    try:
        require_demo(args.repo)
    except ValueError as error:
        print(f"bigbrother: {error}", file=sys.stderr)
        return 2
    print(f"bigbrother: watching {args.repo}, new issues and PRs get a comment", file=sys.stderr)
    tried: set[tuple[str, int]] = set()
    while True:
        try:
            waiting = pending(args.repo)
        except (ValueError, httpx.HTTPError) as error:
            print(f"bigbrother: couldn't list {args.repo}: {error}", file=sys.stderr)
            waiting = []
        for kind, number, url in waiting:
            if (kind, number) in tried:
                continue  # one try each per watch, so a failing one doesn't loop forever
            tried.add((kind, number))
            print(f"bigbrother: checking {url}", file=sys.stderr, flush=True)
            out = args.out / f"{kind}-{number}"
            if kind == "pull":
                run_pr(argparse.Namespace(url=url, repo=None, out=out, comment=True))
            else:
                run_check(argparse.Namespace(issue=url, repo=None, out=out, json=False, replay=None, comment=True,
                                             blocked_label=Label.CANNOT_REPRODUCE.value))
        if args.once:
            return 0
        time.sleep(args.every)


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
        # Rerun only these, but score everything: the others reuse their saved reports.
        saved = {}
        for case in cases:
            path = args.out / case.id / "report.json"
            if case.id not in args.only and path.exists():
                saved[case.id] = Report.model_validate_json(path.read_text(encoding="utf-8"))
        cases = [case for case in cases if case.id in args.only or case.id in saved]
    else:
        saved = {}

    reports, seconds = [], []
    for n, case in enumerate(cases, 1):
        if case.id in saved:
            reports.append(saved[case.id])
            continue
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

    # With --only the timings would cover just the rerun cases, so leave them out.
    results = render(score(cases, reports, None if saved else seconds), list(zip(cases, reports)))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.md").write_text(results, encoding="utf-8")
    print(results)
    return 0


def run_doctor() -> int:
    import shutil

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
    if args.command == "pr":
        return run_pr(args)
    if args.command == "watch":
        return run_watch(args)
    if args.command == "doctor":
        return run_doctor()
    return 0
