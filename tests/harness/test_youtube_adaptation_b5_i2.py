from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.status import GateStatus
from src.scripts.youtube_adaptation_b5_i2_gate import evaluate

ROOT = Path(__file__).parents[2]


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(payload + "\n", encoding="utf-8")
    return _digest_bytes(path.read_bytes())


def _active_profile_ref() -> dict[str, str]:
    active = json.loads((ROOT / "config" / "active_editorial_profile.json").read_text(encoding="utf-8"))
    return {"profile_id": active["ACTIVE_PROFILE_ID"], "profile_version": active["ACTIVE_PROFILE_VERSION"], "profile_checksum": active["profile_checksum"]}


def _early_packaging() -> dict:
    ref = _active_profile_ref()
    return {
        "packaging_id": "PKG-1", "episode_id": "EP-1", "refined_thesis_id": "T-1", "refined_thesis_checksum": "a" * 64,
        "audience": {"persona_concreta": "Espectador que busca una lectura narrativa concreta.", "conocimiento_previo": "Conoce la obra solo de forma general.", "tension_reconocida": "Percibe una contradicción emocional pero no la entiende del todo.", "relevancia": "La lectura promete una interpretación útil y situada.", "expectativa_que_no_debe_generarse": "No prometer verdad absoluta ni resolución terapéutica.", "profile_id": ref["profile_id"], "profile_version": ref["profile_version"], "profile_checksum": ref["profile_checksum"], "brief_checksum": "b" * 64},
        "promesa_visible_provisional": "Una promesa visible honesta y específica.", "tension_central": "Una tensión central clara.", "expectativa_del_espectador": "El espectador espera una reinterpretación concreta.", "diferenciador": "El enfoque no es intercambiable entre episodios.", "titulo_de_trabajo": "Título de trabajo temprano.", "concepto_inicial_miniatura": "Miniatura conceptual temprana.", "titulo_miniatura_complementarity": "Título y miniatura se complementan sin repetir lo mismo.", "overpromise_risk": "LOW",
        "platform_constraints": [{"constraint": "No exagerar la promesa.", "reason": "Evitar sobrepromesa.", "impact": "Mantener honestidad."}],
        "honesty_assessment": {"thesis_relation": "Relacionada con la tesis refinada.", "thesis_refs": ["T-1"], "evidence_refs": ["E-1"], "inherited_constraint_ids": [], "unsupported_elements": [], "risk_level": "LOW", "risk_justification": "No depende de afirmaciones absolutas.", "mitigation_or_pending": None},
        "status": "PROVISIONAL_YOUTUBE_ADAPTATION_INPUT", "created_at": "2026-08-01T10:00:00Z",
    }


