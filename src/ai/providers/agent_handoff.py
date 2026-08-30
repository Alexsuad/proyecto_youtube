"""Paquetes verificables para ejecución humana/agéntica fuera del proceso local."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ai.contracts import ExecutionRequest
from src.ai.manifest import build_input_manifest, canonical_json, file_checksum
from src.ai.registry import skill_checksum
from src.core.mission_completion_gate import (
    load_mission_contract,
    validate_verified_completion_gate,
    verify_completion_gate_for_repository,
)
from src.core.mission_authorization import load_mission_authorization


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

    @staticmethod
    def _verify_pre_handoff_authorization(request: ExecutionRequest, repo_root: Path, directory: Path) -> None:
        """Verify execution authority without requiring final mission evidence.

        A completion gate is evidence produced after a mission.  The first
        handoff instead relies on the already verified execution preflight and
        the same mission/route bindings that preflight checked.
        """
        from src.ai.registry import _VERIFIED_AUTHORIZATION_TOKEN
        from src.core.execution_preflight import _load_registered_capability

        if request.config.get("_mission_authorization_token") is not _VERIFIED_AUTHORIZATION_TOKEN:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED_FOR_HANDOFF")
        authorization_path = request.config.get("mission_authorization_path")
        contract_path = request.config.get("mission_contract_path")
        if not authorization_path or not contract_path:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED: handoff bindings are incomplete")
        authorization_file = Path(str(authorization_path))
        contract_file = Path(str(contract_path))
        if authorization_file.is_absolute() or ".." in authorization_file.parts:
            raise PermissionError("MISSION_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY")
        if contract_file.is_absolute() or ".." in contract_file.parts:
            raise PermissionError("MISSION_CONTRACT_PATH_OUTSIDE_REPOSITORY")
        authorization_file = (repo_root / authorization_file).resolve(strict=True)
        contract_file = (repo_root / contract_file).resolve(strict=True)
        authorization_file.relative_to(repo_root)
        contract_file.relative_to(repo_root)
        contract = load_mission_contract(contract_file)
        authorization = load_mission_authorization(authorization_file)
        if contract.mission_id != authorization.mission_id:
            raise PermissionError("MISSION_CONTRACT_AUTHORIZATION_MISMATCH")
        capability = _load_registered_capability(repo_root, request.capability_id)
        authorization.verify(
            repo_root,
            capability_id=str(request.capability_id),
            role_id=str(request.role),
            operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
            execution_mode=str(request.execution_mode),
            execution_route=str(request.execution_route or "") or None,
            execution_family=str(request.execution_family or request.config.get("execution_family") or "") or None,
            execution_interface=str(request.config.get("execution_interface") or "") or None,
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )
        try:
            relative_directory = directory.resolve().relative_to(repo_root).as_posix()
        except ValueError as exc:
            raise PermissionError("HANDOFF_PATH_OUTSIDE_REPOSITORY") from exc
        authorization.verify(
            repo_root,
            capability_id=str(request.capability_id),
            role_id=str(request.role),
            operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
            path=relative_directory.rstrip("/") + "/",
            execution_mode=str(request.execution_mode),
            execution_route=str(request.execution_route or "") or None,
            execution_family=str(request.execution_family or request.config.get("execution_family") or "") or None,
            execution_interface=str(request.config.get("execution_interface") or "") or None,
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )

    def prepare(self, request: ExecutionRequest, manifest_checksum: str, run_id: str) -> Path:
        # Explicit runtime selections must arrive with the
        # resolver-owned route object.  A mutable request flag is diagnostic
        # only and cannot authorize preparation by itself.
        if request.execution_profile or request.execution_family or request.run_configuration is not None:
            from src.ai.runtime_profiles import READY, ResolvedExecutionRoute, _VERIFIED_ROUTE_TOKEN

            route = request.resolved_route
            if (
                not isinstance(route, ResolvedExecutionRoute)
                or route.status != READY
                or request.resolved_route_token is not _VERIFIED_ROUTE_TOKEN
            ):
                raise PermissionError("RUNTIME_CONFIGURATION_NOT_RESOLVED_BEFORE_HANDOFF")
            if (
                route.execution_profile != request.execution_profile
                or route.execution_family != (request.execution_family or request.config.get("execution_family"))
                or route.execution_route != request.execution_route
                or route.model != (request.model or "")
                or route.executor != (request.executor or "")
            ):
                raise PermissionError("RUNTIME_CONFIGURATION_RESOLUTION_BINDING_MISMATCH")
        gate_path = request.config.get("completion_gate_result_path")
        contract_path = request.config.get("mission_contract_path")
        repo_root = request.config.get("mission_repo_root")
        if not contract_path or not repo_root:
            raise PermissionError(
                "MISSION_COMPLETION_GATE_REQUIRED: handoff requires gate result, mission contract and repository root"
            )
        directory = request.handoff_directory or Path("handoff")
        if not directory.is_absolute():
            directory = Path(repo_root) / directory
        if gate_path:
            completion_gate = verify_completion_gate_for_repository(gate_path, contract_path, repo_root)
        else:
            self._verify_pre_handoff_authorization(request, Path(repo_root).resolve(), directory)
            completion_gate = None
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
            "execution_family": request.execution_family or request.config.get("execution_family"),
            "execution_profile": request.execution_profile,
            "execution_route": request.execution_route,
            "execution_mode": request.execution_mode,
            "model_override": None
            if (request.execution_family or request.config.get("execution_family")) == "AGENT_HARNESS"
            else request.model,
            "reasoning_effort": request.reasoning_effort,
            "artifacts": artifacts,
            **({"completion_gate": completion_gate.to_dict()} if completion_gate is not None else {}),
            **({"mission_id": request.config["mission_id"]} if request.config.get("mission_id") else {}),
            **({"mission_authorization_path": request.config["mission_authorization_path"]} if request.config.get("mission_authorization_path") else {}),
            **({"mission_contract_path": request.config["mission_contract_path"]} if request.config.get("mission_contract_path") else {}),
            **({"mission_repo_root": str(Path(repo_root).resolve())} if repo_root else {}),
            **({"stage": request.config["stage"]} if request.config.get("stage") else {}),
            **({"role": request.role} if request.role else {}),
            **({"expected_return": request.config["expected_return"]} if request.config.get("expected_return") else {}),
            **({"prompt_id": request.config["prompt_id"]} if request.config.get("prompt_id") else {}),
            **({"prompt_version": request.config["prompt_version"]} if request.config.get("prompt_version") else {}),
            **({"prompt_checksum": request.config["prompt_checksum"]} if request.config.get("prompt_checksum") else {}),
            **({"prompt_input_checksum": request.config["prompt_input_checksum"]} if request.config.get("prompt_input_checksum") else {}),
            **({"mission_convergence": request.config["_mission_convergence"]} if request.config.get("_mission_convergence") else {}),
            **({"strategic_return": request.config["strategic_return"]} if "strategic_return" in request.config else {}),
        }
        package["package_checksum"] = checksum(canonical_json(package))
        path = directory / f"{run_id}.json"
        path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def import_result(self, package_path: Path, result_path: Path) -> dict[str, Any]:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        expected_checksum = package.get("package_checksum")
        package_without_checksum = {key: value for key, value in package.items() if key != "package_checksum"}
        if expected_checksum != checksum(canonical_json(package_without_checksum)):
            raise ValueError("checksum incorrecto en paquete de handoff")
        try:
            if package.get("completion_gate") is not None:
                load_verified_completion_gate_from_payload(package.get("completion_gate"))
        except PermissionError as exc:
            raise PermissionError(str(exc)) from exc
        mission_id = package.get("mission_id")
        if mission_id is not None:
            self._verify_import_authorization(package)
            expected_role = {
                "ENRICHMENT": "CHANNEL_INTELLIGENCE_PRODUCER",
                "PRODUCER": "CHANNEL_INTELLIGENCE_PRODUCER",
                "REVIEWER": "CHANNEL_INTELLIGENCE_REVIEWER",
            }.get(str(package.get("stage")))
            if expected_role is None:
                raise ValueError("stage de handoff desconocida")
            if package.get("role") != expected_role:
                raise ValueError("role no coincide con la stage esperada")
            for field in ("mission_id", "episode_id", "capability_id", "stage", "role"):
                if payload.get(field) != package.get(field):
                    raise ValueError(f"resultado importado no corresponde en {field}")
            if not payload.get("result_run_id"):
                raise ValueError("resultado importado requiere result_run_id")
            provenance = payload.get("provenance")
            if provenance is not None and not isinstance(provenance, dict):
                raise ValueError("provenance inválida en resultado importado")
            if isinstance(provenance, dict):
                for field in ("mission_id", "episode_id", "capability_id", "stage", "role"):
                    if field in provenance and provenance[field] != package.get(field):
                        raise ValueError(f"provenance no corresponde en {field}")
        if (payload.get("handoff_id") != package["handoff_id"] or payload.get("package_checksum") != expected_checksum
                or payload.get("input_manifest_checksum") != package["input_manifest_checksum"]
                or payload.get("skill_id") != package["skill_id"] or payload.get("skill_version") != package["skill_version"]):
            raise ValueError("resultado importado no corresponde al paquete de handoff")
        content = payload.get("output")
        declared_return = package.get("strategic_return")
        if declared_return is not None and (not isinstance(content, dict) or content.get("strategic_return") != declared_return):
            raise ValueError("strategic_return no coincide con el handoff canónico")
        encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        if payload.get("output_checksum") != checksum(encoded):
            raise ValueError("checksum incorrecto en resultado importado")
        return content

    @staticmethod
    def _verify_import_authorization(package: dict[str, Any]) -> None:
        from src.core.execution_preflight import _load_registered_capability

        repo_root = Path(str(package.get("mission_repo_root") or ".")).resolve()
        authorization_ref = str(package.get("mission_authorization_path") or "")
        contract_ref = str(package.get("mission_contract_path") or "")
        if not authorization_ref or not contract_ref:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED: imported handoff lacks mission bindings")
        authorization_path = (repo_root / authorization_ref).resolve(strict=True)
        contract_path = (repo_root / contract_ref).resolve(strict=True)
        authorization_path.relative_to(repo_root)
        contract_path.relative_to(repo_root)
        authorization = load_mission_authorization(authorization_path)
        contract = load_mission_contract(contract_path)
        if authorization.mission_id != package.get("mission_id") or contract.mission_id != package.get("mission_id"):
            raise PermissionError("MISSION_SCOPE_AUTHORIZATION_MISMATCH: imported result")
        capability = _load_registered_capability(repo_root, str(package.get("capability_id")))
        authorization.verify(
            repo_root,
            capability_id=str(package.get("capability_id")),
            role_id=str(package.get("role")),
            operation="EXECUTE_CAPABILITY",
            execution_mode=str(package.get("execution_mode") or "REAL"),
            execution_route=str(package.get("execution_route") or "") or None,
            execution_family=str(package.get("execution_family") or "") or None,
            execution_interface="TOPIC_BELONGING_TERMINAL",
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )
