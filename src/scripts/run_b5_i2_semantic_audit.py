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
from src.ai.execution import editorial_projection_schema, execute, manifest_checksum
from src.ai.manifest import file_checksum
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.registry import append_result, consume_handoff, skill_checksum, validate_handoff
from src.core.contract_validation import validate_against_schema


SKILL_PATH = Path(".agent/skills/skill_auditar_suficiencia_semantica_b5_i2.md")
AUDITOR_CAPABILITY = "B5_I2_SEMANTIC_AUDITOR"
AUDITOR_ROLE = "INDEPENDENT_EDITORIAL_AUDITOR"
CRITICAL_CRITERIA = (
    "ANALYSIS_SPECIFICITY",
    "EVIDENCE_TRACEABILITY",
    "EPISTEMIC_SEPARATION",
    "MATERIAL_COVERAGE",
    "CURATION_FUNCTION",
    "CURATION_CONTRAST_AND_PROGRESSION",
    "THESIS_REFINEMENT_SUBSTANCE",
    "THESIS_ARGUMENTATIVE_QUALITY",
    "MATERIAL_THESIS_CONTRIBUTION",
    "INHERITED_RESTRICTIONS",
    "B5_I3_READINESS",
)
REQUIRED_AUDIT_INPUT_KINDS = {"research", "evidence_report", "provisional_thesis", "analysis", "curation", "refined_thesis", "script_promise"}
OPTIONAL_AUDIT_INPUT_KINDS = {"early_packaging_hypothesis"}


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _validate_audit_inputs(artifacts: list[InputArtifact]) -> str | None:
    kinds = {item.artifact_kind for item in artifacts}
    missing = REQUIRED_AUDIT_INPUT_KINDS - kinds
    unsupported = kinds - REQUIRED_AUDIT_INPUT_KINDS - OPTIONAL_AUDIT_INPUT_KINDS
    if missing or unsupported:
        details = []
        if missing:
            details.append("faltan: " + ", ".join(sorted(missing)))
        if unsupported:
            details.append("no admitidos: " + ", ".join(sorted(unsupported)))
        return "inputs de auditoría B5-I2 inválidos; " + "; ".join(details)
    return None


def build_editorial_prompt(request: ExecutionRequest) -> str:
    artifacts = [
        {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "content": item.path.read_text(encoding="utf-8")}
        for item in request.input_artifacts
    ]
    schema_projection = editorial_projection_schema(request.output_schema)
    return "\n\n".join((
        "Eres el auditor editorial independiente de B5-I2.",
        f"Skill obligatoria: {request.skill_id}@{request.skill_version}.",
        "Aplica sus instrucciones editoriales: " + _skill_text(),
        "Criterios críticos obligatorios: " + ", ".join(CRITICAL_CRITERIA) + ".",
        "No apliques reglas heredadas de QA de guion: ni número fijo de eventos, ni ejemplos obligatorios, ni re-hooks, ni regla 80/20, ni estructura de guion terminado.",
        "EarlyPackagingHypothesis es opcional, de solo lectura y no bloquea por ausencia. Si existe, solo permite una observación de honestidad para YOUTUBE_ADAPTATION; no evalúes título, miniatura, clic ni packaging.",
        "Debes emitir solo el dictamen editorial: decision en PASS, WARN, FAIL o BLOCKED.",
        "No decidas readiness operativo ni campos técnicos; eso lo inyecta el runtime.",
        "Esta auditoría no autoriza B5-I3.",
        "Distingue SEMANTIC_AUDIT_INTEGRITY (lo impondrá el runtime) de SEMANTIC_EDITORIAL_DECISION (tu dictamen).",
        "No inventes provenance, runs, checksums ni timestamps. Ancla cada hallazgo a contenido concreto.",
        "Devuelve exclusivamente un objeto JSON que respete esta proyección editorial del schema estructural: " + json.dumps(schema_projection, ensure_ascii=False),
        "Artefactos reales a evaluar: " + json.dumps(artifacts, ensure_ascii=False),
    ))


def _operational_readiness(result: ExecutionResult, editorial_decision: str) -> str:
    provider_kind = str(result.usage.get("provider_kind") or "").upper()
    if editorial_decision == "FAIL":
        return "NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"
    if editorial_decision in {"BLOCKED", "NOT_EVALUATED"}:
        return "BLOCKED"
    if result.status is not ExecutionStatus.SUCCEEDED:
        return "BLOCKED"
    if (provider_kind == "SYNTHETIC") or (not result.is_real_editorial_execution):
        return "BLOCKED"
    return "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"


