"""Machine-verifiable, provider-neutral mission authorization and replay scope."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema


CANONICAL_MATERIAL_DECISION_REGISTRY = "docs/legacy/material_decision_registry.json"


class MissionAuthorizationError(PermissionError):
    """A mission authorization is invalid, stale, out of scope, or replayed."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_scope(data: dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def scope_checksum(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_scope(data)).hexdigest()


def _safe_repository_file(root: Path, reference: str) -> Path:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: path outside repository")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: path outside repository") from exc
    return resolved


def _verify_material_decision_binding(
    repository_root: Path,
    authority_data: dict[str, Any],
    required_reference: dict[str, Any],
    capability_id: str,
) -> None:
    binding = authority_data.get("material_decision_binding")
    if not isinstance(binding, dict):
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_REQUIRED")
    expected = {key: str(required_reference.get(key) or "") for key in ("registry_path", "decision_id", "subject_ref")}
    if expected["registry_path"] != CANONICAL_MATERIAL_DECISION_REGISTRY:
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: non-canonical registry")
    if any(str(binding.get(key) or "") != value for key, value in expected.items()):
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_MISMATCH")
    try:
        registry_path = _safe_repository_file(repository_root, expected["registry_path"])
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: registry unavailable") from exc
    decision = next((item for item in registry.get("decisions", []) if item.get("decision_id") == expected["decision_id"]), None)
    scope = decision.get("authorization_scope") if isinstance(decision, dict) else None
    if (
        not isinstance(decision, dict)
        or decision.get("state") != "VIGENTE"
        or decision.get("subject_ref") != expected["subject_ref"]
        or not isinstance(scope, dict)
        or scope.get("capability_id") != capability_id
        or scope.get("controlled_demonstration") is not True
        or scope.get("general_activation") is not False
        or scope.get("product_use") is not False
        or scope.get("successor_capabilities") is not False
    ):
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID")
    try:
        capability_registry = json.loads(
            (repository_root / "config" / "capability_registry.json").read_text(encoding="utf-8")
        )
        capability = next(
            (item for item in capability_registry.get("capabilities", [])
             if item.get("capability_id") == capability_id),
            None,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: capability registry unavailable") from exc
    if not isinstance(capability, dict) or decision.get("authority") != capability.get("functional_authority_domain"):
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: authority mismatch")
    if str(binding.get("decision_sha256") or "").lower() != scope_checksum(decision):
        raise MissionAuthorizationError("MATERIAL_DECISION_BINDING_INVALID: decision checksum")


@dataclass(frozen=True)
class MissionAuthorization:
    mission_id: str
    contract_sha256: str
    live_state_path: str
    live_state_sha256: str
    capability_ids: tuple[str, ...]
    role_ids: tuple[str, ...]
    execution_profile_ids: tuple[str, ...]
    execution_interface: str
    allowed_operations: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    allowed_routes: tuple[str, ...]
    execution_mode: str
    single_use: bool
    authority_ref: str
    authority_sha256: str
    authorized_scope_sha256: str
    executor_substitution_policy: str
    contains_material_repair: bool
    repair_integrity_evidence_path: str
    contract_path: str | None = None

    def scope_payload(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "capability_ids": list(self.capability_ids),
            "role_ids": list(self.role_ids),
            "execution_profile_ids": list(self.execution_profile_ids),
            "execution_interface": self.execution_interface,
            "allowed_operations": list(self.allowed_operations),
            "allowed_paths": list(self.allowed_paths),
            "allowed_routes": list(self.allowed_routes),
            "execution_mode": self.execution_mode,
            "live_state_sha256": self.live_state_sha256,
            "contains_material_repair": self.contains_material_repair,
            "repair_integrity_evidence_path": self.repair_integrity_evidence_path,
        }

    @classmethod
    def from_contract(
        cls,
        data: dict[str, Any],
        *,
        contract_sha256: str,
        contract_path: str | None = None,
    ) -> "MissionAuthorization":
        auth = data.get("authorization")
        if not isinstance(auth, dict) or not isinstance(data.get("mission_id"), str):
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authorization missing")
        required = (
            "live_state_path", "live_state_sha256", "capability_ids", "role_ids",
            "execution_profile_ids", "execution_interface", "allowed_operations",
            "allowed_paths", "allowed_routes", "execution_mode", "single_use",
            "authority_ref", "authority_sha256", "authorized_scope_sha256",
            "executor_substitution_policy", "contains_material_repair",
            "repair_integrity_evidence_path",
        )
        missing = [key for key in required if key not in auth]
        if missing:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: " + ", ".join(missing))
        flat = {
            "mission_id": data["mission_id"],
            "contract_sha256": contract_sha256,
            **{key: auth[key] for key in required},
        }
        violations = validate_against_schema(flat, "mission_authorization_contract")
        if violations:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: " + "; ".join(violations))
        instance = cls(
            mission_id=str(data["mission_id"]),
            contract_sha256=contract_sha256,
            live_state_path=str(auth["live_state_path"]),
            live_state_sha256=str(auth["live_state_sha256"]).lower(),
            capability_ids=tuple(str(value) for value in auth["capability_ids"]),
            role_ids=tuple(str(value) for value in auth["role_ids"]),
            execution_profile_ids=tuple(str(value) for value in auth["execution_profile_ids"]),
            execution_interface=str(auth["execution_interface"]),
            allowed_operations=tuple(str(value) for value in auth["allowed_operations"]),
            allowed_paths=tuple(str(value) for value in auth["allowed_paths"]),
            allowed_routes=tuple(str(value) for value in auth["allowed_routes"]),
            execution_mode=str(auth["execution_mode"]),
            single_use=bool(auth["single_use"]),
            authority_ref=str(auth["authority_ref"]),
            authority_sha256=str(auth["authority_sha256"]).lower(),
            authorized_scope_sha256=str(auth["authorized_scope_sha256"]).lower(),
            executor_substitution_policy=str(auth["executor_substitution_policy"]),
            contains_material_repair=bool(auth["contains_material_repair"]),
            repair_integrity_evidence_path=str(auth["repair_integrity_evidence_path"]),
            contract_path=contract_path,
        )
        if scope_checksum(instance.scope_payload()) != instance.authorized_scope_sha256:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authorized scope checksum")
        return instance

    def verify(
        self,
        root: str | Path,
        *,
        capability_id: str,
        role_id: str,
        operation: str,
        path: str | None = None,
        execution_mode: str | None = None,
        execution_route: str | None = None,
        execution_profile_id: str | None = None,
        execution_interface: str | None = None,
        required_material_decision_ref: dict[str, Any] | None = None,
    ) -> None:
        repository_root = Path(root).resolve()
        # The dataclass is immutable, but a caller can still construct or
        # replace an instance in memory.  Never treat those fields as
        # authoritative unless they still match the signed scope snapshot.
        if scope_checksum(self.scope_payload()) != self.authorized_scope_sha256:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authorized scope checksum")
        if self.contract_path:
            contract_file = Path(self.contract_path)
            if not contract_file.is_absolute():
                contract_file = repository_root / contract_file
            try:
                contract_file = contract_file.resolve(strict=True)
                contract_file.relative_to(repository_root)
                current_contract = json.loads(contract_file.read_text(encoding="utf-8"))
                current_checksum = hashlib.sha256(canonical_scope(current_contract)).hexdigest()
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: contract unavailable")
            if current_checksum != self.contract_sha256:
                raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: contract checksum")
        state = (repository_root / self.live_state_path).resolve()
        authority = (repository_root / self.authority_ref).resolve()
        for candidate in (state, authority):
            try:
                candidate.relative_to(repository_root)
            except ValueError as exc:
                raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: path outside repository") from exc
        if not state.is_file() or sha256_file(state) != self.live_state_sha256:
            raise MissionAuthorizationError("MISSION_STALE_AGAINST_LIVE_STATE")
        if not authority.is_file() or sha256_file(authority) != self.authority_sha256:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authority checksum")
        try:
            authority_data = json.loads(authority.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authority artifact") from exc
        try:
            state_text = state.read_text(encoding="utf-8")
            current_mission = next(
                line.split(":", 1)[1].strip().strip('"')
                for line in state_text.splitlines()
                if line.startswith("CURRENT_MISSION:")
            )
        except (OSError, UnicodeDecodeError, StopIteration):
            current_mission = None
            state_text = ""
        operational_authority = "## 1. Estado canónico" in state_text
        if operational_authority and current_mission is None:
            raise MissionAuthorizationError("MISSION_STALE_AGAINST_LIVE_STATE: CURRENT_MISSION missing")
        if operational_authority and current_mission != self.mission_id:
            raise MissionAuthorizationError("MISSION_STALE_AGAINST_LIVE_STATE: mission_id does not match CURRENT_MISSION")
        if authority_data.get("mission_id") != self.mission_id:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authority mission binding")
        if authority_data.get("authorized_scope_sha256") != self.authorized_scope_sha256:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authority scope binding")
        if not isinstance(authority_data.get("artifact_version"), str) or not authority_data.get("artifact_version"):
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authority version")
        if authority_data.get("decision") not in {"APPROVE", "AUTHORIZED"}:
            raise MissionAuthorizationError("MISSION_CONTRACT_INVALID: authority decision")
        if required_material_decision_ref is not None:
            _verify_material_decision_binding(
                repository_root,
                authority_data,
                required_material_decision_ref,
                capability_id,
            )
        if capability_id not in self.capability_ids:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: capability scope")
        if role_id not in self.role_ids:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: role scope")
        if execution_profile_id and "ANY" not in self.execution_profile_ids and execution_profile_id not in self.execution_profile_ids:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: execution profile scope")
        if execution_interface and self.execution_interface not in {"ANY", execution_interface}:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: execution interface")
        self.verify_current_mission(repository_root)
        if operation not in self.allowed_operations:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: operation scope")
        if path and self.allowed_paths and not any(path == allowed or path.startswith(allowed.rstrip("/") + "/") for allowed in self.allowed_paths):
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: path scope")
        if execution_route and "ANY" not in self.allowed_routes and execution_route not in self.allowed_routes:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: routing scope")
        if execution_mode and self.execution_mode not in {"ANY", execution_mode}:
            raise MissionAuthorizationError("EXECUTION_NOT_AUTHORIZED: execution mode")

    def verify_current_mission(self, root: str | Path) -> None:
        """Require every hashed state artifact to expose the matching current mission."""
        repository_root = Path(root).resolve()
        state = (repository_root / self.live_state_path).resolve()
        try:
            state.relative_to(repository_root)
            state_text = state.read_text(encoding="utf-8")
            current_mission = next(
                line.split(":", 1)[1].strip().strip('"')
                for line in state_text.splitlines()
                if line.startswith("CURRENT_MISSION:")
            )
        except (OSError, UnicodeDecodeError, ValueError, StopIteration) as exc:
            raise MissionAuthorizationError("MISSION_STALE_AGAINST_LIVE_STATE: CURRENT_MISSION missing") from exc
        if current_mission.upper() == "NONE":
            raise MissionAuthorizationError("NO_ACTIVE_CURRENT_MISSION")
        if current_mission != self.mission_id:
            raise MissionAuthorizationError("MISSION_STALE_AGAINST_LIVE_STATE: mission_id does not match CURRENT_MISSION")


def load_mission_authorization(path: str | Path) -> MissionAuthorization:
    contract_path = Path(path)
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    canonical = canonical_scope(data)
    return MissionAuthorization.from_contract(
        data,
        contract_sha256=hashlib.sha256(canonical).hexdigest(),
        contract_path=str(contract_path),
    )
