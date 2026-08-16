"""Adversarial tests for R1-M9 specialist research contributions."""

from copy import deepcopy

from src.core.contract_validation import loads_strict_json, validate_research_pack
from tests.fixtures.synthetic_contracts import VALID_RESEARCH_PACK


def _specialist(*, status="COMPLETED"):
    value = {
        "specialist_research_id": "SR-1",
        "status": status,
        "responsibility_role_ref": "config/responsibility_registry.json#responsibilities/RESEARCH_AND_CURATION",
        "activation": {
            "activation_id": "ACT-1",
            "specialty": "historia cultural",
            "activation_reason": "La pregunta exige contexto especializado no cubierto por la investigación general.",
            "problem_nature": "interpretación histórica",
            "risk": "atribución histórica incorrecta",
            "sensitivity": "media",
            "complexity": "alta",
            "disciplinary_need": "contrastar historiografía rival",
            "research_question": "¿Qué explicación histórica rival debe conservarse?",
            "scope": "Contexto histórico de la obra y sus límites.",
            "affected_object_refs": ["I2"],
            "affected_claim_ids": [],
            "expected_limits": ["No autoriza por sí sola el claim ni la tesis."],
        },
        "authority_status": "SPECIALIST_CONTRIBUTION_ONLY",
        "does_not_establish": ["FACT", "CLAIM_AUTHORIZATION", "RESEARCH_SUFFICIENCY", "THESIS_APPROVAL"],
    }
    if status == "COMPLETED":
        value["contribution"] = {
            "contribution_id": "CONTR-1",
            "specialty": "historia cultural",
            "research_question": "¿Qué explicación histórica rival debe conservarse?",
            "scope": "Contexto histórico de la obra y sus límites.",
            "method": "comparación de fuentes primarias y análisis historiográfico",
            "source_refs": ["S1"],
            "findings": [{"finding_id": "F-1", "statement": "El contexto admite dos lecturas históricas.", "evidence_refs": ["S1"], "confidence": "MEDIUM"}],
            "rival_status": "NONE_IDENTIFIED",
            "rival_search_justification": "La búsqueda no encontró una posición rival material adicional en el alcance declarado.",
            "rival_positions": [],
            "limitations": ["La fuente disponible no cubre la recepción posterior."],
            "operational_limits": [{"limit_id": "L-1", "condition": "Si se usa para atribución histórica.", "effect": "Formular de modo condicional.", "return_route": "Volver a investigación especializada."}],
            "uncertainty": {"level": "MEDIUM", "statement": "La atribución permanece dependiente del contexto disponible.", "material": True, "impact_on_use": "No usar como afirmación histórica categórica."},
            "conflicts_of_interest": {"status": "NONE_DECLARED", "details": "No se declaró conflicto.", "mitigation": "Revisión de la procedencia y de posiciones rivales."},
            "affected_object_refs": ["I2"],
            "affected_claim_ids": [],
            "claim_dispositions": [],
            "claim_discoveries": [],
            "activation_relation": "WITHIN_ORIGINAL_MISSION",
            "activation_change_dimensions": [],
            "activation_change_description": "La contribución permanece dentro de la misión original.",
            "activation_reassessment_status": "NOT_REQUIRED",
            "claim_assessments": [],
        }
    return value


def _pack(specialist=None):
    pack = deepcopy(VALID_RESEARCH_PACK)
    if specialist is not None:
        pack["specialist_research"] = [specialist]
    return pack


def test_valid_adaptive_specialist_contribution_is_accepted():
    assert validate_research_pack(_pack(_specialist())) == []


def test_unlisted_specialty_is_open_when_justified():
    specialist = _specialist()
    specialist["activation"]["specialty"] = "astroarqueología"
    specialist["contribution"]["specialty"] = "astroarqueología"
    assert validate_research_pack(_pack(specialist)) == []


def test_existing_claim_can_be_referenced_and_supported():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "ASSESSED", "reason": "ASSESSMENT_COMPLETED", "justification": "Evaluado.", "evidence_refs": ["S1"]}]
    specialist["contribution"]["claim_assessments"] = [{"claim_id": "C-1", "support_level": "SUPPORTED", "rationale": "La fuente primaria respalda el alcance declarado.", "evidence_refs": ["S1"], "limitations": []}]
    pack = _pack(specialist)
    pack["claims_candidates"] = [{"item_id": "C-1", "statement": "Claim", "source_refs": ["S1"], "locator": "p. 1", "confidence": "HIGH"}]
    assert validate_research_pack(pack) == []


