"""
Pruebas Unitarias para GateResult y Exit Codes
"""

import unittest
from src.core.status import GateStatus
from src.core.gate_result import GateResult, EXIT_CODE_MAP
from tests.fixtures.synthetic_contracts import (
    VALID_GATE_RESULT_PASS,
    INVALID_GATE_RESULT_CONTRADICTION,
)


class TestGateResultModule(unittest.TestCase):

    def test_gate_result_pass_exit_code(self):
        gr = GateResult.from_dict(VALID_GATE_RESULT_PASS)
        self.assertEqual(gr.status, GateStatus.PASS)
        self.assertEqual(gr.exit_code, 0)

    def test_gate_result_exit_code_mapping(self):
        self.assertEqual(EXIT_CODE_MAP[GateStatus.PASS], 0)
        self.assertEqual(EXIT_CODE_MAP[GateStatus.WARN], 0)
        self.assertEqual(EXIT_CODE_MAP[GateStatus.FAIL], 1)
        self.assertEqual(EXIT_CODE_MAP[GateStatus.BLOCKED], 2)

    def test_contradiction_raises_error(self):
        # Si hay violaciones pero el estado dice PASS, debe lanzar error de contradicción
        with self.assertRaises(ValueError) as ctx:
            GateResult.from_dict(INVALID_GATE_RESULT_CONTRADICTION)
        self.assertIn("Contradiccion detectada", str(ctx.exception))

    def test_unknown_status_raises_error(self):
        data = {**VALID_GATE_RESULT_PASS, "status": "UNKNOWN_STATUS"}
        with self.assertRaises(ValueError):
            GateResult.from_dict(data)


if __name__ == "__main__":
    unittest.main()
