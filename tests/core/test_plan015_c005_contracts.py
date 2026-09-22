from __future__ import annotations

from copy import deepcopy

from src.core.contract_validation import (
    validate_editorial_edit_report,
    validate_final_editorial_audit,
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

    violations = validate_final_editorial_audit(audit)

    assert any("profile_compliance" in violation for violation in violations)
    assert any("opening_quality" in violation for violation in violations)


def test_final_audit_requires_justification_for_na_dimension() -> None:
    audit = _audit()
    audit["opening_quality"] = "N/A_JUSTIFIED"
    audit["dimension_evidence"]["opening_quality"] = {
        "observation": "No aplica al formato de prueba.",
    }

    violations = validate_final_editorial_audit(audit)

    assert any("N/A_JUSTIFIED" in violation for violation in violations)


def test_final_audit_accepts_qualitative_support() -> None:
    assert validate_final_editorial_audit(_audit()) == []


def test_edit_report_requires_documented_changes_or_justified_no_change() -> None:
    report = _edit_report()
    report["changes_by_category"] = {}
    assert validate_editorial_edit_report(report)

    report["edit_type"] = "NO_CHANGE"
    report["no_change_justification"] = "El guion ya cumple sin cambios materiales."
    report["changes_by_category"] = {}
    assert validate_editorial_edit_report(report) == []

    del report["no_change_justification"]
    assert validate_editorial_edit_report(report)
