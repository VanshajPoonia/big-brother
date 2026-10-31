"""Sandbox tests that don't need Docker."""

import subprocess
from pathlib import Path

import pytest

from bigbrother import sandbox
from bigbrother.schema import ExecutionStatus, ReproScript, Revision, RevisionSource, Symptom

SRC = Path("/tmp/work/src")
SCRIPT = Path("/tmp/work/repro.py")

TRACEBACK = """\
Traceback (most recent call last):
  File "/repro.py", line 2, in <module>
    parse_url("http://example.com/" + "a" * 300)
  File "/src/tinylib/urls.py", line 6, in parse_url
    raise ValueError("URL too long")
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: URL too long
"""

CHAINED = """\
Traceback (most recent call last):
  File "/src/tinylib/a.py", line 1, in <module>
KeyError: 'x'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/repro.py", line 4, in <module>
  File "/deps/venv/lib/python3.12/site-packages/other/b.py", line 9, in g
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
"""


def flag_value(command: list[str], flag: str) -> list[str]:
    return [command[i + 1] for i, part in enumerate(command) if part == flag]


def test_install_command_has_network_limits_and_only_src_and_deps():
    command = sandbox.install_command("bb-1-install", SRC, "bb-1-deps")
    assert command[:4] == ["docker", "run", "--name", "bb-1-install"]
    assert "--network" not in command
    assert flag_value(command, "--cpus") == ["1"]
    assert flag_value(command, "--memory") == ["1g"]
    assert flag_value(command, "--pids-limit") == ["256"]
    assert flag_value(command, "--mount") == [
        f"type=bind,source={SRC},target=/src",
        "type=volume,source=bb-1-deps,target=/deps",
    ]
    # The only environment variable is a version for packages that read theirs from git.
    assert flag_value(command, "-e") == ["SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0"]
    assert "--env" not in command and "--env-file" not in command
    assert command[-3:-1] == ["sh", "-c"]
    assert "uv venv /deps/venv --python /usr/local/bin/python3" in command[-1]
    assert "uv pip install --python /deps/venv/bin/python -e /src" in command[-1]
    assert command[-1].endswith("; status=$?; chmod -R a+rwX /src 2>/dev/null; exit $status")


def test_run_command_is_offline_read_only_and_limited():
    command = sandbox.run_command("bb-1-run", SRC, "bb-1-deps", SCRIPT)
    assert command[:4] == ["docker", "run", "--name", "bb-1-run"]
    assert flag_value(command, "--network") == ["none"]
    assert "--read-only" in command
    assert flag_value(command, "--tmpfs") == ["/tmp:size=64m"]
    assert flag_value(command, "--cap-drop") == ["ALL"]
    assert flag_value(command, "--security-opt") == ["no-new-privileges"]
    assert flag_value(command, "--user") == ["1000:1000"]
    assert flag_value(command, "--pids-limit") == ["128"]
    assert flag_value(command, "--memory") == ["1g"]
    assert flag_value(command, "--cpus") == ["1"]
    assert flag_value(command, "--mount") == [
        f"type=bind,source={SRC},target=/src,readonly",
        "type=volume,source=bb-1-deps,target=/deps,readonly",
        f"type=bind,source={SCRIPT},target=/repro.py,readonly",
    ]
    assert command[-2:] == ["/deps/venv/bin/python", "/repro.py"]


def test_parse_traceback_gets_type_and_every_frame():
    assert sandbox.parse_traceback(TRACEBACK) == ("ValueError", ["/repro.py", "/src/tinylib/urls.py"])


def test_parse_traceback_uses_the_last_traceback():
    exception_type, files = sandbox.parse_traceback(CHAINED)
    assert exception_type == "json.decoder.JSONDecodeError"
    assert files == ["/repro.py", "/deps/venv/lib/python3.12/site-packages/other/b.py"]


def test_parse_traceback_without_one():
    assert sandbox.parse_traceback("some warning\n") == (None, [])
    assert sandbox.parse_traceback("") == (None, [])


def test_parse_traceback_bare_exception_name():
    assert sandbox.parse_traceback('Traceback (most recent call last):\n  File "/repro.py", line 1\nKeyboardInterrupt\n') == (
        "KeyboardInterrupt",
        ["/repro.py"],
    )


@pytest.mark.parametrize(
    ("symptom", "exception_type", "stdout", "stderr", "expected"),
    [
        (Symptom(kind="exception", quote="boom", exception_type="ValueError"), "ValueError", "", "", True),
        (Symptom(kind="exception", quote="boom", exception_type="JSONDecodeError"), "json.decoder.JSONDecodeError", "", "", True),
        (Symptom(kind="exception", quote="boom", exception_type="ValueError"), "TypeError", "", "", False),
        (Symptom(kind="wrong_output", quote="Result is  42"), None, "result IS\n42\n", "", True),
        (Symptom(kind="other", quote="URL too long"), None, "", "ValueError: url too long", True),
        (Symptom(kind="wrong_output", quote="Result is 42"), None, "result is 41", "", False),
        (None, "ValueError", "", "", False),
    ],
)
def test_symptom_matches(symptom, exception_type, stdout, stderr, expected):
    assert sandbox.symptom_matches(symptom, exception_type, stdout, stderr) is expected


