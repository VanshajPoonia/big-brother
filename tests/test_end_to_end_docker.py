"""The whole check with the real premise checks and the real Docker sandbox. Only the model is replayed."""

import json

import pytest

from bigbrother.extract.model import ReplayModel
from bigbrother.pipeline import check
from bigbrother.premises import check_premises, resolve_revision
from bigbrother.sandbox import reproduce
from bigbrother.schema import ExecutionStatus, Label, ModelCall
from test_sandbox_docker import docker_running

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(not docker_running(), reason="docker info failed, Docker isn't running"),
]


def test_real_bug_is_confirmed_by_a_real_run(load_issue, tinylib_repo):
    answer = {"central_claim": "parse_url raises ValueError on long URLs", "package": "tinylib", "claimed_version": "1.1.0",
              "premises": [{"kind": "symbol", "value": "tinylib.parse_url", "central": True}],
              "symptom": {"kind": "exception", "quote": "ValueError: URL too long", "exception_type": "ValueError"},
              "has_steps": True}
    model = ReplayModel([ModelCall(step="extract", model="qwen3:4b", request={}, response={"message": {"content": json.dumps(answer)}})])

    report = check(load_issue("real_bug"), tinylib_repo.path, model,
                   resolve_revision=resolve_revision, check_premises=check_premises, reproduce=reproduce)

    assert report.run.status == ExecutionStatus.RAN
    assert report.run.exception_type == "ValueError"
    assert (report.verdict.label, report.verdict.rule) == (Label.CONFIRMED, 1)
