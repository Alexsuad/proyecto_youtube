"""Fail-closed structural validation and freshness checks for evidence reports."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema

_CHECKSUM = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)
_SCHEMA_BY_REPORT = {
    "TH04_capability_audit_universe.json": "capability_audit_universe",
    "HARDENING_COMPLETION_REVIEW.json": "hardening_completion_review",
}


def sha256_path(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if path.is_dir():
        digest = hashlib.sha256()
        ignored = {".git", "__pycache__", ".pytest_cache", ".pytest_tmp", ".runtime-tmp", ".venv"}
        for child in sorted(
            item for item in path.rglob("*")
            if item.is_file() and not any(part in ignored for part in item.relative_to(path).parts)
        ):
            relative = child.relative_to(path).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            content = child.read_bytes()
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        return digest.hexdigest()
    raise OSError(f"EVIDENCE_SOURCE_MISSING:{path}")


def _relative_path(root: Path, reference: str) -> Path | None:
    candidate = Path(reference)
    if not reference or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def _schema_name(report: Path) -> str:
    return _SCHEMA_BY_REPORT.get(report.name, "hardening_report_envelope")


def validate_evidence_report(root: str | Path, report_path: str | Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load and structurally validate evidence before interpreting it."""
    repository_root = Path(root).resolve()
    report = Path(report_path)
    if not report.is_absolute():
        report = repository_root / report
    report = report.resolve()
    try:
        report.relative_to(repository_root)
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, [f"REPORT_UNREADABLE:{exc}"]
    if not isinstance(data, dict):
        return None, ["REPORT_NOT_OBJECT"]
    violations = [f"SCHEMA_INVALID:{entry}" for entry in validate_against_schema(data, _schema_name(report))]
    if not violations:
        for ref in data.get("evidence_refs", []):
            if _relative_path(repository_root, str(ref)) is None or not _relative_path(repository_root, str(ref)).exists():
                violations.append(f"EVIDENCE_REF_UNVERIFIABLE:{ref}")
    return data, violations


def check_report_freshness(root: str | Path, report_path: str | Path) -> dict[str, Any]:
    """Return FRESH only when envelope, schema, references and hashes verify."""
    repository_root = Path(root).resolve()
    report = Path(report_path)
    if not report.is_absolute():
        report = repository_root / report
    report = report.resolve()
    try:
        display = str(report.relative_to(repository_root)).replace("\\", "/")
    except ValueError:
        display = str(report)
    data, violations = validate_evidence_report(repository_root, report)
    if data is None or violations:
        return {
            "report": display,
            "status": "UNVERIFIABLE",
            "mismatches": [],
            "unverifiable_sources": [],
            "violations": violations,
            "repository_revision": data.get("repository_revision") if data else None,
        }

    mismatches: list[dict[str, str]] = []
    unverifiable: list[str] = []
    for entry in data["source_inputs"]:
        relative = str(entry.get("path", "")).replace("\\", "/")
        expected = entry.get("sha256")
        source = _relative_path(repository_root, relative)
        if source is None or not isinstance(expected, str) or not _CHECKSUM.fullmatch(expected):
            unverifiable.append(relative or "UNSPECIFIED_SOURCE")
            continue
        try:
            actual = sha256_path(source)
        except OSError:
            unverifiable.append(relative)
            continue
        if actual.lower() != expected.lower():
            mismatches.append({"path": relative, "expected_sha256": expected, "actual_sha256": actual})

    status = "STALE" if mismatches else ("UNVERIFIABLE" if unverifiable else "FRESH")
    return {
        "report": display,
        "status": status,
        "mismatches": mismatches,
        "unverifiable_sources": sorted(unverifiable),
        "violations": [],
        "repository_revision": data.get("repository_revision"),
    }