def _runtime_audit(payload: dict[str, Any], request: ExecutionRequest, result: ExecutionResult) -> dict[str, Any]:
    """El payload es editorial; la provenance es propiedad exclusiva del runtime."""
    audit = dict(payload)
    artifact_checksums = [
        {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "checksum": file_checksum(item.path), "producer_run_id": item.producer_run_id}
        for item in request.input_artifacts
    ]
    findings = [item for item in audit.get("findings", []) if isinstance(item, dict)]
    cited_evidence = sorted({
        ref
        for finding in findings
        for anchored in finding.get("anchored_findings", [])
        if isinstance(anchored, dict)
        for ref in anchored.get("evidence_refs", [])
        if isinstance(ref, str) and ref
    })
    audit.update({
        "audit_id": audit.get("audit_id") or request.output_artifact_id,
        "episode_id": request.episode_id,
        "auditor_role": AUDITOR_ROLE,
        "auditor_run_id": result.run_id,
        "auditor_skill_id": request.skill_id,
        "auditor_skill_version": request.skill_version,
        "provider_or_adapter": result.provider,
        "model_or_evaluator": result.model,
        "execution_timestamp": result.completed_at,
        "input_manifest_checksum": result.input_manifest_checksum,
        "artifact_checksums": artifact_checksums,
        "audited_artifact_ids": [
            f"{item['artifact_kind']}:{item['artifact_id']}"
            for item in artifact_checksums
            if item["artifact_kind"] in {"analysis", "curation", "refined_thesis", "script_promise"}
        ],
        "audited_artifact_versions": [
            item
            for item in artifact_checksums
            if item["artifact_kind"] in {"analysis", "curation", "refined_thesis", "script_promise"}
        ],
        "criteria_results": [
            {"criterion": item.get("criterion", ""), "status": item.get("status", ""), "summary": item.get("rationale", "")}
            for item in findings
        ],
        "blocking_defects": audit.get("blocking_defects", []),
        "non_blocking_defects": audit.get("non_blocking_defects", []),
        "cited_evidence": audit.get("cited_evidence", cited_evidence),
        "required_corrections": audit.get("required_corrections", []),
        "unresolved_questions": audit.get("unresolved_questions", []),
        "inherited_restrictions_checked": audit.get("inherited_restrictions_checked", []),
        "auditor_statement": audit.get("auditor_statement") or f"Decision {audit.get('decision', 'UNSPECIFIED')} emitida sobre artefactos B5-I2 con evidencia citada.",
        "audit_method": "AI_SEMANTIC_REVIEW",
        "readiness": _operational_readiness(result, str(audit.get("decision") or "")),
        "created_at": result.completed_at,
    })
    return audit


def _transaction_paths(output_path: Path, registry_path: Path) -> dict[str, Path]:
    return {
        "journal": output_path.with_suffix(output_path.suffix + ".txn.json"),
        "audit_backup": output_path.with_suffix(output_path.suffix + ".bak"),
        "registry_backup": registry_path.with_suffix(registry_path.suffix + ".bak"),
    }


