"""Controlled executor smoke path; integrated execution requires a declared protocol."""
from __future__ import annotations

import shutil
import subprocess
import uuid
from typing import Any

from src.ai.contracts import ExecutionRequest


class AgentExecutorProvider:
    name = "agent_executor"

    def execute(self, request: ExecutionRequest) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        if not request.config.get("smoke_test", False):
            raise PermissionError(
                "AGENT_HARNESS_SMOKE_ONLY_UNTIL_R6_B_RETRY: "
                "INTEGRATED_EXECUTOR_PROTOCOL_REQUIRED"
            )
        executor = str(request.executor or request.config.get("selected_executor") or "").strip()
        if not executor:
            raise RuntimeError("EXECUTOR_UNAVAILABLE")
        command = shutil.which(executor) or shutil.which(executor.replace("_cli", ""))
        if not command:
            raise RuntimeError("EXECUTOR_UNAVAILABLE")
        probe_args = request.config.get("probe_args") or ["--help"]
        try:
            completed = subprocess.run(
                [command, *probe_args],
                capture_output=True,
                text=True,
                timeout=request.timeout,
                cwd=request.config.get("isolated_workdir"),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("TIMEOUT") from exc
        except OSError as exc:
            raise RuntimeError("PROVIDER_UNAVAILABLE") from exc

        actual_provider = str(request.config.get("actual_provider") or "MANAGED_BY_EXECUTOR")
        actual_model = str(request.config.get("actual_model") or "UNAVAILABLE_FROM_EXECUTOR")
        reasoning_effort = request.reasoning_effort or request.config.get("reasoning_effort")
        payload = {
            "smoke_id": f"SMOKE-{uuid.uuid4().hex}",
            "role_id": request.role or request.capability_id,
            "execution_profile": str(request.execution_profile or request.config.get("execution_profile") or "unknown_profile"),
            "execution_route": str(request.execution_route or request.config.get("execution_route") or "agent_harness"),
            "selected_executor": executor,
            "selected_provider": actual_provider,
            "selected_model": str(request.model or actual_model),
            "actual_executor": executor,
            "actual_provider": actual_provider,
            "actual_model": actual_model,
            "reasoning_effort": reasoning_effort,
            "result": "SUCCEEDED" if completed.returncode == 0 else "BLOCKED",
            "decision": "SMOKE_PASS" if completed.returncode == 0 else "SMOKE_NONZERO_EXIT",
            "stdout_preview": (completed.stdout or "")[:4000],
            "stderr_preview": (completed.stderr or "")[:4000],
            "exit_code": completed.returncode,
            "notes": ["executor identity verified", "run isolation requested", "structured smoke output generated"],
        }
        usage = {
            "provider_or_adapter": executor,
            "model_or_evaluator": actual_model,
            "actual_executor": executor,
            "actual_provider": actual_provider,
            "actual_model": actual_model,
            "reasoning_effort": reasoning_effort,
            "exit_code": completed.returncode,
            "stdout_preview": payload["stdout_preview"],
            "stderr_preview": payload["stderr_preview"],
        }
        return payload, usage
