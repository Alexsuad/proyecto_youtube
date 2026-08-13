"""T2-A — Evidence Reuse + Semantic Applicability for PLAN 006.

Decides whether existing evidence can be reused for the concrete current use
without re-running expensive verification. Central rule (PLAN 006 §10A.2):

    FRESH != AUTOMATICALLY REUSABLE

Reuse requires structural validity + freshness/historical validity + unchanged
material dependencies + semantic compatibility with the intended use.

Consumes the existing evidence-freshness surface (check_transitive_freshness,
sha256_path) and the historical-completion surface from T1. Plan_006 evidence
reports use the plan_006 evidence envelope, whose schema is not registered in
the foreign evidence_freshness map; for them this module validates freshness
against the plan_006 envelope with the same fail-closed semantics. It does not
create a second observability or evidence-status system.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.evidence_freshness import (
    check_report_freshness,
    check_transitive_freshness,
    sha256_path,
)
from src.core.historical_completion import (
    CompletionSnapshot,
    CurrentApplicability,
    evaluate_current_applicability,
)

REUSE = "REUSE"
TARGETED_REVERIFY = "TARGETED_REVERIFY"
RERUN_REQUIRED = "RERUN_REQUIRED"
UNVERIFIABLE = "UNVERIFIABLE"

REUSE_DECISIONS = (REUSE, TARGETED_REVERIFY, RERUN_REQUIRED, UNVERIFIABLE)

_PLAN_006_REPORTS = ("reports/implementation/plan_006/",)


def _is_plan_006_report(reference: str) -> bool:
    return reference.replace("\\", "/").startswith(_PLAN_006_REPORTS)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class IntendedUse:
    scope: str
    coverage_required: str
    intended_assurance: str
    environment: str = "ANY"
    repository_revision: str | None = None


@dataclass(frozen=True)
class MaterialDependency:
    path: str
    sha256: str


@dataclass(frozen=True)
class ReuseDecision:
    decision: str
    reasons: tuple[str, ...]
    evidence_ref: str | None = None
    snapshot: CompletionSnapshot | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reasons": list(self.reasons),
            "evidence_ref": self.evidence_ref,
            "snapshot_identity": self.snapshot.to_frozen() if self.snapshot else None,
            "provenance": self.provenance,
        }


def check_plan_006_report_freshness(root: str | Path, reference: str) -> dict[str, Any]:
    """Schema-aware freshness for plan_006 evidence (fail-closed, same semantics).

    Validates the plan_006 evidence envelope, its identity checksum and its
    source_inputs hashes. Mirrors evidence_freshness.check_report_freshness
    without requiring registration in the foreign schema map.
    """
    repository_root = Path(root).resolve()
    report = repository_root / Path(reference)
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"report": reference, "status": "UNVERIFIABLE", "violations": [f"REPORT_UNREADABLE:{exc}"]}
    violations = [f"SCHEMA_INVALID:{entry}" for entry in validate_against_schema(data, "plan_006_evidence_envelope")]
    identity = dict(data)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    expected_identity = data.get("evidence_identity_sha256")
    if isinstance(expected_identity, str) and expected_identity:
        calculated = hashlib.sha256(
            json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if calculated.lower() != expected_identity.lower():
            violations.append("EVIDENCE_IDENTITY_MISMATCH")
    mismatches: list[str] = []
    for entry in data.get("source_inputs", []):
        relative = str(entry.get("path", "")).replace("\\", "/")
        source = repository_root / relative
        if not source.is_file():
            violations.append(f"EVIDENCE_REF_UNVERIFIABLE:{relative}")
            continue
        if sha256_path(source).lower() != str(entry.get("sha256", "")).lower():
            mismatches.append(relative)
    if mismatches:
        return {"report": reference, "status": "STALE", "mismatches": mismatches, "violations": []}
    if violations:
        return {"report": reference, "status": "UNVERIFIABLE", "violations": violations}
    return {"report": reference, "status": "FRESH", "violations": []}


def evaluate_evidence_reuse(
    root: str | Path,
    evidence_ref: str,
    *,
    intended_use: IntendedUse,
    material_dependencies: list[MaterialDependency],
    snapshot: CompletionSnapshot | None = None,
) -> ReuseDecision:
    """Decide REUSE / TARGETED_REVERIFY / RERUN_REQUIRED / UNVERIFIABLE.

    Fail-closed: any dependency that cannot be verified resolves to
    UNVERIFIABLE, never to REUSE.
    """
    repository_root = Path(root).resolve()
    evidence_path = repository_root / Path(evidence_ref)
    if not evidence_path.is_file():
        return ReuseDecision(UNVERIFIABLE, ("EVIDENCE_REF_UNRESOLVED",), evidence_ref=evidence_ref)

    if _is_plan_006_report(evidence_ref):
        freshness = check_plan_006_report_freshness(repository_root, evidence_ref)
    else:
        freshness = check_report_freshness(repository_root, evidence_ref)
    if freshness["status"] == "STALE":
        return ReuseDecision(
            RERUN_REQUIRED,
            ("EVIDENCE_STALE",),
            evidence_ref=evidence_ref,
            provenance={"direct_freshness": freshness},
        )
    if freshness["status"] == "UNVERIFIABLE":
        return ReuseDecision(
            UNVERIFIABLE,
            ("EVIDENCE_UNVERIFIABLE",) + tuple(freshness.get("violations", [])),
            evidence_ref=evidence_ref,
            provenance={"direct_freshness": freshness},
        )

    if _is_plan_006_report(evidence_ref):
        transitive = check_plan_006_report_freshness(repository_root, evidence_ref)
    else:
        transitive = check_transitive_freshness(repository_root, evidence_ref)
    if transitive["status"] == "STALE":
        return ReuseDecision(
            RERUN_REQUIRED,
            ("TRANSITIVE_EVIDENCE_STALE",),
            evidence_ref=evidence_ref,
            provenance={"transitive_freshness": transitive},
        )
    if transitive["status"] == "UNVERIFIABLE":
        return ReuseDecision(
            UNVERIFIABLE,
            ("TRANSITIVE_EVIDENCE_UNVERIFIABLE",),
            evidence_ref=evidence_ref,
            provenance={"transitive_freshness": transitive},
        )

    for dependency in material_dependencies:
        dependency_path = repository_root / Path(dependency.path)
        if not dependency_path.is_file():
            return ReuseDecision(
                UNVERIFIABLE,
                (f"MATERIAL_DEPENDENCY_MISSING:{dependency.path}",),
                evidence_ref=evidence_ref,
                provenance={"dependency": dependency.path},
            )
        try:
            actual = _sha256_file(dependency_path)
        except OSError as exc:
            return ReuseDecision(
                UNVERIFIABLE,
                (f"MATERIAL_DEPENDENCY_UNREADABLE:{dependency.path}",),
                evidence_ref=evidence_ref,
                provenance={"dependency": dependency.path, "error": type(exc).__name__},
            )
        if actual.lower() != dependency.sha256.lower():
            return ReuseDecision(
                TARGETED_REVERIFY,
                (f"MATERIAL_DEPENDENCY_CHANGED:{dependency.path}",),
                evidence_ref=evidence_ref,
                provenance={"dependency": dependency.path, "expected_sha256": dependency.sha256, "actual_sha256": actual},
            )

    if snapshot is not None:
        applicability = evaluate_current_applicability(
            snapshot=snapshot,
            current_live_state_sha256=_sha256_file(repository_root / Path(snapshot.live_state_path))
            if (repository_root / Path(snapshot.live_state_path)).is_file()
            else "UNVERIFIABLE",
            material_dependency_hashes={dep.path: dep.sha256 for dep in material_dependencies},
        )
        if not applicability.applicable:
            return ReuseDecision(
                TARGETED_REVERIFY,
                applicability.reasons,
                evidence_ref=evidence_ref,
                snapshot=snapshot,
                provenance={"current_applicability": applicability.to_dict()},
            )

    compatibility = _semantic_compatibility(intended_use, evidence_path)
    if compatibility:
        return ReuseDecision(
            TARGETED_REVERIFY,
            tuple(compatibility),
            evidence_ref=evidence_ref,
            provenance={"intended_use": intended_use.__dict__},
        )

    return ReuseDecision(
        REUSE,
        ("STRUCTURAL_VALID", "FRESH", "MATERIAL_DEPS_UNCHANGED", "COVERAGE_COMPATIBLE"),
        evidence_ref=evidence_ref,
        snapshot=snapshot,
        provenance={"intended_use": intended_use.__dict__},
    )


def _semantic_compatibility(intended_use: IntendedUse, evidence_path: Path) -> list[str]:
    """Return semantic incompatibilities against declared evidence metadata.

    FRESH evidence is reusable only if it declares compatible scope, coverage,
    assurance, environment and revision. Older envelopes lacking that semantic
    declaration are intentionally downgraded to TARGETED_REVERIFY.
    """
    try:
        data = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ["SEMANTIC_DECLARATION_UNVERIFIABLE"]
    declared = data.get("semantic_applicability")
    if not isinstance(declared, dict):
        return ["SEMANTIC_DECLARATION_MISSING"]
    required = ("scope", "coverage_required", "intended_assurance", "environment", "repository_revision")
    if any(not isinstance(declared.get(key), str) or not declared[key] for key in required):
        return ["SEMANTIC_DECLARATION_INCOMPLETE"]
    mismatches: list[str] = []
    for field in required:
        expected = getattr(intended_use, field)
        if expected is None:
            continue
        if declared[field] != expected:
            mismatches.append(f"SEMANTIC_{field.upper()}_MISMATCH")
    return mismatches
