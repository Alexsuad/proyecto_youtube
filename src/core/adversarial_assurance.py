"""T2-C — Adversarial Assurance + Selective Mutation for PLAN 006.

Derives protection invariants from the historical R1-M5 incident families
(PLAN 006 §10C.3): state/history, lineage, authority and critical doubt. Each
check is a pure predicate over a parsed lifecycle observation and returns
violations. A surviving must-kill mutant is an assurance gap, never ignored.

The mutation harness is selective: it only covers the critical invariant checks
defined here, never repo-wide mutation testing (PLAN 006 §10C.4). It consumes
the real `work_lifecycle` surface as data; it does not modify product modules.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# State family (from schemas/work_lifecycle.json state enum)
REQUIRED_TRANSITIONS = {
    "SCREENED_WORK": ("DISCOVERED_WORK",),
    "FINALIST_WORK": ("SCREENED_WORK",),
    "FINAL_SELECTED_WORK": ("FINALIST_WORK",),
    "EXCLUDED_WORK": ("SCREENED_WORK", "DISCOVERED_WORK", "FINALIST_WORK"),
    "INVALIDATED_WORK": ("DISCOVERED_WORK", "SCREENED_WORK", "FINALIST_WORK", "FINAL_SELECTED_WORK", "EXCLUDED_WORK"),
}

_VALID_STATES = {
    "DISCOVERED_WORK", "SCREENED_WORK", "FINALIST_WORK", "FINAL_SELECTED_WORK", "EXCLUDED_WORK", "INVALIDATED_WORK",
}
_VALID_AUTHORIZATION_STATUS = {"NOT_ACTIVATED", "ACTIVE", "RESOLVED", "INVALIDATED"}
_VALID_RETURN_ROUTE = {
    "RETURN_TO_SCREENING", "EXCLUDED_WORK", "MORE_TARGETED_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE",
    "CHANNEL_INTELLIGENCE_REVIEW_REQUIRED", "YOUTUBE_ADAPTATION_REVIEW_REQUIRED",
}
_RETURN_ROUTE_REQUIRES_TRIGGER = {
    "RETURN_TO_SCREENING", "EXCLUDED_WORK", "MORE_TARGETED_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE",
}
_VALID_RETURN_TRIGGERS = {
    "MATERIAL_QUESTION_INTENT_TERRITORY_CHANGE",
    "VISIBLE_PROMISE_OR_EARLY_PACKAGING_IMPACT",
}
_APPROVED_ACTIONS = {
    "CONTINUE_SCREENING", "PROMOTE_TO_FINALIST_CONSIDERATION", "EXCLUDE_FOR_CURRENT_EPISODE",
    "REQUIRE_MORE_TARGETED_RESEARCH", "BLOCK_BY_EVIDENCE",
}


@dataclass(frozen=True)
class AdversarialCheck:
    check_id: str
    description: str
    check: Callable[[dict[str, Any]], list[str]]


def _state_transition_check(observation: dict[str, Any]) -> list[str]:
    """SCREENED/EXCLUDED/INVALIDATED without a required prior transition fails."""
    violations: list[str] = []
    works = observation.get("works") or []
    transitions = observation.get("transitions") or []
    by_work: dict[str, list[dict[str, Any]]] = {}
    for transition in transitions:
        if isinstance(transition, dict) and transition.get("work_id"):
            by_work.setdefault(str(transition["work_id"]), []).append(transition)
    for work in works:
        if not isinstance(work, dict):
            continue
        work_id = str(work.get("work_id") or "")
        state = str(work.get("state") or "")
        if state not in _VALID_STATES:
            violations.append(f"INVALID_WORK_STATE:{work_id}:{state}")
            continue
        required = REQUIRED_TRANSITIONS.get(state)
        if not required:
            continue
        prior_states = {str(tr.get("previous_state") or "") for tr in by_work.get(work_id, [])}
        if state == "DISCOVERED_WORK":
            continue
        if not prior_states or not set(required).intersection(prior_states):
            violations.append(f"MISSING_REQUIRED_TRANSITION:{work_id}:{state}:needs_one_of={','.join(sorted(required))}")
    return violations


def _lineage_check(observation: dict[str, Any]) -> list[str]:
    """Lineage integrity: previous refs exist, belong to the same work, are not
    future, and transition ids are unique."""
    violations: list[str] = []
    works = observation.get("works") or []
    transitions = observation.get("transitions") or []
    known_transitions = {
        str(tr.get("transition_id") or ""): tr
        for tr in transitions
        if isinstance(tr, dict) and tr.get("transition_id")
    }
    seen_ids: set[str] = set()
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        transition_id = str(transition.get("transition_id") or "")
        if transition_id in seen_ids:
            violations.append(f"DUPLICATE_TRANSITION_ID:{transition_id}")
        seen_ids.add(transition_id)
        lineage_ref = str(transition.get("lineage_ref") or "")
        previous_state = str(transition.get("previous_state") or "")
        target_state = str(transition.get("target_state") or "")
        if lineage_ref and lineage_ref not in known_transitions:
            violations.append(f"PREVIOUS_REF_NONEXISTENT:{transition_id}:{lineage_ref}")
        if previous_state and previous_state not in _VALID_STATES:
            violations.append(f"PREVIOUS_STATE_INVALID:{transition_id}:{previous_state}")
        if target_state and target_state not in _VALID_STATES:
            violations.append(f"TARGET_STATE_INVALID:{transition_id}:{target_state}")
        # previous_state must equal the lineage target if lineage is resolvable
        if lineage_ref and lineage_ref in known_transitions:
            lineage = known_transitions[lineage_ref]
            if str(lineage.get("target_state") or "") != previous_state:
                violations.append(f"LINEAGE_STATE_MISMATCH:{transition_id}")
            if str(lineage.get("work_id") or "") != str(transition.get("work_id") or ""):
                violations.append(f"LINEAGE_WORK_MISMATCH:{transition_id}:{lineage_ref}")
            try:
                parent_time = _parse_occurred_at(str(lineage.get("occurred_at") or ""))
                transition_time = _parse_occurred_at(str(transition.get("occurred_at") or ""))
                if parent_time >= transition_time:
                    violations.append(f"LINEAGE_NOT_STRICTLY_PRIOR:{transition_id}:{lineage_ref}")
            except ValueError:
                violations.append(f"LINEAGE_TIME_UNVERIFIABLE:{transition_id}:{lineage_ref}")
    return violations


def _parse_occurred_at(value: str) -> datetime:
    if not value:
        raise ValueError("missing occurred_at")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _authority_check(observation: dict[str, Any]) -> list[str]:
    """Authority integrity: transition_authority_ref and authority_role resolve
    against the canonical responsibility registry."""
    violations: list[str] = []
    transitions = observation.get("transitions") or []
    registry = observation.get("responsibility_registry")
    if not isinstance(registry, dict) or not isinstance(registry.get("responsibilities"), list):
        violations.append("RESPONSIBILITY_REGISTRY_MISSING")
        return violations
    roles = {str(item.get("role_id")) for item in registry["responsibilities"] if isinstance(item, dict) and item.get("role_id")}
    if not roles:
        violations.append("RESPONSIBILITY_REGISTRY_EMPTY")
        return violations
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        authority_ref = str(transition.get("transition_authority_ref") or "")
        authority_role = str(transition.get("authority_role") or "")
        transition_id = str(transition.get("transition_id") or "")
        expected_ref = f"config/responsibility_registry.json#responsibilities/{authority_role}"
        if not authority_ref or authority_ref != expected_ref:
            violations.append(f"AUTHORITY_REF_UNRESOLVABLE:{transition_id}:{authority_ref}")
        if not authority_role or authority_role not in roles:
            violations.append(f"AUTHORITY_ROLE_UNRESOLVABLE:{str(transition.get('transition_id'))}:{authority_role}")
    return violations


def _critical_doubt_check(observation: dict[str, Any]) -> list[str]:
    """RESOLVED requires a valid trigger/activation/authorization/evidence and a
    return route associated with an approved trigger."""
    violations: list[str] = []
    doubts = observation.get("critical_doubts") or []
    for doubt in doubts:
        if not isinstance(doubt, dict):
            continue
        doubt_id = str(doubt.get("doubt_id") or "")
        status = str(doubt.get("authorization_status") or "")
        if status not in _VALID_AUTHORIZATION_STATUS:
            violations.append(f"DOUBT_STATUS_INVALID:{doubt_id}:{status}")
        activation = doubt.get("activation_criteria") or []
        if status == "RESOLVED":
            if not isinstance(activation, list) or not activation:
                violations.append(f"RESOLVED_WITHOUT_ACTIVATION:{doubt_id}")
            if not doubt.get("authorization_ref"):
                violations.append(f"RESOLVED_WITHOUT_AUTHORIZATION:{doubt_id}")
            evidence = doubt.get("evidence_refs") or []
            if not isinstance(evidence, list) or not evidence:
                violations.append(f"RESOLVED_WITHOUT_EVIDENCE:{doubt_id}")
        return_route = str(doubt.get("return_route") or "")
        return_trigger = doubt.get("return_trigger")
        if return_route not in _VALID_RETURN_ROUTE:
            violations.append(f"RETURN_ROUTE_INVALID:{doubt_id}:{return_route}")
        elif return_route in _RETURN_ROUTE_REQUIRES_TRIGGER and return_trigger not in _VALID_RETURN_TRIGGERS:
            violations.append(f"RETURN_ROUTE_WITHOUT_TRIGGER:{doubt_id}")
        outcome = str(doubt.get("outcome") or "")
        if outcome not in {"NOT_APPLICABLE"} and outcome not in _APPROVED_ACTIONS:
            violations.append(f"OUTCOME_NOT_APPROVED:{doubt_id}:{outcome}")
    return violations


ADVERSARIAL_CHECKS: tuple[AdversarialCheck, ...] = (
    AdversarialCheck("STATE_HISTORY_REQUIRED_TRANSITION", "Screened/excluded/invalidated work requires a prior transition.", _state_transition_check),
    AdversarialCheck("LINEAGE_INTEGRITY", "Lineage refs exist, belong to the same work and are not future/incompatible; transition ids unique.", _lineage_check),
    AdversarialCheck("AUTHORITY_RESOLVABLE", "Authority refs resolve against the canonical responsibility registry.", _authority_check),
    AdversarialCheck("CRITICAL_DOUBT_VALID_CLOSURE", "RESOLVED requires trigger/activation/authorization/evidence; return route matches an approved trigger.", _critical_doubt_check),
)

_BY_ID = {check.check_id: check for check in ADVERSARIAL_CHECKS}


def verify_adversarial(invariant_ids: list[str], observation: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    for invariant_id in invariant_ids:
        check = _BY_ID.get(invariant_id)
        if check is None:
            violations.append(f"UNKNOWN_ADVERSARIAL_CHECK:{invariant_id}")
            continue
        violations.extend(check.check(observation))
    return violations


def verify_all_adversarial(observation: dict[str, Any]) -> list[str]:
    return verify_adversarial([check.check_id for check in ADVERSARIAL_CHECKS], observation)


# --- Selective must-kill mutations over the critical checks ---


@dataclass(frozen=True)
class MustKillMutation:
    mutant_id: str
    target_check_id: str
    mutate: Callable[[dict[str, Any]], list[str]]


def _mutate_state_check_removes_required_transition(observation: dict[str, Any]) -> list[str]:
    return []


def _mutate_lineage_check_removes_duplicate_guard(observation: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    transitions = observation.get("transitions") or []
    known_transitions = {str(tr.get("transition_id") or "") for tr in transitions if isinstance(tr, dict)}
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        transition_id = str(transition.get("transition_id") or "")
        lineage_ref = str(transition.get("lineage_ref") or "")
        previous_state = str(transition.get("previous_state") or "")
        if lineage_ref and lineage_ref not in known_transitions:
            violations.append(f"PREVIOUS_REF_NONEXISTENT:{transition_id}:{lineage_ref}")
        if previous_state and previous_state not in _VALID_STATES:
            violations.append(f"PREVIOUS_STATE_INVALID:{transition_id}:{previous_state}")
    return violations


def _mutate_authority_check_accepts_invented_authority(observation: dict[str, Any]) -> list[str]:
    return []


def _mutate_doubt_check_allows_resolved_without_evidence(observation: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    doubts = observation.get("critical_doubts") or []
    for doubt in doubts:
        if not isinstance(doubt, dict):
            continue
        doubt_id = str(doubt.get("doubt_id") or "")
        status = str(doubt.get("authorization_status") or "")
        if status not in _VALID_AUTHORIZATION_STATUS:
            violations.append(f"DOUBT_STATUS_INVALID:{doubt_id}:{status}")
        return_route = str(doubt.get("return_route") or "")
        if return_route not in _VALID_RETURN_ROUTE:
            violations.append(f"RETURN_ROUTE_INVALID:{doubt_id}:{return_route}")
    return violations


MUST_KILL_MUTATIONS: tuple[MustKillMutation, ...] = (
    MustKillMutation("STATE_REQUIRED_TRANSITION_REMOVED", "STATE_HISTORY_REQUIRED_TRANSITION", _mutate_state_check_removes_required_transition),
    MustKillMutation("DUPLICATE_TRANSITION_GUARD_REMOVED", "LINEAGE_INTEGRITY", _mutate_lineage_check_removes_duplicate_guard),
    MustKillMutation("INVENTED_AUTHORITY_ACCEPTED", "AUTHORITY_RESOLVABLE", _mutate_authority_check_accepts_invented_authority),
    MustKillMutation("RESOLVED_WITHOUT_EVIDENCE_ACCEPTED", "CRITICAL_DOUBT_VALID_CLOSURE", _mutate_doubt_check_allows_resolved_without_evidence),
)


def evaluate_must_kill_mutation(
    *,
    mutant: MustKillMutation,
    observation: dict[str, Any],
    adversarial_probe: Callable[[list[str], dict[str, Any]], list[str]] = verify_adversarial,
) -> dict[str, Any]:
    """A must-kill mutant is an assurance gap if the critical probe still passes
    against the original (targeted critical tests must fail on the mutant)."""
    baseline = adversarial_probe([mutant.target_check_id], observation)
    baseline_gap = bool(baseline)
    mutated = mutant.mutate(observation)
    killed = baseline_gap and not mutated
    if killed:
        classification = "KILLED"
    elif baseline_gap and len(mutated) < len(baseline):
        classification = "ASSURANCE_GAP"
    else:
        classification = "NO_FAULT_EXPOSED"
    return {
        "mutant_id": mutant.mutant_id,
        "target_check_id": mutant.target_check_id,
        "baseline_violations": baseline,
        "mutated_violations": mutated,
        "survives": not killed,
        "classification": classification,
    }
