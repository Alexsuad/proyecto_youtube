"""Machine-checkable invariants for PLAN 005 governed autonomy.

Each invariant is a pure predicate over an observation snapshot (a dict built
from real artifacts). A check returns a list of violations; an empty list means
the invariant holds. This module is the single machine-readable input for
adversarial tests, self-adversarial review and the PLAN 005 completion review.
Invariants are never documentary text; a PASS can only be derived from an
evidence chain that satisfies them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

CANONICAL_REVIEW_LEVELS = ("SELF_ONLY", "INDEPENDENT_REVIEW", "OWNER_REVIEW")
REVIEW_ORIGINS = ("INTERNAL", "EXTERNAL", "NOT_APPLICABLE")
REVIEW_RANK = {"SELF_ONLY": 0, "INDEPENDENT_REVIEW": 1, "OWNER_REVIEW": 2}
DECISIONS = ("INLINE", "DELEGATE", "ESCALATE")
DEMONSTRATION_CLASSES = {"UNIT", "INTEGRATION", "RUNTIME_ENTRYPOINT_INTEGRATION", "CONTROLLED_TECHNICAL_HARNESS_E2E"}


@dataclass(frozen=True)
class Invariant:
    invariant_id: str
    description: str
    check: Callable[[dict[str, Any]], list[str]]


def _has_truthy(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else bool(value)


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, (list, tuple, set)) and len(value) > 0


def _no_delegation_without_authorization(obs: dict[str, Any]) -> list[str]:
    if str(obs.get("decision") or "") != "DELEGATE":
        return []
    violations: list[str] = []
    if not _has_truthy(obs.get("delegation_authorized")):
        violations.append("DELEGATION_WITHOUT_AUTHORIZATION")
    if not _non_empty_list(obs.get("authorized_candidate_set")):
        violations.append("DELEGATION_WITHOUT_PARENT_CANDIDATE_SET")
    return violations


def _child_authority_subset_of_parent(obs: dict[str, Any]) -> list[str]:
    """CHILD_AUTHORITY ⊆ PARENT_AUTHORITY for files, context, operations, capability, role and depth."""
    violations: list[str] = []

    def within(child: str, allowed: list[str]) -> bool:
        candidate = str(child).replace("\\", "/").strip("/")
        parts = candidate.split("/")
        for prefix in allowed:
            pref = str(prefix).replace("\\", "/").strip("/").split("/")
            if parts[: len(pref)] == pref or candidate == "/".join(pref):
                return True
        return False

    parent_files = [str(item) for item in obs.get("parent_allowed_files", [])]
    child_files = obs.get("child_allowed_files", [])
    if child_files and not parent_files:
        violations.append("CHILD_ALLOWED_FILES_WITHOUT_PARENT_AUTHORITY")
    for child in child_files:
        if parent_files and not within(child, parent_files):
            violations.append("CHILD_ALLOWED_FILES_EXCEED_PARENT")
    parent_ctx = set(str(item) for item in obs.get("parent_context_refs", []))
    child_ctx = set(str(item) for item in obs.get("child_context_refs", []))
    if child_ctx and not parent_ctx:
        violations.append("CHILD_CONTEXT_REFS_WITHOUT_PARENT_AUTHORITY")
    elif parent_ctx and not child_ctx.issubset(parent_ctx):
        violations.append("CHILD_CONTEXT_REFS_EXCEED_PARENT")
    parent_ops = set(str(item) for item in obs.get("parent_operations", []))
    child_ops = set(str(item) for item in obs.get("child_operations", []))
    if child_ops and not parent_ops:
        violations.append("CHILD_OPERATIONS_WITHOUT_PARENT_AUTHORITY")
    elif parent_ops and not child_ops.issubset(parent_ops):
        violations.append("CHILD_OPERATIONS_EXCEED_PARENT")
    parent_caps = set(str(item) for item in obs.get("parent_capabilities", []))
    child_capability = str(obs.get("child_capability_id") or "")
    if child_capability and not parent_caps:
        violations.append("CHILD_CAPABILITY_WITHOUT_PARENT_AUTHORITY")
    elif parent_caps and child_capability not in parent_caps:
        violations.append("CHILD_CAPABILITY_EXCEEDS_PARENT")
    parent_roles = set(str(item) for item in obs.get("parent_roles", []))
    child_role = str(obs.get("child_role_id") or "")
    if child_role and not parent_roles:
        violations.append("CHILD_ROLE_WITHOUT_PARENT_AUTHORITY")
    elif parent_roles and child_role not in parent_roles:
        violations.append("CHILD_ROLE_EXCEEDS_PARENT")
    parent_max_value = obs.get("parent_max_delegation_depth")
    child_depth = int(obs.get("child_delegation_depth", 0))
    if child_depth > 0 and parent_max_value is None:
        violations.append("CHILD_DEPTH_WITHOUT_PARENT_AUTHORITY")
    elif parent_max_value is not None and child_depth > int(parent_max_value):
        violations.append("CHILD_DEPTH_EXCEEDS_PARENT")
    return violations


def _review_never_downgraded(obs: dict[str, Any]) -> list[str]:
    required = str(obs.get("required_review") or "").upper()
    selected = str(obs.get("selected_review") or "").upper()
    violations: list[str] = []
    if required and required not in REVIEW_RANK:
        violations.append("REQUIRED_REVIEW_NOT_CANONICAL")
    if selected and selected not in REVIEW_RANK:
        violations.append("SELECTED_REVIEW_NOT_CANONICAL")
    if violations or not required or not selected:
        return violations
    if REVIEW_RANK[selected] < REVIEW_RANK[required]:
        violations.append("REVIEW_POLICY_DOWNGRADE")
    return violations


def _review_origin_is_provenance(obs: dict[str, Any]) -> list[str]:
    level = str(obs.get("review_level") or "").upper()
    origin = str(obs.get("review_origin") or "").upper()
    violations: list[str] = []
    if level and level not in CANONICAL_REVIEW_LEVELS:
        violations.append("REVIEW_LEVEL_NOT_CANONICAL")
    if origin and origin not in REVIEW_ORIGINS:
        violations.append("REVIEW_ORIGIN_NOT_PROVENANCE")
    if not level and (origin in {"INTERNAL", "EXTERNAL"}):
        violations.append("REVIEW_ORIGIN_WITHOUT_LEVEL")
    return violations


def _skill_applied_requires_resolved_source(obs: dict[str, Any]) -> list[str]:
    applied = [str(item) for item in obs.get("skills_applied", [])]
    if not applied:
        return []
    violations: list[str] = []
    if not obs.get("canonical_skill_ref"):
        violations.append("SKILL_APPLIED_WITHOUT_CANONICAL_REF")
    if not obs.get("canonical_skill_checksum"):
        violations.append("SKILL_APPLIED_WITHOUT_CHECKSUM")
    if not _non_empty_list(obs.get("resolution_evidence")):
        violations.append("SKILL_APPLIED_WITHOUT_RESOLUTION_EVIDENCE")
    if not _non_empty_list(obs.get("application_evidence")):
        violations.append("SKILL_APPLIED_WITHOUT_APPLICATION_EVIDENCE")
    return violations


def _recovery_unverifiable_does_not_resume(obs: dict[str, Any]) -> list[str]:
    topology = str(obs.get("resume_topology") or "")
    status = str(obs.get("recovery_status") or "").upper()
    blocked_topologies = {"BLOCKED_REPLAY_RESUME_UNSUPPORTED", "NEW_AUTHORIZATION_REQUIRED", "BLOCKED_AMBIGUOUS_RESERVATION", "BLOCKED"}
    if topology in blocked_topologies:
        return []
    if topology == "SAME_RESERVATION_LEASE":
        if not status:
            return ["RECOVERY_RESUMED_WITHOUT_STATUS"]
        if status in {"STALE", "UNVERIFIABLE", "INVALID", "AMBIGUOUS"}:
            return ["RECOVERY_RESUMED_UNVERIFIABLE"]
        return []
    if status in {"STALE", "UNVERIFIABLE", "INVALID", "AMBIGUOUS"}:
        return ["RECOVERY_UNVERIFIABLE_WITHOUT_BLOCKED_TOPOLOGY"]
    if topology not in {""}:
        return ["RECOVERY_TOPOLOGY_UNSUPPORTED"]
    if topology and not status:
        return ["RECOVERY_RESUMED_WITHOUT_STATUS"]
    return []


def _child_manifest_matches_child_run(obs: dict[str, Any]) -> list[str]:
    parent_run = str(obs.get("parent_run_id") or "")
    child_run = str(obs.get("child_run_id") or "")
    manifest_run = str(obs.get("manifest_run_id") or "")
    violations: list[str] = []
    if parent_run and child_run and parent_run == child_run:
        violations.append("PARENT_RUN_EQUALS_CHILD_RUN")
    if child_run and manifest_run and manifest_run != child_run:
        violations.append("MANIFEST_RUN_MISMATCHES_CHILD_RUN")
    if _has_truthy(obs.get("conversation_history_inherited")):
        violations.append("CONVERSATION_HISTORY_INHERITED")
    return violations


def _pass_requires_evidence(obs: dict[str, Any]) -> list[str]:
    result = str(obs.get("result") or "").upper()
    refs = [str(item) for item in obs.get("evidence_refs", [])]
    if result != "PASS":
        return []
    if not refs:
        return ["PASS_WITHOUT_EVIDENCE_REFS"]
    return [f"PASS_EVIDENCE_REF_UNSPECIFIED:{item}" for item in refs if not item.strip()]


def _controlled_demo_not_promotion(obs: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    demo_class = str(obs.get("demonstration_class") or "")
    if demo_class and demo_class not in DEMONSTRATION_CLASSES:
        violations.append("DEMONSTRATION_CLASS_NOT_CONTROLLED")
    for flag in ("real_operational_subagents_promotion", "real_multiagent_runtime_promotion", "functional_readiness_claim", "real_product_operation"):
        if _has_truthy(obs.get(flag)):
            violations.append(f"PROMOTION_FLAG:{flag}")
    return violations


def _routing_inside_authorized_set(obs: dict[str, Any]) -> list[str]:
    status = str(obs.get("status") or "").upper()
    if status != "SELECTED":
        return []
    candidates = set(str(item) for item in obs.get("candidate_set", []))
    selected = str(obs.get("selected_profile") or "")
    if not selected:
        return ["ROUTING_SELECTED_WITHOUT_PROFILE"]
    if not candidates:
        return ["ROUTING_SELECTED_WITHOUT_AUTHORIZED_CANDIDATE_SET"]
    if selected not in candidates:
        return ["ROUTING_OUTSIDE_AUTHORIZED_SET"]
    return []


def _no_implicit_increment_authorization(obs: dict[str, Any]) -> list[str]:
    result = str(obs.get("increment_result") or "").upper()
    if result not in {"PASS", "LIMITATION"}:
        return []
    if _has_truthy(obs.get("next_authorized")):
        return ["INCREMENT_RESULT_GRANTS_NEXT_AUTHORIZATION"]
    return []


def _completion_derived_from_transitive_freshness(obs: dict[str, Any]) -> list[str]:
    completion = str(obs.get("completion_claim") or "").upper()
    if completion not in {"COMPLETED", "PASS", "PASS_WITH_OBSERVABILITY_LIMITATIONS", "HARDENING_COMPLETED_PENDING_OWNER_REVIEW", "TECHNICALLY_COMPLETED_PENDING_OWNER_REVIEW"}:
        return []
    status = str(obs.get("transitive_freshness") or "").upper()
    if not status:
        return ["COMPLETION_CLAIM_WITHOUT_TRANSITIVE_FRESHNESS"]
    if status != "FRESH":
        return ["COMPLETION_CLAIM_WITH_STALE_EVIDENCE"]
    return []


INVARIANTS: tuple[Invariant, ...] = (
    Invariant("NO_DELEGATION_WITHOUT_AUTHORIZATION", "DELEGATE requires explicit delegation authorization and a parent candidate set.", _no_delegation_without_authorization),
    Invariant("CHILD_AUTHORITY_SUBSET_OF_PARENT", "CHILD_AUTHORITY ⊆ PARENT_AUTHORITY; any widening blocks.", _child_authority_subset_of_parent),
    Invariant("REVIEW_NEVER_DOWNGRADED", "OWNER_REVIEW/INDEPENDENT_REVIEW can never be downgraded to SELF_ONLY.", _review_never_downgraded),
    Invariant("REVIEW_ORIGIN_IS_PROVENANCE", "INTERNAL/EXTERNAL is provenance, never a new review level.", _review_origin_is_provenance),
    Invariant("SKILL_APPLIED_REQUIRES_RESOLVED_SOURCE", "APPLIED requires a canonical ref, checksum, resolution evidence and application evidence.", _skill_applied_requires_resolved_source),
    Invariant("RECOVERY_UNVERIFIABLE_DOES_NOT_RESUME", "A stale/unverifiable recovery must not resume.", _recovery_unverifiable_does_not_resume),
    Invariant("CHILD_MANIFEST_MATCHES_CHILD_RUN", "The child manifest must correspond to the real child run without inherited conversation.", _child_manifest_matches_child_run),
    Invariant("PASS_REQUIRES_EVIDENCE", "A PASS without evidence refs is invalid.", _pass_requires_evidence),
    Invariant("CONTROLLED_DEMO_NOT_PROMOTION", "Controlled demonstrations never promote operational/product readiness.", _controlled_demo_not_promotion),
    Invariant("ROUTING_INSIDE_AUTHORIZED_SET", "Routing never leaves the authorized candidate set.", _routing_inside_authorized_set),
    Invariant("NO_IMPLICIT_INCREMENT_AUTHORIZATION", "PASS(P5-Ax) never authorizes P5-Ax+1.", _no_implicit_increment_authorization),
    Invariant("COMPLETION_DERIVED_FROM_TRANSITIVE_FRESHNESS", "A completion claim is derived, never declarative: it requires transitive-fresh evidence.", _completion_derived_from_transitive_freshness),
)

_BY_ID = {invariant.invariant_id: invariant for invariant in INVARIANTS}


def verify_invariants(invariant_ids: list[str], observation: dict[str, Any]) -> list[str]:
    """Evaluate a subset of invariants; unknown invariant ids are fail-closed."""
    violations: list[str] = []
    for invariant_id in invariant_ids:
        invariant = _BY_ID.get(invariant_id)
        if invariant is None:
            violations.append(f"UNKNOWN_INVARIANT:{invariant_id}")
            continue
        violations.extend(invariant.check(observation))
    return violations


def verify_all_invariants(observation: dict[str, Any]) -> list[str]:
    """Evaluate the full invariant set against a single observation snapshot."""
    return verify_invariants([invariant.invariant_id for invariant in INVARIANTS], observation)
