"""Managed RUNNER executor backed by the currently selected OpenCode model."""
from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from typing import Any

from src.ai.contracts import ExecutionRequest


class AgentExecutorProvider:
    name = "agent_executor"

    def execute(self, request: ExecutionRequest) -> tuple[Any, dict[str, Any]]:
        if not request.config.get("smoke_test", False):
            return self._execute_opencode(request)
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

    def _execute_opencode(self, request: ExecutionRequest) -> tuple[Any, dict[str, Any]]:
        if request.model not in (None, "", "UNAVAILABLE_FROM_EXECUTOR") or request.config.get("model_override"):
            raise PermissionError("AGENT_HARNESS_DOES_NOT_SELECT_MODEL")
        prompt = str(request.config.get("prompt") or "").strip()
        if not prompt:
            raise ValueError("AGENT_HARNESS_PROMPT_REQUIRED")
        command = shutil.which("opencode")
        if not command:
            raise RuntimeError("EXECUTOR_UNAVAILABLE")
        timeout = request.timeout
        try:
            completed = subprocess.run(
                [command, "run", "--format", "json"],
                capture_output=True,
                text=True,
                input=prompt,
                timeout=timeout,
                cwd=request.config.get("isolated_workdir"),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("TIMEOUT") from exc
        except OSError as exc:
            raise RuntimeError("PROVIDER_UNAVAILABLE") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[:1000]
            raise RuntimeError(f"MODEL_INVOCATION_FAILED: exit={completed.returncode} {detail}".strip())
        output = self._parse_json_events(completed.stdout or "")
        return output, {
            "provider_kind": "REAL",
            "provider_or_adapter": self.name,
            "model_or_evaluator": "CURRENT_OPENCODE_MODEL",
            "actual_executor": "opencode",
            "actual_provider": "MANAGED_BY_EXECUTOR",
            "actual_model": "CURRENT_OPENCODE_MODEL",
            "execution_route": "agent_harness",
            "execution_profile": None,
            "opencode_format": "json",
            "exit_code": completed.returncode,
        }

    @staticmethod
    def _parse_json_events(stdout: str) -> Any:
        events: list[dict[str, Any]] = []
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
        if not events:
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise ValueError("MODEL_OUTPUT_INVALID: no JSON event") from exc
            if not isinstance(payload, (dict, list)):
                raise ValueError("MODEL_OUTPUT_INVALID: cognitive payload must be an object or list")
            return payload
        text_parts: list[str] = []
        for event in events:
            part = event.get("part") or event.get("properties", {}).get("part")
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
            elif isinstance(event.get("text"), str):
                text_parts.append(event["text"])
            else:
                text_parts.extend(AgentExecutorProvider._nested_text_values(event))
        raw = "".join(text_parts).strip()
        if raw.startswith("```") and raw.endswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            preview = json.dumps(events[-1], ensure_ascii=False)[:500]
            raise ValueError(f"MODEL_OUTPUT_INVALID: cognitive response is not JSON; event={preview}") from exc
        if not isinstance(payload, (dict, list)):
            raise ValueError("MODEL_OUTPUT_INVALID: cognitive payload must be an object or list")
        return payload

    @staticmethod
    def _nested_text_values(value: object) -> list[str]:
        if isinstance(value, dict):
            result: list[str] = []
            for key, child in value.items():
                if key == "text" and isinstance(child, str):
                    result.append(child)
                else:
                    result.extend(AgentExecutorProvider._nested_text_values(child))
            return result
        if isinstance(value, list):
            result: list[str] = []
            for child in value:
                result.extend(AgentExecutorProvider._nested_text_values(child))
            return result
        return []
