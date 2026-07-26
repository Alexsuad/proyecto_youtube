"""Mock deliberadamente no elegible para adjudicación editorial real."""
from __future__ import annotations

from typing import Any

from src.ai.contracts import ExecutionRequest


class MockProvider:
    name = "mock"

    def execute(self, request: ExecutionRequest) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        if request.mock_output is None:
            raise ValueError("mock requiere mock_output explícito; no simula una evaluación editorial")
        return request.mock_output, {"synthetic": True, "provider_or_adapter": self.name, "model_or_evaluator": "structural-test-double"}
