"""Operaciones sobre la sede canónica de provenance de ejecuciones."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ai.contracts import ExecutionResult, ExecutionStatus
from src.ai.manifest import canonical_json, file_checksum
from src.core.contract_validation import validate_against_schema
from src.core.mission_authorization import load_mission_authorization

# Process-local capability issued only after execution preflight verifies authority.
_VERIFIED_AUTHORIZATION_TOKEN = object()

B5_I2_ROLE_ARTIFACT_COMPATIBILITY = {
    "ANALYSIS_PRODUCER": {"analysis"},
    "CURATION_PRODUCER": {"curation"},
    "THESIS_PRODUCER": {"refined_thesis"},
    "SCRIPT_PROMISE_PRODUCER": {"script_promise"},
    "INDEPENDENT_EDITORIAL_AUDITOR": {"semantic_audit"},
    "SCRIPT_PRODUCT_PRODUCER": {"analysis", "curation", "refined_thesis", "script_promise"},
    "SCRIPT_PRODUCT_AUDITOR": {"semantic_audit"},
    "YOUTUBE_ADAPTATION_PRODUCER": {"early_packaging_hypothesis", "youtube_adaptation_b5_i2_package"},
    "YOUTUBE_ADAPTATION_AUDITOR": {"youtube_adaptation_review"},
}
B5_I2_ARTIFACT_KINDS = {
    "analysis",
    "curation",
    "refined_thesis",
    "script_promise",
    "semantic_audit",
    "early_packaging_hypothesis",
    "youtube_adaptation_b5_i2_package",
    "youtube_adaptation_review",
}


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"registry_version": "1.0.0", "runs": [], "handoffs": [], "attempts": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("runs", [])
    data.setdefault("handoffs", [])
    data.setdefault("attempts", [])
    return data


def _write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _repository_root(request: Any) -> Path:
    configured = request.config.get("repository_root") if request is not None else None
    if configured:
        return Path(str(configured)).resolve()
    return Path(__file__).resolve().parents[2]


def _workspace_snapshot(root: Path, authorized_paths: list[str] | tuple[str, ...] | None = None) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not root.is_dir():
        return snapshot
    if not authorized_paths:
        return snapshot
    candidates: set[Path] = set()
    for raw_path in authorized_paths:
        relative = Path(str(raw_path).replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts:
            continue
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            continue
        if target.is_file():
            candidates.add(target)
        elif target.is_dir():
            candidates.update(path for path in target.rglob("*") if path.is_file())
    for candidate in candidates:
        if any(part == ".git" for part in candidate.relative_to(root).parts):
            continue
        try:
            snapshot[candidate.relative_to(root).as_posix()] = file_checksum(candidate)
        except OSError:
            continue
    return snapshot


def capture_pre_run_snapshot(request: Any, *, authorization: Any = None, root: Path | None = None) -> None:
    """Capture the authorized write scope before execution; the reviewer cannot supply it."""
    root = (root or _repository_root(request)).resolve()
    authorized_paths = tuple(str(path) for path in getattr(authorization, "allowed_paths", ()) or ())
    request.config = {
        **request.config,
        "_workspace_root": str(root),
        "_authorized_write_scope": list(authorized_paths),
        "_pre_run_snapshot": _workspace_snapshot(root, authorized_paths),
    }


def _modification_manifest(request: Any) -> dict[str, Any]:
    pre_snapshot = request.config.get("_pre_run_snapshot")
    root_value = request.config.get("_workspace_root")
    authorized_paths = request.config.get("_authorized_write_scope")
    if not isinstance(pre_snapshot, dict) or not root_value or not isinstance(authorized_paths, list) or not authorized_paths:
        return {
            "source": "RUNTIME_PRE_POST_DIFF_UNAVAILABLE",
            "modified_artifact_ids": [],
            "modified_artifact_paths": [],
        }
    root = Path(str(root_value)).resolve()
    authorized_paths = request.config.get("_authorized_write_scope")
    post_snapshot = _workspace_snapshot(root, authorized_paths if isinstance(authorized_paths, list) else None)
    changed_paths = sorted(
        path for path in set(pre_snapshot) | set(post_snapshot)
        if pre_snapshot.get(path) != post_snapshot.get(path)
    )
    path_to_ids: dict[str, set[str]] = {}
    for item in getattr(request, "input_artifacts", []) or []:
        try:
            path_to_ids[Path(item.path).resolve().relative_to(root).as_posix()] = {str(item.artifact_id)}
        except ValueError:
            continue
    output_path = getattr(request, "output_artifact_path", None)
    if output_path:
        try:
            path_to_ids.setdefault(Path(output_path).resolve().relative_to(root).as_posix(), set()).add(str(request.output_artifact_id))
        except ValueError:
            pass
    modified_ids = sorted({artifact_id for path in changed_paths for artifact_id in path_to_ids.get(path, set()) if artifact_id})
    return {
        "source": "RUNTIME_PRE_POST_DIFF",
        "modified_artifact_ids": modified_ids,
        "modified_artifact_paths": changed_paths,
        "pre_run_snapshot_sha256": hashlib.sha256(canonical_json(pre_snapshot)).hexdigest(),
        "post_run_snapshot_sha256": hashlib.sha256(canonical_json(post_snapshot)).hexdigest(),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _seconds_between(started_at: str, finished_at: str) -> float:
    started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    return max(0.0, (finished - started).total_seconds())


def skill_checksum(skill_path: Path | None = None) -> str:
    path = skill_path or Path(".agent/skills/skill_auditar_suficiencia_semantica_b5_i2.md")
    return file_checksum(path)


def package_checksum(package: dict[str, Any]) -> str:
    content = {key: value for key, value in package.items() if key != "package_checksum"}
    return hashlib.sha256(canonical_json(content)).hexdigest()


def _input_rows_from_request(request: Any) -> tuple[list[str], list[str], list[str]]:
    ids: list[str] = []
    versions: list[str] = []
    checksums: list[str] = []
    for item in getattr(request, "input_artifacts", []) or []:
        ids.append(f"{item.artifact_kind}:{item.artifact_id}")
        versions.append(getattr(item, "producer_run_id", "UNKNOWN") or "UNKNOWN")
        checksums.append(file_checksum(item.path))
    return ids, versions, checksums


def _input_rows_from_output(output: dict[str, Any] | None) -> tuple[list[str], list[str], list[str]]:
    rows = output.get("artifact_checksums", []) if isinstance(output, dict) else []
    ids = [f"{row['artifact_kind']}:{row['artifact_id']}" for row in rows]
    versions = [row.get("producer_run_id") or "UNKNOWN" for row in rows]
    checksums = [row["checksum"] for row in rows]
    return ids, versions, checksums


def _output_rows(result: ExecutionResult) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    output_ref = result.output_artifact_ref or f"{result.output_artifact_kind}:{result.output_artifact_id}"
    artifact_path = str(result.output_artifact_path) if result.output_artifact_path else None
    outputs = [{
        "artifact_kind": result.output_artifact_kind,
        "artifact_id": result.output_artifact_id,
        "artifact_path": artifact_path,
        "artifact_ref": output_ref,
        "checksum": result.output_checksum,
    }]
    return outputs, [output_ref], [result.run_id], [result.output_checksum]


def _provenance_fields(
    *,
    role: str,
    provider: str,
    model: str,
    execution_profile: str,
    prompt_version: str,
    started_at: str,
    finished_at: str,
    input_artifact_ids: list[str],
    input_versions: list[str],
    input_checksums: list[str],
    output_artifact_ids: list[str],
    output_versions: list[str],
    output_checksums: list[str],
    usage: dict[str, Any] | None,
    decision: str,
    blocking_reason: str | None,
    handoff_target: str,
) -> dict[str, Any]:
    usage = usage or {}
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", "UNAVAILABLE_FROM_PROVIDER"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens", "UNAVAILABLE_FROM_PROVIDER"))
    estimated_cost = usage.get("estimated_cost", "UNAVAILABLE_FROM_PROVIDER")
    retry_count = int(usage.get("retry_count") or 0)
    return {
        "agent_id": role,
        "role_id": role,
        "execution_route": str(usage.get("execution_route") or f"native:{provider}"),
        "execution_profile": str(usage.get("execution_profile") or execution_profile or "UNSPECIFIED_PROFILE"),
        "actual_executor": str(usage.get("actual_executor") or ("NONE" if provider == "agent_handoff" else "native_provider")),
        "actual_provider": str(usage.get("actual_provider") or provider),
        "actual_model": str(usage.get("actual_model") or model or "NONE"),
        "provider": provider,
        "model": model or "NONE",
        "prompt_version": prompt_version,
        "input_artifact_ids": input_artifact_ids,
        "input_versions": input_versions,
        "input_checksums": input_checksums,
        "output_artifact_ids": output_artifact_ids,
        "output_versions": output_versions,
        "output_checksums": output_checksums,
        "finished_at": finished_at,
        "latency": _seconds_between(started_at, finished_at),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "retry_count": retry_count,
        "decision": decision,
        "error_type": str(usage.get("error_type") or usage.get("availability_status") or "NONE"),
        "blocking_reason": blocking_reason,
        "handoff_target": handoff_target,
    }


def _attempt_status(result: ExecutionResult) -> str:
    if result.status is ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER:
        return "BLOCKED_BY_RUNTIME_PROVIDER"
    if result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR:
        return "BLOCKED_BY_SEMANTIC_EVALUATOR"
    return "FAILED"


def _non_null(values: dict[str, Any]) -> dict[str, Any]:
    """Keep provenance groups explicit without emitting null telemetry."""
    return {key: value for key, value in values.items() if value is not None}


def register_handoff(path: Path, package_path: Path, request: Any) -> None:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    registry = load_registry(path)
    registry.setdefault("handoffs", [])
    if any(item.get("handoff_id") == package.get("handoff_id") for item in registry["handoffs"]):
        raise ValueError("handoff_id duplicado en provenance")
    started_at = _now()
    input_ids, input_versions, input_checksums = _input_rows_from_request(request)
    prompt_version = str(request.config.get("prompt_version") or package.get("skill_version") or request.skill_version)
    handoff_target = str(request.config.get("handoff_target") or request.config.get("expected_provider_or_agent") or request.capability_id)
    record = {
        "handoff_id": package["handoff_id"],
        "capability_id": package["capability_id"],
        "episode_id": package["episode_id"],
        "skill_id": package["skill_id"],
        "skill_version": package["skill_version"],
        "skill_checksum": package["skill_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"],
        "package_checksum": package["package_checksum"],
        "prepared_at": started_at,
        "started_at": started_at,
        "status": "HANDOFF_PREPARED",
        "run_id": package["handoff_id"],
        **_provenance_fields(
            role=str(getattr(request, "role", "UNSPECIFIED_PRODUCER") or "UNSPECIFIED_PRODUCER"),
            provider="agent_handoff",
            model=str(getattr(request, "model", None) or "NONE"),
            execution_profile=str(getattr(request, "execution_profile", None) or request.config.get("execution_profile") or "UNSPECIFIED_PROFILE"),
            prompt_version=prompt_version,
            started_at=started_at,
            finished_at=started_at,
            input_artifact_ids=input_ids,
            input_versions=input_versions,
            input_checksums=input_checksums,
            output_artifact_ids=[],
            output_versions=[],
            output_checksums=[],
            usage=getattr(request, "config", {}) or {},
            decision="HANDOFF_PREPARED",
            blocking_reason=None,
            handoff_target=handoff_target,
        ),
    }
    registry["handoffs"].append(record)
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))
    _write_registry(path, registry)


def consume_handoff(path: Path, *, package: dict[str, Any], result_run_id: str, output_checksum: str, current_skill_checksum: str) -> None:
    validate_handoff(path, package=package, current_skill_checksum=current_skill_checksum)
    registry = load_registry(path)
    record = next(item for item in registry.get("handoffs", []) if item.get("handoff_id") == package.get("handoff_id"))
    finished_at = _now()
    record.update({
        "status": "HANDOFF_CONSUMED",
        "result_run_id": result_run_id,
        "output_checksum": output_checksum,
        "consumed_at": finished_at,
        "finished_at": finished_at,
        "output_artifact_ids": [package.get("output_schema") or "handoff_result"],
        "output_versions": [result_run_id],
        "output_checksums": [output_checksum],
        "decision": "HANDOFF_CONSUMED",
        "error_type": "NONE",
    })
    record["latency"] = _seconds_between(record["started_at"], finished_at)
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))
    _write_registry(path, registry)


def validate_handoff(path: Path, *, package: dict[str, Any], current_skill_checksum: str) -> dict[str, Any]:
    registry = load_registry(path)
    record = next((item for item in registry.get("handoffs", []) if item.get("handoff_id") == package.get("handoff_id")), None)
    if not record:
        raise ValueError("handoff inexistente en provenance")
    if record.get("status") != "HANDOFF_PREPARED":
        raise ValueError("handoff ya consumido o no preparado")
    if record.get("package_checksum") != package_checksum(package):
        raise ValueError("package_checksum no coincide con el registro")
    if record.get("skill_checksum") != package.get("skill_checksum") or record.get("skill_checksum") != current_skill_checksum:
        raise ValueError("skill_checksum no coincide con el registro o la skill actual")
    for field in ("capability_id", "episode_id", "skill_id", "skill_version", "input_manifest_checksum"):
        if record.get(field) != package.get(field):
            raise ValueError(f"handoff no coincide en {field}")
    return record


def _real_provenance_authorized(request: Any) -> bool:
    if request is None:
        return False
    config = request.config or {}
    authorization_path = config.get("mission_authorization_path")
    repository_root = Path(str(config.get("repository_root") or Path(__file__).resolve().parents[2])).resolve()
    if not authorization_path:
        return False
    candidate = Path(str(authorization_path))
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    path = (repository_root / candidate).resolve()
    try:
        path.relative_to(repository_root)
        authorization = load_mission_authorization(path)
        output_path = getattr(request, "output_artifact_path", None)
        relative_output = None
        if output_path:
            relative_output = str(Path(output_path).resolve().relative_to(repository_root)).replace("\\", "/")
        authorization.verify(
            repository_root,
            capability_id=str(request.capability_id),
            role_id=str(getattr(request, "role", "")),
            operation=str(config.get("mission_operation") or "EXECUTE_CAPABILITY"),
            path=relative_output,
            execution_mode="REAL",
            execution_route=str(getattr(request, "execution_route", None) or config.get("execution_route") or "") or None,
            execution_profile_id=str(getattr(request, "execution_profile", None) or config.get("execution_profile") or "") or None,
            execution_interface=str(config.get("execution_interface") or "") or None,
        )
    except Exception:
        return False
    return True


def append_result(
    path: Path,
    result: ExecutionResult,
    *,
    execution_mode: str,
    role: str = "UNSPECIFIED_PRODUCER",
    request: Any | None = None,
) -> None:
    """Registra solo ejecuciones que realmente produjeron un artefacto verificable."""
    if str(execution_mode).upper() == "REAL" and (request is None or not _real_provenance_authorized(request)):
        raise PermissionError("REAL_PROVENANCE_REQUIRES_VERIFIED_MISSION_AUTHORIZATION")
    if result.status is not ExecutionStatus.SUCCEEDED or not result.output_checksum:
        return
    if not result.output_artifact_kind or not result.output_artifact_id:
        raise ValueError("ExecutionResult requiere output_artifact_kind y output_artifact_id")
    if result.output_artifact_kind in B5_I2_ARTIFACT_KINDS and role not in B5_I2_ROLE_ARTIFACT_COMPATIBILITY:
        raise ValueError(f"role {role} no registrado para artifact_kind B5-I2 {result.output_artifact_kind}")
    if result.output_artifact_kind in B5_I2_ARTIFACT_KINDS and role in B5_I2_ROLE_ARTIFACT_COMPATIBILITY and result.output_artifact_kind not in B5_I2_ROLE_ARTIFACT_COMPATIBILITY[role]:
        raise ValueError(f"role {role} incompatible con artifact_kind {result.output_artifact_kind}")
    if role in {"ANALYSIS_PRODUCER", "CURATION_PRODUCER", "THESIS_PRODUCER", "SCRIPT_PROMISE_PRODUCER", "SCRIPT_PRODUCT_PRODUCER", "YOUTUBE_ADAPTATION_PRODUCER"} and not result.output_artifact_path:
        raise ValueError(f"{role} requiere output_artifact_path verificable")
    if result.output_artifact_path:
        if not result.output_artifact_path.exists():
            raise ValueError(f"output inexistente: {result.output_artifact_path}")
        if file_checksum(result.output_artifact_path) != result.output_checksum:
            raise ValueError(f"checksum incorrecto para output: {result.output_artifact_path}")
    registry = load_registry(path)
    if any(run.get("run_id") == result.run_id for run in registry["runs"]):
        raise ValueError(f"run_id duplicado en provenance: {result.run_id}")
    outputs, output_ids, output_versions, output_checksums = _output_rows(result)
    output_refs = [item["artifact_ref"] for item in outputs]
    if len(output_refs) != len(set(output_refs)):
        raise ValueError("outputs duplicados en el mismo run")
    if request is not None:
        input_ids, input_versions, input_checksums = _input_rows_from_request(request)
        prompt_version = str(request.config.get("prompt_version") or result.usage.get("prompt_version") or result.usage.get("skill_version") or result.usage["skill_version"])
        handoff_target = str(request.config.get("handoff_target") or request.capability_id)
        execution_profile = str(getattr(request, "execution_profile", None) or request.config.get("execution_profile") or result.usage.get("execution_profile") or "UNSPECIFIED_PROFILE")
    else:
        input_ids, input_versions, input_checksums = _input_rows_from_output(result.output)
        prompt_version = str(result.usage.get("prompt_version") or result.usage["skill_version"])
        handoff_target = str(result.usage.get("handoff_target") or "NONE")
        execution_profile = str(result.usage.get("execution_profile") or "UNSPECIFIED_PROFILE")
    provenance_config = request.config if request is not None else result.usage
    modification_manifest = _modification_manifest(request) if request is not None else {
        "source": "RUNTIME_PRE_POST_DIFF_UNAVAILABLE",
        "modified_artifact_ids": [],
        "modified_artifact_paths": [],
    }
    functional_identity = _non_null({
        "mission_id": provenance_config.get("mission_id"),
        "capability_id": provenance_config.get("capability_id") or getattr(request, "capability_id", None),
        "role_id": provenance_config.get("role_id") or role,
        "execution_profile_id": provenance_config.get("execution_profile_id") or execution_profile,
    })
    reproducibility = _non_null({
        "mission_contract_sha256": provenance_config.get("mission_contract_sha256"),
        "context_manifest_sha256": provenance_config.get("resolved_context_manifest_sha256"),
        "prompt_sha256": provenance_config.get("prompt_artifact_sha256") or provenance_config.get("prompt_checksum"),
        "input_sha256": provenance_config.get("input_sha256") or provenance_config.get("input_checksum"),
        "output_sha256": provenance_config.get("output_sha256") or result.output_checksum,
    })
    operational_telemetry = _non_null({
        "provider": result.provider,
        "model": result.model,
        "actual_provider": result.usage.get("actual_provider") or provenance_config.get("resolved_actual_provider"),
        "actual_model": result.usage.get("actual_model") or provenance_config.get("resolved_actual_model"),
        "input_tokens": result.usage.get("input_tokens"),
        "output_tokens": result.usage.get("output_tokens"),
        "cached_tokens": result.usage.get("cached_tokens"),
        "cost": result.usage.get("cost") or result.usage.get("estimated_cost"),
        "currency": result.usage.get("currency"),
        "latency": result.usage.get("latency"),
        "fallback": result.usage.get("fallback"),
    })
    registry["runs"].append({
        "run_id": result.run_id,
        "episode_id": result.episode_id,
        "role": role,
        "skill_id": result.usage["skill_id"],
        "skill_version": result.usage["skill_version"],
        "provider_or_adapter": result.provider,
        "provider_kind": str(result.usage.get("provider_kind") or ("SYNTHETIC" if execution_mode == "SYNTHETIC" else "REAL")),
        "model_or_evaluator": result.model,
        "input_manifest_checksum": result.input_manifest_checksum,
        "outputs": outputs,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "status": "SUCCEEDED",
        "execution_mode": execution_mode,
        "prompt_id": str(provenance_config.get("prompt_id") or "UNSPECIFIED_PROMPT"),
        "prompt_checksum": str(provenance_config.get("prompt_checksum") or "0" * 64),
        "input_checksum": str(provenance_config.get("input_checksum") or result.input_manifest_checksum),
        "output_checksum": str(result.output_checksum),
        "validation_result": str(provenance_config.get("validation_result") or "PASS"),
        "modification_manifest_source": modification_manifest["source"],
        "modified_artifact_ids": modification_manifest["modified_artifact_ids"],
        "modified_artifact_paths": modification_manifest["modified_artifact_paths"],
        "functional_identity": functional_identity,
        "reproducibility": reproducibility,
        "operational_telemetry": operational_telemetry,
        **{key: provenance_config[key] for key in ("mission_id", "capability_id", "execution_profile_id", "mission_contract_sha256", "resolved_context_manifest", "resolved_context_manifest_sha256", "input_sha256", "output_sha256", "prompt_artifact_sha256", "result_status") if provenance_config.get(key)},
        **_provenance_fields(
            role=role,
            provider=result.provider,
            model=result.model,
            execution_profile=execution_profile,
            prompt_version=prompt_version,
            started_at=result.started_at,
            finished_at=result.completed_at,
            input_artifact_ids=input_ids,
            input_versions=input_versions,
            input_checksums=input_checksums,
            output_artifact_ids=output_ids,
            output_versions=output_versions,
            output_checksums=output_checksums,
            usage=result.usage,
            decision="SUCCEEDED",
            blocking_reason=result.error,
            handoff_target=handoff_target,
        ),
    })
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))
    _write_registry(path, registry)

def append_attempt(
    path: Path,
    result: ExecutionResult,
    *,
    execution_mode: str,
    role: str = "UNSPECIFIED_PRODUCER",
    request: Any | None = None,
) -> None:
    """Registra intentos fallidos o bloqueados sin contarlos como runs exitosos."""
    if result.status is ExecutionStatus.SUCCEEDED:
        return
    if not result.error:
        raise ValueError("ExecutionResult fallido requiere error")
    registry = load_registry(path)
    attempt_id = f"ATTEMPT-{result.run_id}"
    if any(item.get("attempt_id") == attempt_id for item in registry["attempts"]):
        raise ValueError(f"attempt_id duplicado en provenance: {attempt_id}")
    provenance_config = request.config if request is not None else result.usage
    prompt_id = str(provenance_config.get("prompt_id") or "UNSPECIFIED_PROMPT")
    prompt_version = str(
        provenance_config.get("prompt_version")
        or result.usage.get("prompt_version")
        or result.usage.get("skill_version")
        or "UNSPECIFIED_PROMPT_VERSION"
    )
    execution_profile = str(
        getattr(request, "execution_profile", None)
        or provenance_config.get("execution_profile")
        or result.usage.get("execution_profile")
        or "UNSPECIFIED_PROFILE"
    )
    execution_route = str(
        provenance_config.get("execution_route")
        or getattr(request, "execution_route", None)
        or result.usage.get("execution_route")
        or f"native:{result.provider}"
    )
    record = {
        "attempt_id": attempt_id,
        "run_id": result.run_id,
        "status": _attempt_status(result),
        "error": str(result.error),
        "role_id": role,
        "provider": str(result.provider or "UNSPECIFIED_PROVIDER"),
        "model": str(result.model or "UNSPECIFIED_MODEL"),
        "execution_profile": execution_profile,
        "execution_route": execution_route,
        "actual_executor": str(
            result.usage.get("actual_executor")
            or provenance_config.get("resolved_actual_executor")
            or "native_provider"
        ),
        "actual_provider": str(
            result.usage.get("actual_provider")
            or provenance_config.get("resolved_actual_provider")
            or result.provider
            or "UNSPECIFIED_PROVIDER"
        ),
        "actual_model": str(
            result.usage.get("actual_model")
            or provenance_config.get("resolved_actual_model")
            or result.model
            or "UNSPECIFIED_MODEL"
        ),
        "started_at": result.started_at,
        "finished_at": result.completed_at,
        "latency": _seconds_between(result.started_at, result.completed_at),
        "execution_mode": execution_mode,
        "prompt_id": prompt_id,
        "prompt_version": prompt_version,
        "prompt_checksum": str(provenance_config.get("prompt_checksum") or "0" * 64),
        "input_checksum": str(provenance_config.get("input_checksum") or result.input_manifest_checksum or "0" * 64),
        "output_checksum": str(result.output_checksum or "0" * 64),
        "validation_result": str(provenance_config.get("validation_result") or "NOT_REACHED"),
    }
    if provenance_config.get("metadata_origin"):
        record["metadata_origin"] = str(provenance_config["metadata_origin"])
    if provenance_config.get("evidence_path"):
        record["evidence_path"] = str(provenance_config["evidence_path"])
    if provenance_config.get("notes"):
        record["notes"] = [str(item) for item in provenance_config["notes"]]
    registry["attempts"].append(record)
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))
    _write_registry(path, registry)
