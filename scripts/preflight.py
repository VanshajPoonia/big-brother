"""Run what CI runs, on exactly what you're about to push, before you push it.

    python scripts/preflight.py            check HEAD
    python scripts/preflight.py --rev SHA  check another commit

The pre-push hook in .githooks/ runs this for you. It catches what makes CI fail even though
`pytest` passes on your laptop: a new file you never `git add`ed, a package installed on your
machine but missing from pyproject.toml, a broken test. It also blocks the things that cost
hackathon points: a commit without the coding agent and model lines, and anything that looks
like a secret.

Only the standard library is used, so it runs before the project is installed.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

MODEL_LINE = "Models used in project: Qwen3 4B (qwen3:4b via Ollama)"
CI_PYTHON = "3.12"  # keep in step with .github/workflows/ci.yml
CI_TEST = ["-m", "pytest", "-q", "--cov=bigbrother", "--cov-report=term-missing"]

SECRETS = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}|AKIA[0-9A-Z]{16}|xox[abprs]-[A-Za-z0-9-]{10,}"
    r"|sk-[A-Za-z0-9_-]{32,}|hf_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def message_problems(message: str) -> list[str]:
    """What a commit message is missing under the hackathon rules. Empty when it's fine."""
    lines = [line.strip() for line in message.splitlines()]
    problems = []
    if not any(line.startswith("Coding agent:") and line != "Coding agent:" for line in lines):
        problems.append('no "Coding agent: <agent, or none>" line')
    model_lines = [line for line in lines if line.startswith("Models used in project:")]
    if not model_lines:
        problems.append(f'no "{MODEL_LINE}" line')
    elif any(line != MODEL_LINE for line in model_lines):
        problems.append(f'the models line must be exactly "{MODEL_LINE}", naming another model costs 5 points')
    return problems


def secrets_in(diff: str) -> list[str]:
    """Added lines that look like a token or a private key."""
    return [line[:80] for line in diff.splitlines() if line.startswith("+") and SECRETS.search(line)]


def _base(rev: str) -> str | None:
    for candidate in ("origin/main", "main"):
        try:
            return git("merge-base", candidate, rev).strip()
        except subprocess.CalledProcessError:
            continue
    return None


def check_commits(rev: str, base: str | None) -> list[str]:
    shas = git("rev-list", f"{base}..{rev}" if base else rev, "-n", "50").split()
    problems = []
    for sha in shas:
        for problem in message_problems(git("log", "-1", "--format=%B", sha)):
            problems.append(f"commit {sha[:7]}: {problem}")
    return problems


def _python_in(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run_ci_tests(rev: str) -> bool:
    """Export the commit, install it fresh like CI does, and run CI's test command on it."""
    with tempfile.TemporaryDirectory(prefix="bigbrother-preflight-") as tmp:
        tree = Path(tmp) / "tree"
        tree.mkdir()
        archive = subprocess.run(["git", "archive", "--format=tar", rev], check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(tree, filter="data")

        env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "VIRTUAL_ENV"}}
        uv = shutil.which("uv")
        if uv:
            venv = Path(tmp) / "venv"
            print(f"preflight: fresh Python {CI_PYTHON} environment from the commit's pyproject.toml, like CI")
            subprocess.run([uv, "venv", "-q", "--python", CI_PYTHON, str(venv)], check=True)
            subprocess.run([uv, "pip", "install", "-q", "--python", str(_python_in(venv)), "-e", f"{tree}[dev]"], check=True)
            python = str(_python_in(venv))
        else:
            # Without uv, test the exported code with this Python. A dependency missing from
            # pyproject.toml can slip through this way, so say so.
            print("preflight: uv not found, using this Python. Install uv for a check that matches CI exactly.")
            python = sys.executable
            env["PYTHONPATH"] = str(tree / "src")

        print(f"preflight: {' '.join(['python', *CI_TEST])}")
        result = subprocess.run([python, *CI_TEST], cwd=tree, env=env)
        return result.returncode == 0


def docker_running() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rev", default="HEAD", help="the commit to check (default: HEAD)")
    args = parser.parse_args(argv)

    rev = git("rev-parse", args.rev).strip()
    base = _base(rev)
    failed = False

    problems = check_commits(rev, base)
    for problem in problems:
        print(f"preflight: {problem}")
    if problems:
        print(f'preflight: fix with `git commit --amend` (last commit) and end the message with\n  Coding agent: <agent>\n  {MODEL_LINE}')
        failed = True

    leaks = secrets_in(git("diff", f"{base}..{rev}") if base else "")
    for leak in leaks:
        print(f"preflight: looks like a secret, keep it in .env instead: {leak}")
    failed |= bool(leaks)

    if not docker_running():
        print("preflight: Docker isn't running, so the Docker tests will be skipped here. CI runs them.")
    if not run_ci_tests(rev):
        print("preflight: tests failed on the committed code. Did you `git add` every new file?")
        failed = True

    print("preflight: " + ("FAILED, not pushing" if failed else "all good, same as CI will see"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
