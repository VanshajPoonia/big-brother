"""Check a pull request: does a test in the PR cover the code it changes?

No model. The PR's diff gives the changed lines, the code at the PR's head gives the functions
holding them, and the tests the PR adds or changes either use each function or they don't. Older
tests that use it are listed too, but they were written before the change, so they don't count.
Every answer points at a file and line.

With a sandbox, the PR's test files also run: at the head, then at the base with the PR's test
files copied in. Failing before the change and passing after is the proof that they test it.
"""

from __future__ import annotations

import ast
import re
import subprocess
from enum import StrEnum
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from bigbrother import __version__
from bigbrother.ingest import API, _headers, raise_for_github
from bigbrother.redact import redact
from bigbrother.schema import ExecutionStatus, RunResult

PR_URL = re.compile(r"^https?://(?:www\.)?github\.com/(?P<repo>[\w.-]+/[\w.-]+)/pulls?/(?P<number>\d+)/?(?:[?#].*)?$")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
TEST_DIRS = {"tests", "test", "testing"}
NOT_CODE = {"docs", "doc", "examples", "example", "benchmarks", "scripts", "tools"}
NOT_CODE_FILES = {"setup.py", "noxfile.py", "conftest.py"}
MENTIONS_SHOWN = 3


class Coverage(StrEnum):
    TESTED = "tested"
    PARTLY = "partly tested"
    NO_TEST = "no test for this change"
    NO_CODE = "no function changed"


MEANING = {
    Coverage.TESTED: "every function this PR changes is used in a test the PR adds or changes",
    Coverage.PARTLY: "some functions this PR changes are used in a test the PR adds or changes, others aren't",
    Coverage.NO_TEST: "no test the PR adds or changes uses a function it changes",
    Coverage.NO_CODE: "no function in the package changed",
}


class PullRequest(BaseModel):
    url: str  # empty for a local branch
    repo: str
    number: int
    title: str
    base_sha: str
    head_sha: str


class Mention(BaseModel):
    path: str
    line: int
    text: str = Field(max_length=200)
    in_pr: bool = False  # inside a test the PR adds or changes


class ChangedFunction(BaseModel):
    path: str
    name: str  # qualified, like Console.save_svg
    line: int
    changed_lines: int
    mentions: list[Mention] = Field(default_factory=list)


class PrReport(BaseModel):
    tool_version: str
    pr: PullRequest
    label: Coverage
    reasons: list[str]
    functions: list[ChangedFunction] = Field(default_factory=list)
    tests_changed: list[str] = Field(default_factory=list)
    outside_functions: list[str] = Field(default_factory=list)
    tests_run: list[str] = Field(default_factory=list)
    head_run: RunResult | None = None
    base_run: RunResult | None = None


def _git(repo_dir: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo_dir), *args], check=True, capture_output=True, text=True,
                          timeout=60).stdout


def parse_pr_url(url: str) -> tuple[str, int]:
    match = PR_URL.match(url.strip())
    if not match:
        raise ValueError(f"{url!r} isn't a GitHub pull request URL")
    return match["repo"], int(match["number"])


def fetch_pr(url: str, client: httpx.Client | None = None) -> PullRequest:
    """The PR's title and its base and head commits. Its description and comments aren't used."""
    repo, number = parse_pr_url(url)
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.get(f"{API}/repos/{repo}/pulls/{number}", headers=_headers())
        raise_for_github(response)
        data = response.json()
    finally:
        if owned:
            client.close()
    return PullRequest(url=f"https://github.com/{repo}/pull/{number}", repo=repo, number=number, title=data["title"],
                       base_sha=data["base"]["sha"], head_sha=data["head"]["sha"])


def local_pr(repo_dir: Path, base: str, head: str = "HEAD") -> PullRequest:
    """A branch in a local clone, checked like a PR. Nothing goes online."""
    base_sha, head_sha = (_git(repo_dir, "rev-parse", "--verify", f"{ref}^{{commit}}").strip() for ref in (base, head))
    return PullRequest(url="", repo="", number=0, title=f"{head} against {base}", base_sha=base_sha, head_sha=head_sha)


def fetch_commits(repo_dir: Path, pr: PullRequest) -> None:
    """Make sure the clone has both ends of the PR. GitHub keeps every PR's head at refs/pull/N/head."""
    _git(repo_dir, "fetch", "--quiet", "origin", f"+refs/pull/{pr.number}/head:refs/remotes/origin/pr/{pr.number}")
    for sha in (pr.base_sha, pr.head_sha):
        try:
            _git(repo_dir, "cat-file", "-e", f"{sha}^{{commit}}")
        except subprocess.CalledProcessError:
            _git(repo_dir, "fetch", "--quiet", "origin", sha)


