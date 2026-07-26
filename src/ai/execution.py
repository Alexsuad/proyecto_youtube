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
from src.ai.providers import AgentHandoffProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider
from src.ai.router import KNOWN_PROVIDERS, resolve_provider
from src.core.contract_validation import load_schema, validate_against_schema


def manifest_checksum(request: ExecutionRequest) -> str:
    return canonical_manifest_checksum(request.episode_id, [
        {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "artifact_checksum": file_checksum(item.path)}
        for item in request.input_artifacts
    ])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _result(request: ExecutionRequest, provider: str, status: ExecutionStatus, started: str, manifest: str, *, output: dict[str, Any] | None = None, error: str | None = None, usage: dict[str, Any] | None = None, real: bool = False, run_id: str | None = None) -> ExecutionResult:
    usage = usage or {}
    output_checksum = hashlib.sha256(canonical_json(output)).hexdigest() if output is not None else None
    model = str(usage.get("model_or_evaluator") or request.model or "unconfigured")
    effective_provider = str(usage.get("provider_or_adapter") or provider)
    return ExecutionResult(run_id or f"RUN-AI-{uuid.uuid4().hex}", status, "provider", effective_provider, model, manifest, output, output_checksum, started, _now(), error, {"skill_id": request.skill_id, "skill_version": request.skill_version, **usage}, request.output_artifact_id, is_real_editorial_execution=real)


def validate_editorial_payload(payload: dict[str, Any], schema_name: str) -> list[str]:
    """Valida solo campos editoriales usando una proyección del schema canónico."""
    schema = load_schema(schema_name)
    provenance_fields = {
        "episode_id", "auditor_role", "auditor_run_id", "auditor_skill_id", "auditor_skill_version",
        "provider_or_adapter", "model_or_evaluator", "execution_timestamp", "input_manifest_checksum",
        "artifact_checksums", "created_at",
        "audit_method",
    }
    editorial_schema = {**schema, "required": [field for field in schema.get("required", []) if field not in provenance_fields]}
    editorial_schema["properties"] = {key: value for key, value in schema.get("properties", {}).items() if key not in provenance_fields}
    errors = Draft7Validator(editorial_schema).iter_errors(payload)
    return [
        f"[{ ' -> '.join(str(p) for p in error.path) if error.path else 'root' }] {error.message}"
        for error in sorted(errors, key=lambda e: e.path)
    ]


def editorial_only_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in {
        "episode_id", "auditor_role", "auditor_run_id", "auditor_skill_id", "auditor_skill_version",
        "provider_or_adapter", "model_or_evaluator", "execution_timestamp", "input_manifest_checksum",
        "artifact_checksums", "created_at",
        "audit_method",
    }}


def execute(request: ExecutionRequest) -> ExecutionResult:
    started, manifest = _now(), manifest_checksum(request)
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
    provider = {"mock": MockProvider(), "ollama": OllamaProvider(), "openai_compatible": OpenAICompatibleProvider()}[provider_name]
    try:
        output, usage = provider.execute(request)
    except PermissionError as exc:
        return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc))
    except (RuntimeError, ValueError) as exc:
        status = ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR if provider_name in {"ollama", "openai_compatible"} else ExecutionStatus.FAILED
        return _result(request, provider_name, status, started, manifest, error=str(exc))
    output = editorial_only_payload(output or {})
    violations = validate_editorial_payload(output, request.output_schema)
    if violations:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, output=output, error="output inválido: " + "; ".join(violations), usage=usage)
    return _result(request, provider_name, ExecutionStatus.SUCCEEDED, started, manifest, output=output, usage=usage, real=provider_name != "mock")
