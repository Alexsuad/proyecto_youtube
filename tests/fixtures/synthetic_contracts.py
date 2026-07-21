"""
Fixtures Sintéticos Mínimos para Contratos Válidos e Inválidos (Misión B1)
Proyecto YouTube — Sistema Agéntico Editorial
"""

from typing import Dict, Any

VALID_CHECKSUM = "a" * 64

VALID_EDITORIAL_PROFILE: Dict[str, Any] = {
    "profile_id": "EP-MAS-ALLA-DEL-GUION",
    "channel_id": "MasAllaDelGuion",
    "version": "1.0.0",
    "status": "DRAFT",
    "created_at": "2026-07-21T20:00:00Z",
    "updated_at": "2026-07-21T20:00:00Z",
    "functional_owner_role": "EDITORIAL_LEAD",
    "functional_approval_status": "APPROVED",
    "functional_approved_by": "editor_jefe_editorial_01",
    "functional_approved_at": "2026-07-21T20:00:00Z",
    "identity": "Canal de ensayismo cinematográfico y narrativo profundo.",
    "purpose": "Analizar la estructura y significado humano de las historias.",
    "positioning": "Ensayismo riguroso y accesible.",
    "primary_promise": "Revelar el subtexto y la maestría narrativa Detrás del Guion.",
    "checksum": VALID_CHECKSUM,
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
    "facts": ["El director filmó la escena en 1999."],
    "interpretations": ["La escena simboliza el aislamiento del personaje."],
    "hypotheses": ["El uso del color azul anticipa la tragedia."],
    "contradictions": [],
    "source_registry": [{"source_id": "S1", "name": "Entrevista oficial"}],
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
