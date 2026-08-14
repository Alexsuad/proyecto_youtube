"""Adversarial tests for R1-M9 specialist research contributions."""

from copy import deepcopy

from src.core.contract_validation import validate_research_pack
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
