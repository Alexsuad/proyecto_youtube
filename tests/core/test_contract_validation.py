"""
Pruebas Unitarias para la Validación Determinista de Contratos (contract_validation.py)
"""

import hashlib
import json
import unittest
from copy import deepcopy
from src.core.contract_validation import (
    validate_editorial_script_approval,
    validate_human_production_approval,
    validate_human_publication_approval,
    validate_research_pack,
    validate_claims_ledger,
    validate_source_access_and_evidence_report,
    validate_work_research_dossier,
)
from tests.fixtures.synthetic_contracts import (
    VALID_EDITORIAL_SCRIPT_APPROVAL,
    INVALID_EDITORIAL_SCRIPT_APPROVAL_AMBIGUOUS_APPROVER,
    INVALID_EDITORIAL_SCRIPT_APPROVAL_NO_CHECKSUM,
    VALID_HUMAN_PRODUCTION_APPROVAL,
    INVALID_HUMAN_PRODUCTION_APPROVAL_TRYING_YOUTUBE_READY,
    VALID_HUMAN_PUBLICATION_APPROVAL,
    INVALID_HUMAN_PUBLICATION_APPROVAL_WITHOUT_ASSETS,
    VALID_RESEARCH_PACK,
    INVALID_CLAIMS_LEDGER_NO_SOURCE,
)


