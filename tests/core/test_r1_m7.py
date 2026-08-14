"""Casos adversariales de R1-M7: disposición y anti cherry-picking."""

from copy import deepcopy

from src.core.contract_validation import validate_contradiction_disposition, validate_research_pack, validate_research_stop_decision
from tests.fixtures.synthetic_contracts import VALID_RESEARCH_PACK


def _contradiction(
    disposition="RESOLVED",
    treatments=("RETAINED", "REJECTED"),
    *,
    subject_kind="MATERIAL_CLAIM",
    subject_ref="C1",
    affected_claim_ids=None,
):
    pending = ["Obtener verificación primaria adicional."] if disposition == "INVESTIGATION_REQUIRED" else []
    limitations = ["La formulación debe conservar el desacuerdo explícito."] if disposition in {"CONTROVERSY", "LIMITED", "RIVAL"} else []
    return {
        "item_id": "X1",
        "statement": "Las fuentes discrepan sobre la causa del hecho.",
        "source_refs": ["S1", "S2"],
        "locator": "p. 10 / p. 22",
        "confidence": "HIGH",
        "subject_kind": subject_kind,
        "subject_ref": subject_ref,
        "subject_state": "PROVISIONAL",
        "subject_version": "1.0.0",
        "subject_formulation": "La formulación afectada.",
        "affected_use": "CENTRAL_CLAIM_SUPPORT",
        "affected_claim_ids": ["C1"] if affected_claim_ids is None else affected_claim_ids,
        "conflicting_source_refs": ["S1", "S2"],
        "discrepancy_kind": "CAUSAL",
        "materiality": "MATERIAL",
        "disposition": disposition,
        "compared_positions": [
            {"position_id": "P1", "statement": "La causa es A.", "source_refs": ["S1"], "treatment": treatments[0]},
            {"position_id": "P2", "statement": "La causa es B.", "source_refs": ["S2"], "treatment": treatments[1]},
        ],
        "decision_evidence_refs": ["S1", "S2"],
        "contrary_evidence_refs": ["S2"],
        "disposition_justification": "Se comparan ambas posiciones y se explicita el impacto sobre el claim.",
        "remaining_limitations": limitations,
        "pending_matters": pending,
        "return_route": "Revisar la formulación según la disposición de la contradicción.",
        "return_route_code": {
            "RESOLVED": "AUTHORIZE_INTENDED_USE_ONLY",
            "CONTROVERSY": "RESTRICT_FORMULATION_AND_DISCLOSE",
            "LIMITED": "RESTRICT_FORMULATION_AND_DISCLOSE",
            "RIVAL": "RESTRICT_FORMULATION_AND_DISCLOSE",
            "INVESTIGATION_REQUIRED": "RETURN_TO_RESEARCH",
            "BLOCKED": "REMOVE_REPLACE_OR_REFORMULATE",
        }[disposition],
        "invalidator_codes": ["MATERIAL_CONTRADICTION_FOUND", "NEW_MATERIAL_EVIDENCE"],
        "dependent_artifact_refs": ["claim:C1"],
        "revalidation_requirements": [] if disposition == "RESOLVED" else ["Revalidar el claim afectado antes de reutilizarlo."],
    }


def _pack(contradiction, *, include_claim=True, include_interpretation=False):
    pack = deepcopy(VALID_RESEARCH_PACK)
    pack["source_registry"].append(deepcopy(pack["source_registry"][0]) | {"source_id": "S2", "title": "Fuente rival"})
    pack["claims_candidates"] = ([{"item_id": "C1", "statement": "Claim afectado.", "source_refs": ["S1", "S2"], "locator": "p. 1", "confidence": "HIGH"}] if include_claim else [])
    pack["interpretations"] = ([{"item_id": "WI-1", "statement": "Interpretación de la obra.", "source_refs": ["S1"], "locator": "p. 2", "confidence": "HIGH"}] if include_interpretation else [])
    pack["contradictions"] = [contradiction]
    return pack


def test_resolved_contradiction_requires_explicit_comparison_and_evidence():
    assert validate_research_pack(_pack(_contradiction())) == []


