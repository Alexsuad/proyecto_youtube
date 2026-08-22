"""Brecha 5 — integración real con el consumidor runtime (execution.execute).

Prueba que la gobernanza PLAN 005 se consume desde el camino real de ejecución,
no solo desde helpers aislados: una autorización de misión real acotada por
routing (allowed_routes) gobierna la ejecución del runtime y bloquea rutas y
perfiles fuera del candidate set autorizado.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionStatus
from src.ai.execution import execute
from src.core.mission_authorization import scope_checksum
from tests.core.test_all_schemas import VALID_FIXTURES


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _setup(
    root: Path,
    *,
    allowed_routes: list[str],
    role_id: str = "SCRIPT_PRODUCT_AUDITOR",
    availability_status: str | None = None,
    maturity_status: str = "DEFINED",
    authorized_profiles: list[str] | None = None,
    authorized_mode: str = "ANY",
) -> Path:
    (root / "config").mkdir(exist_ok=True)
    (root / "output").mkdir(exist_ok=True)
    import shutil
    shutil.copy(Path(__file__).resolve().parents[2] / "config/context_resolution_policy.json", root / "config/context_resolution_policy.json")
    capability = {
        "capability_id": "B5_I2_SEMANTIC_AUDITOR", "domain": "SCRIPT_PRODUCT",
        "functional_authority_domain": "SCRIPT_PRODUCT", "purpose": "Fixture real consumer",
        "functional_requirements": ["REQ-P5"], "implementation_kind": "DETERMINISTIC",
        "maturity_status": maturity_status,
        "assigned_role": [role_id],
        "prompt_reference": [],
        "execution_profile_refs": [],
        "routing_required": False,
    }
    if availability_status:
        capability["availability_status"] = availability_status
        capability["executability_evidence"] = {
            "contracts_resolvable": True,
            "implementation_present": True,
            "dependencies_satisfied": True,
        }
    if maturity_status == "DEMONSTRATED":
        (root / "impl.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "evidence.json").write_text("{}\n", encoding="utf-8")
        (root / "execution-evidence.json").write_text("{}\n", encoding="utf-8")
        capability.update({
            "implementation_refs": ["impl.py"],
            "evidence_refs": ["evidence.json"],
            "execution_evidence_refs": ["execution-evidence.json"],
        })
    (root / "config" / "capability_registry.json").write_text(json.dumps({
        "registry_version": "1.0.0", "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "P5_INTEGRATION", "compatibility_tokens": {
            "maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {},
        },
        "capabilities": [capability],
    }), encoding="utf-8")
    (root / "control.md").write_text("CURRENT_MISSION: P5_INTEGRATION\n", encoding="utf-8")
    state_sha = _sha(root / "control.md")
    profiles = authorized_profiles or ["ANY"]
    scope = {
        "mission_id": "P5_INTEGRATION", "capability_ids": ["B5_I2_SEMANTIC_AUDITOR"],
        "role_ids": [role_id], "execution_profile_ids": profiles,
        "execution_interface": "ANY", "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": ["output/"], "allowed_routes": allowed_routes,
        "execution_mode": authorized_mode, "live_state_sha256": state_sha,
        "contains_material_repair": False, "repair_integrity_evidence_path": "repair.json",
    }
    decision = root / "authority-decision.json"
    decision.write_text(json.dumps({"mission_id": "P5_INTEGRATION", "decision": "APPROVE", "artifact_version": "1.0.0", "authorized_scope_sha256": scope_checksum(scope)}), encoding="utf-8")
    auth = root / "mission-authorization.json"
    auth.write_text(json.dumps({"mission_id": "P5_INTEGRATION", "authorization": {
        "live_state_path": "control.md", "live_state_sha256": state_sha, "capability_ids": ["B5_I2_SEMANTIC_AUDITOR"],
        "role_ids": [role_id], "execution_profile_ids": profiles, "execution_interface": "ANY",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output/"], "allowed_routes": allowed_routes,
        "execution_mode": authorized_mode, "single_use": False,
        "authority_ref": "authority-decision.json", "authority_sha256": _sha(decision),
        "authorized_scope_sha256": scope_checksum(scope),
        "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY", "contains_material_repair": False,
        "repair_integrity_evidence_path": "repair.json",
    }}), encoding="utf-8")
    return auth


def _request(root: Path, *, execution_route: str, execution_profile: str = "mock", provider: str = "mock") -> ExecutionRequest:
    source = root / "analysis.json"
    source.write_text('{"analysis_id":"A-1"}', encoding="utf-8")
    from src.ai.contracts import InputArtifact

    return ExecutionRequest(
        capability_id="B5_I2_SEMANTIC_AUDITOR",
        skill_id="skill_auditar_suficiencia_semantica_b5_i2",
        skill_version="1.0.0",
        input_artifacts=[InputArtifact("analysis", "A-1", source, "RUN-P")],
        output_schema="b5_i2_semantic_sufficiency_audit",
        execution_mode="mock",
        provider=provider,
        execution_route=execution_route,
        execution_profile=execution_profile,
        mock_output=copy.deepcopy(VALID_FIXTURES["b5_i2_semantic_sufficiency_audit"]),
        output_artifact_kind="semantic_audit",
        output_artifact_id="B5I2-SSA-1",
        output_artifact_ref="semantic_audit:B5I2-SSA-1",
        episode_id="EP-1",
        role="SCRIPT_PRODUCT_AUDITOR",
        config={
            "repository_root": str(root),
            "mission_authorization_path": "mission-authorization.json",
            "execution_profile": execution_profile,
            "execution_route": execution_route,
            "mission_operation": "EXECUTE_CAPABILITY",
            "execution_interface": "ANY",
        },
    )


def test_real_runtime_blocks_route_outside_authorized_candidate_set(tmp_path: Path, monkeypatch) -> None:
    auth = _setup(tmp_path, allowed_routes=["local_model"])
    request = _request(tmp_path, execution_route="api_model", execution_profile="deepseek_chat")
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "routing scope" in (result.error or "") or "ROUTE" in (result.error or "")


def test_real_runtime_blocks_profile_outside_authorized_set(tmp_path: Path) -> None:
    _setup(tmp_path, allowed_routes=["local_model"])
    request = _request(tmp_path, execution_route="local_model", execution_profile="paid_profile")
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_real_runtime_rejects_unknown_provider_fail_closed(tmp_path: Path) -> None:
    _setup(tmp_path, allowed_routes=["local_model"])
    request = _request(tmp_path, execution_route="local_model", execution_profile="mock", provider="ghost")
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_real_runtime_requires_authorized_candidate_set_when_governed(tmp_path: Path, monkeypatch) -> None:
    _setup(tmp_path, allowed_routes=[])
    request = _request(tmp_path, execution_route="local_model")
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def _ready_route():
    return SimpleNamespace(
        status="READY", provider_adapter="mock", provider="mock", model="test",
        executor="test", timeout_seconds=30, max_retries=0, temperature=None,
        max_tokens=None, budget_limit=None, paid_cost_approved=False,
        cost_policy="LOCAL_FREE", provider_config_ref=None,
        execution_profile="mock", execution_route="local_model",
        provider_label="mock", api_base_env=None, api_key_env=None, model_env=None,
        model_selection="USER_SELECTED", executor_accepts_model_override=False,
    )


def test_ready_not_authorized_without_authorization_path_is_blocked_by_execute(tmp_path: Path) -> None:
    _setup(tmp_path, allowed_routes=["local_model"], availability_status="READY_NOT_AUTHORIZED")
    request = _request(tmp_path, execution_route="local_model")
    request.config.pop("mission_authorization_path")
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "MISSION_AUTHORIZATION_REQUIRED" in (result.error or "")


@pytest.mark.parametrize("availability", ["NON_EXECUTABLE_CURRENT", "SUSPENDED", "DEPRECATED"])
def test_non_executable_capability_without_authorization_is_blocked_by_execute(tmp_path: Path, availability: str) -> None:
    _setup(tmp_path, allowed_routes=["local_model"], availability_status=availability)
    request = _request(tmp_path, execution_route="local_model")
    request.config.pop("mission_authorization_path")
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert f"CAPABILITY_UNAVAILABLE:B5_I2_SEMANTIC_AUDITOR" in (result.error or "")


def test_ready_not_authorized_with_invalid_authorization_is_blocked_by_execute(tmp_path: Path) -> None:
    _setup(tmp_path, allowed_routes=["local_model"], availability_status="READY_NOT_AUTHORIZED")
    (tmp_path / "mission-authorization.json").write_text("{}", encoding="utf-8")
    result = execute(_request(tmp_path, execution_route="local_model"))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "MISSION_CONTRACT_INVALID" in (result.error or "")


def test_ready_not_authorized_with_exact_fixture_scope_reaches_runtime(tmp_path: Path, monkeypatch) -> None:
    _setup(
        tmp_path,
        allowed_routes=["local_model"],
        availability_status="READY_NOT_AUTHORIZED",
        authorized_profiles=["mock"],
        authorized_mode="mock",
    )
    monkeypatch.setattr("src.ai.execution.AgentRuntimePort.resolve_run_configuration", lambda self, config: _ready_route())
    result = execute(_request(tmp_path, execution_route="local_model"))
    assert result.status is ExecutionStatus.SUCCEEDED, result.error


def test_ready_not_authorized_ignores_alternate_registry_path(tmp_path: Path) -> None:
    _setup(tmp_path, allowed_routes=["local_model"], availability_status="READY_NOT_AUTHORIZED")
    (tmp_path / "alternate_registry.json").write_text(json.dumps({
        "registry_version": "1.0.0", "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "fixture", "compatibility_tokens": {
            "maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {},
        }, "capabilities": [],
    }), encoding="utf-8")
    request = _request(tmp_path, execution_route="local_model")
    request.config.pop("mission_authorization_path")
    request.config["capability_registry_path"] = "alternate_registry.json"
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "MISSION_AUTHORIZATION_REQUIRED" in (result.error or "")


def test_ready_not_authorized_capability_outside_authorization_scope_is_blocked(tmp_path: Path) -> None:
    _setup(tmp_path, allowed_routes=["local_model"], availability_status="READY_NOT_AUTHORIZED")
    request = _request(tmp_path, execution_route="local_model")
    request.capability_id = "OTHER_CAPABILITY"
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "CAPABILITY_UNREGISTERED:B5_I2_SEMANTIC_AUDITOR" not in (result.error or "")
    assert "CAPABILITY_UNREGISTERED:OTHER_CAPABILITY" in (result.error or "")


def test_active_capability_keeps_no_authorization_path_semantics(tmp_path: Path, monkeypatch) -> None:
    _setup(
        tmp_path,
        allowed_routes=["local_model"],
        availability_status="ACTIVE",
        maturity_status="DEMONSTRATED",
    )
    request = _request(tmp_path, execution_route="local_model")
    request.config.pop("mission_authorization_path")
    monkeypatch.setattr("src.ai.execution.AgentRuntimePort.resolve_run_configuration", lambda self, config: _ready_route())
    result = execute(request)
    assert "MISSION_AUTHORIZATION_REQUIRED" not in (result.error or "")
