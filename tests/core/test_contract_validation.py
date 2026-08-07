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
            "claims_by_criticality": {"C-001": "CENTRAL"},
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
                "status_per_claim": [{"claim_id": "C-001", "semantic_level": "PLAUSIBLE", "intended_use": "CENTRAL_CLAIM_SUPPORT"}],
                "ir4_dependency": "DEFERRED_TO_R1_M6",
            },
        }
        self.assertEqual(validate_research_pack(pack), [])

    def test_research_pack_rejects_unknown_claim_reference(self):
        pack = {**VALID_RESEARCH_PACK, "claims_by_criticality": {"UNKNOWN": "CENTRAL"}}
        violations = validate_research_pack(pack)
        self.assertTrue(any("claims_by_criticality referencia claim no declarada" in v for v in violations))

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


if __name__ == "__main__":
    unittest.main()
