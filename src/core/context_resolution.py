"""Fail-closed, repository-relative resolution of execution context."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from src.core.plan_005_invariants import verify_invariants


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ContextResolutionError(ValueError):
    """A context reference cannot be safely resolved."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_policy(root: Path, policy_path: str | Path | None) -> dict[str, list[str]]:
    candidate = Path(policy_path) if policy_path else Path("config/context_resolution_policy.json")
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ContextResolutionError("CONTEXT_POLICY_UNRESOLVED")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root.resolve())
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ContextResolutionError("CONTEXT_POLICY_UNRESOLVED") from exc
    return {key: list(data.get(key, [])) for key in ("normative_allowed_roots", "evidentiary_allowed_roots", "historical_allowed_roots")}


def _safe_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts or not relative:
        raise ContextResolutionError("CONTEXT_PATH_NOT_ALLOWED")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ContextResolutionError("CONTEXT_PATH_NOT_ALLOWED") from exc
    return resolved


def _allowed(resolved: Path, root: Path, allowed_roots: list[str]) -> bool:
    for allowed_root in allowed_roots:
        candidate = Path(allowed_root)
        if candidate.is_absolute() or ".." in candidate.parts:
            continue
        try:
            resolved.relative_to((root / candidate).resolve())
            return True
        except ValueError:
            continue
    return False


def _artifact_digests(resolved: Path, artifact_type: str) -> tuple[str, str | None]:
    raw_digest = _sha256_bytes(resolved.read_bytes())
    if artifact_type.strip().lower() in {"json", "application/json", "structured_json"}:
        try:
            canonical_digest = _sha256_bytes(canonical_json(json.loads(resolved.read_text(encoding="utf-8"))))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContextResolutionError("CONTEXT_JSON_CANONICALIZATION_FAILED") from exc
        return raw_digest, canonical_digest
    return raw_digest, None


def _reference_row(reference: dict[str, Any], resolved: Path, raw_digest: str, canonical_digest: str | None) -> dict[str, Any]:
    row = {
        "ref_id": reference["ref_id"],
        "context_class": reference["context_class"],
        "artifact_path": reference["artifact_path"],
        "artifact_type": reference["artifact_type"],
        "artifact_version": reference.get("artifact_version") or "UNDECLARED",
        "artifact_sha256": raw_digest,
        "authority_domain": reference["authority_domain"],
        "required": bool(reference["required"]),
    }
    if canonical_digest is not None:
        row["canonical_payload_sha256"] = canonical_digest
    return row