def test_preclaim_contradiction_has_a_real_nonclaim_subject():
    case = _contradiction(subject_kind="WORK_INTERPRETATION", subject_ref="WI-1", affected_claim_ids=[])
    assert validate_research_pack(_pack(case, include_claim=False, include_interpretation=True)) == []


def test_work_interpretation_can_later_be_linked_to_a_claim_without_losing_origin():
    case = _contradiction(subject_kind="WORK_INTERPRETATION", subject_ref="WI-1", affected_claim_ids=["C1"])
    assert validate_research_pack(_pack(case, include_interpretation=True)) == []


def test_work_interpretation_subject_ref_must_exist_in_research_pack():
    case = _contradiction(subject_kind="WORK_INTERPRETATION", subject_ref="DOES_NOT_EXIST", affected_claim_ids=[])
    violations = validate_research_pack(_pack(case, include_claim=False, include_interpretation=True))
    assert any("subject_ref inexistente" in item for item in violations)


def test_existing_claim_subject_must_be_linked_explicitly():
    case = _contradiction(subject_kind="MATERIAL_CLAIM", subject_ref="C1", affected_claim_ids=[])
    violations = validate_research_pack(_pack(case))
    assert any("requiere affected_claim_ids" in item for item in violations)


def test_limited_controversy_rival_research_and_blocked_are_supported():
    cases = [
        _contradiction("CONTROVERSY", ("RETAINED", "OPEN")),
        _contradiction("LIMITED", ("LIMITED", "RETAINED")),
        _contradiction("RIVAL", ("RETAINED", "OPEN")),
        _contradiction("INVESTIGATION_REQUIRED", ("INVESTIGATE", "OPEN")),
        _contradiction("BLOCKED", ("BLOCKED", "OPEN")),
    ]
    for case in cases:
        assert validate_research_pack(_pack(case)) == []


def test_resolved_without_evidence_or_justification_is_rejected():
    case = _contradiction()
    case.pop("decision_evidence_refs")
    case.pop("disposition_justification")
    violations = validate_research_pack(_pack(case))
    assert any("disposición trazable" in item for item in violations)


def test_favorable_source_cannot_be_selected_without_rival_treatment():
    case = _contradiction()
    case["compared_positions"] = [case["compared_positions"][0], {**case["compared_positions"][1], "source_refs": ["S1"]}]
    case["contrary_evidence_refs"] = ["S1"]
    violations = validate_research_pack(_pack(case))
    assert any("todas las fuentes en conflicto" in item or "evidencia contraria" in item for item in violations)


def test_rival_interpretation_cannot_disappear_from_reasoning():
    case = _contradiction("RIVAL", ("RETAINED", "REJECTED"))
    violations = validate_research_pack(_pack(case))
    assert any("posición rival" in item for item in violations)


def test_real_controversy_cannot_be_declared_resolved():
    case = _contradiction("RESOLVED", ("RETAINED", "OPEN"))
    violations = validate_research_pack(_pack(case))
    assert any("RESOLVED" in item for item in violations)


def test_open_material_contradiction_still_blocks_m6_positive_sufficiency():
    decision = {
        "decision_id": "RSD-C1", "decision_version": "1.0.0", "subject_kind": "MATERIAL_CLAIM", "subject_ref": "C1",
        "intended_use": "CENTRAL_CLAIM_SUPPORT", "evidence_refs": ["S1"], "claim_decision": "CLAIM_ALLOWED",
        "sufficiency_status": "SUFFICIENT_FOR_INTENDED_USE", "limitations": [], "pending_matters": [],
        "unresolved_material_contradiction_refs": ["X1"], "invalidators": ["MATERIAL_CONTRADICTION_FOUND"],
        "invalidator_codes": ["MATERIAL_CONTRADICTION_FOUND"], "return_route": "Revisar investigación.",
        "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_basis": "No debe pasar.",
    }
    assert any("contradicción material abierta" in item for item in validate_research_stop_decision(decision))


def test_contradiction_helper_rejects_missing_rival_source_directly():
    case = _contradiction()
    case["conflicting_source_refs"] = ["S1"]
    violations = validate_contradiction_disposition(case, {"S1", "S2"}, {"S1", "S2", "X1"}, {"C1"})
    assert any("al menos dos fuentes" in item for item in violations)
