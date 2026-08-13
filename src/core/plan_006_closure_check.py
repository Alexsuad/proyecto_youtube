"""T5 — Measured OpenCode pilot: deterministic PLAN 006 closure check.

Composes the T1/T2/T4 surfaces into a single fail-closed closure verification
for the PLAN 006 technical mission (PLAN 006 §15.3, §18, §24, §30). It never
grants functional approval, never re-verifies historical completion against a
future live state, and never creates functional authority. This is the pilot
deliverable implemented by the primary orchestrator; discovery was delegated to
temporary subagents during the measured pilot.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.evidence_reuse import evaluate_evidence_reuse, IntendedUse, MaterialDependency
from src.core.evidence_reuse import check_plan_006_report_freshness
from src.core.historical_completion import verify_historical_completion
from src.core.mission_authorization import MissionAuthorizationError, load_mission_authorization
from src.core.resource_aware_decision import make_execution_decision

CLOSURE_OK = "OK"
CLOSURE_FAIL = "FAIL"

REQUIRED_INCREMENTS = ("T0", "T1", "T2-A", "T2-B", "T2-C", "T2-D", "T3", "T4-0", "T4", "T5", "D1")

FORBIDDEN_CLAIMS = ("functional_approval_claim", "product_readiness_claim")


@dataclass(frozen=True)
class ClosureFinding:
    check: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"check": self.check, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class ClosureReport:
    mission_id: str
    findings: tuple[ClosureFinding, ...]
    overall: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "overall": self.overall,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def _recompute_evidence_identity(data: dict[str, Any]) -> str:
    identity = dict(data)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_evidence(root: Path, reference: str) -> dict[str, Any] | None:
    target = root / reference
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data


def _verify_report(root: Path, reference: str) -> list[str]:
    violations: list[str] = []
    data = _load_evidence(root, reference)
    if data is None:
        return [f"EVIDENCE_UNREADABLE:{reference}"]
    schema_violations = validate_against_schema(data, "plan_006_evidence_envelope")
    violations.extend(f"SCHEMA_INVALID:{entry}" for entry in schema_violations)
    declared = data.get("evidence_identity_sha256")
    if not isinstance(declared, str) or _recompute_evidence_identity(data) != declared:
        violations.append("EVIDENCE_IDENTITY_MISMATCH")
    for claim in FORBIDDEN_CLAIMS:
        if data.get(claim) is True:
            violations.append(f"{claim.upper()}_MUST_NOT_BE_CLAIMED")
    if data.get("result") != "PASS":
        violations.append(f"EVIDENCE_RESULT_NOT_PASS:{data.get('result')}")
    freshness = check_plan_006_report_freshness(root, reference)
    if freshness["status"] != "FRESH":
        violations.append(f"EVIDENCE_NOT_FRESH:{freshness['status']}")
    return violations


def _report_path(increment: str) -> str:
    names = {
        "T0": "T0_BASELINE",
        "T1": "T1_HISTORICAL_COMPLETION",
        "T2-A": "T2_A_EVIDENCE_REUSE",
        "T2-B": "T2_B_PROPORTIONAL_VERIFICATION",
        "T2-C": "T2_C_ADVERSARIAL_ASSURANCE",
        "T2-D": "T2_D_CONTEXT_OUTPUT_ECONOMY",
        "T3": "T3_PERMISSION_MODEL",
        "T4-0": "T4_0_GAP_ANALYSIS",
        "T4": "T4_RESOURCE_AWARE_DECISION",
        "T5": "T5_PILOT",
        "D1": "D1_CONCURRENCY_DECISION",
    }
    return f"reports/implementation/plan_006/{names[increment]}.json"


def run_closure_check(
    root: str | Path,
    *,
    mission_id: str,
    increments: list[str] | None = None,
    verify_reuse_for: str | None = None,
    intended_use: IntendedUse | None = None,
    material_dependencies: list[MaterialDependency] | None = None,
    include_t5_pilot: bool = True,
) -> ClosureReport:
    """Fail-closed closure verification for the PLAN 006 technical mission.

    - authority/live state binding is read from the T5 authorization contract;
    - every required evidence report validates schema + identity + forbidden claims;
    - historical completion is verified (never against a future live state);
    - optional evidence reuse decision remains fail-closed;
    - returns OK only if no finding reports a FAIL.
    """
    repository_root = Path(root).resolve()
    findings: list[ClosureFinding] = []
    increments = list(REQUIRED_INCREMENTS if increments is None else increments)

    authorization_path = repository_root / "plans/plan_006/PLAN_006_T5_AUTHORIZATION.json"
    if not authorization_path.is_file():
        findings.append(ClosureFinding("T5_AUTHORIZATION", CLOSURE_FAIL, "PLAN_006_T5_AUTHORIZATION.json missing"))
    else:
        try:
            authorization = load_mission_authorization(authorization_path)
            authorization.verify(
                repository_root,
                capability_id="PLAN_006_T5_PILOT",
                role_id="ENGINEERING_IMPLEMENTER",
                operation="VERIFY_EVIDENCE",
                path="reports/implementation/plan_006/",
                execution_mode="SYNTHETIC",
            )
            findings.append(ClosureFinding("T5_AUTHORIZATION", CLOSURE_OK, "T5 authorization verified"))
        except (MissionAuthorizationError, OSError, ValueError, json.JSONDecodeError) as exc:
            findings.append(ClosureFinding("T5_AUTHORIZATION", CLOSURE_FAIL, str(exc)))

    for increment in increments:
        if not include_t5_pilot and increment == "T5":
            continue
        reference = _report_path(increment)
        violations = _verify_report(repository_root, reference)
        if violations:
            findings.append(ClosureFinding(f"EVIDENCE_{increment}", CLOSURE_FAIL, "; ".join(violations)))
        else:
            findings.append(ClosureFinding(f"EVIDENCE_{increment}", CLOSURE_OK, reference))

    t1_path = _report_path("T1")
    t1 = _load_evidence(repository_root, t1_path)
    if t1 is not None:
        try:
            violations = verify_historical_completion(t1)
            if violations:
                findings.append(ClosureFinding("HISTORICAL_COMPLETION", CLOSURE_FAIL, "; ".join(violations)))
            else:
                findings.append(ClosureFinding("HISTORICAL_COMPLETION", CLOSURE_OK, "T1 identity verified"))
        except Exception as exc:
            findings.append(ClosureFinding("HISTORICAL_COMPLETION", CLOSURE_FAIL, str(exc)))
    else:
        findings.append(ClosureFinding("HISTORICAL_COMPLETION", CLOSURE_FAIL, "T1 report missing"))

    if verify_reuse_for and intended_use is not None:
        decision = evaluate_evidence_reuse(
            repository_root,
            verify_reuse_for,
            intended_use=intended_use,
            material_dependencies=material_dependencies or [],
        )
        if decision.decision != "REUSE":
            findings.append(ClosureFinding("EVIDENCE_REUSE", CLOSURE_FAIL, decision.decision + ": " + ";".join(decision.reasons)))
        else:
            findings.append(ClosureFinding("EVIDENCE_REUSE", CLOSURE_OK, decision.decision))

    try:
        execution = make_execution_decision(
            task={
                "trivial": True,
                "deterministic": True,
                "separable": False,
                "risk": "LOW",
                "sensitive": False,
                "findings": False,
                "touched_surface": "src/core/plan_006_closure_check.py",
                "targeted_covers_consumers": True,
                "authorized_candidate_set": [],
            }
        )
        findings.append(ClosureFinding("EXECUTION_DECISION", CLOSURE_OK, f"topology={execution.topology}"))
    except Exception as exc:
        findings.append(ClosureFinding("EXECUTION_DECISION", CLOSURE_FAIL, str(exc)))

    overall = CLOSURE_OK if not any(finding.status == CLOSURE_FAIL for finding in findings) else CLOSURE_FAIL
    return ClosureReport(mission_id=mission_id, findings=tuple(findings), overall=overall)
