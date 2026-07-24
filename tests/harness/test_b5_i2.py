"""Pruebas aisladas de integridad funcional, lineage y suficiencia de B5-I2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.core.status import GateStatus
from src.scripts.b5_i2_gate import evaluate
from tests.harness.test_b5_i1_editorial_input import _valid_thesis, valid_brief, valid_report, valid_research


EP = "EP-001"
CONSTRAINT = "CONSTRAINT-ACCESS-1"
CRITERIA = [
    "ANALYSIS_SPECIFICITY", "MATERIAL_ANALYSIS_COVERAGE", "RIVAL_INTERPRETATION_AND_LIMITS",
    "INHERITED_RESTRICTION_PROPAGATION", "CURATION_COMPLETENESS", "CURATION_CONTRAST_AND_PROGRESSION",
    "THESIS_REFINEMENT_SUBSTANCE", "EVIDENCE_TRACEABILITY", "EARLY_PACKAGING_HONESTY",
]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _put(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _analysis(material_id: str = "M1", analysis_id: str = "A-1") -> dict:
    return {
        "analysis_id": analysis_id, "episode_id": EP, "research_id": "RP-001", "evidence_report_id": "ER-001",
        "semantic_audit_id": "SSA-1", "material_id": material_id, "material_checksum": "a" * 64,
        "inherited_constraint_ids": [CONSTRAINT],
        "findings": [{"finding_id": f"F-{material_id}", "claim_type": "INTERPRETATION", "statement": "La escena muestra una decisión condicionada por el miedo.", "narrative_evidence_refs": ["N1"], "source_refs": ["S1"], "human_dimension": "BELIEF", "causal_relation": "La creencia condiciona la decisión.", "confidence": "HIGH"}],
        "rival_interpretations": ["La demora también puede ser prudencia."], "rival_interpretation_status": "PRESENT", "rival_interpretation_justification": None,
        "limitations": ["No permite diagnóstico clínico."], "limits_status": "PRESENT", "limits_justification": None,
        "demonstrates": "La decisión se relaciona con una creencia observable.", "does_not_establish": "No prueba una causa universal.", "created_at": "2026-07-24T20:00:00Z",
    }


def _curation() -> dict:
    def candidate(material_id: str, status: str) -> dict:
        return {"material_id": material_id, "function": "Complicación", "thesis_contribution": f"Aporte de {material_id}.", "new_perspective": f"Matiz de {material_id}.", "redundancy_with_selected": [], "context_cost": "Bajo.", "narrative_evidence_strength": "HIGH", "contradiction_or_nuance": "Matiz verificable.", "narrative_use": "COMPLICATION", "selection_status": status}
    return {"curation_id": "C-1", "episode_id": EP, "research_id": "RP-001", "analysis_ids": ["A-1"], "candidates": [candidate("M1", "SELECTED"), candidate("M2", "EXCLUDED")], "selected_material_ids": ["M1"], "selection_stage": "FINAL", "exclusions": [{"material_id": "M2", "reason": "No añade contraste suficiente.", "context_cost": "Medio.", "evidence_limitation": "No se analizó porque se excluye."}], "sequence_rationale": "El material seleccionado introduce la complicación después del contexto.", "set_relationship": "El conjunto conserva una sola línea de tensión con exclusión justificada.", "unique_contributions": [{"material_id": "M1", "contribution": "Hace visible la complicación."}], "function_overlap_justification": "No hay funciones repetidas entre materiales seleccionados.", "created_at": "2026-07-24T20:00:00Z"}


def _thesis() -> dict:
    return {"thesis_id": "T-1", "episode_id": EP, "brief_version": "1.0.0", "research_id": "RP-001", "evidence_report_id": "ER-001", "semantic_audit_id": "SSA-1", "provisional_thesis_id": "TH-001", "analysis_ids": ["A-1"], "curation_id": "C-1", "statement": "Evitar el error puede proteger la identidad a corto plazo y estrechar las decisiones posibles.", "supporting_evidence_refs": ["F-M1"], "counterevidence_refs": ["A1"], "rival_interpretations": ["La demora también puede ser prudencia."], "main_objection": "No toda demora implica miedo.", "nuance": "El contexto altera el coste de evitar.", "material_contributions": [{"material_id": "M1", "contribution": "Convierte la tensión en una decisión concreta."}], "analysis_confirmed": ["La creencia condiciona la decisión observada."], "changes_from_provisional": ["La formulación incorpora el coste de la evitación."], "discarded_from_provisional": ["Se descarta explicar toda demora como miedo."], "refinement_rationale": "Análisis, contraevidencia y curación obligan a acotar la tesis.", "inherited_constraint_ids": [CONSTRAINT], "statement_unchanged_justification": None, "limits": ["No es un diagnóstico clínico."], "revision_conditions": ["Nueva evidencia que contradiga la relación."], "stage": "THESIS_REFINED", "created_at": "2026-07-24T20:00:00Z"}


def _packaging(brief: dict, thesis: dict, risk: str = "LOW") -> dict:
    return {"packaging_id": "P-1", "episode_id": EP, "refined_thesis_id": thesis["thesis_id"], "refined_thesis_checksum": "", "audience": {"persona_concreta": "Adulto que pospone una decisión importante.", "conocimiento_previo": "Reconoce el miedo a equivocarse.", "tension_reconocida": "Desea avanzar pero teme el coste del error.", "relevancia": "La tesis explica el coste de la evitación.", "expectativa_que_no_debe_generarse": "No ofrece terapia ni diagnóstico.", "profile_id": brief["profile_id"], "profile_version": brief["profile_version"], "profile_checksum": brief["profile_checksum"], "brief_checksum": ""}, "promesa_visible_provisional": "Explora el coste de evitar el error sin prometer una solución clínica.", "tension_central": "Avanzar o proteger la identidad.", "expectativa_del_espectador": "Reinterpretar una decisión pendiente.", "diferenciador": "Conecta evidencia narrativa, límite y contraargumento.", "titulo_de_trabajo": "Cuando evitar también decide", "concepto_inicial_miniatura": "Una puerta entreabierta frente a una decisión.", "titulo_miniatura_complementarity": "El título nombra la decisión y la miniatura hace visible la tensión.", "overpromise_risk": risk, "platform_constraints": [{"constraint": "Sin promesas terapéuticas.", "reason": "El reporte B5-I1 limita el alcance.", "impact": "La promesa se formula como exploración."}], "honesty_assessment": {"thesis_relation": "La promesa resume la tesis refinada sin ampliarla.", "thesis_refs": [thesis["thesis_id"]], "evidence_refs": ["F-M1"], "inherited_constraint_ids": [CONSTRAINT], "unsupported_elements": [], "risk_level": risk, "risk_justification": "Las referencias cubren la promesa propuesta.", "mitigation_or_pending": None}, "status": "PROVISIONAL_TEAM_03_INPUT", "created_at": "2026-07-24T20:00:00Z"}


def _write_case(tmp_path: Path, risk: str = "LOW") -> dict[str, Path]:
    brief, research, evidence, provisional = valid_brief(), valid_research(), valid_report(), _valid_thesis()
    evidence["propagated_constraints"] = [CONSTRAINT]
    provisional["inherited_constraints"] = [CONSTRAINT]
    paths = {name: _put(tmp_path / f"{name}.json", value) for name, value in {"brief": brief, "research": research, "evidence": evidence, "provisional": provisional}.items()}
    b5audit = {"audit_id": "SSA-1", "episode_id": EP, "brief_checksum": _digest(paths["brief"]), "research_checksum": _digest(paths["research"]), "evidence_report_checksum": _digest(paths["evidence"]), "thesis_checksum": _digest(paths["provisional"]), "audited_by": "team_02_ai", "audit_method": "AI_SEMANTIC_REVIEW", "findings": [{"criterion": c, "assessment": "SATISFIED", "rationale": "Revisión B5-I1 completa.", "references": ["thesis.statement"]} for c in ["CENTRAL_QUESTION_SPECIFICITY", "RESEARCH_RELEVANCE", "DEPTH_FIT", "RIVAL_PERSPECTIVE_SUBSTANCE", "NARRATIVE_UTILITY", "CRITICAL_CLAIMS_QUALITY", "THESIS_SUBSTANCE", "READINESS_FOR_B5_I2"]], "decision": "PASS", "created_at": "2026-07-24T20:00:00Z"}
    paths["audit"] = _put(tmp_path / "audit.json", b5audit)
    thesis = _thesis(); packaging = _packaging(brief, thesis, risk)
    paths.update({"analysis": _put(tmp_path / "analysis.json", _analysis()), "curation": _put(tmp_path / "curation.json", _curation()), "thesis": _put(tmp_path / "thesis.json", thesis)})
    packaging["refined_thesis_checksum"] = _digest(paths["thesis"]); packaging["audience"]["brief_checksum"] = _digest(paths["brief"])
    paths["packaging"] = _put(tmp_path / "packaging.json", packaging)
    _refresh_b5_i2_audit(paths)
    return paths


def _refresh_b5_i2_audit(paths: dict[str, Path], decision: str = "PASS") -> None:
    analysis_paths = [paths[key] for key in ("analysis", "analysis2") if key in paths]
    payload = {"audit_id": "B5I2-SSA-1", "episode_id": EP, "analysis_checksums": [{"analysis_id": _read(path)["analysis_id"], "checksum": _digest(path)} for path in analysis_paths], "curation_checksum": _digest(paths["curation"]), "refined_thesis_checksum": _digest(paths["thesis"]), "early_packaging_checksum": _digest(paths["packaging"]), "audited_by": "team_02_ai", "audit_method": "AI_SEMANTIC_REVIEW", "findings": [{"criterion": c, "assessment": "SATISFIED", "rationale": "Revisión B5-I2 explícita.", "references": ["artifact"]} for c in CRITERIA], "decision": decision, "created_at": "2026-07-24T20:00:00Z"}
    paths["b5_i2_audit"] = _put(paths["analysis"].parent / "b5_i2_audit.json", payload)


def _evaluate(paths: dict[str, Path]):
    analyses = [paths["analysis"]] + ([paths["analysis2"]] if "analysis2" in paths else [])
    return evaluate({key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")}, analyses, paths["curation"], paths["thesis"], paths["packaging"], paths["b5_i2_audit"], EP)


def _mutate(paths: dict[str, Path], name: str, mutate, refresh: bool = True) -> None:
    value = _read(paths[name]); mutate(value); _put(paths[name], value)
    if refresh:
        _refresh_b5_i2_audit(paths)


def test_complete_coherent_case_passes_and_unanalysed_exclusion_is_allowed(tmp_path: Path) -> None:
    assert _evaluate(_write_case(tmp_path)).status is GateStatus.PASS


@pytest.mark.parametrize("field", ["brief_checksum", "research_checksum", "evidence_report_checksum", "thesis_checksum"])
def test_b5_i1_checksum_divergence_fails(tmp_path: Path, field: str) -> None:
    paths = _write_case(tmp_path); _mutate(paths, "audit", lambda d: d.update({field: "b" * 64}), refresh=False)
    assert _evaluate(paths).status is GateStatus.FAIL


@pytest.mark.parametrize(("name", "target", "mutation", "needle"), [
    ("selected_without_analysis", "curation", lambda d: d.update(selected_material_ids=["M2"]), "Material seleccionado sin NarrativeHumanAnalysis"),
    ("final_candidate_unresolved", "curation", lambda d: d["candidates"][1].update(selection_status="CANDIDATE"), "Curación FINAL no puede conservar candidatos sin resolver"),
    ("without_sequence", "curation", lambda d: d.pop("sequence_rationale"), "sequence_rationale"),
    ("without_set_relationship", "curation", lambda d: d.pop("set_relationship"), "set_relationship"),
    ("without_unique_contribution", "curation", lambda d: d.update(unique_contributions=[]), "unique_contributions"),
    ("thesis_without_delta", "thesis", lambda d: d.pop("changes_from_provisional"), "changes_from_provisional"),
    ("supporting_evidence_missing", "thesis", lambda d: d.update(supporting_evidence_refs=["F-404"]), "evidencia favorable inexistente"),
    ("counterevidence_missing", "thesis", lambda d: d.update(counterevidence_refs=["F-404"]), "contraevidencia inexistente"),
    ("restriction_lost", "thesis", lambda d: d.update(inherited_constraint_ids=[]), "pierde restricciones heredadas"),
    ("audience_incomplete", "packaging", lambda d: d["audience"].pop("persona_concreta"), "persona_concreta"),
    ("packaging_without_tension", "packaging", lambda d: d.pop("tension_central"), "tension_central"),
    ("packaging_without_complementarity", "packaging", lambda d: d.pop("titulo_miniatura_complementarity"), "titulo_miniatura_complementarity"),
    ("low_unsupported_promise", "packaging", lambda d: d["honesty_assessment"].update(unsupported_elements=["Promesa no sustentada"]), "LOW no puede declarar elementos no sustentados"),
    ("medium_without_mitigation", "packaging", lambda d: (d.update(overpromise_risk="MEDIUM"), d["honesty_assessment"].update(risk_level="MEDIUM")), "MEDIUM exige mitigación"),
    ("curation_research_id", "curation", lambda d: d.update(research_id="RP-404"), "curation.research_id"),
    ("thesis_research_id", "thesis", lambda d: d.update(research_id="RP-404"), "thesis.research_id"),
    ("thesis_evidence_id", "thesis", lambda d: d.update(evidence_report_id="ER-404"), "thesis.evidence_report_id"),
    ("thesis_audit_id", "thesis", lambda d: d.update(semantic_audit_id="SSA-404"), "thesis.semantic_audit_id"),
])
def test_isolated_functional_control_fails(tmp_path: Path, name: str, target: str, mutation, needle: str) -> None:
    paths = _write_case(tmp_path); _mutate(paths, target, mutation)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL, name
    assert any(needle in item for item in result.violations), result.violations


@pytest.mark.parametrize("field", ["analysis_checksum", "curation_checksum", "refined_thesis_checksum", "early_packaging_checksum"])
def test_b5_i2_declared_checksum_divergence_fails(tmp_path: Path, field: str) -> None:
    paths = _write_case(tmp_path)
    if field == "analysis_checksum":
        _mutate(paths, "b5_i2_audit", lambda d: d["analysis_checksums"][0].update(checksum="b" * 64), refresh=False)
    else:
        _mutate(paths, "b5_i2_audit", lambda d: d.update({field: "b" * 64}), refresh=False)
    assert _evaluate(paths).status is GateStatus.FAIL


def test_b5_i2_audit_incomplete_or_duplicate_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path); _mutate(paths, "b5_i2_audit", lambda d: d.update(findings=d["findings"][:-1]), refresh=False)
    assert _evaluate(paths).status is GateStatus.FAIL


def test_b5_i2_audit_duplicate_or_semantically_insufficient_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d["findings"].append(dict(d["findings"][0])), refresh=False)
    assert _evaluate(paths).status is GateStatus.FAIL
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d["findings"][0].update(assessment="NOT_SATISFIED"), refresh=False)
    assert _evaluate(paths).status is GateStatus.FAIL


@pytest.mark.parametrize("field", ["expectativa_del_espectador", "diferenciador"])
def test_packaging_required_promise_structure_fails_when_missing(tmp_path: Path, field: str) -> None:
    paths = _write_case(tmp_path); _mutate(paths, "packaging", lambda d: d.pop(field))
    assert _evaluate(paths).status is GateStatus.FAIL


def test_honesty_boolean_cannot_replace_structured_assessment(tmp_path: Path) -> None:
    paths = _write_case(tmp_path); _mutate(paths, "packaging", lambda d: d.update(honesty_check=True))
    assert _evaluate(paths).status is GateStatus.FAIL


def _add_analysis(paths: dict[str, Path], material_id: str = "M2", analysis_id: str = "A-2") -> None:
    paths["analysis2"] = _put(paths["analysis"].parent / "analysis2.json", _analysis(material_id, analysis_id))
    _refresh_b5_i2_audit(paths)


@pytest.mark.parametrize("redundant_id", ["M-404", "M1"])
def test_redundancy_missing_or_self_reference_fails(tmp_path: Path, redundant_id: str) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: d["candidates"][0].update(redundancy_with_selected=[redundant_id]))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("Redundancia" in item for item in result.violations)


def test_selected_analysis_omitted_from_curation_lineage_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: d.update(analysis_ids=["A-404"]))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("analysis_id" in item or "análisis del material seleccionado" in item for item in result.violations)


def test_analysis_id_duplicate_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path); _add_analysis(paths, "M2", "A-1")
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("analysis_id debe ser único" in item for item in result.violations)


def test_material_analyzed_twice_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path); _add_analysis(paths, "M1", "A-2")
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("análisis canónico" in item for item in result.violations)


def test_candidate_material_id_duplicate_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: d["candidates"].append(dict(d["candidates"][0])))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("único entre candidatos" in item for item in result.violations)


def test_exclusion_material_id_duplicate_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: d["exclusions"].append(dict(d["exclusions"][0])))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("único entre exclusiones" in item for item in result.violations)


def test_analysis_checksum_duplicate_id_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d["analysis_checksums"].append({"analysis_id": "A-1", "checksum": "b" * 64}), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("una sola vez por analysis_id" in item for item in result.violations)


def test_medium_with_mitigation_warns(tmp_path: Path) -> None:
    paths = _write_case(tmp_path, risk="MEDIUM")
    _mutate(paths, "packaging", lambda d: d["honesty_assessment"].update(mitigation_or_pending="Revisar la formulación antes de Team 03."))
    assert _evaluate(paths).status is GateStatus.WARN


def test_equal_provisional_thesis_with_justification_is_allowed(tmp_path: Path) -> None:
    paths = _write_case(tmp_path); provisional = _read(paths["provisional"])
    _mutate(paths, "thesis", lambda d: d.update(statement=provisional["statement"], statement_unchanged_justification="La revisión confirma la formulación y documenta sus límites."), refresh=False)
    _mutate(paths, "packaging", lambda d: d.update(refined_thesis_checksum=_digest(paths["thesis"])), refresh=True)
    assert _evaluate(paths).status is GateStatus.PASS


def test_b5_i3_not_started() -> None:
    assert not Path("src/scripts/b5_i3_gate.py").exists()
