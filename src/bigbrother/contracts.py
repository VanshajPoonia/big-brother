"""The function each lane implements. The pipeline only talks to lanes through these.

Lane B puts `resolve_revision` and `check_premises` in `bigbrother.premises`.
Lane C puts `reproduce` in `bigbrother.sandbox`.
Lane D puts `render_markdown` in `bigbrother.report`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from bigbrother.schema import (
    Extraction,
    Issue,
    Premise,
    PremiseResult,
    Report,
    ReproScript,
    Revision,
    RunResult,
    Symptom,
)


class ResolveRevision(Protocol):
    def __call__(self, repo_dir: Path, issue: Issue, extraction: Extraction) -> Revision:
        """Pick the commit the reporter most likely had: claimed tag, PyPI version, or the
        last commit before the issue was opened. Record which one in `Revision.source`."""


class CheckPremises(Protocol):
    def __call__(self, repo_dir: Path, revision: Revision, premises: list[Premise]) -> list[PremiseResult]:
        """Return one result per premise. Say `unknown` rather than `absent` when unsure."""


class Reproduce(Protocol):
    def __call__(
        self,
        repo_dir: Path,
        revision: Revision,
        script: ReproScript,
        symptom: Symptom | None,
        package: str | None,
    ) -> RunResult:
        """Install the repo at `revision`, run `script` offline, and report what happened.
        `symptom_matched` and `in_package` must come from the actual output."""


class RenderMarkdown(Protocol):
    def __call__(self, report: Report) -> str:
        """Turn a report into the Markdown a maintainer reads."""
