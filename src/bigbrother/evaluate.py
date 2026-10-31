"""Score Big Brother against hand-checked issues, honestly whichever way it's graded."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from bigbrother.schema import Basis, EvalCase, Label, Report

LABELS = list(Label)


def load_cases(path: Path) -> list[EvalCase]:
    return [EvalCase.model_validate(case) for case in yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []]


@dataclass
class Metrics:
    total: int
    correct: int
    decided: int  # cases where the label came from evidence, not the blocked fallback
    decided_correct: int
    crashed: int
    confusion: dict[Label, dict[Label | None, int]] = field(default_factory=dict)
    false_invalid: int = 0
    seconds: list[float] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def decided_accuracy(self) -> float:
        return self.decided_correct / self.decided if self.decided else 0.0

    def precision_recall(self, label: Label) -> tuple[float | None, float | None]:
        said = sum(row.get(label, 0) for row in self.confusion.values())
        hit = self.confusion.get(label, {}).get(label, 0)
        expected = sum(self.confusion.get(label, {}).values())
        return (hit / said if said else None, hit / expected if expected else None)


def score(cases: list[EvalCase], reports: list[Report | None], seconds: list[float] | None = None) -> Metrics:
    """`reports[i]` is None when that case crashed. A crash always counts as wrong."""
    confusion: dict[Label, dict[Label | None, int]] = {label: {} for label in LABELS}
    metrics = Metrics(total=len(cases), correct=0, decided=0, decided_correct=0, crashed=0,
                      confusion=confusion, seconds=list(seconds or []))
    for case, report in zip(cases, reports, strict=True):
        said = report.verdict.label if report else None
        row = confusion[case.expected]
        row[said] = row.get(said, 0) + 1
        right = said == case.expected
        metrics.correct += right
        if report is None:
            metrics.crashed += 1
        elif report.verdict.basis == Basis.EVIDENCE:
            metrics.decided += 1
            metrics.decided_correct += right
        if said == Label.INVALID and case.expected != Label.INVALID:
            metrics.false_invalid += 1
    return metrics


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def render(metrics: Metrics, rows: list[tuple[EvalCase, Report | None]]) -> str:
    lines = [
        "# Eval results",
        "",
        f"- Accuracy, all cases: **{metrics.correct}/{metrics.total} ({_pct(metrics.accuracy)})**",
        f"- Accuracy where the label came from evidence: {metrics.decided_correct}/{metrics.decided} ({_pct(metrics.decided_accuracy)})",
        f"- Fell back because nothing could run: {metrics.total - metrics.decided - metrics.crashed}. Crashed: {metrics.crashed}",
        f"- Said invalid when it wasn't: {metrics.false_invalid}",
    ]
    if metrics.seconds:
        lines.append(f"- Seconds per issue: {sum(metrics.seconds) / len(metrics.seconds):.0f} on average")
    lines += ["", "| Expected \\ Said | " + " | ".join(l.value for l in LABELS) + " | crashed |", "| --- " * (len(LABELS) + 2) + "|"]
    for expected in LABELS:
        row = metrics.confusion[expected]
        lines.append(f"| {expected.value} | " + " | ".join(str(row.get(l, 0)) for l in LABELS) + f" | {row.get(None, 0)} |")
    lines += ["", "| Label | Precision | Recall |", "| --- | --- | --- |"]
    for label in LABELS:
        p, r = metrics.precision_recall(label)
        lines.append(f"| {label.value} | {_pct(p)} | {_pct(r)} |")
    lines += ["", "| Case | Expected | Said | Rule | Why |", "| --- | --- | --- | --- | --- |"]
    for case, report in rows:
        if report is None:
            lines.append(f"| {case.id} | {case.expected.value} | crashed | | |")
            continue
        v = report.verdict
        mark = "" if v.label == case.expected else " ✗"
        lines.append(f"| [{case.id}]({case.issue_url}) | {case.expected.value} | {v.label.value}{mark} | {v.rule} | {v.reasons[0] if v.reasons else ''} |")
    return "\n".join(lines) + "\n"
