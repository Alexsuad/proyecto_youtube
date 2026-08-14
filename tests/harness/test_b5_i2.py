"""Pruebas aisladas de integridad funcional, lineage y adjudicación semántica B5-I2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ai.manifest import canonical_json
from src.core.status import GateStatus
from src.scripts.b5_i2_gate import _canonical_manifest_checksum, evaluate
from tests.harness.test_b5_i1_editorial_input import _valid_thesis, valid_brief, valid_report, valid_research


EP = "EP-001"
CONSTRAINT = "CONSTRAINT-ACCESS-1"
DISCLOSURE = "No diagnóstico clínico."
EXCLUDED_CLAIM = "Causalidad clínica universal."
CRITERIA = [
    "ANALYSIS_SPECIFICITY", "EVIDENCE_TRACEABILITY", "EPISTEMIC_SEPARATION", "EDITORIAL_DEPTH_AND_UTILITY",
    "MATERIAL_COVERAGE", "CURATION_FUNCTION", "CURATION_CONTRAST_AND_PROGRESSION", "REDUNDANCY_AND_CONTEXT_COST",
    "THESIS_REFINEMENT_SUBSTANCE", "THESIS_ARGUMENTATIVE_QUALITY", "MATERIAL_THESIS_CONTRIBUTION",
    "INHERITED_RESTRICTIONS", "SCRIPT_PROMISE_HONESTY", "EARLY_PACKAGING_HONESTY", "B5_I3_READINESS",
]
ALL_CONSTRAINTS = [CONSTRAINT, DISCLOSURE, EXCLUDED_CLAIM]
RUN_ANALYSIS = "RUN-B5I2-AN-1"
RUN_ANALYSIS_2 = "RUN-B5I2-AN-2"
RUN_CURATION = "RUN-B5I2-CU-1"
RUN_THESIS = "RUN-B5I2-TH-1"
RUN_RESEARCH = "RUN-B5I1-RE-1"
RUN_EVIDENCE = "RUN-B5I1-EV-1"
RUN_PROVISIONAL = "RUN-B5I1-TH-1"
RUN_PROMISE = "RUN-B5I2-SP-1"
RUN_AUDIT = "RUN-B5I2-AU-1"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _put(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _material_checksum_from_research(research: dict, material_id: str) -> str:
    matches = [
        item
        for field in ("facts", "interpretations", "hypotheses", "contradictions", "alternative_views", "narrative_evidence", "external_reality_evidence", "claims_candidates")
        for item in research.get(field, [])
        if isinstance(item, dict) and item.get("material_id") == material_id
    ]
    assert len(matches) == 1, f"material_id {material_id} debe tener una única referencia canónica de prueba"
    return hashlib.sha256(canonical_json(matches[0])).hexdigest()


def _analysis(material_id: str = "M1", analysis_id: str = "A-1") -> dict:
    return {
        "analysis_id": analysis_id,
        "episode_id": EP,
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "semantic_audit_id": "SSA-1",
        "material_id": material_id,
        "material_checksum": "",
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


def _script_promise(brief: dict, thesis: dict, risk: str = "LOW") -> dict:
    return {
        "promise_id": "SP-1",
        "episode_id": EP,
        "refined_thesis_id": thesis["thesis_id"],
        "refined_thesis_checksum": "",
        "audience": brief["audiencia_concreta"],
        "editorial_promise": "Explora el coste de evitar el error sin prometer una solución clínica.",
        "central_tension": "Avanzar o proteger la identidad.",
        "legitimate_expectations": ["Reinterpretar una decisión pendiente."],
        "expectations_to_avoid": ["No ofrece terapia ni diagnóstico."],
        "thesis_alignment": "La promesa resume la tesis refinada sin ampliarla.",
        "textual_overpromise_risk": {"level": risk, "justification": "La formulación se limita a la evidencia disponible.", "mitigation_or_pending": None},
        "opening_obligations": ["Presentar la tensión antes de proponer la lectura."],
        "inherited_constraint_ids": list(ALL_CONSTRAINTS),
        "status": "SCRIPT_CORE_INPUT",
        "created_at": "2026-07-24T20:00:00Z",
    }


def _artifact_checksum_rows(paths: dict[str, Path]) -> list[dict]:
    rows = [
        {"artifact_kind": "research", "artifact_id": _read(paths["research"])["research_id"], "checksum": _digest(paths["research"]), "producer_run_id": RUN_RESEARCH},
        {"artifact_kind": "evidence_report", "artifact_id": _read(paths["evidence"])["report_id"], "checksum": _digest(paths["evidence"]), "producer_run_id": RUN_EVIDENCE},
        {"artifact_kind": "provisional_thesis", "artifact_id": _read(paths["provisional"])["thesis_id"], "checksum": _digest(paths["provisional"]), "producer_run_id": RUN_PROVISIONAL},
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
                "artifact_kind": "refined_thesis",
                "artifact_id": _read(paths["thesis"])["thesis_id"],
                "checksum": _digest(paths["thesis"]),
                "producer_run_id": RUN_THESIS,
            },
            {
                "artifact_kind": "script_promise",
                "artifact_id": _read(paths["script_promise"])["promise_id"],
                "checksum": _digest(paths["script_promise"]),
                "producer_run_id": RUN_PROMISE,
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
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La observación liga una escena concreta con una interpretación no intercambiable.",
                "why_specific_or_generic": "Cita una conducta concreta y el límite de no generalizar a cualquier demora.",
                "decision": "SATISFIED",
            }
        ],
        "EVIDENCE_TRACEABILITY": [
            {
                "artifact_kind": "analysis",
                "artifact_id": "A-1",
                "artifact_field": "demonstrates",
                "evaluated_excerpt": "La decisión se relaciona con una creencia observable.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La cobertura conecta hallazgo, interpretación y evidencia narrativa.",
                "why_specific_or_generic": "No se limita a afirmar cobertura; muestra el hallazgo exacto auditado.",
                "decision": "SATISFIED",
            }
        ],
        "EPISTEMIC_SEPARATION": [
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
        "EDITORIAL_DEPTH_AND_UTILITY": [
            {
                "artifact_kind": "analysis",
                "artifact_id": "A-1",
                "artifact_field": "demonstrates",
                "evaluated_excerpt": "La decisión se relaciona con una creencia observable.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "El análisis resuelve una utilidad editorial concreta para la tesis futura.",
                "why_specific_or_generic": "Traduce la evidencia a una decisión editorial verificable.",
                "decision": "SATISFIED",
            }
        ],
        "MATERIAL_COVERAGE": [
            {
                "artifact_kind": "analysis",
                "artifact_id": "A-1",
                "artifact_field": "demonstrates",
                "evaluated_excerpt": "La decisión se relaciona con una creencia observable.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La cobertura conecta hallazgo, interpretación y evidencia narrativa.",
                "why_specific_or_generic": "No se limita a afirmar cobertura; muestra el hallazgo exacto auditado.",
                "decision": "SATISFIED",
            }
        ],
        "CURATION_FUNCTION": [
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
        "REDUNDANCY_AND_CONTEXT_COST": [
            {
                "artifact_kind": "curation",
                "artifact_id": "C-1",
                "artifact_field": "sequence_rationale",
                "evaluated_excerpt": "El material seleccionado introduce la complicación después del contexto.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
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
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La curación muestra un antes y un después ligados a un material no sustituible.",
                "why_specific_or_generic": "El cambio se apoya en un hallazgo concreto y en una pérdida identificable si se elimina el material.",
                "decision": "SATISFIED",
            }
        ],
        "THESIS_REFINEMENT_SUBSTANCE": [
            {
                "artifact_kind": "refined_thesis",
                "artifact_id": "T-1",
                "artifact_field": "refinement_dimensions[0].resulting_position",
                "evaluated_excerpt": "La evitación explica solo decisiones donde la escena muestra protección identitaria.",
                "evidence_refs": ["N1", "A1"],
                "evidence_excerpts": [
                    {"evidence_ref": "N1", "excerpt": "Hallazgo N1"},
                    {"evidence_ref": "A1", "excerpt": "Hallazgo A1"},
                ],
                "editorial_comparison": "La tesis compara posición provisional y posición resultante en una dimensión concreta.",
                "why_specific_or_generic": "Explicita qué cambió, qué evidencia lo causó y qué alternativa quedó descartada.",
                "decision": "SATISFIED",
            }
        ],
        "THESIS_ARGUMENTATIVE_QUALITY": [
            {
                "artifact_kind": "refined_thesis",
                "artifact_id": "T-1",
                "artifact_field": "refinement_rationale",
                "evaluated_excerpt": "Análisis, contraevidencia y curación obligan a acotar la tesis.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La razón de refinamiento enlaza explícitamente el cambio con evidencia trazable.",
                "why_specific_or_generic": "No apela a intuición editorial; cita el soporte real usado para refinar.",
                "decision": "SATISFIED",
            }
        ],
        "MATERIAL_THESIS_CONTRIBUTION": [
            {
                "artifact_kind": "refined_thesis",
                "artifact_id": "T-1",
                "artifact_field": "material_contributions[0].contribution",
                "evaluated_excerpt": "Convierte la tensión en una decisión concreta.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La tesis asigna a cada material una contribución verificable.",
                "why_specific_or_generic": "No trata los materiales como decorativos ni intercambiables.",
                "decision": "SATISFIED",
            }
        ],
        "INHERITED_RESTRICTIONS": [
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
        "SCRIPT_PROMISE_HONESTY": [
            {
                "artifact_kind": "script_promise",
                "artifact_id": "SP-1",
                "artifact_field": "editorial_promise",
                "evaluated_excerpt": "Explora el coste de evitar el error sin prometer una solución clínica.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La promesa se compara con la tesis y con la restricción heredada.",
                "why_specific_or_generic": "La honestidad se demuestra contra evidencia y límite explícito, no por etiqueta abstracta.",
                "decision": "SATISFIED",
            }
        ],
        "EARLY_PACKAGING_HONESTY": [],
        "B5_I3_READINESS": [
            {
                "artifact_kind": "curation",
                "artifact_id": "C-1",
                "artifact_field": "sequence_rationale",
                "evaluated_excerpt": "El material seleccionado introduce la complicación después del contexto.",
                "evidence_refs": ["N1"],
                "evidence_excerpts": [{"evidence_ref": "N1", "excerpt": "Hallazgo N1"}],
                "editorial_comparison": "La tesis, la curación y la promesa dejan explícitas las decisiones que B5-I3 podrá heredar.",
                "why_specific_or_generic": "La preparación para B5-I3 no queda implícita ni delegada a una futura invención.",
                "decision": "SATISFIED",
            }
        ],
    }
    return by_criterion[criterion]


def _write_case(tmp_path: Path, risk: str = "LOW") -> dict[str, Path]:
    brief, research, evidence, provisional = valid_brief(), valid_research(), valid_report(), _valid_thesis()
    research["narrative_evidence"][0]["material_id"] = "M1"
    research["narrative_evidence"].append({**research["narrative_evidence"][0], "item_id": "N2", "statement": "Escena excluida.", "locator": "00:11", "material_id": "M2"})
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
        "audited_by": "script_product_ai_reviewer",
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
    script_promise = _script_promise(brief, thesis, risk)
    paths.update(
        {
            "analysis": _put(tmp_path / "analysis.json", _analysis()),
            "curation": _put(tmp_path / "curation.json", _curation()),
            "thesis": _put(tmp_path / "thesis.json", thesis),
        }
    )
    script_promise["refined_thesis_checksum"] = _digest(paths["thesis"])
    paths["script_promise"] = _put(tmp_path / "script_promise.json", script_promise)
    analysis = _read(paths["analysis"])
    analysis.update({
        "material_function_candidate": "Complicación",
        "specific_scene_or_passage": "Escena concreta donde el personaje cambia una decisión central.",
        "observable_decision_or_action": "El personaje decide sostener la contradicción aun con coste visible.",
        "conflict": "La decisión enfrenta deseo personal y presión social.",
        "consequence": "La consecuencia modifica la lectura del material y la tesis provisional.",
        "main_interpretation": "La escena muestra que el conflicto no se resuelve sin costo moral.",
        "supporting_evidence": ["N1", "claim-1"],
        "interpretive_limit": "La escena no demuestra por sí sola una regla universal.",
        "relationship_to_provisional_thesis": "Confirma la intuición central pero la vuelve más condicional.",
        "potential_contribution_to_progression": "Introduce la primera complicación real del recorrido argumental.",
    })
    analysis["material_checksum"] = _material_checksum_from_research(research, analysis["material_id"])
    _put(paths["analysis"], analysis)
    curation = _read(paths["curation"])
    curation.update({
        "selected_materials": ["M1"],
        "excluded_materials": ["M2"],
        "function_of_each_selected_material": [{"material_id": "M1", "contribution": "Complica la tesis provisional con un costo visible."}],
        "reason_for_each_exclusion": [{"material_id": "M2", "reason": "Repite la misma función sin ampliar comprensión."}],
        "pairwise_redundancy_review": [{"left_material_id": "M1", "right_material_id": "M2", "result": "M2 es redundante frente a M1."}],
        "contrast_map": [{"from_material_id": "M1", "to_material_id": "M2", "contrast": "M2 no añade un giro nuevo frente a M1."}],
        "progression_map": [{"material_id": "M1", "change_in_understanding": "La tesis gana tensión y límite.", "evidence_refs": ["F-M1"], "non_substitutability": "Sin M1 no aparece la complicación central."}],
        "context_cost": "Bajo porque el material ya concentra la tensión necesaria.",
        "expected_order": ["M1"],
        "dependency_between_materials": [],
    })
    _put(paths["curation"], curation)
    thesis = _read(paths["thesis"])
    thesis.update({
        "refined_position": "La tesis se sostiene, pero solo cuando el conflicto se lee junto con su costo explícito.",
        "what_was_confirmed": ["La pregunta central sí se confirma en el material principal."],
        "what_was_changed": ["La tesis ahora depende de una condición narrativa explícita."],
        "what_was_rejected": ["Se descarta una lectura totalmente heroica del personaje."],
        "what_was_limited": ["El material no permite generalizar la conclusión a todos los casos."],
        "strongest_objection": "Otra lectura diría que el conflicto es circunstancial y no estructural.",
        "alternative_explanation": "La conducta podría explicarse por miedo inmediato y no por convicción estable.",
        "conditions_of_validity": ["La lectura vale solo si se conserva el costo visible como parte del análisis."],
        "remaining_uncertainties": ["No puede saberse si la consecuencia habría sido igual en otro contexto."],
        "evidence_dependencies": ["F-M1", "N1"],
    })
    _put(paths["thesis"], thesis)
    script_promise = _read(paths["script_promise"])
    script_promise["refined_thesis_checksum"] = _digest(paths["thesis"])
    _put(paths["script_promise"], script_promise)
    _refresh_b5_i2_audit(paths)
    _refresh_execution_registry(paths)
    return paths


def _refresh_b5_i2_audit(paths: dict[str, Path], decision: str = "PASS", readiness: str | None = None, provider_or_adapter: str = "mock") -> None:
    artifact_rows = _artifact_checksum_rows(paths)
    if readiness is not None:
        effective_readiness = readiness
    elif provider_or_adapter == "mock":
        effective_readiness = "BLOCKED"
    elif decision in {"PASS", "REQUEST_CHANGES"}:
        effective_readiness = "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"
    elif decision == "FAIL":
        effective_readiness = "NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"
    else:
        effective_readiness = "BLOCKED"
    criteria_results = [{"criterion": criterion, "status": "SATISFIED", "summary": "La revisión editorial independiente quedó anclada a fragmentos y evidencia reales."} for criterion in CRITERIA]
    findings = [
        {
            "criterion": criterion,
            "status": "SATISFIED",
            "anchored_findings": _anchored(criterion),
            "rationale": "La revisión editorial independiente quedó anclada a fragmentos y evidencia reales.",
        }
        for criterion in CRITERIA
    ]
    if decision == "FAIL":
        criteria_results[0]["status"] = "NOT_SATISFIED"
        findings[0]["status"] = "NOT_SATISFIED"
        findings[0]["anchored_findings"][0]["decision"] = "NOT_SATISFIED"
        findings[0]["rationale"] = "La revisión editorial detectó una insuficiencia sustantiva."
    elif decision == "BLOCKED":
        criteria_results[0]["status"] = "UNRESOLVED"
        findings[0]["status"] = "UNRESOLVED"
        findings[0]["anchored_findings"][0]["decision"] = "UNRESOLVED"
        findings[0]["rationale"] = "La revisión editorial quedó bloqueada y no puede emitir un cierre operativo."
    payload = {
        "audit_id": "B5I2-SSA-1",
        "episode_id": EP,
        "artifact_references": [f"{item['artifact_kind']}:{item['artifact_id']}" for item in artifact_rows],
        "producer_run_reference": RUN_ANALYSIS,
        "auditor_run_reference": RUN_AUDIT,
        "producer_actor_id": "SCRIPT_PRODUCT_PRODUCER",
        "auditor_actor_id": "SCRIPT_PRODUCT_AUDITOR",
        "auditor_input_checksum": _canonical_manifest_checksum(EP, artifact_rows),
        "auditor_write_scope": "AUDIT_ONLY",
        "independence_result": "PASS",
        "auditor_role": "SCRIPT_PRODUCT_AUDITOR",
        "auditor_run_id": RUN_AUDIT,
        "auditor_skill_id": "skill_auditar_suficiencia_semantica_b5_i2",
        "auditor_skill_version": "1.0.0",
        "provider_or_adapter": provider_or_adapter,
        "model_or_evaluator": "semantic-mock-v1",
        "execution_timestamp": "2026-07-25T08:00:00Z",
        "input_manifest_checksum": _canonical_manifest_checksum(EP, artifact_rows),
        "artifact_checksums": artifact_rows,
        "audit_method": "AI_SEMANTIC_REVIEW",
        "audited_artifact_ids": ["analysis:A-1", "curation:C-1", "refined_thesis:T-1", "script_promise:SP-1"],
        "audited_artifact_versions": [item for item in artifact_rows if item["artifact_kind"] in {"analysis", "curation", "refined_thesis", "script_promise"}],
        "criteria_results": criteria_results,
        "dimension_results": [{"dimension": name, "status": "PASS" if decision == "PASS" else ("REQUEST_CHANGES" if decision == "REQUEST_CHANGES" else decision), "summary": "Dimensión controlada por fixture."} for name in ["TRIVIAL_THESIS", "INTERCHANGEABLE_ANALYSIS", "DECORATIVE_OBJECTION", "FALSE_DEPTH", "REPHRASED_NOT_REFINED_THESIS", "REDUNDANT_CURATION", "NO_ARGUMENTATIVE_PROGRESSION", "UNSUPPORTED_INFERENCE", "SUMMARY_INSTEAD_OF_ANALYSIS", "MISSING_INTERPRETIVE_LIMIT"]],
        "findings": findings,
        "blocking_defects": [],
        "non_blocking_defects": [],
        "cited_evidence": sorted({ref for criterion in CRITERIA for finding in _anchored(criterion) for ref in finding.get("evidence_refs", [])}),
        "required_corrections": [],
        "required_changes": [],
        "excluded_claims_detected": [EXCLUDED_CLAIM],
        "unsupported_inferences": [],
        "redundancy_findings": [],
        "progression_findings": [],
        "thesis_refinement_finding": {"status": "PASS" if decision == "PASS" else ("REQUEST_CHANGES" if decision == "REQUEST_CHANGES" else decision), "summary": "El fixture sintetiza el estado de refinamiento."},
        "blocking_reasons": [] if decision != "BLOCKED" else ["Bloqueo de fixture"],
        "reaudit_requirements": [],
        "unresolved_questions": [],
        "inherited_restrictions_checked": [CONSTRAINT, DISCLOSURE, EXCLUDED_CLAIM],
        "auditor_statement": "Decision PASS emitida sobre artefactos B5-I2 con evidencia citada.",
        "decision": decision,
        "readiness": effective_readiness,
        "created_at": "2026-07-25T08:00:00Z",
    }
    paths["b5_i2_audit"] = _put(paths["analysis"].parent / "b5_i2_audit.json", payload)
    _sync_auditor_run(paths)


def _sync_auditor_run(paths: dict[str, Path]) -> None:
    registry_path = paths.get("execution_registry")
    if not registry_path or not registry_path.exists():
        return
    registry = _read(registry_path)
    audit = _read(paths["b5_i2_audit"])
    for run in registry.get("runs", []):
        if run.get("run_id") != RUN_AUDIT:
            continue
        run["provider_or_adapter"] = audit["provider_or_adapter"]
        run["provider"] = audit["provider_or_adapter"]
        run["actual_provider"] = audit["provider_or_adapter"]
        run["skill_id"] = audit["auditor_skill_id"]
        run["skill_version"] = audit["auditor_skill_version"]
        run["prompt_version"] = audit["auditor_skill_version"]
        run["model_or_evaluator"] = audit["model_or_evaluator"]
        run["model"] = audit["model_or_evaluator"]
        run["actual_model"] = audit["model_or_evaluator"]
        run["input_manifest_checksum"] = audit["input_manifest_checksum"]
        run["output_artifact_ids"] = [f"semantic_audit:{audit['audit_id']}"]
        run["output_versions"] = [RUN_AUDIT]
        run["output_checksums"] = [_digest(paths["b5_i2_audit"])]
        run["decision"] = audit["decision"]
        run["blocking_reason"] = None if audit["decision"] in {"PASS", "REQUEST_CHANGES"} else audit["decision"]
        run["outputs"] = [
            {
                "artifact_kind": "semantic_audit",
                "artifact_id": audit["audit_id"],
                "artifact_ref": f"semantic_audit:{audit['audit_id']}",
                "artifact_path": None,
                "checksum": _digest(paths["b5_i2_audit"]),
            }
        ]
        break
    _put(registry_path, registry)


def _refresh_execution_registry(paths: dict[str, Path], auditor_status: str = "SUCCEEDED", execution_mode: str = "SYNTHETIC", auditor_provider_kind: str = "SYNTHETIC", auditor_provider: str = "mock") -> None:
    outputs = _artifact_checksum_rows(paths)
    registry_outputs = [
        {"artifact_kind": item["artifact_kind"], "artifact_id": item["artifact_id"], "artifact_ref": f"{item['artifact_kind']}:{item['artifact_id']}", "artifact_path": None, "checksum": item["checksum"]}
        for item in outputs
    ]

    def make_run(
        run_id: str,
        role: str,
        skill_id: str,
        artifact_kind: str,
        *,
        provider_or_adapter: str = "synthetic-fixture",
        provider_kind: str = "SYNTHETIC",
        model_or_evaluator: str = "fixture",
        status: str = "SUCCEEDED",
        mode: str = "SYNTHETIC",
        started_at: str = "2026-07-25T07:00:00Z",
        completed_at: str = "2026-07-25T07:01:00Z",
        input_manifest_checksum: str = "a" * 64,
        decision: str = "SUCCEEDED",
        blocking_reason: str | None = None,
    ) -> dict:
        outputs_for_kind = [item for item in registry_outputs if item["artifact_kind"] == artifact_kind]
        output_artifact_ids = [item["artifact_ref"] for item in outputs_for_kind]
        output_checksums = [item["checksum"] for item in outputs_for_kind]
        return {
            "run_id": run_id,
            "episode_id": EP,
            "role": role,
            "skill_id": skill_id,
            "skill_version": "1.0.0",
            "provider_or_adapter": provider_or_adapter,
            "provider_kind": provider_kind,
            "model_or_evaluator": model_or_evaluator,
            "input_manifest_checksum": input_manifest_checksum,
            "outputs": outputs_for_kind,
            "started_at": started_at,
            "completed_at": completed_at,
            "status": status,
            "execution_mode": mode,
            "agent_id": role,
            "role_id": role,
            "execution_route": f"native:{provider_or_adapter}",
            "actual_executor": "native_provider",
            "actual_provider": provider_or_adapter,
            "actual_model": model_or_evaluator,
            "provider": provider_or_adapter,
            "model": model_or_evaluator,
            "prompt_version": "1.0.0",
            "input_artifact_ids": ["fixture:input"],
            "input_versions": ["RUN-FIXTURE-INPUT"],
            "input_checksums": ["a" * 64],
            "output_artifact_ids": output_artifact_ids,
            "output_versions": [run_id for _ in outputs_for_kind],
            "output_checksums": output_checksums,
            "finished_at": completed_at,
            "latency": 60,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0.0,
            "retry_count": 0,
            "decision": decision,
            "blocking_reason": blocking_reason,
            "handoff_target": "NONE",
        }

    registry = {
        "registry_version": "1.0.0",
        "runs": [
            make_run(RUN_ANALYSIS, "ANALYSIS_PRODUCER", "skill_analisis_patrones", "analysis"),
            *([make_run(RUN_ANALYSIS_2, "ANALYSIS_PRODUCER", "skill_analisis_patrones", "analysis", started_at="2026-07-25T07:01:30Z", completed_at="2026-07-25T07:01:45Z")] if "analysis2" in paths else []),
            make_run(RUN_CURATION, "CURATION_PRODUCER", "skill_curation_obras", "curation", started_at="2026-07-25T07:02:00Z", completed_at="2026-07-25T07:03:00Z"),
            make_run(RUN_THESIS, "THESIS_PRODUCER", "skill_sintesis_tesis", "refined_thesis", started_at="2026-07-25T07:04:00Z", completed_at="2026-07-25T07:05:00Z"),
            make_run(RUN_RESEARCH, "RESEARCHER", "skill_research_tema_y_obras", "research", started_at="2026-07-25T07:06:00Z", completed_at="2026-07-25T07:07:00Z"),
            make_run(RUN_EVIDENCE, "EVIDENCE_REVIEWER", "skill_qa_brief_research", "evidence_report", started_at="2026-07-25T07:06:00Z", completed_at="2026-07-25T07:07:00Z"),
            make_run(RUN_PROVISIONAL, "THESIS_EDITOR", "skill_sintesis_tesis", "provisional_thesis", started_at="2026-07-25T07:06:00Z", completed_at="2026-07-25T07:07:00Z"),
            make_run(RUN_PROMISE, "SCRIPT_PROMISE_PRODUCER", "skill_crear_brief_episodio", "script_promise", started_at="2026-07-25T07:06:00Z", completed_at="2026-07-25T07:07:00Z"),
            make_run(
                RUN_AUDIT,
                "SCRIPT_PRODUCT_AUDITOR",
                "skill_auditar_suficiencia_semantica_b5_i2",
                "semantic_audit",
                provider_or_adapter=auditor_provider,
                provider_kind=auditor_provider_kind,
                model_or_evaluator="semantic-mock-v1",
                status=auditor_status,
                mode=execution_mode,
                started_at="2026-07-25T08:00:00Z",
                completed_at="2026-07-25T08:01:00Z",
                input_manifest_checksum=_canonical_manifest_checksum(EP, outputs),
                decision="SUCCEEDED" if auditor_status == "SUCCEEDED" else ("BLOCKED" if auditor_status == "BLOCKED_BY_SEMANTIC_EVALUATOR" else "FAILED"),
                blocking_reason=None if auditor_status == "SUCCEEDED" else auditor_status,
            ),
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
        paths["script_promise"],
        paths["b5_i2_audit"],
        paths["execution_registry"],
        EP,
    )


def test_research_closure_mode_requires_explicit_stage_and_components(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    result = evaluate(
        {key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")},
        [paths["analysis"]], paths["curation"], paths["thesis"], paths["script_promise"],
        paths["b5_i2_audit"], paths["execution_registry"], EP, require_research_closure=True,
    )
    assert result.status is GateStatus.BLOCKED
    assert any("research_pack_stage" in item for item in result.violations)
    assert any("ResearchStopDecision" in item for item in result.violations)


def test_research_closure_does_not_fabricate_aggregate_decision(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    research = _read(paths["research"])
    research.update({
        "research_pack_stage": "RESEARCH_COMPLETE",
        "aggregate_research_stop_decision_ref": "RSD-AGG-1",
        "required_component_decision_refs": ["RSD-1"],
    })
    _put(paths["research"], research)
    _refresh_b5_i2_audit(paths)
    result = evaluate(
        {key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")},
        [paths["analysis"]], paths["curation"], paths["thesis"], paths["script_promise"],
        paths["b5_i2_audit"], paths["execution_registry"], EP,
        aggregate_decisions=[{"decision_id": "RSD-1", "sufficiency_status": "SUFFICIENT_FOR_INTENDED_USE"}],
        require_research_closure=True,
    )
    assert result.status is GateStatus.BLOCKED
    assert any("canonical aggregate ResearchStopDecision" in item for item in result.violations)


def test_b5_i2_consumes_research_pack_contradiction_disposition(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    research = _read(paths["research"])
    research["contradictions"] = [{
        "item_id": "X1",
        "statement": "Fuentes en conflicto.",
        "source_refs": ["S1"],
        "locator": "p. 1",
        "confidence": "HIGH",
    }]
    _put(paths["research"], research)
    _refresh_b5_i2_audit(paths)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("disposición trazable" in item for item in result.violations)


def test_b5_i2_consumes_specialist_research_validation(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    research = _read(paths["research"])
    research["specialist_research"] = [{
        "specialist_research_id": "SR-1",
        "status": "COMPLETED",
        "responsibility_role_ref": "config/responsibility_registry.json#responsibilities/RESEARCH_AND_CURATION",
        "activation": {
            "activation_id": "ACT-1", "specialty": "historia", "activation_reason": "Riesgo histórico material.",
            "problem_nature": "interpretación", "risk": "atribución", "sensitivity": "media", "complexity": "alta",
            "disciplinary_need": "contraste", "research_question": "¿Qué lectura rival debe conservarse?", "scope": "alcance acotado",
            "affected_object_refs": ["I2"], "affected_claim_ids": [], "expected_limits": ["No autoriza la tesis."],
        },
        "authority_status": "SPECIALIST_CONTRIBUTION_ONLY",
        "does_not_establish": ["FACT", "CLAIM_AUTHORIZATION", "RESEARCH_SUFFICIENCY", "THESIS_APPROVAL"],
        "contribution": {
            "contribution_id": "CONTR-1", "specialty": "historia", "research_question": "¿Qué lectura rival debe conservarse?",
            "scope": "alcance acotado", "method": "comparación", "source_refs": ["UNKNOWN"],
            "findings": [{"finding_id": "F-1", "statement": "Hallazgo", "evidence_refs": ["UNKNOWN"], "confidence": "LOW"}],
            "rival_status": "NONE_IDENTIFIED", "rival_search_justification": "Búsqueda acotada.", "rival_positions": [],
            "limitations": ["Cobertura limitada."],
            "operational_limits": [{"limit_id": "L-1", "condition": "Si se usa para atribución.", "effect": "Formular condicionalmente.", "return_route": "Volver a investigación."}],
            "uncertainty": {"level": "HIGH", "statement": "Incierto.", "material": True, "impact_on_use": "No usar como afirmación categórica."},
            "conflicts_of_interest": {"status": "NONE_DECLARED", "details": "Ninguno.", "mitigation": "Revisión."},
            "affected_object_refs": ["I2"], "affected_claim_ids": [], "claim_assessments": [],
        },
    }]
    _put(paths["research"], research)
    _refresh_b5_i2_audit(paths)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("fuentes desconocidas" in item or "evidencia no declarada" in item for item in result.violations)


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
    analysis = _analysis(material_id, analysis_id)
    analysis["material_checksum"] = _material_checksum_from_research(_read(paths["research"]), material_id)
    paths["analysis2"] = _put(paths["analysis"].parent / "analysis2.json", analysis)
    _refresh_b5_i2_audit(paths)
    _refresh_execution_registry(paths)


def test_complete_coherent_case_passes_and_unanalysed_exclusion_is_allowed(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _refresh_execution_registry(paths, execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="PASS", readiness="READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", provider_or_adapter="openai_compatible")
    result = _evaluate(paths)
    assert result.status is GateStatus.PASS
    assert result.evidence["semantic_audit"]["TECHNICAL_INTEGRITY"] == "PASS"
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "PASS"
    assert result.evidence["semantic_audit"]["OPERATIONAL_READINESS"] == "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"


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
    ("promise_without_tension", "script_promise", lambda d: d.pop("central_tension"), "central_tension"),
    ("promise_without_opening_obligation", "script_promise", lambda d: d.update(opening_obligations=[]), "opening_obligations"),
    ("medium_without_mitigation", "script_promise", lambda d: d["textual_overpromise_risk"].update(level="MEDIUM"), "MEDIUM exige mitigación"),
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


def test_analysis_finding_cannot_be_used_as_its_own_audit_evidence(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    def mutate(audit: dict) -> None:
        anchored = _criterion(audit, "ANALYSIS_SPECIFICITY")["anchored_findings"][0]
        anchored["evidence_refs"] = ["F-M1"]
        anchored["evidence_excerpts"] = [{"evidence_ref": "F-M1", "excerpt": "La escena muestra una decisión condicionada por el miedo."}]
    _mutate(paths, "b5_i2_audit", mutate, refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("evidencia inexistente" in item for item in result.violations)


def test_relevant_artifact_must_be_covered_by_critical_audit(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "b5_i2_audit", lambda d: _criterion(d, "THESIS_REFINEMENT_SUBSTANCE").update(anchored_findings=[]), refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("THESIS_REFINEMENT_SUBSTANCE" in item for item in result.violations)


def test_audit_created_by_same_execution_as_produced_artifacts_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(
        paths,
        "b5_i2_audit",
        lambda d: next(item for item in d["artifact_checksums"] if item["artifact_kind"] == "analysis").update(producer_run_id=RUN_AUDIT),
        refresh=False,
    )
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("misma ejecución" in item for item in result.violations)


def test_auditor_that_also_produced_thesis_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    def mutate(registry: dict) -> None:
        registry["runs"][-1]["outputs"].append({"artifact_kind": "refined_thesis", "artifact_id": "T-1", "artifact_ref": "refined_thesis:T-1", "artifact_path": None, "checksum": _digest(paths["thesis"])})
    _mutate(paths, "execution_registry", mutate, refresh=False)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("también produjo análisis, curación o tesis" in item for item in result.violations)


@pytest.mark.parametrize("status", ["NOT_SATISFIED", "UNRESOLVED"])
def test_critical_editorial_failure_or_unresolved_fails(tmp_path: Path, status: str) -> None:
    paths = _write_case(tmp_path)
    _refresh_execution_registry(paths, execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="FAIL", readiness="NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", provider_or_adapter="openai_compatible")
    def mutate(audit: dict) -> None:
        _criterion(audit, "ANALYSIS_SPECIFICITY")["status"] = status
        _criterion(audit, "ANALYSIS_SPECIFICITY")["anchored_findings"][0]["decision"] = status
        audit["decision"] = "FAIL"
    _mutate(paths, "b5_i2_audit", mutate, refresh=False)
    _sync_auditor_run(paths)
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "FAIL"


def test_limited_critical_editorial_decision_warns(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _refresh_execution_registry(paths, execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="REQUEST_CHANGES", readiness="NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", provider_or_adapter="openai_compatible")
    def mutate(audit: dict) -> None:
        _criterion(audit, "THESIS_REFINEMENT_SUBSTANCE")["status"] = "LIMITED"
        _criterion(audit, "THESIS_REFINEMENT_SUBSTANCE")["anchored_findings"][0]["decision"] = "LIMITED"
        audit["decision"] = "REQUEST_CHANGES"
    _mutate(paths, "b5_i2_audit", mutate, refresh=False)
    _sync_auditor_run(paths)
    result = _evaluate(paths)
    assert result.status is GateStatus.REQUEST_CHANGES
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "REQUEST_CHANGES"


def test_synthetic_complete_provenance_passes_technical_integrity(tmp_path: Path) -> None:
    result = _evaluate(_write_case(tmp_path))
    assert result.status is GateStatus.FAIL
    assert result.evidence["semantic_audit"]["TECHNICAL_INTEGRITY"] == "FAIL"
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "NOT_EVALUATED"
    assert result.evidence["semantic_audit"]["OPERATIONAL_READINESS"] == "BLOCKED"


def test_real_operation_without_evaluator_blocks(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _refresh_execution_registry(paths, auditor_status="BLOCKED_BY_SEMANTIC_EVALUATOR", execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="BLOCKED", readiness="BLOCKED", provider_or_adapter="openai_compatible")
    result = _evaluate(paths)
    assert result.status is GateStatus.BLOCKED
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "BLOCKED"


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
    _mutate(paths, "script_promise", lambda d: d["textual_overpromise_risk"].update(mitigation_or_pending="Revisar la formulación antes de escribir el guion."), refresh=False)
    _refresh_execution_registry(paths, execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="REQUEST_CHANGES", readiness="NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", provider_or_adapter="openai_compatible")
    assert _evaluate(paths).status is GateStatus.REQUEST_CHANGES


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
    _mutate(paths, "script_promise", lambda d: d.update(refined_thesis_checksum=_digest(paths["thesis"])), refresh=False)
    _refresh_execution_registry(paths, execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="PASS", readiness="READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", provider_or_adapter="openai_compatible")
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


def test_synthetic_warn_is_operationally_blocked(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _refresh_b5_i2_audit(paths, decision="REQUEST_CHANGES", readiness="BLOCKED")
    result = _evaluate(paths)
    assert result.status is GateStatus.BLOCKED
    assert result.evidence["semantic_audit"]["SEMANTIC_EDITORIAL_DECISION"] == "NOT_EVALUATED"
    assert result.evidence["semantic_audit"]["OPERATIONAL_READINESS"] == "BLOCKED"


def test_real_provider_fail_is_not_ready(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _refresh_execution_registry(paths, execution_mode="REAL", auditor_provider_kind="REAL", auditor_provider="openai_compatible")
    _refresh_b5_i2_audit(paths, decision="FAIL", readiness="NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", provider_or_adapter="openai_compatible")
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert result.evidence["semantic_audit"]["OPERATIONAL_READINESS"] == "NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"


@pytest.mark.parametrize(("decision", "readiness", "expected"), [("FAIL", "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", GateStatus.FAIL), ("BLOCKED", "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", GateStatus.FAIL), ("PASS", "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", GateStatus.FAIL)])
def test_incoherent_decision_readiness_is_rejected(tmp_path: Path, decision: str, readiness: str, expected: GateStatus) -> None:
    paths = _write_case(tmp_path)
    _refresh_b5_i2_audit(paths, decision=decision, readiness=readiness)
    result = _evaluate(paths)
    assert result.status is expected
    assert any("readiness operativo incoherente" in item or "no puede autorizar readiness operativo" in item for item in result.violations)


def test_material_checksum_incorrect_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "analysis", lambda d: d.update(material_checksum="b" * 64))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("material_checksum no coincide" in item for item in result.violations)


def test_material_reference_missing_blocks(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "research", lambda d: d["narrative_evidence"][0].pop("material_id"), refresh=False)
    _refresh_b5_i2_audit(paths)
    _refresh_execution_registry(paths)
    result = _evaluate(paths)
    assert result.status is GateStatus.BLOCKED
    assert any("No existe referencia canónica suficiente" in item for item in result.violations)


def test_material_checksum_from_other_material_fails(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "analysis", lambda d: d.update(material_checksum=_material_checksum_from_research(_read(paths["research"]), "M2")))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("material_checksum no coincide" in item for item in result.violations)


def test_excluded_material_analysis_is_rejected(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "analysis", lambda d: d.update(material_id="M2", material_checksum=_material_checksum_from_research(_read(paths["research"]), "M2")))
    result = _evaluate(paths)
    assert result.status is GateStatus.FAIL
    assert any("está excluido" in item for item in result.violations)


def test_unauthorized_material_analysis_is_blocked(tmp_path: Path) -> None:
    paths = _write_case(tmp_path)
    _mutate(paths, "analysis", lambda d: d.update(material_id="M3", material_checksum="a" * 64))
    result = _evaluate(paths)
    assert result.status is GateStatus.BLOCKED
