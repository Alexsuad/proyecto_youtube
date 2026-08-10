"""Gate for independent, evidence-backed repair integrity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.gate_result import GateResult
from src.core.repair_integrity import resolve_canonical_downstream, validate_repair_integrity
from src.core.status import GateStatus


def run_repair_integrity_gate(
    evidence: dict[str, Any],
    *,
    repo_root: str | Path = ".",
    expected_mission_id: str | None = None,
    expected_contract_sha256: str | None = None,
    known_downstream: dict[str, list[str]] | None = None,
    protected_paths: tuple[str, ...] = (),
    repair_evidence_path: str | None = None,
) -> GateResult:
    downstream_violations: list[str] = []
    if evidence.get("contains_material_repair") is True and known_downstream is None:
        known_downstream, downstream_violations = resolve_canonical_downstream(evidence, repo_root)
    if downstream_violations:
        violations = list(downstream_violations)
    else:
        violations = validate_repair_integrity(
            evidence,
            repo_root,
            expected_mission_id=expected_mission_id,
            expected_contract_sha256=expected_contract_sha256,
            known_downstream=known_downstream,
            protected_paths=protected_paths,
            repair_evidence_path=repair_evidence_path,
        )
    blocked = {"REPAIR_SELF_REVIEW", "REPAIR_REVIEW_INVALIDATED", "REPAIR_REVIEW_PROVENANCE_INCOMPLETE", "REPAIR_GOVERNANCE_CHANGE_REQUIRED", "GOVERNANCE_RESOLUTION_UNRESOLVED", "REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN", "REPAIR_NONCANONICAL_PROVENANCE_REGISTRY", "REPAIR_CANONICAL_PROVENANCE_POLICY_UNRESOLVED", "REPAIR_CANONICAL_PROVENANCE_POLICY_INVALID", "REPAIR_COMPLETION_BLOCKED"}
    status = GateStatus.BLOCKED if blocked.intersection(violations) else GateStatus.FAIL if violations else GateStatus.PASS
    return GateResult(
        gate_id="REPAIR_INTEGRITY_GATE",
        artifact_id=evidence.get("repair_id", "UNKNOWN_REPAIR"),
        artifact_version=evidence.get("schema_version", "UNKNOWN"),
        status=status,
        summary="Repair integrity accepted" if not violations else "Repair integrity rejected",
        violations=violations,
        evidence={
            "evidence_sha256": evidence.get("evidence_sha256"),
            "violation_codes": violations,
            "downstream_resolution": "CANONICAL_PROVENANCE" if known_downstream is not None else "UNKNOWN",
            "reality_verification": "VERIFIED" if not violations else "UNRESOLVED",
        },
    )
