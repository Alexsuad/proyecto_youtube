"""Controlled cognitive fixtures for the PLAN012 M7 coordinator.

This module contains only synthetic cognitive responses.  It deliberately
does not persist, assign technical identity, or create Research artifacts;
the canonical B2/B3/B4 orchestrators own those responsibilities.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


def b5_i3_transversal_fixtures(
    *,
    episode_id: str,
    topic: str,
    works: list[str],
    profile: Mapping[str, Any],
    research_pack: Mapping[str, Any],
    source_report_payload: Mapping[str, Any],
    claims_ledger: Mapping[str, Any],
    refined_thesis_payload: Mapping[str, Any],
    refined_thesis_checksum: str,
) -> dict[str, dict[str, Any]]:
    """Return schema-shaped non-Research fixtures for the B5-I3 preflight.

    These fixtures are only the legacy/transversal inputs required by the
    existing B5-I3 consumer.  They do not execute narrative cognition and do
    not replace any Research V2 artifact produced by B2/B3/B4.
    """
    profile_id = str(profile["ACTIVE_PROFILE_ID"])
    profile_version = str(profile["ACTIVE_PROFILE_VERSION"])
    profile_checksum = str(profile["profile_checksum"])
    research_id = str(research_pack["research_id"])
    source_id = str(source_report_payload["report_id"])
    first_work = str(works[0])
    human = {
        "contract": "human_episode_input", "contract_version": "1.0.0",
        "interaction_id": f"INT-M7-{episode_id}", "occurred_at": "2026-09-06T00:00:00Z",
        "channel": "TERMINAL", "mode": "TOPIC_FIRST", "content": topic,
        "initial_question": "¿Qué puede afirmarse con evidencia?",
        "context": "Fixture sintético de integración; no es una entrada productiva.",
        "works": list(works), "actor_ref": "m7-synthetic-fixture",
        "provenance": {"capture_method": "TEXT", "source": "CONTROLLED_FIXTURE"},
        "processing_status": "RECEIVED",
    }
    brief = {
        "episode_id": episode_id, "brief_version": "1.0.0", "profile_id": profile_id,
        "profile_version": profile_version, "profile_checksum": profile_checksum,
        "tema": topic, "pregunta_central": "¿Qué puede afirmarse con evidencia?",
        "conflicto_o_tension": "La evidencia limita las explicaciones demasiado amplias.",
        "initial_editorial_hypothesis": {"statement": "La evidencia debe acotar la tesis.", "status": "HYPOTHESIS_UNAPPROVED", "research_role": "ORIENTS_RESEARCH_NOT_APPROVED_THESIS", "revisable": True, "adversarial_research_required": True},
        "objetivo": "Comprender el alcance defendible.",
        "transformacion_esperada": "Pasar de una explicación amplia a una lectura limitada.",
        "audiencia_concreta": "Audiencia de prueba del harness.", "audience_status": "INITIAL_HYPOTHESIS",
        "angulo_diferencial": "Separar evidencia de obra y realidad externa.",
        "alcance": "Integración técnica Research V2 hacia B5-I3.", "fuera_de_alcance": "Cognición narrativa y producción.",
        "spoilers": "SI_LIMITADOS", "tono": "Riguroso y claro.", "duracion_objetivo": "15 minutos",
        "ritmo_locucion": "150 palabras por minuto", "nivel_investigacion": "PROFUNDO",
        "fuentes_requeridas": ["fixture S1"], "narrative_materials": [f"Obra {first_work}"],
        "tipo_de_guion_principal": "VIDEOENSAYO_NARRATIVO", "tipo_de_guion_secundario": None,
        "estructura_candidata": "evidencia-reinterpretación", "structure_status": "INITIAL_HYPOTHESIS_REVISABLE_AFTER_RESEARCH",
        "razon_eleccion_estructura": "Permite conservar las restricciones de investigación.",
        "citation_style": "Atribución trazable.", "attribution_policy": "Atribuir hechos e ideas específicas.",
        "quotation_policy": "Citas breves y verificadas.", "source_visibility": "PUBLIC_SUMMARY",
        "salida_esperada": "Input contractual de prueba para B5-I3.", "created_at": "2026-09-06T00:00:00Z",
    }
    analysis_id = f"A-M7-{episode_id}"
    analysis = {
        "analysis_id": analysis_id, "artifact_version": "1.0.0", "episode_id": episode_id,
        "research_id": research_id, "evidence_report_id": source_id, "semantic_audit_id": f"B5I2-SSA-{episode_id}",
        "material_id": first_work, "material_checksum": "a" * 64, "inherited_constraint_ids": [],
        "findings": [{"finding_id": f"F-{episode_id}", "claim_type": "INTERPRETATION", "statement": "Lectura sintética limitada.", "narrative_evidence_refs": [f"D-{first_work}"], "source_refs": ["S1"], "human_dimension": "BELIEF", "causal_relation": "Relación condicionada.", "confidence": "HIGH"}],
        "rival_interpretations": ["La explicación rival reduce la generalización."], "rival_interpretation_status": "PRESENT", "rival_interpretation_justification": None,
        "limitations": ["Fixture controlado."], "limits_status": "PRESENT", "limits_justification": None,
        "demonstrates": "Una relación investigativa limitada.", "does_not_establish": "No demuestra causalidad universal.",
        "material_function_candidate": "Complicación.", "specific_scene_or_passage": "Registro sintético.",
        "observable_decision_or_action": "Acción observable de fixture.", "conflict": "Conflicto limitado.", "consequence": "Consecuencia documentada.",
        "main_interpretation": "Interpretación limitada.", "supporting_evidence": [f"F-{episode_id}"],
        "interpretive_limit": "No generalizar fuera del alcance.", "relationship_to_provisional_thesis": "Refina la tesis provisional.",
        "potential_contribution_to_progression": "Aporta un límite.", "created_at": "2026-09-06T00:00:00Z",
    }
    curation_id = f"C-M7-{episode_id}"
    curation = {
        "curation_id": curation_id, "episode_id": episode_id, "research_id": research_id,
        "analysis_ids": [analysis_id], "candidates": [{"material_id": first_work, "function": "Complicación", "thesis_contribution": "Aporta contraste.", "new_perspective": "Introduce un límite.", "redundancy_with_selected": [], "context_cost": "Bajo.", "narrative_evidence_strength": "HIGH", "contradiction_or_nuance": "Matiz.", "narrative_use": "COMPLICATION", "selection_status": "SELECTED"}],
        "selected_material_ids": [first_work], "selection_stage": "FINAL", "exclusions": [], "sequence_rationale": "Secuencia de prueba.", "set_relationship": "Relación complementaria.",
        "unique_contributions": [{"material_id": first_work, "contribution": "Aporta contraste."}], "function_overlap_justification": "No hay solapamiento.",
        "progression_evidence": [{"material_id": first_work, "change_in_understanding": "Cambia el alcance.", "evidence_refs": [f"F-{episode_id}"], "non_substitutability": "No sustituible."}],
        "inherited_restrictions": [], "selected_materials": [first_work], "excluded_materials": [],
        "function_of_each_selected_material": [{"material_id": first_work, "contribution": "Aporta contraste."}], "reason_for_each_exclusion": [],
        "pairwise_redundancy_review": [], "contrast_map": [{"from_material_id": first_work, "to_material_id": first_work, "contrast": "Autocontraste de fixture."}],
        "progression_map": [{"material_id": first_work, "change_in_understanding": "Cambia el alcance.", "evidence_refs": [f"F-{episode_id}"], "non_substitutability": "No sustituible."}],
        "context_cost": "Bajo.", "expected_order": [first_work], "dependency_between_materials": [], "created_at": "2026-09-06T00:00:00Z",
    }
    promise = {
        "promise_id": f"SP-M7-{episode_id}", "episode_id": episode_id, "refined_thesis_id": str(refined_thesis_payload["thesis_id"]), "refined_thesis_checksum": refined_thesis_checksum,
        "audience": "Audiencia de prueba.", "editorial_promise": "Examinar una tesis sin sobregeneralizar.", "central_tension": "Alcance frente a evidencia.",
        "legitimate_expectations": ["Comprensión."], "expectations_to_avoid": ["Certeza absoluta."], "thesis_alignment": "Alineada.",
        "textual_overpromise_risk": {"level": "LOW", "justification": "La limitación está declarada.", "mitigation_or_pending": None},
        "opening_obligations": ["Abrir con la tensión investigativa."], "inherited_constraint_ids": [], "status": "SCRIPT_CORE_INPUT", "created_at": "2026-09-06T00:00:00Z",
    }
    packaging = {
        "packaging_id": f"P-M7-{episode_id}", "episode_id": episode_id, "refined_thesis_id": str(refined_thesis_payload["thesis_id"]), "refined_thesis_checksum": refined_thesis_checksum,
        "audience": {"persona_concreta": "Audiencia de prueba.", "conocimiento_previo": "Básico.", "tension_reconocida": "Alcance de una explicación.", "relevancia": "Comprender límites.", "expectativa_que_no_debe_generarse": "No prometer certeza.", "profile_id": profile_id, "profile_version": profile_version, "profile_checksum": profile_checksum, "brief_checksum": "b" * 64},
        "promesa_visible_provisional": "Comprender el alcance.", "tension_central": "Evidencia y generalización.", "expectativa_del_espectador": "Leer con matiz.", "diferenciador": "Separación epistemológica.", "titulo_de_trabajo": "Una tesis con límites.", "concepto_inicial_miniatura": "Evidencia frente a intuición.", "titulo_miniatura_complementarity": "No es una promesa final.",
        "overpromise_risk": "LOW", "platform_constraints": [{"constraint": "No producción.", "reason": "Misión técnica.", "impact": "No aplica."}],
        "honesty_assessment": {"thesis_relation": "Relación limitada.", "thesis_refs": [str(refined_thesis_payload["thesis_id"])], "evidence_refs": ["S1"], "inherited_constraint_ids": [], "unsupported_elements": [], "risk_level": "LOW", "risk_justification": "Fixture controlado.", "mitigation_or_pending": None},
        "status": "PROVISIONAL_YOUTUBE_ADAPTATION_INPUT", "created_at": "2026-09-06T00:00:00Z",
    }
    audit_id = f"B5I2-SSA-{episode_id}"
    criteria = ["ANALYSIS_SPECIFICITY", "EVIDENCE_TRACEABILITY", "EPISTEMIC_SEPARATION", "EDITORIAL_DEPTH_AND_UTILITY", "MATERIAL_COVERAGE", "CURATION_FUNCTION", "CURATION_CONTRAST_AND_PROGRESSION", "REDUNDANCY_AND_CONTEXT_COST", "THESIS_REFINEMENT_SUBSTANCE", "THESIS_ARGUMENTATIVE_QUALITY", "MATERIAL_THESIS_CONTRIBUTION", "INHERITED_RESTRICTIONS", "SCRIPT_PROMISE_HONESTY", "EARLY_PACKAGING_HONESTY", "B5_I3_READINESS"]
    audited = [{"artifact_kind": "analysis", "artifact_id": analysis_id, "checksum": "a" * 64, "producer_run_id": "M7-TRANSVERSAL-FIXTURE"}, {"artifact_kind": "curation", "artifact_id": curation_id, "checksum": "b" * 64, "producer_run_id": "M7-TRANSVERSAL-FIXTURE"}, {"artifact_kind": "refined_thesis", "artifact_id": str(refined_thesis_payload["thesis_id"]), "checksum": refined_thesis_checksum, "producer_run_id": "M7-M5"}, {"artifact_kind": "script_promise", "artifact_id": promise["promise_id"], "checksum": "c" * 64, "producer_run_id": "M7-TRANSVERSAL-FIXTURE"}]
    audit = {
        "audit_id": audit_id, "episode_id": episode_id, "auditor_role": "INDEPENDENT_EDITORIAL_AUDITOR", "auditor_run_id": "M7-TRANSVERSAL-AUDIT", "auditor_skill_id": "skill_auditar_suficiencia_semantica_b5_i2", "auditor_skill_version": "1.0.0", "provider_or_adapter": "controlled-fixture", "model_or_evaluator": "synthetic-contract-fixture", "execution_timestamp": "2026-09-06T00:00:00Z", "input_manifest_checksum": "d" * 64, "artifact_checksums": [{"artifact_kind": "research", "artifact_id": research_id, "checksum": "e" * 64, "producer_run_id": "M7-M5"}, {"artifact_kind": "evidence_report", "artifact_id": source_id, "checksum": "f" * 64, "producer_run_id": "M7-SOURCE"}, {"artifact_kind": "provisional_thesis", "artifact_id": f"{research_id}:THESIS:PROVISIONAL", "checksum": "1" * 64, "producer_run_id": "M7-B2"}, *audited], "audit_method": "CONTROLLED_SYNTHETIC_CONTRACT", "audited_artifact_ids": [f"analysis:{analysis_id}", f"curation:{curation_id}", f"refined_thesis:{refined_thesis_payload['thesis_id']}", f"script_promise:{promise['promise_id']}"], "audited_artifact_versions": audited, "criteria_results": [{"criterion": item, "status": "SATISFIED", "summary": "Fixture de compatibilidad."} for item in criteria], "findings": [{"criterion": item, "status": "SATISFIED", "anchored_findings": [], "rationale": "Fixture de compatibilidad."} for item in criteria], "blocking_defects": [], "non_blocking_defects": [], "cited_evidence": ["S1"], "required_corrections": [], "unresolved_questions": [], "inherited_restrictions_checked": [], "auditor_statement": "Fixture sintético; no es aprobación funcional.", "artifact_references": [f"analysis:{analysis_id}", f"curation:{curation_id}", f"refined_thesis:{refined_thesis_payload['thesis_id']}", f"script_promise:{promise['promise_id']}"], "producer_run_reference": "M7-TRANSVERSAL-FIXTURE", "auditor_run_reference": "M7-TRANSVERSAL-AUDIT", "producer_actor_id": "m7-fixture", "auditor_actor_id": "m7-fixture-auditor", "auditor_input_checksum": "2" * 64, "auditor_write_scope": "AUDIT_ONLY", "independence_result": "PASS", "dimension_results": [{"dimension": item, "status": "PASS", "summary": "Fixture de compatibilidad."} for item in ["TRIVIAL_THESIS", "INTERCHANGEABLE_ANALYSIS", "DECORATIVE_OBJECTION", "FALSE_DEPTH"]], "required_changes": [], "excluded_claims_detected": [], "unsupported_inferences": [], "redundancy_findings": [], "progression_findings": [], "thesis_refinement_finding": {"status": "PASS", "summary": "Fixture de compatibilidad."}, "blocking_reasons": [], "reaudit_requirements": [], "decision": "PASS", "readiness": "BLOCKED", "created_at": "2026-09-06T00:00:00Z",
    }
    audit["audit_method"] = "AI_SEMANTIC_REVIEW"
    anchor = {"artifact_kind": "analysis", "artifact_id": analysis_id, "artifact_field": "statement", "evaluated_excerpt": "Lectura sintética limitada.", "evidence_refs": [f"F-{episode_id}"], "evidence_excerpts": [{"evidence_ref": f"F-{episode_id}", "excerpt": "Lectura sintética limitada."}], "editorial_comparison": "Comparación controlada.", "why_specific_or_generic": "Anclaje sintético explícito.", "decision": "SATISFIED"}
    audit["findings"] = [{"criterion": item, "status": "SATISFIED", "anchored_findings": [deepcopy(anchor)], "rationale": "Fixture de compatibilidad."} for item in criteria]
    review = {
        "review_id": f"YT-REV-{episode_id}", "episode_id": episode_id, "artifact_id": f"YT-PKG-{episode_id}", "artifact_checksum": "3" * 64, "producer_run_id": "M7-TRANSVERSAL-PRODUCER", "auditor_run_id": "M7-TRANSVERSAL-AUDITOR", "independence_check": {"producer_actor_id": "m7-fixture", "auditor_actor_id": "m7-fixture-auditor", "producer_run_id": "M7-TRANSVERSAL-PRODUCER", "auditor_run_id": "M7-TRANSVERSAL-AUDITOR", "decision": "PASS"}, "active_profile_reference": {"profile_id": profile_id, "profile_version": profile_version, "profile_checksum": profile_checksum}, "capability_results": {}, "overpromise_decision": {"decision": "PASS", "rationale": "Fixture de compatibilidad.", "evidence_refs": ["S1"], "mitigation_or_pending": None, "blocking_reason": None}, "unsupported_elements": [], "platform_risk_summary": {"severity": "LOW", "summary": "Fixture controlado.", "mitigations": [], "uncertainties": [], "evidence_refs": ["S1"]}, "rights_reuse_summary": {"severity": "LOW", "summary": "Fixture controlado.", "mitigations": [], "unresolved_items": [], "evidence_refs": ["S1"]}, "opening_readiness": {"decision": "PASS", "rationale": "No se diseña apertura.", "pending_items": []}, "duration_assessment": {"decision": "PASS", "rationale": "No se ejecuta narrativa.", "recommended_range": "15 minutos"}, "findings": [], "required_changes": [], "blocking_reasons": [], "unresolved_items": [], "publication_limit": {"DOES_NOT_AUTHORIZE": ["B5_I3", "FINAL_PACKAGING", "PRODUCTION", "PUBLICATION"]}, "strategic_return": {"return_required": False, "target_domain": None, "strategic_triggers": {"political_partisan_sensitivity": False, "high_sensitivity": False, "audience_matrix_change": False, "excluded_boundary_reinterpretation": False, "new_personal_exposure": False, "voice_or_author_persona_change": False, "positioning_expansion": False, "permanent_effect": False, "high_precedent_risk": False, "experimental_territory": False}, "reason": None, "evidence_refs": []}, "decision": "APPROVAL", "created_at": "2026-09-06T00:00:00Z",
    }
    capability_result = {"decision": "PASS", "rationale": "Fixture de compatibilidad; no ejecuta la capacidad.", "evidence_refs": ["S1"], "mitigation_or_pending": None, "blocking_reason": None}
    review["capability_results"] = {key: deepcopy(capability_result) for key in ["YT_EARLY_AUDIENCE_FIT", "YT_VISIBLE_PROMISE", "YT_EARLY_PACKAGING_HYPOTHESIS", "YT_PROMISE_CONTENT_ALIGNMENT", "YT_OPENING_READINESS", "YT_DURATION_ENVELOPE", "YT_OVERPROMISE_REVIEW", "YT_TEXT_PLATFORM_RISK", "YT_SCRIPT_RIGHTS_REUSE_RISK"]}
    review["duration_assessment"]["recommended_range"] = "10-15 minutos"
    review["publication_limit"]["DOES_NOT_AUTHORIZE"] = ["B5_I3", "FINAL_PACKAGING", "PRODUCTION", "PUBLICATION", "LEGAL_APPROVAL", "MONETIZATION_GUARANTEE"]
    return {"human_input": human, "active_editorial_profile_reference": dict(profile), "episode_brief": brief, "narrative_human_analysis": analysis, "material_curation": curation, "editorial_script_promise": promise, "early_packaging_hypothesis": packaging, "b5_i2_semantic_audit": audit, "youtube_adaptation_review": review}


def source_report(episode_id: str, research_id: str) -> dict[str, Any]:
    provenance = {
        "source_kind": "SOURCE_ORIGINAL",
        "original_source_ref": None,
        "derived_from_source_ref": None,
        "version": "1.0.0",
        "original_language": "es",
        "derivative_language": None,
        "locator": "fixture://S1",
        "acquisition_method": "DIRECT_ACCESS",
        "transformation_method": "NONE",
        "transcription_type": "NOT_APPLICABLE",
        "verification_status": "PRIMARY_VERIFIED",
        "translation_transcription_risk": "NONE",
        "limitations": [],
        "permitted_uses": ["CONTEXT_ONLY"],
        "primary_verification_required": False,
        "primary_verification_performed": True,
        "claim_authority": "PRIMARY",
        "authority_domain": "GENERAL",
        "official_primary": False,
    }
    source = {
        "source_id": "S1",
        "title": "Fuente sintética materializada por Software",
        "source_type": "PRIMARY",
        "url": "fixture://S1",
        "access_type": "DIRECT",
        "locator": "fixture://S1",
        "confidence": "HIGH",
        "provenance": provenance,
    }
    return {
        "report_id": f"{research_id}:SOURCE_ACCESS",
        "episode_id": episode_id,
        "research_id": research_id,
        "brief_version": "1.0.0",
        "material_principal_disponible": True,
        "tipo_de_acceso": "DIRECT",
        "fuentes_primarias": [source],
        "fuentes_secundarias": [],
        "escenas_verificadas": [{
            "scene_id": "SC-S1",
            "description": "Registro sintético recuperado.",
            "source_id": "S1",
            "locator": "fixture://S1#scene",
            "verification_mode": "DIRECT",
        }],
        "escenas_descritas_indirectamente": [],
        "claims_sostenibles": [{
            "claim_id": f"{research_id}:CLAIM:S1",
            "claim_text": "La fuente sintética documenta el fenómeno con alcance limitado.",
            "source_refs": ["S1"],
            "locator": "fixture://S1#claim",
            "confidence": "HIGH",
        }],
        "claims_pendientes": [],
        "limitaciones": ["Fixture controlado; no representa investigación real."],
        "nivel_de_confianza": "HIGH",
        "can_proceed": True,
        "required_disclosures": ["Contenido sintético."],
        "independence_groups": [{
            "group_id": "GRP-S1", "source_ids": ["S1"],
            "independence": "INDEPENDENT", "rationale": "Fuente fixture única.",
        }],
        "coverage_gaps": [{
            "dimension": "TRANSFERENCIA",
            "reason": "No se prueba fuera del fixture.",
            "impact": "NON_CRITICAL",
            "mitigation": "Mantener límite explícito.",
        }],
        "reopening_conditions": [{
            "condition_id": "REOPEN-S1",
            "trigger_type": "NEW_EVIDENCE",
            "description": "Nueva evidencia material.",
        }],
        "claim_dependent_source_evaluations": [{
            "claim_id": f"{research_id}:CLAIM:S1",
            "source_id": "S1",
            "object_relation": "Directa",
            "claim_authority": "Alta",
            "access_level": "DIRECT",
            "independence": "INDEPENDENT",
            "currency": "Vigente",
            "locator": "fixture://S1#claim",
            "assessment": "SUPPORTED",
        }],
        "allowed_analyses": ["CONTEXTUAL_ANALYSIS"],
        "limited_analyses": [],
        "prohibited_analyses": [],
        "excluded_claims": [],
        "propagated_constraints": [],
        "critical_claim_assessments": [],
        "critical_claims_propagation": {
            "status": "NONE_JUSTIFIED",
            "claim_ids": [],
            "justification": "Fixture sin claims críticos.",
            "editorial_impact": "LIMITED",
            "scope_decision": "REDUCED_SCOPE",
        },
        "sufficiency_basis": {
            "central_question": "¿Qué puede sostenerse con evidencia?",
            "critical_claims": [],
            "analysis_type": "CONTEXTUAL_ANALYSIS",
            "material_roles": ["PRIMARY_NARRATIVE_MATERIAL"],
            "requested_depth": "PROFUNDO",
            "research_coverage": "Cobertura controlada.",
        },
        "multilingual_research": {
            "activation_status": "NOT_ACTIVATED",
            "triggers": [],
            "non_trigger_examples": ["NO_LINGUISTIC_DIFFERENCE_REQUIRED"],
            "affected_source_ids": [],
            "affected_claim_ids": [],
            "required_language": None,
            "material_risk": [],
            "consultation_result": "NOT_APPLICABLE",
            "limitations": [],
            "invalidators": [],
            "return_route": "NOT_APPLICABLE",
            "decision_basis": "No depende de una diferencia lingüística material.",
        },
        "created_at": "2026-09-06T00:00:00+00:00",
    }


def research_plan(human_input: Mapping[str, Any]) -> dict[str, Any]:
    episode_id = str(human_input["episode_id"])
    research_id = f"RP-M7-{episode_id}"
    work_ids = [str(item) for item in human_input["works"]]
    target = human_input["target_final_works"]
    if isinstance(target, Mapping):
        requested_count = int(target["requested_count"])
        status = str(target.get("status", "CONFIRMED"))
        basis = str(target.get("decision_basis", "Decisión explícita del fixture."))
        decision_ref = target.get("decision_ref")
    else:
        requested_count = int(target)
        status = "CONFIRMED"
        basis = "Decisión explícita del input sintético controlado."
        decision_ref = "human-input:target-final-works"
    return {
        "contract": "research_plan",
        "contract_version": "2.0.0",
        "research_plan_id": research_id,
        "episode_id": episode_id,
        "brief_version": "1.0.0",
        "research_role": "NORMAL",
        "editorial_intent": "NO_DECLARADA",
        "editorial_intent_provenance": {"source": "USER_INTAKE", "reference": f"human-input:{episode_id}"},
        "origin": {"input_ref": f"human-input:{episode_id}", "source_kind": "HUMAN_EPISODE_INPUT", "question_ref": f"question:{episode_id}"},
        "central_question": {"question": str(human_input["initial_question"]), "decision_relevance": "Define el alcance investigativo."},
        "intended_use": {"uses": ["RESEARCH_AND_THESIS"], "required_outputs": ["claims", "limitations"]},
        "scope": {"included": [str(human_input["topic"]), "obras declaradas por el input"], "excluded": ["Arquitectura narrativa"]},
        "dimensions": [{"dimension_id": "D-PHENOMENON", "label": "Fenómeno", "research_question": "¿Qué evidencia lo describe?"}],
        "subquestions": [{"subquestion_id": "SQ-1", "dimension_id": "D-PHENOMENON", "question": "¿Qué evidencia lo describe?"}],
        "evidence_requirements": [{"evidence_requirement_id": "ER-1", "subquestion_refs": ["SQ-1"], "evidence_kind": "EXTERNAL_REALITY_EVIDENCE", "minimum_strength": "Fuente primaria o especialista adecuada al claim concreto.", "preferred_source_types": ["PRIMARY_SOURCE"], "failure_condition": "No se puede sostener el claim.", "claim_specific_basis": "Identidad de fuente, localizador reproducible y correspondencia con la afirmación.", "required_evidence_properties": ["identity", "locator", "claim_alignment"], "disqualifying_conditions": ["fuente no verificable"]}],
        "source_strategy": [{"strategy_id": "SS-1", "source_types": ["PRIMARY_SOURCE"], "purpose": "Contrastar el fenómeno.", "limitations": ["Acceso controlado."]}],
        "critical_claims": [{"claim_id": "CL-1", "statement": "El fenómeno presenta una característica observable.", "intended_use": "CENTRAL_CLAIM_SUPPORT", "strength": "Afirmación descriptiva dentro del alcance declarado.", "evidence_requirement_refs": ["ER-1"], "material_if_false": True, "claim_dimensions": {"nature": "descriptive observation", "scope": "fixture and declared phenomenon only", "contestation": "open to rival explanation", "conditions": ["no causal generalization"]}}],
        "rival_refutation": [{"rival_id": "RV-1", "explanation": "Explicación alternativa.", "refutation_signals": ["Evidencia incompatible."], "evidence_requirement_refs": ["ER-1"]}],
        "gaps_risks": [{"gap_id": "G-1", "kind": "EVIDENCE", "description": "Falta transferencia externa.", "material_impact": "Limita el claim.", "mitigation": "Mantener alcance limitado."}],
        "potential_specialists": [],
        "sufficiency_criteria": [{"criterion_id": "SC-1", "dimension_id": "D-PHENOMENON", "condition": "Existe evidencia suficiente para el uso previsto.", "pass_route": "CONTINUE_WITH_LIMITATIONS"}],
        "target_final_works_decision": {"status": status, "requested_count": requested_count, "decision_basis": basis, "decision_ref": decision_ref},
        "supplied_works": [{"work_ref": f"work:{work_id}", "research_role": "NORMAL", "editorial_intent": "NO_DECLARADA", "origin_ref": f"human-input:{episode_id}"} for work_id in work_ids],
        "selection_policy": {"mode": "OWNER_OR_DELEGATED", "decision_rule": "Comparar evidencia, fidelidad y complementariedad.", "reconsideration_rule": "Reabrir si cambia la defendibilidad.", "decision_ref": None},
        "origin_artifact_refs": [{"artifact_ref": f"human-input:{episode_id}", "artifact_kind": "human_episode_input", "artifact_version": "1.0.0", "checksum": None}],
        "planned_stages": ["PLANNING", "BASE_RESEARCH", "SYNTHESIS"],
        "created_at": "2026-09-06T00:00:00+00:00",
    }


def research_plan_proposal(human_input: Mapping[str, Any]) -> dict[str, Any]:
    """Return the synthetic cognitive proposal consumed by the real binder."""
    topic = str(human_input["topic"])
    question = str(human_input["initial_question"])
    works = [str(item) for item in human_input["works"]]
    return {
        "contract": "research_plan_proposal",
        "contract_version": "1.0.0",
        "central_question": question,
        "intended_use": "RESEARCH_AND_THESIS",
        "scope": f"Cobertura controlada de {topic}.",
        "dimensions": ["Fenómeno", "Obras declaradas"],
        "subquestions": ["¿Qué evidencia describe el fenómeno?", "¿Qué aportan las obras declaradas?"],
        "evidence_requirements": ["Evidencia verificable para el fenómeno y las obras."],
        "source_strategy": "Material local controlado; sin búsqueda web.",
        "critical_claims": ["No exceder la evidencia disponible."],
        "rival_refutation": ["Considerar explicaciones alternativas."],
        "gaps_risks": ["El fixture no representa investigación real."],
        "potential_specialists": [],
        "sufficiency_criteria": ["Evidencia suficiente para el uso declarado."],
        "target_final_works_decision": {
            "status": "CONFIRMED",
            "requested_count": int(human_input["target_final_works"]),
            "decision_basis": "Decisión explícita del input sintético controlado.",
            "decision_ref": "human-input:target-final-works",
        },
        "supplied_works": [{"work_ref": work_id} for work_id in works],
        "selection_policy": {"mode": "OWNER_OR_DELEGATED", "decision_rule": "Decisión explícita"},
        "planned_stages": ["PLANNING", "BASE_RESEARCH", "SYNTHESIS"],
    }


def phenomenon(episode_id: str, research_id: str, topic: str) -> dict[str, Any]:
    report = source_report(episode_id, research_id)
    return {
        "research_id": research_id,
        "episode_id": episode_id,
        "brief_version": "1.0.0",
        "scope": f"Cobertura controlada de {topic}.",
        "facts": [{"item_id": "I1", "statement": "Hecho sintético recuperado.", "source_refs": ["S1"], "locator": "fixture://S1#fact", "confidence": "HIGH"}],
        "interpretations": [{"item_id": "I2", "statement": "Lectura interpretativa limitada.", "source_refs": ["S1"], "locator": "fixture://S1#interpretation", "confidence": "MEDIUM"}],
        "hypotheses": [], "contradictions": [], "alternative_views": [],
        "coverage": [{"dimension_id": d, "status": "COVERED", "related_finding_ids": ["I1"], "related_source_ids": ["S1"], "limitation_or_pending": None, "scope_decision": "NONE", "editorial_impact": "NOT_APPLICABLE", "propagated_constraint": None, "mitigation_status": "NOT_REQUIRED"} for d in ["CENTRAL_QUESTION", "CONFLICT", "INITIAL_HYPOTHESIS", "HUMAN_SOCIAL_HISTORICAL_OR_CULTURAL_PHENOMENON", "PRIMARY_NARRATIVE_MATERIAL", "CRITICAL_CLAIMS", "ALTERNATIVE_PERSPECTIVES"]],
        "critical_claims_assessment": {"status": "NONE_JUSTIFIED", "claim_ids": [], "justification": "Fixture sin claim central autónomo.", "editorial_impact": "LIMITED"},
        "narrative_evidence": [{"item_id": "N1", "statement": "Pasaje sintético.", "source_refs": ["S1"], "locator": "fixture://S1#scene", "confidence": "HIGH", "evidence_kind": "SCENE"}],
        "external_reality_evidence": [{"item_id": "E1", "statement": "Registro sintético.", "source_refs": ["S1"], "locator": "fixture://S1#claim", "confidence": "HIGH", "evidence_kind": "STUDY"}],
        "source_registry": [{"source_id": "S1", "title": "Fuente sintética", "source_type": "PRIMARY", "url": "fixture://S1", "access_type": "DIRECT", "locator": "fixture://S1", "confidence": "HIGH", "provenance": report["fuentes_primarias"][0]["provenance"]}, {"source_id": "SUGGESTED_ONLY", "title": "Fuente solo sugerida", "source_type": "PRIMARY", "url": "fixture://not-recovered", "access_type": "INDIRECT", "locator": "not-recovered", "confidence": "LOW", "provenance": {**report["fuentes_primarias"][0]["provenance"], "verification_status": "NOT_VERIFIED"}}],
        "claims_candidates": [{"item_id": "CLAIM-X", "statement": "Claim limitado.", "source_refs": ["S1"], "locator": "fixture://S1#claim", "confidence": "MEDIUM"}],
        "unsupported_claims": [], "limitations": ["No generalizar fuera del fixture."],
        "multilingual_research": report["multilingual_research"],
        "research_sufficiency": "LIMITED_BUT_USABLE",
        "evidence_type_separation": {"work_evidence_refs": [], "external_reality_evidence_refs": ["S1"]},
        "research_pack_kind": "PHENOMENON",
        "phenomenon": {"phenomenon_id": f"PHEN-{research_id}", "phenomenon_kind": "CULTURAL", "definition": f"Fenómeno sintético de {topic}."},
    }


def discovery(episode_id: str, research_id: str, work_ids: list[str]) -> dict[str, Any]:
    return {
        "lifecycle_id": f"{research_id}:DISCOVERY",
        "lifecycle_version": "2.0.0",
        "episode_id": episode_id,
        "research_id": research_id,
        "entry_mode": "TOPIC_FIRST",
        "anchor_work_id": None,
        "works": [{"work_id": work_id, "state": "DISCOVERED_WORK", "state_version": "2.0.0", "identity_ref": f"identity:{work_id}", "version_ref": f"version:{work_id}", "is_anchor": False, "lineage_refs": [f"human-input:{episode_id}"], "stage_evidence_refs": [], "research_stage": "DISCOVERY", "selection_state": "NOT_EVALUATED", "preliminary_fidelity": "NOT_ASSESSED", "deep_fidelity": "NOT_ASSESSED", "research_sufficiency": "MORE_RESEARCH_REQUIRED", "artifact_validity": "VALID", "thesis_stage": "NONE", "research_contract_version": "2.0.0"} for work_id in work_ids],
        "transitions": [],
        "screening": {"candidate_work_ids": [], "format_policy_ref": "policies/script_product/main_episode_format_policy.md", "range_status": "NOT_APPLICABLE", "exception": None},
        "final_selection": {"selected_work_ids": [], "format_policy_ref": "policies/script_product/main_episode_format_policy.md", "range_status": "NOT_APPLICABLE", "curation_ref": None, "exception": None},
        "critical_doubts": [], "created_at": "2026-09-06T00:00:00+00:00", "research_contract_version": "2.0.0",
    }


def dossier(episode_id: str, research_id: str, work_id: str, stage: str = "BASE_RESEARCH", fidelity: str = "NOT_ASSESSED") -> dict[str, Any]:
    return {
        "dossier_id": f"D-{work_id}", "dossier_version": "2.0.0", "episode_id": episode_id, "research_id": research_id, "evidence_report_id": f"{research_id}:SOURCE_ACCESS",
        "work": {"material_id": work_id, "title": f"Obra {work_id}", "creator": "Creador sintético", "consulted_representations": [{"representation_kind": "ORIGINAL_WORK", "edition_or_version": "fixture-1", "consulted_locator": f"fixture://{work_id}"}]},
        "dossier_stage": "RESEARCH_IN_PROGRESS", "pending_items": [], "confidence": "MEDIUM", "created_at": "2026-09-06T00:00:00+00:00", "research_stage": stage, "selection_state": "CANDIDATE", "preliminary_fidelity": fidelity, "deep_fidelity": "NOT_ASSESSED", "research_sufficiency": "MORE_RESEARCH_REQUIRED", "artifact_validity": "VALID", "thesis_stage": "NONE", "research_contract_version": "2.0.0", "lineage": [f"human-input:{episode_id}"],
    }


def sufficiency(research_id: str, subject_kind: str = "PHENOMENON", subject_ref: str | None = None, intended_use: str = "FORMULAR_TESIS_PROVISIONAL", status: str = "SUFFICIENT_FOR_INTENDED_USE") -> dict[str, Any]:
    return {"decision_id": f"RSD-{research_id}-{subject_kind}-{subject_ref or research_id}", "decision_version": "2.0.0", "subject_kind": subject_kind, "subject_ref": subject_ref or research_id, "intended_use": intended_use, "evidence_refs": ["S1"], "claim_decision": None, "sufficiency_status": status, "limitations": ["Alcance controlado."] if status == "LIMITED_BUT_USABLE" else [], "pending_matters": ["Nueva evidencia requerida."] if status == "MORE_RESEARCH_REQUIRED" else [], "unresolved_material_contradiction_refs": [], "invalidators": ["NEW_MATERIAL_EVIDENCE"], "return_route": "Continuar según el uso declarado.", "decision_basis": "Decisión sintética sobre evidencia materializada.", "research_contract_version": "2.0.0", "artifact_validity": "VALID", "research_stage": "BASE_RESEARCH"}


def comparison(research_id: str, work_ids: list[str], *, post_deep: bool = False, selection_mode: str = "USER_SELECTION", authority_ref: str | None = None) -> dict[str, Any]:
    value = {"dimensions": ["CONTRIBUTION", "COVERAGE", "COMPLEMENTARITY", "REDUNDANCY", "CONTRAST", "FIDELITY", "LIMITATIONS", "EVIDENCE"], "entries": [{"work_id": work_id, "evidence_refs": [f"D-{work_id}"], "contribution": "Aporta evidencia propia.", "coverage": "Cubre una dimensión declarada.", "complementarity": "Complementa el conjunto.", "redundancy": "Redundancia revisada.", "contrast": "Permite contraste investigativo.", "fidelity": "Fidelidad documentada.", "limitations": ["No decide orden narrativo."], **({"missing_perspectives": [], "overinterpretation_risk": "Bajo si se conserva el alcance."} if post_deep else {})} for work_id in work_ids], "decision_stage": "POST_DEEP_REEVALUATION" if post_deep else "INITIAL_RESEARCH_COMPARISON", "narrative_decision_made": False, "created_at": "2026-09-06T00:00:00+00:00"}
    if post_deep:
        value.update({"selected_work_ids": list(work_ids), "selection_mode": selection_mode, "selection_authority_ref": authority_ref, "human_decision_required": False, "set_recommendations": [{"recommendation_id": "REC-KEEP", "action": "MAINTAIN", "affected_work_ids": list(work_ids), "rationale": "El conjunto conserva complementariedad.", "evidence_refs": [f"D-{work_ids[0]}"], "material_change": False}]})
    else:
        value["comparison_id"] = f"{research_id}:COMPARISON:INITIAL"
        value["comparison_version"] = "2.0.0"
        value["episode_id"] = research_id.removeprefix("RP-M7-")
        value["research_id"] = research_id
        value["candidate_work_ids"] = list(work_ids)
        value["deepening_targets"] = {"phenomenon": {"targets": ["DEEPEN_MATERIAL_CLAIM"]}, "works": {work_id: {"targets": [f"DEEPEN_{work_id}_CLAIM"]} for work_id in work_ids}}
    return value


def deep_research(episode_id: str, research_id: str, work_id: str) -> dict[str, Any]:
    value = dossier(episode_id, research_id, work_id, stage="DEEP_RESEARCH")
    value.update({"evidence_type_separation": {"work_evidence_refs": [f"D-{work_id}"], "external_reality_evidence_refs": ["S1"]}, "deep_research": {"facts": [f"Hecho verificable de {work_id}."], "actions": [f"Acción observable de {work_id}."], "decisions": [f"Decisión observable de {work_id}."], "consequences": [f"Consecuencia documentada de {work_id}."], "interpretations": [f"Interpretación limitada de {work_id}."], "rival_readings": [f"Lectura rival de {work_id}."], "contradictions": [], "limits": ["No permite generalizar."], "risks": ["Sobreinterpretación controlada."], "pending_questions": [], "work_evidence_refs": [f"D-{work_id}"], "external_reality_evidence_refs": ["S1"]}, "provisional_thesis_relation": {"thesis_ref": f"{research_id}:THESIS:PROVISIONAL", "supports": ["Apoyo parcial."], "qualifies": ["Alcance limitado."], "does_not_establish": ["No demuestra causalidad."], "refutation_signals": ["Nueva evidencia contraria."]}})
    return value


def claims(work_ids: list[str]) -> dict[str, Any]:
    first = work_ids[0]
    return {"claims": [{"claim_id": "C-EXT", "claim_text": "El fenómeno admite una explicación limitada.", "claim_type": "INTERPRETATION", "source_refs": ["S1"], "external_reality_evidence_refs": ["S1"], "work_evidence_refs": [], "supporting_evidence_refs": ["S1"], "limiting_evidence_refs": ["S1"], "refuting_evidence_refs": ["S1"], "verification_status": "VERIFIED", "confidence": 0.8, "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT", "claim_decision": "CLAIM_LIMITED", "research_sufficiency": "LIMITED_BUT_USABLE", "limitations": "El rival limita la generalización.", "decision_basis": "Evidencia externa limitada.", "return_route": "Usar con alcance limitado.", "materiality": {"is_material": True, "activation_criteria": ["THESIS_DEPENDENCY"], "non_trigger_examples": [], "invalidator_codes": ["NEW_MATERIAL_EVIDENCE"], "return_route_code": "RESTRICT_FORMULATION_AND_DISCLOSE", "decision_ref": None}, "contradiction_refs": [], "pending_matters": []}, {"claim_id": "C-WORK", "claim_text": "La obra documenta una conducta observable.", "claim_type": "INTERPRETATION", "source_refs": [f"D-{first}"], "external_reality_evidence_refs": [], "work_evidence_refs": [f"D-{first}"], "supporting_evidence_refs": [f"D-{first}"], "limiting_evidence_refs": [f"D-{first}"], "refuting_evidence_refs": [], "verification_status": "VERIFIED", "confidence": 0.7, "criticality": "SECONDARY", "intended_use": "NARRATIVE_MATERIAL", "claim_decision": "CLAIM_LIMITED", "research_sufficiency": "LIMITED_BUT_USABLE", "limitations": "No prueba una regularidad externa.", "decision_basis": "Evidencia de obra.", "return_route": "Describir sin generalizar.", "materiality": {"is_material": True, "activation_criteria": ["WORK_FIDELITY"], "non_trigger_examples": [], "invalidator_codes": ["WORK_VERSION_OR_ADAPTATION_CHANGED"], "return_route_code": "RESTRICT_FORMULATION_AND_DISCLOSE", "decision_ref": None}, "contradiction_refs": [], "pending_matters": []}], "evidence_type_separation": {"work_evidence_refs": [f"D-{first}"], "external_reality_evidence_refs": ["S1"]}, "rival_explanations": [{"rival_id": "RIVAL-1", "statement": "Una explicación rival limita la fuerza causal.", "affected_claim_ids": ["C-EXT"], "evidence_refs": ["S1"], "material_impact": "Limita la generalización.", "disposition": "Se conserva como límite."}], "contradictions": [], "gaps": [{"gap_id": "GAP-1", "statement": "Falta transferencia a otros contextos.", "affected_claim_ids": ["C-EXT"], "evidence_refs": [], "materiality": "MATERIAL", "status": "OPEN", "return_route": "RETURN_TO_RESEARCH"}]}


def refined_thesis(research_id: str, work_ids: list[str]) -> dict[str, Any]:
    first = work_ids[0]
    return {"provisional_disposition": "LIMITED", "statement": "La tesis se sostiene solo como interpretación limitada.", "supporting_evidence_refs": ["S1"], "counterevidence_refs": [f"D-{first}"], "rival_interpretations": ["La explicación rival reduce la generalización."], "main_objection": "La evidencia no permite causalidad universal.", "nuance": "La obra ilustra una relación sin demostrarla fuera de ella.", "material_contributions": [{"material_id": work_id, "contribution": "Aporta contraste documentado."} for work_id in work_ids], "analysis_confirmed": ["La pregunta sigue siendo investigable."], "changes_from_provisional": ["Se limita el alcance."], "discarded_from_provisional": ["La generalización universal."], "refinement_rationale": "Los rivales y los límites obligan a restringir la tesis.", "refinement_dimensions": [{"dimension": "CAUSALITY", "provisional_position": "Explicación amplia.", "resulting_position": "Interpretación condicionada.", "evidence_refs": ["S1"], "rationale": "La evidencia rival limita la inferencia."}], "inherited_constraint_ids": [], "statement_unchanged_justification": None, "limits": ["No confundir obra y realidad externa."], "revision_conditions": ["Nueva evidencia material."], "refined_position": "Posición investigativa limitada.", "what_was_confirmed": ["La relación sigue siendo relevante."], "what_was_changed": ["Se redujo la fuerza de la afirmación."], "what_was_rejected": ["Causalidad universal."], "what_was_limited": ["Generalización fuera del contexto."], "strongest_objection": "La evidencia puede ser contextual.", "alternative_explanation": "El contexto explica parte del patrón.", "conditions_of_validity": ["Mantener el alcance delimitado."], "remaining_uncertainties": ["Transferencia contextual."], "evidence_dependencies": ["S1", *[f"D-{work_id}" for work_id in work_ids]]}


def audit(request: Any) -> dict[str, Any]:
    criteria = request.prepared_contract["input_payload"]["audit_scope"]["required_criteria"]
    evidence_ref = request.input_artifacts[0]["artifact_id"]
    return {"audit_id": "M7-SYNTHETIC-INDEPENDENT-AUDIT", "audit_version": "1.0.0", "audited_artifacts": [{"artifact_id": evidence_ref, "checksum": "0" * 64, "producer_run_id": "M7-SYNTHETIC"}], "research_ready_state": "RESEARCH_READY_WITH_LIMITATIONS", "independence_result": "PASS", "findings": [{"criterion": criterion, "status": "SATISFIED", "evidence_refs": [evidence_ref], "limitations": [], "judgment_basis": "Criterio cubierto por la cadena canónica."} for criterion in criteria], "evidence_refs": [evidence_ref], "limitations": ["Ejecución sintética controlada."], "defects": [], "correction_routes": [], "decision": "PASS"}


class SyntheticResearchExecutor:
    """Dispatch only cognitive payloads; canonical Software owns all binding."""

    def __init__(self, human_input: Mapping[str, Any]):
        self.input = human_input
        self.episode_id = str(human_input["episode_id"])
        self.research_id = f"RP-M7-{self.episode_id}"
        self.work_ids = [str(item) for item in human_input["works"]]
        self.stop_status = str(human_input.get("deep_stop_status", "SUFFICIENT_FOR_INTENDED_USE"))

    def __call__(self, request: Any) -> Any:
        stage = request.stage
        topic = str(self.input["topic"])
        if stage == "RESEARCH_PLANNING":
            return research_plan_proposal(self.input)
        if stage == "PHENOMENON_BASE_RESEARCH":
            return phenomenon(self.episode_id, self.research_id, topic)
        if stage == "WORK_DISCOVERY":
            return discovery(self.episode_id, self.research_id, self.work_ids)
        if stage in {"BASE_RESEARCH_POOL", "PRELIMINARY_FIDELITY"}:
            ids = self.work_ids
            return [dossier(self.episode_id, self.research_id, work_id, stage="BASE_RESEARCH" if stage == "BASE_RESEARCH_POOL" else "PRELIMINARY_FIDELITY", fidelity="NOT_ASSESSED" if stage == "BASE_RESEARCH_POOL" else "APTA") for work_id in ids]
        if stage == "INITIAL_SUFFICIENCY":
            status = "SUFFICIENT_FOR_INTENDED_USE"
            return [sufficiency(self.research_id)] + [sufficiency(self.research_id, "WORK_RESEARCH_DOSSIER", f"{self.research_id}:DOSSIER:{work_id}", "RESEARCH_COMPARISON", status) for work_id in self.work_ids]
        if stage == "PROVISIONAL_THESIS":
            return {"thesis_id": f"{self.research_id}:THESIS:PROVISIONAL", "episode_id": self.episode_id, "brief_version": "1.0.0", "research_id": self.research_id, "evidence_report_id": f"{self.research_id}:SOURCE_ACCESS", "stage": "THESIS_PROVISIONAL", "statement": "El fenómeno admite una explicación condicionada.", "premises": [{"premise_id": "P1", "statement": "Existe evidencia recuperada.", "finding_ids": ["I1"], "source_refs": ["S1"]}], "supporting_findings": ["I1"], "tensioning_evidence": [{"finding_id": "I2", "explanation": "Matiza."}], "alternative_explanations": ["Otro factor."], "assumptions": ["El fixture representa el alcance declarado."], "revision_conditions": ["Nueva evidencia."], "inherited_constraints": ["Contenido sintético.", "Fixture controlado; no representa investigación real."], "open_questions": ["¿Qué evidencia adicional cambiaría la tesis?"], "version": "2.0.0", "created_at": "2026-09-06T00:00:00+00:00"}
        if stage == "RESEARCH_COMPARISON":
            return comparison(self.research_id, self.work_ids)
        if stage == "DEEP_PHENOMENON_RESEARCH":
            return phenomenon(self.episode_id, self.research_id, topic)
        if stage == "DELEGATED_SELECTION":
            selected = list(self.input.get("_effective_selected_work_ids", self.work_ids))
            return {"selected_work_ids": selected, "set_rationale": "Conjunto delegado dentro del alcance autorizado.", "evidence_refs": [f"D-{work_id}" for work_id in selected], "criteria_used": ["evidencia", "fidelidad", "complementariedad"], "limitations": ["No es decisión narrativa final."]}
        if stage == "DEEP_PHENOMENON_SUFFICIENCY":
            status = "SUFFICIENT_FOR_INTENDED_USE" if self.input.get("_research_stop_new_evidence_ref") else self.stop_status
            return sufficiency(self.research_id, "PHENOMENON", self.research_id, "DEEP_PHENOMENON_RESEARCH", status)
        if stage in {"DEEP_WORK_RESEARCH", "DEEP_FIDELITY"}:
            work_id = request.prepared_contract["input_payload"].get("work_id")
            value = deep_research(self.episode_id, self.research_id, str(work_id))
            if stage == "DEEP_FIDELITY":
                value["deep_fidelity"] = "APROBADA"
            return value
        if stage == "DEEP_WORK_SUFFICIENCY":
            work_id = request.prepared_contract["input_payload"].get("work_id")
            return sufficiency(self.research_id, "WORK_RESEARCH_DOSSIER", str(request.prepared_contract["input_payload"].get("subject_ref")), "DEEP_WORK_RESEARCH", "SUFFICIENT_FOR_INTENDED_USE")
        if stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return claims(self.work_ids)
        if stage == "M5_POST_DEEP_SET_REEVALUATION":
            selected = list(self.input.get("_effective_selected_work_ids", self.work_ids))
            return comparison(self.research_id, selected, post_deep=True, selection_mode="DELEGATED_SELECTION" if self.input.get("selection_mode") == "DELEGATED" else "USER_SELECTION", authority_ref=self.input.get("_selection_authority_ref"))
        if stage == "M5_REFINED_THESIS":
            selected = list(self.input.get("_effective_selected_work_ids", self.work_ids))
            return refined_thesis(self.research_id, selected)
        if stage == "M6_INDEPENDENT_RESEARCH_AUDIT":
            return audit(request)
        raise RuntimeError(f"M7_SYNTHETIC_COGNITIVE_STAGE_UNSUPPORTED:{stage}")
