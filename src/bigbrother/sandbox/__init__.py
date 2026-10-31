"""Lane C: install a repo at a revision and run a repro script in Docker.

Two containers per run. The install container has the network and writes the
dependencies into a fresh named volume. The run container has no network, a
read-only filesystem and sees the source and the dependencies read-only.
Every docker command goes into RunResult.commands as evidence, along with the
image digest, the Python version, `uv pip freeze` and where the package was
imported from.
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
import threading
import time
import uuid
from pathlib import Path

from bigbrother.schema import OUTPUT_CAP, ExecutionStatus, ReproScript, Revision, RunResult, Symptom

IMAGE = "bigbrother-sandbox:0.1"
DOCKER_DIR = Path(__file__).resolve().parents[3] / "docker"
INSTALL_TIMEOUT = 300
RUN_TIMEOUT = 60
BUILD_TIMEOUT = 600
# Lines of install output kept when the install times out.
TAIL_LINES = 50

# Imports the package with its own output swallowed, then prints the marker and
# the file it came from. Prints nothing if the import fails.
IMPORT_CHECK = """\
import contextlib, importlib, io, sys
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        module = importlib.import_module(sys.argv[1])
except BaseException:
    sys.exit(0)
path = getattr(module, "__file__", None) or next(iter(getattr(module, "__path__", [])), "")
print(sys.argv[2])
print(path)
"""
PACKAGE_NAME = re.compile(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)*$")

FRAME = re.compile(r'^\s+File "(?P<file>[^"]+)", line \d+')
EXCEPTION = re.compile(r"^(?P<type>[A-Za-z_][\w.]*)(:|$)")


class SandboxError(Exception):
    """Docker itself failed, not the repo or the script."""


def install_script(marker: str) -> str:
    # After a good install, the marker line and `uv pip freeze` go to stdout.
    # The build writes files like *.egg-info into /src as uid 1000. The chmod lets
    # the host user delete them afterwards, so it runs even when the install fails.
    return (
        "uv venv /deps/venv --python /usr/local/bin/python3"
        " && uv pip install --python /deps/venv/bin/python -e /src;"
        f" status=$?; if [ $status -eq 0 ]; then echo {marker}; uv pip freeze --python /deps/venv/bin/python; fi;"
        " chmod -R a+rwX /src 2>/dev/null; exit $status"
    )


def install_command(
    name: str, src: Path, volume: str, marker: str, image: str = IMAGE, version: str | None = None
) -> list[str]:
    # Network on, only the exported source and the volume. The one environment variable is a
    # version: packages that read theirs from git (setuptools-scm, hatch-vcs) fail without .git.
    return [
        "docker", "run", "--name", name, "-e", f"SETUPTOOLS_SCM_PRETEND_VERSION={version or FALLBACK_VERSION}",
        "--cpus", "1", "--memory", "1g", "--pids-limit", "256",
        "--mount", f"type=bind,source={src},target=/src",
        "--mount", f"type=volume,source={volume},target=/deps",
        image, "sh", "-c", install_script(marker),
    ]  # fmt: skip


FALLBACK_VERSION = "0.0.0"


def _release_version(revision: Revision) -> str | None:
    """The plain version for a tag like v4.3.0, or None when the revision isn't a release."""
    if revision.ref and re.fullmatch(r"v?\d+(\.\d+){0,3}", revision.ref):
        return revision.ref.removeprefix("v")
    return None


