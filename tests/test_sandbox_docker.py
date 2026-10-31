"""Sandbox tests against a real Docker daemon, on the tinylib fixture."""

import os
import subprocess

import pytest

from bigbrother import sandbox
from bigbrother.schema import OUTPUT_CAP, ExecutionStatus, ReproScript, Revision, RevisionSource, Symptom


def docker_running() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# GitHub Actions sets CI. There a missing Docker should fail the run, not skip it.
pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(
        not docker_running() and not os.environ.get("CI"), reason="docker info failed, Docker isn't running"
    ),
]

LONG_URL = ReproScript(
    code='from tinylib import parse_url\n\nparse_url("http://example.com/" + "a" * 300)\nprint("parsed")\n',
    origin="reporter",
)
SYMPTOM = Symptom(kind="exception", quote="ValueError: URL too long", exception_type="ValueError")


def at(repo, tag: str) -> Revision:
    return Revision(sha=repo.tags[tag], source=RevisionSource.TAG, ref=tag)


def leftovers(commands: list[str]) -> list[str]:
    names = {part for command in commands for part in command.split() if part.startswith("bb-")}
    containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, check=True
    ).stdout.split()
    volumes = subprocess.run(
        ["docker", "volume", "ls", "--format", "{{.Name}}"], capture_output=True, text=True, check=True
    ).stdout.split()
    return sorted(names & (set(containers) | set(volumes)))


def test_long_url_raises_in_package_at_1_1_0(tinylib_repo):
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), LONG_URL, SYMPTOM, "tinylib")
    assert result.status == ExecutionStatus.RAN, result.stderr
    assert result.exit_code == 1
    assert result.exception_type == "ValueError"
    assert "/src/tinylib/urls.py" in result.traceback_files
    assert result.symptom_matched
    assert result.in_package
    assert result.python_version and result.python_version.startswith("3.12")
    assert result.image_digest and result.image_digest.startswith("sha256:")
    assert result.imported_from_checkout is True
    assert any(line.startswith("-e file:///src") for line in result.packages), result.packages
    assert any("--network none" in command for command in result.commands)
    assert leftovers(result.commands) == []


def test_long_url_runs_cleanly_at_1_0_0(tinylib_repo):
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.0.0"), LONG_URL, SYMPTOM, "tinylib")
    assert result.status == ExecutionStatus.RAN, result.stderr
    assert result.exit_code == 0
    assert result.stdout.strip() == "parsed"
    assert result.imported_from_checkout is True
    assert result.exception_type is None
    assert not result.symptom_matched
    assert not result.in_package
    assert leftovers(result.commands) == []


def test_no_network_and_read_only_inside_the_run(tinylib_repo):
    script = ReproScript(
        code=(
            "import socket\n"
            "try:\n"
            "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
            "    print('network: yes')\n"
            "except OSError:\n"
            "    print('network: no')\n"
            "try:\n"
            "    open('/src/tinylib/new.py', 'w')\n"
            "    print('src: writable')\n"
            "except OSError:\n"
            "    print('src: read-only')\n"
        ),
        origin="model",
    )
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), script, None, "tinylib")
    assert result.status == ExecutionStatus.RAN, result.stderr
    assert result.stdout.split("\n")[:2] == ["network: no", "src: read-only"]


def test_unknown_package_leaves_the_import_check_open(tinylib_repo):
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), LONG_URL, None, "not_tinylib")
    assert result.status == ExecutionStatus.RAN, result.stderr
    assert result.imported_from_checkout is None


def test_huge_output_is_capped(tinylib_repo):
    script = ReproScript(code="import sys\nsys.stdout.write('x' * 5_000_000 + 'end')\n", origin="model")
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), script, None, "tinylib")
    assert result.status == ExecutionStatus.RAN, result.stderr
    assert len(result.stdout) <= OUTPUT_CAP
    assert result.stdout.endswith("end")


def test_install_timeout_is_install_failed(tinylib_repo, monkeypatch):
    monkeypatch.setattr(sandbox, "INSTALL_TIMEOUT", 1)
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), LONG_URL, SYMPTOM, "tinylib")
    assert result.status == ExecutionStatus.INSTALL_FAILED
    assert result.stderr.startswith("install took longer than 1 seconds")
    assert any(command.startswith("docker kill") for command in result.commands)
    assert not any("--network none" in command for command in result.commands)
    assert leftovers(result.commands) == []


def test_run_timeout_kills_the_container(tinylib_repo, monkeypatch):
    monkeypatch.setattr(sandbox, "RUN_TIMEOUT", 3)
    script = ReproScript(code="import time\ntime.sleep(30)\n", origin="model")
    result = sandbox.reproduce(tinylib_repo.path, at(tinylib_repo, "v1.1.0"), script, None, "tinylib")
    assert result.status == ExecutionStatus.TIMEOUT
    assert any(command.startswith("docker kill") for command in result.commands)
    assert leftovers(result.commands) == []