def _valid_package() -> dict:
    ref = _active_profile_ref()
    return {
        "package_id": "YT-PKG-1", "episode_id": "EP-1", "active_profile_reference": ref,
        "input_references": {"episode_brief": {"artifact_id": "EP-1", "version": "1.0.0", "checksum": "a" * 64}, "refined_thesis": {"artifact_id": "T-1", "version": "1.0.0", "checksum": "a" * 64}, "editorial_script_promise": {"artifact_id": "SP-1", "version": "1.0.0", "checksum": "a" * 64}, "evidence_or_claims_reference": {"artifact_id": "E-1", "version": "1.0.0", "checksum": "a" * 64}},
        "producer_run_id": "RUN-PROD-1",
        "episode_youtube_positioning": {"concrete_audience": {"audience_segment": "Personas que ya conocen la obra pero no han articulado esta tensión narrativa.", "prior_knowledge": "Conocimiento general de la obra y su conflicto principal.", "recognized_tension": "Perciben una contradicción emocional aún no explicada.", "relevance": "La lectura promete una reinterpretación útil y situada.", "expected_language_level": "Lenguaje claro con precisión conceptual media.", "likely_misinterpretation": "Confundir interpretación con verdad cerrada.", "expectation_not_to_create": "No prometer certeza total ni cierre definitivo."}, "visible_promise": {"promise_statement": "Una promesa visible específica y no intercambiable.", "viewer_gain": "Comprender una tensión concreta del episodio.", "scope": "Solo la lectura desarrollada en el episodio.", "limits": ["No reemplaza el análisis audiovisual final."], "supporting_claims": ["C1"], "unsupported_elements": [], "differentiation": "Se apoya en una tensión concreta del episodio."}},
        "early_packaging_hypothesis": _early_packaging(),
        "youtube_design_constraints": {"opening_readiness": {"click_confirmation": "Confirmar desde el inicio la promesa visible.", "early_substance": "Aportar sustancia antes de cualquier expansión lateral.", "minimum_context": "Dar contexto mínimo suficiente para seguir la lectura.", "central_tension": "Exponer la tensión central temprano.", "viewer_relevance": "Mostrar por qué esto importa al espectador.", "route_preview": "Anticipar la ruta del episodio sin redactarla entera.", "transition_obligation": "Conectar la apertura con el desarrollo sin salto brusco.", "expectations_to_avoid": ["No prometer cierre total.", "No fingir certeza absoluta."], "invalidated_by": ["Apertura redactada como versión final."]}, "duration_assessment": {"recommended_range": "14-18 minutos", "assumptions": ["El episodio conserva densidad media."], "complexity_factors": ["Exige contextualizar una tensión narrativa."], "density_factors": ["Hay varias relaciones conceptuales que deben sostenerse."], "audience_factors": ["Se asume audiencia interesada pero no experta."], "compression_risk": "Perder matices si se comprime demasiado.", "padding_risk": "Repetición si se estira sin aportar progresión.", "mitigation_or_pending": "Ajustar después del outline, sin fijar cifra universal."}},
        "preliminary_youtube_risk_review": {"platform_risk": {"signals_detected": ["Tema sensible, pero tratado en contexto analítico."], "surface": {"narration": "Narración analítica contextualizada.", "working_title": "Título temprano sin afirmaciones absolutas.", "thumbnail_concept": "Miniatura sin shock gratuito."}, "context": "Lectura cultural situada, no instrucción dañina.", "treatment": "Analítico y prudente.", "advertising_risk": "LOW", "community_guidelines_risk": "LOW", "severity": "LOW", "mitigations": ["Contextualizar afirmaciones sensibles."], "uncertainties": ["Pendiente revisión audiovisual final."], "audiovisual_review_pending": True}, "rights_reuse_risk": {"quotes": "Citas breves y no sustitutivas.", "paraphrases": "Paráfrasis orientadas a análisis.", "dialogue_reproduction": "No se usa como columna vertebral.", "scene_dependency": "Dependencia parcial y comentada.", "chronological_summary_dependency": "No se apoya en resumen cronológico sustitutivo.", "transformative_function": "La función es interpretativa y comparativa.", "commentary_and_analysis": "El comentario domina sobre la reproducción.", "summary_substitution_risk": "LOW", "textual_risk": "LOW", "audiovisual_review_pending": True, "unresolved_items": [], "mitigations": ["Mantener citas breves y funcionales."]}},
        "unsupported_elements": [], "unresolved_items": [], "producer_limits": ["No autoriza B5-I3.", "No autoriza packaging final."], "created_at": "2026-08-01T10:00:00Z",
    }


def _capability(decision: str = "PASS", mitigation: str | None = "Mitigado.", blocking: str | None = None) -> dict:
    return {"decision": decision, "rationale": "Evaluación trazable.", "evidence_refs": ["E-1"], "mitigation_or_pending": mitigation, "blocking_reason": blocking}

