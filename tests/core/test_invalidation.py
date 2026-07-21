"""
Pruebas Unitarias para el Motor de Invalidación (invalidation.py)
"""

import unittest
from src.core.invalidation import InvalidationEngine
from src.core.version_manifest import compute_checksum


class TestInvalidationModule(unittest.TestCase):

    def setUp(self):
        self.engine = InvalidationEngine()

    def test_approval_validity_by_checksum(self):
        original_content = {"script": "Texto original del guion."}
        approved_checksum = compute_checksum(original_content)

        # Si el contenido no cambia -> Aprobación válida
        self.assertTrue(self.engine.check_approval_validity(approved_checksum, original_content))

        # Si el contenido cambia -> Aprobación inválida
        modified_content = {"script": "Texto modificado del guion."}
        self.assertFalse(self.engine.check_approval_validity(approved_checksum, modified_content))

    def test_candidate_learning_cannot_modify_profile(self):
        # CANDIDATE no puede modificar perfil activo
        self.assertFalse(self.engine.can_candidate_learning_modify_profile("CANDIDATE"))
        self.assertFalse(self.engine.can_candidate_learning_modify_profile("candidate"))

        # APPROVED o INTEGRATED sí pueden
        self.assertTrue(self.engine.can_candidate_learning_modify_profile("APPROVED"))
        self.assertTrue(self.engine.can_candidate_learning_modify_profile("INTEGRATED"))

    def test_invalidation_record_logging(self):
        record = self.engine.invalidate_artifact(
            artifact_id="SCRIPT-01",
            version="1.0.0",
            reason="Tesis modificada en la fase de estructuracion.",
            by_role="EDITORIAL_LEAD",
            dependents=["SHORTS-01", "PACKAGING-01"],
        )
        self.assertEqual(record.target_artifact_id, "SCRIPT-01")
        # Con propagación recursiva, se generan 3 registros (SCRIPT-01, SHORTS-01 y PACKAGING-01)
        self.assertEqual(len(self.engine.invalidation_log), 3)
        self.assertIn("SHORTS-01", record.affected_dependent_artifacts)

    def test_recursive_invalidation_and_cycle_prevention(self):
        # Configurar dependencias complejas con ciclos
        # A -> B -> C -> A
        self.engine.register_dependency("A", "B")
        self.engine.register_dependency("B", "C")
        self.engine.register_dependency("C", "A")

        records = self.engine.invalidate_artifact(
            artifact_id="A",
            version="1.1.0",
            reason="Modificacion inicial de A",
            by_role="EDITORIAL_LEAD",
        )

        # Debería registrar A, B y C exactamente una vez sin bucles infinitos
        self.assertEqual(len(self.engine.invalidation_log), 3)
        
        target_ids = {r.target_artifact_id for r in self.engine.invalidation_log}
        self.assertEqual(target_ids, {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
