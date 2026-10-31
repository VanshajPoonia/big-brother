from datetime import datetime, timezone

from bigbrother.evaluate import load_cases, render, score
from bigbrother.schema import Basis, Confidence, EvalCase, Issue, Label, Report, Verdict

ISSUE = Issue(url="https://github.com/o/r/issues/1", repo="o/r", number=1, title="t", body="b",
              created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))


def case(expected, n=1):
    return EvalCase(id=f"r-{n}", issue_url=f"https://github.com/o/r/issues/{n}", repo="o/r", expected=expected, checked_by="test")


def report(label, basis=Basis.EVIDENCE):
    verdict = Verdict(label=label, confidence=Confidence.LOW, basis=basis, rule=5 if basis == Basis.FALLBACK else 3, reasons=["why"])
    return Report(tool_version="0", model_available=True, issue=ISSUE, verdict=verdict)


def test_accuracy_is_counted_both_ways():
    cases = [case(Label.CONFIRMED, 1), case(Label.INVALID, 2), case(Label.CANNOT_REPRODUCE, 3), case(Label.INVALID, 4)]
    reports = [report(Label.CONFIRMED), report(Label.CANNOT_REPRODUCE, Basis.FALLBACK),
               report(Label.CANNOT_REPRODUCE, Basis.FALLBACK), None]
    m = score(cases, reports)

    assert (m.correct, m.total) == (2, 4)  # a crash counts as wrong
    assert (m.decided_correct, m.decided) == (1, 1)  # fallbacks and crashes left out
    assert m.crashed == 1
    assert m.confusion[Label.INVALID] == {Label.CANNOT_REPRODUCE: 1, None: 1}
    assert m.precision_recall(Label.CONFIRMED) == (1.0, 1.0)
    assert m.precision_recall(Label.INVALID) == (None, 0.0)


def test_false_invalids_are_counted():
    m = score([case(Label.CONFIRMED)], [report(Label.INVALID)])
    assert m.false_invalid == 1


def test_render_marks_wrong_answers():
    cases = [case(Label.CONFIRMED, 1), case(Label.INVALID, 2)]
    text = render(score(cases, [report(Label.CONFIRMED), report(Label.CANNOT_REPRODUCE)]), list(zip(cases, [report(Label.CONFIRMED), report(Label.CANNOT_REPRODUCE)])))
    assert "**1/2 (50%)**" in text
    assert "| cannot reproduce ✗ |" in text


def test_the_real_cases_file_loads():
    cases = load_cases("eval/cases.yaml")
    assert len(cases) >= 10
    assert len({c.id for c in cases}) == len(cases)
