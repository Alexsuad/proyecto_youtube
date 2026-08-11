"""Portable preflight shared by controlled execution entrypoints."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.capability_governance import validate_capability_registry
from src.core.context_resolution import resolve_context
from src.core.mission_authorization import load_mission_authorization
from src.core.mission_completion_gate import load_mission_contract
from src.core.replay_protection import mark_mission_reservation, reserve_mission_execution


def _registry_capability(root: Path, capability_id: str, registry_path: str | None) -> dict[str, Any]:
    path = root / (Path(registry_path) if registry_path else Path("config/capability_registry.json"))
    violations = validate_capability_registry(path)
    if violations:
        raise PermissionError("CAPABILITY_REGISTRY_INVALID: " + "; ".join(violations))
    data = json.loads(path.read_text(encoding="utf-8"))
    capability = next((item for item in data.get("capabilities", []) if item.get("capability_id") == capability_id), None)
    if capability is None:
        raise PermissionError("CAPABILITY_UNREGISTERED:" + capability_id)
    if capability.get("availability_status") in {"NON_EXECUTABLE_CURRENT", "SUSPENDED", "DEPRECATED"}:
        raise PermissionError("CAPABILITY_UNAVAILABLE:" + capability_id)
    return capability


def _mark_failed(registry_path: str | None, reservation: dict[str, str] | None, request: Any) -> None:
    if reservation and registry_path:
        mark_mission_reservation(registry_path, reservation["reservation_id"], "FAILED")
        request.config = {**request.config, "_mission_reservation_status": "FAILED"}


def preflight_controlled_execution(request: Any, *, root: str | Path) -> dict[str, Any]:
    """Validate authorization, replay, capability and context before execution."""
    config = getattr(request, "config", {}) or {}
    authorization_path = config.get("mission_authorization_path")
    if not authorization_path:
        if config.get("mission_authorization_required"):
            raise PermissionError("MISSION_CONTRACT_INVALID: mission authorization path missing")
        return {"authorization": None, "context_manifest": None, "reservation": None}

    repository_root = Path(root).resolve()
    authorization_candidate = Path(str(authorization_path))
    if authorization_candidate.is_absolute() or ".." in authorization_candidate.parts:
        raise PermissionError("MISSION_CONTRACT_INVALID: authorization path outside repository")
    authorization_file = (repository_root / authorization_candidate).resolve()
    try:
        authorization_file.relative_to(repository_root)
    except ValueError as exc:
        raise PermissionError("MISSION_CONTRACT_INVALID: authorization path outside repository") from exc
    authorization = load_mission_authorization(authorization_file)
    mission_contract = None
    contract_path = config.get("mission_contract_path")
    if contract_path:
        contract_candidate = Path(str(contract_path))
        if contract_candidate.is_absolute() or ".." in contract_candidate.parts:
            raise PermissionError("MISSION_CONTRACT_INVALID: mission contract outside repository")
        contract_file = (repository_root / contract_candidate).resolve()
        try:
            contract_file.relative_to(repository_root)
        except ValueError as exc:
            raise PermissionError("MISSION_CONTRACT_INVALID: mission contract outside repository") from exc
        mission_contract = load_mission_contract(contract_file)
        if mission_contract.mission_mode == "REDUCED" and mission_contract.mission_id != authorization.mission_id:
            raise PermissionError("MISSION_CONTRACT_INVALID: reduced mission id does not match authorization")

    output_path = getattr(request, "output_artifact_path", None)
    relative_output = None
    if output_path:
        try:
            relative_output = str(Path(output_path).resolve().relative_to(repository_root)).replace("\\", "/")
        except ValueError:
            relative_output = str(output_path).replace("\\", "/")
    requested_route = str(request.execution_route or config.get("execution_route") or config.get("default_execution_route") or "")
    requested_profile = str(request.execution_profile or config.get("execution_profile") or "UNSPECIFIED_PROFILE")
    requested_interface = str(config.get("execution_interface") or "UNSPECIFIED_INTERFACE")
    authorization.verify(
        repository_root,
        capability_id=str(request.capability_id),
        role_id=str(getattr(request, "role", "")),
        operation=str(config.get("mission_operation") or "EXECUTE_CAPABILITY"),
        path=relative_output,
        execution_mode=str(getattr(request, "execution_mode", "")),
        execution_route=requested_route or None,
        execution_profile_id=requested_profile,
        execution_interface=requested_interface,

    )

    registry_path = config.get("execution_registry_path")
    if authorization.single_use and not registry_path:
        raise PermissionError("MISSION_PROVENANCE_REQUIRED: execution registry path missing")
    reservation = None
    if authorization.single_use:
        reservation = reserve_mission_execution(
            registry_path,
            mission_id=authorization.mission_id,
            contract_sha256=authorization.contract_sha256,
            run_id=str(config.get("run_id") or "PENDING_RUN"),
        )
        request.config = {
            **request.config,
            "_mission_reservation_id": reservation["reservation_id"],
            "_mission_reservation_status": "RESERVED",
            "mission_id": authorization.mission_id,
            "mission_contract_sha256": authorization.contract_sha256,
            "capability_id": str(request.capability_id),
        }

    try:
        registry_capability = _registry_capability(repository_root, str(request.capability_id), config.get("capability_registry_path"))
        if str(getattr(request, "role", "")) not in set(registry_capability.get("assigned_role", [])):
            raise PermissionError("EXECUTION_NOT_AUTHORIZED: capability role scope")
        context_manifest = resolve_context(
            config.get("context_references", []),
            root=repository_root,
            capability_id=str(request.capability_id),
            role_id=str(getattr(request, "role", "")),
            run_id=str(config.get("run_id") or "PENDING_RUN"),
            policy_path=config.get("context_policy_path"),
            mission_id=str(config.get("mission_id") or authorization.mission_id),
            execution_profile_id=requested_profile,
            prompt_id=str(config.get("prompt_id") or "UNSPECIFIED_PROMPT"),
            input_refs=[str(item) for item in config.get("input_refs", [])],
            output_refs=[str(item) for item in config.get("output_refs", ([relative_output] if relative_output else []))],
        )
    except Exception:
        _mark_failed(registry_path, reservation, request)
        raise
    return {"authorization": authorization, "context_manifest": context_manifest, "reservation": reservation, "mission_contract": mission_contract}
