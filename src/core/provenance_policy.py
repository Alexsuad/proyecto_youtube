"""Canonical execution-provenance location resolved outside repair evidence."""

from __future__ import annotations

import json
from pathlib import Path


POLICY_PATH = Path("config/execution_provenance_policy.json")


class ProvenancePolicyError(ValueError):
    """The repository has no safe canonical provenance location."""


def canonical_registry_path(root: str | Path) -> str:
    repository_root = Path(root).resolve()
    policy_path = repository_root / POLICY_PATH
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        configured = str(policy["canonical_registry_path"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ProvenancePolicyError("REPAIR_CANONICAL_PROVENANCE_POLICY_UNRESOLVED") from exc
    candidate = Path(configured)
    if candidate.is_absolute() or not configured or ".." in candidate.parts:
        raise ProvenancePolicyError("REPAIR_CANONICAL_PROVENANCE_POLICY_INVALID")
    return candidate.as_posix()
