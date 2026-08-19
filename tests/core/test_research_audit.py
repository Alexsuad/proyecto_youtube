from __future__ import annotations

import copy

from src.core.research_audit import resolve_correction_routes, validate_independent_research_audit


def _audit(**overrides):
    data = {
        "audit_id": "AUDIT-1",
        "audit_version": "1.0.0",
        "episode_id": "EP-1",
        "audit_type": "FIDELITY",
        "audited_artifacts": [{"artifact_id": "WORK-DOSSIER-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}],
        "producer": {"actor_id": "PRODUCER-1", "run_id": "RUN-P"},
        "auditor": {"actor_id": "AUDITOR-1", "run_id": "RUN-A"},
        "auditor_write_scope": "AUDIT_ONLY",
        "independence_result": "PASS",
        "findings": [{"criterion": "SCRIPT_PRODUCT_DEFINED_CRITERION", "status": "LIMITED", "evidence_refs": ["WORK-DOSSIER-1"], "limitations": ["fixture"]}],
        "evidence_refs": ["WORK-DOSSIER-1"],
        "limitations": ["Synthetic fixture; no functional approval."],
        "defects": [{"defect_id": "DEF-1", "defect_type": "FIDELITY_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "description": "Fixture defect."}],
        "correction_routes": [{"defect_id": "DEF-1", "defect_type": "FIDELITY_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "invalidated_artifacts": ["WORK-DOSSIER-1"], "return_state": "RESEARCH_REVIEW_PENDING", "required_revalidation": "FIDELITY_AUDIT", "suggested_role": "SCRIPT_PRODUCT"}],
        "decision": "REQUEST_CHANGES",
        "created_at": "2026-08-18T12:00:00Z",
    }
    data.update(overrides)
    return data


def test_independent_audit_accepts_distinct_actor_and_run():
    assert validate_independent_research_audit(_audit()) == []


def test_same_producer_and_auditor_cannot_be_independent():
    data = _audit(auditor={"actor_id": "PRODUCER-1", "run_id": "RUN-P"})
    violations = validate_independent_research_audit(data)
    assert "AUDITOR_EQUALS_PRODUCER_RUN" in violations
    assert "AUDITOR_EQUALS_PRODUCER_ACTOR" in violations


def test_detected_defect_routes_to_origin_without_mutating_producer_output():
    producer_output = {"artifact_id": "WORK-DOSSIER-1", "status": "ORIGINAL"}
    before = copy.deepcopy(producer_output)
    routes = resolve_correction_routes(_audit())
    assert routes[0]["origin_artifact"] == "WORK-DOSSIER-1"
    assert producer_output == before


def test_defect_without_origin_route_fails_closed():
    data = _audit(correction_routes=[])
    assert "CORRECTION_ROUTE_MISSING:DEF-1" in validate_independent_research_audit(data)


def test_each_defect_requires_its_own_route_even_with_same_origin():
    data = _audit(
        defects=[
            {"defect_id": "DEF-1", "defect_type": "FIDELITY_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "description": "First."},
            {"defect_id": "DEF-2", "defect_type": "LOCATOR_DEFECT", "severity": "MINOR", "origin_artifact": "WORK-DOSSIER-1", "description": "Second."},
        ]
    )
    assert "CORRECTION_ROUTE_MISSING:DEF-2" in validate_independent_research_audit(data)


def test_pass_with_pending_findings_or_defects_fails_closed():
    pending = [{"criterion": "SCRIPT_PRODUCT_DEFINED_CRITERION", "status": "NOT_SATISFIED", "evidence_refs": ["WORK-DOSSIER-1"], "limitations": ["fixture"]}]
    assert "PASS_WITH_PENDING_FINDINGS" in validate_independent_research_audit(_audit(decision="PASS", findings=pending, defects=[], correction_routes=[]))
    assert "PASS_WITH_PENDING_DEFECTS" in validate_independent_research_audit(_audit(decision="PASS"))
    limited = _audit(decision="PASS", findings=[{"criterion": "SCRIPT_PRODUCT_DEFINED_CRITERION", "status": "LIMITED", "evidence_refs": ["WORK-DOSSIER-1"], "limitations": ["fixture"]}], defects=[], correction_routes=[])
    assert validate_independent_research_audit(limited) == []


def test_multiple_producer_runs_follow_canonical_b5_pattern():
    data = _audit(
        producer={"actor_id": "MIXED_PRODUCER_ACTORS", "run_id": "MULTIPLE_PRODUCER_RUNS"},
        audited_artifacts=[
            {"artifact_id": "WORK-DOSSIER-1", "checksum": "a" * 64, "producer_run_id": "RUN-P1"},
            {"artifact_id": "CLAIMS-1", "checksum": "b" * 64, "producer_run_id": "RUN-P2"},
        ],
        defects=[],
        correction_routes=[],
        decision="PASS",
    )
    assert validate_independent_research_audit(data) == []


def test_multiple_producer_auditor_sharing_a_producer_run_is_rejected():
    data = _audit(
        producer={"actor_id": "MIXED_PRODUCER_ACTORS", "run_id": "MULTIPLE_PRODUCER_RUNS"},
        audited_artifacts=[
            {"artifact_id": "WORK-DOSSIER-1", "checksum": "a" * 64, "producer_run_id": "RUN-P1"},
            {"artifact_id": "CLAIMS-1", "checksum": "b" * 64, "producer_run_id": "RUN-P2"},
        ],
        auditor={"actor_id": "AUDITOR-1", "run_id": "RUN-P1"},
        defects=[],
        correction_routes=[],
        decision="PASS",
    )
    violations = validate_independent_research_audit(data)
    assert "AUDITOR_EQUALS_PRODUCER_RUN" in violations


def test_declared_single_producer_must_match_all_audited_artifacts():
    data = _audit(audited_artifacts=[{"artifact_id": "WORK-DOSSIER-1", "checksum": "a" * 64, "producer_run_id": "RUN-OTHER"}])
    assert "AUDITED_ARTIFACT_PRODUCER_RUN_MISMATCH" in validate_independent_research_audit(data)


def test_duplicate_defect_id_fails_closed():
    defect = {"defect_id": "DEF-1", "defect_type": "FIDELITY_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "description": "Duplicate."}
    violations = validate_independent_research_audit(_audit(defects=[defect, dict(defect)]))
    assert "DUPLICATE_DEFECT_ID" in violations


def test_duplicate_correction_route_defect_id_fails_closed():
    route = {"defect_id": "DEF-1", "defect_type": "FIDELITY_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "invalidated_artifacts": ["WORK-DOSSIER-1"], "return_state": "RESEARCH_REVIEW_PENDING", "required_revalidation": "FIDELITY_AUDIT", "suggested_role": "SCRIPT_PRODUCT"}
    violations = validate_independent_research_audit(_audit(correction_routes=[route, dict(route)]))
    assert "DUPLICATE_CORRECTION_ROUTE_DEFECT_ID" in violations
