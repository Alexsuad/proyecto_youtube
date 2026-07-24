"""Pruebas B5-I1 para entrada editorial canónica."""
from __future__ import annotations

import copy
import hashlib
import json
import socket
from pathlib import Path

from src.core.contract_validation import (
    validate_against_schema,
    validate_source_access_and_evidence_report,
    validate_thesis_artifact,
)
from src.core.status import GateStatus
from src.scripts.evidence_sufficiency_gate import evaluate as evaluate_evidence
from src.scripts.qa_brief_research import evaluate as evaluate_brief_research
from src.scripts.thesis_provisional_gate import evaluate as evaluate_thesis_gate
from src.scripts.semantic_sufficiency_gate import evaluate as evaluate_semantic_gate

CHECKSUM = "a" * 64


def valid_brief() -> dict:
    return {
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "profile_id": "mas_alla_del_guion",
        "profile_version": "1.1.0",
        "profile_checksum": CHECKSUM,
        "tema": "Miedo al fracaso",
        "pregunta_central": "¿Por qué evitamos aquello que más deseamos?",
        "conflicto_o_tension": "Deseo de avanzar frente al miedo a equivocarse.",
        "initial_editorial_hypothesis": {"statement": "Confundir el error con la identidad amplifica el miedo.", "status": "HYPOTHESIS_UNAPPROVED", "research_role": "ORIENTS_RESEARCH_NOT_APPROVED_THESIS", "revisable": True, "adversarial_research_required": True},
        "objetivo": "Comprender el coste de evitar el error.",
        "transformacion_esperada": "Interpretar el fracaso como información.",
        "audiencia_concreta": "Adultos que posponen decisiones importantes.",
        "audience_status": "INITIAL_HYPOTHESIS",
        "angulo_diferencial": "Contrastar respuestas narrativas distintas al error.",
        "alcance": "Consecuencias humanas y narrativas.",
        "fuera_de_alcance": "Diagnóstico clínico.",
        "spoilers": "SI_LIMITADOS",
        "tono": "Cercano y riguroso.",
        "duracion_objetivo": "18 minutos",
        "ritmo_locucion": "130 palabras por minuto",
        "nivel_investigacion": "PROFUNDO",
        "fuentes_requeridas": ["obra principal", "fuente conceptual"],
        "narrative_materials": ["Obra sintética"],
        "tipo_de_guion_principal": "VIDEOENSAYO_NARRATIVO",
        "tipo_de_guion_secundario": None,
        "estructura_candidata": "creencia-evidencia-reinterpretación",
        "structure_status": "INITIAL_HYPOTHESIS_REVISABLE_AFTER_RESEARCH",
        "razon_eleccion_estructura": "Permite transformar la lectura inicial.",
        "citation_style": "Atribución narrativa con registro interno.",
        "attribution_policy": "Atribuir hechos e ideas específicas.",
        "quotation_policy": "Citas breves y verificadas.",
        "source_visibility": "PUBLIC_SUMMARY",
        "salida_esperada": "Diseño listo para B5-I2.",
        "created_at": "2026-07-23T20:00:00Z",
    }


def source(source_id: str) -> dict:
    return {
        "source_id": source_id,
        "title": f"Fuente {source_id}",
        "source_type": "PRIMARY",
        "url": f"https://example.com/{source_id}",
        "access_type": "DIRECT",
        "locator": "documento completo",
        "confidence": "HIGH",
    }


def item(item_id: str, source_id: str = "S1") -> dict:
    return {
        "item_id": item_id,
        "statement": f"Hallazgo {item_id}",
        "source_refs": [source_id],
        "locator": "p. 10",
        "confidence": "HIGH",
    }