def test_specialty_requires_adaptive_activation():
    specialist = _specialist()
    del specialist["activation"]["activation_reason"]
    assert any("activation" in violation for violation in validate_research_pack(_pack(specialist)))


def test_specialist_contribution_requires_identity():
    specialist = _specialist()
    del specialist["contribution"]["contribution_id"]
    assert any("contribution_id" in violation for violation in validate_research_pack(_pack(specialist)))


def test_specialty_is_not_an_agent_identity():
    specialist = _specialist()
    specialist["agent_id"] = "agent-1"
    assert any("agent_id" in violation for violation in validate_research_pack(_pack(specialist)))


def test_supported_claim_requires_provenance_with_authority():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "ASSESSED", "reason": "ASSESSMENT_COMPLETED", "justification": "Evaluado.", "evidence_refs": ["S1"]}]
    specialist["contribution"]["claim_assessments"] = [{"claim_id": "C-1", "support_level": "SUPPORTED", "rationale": "Apoyo declarado.", "evidence_refs": ["S1"], "limitations": []}]
    pack = _pack(specialist)
    pack["claims_candidates"] = [{"item_id": "C-1", "statement": "Claim", "source_refs": ["S1"], "locator": "p. 1", "confidence": "HIGH"}]
    pack["source_registry"][0]["provenance"]["claim_authority"] = "NONE"
    assert any("autoridad suficiente" in violation for violation in validate_research_pack(pack))


def test_unknown_claim_cannot_be_assessed():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["UNKNOWN"]
    specialist["contribution"]["claim_assessments"] = [{"claim_id": "UNKNOWN", "support_level": "NOT_SUPPORTED", "rationale": "No se sostiene.", "evidence_refs": ["S1"], "limitations": ["Falta evidencia."]}]
    assert any("claims no declarados" in violation for violation in validate_research_pack(_pack(specialist)))


def test_incompatible_support_declarations_for_one_claim_are_rejected():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "ASSESSED", "reason": "ASSESSMENT_COMPLETED", "justification": "Evaluado.", "evidence_refs": ["S1"]}]
    specialist["contribution"]["claim_assessments"] = [
        {"claim_id": "C-1", "support_level": "SUPPORTED", "rationale": "Apoyo inicial.", "evidence_refs": ["S1"], "limitations": []},
        {"claim_id": "C-1", "support_level": "NOT_SUPPORTED", "rationale": "La evidencia no alcanza.", "evidence_refs": ["S1"], "limitations": ["Falta corroboración."]},
    ]
    pack = _pack(specialist)
    pack["claims_candidates"] = [{"item_id": "C-1", "statement": "Claim", "source_refs": ["S1"], "locator": "p. 1", "confidence": "HIGH"}]
    assert any("niveles de soporte incompatibles" in violation for violation in validate_research_pack(pack))


def test_limited_claim_requires_explicit_limits():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "ASSESSED", "reason": "ASSESSMENT_COMPLETED", "justification": "Evaluado.", "evidence_refs": ["S1"]}]
    specialist["contribution"]["claim_assessments"] = [{"claim_id": "C-1", "support_level": "LIMITED", "rationale": "Apoyo parcial.", "evidence_refs": ["S1"], "limitations": []}]
    pack = _pack(specialist)
    pack["claims_candidates"] = [{"item_id": "C-1", "statement": "Claim", "source_refs": ["S1"], "locator": "p. 1", "confidence": "HIGH"}]
    assert any("limitaciones explícitas" in violation for violation in validate_research_pack(pack))


def test_rival_without_sources_is_rejected():
    specialist = _specialist()
    specialist["contribution"]["rival_status"] = "PRESENT"
    specialist["contribution"].pop("rival_search_justification")
    specialist["contribution"]["rival_positions"] = [{"position_id": "R-1", "statement": "Rival", "evidence_refs": [], "treatment": "OPEN"}]
    assert validate_research_pack(_pack(specialist))


def test_declared_material_rival_cannot_be_omitted():
    specialist = _specialist()
    specialist["contribution"]["rival_status"] = "PRESENT"
    specialist["contribution"]["rival_positions"] = []
    assert any("minItems" in violation or "rival_positions" in violation for violation in validate_research_pack(_pack(specialist)))


def test_generic_limit_is_not_enough_for_unresolved_claim():
    specialist = _specialist()
    specialist["contribution"].pop("operational_limits")
    assert any("operational_limits" in violation for violation in validate_research_pack(_pack(specialist)))


def test_conflict_of_interest_and_uncertainty_are_mandatory():
    specialist = _specialist()
    specialist["contribution"].pop("conflicts_of_interest")
    specialist["contribution"].pop("uncertainty")
    assert validate_research_pack(_pack(specialist))


