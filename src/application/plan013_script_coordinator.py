"""Deterministic coordinator for the PLAN013 editorial script handoff.

This module only assembles, validates, and traces handoffs.  It does not select
editorial outcomes, invoke providers, approve a script, or create a lifecycle.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from src.core.contract_validation import (
    validate_against_schema,
    validate_editorial_edit_report,
    validate_final_editorial_audit,
)


class ScriptCoordinatorError(ValueError):
    """A required handoff is missing, stale, or internally inconsistent."""


def _checksum(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _require_object(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScriptCoordinatorError(f"{name} must be an object")
    return value


def _validate_schema(name: str, value: dict[str, Any]) -> None:
    violations = validate_against_schema(value, name)
    if violations:
        raise ScriptCoordinatorError(f"{name} invalid: {'; '.join(violations)}")


def coordinate_script_pipeline(
    *,
    episode_id: str,
    narrative_plan: dict[str, Any],
    thesis_artifact: dict[str, Any],
    script_draft: dict[str, Any],
    edited_script: dict[str, Any],
    edit_report: dict[str, Any],
    final_audit: dict[str, Any],
    producer_run_id: str,
    editor_run_id: str,
    auditor_run_id: str,
) -> dict[str, Any]:
    """Validate one synthetic editorial graph and return its trace.

    The coordinator deliberately treats audit decisions as data.  A failed or
    blocked audit is routed to the declared correction owner; it is never
    converted into approval by this function.
    """
    if not episode_id:
        raise ScriptCoordinatorError("episode_id is required")
    if not producer_run_id or not editor_run_id or not auditor_run_id:
        raise ScriptCoordinatorError("producer, editor, and auditor run references are required")
    if len({producer_run_id, editor_run_id, auditor_run_id}) != 3:
        raise ScriptCoordinatorError("producer, editor, and auditor runs must be independent")

    plan = _require_object("narrative_plan", narrative_plan)
    thesis = _require_object("thesis_artifact", thesis_artifact)
    draft = _require_object("script_draft", script_draft)
    edited = _require_object("edited_script", edited_script)
    report = _require_object("editorial_edit_report", edit_report)
    audit = _require_object("final_editorial_audit", final_audit)

    for name, artifact in (("narrative_plan", plan), ("thesis_artifact", thesis), ("script_draft", draft), ("edited_script", edited)):
        if artifact.get("episode_id") != episode_id:
            raise ScriptCoordinatorError(f"{name} episode_id does not match coordinator episode_id")
    if report.get("episode_id", episode_id) != episode_id or audit.get("episode_id", episode_id) != episode_id:
        raise ScriptCoordinatorError("review artifacts episode_id does not match coordinator episode_id")

    thesis_id = thesis.get("thesis_id")
    thesis_version = thesis.get("artifact_version") or thesis.get("version")
    thesis_checksum = thesis.get("checksum")
    binding = draft.get("thesis_binding")
    edited_binding = edited.get("thesis_binding")
    for label, candidate in (("script_draft", binding), ("edited_script", edited_binding)):
        if not isinstance(candidate, dict) or candidate.get("thesis_id") != thesis_id:
            raise ScriptCoordinatorError(f"{label} thesis binding is missing or stale")
        if thesis_version and candidate.get("artifact_version") != thesis_version:
            raise ScriptCoordinatorError(f"{label} thesis version is stale")
        if thesis_checksum and candidate.get("checksum") != thesis_checksum:
            raise ScriptCoordinatorError(f"{label} thesis checksum is stale")

    _validate_schema("script_draft", draft)
    _validate_schema("edited_script", edited)
    _validate_schema("editorial_edit_report", report)
    _validate_schema("final_editorial_audit", audit)
    report_violations = validate_editorial_edit_report(report, check_schema=False)
    if report_violations:
        raise ScriptCoordinatorError("editorial_edit_report invalid: " + "; ".join(report_violations))
    audit_violations = validate_final_editorial_audit(audit, check_schema=False)
    if audit_violations:
        raise ScriptCoordinatorError("final_editorial_audit invalid: " + "; ".join(audit_violations))

    if report.get("input_artifact_id") != draft.get("script_id") or report.get("output_artifact_id") != edited.get("script_id"):
        raise ScriptCoordinatorError("edit report does not identify its input and output scripts")
    if report.get("input_version") != draft.get("artifact_version") or report.get("output_version") != edited.get("artifact_version"):
        raise ScriptCoordinatorError("edit report versions do not match the script artifacts")
    if report.get("input_checksum") != draft.get("checksum") or report.get("output_checksum") != edited.get("checksum"):
        raise ScriptCoordinatorError("edit report checksums do not match the script artifacts")
    if audit.get("artifact_id") != edited.get("script_id") or audit.get("script_version") != edited.get("artifact_version"):
        raise ScriptCoordinatorError("final audit does not identify the edited script exactly")
    if audit.get("script_checksum") != edited.get("checksum") or audit.get("auditor_run_id") != auditor_run_id:
        raise ScriptCoordinatorError("final audit identity or auditor run is inconsistent")
    if audit.get("independence_result") != "PASS":
        raise ScriptCoordinatorError("final audit independence is not proven")

    decision = audit.get("decision")
    correction_route = audit.get("correction_route")
    route = None
    if decision in {"FAIL", "BLOCKED"}:
        route = correction_route or "EDITOR"
    elif decision not in {"PASS", "WARN"}:
        raise ScriptCoordinatorError("final audit decision is invalid")

    return {
        "trace_type": "PLAN013_SCRIPT_COORDINATION_TRACE",
        "episode_id": episode_id,
        "status": "CORRECTION_REQUIRED" if route else "HANDOFF_READY",
        "approval_inferred": False,
        "stages": [
            {"stage": "NARRATIVE_ARCHITECTURE", "artifact_ref": plan.get("script_plan_id"), "checksum": _checksum(plan)},
            {"stage": "WRITING", "artifact_ref": draft.get("script_id"), "version": draft.get("artifact_version"), "checksum": draft.get("checksum") or _checksum(draft), "run_id": producer_run_id},
            {"stage": "EDITOR", "artifact_ref": edited.get("script_id"), "version": edited.get("artifact_version"), "checksum": edited.get("checksum") or _checksum(edited), "run_id": editor_run_id, "edit_report_ref": edited.get("edit_report_ref")},
            {"stage": "FINAL_EDITORIAL_AUDITOR", "decision": decision, "run_id": auditor_run_id, "audited_artifact_ref": edited.get("script_id")},
        ],
        "correction_route": route,
        "references": {
            "thesis_id": thesis_id,
            "thesis_version": thesis_version,
            "thesis_checksum": thesis_checksum,
            "edit_report_checksum": _checksum(report),
            "final_audit_checksum": _checksum(audit),
        },
    }
