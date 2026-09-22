"""Fail-closed resolution of ordinary product capability authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.core.contract_validation import validate_against_schema


PRODUCT_AUTHORIZATION_PATH = "config/product_capability_authorizations.json"
PRODUCT_AUTHORIZATION_SCHEMA = "product_capability_authorizations"
MATERIAL_DECISION_PATH = "docs/legacy/material_decision_registry.json"


class ProductAuthorizationError(PermissionError):
    """Product authority is missing, stale, conflicting, or out of scope."""


def _canonical_without_checksum(record: Mapping[str, Any]) -> bytes:
    payload = {key: value for key, value in record.items() if key != "authorization_checksum"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def authorization_checksum(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_without_checksum(record)).hexdigest()


def _parse_datetime(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ProductAuthorizationError(f"PRODUCT_AUTHORIZATION_{label}_INVALID") from exc
    if parsed.tzinfo is None:
        raise ProductAuthorizationError(f"PRODUCT_AUTHORIZATION_{label}_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)


def _safe_repo_path(root: Path, reference: str, label: str) -> Path:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ProductAuthorizationError(f"{label}_OUTSIDE_REPOSITORY")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ProductAuthorizationError(f"{label}_OUTSIDE_REPOSITORY") from exc
    return resolved


def _normalize_authorized_path(value: str, label: str) -> str:
    """Normalize a repository-relative scope without weakening traversal checks."""
    raw = str(value).replace("\\", "/")
    if not raw or raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        raise ProductAuthorizationError(f"{label}_OUTSIDE_REPOSITORY")
    parts = raw.split("/")
    if any(part == ".." for part in parts):
        raise ProductAuthorizationError(f"{label}_OUTSIDE_REPOSITORY")
    normalized = "/".join(part for part in parts if part not in {"", "."}).rstrip("/")
    if not normalized:
        raise ProductAuthorizationError(f"{label}_OUTSIDE_REPOSITORY")
    return normalized


def _path_allowed(path: str, allowed_paths: list[str] | tuple[str, ...], label: str) -> bool:
    normalized = _normalize_authorized_path(path, label)
    return any(
        normalized == allowed or normalized.startswith(allowed + "/")
        for allowed in (
            _normalize_authorized_path(item, f"{label}_SCOPE") for item in allowed_paths
        )
    )


def _resolve_requested_path(root: Path, path: str, label: str) -> str:
    """Validate textual scope and physical repository containment.

    The authorization registry is expressed in repository-relative text, but
    the target supplied by a caller may traverse a symlink, junction, or
    another Windows reparse point.  Normalize first for scope matching and
    then resolve the actual filesystem target before accepting it.
    """
    normalized = _normalize_authorized_path(path, label)
    _safe_repo_path(root.resolve(), normalized, label)
    return normalized


def _load_registry(root: Path) -> list[dict[str, Any]]:
    path = _safe_repo_path(root, PRODUCT_AUTHORIZATION_PATH, "PRODUCT_AUTHORIZATION_REGISTRY")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_REGISTRY_UNREADABLE") from exc
    violations = validate_against_schema(registry, PRODUCT_AUTHORIZATION_SCHEMA)
    if violations:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_REGISTRY_INVALID: " + "; ".join(violations))
    authorizations = registry.get("authorizations", [])
    if not isinstance(authorizations, list):
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_REGISTRY_INVALID")
    ids: set[str] = set()
    checksums: set[str] = set()
    for raw in authorizations:
        if not isinstance(raw, dict):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_RECORD_INVALID")
        authorization_id = str(raw.get("authorization_id") or "")
        checksum = str(raw.get("authorization_checksum") or "")
        if authorization_id in ids or checksum in checksums:
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_DUPLICATE")
        ids.add(authorization_id)
        checksums.add(checksum)
        if authorization_checksum(raw) != checksum:
            raise ProductAuthorizationError(f"PRODUCT_AUTHORIZATION_CHECKSUM_MISMATCH:{authorization_id}")
        if raw.get("status") == "REVOKED" and not all(raw.get(key) for key in ("revoked_at", "revoked_by", "revocation_reason")):
            raise ProductAuthorizationError(f"PRODUCT_AUTHORIZATION_REVOCATION_INCOMPLETE:{authorization_id}")
        for allowed_path in raw.get("allowed_paths", []):
            _normalize_authorized_path(str(allowed_path), "PRODUCT_AUTHORIZATION_ALLOWED_PATH")
    return [dict(item) for item in authorizations]


def _verify_material_decision(root: Path, reference: Mapping[str, Any], capability_id: str) -> None:
    if reference.get("registry_path") != MATERIAL_DECISION_PATH:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_MATERIAL_DECISION_REGISTRY_INVALID")
    path = _safe_repo_path(root, MATERIAL_DECISION_PATH, "PRODUCT_AUTHORIZATION_MATERIAL_DECISION")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_MATERIAL_DECISION_UNREADABLE") from exc
    decision = next((item for item in registry.get("decisions", []) if item.get("decision_id") == reference.get("decision_id")), None)
    if (
        not isinstance(decision, dict)
        or decision.get("state") != "VIGENTE"
        or decision.get("subject_ref") != reference.get("subject_ref")
    ):
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_MATERIAL_DECISION_MISSING")
    if decision.get("authorization_scope", {}).get("capability_id") != capability_id:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_MATERIAL_DECISION_CAPABILITY_MISMATCH")
    if authorization_checksum({**decision, "authorization_checksum": None}) != reference.get("decision_sha256"):
        # Decision checksums use the same canonical serialization, but do not
        # add an authorization field to the persisted decision.
        actual = hashlib.sha256(json.dumps(decision, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if actual != reference.get("decision_sha256"):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_MATERIAL_DECISION_CHECKSUM_MISMATCH")


@dataclass(frozen=True)
class ProductCapabilityAuthorization:
    values: dict[str, Any]

    @property
    def authorization_id(self) -> str:
        return str(self.values["authorization_id"])

    @property
    def authority_version(self) -> str:
        return str(self.values["authority_version"])

    @property
    def authorization_checksum(self) -> str:
        return str(self.values["authorization_checksum"])

    @property
    def capability_id(self) -> str:
        return str(self.values["capability_id"])

    @property
    def allowed_paths(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.values.get("allowed_paths", ()))

    @property
    def mission_id(self) -> str | None:
        """PRODUCT authority is not mission-bound and has no mission id."""
        return None

    @property
    def contract_sha256(self) -> None:
        return None

    def verify(
        self,
        repository_root: Path,
        *,
        capability_id: str,
        role_id: str,
        operation: str = "EXECUTE_CAPABILITY",
        path: str | None = None,
        execution_mode: str | None = None,
        execution_route: str | None = None,
        execution_profile_id: str | None = None,
        execution_family: str | None = None,
        execution_interface: str | None = None,
        required_material_decision_ref: Mapping[str, Any] | None = None,
    ) -> None:
        if self.values.get("status") != "ACTIVE" or self.values.get("authorization_mode") != "PRODUCT":
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_NOT_ACTIVE")
        if capability_id != self.capability_id or operation != "EXECUTE_CAPABILITY":
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_SCOPE_MISMATCH")
        if role_id not in self.values.get("allowed_role_ids", []):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_ROLE_DENIED")
        if execution_family not in self.values.get("allowed_execution_families", []):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_FAMILY_DENIED")
        if execution_route not in self.values.get("allowed_routes", []):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_ROUTE_DENIED")
        profile = execution_profile_id or ("EXECUTOR_MANAGED" if execution_family == "AGENT_HARNESS" else None)
        if profile not in self.values.get("allowed_profiles", []):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_PROFILE_DENIED")
        if execution_interface not in self.values.get("allowed_interfaces", []):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_INTERFACE_DENIED")
        if path is not None:
            normalized_path = _resolve_requested_path(repository_root, path, "PRODUCT_AUTHORIZATION_PATH")
            if not _path_allowed(normalized_path, self.allowed_paths, "PRODUCT_AUTHORIZATION_PATH"):
                raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_PATH_DENIED")
        now = datetime.now(timezone.utc)
        if now < _parse_datetime(str(self.values["valid_from"]), "VALID_FROM"):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_NOT_YET_VALID")
        valid_until = self.values.get("valid_until")
        if valid_until is not None and now >= _parse_datetime(str(valid_until), "VALID_UNTIL"):
            raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_EXPIRED")
        if required_material_decision_ref is not None:
            actual = self.values.get("material_decision_ref")
            if actual != required_material_decision_ref:
                raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_MATERIAL_DECISION_BINDING_MISMATCH")


def resolve_product_authorization(
    root: str | Path,
    *,
    capability_id: str,
    role_id: str,
    execution_family: str,
    execution_route: str,
    execution_profile_id: str | None,
    execution_interface: str,
    path: str | None = None,
) -> tuple[ProductCapabilityAuthorization, dict[str, Any] | None]:
    repository_root = Path(root).resolve()
    candidates = [
        item for item in _load_registry(repository_root)
        if item.get("capability_id") == capability_id
        and item.get("status") == "ACTIVE"
        and role_id in item.get("allowed_role_ids", [])
        and execution_family in item.get("allowed_execution_families", [])
        and execution_route in item.get("allowed_routes", [])
        and (execution_profile_id or ("EXECUTOR_MANAGED" if execution_family == "AGENT_HARNESS" else None)) in item.get("allowed_profiles", [])
        and execution_interface in item.get("allowed_interfaces", [])
    ]
    if path is not None:
        # Validate before filtering so traversal cannot be normalized into an
        # apparently authorized descendant or silently become a plain DENY.
        normalized_path = _resolve_requested_path(repository_root, path, "PRODUCT_AUTHORIZATION_PATH")
        candidates = [
            item
            for item in candidates
            if _path_allowed(normalized_path, [str(value) for value in item.get("allowed_paths", [])], "PRODUCT_AUTHORIZATION_PATH")
        ]
    if len(candidates) == 0:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_DENY")
    if len(candidates) > 1:
        raise ProductAuthorizationError("PRODUCT_AUTHORIZATION_CONFLICT")
    selected = ProductCapabilityAuthorization(candidates[0])
    material_ref = candidates[0].get("material_decision_ref")
    if isinstance(material_ref, dict):
        _verify_material_decision(repository_root, material_ref, capability_id)
    selected.verify(
        repository_root,
        capability_id=capability_id,
        role_id=role_id,
        execution_family=execution_family,
        execution_route=execution_route,
        execution_profile_id=execution_profile_id,
        execution_interface=execution_interface,
        path=path,
        required_material_decision_ref=material_ref,
    )
    return selected, material_ref if isinstance(material_ref, dict) else None
