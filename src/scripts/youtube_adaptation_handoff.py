"""Canonical structural handoff from controlled B5 artifacts to YA package inputs."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any

_FIELDS = {
    "episode_brief": ("episode_id", "episode_brief"),
    "refined_thesis": ("thesis_id", "refined_thesis"),
    "editorial_script_promise": ("promise_id", "editorial_script_promise"),
    "evidence_report": ("report_id", "evidence_report"),
    "claims_ledger": ("ledger_id", "claims_ledger"),
}

def build_structural_youtube_package(template: dict[str, Any], artifacts: dict[str, Path]) -> dict[str, Any]:
    """Build one YA package from the exact controlled B5 artifact files."""
    package = copy.deepcopy(template)
    refs = package.setdefault("input_references", {})
    for field, (id_key, _) in _FIELDS.items():
        path = Path(artifacts[field])
        payload = json.loads(path.read_text(encoding="utf-8"))
        artifact_id = payload.get(id_key)
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError(f"B5 artifact {field} lacks {id_key}")
        refs[field] = {"artifact_id": artifact_id, "version": str(payload.get("brief_version") or payload.get("script_version") or "1.0.0"), "checksum": hashlib.sha256(path.read_bytes()).hexdigest()}
    package["episode_id"] = json.loads(Path(artifacts["episode_brief"]).read_text(encoding="utf-8"))["episode_id"]
    package["input_references"]["evidence_or_claims_reference"] = dict(refs["evidence_report"])
    return package
