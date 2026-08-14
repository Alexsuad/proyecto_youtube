"""T5 — measured OpenCode pilot tests: PLAN 006 closure check (PLAN 006 §13)."""
import json
from pathlib import Path

import pytest

from src.core.plan_006_closure_check import (
    CLOSURE_FAIL,
    CLOSURE_OK,
    ClosureReport,
    REQUIRED_INCREMENTS,
    run_closure_check,
)
from src.core.evidence_reuse import IntendedUse

ROOT = Path(__file__).resolve().parents[2]


class TestEvidenceIntegrity:
    def test_default_closure_requires_t5_and_d1(self):
        assert {"T5", "D1"}.issubset(REQUIRED_INCREMENTS)

    def test_current_t1_distinct_bindings_allow_final_closure(self):
        report = run_closure_check(ROOT, mission_id="PLAN_006_T5_PILOT")
        assert report.overall == CLOSURE_OK
        assert any(f.check == "HISTORICAL_COMPLETION" and f.status == CLOSURE_OK for f in report.findings)
        assert any(f.check == "EVIDENCE_T1" and f.status == CLOSURE_OK for f in report.findings)

    def test_reuse_decision_stays_fail_closed(self):
        report = run_closure_check(
            ROOT,
            mission_id="PLAN_006_T5_PILOT",
            verify_reuse_for="reports/implementation/plan_006/T0_BASELINE.json",
            intended_use=IntendedUse(
                scope="pilot",
                coverage_required="T0 baseline",
                intended_assurance="structural consistency of evidence envelope",
            ),
        )
        assert report.overall == CLOSURE_FAIL
        assert any(f.check == "EVIDENCE_REUSE" and f.status == CLOSURE_FAIL for f in report.findings)

    def test_forbidden_claims_never_true(self):
        for finding in run_closure_check(ROOT, mission_id="PLAN_006_T5_PILOT").findings:
            assert "MUST_NOT_BE_CLAIMED" not in finding.detail

    def test_reuse_unverifiable_fails_closed(self, tmp_path):
        report = run_closure_check(
            tmp_path,
            mission_id="PLAN_006_T5_PILOT",
            increments=["T0"],
            verify_reuse_for="reports/implementation/plan_006/T0_BASELINE.json",
            intended_use=IntendedUse(
                scope="pilot",
                coverage_required="T0 baseline",
                intended_assurance="structural consistency of evidence envelope",
            ),
        )
        assert report.overall == CLOSURE_FAIL
        assert any(f.check == "EVIDENCE_REUSE" and f.status == CLOSURE_FAIL for f in report.findings)

    def test_forbidden_claim_in_report_fails_closed(self, tmp_path):
        (tmp_path / "reports/implementation/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006" / "PLAN_006_T5_AUTHORIZATION.json").write_text("{}", encoding="utf-8")
        (tmp_path / "reports/implementation/plan_006" / "T0_BASELINE.json").write_text(
            json.dumps({"functional_approval_claim": True}), encoding="utf-8"
        )
        report = run_closure_check(tmp_path, mission_id="PLAN_006_T5_PILOT", increments=["T0"])
        assert report.overall == CLOSURE_FAIL
        assert any(f.check == "EVIDENCE_T0" and f.status == CLOSURE_FAIL for f in report.findings)

    def test_non_pass_report_fails_closed(self, tmp_path):
        (tmp_path / "reports/implementation/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006" / "PLAN_006_T5_AUTHORIZATION.json").write_text("{}", encoding="utf-8")
        (tmp_path / "reports/implementation/plan_006" / "T0_BASELINE.json").write_text(
            json.dumps({"result": "BLOCKED"}), encoding="utf-8"
        )
        report = run_closure_check(tmp_path, mission_id="PLAN_006_T5_PILOT", increments=["T0"])
        assert report.overall == CLOSURE_FAIL
        assert any("EVIDENCE_RESULT_NOT_PASS:BLOCKED" in f.detail for f in report.findings)

    def test_invalid_t1_fails_closed(self, tmp_path):
        (tmp_path / "reports/implementation/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006" / "PLAN_006_T5_AUTHORIZATION.json").write_text("{}", encoding="utf-8")
        for name in ("T0", "T1", "T2-A", "T2-B", "T2-C", "T2-D", "T3", "T4-0", "T4"):
            ref = {
                "T0": "T0_BASELINE",
                "T1": "T1_HISTORICAL_COMPLETION",
                "T2-A": "T2_A_EVIDENCE_REUSE",
                "T2-B": "T2_B_PROPORTIONAL_VERIFICATION",
                "T2-C": "T2_C_ADVERSARIAL_ASSURANCE",
                "T2-D": "T2_D_CONTEXT_OUTPUT_ECONOMY",
                "T3": "T3_PERMISSION_MODEL",
                "T4-0": "T4_0_GAP_ANALYSIS",
                "T4": "T4_RESOURCE_AWARE_DECISION",
            }[name]
            (tmp_path / "reports/implementation/plan_006" / f"{ref}.json").write_text(
                json.dumps({"artifact_id": f"PLAN_006_{name}"}), encoding="utf-8"
            )
        report = run_closure_check(tmp_path, mission_id="PLAN_006_T5_PILOT")
        assert report.overall == CLOSURE_FAIL
        assert any(f.check == "HISTORICAL_COMPLETION" and f.status == CLOSURE_FAIL for f in report.findings)


