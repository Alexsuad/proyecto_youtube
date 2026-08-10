import copy
import hashlib
import json
from pathlib import Path

from src.core.repair_integrity import evidence_checksum, validate_repair_integrity
from src.core.mission_authorization import scope_checksum
from src.scripts.repair_integrity_gate import run_repair_integrity_gate
from tests.core.test_all_schemas import VALID_FIXTURES


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ref(root: Path, name: str, content: str, result: str = "PASS") -> dict:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return {
        "ref_id": name,
        "artifact_path": name,
        "artifact_type": "TEXT",
        "artifact_version": "UNDECLARED",
        "artifact_sha256": _sha(path),
        "result": result,
        "required": True,
    }


def _registry(root: Path) -> tuple[str, str]:
    (root / "config").mkdir(exist_ok=True)
    (root / "output").mkdir(exist_ok=True)
    (root / "config" / "execution_provenance_policy.json").write_text(
        json.dumps({"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"}) + "\n",
        encoding="utf-8",
    )
    registry = copy.deepcopy(VALID_FIXTURES["execution_provenance_registry"])
    base = registry["runs"][0]
    repair = copy.deepcopy(base)
    review = copy.deepcopy(base)
    repair["run_id"] = "RUN-REPAIR"
    repair["actual_executor"] = "id_executor"
    repair["agent_id"] = "id_executor"
    review["run_id"] = "RUN-REVIEW"
    review["actual_executor"] = "id_reviewer"
    review["agent_id"] = "id_reviewer"
    review_output = root / "review-output.json"
    review_output.write_text("{\"review\": true}\n", encoding="utf-8")
    review["outputs"] = [{
        "artifact_kind": "semantic_audit", "artifact_id": "review-output",
        "artifact_ref": "review-output", "artifact_path": "review-output.json", "checksum": _sha(review_output),
    }]
    review["output_artifact_ids"] = ["review-output"]
    review["output_checksums"] = [_sha(review_output)]
    review["modified_artifact_ids"] = []
    review["modified_artifact_paths"] = []
    repair["modification_manifest_source"] = "RUNTIME_PRE_POST_DIFF"
    review["modification_manifest_source"] = "RUNTIME_PRE_POST_DIFF"
    registry["runs"] = [repair, review]
    registry["dependencies"] = {"origin_001": ["artifact_002"]}
    path = root / "output" / "execution_provenance_registry.json"
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "output/execution_provenance_registry.json", _sha(path)


