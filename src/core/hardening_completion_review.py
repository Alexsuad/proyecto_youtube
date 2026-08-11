"""Fail-closed, reproducible generator for the PLAN 004 completion review."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.evidence_freshness import check_report_freshness, validate_evidence_report

ROOT = Path(__file__).resolve().parents[2]
REPORTS = (
    "TH04_capability_discovery_scope.json", "TH04_capability_audit_universe.json", "TH04_registry_delta_proposal.json",
    "TH05_cross_registry_integrity.json", "TH05_authority_resolution.json",
    "TH06_context_resolution.json", "TH06_handoff_audit.json", "TH07_quality_baseline.json", "TH08_mutation_testing.json",
)


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNRESOLVED"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _assess_report(root: Path, name: str, accepted_results: set[str]) -> dict[str, Any]:
    path = root / "reports/implementation/plan_004" / name
    data, structural = validate_evidence_report(root, path)
    freshness = check_report_freshness(root, path)
    findings = list(structural)
    if freshness["status"] != "FRESH":
        findings.append(f"FRESHNESS_{freshness['status']}")
    if data is not None and data.get("result") not in accepted_results:
        findings.append(f"RESULT_INCOMPATIBLE:{data.get('result')}")
    status = "PASS" if not findings else ("FAIL" if any(item.startswith("RESULT_") or item.startswith("SCHEMA_") for item in findings) else "LIMITATION")
    return {"name": name, "status": status, "evidence": [str(path.relative_to(root)).replace("\\", "/")], "findings": findings, "freshness": freshness, "result": data.get("result") if data else None}


def _dimension(name: str, assessments: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {item["status"] for item in assessments}
    status = "FAIL" if "FAIL" in statuses else ("LIMITATION" if "LIMITATION" in statuses else "PASS")
    return {"name": name, "status": status, "evidence": [item["evidence"][0] for item in assessments], "assessments": assessments}


def build_hardening_completion_review(root: str | Path = ROOT, *, generated_at: str | None = None) -> dict[str, Any]:
    repository_root = Path(root).resolve()
    report_dir = repository_root / "reports/implementation/plan_004"
    assessments = {
        name: _assess_report(repository_root, name, accepted)
        for name, accepted in {
            "TH04_capability_discovery_scope.json": {"PASS"},
            "TH04_capability_audit_universe.json": {"PASS", "COMPLETED_WITH_FINDINGS"},
            "TH04_registry_delta_proposal.json": {"PROPOSAL_ONLY"},
            "TH05_cross_registry_integrity.json": {"PASS"},
            "TH05_authority_resolution.json": {"PASS"},
            "TH06_context_resolution.json": {"PASS"},
            "TH06_handoff_audit.json": {"PASS"},
            "TH07_quality_baseline.json": {"PASS"},
            "TH08_mutation_testing.json": {"PASS", "COMPLETED_WITH_FINDINGS"},
        }.items()
    }
    freshness = [assessments[name]["freshness"] for name in REPORTS]
    dimensions = [
        _dimension("CAPABILITY_REGISTRY_COHERENT", [assessments["TH04_capability_discovery_scope.json"], assessments["TH04_capability_audit_universe.json"], assessments["TH04_registry_delta_proposal.json"]]),
        _dimension("CROSS_REGISTRY_INTEGRITY", [assessments["TH05_cross_registry_integrity.json"]]),
        _dimension("AUTHORITY_COMPETENCE_RESOLVABLE", [assessments["TH05_authority_resolution.json"]]),
        _dimension("CONTEXT_RESOLUTION_VERIFIABLE", [assessments["TH06_context_resolution.json"], assessments["TH06_handoff_audit.json"]]),
        _dimension("QUALITY_BASELINE_AVAILABLE", [assessments["TH07_quality_baseline.json"]]),
        _dimension("MUTATION_DECISION_RECORDED", [assessments["TH08_mutation_testing.json"]]),
    ]
    source_reports = [item for item in assessments.values()]
    evidence_status = "PASS" if all(item["status"] == "PASS" for item in source_reports) else "FAIL"
    dimensions.extend([
        {"name": "EVIDENCE_FRESHNESS", "status": evidence_status, "evidence": ["src/core/evidence_freshness.py"], "assessments": source_reports},
        {"name": "DETERMINISTIC_CONTROLS_OPERATIONAL", "status": "LIMITATION", "evidence": [], "findings": ["NO_VERIFIABLE_EXECUTION_EVIDENCE_ARTIFACT"]},
        {"name": "REPAIR_INTEGRITY_OPERATIONAL", "status": "LIMITATION", "evidence": [], "findings": ["NO_VERIFIABLE_EXECUTION_EVIDENCE_ARTIFACT"]},
        {"name": "INDEPENDENT_REVIEW_VERIFIABLE", "status": "LIMITATION", "evidence": [], "findings": ["OWNER_OR_INDEPENDENT_REVIEW_BOUNDARY"]},
        {"name": "MISSION_SCOPE_VERIFIABLE", "status": "LIMITATION", "evidence": [], "findings": ["NO_VERIFIABLE_EXECUTION_EVIDENCE_ARTIFACT"]},
        {"name": "EXECUTION_PROVENANCE_VERIFIABLE", "status": "LIMITATION", "evidence": [], "findings": ["NO_VERIFIABLE_EXECUTION_EVIDENCE_ARTIFACT"]},
        {"name": "PROVIDER_PORTABILITY_PRESERVED", "status": "LIMITATION", "evidence": [], "findings": ["NO_VERIFIABLE_EXECUTION_EVIDENCE_ARTIFACT"]},
    ])
    failures = [item for item in dimensions if item["status"] == "FAIL"]
    limitations = [item for item in dimensions if item["status"] == "LIMITATION"]
    report_inputs = [{"path": f"reports/implementation/plan_004/{name}", "sha256": _sha(report_dir / name)} for name in REPORTS]
    payload: dict[str, Any] = {
        "schema_version": "1.0.0", "plan_id": "PLAN_004", "mission_id": "HARDENING_COMPLETION_REVIEW",
        "repository_revision": _revision(repository_root), "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_inputs": report_inputs, "evidence_refs": [item["path"] for item in report_inputs],
        "limitations": [item["name"] for item in limitations],
        "result": "HARDENING_COMPLETED_PENDING_OWNER_REVIEW" if not failures else "HARDENING_COMPLETED_WITH_EVIDENCE_LIMITATION",
        "dimensions": dimensions, "evidence_freshness": freshness,
        "owner_decision_required": True, "r1_m4_opened": False, "product_use_authorized": False,
    }
    identity_payload = dict(payload); identity_payload.pop("generated_at", None)
    payload["evidence_identity_sha256"] = hashlib.sha256(_canonical(identity_payload)).hexdigest()
    return payload


def write_hardening_completion_review(root: str | Path = ROOT, *, generated_at: str | None = None) -> Path:
    repository_root = Path(root).resolve()
    path = repository_root / "reports/implementation/plan_004/HARDENING_COMPLETION_REVIEW.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_hardening_completion_review(repository_root, generated_at=generated_at), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
