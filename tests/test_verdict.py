import pytest

from bigbrother.schema import (
    Basis,
    CheckState,
    Confidence,
    ExecutionStatus,
    Excerpt,
    Extraction,
    Label,
    OldInstall,
    Premise,
    PremiseResult,
    ReproScript,
    Revision,
    RevisionSource,
    RunResult,
    Shadowing,
    Symptom,
)
from bigbrother.verdict import decide

TAG = Revision(sha="a" * 40, source=RevisionSource.TAG, ref="v1.1.0")
GUESS = Revision(sha="b" * 40, source=RevisionSource.ISSUE_DATE, note="last commit before the issue")

EXTRACTION = Extraction(
    central_claim="parse_url raises ValueError on long URLs",
    package="tinylib",
    claimed_version="1.1.0",
    symptom=Symptom(kind="exception", quote="ValueError: URL too long", exception_type="ValueError"),
    has_steps=True,
)
OWN_CODE = ReproScript(code="from tinylib import parse_url", origin="reporter")
GENERATED = ReproScript(code="from tinylib import parse_url", origin="model")


def present(value, central=True):
    return PremiseResult(premise=Premise(kind="symbol", value=value, central=central), state=CheckState.PRESENT,
                         excerpt=Excerpt(path="tinylib/urls.py", line=4, text=f"def {value.split('.')[-1]}(url):"))


def absent(value, central=True, kind="symbol"):
    return PremiseResult(premise=Premise(kind=kind, value=value, central=central), state=CheckState.ABSENT,
                         detail="not defined anywhere in tinylib")


def ran(**fields):
    base = {"status": ExecutionStatus.RAN, "exit_code": 0, "imported_from_checkout": True}
    return RunResult(**(base | fields))


CRASHED_AS_REPORTED = {"exit_code": 1, "exception_type": "ValueError", "symptom_matched": True, "in_package": True}


def test_rule_1_reproduced_is_confirmed():
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], ran(**CRASHED_AS_REPORTED), TAG)
    assert (verdict.label, verdict.confidence, verdict.basis, verdict.rule) == (Label.CONFIRMED, Confidence.HIGH, Basis.EVIDENCE, 1)
    assert "(ValueError: URL too long) inside the package" in verdict.reasons[0]


def test_rule_1_wins_over_a_wrong_minor_version_but_lists_it():
    premises = [present("tinylib.parse_url"), absent("1.1.5", central=False, kind="version")]
    verdict = decide(EXTRACTION, premises, ran(**CRASHED_AS_REPORTED), TAG)
    assert verdict.label == Label.CONFIRMED
    assert any("minor version '1.1.5' is absent" in r for r in verdict.reasons)


def test_rule_1_wins_even_over_an_absent_central_premise():
    # The bug really happens, so a misnamed function in the report doesn't make it invalid.
    verdict = decide(EXTRACTION, [absent("tinylib.parse_uri")], ran(**CRASHED_AS_REPORTED), TAG)
    assert verdict.rule == 1
    assert any("central symbol 'tinylib.parse_uri' is absent" in r for r in verdict.reasons)


@pytest.mark.parametrize("run", [
    ran(exit_code=1, exception_type="ValueError", symptom_matched=True, in_package=False),
    ran(symptom_matched=True),  # exited cleanly but printed the reported text
])
def test_a_symptom_outside_the_package_is_not_confirmed(run):
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], run, TAG)
    assert (verdict.rule, verdict.confidence) == (4, Confidence.LOW)
    assert "not from inside the package" in verdict.reasons[0]


def test_rule_2_missing_central_function_is_invalid():
    verdict = decide(EXTRACTION, [absent("tinylib.parse_url_v2")], None, TAG)
    assert (verdict.label, verdict.confidence, verdict.rule) == (Label.INVALID, Confidence.HIGH, 2)
    assert "central symbol 'tinylib.parse_url_v2' doesn't exist (not defined anywhere in tinylib)" in verdict.reasons[0]
    assert any("v1.1.0" in r and "the tag" in r for r in verdict.reasons)


