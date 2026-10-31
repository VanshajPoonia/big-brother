import json
from pathlib import Path

import pytest

from bigbrother import __version__, sandbox
from bigbrother.cli import main
from bigbrother.extract import model as model_module
from bigbrother.extract.model import ReplayModel
from bigbrother.schema import ExecutionStatus, ModelCall, Report, RunResult

FIXTURES = Path(__file__).parent / "fixtures"


def test_version_prints_package_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"bigbrother {__version__}"


def test_no_arguments_exits_cleanly():
    assert main([]) == 0


def test_a_missing_issue_file_is_bad_input(tmp_path, capsys):
    assert main(["check", str(tmp_path / "nope.json"), "--repo", str(tmp_path)]) == 2
    assert "can't read the issue" in capsys.readouterr().err


def test_a_repo_that_isnt_a_clone_is_bad_input(tmp_path, capsys):
    issue = FIXTURES / "issues" / "real_bug.json"
    assert main(["check", str(issue), "--repo", str(tmp_path)]) == 2
    assert "isn't a git clone" in capsys.readouterr().err


def test_check_writes_both_reports(tmp_path, tinylib_repo, monkeypatch, capsys):
    monkeypatch.setattr(model_module, "default_model", lambda: ReplayModel.from_files(FIXTURES / "model" / "real_bug_extract.json"))
    crashed = RunResult(status=ExecutionStatus.RAN, exit_code=1, exception_type="ValueError", symptom_matched=True,
                        in_package=True, imported_from_checkout=True, commands=["docker run ..."])
    monkeypatch.setattr(sandbox, "reproduce", lambda *args: crashed)
    out = tmp_path / "out"

    code = main(["check", str(FIXTURES / "issues" / "real_bug.json"), "--repo", str(tinylib_repo.path), "--out", str(out)])

    assert code == 0
    report = Report.model_validate_json((out / "report.json").read_text())
    assert report.verdict.label == "confirmed"
    markdown = (out / "report.md").read_text()
    assert "**confirmed** (high confidence, rule 1, basis evidence)" in markdown
    assert "tinylib/urls.py:4" in markdown
    assert "**confirmed**" in capsys.readouterr().out


def test_json_flag_prints_the_report(tmp_path, tinylib_repo, monkeypatch, capsys):
    monkeypatch.setattr(model_module, "default_model", lambda: ReplayModel([]))
    issue = FIXTURES / "issues" / "no_steps.json"
    assert main(["check", str(issue), "--repo", str(tinylib_repo.path), "--out", str(tmp_path), "--json",
                 "--blocked-label", "invalid"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["verdict"]["label"] == "invalid"
    assert printed["verdict"]["basis"] == "fallback"
    assert printed["model_available"] is False
