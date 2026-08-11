"""Adversarial invariant tests for PLAN 005 governed autonomy.

Every negative case must be fail-closed: the invariant must report a violation
so that no completion can be derived from it. These tests attack observable
behaviour of the machine-checkable invariants, not merely code structure.
"""
from __future__ import annotations

from src.core.plan_005_invariants import (
    REVIEW_RANK,
    verify_all_invariants,
    verify_invariants,
)


def _assert_violation(invariant_ids, observation, *tokens) -> None:
    violations = verify_invariants(invariant_ids, observation)
    assert violations, f"expected violations for {invariant_ids} with {observation!r}"
    for token in tokens:
        assert any(token in item for item in violations), f"missing {token!r} in {violations}"


def _assert_holds(invariant_ids, observation) -> None:
    assert verify_invariants(invariant_ids, observation) == []


# --- Delegation ---

def test_delegate_without_authorization_is_fail_closed() -> None:
    _assert_violation(["NO_DELEGATION_WITHOUT_AUTHORIZATION"], {"decision": "DELEGATE"}, "DELEGATION_WITHOUT_AUTHORIZATION")


def test_delegate_without_parent_candidate_set_is_fail_closed() -> None:
    _assert_violation(
        ["NO_DELEGATION_WITHOUT_AUTHORIZATION"],
        {"decision": "DELEGATE", "delegation_authorized": True, "authorized_candidate_set": []},
        "DELEGATION_WITHOUT_PARENT_CANDIDATE_SET",
    )


def test_inline_or_escalate_do_not_require_delegation_authorization() -> None:
    assert verify_all_invariants({"decision": "INLINE"}) == []
    assert verify_all_invariants({"decision": "ESCALATE"}) == []


def test_child_scope_wider_than_parent_blocks() -> None:
    _assert_violation(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {"parent_allowed_files": ["src/"], "child_allowed_files": ["src/", "config/"]},
        "CHILD_ALLOWED_FILES_EXCEED_PARENT",
    )


def test_child_context_refs_outside_parent_blocks() -> None:
    _assert_violation(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {"parent_context_refs": ["a", "b"], "child_context_refs": ["a", "c"]},
        "CHILD_CONTEXT_REFS_EXCEED_PARENT",
    )


def test_child_operation_outside_parent_blocks() -> None:
    _assert_violation(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {"parent_operations": ["EXECUTE_CAPABILITY"], "child_operations": ["EXECUTE_CAPABILITY", "PUSH"]},
        "CHILD_OPERATIONS_EXCEED_PARENT",
    )


def test_child_capability_and_role_outside_parent_block() -> None:
    _assert_violation(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {"parent_capabilities": ["CAP"], "child_capability_id": "OTHER"},
        "CHILD_CAPABILITY_EXCEEDS_PARENT",
    )
    _assert_violation(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {"parent_roles": ["ROLE"], "child_role_id": "OTHER"},
        "CHILD_ROLE_EXCEEDS_PARENT",
    )


def test_child_depth_exceeding_parent_blocks() -> None:
    _assert_violation(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {"parent_max_delegation_depth": 1, "child_delegation_depth": 2},
        "CHILD_DEPTH_EXCEEDS_PARENT",
    )


def test_child_within_parent_authority_holds() -> None:
    _assert_holds(
        ["CHILD_AUTHORITY_SUBSET_OF_PARENT"],
        {
            "parent_allowed_files": ["src/", "reports/"], "child_allowed_files": ["src/core/"],
            "parent_context_refs": ["a"], "child_context_refs": ["a"],
            "parent_operations": ["EXECUTE_CAPABILITY"], "child_operations": ["EXECUTE_CAPABILITY"],
            "parent_capabilities": ["CAP"], "child_capability_id": "CAP",
            "parent_roles": ["ROLE"], "child_role_id": "ROLE",
            "parent_max_delegation_depth": 1, "child_delegation_depth": 1,
        },
    )


# --- Review ---

def test_owner_review_cannot_become_self_only() -> None:
    _assert_violation(["REVIEW_NEVER_DOWNGRADED"], {"required_review": "OWNER_REVIEW", "selected_review": "SELF_ONLY"}, "REVIEW_POLICY_DOWNGRADE")


def test_independent_review_cannot_become_self_only() -> None:
    _assert_violation(["REVIEW_NEVER_DOWNGRADED"], {"required_review": "INDEPENDENT_REVIEW", "selected_review": "SELF_ONLY"}, "REVIEW_POLICY_DOWNGRADE")


def test_owner_review_downgrade_to_internal_is_blocked() -> None:
    _assert_violation(["REVIEW_NEVER_DOWNGRADED"], {"required_review": "OWNER_REVIEW", "selected_review": "INDEPENDENT_REVIEW"}, "REVIEW_POLICY_DOWNGRADE")


