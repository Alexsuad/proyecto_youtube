from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.application.research_b3 import ResearchB3Error, ResearchB3Orchestrator, ResearchB3Persistence
from src.application.research_b2 import SoftwareAcquisitionAdapter
from src.application.interaction import HumanDecision, HumanDecisionRequest
from tests.core.test_plan012_m4_b3_deep_research import _baseline, _m4_context, _run_m4


def _read(ref):
    return json.loads(open(ref["path"], encoding="utf-8").read())


def _claims():
    return {
        "claims": [
            {
                "claim_id": "C-EXT",
                "claim_text": "El fenómeno admite una explicación limitada.",
                "claim_type": "INTERPRETATION",
                "source_refs": ["S1"],
                "external_reality_evidence_refs": ["S1"],
                "work_evidence_refs": [],
                "supporting_evidence_refs": ["S1"],
                "limiting_evidence_refs": ["S1"],
                "refuting_evidence_refs": ["S1"],
                "verification_status": "VERIFIED",
                "confidence": 0.8,
                "criticality": "CENTRAL",
                "intended_use": "CENTRAL_CLAIM_SUPPORT",
                "claim_decision": "CLAIM_LIMITED",
                "research_sufficiency": "LIMITED_BUT_USABLE",
                "limitations": "El rival impide afirmar una explicación causal general.",
                "decision_basis": "La evidencia externa y el rival material sostienen solo un alcance limitado.",
                "return_route": "Usar con formulación limitada y disclosure del rival.",
                "materiality": {
                    "is_material": True,
                    "activation_criteria": ["THESIS_DEPENDENCY"],
                    "non_trigger_examples": ["CURIOSIDAD_GENERAL"],
                    "invalidator_codes": ["NEW_MATERIAL_EVIDENCE"],
                    "return_route_code": "RESTRICT_FORMULATION_AND_DISCLOSE",
                    "decision_ref": None,
                },
                "contradiction_refs": [],
                "pending_matters": [],
            },
            {
                "claim_id": "C-WORK",
                "claim_text": "La obra documenta una conducta observable.",
                "claim_type": "INTERPRETATION",
                "source_refs": ["D-W1"],
                "external_reality_evidence_refs": [],
                "work_evidence_refs": ["D-W1"],
                "supporting_evidence_refs": ["D-W1"],
                "limiting_evidence_refs": ["D-W1"],
                "refuting_evidence_refs": [],
                "verification_status": "VERIFIED",
                "confidence": 0.7,
                "criticality": "SECONDARY",
                "intended_use": "NARRATIVE_MATERIAL",
                "claim_decision": "CLAIM_LIMITED",
                "research_sufficiency": "LIMITED_BUT_USABLE",
                "limitations": "La observación de la obra no demuestra una regularidad externa.",
                "decision_basis": "La evidencia de obra permite describir el pasaje, pero no generalizar.",
                "return_route": "Describir la obra sin convertirla en prueba de realidad externa.",
                "materiality": {
                    "is_material": True,
                    "activation_criteria": ["WORK_FIDELITY"],
                    "non_trigger_examples": ["PREFERENCIA_SUBJETIVA"],
                    "invalidator_codes": ["WORK_VERSION_OR_ADAPTATION_CHANGED"],
                    "return_route_code": "RESTRICT_FORMULATION_AND_DISCLOSE",
                    "decision_ref": None,
                },
                "contradiction_refs": [],
                "pending_matters": [],
            },
        ],
        "evidence_type_separation": {
            "work_evidence_refs": ["D-W1"],
            "external_reality_evidence_refs": ["S1"],
        },
        "rival_explanations": [
            {
                "rival_id": "RIVAL-1",
                "statement": "Una explicación rival reduce la fuerza causal de la tesis.",
                "affected_claim_ids": ["C-EXT"],
                "evidence_refs": ["S1"],
                "material_impact": "Limita la generalización del claim.",
                "disposition": "Se conserva como límite explícito.",
            }
        ],
        "contradictions": [
            {
                "contradiction_id": "CONTRA-1",
                "statement": "La evidencia disponible no converge en una explicación única.",
                "source_refs": ["S1", "D-W1"],
                "subject_kind": "MATERIAL_CLAIM",
                "subject_ref": "C-EXT",
                "subject_state": "PROVISIONAL",
                "subject_version": "1.0.0",
                "subject_formulation": "La explicación del fenómeno.",
                "affected_use": "CENTRAL_CLAIM_SUPPORT",
                "affected_claim_ids": ["C-EXT"],
                "conflicting_source_refs": ["S1", "D-W1"],
                "discrepancy_kind": "CAUSAL",
                "evidence_refs": ["S1"],
                "materiality": "MATERIAL",
                "status": "TREATED",
                "disposition": "LIMITED",
                "compared_positions": [
                    {"position_id": "P1", "statement": "La explicación es generalizable.", "source_refs": ["S1"], "treatment": "RETAINED"},
                    {"position_id": "P2", "statement": "La explicación es contextual.", "source_refs": ["D-W1"], "treatment": "LIMITED"},
                ],
                "decision_evidence_refs": ["S1", "D-W1"],
                "contrary_evidence_refs": ["D-W1"],
                "disposition_justification": "Se comparan las posiciones y se limita la conclusión.",
                "remaining_limitations": ["No se generaliza fuera del contexto documentado."],
                "pending_matters": [],
                "return_route": "Mantener la formulación limitada.",
                "return_route_code": "RESTRICT_FORMULATION_AND_DISCLOSE",
                "invalidator_codes": ["NEW_MATERIAL_EVIDENCE"],
                "dependent_artifact_refs": ["C-EXT"],
                "revalidation_requirements": ["Revalidar si cambia la evidencia."],
                "resolution_or_limit": "Se limita la formulación y se conserva la incertidumbre.",
            }
        ],
        "gaps": [
            {
                "gap_id": "GAP-1",
                "statement": "Falta evidencia para determinar la transferencia a otros contextos.",
                "affected_claim_ids": ["C-EXT"],
                "evidence_refs": [],
                "materiality": "MATERIAL",
                "status": "OPEN",
                "return_route": "RETURN_TO_RESEARCH",
            }
        ],
    }


