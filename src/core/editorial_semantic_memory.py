"""Repositorio portable y consulta determinista de memoria editorial R1-M8."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Mapping

from src.core.contract_validation import validate_editorial_semantic_memory


REQUIRED_CONSULTATION_POINTS = (
    "PROPOSAL",
    "PRE_FINAL_CURATION",
    "PRE_THESIS_OR_ARCHITECTURE",
    "OPENING_UNIT_REVIEW",
    "PRE_FINAL_SCRIPT",
)

CHECKPOINT_INTEGRATION_STATUS = {
    "PROPOSAL": "CONNECTED",
    "PRE_FINAL_CURATION": "CONNECTED",
    "PRE_THESIS_OR_ARCHITECTURE": "CONNECTED",
    "OPENING_UNIT_REVIEW": "PREPARED_DEFERRED_UNTIL_CANONICAL_OPENING_UNIT_REVIEW",
    "PRE_FINAL_SCRIPT": "PREPARED_DEFERRED_UNTIL_CANONICAL_FINAL_SCRIPT_APPROVAL",
}


def current_artifacts_from_paths(
    paths: Mapping[str, str | Path],
    versions: Mapping[str, str] | None = None,
) -> dict[str, dict[str, str]]:
    """Build the freshness map from canonical gate inputs, never from caller text."""
    result: dict[str, dict[str, str]] = {}
    versions = versions or {}
    for artifact_ref, raw_path in paths.items():
        path = Path(raw_path)
        if not path.is_file():
            continue
        payload = path.read_bytes()
        version = versions.get(artifact_ref, "1.0.0")
        try:
            data = json.loads(payload.decode("utf-8"))
            for key in ("version", "brief_version", "dossier_version", "memory_version"):
                if isinstance(data, dict) and isinstance(data.get(key), str):
                    version = data[key]
                    break
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        result[artifact_ref] = {"version": version, "checksum": hashlib.sha256(payload).hexdigest()}
    return result


def run_memory_checkpoint(
    memory_path: str | Path | None,
    candidate_episode_ref: Mapping[str, Any],
    consultation_point: str,
    current_artifacts: Mapping[str, Mapping[str, str]] | None = None,
    artifact_paths: Mapping[str, str | Path] | None = None,
    artifact_versions: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Run one workflow checkpoint when a governed memory artifact is supplied.

    A missing optional memory artifact preserves legacy pre-M8 workflows. Once a
    memory artifact is supplied, freshness is mandatory and failures are returned
    to the caller instead of being converted into an editorial PASS.
    """
    if memory_path is None or not Path(memory_path).is_file():
        return None
    store = EditorialSemanticMemoryStore.load(memory_path)
    resolved = dict(current_artifacts or {})
    if artifact_paths:
        resolved.update(current_artifacts_from_paths(artifact_paths, artifact_versions))
    return store.consult(candidate_episode_ref, consultation_point, resolved)


def _ref_key(ref: Mapping[str, Any]) -> tuple[str, str, str]:
    return (str(ref.get("artifact_ref", "")), str(ref.get("version", "")), str(ref.get("checksum", "")))


def validate_memory_freshness(
    memory: Mapping[str, Any],
    current_artifacts: Mapping[str, Mapping[str, str]],
) -> list[str]:
    """Return invalidation violations when a stored version/checksum is stale."""
    violations: list[str] = []
    refs = []
    for entry in memory.get("episode_entries", []):
        refs.extend(entry.get("artifact_refs", []))
    for decision in memory.get("comparison_decisions", []):
        refs.append(decision.get("candidate_episode_ref"))
        refs.extend(decision.get("compared_episode_refs", []))
    for ref in refs:
        if not isinstance(ref, dict):
            violations.append("MEMORY_REF_INVALID")
            continue
        artifact_ref = ref.get("artifact_ref")
        current = current_artifacts.get(artifact_ref)
        if not isinstance(current, Mapping):
            violations.append(f"MEMORY_REF_UNVERIFIABLE:{artifact_ref}")
            continue
        if current.get("version") != ref.get("version") or current.get("checksum") != ref.get("checksum"):
            violations.append(f"MEMORY_REF_STALE:{artifact_ref}")
    return violations


class EditorialSemanticMemoryStore:
    """Persistencia JSON gobernada por el repositorio y consultas por candidato."""

    def __init__(self, memory: Mapping[str, Any]):
        self.memory = json.loads(json.dumps(memory, ensure_ascii=False))
        violations = validate_editorial_semantic_memory(self.memory)
        if violations:
            raise ValueError("Invalid EditorialSemanticMemory: " + "; ".join(violations))

    @classmethod
    def load(cls, path: str | Path) -> "EditorialSemanticMemoryStore":
        source = Path(path)
        return cls(json.loads(source.read_text(encoding="utf-8")))

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.memory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def consult(
        self,
        candidate_episode_ref: Mapping[str, Any],
        consultation_point: str,
        current_artifacts: Mapping[str, Mapping[str, str]] | None = None,
    ) -> dict[str, Any]:
        if consultation_point not in REQUIRED_CONSULTATION_POINTS:
            raise ValueError(f"UNKNOWN_CONSULTATION_POINT:{consultation_point}")
        if current_artifacts is None:
            raise ValueError("CURRENT_ARTIFACTS_REQUIRED_FOR_MEMORY_CONSULTATION")
        freshness = validate_memory_freshness(self.memory, current_artifacts)
        if freshness:
            return {"status": "INVALIDATED", "consultation_point": consultation_point, "violations": freshness, "decisions": []}
        candidate_key = _ref_key(candidate_episode_ref)
        decisions = [
            decision for decision in self.memory.get("comparison_decisions", [])
            if _ref_key(decision.get("candidate_episode_ref", {})) == candidate_key
        ]
        if not decisions:
            return {"status": "INSUFFICIENT_HISTORY", "consultation_point": consultation_point, "violations": [], "decisions": []}
        return {
            "status": "READY_FOR_FUNCTIONAL_REVIEW",
            "consultation_point": consultation_point,
            "violations": [],
            "decisions": decisions,
        }
