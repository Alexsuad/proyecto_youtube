"""Ejecución e importación verificable de la auditoría semántica B5-I2."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute, manifest_checksum
from src.ai.manifest import file_checksum
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.registry import append_result, consume_handoff, skill_checksum, validate_handoff
from src.core.contract_validation import validate_against_schema


SKILL_PATH = Path(".agent/skills/skill_qa_editorial.md")
CRITICAL_CRITERIA = ("ANALYSIS_SPECIFICITY", "CURATION_CONTRAST_AND_PROGRESSION", "THESIS_REFINEMENT_SUBSTANCE")


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def build_editorial_prompt(request: ExecutionRequest) -> str:
    artifacts = [
        {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "content": item.path.read_text(encoding="utf-8")}
        for item in request.input_artifacts
    ]
    schema = Path("schemas") / f"{request.output_schema}.json"
    return "\n\n".join((
        "Eres el auditor editorial independiente de B5-I2.",
        f"Skill obligatoria: {request.skill_id}@{request.skill_version}.",
        "Aplica sus instrucciones editoriales: " + _skill_text(),
        "Criterios críticos obligatorios: " + ", ".join(CRITICAL_CRITERIA) + ".",
        "Distingue SEMANTIC_AUDIT_INTEGRITY (lo impondrá el runtime) de SEMANTIC_EDITORIAL_DECISION (tu dictamen).",
        "No inventes provenance, runs, checksums ni timestamps. Ancla cada hallazgo a contenido concreto.",
        "Devuelve exclusivamente un objeto JSON que respete este schema estructural: " + schema.read_text(encoding="utf-8"),
        "Artefactos reales a evaluar: " + json.dumps(artifacts, ensure_ascii=False),
    ))


def _runtime_audit(payload: dict[str, Any], request: ExecutionRequest, result: ExecutionResult) -> dict[str, Any]:
    """El payload es editorial; la provenance es propiedad exclusiva del runtime."""
    audit = dict(payload)
    audit.update({
        "audit_id": audit.get("audit_id") or request.output_artifact_id,
        "episode_id": request.episode_id,
        "auditor_role": "INDEPENDENT_EDITORIAL_AUDITOR",
        "auditor_run_id": result.run_id,
        "auditor_skill_id": request.skill_id,
        "auditor_skill_version": request.skill_version,
        "provider_or_adapter": result.provider,
        "model_or_evaluator": result.model,
        "execution_timestamp": result.completed_at,
        "input_manifest_checksum": result.input_manifest_checksum,
        "artifact_checksums": [
            {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id,
             "checksum": file_checksum(item.path), "producer_run_id": item.producer_run_id}
            for item in request.input_artifacts
        ],
        "audit_method": "AI_SEMANTIC_REVIEW",
        "created_at": result.completed_at,
    })
    return audit


def _atomic_persist(output_path: Path, registry_path: Path, audit: dict[str, Any], result: ExecutionResult) -> None:
    """Prevalida y sustituye los dos documentos; si falla el segundo, restaura el primero."""
    output_bytes = json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    old_audit = output_path.read_bytes() if output_path.exists() else None
    old_registry = registry_path.read_bytes() if registry_path.exists() else None
    draft_registry_path = registry_path.with_suffix(registry_path.suffix + ".draft")
    try:
        # append_result remains canonical for registry shape and validation.
        draft_registry_path.write_bytes(old_registry or b'{"registry_version":"1.0.0","runs":[]}')
        append_result(draft_registry_path, result, execution_mode="REAL")
        registry_bytes = draft_registry_path.read_bytes()
        with tempfile.NamedTemporaryFile(delete=False, dir=output_path.parent, suffix=".tmp") as audit_tmp:
            audit_tmp.write(output_bytes); audit_name = audit_tmp.name
        with tempfile.NamedTemporaryFile(delete=False, dir=registry_path.parent, suffix=".tmp") as registry_tmp:
            registry_tmp.write(registry_bytes); registry_name = registry_tmp.name
        try:
            os.replace(audit_name, output_path)
            os.replace(registry_name, registry_path)
        except Exception:
            if old_audit is None:
                output_path.unlink(missing_ok=True)
            else:
                output_path.write_bytes(old_audit)
            if old_registry is not None:
                registry_path.write_bytes(old_registry)
            raise
    finally:
        draft_registry_path.unlink(missing_ok=True)
        for name in (locals().get("audit_name"), locals().get("registry_name")):
            if name:
                Path(name).unlink(missing_ok=True)


def execute_b5_i2_audit(*, artifacts: list[InputArtifact], output_path: Path, registry_path: Path, episode_id: str = "", provider: str | None = None, execution_mode: str = "auto", model: str | None = None, timeout: float = 30.0, mock_output: dict | None = None, handoff_directory: Path | None = None, config: dict[str, Any] | None = None) -> ExecutionResult:
    request = ExecutionRequest(
        capability_id="editorial_semantic_audit_b5_i2", skill_id="skill_qa_editorial", skill_version="2.0.0",
        input_artifacts=artifacts, output_schema="b5_i2_semantic_sufficiency_audit", execution_mode=execution_mode,
        provider=provider, model=model, timeout=timeout, output_artifact_id="B5I2-SSA-1", mock_output=mock_output,
        handoff_directory=handoff_directory, config={**(config or {}), "execution_registry_path": str(registry_path)}, episode_id=episode_id,
    )
    request.config["prompt"] = build_editorial_prompt(request)
    result = execute(request)
    if result.status is not ExecutionStatus.SUCCEEDED:
        return result
    if not result.is_real_editorial_execution:
        return replace(result, status=ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, error="mock solo valida el flujo estructural; no cierra la auditoría editorial")
    audit = _runtime_audit(result.output or {}, request, result)
    violations = validate_against_schema(audit, request.output_schema)
    if violations:
        return replace(result, status=ExecutionStatus.FAILED, output=audit, error="output B5-I2 inválido: " + "; ".join(violations))
    result = replace(result, output=audit, output_checksum=None, output_artifact_id=audit["audit_id"])
    result = replace(result, output_checksum=__import__("hashlib").sha256(json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8") + b"\n").hexdigest())
    try:
        _atomic_persist(output_path, registry_path, audit, result)
    except (OSError, ValueError) as exc:
        return replace(result, status=ExecutionStatus.FAILED, error=f"persistencia atómica falló: {exc}")
    return result


def import_b5_i2_handoff(*, package_path: Path, result_path: Path, artifacts: list[InputArtifact], output_path: Path, registry_path: Path, episode_id: str, provider: str = "agent_handoff", model: str = "external-agent") -> ExecutionResult:
    """Importa un dictamen de un paquete exacto; nunca acepta provenance del agente."""
    package = json.loads(package_path.read_text(encoding="utf-8"))
    request = ExecutionRequest(
        capability_id="editorial_semantic_audit_b5_i2", skill_id="skill_qa_editorial", skill_version="2.0.0",
        input_artifacts=artifacts, output_schema="b5_i2_semantic_sufficiency_audit", output_artifact_id="B5I2-SSA-1",
        episode_id=episode_id,
    )
    computed_manifest = manifest_checksum(request)
    if package.get("input_manifest_checksum") != computed_manifest or package.get("episode_id") != episode_id:
        return ExecutionResult("", ExecutionStatus.FAILED, "handoff", provider, model, computed_manifest, None, None, "", "", "paquete no corresponde a los inputs actuales")
    try:
        validate_handoff(registry_path, package=package, current_skill_checksum=skill_checksum())
        editorial_payload = AgentHandoffProvider().import_result(package_path, result_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ExecutionResult("", ExecutionStatus.FAILED, "handoff", provider, model, computed_manifest, None, None, "", "", str(exc))
    from src.ai.execution import _now  # mantiene un único formato de timestamp del runtime
    run_id, timestamp = f"RUN-AI-IMPORT-{package['handoff_id'].replace('RUN-AI-', '')}", _now()
    result = ExecutionResult(run_id, ExecutionStatus.SUCCEEDED, "handoff", provider, model, computed_manifest, editorial_payload, None, timestamp, timestamp, usage={"skill_id": request.skill_id, "skill_version": request.skill_version}, output_artifact_id=request.output_artifact_id, is_real_editorial_execution=True)
    audit = _runtime_audit(editorial_payload, request, result)
    violations = validate_against_schema(audit, request.output_schema)
    if violations:
        return replace(result, status=ExecutionStatus.FAILED, output=audit, error="output B5-I2 inválido: " + "; ".join(violations))
    result = replace(result, output=audit, output_artifact_id=audit["audit_id"], output_checksum=__import__("hashlib").sha256(json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8") + b"\n").hexdigest())
    try:
        _atomic_persist(output_path, registry_path, audit, result)
    except (OSError, ValueError) as exc:
        return replace(result, status=ExecutionStatus.FAILED, error=f"persistencia atómica falló: {exc}")
    try:
        consume_handoff(registry_path, package=package, result_run_id=result.run_id, output_checksum=result.output_checksum or "", current_skill_checksum=skill_checksum())
    except (OSError, ValueError) as exc:
        return replace(result, status=ExecutionStatus.FAILED, error=f"handoff no pudo consumirse: {exc}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", action="append", required=True, metavar="KIND:ID:PATH[:PRODUCER_RUN]")
    parser.add_argument("--output", required=True); parser.add_argument("--execution-registry", required=True)
    parser.add_argument("--episode-id", required=True); parser.add_argument("--provider"); parser.add_argument("--execution-mode", default="auto")
    parser.add_argument("--model"); parser.add_argument("--timeout", type=float, default=30.0); parser.add_argument("--handoff-directory")
    parser.add_argument("--import-package"); parser.add_argument("--import-result")
    args = parser.parse_args()
    artifacts = []
    for value in args.artifact:
        parts = value.split(":", 3)
        if len(parts) not in (3, 4): parser.error("--artifact requiere KIND:ID:PATH[:PRODUCER_RUN]")
        artifacts.append(InputArtifact(parts[0], parts[1], Path(parts[2]), parts[3] if len(parts) == 4 else ""))
    if bool(args.import_package) != bool(args.import_result):
        parser.error("--import-package y --import-result se usan juntos")
    if args.import_package:
        result = import_b5_i2_handoff(package_path=Path(args.import_package), result_path=Path(args.import_result), artifacts=artifacts, output_path=Path(args.output), registry_path=Path(args.execution_registry), episode_id=args.episode_id, model=args.model or "external-agent")
    else:
        result = execute_b5_i2_audit(artifacts=artifacts, output_path=Path(args.output), registry_path=Path(args.execution_registry), episode_id=args.episode_id, provider=args.provider, execution_mode=args.execution_mode, model=args.model, timeout=args.timeout, handoff_directory=Path(args.handoff_directory) if args.handoff_directory else None)
    print(json.dumps({"run_id": result.run_id, "status": result.status.value, "error": result.error}, ensure_ascii=False))
    return 0 if result.status.value in {"SUCCEEDED", "HANDOFF_PREPARED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
