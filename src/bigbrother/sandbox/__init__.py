"""Lane C: install a repo at a revision and run a repro script in Docker.

Two containers per run. The install container has the network and writes the
dependencies into a fresh named volume. The run container has no network, a
read-only filesystem and sees the source and the dependencies read-only.
Every docker command goes into RunResult.commands as evidence.
"""

from __future__ import annotations

import io
import json
import os
import re
import shlex
import subprocess
import tarfile
import tempfile
import time
import uuid
from pathlib import Path

from bigbrother.schema import OUTPUT_CAP, ExecutionStatus, ReproScript, Revision, RunResult, Symptom

IMAGE = "bigbrother-sandbox:0.1"
DOCKER_DIR = Path(__file__).resolve().parents[3] / "docker"
INSTALL_TIMEOUT = 300
RUN_TIMEOUT = 60
BUILD_TIMEOUT = 600

INSTALL_SCRIPT = "uv venv /deps/venv --python /usr/local/bin/python3 && uv pip install --python /deps/venv/bin/python -e /src"

FRAME = re.compile(r'^\s+File "(?P<file>[^"]+)", line \d+')
EXCEPTION = re.compile(r"^(?P<type>[A-Za-z_][\w.]*)(:|$)")


class SandboxError(Exception):
    """Docker itself failed, not the repo or the script."""


def install_command(name: str, src: Path, volume: str, image: str = IMAGE) -> list[str]:
    # Network on, no environment variables, only the exported source and the volume.
    return [
        "docker", "run", "--name", name,
        "--cpus", "1", "--memory", "1g", "--pids-limit", "256",
        "--mount", f"type=bind,source={src},target=/src",
        "--mount", f"type=volume,source={volume},target=/deps",
        image, "sh", "-c", INSTALL_SCRIPT,
    ]  # fmt: skip


def run_command(name: str, src: Path, volume: str, script: Path, image: str = IMAGE) -> list[str]:
    return [
        "docker", "run", "--name", name,
        "--network", "none", "--read-only", "--tmpfs", "/tmp:size=64m",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--user", "1000:1000", "--pids-limit", "128", "--memory", "1g", "--cpus", "1",
        "--mount", f"type=bind,source={src},target=/src,readonly",
        "--mount", f"type=volume,source={volume},target=/deps,readonly",
        "--mount", f"type=bind,source={script},target=/repro.py,readonly",
        "--workdir", "/tmp",
        image, "/deps/venv/bin/python", "/repro.py",
    ]  # fmt: skip


def parse_traceback(stderr: str) -> tuple[str | None, list[str]]:
    """Exception type and frame files of the last traceback in stderr."""
    lines = stderr.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("Traceback (most recent call last):")]
    if not starts:
        return None, []
    files = []
    for line in lines[starts[-1] + 1 :]:
        frame = FRAME.match(line)
        if frame:
            files.append(frame["file"])
            continue
        if line[:1].isspace() or not line:
            continue
        exception = EXCEPTION.match(line)
        return (exception["type"] if exception else None), files
    return None, files


def _squash(text: str) -> str:
    return "".join(text.split()).casefold()


def symptom_matches(symptom: Symptom | None, exception_type: str | None, stdout: str, stderr: str) -> bool:
    if symptom is None:
        return False
    if symptom.exception_type and exception_type:
        # A dotted name in the traceback still matches the bare name the reporter wrote.
        if exception_type.rsplit(".", 1)[-1] == symptom.exception_type.rsplit(".", 1)[-1]:
            return True
    quote = _squash(symptom.quote)
    return bool(quote) and (quote in _squash(stdout) or quote in _squash(stderr))


def frames_in_package(files: list[str], package: str | None) -> bool:
    if not package:
        return False
    path = package.replace(".", "/")
    # Also accept the src layout, which is common in real repos.
    prefixes = (f"/src/{path}/", f"/src/src/{path}/")
    return any(file.startswith(prefixes) for file in files)


def _docker(args: list[str], commands: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    commands.append(shlex.join(args))
    try:
        return subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
        )
    except FileNotFoundError as error:
        raise SandboxError("docker isn't installed or isn't on PATH") from error


def _cleanup(args: list[str], commands: list[str]) -> None:
    try:
        _docker(args, commands, timeout=60)
    except (SandboxError, subprocess.TimeoutExpired):
        pass


def ensure_image(commands: list[str] | None = None) -> str:
    """Build the sandbox image unless it's already there."""
    commands = [] if commands is None else commands
    if _docker(["docker", "image", "inspect", IMAGE], commands, timeout=60).returncode == 0:
        return IMAGE
    built = _docker(["docker", "build", "-t", IMAGE, str(DOCKER_DIR)], commands, timeout=BUILD_TIMEOUT)
    if built.returncode != 0:
        raise SandboxError(f"docker build failed:\n{built.stderr[-2000:]}")
    return IMAGE


