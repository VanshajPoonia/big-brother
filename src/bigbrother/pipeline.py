"""One issue from start to finish. Lane functions come in as arguments, so tests can use fakes.

Every stage turns its own failure into a note and carries on, and a report is always returned.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from bigbrother import __version__
from bigbrother.contracts import CheckPremises, Reproduce, ResolveRevision
from bigbrother.extract import extract
from bigbrother.extract.code import reporter_script
from bigbrother.extract.model import Model, ModelError
from bigbrother.extract.repair import broke_on_its_own, repair
from bigbrother.schema import (
    CheckState,
    ExecutionStatus,
    Extraction,
    Issue,
    Label,
    Premise,
    Report,
    Revision,
    RunResult,
)
from bigbrother.verdict import decide

NOT_THE_PACKAGE = {"tests", "test", "testing", "docs", "doc", "examples", "example", "benchmarks", "scripts", "tools"}


def repo_packages(repo_dir: Path, sha: str) -> list[str]:
    """Importable top-level packages in the checkout: folders with an __init__.py, plain or under src/."""
    listed = subprocess.run(["git", "-C", str(repo_dir), "ls-tree", "-r", "--name-only", sha],
                            capture_output=True, text=True, timeout=30, check=True).stdout.splitlines()
    found = []
    for path in listed:
        parts = path.split("/")
        if parts[0] == "src":
            parts = parts[1:]
        if len(parts) == 2 and parts[1] == "__init__.py" and parts[0] not in NOT_THE_PACKAGE and parts[0].isidentifier():
            found.append(parts[0])
    return sorted(set(found))


def pick_package(candidates: list[str], guess: str | None, repo: str) -> str | None:
    """Qwen's guess if the repo has it, else the one named like the repo, else the only one."""
    top = guess.split(".")[0] if guess else None
    if top in candidates:
        return guess
    name = repo.split("/")[1].lower().replace("-", "_")
    for wanted in (name, name.removeprefix("python_"), name.removeprefix("py"), name.removesuffix("_python")):
        if wanted in candidates:
            return wanted
    return candidates[0] if len(candidates) == 1 else guess


def _missing_in(repo_dir: Path, revision: Revision, check_premises: CheckPremises):
    """True when the source at `revision` definitely lacks module.name. Unsure counts as present."""

    def missing(module: str, name: str) -> bool:
        try:
            [result] = check_premises(repo_dir, revision, [Premise(kind="symbol", value=f"{module}.{name}", central=False)])
        except Exception:  # noqa: BLE001  an unsure check never removes anything
            return False
        return result.state == CheckState.ABSENT

    return missing


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

    # 2b. Which package the report is about comes from the repo, not from the model.
    if revision is not None:
        try:
            package = pick_package(repo_packages(repo_dir, revision.sha), extraction.package, issue.repo)
        except (OSError, subprocess.SubprocessError) as error:
            package = extraction.package
            notes.append(f"couldn't list the repo's packages: {error}")
        if package != extraction.package:
            notes.append(f"the package is {package!r} from the repo, not {extraction.package!r} as Qwen read it")
            extraction = extraction.model_copy(update={"package": package})

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
    elif not model_available:
        # Without the model there's no quoted symptom, so a run couldn't show anything either way.
        notes.append("skipped the run, without the model there's no reported symptom to look for")
    elif script is None:
        run = RunResult(status=ExecutionStatus.NO_STEPS)
    else:
        try:
            run = reproduce(repo_dir, revision, script, extraction.symptom, extraction.package)
        except Exception as error:  # noqa: BLE001
            run = RunResult(status=ExecutionStatus.SANDBOX_ERROR, stderr=str(error))
            notes.append(f"the sandbox failed: {error}")

    # 4b. One repair if the reporter's script broke on its own, like a missing import.
    if model_available and script is not None and broke_on_its_own(run):
        first_error = run.exception_type
        try:
            fixed, call, repair_notes = repair(script, run, extraction.package, extraction.symptom, model,
                                               missing=_missing_in(repo_dir, revision, check_premises))
            calls.append(call)
            notes += repair_notes
        except ModelError as error:
            fixed = None
            notes.append(f"the model couldn't repair the script: {error}")
        if fixed is not None:
            notes.append(f"the reporter's script failed with its own {first_error}, so Qwen repaired it once and it ran again")
            script = fixed
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
