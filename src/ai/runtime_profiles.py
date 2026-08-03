"""Owner-selected per-run resolution for local, API, and agent harness executions."""
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
UNAVAILABLE_FROM_EXECUTOR = "UNAVAILABLE_FROM_EXECUTOR"
MANAGED_BY_EXECUTOR = "MANAGED_BY_EXECUTOR"
READY = "READY"
NON_EXECUTABLE_PROFILES = {"NONE_SELECTED"}


@dataclass(frozen=True)
class ResolvedExecutionRoute:
    role_id: str
    execution_route: str
    execution_profile: str
    route_type: str
    executor: str
    provider: str
    provider_adapter: str
    model: str
    status: str
    timeout_seconds: int = 30
    max_retries: int = 0
    temperature: float | None = None
    max_tokens: int | None = None
    budget_limit: float | int | None = None
    paid_cost_approved: bool = False
    cost_policy: str = "UNSPECIFIED"
    provider_config_ref: str | None = None
    blocking_reason: str | None = None
    error_type: str | None = None
    api_base_env: str | None = None
    api_key_env: str | None = None
    model_env: str | None = None
    provider_label: str | None = None
    executor_accepts_model_override: bool = False
    model_selection: str = "USER_SELECTED"

    def as_run_configuration(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "execution_route": self.execution_route,
            "execution_profile": self.execution_profile,
            "executor_override": self.executor,
            "provider_override": None if self.provider == MANAGED_BY_EXECUTOR else self.provider,
            "model_override": None if self.model == UNAVAILABLE_FROM_EXECUTOR else self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "budget_limit": self.budget_limit,
            "paid_cost_approved": self.paid_cost_approved,
        }


def load_execution_profiles(path: Path | None = None) -> dict[str, Any]:
    target = path or PROFILE_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    violations = validate_against_schema(data, "agent_execution_profiles")
    if violations:
        raise ValueError("AgentExecutionProfiles invalido: " + "; ".join(violations))
    return data


def validate_run_configuration(run_configuration: dict[str, Any]) -> list[str]:
    return validate_against_schema(run_configuration, "run_configuration")


def inventory_executor(executor_id: str, profiles: dict[str, Any] | None = None) -> str:
    profiles = profiles or load_execution_profiles()
    executor = profiles["executors"].get(executor_id)
    if executor is None:
        return "UNAVAILABLE"
    if executor["kind"] == "NATIVE_PROVIDER":
        return str(executor.get("status", READY))
    command = str(executor.get("command") or "").strip()
    if not command or not shutil.which(command):
        return "UNAVAILABLE"
    return str(executor.get("status", "UNAVAILABLE"))