def _valid_review(package_checksum: str) -> dict:
    ref = _active_profile_ref()
    results = {key: _capability() for key in ["YT_EARLY_AUDIENCE_FIT", "YT_VISIBLE_PROMISE", "YT_EARLY_PACKAGING_HYPOTHESIS", "YT_PROMISE_CONTENT_ALIGNMENT", "YT_OPENING_READINESS", "YT_DURATION_ENVELOPE", "YT_OVERPROMISE_REVIEW", "YT_TEXT_PLATFORM_RISK", "YT_SCRIPT_RIGHTS_REUSE_RISK"]}
    return {
        "review_id": "YT-REV-1", "episode_id": "EP-1", "artifact_id": "YT-PKG-1", "artifact_checksum": package_checksum, "producer_run_id": "RUN-PROD-1", "auditor_run_id": "RUN-AUD-1",
        "independence_check": {"producer_actor_id": "YOUTUBE_ADAPTATION_PRODUCER", "auditor_actor_id": "YOUTUBE_ADAPTATION_AUDITOR", "producer_run_id": "RUN-PROD-1", "auditor_run_id": "RUN-AUD-1", "decision": "PASS"},
        "active_profile_reference": ref, "capability_results": results, "overpromise_decision": _capability(), "unsupported_elements": [],
        "platform_risk_summary": {"severity": "LOW", "summary": "Riesgo contextual bajo.", "mitigations": ["Contextualizar."], "uncertainties": ["Pendiente revisión audiovisual."]},
        "rights_reuse_summary": {"severity": "LOW", "summary": "Uso transformativo preliminarmente aceptable.", "mitigations": ["Mantener citas breves."], "unresolved_items": []},
        "opening_readiness": {"decision": "PASS", "rationale": "Se expresan obligaciones, no un texto redactado.", "pending_items": []},
        "duration_assessment": {"decision": "PASS", "rationale": "Tiene justificación proporcional.", "recommended_range": "14-18 minutos"},
        "findings": ["Sin hallazgos bloqueantes."], "required_changes": [], "blocking_reasons": [], "unresolved_items": [],
        "publication_limit": {"DOES_NOT_AUTHORIZE": ["B5_I3", "FINAL_PACKAGING", "PRODUCTION", "PUBLICATION", "MONETIZATION_GUARANTEE", "LEGAL_APPROVAL"]},
        "decision": "APPROVAL", "created_at": "2026-08-01T10:05:00Z",
    }