def valid_evidence(root: Path) -> dict:
    registry_path, registry_sha = _registry(root)
    origin_path = root / "origin.md"
    origin_path.write_text("Root cause source.\n", encoding="utf-8")
    origin = {
        "ref_id": "origin_001", "artifact_path": "origin.md", "artifact_type": "TEXT",
        "artifact_version": "UNDECLARED", "artifact_sha256": _sha(origin_path), "required": True,
    }
    evidence = {
        "schema_version": "1.0.0", "repair_id": "repair_001", "finding_id": "finding_001",
        "mission_id": "TH_03", "mission_contract_sha256": "a" * 64, "contains_material_repair": True,
        "capability_id": "REPAIR_INTEGRITY", "domain": "INFRASTRUCTURE_GOVERNANCE",
        "symptom": "Detector accepted an invalid repair.", "root_cause": "Missing independent repair evidence.",
        "root_cause_class": "L4_EVIDENCE", "origin_artifact": origin,
        "affected_artifacts": ["artifact_002"], "repair_depth": "L4_EVIDENCE",
        "repair_actions": ["Added schema-backed evidence and independent review."],
        "downstream_impact": {"affected_artifacts": ["artifact_002"], "no_impact_justification": ""},
        "downstream_invalidations": [], "downstream_revalidations": [],
        "detector_impact": "NO", "detector_change_required": "NO", "detector_changes": [],
        "sensitive_detector_changes": {"changed": False, "justification": "No detector changed.", "before_behavior": "", "after_behavior": "", "reason_change_is_valid": "", "regression_evidence_ref": []},
        "regression_evidence": {"defect_no_longer_occurs": True, "neighboring_valid_behavior": True, "evidence_refs": [_ref(root, "regression.txt", "defect absent; neighboring behavior preserved\n")]},
        "compensating_changes": [], "governance_change_requested": False, "governance_resolution": None,
        "provenance": {"registry_path": registry_path, "registry_sha256": registry_sha, "repair_run_id": "RUN-REPAIR", "review_run_id": "RUN-REVIEW"},
        "executor_id": "id_executor", "reviewer_id": "id_reviewer",
        "review_status": "APPROVED", "review_evidence": {"reviewer_id": "id_reviewer", "decision": "APPROVED", "evidence_refs": [_ref(root, "review.txt", "independent review approved\n")], "protected_artifact_refs": [origin], "reviewer_modified_under_review": False},
        "created_at": "2026-08-09T00:00:00Z",
    }
    evidence["downstream_invalidations"] = [{"artifact_id": "artifact_002", "status": "COMPLETED", "evidence_ref": _ref(root, "invalidation.txt", "invalidated\n", "COMPLETED"), "justification": "Dependency invalidated."}]
    evidence["downstream_revalidations"] = [{"artifact_id": "artifact_002", "status": "COMPLETED", "evidence_ref": _ref(root, "revalidation.txt", "revalidated\n", "PASS"), "justification": "Dependency revalidated."}]
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    return evidence


def _write_l5_capability_registry(root: Path) -> Path:
    registry_path = root / "config" / "capability_registry.json"
    registry_path.parent.mkdir(exist_ok=True)
    registry_path.write_text(json.dumps({
        "registry_version": "1.0.0",
        "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "fixture",
        "compatibility_tokens": {
            "maturity": {"DEFINED": "DEFINED"},
            "availability": {"NON_EXECUTABLE": "NON_EXECUTABLE_CURRENT"},
            "assurance": {"NOT_TESTED": "NOT_TESTED"},
            "approval": {"PENDING": "PENDING"},
            "evidence": {"NOT_TESTED": "NOT_TESTED"},
        },
        "capabilities": [
            {
                "capability_id": "REPAIR_INTEGRITY",
                "domain": "INFRASTRUCTURE_GOVERNANCE",
                "functional_authority_domain": "INFRASTRUCTURE_GOVERNANCE",
                "purpose": "Fixture para gobernanza L5.",
                "functional_requirements": [],
                "implementation_kind": "DEFERRED",
                "maturity_status": "DEFINED",
                "decision_authority": "AUTHORITY_A",
            },
            {
                "capability_id": "OTHER_CAPABILITY",
                "domain": "SCRIPT_PRODUCT",
                "functional_authority_domain": "SCRIPT_PRODUCT",
                "purpose": "Fixture de autoridad ajena.",
                "functional_requirements": [],
                "implementation_kind": "DEFERRED",
                "maturity_status": "DEFINED",
                "decision_authority": "AUTHORITY_B",
            },
        ],
    }) + "\n", encoding="utf-8")
    return registry_path


def test_valid_repair_passes_and_gate_is_green(tmp_path):
    evidence = valid_evidence(tmp_path)
    assert validate_repair_integrity(evidence, tmp_path) == []
    assert run_repair_integrity_gate(evidence, repo_root=tmp_path, known_downstream={"origin_001": ["artifact_002"]}).status.value == "PASS"


