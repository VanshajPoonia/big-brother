"""The label rules from docs/ARCHITECTURE.md. The model never picks the label: this file does.

Rules are tried top to bottom and the first one that fits wins:

1. The repro ran and hit the quoted symptom inside the package: confirmed, high.
2. A central premise is absent: invalid, high (medium when the revision is a date guess).
3. The repro ran cleanly against the checked-out package: cannot reproduce, medium
   (high when it was the reporter's own code).
4. The repro failed some other way: cannot reproduce, low.
5. Nothing ran (install failed, timeout, no steps, sandbox error): the blocked label,
   low, basis fallback. `cannot reproduce` by default, changeable with `blocked_label`.
"""

from __future__ import annotations

from bigbrother.schema import (
    Basis,
    CheckState,
    Confidence,
    ExecutionStatus,
    Extraction,
    Label,
    PremiseResult,
    ReproScript,
    Revision,
    RevisionSource,
    RunResult,
    Verdict,
)


def _where(result: PremiseResult) -> str:
    if result.excerpt:
        return f" ({result.excerpt.path}:{result.excerpt.line})"
    return f" ({result.detail})" if result.detail else ""


def _premise_notes(premises: list[PremiseResult], skip: set[int]) -> list[str]:
    """Every premise that isn't simply present gets a line, so nothing is hidden by the label."""
    notes = []
    for i, result in enumerate(premises):
        if i in skip or result.state == CheckState.PRESENT:
            continue
        kind = "central" if result.premise.central else "minor"
        notes.append(f"{kind} {result.premise.kind} {result.premise.value!r} is {result.state.value}{_where(result)}")
    return notes


def _revision_note(revision: Revision | None) -> list[str]:
    if revision is None:
        return ["no revision could be picked"]
    how = {RevisionSource.TAG: "the tag", RevisionSource.PYPI: "the PyPI release", RevisionSource.ISSUE_DATE: "the issue date"}
    ref = f" {revision.ref}" if revision.ref else ""
    return [f"checked at {revision.sha[:12]}{ref}, picked from {how[revision.source]}"]


def _blocked(run: RunResult | None, extraction: Extraction) -> str | None:
    """Why nothing usable ran, or None if something did."""
    if run is None or run.status == ExecutionStatus.NOT_RUN:
        return "the report has no steps to run" if not extraction.has_steps else "nothing was run"
    if run.status != ExecutionStatus.RAN:
        return {
            ExecutionStatus.INSTALL_FAILED: "the package didn't install at that revision",
            ExecutionStatus.TIMEOUT: "the repro timed out",
            ExecutionStatus.NO_STEPS: "the report has no steps to run",
            ExecutionStatus.SANDBOX_ERROR: "the sandbox failed",
        }[run.status]
    if run.imported_from_checkout is False:
        return "the script imported the package from somewhere other than the checkout"
    return None


def decide(
    extraction: Extraction,
    premises: list[PremiseResult],
    run: RunResult | None,
    revision: Revision | None,
    *,
    repro: ReproScript | None = None,
    blocked_label: Label = Label.CANNOT_REPRODUCE,
) -> Verdict:
    context = _revision_note(revision)
    blocked = _blocked(run, extraction)

    # Rule 1. A wrong minor detail never overrides a real reproduction, it's only listed.
    if blocked is None and run.symptom_matched and run.in_package:
        hit = f"{run.exception_type}: " if run.exception_type else ""
        reasons = [f"the repro hit the reported symptom ({hit}{extraction.symptom.quote if extraction.symptom else 'as reported'}) inside the package"]
        return Verdict(label=Label.CONFIRMED, confidence=Confidence.HIGH, basis=Basis.EVIDENCE, rule=1,
                       reasons=reasons + _premise_notes(premises, set()) + context)

    # Rule 2.
    absent = [i for i, r in enumerate(premises) if r.premise.central and r.state == CheckState.ABSENT]
    if absent and revision is not None:
        guessed = revision.source == RevisionSource.ISSUE_DATE
        reasons = [f"central {premises[i].premise.kind} {premises[i].premise.value!r} doesn't exist{_where(premises[i])}" for i in absent]
        if guessed:
            reasons.append("the revision is a guess from the issue date, so it may not be the version the reporter used")
        return Verdict(label=Label.INVALID, confidence=Confidence.MEDIUM if guessed else Confidence.HIGH,
                       basis=Basis.EVIDENCE, rule=2, reasons=reasons + _premise_notes(premises, set(absent)) + context)

    if blocked is None and run.exit_code == 0 and run.exception_type is None and not run.symptom_matched:
        # Rule 3.
        own_code = repro is not None and repro.origin == "reporter"
        confidence = Confidence.HIGH if own_code else Confidence.MEDIUM
        what = "the reporter's own code" if own_code else "a generated script"
        reasons = [f"{what} ran cleanly, the reported symptom didn't appear"]
        if run.imported_from_checkout is None:
            confidence = Confidence.MEDIUM
            reasons.append("couldn't confirm the script used the checked-out package")
        return Verdict(label=Label.CANNOT_REPRODUCE, confidence=confidence, basis=Basis.EVIDENCE, rule=3,
                       reasons=reasons + _premise_notes(premises, set()) + context)

    if blocked is None:
        # Rule 4.
        if run.symptom_matched:
            # Matching text alone isn't enough: a script can print anything. Only a failure
            # inside the package counts, so wrong-output reports can't be confirmed yet.
            reasons = ["the reported symptom showed up, but not from inside the package, so it doesn't count"]
        else:
            how = f"with {run.exception_type}" if run.exception_type else f"with exit code {run.exit_code}"
            where = "inside the package" if run.in_package else "outside the package"
            reasons = [f"the repro failed {how} {where}, which isn't the reported symptom"]
        return Verdict(label=Label.CANNOT_REPRODUCE, confidence=Confidence.LOW, basis=Basis.EVIDENCE, rule=4,
                       reasons=reasons + _premise_notes(premises, set()) + context)

    # Rule 5.
    reasons = [f"{blocked}, so the label is the blocked policy ({blocked_label.value}), not evidence"]
    return Verdict(label=blocked_label, confidence=Confidence.LOW, basis=Basis.FALLBACK, rule=5,
                   reasons=reasons + _premise_notes(premises, set()) + context)
