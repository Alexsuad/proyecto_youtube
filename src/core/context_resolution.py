"""Fail-closed, repository-relative resolution of execution context."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ContextResolutionError(ValueError):
    """A context reference cannot be safely resolved."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
) -> dict[str, Any]:
    """Resolve context with raw-byte identity and optional canonical JSON identity."""
    repository_root = Path(root).resolve()
    policy = _load_policy(repository_root, policy_path)
    grouped = {"NORMATIVE": [], "EVIDENTIARY": [], "HISTORICAL": []}
    unresolved: list[str] = []
    for reference in references:
        try:
            if not isinstance(reference, dict):
                raise ContextResolutionError("CONTEXT_REQUIRED_UNRESOLVED")
            context_class = reference.get("context_class")
            if context_class not in grouped:
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

    body = {
        "manifest_id": f"CTX-{uuid.uuid4().hex}",
        "manifest_schema_version": "1.0.0",
        "capability_id": capability_id,
        "role_id": role_id,
        "run_id": run_id,
        "normative_refs": grouped["NORMATIVE"],
        "evidentiary_refs": grouped["EVIDENTIARY"],
        "historical_refs": grouped["HISTORICAL"],
        "unresolved_optional_refs": sorted(unresolved),
        "resolved_at": _now(),
    }
    manifest = dict(body)
    manifest["manifest_sha256"] = _sha256_bytes(canonical_json(body))
    return manifest