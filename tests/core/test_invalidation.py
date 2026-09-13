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

    def test_selective_invalidation_with_real_dependency_consumer(self):
        import json
        import tempfile
        from pathlib import Path
        from src.core.editorial_profile_registry import EditorialProfileRegistry
        from src.core.invalidation import InvalidationEngine

        with tempfile.TemporaryDirectory() as td:
            rp = Path(td) / "registry.json"
            rp.write_text(json.dumps({"registry_version": "1.0.0", "active_profile_key": "mas_alla_del_guion@1.2.2", "profiles": {}, "dependencies": {}}), encoding="utf-8")
            registry = EditorialProfileRegistry(rp)
            engine = InvalidationEngine(registry=registry)
            profile_key = "mas_alla_del_guion@1.2.2"
            # Real consumer: profile -> SCRIPT and RESEARCH artifacts
            engine.register_dependency(profile_key, "SCRIPT-PLAN013-001")
            engine.register_dependency(profile_key, "RESEARCH-PACK-001")
            # NO_IMPACT must not invalidate
            self.assertEqual(engine.invalidate_profile_change(profile_key, "1.2.2", "NO_IMPACT", "CHANNEL_INTELLIGENCE"), [])
            self.assertEqual(len(engine.invalidation_log), 0)
            # PARTIAL with allowed subset must invalidate only that subset
            partial = engine.invalidate_profile_change(profile_key, "1.2.2", "PARTIAL_INVALIDATION", "CHANNEL_INTELLIGENCE", affected=["SCRIPT-PLAN013-001", "UNKNOWN-ARTIFACT"])
            self.assertEqual(len(partial), 1)
            self.assertEqual(partial[0].target_artifact_id, "SCRIPT-PLAN013-001")
            # PARTIAL with empty affected must produce no invalidation
            engine2 = InvalidationEngine(registry=registry)
            engine2.register_dependency(profile_key, "SCRIPT-PLAN013-001")
            self.assertEqual(engine2.invalidate_profile_change(profile_key, "1.2.2", "PARTIAL_INVALIDATION", "CHANNEL_INTELLIGENCE", affected=[]), [])
            # FULL must invalidate profile and all dependents
            engine3 = InvalidationEngine(registry=registry)
            engine3.register_dependency(profile_key, "SCRIPT-PLAN013-001")
            engine3.register_dependency(profile_key, "RESEARCH-PACK-001")
            full = engine3.invalidate_profile_change(profile_key, "1.2.2", "FULL_INVALIDATION", "CHANNEL_INTELLIGENCE")
            target_ids = {r.target_artifact_id for r in full}
            self.assertIn(profile_key, target_ids)
            self.assertIn("SCRIPT-PLAN013-001", target_ids)
            self.assertIn("RESEARCH-PACK-001", target_ids)
            # Registry persistence of dependencies
            self.assertIn("SCRIPT-PLAN013-001", registry.dependencies_for(profile_key))

    def test_profile_change_classification_is_strict(self):
        from src.core.invalidation import InvalidationEngine
        engine = InvalidationEngine()
        self.assertEqual(engine.classify_profile_change("NO_IMPACT"), "NO_IMPACT")
        self.assertEqual(engine.classify_profile_change("PARTIAL_INVALIDATION"), "PARTIAL_INVALIDATION")
        self.assertEqual(engine.classify_profile_change("FULL_INVALIDATION"), "FULL_INVALIDATION")
        with self.assertRaises(ValueError):
            engine.classify_profile_change("INVALID")


if __name__ == "__main__":
    unittest.main()
