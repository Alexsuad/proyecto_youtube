"""T2-D — context/output economy + product impact check tests (PLAN 006 §10D)."""
import pytest

from src.core.context_output_economy import (
    EXPANSION_TRIGGERS,
    ConsumerRegistration,
    ContextPlan,
    ReviewerDelegation,
    build_reviewer_delegation,
    compress_parent_output,
    plan_minimal_context,
    product_impact_guard,
    run_product_impact_check,
)


class TestContextEconomy:
    def test_plan_minimal_starts_minimal(self):
        plan = plan_minimal_context(["plans/001_CONTROL_OPERATIVO.md", "docs/product/MVP_BASELINE.md"])
        assert plan.context_kind == "MINIMAL_CONTEXT"
        assert plan.minimal is True

    def test_plan_expands_only_on_valid_trigger(self):
        plan = plan_minimal_context(
            ["plans/001_CONTROL_OPERATIVO.md"],
            expand_on=["MATERIAL_TEST_FAILURE"],
        )
        assert plan.context_kind == "EXPANDED_CONTEXT"
        assert plan.expansion_triggers == ("MATERIAL_TEST_FAILURE",)
        assert plan.minimal is False

    def test_invalid_trigger_rejected(self):
        with pytest.raises(ValueError, match="UNKNOWN_EXPANSION_TRIGGER"):
            plan_minimal_context(["authority"], expand_on=["WHIM"])

    def test_expand_method_accepts_only_known_triggers(self):
        plan = ContextPlan(context_kind="MINIMAL_CONTEXT", base_surface=("authority",))
        with pytest.raises(ValueError, match="UNKNOWN_EXPANSION_TRIGGER"):
            plan.expand("INVALIDATED_CURIOSITY", "no")

    def test_all_required_triggers_are_defined(self):
        expected = {
            "CONTRADICTION",
            "MISSING_DEPENDENCY",
            "INSUFFICIENT_EVIDENCE",
            "UNRESOLVED_REFERENCE",
            "MATERIAL_TEST_FAILURE",
        }
        assert set(EXPANSION_TRIGGERS) == expected


class TestDelegatedContext:
    def test_reviewer_gets_scoped_context_not_full_conversation(self):
        delegation = build_reviewer_delegation(
            mission_ref="PLAN_006_T2D",
            authority_ref="plans/001_CONTROL_OPERATIVO.md",
            diff_ref="git diff 29b5218..HEAD",
            invariant_ids=["CRITICAL_DOUBT_VALID_CLOSURE"],
            affected_files=["src/core/context_output_economy.py"],
            relevant_test_refs=["tests/core/test_plan_006_t2d_context_output_economy.py"],
            evidence_refs=["reports/implementation/plan_006/T2_D_CONTEXT_ECONOMY.json"],
        )
        assert delegation.inherited_conversation is False
        assert delegation.contaminated is False
        assert delegation.context_kind == "DELEGATED_CONTEXT"
        assert "conversation" not in delegation.__dict__ or delegation.inherited_conversation is False

    def test_contamination_detected(self):
        delegation = build_reviewer_delegation(
            mission_ref="M",
            authority_ref="A",
            diff_ref="D",
            invariant_ids=["X"],
            affected_files=["F"],
            relevant_test_refs=["T"],
            evidence_refs=["E"],
        )
        clean = delegation.__class__(**{**delegation.__dict__, "inherited_conversation": True})
        assert clean.contaminated is True


class TestOutputEconomy:
    def test_compress_parent_output_keeps_traceability(self):
        compact = compress_parent_output(
            outcome="PASS",
            exit_code=0,
            test_counts={"passed": 28, "failed": 0},
            failing_nodes=[],
            evidence_ref="reports/implementation/plan_006/T2_C_ADVERSARIAL_ASSURANCE.json",
            finding="T2-C invariants green",
            raw_log_ref="logs/plan_006_t2c.txt",
        )
        summary = compact.as_summary()
        assert summary["outcome"] == "PASS"
        assert summary["exit_code"] == 0
        assert summary["test_counts"] == {"passed": 28, "failed": 0}
        assert summary["failing_nodes"] == []
        assert summary["evidence_ref"].endswith("T2_C_ADVERSARIAL_ASSURANCE.json")
        assert summary["raw_log_ref"] == "logs/plan_006_t2c.txt"

    def test_raw_log_optional_by_reference(self):
        compact = compress_parent_output(
            outcome="PASS",
            exit_code=0,
            test_counts={"passed": 1},
            failing_nodes=[],
            evidence_ref=None,
            finding="ok",
        )
        assert compact.as_summary()["raw_log_ref"] is None


REGISTRATIONS = [
    ConsumerRegistration(
        surface="src/core/context_resolution.py",
        consumer="mission_preflight",
        functional_responsibility="ResolvedContextManifest exacto",
        regression_ref="tests/core/test_context_resolution.py",
    ),
    ConsumerRegistration(
        surface="src/core/evidence_freshness.py",
        consumer="technical_reviewer",
        functional_responsibility="fail-closed freshness",
        regression_ref="tests/core/test_evidence_freshness.py",
    ),
]


class TestProductImpactCheck:
    def test_touched_surface_with_known_consumers_passes(self):
        check = product_impact_guard(
            touched_surfaces=["src/core/context_resolution.py"],
            registrations=REGISTRATIONS,
        )
        assert check.checked is True
        assert check.fails_closed is False
        assert check.targeted_regression_refs == ("tests/core/test_context_resolution.py",)

    def test_touched_surface_without_consumers_fails_closed(self):
        check = product_impact_guard(
            touched_surfaces=["src/core/secret_unmapped.py"],
            registrations=REGISTRATIONS,
        )
        assert check.checked is False
        assert check.fails_closed is True
        assert "NO_KNOWN_CONSUMERS:src/core/secret_unmapped.py" in check.reason

    def test_unknown_resolution_fails_closed(self):
        check = run_product_impact_check(
            touched_surfaces=["src/core/context_resolution.py"],
            registrations=REGISTRATIONS,
            resolution="GUESSED",
        )
        assert check.checked is False
        assert check.fails_closed is True
        assert "UNKNOWN_RESOLUTION" in check.reason

    def test_multiple_surfaces_collect_responsibilities(self):
        check = run_product_impact_check(
            touched_surfaces=["src/core/context_resolution.py", "src/core/evidence_freshness.py"],
            registrations=REGISTRATIONS,
        )
        assert check.checked is True
        assert set(check.responsibilities_affected) == {
            "ResolvedContextManifest exacto",
            "fail-closed freshness",
        }
        assert len(check.consumers_known) == 2

    def test_not_an_audit(self):
        """Plan §10D.4: never becomes a complete audit. Untouched unmapped
        surfaces are not reported as defects."""
        check = run_product_impact_check(
            touched_surfaces=["src/core/context_resolution.py"],
            registrations=REGISTRATIONS,
        )
        assert check.checked is True
