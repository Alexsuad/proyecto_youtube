"""Paquetes verificables para ejecución humana/agéntica fuera del proceso local."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ai.contracts import ExecutionRequest
from src.ai.manifest import build_input_manifest, canonical_json, file_checksum
from src.ai.registry import skill_checksum
from src.core.mission_completion_gate import validate_verified_completion_gate, verify_completion_gate_for_repository


def load_verified_completion_gate_from_payload(data: dict[str, Any] | None):
    if not isinstance(data, dict):
        raise PermissionError("MISSION_COMPLETION_GATE_REQUIRED: package lacks completion gate")
    try:
        from src.core.gate_result import GateResult

        result = GateResult.from_dict(data)
    except (ValueError, TypeError) as exc:
        raise PermissionError(f"MISSION_COMPLETION_GATE_REQUIRED: {exc}") from exc
    return validate_verified_completion_gate(result)


def checksum(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class AgentHandoffProvider:
    name = "agent_handoff"

    def prepare(self, request: ExecutionRequest, manifest_checksum: str, run_id: str) -> Path:
        gate_path = request.config.get("completion_gate_result_path")
        contract_path = request.config.get("mission_contract_path")
        repo_root = request.config.get("mission_repo_root")
        if not gate_path or not contract_path or not repo_root:
            raise PermissionError(
                "MISSION_COMPLETION_GATE_REQUIRED: handoff requires gate result, mission contract and repository root"
            )
        completion_gate = verify_completion_gate_for_repository(gate_path, contract_path, repo_root)
        directory = request.handoff_directory or Path("handoff")
        directory.mkdir(parents=True, exist_ok=True)
        artifacts = [
            {"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "artifact_checksum": file_checksum(item.path),
             "content": item.path.read_text(encoding="utf-8")}
            for item in request.input_artifacts
        ]
        package = {
            "handoff_id": run_id,
            "capability_id": request.capability_id,
            "episode_id": request.episode_id,
            "skill_id": request.skill_id,
            "skill_version": request.skill_version,
            "skill_checksum": skill_checksum(),
            "input_manifest_checksum": manifest_checksum,
            "input_manifest": build_input_manifest(request.episode_id, artifacts),
            "output_schema": request.output_schema,
            "prompt": request.config.get("prompt", ""),
            "expected_provider_or_agent": request.config.get("expected_provider_or_agent"),
            "artifacts": artifacts,
            "completion_gate": completion_gate.to_dict(),
        }
        package["package_checksum"] = checksum(canonical_json(package))
        path = directory / f"{run_id}.json"
        path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def import_result(self, package_path: Path, result_path: Path) -> dict[str, Any]:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        expected_checksum = package.pop("package_checksum", None)
        if expected_checksum != checksum(canonical_json(package)):
            raise ValueError("checksum incorrecto en paquete de handoff")
        try:
            load_verified_completion_gate_from_payload(package.get("completion_gate"))
        except PermissionError as exc:
            raise PermissionError(str(exc)) from exc
        if (payload.get("handoff_id") != package["handoff_id"] or payload.get("package_checksum") != expected_checksum
                or payload.get("input_manifest_checksum") != package["input_manifest_checksum"]
                or payload.get("skill_id") != package["skill_id"] or payload.get("skill_version") != package["skill_version"]):
            raise ValueError("resultado importado no corresponde al paquete de handoff")
        content = payload.get("output")
        encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        if payload.get("output_checksum") != checksum(encoded):
            raise ValueError("checksum incorrecto en resultado importado")
        return content
