"""Proportional review workload using canonical review levels only."""
from __future__ import annotations

from typing import Any

from src.core.contract_validation import validate_against_schema


LEVELS = {"SELF_ONLY", "INDEPENDENT_REVIEW", "OWNER_REVIEW"}
RANK = {"SELF_ONLY": 0, "INDEPENDENT_REVIEW": 1, "OWNER_REVIEW": 2}


def choose_review_workload(policy: dict[str, Any] | None = None, *, risk: str = "LOW", sensitive: bool = False, findings: bool = False, external_required: bool = False, owner_required: bool = False, evidence_refs: list[str] | None = None, required_review: str | None = None) -> dict[str, Any]:
    """Choose a proportional review workload.

    ``required_review`` is the canonical floor derived from the convergence
    authority (``mission_convergence.required_review_stage``). When provided,
    the selected level can never downgrade below it; this is the single point
    where the workload decision is reconciled with the mission authority.
    """
    policy = policy or {}
    reasons: list[str] = []
    if owner_required or bool(policy.get("owner_review")):
        level, origin = "OWNER_REVIEW", "EXTERNAL"
        reasons.append("OWNER_AUTHORITY_REQUIRED")
    elif external_required or str(policy.get("review_origin", "")).upper() == "EXTERNAL":
        level, origin = "INDEPENDENT_REVIEW", "EXTERNAL"
        reasons.append("EXTERNAL_INDEPENDENCE_REQUIRED")
    elif sensitive or findings or str(risk).upper() in {"HIGH", "CRITICAL"} or str(policy.get("required_review", "")).upper() == "INDEPENDENT_REVIEW":
        level, origin = "INDEPENDENT_REVIEW", "INTERNAL"
        reasons.append("INTERNAL_INDEPENDENCE_PROPORTIONAL_TO_RISK")
    else:
        level, origin = "SELF_ONLY", "NOT_APPLICABLE"
        reasons.append("LOW_RISK_SELF_REVIEW_SUFFICIENT")
    if required_review:
        if str(required_review).upper() not in LEVELS:
            raise ValueError("REVIEW_LEVEL_INVALID")
        floor = str(required_review).upper()
        if RANK[floor] > RANK[level]:
            level = floor
            reasons.append("ELEVATED_TO_MISSION_REVIEW_FLOOR")
        reasons.append("RECONCILED_WITH_MISSION_REVIEW_AUTHORITY")
    decision = {"review_level": level, "review_origin": origin, "reasons": reasons, "evidence_refs": list(evidence_refs or [])}
    violations = validate_against_schema(decision, "review_workload_decision")
    if violations:
        raise ValueError("REVIEW_WORKLOAD_DECISION_INVALID: " + "; ".join(violations))
    return decision


def assert_no_review_downgrade(original: str, proposed: str) -> None:
    original_level, proposed_level = str(original).upper(), str(proposed).upper()
    if original_level not in LEVELS or proposed_level not in LEVELS:
        raise ValueError("REVIEW_LEVEL_INVALID")
    if RANK[proposed_level] < RANK[original_level]:
        raise PermissionError("REVIEW_POLICY_DOWNGRADE_FORBIDDEN")
