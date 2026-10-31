import pytest
from pydantic import ValidationError

from bigbrother.schema import (
    OUTPUT_CAP,
    Basis,
    CheckState,
    Confidence,
    ExecutionStatus,
    Excerpt,
    Extraction,
    Label,
    Premise,
    PremiseResult,
    Report,
    RunResult,
    Symptom,
    Verdict,
)


def test_labels_match_the_graded_names():
    assert [label.value for label in Label] == ["confirmed", "cannot reproduce", "invalid"]


@pytest.mark.parametrize("value", ["parse_url", "tinylib.urls.parse_url", "_private"])
def test_symbol_premise_accepts_dotted_names(value):
    Premise(kind="symbol", value=value, central=True)


@pytest.mark.parametrize("value", ["rm -rf /", "parse_url()", "1abc", "a..b"])
def test_symbol_premise_rejects_anything_else(value):
    with pytest.raises(ValidationError):
        Premise(kind="symbol", value=value, central=True)


@pytest.mark.parametrize("value", ["1.1.0", "v2.4.1", "3.0.0rc1", "2026.1"])
def test_version_premise_accepts_versions(value):
    Premise(kind="version", value=value, central=False)


def test_version_premise_rejects_words():
    with pytest.raises(ValidationError):
        Premise(kind="version", value="latest", central=False)


def test_extraction_rejects_fields_it_does_not_know():
    with pytest.raises(ValidationError):
        Extraction.model_validate({"central_claim": "x", "has_steps": False, "label": "confirmed"})


def test_extraction_schema_is_strict_for_ollama():
    assert Extraction.model_json_schema()["additionalProperties"] is False


def test_symptom_needs_a_real_exception_name():
    with pytest.raises(ValidationError):
        Symptom(kind="exception", quote="boom", exception_type="os.system('x')")


def test_present_symbol_needs_an_excerpt():
    premise = Premise(kind="symbol", value="parse_url", central=True)
    with pytest.raises(ValidationError):
        PremiseResult(premise=premise, state=CheckState.PRESENT)

    excerpt = Excerpt(path="tinylib/urls.py", line=1, text="def parse_url(url):")
    PremiseResult(premise=premise, state=CheckState.PRESENT, excerpt=excerpt)
    PremiseResult(premise=premise, state=CheckState.UNKNOWN)


def test_run_output_is_capped():
    run = RunResult(status=ExecutionStatus.RAN, stdout="x" * (OUTPUT_CAP + 10))
    assert len(run.stdout) == OUTPUT_CAP


def test_eval_cases_load_from_yaml():
    import yaml

    from bigbrother.schema import EvalCase

    raw = yaml.safe_load(
        """
- id: tinylib-2
  issue_url: https://github.com/daggers/tinylib/issues/2
  repo: daggers/tinylib
  expected: cannot reproduce
  checked_by: Radhika
"""
    )
    assert EvalCase.model_validate(raw[0]).expected == Label.CANNOT_REPRODUCE


def test_report_round_trips_through_json(load_issue):
    report = Report(
        tool_version="0.1.0",
        model_available=False,
        issue=load_issue("no_steps"),
        verdict=Verdict(label=Label.CANNOT_REPRODUCE, confidence=Confidence.LOW, basis=Basis.FALLBACK, rule=5),
    )
    assert Report.model_validate_json(report.model_dump_json()) == report
