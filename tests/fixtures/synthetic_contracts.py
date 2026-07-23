"""
Fixtures Sintéticos Mínimos para Contratos Válidos e Inválidos (Misión B1)
Proyecto YouTube — Sistema Agéntico Editorial
"""

from typing import Dict, Any

VALID_CHECKSUM = "a" * 64

VALID_EDITORIAL_PROFILE: Dict[str, Any] = {
    "profile_id": "MADG-EDITORIAL-PROFILE",
    "channel_id": "MasAllaDelGuion",
    "version": "1.0.0",
    "status": "DRAFT",
    "functional_owner_role": "TEAM_01",
    "source_lineage": [{"source_id": "B3-FUNCTIONAL-SPEC", "locator": "docs/specifications/B3_especificacion_funcional_equipo_01.md", "checksum": VALID_CHECKSUM, "role": "FUNCTIONAL_SPECIFICATION"}],
    "identity_stable": {"identity": "Videoensayos narrativos", "purpose": ["Comprender historias"], "positioning": "Reflexión narrativa", "primary_promise": "Comprender cómo vivimos", "differentiator": ["Interpretación propia"], "editorial_pillars": ["Individuo e identidad"], "territories": [{"name": "Cultura", "classification": "ACTIVE"}], "permanent_limits": ["No inventar"], "authorial_persona": {"acts_as": "Observador con criterio", "does_not_act_as": ["Terapeuta"], "voice_traits": ["Claridad"]}, "first_person_rule": "FIRST_PERSON_ALLOWED_WHEN_TRUE_AND_EDITORIALLY_RELEVANT"},
    "audience_hypotheses": [{"classification": "AUDIENCE_HYPOTHESIS_INITIAL", "statement": "Audiencia inicial", "status": "HYPOTHESIS"}],
    "voice_profile": {"corpus_status": "INCOMPLETE_MISSING_REQUIRED_SAMPLE", "approved_sample_ids": [], "initial_authorized_patterns": ["Observación concreta"], "anti_imitation_rules": ["No copiar referentes"], "approved_positive_examples": ["Ejemplo editorial compatible derivado de la especificación."], "approved_negative_examples": ["Ejemplo editorial incompatible derivado de la especificación."]},
    "supported_delivery_formats": ["VIDEO_ESSAY", "NARRATIVE_PODCAST", "AUDIO_CONTENT"],
    "external_policy_references": [],
    "pending_decisions": ["Muestra real principal"],
}

INVALID_EDITORIAL_PROFILE_EMPTY_VERSION: Dict[str, Any] = {
    **VALID_EDITORIAL_PROFILE,
    "version": "   ",
}

VALID_GATE_RESULT_PASS: Dict[str, Any] = {
    "gate_id": "GATE-01-RESEARCH",
    "artifact_id": "RP-001",
    "artifact_version": "1.0.0",
    "status": "PASS",
    "summary": "Investigacion completada con fuentes primarias verificadas.",
    "violations": [],
    "warnings": [],
    "evidence": {"sources_checked": 5},
    "checked_at": "2026-07-21T20:00:00Z",
    "checker_version": "1.0.0",
    "exit_code": 0,
}

INVALID_GATE_RESULT_CONTRADICTION: Dict[str, Any] = {
    "gate_id": "GATE-01-RESEARCH",
    "artifact_id": "RP-001",
    "artifact_version": "1.0.0",
    "status": "PASS",
    "summary": "Pasó la validación.",
    "violations": ["Violación crítica detectada."],
    "warnings": [],
    "evidence": {},
    "checked_at": "2026-07-21T20:00:00Z",
    "checker_version": "1.0.0",
    "exit_code": 0,
}

VALID_EDITORIAL_SCRIPT_APPROVAL: Dict[str, Any] = {
    "artifact_id": "SCRIPT-EP01",
    "script_version": "1.0.0",
    "checksum": VALID_CHECKSUM,
    "decision": "APPROVED",
    "approved_by": "editor_jefe_01",
    "approved_role": "EDITORIAL_LEAD",
    "approved_at": "2026-07-21T20:00:00Z",
}