def test_rule_2_on_a_date_guess_is_medium():
    verdict = decide(EXTRACTION, [absent("tinylib.parse_url_v2")], None, GUESS)
    assert (verdict.label, verdict.confidence) == (Label.INVALID, Confidence.MEDIUM)
    assert any("guess from the issue date" in r for r in verdict.reasons)


def test_rule_2_beats_a_clean_run():
    verdict = decide(EXTRACTION, [absent("tinylib.parse_url_v2")], ran(), TAG, repro=OWN_CODE)
    assert verdict.rule == 2


def test_an_absent_minor_premise_alone_is_not_invalid():
    verdict = decide(EXTRACTION, [absent("tinylib.helper", central=False)], ran(), TAG, repro=GENERATED)
    assert verdict.rule == 3


def test_unknown_central_premise_is_not_invalid():
    unknown = PremiseResult(premise=Premise(kind="symbol", value="otherlib.f", central=True), state=CheckState.UNKNOWN,
                            detail="package not found")
    verdict = decide(EXTRACTION, [unknown], None, TAG)
    assert verdict.rule == 5
    assert any("is unknown (package not found)" in r for r in verdict.reasons)


def test_rule_3_reporters_own_code_running_cleanly_is_high():
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], ran(), TAG, repro=OWN_CODE)
    assert (verdict.label, verdict.confidence, verdict.rule) == (Label.CANNOT_REPRODUCE, Confidence.HIGH, 3)
    assert "reporter's own code ran cleanly" in verdict.reasons[0]


def test_rule_3_a_script_qwen_wrote_running_cleanly_is_low():
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], ran(), TAG, repro=GENERATED)
    assert (verdict.confidence, verdict.rule) == (Confidence.LOW, 3)
    assert "Qwen wrote" in verdict.reasons[0]


def test_rule_1_with_a_script_qwen_wrote_is_medium():
    crashed = ran(exit_code=1, exception_type="ValueError", symptom_matched=True, in_package=True)
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], crashed, TAG, repro=GENERATED)
    assert (verdict.label, verdict.confidence, verdict.rule) == (Label.CONFIRMED, Confidence.MEDIUM, 1)
    assert any("Qwen wrote the script" in r for r in verdict.reasons)


def test_rule_3_is_medium_when_the_import_wasnt_checked():
    verdict = decide(EXTRACTION, [], ran(imported_from_checkout=None), TAG, repro=OWN_CODE)
    assert verdict.confidence == Confidence.MEDIUM
    assert any("checked-out package" in r for r in verdict.reasons)


def test_rule_4_different_failure_is_low():
    run = ran(exit_code=1, exception_type="KeyError", in_package=True)
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], run, TAG)
    assert (verdict.label, verdict.confidence, verdict.rule) == (Label.CANNOT_REPRODUCE, Confidence.LOW, 4)
    assert "KeyError inside the package" in verdict.reasons[0]


@pytest.mark.parametrize("status", [ExecutionStatus.INSTALL_FAILED, ExecutionStatus.TIMEOUT,
                                    ExecutionStatus.NO_STEPS, ExecutionStatus.SANDBOX_ERROR, ExecutionStatus.NOT_RUN])
def test_rule_5_blocked_is_a_fallback(status):
    verdict = decide(EXTRACTION, [present("tinylib.parse_url")], RunResult(status=status), TAG)
    assert (verdict.label, verdict.confidence, verdict.basis, verdict.rule) == (
        Label.CANNOT_REPRODUCE, Confidence.LOW, Basis.FALLBACK, 5)


def test_rule_5_with_no_steps_says_so():
    no_steps = EXTRACTION.model_copy(update={"has_steps": False})
    verdict = decide(no_steps, [], None, TAG)
    assert verdict.rule == 5
    assert verdict.reasons[0].startswith("the report has no steps to run")


def test_a_run_against_some_other_install_is_blocked():
    run = ran(**CRASHED_AS_REPORTED, imported_from_checkout=False)
    verdict = decide(EXTRACTION, [], run, TAG)
    assert verdict.rule == 5
    assert "other than the checkout" in verdict.reasons[0]