def _registry(package_checksum: str, review_checksum: str) -> dict:
    return {
        "registry_version": "1.0.0",
        "runs": [
            {"run_id": "RUN-PROD-1", "episode_id": "EP-1", "role": "YOUTUBE_ADAPTATION_PRODUCER", "skill_id": "skill_packaging", "skill_version": "1.0.0", "provider_or_adapter": "provider-real", "provider_kind": "REAL", "model_or_evaluator": "model-real", "input_manifest_checksum": "a" * 64, "outputs": [{"artifact_kind": "youtube_adaptation_b5_i2_package", "artifact_id": "YT-PKG-1", "artifact_ref": "youtube_adaptation_b5_i2_package:YT-PKG-1", "artifact_path": None, "checksum": package_checksum}], "started_at": "2026-08-01T10:00:00Z", "completed_at": "2026-08-01T10:01:00Z", "status": "SUCCEEDED", "execution_mode": "REAL", "agent_id": "YOUTUBE_ADAPTATION_PRODUCER", "role_id": "YOUTUBE_ADAPTATION_PRODUCER", "execution_route": "native:provider-real", "execution_profile": "real_profile", "actual_executor": "native_provider", "actual_provider": "provider-real", "actual_model": "model-real", "provider": "provider-real", "model": "model-real", "prompt_version": "1.0.0", "input_artifact_ids": ["refined_thesis:T-1"], "input_versions": ["RUN-T-1"], "input_checksums": ["a" * 64], "output_artifact_ids": ["youtube_adaptation_b5_i2_package:YT-PKG-1"], "output_versions": ["RUN-PROD-1"], "output_checksums": [package_checksum], "finished_at": "2026-08-01T10:01:00Z", "latency": 60, "input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0, "retry_count": 0, "decision": "SUCCEEDED", "error_type": "NONE", "blocking_reason": None, "handoff_target": "YOUTUBE_ADAPTATION_AUDITOR", "prompt_id": "prompt_yap", "prompt_checksum": "a" * 64, "input_checksum": "a" * 64, "validation_result": "PASS"},
            {"run_id": "RUN-AUD-1", "episode_id": "EP-1", "role": "YOUTUBE_ADAPTATION_AUDITOR", "skill_id": "skill_packaging", "skill_version": "1.0.0", "provider_or_adapter": "provider-real", "provider_kind": "REAL", "model_or_evaluator": "model-real", "input_manifest_checksum": "b" * 64, "outputs": [{"artifact_kind": "youtube_adaptation_review", "artifact_id": "YT-REV-1", "artifact_ref": "youtube_adaptation_review:YT-REV-1", "artifact_path": None, "checksum": review_checksum}], "started_at": "2026-08-01T10:02:00Z", "completed_at": "2026-08-01T10:03:00Z", "status": "SUCCEEDED", "execution_mode": "REAL", "agent_id": "YOUTUBE_ADAPTATION_AUDITOR", "role_id": "YOUTUBE_ADAPTATION_AUDITOR", "execution_route": "native:provider-real", "execution_profile": "real_profile", "actual_executor": "native_provider", "actual_provider": "provider-real", "actual_model": "model-real", "provider": "provider-real", "model": "model-real", "prompt_version": "1.0.0", "input_artifact_ids": ["youtube_adaptation_b5_i2_package:YT-PKG-1"], "input_versions": ["RUN-PROD-1"], "input_checksums": [package_checksum], "output_artifact_ids": ["youtube_adaptation_review:YT-REV-1"], "output_versions": ["RUN-AUD-1"], "output_checksums": [review_checksum], "finished_at": "2026-08-01T10:03:00Z", "latency": 60, "input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0, "retry_count": 0, "decision": "SUCCEEDED", "error_type": "NONE", "blocking_reason": None, "handoff_target": "OWNER_REVIEW", "prompt_id": "prompt_yaa", "prompt_checksum": "a" * 64, "input_checksum": package_checksum, "validation_result": "PASS"},
        ],
        "handoffs": [],
        "attempts": [],
    }


def _sync_review_registry_checksum(registry_path: Path, review_path: Path) -> None:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    checksum = _digest_bytes(review_path.read_bytes())
    registry["runs"][1]["outputs"][0]["checksum"] = checksum
    registry["runs"][1]["output_checksums"] = [checksum]
    _write_json(registry_path, registry)


def _paths(tmp_path: Path, package: dict | None = None, review: dict | None = None, registry: dict | None = None):
    base = tmp_path / "youtube_adaptation_case"
    base.mkdir(parents=True, exist_ok=True)
    package = copy.deepcopy(package or _valid_package())
    package_path = base / "package.json"
    package_checksum = _write_json(package_path, package)
    review = copy.deepcopy(review or _valid_review(package_checksum))
    review_path = base / "review.json"
    review_checksum = _write_json(review_path, review)
    registry_path = base / "registry.json"
    _write_json(registry_path, registry or _registry(package_checksum, review_checksum))
    return package, review, package_path, review_path, registry_path


def test_valid_gate_with_exact_real_provenance_passes(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.PASS


def test_valid_producer_package_schema():
    assert not validate_against_schema(_valid_package(), "youtube_adaptation_b5_i2_package")


def test_valid_review_schema_uses_nine_capabilities():
    review = _valid_review("a" * 64)
    assert not validate_against_schema(review, "youtube_adaptation_review")
    assert len(review["capability_results"]) == 9

def test_wrong_producer_output_checksum_fails(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][0]["outputs"][0]["checksum"] = "0" * 64
    registry["runs"][0]["output_checksums"] = ["0" * 64]
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_producer_with_other_role_or_agent_fails(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][0]["agent_id"] = "OTHER_AGENT"
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_wrong_auditor_input_checksum_fails(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][1]["input_checksum"] = "0" * 64
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_wrong_auditor_output_checksum_fails(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][1]["outputs"][0]["checksum"] = "0" * 64
    registry["runs"][1]["output_checksums"] = ["0" * 64]
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_auditor_that_did_not_consume_exact_package_fails(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][1]["input_artifact_ids"] = ["youtube_adaptation_b5_i2_package:OTHER"]
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_synthetic_run_cannot_close_real_gate(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][0]["execution_mode"] = "SYNTHETIC"
    registry["runs"][0]["provider_kind"] = "SYNTHETIC"
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.BLOCKED


def test_overpromise_block_with_global_approval_fails(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["overpromise_decision"] = _capability("BLOCK", None, "Unsupported overpromise.")
    review["capability_results"]["YT_OVERPROMISE_REVIEW"] = _capability("BLOCK", None, "Unsupported overpromise.")
    review["decision"] = "APPROVAL"
    _write_json(review_path, review)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_opening_block_with_capability_pass_fails(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["opening_readiness"]["decision"] = "BLOCK"
    _write_json(review_path, review)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL

def test_platform_high_without_mitigation_fails(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["platform_risk_summary"] = {"severity": "HIGH", "summary": "High unresolved platform risk.", "mitigations": [], "uncertainties": []}
    review["capability_results"]["YT_TEXT_PLATFORM_RISK"] = _capability("PASS", None, None)
    _write_json(review_path, review)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_rights_high_without_mitigation_fails(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["rights_reuse_summary"] = {"severity": "HIGH", "summary": "High rights risk.", "mitigations": [], "unresolved_items": []}
    review["capability_results"]["YT_SCRIPT_RIGHTS_REUSE_RISK"] = _capability("PASS", None, None)
    _write_json(review_path, review)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_blocking_reasons_with_approval_fails(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["blocking_reasons"] = ["Missing essential evidence."]
    _write_json(review_path, review)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_required_changes_with_approval_fails(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["required_changes"] = ["Refine visible promise."]
    _write_json(review_path, review)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.FAIL


def test_independence_not_demonstrated_blocks(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["independence_check"]["producer_actor_id"] = "producer-1"
    review["independence_check"]["auditor_actor_id"] = "auditor-1"
    _write_json(review_path, review)
    _sync_review_registry_checksum(registry_path, review_path)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.BLOCKED


def test_missing_provenance_blocks(tmp_path: Path):
    _, _, package_path, review_path, registry_path = _paths(tmp_path)
    registry = {"registry_version": "1.0.0", "runs": [], "handoffs": [], "attempts": []}
    _write_json(registry_path, registry)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.BLOCKED


def test_coherent_request_changes_is_preserved(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["capability_results"]["YT_VISIBLE_PROMISE"] = _capability("REQUEST_CHANGES", "Refinar promesa visible.", "New version required.")
    review["required_changes"] = ["Refinar promesa visible."]
    review["decision"] = "REQUEST_CHANGES"
    _write_json(review_path, review)
    _sync_review_registry_checksum(registry_path, review_path)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.REQUEST_CHANGES


def test_coherent_block_is_preserved(tmp_path: Path):
    _, review, package_path, review_path, registry_path = _paths(tmp_path)
    review["capability_results"]["YT_TEXT_PLATFORM_RISK"] = _capability("BLOCK", None, "Platform risk unresolved.")
    review["blocking_reasons"] = ["Platform risk unresolved."]
    review["decision"] = "BLOCK"
    review["platform_risk_summary"] = {"severity": "HIGH", "summary": "High unresolved platform risk.", "mitigations": [], "uncertainties": []}
    _write_json(review_path, review)
    _sync_review_registry_checksum(registry_path, review_path)
    assert evaluate(package_path, review_path, registry_path).status is GateStatus.BLOCKED
