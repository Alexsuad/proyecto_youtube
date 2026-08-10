"""
Pruebas Unitarias de Integridad y Validación de los 24 JSON Schemas y sus Fixtures Válidos
"""

import os
import json
import unittest
import jsonschema
from jsonschema import Draft7Validator

from src.core.contract_validation import (
    SCHEMAS_DIR, 
    load_schema, 
    validate_against_schema,
    validate_editorial_script_approval,
    validate_human_production_approval,
    validate_human_publication_approval,
    validate_research_pack,
    validate_claims_ledger,
    validate_source_access_and_evidence_report,
    validate_work_research_dossier,
)

VALID_FIXTURES = {
    "agent_execution_profiles": {
        "registry_version": "2.0.0",
        "policy": {
            "model_selection_authority": "OWNER",
            "execution_route_selection_authority": "OWNER",
            "per_run_override_required": True,
            "any_supported_model_allowed": True,
            "defaults_are_non_binding": True,
            "benchmarks_determine_fit": True,
            "free_or_local_first": True,
            "paid_provider_requires_owner_approval": True,
            "executors_optional": True,
            "native_provider_preferred_for_product_runtime": True
        },
        "global_defaults": {
            "execution_route": "local_model",
            "execution_profile": "ollama_local",
            "timeout_seconds": 30,
            "max_retries": 0,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False
        },
        "providers": {
            "ollama": {"route_type": "LOCAL_MODEL_RUNTIME", "adapter": "ollama", "enabled": True, "api_base_env": "OLLAMA_API_BASE", "model_env": "OLLAMA_MODEL", "timeout_seconds": 30, "max_retries": 0, "cost_policy": "LOCAL_FREE"},
            "deepseek": {"route_type": "API_MODEL_RUNTIME", "adapter": "deepseek", "enabled": True, "api_base_env": "DEEPSEEK_API_BASE", "api_key_env": "DEEPSEEK_API_KEY", "model_env": "DEEPSEEK_MODEL", "timeout_seconds": 30, "max_retries": 0, "cost_policy": "OWNER_APPROVAL_REQUIRED_FOR_PAID_USAGE"},
            "openai": {"route_type": "API_MODEL_RUNTIME", "adapter": "openai_compatible", "enabled": True, "api_base_env": "OPENAI_API_BASE", "api_key_env": "OPENAI_API_KEY", "model_env": "OPENAI_MODEL", "timeout_seconds": 60, "max_retries": 1, "cost_policy": "OWNER_APPROVAL_REQUIRED_FOR_PAID_USAGE"}
        },
        "executors": {
            "native_provider": {"kind": "NATIVE_PROVIDER", "status": "READY"},
            "controlled_exec": {"kind": "CONTROLLED_EXECUTOR", "command": "runnerctl", "status": "HANDOFF_ONLY", "accepts_model_override": True, "managed_provider_identity": "MANAGED_BY_EXECUTOR", "managed_model_identity": "UNAVAILABLE_FROM_EXECUTOR"}
        },
        "execution_profiles": {
            "ollama_local": {"route_type": "LOCAL_MODEL_RUNTIME", "execution_route": "local_model", "executor": "native_provider", "provider": "ollama", "provider_config_ref": "ollama", "timeout_seconds": 30, "max_retries": 0, "cost_policy": "LOCAL_FREE", "supports_model_override": True, "default_model": None, "model_env": "OLLAMA_MODEL"},
            "deepseek_chat": {"route_type": "API_MODEL_RUNTIME", "execution_route": "api_model", "executor": "native_provider", "provider": "deepseek", "provider_config_ref": "deepseek", "timeout_seconds": 30, "max_retries": 0, "cost_policy": "OWNER_APPROVAL_REQUIRED_FOR_PAID_USAGE", "supports_model_override": True, "default_model": "deepseek-chat", "model_env": "DEEPSEEK_MODEL"},
            "managed_current": {"route_type": "AGENT_HARNESS_RUNTIME", "execution_route": "agent_harness", "executor": "controlled_exec", "provider": "MANAGED_BY_EXECUTOR", "timeout_seconds": 180, "max_retries": 1, "cost_policy": "PLAN_MANAGED", "supports_model_override": True, "model_selection": "USER_SELECTED_OR_EXECUTOR_MANAGED", "model_env": "MANAGED_MODEL_ENV"}
        },
        "role_defaults": {
            "SCRIPT_PRODUCT_PRODUCER": {"default_execution_profile": "ollama_local", "default_execution_route": "local_model", "allowed_execution_profiles": ["ollama_local", "deepseek_chat", "managed_current"]},
            "SCRIPT_PRODUCT_AUDITOR": {"default_execution_profile": "ollama_local", "default_execution_route": "local_model", "allowed_execution_profiles": ["ollama_local", "deepseek_chat", "managed_current"]}
        }
    },    "agent_prompt_registry": {
        "registry_version": "1.0.0",
        "prompts": [
            {"role_id":"ORCHESTRATION","prompt_id":"prompt_orch","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"RESEARCH_AND_CURATION","prompt_id":"prompt_rc","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"NARRATIVE_ARCHITECTURE","prompt_id":"prompt_na","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"WRITING","prompt_id":"prompt_writing","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"EDITOR","prompt_id":"prompt_editor","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"FINAL_EDITORIAL_AUDITOR","prompt_id":"prompt_fea","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"SCRIPT_PRODUCT_PRODUCER","prompt_id":"prompt_spp","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"SCRIPT_PRODUCT_AUDITOR","prompt_id":"prompt_spa","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"YOUTUBE_ADAPTATION_PRODUCER","prompt_id":"prompt_yap","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"YOUTUBE_ADAPTATION_AUDITOR","prompt_id":"prompt_yaa","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]}
        ]
    },
    "ai_runtime_config": {
        "registry_version": "1.0.0",
        "entries": [
            {"role_id":"ORCHESTRATION","provider":"mock","model":"default","adapter":"mock","tools":[],"permissions":{"read":[],"write":[]},"execution_mode":"DIRECT"}
        ]
    },
    "execution_provenance_registry": {
        "registry_version": "1.0.0",
        "runs": [
            {
                "run_id": "RUN-001",
                "episode_id": "EP-1",
                "role": "INDEPENDENT_EDITORIAL_AUDITOR",
                "skill_id": "skill_auditar_suficiencia_semantica_b5_i2",
                "skill_version": "1.0.0",
                "provider_or_adapter": "mock",
                "provider_kind": "SYNTHETIC",
                "model_or_evaluator": "mock",
                "input_manifest_checksum": "a" * 64,
                "outputs": [{"artifact_kind": "semantic_audit", "artifact_id": "AUD-1", "artifact_ref": "semantic_audit:AUD-1", "artifact_path": None, "checksum": "a" * 64}],
                "started_at": "2026-07-25T08:00:00Z",
                "completed_at": "2026-07-25T08:01:00Z",
                "status": "SUCCEEDED",
                "execution_mode": "SYNTHETIC",
                "agent_id": "INDEPENDENT_EDITORIAL_AUDITOR",
                "role_id": "INDEPENDENT_EDITORIAL_AUDITOR",
                "execution_route": "native:mock",
                "execution_profile": "mock_audit",
                "actual_executor": "native_provider",
                "actual_provider": "mock",
                "actual_model": "mock",
                "provider": "mock",
                "model": "mock",
                "prompt_version": "1.0.0",
                "input_artifact_ids": ["analysis:A-1"],
                "input_versions": ["RUN-P"],
                "input_checksums": ["a" * 64],
                "output_artifact_ids": ["semantic_audit:AUD-1"],
                "output_versions": ["RUN-001"],
                "output_checksums": ["a" * 64],
                "modification_manifest_source": "RUNTIME_PRE_POST_DIFF",
                "modified_artifact_ids": [],
                "modified_artifact_paths": [],
                "finished_at": "2026-07-25T08:01:00Z",
                "latency": 60,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0,
                "retry_count": 0,
                "decision": "SUCCEEDED",
                "error_type": "NONE",
                "blocking_reason": None,
                "handoff_target": "NONE"
            }
        ]
    },
    "run_configuration": {
        "role_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_route": "agent_harness",
        "execution_profile": "managed_current",
        "executor_override": "controlled_exec",
        "provider_override": None,
        "model_override": "managed-model",
        "timeout_seconds": 180,
        "max_retries": 1,
        "temperature": None,
        "max_tokens": None,
        "budget_limit": None,
        "paid_cost_approved": False
    },
    "execution_smoke_report": {
        "smoke_id": "SMOKE-001",
        "role_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_profile": "managed_current",
        "execution_route": "agent_harness",
        "selected_executor": "controlled_exec",
        "selected_provider": "MANAGED_BY_EXECUTOR",
        "selected_model": "managed-model",
        "actual_executor": "controlled_exec",
        "actual_provider": "MANAGED_BY_EXECUTOR",
        "actual_model": "UNAVAILABLE_FROM_EXECUTOR",
        "result": "SUCCEEDED",
        "decision": "SMOKE_PASS",
        "stdout_preview": "usage: runnerctl ...",
        "stderr_preview": "",
        "exit_code": 0,
        "notes": ["executor identity verified"]
    },
    "claims_ledger": {
        "ledger_id": "CL-001",
        "script_version": "1.0.0",
        "claims": [
            {
                "claim_id": "CLAIM-001",
                "script_location": "Bloque 1, Linea 10",
                "claim_text": "Dato historico verificado.",
                "claim_type": "FACT",
                "source_refs": [
                    "REF-001"
                ],
                "verification_status": "VERIFIED",
                "criticality": "CENTRAL",
                "intended_use": "CENTRAL_CLAIM_SUPPORT"
            }
        ]
    },
    "correction_routing_policy": {
        "defect_type": "FACTUAL_ERROR",
        "severity": "CRITICAL",
        "origin_artifact": "SCRIPT-001",
        "invalidated_artifacts": ["SHORTS-001"],
        "return_state": "DRAFT",
        "required_revalidation": "2026-07-21T22:00:00Z",
        "suggested_role": "EDITORIAL_LEAD"
    },
    "curation_decision": {
        "curation_id": "CUR-001",
        "research_version": "1.0.0",
        "preselected_materials": ["M1"],
        "selected_materials": ["M1"],
        "rejected_materials": [],
        "decision": "APPROVED"
    },
    "editorial_edit_report": {
        "input_version": "1.0.0",
        "output_version": "1.1.0",
        "edit_type": "RESTRUCTURE",
        "changes_by_category": {}
    },
    "editorial_learning_candidate": {
        "learning_id": "LEARN-001",
        "target_profile_id": "MADG-EDITORIAL-PROFILE",
        "target_profile_version": "1.0.0",
        "observed_change": "Ajuste de ritmo",
        "scope": "VOICE",
        "lineage": ["SAMPLE-001"],
        "evidence_items": [{"source_id": "SAMPLE-001", "locator": "fixtures/sample.md", "checksum": "a" * 64, "observation": "Patrón repetido"}],
        "confidence": 0.5,
        "examples": ["Ejemplo válido"],
        "counterexamples": ["Contraejemplo válido"],
        "exceptions": [],
        "functional_decision": {"status": "PENDING"},
        "status_history": [{"status": "CANDIDATE", "recorded_at": "2026-07-22T20:00:00Z"}]
    },
    "editorial_profile": {
        "profile_id": "MADG-EDITORIAL-PROFILE",
        "channel_id": "MasAllaDelGuion",
        "version": "1.0.0",
        "status": "DRAFT",
        "functional_owner_role": "CHANNEL_INTELLIGENCE",
        "source_lineage": [{"source_id": "B3-FUNCTIONAL-SPEC", "locator": "docs/specifications/B3_editorial_profile_functional_specification.md", "checksum": "a" * 64, "role": "FUNCTIONAL_SPECIFICATION"}],
        "identity_stable": {"identity": "Videoensayos narrativos", "purpose": ["Comprender historias"], "positioning": "Reflexión narrativa", "primary_promise": "Comprender cómo vivimos", "differentiator": ["Interpretación propia"], "editorial_pillars": ["Individuo e identidad"], "territories": [{"name": "Cultura", "classification": "ACTIVE"}], "permanent_limits": ["No inventar"], "authorial_persona": {"acts_as": "Observador con criterio", "does_not_act_as": ["Terapeuta"], "voice_traits": ["Claridad"]}, "first_person_rule": "FIRST_PERSON_ALLOWED_WHEN_TRUE_AND_EDITORIALLY_RELEVANT"},
        "audience_hypotheses": [{"classification": "AUDIENCE_HYPOTHESIS_INITIAL", "statement": "Personas aproximadamente entre 25 y 45 años", "status": "HYPOTHESIS"}],
        "voice_profile": {"corpus_status": "INCOMPLETE_MISSING_REQUIRED_SAMPLE", "approved_sample_ids": [], "initial_authorized_patterns": ["Observación concreta"], "anti_imitation_rules": ["No copiar referentes"], "approved_positive_examples": ["Ejemplo editorial compatible derivado de la especificación."], "approved_negative_examples": ["Ejemplo editorial incompatible derivado de la especificación."]},
        "supported_delivery_formats": ["VIDEO_ESSAY", "NARRATIVE_PODCAST", "AUDIO_CONTENT"],
        "external_policy_references": [],
        "pending_decisions": ["Incorporar muestra real principal autorizada"]
    },
    "editorial_profile_approval": {"profile_id": "MADG-EDITORIAL-PROFILE", "profile_version": "1.0.0", "profile_checksum": "a" * 64, "decision": "APPROVE", "approval_status": "APPROVE", "reviewer_role": "CHANNEL_INTELLIGENCE", "approval_timestamp": "2026-07-22T20:00:00Z", "review_scope": ["identidad", "voz", "límites"], "functional_owner_role": "CHANNEL_INTELLIGENCE", "voice_evidence_level": "SPECIFICATION_BASED", "evidence_summary": "Aprobación final de fixture sintético.", "limitations": ["Fixture de validación."], "approved_by": "channel_intelligence_owner", "approved_at": "2026-07-22T20:00:00Z"},
    "active_editorial_profile": {"ACTIVE_PROFILE_ID": "MADG-EDITORIAL-PROFILE", "ACTIVE_PROFILE_VERSION": "1.0.0", "profile_checksum": "a" * 64, "functional_approval": {"decision": "APPROVE", "profile_checksum": "a" * 64}, "technical_validation": {"gate_id": "B3_TECHNICAL_PROFILE_VALIDATION", "status": "PASS", "profile_checksum": "a" * 64}, "activation": {"activated_by": "technical_auditor_user", "activated_at": "2026-07-22T20:00:00Z"}, "status": "ACTIVE"},
    "voice_sample": {"sample_id": "SAMPLE-001", "locator": "fixtures/sample.md", "checksum": "a" * 64, "authorship": "OWNER", "text_type": "PERSONAL_TEXT", "classification": "AUTHENTIC", "usage_authorization": "AUTHORIZED", "representativeness": "HIGH", "recorded_at": "2026-07-22T20:00:00Z", "lineage": ["OWNER_PROVIDED"], "inclusion_reason": "Muestra autorizada"},
    "editorial_script_approval": {
        "artifact_id": "SCRIPT-001",
        "script_version": "1.0.0",
        "checksum": "a" * 64,
        "decision": "APPROVED",
        "approved_by": "editor_jefe_01",
        "approved_role": "EDITORIAL_LEAD",
        "approved_at": "2026-07-21T22:00:00Z"
    },
    "episode_brief": {
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "profile_id": "mas_alla_del_guion",
        "profile_version": "1.1.0",
        "profile_checksum": "a" * 64,
        "tema": "El miedo al fracaso",
        "pregunta_central": "¿Por qué tememos fracasar?",
        "conflicto_o_tension": "El deseo de avanzar choca con el miedo a equivocarse.",
        "initial_editorial_hypothesis": {"statement": "El miedo al fracaso crece cuando confundimos error con identidad.", "status": "HYPOTHESIS_UNAPPROVED", "research_role": "ORIENTS_RESEARCH_NOT_APPROVED_THESIS", "revisable": True, "adversarial_research_required": True},
        "objetivo": "Comprender el coste de evitar el error.",
        "transformacion_esperada": "Pasar de juzgar el fracaso a interpretarlo como información.",
        "audiencia_concreta": "Adultos que posponen decisiones por miedo a equivocarse.",
        "audience_status": "INITIAL_HYPOTHESIS",
        "angulo_diferencial": "Contrastar obras que muestran respuestas distintas al error.",
        "alcance": "Consecuencias humanas y narrativas del miedo al fracaso.",
        "fuera_de_alcance": "Diagnóstico clínico y promesas terapéuticas.",
        "spoilers": "SI_LIMITADOS",
        "tono": "Cercano, reflexivo y riguroso.",
        "duracion_objetivo": "18 minutos",
        "ritmo_locucion": "130 palabras por minuto",
        "nivel_investigacion": "PROFUNDO",
        "fuentes_requeridas": ["obra principal", "fuentes conceptuales"],
        "narrative_materials": ["Obra sintética de prueba"],
        "tipo_de_guion_principal": "VIDEOENSAYO_NARRATIVO",
        "tipo_de_guion_secundario": None,
        "estructura_candidata": "creencia-evidencia-reinterpretación",
        "structure_status": "INITIAL_HYPOTHESIS_REVISABLE_AFTER_RESEARCH",
        "razon_eleccion_estructura": "Permite transformar gradualmente la lectura inicial.",
        "citation_style": "Atribución narrativa con registro interno.",
        "attribution_policy": "Atribuir hechos e ideas específicas.",
        "quotation_policy": "Citas breves y verificadas.",
        "source_visibility": "PUBLIC_SUMMARY",
        "salida_esperada": "Diseño editorial listo para B5-I2.",
        "created_at": "2026-07-23T20:00:00Z"
    },
    "fact_check_report": {
        "input_version": "1.0.0",
        "output_version": "1.0.0",
        "verified_claims": ["CLAIM-001"],
        "status": "PASS"
    },
    "final_delivery_manifest": {
        "final_script_clean": "06_guion_longform.md",
        "final_script_annotated": "06_guion_longform_anotado.md",
        "claims_ledger": "claims_ledger.json",
        "final_candidate_version": "1.0.0",
        "human_approved_version": "1.0.0",
        "checksums": {"06_guion_longform.md": "a" * 64},
        "approval_record": {}
    },
    "final_editorial_audit": {
        "profile_compliance": "PASS",
        "brief_compliance": "PASS",
        "packaging_promise_compliance": "PASS",
        "evidence_sufficiency": "PASS",
        "thesis_quality": "PASS",
        "decision": "PASS",
        "correction_route": "NONE"
    },
    "gate_result": {
        "gate_id": "GATE-001",
        "artifact_id": "ART-001",
        "artifact_version": "1.0.0",
        "status": "PASS",
        "summary": "Verificacion de gate exitosa",
        "violations": [],
        "warnings": [],
        "evidence": {},
        "checked_at": "2026-07-21T22:00:00Z",
        "checker_version": "1.0.0",
        "exit_code": 0
    },
    "human_production_approval": {
        "publication_package_id": "PUB-PKG-001",
        "publication_package_version": "1.0.0",
        "script_version": "1.0.0",
        "packaging_version": "1.0.0",
        "checksum": "a" * 64,
        "decision": "APPROVED_FOR_PRODUCTION",
        "approved_by": "lead_produccion_01",
        "approved_role": "PRODUCTION_LEAD",
        "approved_at": "2026-07-21T22:00:00Z"
    },
    "human_publication_approval": {
        "final_candidate_id": "FC-001",
        "audiovisual_version": "1.0.0",
        "thumbnail_version": "1.0.0",
        "title_version": "1.0.0",
        "checksum": "a" * 64,
        "decision": "APPROVED_FOR_PUBLICATION",
        "approved_by": "lead_publicacion_01",
        "approved_role": "PUBLICATION_LEAD",
        "approved_at": "2026-07-21T22:00:00Z",
        "has_final_audiovisual_assets": True
    },
    "narrative_plan": {
        "script_plan_id": "PLAN-001",
        "episode_id": "EP-001",
        "script_type": "LONGFORM",
        "thesis_provisional": "El exito requiere paciencia.",
        "blocks": [{}, {}],
        "word_budget_total": 2000
    },
    "packaging_hypothesis": {
        "episode_audience": "General",
        "promesa_de_clic": "La verdad detras del guion",
        "titulo_de_trabajo": "Detras del guion",
        "concepto_de_miniatura": "Imagen del director",
        "functional_owner_role": "EDITORIAL_LEAD",
        "authorized_approval_status": "APPROVED",
        "version": "1.0.0",
        "checksum": "a" * 64
    },
    "performance_snapshot": {
        "published_version": "1.0.0",
        "observation_window": "24H",
        "status": "PUBLISHED"
    },
    "publication_package": {
        "package_id": "PKG-001",
        "package_version": "1.0.0",
        "script_version": "1.0.0",
        "approved_title": "Detras del guion",
        "approved_thumbnail_or_brief": "miniatura_v1.png",
        "description": "Descripcion del episodio.",
        "status": "PUBLISHED"
    },
    "published_version_manifest": {
        "video_id": "YT-VIDEO-001",
        "publication_date": "2026-07-21T22:00:00Z",
        "script_version": "1.0.0",
        "audiovisual_version": "1.0.0",
        "publication_package_version": "1.0.0",
        "change_history": [],
        "status": "PUBLISHED"
    },
    "research_pack": {
        "research_id": "RP-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "scope": "Cobertura conceptual y narrativa.",
        "facts": [{"item_id": "I1", "statement": "Hecho verificado.", "source_refs": ["S1"], "locator": "p. 10", "confidence": "HIGH"}],
        "interpretations": [{"item_id": "I2", "statement": "Lectura interpretativa.", "source_refs": ["S1"], "locator": "escena 2", "confidence": "MEDIUM"}],
        "hypotheses": [],
        "contradictions": [],
        "alternative_views": [],
        "coverage": [{"dimension_id": d, "status": "COVERED", "related_finding_ids": ["I1"], "related_source_ids": ["S1"], "limitation_or_pending": None, "scope_decision": "NONE", "editorial_impact": "NOT_APPLICABLE", "propagated_constraint": None, "mitigation_status": "NOT_REQUIRED"} for d in ["CENTRAL_QUESTION", "CONFLICT", "INITIAL_HYPOTHESIS", "HUMAN_SOCIAL_HISTORICAL_OR_CULTURAL_PHENOMENON", "PRIMARY_NARRATIVE_MATERIAL", "CRITICAL_CLAIMS", "ALTERNATIVE_PERSPECTIVES"]],
        "critical_claims_assessment": {"status": "NONE_JUSTIFIED", "claim_ids": [], "justification": "Fixture sin claim central.", "editorial_impact": "LIMITED"},
        "narrative_evidence": [{"item_id": "N1", "statement": "Escena.", "source_refs": ["S1"], "locator": "00:10", "confidence": "HIGH", "evidence_kind": "SCENE"}],
        "external_reality_evidence": [{"item_id": "E1", "statement": "Estudio.", "source_refs": ["S1"], "locator": "p. 11", "confidence": "HIGH", "evidence_kind": "STUDY"}],
        "source_registry": [{"source_id": "S1", "title": "Fuente oficial", "source_type": "PRIMARY", "url": "https://example.com/source", "access_type": "DIRECT", "locator": "documento completo", "confidence": "HIGH"}],
        "claims_candidates": [{"item_id": "CLAIM-X", "statement": "Claim candidata del fenómeno.", "source_refs": ["S1"], "locator": "escena 3", "confidence": "MEDIUM"}],
        "unsupported_claims": [],
        "narrative_opportunities": [],
        "limitations": [],
        "research_pack_kind": "PHENOMENON",
        "phenomenon": {"phenomenon_id": "PHEN-001", "phenomenon_kind": "CULTURAL", "definition": "Fenómeno de fixture."},
        "editorial_uses": {"intended_uses": ["CENTRAL_CLAIM_SUPPORT", "CONTEXTUAL_BACKGROUND"], "criticality_map": {"claims": [{"claim_id": "CLAIM-X", "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT"}]}},
        "rival_analysis": [{"rival_explanation_id": "RIVAL-1", "statement": "Explicación rival.", "agreement_status": "DISAGREEMENT", "disagreement_kind": "RIVAL_OPEN", "claim_ids": ["CLAIM-X"], "source_refs": ["S1"]}],
        "semantic_status": {"status_per_claim": [{"claim_id": "CLAIM-X", "semantic_level": "PLAUSIBLE", "intended_use": "CENTRAL_CLAIM_SUPPORT", "sufficiency_for_intended_use": "NOT_FUNCTIONALLY_VALIDATED"}], "ir4_dependency": "DEFERRED_TO_R1_M6"},
        "created_at": "2026-07-21T22:00:00Z"
    },
    "script_block_contract": {
        "block_id": "BLOCK-001",
        "plan_version": "1.0.0",
        "required_sources": ["SRC-01"],
        "word_budget_min": 100,
        "word_budget_max": 200,
        "narrative_function": "Introduccion y gancho",
        "output_path": "output/bloques/block_01.md"
    },
    "script_version_manifest": {
        "script_id": "SCRIPT-001",
        "version": "1.0.0",
        "checksum": "a" * 64,
        "narrative_plan_version": "1.0.0",
        "status": "DRAFT"
    },
    "source_access_and_evidence_report": {
        "report_id": "ER-001",
        "episode_id": "EP-001",
        "research_id": "RP-001",
        "brief_version": "1.0.0",
        "material_principal_disponible": True,
        "tipo_de_acceso": "DIRECT",
        "fuentes_primarias": [{"source_id": "S1", "title": "Fuente oficial", "url": "https://example.com/source", "access_type": "DIRECT", "locator": "documento completo", "confidence": "HIGH"}],
        "fuentes_secundarias": [],
        "escenas_verificadas": [{"scene_id": "SC1", "description": "Escena verificada.", "source_id": "S1", "locator": "00:10:00", "verification_mode": "DIRECT"}],
        "escenas_descritas_indirectamente": [],
        "claims_sostenibles": [{"claim_id": "CLAIM-001", "claim_text": "Claim sostenible.", "source_refs": ["S1"], "locator": "p. 15", "confidence": "HIGH"}],
        "claims_pendientes": [],
        "limitaciones": [],
        "nivel_de_confianza": "HIGH",
        "can_proceed": True,
        "required_disclosures": [],
        "independence_groups": [{"group_id": "GRP-1", "source_ids": ["S1"], "independence": "INDEPENDENT", "rationale": "Fuente primaria."}],
        "coverage_gaps": [{"dimension": "CONTEXTO", "reason": "Solo una fuente.", "impact": "NON_CRITICAL", "mitigation": "Complementar."}],
        "reopening_conditions": [{"condition_id": "REO-1", "trigger_type": "NEW_EVIDENCE", "description": "Nueva evidencia."}],
        "claim_dependent_source_evaluations": [{"claim_id": "CLAIM-001", "source_id": "S1", "object_relation": "Directa", "claim_authority": "Alta", "access_level": "DIRECT", "independence": "INDEPENDENT", "currency": "Vigente", "locator": "p.15", "assessment": "SUPPORTED"}],
        "allowed_analyses": ["CONTEXTUAL_ANALYSIS"], "limited_analyses": [], "prohibited_analyses": [], "excluded_claims": [], "propagated_constraints": [], "critical_claim_assessments": [], "critical_claims_propagation": {"status": "NONE_JUSTIFIED", "claim_ids": [], "justification": "Fixture sin claims críticos.", "editorial_impact": "LIMITED", "scope_decision": "REDUCED_SCOPE"},
        "sufficiency_basis": {"central_question": "Pregunta", "critical_claims": [], "analysis_type": "CONTEXTUAL_ANALYSIS", "material_roles": ["PRIMARY_NARRATIVE_MATERIAL"], "requested_depth": "PROFUNDO", "research_coverage": "Cobertura revisada"},
        "created_at": "2026-07-23T20:00:00Z"
    },
    "thesis_artifact": {
        "thesis_id": "THESIS-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "research_id": "RP-001",
        "evidence_report_id": "ER-001",
        "stage": "THESIS_PROVISIONAL",
        "statement": "La tesis provisional del ensayo.",
        "premises": [{"premise_id": "P1", "statement": "Premisa.", "finding_ids": ["I1"], "source_refs": ["S1"]}], "supporting_findings": ["I1"], "tensioning_evidence": [{"finding_id": "I2", "explanation": "Matiza."}], "alternative_explanations": ["Otro factor."], "assumptions": ["Supuesto."], "revision_conditions": ["Nueva evidencia."], "inherited_constraints": [],
        "open_questions": ["¿Qué evidencia adicional puede cambiar la tesis?"],
        "version": "1.0.0",
        "created_at": "2026-07-23T20:00:00Z"
    },
    "semantic_sufficiency_audit": {
        "audit_id": "SSA-001", "episode_id": "EP-001", "brief_checksum": "a" * 64,
        "research_checksum": "a" * 64, "evidence_report_checksum": "a" * 64, "thesis_checksum": "a" * 64,
        "audited_by": "script_product_ai_reviewer", "audit_method": "AI_SEMANTIC_REVIEW",
        "findings": [{"criterion": criterion, "assessment": "SATISFIED", "rationale": "La auditoría evalúa el criterio.", "references": ["thesis.statement"]} for criterion in ["CENTRAL_QUESTION_SPECIFICITY", "RESEARCH_RELEVANCE", "DEPTH_FIT", "RIVAL_PERSPECTIVE_SUBSTANCE", "NARRATIVE_UTILITY", "CRITICAL_CLAIMS_QUALITY", "THESIS_SUBSTANCE", "READINESS_FOR_B5_I2"]],
        "decision": "PASS", "created_at": "2026-07-24T20:00:00Z"
    },
    "narrative_human_analysis": {"analysis_id":"A-1","episode_id":"EP-1","research_id":"R-1","evidence_report_id":"E-1","semantic_audit_id":"S-1","material_id":"M-1","material_checksum":"a"*64,"inherited_constraint_ids":[],"findings":[{"finding_id":"F-1","claim_type":"INTERPRETATION","statement":"Lectura.","narrative_evidence_refs":["NE-1"],"source_refs":["S-1"],"human_dimension":"BELIEF","causal_relation":"Relación.","confidence":"HIGH"}],"rival_interpretations":["Rival."],"rival_interpretation_status":"PRESENT","rival_interpretation_justification":None,"limitations":["Límite."],"limits_status":"PRESENT","limits_justification":None,"demonstrates":"Demuestra una relación.","does_not_establish":"No demuestra causalidad universal.","created_at":"2026-07-24T20:00:00Z"},
    "material_curation": {"curation_id":"C-1","episode_id":"EP-1","research_id":"R-1","analysis_ids":["A-1"],"candidates":[{"material_id":"M-1","function":"Complicación","thesis_contribution":"Aporta.","new_perspective":"Nueva.","redundancy_with_selected":[],"context_cost":"Bajo.","narrative_evidence_strength":"HIGH","contradiction_or_nuance":"Matiz.","narrative_use":"COMPLICATION","selection_status":"SELECTED"}],"selected_material_ids":["M-1"],"selection_stage":"FINAL","exclusions":[],"sequence_rationale":"Secuencia justificada.","set_relationship":"Relación del conjunto.","unique_contributions":[{"material_id":"M-1","contribution":"Aporta."}],"function_overlap_justification":"No hay solapamiento.","progression_evidence":[{"material_id":"M-1","change_in_understanding":"Cambio.","evidence_refs":["F-1"],"non_substitutability":"No sustituible."}],"inherited_restrictions":[],"created_at":"2026-07-24T20:00:00Z"},
    "refined_thesis": {"thesis_id":"T-1","episode_id":"EP-1","brief_version":"1.0.0","research_id":"R-1","evidence_report_id":"E-1","semantic_audit_id":"S-1","provisional_thesis_id":"TP-1","analysis_ids":["A-1"],"curation_id":"C-1","statement":"Tesis.","supporting_evidence_refs":["F-1"],"counterevidence_refs":["R-1"],"rival_interpretations":["Rival."],"main_objection":"Objeción.","nuance":"Matiz.","material_contributions":[{"material_id":"M-1","contribution":"Aporta."}],"analysis_confirmed":["Confirmación."],"changes_from_provisional":["Cambio."],"discarded_from_provisional":["Descartado."],"refinement_rationale":"Razón.","refinement_dimensions":[{"dimension":"SCOPE","provisional_position":"Antes.","resulting_position":"Después.","evidence_refs":["F-1"],"rationale":"Razón."}],"inherited_constraint_ids":[],"statement_unchanged_justification":None,"limits":["Límite."],"revision_conditions":["Nueva evidencia."],"stage":"THESIS_REFINED","created_at":"2026-07-24T20:00:00Z"},
    "early_packaging_hypothesis": {"packaging_id":"P-1","episode_id":"EP-1","refined_thesis_id":"T-1","refined_thesis_checksum":"a"*64,"audience":{"persona_concreta":"Persona.","conocimiento_previo":"Conocimiento.","tension_reconocida":"Tensión.","relevancia":"Relevancia.","expectativa_que_no_debe_generarse":"No promesa.","profile_id":"P-1","profile_version":"1.0.0","profile_checksum":"a"*64,"brief_checksum":"a"*64},"promesa_visible_provisional":"Promesa.","tension_central":"Tensión.","expectativa_del_espectador":"Expectativa.","diferenciador":"Diferenciador.","titulo_de_trabajo":"Título.","concepto_inicial_miniatura":"Concepto.","titulo_miniatura_complementarity":"Complemento.","overpromise_risk":"LOW","platform_constraints":[{"constraint":"Restricción.","reason":"Motivo.","impact":"Impacto."}],"honesty_assessment":{"thesis_relation":"Relación.","thesis_refs":["T-1"],"evidence_refs":["F-1"],"inherited_constraint_ids":[],"unsupported_elements":[],"risk_level":"LOW","risk_justification":"Justificación.","mitigation_or_pending":None},"status":"PROVISIONAL_YOUTUBE_ADAPTATION_INPUT","created_at":"2026-07-24T20:00:00Z"},
    "editorial_script_promise": {"promise_id":"SP-1","episode_id":"EP-1","refined_thesis_id":"T-1","refined_thesis_checksum":"a"*64,"audience":"Persona.","editorial_promise":"Promesa.","central_tension":"Tensión.","legitimate_expectations":["Comprensión."],"expectations_to_avoid":["No promesa."],"thesis_alignment":"Alineada.","textual_overpromise_risk":{"level":"LOW","justification":"Justificación.","mitigation_or_pending":None},"opening_obligations":["Abrir con tensión."],"inherited_constraint_ids":[],"status":"SCRIPT_CORE_INPUT","created_at":"2026-07-24T20:00:00Z"},
    "b5_i2_semantic_sufficiency_audit": {"audit_id":"B5I2-SSA-1","episode_id":"EP-1","auditor_role":"INDEPENDENT_EDITORIAL_AUDITOR","auditor_run_id":"RUN-AUDIT-1","auditor_skill_id":"skill_auditar_suficiencia_semantica_b5_i2","auditor_skill_version":"1.0.0","provider_or_adapter":"local-mock-semantic","model_or_evaluator":"semantic-mock-v1","execution_timestamp":"2026-07-25T08:00:00Z","input_manifest_checksum":"a"*64,"artifact_checksums":[{"artifact_kind":kind,"artifact_id":artifact_id,"checksum":"a"*64,"producer_run_id":"RUN-P"} for kind, artifact_id in [("research","R-1"),("evidence_report","E-1"),("provisional_thesis","TP-1"),("analysis","A-1"),("curation","C-1"),("refined_thesis","T-1"),("script_promise","SP-1")]],"audit_method":"AI_SEMANTIC_REVIEW","audited_artifact_ids":["analysis:A-1","curation:C-1","refined_thesis:T-1","script_promise:SP-1"],"audited_artifact_versions":[{"artifact_kind":"analysis","artifact_id":"A-1","checksum":"a"*64,"producer_run_id":"RUN-P"},{"artifact_kind":"curation","artifact_id":"C-1","checksum":"a"*64,"producer_run_id":"RUN-P"},{"artifact_kind":"refined_thesis","artifact_id":"T-1","checksum":"a"*64,"producer_run_id":"RUN-P"},{"artifact_kind":"script_promise","artifact_id":"SP-1","checksum":"a"*64,"producer_run_id":"RUN-P"}],"criteria_results":[{"criterion":criterion,"status":"SATISFIED","summary":"Evaluado."} for criterion in ["ANALYSIS_SPECIFICITY","EVIDENCE_TRACEABILITY","EPISTEMIC_SEPARATION","EDITORIAL_DEPTH_AND_UTILITY","MATERIAL_COVERAGE","CURATION_FUNCTION","CURATION_CONTRAST_AND_PROGRESSION","REDUNDANCY_AND_CONTEXT_COST","THESIS_REFINEMENT_SUBSTANCE","THESIS_ARGUMENTATIVE_QUALITY","MATERIAL_THESIS_CONTRIBUTION","INHERITED_RESTRICTIONS","SCRIPT_PROMISE_HONESTY","EARLY_PACKAGING_HONESTY","B5_I3_READINESS"]],"findings":[{"criterion":criterion,"status":"SATISFIED","anchored_findings":[{"artifact_kind":"analysis","artifact_id":"A-1","artifact_field":"statement","evaluated_excerpt":"Lectura.","evidence_refs":["F-1"],"evidence_excerpts":[{"evidence_ref":"F-1","excerpt":"Lectura."}],"editorial_comparison":"Comparación editorial trazable.","why_specific_or_generic":"Justificación editorial concreta.","decision":"SATISFIED"}],"rationale":"Evaluado."} for criterion in ["ANALYSIS_SPECIFICITY","EVIDENCE_TRACEABILITY","EPISTEMIC_SEPARATION","EDITORIAL_DEPTH_AND_UTILITY","MATERIAL_COVERAGE","CURATION_FUNCTION","CURATION_CONTRAST_AND_PROGRESSION","REDUNDANCY_AND_CONTEXT_COST","THESIS_REFINEMENT_SUBSTANCE","THESIS_ARGUMENTATIVE_QUALITY","MATERIAL_THESIS_CONTRIBUTION","INHERITED_RESTRICTIONS","SCRIPT_PROMISE_HONESTY","EARLY_PACKAGING_HONESTY","B5_I3_READINESS"]],"blocking_defects":[],"non_blocking_defects":[],"cited_evidence":["F-1"],"required_corrections":[],"unresolved_questions":[],"inherited_restrictions_checked":[],"auditor_statement":"Decision PASS emitida sobre artefactos B5-I2 con evidencia citada.","decision":"PASS","readiness":"BLOCKED","created_at":"2026-07-25T08:00:00Z"},
    "viewer_journey": {
        "estado_inicial_del_espectador": "Curioso y expectante",
        "creencia_inicial_probable": "Cree que es simple",
        "pregunta_que_lo_mantiene": "¿Cual es el giro narrativo?",
        "estado_final_del_espectador": "Sorprendido e iluminado"
    }
}