def test_specialist_cannot_create_parallel_claim_ledger_or_authority():
    specialist = _specialist()
    specialist["authority_status"] = "CLAIM_AUTHORIZED"
    specialist["contribution"]["claim_decision"] = "CLAIM_ALLOWED"
    assert validate_research_pack(_pack(specialist))


def test_planned_activation_can_exist_without_contribution():
    assert validate_research_pack(_pack(_specialist(status="PLANNED"))) == []


def _claim_pack(specialist, claim_ids):
    pack = _pack(specialist)
    pack["claims_candidates"] = [
        {"item_id": claim_id, "statement": f"Claim {claim_id}", "source_refs": ["S1"], "locator": "p. 1", "confidence": "HIGH"}
        for claim_id in claim_ids
    ]
    return pack


def _assessed(claim_id):
    return {"claim_id": claim_id, "disposition": "ASSESSED", "reason": "ASSESSMENT_COMPLETED", "justification": "Evaluado en la contribución.", "evidence_refs": ["S1"]}


def _assessment(claim_id, level="SUPPORTED"):
    return {"claim_id": claim_id, "support_level": level, "rationale": "Resultado explícito.", "evidence_refs": ["S1"], "limitations": [] if level == "SUPPORTED" else ["Alcance limitado."]}


def _discovered(claim_id="C-2", relation="NEW_CLAIM_WITHIN_ORIGINAL_SCOPE"):
    return {"claim_id": claim_id, "discovery_origin": "INVESTIGATIVE_DISCOVERY", "activation_ref": "ACT-1", "discovery_reason": "La evidencia reveló un claim relacionado durante la investigación.", "evidence_refs": ["S1"], "scope_relation": relation}


def test_initial_claims_must_all_be_assessed_or_disposed():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1", "C-2"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1", "C-2"]
    specialist["contribution"]["claim_dispositions"] = [_assessed("C-1"), _assessed("C-2")]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-1"), _assessment("C-2")]
    assert validate_research_pack(_claim_pack(specialist, ["C-1", "C-2"])) == []


def test_initial_claim_disappearing_without_disposition_is_rejected():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1", "C-2"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [_assessed("C-1")]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-1")]
    assert any("disposición final" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-1", "C-2"])))


def test_initial_claim_can_be_explicitly_not_assessed():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1", "C-2"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [_assessed("C-1"), {"claim_id": "C-2", "disposition": "NOT_ASSESSED", "reason": "INSUFFICIENT_EVIDENCE", "justification": "No se obtuvo evidencia suficiente.", "evidence_refs": ["S1"]}]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-1")]
    assert validate_research_pack(_claim_pack(specialist, ["C-1", "C-2"])) == []


def test_not_assessed_requires_reason():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "NOT_ASSESSED", "justification": "No pudo evaluarse.", "evidence_refs": ["S1"]}]
    assert validate_research_pack(_claim_pack(specialist, ["C-1"]))


def test_no_longer_relevant_requires_justification():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "NOT_ASSESSED", "reason": "NO_LONGER_RELEVANT", "evidence_refs": ["S1"]}]
    assert validate_research_pack(_claim_pack(specialist, ["C-1"]))