def _python_version(image: str, commands: list[str]) -> str | None:
    inspected = _docker(["docker", "image", "inspect", "--format", "{{json .Config.Env}}", image], commands, 60)
    if inspected.returncode != 0:
        return None
    for entry in json.loads(inspected.stdout or "[]"):
        if entry.startswith("PYTHON_VERSION="):
            return entry.split("=", 1)[1]
    return None


def export_revision(repo_dir: Path, sha: str, dest: Path, commands: list[str]) -> None:
    """Copy the tree at `sha` into `dest` with git archive. The checkout itself is never touched."""
    args = ["git", "-C", str(repo_dir), "archive", "--format=tar", sha]
    commands.append(shlex.join(args))
    archive = subprocess.run(args, capture_output=True, timeout=120)
    if archive.returncode != 0:
        raise SandboxError(f"git archive failed: {archive.stderr.decode(errors='replace').strip()}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(dest, filter="data")
    # uid 1000 in the container must read everything and write build files during install.
    for root, dirs, files in os.walk(dest):
        os.chmod(root, 0o777)
        for file in files:
            os.chmod(Path(root) / file, 0o644)


def reproduce(
    repo_dir: Path,
    revision: Revision,
    script: ReproScript,
    symptom: Symptom | None,
    package: str | None,
) -> RunResult:
    started = time.monotonic()
    commands: list[str] = []
    run_id = uuid.uuid4().hex[:12]
    names = {"install": f"bb-{run_id}-install", "run": f"bb-{run_id}-run", "volume": f"bb-{run_id}-deps"}

    with tempfile.TemporaryDirectory(prefix="bigbrother-") as tmp:
        try:
            result = _reproduce(Path(tmp), Path(repo_dir), revision, script, symptom, package, names, commands)
        except (SandboxError, subprocess.TimeoutExpired, OSError, tarfile.TarError) as error:
            result = RunResult(status=ExecutionStatus.SANDBOX_ERROR, stderr=str(error))
        finally:
            # Always, even when the install or run timed out or docker failed.
            _cleanup(["docker", "rm", "-f", names["install"], names["run"]], commands)
            _cleanup(["docker", "volume", "rm", "-f", names["volume"]], commands)

    return result.model_copy(update={"commands": commands, "duration_s": round(time.monotonic() - started, 2)})


def _reproduce(
    work: Path,
    repo_dir: Path,
    revision: Revision,
    script: ReproScript,
    symptom: Symptom | None,
    package: str | None,
    names: dict[str, str],
    commands: list[str],
) -> RunResult:
    os.chmod(work, 0o755)
    src = work / "src"
    src.mkdir()
    script_path = work / "repro.py"
    script_path.write_text(script.code, encoding="utf-8")
    os.chmod(script_path, 0o644)

    image = ensure_image(commands)
    python_version = _python_version(image, commands)
    export_revision(repo_dir, revision.sha, src, commands)

    created = _docker(["docker", "volume", "create", names["volume"]], commands, timeout=60)
    if created.returncode != 0:
        raise SandboxError(f"docker volume create failed: {created.stderr.strip()}")

    try:
        install = _docker(install_command(names["install"], src, names["volume"], image), commands, INSTALL_TIMEOUT)
    except subprocess.TimeoutExpired:
        _cleanup(["docker", "kill", names["install"]], commands)
        return RunResult(
            status=ExecutionStatus.INSTALL_FAILED,
            stderr=f"install took longer than {INSTALL_TIMEOUT} seconds",
            python_version=python_version,
        )
    if install.returncode != 0:
        return RunResult(
            status=ExecutionStatus.INSTALL_FAILED,
            exit_code=install.returncode,
            stdout=install.stdout[-OUTPUT_CAP:],
            stderr=install.stderr[-OUTPUT_CAP:],
            python_version=python_version,
        )

    try:
        run = _docker(run_command(names["run"], src, names["volume"], script_path, image), commands, RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        _cleanup(["docker", "kill", names["run"]], commands)
        return RunResult(
            status=ExecutionStatus.TIMEOUT,
            stderr=f"the script ran longer than {RUN_TIMEOUT} seconds",
            python_version=python_version,
        )
    # 125 to 127 mean docker couldn't start the container, not that the script exited.
    if run.returncode in (125, 126, 127):
        return RunResult(
            status=ExecutionStatus.SANDBOX_ERROR,
            exit_code=run.returncode,
            stderr=run.stderr,
            python_version=python_version,
        )

    exception_type, files = parse_traceback(run.stderr)
    return RunResult(
        status=ExecutionStatus.RAN,
        exit_code=run.returncode,
        stdout=run.stdout,
        stderr=run.stderr,
        exception_type=exception_type,
        traceback_files=files,
        symptom_matched=symptom_matches(symptom, exception_type, run.stdout, run.stderr),
        in_package=frames_in_package(files, package),
        python_version=python_version,
    )
