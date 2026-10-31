import json

import pytest

from bigbrother.extract.model import ModelError, ReplayModel
from bigbrother.pipeline import check, pick_package, repo_packages
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
    # Without the model there's no quoted symptom, so nothing runs and the label is a fallback.
    assert (report.verdict.label, report.verdict.rule, report.verdict.basis) == (Label.CANNOT_REPRODUCE, 5, "fallback")
    assert report.run is None


@pytest.mark.parametrize("broken", ["resolve_revision", "check_premises", "reproduce"])
def test_a_crashing_lane_never_loses_the_report(load_issue, tinylib_repo, broken):
    def boom(*args):
        raise RuntimeError(f"{broken} blew up")

    lanes = {**LANES, "reproduce": FakeSandbox(CRASHED), broken: boom}
    report = check(load_issue("real_bug"), tinylib_repo.path, qwen("real_bug"), **lanes)
    assert any(f"{broken} blew up" in n for n in report.notes)
    assert report.verdict is not None


class SequenceSandbox:
    """Returns each result in turn, so the second run can differ from the first."""

    def __init__(self, *results):
        self.results, self.scripts = list(results), []

    def __call__(self, repo_dir, revision, script, symptom, package):
        self.scripts.append(script)
        return self.results.pop(0)


def qwen_and_repair(name, repaired_code):
    calls = [
        ModelCall(step="extract", model="qwen3:4b", request={}, response={"message": {"content": json.dumps(EXTRACT[name])}}),
        ModelCall(step="repro", model="qwen3:4b", request={}, response={"message": {"content": json.dumps({"code": repaired_code})}}),
    ]
    return ReplayModel(calls)


def test_a_script_missing_its_import_is_repaired_once_and_rerun(load_issue, tinylib_repo):
    own_error = RunResult(status=ExecutionStatus.RAN, exit_code=1, exception_type="NameError")
    sandbox = SequenceSandbox(own_error, CRASHED)
    model = qwen_and_repair("real_bug", 'from tinylib import parse_url\nparse_url("https://example.com/" + "a" * 300)')

    report = check(load_issue("real_bug"), tinylib_repo.path, model, reproduce=sandbox, **LANES)

    # The repair only added an import, so the code that ran is still the reporter's.
    assert [s.origin for s in sandbox.scripts] == ["reporter", "reporter"]
    assert sandbox.scripts[1].code.startswith("from tinylib import parse_url")
    assert (report.verdict.label, report.verdict.rule) == (Label.CONFIRMED, 1)
    assert [c.step for c in report.model_calls] == ["extract", "repro"]
    assert any("repaired it once" in n for n in report.notes)


def test_a_failure_inside_the_package_is_never_repaired(load_issue, tinylib_repo):
    sandbox = SequenceSandbox(CRASHED)
    report = check(load_issue("real_bug"), tinylib_repo.path, qwen("real_bug"), reproduce=sandbox, **LANES)
    assert len(sandbox.scripts) == 1
    assert report.repro.origin == "reporter"


def test_repo_packages_finds_the_importable_package(tinylib_repo):
    assert repo_packages(tinylib_repo.path, tinylib_repo.tags["v1.1.0"]) == ["tinylib"]


@pytest.mark.parametrize("candidates, guess, repo, picked", [
    (["toolz", "tlz"], "update_in", "pytoolz/toolz", "toolz"),  # toolz #99: Qwen named a function
    (["tlz", "toolz"], "tlz", "pytoolz/toolz", "tlz"),  # Qwen's guess is kept when the repo has it
    (["humanize"], "humanise", "python-humanize/humanize", "humanize"),
    (["yaml"], None, "yaml/pyyaml", "yaml"),  # the only one
    (["a", "b"], "c", "o/r", "c"),  # can't tell, keep the guess
    (["requests"], "requests.adapters", "psf/requests", "requests.adapters"),
])
def test_pick_package(candidates, guess, repo, picked):
    assert pick_package(candidates, guess, repo) == picked


def test_a_wrong_package_from_qwen_is_replaced_and_noted(load_issue, tinylib_repo):
    wrong = dict(EXTRACT["real_bug"], package="parse_url")
    call = ModelCall(step="extract", model="qwen3:4b", request={}, response={"message": {"content": json.dumps(wrong)}})
    sandbox = FakeSandbox(CRASHED)
    report = check(load_issue("real_bug"), tinylib_repo.path, ReplayModel([call]), reproduce=sandbox, **LANES)

    assert report.extraction.package == "tinylib"
    assert sandbox.calls[0][3] == "tinylib"
    assert "the package is 'tinylib' from the repo, not 'parse_url' as Qwen read it" in report.notes