def test_final_affected_claim_requires_exactly_one_assessment():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_assessments"] = []
    assert any("exactamente un assessment" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-1"])))


def test_duplicate_assessments_are_rejected():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-1"), _assessment("C-1", "LIMITED")]
    assert any("no puede duplicar" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-1"])))


def test_not_supported_cannot_replace_not_assessed():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "NOT_ASSESSED", "reason": "INSUFFICIENT_EVIDENCE", "justification": "No se investigó finalmente.", "evidence_refs": ["S1"]}]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-1", "NOT_SUPPORTED")]
    assert any("NOT_ASSESSED" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-1"])))


def test_new_claim_within_scope_keeps_discovery_lineage():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["affected_claim_ids"] = ["C-1", "C-2"]
    specialist["contribution"]["claim_dispositions"] = [_assessed("C-1")]
    specialist["contribution"]["claim_discoveries"] = [_discovered()]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-1"), _assessment("C-2", "LIMITED")]
    assert validate_research_pack(_claim_pack(specialist, ["C-1", "C-2"])) == []


def test_new_claim_without_discovery_trace_is_rejected():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-2"]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-2")]
    assert any("descubrimiento trazable" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-2"])))


def test_new_claim_requires_activation_relationship():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-2"]
    specialist["contribution"]["claim_discoveries"] = [{**_discovered(), "activation_ref": "OTHER-ACTIVATION"}]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-2")]
    assert any("activation_ref" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-2"])))


def test_new_claim_requires_originating_evidence():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-2"]
    specialist["contribution"]["claim_discoveries"] = [{**_discovered(), "evidence_refs": []}]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-2")]
    assert validate_research_pack(_claim_pack(specialist, ["C-2"]))


def test_material_mission_change_requires_activation_reassessment():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-2"]
    specialist["contribution"]["claim_discoveries"] = [_discovered(relation="ACTIVATION_REASSESSMENT_REQUIRED")]
    specialist["contribution"]["claim_assessments"] = [_assessment("C-2")]
    assert any("ACTIVATION_REASSESSMENT_REQUIRED" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-2"])))


def test_material_mission_change_can_be_explicitly_reassessed():
    specialist = _specialist()
    specialist["contribution"]["affected_claim_ids"] = ["C-2"]
    specialist["contribution"]["claim_discoveries"] = [_discovered(relation="ACTIVATION_REASSESSMENT_REQUIRED")]
    specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
    specialist["contribution"]["activation_change_dimensions"] = ["QUESTION"]
    specialist["contribution"]["activation_change_description"] = "El descubrimiento exige una pregunta especializada distinta."
    specialist["contribution"]["activation_reassessment_status"] = "REQUIRED"
    specialist["contribution"]["activation_reassessment_reason"] = "El nuevo claim requiere otra pregunta especializada."
    specialist["contribution"]["claim_assessments"] = [_assessment("C-2")]
    assert validate_research_pack(_claim_pack(specialist, ["C-2"])) == []


def test_same_mission_explicitly_remains_not_required():
    specialist = _specialist()
    assert validate_research_pack(_pack(specialist)) == []


def test_non_material_reformulation_within_scope_passes():
    specialist = _specialist()
    specialist["contribution"]["research_question"] = "Pregunta refinada sin cambio de misión."
    specialist["contribution"]["activation_change_description"] = "Reformulación no material dentro del alcance original."
    assert validate_research_pack(_pack(specialist)) == []


def test_material_question_change_without_new_claim_can_require_reassessment():
    specialist = _specialist()
    specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
    specialist["contribution"]["activation_change_dimensions"] = ["QUESTION"]
    specialist["contribution"]["activation_change_description"] = "La pregunta especializada cambió materialmente."
    specialist["contribution"]["activation_reassessment_status"] = "REQUIRED"
    specialist["contribution"]["activation_reassessment_reason"] = "La misión original ya no cubre la pregunta resultante."
    assert validate_research_pack(_pack(specialist)) == []


def test_material_specialty_scope_and_object_changes_require_reassessment():
    for dimension in ("SPECIALTY", "SCOPE", "OBJECT"):
        specialist = _specialist()
        specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
        specialist["contribution"]["activation_change_dimensions"] = [dimension]
        specialist["contribution"]["activation_change_description"] = f"Cambio material declarado en {dimension}."
        specialist["contribution"]["activation_reassessment_status"] = "REQUIRED"
        specialist["contribution"]["activation_reassessment_reason"] = "La misión requiere reevaluación explícita."
        assert validate_research_pack(_pack(specialist)) == []


def test_material_specialty_change_is_valid_when_explicitly_reassessed():
    specialist = _specialist()
    specialist["contribution"]["specialty"] = "derecho"
    specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
    specialist["contribution"]["activation_change_dimensions"] = ["SPECIALTY"]
    specialist["contribution"]["activation_change_description"] = "La especialidad requerida cambió materialmente."
    specialist["contribution"]["activation_reassessment_status"] = "REQUIRED"
    specialist["contribution"]["activation_reassessment_reason"] = "La pregunta requiere ahora conocimiento jurídico."
    assert validate_research_pack(_pack(specialist)) == []


def test_specialty_change_cannot_be_within_original_mission():
    specialist = _specialist()
    specialist["contribution"]["specialty"] = "derecho"
    assert any("no puede cambiar especialidad" in violation for violation in validate_research_pack(_pack(specialist)))


def test_specialty_change_requires_specialty_dimension():
    specialist = _specialist()
    specialist["contribution"]["specialty"] = "derecho"
    specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
    specialist["contribution"]["activation_change_dimensions"] = ["QUESTION"]
    specialist["contribution"]["activation_change_description"] = "Cambio material declarado."
    specialist["contribution"]["activation_reassessment_status"] = "REQUIRED"
    specialist["contribution"]["activation_reassessment_reason"] = "La misión requiere reevaluación."
    assert any("dimensión SPECIALTY" in violation for violation in validate_research_pack(_pack(specialist)))


def test_specialty_change_cannot_remain_not_required():
    specialist = _specialist()
    specialist["contribution"]["specialty"] = "derecho"
    specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
    specialist["contribution"]["activation_change_dimensions"] = ["SPECIALTY"]
    specialist["contribution"]["activation_change_description"] = "Cambio material declarado."
    assert any("cambio de especialidad requiere ACTIVATION_REASSESSMENT_REQUIRED=YES" in violation for violation in validate_research_pack(_pack(specialist)))


def test_not_assessed_blocked_by_prerequisite_allows_no_evidence_refs():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "NOT_ASSESSED", "reason": "BLOCKED_BY_PREREQUISITE", "justification": "Falta el prerrequisito de acceso."}]
    assert validate_research_pack(_claim_pack(specialist, ["C-1"])) == []


def test_not_assessed_insufficient_evidence_allows_no_evidence_refs():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "NOT_ASSESSED", "reason": "INSUFFICIENT_EVIDENCE", "justification": "No se obtuvo evidencia suficiente."}]
    assert validate_research_pack(_claim_pack(specialist, ["C-1"])) == []


