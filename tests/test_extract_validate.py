from bigbrother.extract.validate import symptom_is_quoted
from bigbrother.schema import Symptom


def test_symptom_quote_must_come_from_the_report(load_issue):
    issue = load_issue("real_bug")

    assert symptom_is_quoted(issue, Symptom(kind="exception", quote="ValueError:   URL too long"))
    assert not symptom_is_quoted(issue, Symptom(kind="exception", quote="KeyError: host"))