def test_review_levels_are_canonical() -> None:
    _assert_violation(["REVIEW_ORIGIN_IS_PROVENANCE"], {"review_level": "EXTERNAL_REVIEW"}, "REVIEW_LEVEL_NOT_CANONICAL")


def test_review_origin_is_provenance_not_level() -> None:
    assert {"SELF_ONLY", "INDEPENDENT_REVIEW", "OWNER_REVIEW"} == set(REVIEW_RANK)
    _assert_violation(["REVIEW_ORIGIN_IS_PROVENANCE"], {"review_level": "SELF_ONLY", "review_origin": "INTERNAL_INDEPENDENT"}, "REVIEW_ORIGIN_NOT_PROVENANCE")


def test_internal_review_is_provenance_with_canonical_level() -> None:
    assert verify_all_invariants({"review_level": "INDEPENDENT_REVIEW", "review_origin": "INTERNAL"}) == []


# --- Skill provenance ---

def test_applied_skill_without_canonical_ref_blocks() -> None:
    _assert_violation(["SKILL_APPLIED_REQUIRES_RESOLVED_SOURCE"], {"skills_applied": ["s"], "canonical_skill_checksum": "a" * 64, "resolution_evidence": ["r"], "application_evidence": ["a"]}, "SKILL_APPLIED_WITHOUT_CANONICAL_REF")


def test_applied_skill_with_wrong_checksum_or_missing_evidence_blocks() -> None:
    _assert_violation(["SKILL_APPLIED_REQUIRES_RESOLVED_SOURCE"], {"skills_applied": ["s"], "canonical_skill_ref": "p", "resolution_evidence": ["r"], "application_evidence": ["a"]}, "SKILL_APPLIED_WITHOUT_CHECKSUM")
    _assert_violation(["SKILL_APPLIED_REQUIRES_RESOLVED_SOURCE"], {"skills_applied": ["s"], "canonical_skill_ref": "p", "canonical_skill_checksum": "a" * 64, "application_evidence": ["a"]}, "SKILL_APPLIED_WITHOUT_RESOLUTION_EVIDENCE")
    _assert_violation(["SKILL_APPLIED_REQUIRES_RESOLVED_SOURCE"], {"skills_applied": ["s"], "canonical_skill_ref": "p", "canonical_skill_checksum": "a" * 64, "resolution_evidence": ["r"]}, "SKILL_APPLIED_WITHOUT_APPLICATION_EVIDENCE")


def test_applied_skill_with_full_provenance_holds() -> None:
    _assert_holds(
        ["SKILL_APPLIED_REQUIRES_RESOLVED_SOURCE"],
        {"skills_applied": ["s"], "canonical_skill_ref": "p", "canonical_skill_checksum": "a" * 64, "resolution_evidence": ["r"], "application_evidence": ["a"]},
    )


# --- Recovery ---

def test_stale_recovery_does_not_resume() -> None:
    _assert_violation(["RECOVERY_UNVERIFIABLE_DOES_NOT_RESUME"], {"resume_topology": "SAME_RESERVATION_LEASE", "recovery_status": "STALE"}, "RECOVERY_RESUMED_UNVERIFIABLE")


def test_blocked_recovery_topologies_are_safe() -> None:
    for topology in ("BLOCKED_REPLAY_RESUME_UNSUPPORTED", "NEW_AUTHORIZATION_REQUIRED", "BLOCKED_AMBIGUOUS_RESERVATION"):
        assert verify_all_invariants({"resume_topology": topology}) == []


def test_orphan_or_ambiguous_reservation_is_not_authorization() -> None:
    assert verify_all_invariants({"resume_topology": "BLOCKED_AMBIGUOUS_RESERVATION", "recovery_status": "STALE"}) == []
    assert verify_all_invariants({"resume_topology": "NEW_AUTHORIZATION_REQUIRED", "recovery_status": "UNVERIFIABLE"}) == []


def test_fresh_lease_resume_is_allowed() -> None:
    _assert_holds(["RECOVERY_UNVERIFIABLE_DOES_NOT_RESUME"], {"resume_topology": "SAME_RESERVATION_LEASE", "recovery_status": "FRESH"})


# --- Fresh context ---

def test_parent_run_equals_child_run_blocks() -> None:
    _assert_violation(["CHILD_MANIFEST_MATCHES_CHILD_RUN"], {"parent_run_id": "R", "child_run_id": "R"}, "PARENT_RUN_EQUALS_CHILD_RUN")


def test_manifest_run_mismatches_child_run_blocks() -> None:
    _assert_violation(["CHILD_MANIFEST_MATCHES_CHILD_RUN"], {"child_run_id": "CHILD", "manifest_run_id": "OTHER"}, "MANIFEST_RUN_MISMATCHES_CHILD_RUN")


