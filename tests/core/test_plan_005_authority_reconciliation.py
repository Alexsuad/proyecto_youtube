"""Brecha 10 — reconciliation between PLAN 005 workload authorities and the canonical mission authority.

These tests prove that the workload decisions (review and routing) are bounded
by the canonical authorities (mission_convergence.required_review_stage and the
authorized candidate set), never inventing a parallel authority.
"""
from __future__ import annotations

import pytest

from src.core.mission_convergence import required_review_stage
from src.core.review_workload import assert_no_review_downgrade, choose_review_workload
from src.core.routing_policy import assert_route_resolution_authorized, choose_authorized_route


def test_workload_respects_convergence_owner_floor() -> None:
    policy = {"required_review": "OWNER_REVIEW"}
    stage = required_review_stage(policy)
    assert stage == "OWNER_REVIEW"
    decision = choose_review_workload(policy, required_review=stage)
    assert decision["review_level"] == "OWNER_REVIEW"
    assert "RECONCILED_WITH_MISSION_REVIEW_AUTHORITY" in decision["reasons"]


def test_workload_escalated_above_floor_is_never_downgraded() -> None:
    stage = required_review_stage({"required_review": "SELF_ONLY"})
    decision = choose_review_workload(sensitive=True, required_review=stage)
    assert decision["review_level"] == "INDEPENDENT_REVIEW"


def test_workload_cannot_silently_downgrade_convergence_floor() -> None:
    stage = required_review_stage({"required_review": "INDEPENDENT_REVIEW"}, sensitive_change=False)
    decision = choose_review_workload(sensitive=False, findings=False, required_review=stage)
    assert decision["review_level"] == "INDEPENDENT_REVIEW"
    assert "ELEVATED_TO_MISSION_REVIEW_FLOOR" in decision["reasons"]


def test_workload_policy_origin_reconciled_with_default() -> None:
    stage = required_review_stage({"required_review": "INDEPENDENT_REVIEW"})
    decision = choose_review_workload({"review_origin": "INTERNAL"}, required_review=stage)
    assert decision["review_level"] == "INDEPENDENT_REVIEW"


def test_assert_no_review_downgrade_is_canonical_reconciliation_guard() -> None:
    with pytest.raises(PermissionError, match="REVIEW_POLICY_DOWNGRADE_FORBIDDEN"):
        assert_no_review_downgrade("OWNER_REVIEW", "INDEPENDENT_REVIEW")
    assert_no_review_downgrade("INDEPENDENT_REVIEW", "INDEPENDENT_REVIEW")


def test_route_reconciliation_bounds_resolved_provider() -> None:
    route = assert_route_resolution_authorized(
        resolved_provider="mock",
        provider_to_route={"mock": "local_model"},
        authorized_candidate_set=["local_model"],
    )
    assert route == "local_model"


def test_route_reconciliation_blocks_unknown_provider_fail_closed() -> None:
    with pytest.raises(PermissionError, match="ROUTE_RESOLUTION_UNKNOWN_PROVIDER_ROUTE"):
        assert_route_resolution_authorized(
            resolved_provider="ghost",
            provider_to_route={"mock": "local_model"},
            authorized_candidate_set=["local_model"],
        )


def test_route_reconciliation_blocks_provider_outside_candidate_set() -> None:
    with pytest.raises(PermissionError, match="ROUTE_RESOLUTION_OUTSIDE_AUTHORIZED_CANDIDATE_SET"):
        assert_route_resolution_authorized(
            resolved_provider="mock",
            provider_to_route={"mock": "api_model"},
            authorized_candidate_set=["local_model"],
        )


def test_route_reconciliation_requires_authorized_candidate_set() -> None:
    with pytest.raises(PermissionError, match="ROUTE_RESOLUTION_UNVERIFIABLE_WITHOUT_AUTHORIZED_CANDIDATE_SET"):
        assert_route_resolution_authorized(
            resolved_provider="mock",
            provider_to_route={"mock": "local_model"},
            authorized_candidate_set=[],
        )


def test_route_reconciliation_rejects_profile_outside_candidate_set() -> None:
    with pytest.raises(PermissionError, match="ROUTE_RESOLUTION_OUTSIDE_AUTHORIZED_CANDIDATE_SET"):
        assert_route_resolution_authorized(
            resolved_provider="mock",
            provider_to_route={"mock": "local_model"},
            authorized_candidate_set=["local_model"],
            requested_profile="paid_profile",
        )


def test_route_reconciliation_consistent_with_policy_decision() -> None:
    decision = choose_authorized_route(candidate_set=["local_model"], owner_selection_authority=False)
    assert decision["status"] == "SELECTED"
    route = assert_route_resolution_authorized(
        resolved_provider="mock",
        provider_to_route={"mock": "local_model"},
        authorized_candidate_set=["local_model"],
    )
    assert route == decision["selected_profile"]
