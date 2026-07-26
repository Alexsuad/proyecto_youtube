"""Manifiesto canónico de las entradas que consume la auditoría B5-I2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_input_manifest(episode_id: str, artifacts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Construye una única representación estable para runtime, handoff y gate."""
    rows = [
        {
            "artifact_kind": item["artifact_kind"],
            "artifact_id": item["artifact_id"],
            "artifact_checksum": item.get("artifact_checksum", item.get("checksum")),
        }
        for item in artifacts
    ]
    return {
        "episode_id": episode_id,
        "artifacts": sorted(rows, key=lambda item: (item["artifact_kind"], item["artifact_id"])),
    }


def manifest_checksum(episode_id: str, artifacts: Iterable[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_json(build_input_manifest(episode_id, artifacts))).hexdigest()
