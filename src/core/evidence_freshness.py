"""Fail-closed structural validation, freshness and transitive invalidation for evidence reports."""
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
    "PLAN_005_COMPLETION_REVIEW.json": "plan_005_completion_review",
    "PLAN_005_TEST_RUN_EVIDENCE.json": "plan_005_test_run_evidence",
    "PLAN_005_CONTROLLED_E2E.json": "plan_005_e2e_demonstration",
    "PLAN_005_D5_RECOVERY_E2E.json": "plan_005_d5_recovery_evidence",
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


def _identity_checksum(data: dict[str, Any]) -> str:
    identity = dict(data)
    identity.pop("generated_at", None)
    identity.pop("evidence_identity_sha256", None)
    payload = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
        if "evidence_identity_sha256" in data and str(data.get("evidence_identity_sha256", "")).lower() != _identity_checksum(data).lower():
            violations.append("EVIDENCE_IDENTITY_MISMATCH")
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


def _report_relative(root: Path, reference: str) -> str | None:
    """Return the repository-relative posix path for an evidence report reference, or None."""
    source = _relative_path(root, reference)
    if source is None:
        return None
    try:
        return str(source.relative_to(root)).replace("\\", "/")
    except ValueError:
        return None


def _is_report_source(root: Path, source: Path) -> bool:
    """True when the source is a JSON evidence report with its own source_inputs."""
    if not source.is_file() or source.suffix.lower() != ".json":
        return False
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    return isinstance(data, dict) and isinstance(data.get("source_inputs"), list)


def check_transitive_freshness(root: str | Path, report_path: str | Path) -> dict[str, Any]:
    """Fail-closed freshness that propagates staleness through the report graph.

    A report is only FRESH when its own source_inputs AND every source_input that
    is itself an evidence report (its source_inputs) verify. Any STALE or
    UNVERIFIABLE descendant invalidates the report: downstream evidence can never
    stay FRESH while its transitive inputs moved. Cycle-safe and fail-closed.
    """
    repository_root = Path(root).resolve()
    report = Path(report_path)
    if not report.is_absolute():
        report = repository_root / report
    report = report.resolve()
    try:
        display = str(report.relative_to(repository_root)).replace("\\", "/")
    except ValueError:
        display = str(report)

    visited: set[str] = set()
    invalidated_by: list[dict[str, str]] = []
    status = "FRESH"

    def propagate(current: Path) -> None:
        nonlocal status
        try:
            current_rel = str(current.relative_to(repository_root)).replace("\\", "/")
        except ValueError:
            current_rel = str(current)
        if current_rel in visited:
            return
        visited.add(current_rel)
        direct = check_report_freshness(repository_root, current)
        if direct["status"] == "STALE":
            status = "STALE"
            invalidated_by.append({"report": current_rel, "downstream_status": "STALE", "mismatches": direct["mismatches"]})
            return
        if direct["status"] == "UNVERIFIABLE":
            if status != "STALE":
                status = "UNVERIFIABLE"
            invalidated_by.append({"report": current_rel, "downstream_status": "UNVERIFIABLE"})
            return
        data, _ = validate_evidence_report(repository_root, current)
        if data is None:
            return
        for ref in data.get("source_inputs", []):
            relative = _report_relative(repository_root, str(ref.get("path", "")))
            if relative is None:
                continue
            source = repository_root / relative
            if _is_report_source(repository_root, source):
                propagate(source)

    propagate(report)
    return {
        "report": display,
        "status": status,
        "invalidated_by": invalidated_by,
        "visited_reports": sorted(visited),
        "repository_revision": None,
    }
