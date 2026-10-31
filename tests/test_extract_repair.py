import json

import pytest

from bigbrother.extract.model import ReplayModel
from bigbrother.extract.repair import broke_on_its_own, repair, unsafe
from bigbrother.schema import ExecutionStatus, ModelCall, ReproScript, RunResult, Symptom

SYMPTOM = Symptom(kind="exception", quote="ValueError: URL too long", exception_type="ValueError")
BROKEN = ReproScript(code='parse_url("x" * 300)\n', origin="reporter")
NAME_ERROR = RunResult(status=ExecutionStatus.RAN, exit_code=1, exception_type="NameError",
                       stderr="Traceback (most recent call last):\nNameError: name 'parse_url' is not defined")


def qwen_writes(code):
    return ReplayModel([ModelCall(step="repro", model="qwen3:4b", request={}, response={"message": {"content": json.dumps({"code": code})}})])


@pytest.mark.parametrize("run, broken", [
    (NAME_ERROR, True),
    (NAME_ERROR.model_copy(update={"exception_type": "ModuleNotFoundError"}), True),
    (NAME_ERROR.model_copy(update={"in_package": True}), False),  # failed inside the package: that's evidence
    (NAME_ERROR.model_copy(update={"exception_type": "ValueError"}), False),
    (RunResult(status=ExecutionStatus.INSTALL_FAILED), False),
    # humanize #400: the wrong output printed, then a pasted root-cause block hit NameError.
    (NAME_ERROR.model_copy(update={"symptom_matched": True}), False),
    (None, False),
])
def test_which_failures_are_the_scripts_own(run, broken):
    assert broke_on_its_own(run) is broken


def test_a_repair_is_a_repro_call_with_the_fixed_code():
    fixed, call, _ = repair(BROKEN, NAME_ERROR, "tinylib", SYMPTOM, qwen_writes('from tinylib import parse_url\nparse_url("x" * 300)'))
    assert fixed.code.startswith("from tinylib import parse_url\n")
    assert call.step == "repro"


@pytest.mark.parametrize("code, why", [
    ("raise ValueError('URL too long')", "raises"),
    ("assert False", "raises"),
    ("import sys\nsys.exit(1)", "sys.exit"),
    ("try:\n    f()\nexcept Exception:\n    pass", "catches"),
    ("print('ValueError: URL too long')", "reported text"),
    ("def (", "doesn't parse"),
])
def test_repairs_that_could_fake_evidence_are_rejected(code, why):
    assert why in unsafe(code, SYMPTOM)
    fixed, _, notes = repair(BROKEN, NAME_ERROR, "tinylib", SYMPTOM, qwen_writes(code))
    assert fixed is None
    assert why in notes[0]


def test_the_script_and_error_are_marked_as_untrusted():
    model = qwen_writes("from tinylib import parse_url\nparse_url('x')")
    repair(BROKEN, NAME_ERROR, "tinylib", SYMPTOM, model)
    # ReplayModel doesn't keep messages, so check the prompt text directly.
    from bigbrother.extract.repair import SYSTEM_PROMPT
    assert "untrusted" in SYSTEM_PROMPT


ORIGINAL = "# feed it an empty dict\nupdate_in({}, [4], f)\nclojure_update_in({}, [4], f)\n"


@pytest.mark.parametrize("fixed, same", [
    ("from toolz import update_in\n# feed it an empty dict\nupdate_in({}, [4], f)\nclojure_update_in({}, [4], f)\n", True),
    ("from toolz import update_in\nupdate_in({}, [4], f)\n", True),  # a line dropped
    ("import math\nupdate_in({}, [4], f)\n", True),  # stdlib import
    ("from toolz import update_in\nupdate_in({}, [5], f)\n", False),  # an argument changed
    ("from toolz import update_in\nf = 1\nupdate_in({}, [4], f)\n", False),  # a line added
    ("clojure_update_in({}, [4], f)\nupdate_in({}, [4], f)\n", False),  # reordered
    ("import requests\nupdate_in({}, [4], f)\n", False),  # import from another package
    ("from . import x\nupdate_in({}, [4], f)\n", False),  # relative import
])
def test_only_added_imports(fixed, same):
    from bigbrother.extract.repair import only_added_imports
    assert only_added_imports(ORIGINAL, fixed, "toolz") is same


def test_an_import_only_repair_keeps_the_reporters_code_as_evidence():
    fixed, _, notes = repair(BROKEN, NAME_ERROR, "tinylib", SYMPTOM, qwen_writes('from tinylib import parse_url\nparse_url("x" * 300)'))
    assert fixed.origin == "reporter"
    assert "still the reporter's" in notes[0]


def test_a_repair_that_changes_the_code_is_the_models():
    fixed, _, notes = repair(BROKEN, NAME_ERROR, "tinylib", SYMPTOM, qwen_writes('from tinylib import parse_url\nparse_url("y")'))
    assert fixed.origin == "model"
    assert notes == []