def test_frames_in_package():
    files = ["/repro.py", "/src/tinylib/urls.py"]
    assert sandbox.frames_in_package(files, "tinylib")
    assert sandbox.frames_in_package(["/src/src/tinylib/urls.py"], "tinylib")
    assert sandbox.frames_in_package(["/src/tinylib/sub/x.py"], "tinylib.sub")
    assert not sandbox.frames_in_package(files, "tiny")
    assert not sandbox.frames_in_package(files, None)
    assert not sandbox.frames_in_package(["/deps/venv/lib/python3.12/site-packages/tinylib/urls.py"], "tinylib")


def container(args):
    """"install" or "run" for a docker run command, else None."""
    if args[:3] == ["docker", "run", "--name"]:
        return args[3].rsplit("-", 1)[-1]
    return None


@pytest.fixture
def fake_docker(tmp_path, monkeypatch):
    """Swap docker for `respond(args)`, which returns (exit code, stdout, stderr) or raises."""
    monkeypatch.setattr(sandbox, "export_revision", lambda repo_dir, sha, dest, commands: None)
    calls = []

    def run(respond, symptom=None, package=None):
        def docker(args, commands, timeout):
            commands.append(" ".join(args))
            calls.append(args)
            return subprocess.CompletedProcess(args, *(respond(args) or (0, "", "")))

        monkeypatch.setattr(sandbox, "_docker", docker)
        revision = Revision(sha="a" * 40, source="tag")
        return sandbox.reproduce(tmp_path, revision, ReproScript(code="x", origin="model"), symptom, package)

    run.calls = calls
    return run


def assert_cleaned_up(calls):
    assert calls[-2][:3] == ["docker", "rm", "-f"]
    assert calls[-1][:4] == ["docker", "volume", "rm", "-f"]


def test_install_failure_skips_the_run(fake_docker):
    result = fake_docker(lambda args: (1, "", "error: no build backend") if container(args) == "install" else None)
    assert result.status == ExecutionStatus.INSTALL_FAILED
    assert result.exit_code == 1
    assert "no build backend" in result.stderr
    assert "run" not in [container(args) for args in fake_docker.calls]
    assert_cleaned_up(fake_docker.calls)


def test_install_timeout_is_install_failed(fake_docker):
    def respond(args):
        if container(args) == "install":
            raise subprocess.TimeoutExpired(args, 300)

    result = fake_docker(respond)
    assert result.status == ExecutionStatus.INSTALL_FAILED
    assert ["docker", "kill", fake_docker.calls[-4][3]] in fake_docker.calls
    assert_cleaned_up(fake_docker.calls)


def test_run_timeout_kills_and_cleans_up(fake_docker):
    def respond(args):
        if container(args) == "run":
            raise subprocess.TimeoutExpired(args, 60)

    result = fake_docker(respond)
    assert result.status == ExecutionStatus.TIMEOUT
    assert fake_docker.calls[-3][:2] == ["docker", "kill"]
    assert fake_docker.calls[-3][2].endswith("-run")
    assert_cleaned_up(fake_docker.calls)
    assert result.commands[-1].startswith("docker volume rm -f")


def test_docker_missing_is_sandbox_error(fake_docker):
    def respond(args):
        raise sandbox.SandboxError("docker isn't installed or isn't on PATH")

    result = fake_docker(respond)
    assert result.status == ExecutionStatus.SANDBOX_ERROR
    assert "docker" in result.stderr


def test_docker_refusing_to_start_is_sandbox_error(fake_docker):
    result = fake_docker(lambda args: (125, "", "docker: invalid mount") if container(args) == "run" else None)
    assert result.status == ExecutionStatus.SANDBOX_ERROR
    assert result.exit_code == 125
    assert_cleaned_up(fake_docker.calls)


def test_ran_parses_output(fake_docker):
    def respond(args):
        if container(args) == "run":
            return 1, "", TRACEBACK
        if "--format" in args:
            return 0, '["PATH=/usr/bin","PYTHON_VERSION=3.12.7"]', ""

    symptom = Symptom(kind="exception", quote="URL too long", exception_type="ValueError")
    result = fake_docker(respond, symptom=symptom, package="tinylib")
    assert result.status == ExecutionStatus.RAN
    assert result.exit_code == 1
    assert result.exception_type == "ValueError"
    assert result.traceback_files == ["/repro.py", "/src/tinylib/urls.py"]
    assert result.symptom_matched and result.in_package
    assert result.python_version == "3.12.7"
    assert len(result.commands) == len(fake_docker.calls)


def test_export_revision_copies_the_tree(tinylib_repo, tmp_path):
    dest = tmp_path / "export"
    dest.mkdir()
    commands = []
    sandbox.export_revision(tinylib_repo.path, tinylib_repo.tags["v1.0.0"], dest, commands)
    assert "MAX_LENGTH" not in (dest / "tinylib" / "urls.py").read_text()
    assert not (dest / ".git").exists()
    assert commands[0].startswith("git -C")


def test_a_release_tag_gives_the_build_its_version():
    command = sandbox.install_command("bb-1-install", SRC, "bb-1-deps", version="4.3.0")
    assert flag_value(command, "-e") == ["SETUPTOOLS_SCM_PRETEND_VERSION=4.3.0"]


@pytest.mark.parametrize("ref, version", [("v4.3.0", "4.3.0"), ("4.7.0", "4.7.0"), ("origin/main", None), (None, None), ("v1.2.3rc1", None)])
def test_release_version_only_for_plain_tags(ref, version):
    revision = Revision(sha="a" * 40, source=RevisionSource.TAG, ref=ref)
    assert sandbox._release_version(revision) == version
