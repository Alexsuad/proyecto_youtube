"""Ejecución común: routing, comprobación de schema y metadatos reproducibles."""
from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jsonschema import Draft7Validator

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.ai.manifest import canonical_json, file_checksum, manifest_checksum as canonical_manifest_checksum
from src.ai.providers import AgentHandoffProvider, DeepSeekProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider
from src.ai.router import KNOWN_PROVIDERS, resolve_provider
from src.ai.runtime_profiles import AgentRuntimePort
from src.core.contract_validation import load_schema, validate_against_schema

B5_I2_ROLE_ARTIFACT_COMPATIBILITY = {
    "ANALYSIS_PRODUCER": "analysis",
    "CURATION_PRODUCER": "curation",
    "THESIS_PRODUCER": "refined_thesis",
    "SCRIPT_PROMISE_PRODUCER": "script_promise",
    "INDEPENDENT_EDITORIAL_AUDITOR": "semantic_audit",
}
EDITORIAL_RUNTIME_FIELDS = {
    "episode_id", "auditor_role", "auditor_run_id", "auditor_skill_id", "auditor_skill_version",
    "provider_or_adapter", "model_or_evaluator", "execution_timestamp", "input_manifest_checksum",
    "artifact_checksums", "created_at", "audit_method", "readiness",
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
    """Registra por runtime cualquier productor o auditor con salida verificable."""
    from src.ai.registry import append_result
    append_result(path, result, execution_mode=execution_mode, role=request.role or "UNSPECIFIED_PRODUCER", request=request)


def manifest_checksum(request: ExecutionRequest) -> str:
    return canonical_manifest_checksum(request.episode_id, [
        {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "artifact_checksum": file_checksum(item.path)}
        for item in request.input_artifacts
    ])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _availability_metadata(error: str) -> dict[str, str]:
    token = str(error or "").strip()
    category = token.split(":", 1)[0]
    if category in {"CREDENTIALS_MISSING", "MODEL_UNAVAILABLE", "PROVIDER_UNAVAILABLE", "TIMEOUT", "INVALID_RESPONSE", "EXECUTOR_UNAVAILABLE", "ACTUAL_PROVIDER_AND_MODEL_REQUIRED"}:
        return {"availability_status": category, "error_category": category}
    return {}


def _result(request: ExecutionRequest, provider: str, status: ExecutionStatus, started: str, manifest: str, *, output: dict[str, Any] | None = None, error: str | None = None, usage: dict[str, Any] | None = None, real: bool = False, run_id: str | None = None) -> ExecutionResult:
    usage = {**_availability_metadata(error or ""), **(usage or {})}
    model = str(usage.get("model_or_evaluator") or request.model or "unconfigured")
    actual_executor = str(usage.get("actual_executor") or request.executor or ("NONE" if provider == "agent_handoff" else "native_provider"))
    actual_provider = str(usage.get("actual_provider") or provider)
    actual_model = str(usage.get("actual_model") or (model if provider != "agent_handoff" else "NONE"))
    execution_route = str(usage.get("execution_route") or request.execution_route or f"native:{provider}")
    usage = {**usage, "provider_kind": _classify_provider_kind(provider, request, usage), "actual_executor": actual_executor, "actual_provider": actual_provider, "actual_model": actual_model, "execution_route": execution_route}
    if request.output_artifact_path and request.output_artifact_path.exists():
        output_checksum = file_checksum(request.output_artifact_path)
    else:
        output_checksum = hashlib.sha256(canonical_json(output)).hexdigest() if output is not None else None
    effective_provider = str(usage.get("provider_or_adapter") or provider)
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
    """Valida solo campos editoriales usando una proyección del schema canónico."""
    schema = load_schema(schema_name)
    editorial_schema = {**schema, "required": [field for field in schema.get("required", []) if field not in EDITORIAL_RUNTIME_FIELDS]}
    editorial_schema["properties"] = {key: value for key, value in schema.get("properties", {}).items() if key not in EDITORIAL_RUNTIME_FIELDS}
    errors = Draft7Validator(editorial_schema).iter_errors(payload)
    return [
        f"[{ ' -> '.join(str(p) for p in error.path) if error.path else 'root' }] {error.message}"
        for error in sorted(errors, key=lambda e: e.path)
    ]


def editorial_only_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in EDITORIAL_RUNTIME_FIELDS}


def editorial_projection_schema(schema_name: str) -> dict[str, Any]:
    schema = load_schema(schema_name)
    projected = dict(schema)
    projected["required"] = [field for field in schema.get("required", []) if field not in EDITORIAL_RUNTIME_FIELDS]
    projected["properties"] = {key: value for key, value in schema.get("properties", {}).items() if key not in EDITORIAL_RUNTIME_FIELDS}
    return projected


def execute(request: ExecutionRequest) -> ExecutionResult:
    started, manifest = _now(), manifest_checksum(request)
    if request.execution_route:
        try:
            route = AgentRuntimePort(Path(request.config["execution_profiles_path"]) if request.config.get("execution_profiles_path") else None).resolve(request.role, request.execution_route)
        except ValueError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if route.status != "READY":
            return _result(request, route.provider, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(route.blocking_reason), usage={**_availability_metadata(str(route.blocking_reason)), "timeout_seconds": route.timeout_seconds, "max_retries": route.max_retries, "cost_policy": route.cost_policy, "provider_config_ref": route.provider_config_ref})
        request.provider, request.model, request.executor = route.provider, route.model, route.executor
        request.timeout = float(route.timeout_seconds)
    provider_name = resolve_provider(request)
    if not provider_name:
        return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error="no hay ruta real configurada")
    if provider_name not in KNOWN_PROVIDERS:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, error="provider desconocido")
    if provider_name == "agent_handoff":
        run_id = f"RUN-AI-{uuid.uuid4().hex}"
        package = AgentHandoffProvider().prepare(request, manifest, run_id)
        if request.config.get("execution_registry_path"):
            from src.ai.registry import register_handoff
            register_handoff(Path(request.config["execution_registry_path"]), package, request)
        return _result(request, provider_name, ExecutionStatus.HANDOFF_PREPARED, started, manifest, usage={"package": str(package)}, run_id=run_id)
    provider = {"mock": MockProvider(), "ollama": OllamaProvider(), "deepseek": DeepSeekProvider(), "openai_compatible": OpenAICompatibleProvider()}[provider_name]
    try:
        output, usage = provider.execute(request)
    except PermissionError as exc:
        return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
    except (RuntimeError, ValueError) as exc:
        availability = _availability_metadata(str(exc))
        status = ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR if availability.get("availability_status") in {"CREDENTIALS_MISSING", "MODEL_UNAVAILABLE", "PROVIDER_UNAVAILABLE", "TIMEOUT"} else ExecutionStatus.FAILED
        return _result(request, provider_name, status, started, manifest, error=str(exc), usage=availability)
    output = editorial_only_payload(output or {})
    violations = validate_editorial_payload(output, request.output_schema)
    if violations:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, output=output, error="output inválido: " + "; ".join(violations), usage=usage)
    return _result(request, provider_name, ExecutionStatus.SUCCEEDED, started, manifest, output=output, usage=usage, real=provider_name != "mock")