def _comparison(selected):
    return {
        "dimensions": ["CONTRIBUTION", "COVERAGE", "COMPLEMENTARITY", "REDUNDANCY", "CONTRAST", "FIDELITY", "LIMITATIONS", "EVIDENCE"],
        "entries": [
            {
                "work_id": work_id,
                "evidence_refs": [f"D-{work_id}"],
                "contribution": "Aporte diferencial.",
                "coverage": "Cubre una dimensión distinta.",
                "complementarity": "Complementa el conjunto.",
                "redundancy": "Redundancia limitada.",
                "contrast": "Introduce contraste.",
                "fidelity": "Fidelidad profunda documentada.",
                "limitations": ["No decide orden ni estructura narrativa."],
                "missing_perspectives": [],
                "overinterpretation_risk": "Riesgo bajo si se mantiene el alcance documentado.",
            }
            for work_id in selected
        ],
        "selected_work_ids": list(selected),
        "selection_mode": "USER_SELECTION",
        "selection_authority_ref": "RP-FIXTURE:M4:HUMAN_DECISION",
        "human_decision_required": False,
        "set_recommendations": [
            {
                "recommendation_id": "REC-KEEP",
                "action": "MAINTAIN",
                "affected_work_ids": list(selected),
                "rationale": "El conjunto conserva complementariedad pese a sus límites.",
                "evidence_refs": [f"D-{selected[0]}"],
                "material_change": False,
            }
        ],
    }


def _delegation_input():
    return {
        "decision": "DELEGATE",
        "reasons": ["scope explícito"],
        "policy_version": "1.0.0",
        "evidence_refs": ["D-W1", "D-W2", "D-W3"],
        "authorized_candidate_set": ["W1", "W2", "W3"],
    }


def _thesis(provisional_id):
    return {
        "provisional_disposition": "LIMITED",
        "statement": "La tesis se sostiene solo como interpretación limitada y condicionada.",
        "supporting_evidence_refs": ["S1"],
        "counterevidence_refs": ["D-W1"],
        "rival_interpretations": ["La explicación rival reduce la generalización."],
        "main_objection": "La evidencia externa no permite afirmar causalidad universal.",
        "nuance": "La obra ilustra una relación sin demostrarla fuera de ella.",
        "material_contributions": [{"material_id": "W1", "contribution": "Aporta el contraste documentado."}],
        "analysis_confirmed": ["La pregunta inicial sigue siendo investigable."],
        "changes_from_provisional": ["Se limita el alcance causal."],
        "discarded_from_provisional": ["Se descarta la generalización universal."],
        "refinement_rationale": "Los rivales y el gap abierto obligan a limitar la tesis.",
        "refinement_dimensions": [
            {
                "dimension": "CAUSALITY",
                "provisional_position": "Explicación amplia.",
                "resulting_position": "Interpretación no causal y condicionada.",
                "evidence_refs": ["S1"],
                "rationale": "La evidencia rival limita la inferencia.",
            }
        ],
        "inherited_constraint_ids": [],
        "statement_unchanged_justification": None,
        "limits": ["No confundir evidencia de obra con realidad externa."],
        "revision_conditions": ["Recuperar evidencia sobre transferencia contextual."],
        "refined_position": "Posición investigativa limitada.",
        "what_was_confirmed": ["La relación con el fenómeno sigue siendo relevante."],
        "what_was_changed": ["La fuerza de la afirmación se redujo."],
        "what_was_rejected": ["La causalidad universal."],
        "what_was_limited": ["La generalización fuera del contexto."],
        "strongest_objection": "La evidencia puede reflejar selección contextual.",
        "alternative_explanation": "El contexto puede explicar parte del patrón observado.",
        "conditions_of_validity": ["Mantener el alcance delimitado."],
        "remaining_uncertainties": ["Transferencia a otros contextos."],
        "evidence_dependencies": ["S1", "D-W1"],
    }


