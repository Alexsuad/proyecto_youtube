"""Ejecución común: routing, comprobación de schema y metadatos reproducibles."""
from __future__ import annotations

import hashlib
import copy
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.ai.manifest import canonical_json, file_checksum, manifest_checksum as canonical_manifest_checksum
from src.ai.providers import AgentExecutorProvider, AgentHandoffProvider, DeepSeekProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider
from src.ai.router import KNOWN_PROVIDERS, resolve_provider
from src.ai.runtime_profiles import AgentRuntimePort, READY, _VERIFIED_ROUTE_TOKEN
from src.core.contract_validation import load_schema, validate_against_schema
from src.core.execution_preflight import preflight_controlled_execution
from src.core.replay_protection import mark_mission_reservation

REAL_EXTERNAL_PROVIDERS = {"ollama", "deepseek", "openai_compatible"}
TECHNICAL_HARNESS_PROVIDERS = {"mock", "agent_handoff", "agent_executor"}

B5_I2_ROLE_ARTIFACT_COMPATIBILITY = {
    "ANALYSIS_PRODUCER": {"analysis"},
    "CURATION_PRODUCER": {"curation"},
    "THESIS_PRODUCER": {"refined_thesis"},
    "SCRIPT_PROMISE_PRODUCER": {"script_promise"},
    "INDEPENDENT_EDITORIAL_AUDITOR": {"semantic_audit"},
    "SCRIPT_PRODUCT_PRODUCER": {
        "analysis", "curation", "refined_thesis", "script_promise",
        "claims_ledger", "work_lifecycle", "work_research_dossier",
    },
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
    if provider in TECHNICAL_HARNESS_PROVIDERS or (request.execution_mode or "").lower() == "mock":
        return "SYNTHETIC"
    return "REAL"


def _duration_package_input(request: ExecutionRequest) -> Path | None:
    """Return the sole B5-I2 package consumed by a duration-review run."""
    if request.role != "YOUTUBE_ADAPTATION_AUDITOR" or request.output_artifact_kind != "youtube_adaptation_review":
        return None
    packages = [
        item.path
        for item in request.input_artifacts
        if item.artifact_kind == "youtube_adaptation_b5_i2_package"
    ]
    if len(packages) != 1:
        raise ValueError(
            "YOUTUBE_ADAPTATION_AUDITOR requiere exactamente un package B5-I2 trazable para persistir una review."
        )
    return Path(packages[0])


def _restore_registry(path: Path, prior: bytes | None) -> None:
    if prior is None:
        if path.exists():
            path.unlink()
        return
    path.write_bytes(prior)


def persist_execution_result(
    path: Path,
    result: ExecutionResult,
    request: ExecutionRequest,
    *,
    execution_mode: str,
    _allow_duration_registry_override: bool = False,
) -> None:
    from src.ai.registry import append_result
    from src.core.duration_envelope import canonical_active_profile_path, canonical_duration_registry_path, register_approved_duration_envelope
    from src.core.status import GateStatus
    from src.scripts.youtube_adaptation_b5_i2_gate import evaluate as evaluate_youtube_adaptation

    if str(execution_mode).upper() == "REAL" and request.config.get("_mission_authorization_token") is None:
        raise PermissionError("REAL_PROVENANCE_REQUIRES_VERIFIED_MISSION_AUTHORIZATION")
    package_path = _duration_package_input(request)
    registry_path = Path(path).resolve()
    configured_profile = request.config.get("active_editorial_profile_path")
    if configured_profile is not None and Path(str(configured_profile)).resolve() != canonical_active_profile_path():
        raise ValueError("request.config no puede sustituir el perfil editorial activo canónico.")
    if package_path is not None and registry_path != canonical_duration_registry_path() and not _allow_duration_registry_override:
        raise ValueError("La aprobación de duración solo puede materializarse en el registry canónico.")
    prior = registry_path.read_bytes() if registry_path.exists() else None
    append_result(path, result, execution_mode=execution_mode, role=request.role or "UNSPECIFIED_PRODUCER", request=request)
    if package_path is None:
        return
    gate = evaluate_youtube_adaptation(
        package_path,
        result.output_artifact_path,
        registry_path,
        (Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json"),
        request.episode_id,
    )
    if gate.status is not GateStatus.PASS:
        return
    try:
        register_approved_duration_envelope(
            package_path,
            result.output_artifact_path,
            registry_path,
        )
    except Exception:
        _restore_registry(registry_path, prior)
        raise


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
        **({"reasoning_effort": request.reasoning_effort} if request.reasoning_effort else {}),
        "provider_kind": _classify_provider_kind(provider, request, usage),
        "actual_executor": actual_executor,
        "actual_provider": actual_provider,
        "actual_model": actual_model,
        "execution_route": execution_route,
        "execution_profile": execution_profile,
        "execution_family": str(
            usage.get("execution_family")
            or request.execution_family
            or request.config.get("execution_family")
            or "UNSPECIFIED_FAMILY"
        ),
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


def _bind_runtime_fields(request: ExecutionRequest, output: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Bind cognitive provenance fields to the authoritative runtime ID.

    Synthetic providers may omit IDs, but declared values remain reviewable by
    the application boundary. REAL provider output is bound to the runtime ID
    so the provider cannot choose or forge execution lineage.
    """
    if request.execution_mode == "SYNTHETIC_TEST" and request.mock_output is None:
        return output, None
    if request.execution_mode not in {"SYNTHETIC_TEST", "REAL"}:
        return output, None
    run_key = {
        "topic_belonging_assessment": "producer_run_id",
        "topic_belonging_decision": "reviewer_run_id",
    }.get(request.output_schema)
    if run_key is None:
        return output, None
    runtime_run_id = f"RUN-AI-{uuid.uuid4().hex}"
    bound = copy.deepcopy(output)
    provenance = bound.get("provenance")
    if not isinstance(provenance, dict):
        return bound, runtime_run_id
    if request.execution_mode == "REAL":
        bound[run_key] = runtime_run_id
        provenance["run_id"] = runtime_run_id
    else:
        if not bound.get(run_key):
            bound[run_key] = runtime_run_id
        if not provenance.get("run_id"):
            provenance["run_id"] = runtime_run_id
    return bound, runtime_run_id


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
    if not request.execution_profile and not request.execution_family and not request.config.get("execution_family"):
        return None
    selection_path = request.config.get("execution_family_selection_path")
    if str(request.execution_mode).upper() in {"SYNTHETIC", "SYNTHETIC_TEST", "MOCK"}:
        selection_path = None
    return {
        "role_id": request.role,
        "execution_route": request.execution_route or request.config.get("execution_route") or request.config.get("default_execution_route") or "local_model",
        "execution_profile": request.execution_profile,
        "execution_family": request.execution_family or request.config.get("execution_family"),
        "executor_override": request.config.get("executor_override"),
        "provider_override": request.config.get("provider_override"),
        "model_override": request.model,
        "reasoning_effort": request.reasoning_effort or request.config.get("reasoning_effort"),
        "timeout_seconds": int(request.config.get("timeout_seconds") or request.timeout or 30),
        "max_retries": int(request.config.get("max_retries") or 0),
        "temperature": request.config.get("temperature"),
        "max_tokens": request.config.get("max_tokens"),
        "budget_limit": request.config.get("budget_limit"),
        "paid_cost_approved": bool(request.config.get("paid_cost_approved", False)),
        "execution_family_selection_path": selection_path,
        "mission_contract_path": request.config.get("mission_contract_path"),
        "completion_gate_result_path": request.config.get("completion_gate_result_path"),
        "mission_repo_root": request.config.get("mission_repo_root"),
    }


def _apply_route_resolution(request: ExecutionRequest, route: Any) -> None:
    # An explicitly requested canonical handoff remains handoff-only after
    # profile resolution.  The selected profile is still resolved by
    # AgentRuntimePort; this branch prevents the HANDOFF_ONLY route from being
    # silently converted into the integrated AgentExecutorProvider.
    request.resolved_route = route
    request.resolved_route_token = _VERIFIED_ROUTE_TOKEN
    handoff_requested = (
        request.provider == "agent_handoff"
        or (request.execution_mode or "").lower() == "agent_handoff"
        or getattr(route, "execution_family", None) == "AGENT_HARNESS"
    )
    request.provider = "agent_handoff" if handoff_requested and getattr(route, "route_type", None) == "AGENT_HARNESS_RUNTIME" else route.provider_adapter
    request.model = route.model
    request.reasoning_effort = getattr(route, "reasoning_effort", None)
    request.executor = route.executor
    request.timeout = float(route.timeout_seconds)
    request.execution_route = route.execution_route
    request.execution_profile = route.execution_profile
    request.execution_family = getattr(route, "execution_family", None)
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
        "reasoning_effort": getattr(route, "reasoning_effort", None),
        "reasoning_effort_supported": getattr(route, "reasoning_effort_supported", False),
        "execution_profile": route.execution_profile,
        "execution_family": getattr(route, "execution_family", None),
        "execution_route": route.execution_route,
        "provider_label": getattr(route, "provider_label", None),
        "api_base_env": getattr(route, "api_base_env", None),
        "api_key_env": getattr(route, "api_key_env", None),
        "model_env": getattr(route, "model_env", None),
        "selected_executor": route.executor,
        "selected_provider": route.provider,
        "selected_model": route.model,
        "actual_provider": route.provider,
        "actual_model": route.model,
        "runtime_route_resolved": True,
        "model_selection": getattr(route, "model_selection", "USER_SELECTED"),
        "executor_accepts_model_override": getattr(route, "executor_accepts_model_override", False),
    }


def _execute_unfinalized(request: ExecutionRequest) -> ExecutionResult:
    started, manifest = _now(), manifest_checksum(request)
    if request.execution_mode == "SYNTHETIC_TEST" and request.mock_output is None:
        return _result(
            request,
            "none",
            ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
            started,
            manifest,
            error="SYNTHETIC_MOCK_OUTPUT_REQUIRED: real providers are unavailable in synthetic test mode",
        )
    repository_root = Path(str(request.config.get("repository_root") or Path(__file__).resolve().parents[2])).resolve()
    try:
        preflight = preflight_controlled_execution(request, root=repository_root)
        from src.ai.registry import capture_pre_run_snapshot

        if preflight.get("authorization") is not None:
            from src.ai.registry import _VERIFIED_AUTHORIZATION_TOKEN
            request.config = {
                **request.config,
                "_mission_authorization_verified": True,
                "_mission_authorization_token": _VERIFIED_AUTHORIZATION_TOKEN,
                "mission_id": getattr(preflight["authorization"], "mission_id", request.config.get("mission_id")),
                "mission_contract_sha256": getattr(preflight["authorization"], "contract_sha256", None),
            }
        capture_pre_run_snapshot(request, authorization=preflight.get("authorization"), root=repository_root)
        if preflight.get("context_manifest") is not None:
            request.config = {**request.config, "resolved_context_manifest": preflight["context_manifest"], "resolved_context_manifest_sha256": preflight["context_manifest"]["manifest_sha256"], "mission_contract_sha256": getattr(preflight.get("authorization"), "contract_sha256", None)}
    except (PermissionError, ValueError) as exc:
        return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc))
    mission_contract = preflight.get("mission_contract")
    if mission_contract is not None and mission_contract.mission_mode == "REDUCED":
        convergence_result = _execute_reduced_mission(request, started, manifest, mission_contract)
        if convergence_result.status is not ExecutionStatus.CONVERGED:
            return convergence_result
        if request.execution_family != "AGENT_HARNESS" and request.execution_route != "agent_harness":
            return convergence_result
        request.config = {
            **request.config,
            "_mission_convergence": convergence_result.usage,
        }
    runtime_port = AgentRuntimePort(Path(request.config["execution_profiles_path"]) if request.config.get("execution_profiles_path") else None)
    run_configuration = _normalized_run_configuration(request)
    if run_configuration:
        request.config = {
            **request.config,
            **{
                key: run_configuration[key]
                for key in ("execution_family_selection_path", "mission_contract_path", "completion_gate_result_path", "mission_repo_root")
                if run_configuration.get(key) not in (None, "")
            },
        }
        try:
            route = runtime_port.resolve_run_configuration(
                run_configuration,
                enforce_selector=str(request.execution_mode).upper() not in {"SYNTHETIC", "SYNTHETIC_TEST", "MOCK"},
            )
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
    resolved_authorization = preflight.get("authorization")
    if resolved_authorization is not None and callable(getattr(resolved_authorization, "verify", None)) and (request.execution_profile or request.execution_family) and request.execution_route:
        try:
            resolved_authorization.verify(
                repository_root,
                capability_id=str(request.capability_id),
                role_id=str(request.role),
                operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
                execution_profile_id=request.execution_profile,
                execution_family=request.execution_family or request.config.get("execution_family"),
                execution_route=str(request.execution_route),
                execution_interface=str(request.config.get("execution_interface") or "UNSPECIFIED_INTERFACE"),
                required_material_decision_ref=preflight.get("required_material_decision_ref"),
            )
        except PermissionError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=f"ROUTE_NOT_AUTHORIZED_AFTER_RESOLUTION:{exc}")
    if request.mock_output is not None and request.execution_mode == "SYNTHETIC_TEST":
        request.provider = "mock"
    provider_name = resolve_provider(request)
    if not provider_name:
        return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error="no hay ruta real configurada")
    if provider_name not in KNOWN_PROVIDERS:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, error="provider desconocido")
    if provider_name in REAL_EXTERNAL_PROVIDERS and resolved_authorization is None:
        return _result(
            request,
            provider_name,
            ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
            started,
            manifest,
            error=f"ENTRY_FAIL_CLOSED:REAL_PROVIDER_WITHOUT_MISSION_AUTHORIZATION:{provider_name}",
            usage=_availability_metadata("ENTRY_FAIL_CLOSED:REAL_PROVIDER_WITHOUT_MISSION_AUTHORIZATION"),
        )
    if provider_name == "agent_handoff":
        run_id = f"RUN-AI-{uuid.uuid4().hex}"
        try:
            package = AgentHandoffProvider().prepare(request, manifest, run_id)
        except PermissionError as exc:
            return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if request.config.get("execution_registry_path"):
            from src.ai.registry import register_handoff

            register_handoff(Path(request.config["execution_registry_path"]), package, request)
        return _result(
            request,
            provider_name,
            ExecutionStatus.HANDOFF_PREPARED,
            started,
            manifest,
            usage={"package": str(package), **request.config.get("_mission_convergence", {})},
            run_id=run_id,
        )
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
    output, runtime_run_id = _bind_runtime_fields(request, output)
    violations = validate_editorial_payload(output, request.output_schema) if request.output_schema in EDITORIAL_ONLY_SCHEMAS else validate_against_schema(output, request.output_schema)
    if violations:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, output=output, error="OUTPUT_CONTRACT_INVALID: " + "; ".join(violations), usage=usage)
    return _result(request, provider_name, ExecutionStatus.SUCCEEDED, started, manifest, output=output, usage=usage, real=provider_name in REAL_EXTERNAL_PROVIDERS, run_id=runtime_run_id)


def _execute_reduced_mission(request: ExecutionRequest, started: str, manifest: str, mission_contract: Any) -> ExecutionResult:
    """Run the canonical reduced-mission loop after authorization and preflight."""
    from src.core.mission_convergence import BLOCKED, CONVERGED, MAX_ITERATIONS_REACHED, run_convergence_loop

    callbacks = request.config.get("convergence_callbacks")
    required = ("implement", "verify", "adversarial_review", "repair")
    if not isinstance(callbacks, dict) or any(not callable(callbacks.get(name)) for name in required):
        return _result(request, "mission_convergence", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error="REDUCED_MISSION_CALLBACKS_REQUIRED")
    try:
        outcome = run_convergence_loop(
            implement=callbacks["implement"], verify=callbacks["verify"],
            adversarial_review=callbacks["adversarial_review"], repair=callbacks["repair"],
            max_iterations=int(request.config.get("convergence_max_iterations", 3)),
            review_policy=mission_contract.reduced_fields["review_policy"],
            sensitive_change=bool(mission_contract.contains_material_repair), governed=True,
        )
    except (TypeError, ValueError) as exc:
        return _result(request, "mission_convergence", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=f"MISSION_CONVERGENCE_INVALID:{exc}")
    usage = {"mission_convergence": outcome.to_dict(), "next_review_stage": outcome.review_stage, "mission_contract_mode": "REDUCED"}
    if outcome.status == CONVERGED:
        return _result(request, "mission_convergence", ExecutionStatus.CONVERGED, started, manifest, usage=usage)
    status = ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR if outcome.status == BLOCKED else ExecutionStatus.FAILED
    return _result(request, "mission_convergence", status, started, manifest, error=f"MISSION_CONVERGENCE_{outcome.status}", usage=usage)


def _finalize_mission_reservation(request: ExecutionRequest, result: ExecutionResult) -> ExecutionResult:
    reservation_id = request.config.get("_mission_reservation_id")
    registry_path = request.config.get("execution_registry_path")
    if not reservation_id or not registry_path or request.config.get("_mission_reservation_status") != "RESERVED":
        return result
    status = "CONSUMED" if result.status in {ExecutionStatus.SUCCEEDED, ExecutionStatus.HANDOFF_PREPARED, ExecutionStatus.CONVERGED} else "FAILED"
    try:
        mark_mission_reservation(registry_path, reservation_id, status)
        request.config = {**request.config, "_mission_reservation_status": status}
        result.usage["mission_reservation_status"] = status
    except (OSError, ValueError, PermissionError) as exc:
        error = f"MISSION_RESERVATION_FINALIZATION_FAILED: {exc}"
        result.status = ExecutionStatus.FAILED
        result.error = error
        result.usage["provenance_error"] = error
        result.usage["mission_reservation_status"] = "RESERVED"
    return result


def execute(request: ExecutionRequest) -> ExecutionResult:
    return _finalize_mission_reservation(request, _execute_unfinalized(request))