def _write_transaction_journal(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _cleanup_transaction_files(*paths: Path) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


def _restore_from_backup(target: Path, backup: Path, existed_before: bool) -> None:
    if existed_before:
        if not backup.exists():
            raise OSError(f"backup faltante para restaurar {target}")
        if target.exists():
            target.unlink()
        os.replace(backup, target)
        return
    target.unlink(missing_ok=True)
    backup.unlink(missing_ok=True)


def _recover_prepared_transaction(output_path: Path, registry_path: Path) -> None:
    txn_paths = _transaction_paths(output_path, registry_path)
    journal_path = txn_paths["journal"]
    if not journal_path.exists():
        return
    payload = json.loads(journal_path.read_text(encoding="utf-8"))
    status = str(payload.get("status") or "")
    if status == "PREPARED":
        _restore_from_backup(output_path, txn_paths["audit_backup"], bool(payload.get("audit_existed")))
        _restore_from_backup(registry_path, txn_paths["registry_backup"], bool(payload.get("registry_existed")))
        payload["status"] = "ROLLED_BACK"
        _write_transaction_journal(journal_path, payload)
        journal_path.unlink(missing_ok=True)
        return
    if status == "COMMITTED":
        _cleanup_transaction_files(txn_paths["audit_backup"], txn_paths["registry_backup"], journal_path)
        return
    _cleanup_transaction_files(txn_paths["audit_backup"], txn_paths["registry_backup"], journal_path)


def _atomic_persist(output_path: Path, registry_path: Path, audit: dict[str, Any], result: ExecutionResult, *, handoff_package: dict[str, Any] | None = None, current_skill_checksum: str | None = None) -> None:
    """Prevalida y sustituye los documentos de auditoría+provenance como una sola unidad."""
    _recover_prepared_transaction(output_path, registry_path)
    output_bytes = json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    old_audit = output_path.read_bytes() if output_path.exists() else None
    old_registry = registry_path.read_bytes() if registry_path.exists() else None
    draft_registry_path = registry_path.with_suffix(registry_path.suffix + ".draft")
    txn_paths = _transaction_paths(output_path, registry_path)
    journal_payload = {
        "status": "PREPARED",
        "audit_path": str(output_path),
        "registry_path": str(registry_path),
        "audit_existed": old_audit is not None,
        "registry_existed": old_registry is not None,
    }
    try:
        # append_result remains canonical for registry shape and validation.
        draft_registry_path.write_bytes(old_registry or b'{"registry_version":"1.0.0","runs":[]}')
        append_result(draft_registry_path, result, execution_mode="REAL", role=AUDITOR_ROLE)
        if handoff_package:
            consume_handoff(
                draft_registry_path,
                package=handoff_package,
                result_run_id=result.run_id,
                output_checksum=result.output_checksum or "",
                current_skill_checksum=current_skill_checksum or skill_checksum(),
            )
        registry_bytes = draft_registry_path.read_bytes()
        with tempfile.NamedTemporaryFile(delete=False, dir=output_path.parent, suffix=".tmp") as audit_tmp:
            audit_tmp.write(output_bytes); audit_name = audit_tmp.name
        with tempfile.NamedTemporaryFile(delete=False, dir=registry_path.parent, suffix=".tmp") as registry_tmp:
            registry_tmp.write(registry_bytes); registry_name = registry_tmp.name
        if old_audit is not None:
            txn_paths["audit_backup"].write_bytes(old_audit)
        else:
            txn_paths["audit_backup"].unlink(missing_ok=True)
        if old_registry is not None:
            txn_paths["registry_backup"].write_bytes(old_registry)
        else:
            txn_paths["registry_backup"].unlink(missing_ok=True)
        _write_transaction_journal(txn_paths["journal"], journal_payload)
        try:
            os.replace(audit_name, output_path)
            os.replace(registry_name, registry_path)
            journal_payload["status"] = "COMMITTED"
            _write_transaction_journal(txn_paths["journal"], journal_payload)
            _cleanup_transaction_files(txn_paths["audit_backup"], txn_paths["registry_backup"], txn_paths["journal"])
        except Exception:
            _recover_prepared_transaction(output_path, registry_path)
            raise
    finally:
        draft_registry_path.unlink(missing_ok=True)
        for name in (locals().get("audit_name"), locals().get("registry_name")):
            if name:
                Path(name).unlink(missing_ok=True)


def execute_b5_i2_audit(*, artifacts: list[InputArtifact], output_path: Path, registry_path: Path, episode_id: str = "", provider: str | None = None, execution_mode: str = "auto", model: str | None = None, timeout: float = 30.0, mock_output: dict | None = None, handoff_directory: Path | None = None, config: dict[str, Any] | None = None) -> ExecutionResult:
    input_error = _validate_audit_inputs(artifacts)
    if input_error:
        return ExecutionResult(run_id="", status=ExecutionStatus.FAILED, executor_type="validation", provider=provider or "none", model=model or "none", input_manifest_checksum="", output=None, output_checksum=None, started_at="", completed_at="", error=input_error)
    request = ExecutionRequest(
        capability_id=AUDITOR_CAPABILITY, skill_id="skill_auditar_suficiencia_semantica_b5_i2", skill_version="1.0.0",
        input_artifacts=artifacts, output_schema="b5_i2_semantic_sufficiency_audit", execution_mode=execution_mode,
        provider=provider, model=model, timeout=timeout, output_artifact_kind="semantic_audit", output_artifact_id="B5I2-SSA-1", output_artifact_ref="semantic_audit:B5I2-SSA-1", mock_output=mock_output,
        handoff_directory=handoff_directory, config={**(config or {}), "execution_registry_path": str(registry_path)}, episode_id=episode_id, role=AUDITOR_ROLE,
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
    result = replace(result, output=audit, output_checksum=None, output_artifact_id=audit["audit_id"], output_artifact_kind="semantic_audit", output_artifact_ref=f"semantic_audit:{audit['audit_id']}")
    result = replace(result, output_checksum=__import__("hashlib").sha256(json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8") + b"\n").hexdigest())
    try:
        _atomic_persist(output_path, registry_path, audit, result)
    except (OSError, ValueError) as exc:
        return replace(result, status=ExecutionStatus.FAILED, error=f"persistencia atómica falló: {exc}")
    return result


def import_b5_i2_handoff(*, package_path: Path, result_path: Path, artifacts: list[InputArtifact], output_path: Path, registry_path: Path, episode_id: str, provider: str = "agent_handoff", model: str = "external-agent") -> ExecutionResult:
    """Importa un dictamen de un paquete exacto; nunca acepta provenance del agente."""
    input_error = _validate_audit_inputs(artifacts)
    if input_error:
        return ExecutionResult(run_id="", status=ExecutionStatus.FAILED, executor_type="validation", provider=provider, model=model, input_manifest_checksum="", output=None, output_checksum=None, started_at="", completed_at="", error=input_error)
    package = json.loads(package_path.read_text(encoding="utf-8"))
    request = ExecutionRequest(
        capability_id=AUDITOR_CAPABILITY, skill_id="skill_auditar_suficiencia_semantica_b5_i2", skill_version="1.0.0",
        input_artifacts=artifacts, output_schema="b5_i2_semantic_sufficiency_audit", output_artifact_kind="semantic_audit", output_artifact_id="B5I2-SSA-1", output_artifact_ref="semantic_audit:B5I2-SSA-1",
        episode_id=episode_id, role=AUDITOR_ROLE,
    )
    computed_manifest = manifest_checksum(request)
    if package.get("input_manifest_checksum") != computed_manifest or package.get("episode_id") != episode_id:
        return ExecutionResult(run_id="", status=ExecutionStatus.FAILED, executor_type="handoff", provider=provider, model=model, input_manifest_checksum=computed_manifest, output=None, output_checksum=None, started_at="", completed_at="", error="paquete no corresponde a los inputs actuales")
    try:
        validate_handoff(registry_path, package=package, current_skill_checksum=skill_checksum())
        editorial_payload = AgentHandoffProvider().import_result(package_path, result_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ExecutionResult(run_id="", status=ExecutionStatus.FAILED, executor_type="handoff", provider=provider, model=model, input_manifest_checksum=computed_manifest, output=None, output_checksum=None, started_at="", completed_at="", error=str(exc))
    from src.ai.execution import _now  # mantiene un único formato de timestamp del runtime
    run_id, timestamp = f"RUN-AI-IMPORT-{package['handoff_id'].replace('RUN-AI-', '')}", _now()
    result = ExecutionResult(run_id, ExecutionStatus.SUCCEEDED, "handoff", provider, model, computed_manifest, editorial_payload, None, timestamp, timestamp, usage={"skill_id": request.skill_id, "skill_version": request.skill_version}, episode_id=request.episode_id, output_artifact_id=request.output_artifact_id, output_artifact_kind="semantic_audit", output_artifact_ref=request.output_artifact_ref, is_real_editorial_execution=True)
    audit = _runtime_audit(editorial_payload, request, result)
    violations = validate_against_schema(audit, request.output_schema)
    if violations:
        return replace(result, status=ExecutionStatus.FAILED, output=audit, error="output B5-I2 inválido: " + "; ".join(violations))
    result = replace(result, output=audit, output_artifact_id=audit["audit_id"], output_checksum=__import__("hashlib").sha256(json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8") + b"\n").hexdigest())
    try:
        _atomic_persist(output_path, registry_path, audit, result, handoff_package=package, current_skill_checksum=skill_checksum())
    except (OSError, ValueError) as exc:
        return replace(result, status=ExecutionStatus.FAILED, error=f"persistencia atómica falló: {exc}")
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