def valid_research(source_count: int = 3) -> dict:
    sources = [source(f"S{i}") for i in range(1, source_count + 1)]
    return {
        "research_id": "RP-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "scope": "Cobertura conceptual y narrativa.",
        "facts": [item("F1")],
        "interpretations": [item("I1")],
        "hypotheses": [],
        "contradictions": [],
        "alternative_views": [item("A1")],
        "coverage": [{"dimension_id": dimension, "status": "COVERED", "related_finding_ids": ["F1"], "related_source_ids": ["S1"], "limitation_or_pending": None, "scope_decision": "NONE", "editorial_impact": "NOT_APPLICABLE", "propagated_constraint": None, "mitigation_status": "NOT_REQUIRED"} for dimension in ["CENTRAL_QUESTION", "CONFLICT", "INITIAL_HYPOTHESIS", "HUMAN_SOCIAL_HISTORICAL_OR_CULTURAL_PHENOMENON", "PRIMARY_NARRATIVE_MATERIAL", "CRITICAL_CLAIMS", "ALTERNATIVE_PERSPECTIVES"]],
        "critical_claims_assessment": {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL"},
        "narrative_evidence": [{**item("N1"), "evidence_kind": "SCENE"}],
        "external_reality_evidence": [{**item("E1"), "evidence_kind": "STUDY"}],
        "source_registry": sources,
        "claims_candidates": [],
        "unsupported_claims": [],
        "narrative_opportunities": [],
        "limitations": [],
        "created_at": "2026-07-23T20:00:00Z",
    }


def valid_report() -> dict:
    return {
        "report_id": "ER-001",
        "episode_id": "EP-001",
        "research_id": "RP-001",
        "brief_version": "1.0.0",
        "material_principal_disponible": True,
        "tipo_de_acceso": "DIRECT",
        "fuentes_primarias": [
            {
                "source_id": "S1",
                "title": "Fuente oficial",
                "url": "https://example.com/S1",
                "access_type": "DIRECT",
                "locator": "documento completo",
                "confidence": "HIGH",
            }
        ],
        "fuentes_secundarias": [],
        "escenas_verificadas": [
            {
                "scene_id": "SC1",
                "description": "Escena verificada.",
                "source_id": "S1",
                "locator": "00:10:00",
                "verification_mode": "DIRECT",
            }
        ],
        "escenas_descritas_indirectamente": [],
        "claims_sostenibles": [],
        "claims_pendientes": [],
        "limitaciones": [],
        "nivel_de_confianza": "HIGH",
        "can_proceed": True,
        "required_disclosures": [],
        "allowed_analyses": ["CONTEXTUAL_ANALYSIS"],
        "limited_analyses": [],
        "prohibited_analyses": [],
        "excluded_claims": [],
        "propagated_constraints": [],
        "critical_claim_assessments": [{"claim_id": "C1", "claim_text": "Claim central.", "support_status": "SUPPORTED", "confidence": "HIGH", "allowed_scope": "Contexto del episodio", "evidence_refs": ["S1"]}],
        "critical_claims_propagation": {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL", "scope_decision": "CONTINUE_WITH_REVIEW"},
        "sufficiency_basis": {"central_question": "¿Por qué evitamos aquello que más deseamos?", "critical_claims": [], "analysis_type": "CONTEXTUAL_ANALYSIS", "material_roles": ["PRIMARY_NARRATIVE_MATERIAL"], "requested_depth": "PROFUNDO", "research_coverage": "Cobertura revisada"},
        "created_at": "2026-07-23T20:00:00Z",
    }


def write_inputs(tmp_path: Path, brief: dict | None = None, research: dict | None = None) -> tuple[Path, Path]:
    ep = tmp_path / "ep"
    ep.mkdir()
    (ep / "episode_brief.json").write_text(json.dumps(brief or valid_brief()), encoding="utf-8")
    (ep / "research_pack.json").write_text(json.dumps(research or valid_research()), encoding="utf-8")
    active = tmp_path / "active.json"
    active.write_text(
        json.dumps(
            {
                "ACTIVE_PROFILE_ID": "mas_alla_del_guion",
                "ACTIVE_PROFILE_VERSION": "1.1.0",
                "profile_checksum": CHECKSUM,
            }
        ),
        encoding="utf-8",
    )
    return ep, active


def test_episode_brief_requires_profile_checksum() -> None:
    brief = valid_brief()
    del brief["profile_checksum"]
    violations = validate_against_schema(brief, "episode_brief")
    assert any("profile_checksum" in violation for violation in violations)


def test_active_profile_must_match_exactly(tmp_path: Path) -> None:
    brief = valid_brief()
    brief["profile_checksum"] = "b" * 64
    ep, active = write_inputs(tmp_path, brief=brief)
    result = evaluate_brief_research(ep, active_profile_path=active)
    assert result.status is GateStatus.FAIL
    assert any("profile_checksum" in violation for violation in result.violations)


def test_brief_contains_type_structure_and_source_policies() -> None:
    assert validate_against_schema(valid_brief(), "episode_brief") == []


def test_three_good_sources_are_valid_without_eight_url_minimum(tmp_path: Path) -> None:
    ep, active = write_inputs(tmp_path, research=valid_research(source_count=3))
    result = evaluate_brief_research(ep, active_profile_path=active)
    assert result.status is GateStatus.PASS
    assert result.evidence["source_count"] == 3


def test_research_separates_fact_interpretation_and_hypothesis() -> None:
    research = valid_research()
    research["hypotheses"] = [item("H1")]
    assert validate_against_schema(research, "research_pack") == []
    assert research["facts"] != research["interpretations"] != research["hypotheses"]


def test_research_entry_without_locator_fails() -> None:
    research = valid_research()
    del research["facts"][0]["locator"]
    violations = validate_against_schema(research, "research_pack")
    assert any("locator" in violation for violation in violations)


def test_formal_but_empty_evidence_does_not_pass(tmp_path: Path) -> None:
    report = valid_report()
    report["fuentes_primarias"] = []
    report["escenas_verificadas"] = []
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    result = evaluate_evidence(path, "EP-001")
    assert result.status is GateStatus.FAIL


def test_can_proceed_false_blocks(tmp_path: Path) -> None:
    report = valid_report()
    report["can_proceed"] = False
    report["limitaciones"] = ["No se verificó la obra principal."]
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    result = evaluate_evidence(path, "EP-001")
    assert result.status is GateStatus.BLOCKED
    assert result.exit_code == 2


def test_declared_limitations_warn(tmp_path: Path) -> None:
    report = valid_report()
    report["limitaciones"] = ["Una escena se verificó solo parcialmente."]
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    result = evaluate_evidence(path, "EP-001")
    assert result.status is GateStatus.WARN
    assert result.exit_code == 0


def test_provisional_thesis_requires_research_and_evidence_lineage() -> None:
    thesis = {
        "thesis_id": "TH-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "stage": "THESIS_PROVISIONAL",
        "statement": "Tesis provisional.",
        "premises": [{"premise_id": "P1", "statement": "Premisa trazable.", "finding_ids": ["F1"], "source_refs": ["S1"]}],
        "supporting_findings": ["F1"],
        "tensioning_evidence": [{"finding_id": "I1", "explanation": "La interpretación tensiona la formulación."}],
        "alternative_explanations": ["Explicación alternativa."],
        "assumptions": ["Supuesto declarado."],
        "revision_conditions": ["Nueva evidencia relevante."],
        "inherited_constraints": [],
        "open_questions": ["¿Qué evidencia puede cambiarla?"],
        "version": "1.0.0",
        "created_at": "2026-07-23T20:00:00Z",
    }
    assert validate_against_schema(thesis, "thesis_artifact") == []


def test_provisional_and_refined_stages_are_not_confused() -> None:
    skill = Path(".agent/skills/skill_sintesis_tesis.md").read_text(encoding="utf-8")
    assert "THESIS_REFINED" in skill
    assert "bloqueado hasta B5-I2" in skill


def test_workflow_stops_before_curation_and_outline() -> None:
    workflow = Path(".agent/workflows/01_pipeline_episodio.md").read_text(encoding="utf-8")
    assert "READY_FOR_TEAM_02_FUNCTIONAL_REAUDIT" in workflow
    assert "no autoriza B5-I2" in workflow
    assert "03_mapa_eventos.md" not in workflow


def test_evaluation_makes_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    def forbidden_socket(*args, **kwargs):
        raise AssertionError("No se permiten llamadas externas")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    ep, active = write_inputs(tmp_path)
    assert evaluate_brief_research(ep, active_profile_path=active).status is GateStatus.PASS
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(valid_report()), encoding="utf-8")
    assert evaluate_evidence(report_path, "EP-001").status is GateStatus.PASS


# ─── B5-I1 correction tests: evidence gate falsos PASS ───


def write_report(report: dict, tmp_path: Path, name: str = "report.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(report), encoding="utf-8")
    return p


def test_unavailable_with_can_proceed_true_blocks(tmp_path: Path) -> None:
    report = valid_report()
    report["tipo_de_acceso"] = "UNAVAILABLE"
    report["can_proceed"] = True
    path = write_report(report, tmp_path)
    result = evaluate_evidence(path, "EP-001")
    assert result.status is GateStatus.BLOCKED
    assert result.exit_code == 2


def test_global_low_confidence_blocks(tmp_path: Path) -> None:
    report = valid_report()
    report["nivel_de_confianza"] = "LOW"
    path = write_report(report, tmp_path)
    result = evaluate_evidence(path, "EP-001")
    assert result.status is GateStatus.BLOCKED
    assert result.exit_code == 2


def test_indirect_access_with_medium_confidence_warns(tmp_path: Path) -> None:
    report = valid_report()
    report["tipo_de_acceso"] = "INDIRECT"
    report["nivel_de_confianza"] = "MEDIUM"
    report["prohibited_analyses"] = ["CLOSE_SCENE_ANALYSIS", "UNSUPPORTED_AUTHORIAL_INTENT", "PRIMARY_EVIDENCE_FOR_DEEP_READING"]
    report["required_disclosures"] = ["Acceso indirecto declarado."]
    report["propagated_constraints"] = ["Acceso indirecto declarado."]
    path = write_report(report, tmp_path)
    result = evaluate_evidence(path, "EP-001")
    assert result.status is GateStatus.WARN
    assert result.exit_code == 0


def test_indirect_scene_in_escenas_verificadas_fails(tmp_path: Path) -> None:
    report = valid_report()
    report["escenas_verificadas"] = [
        {
            "scene_id": "SC_BAD",
            "description": "Escena con modo incorrecto.",
            "source_id": "S1",
            "locator": "00:15:00",
            "verification_mode": "INDIRECT",
        }
    ]
    report["escenas_descritas_indirectamente"] = []
    violations = validate_source_access_and_evidence_report(report)
    assert any("verification_mode" in v for v in violations)


def test_direct_scene_in_escenas_descritas_indirectamente_fails(tmp_path: Path) -> None:
    report = valid_report()
    report["escenas_descritas_indirectamente"] = [
        {
            "scene_id": "SC_BAD2",
            "description": "Escena directa mal colocada.",
            "source_id": "S1",
            "locator": "00:20:00",
            "verification_mode": "DIRECT",
        }
    ]
    violations = validate_source_access_and_evidence_report(report)
    assert any("verification_mode" in v for v in violations)


def _valid_thesis() -> dict:
    return {
        "thesis_id": "TH-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "stage": "THESIS_PROVISIONAL",
        "statement": "Tesis provisional de prueba.",
        "premises": [{"premise_id": "P1", "statement": "Premisa trazable.", "finding_ids": ["F1"], "source_refs": ["S1"]}],
        "supporting_findings": ["F1"],
        "tensioning_evidence": [{"finding_id": "F1", "explanation": "El alcance de este hallazgo obliga a matizar."}],
        "alternative_explanations": ["Explicación alternativa."],
        "assumptions": ["Supuesto declarado."],
        "revision_conditions": ["Nueva evidencia relevante."],
        "inherited_constraints": [],
        "open_questions": ["?Se sostiene con mas evidencia?"],
        "version": "1.0.0",
        "created_at": "2026-07-23T20:00:00Z",
    }


def _valid_research_dict() -> dict:
    return {
        "research_id": "RP-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "scope": "Cobertura de prueba.",
        "facts": [{"item_id": "F1", "statement": "Hecho.", "source_refs": ["S1"], "locator": "p.5", "confidence": "HIGH"}],
        "interpretations": [],
        "hypotheses": [],
        "contradictions": [],
        "alternative_views": [{"item_id": "A1", "statement": "Alternativa.", "source_refs": ["S2"], "locator": "web", "confidence": "MEDIUM"}],
        "coverage": [{"dimension_id": dimension, "status": "COVERED", "related_finding_ids": ["F1"], "related_source_ids": ["S1"], "limitation_or_pending": None, "scope_decision": "NONE", "editorial_impact": "NOT_APPLICABLE", "propagated_constraint": None, "mitigation_status": "NOT_REQUIRED"} for dimension in ["CENTRAL_QUESTION", "CONFLICT", "INITIAL_HYPOTHESIS", "HUMAN_SOCIAL_HISTORICAL_OR_CULTURAL_PHENOMENON", "PRIMARY_NARRATIVE_MATERIAL", "CRITICAL_CLAIMS", "ALTERNATIVE_PERSPECTIVES"]],
        "critical_claims_assessment": {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL"},
        "narrative_evidence": [{"item_id": "N1", "statement": "Escena.", "source_refs": ["S1"], "locator": "00:10", "confidence": "HIGH", "evidence_kind": "SCENE"}],
        "external_reality_evidence": [{"item_id": "E1", "statement": "Estudio.", "source_refs": ["S2"], "locator": "web", "confidence": "MEDIUM", "evidence_kind": "STUDY"}],
        "source_registry": [
            {"source_id": "S1", "title": "Fuente 1", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "doc", "confidence": "HIGH"},
            {"source_id": "S2", "title": "Fuente 2", "source_type": "SECONDARY", "access_type": "INDIRECT", "locator": "web", "confidence": "MEDIUM"},
        ],
        "claims_candidates": [],
        "unsupported_claims": [],
        "narrative_opportunities": [],
        "limitations": [],
        "created_at": "2026-07-23T20:00:00Z",
    }


def _valid_evidence_dict() -> dict:
    return {
        "report_id": "ER-001",
        "episode_id": "EP-001",
        "research_id": "RP-001",
        "brief_version": "1.0.0",
        "material_principal_disponible": True,
        "tipo_de_acceso": "DIRECT",
        "fuentes_primarias": [
            {"source_id": "S1", "title": "Fuente 1", "access_type": "DIRECT", "locator": "doc", "confidence": "HIGH"},
        ],
        "fuentes_secundarias": [
            {"source_id": "S2", "title": "Fuente 2", "access_type": "INDIRECT", "locator": "web", "confidence": "MEDIUM"},
        ],
        "escenas_verificadas": [
            {"scene_id": "SC1", "description": "Escena.", "source_id": "S1", "locator": "00:10", "verification_mode": "DIRECT"},
        ],
        "escenas_descritas_indirectamente": [],
        "claims_sostenibles": [],
        "claims_pendientes": [],
        "limitaciones": [],
        "nivel_de_confianza": "HIGH",
        "can_proceed": True,
        "required_disclosures": [],
        "allowed_analyses": ["CONTEXTUAL_ANALYSIS"],
        "limited_analyses": [],
        "prohibited_analyses": [],
        "excluded_claims": [],
        "propagated_constraints": [],
        "critical_claim_assessments": [{"claim_id": "C1", "claim_text": "Claim central.", "support_status": "SUPPORTED", "confidence": "HIGH", "allowed_scope": "Contexto del episodio", "evidence_refs": ["S1"]}],
        "critical_claims_propagation": {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL", "scope_decision": "CONTINUE_WITH_REVIEW"},
        "sufficiency_basis": {"central_question": "Pregunta", "critical_claims": [], "analysis_type": "CONTEXTUAL_ANALYSIS", "material_roles": ["PRIMARY_NARRATIVE_MATERIAL"], "requested_depth": "ESTANDAR", "research_coverage": "Cobertura revisada"},
        "created_at": "2026-07-23T20:00:00Z",
    }


def test_thesis_refined_stage_fails(tmp_path: Path) -> None:
    thesis = _valid_thesis()
    thesis["stage"] = "THESIS_REFINED"
    violations = validate_thesis_artifact(thesis, _valid_research_dict(), _valid_evidence_dict())
    assert any("THESIS_REFINED" in v for v in violations)


def test_thesis_source_ref_not_in_research_fails(tmp_path: Path) -> None:
    thesis = _valid_thesis()
    thesis["premises"][0]["source_refs"] = ["S99"]
    violations = validate_thesis_artifact(thesis, _valid_research_dict(), _valid_evidence_dict())
    assert any("S99" in v for v in violations)


def test_thesis_source_ref_in_research_but_not_in_evidence_fails(tmp_path: Path) -> None:
    research = _valid_research_dict()
    research["source_registry"].append(
        {"source_id": "S3", "title": "Fuente 3", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "doc", "confidence": "HIGH"}
    )
    thesis = _valid_thesis()
    thesis["premises"][0]["source_refs"] = ["S3"]
    violations = validate_thesis_artifact(thesis, research, _valid_evidence_dict())
    assert any("S3" in v for v in violations)


def test_cross_artifact_id_mismatch_fails(tmp_path: Path) -> None:
    thesis_dict = _valid_thesis()
    thesis_dict["episode_id"] = "EP-999"
    research_dict = _valid_research_dict()
    evidence_dict = _valid_evidence_dict()
    thesis_p = tmp_path / "thesis.json"
    research_p = tmp_path / "research.json"
    evidence_p = tmp_path / "evidence.json"
    thesis_p.write_text(json.dumps(thesis_dict), encoding="utf-8")
    research_p.write_text(json.dumps(research_dict), encoding="utf-8")
    evidence_p.write_text(json.dumps(evidence_dict), encoding="utf-8")
    result = evaluate_thesis_gate(thesis_p, research_p, evidence_p, "TH-001")
    assert result.status is GateStatus.FAIL
    assert any("episode_id" in v for v in result.violations)


def test_valid_provisional_thesis_with_pass_evidence_passes(tmp_path: Path) -> None:
    thesis_dict = _valid_thesis()
    research_dict = _valid_research_dict()
    evidence_dict = _valid_evidence_dict()
    thesis_p = tmp_path / "thesis.json"
    research_p = tmp_path / "research.json"
    evidence_p = tmp_path / "evidence.json"
    thesis_p.write_text(json.dumps(thesis_dict), encoding="utf-8")
    research_p.write_text(json.dumps(research_dict), encoding="utf-8")
    evidence_p.write_text(json.dumps(evidence_dict), encoding="utf-8")
    result = evaluate_thesis_gate(thesis_p, research_p, evidence_p, "TH-001")
    assert result.status is GateStatus.PASS


def test_brief_without_narrative_material_does_not_pass(tmp_path: Path) -> None:
    brief = valid_brief()
    brief["narrative_materials"] = []
    ep, active = write_inputs(tmp_path, brief=brief)
    assert evaluate_brief_research(ep, active_profile_path=active).status is GateStatus.FAIL


def test_pending_critical_coverage_requires_scope_decision() -> None:
    research = valid_research()
    research["coverage"][0].update({"status": "PENDING", "limitation_or_pending": "Falta verificar.", "scope_decision": "NONE"})
    from src.core.contract_validation import validate_research_pack
    assert any("bloqueo o reducción" in v for v in validate_research_pack(research))


def test_indirect_report_requires_prohibitions_and_disclosure() -> None:
    report = valid_report()
    report["tipo_de_acceso"] = "INDIRECT"
    violations = validate_source_access_and_evidence_report(report)
    assert any("Acceso INDIRECT" in violation or "disclosures" in violation for violation in violations)


def test_thesis_must_inherit_evidence_constraints() -> None:
    thesis = _valid_thesis()
    report = _valid_evidence_dict()
    report["limitaciones"] = ["Lectura parcial."]
    report["propagated_constraints"] = ["Lectura parcial."]
    violations = validate_thesis_artifact(thesis, _valid_research_dict(), report)
    assert any("no hereda restricciones" in violation for violation in violations)


def test_valid_provisional_thesis_with_warn_evidence_warns(tmp_path: Path) -> None:
    evidence_dict = _valid_evidence_dict()
    evidence_dict["nivel_de_confianza"] = "MEDIUM"
    thesis_dict = _valid_thesis()
    research_dict = _valid_research_dict()
    thesis_p = tmp_path / "thesis.json"
    research_p = tmp_path / "research.json"
    evidence_p = tmp_path / "evidence.json"
    thesis_p.write_text(json.dumps(thesis_dict), encoding="utf-8")
    research_p.write_text(json.dumps(research_dict), encoding="utf-8")
    evidence_p.write_text(json.dumps(evidence_dict), encoding="utf-8")
    result = evaluate_thesis_gate(thesis_p, research_p, evidence_p, "TH-001")
    assert result.status is GateStatus.WARN
    assert result.exit_code == 0


def test_thesis_gate_makes_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    def forbidden_socket(*args, **kwargs):
        raise AssertionError("No se permiten llamadas externas")
    monkeypatch.setattr(socket, "socket", forbidden_socket)
    thesis_dict = _valid_thesis()
    research_dict = _valid_research_dict()
    evidence_dict = _valid_evidence_dict()
    thesis_p = tmp_path / "thesis.json"
    research_p = tmp_path / "research.json"
    evidence_p = tmp_path / "evidence.json"
    thesis_p.write_text(json.dumps(thesis_dict), encoding="utf-8")
    research_p.write_text(json.dumps(research_dict), encoding="utf-8")
    evidence_p.write_text(json.dumps(evidence_dict), encoding="utf-8")
    result = evaluate_thesis_gate(thesis_p, research_p, evidence_p, "TH-001")
    assert result.status is GateStatus.PASS


def _write_semantic_inputs(tmp_path: Path, decision: str = "PASS") -> tuple[Path, Path, Path, Path, Path]:
    brief, research, evidence, thesis = tmp_path / "brief.json", tmp_path / "research.json", tmp_path / "evidence.json", tmp_path / "thesis.json"
    brief.write_text(json.dumps(valid_brief()), encoding="utf-8")
    research.write_text(json.dumps(_valid_research_dict()), encoding="utf-8")
    evidence.write_text(json.dumps(_valid_evidence_dict()), encoding="utf-8")
    thesis.write_text(json.dumps(_valid_thesis()), encoding="utf-8")
    checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    audit = tmp_path / "audit.json"
    criteria = ["CENTRAL_QUESTION_SPECIFICITY", "RESEARCH_RELEVANCE", "DEPTH_FIT", "RIVAL_PERSPECTIVE_SUBSTANCE", "NARRATIVE_UTILITY", "CRITICAL_CLAIMS_QUALITY", "THESIS_SUBSTANCE", "READINESS_FOR_B5_I2"]
    findings = [{"criterion": criterion, "assessment": "SATISFIED" if decision == "PASS" else "NOT_SATISFIED", "rationale": "Juicio semántico explícito.", "references": ["thesis.statement"]} for criterion in criteria]
    audit.write_text(json.dumps({"audit_id": "SSA-1", "episode_id": "EP-001", "brief_checksum": checksum(brief), "research_checksum": checksum(research), "evidence_report_checksum": checksum(evidence), "thesis_checksum": checksum(thesis), "audited_by": "team_02_ai", "audit_method": "AI_SEMANTIC_REVIEW", "findings": findings, "decision": decision, "created_at": "2026-07-24T20:00:00Z"}), encoding="utf-8")
    return brief, research, evidence, thesis, audit


def test_semantic_audit_missing_blocks(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    audit.unlink()
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.BLOCKED


def test_semantic_audit_wrong_checksum_fails(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    data = json.loads(audit.read_text(encoding="utf-8")); data["thesis_checksum"] = "b" * 64; audit.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_semantic_audit_generic_content_can_fail(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path, "FAIL")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_semantic_audit_specific_candidate_can_pass(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path, "PASS")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.PASS


def test_identified_claim_without_report_assessment_fails(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    report = json.loads(evidence.read_text(encoding="utf-8")); report["critical_claim_assessments"] = []; evidence.write_text(json.dumps(report), encoding="utf-8"); data = json.loads(audit.read_text(encoding="utf-8")); data["evidence_report_checksum"] = hashlib.sha256(evidence.read_bytes()).hexdigest(); audit.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_untraceable_additional_claim_fails(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    report = json.loads(evidence.read_text(encoding="utf-8")); report["critical_claim_assessments"].append({"claim_id": "C2", "claim_text": "No trazable.", "support_status": "SUPPORTED", "confidence": "HIGH", "allowed_scope": "Ninguno", "evidence_refs": ["S1"]}); evidence.write_text(json.dumps(report), encoding="utf-8"); data = json.loads(audit.read_text(encoding="utf-8")); data["evidence_report_checksum"] = hashlib.sha256(evidence.read_bytes()).hexdigest(); audit.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_semantic_audit_criteria_are_complete_and_unique(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    data = json.loads(audit.read_text(encoding="utf-8")); data["findings"] = data["findings"][:1]; audit.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_critical_not_satisfied_cannot_claim_pass_or_warn(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    data = json.loads(audit.read_text(encoding="utf-8")); data["findings"][6]["assessment"] = "NOT_SATISFIED"; data["decision"] = "WARN"; audit.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_limited_finding_requires_warn(tmp_path: Path) -> None:
    brief, research, evidence, thesis, audit = _write_semantic_inputs(tmp_path)
    data = json.loads(audit.read_text(encoding="utf-8")); data["findings"][0]["assessment"] = "LIMITED"; data["decision"] = "PASS"; audit.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate_semantic_gate(brief, research, evidence, thesis, audit, "EP-001").status is GateStatus.FAIL


def test_partial_coverage_dispositions(tmp_path: Path) -> None:
    research = valid_research()
    entry = research["coverage"][0]
    entry.update({"status": "PARTIALLY_COVERED", "limitation_or_pending": "Falta contexto.", "editorial_impact": "NON_CRITICAL", "scope_decision": "REDUCED_SCOPE", "propagated_constraint": "No generalizar.", "mitigation_status": "MITIGATED"})
    ep, active = write_inputs(tmp_path, research=research)
    assert evaluate_brief_research(ep, active_profile_path=active).status is GateStatus.WARN
    entry.update({"editorial_impact": "CRITICAL", "mitigation_status": "INSUFFICIENT"})
    (ep / "research_pack.json").write_text(json.dumps(research), encoding="utf-8")
    assert evaluate_brief_research(ep, active_profile_path=active).status is GateStatus.BLOCKED


def test_partial_coverage_without_impact_fails(tmp_path: Path) -> None:
    research = valid_research()
    research["coverage"][0].update({"status": "PARTIALLY_COVERED", "limitation_or_pending": "Falta contexto.", "scope_decision": "REDUCED_SCOPE", "propagated_constraint": "No generalizar.", "mitigation_status": "MITIGATED", "editorial_impact": "NOT_APPLICABLE"})
    ep, active = write_inputs(tmp_path, research=research)
    assert evaluate_brief_research(ep, active_profile_path=active).status is GateStatus.FAIL


def test_inherited_skills_are_marked_non_executable() -> None:
    catalog = json.loads(Path("config/skill_catalog.json").read_text(encoding="utf-8"))
    deferred = {item["skill_id"]: item for item in catalog["skills"] if item.get("non_executable_current")}
    assert set(deferred) >= {"skill_analisis_patrones", "skill_curation_obras", "skill_mapa_eventos_y_outline", "skill_guion_longform", "skill_qa_editorial", "skill_verificacion_veracidad_notebooklm", "skill_extraer_voice_learnings"}
