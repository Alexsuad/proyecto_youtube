"""Hybrid route profiles kept separate from functional agent roles."""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema

PROFILE_PATH = Path("config/agent_execution_profiles.json")
UNAVAILABLE = "UNAVAILABLE_FROM_PROVIDER"


@dataclass(frozen=True)
class ResolvedExecutionRoute:
    role_id: str
    execution_route: str
    executor: str
    provider: str
    model: str
    status: str
    timeout_seconds: int = 30
    max_retries: int = 0
    cost_policy: str = "UNSPECIFIED"
    provider_config_ref: str | None = None
    blocking_reason: str | None = None


def load_execution_profiles(path: Path | None = None) -> dict[str, Any]:
    target = path or PROFILE_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    violations = validate_against_schema(data, "agent_execution_profiles")
    if violations:
        raise ValueError("AgentExecutionProfiles invalido: " + "; ".join(violations))
    return data


def inventory_executor(executor_id: str, profiles: dict[str, Any] | None = None) -> str:
    profiles = profiles or load_execution_profiles()
    executor = profiles["executors"].get(executor_id)
    if executor is None:
        return "UNAVAILABLE"
    if executor["kind"] == "NATIVE_PROVIDER":
        return "READY"
    if not shutil.which(executor.get("command", "")):
        return "UNAVAILABLE"
    return "HANDOFF_ONLY" if executor.get("requires_actual_provider_and_model", False) else executor["status"]


def resolve_execution_route(role_id: str, execution_route: str, *, profiles: dict[str, Any] | None = None, environ: dict[str, str] | None = None) -> ResolvedExecutionRoute:
    profiles = profiles or load_execution_profiles()
    environ = environ or os.environ
    profile = next((item for item in profiles["agent_profiles"] if item["role_id"] == role_id), None)
    if profile is None:
        raise ValueError(f"role no tiene perfil hibrido: {role_id}")
    route = next((item for item in profile["routes"] if item["execution_route"] == execution_route), None)
    if route is None:
        raise ValueError(f"ruta no permitida para {role_id}: {execution_route}")
    provider_config = profiles.get("providers", {}).get(route.get("provider_config_ref", ""), {})
    timeout_seconds = int(route.get("timeout_seconds", provider_config.get("timeout_seconds", 30)))
    max_retries = int(route.get("max_retries", provider_config.get("max_retries", 0)))
    cost_policy = str(route.get("cost_policy", provider_config.get("cost_policy", "UNSPECIFIED")))
    executor_status = inventory_executor(route["executor"], profiles)
    model = environ.get(route["model_env"], "").strip()
    provider_config_ref = route.get("provider_config_ref")
    if executor_status == "UNAVAILABLE":
        return ResolvedExecutionRoute(role_id, execution_route, route["executor"], route["provider"], UNAVAILABLE, "EXECUTOR_UNAVAILABLE", timeout_seconds, max_retries, cost_policy, provider_config_ref, "EXECUTOR_UNAVAILABLE")
    if route["provider"] == "deepseek" and not environ.get("DEEPSEEK_API_KEY", "").strip():
        return ResolvedExecutionRoute(role_id, execution_route, route["executor"], "deepseek", model or UNAVAILABLE, "CREDENTIALS_MISSING", timeout_seconds, max_retries, cost_policy, provider_config_ref, "CREDENTIALS_MISSING")
    if not model:
        return ResolvedExecutionRoute(role_id, execution_route, route["executor"], route["provider"], UNAVAILABLE, "MODEL_UNAVAILABLE", timeout_seconds, max_retries, cost_policy, provider_config_ref, "MODEL_UNAVAILABLE")
    if route["provider"] == "EXTERNAL_REPORTED":
        return ResolvedExecutionRoute(role_id, execution_route, route["executor"], UNAVAILABLE, UNAVAILABLE, "HANDOFF_ONLY", timeout_seconds, max_retries, cost_policy, provider_config_ref, "ACTUAL_PROVIDER_AND_MODEL_REQUIRED")
    return ResolvedExecutionRoute(role_id, execution_route, route["executor"], route["provider"], model, "READY", timeout_seconds, max_retries, cost_policy, provider_config_ref)


class AgentRuntimePort:
    """Common entry point for configurable provider and executor routes."""

    def __init__(self, profiles_path: Path | None = None) -> None:
        self._profiles_path = profiles_path

    def resolve(self, role_id: str, execution_route: str) -> ResolvedExecutionRoute:
        return resolve_execution_route(role_id, execution_route, profiles=load_execution_profiles(self._profiles_path))