"""Pruebas B5-I1 para entrada editorial canónica."""
from __future__ import annotations

import copy
import json
import socket
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.status import GateStatus
from src.scripts.evidence_sufficiency_gate import evaluate as evaluate_evidence
from src.scripts.qa_brief_research import evaluate as evaluate_brief_research

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
        "tesis_provisional": "Confundir el error con la identidad amplifica el miedo.",
        "objetivo": "Comprender el coste de evitar el error.",
        "transformacion_esperada": "Interpretar el fracaso como información.",
        "audiencia_concreta": "Adultos que posponen decisiones importantes.",
        "angulo_diferencial": "Contrastar respuestas narrativas distintas al error.",
        "alcance": "Consecuencias humanas y narrativas.",
        "fuera_de_alcance": "Diagnóstico clínico.",
        "spoilers": "SI_LIMITADOS",
        "tono": "Cercano y riguroso.",
        "duracion_objetivo": "18 minutos",
        "ritmo_locucion": "130 palabras por minuto",
        "nivel_investigacion": "PROFUNDO",
        "fuentes_requeridas": ["obra principal", "fuente conceptual"],
        "obra_o_fuente_principal": "Obra sintética",
        "tipo_de_guion_principal": "VIDEOENSAYO_NARRATIVO",
        "tipo_de_guion_secundario": None,
        "estructura_candidata": "creencia-evidencia-reinterpretación",
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
        "alternative_views": [],
        "scene_evidence": [],
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
        "supporting_reasoning": "Razonamiento inicial.",
        "main_objection": "Objeción principal.",
        "simplification_risk": "Riesgo de generalización.",
        "open_questions": ["¿Qué evidencia puede cambiarla?"],
        "source_refs": ["S1"],
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
    assert "BLOCKED_PENDING_B5_I2" in workflow
    assert "fases heredadas de curación" in workflow
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
