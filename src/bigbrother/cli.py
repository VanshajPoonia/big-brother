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
    check.add_argument(
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
        model = default_model()
    except ModelError as error:
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check":
        return run_check(args)
    return 0