def resolve_context(
    references: Iterable[dict[str, Any]],
    *,
    root: str | Path,
    capability_id: str,
    role_id: str,
    run_id: str,
    policy_path: str | Path | None = None,
    mission_id: str | None = None,
    parent_run_id: str | None = None,
    child_run_id: str | None = None,
    delegation_lineage_ref: str | None = None,
    authorized_context_refs: list[str] | None = None,
    conversation_history_inherited: bool = False,
    execution_profile_id: str | None = None,
    execution_family: str | None = None,
    prompt_id: str | None = None,
    input_refs: list[str] | None = None,
    output_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve context with raw-byte identity and optional canonical JSON identity."""
    repository_root = Path(root).resolve()
    if parent_run_id is not None and child_run_id is not None:
        if not parent_run_id or not child_run_id or parent_run_id == child_run_id:
            raise ContextResolutionError("CONTEXT_CHILD_RUN_NOT_ISOLATED")
    if child_run_id is not None and (not child_run_id or run_id != child_run_id):
        raise ContextResolutionError("CONTEXT_MANIFEST_CHILD_RUN_MISMATCH")
    if child_run_id is not None and (not parent_run_id or not delegation_lineage_ref or not authorized_context_refs):
        raise ContextResolutionError("CONTEXT_AUTHORIZED_CHILD_REFS_REQUIRED")
    if conversation_history_inherited:
        raise ContextResolutionError("CONTEXT_CONVERSATION_HISTORY_INHERITED")
    policy = _load_policy(repository_root, policy_path)
    grouped = {"NORMATIVE": [], "EVIDENTIARY": [], "HISTORICAL": []}
    unresolved: list[str] = []
    for reference in references:
        try:
            if not isinstance(reference, dict):
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            if child_run_id is not None:
                authorized = {str(item) for item in authorized_context_refs or []}
                if str(reference.get("ref_id", "")) not in authorized and str(reference.get("artifact_path", "")) not in authorized:
                    raise ContextResolutionError("CONTEXT_CHILD_REF_OUTSIDE_AUTHORIZED_CONTEXT")
            context_class = reference.get("context_class")
            if context_class not in grouped:
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            layer = reference.get("precedence_layer")
            if layer and layer not in {"NORMATIVE_CONTEXT", "OWNER_AUTHORIZED_MISSION_SCOPE", "CASE_INPUT", "OPTIONAL_EVIDENCE"}:
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            if context_class == "NORMATIVE" and layer and layer != "NORMATIVE_CONTEXT":
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            resolved = _safe_path(repository_root, str(reference.get("artifact_path", "")))
            if not _allowed(resolved, repository_root, policy[f"{context_class.lower()}_allowed_roots"]):
                raise ContextResolutionError("CONTEXT_PATH_NOT_ALLOWED")
            raw_digest, canonical_digest = _artifact_digests(resolved, str(reference.get("artifact_type", "")))
            expected_raw = str(reference.get("artifact_sha256", "")).lower()
            if expected_raw and expected_raw != raw_digest.lower():
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            expected_canonical = str(reference.get("canonical_payload_sha256", "")).lower()
            if expected_canonical and expected_canonical != str(canonical_digest or "").lower():
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            grouped[context_class].append(_reference_row(reference, resolved, raw_digest, canonical_digest))
        except (ContextResolutionError, KeyError, TypeError, OSError):
            if bool(reference.get("required")) if isinstance(reference, dict) else True:
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            ref_id = str(reference.get("ref_id", "UNSPECIFIED_REF")) if isinstance(reference, dict) else "UNSPECIFIED_REF"
            unresolved.append(f"CONTEXT_OPTIONAL_UNRESOLVED:{ref_id}")

    resolved_rows = [row for rows in grouped.values() for row in rows]
    resolved_size = sum((repository_root / row["artifact_path"]).stat().st_size for row in resolved_rows)
    body = {
        "manifest_schema_version": "1.0.0",
        "capability_id": capability_id,
        "role_id": role_id,
        "run_id": run_id,
        "normative_refs": grouped["NORMATIVE"],
        "evidentiary_refs": grouped["EVIDENTIARY"],
        "historical_refs": grouped["HISTORICAL"],
        "unresolved_optional_refs": sorted(unresolved),
        "required_context_count": sum(1 for row in resolved_rows if row["required"]),
        "resolved_context_size": resolved_size,
        "estimated_tokens": math.ceil(resolved_size / 4),
        "token_estimation_method": "UTF8_BYTES_DIVIDED_BY_4",
    }
    if mission_id is not None:
        body["mission_id"] = mission_id
    if parent_run_id is not None:
        body["parent_run_id"] = parent_run_id
    if child_run_id is not None:
        body["child_run_id"] = child_run_id
    if delegation_lineage_ref is not None:
        body["delegation_lineage_ref"] = delegation_lineage_ref
    body["conversation_history_inherited"] = False
    if execution_profile_id is not None:
        body["execution_profile_id"] = execution_profile_id
    if execution_family is not None:
        body["execution_family"] = execution_family
    if prompt_id is not None:
        body["prompt_id"] = prompt_id
    if input_refs is not None:
        body["input_refs"] = list(input_refs)
    if output_refs is not None:
        body["output_refs"] = list(output_refs)
    manifest = {"manifest_id": "CTX-" + _sha256_bytes(canonical_json(body))[:32], **body}
    manifest["manifest_sha256"] = _sha256_bytes(canonical_json(manifest))
    invariant_violations = verify_invariants(
        ["CHILD_MANIFEST_MATCHES_CHILD_RUN"],
        {
            "parent_run_id": manifest.get("parent_run_id"),
            "child_run_id": manifest.get("child_run_id"),
            "manifest_run_id": manifest.get("run_id"),
            "conversation_history_inherited": manifest.get("conversation_history_inherited"),
        },
    )
    if invariant_violations:
        raise ContextResolutionError("CONTEXT_LINEAGE_INVARIANT_VIOLATION:" + ",".join(invariant_violations))
    return manifest
