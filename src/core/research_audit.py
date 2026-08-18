"""Technical contract and routing checks for independent research audits.

This module validates independence and correction routing only. Functional audit
criteria remain owned by SCRIPT_PRODUCT and are carried as opaque criterion IDs.
"""
from __future__ import annotations

from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.invalidation import InvalidationEngine


def validate_independent_research_audit(data: dict[str, Any]) -> list[str]:
    """Validate structure, independence and origin-preserving correction routes."""
    violations = [f"SCHEMA_INVALID:{item}" for item in validate_against_schema(data, "independent_research_audit")]
    if violations:
        return violations

    producer = data["producer"]
    auditor = data["auditor"]
    if producer["run_id"] == auditor["run_id"]:
        violations.append("AUDITOR_EQUALS_PRODUCER_RUN")
    if producer["actor_id"] == auditor["actor_id"]:
        violations.append("AUDITOR_EQUALS_PRODUCER_ACTOR")
    if data["independence_result"] != "PASS":
        violations.append("INDEPENDENCE_NOT_PASSED")

    artifact_runs = {item["producer_run_id"] for item in data["audited_artifacts"]}
    declared_producer_run = producer["run_id"]
    if declared_producer_run == "MULTIPLE_PRODUCER_RUNS":
        if len(artifact_runs) < 2:
            violations.append("PRODUCER_RUN_DECLARATION_MULTIPLE_WITHOUT_MULTIPLE_ARTIFACT_RUNS")
    elif artifact_runs != {declared_producer_run}:
        violations.append("AUDITED_ARTIFACT_PRODUCER_RUN_MISMATCH")

    defect_ids = [item["defect_id"] for item in data["defects"]]
    route_ids = [item["defect_id"] for item in data["correction_routes"]]
    if len(defect_ids) != len(set(defect_ids)):
        violations.append("DUPLICATE_DEFECT_ID")
    if len(route_ids) != len(set(route_ids)):
        violations.append("DUPLICATE_CORRECTION_ROUTE_DEFECT_ID")
    defects_by_id = {item["defect_id"]: item for item in data["defects"]}
    routes_by_id = {item["defect_id"]: item for item in data["correction_routes"]}
    missing_routes = sorted(set(defects_by_id) - set(routes_by_id))
    violations.extend(f"CORRECTION_ROUTE_MISSING:{defect_id}" for defect_id in missing_routes)
    for route in data["correction_routes"]:
        defect = defects_by_id.get(route["defect_id"])
        if defect is None:
            violations.append(f"CORRECTION_ROUTE_WITHOUT_DEFECT:{route['defect_id']}")
            continue
        if route["origin_artifact"] != defect["origin_artifact"]:
            violations.append(f"CORRECTION_ROUTE_ORIGIN_MISMATCH:{route['defect_id']}")
        if route["defect_type"] != defect["defect_type"]:
            violations.append(f"CORRECTION_ROUTE_DEFECT_TYPE_MISMATCH:{route['defect_id']}")
        if route["severity"] != defect["severity"]:
            violations.append(f"CORRECTION_ROUTE_SEVERITY_MISMATCH:{route['defect_id']}")
    pending_findings = {"NOT_SATISFIED", "UNRESOLVED"}
    if data["decision"] == "PASS" and any(item["status"] in pending_findings for item in data["findings"]):
        violations.append("PASS_WITH_PENDING_FINDINGS")
    if data["decision"] == "PASS" and data["defects"]:
        violations.append("PASS_WITH_PENDING_DEFECTS")
    return sorted(set(violations))


def resolve_correction_routes(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return validated route copies without mutating audited producer artifacts."""
    violations = validate_independent_research_audit(data)
    if violations:
        raise ValueError("INDEPENDENT_RESEARCH_AUDIT_INVALID:" + ";".join(violations))
    engine = InvalidationEngine()
    return [engine.resolve_correction_route(route) for route in data["correction_routes"]]
