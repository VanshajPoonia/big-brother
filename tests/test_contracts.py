from bigbrother import contracts
from bigbrother.schema import ExecutionStatus, ReproScript, RunResult


def skip_everything(repo_dir, revision, script, symptom, package) -> RunResult:
    return RunResult(status=ExecutionStatus.NOT_RUN)


def test_a_lane_function_fits_its_contract():
    reproduce: contracts.Reproduce = skip_everything
    result = reproduce(None, None, ReproScript(code="pass", origin="model"), None, None)
    assert result.status == ExecutionStatus.NOT_RUN
