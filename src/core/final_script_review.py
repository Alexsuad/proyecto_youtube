"""Contextual FINAL_SCRIPT_REVIEW sensors for the PLAN013 YouTube handoff."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.editorial_profile_registry import load_active_profile_authority


class FinalScriptReviewError(ValueError):
    """The final review cannot be bound to the exact script artifact."""


def build_final_script_review(
    *,
    review_id: str,
    episode_id: str,
    artifact_id: str,
    script_version: str,
    script_checksum: str,
    profile_reference: dict[str, str],
    visible_promise_ref: str,
    final_audit_ref: str,
    final_audit_checksum: str,
    review_run_id: str,
    producer_run_id: str,
    editor_run_id: str,
    auditor_run_id: str,
    review_actor_id: str,
    producer_actor_id: str,
    editor_actor_id: str,
    auditor_actor_id: str,
    evidence_refs: list[str] | None = None,
    lexical_findings: list[str] | None = None,
    estimated_minutes: float | None = None,
    target_range: tuple[float, float] | None = None,
    authenticity: str = "PASS",
    reuse_context: str = "PASS",
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a review envelope without turning sensors into universal gates."""
    if not all((review_id, episode_id, artifact_id, script_version, script_checksum, visible_promise_ref, final_audit_ref, final_audit_checksum, review_run_id, producer_run_id, editor_run_id, auditor_run_id, review_actor_id, producer_actor_id, editor_actor_id, auditor_actor_id)) or not isinstance(profile_reference, dict):
        raise FinalScriptReviewError("exact script identity and final audit reference are required")
    active = load_active_profile_authority()
    expected_profile = {
        "profile_id": active["ACTIVE_PROFILE_ID"],
        "profile_version": active["ACTIVE_PROFILE_VERSION"],
        "profile_checksum": active["profile_checksum"],
    }
    if profile_reference != expected_profile:
        raise FinalScriptReviewError("active editorial profile identity is stale or inconsistent")
    run_ids = {producer_run_id, editor_run_id, auditor_run_id, review_run_id}
    if len(run_ids) != 4:
        raise FinalScriptReviewError("FINAL_SCRIPT_REVIEW runs must be independent")
    actor_ids = {producer_actor_id, editor_actor_id, auditor_actor_id}
    if review_actor_id in actor_ids:
        raise FinalScriptReviewError("FINAL_SCRIPT_REVIEW actor is incompatible with an editorial authority")
    findings = list(lexical_findings or [])
    duration_status = "MEASURED" if estimated_minutes is not None and target_range else "UNRESOLVED"
    basis: list[str] = []
    if findings:
        basis.append("LEXICAL_SENSOR_REQUIRES_CONTEXTUAL_REVIEW")
    if duration_status == "UNRESOLVED":
        basis.append("DURATION_TELEMETRY_UNRESOLVED")
    if authenticity != "PASS":
        basis.append("AUTHENTICITY_REQUIRES_REVIEW")
    if reuse_context != "PASS":
        basis.append("REUSE_CONTEXT_REQUIRES_REVIEW")
    decision = "WARN" if basis else "PASS"
    review = {
        "review_id": review_id,
        "episode_id": episode_id,
        "artifact_id": artifact_id,
        "script_version": script_version,
        "script_checksum": script_checksum,
        "profile_reference": profile_reference,
        "visible_promise_ref": visible_promise_ref,
        "final_audit_ref": final_audit_ref,
        "final_audit_checksum": final_audit_checksum,
        "review_run_id": review_run_id,
        "producer_run_id": producer_run_id,
        "editor_run_id": editor_run_id,
        "auditor_run_id": auditor_run_id,
        "review_actor_id": review_actor_id,
        "producer_actor_id": producer_actor_id,
        "editor_actor_id": editor_actor_id,
        "auditor_actor_id": auditor_actor_id,
        "evidence_refs": list(evidence_refs or []),
        "lexical_sensor": {"status": "WARN" if findings else "PASS", "findings": findings, "normative": False},
        "duration_telemetry": {
            "status": duration_status,
            "estimated_minutes": estimated_minutes,
            "target_range": list(target_range) if target_range else None,
            "normative": False,
        },
        "authenticity": authenticity,
        "reuse_context": reuse_context,
        "decision": decision,
        "decision_basis": basis,
        "created_at": created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    violations = validate_against_schema(review, "final_script_review")
    if violations:
        raise FinalScriptReviewError("final_script_review invalid: " + "; ".join(violations))
    return review
