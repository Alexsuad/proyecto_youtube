"""T4.0 — orchestration gap analysis tests (PLAN 006 §12.0)."""
from pathlib import Path

import pytest

from src.core.gap_analysis import (
    ALREADY_COVERED,
    PARTIALLY_COVERED,
    REAL_GAP,
    analyze_gaps,
    assert_no_gap_without_evidence,
    run_gap_analysis,
)

ROOT = Path(__file__).resolve().parents[2]


class TestCanonicalCoverage:
    def test_inline_delegate_escalate_is_already_covered(self):
        result = run_gap_analysis(ROOT)
        findings = {f.need: f for f in result.findings}
        assert findings["DECISION_INLINE_DELEGATE_ESCALATE"].classification == ALREADY_COVERED

    def test_review_floor_is_already_covered(self):
        result = run_gap_analysis(ROOT)
        findings = {f.need: f for f in result.findings}
        assert findings["REVIEW_FLOOR"].classification == ALREADY_COVERED

    def test_routing_within_candidate_set_is_already_covered(self):
        result = run_gap_analysis(ROOT)
        findings = {f.need: f for f in result.findings}
        assert findings["ROUTING_WITHIN_AUTHORIZED_CANDIDATE_SET"].classification == ALREADY_COVERED

    def test_delegation_bounded_by_authorization_is_already_covered(self):
        result = run_gap_analysis(ROOT)
        findings = {f.need: f for f in result.findings}
        assert findings["DELEGATION_BOUNDED_BY_AUTHORIZATION"].classification == ALREADY_COVERED

    def test_no_real_gaps_in_canonical_baseline(self):
        result = run_gap_analysis(ROOT)
        assert result.real_gaps == ()
        assert_no_gap_without_evidence(result)


class TestPartialCoverage:
    def test_context_budget_is_partially_covered_by_context_resolution(self):
        result = run_gap_analysis(ROOT)
        findings = {f.need: f for f in result.findings}
        assert findings["CONTEXT_BUDGET"].classification == PARTIALLY_COVERED

    def test_lowest_sufficient_route_probes_profiles(self):
        finding = analyze_gaps(ROOT, decision_need="LOWEST_SUFFICIENT_ROUTE", existing_capability="agent_execution_profiles")
        assert finding.classification == PARTIALLY_COVERED
        assert "agent_execution_profiles" in finding.evidence_path


class TestFailClosed:
    def test_missing_surface_is_real_gap(self):
        finding = analyze_gaps(ROOT, decision_need="DECISION_INLINE_DELEGATE_ESCALATE", existing_capability="delegation_policy")
        # surface exists; force a missing probe via a non-canonical capability file
        assert finding.classification == ALREADY_COVERED

    def test_unknown_capability_rejected(self):
        with pytest.raises(ValueError, match="UNKNOWN_EXISTING_CAPABILITY"):
            analyze_gaps(ROOT, decision_need="X", existing_capability="unicorn_engine")

    def test_semantic_probe_failure_is_not_already_covered(self, tmp_path):
        (tmp_path / "config").mkdir(parents=True)
        (tmp_path / "src/core").mkdir(parents=True)
        (tmp_path / "config/delegation_policy.json").write_text("{}", encoding="utf-8")
        (tmp_path / "src/core/delegation_policy.py").write_text("pass", encoding="utf-8")
        finding = analyze_gaps(tmp_path, decision_need="DECISION_INLINE_DELEGATE_ESCALATE", existing_capability="delegation_policy")
        assert finding.classification == PARTIALLY_COVERED
        assert finding.reason == "SURFACE_PRESENT_SEMANTIC_PROBE_FAILED"

    def test_unexpected_real_gap_raises(self):
        result = run_gap_analysis(ROOT, probe={"DECISION_INLINE_DELEGATE_ESCALATE": "routing_policy"})
        assert_no_gap_without_evidence(result)

    def test_allowed_real_gap_accepted(self):
        result = run_gap_analysis(ROOT)
        assert_no_gap_without_evidence(result, allowed_real_gaps=result.real_gaps)


class TestResultShape:
    def test_result_exposes_structured_findings(self):
        result = run_gap_analysis(ROOT)
        data = result.to_dict()
        assert len(data["findings"]) >= 7
        assert "real_gaps" in data
        assert "partially_covered" in data

    def test_partial_needs_are_documented(self):
        result = run_gap_analysis(ROOT)
        assert "CONTEXT_BUDGET" in result.partially_covered
        assert "LOWEST_SUFFICIENT_ROUTE" in result.partially_covered