def test_not_assessed_unknown_declared_evidence_is_rejected():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["C-1"]
    specialist["contribution"]["claim_dispositions"] = [{"claim_id": "C-1", "disposition": "NOT_ASSESSED", "reason": "INSUFFICIENT_EVIDENCE", "justification": "No se obtuvo evidencia suficiente.", "evidence_refs": ["UNKNOWN"]}]
    assert any("evidencia no declarada" in violation for violation in validate_research_pack(_claim_pack(specialist, ["C-1"])))


def test_material_change_hidden_by_not_required_is_rejected():
    specialist = _specialist()
    specialist["contribution"]["activation_relation"] = "MATERIAL_MISSION_CHANGE"
    specialist["contribution"]["activation_change_dimensions"] = ["SCOPE"]
    specialist["contribution"]["activation_change_description"] = "El alcance cambió materialmente."
    assert any("mantiene ACTIVATION_REASSESSMENT_REQUIRED=NO" in violation for violation in validate_research_pack(_pack(specialist)))


def test_required_without_material_change_or_discovery_is_rejected():
    specialist = _specialist()
    specialist["contribution"]["activation_reassessment_status"] = "REQUIRED"
    specialist["contribution"]["activation_reassessment_reason"] = "Se solicita reevaluación."
    assert any("sin cambio material" in violation for violation in validate_research_pack(_pack(specialist)))


def test_text_difference_does_not_infer_materiality():
    specialist = _specialist()
    specialist["activation"]["research_question"] = "Pregunta original."
    specialist["contribution"]["research_question"] = "Pregunta reformulada."
    assert validate_research_pack(_pack(specialist)) == []


def test_activation_original_is_preserved():
    specialist = _specialist()
    original = dict(specialist["activation"])
    validate_research_pack(_pack(specialist))
    assert specialist["activation"] == original


def test_initial_unknown_claim_remains_rejected():
    specialist = _specialist()
    specialist["activation"]["affected_claim_ids"] = ["DOES_NOT_EXIST"]
    assert any("claims no declarados" in violation for violation in validate_research_pack(_pack(specialist)))


def test_duplicate_json_members_are_rejected_before_schema_validation():
    try:
        loads_strict_json('{"capability_id":"A","capability_id":"B"}')
    except ValueError as exc:
        assert "duplicate JSON key" in str(exc)
    else:
        raise AssertionError("duplicate JSON member was silently accepted")


def test_contribution_evidence_must_be_declared_by_contribution():
    specialist = _specialist()
    specialist["contribution"]["findings"][0]["evidence_refs"] = ["S2"]
    pack = _pack(specialist)
    pack["source_registry"].append({**pack["source_registry"][0], "source_id": "S2"})
    violations = validate_research_pack(pack)
    assert any("fuera de contribution.source_refs" in violation for violation in violations)


def test_specialist_identity_ids_are_unique_within_research_pack():
    first = _specialist()
    second = deepcopy(first)
    second["activation"]["activation_id"] = "ACT-2"
    second["contribution"]["contribution_id"] = "CONTR-2"
    second["contribution"]["findings"][0]["finding_id"] = "F-2"
    second["contribution"]["operational_limits"][0]["limit_id"] = "L-2"
    pack = _pack(first)
    pack["specialist_research"] = [first, second]
    violations = validate_research_pack(pack)
    assert any("specialist_research_id duplicado" in violation for violation in violations)
