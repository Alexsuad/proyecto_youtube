"""T4 — resource-aware orchestration decision tests (PLAN 006 §12)."""
import pytest

from src.core.resource_aware_decision import (
    DELEGATE,
    ESCALATE,
    INLINE,
    REVIEW_LEVELS,
    ExecutionDecision,
    make_execution_decision,
)

from src.core.delegation_policy import DelegationDecision


def _task(**overrides):
    task = {
        "trivial": True,
        "deterministic": True,
        "separable": False,
        "risk": "LOW",
        "sensitive": False,
        "findings": False,
        "touched_surface": "src/core/lean_measurement.py",
        "targeted_covers_consumers": True,
        "shared_utility": False,
        "schema_consumers": 0,
        "core_harness_touched": False,
        "repair_showed_broad_damage": False,
        "closure_needs_distinct_evidence": False,
        "authorized_candidate_set": [],
        "delegation_depth": 0,
        "max_delegation_depth": 1,
    }
    task.update(overrides)
    return task


class TestTopologySelection:
    def test_small_low_risk_task_selects_inline(self):
        decision = make_execution_decision(task=_task())
        assert decision.topology == INLINE
        assert decision.review_floor == "SELF_ONLY"

    def test_delegate_only_with_authorized_candidate(self):
        injected = DelegationDecision(
            DELEGATE,
            ("DELEGATION_REDUCES_CONTEXT_OR_SPECIALIZES_WORK",),
            "1.0.0",
            evidence_refs=(),
            candidate_capability_id="SPECIALIST",
            delegation_depth=1,
            authorized_candidate_set=("SPECIALIST",),
        )
        decision = make_execution_decision(task=_task(), delegation=injected)
        assert decision.topology == DELEGATE

    def test_caller_booleans_never_grant_delegation(self):
        decision = make_execution_decision(
            task=_task(
                trivial=False,
                deterministic=False,
                separable=True,
                scope_authorized=True,
                delegation_authorized=True,
                capability_available=True,
                candidate_capability_id="SPECIALIST",
                authorized_candidate_set=["SPECIALIST"],
            )
        )
        assert decision.topology != DELEGATE

    def test_out_of_authority_task_escalates(self):
        decision = make_execution_decision(
            task=_task(
                trivial=False,
                deterministic=False,
                separable=True,
                delegation_authorized=False,
            )
        )
        assert decision.topology == ESCALATE

    def test_invalid_topology_rejected(self):
        with pytest.raises(ValueError, match="UNKNOWN_TOPOLOGY"):
            make_execution_decision(
                task=_task(),
                delegation=DelegationDecision("BOGUS", ("x",), "1.0.0"),
            )


class TestReviewFloor:
    def test_review_floor_never_downgrades(self):
        decision = make_execution_decision(task=_task(required_review="INDEPENDENT_REVIEW"))
        assert decision.review_floor in REVIEW_LEVELS
        assert decision.review_floor == "INDEPENDENT_REVIEW"

    def test_high_risk_elevates_to_independent(self):
        decision = make_execution_decision(task=_task(risk="HIGH"))
        assert decision.review_floor == "INDEPENDENT_REVIEW"

    def test_owner_required_elevates(self):
        decision = make_execution_decision(task=_task(owner_required=True))
        assert decision.review_floor == "OWNER_REVIEW"


class TestVerificationBudget:
    def test_verification_plan_is_proportional(self):
        decision = make_execution_decision(task=_task())
        assert decision.verification_steps[0] == "DIRECT_CHECK_OR_ADVERSARIAL_INVARIANT"
        assert decision.verification_steps[-1] == "GIT_DIFF_CHECK"

    def test_broader_only_when_justified(self):
        decision = make_execution_decision(
            task=_task(shared_utility=True, schema_consumers=3)
        )
        assert "BROADER_SUITE" in decision.verification_steps

    def test_materiality_exposed_for_owner_decision(self):
        decision = make_execution_decision(task=_task())
        assert decision.verification_materiality in (
            "DIRECT_IMPACT",
            "PARTIAL_DEPENDENCY_IMPACT",
            "FULL_REASSESSMENT_REQUIRED",
            "NO_MATERIAL_IMPACT",
        )


class TestLowestSufficientRoute:
    def test_profile_traceable_when_observable(self):
        decision = make_execution_decision(
            task=_task(
                execution_profile_id="PROFILE_FAST",
                authorized_candidate_set=["PROFILE_FAST"],
                owner_route_selection_authority=False,
            )
        )
        assert decision.profile_traceability == "TRACEABLE"

    def test_profile_not_observable_when_absent(self):
        decision = make_execution_decision(task=_task())
        assert decision.profile_traceability == "NOT_OBSERVABLE"

    def test_authorized_route_is_selected_when_owner_delegates_selection(self):
        decision = make_execution_decision(
            task=_task(
                authorized_candidate_set=["PROFILE_FAST"],
                execution_profile_id="PROFILE_FAST",
                owner_route_selection_authority=False,
            )
        )
        assert decision.routing_status == "SELECTED"
        assert decision.selected_profile == "PROFILE_FAST"
        assert decision.profile_traceability == "TRACEABLE"

    def test_profile_outside_authorized_set_blocks_route(self):
        decision = make_execution_decision(
            task=_task(
                authorized_candidate_set=["PROFILE_FAST"],
                execution_profile_id="PROFILE_SLOW",
            )
        )
        assert decision.routing_status == "BLOCKED"
        assert decision.selected_profile is None


class TestContextBudget:
    def test_context_budget_is_exposed(self):
        decision = make_execution_decision(task=_task(resolved_context_size=128, context_budget_bytes=64))
        assert decision.context_budget_status == "BUDGET_EXCEEDED"
        assert "CONTEXT_BUDGET_EXCEEDED" in decision.reasons

    def test_context_budget_within_limit(self):
        decision = make_execution_decision(task=_task(resolved_context_size=64, context_budget_bytes=64))
        assert decision.context_budget_status == "WITHIN_BUDGET"


class TestSequentialVsParallel:
    def test_parallel_only_when_independent_and_delegated(self):
        injected = DelegationDecision(
            DELEGATE,
            ("DELEGATION_REDUCES_CONTEXT_OR_SPECIALIZES_WORK",),
            "1.0.0",
            evidence_refs=(),
            candidate_capability_id="SPECIALIST",
            delegation_depth=1,
            authorized_candidate_set=("SPECIALIST",),
        )
        decision = make_execution_decision(
            task=_task(parallelizable=True),
            delegation=injected,
        )
        assert decision.sequential_or_parallel == "PARALLEL"

    def test_inline_is_sequential(self):
        decision = make_execution_decision(task=_task(parallelizable=True))
        assert decision.sequential_or_parallel == "SEQUENTIAL"


class TestDecisionShape:
    def test_decision_is_reproducible_and_structured(self):
        first = make_execution_decision(task=_task()).to_dict()
        second = make_execution_decision(task=_task()).to_dict()
        assert first == second
        assert "topology" in first
        assert "review_floor" in first
        assert "verification_materiality" in first
        assert "decision_order" in first

    def test_evidence_reuse_observation_carried(self):
        decision = make_execution_decision(task=_task(evidence_reuse_decision="REUSE"))
        assert decision.evidence_reuse_decision == "REUSE"

    def test_no_new_functional_authority_created(self):
        decision = make_execution_decision(task=_task())
        assert decision.topology in (INLINE, DELEGATE, ESCALATE)
        assert decision.review_floor in REVIEW_LEVELS
