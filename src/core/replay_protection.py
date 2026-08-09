"""Atomic single-use mission reservation on the canonical provenance file."""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.core.contract_validation import validate_against_schema


class ReplayProtectionError(PermissionError):
    """A mission authorization is already reserved or the registry is invalid."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _lock(path: Path, timeout: float = 5.0) -> int:
    lock_path = Path(str(path) + ".mission-lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            return os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):
            if time.monotonic() >= deadline:
                raise ReplayProtectionError("MISSION_REPLAY_LOCK_TIMEOUT")
            time.sleep(0.01)


def reserve_mission_execution(
    provenance_path: str | Path,
    *,
    mission_id: str,
    contract_sha256: str,
    run_id: str,
) -> dict[str, str]:
    """Atomically reserve a single-use mission before invoking its executor."""
    path = Path(provenance_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = _lock(path)
    lock_path = Path(str(path) + ".mission-lock")
    try:
        if path.exists():
            registry = json.loads(path.read_text(encoding="utf-8"))
        else:
            registry = {"registry_version": "1.0.0", "runs": [], "handoffs": [], "attempts": [], "reservations": []}
        registry.setdefault("reservations", [])
        if any(item.get("mission_id") == mission_id and item.get("contract_sha256") == contract_sha256 for item in registry["reservations"]):
            raise ReplayProtectionError("MISSION_REPLAY_DETECTED")
        record = {
            "reservation_id": f"RES-{uuid.uuid4().hex}",
            "mission_id": mission_id,
            "contract_sha256": contract_sha256.lower(),
            "run_id": run_id,
            "status": "RESERVED",
            "reserved_at": _now(),
        }
        registry["reservations"].append(record)
        violations = validate_against_schema(registry, "execution_provenance_registry")
        if violations:
            raise ReplayProtectionError("PROVENANCE_REGISTRY_INVALID: " + "; ".join(violations))
        temporary = path.with_name(path.name + ".mission-tmp")
        temporary.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
        return record
    finally:
        os.close(lock_fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def mark_mission_reservation(provenance_path: str | Path, reservation_id: str, status: str) -> None:
    if status not in {"CONSUMED", "FAILED"}:
        raise ValueError("invalid reservation status")
    path = Path(provenance_path)
    lock_fd = _lock(path)
    lock_path = Path(str(path) + ".mission-lock")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
        record = next((item for item in registry.get("reservations", []) if item.get("reservation_id") == reservation_id), None)
        if record is None:
            raise ReplayProtectionError("MISSION_RESERVATION_NOT_FOUND")
        record["status"] = status
        violations = validate_against_schema(registry, "execution_provenance_registry")
        if violations:
            raise ReplayProtectionError("PROVENANCE_REGISTRY_INVALID: " + "; ".join(violations))
        temporary = path.with_name(path.name + ".mission-tmp")
        temporary.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        os.close(lock_fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
