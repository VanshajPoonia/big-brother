"""Shared data models. This file is the contract between lanes: only Lane A changes it."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
VERSION = re.compile(r"^v?\d+(\.\d+){0,3}[A-Za-z0-9.+-]*$")
SHA = r"^[0-9a-f]{7,40}$"
OUTPUT_CAP = 64 * 1024


class Label(StrEnum):
    CONFIRMED = "confirmed"
    CANNOT_REPRODUCE = "cannot reproduce"
    INVALID = "invalid"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Basis(StrEnum):
    EVIDENCE = "evidence"
    FALLBACK = "fallback"


class CheckState(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"
    ERROR = "error"


class ExecutionStatus(StrEnum):
    RAN = "ran"
    INSTALL_FAILED = "install_failed"
    TIMEOUT = "timeout"
    NO_STEPS = "no_steps"
    NOT_RUN = "not_run"
    SANDBOX_ERROR = "sandbox_error"


class RevisionSource(StrEnum):
    TAG = "tag"
    PYPI = "pypi"
    ISSUE_DATE = "issue_date"


class Issue(BaseModel):
    """A GitHub issue. Only the title and body are ever used, never comments or labels."""

    url: str
    repo: str = Field(pattern=r"^[\w.-]+/[\w.-]+$")
    number: int
    title: str
    body: str
    created_at: datetime

    @property
    def text(self) -> str:
        return f"{self.title}\n\n{self.body}"


# Qwen fills in the models below, so they reject unknown fields and odd values.


class Premise(BaseModel):
    """Something the report takes for granted, like a function or version existing."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["symbol", "version"]
    value: str = Field(min_length=1, max_length=200)
    central: bool

    @model_validator(mode="after")
    def check_shape(self) -> Premise:
        pattern = IDENTIFIER if self.kind == "symbol" else VERSION
        if not pattern.match(self.value):
            raise ValueError(f"{self.value!r} doesn't look like a {self.kind}")
        return self


class Symptom(BaseModel):
    """What the reporter says goes wrong. `quote` must come word for word from the report."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["exception", "wrong_output", "hang", "other"]
    quote: str = Field(min_length=1, max_length=300)
    exception_type: str | None = Field(default=None, max_length=100)

    @field_validator("exception_type")
    @classmethod
    def check_exception_type(cls, value: str | None) -> str | None:
        if value is not None and not IDENTIFIER.match(value):
            raise ValueError(f"{value!r} isn't an exception name")
        return value


class Extraction(BaseModel):
    """Output of Qwen call 1."""

    model_config = ConfigDict(extra="forbid")

    central_claim: str = Field(min_length=1, max_length=300)
    package: str | None = Field(default=None, max_length=100)
    claimed_version: str | None = Field(default=None, max_length=50)
    premises: list[Premise] = Field(default_factory=list, max_length=10)
    symptom: Symptom | None = None
    has_steps: bool

    @field_validator("package")
    @classmethod
    def check_package(cls, value: str | None) -> str | None:
        if value is not None and not IDENTIFIER.match(value):
            raise ValueError(f"{value!r} isn't an import name")
        return value

    @field_validator("claimed_version")
    @classmethod
    def check_version(cls, value: str | None) -> str | None:
        if value is not None and not VERSION.match(value):
            raise ValueError(f"{value!r} isn't a version")
        return value


class GeneratedScript(BaseModel):
    """Output of Qwen call 2."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=4000)


class ReproScript(BaseModel):
    code: str = Field(min_length=1, max_length=4000)
    origin: Literal["reporter", "model"]


class Revision(BaseModel):
    sha: str = Field(pattern=SHA)
    source: RevisionSource
    ref: str | None = None
    note: str = ""


class Excerpt(BaseModel):
    path: str
    line: int = Field(ge=1)
    text: str = Field(max_length=500)


class PremiseResult(BaseModel):
    premise: Premise
    state: CheckState
    excerpt: Excerpt | None = None
    detail: str = ""

    @model_validator(mode="after")
    def present_symbols_need_source(self) -> PremiseResult:
        if self.premise.kind == "symbol" and self.state == CheckState.PRESENT and self.excerpt is None:
            raise ValueError("a present symbol needs a source excerpt")
        return self


class RunResult(BaseModel):
    status: ExecutionStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    exception_type: str | None = None
    traceback_files: list[str] = Field(default_factory=list)
    symptom_matched: bool = False
    in_package: bool = False
    imported_from_checkout: bool | None = None
    commands: list[str] = Field(default_factory=list)
    image_digest: str | None = None
    python_version: str | None = None
    packages: list[str] = Field(default_factory=list)
    duration_s: float = 0.0

    @field_validator("stdout", "stderr")
    @classmethod
    def cap_output(cls, value: str) -> str:
        return value[:OUTPUT_CAP]


class ModelCall(BaseModel):
    """One request to the model and its raw response, saved as evidence."""

    step: Literal["extract", "repro"]
    model: str
    request: dict
    response: dict
    attempts: int = 1
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    duration_s: float | None = None


class Verdict(BaseModel):
    label: Label
    confidence: Confidence
    basis: Basis
    rule: int = Field(ge=1, le=5)
    reasons: list[str] = Field(default_factory=list)


class EvalCase(BaseModel):
    """One hand-checked issue in eval/cases.yaml."""

    id: str = Field(pattern=r"^[\w.-]+$")
    issue_url: str
    repo: str = Field(pattern=r"^[\w.-]+/[\w.-]+$")
    expected: Label
    checked_by: str
    note: str = ""


class Report(BaseModel):
    tool_version: str
    model_available: bool
    issue: Issue
    revision: Revision | None = None
    extraction: Extraction | None = None
    premises: list[PremiseResult] = Field(default_factory=list)
    repro: ReproScript | None = None
    run: RunResult | None = None
    verdict: Verdict
    model_calls: list[ModelCall] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
