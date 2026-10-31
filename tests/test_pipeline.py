import json

import pytest

from bigbrother.extract.model import ModelError, ReplayModel
from bigbrother.pipeline import check
from bigbrother.premises import check_premises, resolve_revision
from bigbrother.schema import ExecutionStatus, Label, ModelCall, RunResult

EXTRACT = {
    "real_bug": {"central_claim": "parse_url raises ValueError on long URLs", "package": "tinylib", "claimed_version": "1.1.0",
                 "premises": [{"kind": "symbol", "value": "tinylib.parse_url", "central": True}],
                 "symptom": {"kind": "exception", "quote": "ValueError: URL too long", "exception_type": "ValueError"},
                 "has_steps": True},
    "missing_function": {"central_claim": "parse_url_v2 allows remote code execution", "package": "tinylib",
                         "claimed_version": "1.1.0", "premises": [{"kind": "symbol", "value": "tinylib.parse_url_v2", "central": True}],
                         "symptom": None, "has_steps": True},
    "no_steps": {"central_claim": "parse_url gives wrong results", "package": "tinylib", "claimed_version": None,
                 "premises": [{"kind": "symbol", "value": "tinylib.parse_url", "central": True}], "symptom": None, "has_steps": False},
}


def qwen(name):
    call = ModelCall(step="extract", model="qwen3:4b", request={}, response={"message": {"content": json.dumps(EXTRACT[name])}})
    return ReplayModel([call])


class FakeSandbox:
    def __init__(self, result):
        self.result, self.calls = result, []

    def __call__(self, repo_dir, revision, script, symptom, package):
        self.calls.append((revision.ref, script.origin, symptom, package))
        return self.result


CRASHED = RunResult(status=ExecutionStatus.RAN, exit_code=1, exception_type="ValueError", symptom_matched=True,
                    in_package=True, imported_from_checkout=True)
LANES = {"resolve_revision": resolve_revision, "check_premises": check_premises}


def test_real_bug_is_confirmed(load_issue, tinylib_repo):
    sandbox = FakeSandbox(CRASHED)
    report = check(load_issue("real_bug"), tinylib_repo.path, qwen("real_bug"), reproduce=sandbox, **LANES)

    assert (report.verdict.label, report.verdict.rule) == (Label.CONFIRMED, 1)
    assert sandbox.calls == [("v1.1.0", "reporter", report.extraction.symptom, "tinylib")]
    assert report.revision.sha == tinylib_repo.tags["v1.1.0"]
    assert report.model_available and report.model_calls[0].model == "qwen3:4b"


def test_missing_function_is_invalid_and_never_runs(load_issue, tinylib_repo):
    sandbox = FakeSandbox(CRASHED)
    report = check(load_issue("missing_function"), tinylib_repo.path, qwen("missing_function"), reproduce=sandbox, **LANES)

    assert (report.verdict.label, report.verdict.rule) == (Label.INVALID, 2)
    assert sandbox.calls == []
    assert report.extraction.has_steps is False
    assert "the model said the report has steps, but it has no runnable Python block" in report.notes


def test_no_steps_is_a_fallback(load_issue, tinylib_repo):
    report = check(load_issue("no_steps"), tinylib_repo.path, qwen("no_steps"), reproduce=FakeSandbox(CRASHED), **LANES)
    assert (report.verdict.label, report.verdict.rule, report.run.status) == (Label.CANNOT_REPRODUCE, 5, ExecutionStatus.NO_STEPS)


def test_blocked_label_is_passed_through(load_issue, tinylib_repo):
    report = check(load_issue("no_steps"), tinylib_repo.path, qwen("no_steps"), reproduce=FakeSandbox(CRASHED),
                   blocked_label=Label.INVALID, **LANES)
    assert report.verdict.label == Label.INVALID


def test_no_model_still_gives_a_report(load_issue, tinylib_repo):
    report = check(load_issue("real_bug"), tinylib_repo.path, ReplayModel([]), reproduce=FakeSandbox(CRASHED), **LANES)
    assert report.model_available is False
    assert report.model_calls == []
    assert any("the model couldn't read the issue" in n for n in report.notes)
    # Without the model there's no quoted symptom, so even a crash can't confirm anything.
    assert report.verdict.label == Label.CANNOT_REPRODUCE


@pytest.mark.parametrize("broken", ["resolve_revision", "check_premises", "reproduce"])
def test_a_crashing_lane_never_loses_the_report(load_issue, tinylib_repo, broken):
    def boom(*args):
        raise RuntimeError(f"{broken} blew up")

    lanes = {**LANES, "reproduce": FakeSandbox(CRASHED), broken: boom}
    report = check(load_issue("real_bug"), tinylib_repo.path, qwen("real_bug"), **lanes)
    assert any(f"{broken} blew up" in n for n in report.notes)
    assert report.verdict is not None
