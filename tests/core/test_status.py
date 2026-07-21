"""
Pruebas Unitarias para el Módulo de Estados Canónicos status.py
"""

import unittest
from src.core.status import (
    ArtifactStatus,
    GateStatus,
    ApprovalType,
    ApprovalDecision,
    is_valid_artifact_status,
    is_valid_gate_status,
    is_valid_approver_identity,
    validate_status_transition,
)


class TestStatusModule(unittest.TestCase):

    def test_valid_artifact_status(self):
        self.assertTrue(is_valid_artifact_status("EDITORIAL_SCRIPT_APPROVED"))
        self.assertTrue(is_valid_artifact_status("YOUTUBE_PRODUCTION_READY"))
        self.assertTrue(is_valid_artifact_status("YOUTUBE_READY"))
        self.assertFalse(is_valid_artifact_status("ESTADO_INVENTADO"))

    def test_valid_gate_status(self):
        self.assertTrue(is_valid_gate_status("PASS"))
        self.assertTrue(is_valid_gate_status("WARN"))
        self.assertTrue(is_valid_gate_status("FAIL"))
        self.assertTrue(is_valid_gate_status("BLOCKED"))
        self.assertFalse(is_valid_gate_status("SUCCESS"))

    def test_approver_identity_validation(self):
        # Válidas
        self.assertTrue(is_valid_approver_identity("editor_jefe_01"))
        self.assertTrue(is_valid_approver_identity("lead_produccion_nalex"))
        
        # Inválidas / ambiguas
        self.assertFalse(is_valid_approver_identity("aprobado"))
        self.assertFalse(is_valid_approver_identity("usuario"))
        self.assertFalse(is_valid_approver_identity("equipo"))
        self.assertFalse(is_valid_approver_identity("admin"))
        self.assertFalse(is_valid_approver_identity(""))
        self.assertFalse(is_valid_approver_identity(None))

    def test_status_transitions(self):
        # HumanProductionApproval NO puede declarar YOUTUBE_READY
        self.assertFalse(
            validate_status_transition(
                current_status=ArtifactStatus.DRAFT,
                target_status=ArtifactStatus.YOUTUBE_READY,
                approval_type=ApprovalType.HUMAN_PRODUCTION_APPROVAL,
                approval_decision=ApprovalDecision.APPROVED_FOR_PRODUCTION,
            )
        )

        # YOUTUBE_READY requiere HumanPublicationApproval y activos audiovisuales finales
        self.assertTrue(
            validate_status_transition(
                current_status=ArtifactStatus.YOUTUBE_PRODUCTION_READY,
                target_status=ArtifactStatus.YOUTUBE_READY,
                approval_type=ApprovalType.HUMAN_PUBLICATION_APPROVAL,
                approval_decision=ApprovalDecision.APPROVED_FOR_PUBLICATION,
                has_final_audiovisual_assets=True,
            )
        )

        # Sin activos finales falla la transición a YOUTUBE_READY
        self.assertFalse(
            validate_status_transition(
                current_status=ArtifactStatus.YOUTUBE_PRODUCTION_READY,
                target_status=ArtifactStatus.YOUTUBE_READY,
                approval_type=ApprovalType.HUMAN_PUBLICATION_APPROVAL,
                approval_decision=ApprovalDecision.APPROVED_FOR_PUBLICATION,
                has_final_audiovisual_assets=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
