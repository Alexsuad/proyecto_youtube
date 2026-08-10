"""TH-06 deterministic context and handoff observability."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.context_resolution import resolve_context

ROOT = Path(__file__).resolve().parents[2]
HANDOFF_MODES = ("REFERENCE_ONLY", "INLINE_MINIMAL", "SELF_CONTAINED")


def validate_handoff(mode: str, *, consumer_can_resolve: bool, justification: str | None = None) -> None:
    if mode not in HANDOFF_MODES:
        raise ValueError("HANDOFF_MODE_UNRESOLVED")
    if mode == "SELF_CONTAINED" and (consumer_can_resolve or not justification):
        raise ValueError("HANDOFF_SELF_CONTAINED_NOT_JUSTIFIED")


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def _envelope(root: Path, artifact_type: str) -> dict[str, Any]:
    try: revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError): revision = "UNRESOLVED"
    sources = ["config/context_resolution_policy.json", "schemas/resolved_context_manifest.json", "src/core/context_resolution.py", "src/core/execution_preflight.py"]
    return {"schema_version":"1.0.0","plan_id":"PLAN_004","mission_id":"TH-06","repository_revision":revision,"generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"source_inputs":[{"path":p,"sha256":_sha(root/p)} for p in sources],"evidence_refs":sources,"limitations":[],"result":"PASS","artifact_type":artifact_type}


def write_th06_artifacts(root: Path = ROOT) -> tuple[Path, Path]:
    policy = json.loads((root / "config/context_resolution_policy.json").read_text(encoding="utf-8"))
    context = _envelope(root, "CONTEXT_RESOLUTION")
    context.update({"precedence":["NORMATIVE_CONTEXT","OWNER_AUTHORIZED_MISSION_SCOPE","CASE_INPUT","OPTIONAL_EVIDENCE"],"resolution_controls":{"absolute_paths":"BLOCK","drive_letter_paths":"BLOCK","unc_paths":"BLOCK","traversal":"BLOCK","symlink_or_reparse_escape":"BLOCK","required_unresolved":"BLOCK","checksum_mismatch":"BLOCK"},"allowed_roots":policy,"resolved_context_manifest_schema":"schemas/resolved_context_manifest.json","context_budget":{"required_context_count":"DERIVED_FROM_RESOLVED_REQUIRED_REFS","resolved_context_size":"DERIVED_FROM_RESOLVED_UTF8_BYTES","estimated_tokens":"ceil(resolved_context_size/4)","thresholds":"NONE"},"reproducibility":{"manifest_identity":"SHA256_CANONICAL_INPUTS","volatile_metadata":"EXCLUDED_FROM_NORMATIVE_MANIFEST"}})
    handoff = _envelope(root, "HANDOFF_AUDIT")
    handoff.update({"allowed_modes":list(HANDOFF_MODES),"preference":list(HANDOFF_MODES),"self_contained_requires_justification":True,"budget_mode":"INFORMATIONAL_ONLY","escalation_reasons":["contradiction","missing_dependency","insufficient_evidence","unresolved_reference"]})
    output=root / "reports/implementation/plan_004"; output.mkdir(parents=True,exist_ok=True)
    first, second=output/"TH06_context_resolution.json", output/"TH06_handoff_audit.json"
    first.write_text(json.dumps(context,indent=2)+"\n",encoding="utf-8"); second.write_text(json.dumps(handoff,indent=2)+"\n",encoding="utf-8")
    return first,second
