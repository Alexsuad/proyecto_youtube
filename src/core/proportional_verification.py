"""T2-B — Targeted Invalidation + Proportional Verification for PLAN 006.

Reduces revalidation cascades without losing sensitivity to material changes.
Encodes the proportional validation chain (PLAN 006 §10B.3), the materiality
classification, a repeated-equivalent-work detector and the fan-in rule
(§10B.5). Infraestructure represents impact; functional materiality is decided
by the domain owner — this module never overrides a domain decision.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DIRECT_IMPACT = "DIRECT_IMPACT"
PARTIAL_DEPENDENCY_IMPACT = "PARTIAL_DEPENDENCY_IMPACT"
FULL_REASSESSMENT_REQUIRED = "FULL_REASSESSMENT_REQUIRED"
NO_MATERIAL_IMPACT = "NO_MATERIAL_IMPACT"

MATERIALITY_VALUES = (DIRECT_IMPACT, PARTIAL_DEPENDENCY_IMPACT, FULL_REASSESSMENT_REQUIRED, NO_MATERIAL_IMPACT)

STEP_DIRECT = "DIRECT_CHECK_OR_ADVERSARIAL_INVARIANT"
STEP_TARGETED = "TARGETED_MODULE_TESTS"
STEP_AFFECTED = "AFFECTED_CONSUMER_REGRESSION"
STEP_BROADER = "BROADER_SUITE"
STEP_DIFF = "GIT_DIFF_CHECK"

PROPORTIONAL_CHAIN = (STEP_DIRECT, STEP_TARGETED, STEP_AFFECTED, STEP_BROADER, STEP_DIFF)

_PYTEST_FILE = re.compile(r"(tests/[^ :]+\.py)(::[^ ]+)?")


@dataclass(frozen=True)
class VerificationStep:
    step: str
    reason: str
    command: tuple[str, ...] | None = None
    evidence_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"step": self.step, "reason": self.reason, "command": list(self.command) if self.command else None, "evidence_ref": self.evidence_ref}


@dataclass(frozen=True)
class VerificationPlan:
    materiality: str
    steps: tuple[VerificationStep, ...]
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "materiality": self.materiality,
            "steps": [step.to_dict() for step in self.steps],
            "reasons": list(self.reasons),
        }


def _materiality_from_owner(owner_decision: str | None) -> str | None:
    if owner_decision in MATERIALITY_VALUES:
        return owner_decision
    return None


def build_verification_plan(
    *,
    touched_surface: str,
    shared_utility: bool,
    schema_consumers: int,
    core_harness_touched: bool,
    targeted_covers_consumers: bool,
    repair_showed_broad_damage: bool,
    closure_needs_distinct_evidence: bool,
    owner_materiality: str | None = None,
) -> VerificationPlan:
    """Build a proportional verification plan starting from the affected risk.

    Broader suite is included only when fan-in/risk/closure justifies it
    (PLAN 006 §10B.5); otherwise the plan stops after targeted + affected.
    git diff --check is always the final step.
    """
    materiality = _materiality_from_owner(owner_materiality)
    if materiality is None:
        if shared_utility or schema_consumers > 1 or core_harness_touched or repair_showed_broad_damage:
            materiality = FULL_REASSESSMENT_REQUIRED
        elif touched_surface:
            materiality = PARTIAL_DEPENDENCY_IMPACT
        else:
            materiality = NO_MATERIAL_IMPACT

    steps: list[VerificationStep] = []
    steps.append(VerificationStep(STEP_DIRECT, f"adversarial/direct check for {touched_surface}"))
    steps.append(VerificationStep(STEP_TARGETED, f"targeted module tests for {touched_surface}"))

    broader_needed = (
        shared_utility
        or schema_consumers > 1
        or core_harness_touched
        or not targeted_covers_consumers
        or repair_showed_broad_damage
        or closure_needs_distinct_evidence
    )
    if broader_needed:
        steps.append(VerificationStep(STEP_AFFECTED, "affected consumer regression"))
        steps.append(VerificationStep(STEP_BROADER, "broader suite justified by fan-in/risk/closure"))
    else:
        steps.append(VerificationStep(STEP_AFFECTED, "affected consumer regression (targeted covers known consumers)"))
    steps.append(VerificationStep(STEP_DIFF, "git diff --check"))
    return VerificationPlan(materiality=materiality, steps=tuple(steps))


def normalize_repeated_work(runs: list[str]) -> dict[str, Any]:
    """Detect repeated equivalent pytest runs (PLAN 006 §10B.4).

    Returns grouped node identifiers with their occurrence counts so wrappers
    that rerun the same material test are identified without banning repeats:
    every repetition must have a reason.
    """
    normalized: dict[str, int] = {}
    for run in runs:
        match = _PYTEST_FILE.match(run)
        if match:
            file_part = match.group(1)
            node_part = match.group(2) or ""
            normalized[f"tests/{file_part.split('tests/')[-1]}{node_part}"] = (
                normalized.get(f"tests/{file_part.split('tests/')[-1]}{node_part}", 0) + 1
            )
        else:
            normalized[run] = normalized.get(run, 0) + 1
    repeated = {key: count for key, count in normalized.items() if count > 1}
    return {
        "total_runs": len(runs),
        "unique_material_tests": len(normalized),
        "repeated_equivalently": sorted(repeated),
        "occurrences": repeated,
    }


def justify_broader_suite(
    *,
    shared_utility: bool,
    schema_consumers: int,
    core_harness_touched: bool,
    targeted_covers_consumers: bool,
    repair_showed_broad_damage: bool,
    closure_needs_distinct_evidence: bool,
) -> tuple[bool, list[str]]:
    """Apply the fan-in rule (PLAN 006 §10B.5) and explain the decision."""
    reasons: list[str] = []
    if shared_utility:
        reasons.append("SHARED_UTILITY_CHANGED")
    if schema_consumers > 1:
        reasons.append(f"SCHEMA_CONSUMED_BY_{schema_consumers}_MODULES")
    if core_harness_touched:
        reasons.append("MISSION_AUTHORIZATION_COMPLETION_CORE")
    if not targeted_covers_consumers:
        reasons.append("TARGETED_TEST_DOES_NOT_COVER_KNOWN_CONSUMERS")
    if repair_showed_broad_damage:
        reasons.append("REPAIR_SHOWED_BROADER_DAMAGE")
    if closure_needs_distinct_evidence:
        reasons.append("CLOSURE_REQUIRES_DISTINCT_ADDITIONAL_EVIDENCE")
    return bool(reasons), reasons