def run_command(
    name: str, src: Path, volume: str, script: Path, package: str | None = None, marker: str = "", image: str = IMAGE
) -> list[str]:
    entry = ["/deps/venv/bin/python", "/repro.py"]
    if package and marker and PACKAGE_NAME.match(package):
        # The import check runs first, in the same container, and its stderr is dropped.
        check = shlex.join(["/deps/venv/bin/python", "-c", IMPORT_CHECK, package, marker])
        entry = ["sh", "-c", f"{check} 2>/dev/null; exec {shlex.join(entry)}"]
    return [
        "docker", "run", "--name", name,
        "--network", "none", "--read-only", "--tmpfs", "/tmp:size=64m",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--user", "1000:1000", "--pids-limit", "128", "--memory", "1g", "--cpus", "1",
        "--mount", f"type=bind,source={src},target=/src,readonly",
        "--mount", f"type=volume,source={volume},target=/deps,readonly",
        "--mount", f"type=bind,source={script},target=/repro.py,readonly",
        "--workdir", "/tmp",
        image, *entry,
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


def split_at_marker(text: str, marker: str) -> tuple[str, str | None]:
    """The text before the marker line and the text after it, None when the marker isn't there."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == marker:
            return "".join(lines[:i]), "".join(lines[i + 1 :])
    return text, None


def imported_from(stdout: str, marker: str, package: str | None) -> tuple[str, bool | None]:
    """The script's own stdout, and whether the import check found the package under /src."""
    before, after = split_at_marker(stdout, marker) if package and marker else (stdout, None)
    if after is None:
        return stdout, None
    path, _, rest = after.partition("\n")
    return before + rest, path.strip().startswith("/src/")


class Capped:
    """Keeps the start and the end of a stream while it's read, at most `cap` characters in all."""

    def __init__(self, cap: int = OUTPUT_CAP) -> None:
        # Room for the note that says how much was cut.
        self.half = (cap - 100) // 2
        self.head = bytearray()
        self.tail = bytearray()
        self.dropped = 0

    def feed(self, chunk: bytes) -> None:
        room = self.half - len(self.head)
        if room > 0:
            self.head += chunk[:room]
            chunk = chunk[room:]
        self.tail += chunk
        extra = len(self.tail) - self.half
        if extra > 0:
            del self.tail[:extra]
            self.dropped += extra

    def text(self) -> str:
        head = self.head.decode("utf-8", errors="replace")
        tail = self.tail.decode("utf-8", errors="replace")
        cut = f"\n[{self.dropped} bytes cut]\n" if self.dropped else ""
        return (head + cut + tail).replace("\r\n", "\n")


def _read(stream, sink: Capped) -> None:
    for chunk in iter(lambda: stream.read(8192), b""):
        sink.feed(chunk)


def _docker(args: list[str], commands: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    """Run a command with its output capped while it's read. A timeout still carries the output so far."""
    commands.append(shlex.join(args))
    try:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as error:
        raise SandboxError("docker isn't installed or isn't on PATH") from error
    out, err = Capped(), Capped()
    readers = [
        threading.Thread(target=_read, args=(process.stdout, out), daemon=True),
        threading.Thread(target=_read, args=(process.stderr, err), daemon=True),
    ]
    timed_out = False
    with process:
        for reader in readers:
            reader.start()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait()
        except BaseException:
            process.kill()
            raise
        for reader in readers:
            reader.join(timeout=10)
    if timed_out:
        raise subprocess.TimeoutExpired(args, timeout, output=out.text(), stderr=err.text())
    return subprocess.CompletedProcess(args, process.returncode, out.text(), err.text())


def _cleanup(args: list[str], commands: list[str]) -> None:
    try:
        _docker(args, commands, timeout=60)
    except (SandboxError, subprocess.TimeoutExpired, OSError):
        pass


def _last_lines(*outputs: str | bytes | None) -> str:
    lines: list[str] = []
    for output in outputs:
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        lines += (output or "").splitlines()
    return "\n".join(lines[-TAIL_LINES:])


def ensure_image(commands: list[str] | None = None) -> str:
    """Build the sandbox image unless it's already there."""
    commands = [] if commands is None else commands
    if _docker(["docker", "image", "inspect", IMAGE], commands, timeout=60).returncode == 0:
        return IMAGE
    built = _docker(["docker", "build", "-t", IMAGE, str(DOCKER_DIR)], commands, timeout=BUILD_TIMEOUT)
    if built.returncode != 0:
        raise SandboxError(f"docker build failed:\n{built.stderr[-2000:]}")
    return IMAGE


def _image_info(image: str, commands: list[str]) -> dict:
    """The image digest and the Python version inside it."""
    args = ["docker", "image", "inspect", "--format", "{{.Id}} {{json .Config.Env}}", image]
    inspected = _docker(args, commands, 60)
    info = {"image_digest": None, "python_version": None}
    if inspected.returncode != 0:
        return info
    digest, _, env = inspected.stdout.strip().partition(" ")
    info["image_digest"] = digest or None
    for entry in json.loads(env or "[]"):
        if entry.startswith("PYTHON_VERSION="):
            info["python_version"] = entry.split("=", 1)[1]
    return info


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
    # Marks where our own output starts. The repo and the script can't guess it.
    marker = f"bigbrother-{uuid.uuid4().hex}"
    names = {"install": f"bb-{run_id}-install", "run": f"bb-{run_id}-run", "volume": f"bb-{run_id}-deps"}

    # A killed install can leave files the host user can't delete. Don't fail the result over that.
    with tempfile.TemporaryDirectory(prefix="bigbrother-", ignore_cleanup_errors=True) as tmp:
        try:
            result = _reproduce(Path(tmp), Path(repo_dir), revision, script, symptom, package, names, marker, commands)
        except Exception as error:
            # Never crash the pipeline. Anything that gets here is the sandbox's fault, not the repo's.
            result = RunResult(status=ExecutionStatus.SANDBOX_ERROR, stderr=f"{type(error).__name__}: {error}")
        finally:
            # Always, even when the install or run timed out, docker failed or our own code raised.
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
    marker: str,
    commands: list[str],
) -> RunResult:
    os.chmod(work, 0o755)
    src = work / "src"
    src.mkdir()
    script_path = work / "repro.py"
    script_path.write_text(script.code, encoding="utf-8")
    os.chmod(script_path, 0o644)

    image = ensure_image(commands)
    env = _image_info(image, commands)
    export_revision(repo_dir, revision.sha, src, commands)

    created = _docker(["docker", "volume", "create", names["volume"]], commands, timeout=60)
    if created.returncode != 0:
        raise SandboxError(f"docker volume create failed: {created.stderr.strip()}")

    try:
        install_args = install_command(names["install"], src, names["volume"], marker, image, _release_version(revision))
        install = _docker(install_args, commands, INSTALL_TIMEOUT)
    except subprocess.TimeoutExpired as timeout:
        _cleanup(["docker", "kill", names["install"]], commands)
        tail = _last_lines(timeout.output, timeout.stderr)
        return RunResult(
            status=ExecutionStatus.INSTALL_FAILED,
            stderr=f"install took longer than {INSTALL_TIMEOUT} seconds, last {TAIL_LINES} lines:\n{tail}",
            **env,
        )
    if install.returncode != 0:
        return RunResult(
            status=ExecutionStatus.INSTALL_FAILED,
            exit_code=install.returncode,
            stdout=install.stdout,
            stderr=install.stderr,
            **env,
        )
    _, freeze = split_at_marker(install.stdout, marker)
    env["packages"] = [line.strip() for line in (freeze or "").splitlines() if line.strip()]

    try:
        run_args = run_command(names["run"], src, names["volume"], script_path, package, marker, image)
        run = _docker(run_args, commands, RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        _cleanup(["docker", "kill", names["run"]], commands)
        return RunResult(
            status=ExecutionStatus.TIMEOUT,
            stderr=f"the script ran longer than {RUN_TIMEOUT} seconds",
            **env,
        )
    # 125 to 127 mean docker couldn't start the container, not that the script exited.
    if run.returncode in (125, 126, 127):
        return RunResult(
            status=ExecutionStatus.SANDBOX_ERROR,
            exit_code=run.returncode,
            stderr=run.stderr,
            **env,
        )

    stdout, from_checkout = imported_from(run.stdout, marker, package)
    exception_type, files = parse_traceback(run.stderr)
    return RunResult(
        status=ExecutionStatus.RAN,
        exit_code=run.returncode,
        stdout=stdout,
        stderr=run.stderr,
        exception_type=exception_type,
        traceback_files=files,
        symptom_matched=symptom_matches(symptom, exception_type, stdout, run.stderr),
        in_package=frames_in_package(files, package),
        imported_from_checkout=from_checkout,
        **env,
    )
