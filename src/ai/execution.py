"""Ejecución común: routing, comprobación de schema y metadatos reproducibles."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.ai.manifest import canonical_json, file_checksum, manifest_checksum as canonical_manifest_checksum
from src.ai.providers import AgentExecutorProvider, AgentHandoffProvider, DeepSeekProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider
from src.ai.router import KNOWN_PROVIDERS, resolve_provider
from src.ai.runtime_profiles import AgentRuntimePort, READY
from src.core.contract_validation import load_schema, validate_against_schema

B5_I2_ROLE_ARTIFACT_COMPATIBILITY = {
    "ANALYSIS_PRODUCER": "analysis",
    "CURATION_PRODUCER": "curation",
    "THESIS_PRODUCER": "refined_thesis",
    "SCRIPT_PROMISE_PRODUCER": "script_promise",
    "INDEPENDENT_EDITORIAL_AUDITOR": "semantic_audit",
}
EDITORIAL_RUNTIME_FIELDS = {
    "episode_id",
    "auditor_role",
    "auditor_run_id",
    "auditor_skill_id",
    "auditor_skill_version",
    "provider_or_adapter",
    "model_or_evaluator",
    "execution_timestamp",
    "input_manifest_checksum",
    "artifact_checksums",
    "created_at",
    "audit_method",
    "readiness",
    "artifact_references",
    "producer_run_reference",
    "auditor_run_reference",
    "producer_actor_id",
    "auditor_actor_id",
    "auditor_input_checksum",
    "auditor_write_scope",
    "independence_result",
}
EDITORIAL_RUNTIME_NORMALIZED_FIELDS = {
    "required_changes",
    "excluded_claims_detected",
    "unsupported_inferences",
    "redundancy_findings",
    "progression_findings",
    "blocking_reasons",
    "reaudit_requirements",
}
EDITORIAL_ONLY_SCHEMAS = {
    "narrative_human_analysis",
    "material_curation",
    "refined_thesis",
    "editorial_script_promise",
    "b5_i2_semantic_sufficiency_audit",
    "early_packaging_hypothesis",
    "youtube_adaptation_b5_i2_package",
    "youtube_adaptation_review",
}


def _classify_provider_kind(provider: str, request: ExecutionRequest, usage: dict[str, Any]) -> str:
    explicit = str(usage.get("provider_kind") or "").strip().upper()
    if explicit in {"REAL", "SYNTHETIC"}:
        return explicit
    if usage.get("synthetic"):
        return "SYNTHETIC"
    if provider == "mock" or (request.execution_mode or "").lower() == "mock":
        return "SYNTHETIC"
    return "REAL"


def persist_execution_result(path: Path, result: ExecutionResult, request: ExecutionRequest, *, execution_mode: str) -> None:
    from src.ai.registry import append_result

    append_result(path, result, execution_mode=execution_mode, role=request.role or "UNSPECIFIED_PRODUCER", request=request)


def persist_execution_attempt(path: Path, result: ExecutionResult, request: ExecutionRequest, *, execution_mode: str) -> None:
    from src.ai.registry import append_attempt

    append_attempt(path, result, execution_mode=execution_mode, role=request.role or "UNSPECIFIED_PRODUCER", request=request)


def manifest_checksum(request: ExecutionRequest) -> str:
    return canonical_manifest_checksum(
        request.episode_id,
        [
            {
                "artifact_kind": item.artifact_kind,
                "artifact_id": item.artifact_id,
                "artifact_checksum": file_checksum(item.path),
            }
            for item in request.input_artifacts
        ],
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _availability_metadata(error: str) -> dict[str, str]:
    token = str(error or "").strip()
    category = token.split(":", 1)[0]
    if category in {
        "CREDENTIALS_MISSING",
        "MODEL_UNAVAILABLE",
        "PROVIDER_UNAVAILABLE",
        "TIMEOUT",
        "INVALID_RESPONSE",
        "MODEL_INVOCATION_FAILED",
        "EMPTY_RESPONSE",
        "INVALID_JSON",
        "OUTPUT_CONTRACT_INVALID",
        "EXECUTOR_UNAVAILABLE",
        "ACTUAL_PROVIDER_AND_MODEL_REQUIRED",
        "BLOCKED_PENDING_OWNER_COST_AUTHORIZATION",
        "AGENT_HARNESS_SMOKE_ONLY_UNTIL_R6_B_RETRY",
    }:
        return {
            "availability_status": category,
            "error_category": category,
            "error_type": category,
        }
    return {"error_type": category} if category else {}


def _result(
    request: ExecutionRequest,
    provider: str,
    status: ExecutionStatus,
    started: str,
    manifest: str,
    *,
    output: dict[str, Any] | None = None,
    error: str | None = None,
    usage: dict[str, Any] | None = None,
    real: bool = False,
    run_id: str | None = None,
) -> ExecutionResult:
    usage = {**_availability_metadata(error or ""), **(usage or {})}
    model = str(usage.get("model_or_evaluator") or request.model or "unconfigured")
    actual_executor = str(
        usage.get("actual_executor")
        or request.config.get("resolved_actual_executor")
        or request.executor
        or ("NONE" if provider == "agent_handoff" else "native_provider")
    )
    actual_provider = str(usage.get("actual_provider") or request.config.get("resolved_actual_provider") or provider)
    actual_model = str(usage.get("actual_model") or request.config.get("resolved_actual_model") or (model if provider != "agent_handoff" else "NONE"))
    execution_route = str(usage.get("execution_route") or request.execution_route or f"native:{provider}")
    execution_profile = str(usage.get("execution_profile") or request.execution_profile or request.config.get("execution_profile") or "UNSPECIFIED_PROFILE")
    usage = {
        **usage,
        "provider_kind": _classify_provider_kind(provider, request, usage),
        "actual_executor": actual_executor,
        "actual_provider": actual_provider,
        "actual_model": actual_model,
        "execution_route": execution_route,
        "execution_profile": execution_profile,
        "error_type": str(usage.get("error_type") or usage.get("availability_status") or "NONE"),
    }
    if request.output_artifact_path and request.output_artifact_path.exists():
        output_checksum = file_checksum(request.output_artifact_path)
    else:
        output_checksum = hashlib.sha256(canonical_json(output)).hexdigest() if output is not None else None
    effective_provider = str(usage.get("provider_or_adapter") or actual_provider)
    return ExecutionResult(
        run_id or f"RUN-AI-{uuid.uuid4().hex}",
        status,
        "provider",
        effective_provider,
        model,
        manifest,
        output,
        output_checksum,
        started,
        _now(),
        error,
        {"skill_id": request.skill_id, "skill_version": request.skill_version, **usage},
        request.episode_id,
        request.output_artifact_id,
        request.output_artifact_kind,
        request.output_artifact_path,
        request.output_artifact_ref,
        real,
    )


def validate_editorial_payload(payload: dict[str, Any], schema_name: str) -> list[str]:
    schema = load_schema(schema_name)
    required_exempt = EDITORIAL_RUNTIME_FIELDS | EDITORIAL_RUNTIME_NORMALIZED_FIELDS
    editorial_schema = {**schema, "required": [field for field in schema.get("required", []) if field not in required_exempt]}
    editorial_schema["properties"] = {key: value for key, value in schema.get("properties", {}).items() if key not in EDITORIAL_RUNTIME_FIELDS}
    errors = Draft7Validator(editorial_schema).iter_errors(payload)
    return [
        f"[{' -> '.join(str(p) for p in error.path) if error.path else 'root'}] {error.message}"
        for error in sorted(errors, key=lambda e: e.path)
    ]


def editorial_only_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in EDITORIAL_RUNTIME_FIELDS}


def editorial_projection_schema(schema_name: str) -> dict[str, Any]:
    schema = load_schema(schema_name)
    projected = dict(schema)
    required_exempt = EDITORIAL_RUNTIME_FIELDS | EDITORIAL_RUNTIME_NORMALIZED_FIELDS
    projected["required"] = [field for field in schema.get("required", []) if field not in required_exempt]
    projected["properties"] = {key: value for key, value in schema.get("properties", {}).items() if key not in EDITORIAL_RUNTIME_FIELDS}
    return projected


def _normalized_run_configuration(request: ExecutionRequest) -> dict[str, Any] | None:
    if request.run_configuration:
        return dict(request.run_configuration)
    if not request.execution_profile:
        return None
    return {
        "role_id": request.role,
        "execution_route": request.execution_route or request.config.get("execution_route") or request.config.get("default_execution_route") or "local_model",
        "execution_profile": request.execution_profile,
        "executor_override": request.config.get("executor_override"),
        "provider_override": request.config.get("provider_override"),
        "model_override": request.model,
        "timeout_seconds": int(request.config.get("timeout_seconds") or request.timeout or 30),
        "max_retries": int(request.config.get("max_retries") or 0),
        "temperature": request.config.get("temperature"),
        "max_tokens": request.config.get("max_tokens"),
        "budget_limit": request.config.get("budget_limit"),
        "paid_cost_approved": bool(request.config.get("paid_cost_approved", False)),
    }


def _apply_route_resolution(request: ExecutionRequest, route: Any) -> None:
    request.provider = route.provider_adapter
    request.model = route.model
    request.executor = route.executor
    request.timeout = float(route.timeout_seconds)
    request.execution_route = route.execution_route
    request.execution_profile = route.execution_profile
    request.config = {
        **request.config,
        "timeout_seconds": route.timeout_seconds,
        "max_retries": route.max_retries,
        "temperature": route.temperature,
        "max_tokens": route.max_tokens,
        "budget_limit": route.budget_limit,
        "paid_cost_approved": route.paid_cost_approved,
        "cost_policy": route.cost_policy,
        "provider_config_ref": route.provider_config_ref,
        "resolved_actual_executor": route.executor,
        "resolved_actual_provider": route.provider,
        "resolved_actual_model": route.model,
        "execution_profile": route.execution_profile,
        "execution_route": route.execution_route,
        "provider_label": route.provider_label,
        "api_base_env": route.api_base_env,
        "api_key_env": route.api_key_env,
        "model_env": route.model_env,
        "selected_executor": route.executor,
        "selected_provider": route.provider,
        "selected_model": route.model,
        "actual_provider": route.provider,
        "actual_model": route.model,
        "model_selection": route.model_selection,
        "executor_accepts_model_override": route.executor_accepts_model_override,
    }


def execute(request: ExecutionRequest) -> ExecutionResult:
    started, manifest = _now(), manifest_checksum(request)
    runtime_port = AgentRuntimePort(Path(request.config["execution_profiles_path"]) if request.config.get("execution_profiles_path") else None)
    run_configuration = _normalized_run_configuration(request)
    if run_configuration:
        try:
            route = runtime_port.resolve_run_configuration(run_configuration)
        except ValueError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if route.status != READY:
            return _result(
                request,
                route.provider_adapter,
                ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
                started,
                manifest,
                error=str(route.blocking_reason),
                usage={
                    **_availability_metadata(str(route.blocking_reason)),
                    "timeout_seconds": route.timeout_seconds,
                    "max_retries": route.max_retries,
                    "cost_policy": route.cost_policy,
                    "provider_config_ref": route.provider_config_ref,
                    "execution_profile": route.execution_profile,
                    "actual_executor": route.executor,
                    "actual_provider": route.provider,
                    "actual_model": route.model,
                    "execution_route": route.execution_route,
                },
            )
        _apply_route_resolution(request, route)
    elif request.execution_route:
        try:
            route = runtime_port.resolve(request.role, request.execution_route)
        except ValueError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if route.status != READY:
            return _result(
                request,
                route.provider_adapter,
                ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
                started,
                manifest,
                error=str(route.blocking_reason),
                usage={
                    **_availability_metadata(str(route.blocking_reason)),
                    "timeout_seconds": route.timeout_seconds,
                    "max_retries": route.max_retries,
                    "cost_policy": route.cost_policy,
                    "provider_config_ref": route.provider_config_ref,
                    "execution_profile": route.execution_profile,
                    "actual_executor": route.executor,
                    "actual_provider": route.provider,
                    "actual_model": route.model,
                    "execution_route": route.execution_route,
                },
            )
        _apply_route_resolution(request, route)
    provider_name = resolve_provider(request)
    if not provider_name:
        return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error="no hay ruta real configurada")
    if provider_name not in KNOWN_PROVIDERS:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, error="provider desconocido")
    if provider_name == "agent_handoff":
        run_id = f"RUN-AI-{uuid.uuid4().hex}"
        try:
            package = AgentHandoffProvider().prepare(request, manifest, run_id)
        except PermissionError as exc:
            return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if request.config.get("execution_registry_path"):
            from src.ai.registry import register_handoff

            register_handoff(Path(request.config["execution_registry_path"]), package, request)
        return _result(request, provider_name, ExecutionStatus.HANDOFF_PREPARED, started, manifest, usage={"package": str(package)}, run_id=run_id)
    provider = {
        "mock": MockProvider(),
        "ollama": OllamaProvider(),
        "deepseek": DeepSeekProvider(),
        "openai_compatible": OpenAICompatibleProvider(),
        "agent_executor": AgentExecutorProvider(),
    }[provider_name]
    try:
        output, usage = provider.execute(request)
    except PermissionError as exc:
        return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
    except (RuntimeError, ValueError) as exc:
        availability = _availability_metadata(str(exc))
        status = ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER if availability.get("availability_status") in {"CREDENTIALS_MISSING", "MODEL_UNAVAILABLE", "PROVIDER_UNAVAILABLE", "TIMEOUT", "MODEL_INVOCATION_FAILED"} else (ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR if availability.get("availability_status") in {"BLOCKED_PENDING_OWNER_COST_AUTHORIZATION", "EXECUTOR_UNAVAILABLE", "AGENT_HARNESS_SMOKE_ONLY_UNTIL_R6_B_RETRY"} else ExecutionStatus.FAILED)
        return _result(request, provider_name, status, started, manifest, error=str(exc), usage=availability)
    output = editorial_only_payload(output or {}) if request.output_schema in EDITORIAL_ONLY_SCHEMAS else (output or {})
    violations = validate_editorial_payload(output, request.output_schema) if request.output_schema in EDITORIAL_ONLY_SCHEMAS else validate_against_schema(output, request.output_schema)
    if violations:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, output=output, error="OUTPUT_CONTRACT_INVALID: " + "; ".join(violations), usage=usage)
    return _result(request, provider_name, ExecutionStatus.SUCCEEDED, started, manifest, output=output, usage=usage, real=provider_name not in {"mock", "agent_handoff"})