class TestFailClosed:
    def test_missing_evidence_fails_closed(self, tmp_path):
        report = run_closure_check(
            tmp_path,
            mission_id="PLAN_006_T5_PILOT",
            increments=["T0"],
        )
        assert report.overall == CLOSURE_FAIL
        assert any("EVIDENCE_UNREADABLE" in f.detail for f in report.findings)

    def test_missing_t5_authorization_fails_closed(self, tmp_path):
        report = run_closure_check(
            tmp_path,
            mission_id="PLAN_006_T5_PILOT",
            increments=["T0"],
        )
        assert any(f.check == "T5_AUTHORIZATION" and f.status == CLOSURE_FAIL for f in report.findings)

    def test_invalid_t5_authorization_fails_closed(self, tmp_path):
        (tmp_path / "plans/plan_006").mkdir(parents=True)
        (tmp_path / "plans/plan_006" / "PLAN_006_T5_AUTHORIZATION.json").write_text("{}", encoding="utf-8")
        report = run_closure_check(tmp_path, mission_id="PLAN_006_T5_PILOT", increments=[])
        assert report.overall == CLOSURE_FAIL
        assert any(f.check == "T5_AUTHORIZATION" and f.status == CLOSURE_FAIL for f in report.findings)

    def test_t5_and_d1_evidence_are_required(self, tmp_path):
        (tmp_path / "plans/plan_006").mkdir(parents=True)
        report = run_closure_check(tmp_path, mission_id="PLAN_006_T5_PILOT", increments=["T5", "D1"])
        assert report.overall == CLOSURE_FAIL
        assert {f.check for f in report.findings if f.status == CLOSURE_FAIL} >= {"EVIDENCE_T5", "EVIDENCE_D1"}


class TestReportShape:
    def test_report_exposes_structured_findings(self):
        report = run_closure_check(ROOT, mission_id="PLAN_006_T5_PILOT")
        data = report.to_dict()
        assert data["mission_id"] == "PLAN_006_T5_PILOT"
        assert data["overall"] in {CLOSURE_OK, CLOSURE_FAIL}
        assert isinstance(data["findings"], list)
        assert all("check" in item and "status" in item for item in data["findings"])

    def test_closure_check_does_not_create_authority(self):
        report = run_closure_check(ROOT, mission_id="PLAN_006_T5_PILOT")
        # Pilot deliverable never claims functional/product readiness
        for finding in report.findings:
            assert "FUNCTIONAL_APPROVAL" not in finding.detail
            assert "PRODUCT_READINESS" not in finding.detail
