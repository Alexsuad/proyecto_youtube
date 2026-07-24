"""Harness determinista para el gate de integridad y lineage de B5-I2."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.core.status import GateStatus
from src.scripts.b5_i2_gate import evaluate
from tests.harness.test_b5_i1_editorial_input import (
    _valid_thesis,
    valid_brief,
    valid_report,
    valid_research,
)


EPISODE_ID = "EP-001"
ANALYSIS_ID = "A-1"
CURATION_ID = "C-1"
PROVISIONAL_ID = "TH-001"
REFINED_ID = "T-1"


def _audit(brief: dict, research: dict, evidence: dict, provisional: dict) -> dict:
    def digest(value: dict) -> str:
        return hashlib.sha256(json.dumps(value).encode("utf-8")).hexdigest()

    criteria = [
        "CENTRAL_QUESTION_SPECIFICITY",
        "RESEARCH_RELEVANCE",
        "DEPTH_FIT",
        "RIVAL_PERSPECTIVE_SUBSTANCE",
        "NARRATIVE_UTILITY",
        "CRITICAL_CLAIMS_QUALITY",
        "THESIS_SUBSTANCE",
        "READINESS_FOR_B5_I2",
    ]
    return {
        "audit_id": "SSA-1",
        "episode_id": EPISODE_ID,
        "brief_checksum": digest(brief),
        "research_checksum": digest(research),
        "evidence_report_checksum": digest(evidence),
        "thesis_checksum": digest(provisional),
        "audited_by": "team_02_ai",
        "audit_method": "AI_SEMANTIC_REVIEW",
        "findings": [
            {
                "criterion": criterion,
                "assessment": "SATISFIED",
                "rationale": "Juicio semántico explícito.",
                "references": ["thesis.statement"],
            }
            for criterion in criteria
        ],
        "decision": "PASS",
        "created_at": "2026-07-24T20:00:00Z",
    }


def _analysis() -> dict:
    return {
        "analysis_id": ANALYSIS_ID,
        "episode_id": EPISODE_ID,
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "semantic_audit_id": "SSA-1",
        "material_id": "M1",
        "material_checksum": "a" * 64,
        "findings": [
            {
                "finding_id": "F-1",
                "claim_type": "INTERPRETATION",
                "statement": "La escena convierte el temor en una decisión visible.",
                "narrative_evidence_refs": ["N1"],
                "source_refs": ["S1"],
                "human_dimension": "BELIEF",
                "causal_relation": "La creencia condiciona la decisión.",
                "confidence": "HIGH",
            }
        ],
        "rival_interpretations": ["La evitación también puede ser prudencia."],
        "limitations": ["La lectura no sustituye evidencia clínica."],
        "created_at": "2026-07-24T20:00:00Z",
    }


def _curation() -> dict:
    def material(material_id: str, status: str, narrative_use: str) -> dict:
        return {
            "material_id": material_id,
            "function": "Complicación narrativa",
            "thesis_contribution": f"Contribución de {material_id}.",
            "new_perspective": f"Perspectiva de {material_id}.",
            "redundancy_with_selected": [],
            "context_cost": "Bajo.",
            "narrative_evidence_strength": "HIGH",
            "contradiction_or_nuance": "Introduce un matiz verificable.",
            "narrative_use": narrative_use,
            "selection_status": status,
        }

    return {
        "curation_id": CURATION_ID,
        "episode_id": EPISODE_ID,
        "research_id": "RP-001",
        "analysis_ids": [ANALYSIS_ID],
        # Cuatro materiales prueban que no existe una cardinalidad fija de 3 o 5.
        "candidates": [
            material("M1", "SELECTED", "COMPLICATION"),
            material("M2", "EXCLUDED", "OTHER"),
            material("M3", "CANDIDATE", "RECOGNITION"),
            material("M4", "CANDIDATE", "CONCLUSION"),
        ],
        "selected_material_ids": ["M1"],
        "selection_stage": "FINAL",
        "exclusions": [
            {
                "material_id": "M2",
                "reason": "Redundante para el arco principal.",
                "context_cost": "Medio.",
                "evidence_limitation": "No añade evidencia independiente.",
            }
        ],
        "created_at": "2026-07-24T20:00:00Z",
    }


def _refined_thesis() -> dict:
    return {
        "thesis_id": REFINED_ID,
        "episode_id": EPISODE_ID,
        "brief_version": "1.0.0",
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "semantic_audit_id": "SSA-1",
        "provisional_thesis_id": PROVISIONAL_ID,
        "analysis_ids": [ANALYSIS_ID],
        "curation_id": CURATION_ID,
        "statement": "La evitación protege la identidad a corto plazo, pero estrecha las decisiones posibles.",
        "supporting_evidence_refs": ["F-1"],
        "counterevidence_refs": ["A1"],
        "rival_interpretations": ["La evitación también puede ser prudencia."],
        "main_objection": "No toda demora implica miedo.",
        "nuance": "El contexto y los recursos disponibles modifican el coste.",
        "material_contributions": [{"material_id": "M1", "contribution": "Introduce la complicación central."}],
        "limits": ["No permite generalizar a diagnósticos clínicos."],
        "revision_conditions": ["Nueva evidencia que contradiga la relación causal."],
        "stage": "THESIS_REFINED",
        "created_at": "2026-07-24T20:00:00Z",
    }


def _write_case(tmp_path: Path, packaging_risk: str = "LOW") -> dict[str, Path]:
    """Escribe una copia profunda de un caso completo y coherente."""
    brief = valid_brief()
    research = valid_research(source_count=3)
    evidence = valid_report()
    provisional = _valid_thesis()
    analysis = _analysis()
    curation = _curation()
    refined = _refined_thesis()
    packaging = {
        "packaging_id": "P-1",
        "episode_id": EPISODE_ID,
        "refined_thesis_id": REFINED_ID,
        "refined_thesis_checksum": "",
        "audience_concreta": "Adultos que posponen decisiones importantes.",
        "promesa_visible_provisional": "Entender el coste de evitar el error sin prometer una solución clínica.",
        "titulo_de_trabajo": "Cuando evitar también decide",
        "concepto_inicial_miniatura": "Una puerta entreabierta y una decisión pendiente.",
        "overpromise_risk": packaging_risk,
        "platform_constraints": [],
        "honesty_check": True,
        "status": "PROVISIONAL_TEAM_03_INPUT",
        "created_at": "2026-07-24T20:00:00Z",
    }
    packaging["refined_thesis_checksum"] = hashlib.sha256(
        json.dumps(refined).encode("utf-8")
    ).hexdigest()
    artifacts = {
        "brief": brief,
        "research": research,
        "evidence": evidence,
        "audit": _audit(brief, research, evidence, provisional),
        "provisional": provisional,
        "analysis": analysis,
        "curation": curation,
        "thesis": refined,
        "packaging": packaging,
    }
    paths: dict[str, Path] = {}
    for name, value in copy.deepcopy(artifacts).items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        paths[name] = path
    return paths


def _evaluate(paths: dict[str, Path]):
    b5_i1 = {name: paths[name] for name in ("brief", "research", "evidence", "audit", "provisional")}
    return evaluate(
        b5_i1,
        paths["analysis"],
        paths["curation"],
        paths["thesis"],
        paths["packaging"],
        EPISODE_ID,
    )


def _mutate(path: Path, mutation) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutation(data)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_b5_i2_valid_and_variable_materials(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    result = _evaluate(paths)
    assert result.status is GateStatus.PASS


@pytest.mark.parametrize(
    ("name", "target", "mutation", "expected"),
    [
        ("research_id_divergente", "analysis", lambda d: d.update(research_id="RP-999"), "analysis.research_id"),
        ("evidence_report_id_divergente", "analysis", lambda d: d.update(evidence_report_id="ER-999"), "analysis.evidence_report_id"),
        ("semantic_audit_id_divergente", "analysis", lambda d: d.update(semantic_audit_id="SSA-999"), "analysis.semantic_audit_id"),
        ("provisional_thesis_id_divergente", "thesis", lambda d: d.update(provisional_thesis_id="TH-999"), "provisional_thesis_id"),
        ("curation_id_divergente", "thesis", lambda d: d.update(curation_id="C-999"), "curation_id"),
        ("refined_thesis_checksum_incorrecto", "packaging", lambda d: d.update(refined_thesis_checksum="b" * 64), "Checksum"),
        ("analysis_id_inexistente", "curation", lambda d: d.update(analysis_ids=["A-999"]), "analysis_id inexistente"),
        ("evidencia_referenciada_inexistente", "analysis", lambda d: d["findings"][0].update(narrative_evidence_refs=["N-999"]), "evidencia narrativa inexistente"),
        ("material_excluido_seleccionado", "curation", lambda d: d.update(selected_material_ids=["M2"]), "EXCLUDED"),
        ("material_seleccionado_sin_contribucion", "curation", lambda d: d.update(selected_material_ids=["M1", "M3"]), "contributions"),
        ("contribucion_no_seleccionada", "thesis", lambda d: d["material_contributions"].__setitem__(0, {"material_id": "M3", "contribution": "Contribución fuera de selección."}), "contributions"),
        ("redundancia_material_inexistente", "curation", lambda d: d["candidates"][0].update(redundancy_with_selected=["M-999"]), "Redundancia"),
        ("redundancia_consigo_mismo", "curation", lambda d: d["candidates"][0].update(redundancy_with_selected=["M1"]), "Redundancia"),
        ("artefacto_b5_i1_invalido", "brief", lambda d: d.pop("profile_checksum"), "brief:"),
        ("auditoria_semantica_incompleta", "audit", lambda d: d.update(findings=d["findings"][:7]), "audit:"),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_b5_i2_negative_control_isolated(tmp_path: Path, name: str, target: str, mutation, expected: str) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths[target], mutation)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL, name
    assert any(expected in violation for violation in result.violations), result.violations


def test_packaging_overpromise_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path, packaging_risk="HIGH")
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("sobrepromete" in violation for violation in result.violations)


def test_b5_i3_not_started() -> None:
    workflow = Path(".agent/workflows/01_pipeline_episodio.md").read_text(encoding="utf-8")
    assert "B5-I3, B6 y B7 permanecen sin iniciar" in workflow
    assert not Path("src/scripts/b5_i3_gate.py").exists()