def _run_m5(
    tmp_path, *, cognitive=None, m4_result=None, baseline=None,
    selection_change_decision=None, selection_change_delegation=None, m4_kwargs=None,
):
    baseline = baseline or _baseline(tmp_path / "fixture")
    if m4_result is None:
        m4_result, _ = _run_m4(tmp_path / "m4", baseline=baseline, **(m4_kwargs or {}))
    selected = _read(m4_result["execution_manifest"])["selection"]["selected_work_ids"] if "execution_manifest" in m4_result else ["W1", "W2", "W3"]
    seen = []

    def executor(request):
        seen.append(request)
        if cognitive:
            return cognitive(request)
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(selected)
        if request.stage == "M5_REFINED_THESIS":
            return _thesis(baseline["provisional_thesis"]["thesis_id"])
        raise AssertionError(request.stage)

    result = ResearchB3Orchestrator(
        executor,
        ResearchB3Persistence(tmp_path / "m5"),
        acquisition_adapter=SoftwareAcquisitionAdapter(),
    ).run_m5(
        baseline,
        m4_result,
        context=_m4_context(),
        selection_change_decision=selection_change_decision,
        selection_change_delegation=selection_change_delegation,
    )
    return result, seen


def test_m5_consumes_real_m4_outputs_and_keeps_m6_boundary(tmp_path):
    baseline = _baseline(tmp_path / "fixture")
    m4_result, _ = _run_m4(tmp_path / "m4", baseline=baseline)
    result, seen = _run_m5(tmp_path, baseline=baseline, m4_result=m4_result)
    assert [request.stage for request in seen] == [
        "M5_CLAIMS_EVIDENCE_CONSOLIDATION",
        "M5_POST_DEEP_SET_REEVALUATION",
        "M5_REFINED_THESIS",
    ]
    assert seen[0].input_artifacts[0]["artifact_kind"] == "ResearchM4ExecutionManifest"
    manifest = _read(result["execution_manifest"])
    assert manifest["m4_inputs_verified"] is True
    assert manifest["research_ready_manifest_not_produced"] is True
    assert manifest["b5_i3_outputs_not_produced"] is True
    assert manifest["narrative_decisions_not_made"] is True


def test_m5_consolidates_domains_rivals_and_open_gap(tmp_path):
    result, _ = _run_m5(tmp_path)
    ledger = _read(result["claims_ledger"])
    assert ledger["evidence_type_separation"] == {"work_evidence_refs": ["D-W1"], "external_reality_evidence_refs": ["S1"]}
    assert ledger["claims"][0]["supporting_evidence_refs"] == ["S1"]
    assert ledger["claims"][1]["supporting_evidence_refs"] == ["D-W1"]
    assert ledger["rival_explanations"][0]["affected_claim_ids"] == ["C-EXT"]
    assert ledger["gaps"][0]["status"] == "OPEN"
    assert ledger["gaps"][0]["evidence_refs"] == []
    assert all(item["materiality"]["decision_ref"] for item in ledger["claims"])
    assert _read(result["claim_sufficiency"])["decisions"][0]["sufficiency_status"] == "LIMITED_BUT_USABLE"
    assert ledger["claims"][0]["claim_decision"] == "CLAIM_LIMITED"


@pytest.mark.parametrize("mutator,match", [
    (lambda c: c["claims"][0]["source_refs"].append("UNKNOWN"), "EVIDENCE_REF_UNRESOLVED"),
    (lambda c: c["evidence_type_separation"]["work_evidence_refs"].append("S1"), "EVIDENCE_TYPES_MIXED"),
    (lambda c: c["claims"][0].update(work_evidence_refs=["S1"], external_reality_evidence_refs=[]), "EVIDENCE_TYPES_MIXED"),
    (lambda c: c["claims"][0].pop("supporting_evidence_refs"), "SUPPORTING_EVIDENCE_REQUIRED"),
    (lambda c: c["claims"][0].update(supporting_evidence_refs=["D-W1"]), "SUPPORTING_EVIDENCE_NOT_IN_SOURCE_REFS"),
])
def test_m5_rejects_unknown_or_mixed_evidence(tmp_path, mutator, match):
    def cognitive(request):
        value = _claims()
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            mutator(value)
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        if request.stage == "M5_REFINED_THESIS":
            return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")
        return value

    with pytest.raises(ResearchB3Error, match=match):
        _run_m5(tmp_path, cognitive=cognitive)