def test_the_blocked_label_is_a_setting():
    verdict = decide(EXTRACTION, [], None, TAG, blocked_label=Label.INVALID)
    assert (verdict.label, verdict.basis) == (Label.INVALID, Basis.FALLBACK)


def test_no_revision_skips_rule_2():
    verdict = decide(EXTRACTION, [absent("tinylib.parse_url_v2")], None, None)
    assert verdict.rule == 5
    assert "no revision could be picked" in verdict.reasons


def test_no_quoted_symptom_means_nothing_to_confirm():
    no_symptom = EXTRACTION.model_copy(update={"symptom": None})
    verdict = decide(no_symptom, [], ran(**CRASHED_AS_REPORTED), TAG)
    assert verdict.label != Label.CONFIRMED


WRONG_OUTPUT = EXTRACTION.model_copy(update={"symptom": Symptom(kind="wrong_output", quote="1000.0 sextillion")})
PRINTS_IT = ReproScript(code="from humanize import intword\nprint(intword(10**24 - 1))  # '1000.0 sextillion'\n", origin="reporter")


def test_reporters_code_printing_the_wrong_output_is_confirmed_at_medium():
    # humanize #400: a real bug, the comment holding the expected text doesn't count as faking it.
    verdict = decide(WRONG_OUTPUT, [], ran(symptom_matched=True), TAG, repro=PRINTS_IT)
    assert (verdict.label, verdict.confidence, verdict.rule) == (Label.CONFIRMED, Confidence.MEDIUM, 1)


def test_a_script_that_just_prints_the_text_proves_nothing():
    fake = ReproScript(code="print('1000.0 sextillion')\n", origin="reporter")
    verdict = decide(WRONG_OUTPUT, [], ran(symptom_matched=True), TAG, repro=fake)
    assert verdict.rule == 4


def test_a_generated_script_printing_wrong_output_doesnt_confirm():
    generated = PRINTS_IT.model_copy(update={"origin": "model"})
    verdict = decide(WRONG_OUTPUT, [], ran(symptom_matched=True), TAG, repro=generated)
    assert verdict.rule == 4


SHADOWED = Shadowing(module="select", path="/Users/me/scripts/select.py",
                     quote="AttributeError: module 'select' has no attribute 'select'")


def test_a_shadowed_module_is_invalid_at_medium():
    run = ran(exit_code=1, exception_type="ModuleNotFoundError")
    verdict = decide(EXTRACTION, [], run, TAG, shadowing=SHADOWED)
    assert (verdict.label, verdict.confidence, verdict.rule) == (Label.INVALID, Confidence.MEDIUM, 2)
    assert "/Users/me/scripts/select.py loaded in place of the module 'select'" in verdict.reasons[0]


def test_a_real_reproduction_beats_shadowing():
    verdict = decide(EXTRACTION, [], ran(**CRASHED_AS_REPORTED), TAG, shadowing=SHADOWED)
    assert verdict.label == Label.CONFIRMED


def test_shadowing_needs_no_run_at_all():
    verdict = decide(EXTRACTION.model_copy(update={"has_steps": False}), [], None, TAG, shadowing=SHADOWED)
    assert (verdict.label, verdict.basis) == (Label.INVALID, Basis.EVIDENCE)


OLD = OldInstall(owner="Console", name="save_svg", path="rich/console.py", line=2479, text="def save_svg(",
                 added_in="v12.1.0", released="2022-04-03T14:48:15+01:00")


def test_an_old_install_is_invalid_at_medium():
    verdict = decide(EXTRACTION.model_copy(update={"has_steps": False}), [], None, TAG, old_install=OLD)
    assert (verdict.label, verdict.confidence, verdict.rule, verdict.basis) == (Label.INVALID, Confidence.MEDIUM, 2, Basis.EVIDENCE)
    assert "defined at rich/console.py:2479" in verdict.reasons[0]
    assert "first shipped in v12.1.0 on 03 Apr 2022" in verdict.reasons[0]


def test_a_real_reproduction_beats_an_old_install():
    assert decide(EXTRACTION, [], ran(**CRASHED_AS_REPORTED), TAG, old_install=OLD).label == Label.CONFIRMED