def _pick(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _int_or_none(value: Any) -> int | None:
    return None if value is None else int(value)


def _float_or_none(value: Any) -> float | None:
    return None if value is None else float(value)


def _build_blocked(
    *,
    role_id: str,
    execution_route: str,
    execution_profile: str,
    route_type: str,
    executor: str,
    provider: str,
    provider_adapter: str,
    model: str,
    timeout_seconds: int,
    max_retries: int,
    temperature: float | None,
    max_tokens: int | None,
    budget_limit: float | int | None,
    paid_cost_approved: bool,
    cost_policy: str,
    provider_config_ref: str | None,
    blocking_reason: str,
    api_base_env: str | None = None,
    api_key_env: str | None = None,
    model_env: str | None = None,
    provider_label: str | None = None,
    executor_accepts_model_override: bool = False,
    model_selection: str = "USER_SELECTED",
) -> ResolvedExecutionRoute:
    return ResolvedExecutionRoute(
        role_id=role_id,
        execution_route=execution_route,
        execution_profile=execution_profile,
        route_type=route_type,
        executor=executor,
        provider=provider,
        provider_adapter=provider_adapter,
        model=model,
        status=blocking_reason,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        temperature=temperature,
        max_tokens=max_tokens,
        budget_limit=budget_limit,
        paid_cost_approved=paid_cost_approved,
        cost_policy=cost_policy,
        provider_config_ref=provider_config_ref,
        blocking_reason=blocking_reason,
        error_type=blocking_reason,
        api_base_env=api_base_env,
        api_key_env=api_key_env,
        model_env=model_env,
        provider_label=provider_label,
        executor_accepts_model_override=executor_accepts_model_override,
        model_selection=model_selection,
    )


def _resolve_provider_identity(provider_id: str, provider_entry: dict[str, Any] | None) -> tuple[str, str]:
    if provider_id == MANAGED_BY_EXECUTOR:
        return MANAGED_BY_EXECUTOR, "agent_executor"
    provider_entry = provider_entry or {}
    adapter = str(provider_entry.get("adapter") or provider_id)
    return provider_id, adapter


def allowed_profiles_for_role(role_id: str, *, profiles: dict[str, Any] | None = None) -> list[str]:
    profiles = profiles or load_execution_profiles()
    role_defaults = profiles.get("role_defaults", {}).get(role_id)
    if not role_defaults:
        raise ValueError(f"role no tiene defaults de seleccion: {role_id}")
    return list(role_defaults.get("allowed_execution_profiles", []))


def resolve_run_configuration(
    run_configuration: dict[str, Any],
    *,
    profiles: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
) -> ResolvedExecutionRoute:
    profiles = profiles or load_execution_profiles()
    environ = environ or os.environ
    violations = validate_run_configuration(run_configuration)
    if violations:
        raise ValueError("RunConfiguration invalido: " + "; ".join(violations))

    role_id = str(run_configuration["role_id"])
    global_defaults = profiles.get("global_defaults", {})
    role_defaults = profiles.get("role_defaults", {}).get(role_id)
    if role_defaults is None:
        raise ValueError(f"role no tiene defaults de seleccion: {role_id}")

    execution_profile = str(
        _pick(
            run_configuration.get("execution_profile"),
            role_defaults.get("default_execution_profile"),
            global_defaults.get("execution_profile"),
        )
    )
    if execution_profile in NON_EXECUTABLE_PROFILES:
        return _build_blocked(
            role_id=role_id,
            execution_route=str(run_configuration.get("execution_route") or "local_model"),
            execution_profile=execution_profile,
            route_type="UNSELECTED",
            executor=str(run_configuration.get("executor_override") or "native_provider"),
            provider="",
            provider_adapter="",
            model=UNAVAILABLE,
            timeout_seconds=int(run_configuration.get("timeout_seconds", 30)),
            max_retries=int(run_configuration.get("max_retries", 0)),
            temperature=_float_or_none(run_configuration.get("temperature")),
            max_tokens=_int_or_none(run_configuration.get("max_tokens")),
            budget_limit=run_configuration.get("budget_limit"),
            paid_cost_approved=bool(run_configuration.get("paid_cost_approved", False)),
            cost_policy="BLOCKED_BY_CONFIGURATION",
            provider_config_ref=None,
            blocking_reason="BLOCKED_BY_CONFIGURATION",
        )
    profile = profiles.get("execution_profiles", {}).get(execution_profile)
    if profile is None:
        raise ValueError(f"execution_profile inexistente: {execution_profile}")
    if execution_profile not in set(role_defaults.get("allowed_execution_profiles", [])):
        raise ValueError(f"execution_profile no permitido para {role_id}: {execution_profile}")

    route_type = str(profile["route_type"])
    execution_route = str(
        _pick(
            run_configuration.get("execution_route"),
            profile.get("execution_route"),
            role_defaults.get("default_execution_route"),
            global_defaults.get("execution_route"),
        )
    )
    if execution_route != str(profile.get("execution_route")):
        raise ValueError(f"ruta incompatible con el perfil {execution_profile}: {execution_route}")

    executor = str(
        _pick(
            run_configuration.get("executor_override"),
            profile.get("executor"),
            role_defaults.get("default_executor"),
            global_defaults.get("default_executor"),
            "native_provider",
        )
    )
    executor_entry = profiles.get("executors", {}).get(executor)
    if executor_entry is None:
        raise ValueError(f"executor inexistente: {executor}")
    executor_kind = str(executor_entry.get("kind") or "")
    if route_type in {"LOCAL_MODEL_RUNTIME", "API_MODEL_RUNTIME"} and executor_kind != "NATIVE_PROVIDER":
        raise ValueError(f"override no permitido para {execution_profile}: executor {executor}")
    if route_type == "AGENT_HARNESS_RUNTIME" and executor_kind != "CONTROLLED_EXECUTOR":
        raise ValueError(f"executor incompatible con route_type {route_type}: {executor}")

    provider_override = run_configuration.get("provider_override")
    provider_ref = _pick(
        provider_override,
        profile.get("provider_config_ref"),
        profile.get("provider"),
        role_defaults.get("default_provider"),
        global_defaults.get("default_provider"),
    )
    provider_entry = profiles.get("providers", {}).get(str(provider_ref), {}) if provider_ref else {}

    if route_type == "AGENT_HARNESS_RUNTIME" and provider_override not in (None, "", MANAGED_BY_EXECUTOR):
        raise ValueError("provider incompatible con execution_route agent_harness")
    if route_type != "AGENT_HARNESS_RUNTIME":
        if not provider_ref or not provider_entry:
            raise ValueError(f"provider inexistente: {provider_ref}")
        if str(provider_entry.get("route_type")) != route_type:
            raise ValueError(f"provider incompatible con route_type {route_type}: {provider_ref}")

    provider, provider_adapter = _resolve_provider_identity(
        MANAGED_BY_EXECUTOR if route_type == "AGENT_HARNESS_RUNTIME" else str(provider_ref),
        None if route_type == "AGENT_HARNESS_RUNTIME" else provider_entry,
    )
    provider_config_ref = None if route_type == "AGENT_HARNESS_RUNTIME" else str(provider_ref)

    timeout_seconds = int(
        _pick(
            run_configuration.get("timeout_seconds"),
            profile.get("timeout_seconds"),
            role_defaults.get("timeout_seconds"),
            provider_entry.get("timeout_seconds"),
            global_defaults.get("timeout_seconds"),
            30,
        )
    )
    max_retries = int(
        _pick(
            run_configuration.get("max_retries"),
            profile.get("max_retries"),
            role_defaults.get("max_retries"),
            provider_entry.get("max_retries"),
            global_defaults.get("max_retries"),
            0,
        )
    )
    temperature = _float_or_none(
        _pick(
            run_configuration.get("temperature"),
            profile.get("temperature"),
            role_defaults.get("temperature"),
            global_defaults.get("temperature"),
        )
    )
    max_tokens = _int_or_none(
        _pick(
            run_configuration.get("max_tokens"),
            profile.get("max_tokens"),
            role_defaults.get("max_tokens"),
            global_defaults.get("max_tokens"),
        )
    )
    budget_limit = _pick(
        run_configuration.get("budget_limit"),
        profile.get("budget_limit"),
        role_defaults.get("budget_limit"),
        global_defaults.get("budget_limit"),
    )
    paid_cost_approved = bool(
        _pick(
            run_configuration.get("paid_cost_approved"),
            profile.get("paid_cost_approved"),
            role_defaults.get("paid_cost_approved"),
            global_defaults.get("paid_cost_approved"),
            False,
        )
    )
    cost_policy = str(
        _pick(
            profile.get("cost_policy"),
            provider_entry.get("cost_policy"),
            role_defaults.get("cost_policy"),
            global_defaults.get("cost_policy"),
            "UNSPECIFIED",
        )
    )

    supports_model_override = bool(profile.get("supports_model_override", True))
    if run_configuration.get("model_override") not in (None, "") and not supports_model_override:
        raise ValueError(f"override no permitido para {execution_profile}: model_override")

    model_env = str(
        _pick(
            provider_entry.get("model_env"),
            profile.get("model_env"),
            role_defaults.get("model_env"),
            global_defaults.get("model_env"),
            "",
        )
    ).strip()
    explicit_model = _pick(
        run_configuration.get("model_override"),
        profile.get("default_model"),
        role_defaults.get("default_model"),
        global_defaults.get("default_model"),
    )
    env_model = str(environ.get(model_env, "")).strip() if model_env else ""
    model_selection = str(
        profile.get("model_selection") or (
            "USER_SELECTED" if route_type != "AGENT_HARNESS_RUNTIME" else "USER_SELECTED_OR_EXECUTOR_MANAGED"
        )
    )
    model = str(_pick(explicit_model, env_model) or "").strip()

    executor_accepts_model_override = bool(executor_entry.get("accepts_model_override", False))
    api_base_env = str(provider_entry.get("api_base_env") or "").strip() or None
    api_key_env = str(provider_entry.get("api_key_env") or "").strip() or None
    provider_label = None if route_type == "AGENT_HARNESS_RUNTIME" else str(provider_ref)

    executor_status = inventory_executor(executor, profiles)
    if executor_status == "UNAVAILABLE":
        return _build_blocked(
            role_id=role_id,
            execution_route=execution_route,
            execution_profile=execution_profile,
            route_type=route_type,
            executor=executor,
            provider=provider,
            provider_adapter=provider_adapter,
            model=UNAVAILABLE if route_type != "AGENT_HARNESS_RUNTIME" else UNAVAILABLE_FROM_EXECUTOR,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
            budget_limit=budget_limit,
            paid_cost_approved=paid_cost_approved,
            cost_policy=cost_policy,
            provider_config_ref=provider_config_ref,
            blocking_reason="EXECUTOR_UNAVAILABLE",
            api_base_env=api_base_env,
            api_key_env=api_key_env,
            model_env=model_env or None,
            provider_label=provider_label,
            executor_accepts_model_override=executor_accepts_model_override,
            model_selection=model_selection,
        )

    if route_type == "AGENT_HARNESS_RUNTIME":
        if model_selection == "EXECUTOR_MANAGED":
            model = UNAVAILABLE_FROM_EXECUTOR
        elif model_selection == "USER_SELECTED_OR_EXECUTOR_MANAGED" and not model:
            model = UNAVAILABLE_FROM_EXECUTOR
        elif model_selection == "USER_SELECTED" and not model:
            return _build_blocked(
                role_id=role_id,
                execution_route=execution_route,
                execution_profile=execution_profile,
                route_type=route_type,
                executor=executor,
                provider=MANAGED_BY_EXECUTOR,
                provider_adapter="agent_executor",
                model=UNAVAILABLE_FROM_EXECUTOR,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                temperature=temperature,
                max_tokens=max_tokens,
                budget_limit=budget_limit,
                paid_cost_approved=paid_cost_approved,
                cost_policy=cost_policy,
                provider_config_ref=provider_config_ref,
                blocking_reason="MODEL_UNAVAILABLE",
                model_env=model_env or None,
                provider_label=provider_label,
                executor_accepts_model_override=executor_accepts_model_override,
                model_selection=model_selection,
            )
        return ResolvedExecutionRoute(
            role_id=role_id,
            execution_route=execution_route,
            execution_profile=execution_profile,
            route_type=route_type,
            executor=executor,
            provider=MANAGED_BY_EXECUTOR,
            provider_adapter="agent_executor",
            model=model or UNAVAILABLE_FROM_EXECUTOR,
            status=READY,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
            budget_limit=budget_limit,
            paid_cost_approved=paid_cost_approved,
            cost_policy=cost_policy,
            provider_config_ref=provider_config_ref,
            model_env=model_env or None,
            provider_label=provider_label,
            executor_accepts_model_override=executor_accepts_model_override,
            model_selection=model_selection,
        )

    if cost_policy == "OWNER_APPROVAL_REQUIRED_FOR_PAID_USAGE" and not paid_cost_approved:
        return _build_blocked(
            role_id=role_id,
            execution_route=execution_route,
            execution_profile=execution_profile,
            route_type=route_type,
            executor=executor,
            provider=provider,
            provider_adapter=provider_adapter,
            model=model or UNAVAILABLE,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
            budget_limit=budget_limit,
            paid_cost_approved=paid_cost_approved,
            cost_policy=cost_policy,
            provider_config_ref=provider_config_ref,
            blocking_reason="BLOCKED_PENDING_OWNER_COST_AUTHORIZATION",
            api_base_env=api_base_env,
            api_key_env=api_key_env,
            model_env=model_env or None,
            provider_label=provider_label,
            executor_accepts_model_override=executor_accepts_model_override,
            model_selection=model_selection,
        )

    if api_key_env and not str(environ.get(api_key_env, "")).strip():
        return _build_blocked(
            role_id=role_id,
            execution_route=execution_route,
            execution_profile=execution_profile,
            route_type=route_type,
            executor=executor,
            provider=provider,
            provider_adapter=provider_adapter,
            model=model or UNAVAILABLE,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
            budget_limit=budget_limit,
            paid_cost_approved=paid_cost_approved,
            cost_policy=cost_policy,
            provider_config_ref=provider_config_ref,
            blocking_reason="CREDENTIALS_MISSING",
            api_base_env=api_base_env,
            api_key_env=api_key_env,
            model_env=model_env or None,
            provider_label=provider_label,
            executor_accepts_model_override=executor_accepts_model_override,
            model_selection=model_selection,
        )

    if not model:
        return _build_blocked(
            role_id=role_id,
            execution_route=execution_route,
            execution_profile=execution_profile,
            route_type=route_type,
            executor=executor,
            provider=provider,
            provider_adapter=provider_adapter,
            model=UNAVAILABLE,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
            budget_limit=budget_limit,
            paid_cost_approved=paid_cost_approved,
            cost_policy=cost_policy,
            provider_config_ref=provider_config_ref,
            blocking_reason="MODEL_UNAVAILABLE",
            api_base_env=api_base_env,
            api_key_env=api_key_env,
            model_env=model_env or None,
            provider_label=provider_label,
            executor_accepts_model_override=executor_accepts_model_override,
            model_selection=model_selection,
        )

    return ResolvedExecutionRoute(
        role_id=role_id,
        execution_route=execution_route,
        execution_profile=execution_profile,
        route_type=route_type,
        executor=executor,
        provider=provider,
        provider_adapter=provider_adapter,
        model=model,
        status=READY,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        temperature=temperature,
        max_tokens=max_tokens,
        budget_limit=budget_limit,
        paid_cost_approved=paid_cost_approved,
        cost_policy=cost_policy,
        provider_config_ref=provider_config_ref,
        api_base_env=api_base_env,
        api_key_env=api_key_env,
        model_env=model_env or None,
        provider_label=provider_label,
        executor_accepts_model_override=executor_accepts_model_override,
        model_selection=model_selection,
    )


def resolve_execution_route(
    role_id: str,
    execution_route: str,
    *,
    profiles: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
) -> ResolvedExecutionRoute:
    profiles = profiles or load_execution_profiles()
    allowed = allowed_profiles_for_role(role_id, profiles=profiles)
    match = next(
        (
            profile_id
            for profile_id in allowed
            if profiles["execution_profiles"][profile_id]["execution_route"] == execution_route
        ),
        None,
    )
    if match is None:
        raise ValueError(f"ruta no permitida para {role_id}: {execution_route}")
    defaults = profiles.get("global_defaults", {})
    return resolve_run_configuration(
        {
            "role_id": role_id,
            "execution_route": execution_route,
            "execution_profile": match,
            "executor_override": None,
            "provider_override": None,
            "model_override": None,
            "timeout_seconds": int(defaults.get("timeout_seconds", 30)),
            "max_retries": int(defaults.get("max_retries", 0)),
            "temperature": defaults.get("temperature"),
            "max_tokens": defaults.get("max_tokens"),
            "budget_limit": defaults.get("budget_limit"),
            "paid_cost_approved": bool(defaults.get("paid_cost_approved", False)),
        },
        profiles=profiles,
        environ=environ,
    )


class AgentRuntimePort:
    """Common entry point for configurable provider and executor routes."""

    def __init__(self, profiles_path: Path | None = None) -> None:
        self._profiles_path = profiles_path

    def resolve(self, role_id: str, execution_route: str) -> ResolvedExecutionRoute:
        return resolve_execution_route(role_id, execution_route, profiles=load_execution_profiles(self._profiles_path))

    def resolve_run_configuration(self, run_configuration: dict[str, Any]) -> ResolvedExecutionRoute:
        return resolve_run_configuration(run_configuration, profiles=load_execution_profiles(self._profiles_path))

    def allowed_profiles(self, role_id: str) -> list[str]:
        return allowed_profiles_for_role(role_id, profiles=load_execution_profiles(self._profiles_path))