def test_inherited_conversation_history_blocks() -> None:
    _assert_violation(["CHILD_MANIFEST_MATCHES_CHILD_RUN"], {"conversation_history_inherited": True}, "CONVERSATION_HISTORY_INHERITED")


def test_fresh_child_manifest_holds() -> None:
    _assert_holds(
        ["CHILD_MANIFEST_MATCHES_CHILD_RUN"],
        {"parent_run_id": "PARENT", "child_run_id": "CHILD", "manifest_run_id": "CHILD", "conversation_history_inherited": False},
    )


# --- Evidence ---

def test_pass_without_evidence_refs_is_invalid() -> None:
    _assert_violation(["PASS_REQUIRES_EVIDENCE"], {"result": "PASS", "evidence_refs": []}, "PASS_WITHOUT_EVIDENCE_REFS")


def test_pass_with_empty_evidence_ref_is_invalid() -> None:
    _assert_violation(["PASS_REQUIRES_EVIDENCE"], {"result": "PASS", "evidence_refs": ["  "]}, "PASS_EVIDENCE_REF_UNSPECIFIED")


def test_pass_with_real_evidence_refs_holds() -> None:
    _assert_holds(["PASS_REQUIRES_EVIDENCE"], {"result": "PASS", "evidence_refs": ["reports/implementation/plan_005/P5_A1_DELEGATION_POLICY_EVIDENCE.json"]})


def test_non_pass_results_do_not_require_evidence() -> None:
    for result in ("LIMITATION", "BLOCKED", "COMPLETED_WITH_FINDINGS"):
        assert verify_all_invariants({"result": result, "evidence_refs": []}) == []


# --- Controlled demos ---

def test_demo_with_promotion_flags_is_blocked() -> None:
    _assert_violation(["CONTROLLED_DEMO_NOT_PROMOTION"], {"demonstration_class": "CONTROLLED_TECHNICAL_HARNESS_E2E", "real_operational_subagents_promotion": True}, "PROMOTION_FLAG")
    _assert_violation(["CONTROLLED_DEMO_NOT_PROMOTION"], {"demonstration_class": "CONTROLLED_TECHNICAL_HARNESS_E2E", "real_multiagent_runtime_promotion": True}, "PROMOTION_FLAG")
    _assert_violation(["CONTROLLED_DEMO_NOT_PROMOTION"], {"demonstration_class": "CONTROLLED_TECHNICAL_HARNESS_E2E", "functional_readiness_claim": True}, "PROMOTION_FLAG")


def test_controlled_demo_without_promotion_holds() -> None:
    _assert_holds(
        ["CONTROLLED_DEMO_NOT_PROMOTION"],
        {"demonstration_class": "CONTROLLED_TECHNICAL_HARNESS_E2E", "real_operational_subagents_promotion": False, "real_multiagent_runtime_promotion": False, "functional_readiness_claim": False, "real_product_operation": False},
    )


# --- Routing ---

def test_route_outside_authorized_candidate_set_blocks() -> None:
    _assert_violation(["ROUTING_INSIDE_AUTHORIZED_SET"], {"status": "SELECTED", "candidate_set": ["local_profile"], "selected_profile": "paid_profile"}, "ROUTING_OUTSIDE_AUTHORIZED_SET")


def test_route_selected_without_profile_blocks() -> None:
    _assert_violation(["ROUTING_INSIDE_AUTHORIZED_SET"], {"status": "SELECTED", "candidate_set": ["local_profile"], "selected_profile": ""}, "ROUTING_SELECTED_WITHOUT_PROFILE")


def test_route_within_candidate_set_holds() -> None:
    _assert_holds(["ROUTING_INSIDE_AUTHORIZED_SET"], {"status": "SELECTED", "candidate_set": ["local_profile", "reasoning_profile"], "selected_profile": "local_profile"})


def test_recommend_or_blocked_do_not_select() -> None:
    for status in ("RECOMMEND_ONLY", "BLOCKED"):
        assert verify_all_invariants({"status": status, "candidate_set": ["local_profile"], "selected_profile": "paid_profile"}) == []


# --- Increment authorization ---

def test_increment_pass_does_not_authorize_next() -> None:
    _assert_violation(["NO_IMPLICIT_INCREMENT_AUTHORIZATION"], {"increment_result": "PASS", "next_authorized": True}, "INCREMENT_RESULT_GRANTS_NEXT_AUTHORIZATION")


def test_increment_pass_without_next_authorization_holds() -> None:
    _assert_holds(["NO_IMPLICIT_INCREMENT_AUTHORIZATION"], {"increment_result": "PASS", "next_authorized": False})


def test_unknown_invariant_is_fail_closed() -> None:
    _assert_violation(["INVARIANT_DOES_NOT_EXIST"], {}, "UNKNOWN_INVARIANT")
