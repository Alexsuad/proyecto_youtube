"""
Pruebas Unitarias para VersionManifest y Calculation of Checksums
"""

import unittest
from src.core.version_manifest import VersionManifest, compute_checksum


class TestVersionManifest(unittest.TestCase):

    def test_compute_checksum_deterministic(self):
        data = {"title": "Guion 01", "version": "1.0.0"}
        c1 = compute_checksum(data)
        c2 = compute_checksum(data)
        self.assertEqual(c1, c2)
        self.assertEqual(len(c1), 64)

    def test_version_registration_and_overwrite_prevention(self):
        vm = VersionManifest("SCRIPT-001")
        entry = vm.register_version("1.0.0", "contenido original")
        self.assertEqual(entry.version, "1.0.0")

        # Mismo contenido / checksum -> Aceptado
        entry2 = vm.register_version("1.0.0", "contenido original")
        self.assertEqual(entry.checksum, entry2.checksum)

        # Contenido distinto -> Error de sobrescritura silenciosa
        with self.assertRaises(ValueError) as ctx:
            vm.register_version("1.0.0", "contenido modificado de forma silenciosa")
        self.assertIn("Sobrescritura silenciosa rechazada", str(ctx.exception))

    def test_empty_version_rejected(self):
        vm = VersionManifest("SCRIPT-001")
        with self.assertRaises(ValueError):
            vm.register_version("   ", "contenido")


if __name__ == "__main__":
    unittest.main()
