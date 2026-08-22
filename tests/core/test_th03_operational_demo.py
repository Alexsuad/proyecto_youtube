from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from src.ai.contracts import ExecutionRequest, InputArtifact
from src.ai.execution import execute, persist_execution_result
from src.core.invalidation import InvalidationEngine
from src.core.mission_authorization import load_mission_authorization, scope_checksum
from src.core.mission_completion_gate import MissionContract, run_mission_completion_gate
from src.core.repair_integrity import evidence_checksum
from src.scripts.repair_integrity_gate import run_repair_integrity_gate


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


class _OperationalProvider:
    def execute(self, request: ExecutionRequest):
        workspace = Path(request.config["workspace_root"])
        if request.config.get("mutate_protected"):
            (workspace / "origin.md").write_text("tampered by reviewer\n", encoding="utf-8")
        elif request.config.get("mutate_undeclared"):
            (workspace / "authorized-sidecar.md").write_text("tampered outside declared artifacts\n", encoding="utf-8")
        elif request.role == "REPAIR_EXECUTOR":
            (workspace / "origin.md").write_text("repaired origin\n", encoding="utf-8")
        output = {"registry_version": "1.0.0", "entries": []}
        request.output_artifact_path.write_text(json.dumps(output) + "\n", encoding="utf-8")
        return output, {"actual_executor": request.role, "actual_provider": "controlled_fixture", "actual_model": "fixture"}


def _request(root: Path, role: str, output_id: str, inputs: list[InputArtifact], *, mutate_protected: bool = False, mutate_undeclared: bool = False) -> ExecutionRequest:
    return ExecutionRequest(
        capability_id="REPAIR_INTEGRITY",
        skill_id="th03_operational_demo",
        skill_version="1.0.0",
        input_artifacts=inputs,
        output_schema="ai_runtime_config",
        execution_mode="REAL",
        provider="mock",
        output_artifact_kind="execution_smoke_report",
        output_artifact_id=output_id,
        output_artifact_path=root / f"{output_id}.json",
        output_artifact_ref=f"execution_smoke_report:{output_id}",
        episode_id="TH03-FIXTURE",
        role=role,
        config={
            "workspace_root": str(root),
            "repository_root": str(root),
            "mission_authorization_path": "mission-authorization.json",
            "mutate_protected": mutate_protected,
            "mutate_undeclared": mutate_undeclared,
        },
    )


def _artifact(root: Path, ref_id: str, name: str) -> dict:
    path = root / name
    return {
        "ref_id": ref_id,
        "artifact_path": name,
        "artifact_type": "TEXT",
        "artifact_version": "UNDECLARED",
        "artifact_sha256": _sha(path),
        "required": True,
    }


def _evidence_ref(root: Path, ref_id: str, name: str, result: str) -> dict:
    ref = _artifact(root, ref_id, name)
    ref["result"] = result
    return ref


def _evidence(root: Path, registry_path: Path, contract: MissionContract, repair_run_id: str, review_run_id: str) -> dict:
    origin = _artifact(root, "origin_001", "origin.md")
    downstream = _artifact(root, "downstream_001", "downstream.md")
    regression = _evidence_ref(root, "regression", "regression.txt", "PASS")
    review = _evidence_ref(root, "review", "review.txt", "PASS")
    invalidation = _evidence_ref(root, "invalidation", "invalidation.txt", "COMPLETED")
    revalidation = _evidence_ref(root, "revalidation", "revalidation.txt", "PASS")
    evidence = {
        "schema_version": "1.0.0", "repair_id": "TH03-DEMO-REPAIR", "finding_id": "TH03-DEMO-FINDING",
        "mission_id": "TH_03", "mission_contract_sha256": contract.contract_sha256, "contains_material_repair": True,
        "capability_id": "REPAIR_INTEGRITY", "domain": "INFRASTRUCTURE_GOVERNANCE",
        "symptom": "A controlled origin changed.", "root_cause": "The fixture required a real repair flow.",
        "root_cause_class": "L4_EVIDENCE", "origin_artifact": origin,
        "affected_artifacts": ["downstream_001"], "repair_depth": "L4_EVIDENCE",
        "repair_actions": ["Changed origin through the runtime provider."],
        "downstream_impact": {"affected_artifacts": ["downstream_001"], "no_impact_justification": ""},
        "downstream_invalidations": [{"artifact_id": "downstream_001", "status": "COMPLETED", "evidence_ref": invalidation, "justification": "Runtime invalidation recorded."}],
        "downstream_revalidations": [{"artifact_id": "downstream_001", "status": "COMPLETED", "evidence_ref": revalidation, "justification": "Downstream revalidation recorded."}],
        "detector_impact": "NO", "detector_change_required": "NO", "detector_changes": [],
        "sensitive_detector_changes": {"changed": False, "justification": "No detector changed.", "before_behavior": "", "after_behavior": "", "reason_change_is_valid": "", "regression_evidence_ref": []},
        "regression_evidence": {"defect_no_longer_occurs": True, "neighboring_valid_behavior": True, "evidence_refs": [regression]},
        "compensating_changes": [], "governance_change_requested": False, "governance_resolution": None,
        "provenance": {"registry_path": "output/execution_provenance_registry.json", "registry_sha256": _sha(registry_path), "repair_run_id": repair_run_id, "review_run_id": review_run_id},
        "executor_id": "REPAIR_EXECUTOR", "reviewer_id": "INDEPENDENT_REVIEWER", "review_status": "APPROVED",
        "review_evidence": {"reviewer_id": "INDEPENDENT_REVIEWER", "decision": "APPROVED", "evidence_refs": [review], "protected_artifact_refs": [origin, downstream], "reviewer_modified_under_review": False},
        "created_at": "2026-08-10T00:00:00Z",
    }
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    return evidence


