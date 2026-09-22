from __future__ import annotations

from copy import deepcopy

import pytest

from src.core.contract_validation import (
    validate_editorial_edit_report,
    validate_final_editorial_audit,
    validate_against_schema,
)
from tests.core.test_all_schemas import VALID_FIXTURES


def _audit() -> dict:
    return deepcopy(VALID_FIXTURES["final_editorial_audit"])


def _edit_report() -> dict:
    return deepcopy(VALID_FIXTURES["editorial_edit_report"])


def test_final_audit_rejects_empty_material_field_and_unsupported_pass() -> None:
    audit = _audit()
    audit["profile_compliance"] = ""
    audit["dimension_evidence"]["opening_quality"] = {}

    schema_violations = validate_against_schema(audit, "final_editorial_audit")
    violations = validate_final_editorial_audit(audit)

    assert schema_violations
    assert any("profile_compliance" in violation for violation in violations)
    assert any("opening_quality" in violation for violation in violations)


def test_final_audit_requires_justification_for_na_dimension() -> None:
    audit = _audit()
    audit["opening_quality"] = "N/A_JUSTIFIED"
    audit["dimension_evidence"]["opening_quality"] = {
        "observation": "No aplica al formato de prueba.",
    }

    schema_violations = validate_against_schema(audit, "final_editorial_audit")
    violations = validate_final_editorial_audit(audit)

    assert schema_violations
    assert any("N/A_JUSTIFIED" in violation for violation in violations)


@pytest.mark.parametrize("decision", ["PASS", "WARN"])
@pytest.mark.parametrize("dimension_state", ["BLOCK", "REQUEST_CHANGES"])
def test_final_audit_rejects_incoherent_overall_decision(decision: str, dimension_state: str) -> None:
    audit = _audit()
    audit["decision"] = decision
    audit["viewer_journey"] = dimension_state

    violations = validate_final_editorial_audit(audit)

    assert any(f"decision={decision}" in violation for violation in violations)
    assert any("viewer_journey" in violation for violation in violations)


def test_final_audit_schema_requires_support_for_each_material_field() -> None:
    audit = _audit()
    del audit["dimension_evidence"]["opening_quality"]

    violations = validate_against_schema(audit, "final_editorial_audit")

    assert violations


def test_final_audit_accepts_qualitative_support() -> None:
    assert validate_against_schema(_audit(), "final_editorial_audit") == []
    assert validate_final_editorial_audit(_audit()) == []

    warn_audit = _audit()
    warn_audit["decision"] = "WARN"
    assert validate_final_editorial_audit(warn_audit) == []


def test_final_audit_accepts_justified_na_dimension() -> None:
    audit = _audit()
    audit["opening_quality"] = "N/A_JUSTIFIED"
    audit["dimension_evidence"]["opening_quality"] = {
        "justification": "El formato de prueba no contiene una apertura separada."
    }

    assert validate_against_schema(audit, "final_editorial_audit") == []
    assert validate_final_editorial_audit(audit) == []


@pytest.mark.parametrize(
    "changes",
    [
        {"structure": True},
        {"structure": [""]},
        {"structure": []},
        {"structure": ""},
    ],
)
def test_edit_report_rejects_non_descriptive_changes(changes: dict) -> None:
    report = _edit_report()
    report["changes_by_category"] = changes

    schema_violations = validate_against_schema(report, "editorial_edit_report")
    violations = validate_editorial_edit_report(report)

    assert schema_violations
    assert violations


def test_edit_report_requires_documented_changes_or_justified_no_change() -> None:
    report = _edit_report()
    report["changes_by_category"] = {}
    assert validate_against_schema(report, "editorial_edit_report")
    assert validate_editorial_edit_report(report)

    report["edit_type"] = "NO_CHANGE"
    report["no_change_justification"] = "El guion ya cumple sin cambios materiales."
    report["changes_by_category"] = {}
    assert validate_against_schema(report, "editorial_edit_report") == []
    assert validate_editorial_edit_report(report) == []

    report["changes_by_category"] = {"structure": "Se reescribió toda la apertura."}
    assert validate_against_schema(report, "editorial_edit_report")
    assert validate_editorial_edit_report(report)

    del report["no_change_justification"]
    assert validate_against_schema(report, "editorial_edit_report")
    assert validate_editorial_edit_report(report)
