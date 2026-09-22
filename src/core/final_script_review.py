"""Contextual FINAL_SCRIPT_REVIEW sensors for the PLAN013 YouTube handoff."""
from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Mapping
import hashlib
import math
from typing import Any

from src.ai.manifest import canonical_json
from src.core.contract_validation import validate_against_schema
from src.core.editorial_profile_registry import load_active_profile_authority


class FinalScriptReviewError(ValueError):
    """The final review cannot be bound to the exact script artifact."""


DURATION_MEASUREMENT_METHOD = "NARRATED_CONTENT_WHITESPACE_WORD_COUNT_DIVIDED_BY_NARRATIVE_PLAN_WPM"


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return None
    numeric = float(value)
    return numeric if numeric > 0 else None


def _valid_checksum(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) != 64:
        return None
    if any(character not in "0123456789abcdefABCDEF" for character in value):
        return None
    return value


def _duration_target(narrative_plan: Mapping[str, Any]) -> float | None:
    return _positive_number(narrative_plan.get("duration_target_minutes"))


def _target_range(duration_target_minutes: float | None) -> list[float] | None:
    if duration_target_minutes is None:
        return None
    return [max(1.0, duration_target_minutes - 2.0), duration_target_minutes + 2.0]


def _unresolved_duration_telemetry(duration_target_minutes: float | None) -> dict[str, Any]:
    return {
        "status": "UNRESOLVED",
        "estimated_minutes": None,
        "duration_target_minutes": duration_target_minutes,
        "target_range": _target_range(duration_target_minutes),
        "normative": False,
        "measurement_method": None,
        "word_count": None,
        "wpm_applied": None,
        "measured_script_checksum": None,
    }


def measure_duration_telemetry(
    edited_script: Mapping[str, Any],
    narrative_plan: Mapping[str, Any],
    *,
    script_draft: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure only explicitly identified narrated text with the episode plan WPM."""
    duration_target_minutes = _duration_target(narrative_plan)
    unresolved = _unresolved_duration_telemetry(duration_target_minutes)
    if not isinstance(edited_script, Mapping) or not isinstance(narrative_plan, Mapping):
        return unresolved

    episode_id = edited_script.get("episode_id")
    if not episode_id or narrative_plan.get("episode_id") != episode_id:
        return unresolved
    if not isinstance(script_draft, Mapping):
        return unresolved
    if (
        script_draft.get("episode_id") != episode_id
        or script_draft.get("narrative_plan_ref") != narrative_plan.get("script_plan_id")
        or edited_script.get("source_script_version") != script_draft.get("artifact_version")
    ):
        return unresolved

    narrated_content = edited_script.get("narrated_content")
    if not isinstance(narrated_content, str) or not narrated_content.strip():
        return unresolved
    wpm_target = narrative_plan.get("wpm_target")
    if isinstance(wpm_target, bool) or not isinstance(wpm_target, int) or wpm_target <= 0:
        return unresolved
    script_checksum = _valid_checksum(edited_script.get("checksum"))
    if script_checksum is None:
        return unresolved
    expected_checksum = hashlib.sha256(
        canonical_json({key: value for key, value in edited_script.items() if key != "checksum"})
    ).hexdigest()
    if script_checksum != expected_checksum:
        return unresolved

    word_count = len(narrated_content.split())
    if word_count <= 0:
        return unresolved
    return {
        "status": "MEASURED",
        "estimated_minutes": word_count / wpm_target,
        "duration_target_minutes": duration_target_minutes,
        "target_range": _target_range(duration_target_minutes),
        "normative": False,
        "measurement_method": DURATION_MEASUREMENT_METHOD,
        "word_count": word_count,
        "wpm_applied": wpm_target,
        "measured_script_checksum": script_checksum,
    }


def _normalise_duration_telemetry(
    duration_telemetry: Mapping[str, Any] | None,
    script_checksum: str,
) -> dict[str, Any]:
    source = dict(duration_telemetry) if isinstance(duration_telemetry, Mapping) else {}
    duration_target_minutes = _positive_number(source.get("duration_target_minutes"))
    unresolved = _unresolved_duration_telemetry(duration_target_minutes)
    if source.get("status") != "MEASURED":
        return unresolved
    if source.get("normative") is not False:
        return unresolved
    if source.get("measurement_method") != DURATION_MEASUREMENT_METHOD:
        return unresolved
    word_count = source.get("word_count")
    wpm_applied = _positive_number(source.get("wpm_applied"))
    estimated_minutes = _positive_number(source.get("estimated_minutes"))
    measured_script_checksum = _valid_checksum(source.get("measured_script_checksum"))
    if (
        isinstance(word_count, bool)
        or not isinstance(word_count, int)
        or word_count <= 0
        or wpm_applied is None
        or estimated_minutes is None
        or measured_script_checksum is None
        or measured_script_checksum != script_checksum
    ):
        return unresolved
    expected_range = _target_range(duration_target_minutes)
    if source.get("target_range") != expected_range:
        return unresolved
    if not math.isclose(estimated_minutes, word_count / wpm_applied, rel_tol=1e-9, abs_tol=1e-9):
        return unresolved
    return {
        "status": "MEASURED",
        "estimated_minutes": estimated_minutes,
        "duration_target_minutes": duration_target_minutes,
        "target_range": expected_range,
        "normative": False,
        "measurement_method": DURATION_MEASUREMENT_METHOD,
        "word_count": word_count,
        "wpm_applied": wpm_applied,
        "measured_script_checksum": measured_script_checksum,
    }


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
    duration_telemetry: Mapping[str, Any] | None = None,
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
    duration = _normalise_duration_telemetry(duration_telemetry, script_checksum)
    duration_status = duration["status"]
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
        "duration_telemetry": duration,
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