def _setup(root: Path) -> tuple[MissionContract, Path, Path, Path]:
    (root / "config").mkdir()
    (root / "output").mkdir()
    (root / "config" / "capability_registry.json").write_text(json.dumps({
        "registry_version": "1.0.0",
        "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "TH03_FIXTURE",
        "compatibility_tokens": {"maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {}},
        "capabilities": [{
            "capability_id": "REPAIR_INTEGRITY",
            "domain": "INFRASTRUCTURE_GOVERNANCE",
            "functional_authority_domain": "INFRASTRUCTURE_GOVERNANCE",
            "purpose": "Controlled repair integrity fixture.",
            "functional_requirements": [],
            "implementation_kind": "DETERMINISTIC",
            "maturity_status": "DEFINED",
            "assigned_role": ["REPAIR_EXECUTOR", "INDEPENDENT_REVIEWER"],
            "routing_required": False,
        }],
    }) + "\n", encoding="utf-8")
    (root / "config" / "execution_provenance_policy.json").write_text(json.dumps({"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"}) + "\n", encoding="utf-8")
    (root / "control.md").write_text("CURRENT_MISSION: TH_03\n", encoding="utf-8")
    (root / "origin.md").write_text("original origin\n", encoding="utf-8")
    (root / "downstream.md").write_text("downstream derived from origin\n", encoding="utf-8")
    (root / "authorized-sidecar.md").write_text("authorized baseline\n", encoding="utf-8")
    for name, content in (("regression.txt", "regression pass\n"), ("review.txt", "independent review\n"), ("invalidation.txt", "invalidated\n"), ("revalidation.txt", "revalidated\n")):
        (root / name).write_text(content, encoding="utf-8")
    state_sha = _sha(root / "control.md")
    scope = {
        "mission_id": "TH_03", "capability_ids": ["REPAIR_INTEGRITY"], "role_ids": ["REPAIR_EXECUTOR", "INDEPENDENT_REVIEWER"],
        "execution_profile_ids": ["ANY"], "execution_interface": "ANY", "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": ["output/", "origin.md", "downstream.md", "authorized-sidecar.md", "repair-output.json", "review-output.json", "review-output-bad.json"], "allowed_routes": ["ANY"], "execution_mode": "ANY", "live_state_sha256": state_sha,
        "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
    }
    decision_path = root / "authority-decision.json"
    decision_path.write_text(json.dumps({"mission_id": "TH_03", "decision": "APPROVE", "artifact_version": "1.0.0", "authorized_scope_sha256": scope_checksum(scope)}) + "\n", encoding="utf-8")
    auth_path = root / "mission-authorization.json"
    auth_path.write_text(json.dumps({"mission_id": "TH_03", "authorization": {
        "live_state_path": "control.md", "live_state_sha256": state_sha, "capability_ids": ["REPAIR_INTEGRITY"],
        "role_ids": ["REPAIR_EXECUTOR", "INDEPENDENT_REVIEWER"], "execution_profile_ids": ["ANY"], "execution_interface": "ANY",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output/", "origin.md", "downstream.md", "authorized-sidecar.md", "repair-output.json", "review-output.json", "review-output-bad.json"], "allowed_routes": ["ANY"], "execution_mode": "ANY", "single_use": False,
        "authority_ref": "authority-decision.json", "authority_sha256": _sha(decision_path), "authorized_scope_sha256": scope_checksum(scope),
        "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY", "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
    }}) + "\n", encoding="utf-8")
    contract_data = {
        "mission_id": "TH_03", "artifact_id": "th03-demo", "artifact_version": "1.0.0",
        "authorized_paths": ["config/", "output/", "control.md", "mission-contract.json", "mission-authorization.json", "authority-decision.json", "origin.md", "downstream.md", "authorized-sidecar.md", "regression.txt", "review.txt", "invalidation.txt", "revalidation.txt", "repair.json", "repair-output.json", "review-output.json", "review-output-bad.json"],
        "protected_untracked_paths": [], "protected_untracked_baseline": [], "required_tests": [{"label": "demo smoke", "command": [sys.executable, "-c", "pass"]}],
        "push_allowed": False, "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
        "mission_authorization_path": "mission-authorization.json", "mission_authorization_sha256": _sha(auth_path),
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "0" * 40},
        "state_requirements": {"control_path": "control.md", "required": {"CURRENT_MISSION": "TH_03"}, "forbidden": {}}, "schema_checks": [],
    }
    contract_path = root / "mission-contract.json"
    contract_path.write_text(json.dumps(contract_data) + "\n", encoding="utf-8")
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "demo@example.test")
    _git(root, "config", "user.name", "TH03 Demo")
    _git(root, "add", "config", "control.md", "mission-authorization.json", "authority-decision.json", "mission-contract.json")
    _git(root, "commit", "-m", "demo baseline", "--quiet")
    contract_data["push_guard"]["baseline_remote_commit"] = _git(root, "rev-parse", "HEAD")
    contract_path.write_text(json.dumps(contract_data) + "\n", encoding="utf-8")
    contract = MissionContract.from_dict(contract_data)
    registry_path = root / "output" / "execution_provenance_registry.json"
    return contract, contract_path, registry_path, root / "origin.md"


