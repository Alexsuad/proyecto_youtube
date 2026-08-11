from types import SimpleNamespace

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionStatus
from src.ai.execution import execute
from src.core.mission_completion_gate import MissionContract


def _evidence(passed: bool, ref: str) -> dict:
    return {"passed": passed, "evidence": [{"kind": "TEST", "ref": ref}]}


def _contract(review: str = "SELF_ONLY") -> MissionContract:
    return MissionContract.from_dict({
        "mission_id": "M-REDUCED", "artifact_id": "reduced", "artifact_version": "1.0.0",
        "authorized_paths": ["src/"], "protected_untracked_paths": [], "protected_untracked_baseline": [],
        "required_tests": [], "push_allowed": False,
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "a" * 40},
        "contains_material_repair": False,
        "state_requirements": {"control_path": "control.md", "required": {}, "forbidden": {}}, "schema_checks": [],
        "mission_mode": "REDUCED", "objective": "Fixture reduced mission.", "canonical_inputs": ["control.md"],
        "allowed_files": ["src/"], "expected_outputs": ["evidence.json"], "deterministic_validations": ["pytest"],
        "stop_conditions": ["canonical contradiction"], "review_policy": {"required_review": review},
        "owner_closure": {"required": True, "artifact": "control.md"},
    })


def _request(callbacks: dict) -> ExecutionRequest:
    return ExecutionRequest("CAP", "skill", "1", [], "execution_smoke_report", role="ROLE", config={"convergence_callbacks": callbacks})


@pytest.fixture
def reduced_execution(monkeypatch):
    import src.ai.execution as execution
    import src.ai.registry as registry

    def setup(contract):
        authorization = SimpleNamespace(contract_sha256="a" * 64)
        monkeypatch.setattr(execution, "preflight_controlled_execution", lambda request, root: {"authorization": authorization, "context_manifest": {"manifest_id": "CTX", "manifest_sha256": "b" * 64}, "reservation": None, "mission_contract": contract})
        monkeypatch.setattr(registry, "capture_pre_run_snapshot", lambda *args, **kwargs: None)
    return setup


def test_reduced_execution_converges_through_canonical_path(reduced_execution):
    reduced_execution(_contract())
    request = _request({"implement": lambda: _evidence(True, "implement"), "verify": lambda: _evidence(True, "verify"), "adversarial_review": lambda: _evidence(True, "review"), "repair": lambda _failure: _evidence(True, "repair")})
    result = execute(request)
    assert result.status is ExecutionStatus.CONVERGED
    assert result.usage["mission_convergence"]["status"] == "CONVERGED"
    assert result.usage["next_review_stage"] == "SELF_ONLY"
    assert request.config["resolved_context_manifest_sha256"] == "b" * 64


def test_reduced_execution_repairs_and_reverifies(reduced_execution):
    reduced_execution(_contract())
    calls = {"verify": 0}
    def verify():
        calls["verify"] += 1
        return _evidence(calls["verify"] > 1, f"verify-{calls['verify']}")
    result = execute(_request({"implement": lambda: _evidence(True, "implement"), "verify": verify, "adversarial_review": lambda: _evidence(True, "review"), "repair": lambda _failure: _evidence(True, "repair")}))
    assert result.status is ExecutionStatus.CONVERGED
    assert any(event["stage"] == "REPAIR" for event in result.usage["mission_convergence"]["events"])


def test_reduced_execution_rejects_false_pass_without_evidence(reduced_execution):
    reduced_execution(_contract())
    result = execute(_request({"implement": lambda: _evidence(True, "implement"), "verify": lambda: {"passed": True}, "adversarial_review": lambda: _evidence(True, "review"), "repair": lambda _failure: _evidence(True, "repair")}))
    assert result.status is ExecutionStatus.FAILED
    assert result.usage["mission_convergence"]["status"] == "MAX_ITERATIONS_REACHED"


def test_reduced_execution_cannot_converge_after_failed_implementation(reduced_execution):
    reduced_execution(_contract())
    result = execute(_request({"implement": lambda: _evidence(False, "implement"), "verify": lambda: _evidence(True, "verify"), "adversarial_review": lambda: _evidence(True, "review"), "repair": lambda _failure: _evidence(True, "repair")}))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert result.usage["mission_convergence"]["status"] == "BLOCKED"


def test_reduced_execution_reports_max_iterations(reduced_execution):
    reduced_execution(_contract())
    request = _request({"implement": lambda: _evidence(True, "implement"), "verify": lambda: _evidence(False, "verify"), "adversarial_review": lambda: _evidence(True, "review"), "repair": lambda _failure: _evidence(True, "repair")})
    request.config["convergence_max_iterations"] = 2
    result = execute(request)
    assert result.status is ExecutionStatus.FAILED
    assert result.usage["mission_convergence"]["status"] == "MAX_ITERATIONS_REACHED"


@pytest.mark.parametrize("review", ["INDEPENDENT_REVIEW", "OWNER_REVIEW"])
def test_reduced_execution_escalates_without_self_approval(reduced_execution, review):
    reduced_execution(_contract(review))
    result = execute(_request({"implement": lambda: _evidence(True, "implement"), "verify": lambda: _evidence(True, "verify"), "adversarial_review": lambda: _evidence(True, "review"), "repair": lambda _failure: _evidence(True, "repair")}))
    assert result.status is ExecutionStatus.CONVERGED
    assert result.usage["next_review_stage"] == review