def is_test(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return bool(TEST_DIRS & set(parts[:-1])) or name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def is_code(path: str) -> bool:
    parts = path.split("/")
    return path.endswith(".py") and not is_test(path) and parts[0] not in NOT_CODE and parts[-1] not in NOT_CODE_FILES


def changed_lines(diff: str) -> dict[str, set[int]]:
    """Line numbers at the head that a unified diff with no context adds or changes, per file.
    A pure deletion marks the line it happened after, so the function around it still counts."""
    lines: dict[str, set[int]] = {}
    path = None
    for row in diff.splitlines():
        if row.startswith("+++ "):
            target = row[4:].strip()
            path = None if target == "/dev/null" else target.removeprefix("b/")
            if path:
                lines.setdefault(path, set())
        elif row.startswith("@@") and path and (m := HUNK.match(row)):
            start, count = int(m["start"]), int(m["count"] or 1)
            lines[path] |= set(range(start, start + count)) if count else {max(start, 1)}
    return lines


def functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Every function and method with its qualified name. A function inside a function belongs to
    the outer one: tests can only call the outer one."""
    found = []

    def visit(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.append((prefix + node.name, node))
            elif isinstance(node, ast.ClassDef):
                visit(node.body, f"{prefix}{node.name}.")

    visit(tree.body, "")
    return found


def _span(node: ast.AST) -> tuple[int, int]:
    first = min([node.lineno, *(d.lineno for d in getattr(node, "decorator_list", []))])
    return first, node.end_lineno or node.lineno


def enclosing(found: list[tuple[str, ast.AST]], line: int) -> tuple[str, ast.AST] | None:
    """The innermost function holding this line."""
    holding = [(name, node) for name, node in found if _span(node)[0] <= line <= _span(node)[1]]
    return max(holding, key=lambda item: item[1].lineno) if holding else None


def _grep(repo_dir: Path, sha: str, word: str, *paths: str) -> list[tuple[str, int, str]]:
    """(path, line, text) for each line naming `word`. git grep exits 1 when nothing matches."""
    try:
        out = _git(repo_dir, "grep", "-n", "-w", "-F", "-e", word, sha, "--", *(paths or ("*.py",)))
    except subprocess.CalledProcessError:
        return []
    rows = []
    for row in out.splitlines():
        _, path, line, text = row.split(":", 3)
        rows.append((path, int(line), text))
    return rows


CONSTRUCTORS = {"__init__", "__new__", "__post_init__"}


def mentions(repo_dir: Path, sha: str, code_path: str, qualname: str) -> list[Mention]:
    """Lines in test files at `sha` that use the function. Imports don't count.

    A method's test file must name its class too, and a constructor is found by its class name.
    When another module defines a function of the same name, the test file must name this module.
    """
    parts = qualname.split(".")
    name, owner = parts[-1], parts[-2] if len(parts) > 1 else None
    called = False
    if owner and name in CONSTRUCTORS:
        name, owner, called = owner, None, True
    module = Path(code_path).stem
    same_name = {path for path, _, _ in _grep(repo_dir, sha, f"def {name}") if is_code(path)}
    needs = [owner] if owner else ([module] if len(same_name) > 1 and module != "__init__" else [])

    found, names_it = [], {}
    for path, line, text in _grep(repo_dir, sha, name):
        if not is_test(path) or text.lstrip().startswith(("import ", "from ")):
            continue
        if called and f"{name}(" not in text:
            continue  # a constructor has to be called, not just named in a string
        if needs:
            if path not in names_it:
                names_it[path] = needs[0] in Path(path).stem or bool(_grep(repo_dir, sha, needs[0], path))
            if not names_it[path]:
                continue
        found.append(Mention(path=path, line=line, text=text.strip()[:200]))
    return found


def changed_tests(repo_dir: Path, sha: str, touched: dict[str, set[int]]) -> dict[str, list[tuple[int, int]]]:
    """Line spans of the test functions the PR adds or changes, decorators included, per test file.
    A new parametrize case changes the test without touching the line that names the function."""
    spans: dict[str, list[tuple[int, int]]] = {}
    for path, lines in touched.items():
        if not is_test(path) or not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(_git(repo_dir, "show", f"{sha}:{path}"))
        except (SyntaxError, subprocess.CalledProcessError):
            continue
        for _, node in functions(tree):
            first, last = _span(node)
            if any(first <= line <= last for line in lines):
                spans.setdefault(path, []).append((first, last))
    return spans


def _outcome(run: RunResult) -> str:
    """pytest's own last line, like "1 failed, 3 passed in 0.12s", or what stopped it."""
    if run.status != ExecutionStatus.RAN:
        return {ExecutionStatus.INSTALL_FAILED: "the package didn't install", ExecutionStatus.TIMEOUT: "the tests timed out"}.get(
            run.status, "the sandbox failed")
    lines = [line.strip("= ") for line in run.stdout.strip().splitlines() if line.strip()]
    return lines[-1] if lines else f"pytest exit code {run.exit_code}"


def _passed(run: RunResult | None) -> bool:
    return run is not None and run.status == ExecutionStatus.RAN and run.exit_code == 0


def _failed(run: RunResult | None) -> bool:
    # 1 is failing tests, 2 a collection error, like importing a function the base doesn't have yet.
    return run is not None and run.status == ExecutionStatus.RAN and run.exit_code in (1, 2)


def run_pr_tests(pr: PullRequest, repo_dir: Path, tests_changed: list[str], run_tests) -> tuple[list[str], RunResult | None, RunResult | None]:
    """Run the PR's test files at its head, then at its base with those files copied in."""
    files = [p for p in tests_changed if Path(p).name.startswith("test_") and p.endswith(".py") or p.endswith("_test.py")]
    present = set(_git(repo_dir, "ls-tree", "-r", "--name-only", pr.head_sha).splitlines())
    files = [p for p in files if p in present]
    if not files:
        return [], None, None
    head = run_tests(repo_dir, pr.head_sha, files, {})
    if not _passed(head):
        return files, head, None  # the base can't show anything the head doesn't already
    overlay = {p: _git(repo_dir, "show", f"{pr.head_sha}:{p}") for p in tests_changed if p in present}
    return files, head, run_tests(repo_dir, pr.base_sha, files, overlay)


def check_pr(pr: PullRequest, repo_dir: Path, run_tests=None) -> PrReport:
    diff = _git(repo_dir, "diff", "--unified=0", "--no-color", "--no-ext-diff", f"{pr.base_sha}...{pr.head_sha}", "--", "*.py")
    touched = changed_lines(diff)
    tests_changed = sorted(path for path in touched if is_test(path))
    in_pr = changed_tests(repo_dir, pr.head_sha, touched)

    changed, outside = [], []
    for path, lines in sorted(touched.items()):
        if not is_code(path) or not lines:
            continue
        try:
            tree = ast.parse(_git(repo_dir, "show", f"{pr.head_sha}:{path}"))
        except SyntaxError:
            outside.append(f"{path} doesn't parse at the PR's head")
            continue
        found = functions(tree)
        hit: dict[str, list] = {}
        loose = 0
        for line in sorted(lines):
            holder = enclosing(found, line)
            if holder is None:
                loose += 1
                continue
            hit.setdefault(holder[0], [holder[1], 0])[1] += 1
        for name, (node, count) in hit.items():
            found_in = mentions(repo_dir, pr.head_sha, path, name)
            for m in found_in:
                m.in_pr = any(first <= m.line <= last for first, last in in_pr.get(m.path, []))
            found_in.sort(key=lambda m: not m.in_pr)  # the PR's own tests first
            changed.append(ChangedFunction(path=path, name=name, line=node.lineno, changed_lines=count,
                                           mentions=found_in[:MENTIONS_SHOWN]))
        if loose:
            outside.append(f"{path}: {loose} changed line{'s' if loose > 1 else ''} outside any function")

    tested = [f for f in changed if f.mentions and f.mentions[0].in_pr]
    if not changed:
        label = Coverage.NO_CODE
    elif len(tested) == len(changed):
        label = Coverage.TESTED
    else:
        label = Coverage.PARTLY if tested else Coverage.NO_TEST

    reasons = []
    for f in changed:
        what = f"`{f.name}` ({f.path}:{f.line}) changed"
        if f.mentions and f.mentions[0].in_pr:
            m = f.mentions[0]
            reasons.append(f"{what}, and a test this PR adds or changes uses it at {m.path}:{m.line}")
        elif f.mentions:
            m = f.mentions[0]
            reasons.append(f"{what}, and no test this PR adds or changes uses it. Older tests do, like {m.path}:{m.line}, "
                           f"but they were written before this change")
        else:
            short = f.name.split(".")[-1]
            private = short.startswith("_") and not short.endswith("__")
            private = ". It's private, so a test may reach it through a public function" if private else ""
            reasons.append(f"{what}, and no test uses it at all{private}")
    if not changed:
        reasons.append("no function in the package's code changed, only lines outside functions or no code at all")
    reasons.append(f"the PR changes {len(tests_changed)} test file{'' if len(tests_changed) == 1 else 's'}"
                   + (f": {', '.join(tests_changed)}" if tests_changed else ""))
    files, head_run, base_run = run_pr_tests(pr, repo_dir, tests_changed, run_tests) if run_tests else ([], None, None)
    head_run, base_run = (r and r.model_copy(update={"commands": [redact(c) for c in r.commands], "stdout": redact(r.stdout),
                                                     "stderr": redact(r.stderr)}) for r in (head_run, base_run))
    if files:
        shown = ", ".join(files)
        one = len(files) == 1
        fail, passes = ("fails", "passes") if one else ("fail", "pass")
        if head_run.status != ExecutionStatus.RAN:
            reasons.insert(0, f"couldn't run {shown}: {_outcome(head_run)}")
        elif not _passed(head_run):
            # Often the sandbox, not the PR: a newer dependency than the project's own CI pins.
            reasons.insert(0, f"{shown} {fail} at the PR's head in the sandbox ({_outcome(head_run)}). That can be the PR, "
                              f"or a dependency version different from the project's own CI, so it doesn't decide the label")
        elif _failed(base_run):
            label = Coverage.TESTED  # running them beats reading names
            reasons.insert(0, f"{shown} {fail} without the change ({_outcome(base_run)}) and {passes} with it "
                              f"({_outcome(head_run)}), so the PR's tests check the change")
        elif _passed(base_run):
            reasons.insert(0, f"{shown} {passes} with and without the change ({_outcome(head_run)}), "
                              f"so {'it doesn' if one else 'they don'}'t show the change is tested")
        else:
            reasons.insert(0, f"{shown} {passes} at the PR's head ({_outcome(head_run)}), but couldn't run at the base: "
                              f"{_outcome(base_run)}")
    return PrReport(tool_version=__version__, pr=pr, label=label, reasons=reasons, functions=changed,
                    tests_changed=tests_changed, outside_functions=outside, tests_run=files,
                    head_run=head_run, base_run=base_run)


def _tail(text: str, lines: int = 15) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def headline(report: PrReport) -> str:
    """The evidence in one line, like "! No test covers the change"."""
    if report.label == Coverage.TESTED and _failed(report.base_run) and _passed(report.head_run):
        return "✓ The PR's tests fail without the change and pass with it"
    return {
        Coverage.TESTED: "✓ A test in this PR covers each change",
        Coverage.PARTLY: "! Tests cover only part of the change",
        Coverage.NO_TEST: "! No test covers the change",
        Coverage.NO_CODE: "No function in the package changed",
    }[report.label]


def summary(report: PrReport, heading: bool = True) -> str:
    pr = report.pr

    def where(path: str, line: int) -> str:
        if not pr.url:
            return f"{path}:{line}"
        return f"[{path}:{line}](https://github.com/{pr.repo}/blob/{pr.head_sha}/{path}#L{line})"

    lines = [f"# {pr.title}", "", pr.url, ""] if heading and pr.url else [f"# {pr.title}", ""] if heading else []
    how = "it ran the PR's tests in the offline sandbox, and read" if report.tests_run else "this comes from"
    lines += [f"### {headline(report)}", "", f"**{report.label.value}**: {MEANING[report.label]}", "",
              f"No model: {how} the PR's diff and the tests at its head.", "",
              "## Why", *[f"- {reason}" for reason in report.reasons]]
    if report.functions:
        lines += ["", "## Changed functions", "", "| Function | Where | A test that uses it |", "| --- | --- | --- |"]
        for f in report.functions:
            if f.mentions:
                m = f.mentions[0]
                whose = "in this PR" if m.in_pr else "older test"
                test = f"{whose}: {where(m.path, m.line)} `{m.text}`"
            else:
                test = "none"
            lines.append(f"| `{f.name}` | {where(f.path, f.line)} | {test} |")
    if report.outside_functions:
        lines += ["", "## Changed outside functions", *[f"- {o}" for o in report.outside_functions]]
    for side, run in (("head, with the change", report.head_run), ("base, without it", report.base_run)):
        if run is None:
            continue
        lines += ["", f"<details><summary>Tests at the {side}: {_outcome(run)}</summary>", "", "```",
                  _tail(run.stdout or run.stderr), "```", "", *[f"- `{c}`" for c in run.commands], "</details>"]
    rerun = f"bigbrother pr {pr.url}" if pr.url else f"bigbrother pr --base {pr.base_sha[:12]} --head {pr.head_sha[:12]}"
    lines += ["", f"Rerun: `{rerun}`", "", f"bigbrother {report.tool_version}, checked {pr.base_sha[:12]}...{pr.head_sha[:12]}"]
    return "\n".join(lines) + "\n"