def test_th03_operational_flow_and_real_attacks(tmp_path: Path, monkeypatch) -> None:
    contract, contract_path, registry_path, origin_path = _setup(tmp_path)
    def authorized_preflight(request: ExecutionRequest, *, root: Path):
        authorization = load_mission_authorization(root / request.config["mission_authorization_path"])
        authorization.verify(
            root,
            capability_id=request.capability_id,
            role_id=request.role,
            operation="EXECUTE_CAPABILITY",
            execution_mode=request.execution_mode,
        )
        return {"authorization": authorization, "context_manifest": None, "reservation": None}

    monkeypatch.setattr("src.ai.execution.preflight_controlled_execution", authorized_preflight)
    monkeypatch.setattr("src.ai.execution.MockProvider", _OperationalProvider)
    origin_input = InputArtifact("TEXT", "origin_001", origin_path)
    downstream_input = InputArtifact("TEXT", "downstream_001", tmp_path / "downstream.md")

    repair_request = _request(tmp_path, "REPAIR_EXECUTOR", "repair-output", [origin_input])
    repair_result = execute(repair_request)
    persist_execution_result(registry_path, repair_result, repair_request, execution_mode="REAL")
    review_request = _request(tmp_path, "INDEPENDENT_REVIEWER", "review-output", [origin_input, downstream_input])
    review_result = execute(review_request)
    persist_execution_result(registry_path, review_result, review_request, execution_mode="REAL")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    engine = InvalidationEngine(registry)
    invalidation = engine.invalidate_artifact("origin_001", "1.0.0", "Origin repair", "REPAIR_EXECUTOR", dependents=["downstream_001"])
    assert "downstream_001" in invalidation.affected_dependent_artifacts
    registry["dependencies"] = {key: sorted(value) for key, value in engine.dependencies.items()}
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    evidence = _evidence(tmp_path, registry_path, contract, repair_result.run_id, review_result.run_id)
    (tmp_path / "repair.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    completion = run_mission_completion_gate(contract, tmp_path)
    assert completion.status.value == "PASS", completion.to_dict()

    omitted = copy.deepcopy(evidence)
    omitted["downstream_impact"]["affected_artifacts"] = []
    omitted["evidence_sha256"] = evidence_checksum(omitted)
    assert "REPAIR_DOWNSTREAM_DEPENDENCY_OMITTED" in run_repair_integrity_gate(omitted, repo_root=tmp_path).violations

    bad_review_request = _request(tmp_path, "INDEPENDENT_REVIEWER", "review-output-bad", [origin_input, downstream_input], mutate_protected=True)
    bad_review_result = execute(bad_review_request)
    persist_execution_result(registry_path, bad_review_result, bad_review_request, execution_mode="REAL")
    bad_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    evidence_bad = copy.deepcopy(evidence)
    evidence_bad["provenance"]["review_run_id"] = bad_review_result.run_id
    evidence_bad["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence_bad["evidence_sha256"] = evidence_checksum(evidence_bad)
    bad_result = run_repair_integrity_gate(evidence_bad, repo_root=tmp_path)
    assert "REPAIR_REVIEW_INVALIDATED" in bad_result.violations

    sidecar_ref = _artifact(tmp_path, "authorized_sidecar", "authorized-sidecar.md")
    undeclared_review_request = _request(tmp_path, "INDEPENDENT_REVIEWER", "review-output-bad", [origin_input, downstream_input], mutate_undeclared=True)
    undeclared_review_result = execute(undeclared_review_request)
    persist_execution_result(registry_path, undeclared_review_result, undeclared_review_request, execution_mode="REAL")
    evidence_undeclared = copy.deepcopy(evidence)
    evidence_undeclared["provenance"]["review_run_id"] = undeclared_review_result.run_id
    evidence_undeclared["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence_undeclared["review_evidence"]["protected_artifact_refs"].append(sidecar_ref)
    evidence_undeclared["evidence_sha256"] = evidence_checksum(evidence_undeclared)
    undeclared_result = run_repair_integrity_gate(evidence_undeclared, repo_root=tmp_path)
    assert "REPAIR_REVIEW_INVALIDATED" in undeclared_result.violations