class TestContractValidation(unittest.TestCase):

    @staticmethod
    def _provenance(source_kind="SOURCE_ORIGINAL", **overrides):
        value = {
            "source_kind": source_kind,
            "original_source_ref": None,
            "derived_from_source_ref": None,
            "version": "1.0.0",
            "original_language": "en",
            "derivative_language": None,
            "locator": "documento completo",
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
        value.update(overrides)
        return value

    def _pack_with_sources(self, sources):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["source_registry"] = sources
        return pack

    def test_source_original_and_derived_lineage_is_valid(self):
        root = {"source_id": "S1", "title": "Audio original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:00", "confidence": "HIGH", "provenance": self._provenance()}
        transcript = {"source_id": "S2", "title": "Transcripción manual", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:00", "confidence": "HIGH", "provenance": self._provenance("TRANSCRIPT", original_source_ref="S1", derived_from_source_ref="S1", derivative_language="en", transcription_type="MANUAL", transformation_method="MANUAL_TRANSCRIPTION")}
        self.assertEqual(validate_research_pack(self._pack_with_sources([root, transcript])), [])

    def test_derived_source_without_origin_fails(self):
        source = {"source_id": "S1", "title": "Traducción huérfana", "source_type": "SECONDARY", "access_type": "INDIRECT", "locator": "p. 1", "confidence": "MEDIUM", "provenance": self._provenance("TRANSLATION", derivative_language="es", transformation_method="MACHINE_TRANSLATION")}
        violations = validate_research_pack(self._pack_with_sources([source]))
        self.assertTrue(any("original_source_ref" in violation for violation in violations))

    def test_audiovisual_provenance_keeps_timestamp(self):
        source = {"source_id": "S1", "title": "Vídeo original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:10:00-00:10:30", "confidence": "HIGH", "provenance": self._provenance(locator="00:10:00-00:10:30", timestamp={"start": "00:10:00", "end": "00:10:30"})}
        self.assertEqual(validate_research_pack(self._pack_with_sources([source])), [])

    def test_transcription_types_are_distinguished(self):
        root = {"source_id": "S1", "title": "Audio original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:00", "confidence": "HIGH", "provenance": self._provenance()}
        sources = [root]
        for index, transcription_type in enumerate(("OFFICIAL", "CREATOR_PROVIDED", "AUTOMATIC", "MANUAL"), start=2):
            sources.append({"source_id": f"S{index}", "title": transcription_type, "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:01", "confidence": "HIGH", "provenance": self._provenance("TRANSCRIPT", original_source_ref="S1", derived_from_source_ref="S1", transcription_type=transcription_type, transformation_method=f"{transcription_type}_TRANSCRIPTION", verification_status="REVIEWED" if transcription_type == "AUTOMATIC" else "PRIMARY_VERIFIED")})
        self.assertEqual(validate_research_pack(self._pack_with_sources(sources)), [])

    def test_unreviewed_automatic_transcript_cannot_support_exact_quote(self):
        root = {"source_id": "S1", "title": "Audio original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:00", "confidence": "HIGH", "provenance": self._provenance()}
        transcript = {"source_id": "S2", "title": "Transcripción automática", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:01", "confidence": "MEDIUM", "provenance": self._provenance("TRANSCRIPT", original_source_ref="S1", derived_from_source_ref="S1", transcription_type="AUTOMATIC", verification_status="NOT_REVIEWED", primary_verification_performed=False, permitted_uses=["EXACT_QUOTE"], translation_transcription_risk="HIGH")}
        violations = validate_research_pack(self._pack_with_sources([root, transcript]))
        self.assertTrue(any("EXACT_QUOTE" in violation for violation in violations))

    def test_material_transcription_error_requires_primary_verification(self):
        root = {"source_id": "S1", "title": "Audio original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:00", "confidence": "HIGH", "provenance": self._provenance()}
        transcript = {"source_id": "S2", "title": "Transcripción con duda material", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "00:02", "confidence": "LOW", "provenance": self._provenance("TRANSCRIPT", original_source_ref="S1", derived_from_source_ref="S1", transcription_type="MANUAL", verification_status="NOT_REVIEWED", primary_verification_performed=False, material_transcription_error=True, translation_transcription_risk="MATERIAL")}
        violations = validate_research_pack(self._pack_with_sources([root, transcript]))
        self.assertTrue(any("error material" in violation for violation in violations))

    def test_unverified_translation_cannot_replace_original_exact_formulation(self):
        root = {"source_id": "S1", "title": "Original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "p. 1", "confidence": "HIGH", "provenance": self._provenance()}
        translation = {"source_id": "S2", "title": "Traducción", "source_type": "SECONDARY", "access_type": "INDIRECT", "locator": "p. 1", "confidence": "MEDIUM", "provenance": self._provenance("TRANSLATION", original_source_ref="S1", derived_from_source_ref="S1", derivative_language="es", transformation_method="HUMAN_TRANSLATION", verification_status="REVIEWED", primary_verification_performed=False, permitted_uses=["EXACT_QUOTE"], translation_transcription_risk="MATERIAL")}
        violations = validate_research_pack(self._pack_with_sources([root, translation]))
        self.assertTrue(any("formulación exacta" in violation for violation in violations))

    def test_summary_or_review_cannot_prove_work_content(self):
        root = {"source_id": "S1", "title": "Obra original", "source_type": "PRIMARY", "access_type": "DIRECT", "locator": "obra", "confidence": "HIGH", "provenance": self._provenance()}
        review = {"source_id": "S2", "title": "Reseña", "source_type": "SECONDARY", "access_type": "SECONDARY_ONLY", "locator": "p. 2", "confidence": "MEDIUM", "provenance": self._provenance("REVIEW", original_source_ref="S1", derived_from_source_ref="S1", derivative_language="es", transformation_method="HUMAN_REVIEW", claim_authority="INTERPRETIVE", permitted_uses=["PROVE_WORK_CONTENT"])}
        violations = validate_research_pack(self._pack_with_sources([root, review]))
        self.assertTrue(any("no prueba por sí sola" in violation for violation in violations))

    def test_secondary_youtube_source_cannot_self_declare_youtube_policy_authority(self):
        source = {"source_id": "S1", "title": "Comentario sobre YouTube", "source_type": "SECONDARY", "access_type": "SECONDARY_ONLY", "locator": "p. 1", "confidence": "MEDIUM", "provenance": self._provenance(claim_authority="SECONDARY", authority_domain="YOUTUBE_ADAPTATION", official_primary=False, permitted_uses=["YOUTUBE_POLICY"])}
        violations = validate_research_pack(self._pack_with_sources([source]))
        self.assertTrue(any("política oficial de YouTube" in violation for violation in violations))

    def test_multilingual_trigger_is_valid_and_tracks_affected_claims(self):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["multilingual_research"] = {"activation_status": "ACTIVATED", "triggers": ["TRANSLATION_SEMANTIC_RISK"], "non_trigger_examples": [], "affected_source_ids": ["S1"], "affected_claim_ids": ["C1"], "required_language": "en", "material_risk": ["CLAIM_VALIDITY", "WORK_INTERPRETATION"], "consultation_result": "LIMITED_BUT_USABLE", "limitations": ["El matiz sigue pendiente de revisión primaria."], "invalidators": ["CLAIM_OR_USE_CHANGED"], "return_route": "LIMITED_BUT_USABLE", "decision_basis": "La formulación original puede cambiar la interpretación."}
        pack["critical_claims_assessment"] = {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL"}
        self.assertEqual(validate_research_pack(pack), [])

    def test_multilingual_non_trigger_does_not_activate(self):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["multilingual_research"] = {"activation_status": "NOT_ACTIVATED", "triggers": [], "non_trigger_examples": ["FIXED_LANGUAGE_QUOTA"], "affected_source_ids": [], "affected_claim_ids": [], "required_language": None, "material_risk": [], "consultation_result": "NOT_APPLICABLE", "limitations": [], "invalidators": [], "return_route": "NOT_APPLICABLE", "decision_basis": "No existe diferencia lingüística material para el uso previsto."}
        self.assertEqual(validate_research_pack(pack), [])

    def test_multilingual_not_activated_cannot_declare_material_risk(self):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["multilingual_research"]["material_risk"] = ["CLAIM_VALIDITY"]
        violations = validate_research_pack(pack)
        self.assertTrue(any("NOT_ACTIVATED" in violation and "impactos" in violation for violation in violations))

    def test_multilingual_invalidation_requires_reevaluation_route(self):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["multilingual_research"] = {"activation_status": "REEVALUATION_REQUIRED", "triggers": ["ORIGINAL_SOURCE_NOT_IN_SPANISH"], "non_trigger_examples": [], "affected_source_ids": ["S1"], "affected_claim_ids": [], "required_language": "en", "material_risk": ["SUFFICIENCY"], "consultation_result": "MORE_RESEARCH_REQUIRED", "limitations": ["Apareció una fuente primaria en español suficiente."], "invalidators": ["PRIMARY_SPANISH_SOURCE_RECOVERED"], "return_route": "MORE_RESEARCH_REQUIRED", "decision_basis": "La decisión previa dejó de ser válida y debe reevaluarse."}
        self.assertEqual(validate_research_pack(pack), [])

    def test_multilingual_decision_preserves_complete_catalogs_and_route_coherence(self):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["critical_claims_assessment"] = {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL"}
        pack["multilingual_research"] = {
            "activation_status": "ACTIVATED",
            "triggers": ["ORIGINAL_SOURCE_NOT_IN_SPANISH", "SPANISH_COVERAGE_DEPENDS_ON_DERIVATIVES", "MATERIAL_SOURCE_GAP", "TRANSLATION_SEMANTIC_RISK", "CONFLICTING_TRANSLATIONS", "LINGUISTICALLY_SPLIT_CONTROVERSY", "LOCAL_CONTEXT_REQUIRED", "AUTHORIAL_OR_CREATOR_STATEMENT", "PRIMARY_VERIFICATION_REQUIRED", "EVIDENCE_SUFFICIENCY_BLOCKED_BY_LANGUAGE"],
            "non_trigger_examples": ["FIXED_LANGUAGE_QUOTA", "SOURCE_VOLUME_ONLY", "OFFICIAL_TRANSLATION_SUFFICIENT", "DUPLICATED_FOREIGN_COVERAGE", "UNRELATED_INTERNATIONAL_PERSPECTIVE", "TRANSLATE_ALL_AUTOMATICALLY", "LANGUAGE_AS_AUTHORITY_SIGNAL", "NO_LINGUISTIC_DIFFERENCE_REQUIRED", "TECHNICAL_CAPABILITY_DEMO"],
            "affected_source_ids": ["S1"],
            "affected_claim_ids": ["C1"],
            "required_language": "en",
            "material_risk": ["CLAIM_VALIDITY", "WORK_INTERPRETATION", "CONTRADICTION", "SUFFICIENCY", "WORK_SELECTION", "THESIS", "DISCLOSURE_OR_LIMITATION"],
            "consultation_result": "YOUTUBE_ADAPTATION_REVIEW_REQUIRED",
            "limitations": ["La consulta reveló un impacto sobre una política de plataforma."],
            "invalidators": ["CLAIM_OR_USE_CHANGED", "PRIMARY_SPANISH_SOURCE_RECOVERED", "AUTHORIZED_TRANSLATION_RESOLVES_RISK", "SAME_ORIGIN_DISCOVERED", "TRANSLATION_LINEAGE_OR_METHOD_LOST", "FOREIGN_SOURCE_LACKS_AUTHORITY", "VERSION_ADAPTATION_OR_CONTEXT_CHANGED", "NEW_CONTROVERSY_INTRODUCED", "TRANSLATED_CONTENT_NOT_VERIFIABLE", "LANGUAGE_QUERY_MASKS_GENERAL_INSUFFICIENCY"],
            "return_route": "YOUTUBE_ADAPTATION_REVIEW_REQUIRED",
            "decision_basis": "La ausencia de consulta lingüística puede cambiar la suficiencia y el disclosure de plataforma.",
        }
        self.assertEqual(validate_research_pack(pack), [])

    def test_multilingual_result_and_return_route_mismatch_fails(self):
        pack = deepcopy(VALID_RESEARCH_PACK)
        pack["multilingual_research"] = {"activation_status": "ACTIVATED", "triggers": ["MATERIAL_SOURCE_GAP"], "non_trigger_examples": [], "affected_source_ids": ["S1"], "affected_claim_ids": ["C1"], "required_language": "en", "material_risk": ["SUFFICIENCY"], "consultation_result": "MORE_RESEARCH_REQUIRED", "limitations": ["Falta una fuente relevante."], "invalidators": ["CLAIM_OR_USE_CHANGED"], "return_route": "LIMITED_BUT_USABLE", "decision_basis": "La cobertura es insuficiente."}
        pack["critical_claims_assessment"] = {"status": "IDENTIFIED", "claim_ids": ["C1"], "justification": None, "editorial_impact": "MATERIAL"}
        self.assertTrue(any("return_route" in violation for violation in validate_research_pack(pack)))

    def test_editorial_script_approval_valid(self):
        violations = validate_editorial_script_approval(VALID_EDITORIAL_SCRIPT_APPROVAL)
        self.assertEqual(len(violations), 0)

    def test_editorial_script_approval_ambiguous_approver(self):
        violations = validate_editorial_script_approval(INVALID_EDITORIAL_SCRIPT_APPROVAL_AMBIGUOUS_APPROVER)
        self.assertTrue(any("Identidad del aprobador invalida o ambigua" in v for v in violations))

    def test_editorial_script_approval_missing_checksum(self):
        violations = validate_editorial_script_approval(INVALID_EDITORIAL_SCRIPT_APPROVAL_NO_CHECKSUM)
        self.assertTrue(any("Checksum obligatorio ausente" in v for v in violations))

    def test_human_production_approval_valid(self):
        violations = validate_human_production_approval(VALID_HUMAN_PRODUCTION_APPROVAL)
        self.assertEqual(len(violations), 0)

    def test_human_production_approval_cannot_declare_youtube_ready(self):
        violations = validate_human_production_approval(INVALID_HUMAN_PRODUCTION_APPROVAL_TRYING_YOUTUBE_READY)
        self.assertTrue(any("HumanProductionApproval NO puede declarar el estado YOUTUBE_READY" in v for v in violations))

    def test_human_publication_approval_valid(self):
        violations = validate_human_publication_approval(VALID_HUMAN_PUBLICATION_APPROVAL)
        self.assertEqual(len(violations), 0)

    def test_human_publication_approval_fails_without_assets(self):
        violations = validate_human_publication_approval(INVALID_HUMAN_PUBLICATION_APPROVAL_WITHOUT_ASSETS)
        self.assertTrue(any("sin la existencia y verificacion previa de los activos audiovisuales finales" in v for v in violations))

    def test_research_pack_validation(self):
        violations = validate_research_pack(VALID_RESEARCH_PACK)
        self.assertEqual(len(violations), 0)

    def test_claims_ledger_no_source_fails(self):
        violations = validate_claims_ledger(INVALID_CLAIMS_LEDGER_NO_SOURCE)
        self.assertTrue(any("sin fuente ni estado de verificacion" in v for v in violations))

    def test_claims_ledger_exact_quote_requires_provenance_evidence(self):
        ledger = {"ledger_id": "CL-001", "script_version": "1.0.0", "claims": [{"claim_id": "C1", "script_location": "B1", "claim_text": "Cita", "claim_type": "QUOTE", "source_refs": ["S1"], "verification_status": "VERIFIED", "intended_use": "EXACT_QUOTE"}]}
        violations = validate_claims_ledger(ledger)
        self.assertTrue(any("provenance_evidence_refs" in violation for violation in violations))

    def test_claims_ledger_provenance_evidence_must_reference_claim_source(self):
        ledger = {"ledger_id": "CL-001", "script_version": "1.0.0", "claims": [{"claim_id": "C1", "script_location": "B1", "claim_text": "Cita", "claim_type": "QUOTE", "source_refs": ["S1"], "verification_status": "VERIFIED", "intended_use": "EXACT_QUOTE", "provenance_evidence_refs": ["UNRELATED"], "provenance_status": "PRIMARY_VERIFIED", "authority_basis": "PRIMARY_SOURCE"}]}
        violations = validate_claims_ledger(ledger)
        self.assertTrue(any("incluidas en source_refs" in violation for violation in violations))

    def test_claims_ledger_youtube_policy_requires_official_primary_authority(self):
        ledger = {"ledger_id": "CL-001", "script_version": "1.0.0", "claims": [{"claim_id": "C1", "script_location": "B1", "claim_text": "Política", "claim_type": "PLATFORM_POLICY", "source_refs": ["S1"], "verification_status": "VERIFIED", "intended_use": "YOUTUBE_POLICY", "provenance_evidence_refs": ["S1"], "provenance_status": "PRIMARY_VERIFIED", "authority_basis": "PRIMARY_SOURCE"}]}
        violations = validate_claims_ledger(ledger)
        self.assertTrue(any("YOUTUBE_OFFICIAL_PRIMARY" in violation for violation in violations))

    def test_research_pack_phenomenon_extensions_validate(self):
        pack = {
            **VALID_RESEARCH_PACK,
            "research_pack_kind": "PHENOMENON",
            "phenomenon_research_stop_decision_ref": "RSD-PHEN-001",
            "aggregate_research_stop_decision_ref": "RSD-AGG-001",
            "phenomenon": {
                "phenomenon_id": "PH-001",
                "phenomenon_kind": "CULTURAL",
            },
            "editorial_uses": {
                "intended_uses": ["CENTRAL_CLAIM_SUPPORT"],
                "criticality_map": {"claims": [{"claim_id": "C-001", "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT"}]},
            },
            "claims_candidates": [
                {"item_id": "C-001", "statement": "Claim", "source_refs": ["S1"], "locator": "p. 1", "confidence": "HIGH"}
            ],
            "rival_analysis": [{
                "rival_explanation_id": "R-001",
                "statement": "Explicación rival",
                "agreement_status": "DISAGREEMENT",
                "disagreement_kind": "RIVAL_OPEN",
                "claim_ids": ["C-001"],
                "source_refs": ["S1"],
            }],
            "semantic_status": {
                "status_per_claim": [{"claim_id": "C-001", "semantic_level": "PLAUSIBLE", "intended_use": "CENTRAL_CLAIM_SUPPORT", "sufficiency_for_intended_use": "NOT_FUNCTIONALLY_VALIDATED"}],
                "ir4_dependency": "DEFERRED_TO_R1_M6",
            },
        }
        self.assertEqual(validate_research_pack(pack), [])

    def test_research_pack_rejects_unknown_claim_reference(self):
        pack = {**VALID_RESEARCH_PACK, "editorial_uses": {"intended_uses": ["CENTRAL_CLAIM_SUPPORT"], "criticality_map": {"claims": [{"claim_id": "UNKNOWN", "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT"}]}}}
        violations = validate_research_pack(pack)
        self.assertTrue(any("criticality_map referencia claim no declarada" in v for v in violations))

    def test_research_pack_rejects_functional_sufficiency_before_ir4(self):
        pack = {
            **VALID_RESEARCH_PACK,
            "claims_candidates": [{
                "item_id": "C-001",
                "statement": "Claim",
                "source_refs": ["S1"],
                "locator": "p. 1",
                "confidence": "HIGH",
            }],
            "semantic_status": {
                "status_per_claim": [{
                    "claim_id": "C-001",
                    "semantic_level": "PLAUSIBLE",
                    "intended_use": "CENTRAL_CLAIM_SUPPORT",
                    "sufficiency_for_intended_use": "PASS",
                }],
                "ir4_dependency": "DEFERRED_TO_R1_M6",
            },
        }
        violations = validate_research_pack(pack)
        self.assertTrue(any("sufficiency_for_intended_use" in v for v in violations))

    def test_source_report_rejects_unknown_dependent_claim(self):
        report = {
            "can_proceed": True,
            "claims_sostenibles": [],
            "claims_pendientes": [],
            "excluded_claims": [],
            "critical_claim_assessments": [],
            "claim_dependent_source_evaluations": [{
                "claim_id": "UNKNOWN",
                "source_id": "UNKNOWN-SOURCE",
                "object_relation": "Directa",
                "claim_authority": "Alta",
                "access_level": "DIRECT",
                "independence": "INDEPENDENT",
                "currency": "Vigente",
                "locator": "p. 1",
                "assessment": "SUPPORTED",
            }],
        }
        violations = validate_source_access_and_evidence_report(report)
        self.assertTrue(any("claim no declarada" in v for v in violations))

    def _valid_work_dossier(self):
        analysis = self._valid_narrative_analyses()[0]
        ledger = self._valid_claims_ledger()
        analysis_checksum = hashlib.sha256(json.dumps(analysis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        ledger_checksum = hashlib.sha256(json.dumps(ledger, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return {
            "dossier_id": "WRD-001", "dossier_version": "1.0.0", "episode_id": "EP-1", "research_id": "R-1", "evidence_report_id": "E-1",
            "work": {"material_id": "M-1", "title": "Obra", "creator": "Autor", "consulted_representations": [{"representation_kind": "ORIGINAL_WORK", "edition_or_version": "Edición 1", "consulted_locator": "Capítulo 1"}]},
            "dossier_stage": "RESEARCH_IN_PROGRESS", "analysis_references": [{"analysis_id": "A-1", "material_id": "M-1", "artifact_version": "1.0.0", "artifact_checksum": analysis_checksum}],
            "question_and_thesis_relation": {"central_question_ref": "EP-1.pregunta_central", "provisional_thesis_ref": "TP-1", "demonstrates_analysis_ref": "A-1", "does_not_establish_analysis_ref": "A-1", "main_interpretation_analysis_ref": "A-1", "rival_interpretation_analysis_refs": ["A-1"]},
            "claim_dispositions": {"claims_ledger_id": "CL-001", "claims_ledger_version": "1.0.0", "claims_ledger_checksum": ledger_checksum, "authority_status": "REPRESENTATION_ONLY_IR4_PENDING", "candidate_allowed_claim_ids": ["CLAIM-001"], "candidate_limited_claim_ids": [], "candidate_blocked_claim_ids": []},
            "overinterpretation_risk": {"level": "MEDIUM", "rationale": "Riesgo contenido."}, "candidate_editorial_function_analysis_ref": "A-1", "locators": [{"analysis_id": "A-1", "locator": "Escena 3"}],
            "pending_items": [], "confidence": "HIGH", "work_use_sufficiency": {"intended_use": "NARRATIVE_MATERIAL", "status": "IR7_FIDELITY_AUDIT_REQUIRED"},
            "independent_fidelity_audit": {"audit_reference": None, "dependency": "FUNCTIONAL_DECISION_REQUIRED"}, "created_at": "2026-08-07T10:00:00Z"
        }

    def _valid_claims_ledger(self):
        return {"ledger_id": "CL-001", "script_version": "1.0.0", "claims": [{"claim_id": "CLAIM-001", "script_location": "B1", "claim_text": "Claim", "claim_type": "FACT", "source_refs": ["S1"], "verification_status": "VERIFIED", "materiality": {"is_material": True, "activation_criteria": ["THESIS_DEPENDENCY"], "non_trigger_examples": ["Ejemplo"], "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"], "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_ref": "DEC-1"}}]}

    def _valid_narrative_analyses(self):
        return [{
            "analysis_id": "A-1", "artifact_version": "1.0.0", "episode_id": "EP-1", "research_id": "R-1", "evidence_report_id": "E-1", "semantic_audit_id": "S-1", "material_id": "M-1", "material_checksum": "a" * 64,
            "inherited_constraint_ids": [], "findings": [{"finding_id": "F-1", "claim_type": "INTERPRETATION", "statement": "Lectura.", "narrative_evidence_refs": ["NE-1"], "source_refs": ["S-1"], "human_dimension": "BELIEF", "causal_relation": "Relación.", "confidence": "HIGH"}],
            "rival_interpretations": ["Rival."], "rival_interpretation_status": "PRESENT", "rival_interpretation_justification": None, "limitations": ["Límite."], "limits_status": "PRESENT", "limits_justification": None,
            "demonstrates": "Demuestra.", "does_not_establish": "No demuestra.", "material_function_candidate": "Complicación", "specific_scene_or_passage": "Escena 3", "observable_decision_or_action": "Decisión.", "conflict": "Conflicto.", "consequence": "Consecuencia.", "main_interpretation": "Interpretación.", "supporting_evidence": ["F-1"], "interpretive_limit": "Límite.", "relationship_to_provisional_thesis": "Relación.", "potential_contribution_to_progression": "Aporta.", "created_at": "2026-08-07T10:00:00Z"
        }]

    def test_work_research_dossier_validates(self):
        self.assertEqual(validate_work_research_dossier(self._valid_work_dossier(), self._valid_claims_ledger(), self._valid_narrative_analyses()), [])

    def test_work_research_dossier_rejects_missing_version(self):
        dossier = self._valid_work_dossier()
        del dossier["dossier_version"]
        self.assertTrue(any("dossier_version" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))

    def test_work_research_dossier_rejects_analysis_checksum_mismatch(self):
        dossier = self._valid_work_dossier()
        dossier["analysis_references"][0]["artifact_checksum"] = "0" * 64
        assert any("checksum no coincide" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses()))

    def test_work_research_dossier_rejects_analysis_version_mismatch(self):
        dossier = self._valid_work_dossier()
        dossier["analysis_references"][0]["artifact_version"] = "9.9.9"
        assert any("version no coincide" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses()))

    def test_work_research_dossier_rejects_claims_ledger_checksum_mismatch(self):
        dossier = self._valid_work_dossier()
        dossier["claim_dispositions"]["claims_ledger_checksum"] = "0" * 64
        assert any("checksum de ClaimsLedger" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses()))

    def test_work_research_dossier_rejects_unknown_claim(self):
        dossier = self._valid_work_dossier()
        dossier["claim_dispositions"]["candidate_allowed_claim_ids"] = ["UNKNOWN"]
        self.assertTrue(any("claim inexistente" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))

    def test_work_research_dossier_rejects_incompatible_claim_states(self):
        dossier = self._valid_work_dossier()
        dossier["claim_dispositions"]["candidate_blocked_claim_ids"] = ["CLAIM-001"]
        self.assertTrue(any("no permite claims" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))

    def test_work_research_dossier_rejects_unknown_analysis(self):
        dossier = self._valid_work_dossier()
        dossier["analysis_references"] = [{"analysis_id": "UNKNOWN", "material_id": "M-1"}]
        self.assertTrue(any("análisis inexistente" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))

    def test_work_research_dossier_rejects_undeclared_relation_analysis(self):
        dossier = self._valid_work_dossier()
        dossier["question_and_thesis_relation"]["main_interpretation_analysis_ref"] = "A-2"
        analyses = self._valid_narrative_analyses() + [{**self._valid_narrative_analyses()[0], "analysis_id": "A-2"}]
        self.assertTrue(any("main_interpretation_analysis_ref referencia análisis no declarado" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), analyses)))

    def test_work_research_dossier_rejects_analysis_from_another_work(self):
        dossier = self._valid_work_dossier()
        dossier["work"]["material_id"] = "M-2"
        self.assertTrue(any("no pertenece a la obra" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))

    def test_work_research_dossier_rejects_malformed_work_without_crashing(self):
        dossier = self._valid_work_dossier()
        dossier["work"] = "invalid"
        violations = validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())
        self.assertTrue(any("not of type 'object'" in violation for violation in violations))

    def test_work_research_dossier_rejects_ledger_mismatch(self):
        dossier = self._valid_work_dossier()
        dossier["claim_dispositions"]["claims_ledger_id"] = "OTHER"
        self.assertTrue(any("distinto del ledger" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))

    def test_work_research_dossier_rejects_claimed_fidelity_audit(self):
        dossier = self._valid_work_dossier()
        dossier["independent_fidelity_audit"]["audit_reference"] = "FID-001"
        self.assertTrue(any("audit_reference" in violation for violation in validate_work_research_dossier(dossier, self._valid_claims_ledger(), self._valid_narrative_analyses())))


if __name__ == "__main__":
    unittest.main()
