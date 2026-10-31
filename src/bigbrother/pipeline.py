"""One issue from start to finish. Lane functions come in as arguments, so tests can use fakes.

Every stage turns its own failure into a note and carries on, and a report is always returned.
"""

from __future__ import annotations

from pathlib import Path

from bigbrother import __version__
from bigbrother.contracts import CheckPremises, Reproduce, ResolveRevision
from bigbrother.extract import extract
from bigbrother.extract.code import reporter_script
from bigbrother.extract.model import Model, ModelError
from bigbrother.schema import (
    CheckState,
    ExecutionStatus,
    Extraction,
    Issue,
    Label,
    Report,
    RunResult,
)
from bigbrother.verdict import decide


def check(
    issue: Issue,
    repo_dir: Path,
    model: Model,
    *,
    resolve_revision: ResolveRevision,
    check_premises: CheckPremises,
    reproduce: Reproduce,
    blocked_label: Label = Label.CANNOT_REPRODUCE,
) -> Report:
    notes: list[str] = []
    calls = []

    # 1. Qwen reads the issue.
    try:
        extraction, call, extract_notes = extract(issue, model)
        calls.append(call)
        notes += extract_notes
        model_available = True
    except ModelError as error:
        extraction = Extraction(central_claim=issue.title[:300] or "(no title)", has_steps=False)
        notes.append(f"the model couldn't read the issue, so no claims were checked: {error}")
        model_available = False

    # Whether there's code to run comes from the report itself, not from the model.
    script = reporter_script(issue.body)
    if extraction.has_steps and script is None:
        notes.append("the model said the report has steps, but it has no runnable Python block")
    extraction = extraction.model_copy(update={"has_steps": script is not None})

    # 2. Which commit the reporter most likely had.
    revision = None
    try:
        revision = resolve_revision(repo_dir, issue, extraction)
    except Exception as error:  # noqa: BLE001  a lane bug must not lose the report
        notes.append(f"couldn't pick a revision: {error}")

    # 3. Do the functions and versions it relies on exist there?
    premises = []
    if revision is not None and extraction.premises:
        try:
            premises = check_premises(repo_dir, revision, extraction.premises)
        except Exception as error:  # noqa: BLE001
            notes.append(f"couldn't check the premises: {error}")

    # 4. Run the reporter's code, unless a central premise is already missing.
    run = None
    if any(r.premise.central and r.state == CheckState.ABSENT for r in premises):
        notes.append("skipped the run, a central premise doesn't exist")
    elif revision is None:
        pass
    elif script is None:
        run = RunResult(status=ExecutionStatus.NO_STEPS)
    else:
        try:
            run = reproduce(repo_dir, revision, script, extraction.symptom, extraction.package)
        except Exception as error:  # noqa: BLE001
            run = RunResult(status=ExecutionStatus.SANDBOX_ERROR, stderr=str(error))
            notes.append(f"the sandbox failed: {error}")

    # 5. Fixed rules pick the label.
    verdict = decide(extraction, premises, run, revision, repro=script, blocked_label=blocked_label)

    return Report(
        tool_version=__version__,
        model_available=model_available,
        issue=issue,
        revision=revision,
        extraction=extraction,
        premises=premises,
        repro=script,
        run=run,
        verdict=verdict,
        model_calls=calls,
        notes=notes,
    )
