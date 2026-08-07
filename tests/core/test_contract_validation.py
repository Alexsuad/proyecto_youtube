"""
Pruebas Unitarias para la Validación Determinista de Contratos (contract_validation.py)
"""

import unittest
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

    def test_research_pack_phenomenon_extensions_validate(self):
        pack = {
            **VALID_RESEARCH_PACK,
            "research_pack_kind": "PHENOMENON",
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
        return {
            "dossier_id": "WRD-001", "dossier_version": "1.0.0", "episode_id": "EP-1", "research_id": "R-1", "evidence_report_id": "E-1",
            "work": {"material_id": "M-1", "title": "Obra", "creator": "Autor", "consulted_representations": [{"representation_kind": "ORIGINAL_WORK", "edition_or_version": "Edición 1", "consulted_locator": "Capítulo 1"}]},
            "dossier_stage": "RESEARCH_IN_PROGRESS", "analysis_references": [{"analysis_id": "A-1", "material_id": "M-1"}],
            "question_and_thesis_relation": {"central_question_ref": "EP-1.pregunta_central", "provisional_thesis_ref": "TP-1", "demonstrates_analysis_ref": "A-1", "does_not_establish_analysis_ref": "A-1", "main_interpretation_analysis_ref": "A-1", "rival_interpretation_analysis_refs": ["A-1"]},
            "claim_dispositions": {"claims_ledger_id": "CL-001", "authority_status": "REPRESENTATION_ONLY_IR4_PENDING", "candidate_allowed_claim_ids": ["CLAIM-001"], "candidate_limited_claim_ids": [], "candidate_blocked_claim_ids": []},
            "overinterpretation_risk": {"level": "MEDIUM", "rationale": "Riesgo contenido."}, "candidate_editorial_function_analysis_ref": "A-1", "locators": [{"analysis_id": "A-1", "locator": "Escena 3"}],
            "pending_items": [], "confidence": "HIGH", "work_use_sufficiency": {"intended_use": "NARRATIVE_MATERIAL", "status": "IR7_FIDELITY_AUDIT_REQUIRED"},
            "independent_fidelity_audit": {"audit_reference": None, "dependency": "DEFERRED_TO_R1_M10_R1_M11"}, "created_at": "2026-08-07T10:00:00Z"
        }

    def _valid_claims_ledger(self):
        return {"ledger_id": "CL-001", "script_version": "1.0.0", "claims": [{"claim_id": "CLAIM-001", "script_location": "B1", "claim_text": "Claim", "claim_type": "FACT", "source_refs": ["S1"], "verification_status": "VERIFIED"}]}

    def _valid_narrative_analyses(self):
        return [{
            "analysis_id": "A-1", "episode_id": "EP-1", "research_id": "R-1", "evidence_report_id": "E-1", "semantic_audit_id": "S-1", "material_id": "M-1", "material_checksum": "a" * 64,
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
