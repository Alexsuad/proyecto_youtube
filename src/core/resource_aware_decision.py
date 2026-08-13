"""T4 — Resource-aware orchestration decision for PLAN 006.

Composes existing provider-neutral capabilities (delegation policy, routing
policy, review workload, mission authorization, T2-B verification plan,
T2-A evidence reuse, T2-D product impact) into a single deterministic
execution decision following PLAN 006 §12.3–§12.11.

It is the provider-neutral decision layer; it never creates a permanent
orchestrator agent, never grants functional authority, and never degrades the
review floor. Lowest sufficient route only, subject to risk/quality/policy and
the authorized candidate set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.delegation_policy import DelegationDecision, choose_delegation
from src.core.proportional_verification import build_verification_plan
from src.core.review_workload import choose_review_workload

INLINE = "INLINE"
DELEGATE = "DELEGATE"
ESCALATE = "ESCALATE"

TOPOLOGY_VALUES = (INLINE, DELEGATE, ESCALATE)

# Ordering per PLAN 006 §12.5.
DECISION_ORDER = (
    "DETERMINISTIC_SUFFICIENT",
    "SEMANTIC_REASONING_REQUIRED",
    "SMALL_AND_LOW_RISK",
    "SEPARABLE_AND_ADDS_VALUE",
    "AUTHORIZED_CANDIDATE",
    "REVIEW_FLOOR",
    "LOWEST_SUFFICIENT_PROFILE",
    "SEQUENTIAL_VS_PARALLEL",
)

SELF_ONLY = "SELF_ONLY"
INDEPENDENT_REVIEW = "INDEPENDENT_REVIEW"
OWNER_REVIEW = "OWNER_REVIEW"

REVIEW_LEVELS = (SELF_ONLY, INDEPENDENT_REVIEW, OWNER_REVIEW)
REVIEW_RANK = {SELF_ONLY: 0, INDEPENDENT_REVIEW: 1, OWNER_REVIEW: 2}

PROFILE_TRACEABLE = "TRACEABLE"
PROFILE_NOT_OBSERVABLE = "NOT_OBSERVABLE"


@dataclass(frozen=True)
class ExecutionDecision:
    topology: str
    reasons: tuple[str, ...]
    review_floor: str
    verification_materiality: str
    verification_steps: tuple[str, ...]
    profile_traceability: str
    sequential_or_parallel: str
    evidence_reuse_decision: str | None = None
    decision_order: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topology": self.topology,
            "reasons": list(self.reasons),
            "review_floor": self.review_floor,
            "verification_materiality": self.verification_materiality,
            "verification_steps": list(self.verification_steps),
            "profile_traceability": self.profile_traceability,
            "sequential_or_parallel": self.sequential_or_parallel,
            "evidence_reuse_decision": self.evidence_reuse_decision,
            "decision_order": list(self.decision_order),
        }


def _choose_review_floor(
    *,
    risk: str,
    sensitive: bool,
    findings: bool,
    canonical_floor: str | None,
    owner_required: bool = False,
) -> tuple[str, list[str]]:
    result = choose_review_workload(
        None,
        risk=risk,
        sensitive=sensitive,
        findings=findings,
        required_review=canonical_floor,
        owner_required=owner_required,
    )
    level = str(result.get("review_level") or SELF_ONLY)
    if level not in REVIEW_LEVELS:
        level = SELF_ONLY
    return level, [f"REVIEW_FLOOR:{level}"]


def make_execution_decision(
    *,
    task: dict[str, Any],
    delegation: DelegationDecision | None = None,
    policy_path: str | Path | None = None,
    root: str | Path | None = None,
) -> ExecutionDecision:
    """Build the unified execution decision from the mission task.

    Consumes ``choose_delegation`` for the INLINE/DELEGATE/ESCALATE topology
    (bounded by MissionAuthorization), the review workload policy for the
    review floor, and the T2-B verification plan for the proportional ladder.
    The evidence reuse decision is a string observation (REUSE/TARGETED_REVERIFY/
    RERUN_REQUIRED/UNVERIFIABLE) when an evidence ref is supplied; functional
    materiality is never granted here.
    """
    delegation = delegation or choose_delegation(task, policy_path=policy_path)
    if delegation.decision not in TOPOLOGY_VALUES:
        raise ValueError(f"UNKNOWN_TOPOLOGY:{delegation.decision}")

    reasons = list(delegation.reasons)
    decision_order = list(DECISION_ORDER)

    risk = str(task.get("risk") or "LOW")
    sensitive = bool(task.get("sensitive"))
    findings = bool(task.get("findings"))
    canonical_floor = task.get("required_review")
    review_floor, review_reasons = _choose_review_floor(
        risk=risk,
        sensitive=sensitive,
        findings=findings,
        canonical_floor=canonical_floor,
        owner_required=bool(task.get("owner_required")),
    )
    reasons.extend(review_reasons)

    verification_plan = build_verification_plan(
        touched_surface=str(task.get("touched_surface") or ""),
        shared_utility=bool(task.get("shared_utility")),
        schema_consumers=int(task.get("schema_consumers") or 0),
        core_harness_touched=bool(task.get("core_harness_touched")),
        targeted_covers_consumers=bool(task.get("targeted_covers_consumers", True)),
        repair_showed_broad_damage=bool(task.get("repair_showed_broad_damage")),
        closure_needs_distinct_evidence=bool(task.get("closure_needs_distinct_evidence")),
        owner_materiality=task.get("owner_materiality"),
    )
    materiality = verification_plan.materiality
    verification_steps = tuple(step.step for step in verification_plan.steps)

    profile_traceability = PROFILE_TRACEABLE if task.get("execution_profile_id") else PROFILE_NOT_OBSERVABLE

    sequential_or_parallel = "PARALLEL" if bool(task.get("parallelizable")) and delegation.decision == DELEGATE else "SEQUENTIAL"

    evidence_reuse_decision = task.get("evidence_reuse_decision")
    if evidence_reuse_decision is not None:
        evidence_reuse_decision = str(evidence_reuse_decision)

    return ExecutionDecision(
        topology=delegation.decision,
        reasons=tuple(reasons),
        review_floor=review_floor,
        verification_materiality=materiality,
        verification_steps=verification_steps,
        profile_traceability=profile_traceability,
        sequential_or_parallel=sequential_or_parallel,
        evidence_reuse_decision=evidence_reuse_decision,
        decision_order=tuple(decision_order),
    )