def test_repair_cannot_be_shallower_than_root_cause(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["repair_depth"] = "L2_STRUCTURE"
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_TOO_SHALLOW" in validate_repair_integrity(evidence, tmp_path)


def test_policy_change_requires_governance_review(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["root_cause_class"] = "L5_REQUIREMENT_OR_POLICY"
    evidence["repair_depth"] = "L5_REQUIREMENT_OR_POLICY"
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    result = run_repair_integrity_gate(evidence, repo_root=tmp_path, known_downstream={"origin_001": ["artifact_002"]})
    assert "REPAIR_GOVERNANCE_CHANGE_REQUIRED" in result.violations
    assert result.status.value == "BLOCKED"


def test_policy_change_can_resume_with_verified_authority_resolution(tmp_path):
    evidence = valid_evidence(tmp_path)
    capability_registry_path = _write_l5_capability_registry(tmp_path)
    state = tmp_path / "state.md"
    state.write_text("CURRENT_MISSION: TH_03\n", encoding="utf-8")
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps({
        "authority_type": "GOVERNANCE_APPROVAL", "decision": "APPROVE",
        "authority_identity": "AUTHORITY_A", "functional_authority_domain": "INFRASTRUCTURE_GOVERNANCE",
        "artifact_version": "UNDECLARED", "mission_id": "TH_03", "requirement_ref": "REQ-TH03",
        "approved_artifact_ref": evidence["origin_artifact"],
    }) + "\n", encoding="utf-8")
    approval = {
        "ref_id": "governance_approval", "artifact_path": "approval.json", "artifact_type": "GOVERNANCE_APPROVAL",
        "artifact_version": "UNDECLARED", "artifact_sha256": _sha(approval_path), "required": True,
    }
    scope = {
        "mission_id": "TH_03", "capability_ids": ["REPAIR_INTEGRITY"],
        "role_ids": ["INDEPENDENT_EDITORIAL_AUDITOR"], "execution_profile_ids": ["mock_audit"],
        "execution_interface": "ANY", "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
        "allowed_routes": ["native:mock"], "execution_mode": "SYNTHETIC", "live_state_sha256": _sha(state),
        "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
    }
    decision_path = tmp_path / "mission-decision.json"
    decision = {
        "authority_type": "MISSION_AUTHORIZATION", "decision": "APPROVE", "artifact_version": "UNDECLARED",
        "mission_id": "TH_03", "requirement_ref": "REQ-TH03", "authorized_scope_sha256": scope_checksum(scope),
    }
    decision_path.write_text(json.dumps(decision) + "\n", encoding="utf-8")
    contract = {
        "mission_id": "TH_03", "authorization": {
            "live_state_path": "state.md", "live_state_sha256": _sha(state),
            "capability_ids": ["REPAIR_INTEGRITY"], "role_ids": ["INDEPENDENT_EDITORIAL_AUDITOR"],
            "execution_profile_ids": ["mock_audit"], "execution_interface": "ANY",
            "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
            "allowed_routes": ["native:mock"], "execution_mode": "SYNTHETIC", "single_use": False,
            "authority_ref": "mission-decision.json", "authority_sha256": _sha(decision_path),
            "authorized_scope_sha256": scope_checksum(scope), "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
            "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
        },
    }
    authority_path = tmp_path / "mission-authority.json"
    authority_path.write_text(json.dumps(contract) + "\n", encoding="utf-8")
    evidence["root_cause_class"] = "L5_REQUIREMENT_OR_POLICY"
    evidence["repair_depth"] = "L5_REQUIREMENT_OR_POLICY"
    evidence["governance_change_requested"] = True
    evidence["governance_resolution"] = {
        "approval_ref": approval,
        "approved_artifact_ref": evidence["origin_artifact"],
        "approved_version": approval["artifact_version"],
        "approved_artifact_sha256": evidence["origin_artifact"]["artifact_sha256"],
        "approval_sha256": approval["artifact_sha256"],
        "authority_ref": "mission-authority.json", "authority_sha256": _sha(authority_path),
        "decision": "APPROVE",
        "resolved_at": "2026-08-08T00:00:00Z", "requirement_ref": "REQ-TH03",
    }
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert validate_repair_integrity(evidence, tmp_path) == []

    arbitrary_authority = copy.deepcopy(evidence)
    approval_data = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_data["authority_identity"] = "SOME_ARBITRARY_AUTHORITY"
    approval_path.write_text(json.dumps(approval_data) + "\n", encoding="utf-8")
    arbitrary_authority["governance_resolution"]["approval_ref"]["artifact_sha256"] = _sha(approval_path)
    arbitrary_authority["governance_resolution"]["approval_sha256"] = _sha(approval_path)
    arbitrary_authority["evidence_sha256"] = evidence_checksum(arbitrary_authority)
    assert "GOVERNANCE_RESOLUTION_UNRESOLVED" in validate_repair_integrity(arbitrary_authority, tmp_path)

    approval_data["authority_identity"] = "AUTHORITY_B"
    approval_path.write_text(json.dumps(approval_data) + "\n", encoding="utf-8")
    other_capability_authority = copy.deepcopy(evidence)
    other_capability_authority["governance_resolution"]["approval_ref"]["artifact_sha256"] = _sha(approval_path)
    other_capability_authority["governance_resolution"]["approval_sha256"] = _sha(approval_path)
    other_capability_authority["evidence_sha256"] = evidence_checksum(other_capability_authority)
    assert "GOVERNANCE_RESOLUTION_UNRESOLVED" in validate_repair_integrity(other_capability_authority, tmp_path)

    without_governance = copy.deepcopy(evidence)
    without_governance["governance_resolution"] = None
    without_governance["evidence_sha256"] = evidence_checksum(without_governance)
    blocked = validate_repair_integrity(without_governance, tmp_path)
    assert "REPAIR_GOVERNANCE_CHANGE_REQUIRED" in blocked
    assert "GOVERNANCE_RESOLUTION_UNRESOLVED" in blocked

    swapped = copy.deepcopy(evidence)
    swapped_ref = dict(swapped["governance_resolution"]["approved_artifact_ref"])
    swapped_ref["artifact_path"] = "state.md"
    swapped_ref["artifact_sha256"] = _sha(state)
    swapped["governance_resolution"]["approved_artifact_ref"] = swapped_ref
    swapped["governance_resolution"]["approved_artifact_sha256"] = swapped_ref["artifact_sha256"]
    swapped["evidence_sha256"] = evidence_checksum(swapped)
    assert "GOVERNANCE_RESOLUTION_UNRESOLVED" in validate_repair_integrity(swapped, tmp_path)

    checksum_mismatch = copy.deepcopy(evidence)
    checksum_mismatch["governance_resolution"]["approved_artifact_sha256"] = "b" * 64
    checksum_mismatch["evidence_sha256"] = evidence_checksum(checksum_mismatch)
    assert "GOVERNANCE_RESOLUTION_UNRESOLVED" in validate_repair_integrity(checksum_mismatch, tmp_path)

    unresolved_capability = copy.deepcopy(evidence)
    capability_registry_path.unlink()
    unresolved_capability["evidence_sha256"] = evidence_checksum(unresolved_capability)
    assert "GOVERNANCE_CAPABILITY_UNRESOLVED" in validate_repair_integrity(unresolved_capability, tmp_path)


def test_unhandled_downstream_is_rejected(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["downstream_revalidations"] = []
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_DOWNSTREAM_NOT_REVALIDATED" in validate_repair_integrity(evidence, tmp_path)


def test_not_required_does_not_satisfy_downstream_obligation(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["downstream_invalidations"][0]["status"] = "NOT_REQUIRED"
    evidence["downstream_invalidations"][0]["justification"] = "No canonical impact proof."
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_DOWNSTREAM_NOT_INVALIDATED" in validate_repair_integrity(evidence, tmp_path)


def test_detector_change_requires_regression(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["detector_impact"] = "YES"
    evidence["detector_change_required"] = "YES"
    evidence["detector_changes"] = [{"path": "src/core/detector.py", "change": "Changed classification rule."}]
    evidence["regression_evidence"]["neighboring_valid_behavior"] = False
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_REGRESSION_MISSING" in validate_repair_integrity(evidence, tmp_path)


def test_fake_provenance_origin_and_evidence_are_rejected(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["origin_artifact"]["artifact_path"] = "does/not/exist.md"
    evidence["review_evidence"]["evidence_refs"][0]["artifact_path"] = "fake_review.txt"
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    violations = validate_repair_integrity(evidence, tmp_path)
    assert "REPAIR_ORIGIN_ARTIFACT_UNRESOLVED" in violations
    assert "REPAIR_EVIDENCE_UNRESOLVED" in violations


def test_self_review_and_same_run_are_blocked(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["reviewer_id"] = evidence["executor_id"]
    evidence["provenance"]["review_run_id"] = evidence["provenance"]["repair_run_id"]
    evidence["review_evidence"]["reviewer_id"] = evidence["executor_id"]
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    violations = validate_repair_integrity(evidence, tmp_path)
    assert "REPAIR_PROVENANCE_UNRESOLVED" in violations or "REPAIR_SELF_REVIEW" in violations


def test_compensating_patch_requires_evidence_and_review(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["compensating_changes"] = [{
        "change": "Added a fallback exception.", "justification": "Temporary containment.",
        "root_cause_relationship": "Contains the affected path while the root fix is deployed.",
        "evidence_refs": [], "regression_refs": [], "review_result": "PENDING",
    }]
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    violations = validate_repair_integrity(evidence, tmp_path)
    assert violations
    assert "REPAIR_COMPENSATING_PATCH_UNJUSTIFIED" in violations


def test_known_downstream_dependency_cannot_be_omitted(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["downstream_impact"]["affected_artifacts"] = ["artifact_002"]
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    violations = validate_repair_integrity(evidence, tmp_path, known_downstream={"origin_001": ["artifact_003"]})
    assert "REPAIR_DOWNSTREAM_DEPENDENCY_OMITTED" in violations


def test_canonical_downstream_resolution_includes_transitive_dependents(tmp_path):
    evidence = valid_evidence(tmp_path)
    registry_path = tmp_path / evidence["provenance"]["registry_path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["dependencies"]["artifact_002"] = ["artifact_003"]
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    result = run_repair_integrity_gate(evidence, repo_root=tmp_path)
    assert "REPAIR_DOWNSTREAM_DEPENDENCY_OMITTED" in result.violations


def test_gate_blocks_unknown_downstream_knowledge(tmp_path):
    evidence = valid_evidence(tmp_path)
    registry_path = tmp_path / evidence["provenance"]["registry_path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry.pop("dependencies", None)
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    result = run_repair_integrity_gate(evidence, repo_root=tmp_path)
    assert result.status.value == "BLOCKED"
    assert "REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN" in result.violations


def test_repair_evidence_cannot_select_fake_provenance_registry(tmp_path):
    evidence = valid_evidence(tmp_path)
    canonical = tmp_path / evidence["provenance"]["registry_path"]
    fake = tmp_path / "fake_provenance_registry.json"
    fake.write_text(json.dumps({"registry_version": "1.0.0", "runs": json.loads(canonical.read_text(encoding="utf-8"))["runs"], "dependencies": {}}) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_path"] = "fake_provenance_registry.json"
    evidence["provenance"]["registry_sha256"] = _sha(fake)
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    result = run_repair_integrity_gate(evidence, repo_root=tmp_path)
    assert result.status.value == "BLOCKED"
    assert "REPAIR_NONCANONICAL_PROVENANCE_REGISTRY" in result.violations


def test_reviewer_output_mutation_is_derived_from_provenance(tmp_path):
    evidence = valid_evidence(tmp_path)
    registry_path = tmp_path / evidence["provenance"]["registry_path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][1]["output_artifact_ids"] = ["origin_001"]
    registry["runs"][1]["modified_artifact_ids"] = ["origin_001"]
    registry["runs"][1]["modified_artifact_paths"] = ["origin.md"]
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_REVIEW_INVALIDATED" in validate_repair_integrity(evidence, tmp_path)


def test_reviewer_without_modification_manifest_cannot_close(tmp_path):
    evidence = valid_evidence(tmp_path)
    registry_path = tmp_path / evidence["provenance"]["registry_path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][1].pop("modified_artifact_ids")
    registry["runs"][1].pop("modified_artifact_paths")
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_REVIEW_PROVENANCE_INCOMPLETE" in validate_repair_integrity(evidence, tmp_path)


def test_capability_must_match_repair_run_when_provenance_registers_it(tmp_path):
    evidence = valid_evidence(tmp_path)
    registry_path = tmp_path / evidence["provenance"]["registry_path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][0]["capability_id"] = "OTHER_CAPABILITY"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = _sha(registry_path)
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_CAPABILITY_PROVENANCE_MISMATCH" in validate_repair_integrity(evidence, tmp_path)


def test_artifact_version_must_match_declared_canonical_version(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["origin_artifact"]["artifact_version"] = "9.9.9"
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert "REPAIR_ARTIFACT_VERSION_MISMATCH" in validate_repair_integrity(evidence, tmp_path)


def test_sensitive_detector_regression_ref_requires_resolvable_structured_reference(tmp_path):
    evidence = valid_evidence(tmp_path)
    evidence["detector_impact"] = "YES"
    evidence["detector_change_required"] = "YES"
    evidence["detector_changes"] = [{"path": "src/core/detector.py", "change": "Changed classification rule."}]
    evidence["sensitive_detector_changes"]["changed"] = True
    evidence["sensitive_detector_changes"]["regression_evidence_ref"] = [_ref(tmp_path, "sensitive.txt", "sensitive detector regression\n")]
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert validate_repair_integrity(evidence, tmp_path) == []

    evidence["sensitive_detector_changes"]["regression_evidence_ref"] = ["fake-ref"]
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    assert any("regression_evidence_ref" in item for item in validate_repair_integrity(evidence, tmp_path))


def test_l5_authority_must_be_recognized_structured_authority(tmp_path):
    evidence = valid_evidence(tmp_path)
    authority_path = tmp_path / "authority.md"
    authority_path.write_text("APPROVE\n", encoding="utf-8")
    approval = dict(evidence["origin_artifact"])
    approval["ref_id"] = "governance_approval"
    evidence["root_cause_class"] = "L5_REQUIREMENT_OR_POLICY"
    evidence["repair_depth"] = "L5_REQUIREMENT_OR_POLICY"
    evidence["governance_change_requested"] = True
    evidence["governance_resolution"] = {
        "approval_ref": approval, "approved_artifact_ref": evidence["origin_artifact"], "approved_version": "UNDECLARED",
        "approved_artifact_sha256": evidence["origin_artifact"]["artifact_sha256"],
        "approval_sha256": approval["artifact_sha256"], "authority_ref": "authority.md", "authority_sha256": _sha(authority_path),
        "decision": "APPROVE", "resolved_at": "2026-08-08T00:00:00Z", "requirement_ref": "REQ-TH03",
    }
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    violations = validate_repair_integrity(evidence, tmp_path)
    assert "GOVERNANCE_CAPABILITY_UNRESOLVED" in violations or "GOVERNANCE_RESOLUTION_UNRESOLVED" in violations


def test_th02_regression_fixture_is_real_guard_coverage():
    from src.scripts.runtime_contamination_guard import scan
    import json

    identifier = "TEAM_" + "02_B5_I2_FUNCTIONAL_SPECIFICATION"
    assert identifier == "TEAM_02_B5_I2_FUNCTIONAL_SPECIFICATION"
    policy = json.loads(Path("config/runtime_contamination_policy.json").read_text(encoding="utf-8"))
    assert any("TEAM" in item["pattern"] for item in policy["patterns"])
    assert scan(Path("."), Path("config/runtime_contamination_policy.json"))["exit_code"] == 0
