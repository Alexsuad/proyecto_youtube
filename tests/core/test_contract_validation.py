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


if __name__ == "__main__":
    unittest.main()
