"""Operaciones sobre la sede canónica de provenance de ejecuciones."""
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ai.contracts import ExecutionResult, ExecutionStatus
from src.ai.manifest import canonical_json, file_checksum
from src.core.contract_validation import validate_against_schema

B5_I2_ROLE_ARTIFACT_COMPATIBILITY = {
    "ANALYSIS_PRODUCER": "analysis",
    "CURATION_PRODUCER": "curation",
    "THESIS_PRODUCER": "refined_thesis",
    "SCRIPT_PROMISE_PRODUCER": "script_promise",
    "INDEPENDENT_EDITORIAL_AUDITOR": "semantic_audit",
}
B5_I2_ARTIFACT_KINDS = set(B5_I2_ROLE_ARTIFACT_COMPATIBILITY.values())


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"registry_version": "1.0.0", "runs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def skill_checksum(skill_path: Path | None = None) -> str:
    path = skill_path or Path(".agent/skills/skill_auditar_suficiencia_semantica_b5_i2.md")
    return file_checksum(path)


def package_checksum(package: dict[str, Any]) -> str:
    content = {key: value for key, value in package.items() if key != "package_checksum"}
    return hashlib.sha256(canonical_json(content)).hexdigest()


def register_handoff(path: Path, package_path: Path, request: Any) -> None:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    registry = load_registry(path)
    registry.setdefault("handoffs", [])
    if any(item.get("handoff_id") == package.get("handoff_id") for item in registry["handoffs"]):
        raise ValueError("handoff_id duplicado en provenance")
    registry["handoffs"].append({
        "handoff_id": package["handoff_id"], "capability_id": package["capability_id"], "episode_id": package["episode_id"],
        "skill_id": package["skill_id"], "skill_version": package["skill_version"], "skill_checksum": package["skill_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"], "package_checksum": package["package_checksum"],
        "prepared_at": _now(), "status": "HANDOFF_PREPARED",
    })
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))
    _write_registry(path, registry)


def consume_handoff(path: Path, *, package: dict[str, Any], result_run_id: str, output_checksum: str, current_skill_checksum: str) -> None:
    record = validate_handoff(path, package=package, current_skill_checksum=current_skill_checksum)
    registry = load_registry(path)
    record = next(item for item in registry.get("handoffs", []) if item.get("handoff_id") == package.get("handoff_id"))
    record.update({"status": "HANDOFF_CONSUMED", "result_run_id": result_run_id, "output_checksum": output_checksum, "consumed_at": _now()})
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


def append_result(
    path: Path,
    result: ExecutionResult,
    *,
    execution_mode: str,
    role: str = "UNSPECIFIED_PRODUCER",
) -> None:
    """Registra solo ejecuciones que realmente produjeron un artefacto verificable."""
    if result.status is not ExecutionStatus.SUCCEEDED or not result.output_checksum:
        return
    if not result.output_artifact_kind or not result.output_artifact_id:
        raise ValueError("ExecutionResult requiere output_artifact_kind y output_artifact_id")
    if result.output_artifact_kind in B5_I2_ARTIFACT_KINDS and role not in B5_I2_ROLE_ARTIFACT_COMPATIBILITY:
        raise ValueError(f"role {role} no registrado para artifact_kind B5-I2 {result.output_artifact_kind}")
    if role in B5_I2_ROLE_ARTIFACT_COMPATIBILITY and result.output_artifact_kind != B5_I2_ROLE_ARTIFACT_COMPATIBILITY[role]:
        raise ValueError(f"role {role} incompatible con artifact_kind {result.output_artifact_kind}")
    if role in {"ANALYSIS_PRODUCER", "CURATION_PRODUCER", "THESIS_PRODUCER", "SCRIPT_PROMISE_PRODUCER"} and not result.output_artifact_path:
        raise ValueError(f"{role} requiere output_artifact_path verificable")
    if result.output_artifact_path:
        if not result.output_artifact_path.exists():
            raise ValueError(f"output inexistente: {result.output_artifact_path}")
        if file_checksum(result.output_artifact_path) != result.output_checksum:
            raise ValueError(f"checksum incorrecto para output: {result.output_artifact_path}")
    registry = load_registry(path)
    if any(run.get("run_id") == result.run_id for run in registry["runs"]):
        raise ValueError(f"run_id duplicado en provenance: {result.run_id}")
    outputs = [{
        "artifact_kind": result.output_artifact_kind,
        "artifact_id": result.output_artifact_id,
        "artifact_path": str(result.output_artifact_path) if result.output_artifact_path else None,
        "artifact_ref": result.output_artifact_ref or f"{result.output_artifact_kind}:{result.output_artifact_id}",
        "checksum": result.output_checksum,
    }]
    output_refs = [item["artifact_ref"] for item in outputs]
    if len(output_refs) != len(set(output_refs)):
        raise ValueError("outputs duplicados en el mismo run")
    registry["runs"].append(
        {
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
        }
    )
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))
    _write_registry(path, registry)
