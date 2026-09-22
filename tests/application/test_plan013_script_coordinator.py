from __future__ import annotations

import copy

import pytest

from src.application.plan013_script_coordinator import ScriptCoordinatorError, coordinate_script_pipeline


def _graph() -> dict[str, object]:
    thesis = {"thesis_id": "T-1", "episode_id": "EP-1", "artifact_version": "1.0.0", "checksum": "b" * 64}
    binding = {key: value for key, value in thesis.items() if key != "episode_id"}
    return {
        "episode_id": "EP-1",
        "narrative_plan": {"episode_id": "EP-1", "script_plan_id": "PLAN-1"},
        "thesis_artifact": thesis,
        "script_draft": {
            "script_id": "SCRIPT-DRAFT-001", "episode_id": "EP-1", "artifact_version": "1.0.0",
            "content": "Borrador sintético.", "checksum": "a" * 64,
            "narrative_plan_ref": "narrative_plan:PLAN-1@1.0.0", "thesis_binding": binding,
            "created_at": "2026-08-22T00:00:00Z",
        },
        "edited_script": {
            "script_id": "SCRIPT-EDITED-001", "episode_id": "EP-1", "artifact_version": "1.1.0",
            "content": "Edición sintética.", "checksum": "c" * 64, "source_script_version": "1.0.0",
            "edit_report_ref": "editorial_edit_report:EDIT-1@1.1.0", "thesis_binding": binding,
            "created_at": "2026-08-22T00:00:00Z",
        },
        "edit_report": {
            "episode_id": "EP-1", "input_artifact_id": "SCRIPT-DRAFT-001", "input_checksum": "a" * 64,
            "output_artifact_id": "SCRIPT-EDITED-001", "output_checksum": "c" * 64,
            "input_version": "1.0.0", "output_version": "1.1.0", "edit_type": "RESTRUCTURE",
            "changes_by_category": {"structure": ["Reorganizacion del argumento."]}, "continuity_findings": [], "redundancy_findings": [],
            "line_findings": [], "orality_findings": [], "unresolved_issues": [], "invalidated_artifacts": [],
        },
        "final_audit": {
            "episode_id": "EP-1", "artifact_id": "SCRIPT-EDITED-001", "script_version": "1.1.0",
            "script_checksum": "c" * 64, "auditor_run_id": "RUN-AUDITOR-1", "independence_result": "PASS",
            "profile_compliance": "PASS", "brief_compliance": "PASS", "packaging_promise_compliance": "PASS",
            "evidence_sufficiency": "PASS", "thesis_quality": "PASS", "viewer_journey": "PASS",
            "opening_quality": "PASS", "progression": "PASS", "coherence": "PASS", "originality": "PASS",
            "source_transformation": "PASS", "voice": "PASS", "orality": "PASS", "closing_quality": "PASS",
            "factual_traceability": "PASS", "decision": "PASS", "correction_route": "NONE",
            "decision_basis": "Evaluacion cualitativa sustentada en el guion y sus artifacts de entrada.",
            "dimension_evidence": {
                field: {"observation": "Fixture cualitativo para validacion de contrato."}
                for field in (
                    "profile_compliance", "brief_compliance", "packaging_promise_compliance",
                    "evidence_sufficiency", "thesis_quality", "viewer_journey", "opening_quality",
                    "progression", "coherence", "originality", "source_transformation", "voice",
                    "orality", "closing_quality", "factual_traceability",
                )
            },
        },
        "producer_run_id": "RUN-WRITING-1", "editor_run_id": "RUN-EDITOR-1", "auditor_run_id": "RUN-AUDITOR-1",
    }


def test_coordinator_returns_trace_without_inferring_approval() -> None:
    trace = coordinate_script_pipeline(**_graph())
    assert trace["status"] == "HANDOFF_READY"
    assert trace["approval_inferred"] is False
    assert [stage["stage"] for stage in trace["stages"]] == [
        "NARRATIVE_ARCHITECTURE", "WRITING", "EDITOR", "FINAL_EDITORIAL_AUDITOR"
    ]


def test_coordinator_routes_failed_audit_without_deciding_editorial_outcome() -> None:
    graph = _graph()
    graph["final_audit"]["decision"] = "FAIL"
    graph["final_audit"]["correction_route"] = "WRITING"
    trace = coordinate_script_pipeline(**graph)
    assert trace["status"] == "CORRECTION_REQUIRED"
    assert trace["correction_route"] == "WRITING"
    assert trace["approval_inferred"] is False


def test_coordinator_rejects_stale_thesis_binding() -> None:
    graph = _graph()
    graph["edited_script"]["thesis_binding"]["checksum"] = "d" * 64
    with pytest.raises(ScriptCoordinatorError, match="stale"):
        coordinate_script_pipeline(**graph)


def test_coordinator_rejects_shared_auditor_run() -> None:
    graph = _graph()
    graph["auditor_run_id"] = graph["editor_run_id"]
    with pytest.raises(ScriptCoordinatorError, match="independent"):
        coordinate_script_pipeline(**graph)
