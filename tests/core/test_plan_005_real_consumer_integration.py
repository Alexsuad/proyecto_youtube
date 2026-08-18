"""Brecha 5 — integración real con el consumidor runtime (execution.execute).

Prueba que la gobernanza PLAN 005 se consume desde el camino real de ejecución,
no solo desde helpers aislados: una autorización de misión real acotada por
routing (allowed_routes) gobierna la ejecución del runtime y bloquea rutas y
perfiles fuera del candidate set autorizado.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionStatus
from src.ai.execution import execute
from src.core.mission_authorization import scope_checksum


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _setup(root: Path, *, allowed_routes: list[str], role_id: str = "SCRIPT_PRODUCT_AUDITOR") -> Path:
    (root / "config").mkdir(exist_ok=True)
    (root / "output").mkdir(exist_ok=True)
    import shutil
    shutil.copy(Path(__file__).resolve().parents[2] / "config/context_resolution_policy.json", root / "config/context_resolution_policy.json")
    (root / "config" / "capability_registry.json").write_text(json.dumps({
        "registry_version": "1.0.0", "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "P5_INTEGRATION", "compatibility_tokens": {
            "maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {},
        },
        "capabilities": [{
            "capability_id": "B5_I2_SEMANTIC_AUDITOR", "domain": "SCRIPT_PRODUCT",
            "functional_authority_domain": "SCRIPT_PRODUCT", "purpose": "Fixture real consumer",
            "functional_requirements": ["REQ-P5"], "implementation_kind": "DETERMINISTIC",
            "maturity_status": "DEFINED",
            "assigned_role": [role_id],
            "prompt_reference": [],
            "execution_profile_refs": [],
            "routing_required": False,
        }],
    }), encoding="utf-8")
    (root / "control.md").write_text("CURRENT_MISSION: P5_INTEGRATION\n", encoding="utf-8")
    state_sha = _sha(root / "control.md")
    scope = {
        "mission_id": "P5_INTEGRATION", "capability_ids": ["B5_I2_SEMANTIC_AUDITOR"],
        "role_ids": [role_id], "execution_profile_ids": ["ANY"],
        "execution_interface": "ANY", "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": ["output/"], "allowed_routes": allowed_routes,
        "execution_mode": "ANY", "live_state_sha256": state_sha,
        "contains_material_repair": False, "repair_integrity_evidence_path": "repair.json",
    }
    decision = root / "authority-decision.json"
    decision.write_text(json.dumps({"mission_id": "P5_INTEGRATION", "decision": "APPROVE", "artifact_version": "1.0.0", "authorized_scope_sha256": scope_checksum(scope)}), encoding="utf-8")
    auth = root / "mission-authorization.json"
    auth.write_text(json.dumps({"mission_id": "P5_INTEGRATION", "authorization": {
        "live_state_path": "control.md", "live_state_sha256": state_sha, "capability_ids": ["B5_I2_SEMANTIC_AUDITOR"],
        "role_ids": [role_id], "execution_profile_ids": ["ANY"], "execution_interface": "ANY",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output/"], "allowed_routes": allowed_routes,
        "execution_mode": "ANY", "single_use": False,
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
        mock_output={"audit_id": "B5I2-SSA-1", "episode_id": "EP-1", "auditor_role": "INDEPENDENT_EDITORIAL_AUDITOR", "auditor_run_id": "RUN-AUDIT", "auditor_skill_id": "skill_auditar_suficiencia_semantica_b5_i2", "auditor_skill_version": "1.0.0", "provider_or_adapter": "mock", "model_or_evaluator": "test", "execution_timestamp": "2026-08-11T00:00:00Z", "input_manifest_checksum": "a" * 64, "artifact_checksums": [], "audit_method": "AI_SEMANTIC_REVIEW", "audited_artifact_ids": [], "audited_artifact_versions": [], "criteria_results": [], "findings": [], "dimension_results": [], "blocking_defects": [], "non_blocking_defects": [], "cited_evidence": [], "required_corrections": [], "unresolved_questions": [], "inherited_restrictions_checked": [], "auditor_statement": "Fixture", "decision": "PASS", "readiness": "BLOCKED", "created_at": "2026-08-11T00:00:00Z"},
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