# B4-I1: los registros canónicos sirven como fixtures válidos de sus schemas.
for _name in ("responsibility_registry", "skill_catalog", "subagent_registry", "editorial_profile_registry"):
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "config", f"{_name}.json"), encoding="utf-8") as _fixture:
        VALID_FIXTURES[_name] = json.load(_fixture)


# CI: fixtures for capability and topic belonging schemas.
with open(os.path.join(os.path.dirname(__file__), "..", "..", "config", "capability_registry.json"), encoding="utf-8") as _fixture:
    VALID_FIXTURES["capability_registry"] = json.load(_fixture)
VALID_FIXTURES["capability_audit_universe"] = {
    "schema_version": "1.0.0", "plan_id": "PLAN_004", "mission_id": "TH-04",
    "repository_revision": "a" * 40, "generated_at": "2026-08-10T00:00:00Z",
    "source_inputs": [{"path": "config/capability_registry.json", "sha256": "a" * 64}],
    "evidence_refs": ["config/capability_registry.json"], "limitations": [], "result": "PASS",
    "artifact_type": "CAPABILITY_AUDIT_UNIVERSE", "discovery_scope_ref": "TH04_capability_discovery_scope.json",
    "candidates": [{
        "candidate_id": "CAP", "canonical_identity": "CAP", "aliases": ["CAP"],
        "source_type": "CAPABILITY_REGISTRY", "source_refs": ["config/capability_registry.json"],
        "current_registry_presence": True, "object_class": "EXECUTABLE_CAPABILITY", "disposition": "CURRENT",
        "registry_state": "REGISTERED", "classification_reason": "fixture", "owner_observation": {
            "status": "RESOLVED_FROM_CANONICAL_FIELD", "functional_authority_domain": "CHANNEL_INTELLIGENCE",
            "decision_authority": "REVIEWER"}, "maturity_observed": "IMPLEMENTED",
        "observed_refs": {"roles": [], "prompts": [], "profiles": [], "routes": [], "contracts": [], "implementation": []},
        "resolved_artifacts": [], "inconsistencies": [], "evidence_refs": ["config/capability_registry.json"],
    }], "unresolved_candidates": [],
}
_VALID_PROFILE_CHECKSUM = "a" * 64
_VALID_PROVENANCE = {"actor_id": "producer-1", "run_id": "run-producer", "role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "input_checksums": ["a" * 64], "output_checksum": "a" * 64}
VALID_FIXTURES["topic_belonging_assessment"] = {
    "assessment_id": "TBA-001", "producer_actor_id": "producer-1", "producer_run_id": "run-producer",
    "producer_role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "profile_id": "mas_alla_del_guion", "profile_version": "1.2.1",
    "profile_checksum": _VALID_PROFILE_CHECKSUM, "topic": "Tema de fixture", "entry_mode": "ANCHOR_WORK_FIRST", "narrative_work": "Obra de fixture",
    "central_question": "Pregunta de fixture", "proposed_angle": "Ángulo de fixture", "proposed_territory": "Individuo e identidad",
    "initial_evidence": ["evidence-1"], "sensitive_risks": [], "territory_classification": "ACTIVE",
    "identity_alignment": "ALIGNED", "promise_alignment": "ALIGNED", "risks": [], "recommended_conditions": [],
    "recommended_exclusions": [], "owner_escalation_recommended": False, "evidence": ["evidence-1"],
    "status": "CLOSED_FOR_REVIEW", "artifact_checksum": _VALID_PROFILE_CHECKSUM, "provenance": _VALID_PROVENANCE
}
VALID_FIXTURES["topic_belonging_decision"] = {
    "decision_id": "TBD-001", "assessment_id": "TBA-001", "profile_id": "mas_alla_del_guion", "profile_version": "1.2.1",
    "profile_checksum": _VALID_PROFILE_CHECKSUM, "producer_artifact_checksum": _VALID_PROFILE_CHECKSUM,
    "reviewer_actor_id": "reviewer-1", "reviewer_run_id": "run-reviewer", "reviewer_role_id": "CHANNEL_INTELLIGENCE_REVIEWER",
    "reviewer_input_checksum": _VALID_PROFILE_CHECKSUM, "decision": "APPROVE", "conditions": [], "exclusions": [], "risks": [],
    "owner_escalation_required": False, "owner_escalation_reason": "", "strategic_dimensions_affected": [],
    "temporary_or_permanent_effect": "NONE", "precedent_risk": "LOW", "evidence": ["evidence-1"],
    "decided_at": "2026-07-30T10:00:00Z",
    "provenance": {"actor_id": "reviewer-1", "run_id": "run-reviewer", "role_id": "CHANNEL_INTELLIGENCE_REVIEWER",
                   "input_checksum": _VALID_PROFILE_CHECKSUM, "output_checksum": _VALID_PROFILE_CHECKSUM}
}

_TOPIC_TRIGGERS = {key: False for key in [
    "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change",
    "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change",
    "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory",
]}
VALID_FIXTURES["topic_belonging_input"] = {
    "topic_input_id": "TBI-FIXTURE", "profile_id": "mas_alla_del_guion", "profile_version": "1.2.1",
    "profile_checksum": "a" * 64, "topic": "Tema", "entry_mode": "ANCHOR_WORK_FIRST", "narrative_work": "Obra",
    "central_question": "Pregunta", "proposed_angle": "?ngulo", "proposed_territory": "Territorio",
    "initial_evidence": ["source-1"], "strategic_triggers": _TOPIC_TRIGGERS,
    "submitted_at": "2026-07-31T10:00:00Z",
}
VALID_FIXTURES["topic_belonging_assessment"].update({
    "topic_input_id": "TBI-FIXTURE", "entry_mode": "ANCHOR_WORK_FIRST", "strategic_triggers": _TOPIC_TRIGGERS,
})
VALID_FIXTURES["topic_belonging_owner_decision"] = {
    "owner_decision_id": "TBO-FIXTURE", "topic_input_id": "TBI-FIXTURE", "assessment_id": "TBA-FIXTURE",
    "review_decision_id": "TBD-FIXTURE", "profile_id": "mas_alla_del_guion", "profile_version": "1.2.1",
    "profile_checksum": "a" * 64, "assessment_checksum": "a" * 64, "review_decision_checksum": "a" * 64,
    "owner_actor_id": "owner", "decision": "OWNER_APPROVE", "conditions": [], "limitations": [],
    "decided_at": "2026-07-31T10:00:00Z", "owner_decision_checksum": "a" * 64,
    "provenance": {"actor_id": "owner", "output_checksum": "a" * 64},
}


VALID_FIXTURES["youtube_adaptation_b5_i2_package"] = {
    "package_id": "YT-PKG-1",
    "episode_id": "EP-1",
    "active_profile_reference": {"profile_id": "mas_alla_del_guion", "profile_version": "1.2.1", "profile_checksum": "a" * 64},
    "input_references": {
        "episode_brief": {"artifact_id": "EP-1", "version": "1.0.0", "checksum": "a" * 64},
        "refined_thesis": {"artifact_id": "T-1", "version": "1.0.0", "checksum": "a" * 64},
        "editorial_script_promise": {"artifact_id": "SP-1", "version": "1.0.0", "checksum": "a" * 64},
        "evidence_or_claims_reference": {"artifact_id": "E-1", "version": "1.0.0", "checksum": "a" * 64},
    },
    "producer_run_id": "RUN-PROD-1",
    "episode_youtube_positioning": {
        "concrete_audience": {
            "audience_segment": "Personas que ya conocen la obra pero no han articulado esta tensión narrativa.",
            "prior_knowledge": "Conocimiento general de la obra.",
            "recognized_tension": "Tensión emocional concreta.",
            "relevance": "La lectura promete utilidad situada.",
            "expected_language_level": "Medio.",
            "likely_misinterpretation": "Confundir interpretación con hecho absoluto.",
            "expectation_not_to_create": "No prometer certeza total."
        },
        "visible_promise": {
            "promise_statement": "Promesa visible concreta.",
            "viewer_gain": "Comprender una tensión narrativa.",
            "scope": "Solo la lectura del episodio.",
            "limits": ["No autoriza publicación."],
            "supporting_claims": ["C1"],
            "unsupported_elements": [],
            "differentiation": "No es intercambiable entre episodios."
        }
    },
    "early_packaging_hypothesis": VALID_FIXTURES["early_packaging_hypothesis"],
    "youtube_design_constraints": {
        "opening_readiness": {
            "click_confirmation": "Confirmar promesa.",
            "early_substance": "Aportar sustancia temprano.",
            "minimum_context": "Contexto mínimo suficiente.",
            "central_tension": "Tensión central clara.",
            "viewer_relevance": "Relevancia explícita.",
            "route_preview": "Ruta anticipada.",
            "transition_obligation": "Transición obligatoria.",
            "expectations_to_avoid": ["No prometer cierre total."],
            "invalidated_by": ["Apertura final redactada."]
        },
        "duration_assessment": {
            "recommended_range": "14-18 minutos",
            "assumptions": ["Densidad media."],
            "complexity_factors": ["Contradicción narrativa."],
            "density_factors": ["Varias relaciones conceptuales."],
            "audience_factors": ["Audiencia interesada no experta."],
            "compression_risk": "Perder matices.",
            "padding_risk": "Repetición.",
            "mitigation_or_pending": "Ajustar tras outline."
        }
    },
    "preliminary_youtube_risk_review": {
        "platform_risk": {
            "signals_detected": ["Tema sensible contextualizado."],
            "surface": {"narration": "Narración analítica.", "working_title": "Título temprano.", "thumbnail_concept": "Miniatura prudente."},
            "context": "Lectura cultural situada.",
            "treatment": "Analítico.",
            "advertising_risk": "LOW",
            "community_guidelines_risk": "LOW",
            "severity": "LOW",
            "mitigations": ["Contextualizar."],
            "uncertainties": ["Pendiente revisión audiovisual."],
            "audiovisual_review_pending": True
        },
        "rights_reuse_risk": {
            "quotes": "Breves.",
            "paraphrases": "Orientadas a análisis.",
            "dialogue_reproduction": "No estructural.",
            "scene_dependency": "Parcial.",
            "chronological_summary_dependency": "No sustitutiva.",
            "transformative_function": "Interpretativa.",
            "commentary_and_analysis": "Predominante.",
            "summary_substitution_risk": "LOW",
            "textual_risk": "LOW",
            "audiovisual_review_pending": True,
            "unresolved_items": [],
            "mitigations": ["Citas breves."]
        }
    },
    "unsupported_elements": [],
    "unresolved_items": [],
    "producer_limits": ["No autoriza B5-I3."],
    "created_at": "2026-08-01T10:00:00Z"
}

VALID_FIXTURES["youtube_adaptation_review"] = {
    "review_id": "YT-REV-1",
    "episode_id": "EP-1",
    "artifact_id": "YT-PKG-1",
    "artifact_checksum": "a" * 64,
    "producer_run_id": "RUN-PROD-1",
    "auditor_run_id": "RUN-AUD-1",
    "independence_check": {"producer_actor_id": "producer-1", "auditor_actor_id": "auditor-1", "producer_run_id": "RUN-PROD-1", "auditor_run_id": "RUN-AUD-1", "decision": "PASS"},
    "active_profile_reference": {"profile_id": "mas_alla_del_guion", "profile_version": "1.2.1", "profile_checksum": "a" * 64},
    "capability_results": {key: {"decision": "PASS", "rationale": "Evaluado.", "evidence_refs": ["E-1"], "mitigation_or_pending": "Mitigado.", "blocking_reason": None} for key in ["YT_EARLY_AUDIENCE_FIT", "YT_VISIBLE_PROMISE", "YT_EARLY_PACKAGING_HYPOTHESIS", "YT_PROMISE_CONTENT_ALIGNMENT", "YT_OPENING_READINESS", "YT_DURATION_ENVELOPE", "YT_OVERPROMISE_REVIEW", "YT_TEXT_PLATFORM_RISK", "YT_SCRIPT_RIGHTS_REUSE_RISK"]},
    "overpromise_decision": {"decision": "PASS", "rationale": "Evaluado.", "evidence_refs": ["E-1"], "mitigation_or_pending": "Mitigado.", "blocking_reason": None},
    "unsupported_elements": [],
    "platform_risk_summary": {"severity": "LOW", "summary": "Riesgo bajo.", "mitigations": ["Contextualizar."], "uncertainties": ["Pendiente revisión audiovisual."]},
    "rights_reuse_summary": {"severity": "LOW", "summary": "Uso transformativo preliminarmente aceptable.", "mitigations": ["Citas breves."], "unresolved_items": []},
    "opening_readiness": {"decision": "PASS", "rationale": "Son obligaciones, no apertura redactada.", "pending_items": []},
    "duration_assessment": {"decision": "PASS", "rationale": "Está justificada.", "recommended_range": "14-18 minutos"},
    "findings": ["Sin hallazgos bloqueantes."],
    "required_changes": [],
    "blocking_reasons": [],
    "unresolved_items": [],
    "publication_limit": {"DOES_NOT_AUTHORIZE": ["B5_I3", "FINAL_PACKAGING", "PRODUCTION", "PUBLICATION", "MONETIZATION_GUARANTEE", "LEGAL_APPROVAL"]},
    "decision": "APPROVAL",
    "created_at": "2026-08-01T10:05:00Z"
}

VALID_FIXTURES["youtube_adaptation_r3_traceability"] = {
    "registry_version": "1.0.0",
    "capabilities": [
        {"capability_id": "YT_EARLY_AUDIENCE_FIT", "producer_component": "episode_youtube_positioning.concrete_audience", "auditor_component": "capability_results.YT_EARLY_AUDIENCE_FIT", "input_contracts": ["episode_brief"], "output_contract": "youtube_adaptation_b5_i2_package", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["generic audience"], "evidence": ["package"], "invalidated_by": ["profile checksum change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_VISIBLE_PROMISE", "producer_component": "episode_youtube_positioning.visible_promise", "auditor_component": "capability_results.YT_VISIBLE_PROMISE", "input_contracts": ["refined_thesis"], "output_contract": "youtube_adaptation_b5_i2_package", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["unsupported promise"], "evidence": ["package"], "invalidated_by": ["thesis change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_EARLY_PACKAGING_HYPOTHESIS", "producer_component": "early_packaging_hypothesis", "auditor_component": "capability_results.YT_EARLY_PACKAGING_HYPOTHESIS", "input_contracts": ["early_packaging_hypothesis"], "output_contract": "youtube_adaptation_b5_i2_package", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["final packaging disguised"], "evidence": ["packaging hypothesis"], "invalidated_by": ["packaging checksum change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_PROMISE_CONTENT_ALIGNMENT", "producer_component": "visible promise + package", "auditor_component": "capability_results.YT_PROMISE_CONTENT_ALIGNMENT", "input_contracts": ["script promise"], "output_contract": "youtube_adaptation_review", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["promise mismatch"], "evidence": ["review"], "invalidated_by": ["promise change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_OPENING_READINESS", "producer_component": "youtube_design_constraints.opening_readiness", "auditor_component": "capability_results.YT_OPENING_READINESS", "input_contracts": ["episode_brief"], "output_contract": "youtube_adaptation_b5_i2_package", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["opening drafted"], "evidence": ["opening obligations"], "invalidated_by": ["brief change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_DURATION_ENVELOPE", "producer_component": "youtube_design_constraints.duration_assessment", "auditor_component": "capability_results.YT_DURATION_ENVELOPE", "input_contracts": ["episode_brief"], "output_contract": "youtube_adaptation_b5_i2_package", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["unjustified duration"], "evidence": ["duration assessment"], "invalidated_by": ["brief change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_OVERPROMISE_REVIEW", "producer_component": "early_packaging_hypothesis.overpromise_risk", "auditor_component": "capability_results.YT_OVERPROMISE_REVIEW", "input_contracts": ["packaging hypothesis"], "output_contract": "youtube_adaptation_review", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["blocking unresolved overpromise"], "evidence": ["review"], "invalidated_by": ["packaging change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_TEXT_PLATFORM_RISK", "producer_component": "preliminary_youtube_risk_review.platform_risk", "auditor_component": "capability_results.YT_TEXT_PLATFORM_RISK", "input_contracts": ["package"], "output_contract": "youtube_adaptation_review", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["high platform risk"], "evidence": ["risk summary"], "invalidated_by": ["surface change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_SCRIPT_RIGHTS_REUSE_RISK", "producer_component": "preliminary_youtube_risk_review.rights_reuse_risk", "auditor_component": "capability_results.YT_SCRIPT_RIGHTS_REUSE_RISK", "input_contracts": ["package"], "output_contract": "youtube_adaptation_review", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["summary substitution essential"], "evidence": ["rights summary"], "invalidated_by": ["script change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"},
        {"capability_id": "YT_B5_I2_FUNCTIONAL_DECISION", "producer_component": "youtube_adaptation_b5_i2_package", "auditor_component": "decision", "input_contracts": ["package", "review"], "output_contract": "youtube_adaptation_review", "decision_authority": "YOUTUBE_ADAPTATION_AUDITOR", "veto_conditions": ["independence not demonstrated"], "evidence": ["review decision"], "invalidated_by": ["review checksum change"], "real_execution_required": True, "availability_status": "IMPLEMENTED_NOT_DEMONSTRATED"}
    ]
}

VALID_FIXTURES["narrative_human_analysis"] = {"analysis_id":"A-1","episode_id":"EP-1","research_id":"R-1","evidence_report_id":"E-1","semantic_audit_id":"S-1","material_id":"M-1","material_checksum":"a"*64,"inherited_constraint_ids":[],"findings":[{"finding_id":"F-1","claim_type":"INTERPRETATION","statement":"Lectura.","narrative_evidence_refs":["NE-1"],"source_refs":["S-1"],"human_dimension":"BELIEF","causal_relation":"Relación.","confidence":"HIGH"}],"rival_interpretations":["Rival."],"rival_interpretation_status":"PRESENT","rival_interpretation_justification":None,"limitations":["Límite."],"limits_status":"PRESENT","limits_justification":None,"demonstrates":"Demuestra una relación.","does_not_establish":"No demuestra causalidad universal.","material_function_candidate":"Complicación.","specific_scene_or_passage":"Escena específica.","observable_decision_or_action":"Acción observable.","conflict":"Conflicto claro.","consequence":"Consecuencia clara.","main_interpretation":"Interpretación principal.","supporting_evidence":["F-1"],"interpretive_limit":"Límite interpretativo.","relationship_to_provisional_thesis":"Relacionada con la tesis provisional.","potential_contribution_to_progression":"Aporta progresión.","created_at":"2026-07-24T20:00:00Z"}
VALID_FIXTURES["material_curation"] = {"curation_id":"C-1","episode_id":"EP-1","research_id":"R-1","analysis_ids":["A-1"],"candidates":[{"material_id":"M-1","function":"Complicación","thesis_contribution":"Aporta.","new_perspective":"Nueva.","redundancy_with_selected":[],"context_cost":"Bajo.","narrative_evidence_strength":"HIGH","contradiction_or_nuance":"Matiz.","narrative_use":"COMPLICATION","selection_status":"SELECTED"}],"selected_material_ids":["M-1"],"selection_stage":"FINAL","exclusions":[],"sequence_rationale":"Secuencia justificada.","set_relationship":"Relación del conjunto.","unique_contributions":[{"material_id":"M-1","contribution":"Aporta."}],"function_overlap_justification":"No hay solapamiento.","progression_evidence":[{"material_id":"M-1","change_in_understanding":"Cambio.","evidence_refs":["F-1"],"non_substitutability":"No sustituible."}],"inherited_restrictions":[],"selected_materials":["M-1"],"excluded_materials":[],"function_of_each_selected_material":[{"material_id":"M-1","contribution":"Aporta."}],"reason_for_each_exclusion":[],"pairwise_redundancy_review":[],"contrast_map":[{"from_material_id":"M-1","to_material_id":"M-1","contrast":"Autocontraste mínimo de fixture."}],"progression_map":[{"material_id":"M-1","change_in_understanding":"Cambio.","evidence_refs":["F-1"],"non_substitutability":"No sustituible."}],"context_cost":"Bajo.","expected_order":["M-1"],"dependency_between_materials":[],"created_at":"2026-07-24T20:00:00Z"}
VALID_FIXTURES["refined_thesis"] = {"thesis_id":"T-1","episode_id":"EP-1","brief_version":"1.0.0","research_id":"R-1","evidence_report_id":"E-1","semantic_audit_id":"S-1","provisional_thesis_id":"TP-1","analysis_ids":["A-1"],"curation_id":"C-1","statement":"Tesis.","supporting_evidence_refs":["F-1"],"counterevidence_refs":["R-1"],"rival_interpretations":["Rival."],"main_objection":"Objeción.","nuance":"Matiz.","material_contributions":[{"material_id":"M-1","contribution":"Aporta."}],"analysis_confirmed":["Confirmación."],"changes_from_provisional":["Cambio."],"discarded_from_provisional":["Descartado."],"refinement_rationale":"Razón.","refinement_dimensions":[{"dimension":"SCOPE","provisional_position":"Antes.","resulting_position":"Después.","evidence_refs":["F-1"],"rationale":"Razón."}],"inherited_constraint_ids":[],"statement_unchanged_justification":None,"limits":["Límite."],"revision_conditions":["Nueva evidencia."],"stage":"THESIS_REFINED","refined_position":"Posición refinada.","what_was_confirmed":["Confirmado."],"what_was_changed":["Cambiado."],"what_was_rejected":["Rechazado."],"what_was_limited":["Limitado."],"strongest_objection":"Objeción fuerte.","alternative_explanation":"Explicación alternativa.","conditions_of_validity":["Condición."],"remaining_uncertainties":["Incertidumbre."],"evidence_dependencies":["Dependencia."],"created_at":"2026-07-24T20:00:00Z"}
VALID_FIXTURES["b5_i2_semantic_sufficiency_audit"].update({"artifact_references":["analysis:A-1","curation:C-1","refined_thesis:T-1","script_promise:SP-1"],"producer_run_reference":"RUN-P","auditor_run_reference":"RUN-AUDIT-1","producer_actor_id":"producer-1","auditor_actor_id":"auditor-1","auditor_input_checksum":"a"*64,"auditor_write_scope":"AUDIT_ONLY","independence_result":"PASS","dimension_results":[{"dimension":d,"status":"PASS","summary":"Evaluado."} for d in ["TRIVIAL_THESIS","INTERCHANGEABLE_ANALYSIS","DECORATIVE_OBJECTION","FALSE_DEPTH"]],"required_changes":[],"excluded_claims_detected":[],"unsupported_inferences":[],"redundancy_findings":[],"progression_findings":[],"thesis_refinement_finding":{"status":"PASS","summary":"Evaluado."},"blocking_reasons":[],"reaudit_requirements":[]})
VALID_FIXTURES["work_research_dossier"] = {
    "dossier_id": "WRD-001", "dossier_version": "1.0.0", "episode_id": "EP-1", "research_id": "R-1", "evidence_report_id": "E-1",
    "work": {"material_id": "M-1", "title": "Obra de fixture", "creator": "Autor", "consulted_representations": [{"representation_kind": "ORIGINAL_WORK", "edition_or_version": "Edición 1", "consulted_locator": "Capítulo 1"}]},
    "dossier_stage": "RESEARCH_IN_PROGRESS",
    "analysis_references": [{"analysis_id": "A-1", "material_id": "M-1"}],
    "question_and_thesis_relation": {"central_question_ref": "EP-1.pregunta_central", "provisional_thesis_ref": "TP-1", "demonstrates_analysis_ref": "A-1", "does_not_establish_analysis_ref": "A-1", "main_interpretation_analysis_ref": "A-1", "rival_interpretation_analysis_refs": ["A-1"]},
    "claim_dispositions": {"claims_ledger_id": "CL-001", "authority_status": "REPRESENTATION_ONLY_IR4_PENDING", "candidate_allowed_claim_ids": ["CLAIM-001"], "candidate_limited_claim_ids": [], "candidate_blocked_claim_ids": []},
    "overinterpretation_risk": {"level": "MEDIUM", "rationale": "Requiere mantener el límite interpretativo."},
    "candidate_editorial_function_analysis_ref": "A-1", "locators": [{"analysis_id": "A-1", "locator": "Escena 3"}],
    "pending_items": [], "confidence": "HIGH",
    "work_use_sufficiency": {"intended_use": "NARRATIVE_MATERIAL", "status": "IR7_FIDELITY_AUDIT_REQUIRED"},
    "independent_fidelity_audit": {"audit_reference": None, "dependency": "DEFERRED_TO_R1_M10_R1_M11"},
    "created_at": "2026-08-07T10:00:00Z"
}

VALID_FIXTURES["execution_provenance_registry"]["runs"][0].update({
    "prompt_id": "prompt_fixture",
    "prompt_checksum": "a" * 64,
    "input_checksum": "a" * 64,
    "validation_result": "PASS",
})

VALID_FIXTURES["mission_contract"] = {
    "mission_id": "TECHNICAL_HARDENING",
    "artifact_id": "mission-completion-gate",
    "artifact_version": "1.0.0",
    "authorized_paths": ["src/"],
    "protected_untracked_paths": [],
    "protected_untracked_baseline": [],
    "required_tests": [{"label": "fixture", "command": ["python", "-c", "pass"]}],
    "push_allowed": False,
    "contains_material_repair": False,
    "push_guard": {"remote": "origin", "ref": "refs/heads/master", "baseline_remote_commit": "0000000000000000000000000000000000000000"},
    "state_requirements": {"control_path": "plans/001_CONTROL_OPERATIVO.md", "required": {}, "forbidden": {}},
    "schema_checks": []
}


_FIXTURE_SHA = "a" * 64
VALID_FIXTURES["context_reference"] = {
    "ref_id": "CTX-1",
    "context_class": "NORMATIVE",
    "artifact_path": "plans/plan_001/README.md",
    "artifact_type": "MARKDOWN",
    "artifact_version": "1.0.0",
    "artifact_sha256": _FIXTURE_SHA,
    "authority_domain": "INFRASTRUCTURE_GOVERNANCE",
    "required": True,
}
VALID_FIXTURES["resolved_context_manifest"] = {
    "manifest_id": "RCM-1",
    "manifest_schema_version": "1.0.0",
    "capability_id": "CAPABILITY_FIXTURE",
    "role_id": "ROLE_FIXTURE",
    "run_id": "RUN-FIXTURE",
    "normative_refs": [VALID_FIXTURES["context_reference"]],
    "evidentiary_refs": [],
    "historical_refs": [],
    "unresolved_optional_refs": [],
    "manifest_sha256": _FIXTURE_SHA,
}
VALID_FIXTURES["mission_authorization_contract"] = {
    "mission_id": "MISSION-FIXTURE",
    "contract_sha256": _FIXTURE_SHA,
    "live_state_path": "plans/001_CONTROL_OPERATIVO.md",
    "live_state_sha256": _FIXTURE_SHA,
    "capability_ids": ["CAPABILITY_FIXTURE"],
    "execution_profile_ids": ["PROFILE_FIXTURE"],
    "execution_interface": "INTERFACE_FIXTURE",
    "role_ids": ["ROLE_FIXTURE"],
    "allowed_operations": ["READ"],
    "allowed_paths": ["src/"],
    "allowed_routes": ["ANY"],
    "execution_mode": "TECHNICAL_VALIDATION",
    "single_use": True,
    "authority_ref": "plans/authority_fixture.json",
    "authority_sha256": _FIXTURE_SHA,
    "authorized_scope_sha256": _FIXTURE_SHA,
    "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
    "contains_material_repair": False,
    "repair_integrity_evidence_path": "NONE",
}

from src.core.repair_integrity import evidence_checksum

VALID_FIXTURES["repair_integrity_evidence"] = {
    "schema_version": "1.0.0", "repair_id": "repair_fixture", "finding_id": "finding_fixture",
    "mission_id": "TH_03", "mission_contract_sha256": "a" * 64, "contains_material_repair": True,
    "capability_id": "REPAIR_INTEGRITY", "domain": "INFRASTRUCTURE_GOVERNANCE",
    "symptom": "Fixture symptom.", "root_cause": "Fixture root cause.", "root_cause_class": "L4_EVIDENCE",
    "origin_artifact": {"ref_id": "origin_fixture", "artifact_path": "src/core/repair_integrity.py", "artifact_type": "TEXT", "artifact_version": "UNDECLARED", "artifact_sha256": "a" * 64, "required": True},
    "affected_artifacts": ["artifact_fixture"], "repair_depth": "L4_EVIDENCE",
    "repair_actions": ["Fixture repair action."],
    "downstream_impact": {"affected_artifacts": ["artifact_fixture"], "no_impact_justification": ""},
    "downstream_invalidations": [{"artifact_id": "artifact_fixture", "status": "COMPLETED", "evidence_ref": {"ref_id": "inv_fixture", "artifact_path": "src/core/repair_integrity.py", "artifact_type": "TEXT", "artifact_version": "UNDECLARED", "artifact_sha256": "a" * 64, "result": "COMPLETED", "required": True}, "justification": "Fixture."}],
    "downstream_revalidations": [{"artifact_id": "artifact_fixture", "status": "COMPLETED", "evidence_ref": {"ref_id": "reval_fixture", "artifact_path": "src/core/repair_integrity.py", "artifact_type": "TEXT", "artifact_version": "UNDECLARED", "artifact_sha256": "a" * 64, "result": "PASS", "required": True}, "justification": "Fixture."}],
    "detector_impact": "NO", "detector_change_required": "NO", "detector_changes": [],
    "sensitive_detector_changes": {"changed": False, "justification": "No detector changed.", "before_behavior": "", "after_behavior": "", "reason_change_is_valid": "", "regression_evidence_ref": []},
    "regression_evidence": {"defect_no_longer_occurs": True, "neighboring_valid_behavior": True, "evidence_refs": [{"ref_id": "test_fixture", "artifact_path": "src/core/repair_integrity.py", "artifact_type": "TEXT", "artifact_version": "UNDECLARED", "artifact_sha256": "a" * 64, "result": "PASS", "required": True}]},
    "compensating_changes": [], "governance_change_requested": False, "governance_resolution": None,
    "provenance": {"registry_path": "output/execution_provenance_registry.json", "registry_sha256": "a" * 64, "repair_run_id": "RUN-REPAIR", "review_run_id": "RUN-REVIEW"},
    "executor_id": "id_a1b2c3d4", "reviewer_id": "id_e5f6a7b8",
    "review_status": "APPROVED", "review_evidence": {"reviewer_id": "id_e5f6a7b8", "decision": "APPROVED", "evidence_refs": [{"ref_id": "review_fixture", "artifact_path": "src/core/repair_integrity.py", "artifact_type": "TEXT", "artifact_version": "UNDECLARED", "artifact_sha256": "a" * 64, "result": "PASS", "required": True}], "protected_artifact_refs": [{"ref_id": "origin_fixture", "artifact_path": "src/core/repair_integrity.py", "artifact_type": "TEXT", "artifact_version": "UNDECLARED", "artifact_sha256": "a" * 64, "required": True}], "reviewer_modified_under_review": False},
    "created_at": "2026-08-09T00:00:00Z"
}
VALID_FIXTURES["repair_integrity_evidence"]["evidence_sha256"] = evidence_checksum(VALID_FIXTURES["repair_integrity_evidence"])

class TestAllJSONSchemas(unittest.TestCase):

    def test_all_schemas_are_valid_draft7(self):
        """Valida el inventario de schemas y su sintaxis Draft 7."""
        schema_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
        self.assertEqual(set(f.replace(".json", "") for f in schema_files), set(VALID_FIXTURES))

        for filename in schema_files:
            with self.subTest(schema=filename):
                schema_path = os.path.join(SCHEMAS_DIR, filename)
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)
                
                try:
                    Draft7Validator.check_schema(schema_data)
                except jsonschema.exceptions.SchemaError as e:
                    self.fail(f"Esquema {filename} inválido contra el metaschema Draft 7: {e.message}")

    def test_schema_required_fields_in_properties(self):
        """Valida que todos los campos requeridos estén declarados en las propiedades del esquema."""
        schema_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
        for filename in schema_files:
            with self.subTest(schema=filename):
                schema_data = load_schema(filename)
                required_fields = schema_data.get("required", [])
                properties = schema_data.get("properties", {})
                for field in required_fields:
                    self.assertIn(
                        field, 
                        properties, 
                        f"El campo requerido '{field}' no está definido en 'properties' en {filename}"
                    )

    def test_every_schema_has_valid_fixture(self):
        """Valida que cada schema tenga un fixture mínimo válido y pase la validación."""
        schema_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
        for filename in schema_files:
            name = filename.replace(".json", "")
            with self.subTest(schema=name):
                self.assertIn(name, VALID_FIXTURES, f"No se encontró fixture válido para el esquema {filename}")
                fixture = VALID_FIXTURES[name]
                
                # 1. Validar contra el JSON Schema (con FormatChecker activo)
                violations = validate_against_schema(fixture, name)
                self.assertEqual(len(violations), 0, f"Fixture válido falló en la validación de schema para {filename}: {violations}")

                # 2. Validar con validadores de negocio específicos si existen
                if name == "claims_ledger":
                    business_violations = validate_claims_ledger(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de claims_ledger falló validaciones de negocio: {business_violations}")
                elif name == "editorial_script_approval":
                    business_violations = validate_editorial_script_approval(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de editorial_script_approval falló validaciones de negocio: {business_violations}")
                elif name == "human_production_approval":
                    business_violations = validate_human_production_approval(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de human_production_approval falló validaciones de negocio: {business_violations}")
                elif name == "human_publication_approval":
                    business_violations = validate_human_publication_approval(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de human_publication_approval falló validaciones de negocio: {business_violations}")
                elif name == "research_pack":
                    business_violations = validate_research_pack(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de research_pack falló validaciones de negocio: {business_violations}")

    def test_every_research_contract_schema_has_valid_fixture(self):
        """Valida que los schemas de investigación de R1-M2 pasen sus validadores de negocio."""
        mapper = {
            "research_pack": validate_research_pack,
            "claims_ledger": validate_claims_ledger,
            "source_access_and_evidence_report": validate_source_access_and_evidence_report,
            "work_research_dossier": lambda dossier: validate_work_research_dossier(
                dossier, VALID_FIXTURES["claims_ledger"], [VALID_FIXTURES["narrative_human_analysis"]]
            ),
        }
        for name, validator in mapper.items():
            with self.subTest(schema=name):
                violations = validator(VALID_FIXTURES[name])
                self.assertEqual(
                    len(violations), 0,
                    f"Fixture válido de {name} falló validaciones de negocio: {violations}",
                )

    def test_representative_invalid_fixtures(self):
        """Valida casos inválidos representativos para asegurar que las fallas sean detectadas."""
        # 1. Caso inválido para editorial_profile (falta campo obligatorio)
        profile_fixture = dict(VALID_FIXTURES["editorial_profile"])
        del profile_fixture["channel_id"]
        violations = validate_against_schema(profile_fixture, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara al faltar 'channel_id'")
        self.assertTrue(any("channel_id" in v for v in violations))

        # 2. Caso inválido para gate_result (enum incorrecto de status)
        gate_fixture = dict(VALID_FIXTURES["gate_result"])
        gate_fixture["status"] = "UNKNOWN_STATUS"
        violations = validate_against_schema(gate_fixture, "gate_result")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara con status inválido")
        self.assertTrue(any("status" in v for v in violations))

    def test_new_invalid_cases_for_hardness(self):
        """Prueba casos de fallo específicos añadidos para comprobar el endurecimiento de los schemas."""
        # A. Status con fecha
        profile_fixture = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture["status"] = "2026-07-21T22:00:00Z" # Fecha en vez de enum de status
        violations = validate_against_schema(profile_fixture, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara al ingresar fecha en 'status'")
        self.assertTrue(any("status" in v for v in violations))

        # B. Versión con fecha
        profile_fixture_v = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture_v["version"] = "2026-07-21T22:00:00Z" # Fecha en vez de SemVer
        violations = validate_against_schema(profile_fixture_v, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara al ingresar fecha en 'version'")
        self.assertTrue(any("version" in v for v in violations))

        # C. Date-time inválido
        profile_fixture_d = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture_d["created_at"] = "fecha-invalida" # String que no cumple date-time
        violations = validate_against_schema(profile_fixture_d, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara con date-time inválido en 'created_at'")
        self.assertTrue(any("created_at" in v for v in violations))

        # D. Checksum inválido
        profile_fixture_c = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture_c["checksum"] = "checksum-invalido-corto" # String que no tiene 64 chars hex
        violations = validate_against_schema(profile_fixture_c, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara con checksum inválido")
        self.assertTrue(any("checksum" in v for v in violations))

        # E. MissionContract sin push_guard debe fallar también en el schema
        contract_fixture = dict(VALID_FIXTURES["mission_contract"])
        del contract_fixture["push_guard"]
        violations = validate_against_schema(contract_fixture, "mission_contract")
        self.assertTrue(any("push_guard" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