def test_m5_persists_owner_review_before_continuing_after_selection_change(tmp_path):
    def change(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["set_recommendations"][0].update(action="REPLACE", material_change=True)
            value["substitution_research_requirements"] = [{"work_id": "W4", "status": "RESEARCH_REQUIRED", "required_scopes": ["DEEP_RESEARCH", "DEEP_FIDELITY"]}]
            value["human_decision_required"] = True
            return value
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    state_root = tmp_path / "same-state"
    baseline = _baseline(state_root / "fixture")
    m4_result, _ = _run_m4(state_root / "m4", baseline=baseline)
    pending, first_seen = _run_m5(state_root, baseline=baseline, m4_result=m4_result, cognitive=change)
    assert pending["status"] == "PENDING_HUMAN_DECISION"
    request = _read(pending["human_decision_request"])
    assert request["status"] == "PENDING"
    assert request["recommendation"]
    previous_refs = {
        key: (pending[key]["path"], pending[key]["checksum"])
        for key in ("claims_ledger", "claim_sufficiency", "post_deep_comparison", "human_decision_request")
    }
    assert not (state_root / "m5" / "refined_thesis_m5.json").exists()
    result, second_seen = _run_m5(
        state_root,
        baseline=baseline,
        m4_result=m4_result,
        cognitive=lambda request: _thesis("RP-FIXTURE:THESIS:PROVISIONAL"),
        selection_change_decision={"decision": "REJECT", "decision_ref": "DECISION-1", "actor_ref": "OWNER"},
    )
    assert [request.stage for request in first_seen] == [
        "M5_CLAIMS_EVIDENCE_CONSOLIDATION", "M5_POST_DEEP_SET_REEVALUATION",
    ]
    assert [request.stage for request in second_seen] == ["M5_REFINED_THESIS"]
    assert result["status"] == "READY_FOR_OWNER_REVIEW"
    assert all((result[key]["path"], result[key]["checksum"]) == previous_refs[key] for key in previous_refs)
    manifest = _read(result["execution_manifest"])
    assert manifest["human_selection_protected"] is True
    assert manifest["selection_change_request_ref"]
    assert manifest["selection_change_decision_ref"]


@pytest.mark.parametrize("action,affected_work_ids", [("REPLACE", ["W1"]), ("ADD", ["W4"])])
def test_m5_approved_material_change_returns_to_research_without_refined_thesis(tmp_path, action, affected_work_ids):
    def change(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["set_recommendations"][0].update(action=action, affected_work_ids=affected_work_ids, material_change=True)
            value["substitution_research_requirements"] = [{
                "work_id": "W4", "status": "RESEARCH_REQUIRED",
                "required_scopes": ["DEEP_RESEARCH", "DEEP_FIDELITY"],
            }]
            value["human_decision_required"] = True
            return value
        raise AssertionError(request.stage)

    state_root = tmp_path / "approved"
    baseline = _baseline(state_root / "fixture")
    m4_result, _ = _run_m4(state_root / "m4", baseline=baseline)
    pending, _ = _run_m5(state_root, baseline=baseline, m4_result=m4_result, cognitive=change)
    result, seen = _run_m5(
        state_root, baseline=baseline, m4_result=m4_result,
        cognitive=lambda request: pytest.fail(f"No debe ejecutar IA en la aprobación: {request.stage}"),
        selection_change_decision={"decision": "APPROVE", "actor_ref": "OWNER"},
    )
    assert pending["status"] == "PENDING_HUMAN_DECISION"
    assert result["status"] == "PENDING_RESEARCH"
    assert seen == []
    assert "refined_thesis" not in result
    assert _read(result["post_deep_comparison"])["set_recommendations"][0]["action"] == action
    stop = _read(result["approved_change_research"])["decisions"][0]
    assert stop["sufficiency_status"] == "MORE_RESEARCH_REQUIRED"
    assert stop["return_route_code"] == "RETURN_TO_RESEARCH"
    assert "W4" not in _read(result["post_deep_comparison"])["selected_work_ids"]
    assert not (state_root / "m5" / "refined_thesis_m5.json").exists()


def test_m5_delegated_selection_does_not_convert_to_owner_request(tmp_path):
    def delegated_change(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["selection_mode"] = "DELEGATED_SELECTION"
            value["selection_authority_ref"] = "RP-FIXTURE:M4:DELEGATED_SELECTION"
            value["set_recommendations"][0].update(action="REDUCE", material_change=True)
            value["human_decision_required"] = True
            return value
        if request.stage == "M5_DELEGATED_POST_DEEP_DECISION":
            return {
                "decision": "REJECT",
                "action": "REJECT",
                "recommendation_ids": ["REC-KEEP"],
                "resulting_work_ids": ["W1", "W2", "W3"],
                "rationale": "El delegado rechaza la reducción por sus limitaciones materiales.",
                "evidence_refs": ["D-W1", "D-W2", "D-W3"],
                "criteria_used": ["EVIDENCE", "COMPLEMENTARITY", "LIMITATIONS"],
                "limitations": ["La decisión no resuelve la investigación externa."],
            }
        if request.stage == "M5_REFINED_THESIS":
            return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")
        raise AssertionError(request.stage)

    delegation = {
        "decision": "DELEGATE",
        "reasons": ["scope explícito"],
        "policy_version": "1.0.0",
        "evidence_refs": ["D-W1", "D-W2", "D-W3"],
        "authorized_candidate_set": ["W1", "W2", "W3"],
    }
    state_root = tmp_path / "delegated"
    baseline = _baseline(state_root / "fixture")
    m4_result, _ = _run_m4(
        state_root / "m4", baseline=baseline,
        selection_mode="DELEGATED_SELECTION", delegation_decision=delegation,
    )
    result, seen = _run_m5(state_root, baseline=baseline, m4_result=m4_result, cognitive=delegated_change)
    assert result["status"] == "READY_FOR_OWNER_REVIEW"
    assert [request.stage for request in seen] == [
        "M5_CLAIMS_EVIDENCE_CONSOLIDATION",
        "M5_POST_DEEP_SET_REEVALUATION",
        "M5_DELEGATED_POST_DEEP_DECISION",
        "M5_REFINED_THESIS",
    ]
    manifest = _read(result["execution_manifest"])
    assert manifest["selection_mode"] == "DELEGATED_SELECTION"
    assert manifest["human_selection_protected"] is False
    assert manifest["selection_change_delegation_ref"]
    assert manifest["delegated_post_deep_decision_ref"] == manifest["selection_change_delegation_ref"]
    decision = _read(result["delegated_post_deep_decision"])
    assert decision["decision"] == "REJECT"
    assert decision["comparison_id"] == result["post_deep_comparison"]["artifact_id"]
    assert decision["comparison_version"] == result["post_deep_comparison"]["artifact_version"]
    assert decision["comparison_checksum"] == result["post_deep_comparison"]["checksum"]
    assert decision["recommendation_ids"] == ["REC-KEEP"]
    assert decision["authorized_candidate_set"] == ["W1", "W2", "W3"]
    assert "human_decision_request" not in result


def _run_delegated_material_case(tmp_path, *, action, affected_work_ids, resulting_work_ids, decision="APPROVE", invalid=None):
    baseline = _baseline(tmp_path / "fixture")
    delegation = _delegation_input()
    m4_result, _ = _run_m4(
        tmp_path / "m4", baseline=baseline,
        selection_mode="DELEGATED_SELECTION", delegation_decision=delegation,
    )

    def cognitive(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["selection_mode"] = "DELEGATED_SELECTION"
            value["set_recommendations"][0].update(
                action=action, affected_work_ids=affected_work_ids, material_change=True,
            )
            if action in {"REPLACE", "ADD"}:
                value["substitution_research_requirements"] = [{
                    "work_id": "W4", "status": "RESEARCH_REQUIRED",
                    "required_scopes": ["DEEP_RESEARCH", "DEEP_FIDELITY"],
                }]
            value["human_decision_required"] = True
            return value
        if request.stage == "M5_DELEGATED_POST_DEEP_DECISION":
            value = {
                "decision": decision,
                "action": "REJECT" if decision == "REJECT" else action,
                "recommendation_ids": ["REC-KEEP"],
                "resulting_work_ids": resulting_work_ids,
                "rationale": "Decisión concreta del delegado basada en el comparison post-deep.",
                "evidence_refs": ["D-W1", "D-W2", "D-W3"],
                "criteria_used": ["EVIDENCE", "COMPLEMENTARITY", "LIMITATIONS"],
                "limitations": ["La decisión conserva los límites de la evidencia."],
            }
            if invalid:
                invalid(value)
            return value
        if request.stage == "M5_REFINED_THESIS":
            return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")
        raise AssertionError(request.stage)

    return _run_m5(tmp_path, baseline=baseline, m4_result=m4_result, cognitive=cognitive)


@pytest.mark.parametrize("invalid,match", [
    (lambda value: value.update(evidence_refs=["INVENTED-EVIDENCE"]), "EVIDENCE_REF_UNRESOLVED"),
    (lambda value: value.update(resulting_work_ids=["W-OUTSIDE-SCOPE"]), "SCOPE_INVALID"),
])
def test_m5_delegated_post_deep_decision_rejects_untrusted_output(tmp_path, invalid, match):
    with pytest.raises(ResearchB3Error, match=match):
        _run_delegated_material_case(
            tmp_path, action="REDUCE", affected_work_ids=["W3"],
            resulting_work_ids=["W1", "W2"], invalid=invalid,
        )


@pytest.mark.parametrize("action,affected_work_ids", [
    ("ADD", ["W4"]),
    ("REPLACE", ["W2"]),
])
def test_m5_delegated_post_deep_rejects_approved_work_outside_authorized_scope(
    tmp_path, action, affected_work_ids,
):
    with pytest.raises(ResearchB3Error, match="M5_DELEGATED_POST_DEEP_SCOPE_INVALID"):
        _run_delegated_material_case(
            tmp_path, action=action, affected_work_ids=affected_work_ids,
            resulting_work_ids=["W1", "W2", "W3"],
        )


@pytest.mark.parametrize("action,affected_work_ids,resulting_work_ids,expected_status", [
    ("REDUCE", ["W3"], ["W1", "W2"], "READY_FOR_OWNER_REVIEW"),
    ("REMOVE", ["W2"], ["W1", "W3"], "READY_FOR_OWNER_REVIEW"),
])
def test_m5_delegated_post_deep_decision_applies_only_authorized_route(
    tmp_path, action, affected_work_ids, resulting_work_ids, expected_status,
):
    result, seen = _run_delegated_material_case(
        tmp_path, action=action, affected_work_ids=affected_work_ids,
        resulting_work_ids=resulting_work_ids,
    )
    assert result["status"] == expected_status
    assert "human_decision_request" not in result
    decision = _read(result["delegated_post_deep_decision"])
    assert decision["decision"] == "APPROVE"
    assert decision["action"] == action
    assert decision["resulting_work_ids"] == resulting_work_ids
    assert decision["comparison_id"] == result["post_deep_comparison"]["artifact_id"]
    assert "M5_DELEGATED_POST_DEEP_DECISION" in [request.stage for request in seen]
    manifest = _read(result["execution_manifest"])
    assert manifest["m6_status"] == "NOT_AUTHORIZED"
    assert manifest["effective_selected_work_ids"] == resulting_work_ids


def test_m5_accepts_canonical_preclaim_contradiction_bound_to_phenomenon(tmp_path):
    def preclaim(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            value["contradictions"][0].update(
                subject_kind="PHENOMENON",
                subject_ref="RP-FIXTURE",
                affected_claim_ids=[],
            )
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    result, _ = _run_m5(tmp_path, cognitive=preclaim)
    contradiction = _read(result["claims_ledger"])["contradictions"][0]
    assert contradiction["affected_claim_ids"] == []
    assert contradiction["subject_kind"] == "PHENOMENON"


def test_m5_links_preclaim_contradiction_to_claim_when_cognition_identifies_material_impact(tmp_path):
    def linked(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            value["contradictions"][0].update(
                subject_kind="PHENOMENON",
                subject_ref="RP-FIXTURE",
                affected_claim_ids=["C-EXT"],
            )
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    result, _ = _run_m5(tmp_path, cognitive=linked)
    contradiction = _read(result["claims_ledger"])["contradictions"][0]
    assert contradiction["subject_kind"] == "PHENOMENON"
    assert contradiction["affected_claim_ids"] == ["C-EXT"]


def test_m5_requires_explicit_post_deep_perspectives_and_overinterpretation_findings(tmp_path):
    def missing(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["entries"][0].pop("missing_perspectives")
            return value
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    with pytest.raises(ResearchB3Error, match="MISSING_PERSPECTIVES_REQUIRED"):
        _run_m5(tmp_path / "missing", cognitive=missing)

    def risk_missing(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["entries"][0].pop("overinterpretation_risk")
            return value
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    with pytest.raises(ResearchB3Error, match="OVERINTERPRETATION_RISK_REQUIRED"):
        _run_m5(tmp_path / "risk", cognitive=risk_missing)


def test_m5_rejects_silent_selection_change_and_unsubstantiated_gap_closure(tmp_path):
    def bad(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            value["gaps"][0]["status"] = "RESOLVED"
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["selected_work_ids"] = ["W1", "W2"]
            return value
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    with pytest.raises(ResearchB3Error, match="CANNOT_CLOSE_WITHOUT_EVIDENCE"):
        _run_m5(tmp_path / "gap", cognitive=bad)

    def silent(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["selected_work_ids"] = ["W1", "W2"]
            return value
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    with pytest.raises(ResearchB3Error, match="SILENT_SELECTION_CHANGE"):
        _run_m5(tmp_path / "selection", cognitive=silent)


def test_m5_thesis_preserves_provisional_lineage_without_audit_or_narrative(tmp_path):
    result, _ = _run_m5(tmp_path)
    thesis = _read(result["refined_thesis"])
    assert thesis["provisional_thesis_id"] == "RP-FIXTURE:THESIS:PROVISIONAL"
    assert thesis["provisional_disposition"] == "LIMITED"
    assert "RP-FIXTURE:THESIS:PROVISIONAL" in thesis["lineage"]
    assert any(item.startswith("software:m5:provisional-disposition:") for item in thesis["lineage"])
    assert thesis["semantic_audit_id"] == "NOT_PERFORMED_M6_PENDING"
    assert thesis["curation_id"] == "NOT_APPLICABLE_M5_RESEARCH_SCOPE"
    assert not any(field in thesis for field in ("hook", "viewer_journey", "narrative_plan", "cta", "title", "thumbnail"))


def test_m5_rejects_modified_provisional_thesis_with_same_id(tmp_path):
    baseline = _baseline(tmp_path / "fixture")
    m4_result, _ = _run_m4(tmp_path / "m4", baseline=baseline)
    mutated = deepcopy(baseline)
    mutated["provisional_thesis"]["statement"] += " Modificación no heredada."
    with pytest.raises(ResearchB3Error, match="PROVISIONAL_THESIS_M4_BINDING_INVALID"):
        _run_m5(tmp_path / "m5", baseline=mutated, m4_result=m4_result)


def test_m5_rejects_m4_output_with_same_id_but_different_canonical_binding(tmp_path):
    baseline = _baseline(tmp_path / "fixture")
    m4_result, _ = _run_m4(tmp_path / "m4", baseline=baseline)
    original = m4_result["deep_work_research"]
    altered_path = tmp_path / "altered_deep_work_research.json"
    altered_path.write_text(json.dumps(_read(original), ensure_ascii=False), encoding="utf-8")
    m4_result["deep_work_research"] = {
        **original,
        "path": str(altered_path),
        "checksum": "0" * 64,
    }
    with pytest.raises(ResearchB3Error, match="M5_M4_INPUT_BINDING_INVALID"):
        _run_m5(tmp_path / "m5", baseline=baseline, m4_result=m4_result)


def test_m5_rejects_m4_work_evidence_reclassified_as_external_reality(tmp_path):
    def reclassified(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            value["evidence_type_separation"]["work_evidence_refs"] = []
            value["evidence_type_separation"]["external_reality_evidence_refs"].append("D-W1")
            value["claims"][1].update(work_evidence_refs=[], external_reality_evidence_refs=["D-W1"])
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    with pytest.raises(ResearchB3Error, match="EVIDENCE_DOMAIN_RECLASSIFICATION"):
        _run_m5(tmp_path, cognitive=reclassified)


@pytest.mark.parametrize("action,affected_work_id,expected_ids", [
    ("REMOVE", "W2", ["W1", "W3"]),
    ("REDUCE", "W3", ["W1", "W2"]),
])
def test_m5_owner_approve_remove_reduce_updates_effective_selection(
    tmp_path, action, affected_work_id, expected_ids,
):
    def change(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["set_recommendations"][0].update(
                action=action,
                affected_work_ids=[affected_work_id],
                material_change=True,
            )
            value["human_decision_required"] = True
            return value
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    result, seen = _run_m5(
        tmp_path,
        cognitive=change,
        selection_change_decision={"action": "APPROVE", "actor_ref": "OWNER"},
    )
    assert result["status"] == "READY_FOR_OWNER_REVIEW"
    assert [request.stage for request in seen] == [
        "M5_CLAIMS_EVIDENCE_CONSOLIDATION",
        "M5_POST_DEEP_SET_REEVALUATION",
        "M5_REFINED_THESIS",
    ]
    manifest = _read(result["execution_manifest"])
    assert manifest["effective_selected_work_ids"] == expected_ids
    assert _read(result["refined_thesis"])["material_contributions"][0]["material_id"] == "W1"


def test_m5_recovers_persisted_human_decision_before_manifest_update(tmp_path):
    baseline = _baseline(tmp_path / "fixture")
    m4_result, _ = _run_m4(tmp_path / "m4", baseline=baseline)

    def change(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            value = _comparison(["W1", "W2", "W3"])
            value["set_recommendations"][0].update(
                action="REMOVE", affected_work_ids=["W2"], material_change=True,
            )
            value["human_decision_required"] = True
            return value
        raise AssertionError(request.stage)

    state_root = tmp_path / "same-state"
    pending, _ = _run_m5(state_root, baseline=baseline, m4_result=m4_result, cognitive=change)
    request_payload = _read(pending["human_decision_request"])
    request = HumanDecisionRequest.from_dict(request_payload, require_contract=True)
    decision = HumanDecision(
        request_id=request.request_id,
        action="APPROVE",
        actor_ref="OWNER",
        channel="TERMINAL",
    ).bind_request(request)
    ResearchB3Persistence(state_root / "m5").persist(
        "M5_SELECTION_CHANGE_DECISION",
        decision.to_dict(),
        artifact_id="RP-FIXTURE:M5:SELECTION_CHANGE:DECISION",
        artifact_kind="HumanDecision",
    )

    def thesis_only(request):
        assert request.stage == "M5_REFINED_THESIS"
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    result, seen = _run_m5(
        state_root,
        baseline=baseline,
        m4_result=m4_result,
        cognitive=thesis_only,
    )
    assert pending["status"] == "PENDING_HUMAN_DECISION"
    assert result["status"] == "READY_FOR_OWNER_REVIEW"
    assert [request.stage for request in seen] == ["M5_REFINED_THESIS"]
    assert _read(result["execution_manifest"])["effective_selected_work_ids"] == ["W1", "W3"]


@pytest.mark.parametrize("mutator,match", [
    (lambda value: value["material_contributions"][0].update(material_id="W-UNKNOWN"), "MATERIAL_CONTRIBUTION_WORK_INVALID"),
    (lambda value: value["evidence_dependencies"].append("EVIDENCE-NOT-VERIFIED"), "EVIDENCE_REF_UNRESOLVED"),
])
def test_m5_refined_thesis_rejects_uninvestigated_work_or_unverified_evidence(tmp_path, mutator, match):
    def bad_thesis(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        value = _thesis("RP-FIXTURE:THESIS:PROVISIONAL")
        mutator(value)
        return value

    with pytest.raises(ResearchB3Error, match=match):
        _run_m5(tmp_path, cognitive=bad_thesis)


@pytest.mark.parametrize("disposition", ["CONFIRMED", "MODIFIED", "REJECTED", "LIMITED"])
def test_m5_records_each_allowed_provisional_disposition(tmp_path, disposition):
    expected_rationale = {
        "CONFIRMED": "La conclusión central provisional sigue siendo defendible tras el deep research.",
        "MODIFIED": "El deep research cambia una parte material de la explicación y conserva una tesis descendiente defendible.",
        "REJECTED": "La evidencia obtenida hace indefendible la tesis provisional y obliga a abandonarla.",
        "LIMITED": "La dirección principal permanece, pero se reduce la fuerza y generalización de la tesis.",
    }[disposition]

    def cognitive(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return _claims()
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        value = _thesis("RP-FIXTURE:THESIS:PROVISIONAL")
        value["provisional_disposition"] = disposition
        value["refinement_rationale"] = expected_rationale
        return value

    result, _ = _run_m5(tmp_path, cognitive=cognitive)
    thesis = _read(result["refined_thesis"])
    assert thesis["provisional_disposition"] == disposition
    assert thesis["refinement_rationale"] == expected_rationale
    assert f"software:m5:provisional-disposition:{disposition}" in thesis["lineage"]


def test_m5_prompt_carries_post_deep_cognitive_boundary():
    prompt = Path("prompts/roles/RESEARCH_AND_CURATION/1.0.0.md").read_text(encoding="utf-8")
    assert "B3 Research V2 — M5 post-deep consolidation" in prompt
    assert "WORK_EVIDENCE" in prompt and "EXTERNAL_REALITY_EVIDENCE" in prompt
    assert "M5 does not produce `ResearchReadyManifest`" in prompt
    assert "viewer journey" in prompt
    assert "`supporting_evidence_refs` explicitly" in prompt
    assert "`affected_claim_ids` empty only when" in prompt
    assert "`missing_perspectives`" in prompt and "`overinterpretation_risk`" in prompt
    assert "central provisional conclusion remains defensible" in prompt
    assert "material part of the explanation changed" in prompt
    assert "must be reduced" in prompt
    assert "no longer defensible" in prompt