INVALID_EDITORIAL_SCRIPT_APPROVAL_AMBIGUOUS_APPROVER: Dict[str, Any] = {
    **VALID_EDITORIAL_SCRIPT_APPROVAL,
    "approved_by": "aprobado",  # Texto ambiguo rechazado por is_valid_approver_identity
}

INVALID_EDITORIAL_SCRIPT_APPROVAL_NO_CHECKSUM: Dict[str, Any] = {
    **VALID_EDITORIAL_SCRIPT_APPROVAL,
    "checksum": "",
}

VALID_HUMAN_PRODUCTION_APPROVAL: Dict[str, Any] = {
    "publication_package_id": "PUB-PKG-01",
    "publication_package_version": "1.0.0",
    "script_version": "1.0.0",
    "packaging_version": "1.0.0",
    "checksum": VALID_CHECKSUM,
    "decision": "APPROVED_FOR_PRODUCTION",
    "approved_by": "lead_produccion_01",
    "approved_role": "PRODUCTION_LEAD",
    "approved_at": "2026-07-21T20:00:00Z",
}

INVALID_HUMAN_PRODUCTION_APPROVAL_TRYING_YOUTUBE_READY: Dict[str, Any] = {
    **VALID_HUMAN_PRODUCTION_APPROVAL,
    "target_status": "YOUTUBE_READY",
}

VALID_HUMAN_PUBLICATION_APPROVAL: Dict[str, Any] = {
    "final_candidate_id": "FINAL-CANDIDATE-01",
    "audiovisual_version": "1.0.0",
    "thumbnail_version": "1.0.0",
    "title_version": "1.0.0",
    "checksum": VALID_CHECKSUM,
    "decision": "APPROVED_FOR_PUBLICATION",
    "approved_by": "lead_publicacion_01",
    "approved_role": "PUBLICATION_LEAD",
    "approved_at": "2026-07-21T20:00:00Z",
    "has_final_audiovisual_assets": True,
}

INVALID_HUMAN_PUBLICATION_APPROVAL_WITHOUT_ASSETS: Dict[str, Any] = {
    **VALID_HUMAN_PUBLICATION_APPROVAL,
    "has_final_audiovisual_assets": False,
}

VALID_RESEARCH_PACK: Dict[str, Any] = {
    "research_id": "RP-001",
    "episode_id": "EP-001",
    "brief_version": "1.0.0",
    "scope": "Cobertura conceptual y narrativa.",
    "facts": [{"item_id": "I1", "statement": "El director filmó la escena en 1999.", "source_refs": ["S1"], "locator": "p. 10", "confidence": "HIGH"}],
    "interpretations": [{"item_id": "I2", "statement": "La escena simboliza el aislamiento.", "source_refs": ["S1"], "locator": "escena 2", "confidence": "MEDIUM"}],
    "hypotheses": [],
    "contradictions": [],
    "alternative_views": [],
    "scene_evidence": [],
    "source_registry": [{"source_id": "S1", "title": "Entrevista oficial", "source_type": "PRIMARY", "url": "https://example.com/source", "access_type": "DIRECT", "locator": "documento completo", "confidence": "HIGH"}],
    "claims_candidates": [],
    "unsupported_claims": [],
    "narrative_opportunities": [],
    "limitations": [],
    "created_at": "2026-07-21T20:00:00Z",
}

INVALID_CLAIMS_LEDGER_NO_SOURCE: Dict[str, Any] = {
    "ledger_id": "CL-001",
    "script_version": "1.0.0",
    "claims": [
        {
            "claim_id": "CLAIM-01",
            "script_location": "Bloque 1, Linea 10",
            "claim_text": "Dato sin fuente probada.",
            "claim_type": "FACT",
            "source_refs": [],  # Inválido: Lista vacía
            "verification_status": "UNVERIFIED",
        }
    ],
}
