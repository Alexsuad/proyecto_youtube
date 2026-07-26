"""Pruebas aisladas de integridad funcional, lineage y adjudicación semántica B5-I2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.core.status import GateStatus
from src.scripts.b5_i2_gate import _canonical_manifest_checksum, evaluate
from tests.harness.test_b5_i1_editorial_input import _valid_thesis, valid_brief, valid_report, valid_research


EP = "EP-001"
CONSTRAINT = "CONSTRAINT-ACCESS-1"
DISCLOSURE = "No diagnóstico clínico."
EXCLUDED_CLAIM = "Causalidad clínica universal."
CRITERIA = [
    "ANALYSIS_SPECIFICITY", "MATERIAL_ANALYSIS_COVERAGE", "RIVAL_INTERPRETATION_AND_LIMITS",
    "INHERITED_RESTRICTION_PROPAGATION", "CURATION_COMPLETENESS", "CURATION_CONTRAST_AND_PROGRESSION",
    "THESIS_REFINEMENT_SUBSTANCE", "EVIDENCE_TRACEABILITY", "EARLY_PACKAGING_HONESTY",
]
ALL_CONSTRAINTS = [CONSTRAINT, DISCLOSURE, EXCLUDED_CLAIM]
RUN_ANALYSIS = "RUN-B5I2-AN-1"
RUN_ANALYSIS_2 = "RUN-B5I2-AN-2"
RUN_CURATION = "RUN-B5I2-CU-1"
RUN_THESIS = "RUN-B5I2-TH-1"
RUN_PACKAGING = "RUN-B5I2-PK-1"
RUN_AUDIT = "RUN-B5I2-AU-1"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _put(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _analysis(material_id: str = "M1", analysis_id: str = "A-1") -> dict:
    return {
        "analysis_id": analysis_id,
        "episode_id": EP,
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "semantic_audit_id": "SSA-1",
        "material_id": material_id,
        "material_checksum": "a" * 64,
        "inherited_constraint_ids": list(ALL_CONSTRAINTS),
        "findings": [
            {
                "finding_id": f"F-{material_id}",
                "claim_type": "INTERPRETATION",
                "statement": "La escena muestra una decisión condicionada por el miedo.",
                "narrative_evidence_refs": ["N1"],
                "source_refs": ["S1"],
                "human_dimension": "BELIEF",
                "causal_relation": "La creencia condiciona la decisión.",
                "confidence": "HIGH",
            }
        ],
        "rival_interpretations": ["La demora también puede ser prudencia."],
        "rival_interpretation_status": "PRESENT",
        "rival_interpretation_justification": None,
        "limitations": ["No permite diagnóstico clínico."],
        "limits_status": "PRESENT",
        "limits_justification": None,
        "demonstrates": "La decisión se relaciona con una creencia observable.",
        "does_not_establish": "No prueba una causa universal.",
        "created_at": "2026-07-24T20:00:00Z",
    }


def _curation() -> dict:
    def candidate(material_id: str, status: str) -> dict:
        return {
            "material_id": material_id,
            "function": "Complicación",
            "thesis_contribution": f"Aporte de {material_id}.",
            "new_perspective": f"Matiz de {material_id}.",
            "redundancy_with_selected": [],
            "context_cost": "Bajo.",
            "narrative_evidence_strength": "HIGH",
            "contradiction_or_nuance": "Matiz verificable.",
            "narrative_use": "COMPLICATION",
            "selection_status": status,
        }

    return {
        "curation_id": "C-1",
        "episode_id": EP,
        "research_id": "RP-001",
        "analysis_ids": ["A-1"],
        "candidates": [candidate("M1", "SELECTED"), candidate("M2", "EXCLUDED")],
        "selected_material_ids": ["M1"],
        "selection_stage": "FINAL",
        "exclusions": [
            {
                "material_id": "M2",
                "reason": "No añade contraste suficiente.",
                "context_cost": "Medio.",
                "evidence_limitation": "No se analizó porque se excluye.",
            }
        ],
        "sequence_rationale": "El material seleccionado introduce la complicación después del contexto.",
        "set_relationship": "El conjunto conserva una sola línea de tensión con exclusión justificada.",
        "unique_contributions": [{"material_id": "M1", "contribution": "Hace visible la complicación."}],
        "function_overlap_justification": "No hay funciones repetidas entre materiales seleccionados.",
        "progression_evidence": [
            {
                "material_id": "M1",
                "change_in_understanding": "La escena desplaza la lectura de prudencia a coste de evitación.",
                "evidence_refs": ["F-M1"],
                "non_substitutability": "Ningún material excluido muestra esta decisión concreta.",
            }
        ],
        "inherited_restrictions": [
            {
                "constraint_id": CONSTRAINT,
                "selection_or_exclusion_impact": "Impide seleccionar materiales que prometan diagnóstico.",
                "affected_material_ids": ["M1", "M2"],
                "required_disclosures": [],
                "unsupported_claims": [],
            },
            {
                "constraint_id": DISCLOSURE,
                "selection_or_exclusion_impact": "Obliga a declarar el límite editorial en la selección final.",
                "affected_material_ids": ["M1"],
                "required_disclosures": [DISCLOSURE],
                "unsupported_claims": [],
            },
            {
                "constraint_id": EXCLUDED_CLAIM,
                "selection_or_exclusion_impact": "Impide prometer una causalidad clínica universal.",
                "affected_material_ids": ["M1"],
                "required_disclosures": [],
                "unsupported_claims": [EXCLUDED_CLAIM],
            },
        ],
        "created_at": "2026-07-24T20:00:00Z",
    }


def _thesis() -> dict:
    return {
        "thesis_id": "T-1",
        "episode_id": EP,
        "brief_version": "1.0.0",
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "semantic_audit_id": "SSA-1",
        "provisional_thesis_id": "TH-001",
        "analysis_ids": ["A-1"],
        "curation_id": "C-1",
        "statement": "Evitar el error puede proteger la identidad a corto plazo y estrechar las decisiones posibles.",
        "supporting_evidence_refs": ["F-M1"],
        "counterevidence_refs": ["A1"],
        "rival_interpretations": ["La demora también puede ser prudencia."],
        "main_objection": "No toda demora implica miedo.",
        "nuance": "El contexto altera el coste de evitar.",
        "material_contributions": [{"material_id": "M1", "contribution": "Convierte la tensión en una decisión concreta."}],
        "analysis_confirmed": ["La creencia condiciona la decisión observada."],
        "changes_from_provisional": ["La formulación incorpora el coste de la evitación."],
        "discarded_from_provisional": ["Se descarta explicar toda demora como miedo."],
        "refinement_rationale": "Análisis, contraevidencia y curación obligan a acotar la tesis.",
        "refinement_dimensions": [
            {
                "dimension": "SCOPE",
                "provisional_position": "La evitación explica toda demora.",
                "resulting_position": "La evitación explica solo decisiones donde la escena muestra protección identitaria.",
                "evidence_refs": ["F-M1", "A1"],
                "rationale": "La escena confirma el caso y la alternativa impide generalizar.",
            }
        ],
        "inherited_constraint_ids": list(ALL_CONSTRAINTS),
        "statement_unchanged_justification": None,
        "limits": ["No es un diagnóstico clínico."],
        "revision_conditions": ["Nueva evidencia que contradiga la relación."],
        "stage": "THESIS_REFINED",
        "created_at": "2026-07-24T20:00:00Z",
    }


def _packaging(brief: dict, thesis: dict, risk: str = "LOW") -> dict:
    return {
        "packaging_id": "P-1",
        "episode_id": EP,
        "refined_thesis_id": thesis["thesis_id"],
        "refined_thesis_checksum": "",
        "audience": {
            "persona_concreta": "Adulto que pospone una decisión importante.",
            "conocimiento_previo": "Reconoce el miedo a equivocarse.",
            "tension_reconocida": "Desea avanzar pero teme el coste del error.",
            "relevancia": "La tesis explica el coste de la evitación.",
            "expectativa_que_no_debe_generarse": "No ofrece terapia ni diagnóstico.",
            "profile_id": brief["profile_id"],
            "profile_version": brief["profile_version"],
            "profile_checksum": brief["profile_checksum"],
            "brief_checksum": "",
        },
        "promesa_visible_provisional": "Explora el coste de evitar el error sin prometer una solución clínica.",
        "tension_central": "Avanzar o proteger la identidad.",
        "expectativa_del_espectador": "Reinterpretar una decisión pendiente.",
        "diferenciador": "Conecta evidencia narrativa, límite y contraargumento.",
        "titulo_de_trabajo": "Cuando evitar también decide",
        "concepto_inicial_miniatura": "Una puerta entreabierta frente a una decisión.",
        "titulo_miniatura_complementarity": "El título nombra la decisión y la miniatura hace visible la tensión.",
        "overpromise_risk": risk,
        "platform_constraints": [
            {
                "constraint": "Sin promesas terapéuticas.",
                "reason": "El reporte B5-I1 limita el alcance.",
                "impact": "La promesa se formula como exploración.",
            }
        ],
        "honesty_assessment": {
            "thesis_relation": "La promesa resume la tesis refinada sin ampliarla.",
            "thesis_refs": [thesis["thesis_id"]],
            "evidence_refs": ["F-M1"],
            "inherited_constraint_ids": list(ALL_CONSTRAINTS),
            "unsupported_elements": [],
            "risk_level": risk,
            "risk_justification": "Las referencias cubren la promesa propuesta.",
            "mitigation_or_pending": None,
        },
        "status": "PROVISIONAL_TEAM_03_INPUT",
        "created_at": "2026-07-24T20:00:00Z",
    }


def _artifact_checksum_rows(paths: dict[str, Path]) -> list[dict]:
    rows = [
        {
            "artifact_kind": "analysis",
            "artifact_id": _read(paths["analysis"])["analysis_id"],
            "checksum": _digest(paths["analysis"]),
            "producer_run_id": RUN_ANALYSIS,
        }
    ]
    if "analysis2" in paths:
        rows.append(
            {
                "artifact_kind": "analysis",
                "artifact_id": _read(paths["analysis2"])["analysis_id"],
                "checksum": _digest(paths["analysis2"]),
                "producer_run_id": RUN_ANALYSIS_2,
            }
        )
    rows.extend(
        [
            {
                "artifact_kind": "curation",
                "artifact_id": _read(paths["curation"])["curation_id"],
                "checksum": _digest(paths["curation"]),
                "producer_run_id": RUN_CURATION,
            },
            {
                "artifact_kind": "thesis",
                "artifact_id": _read(paths["thesis"])["thesis_id"],
                "checksum": _digest(paths["thesis"]),
                "producer_run_id": RUN_THESIS,
            },
            {
                "artifact_kind": "packaging",
                "artifact_id": _read(paths["packaging"])["packaging_id"],
                "checksum": _digest(paths["packaging"]),
                "producer_run_id": RUN_PACKAGING,
            },
        ]
    )
    return rows


def _anchored(criterion: str) -> list[dict]:
    by_criterion = {
        "ANALYSIS_SPECIFICITY": [
            {
                "artifact_kind": "analysis",
                "artifact_id": "A-1",
                "artifact_field": "findings[0].statement",
                "evaluated_excerpt": "La escena muestra una decisión condicionada por el miedo.",
                "evidence_refs": ["F-M1"],
                "evidence_excerpts": [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}],
                "editorial_comparison": "La observación liga una escena concreta con una interpretación no intercambiable.",
                "why_specific_or_generic": "Cita una conducta concreta y el límite de no generalizar a cualquier demora.",
                "decision": "SATISFIED",
            }
        ],
        "MATERIAL_ANALYSIS_COVERAGE": [
            {
                "artifact_kind": "analysis",
                "artifact_id": "A-1",
                "artifact_field": "demonstrates",
                "evaluated_excerpt": "La decisión se relaciona con una creencia observable.",
                "evidence_refs": ["F-M1"],
                "evidence_excerpts": [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}],
                "editorial_comparison": "La cobertura conecta hallazgo, interpretación y evidencia narrativa.",
                "why_specific_or_generic": "No se limita a afirmar cobertura; muestra el hallazgo exacto auditado.",
                "decision": "SATISFIED",
            }
        ],
        "RIVAL_INTERPRETATION_AND_LIMITS": [
            {
                "artifact_kind": "analysis",
                "artifact_id": "A-1",
                "artifact_field": "rival_interpretations[0]",
                "evaluated_excerpt": "La demora también puede ser prudencia.",
                "evidence_refs": ["A1"],
                "evidence_excerpts": [{"evidence_ref": "A1", "excerpt": "Hallazgo A1"}],
                "editorial_comparison": "La lectura rival se contrasta con la interpretación principal y con el límite declarado.",
                "why_specific_or_generic": "El rival no es abstracto; se formula como alternativa concreta.",
                "decision": "SATISFIED",
            }
        ],
        "INHERITED_RESTRICTION_PROPAGATION": [
            {
                "artifact_kind": "curation",
                "artifact_id": "C-1",
                "artifact_field": "inherited_restrictions[1].selection_or_exclusion_impact",
                "evaluated_excerpt": "Obliga a declarar el límite editorial en la selección final.",
                "evidence_refs": [DISCLOSURE],
                "evidence_excerpts": [{"evidence_ref": DISCLOSURE, "excerpt": DISCLOSURE}],
                "editorial_comparison": "La curación traduce la restricción heredada a una decisión editorial operativa.",
                "why_specific_or_generic": "No deja la restricción como etiqueta; muestra su impacto concreto.",
                "decision": "SATISFIED",
            }
        ],
        "CURATION_COMPLETENESS": [
            {
                "artifact_kind": "curation",
                "artifact_id": "C-1",
                "artifact_field": "sequence_rationale",
                "evaluated_excerpt": "El material seleccionado introduce la complicación después del contexto.",
                "evidence_refs": ["F-M1"],
                "evidence_excerpts": [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}],
                "editorial_comparison": "La secuencia se fundamenta en una función narrativa concreta.",
                "why_specific_or_generic": "Justifica el orden con la escena seleccionada y no con una fórmula reusable.",
                "decision": "SATISFIED",
            }
        ],
        "CURATION_CONTRAST_AND_PROGRESSION": [
            {
                "artifact_kind": "curation",
                "artifact_id": "C-1",
                "artifact_field": "progression_evidence[0].change_in_understanding",
                "evaluated_excerpt": "La escena desplaza la lectura de prudencia a coste de evitación.",
                "evidence_refs": ["F-M1"],
                "evidence_excerpts": [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}],
                "editorial_comparison": "La curación muestra un antes y un después ligados a un material no sustituible.",
                "why_specific_or_generic": "El cambio se apoya en un hallazgo concreto y en una pérdida identificable si se elimina el material.",
                "decision": "SATISFIED",
            }
        ],
        "THESIS_REFINEMENT_SUBSTANCE": [
            {
                "artifact_kind": "thesis",
                "artifact_id": "T-1",
                "artifact_field": "refinement_dimensions[0].resulting_position",
                "evaluated_excerpt": "La evitación explica solo decisiones donde la escena muestra protección identitaria.",
                "evidence_refs": ["F-M1", "A1"],
                "evidence_excerpts": [
                    {"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."},
                    {"evidence_ref": "A1", "excerpt": "Hallazgo A1"},
                ],
                "editorial_comparison": "La tesis compara posición provisional y posición resultante en una dimensión concreta.",
                "why_specific_or_generic": "Explicita qué cambió, qué evidencia lo causó y qué alternativa quedó descartada.",
                "decision": "SATISFIED",
            }
        ],
        "EVIDENCE_TRACEABILITY": [
            {
                "artifact_kind": "thesis",
                "artifact_id": "T-1",
                "artifact_field": "refinement_rationale",
                "evaluated_excerpt": "Análisis, contraevidencia y curación obligan a acotar la tesis.",
                "evidence_refs": ["F-M1"],
                "evidence_excerpts": [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}],
                "editorial_comparison": "La razón de refinamiento enlaza explícitamente el cambio con evidencia trazable.",
                "why_specific_or_generic": "No apela a intuición editorial; cita el soporte real usado para refinar.",
                "decision": "SATISFIED",
            }
        ],
        "EARLY_PACKAGING_HONESTY": [
            {
                "artifact_kind": "packaging",
                "artifact_id": "P-1",
                "artifact_field": "promesa_visible_provisional",
                "evaluated_excerpt": "Explora el coste de evitar el error sin prometer una solución clínica.",
                "evidence_refs": ["F-M1"],
                "evidence_excerpts": [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}],
                "editorial_comparison": "La promesa se compara con la tesis y con la restricción heredada.",
                "why_specific_or_generic": "La honestidad se demuestra contra evidencia y límite explícito, no por etiqueta abstracta.",
                "decision": "SATISFIED",
            }
        ],
    }
    return by_criterion[criterion]


def _write_case(tmp_path: Path, risk: str = "LOW") -> dict[str, Path]:
    brief, research, evidence, provisional = valid_brief(), valid_research(), valid_report(), _valid_thesis()
    evidence["propagated_constraints"] = [CONSTRAINT]
    evidence["required_disclosures"] = [DISCLOSURE]
    evidence["excluded_claims"] = [EXCLUDED_CLAIM]
    provisional["inherited_constraints"] = list(ALL_CONSTRAINTS)
    paths = {
        name: _put(tmp_path / f"{name}.json", value)
        for name, value in {"brief": brief, "research": research, "evidence": evidence, "provisional": provisional}.items()
    }
    b5audit = {
        "audit_id": "SSA-1",
        "episode_id": EP,
        "brief_checksum": _digest(paths["brief"]),
        "research_checksum": _digest(paths["research"]),
        "evidence_report_checksum": _digest(paths["evidence"]),
        "thesis_checksum": _digest(paths["provisional"]),
        "audited_by": "team_02_ai",
        "audit_method": "AI_SEMANTIC_REVIEW",
        "findings": [
            {"criterion": c, "assessment": "SATISFIED", "rationale": "Revisión B5-I1 completa.", "references": ["thesis.statement"]}
            for c in ["CENTRAL_QUESTION_SPECIFICITY", "RESEARCH_RELEVANCE", "DEPTH_FIT", "RIVAL_PERSPECTIVE_SUBSTANCE", "NARRATIVE_UTILITY", "CRITICAL_CLAIMS_QUALITY", "THESIS_SUBSTANCE", "READINESS_FOR_B5_I2"]
        ],
        "decision": "PASS",
        "created_at": "2026-07-24T20:00:00Z",
    }
    paths["audit"] = _put(tmp_path / "audit.json", b5audit)
    thesis = _thesis()
    packaging = _packaging(brief, thesis, risk)
    paths.update(
        {
            "analysis": _put(tmp_path / "analysis.json", _analysis()),
            "curation": _put(tmp_path / "curation.json", _curation()),
            "thesis": _put(tmp_path / "thesis.json", thesis),
        }
    )
    packaging["refined_thesis_checksum"] = _digest(paths["thesis"])
    packaging["audience"]["brief_checksum"] = _digest(paths["brief"])
    paths["packaging"] = _put(tmp_path / "packaging.json", packaging)
    _refresh_b5_i2_audit(paths)
    _refresh_execution_registry(paths)
    return paths


def _refresh_b5_i2_audit(paths: dict[str, Path], decision: str = "PASS") -> None:
    artifact_rows = _artifact_checksum_rows(paths)
    payload = {
        "audit_id": "B5I2-SSA-1",
        "episode_id": EP,
        "auditor_role": "INDEPENDENT_EDITORIAL_AUDITOR",
        "auditor_run_id": RUN_AUDIT,
        "auditor_skill_id": "skill_qa_editorial",
        "auditor_skill_version": "2.0.0",
        "provider_or_adapter": "local-mock-semantic",
        "model_or_evaluator": "semantic-mock-v1",
        "execution_timestamp": "2026-07-25T08:00:00Z",
        "input_manifest_checksum": _canonical_manifest_checksum(EP, artifact_rows),
        "artifact_checksums": artifact_rows,
        "audit_method": "AI_SEMANTIC_REVIEW",
        "findings": [
            {
                "criterion": criterion,
                "status": "SATISFIED",
                "anchored_findings": _anchored(criterion),
                "rationale": "La revisión editorial independiente quedó anclada a fragmentos y evidencia reales.",
            }
            for criterion in CRITERIA
        ],
        "decision": decision,
        "created_at": "2026-07-25T08:00:00Z",
    }
    paths["b5_i2_audit"] = _put(paths["analysis"].parent / "b5_i2_audit.json", payload)


def _refresh_execution_registry(paths: dict[str, Path], auditor_status: str = "SUCCEEDED", execution_mode: str = "SYNTHETIC") -> None:
    outputs = _artifact_checksum_rows(paths)
    registry_outputs = [
        {"artifact_kind": item["artifact_kind"], "artifact_id": item["artifact_id"], "checksum": item["checksum"]}
        for item in outputs
    ]
    registry = {
        "registry_version": "1.0.0",
        "runs": [
            {
                "run_id": RUN_ANALYSIS,
                "role": "NARRATIVE_ANALYST",
                "skill_id": "skill_analisis_patrones",
                "skill_version": "1.0.0",
                "provider_or_adapter": "synthetic-fixture",
                "model_or_evaluator": "fixture",
                "input_manifest_checksum": "a" * 64,
                "outputs": [item for item in registry_outputs if item["artifact_kind"] == "analysis" and item["artifact_id"] == "A-1"],
                "started_at": "2026-07-25T07:00:00Z",
                "completed_at": "2026-07-25T07:01:00Z",
                "status": "SUCCEEDED",
                "execution_mode": "SYNTHETIC",
            },
            {
                "run_id": RUN_CURATION,
                "role": "CURATION_EDITOR",
                "skill_id": "skill_curation_obras",
                "skill_version": "1.0.0",
                "provider_or_adapter": "synthetic-fixture",
                "model_or_evaluator": "fixture",
                "input_manifest_checksum": "a" * 64,
                "outputs": [item for item in registry_outputs if item["artifact_kind"] == "curation"],
                "started_at": "2026-07-25T07:02:00Z",
                "completed_at": "2026-07-25T07:03:00Z",
                "status": "SUCCEEDED",
                "execution_mode": "SYNTHETIC",
            },
            {
                "run_id": RUN_THESIS,
                "role": "THESIS_EDITOR",
                "skill_id": "skill_sintesis_tesis",
                "skill_version": "1.0.0",
                "provider_or_adapter": "synthetic-fixture",
                "model_or_evaluator": "fixture",
                "input_manifest_checksum": "a" * 64,
                "outputs": [item for item in registry_outputs if item["artifact_kind"] == "thesis"],
                "started_at": "2026-07-25T07:04:00Z",
                "completed_at": "2026-07-25T07:05:00Z",
                "status": "SUCCEEDED",
                "execution_mode": "SYNTHETIC",
            },
            {
                "run_id": RUN_PACKAGING,
                "role": "PACKAGING_EDITOR",
                "skill_id": "skill_packaging_temprano",
                "skill_version": "1.0.0",
                "provider_or_adapter": "synthetic-fixture",
                "model_or_evaluator": "fixture",
                "input_manifest_checksum": "a" * 64,
                "outputs": [item for item in registry_outputs if item["artifact_kind"] == "packaging"],
                "started_at": "2026-07-25T07:06:00Z",
                "completed_at": "2026-07-25T07:07:00Z",
                "status": "SUCCEEDED",
                "execution_mode": "SYNTHETIC",
            },
            {
                "run_id": RUN_AUDIT,
                "role": "INDEPENDENT_EDITORIAL_AUDITOR",
                "skill_id": "skill_qa_editorial",
                "skill_version": "2.0.0",
                "provider_or_adapter": "local-mock-semantic",
                "model_or_evaluator": "semantic-mock-v1",
                "input_manifest_checksum": _canonical_manifest_checksum(EP, outputs),
                "outputs": [
                    {
                        "artifact_kind": "semantic_audit",
                        "artifact_id": _read(paths["b5_i2_audit"])["audit_id"],
                        "checksum": _digest(paths["b5_i2_audit"]),
                    }
                ],
                "started_at": "2026-07-25T08:00:00Z",
                "completed_at": "2026-07-25T08:01:00Z",
                "status": auditor_status,
                "execution_mode": execution_mode,
            },
        ],
    }
    paths["execution_registry"] = _put(paths["analysis"].parent / "execution_registry.json", registry)


def _evaluate(paths: dict[str, Path]):
    analyses = [paths["analysis"]] + ([paths["analysis2"]] if "analysis2" in paths else [])
    return evaluate(
        {key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")},
        analyses,
        paths["curation"],
        paths["thesis"],
        paths["packaging"],
        paths["b5_i2_audit"],
        paths["execution_registry"],
        EP,
    )


def _mutate(paths: dict[str, Path], name: str, mutate, refresh: bool = True) -> None:
    value = _read(paths[name])
    mutate(value)
    _put(paths[name], value)
    if refresh:
        _refresh_b5_i2_audit(paths)
        _refresh_execution_registry(paths)


def _restriction_by_id(curation: dict, constraint_id: str) -> dict:
    return next(item for item in curation["inherited_restrictions"] if item["constraint_id"] == constraint_id)


def _criterion(audit: dict, criterion: str) -> dict:
    return next(item for item in audit["findings"] if item["criterion"] == criterion)


def _add_analysis(paths: dict[str, Path], material_id: str = "M2", analysis_id: str = "A-2") -> None:
    paths["analysis2"] = _put(paths["analysis"].parent / "analysis2.json", _analysis(material_id, analysis_id))
    _refresh_b5_i2_audit(paths)
    _refresh_execution_registry(paths)


def test_complete_coherent_case_passes_and_unanalysed_exclusion_is_allowed(tmp_path: Path) -> None:
    result = _evaluate(_write_case(tmp_path))
    assert result.status is GateStatus.PASS
    assert result.evidence["semantic_audit"]["SEMANTIC_AUDIT_INTEGRITY"] == "PASS"
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "PASS"


@pytest.mark.parametrize("field", ["brief_checksum", "research_checksum", "evidence_report_checksum", "thesis_checksum"])
def test_b5_i1_checksum_divergence_fails(tmp_path: Path, field: str) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "audit", lambda d: d.update({field: "b" * 64}), refresh=False)
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
    paths = _write_case(tmp_path)
    _mutate(paths, target, mutation)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL, name
    assert any(needle in item for item in result.violations), result.violations


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
    paths = _write_case(tmp_path)
    _add_analysis(paths, "M2", "A-1")
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("analysis_id debe ser único" in item for item in result.violations)


def test_material_analyzed_twice_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _add_analysis(paths, "M1", "A-2")
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


def test_independent_provenance_is_required(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d.update(provider_or_adapter="manual"), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("procedencia no verificable" in item for item in result.violations)


def test_producer_run_id_inexistente_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d["artifact_checksums"][0].update(producer_run_id="RUN-404"), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("producer_run_id inexistente" in item for item in result.violations)


def test_existing_run_that_did_not_produce_artifact_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "execution_registry", lambda d: d["runs"][0].update(outputs=[]), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("no produjo realmente" in item for item in result.violations)


def test_registered_output_checksum_mismatch_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "execution_registry", lambda d: d["runs"][0]["outputs"][0].update(checksum="b" * 64), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("registró un checksum distinto" in item for item in result.violations)


def test_auditor_run_id_inexistente_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d.update(auditor_run_id="RUN-AUDIT-404"), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("auditor_run_id inexistente" in item for item in result.violations)


@pytest.mark.parametrize(("field", "registry_field"), [("auditor_skill_id", "skill_id"), ("auditor_skill_version", "skill_version")])
def test_auditor_skill_or_version_mismatch_fails(tmp_path: Path, field: str, registry_field: str) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "execution_registry", lambda d: d["runs"][-1].update({registry_field: "mismatch"}), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any(field in item for item in result.violations)


def test_audit_over_old_checksums_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d["artifact_checksums"][0].update(checksum="b" * 64), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("checksums obsoletos" in item for item in result.violations)


def test_input_manifest_checksum_must_match_exact_artifacts(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d.update(input_manifest_checksum="b" * 64), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("manifiesto exacto" in item for item in result.violations)


def test_evaluated_excerpt_must_exist_in_referenced_field(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(
        paths,
        "b5_i2_audit",
        lambda d: _criterion(d, "ANALYSIS_SPECIFICITY")["anchored_findings"][0].update(evaluated_excerpt="Fragmento inexistente."),
        refresh=False,
    )
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("evaluated_excerpt" in item for item in result.violations)


def test_evidence_excerpt_must_exist_in_referenced_evidence(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(
        paths,
        "b5_i2_audit",
        lambda d: _criterion(d, "THESIS_REFINEMENT_SUBSTANCE")["anchored_findings"][0]["evidence_excerpts"][0].update(excerpt="Fragmento no citado en evidencia."),
        refresh=False,
    )
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("fragmento que no aparece en la evidencia" in item for item in result.violations)


def test_relevant_artifact_must_be_covered_by_critical_audit(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: _criterion(d, "THESIS_REFINEMENT_SUBSTANCE").update(anchored_findings=[]), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("THESIS_REFINEMENT_SUBSTANCE" in item for item in result.violations)


def test_audit_created_by_same_execution_as_produced_artifacts_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: d["artifact_checksums"][0].update(producer_run_id=RUN_AUDIT), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("misma ejecución" in item for item in result.violations)


def test_auditor_that_also_produced_thesis_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    def mutate(registry: dict) -> None:
        registry["runs"][-1]["outputs"].append({"artifact_kind": "thesis", "artifact_id": "T-1", "checksum": _digest(paths["thesis"])})
    _mutate(paths, "execution_registry", mutate, refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("también produjo análisis, curación o tesis" in item for item in result.violations)


@pytest.mark.parametrize("status", ["NOT_SATISFIED", "UNRESOLVED"])
def test_critical_editorial_failure_or_unresolved_fails(tmp_path: Path, status: str) -> None:
    paths = _write_case(tmp_path)
    def mutate(audit: dict) -> None:
        _criterion(audit, "ANALYSIS_SPECIFICITY")["status"] = status
        _criterion(audit, "ANALYSIS_SPECIFICITY")["anchored_findings"][0]["decision"] = status
        audit["decision"] = "FAIL"
    _mutate(paths, "b5_i2_audit", mutate, refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "FAIL"


def test_limited_critical_editorial_decision_warns(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    def mutate(audit: dict) -> None:
        _criterion(audit, "THESIS_REFINEMENT_SUBSTANCE")["status"] = "LIMITED"
        _criterion(audit, "THESIS_REFINEMENT_SUBSTANCE")["anchored_findings"][0]["decision"] = "LIMITED"
        audit["decision"] = "WARN"
    _mutate(paths, "b5_i2_audit", mutate, refresh=False)
    _refresh_execution_registry(paths)
    result = _evaluate(paths)
    assert result.status is GateStatus.WARN
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "WARN"


def test_synthetic_complete_provenance_passes_technical_integrity(tmp_path: Path) -> None:
    result = _evaluate(_write_case(tmp_path))
    assert result.status is GateStatus.PASS
    assert result.evidence["semantic_audit"]["SEMANTIC_AUDIT_INTEGRITY"] == "PASS"


def test_real_operation_without_evaluator_blocks(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _refresh_execution_registry(paths, auditor_status="BLOCKED_BY_SEMANTIC_EVALUATOR", execution_mode="REAL")
    result = _evaluate(paths)
    assert result.status is GateStatus.BLOCKED
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "BLOCKED_BY_SEMANTIC_EVALUATOR"


def test_orphan_artifact_or_evidence_references_fail(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    def mutate(audit: dict) -> None:
        anchored = _criterion(audit, "CURATION_CONTRAST_AND_PROGRESSION")["anchored_findings"][0]
        anchored["artifact_id"] = "C-404"
        anchored["evidence_refs"] = ["F-404"]
        anchored["evidence_excerpts"] = [{"evidence_ref": "F-404", "excerpt": "Nada."}]
    _mutate(paths, "b5_i2_audit", mutate, refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("referencia artefactos inexistentes" in item or "referencia evidencia inexistente" in item for item in result.violations)


def test_medium_with_mitigation_warns(tmp_path: Path) -> None:
    paths = _write_case(tmp_path, risk="MEDIUM")
    _mutate(paths, "packaging", lambda d: d["honesty_assessment"].update(mitigation_or_pending="Revisar la formulación antes de Team 03."))
    assert _evaluate(paths).status is GateStatus.WARN


def test_equal_provisional_thesis_with_justification_is_allowed(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    provisional = _read(paths["provisional"])
    _mutate(
        paths,
        "thesis",
        lambda d: d.update(
            statement=provisional["statement"],
            statement_unchanged_justification="La revisión confirma la formulación y documenta sus límites.",
        ),
        refresh=False,
    )
    _mutate(paths, "packaging", lambda d: d.update(refined_thesis_checksum=_digest(paths["thesis"])), refresh=True)
    assert _evaluate(paths).status is GateStatus.PASS


def test_inherited_restriction_with_unknown_affected_material_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: _restriction_by_id(d, CONSTRAINT).update(affected_material_ids=["M404"]))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("affected_material_ids inexistentes" in item for item in result.violations)


def test_required_disclosure_lost_in_curation_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: _restriction_by_id(d, DISCLOSURE).update(required_disclosures=[]))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("required_disclosure heredado" in item for item in result.violations)


def test_excluded_claim_lost_in_curation_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "curation", lambda d: _restriction_by_id(d, EXCLUDED_CLAIM).update(unsupported_claims=[]))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("excluded_claim" in item for item in result.violations)


def test_b5_i3_not_started() -> None:
    assert not Path("src/scripts/b5_i3_gate.py").exists()
