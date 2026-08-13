"""Generate PLAN 006 T5 evidence report (measured OpenCode pilot with temporary subagents).

Reproducible from the repo root:  python -3 tools/plan_006_gen_t5_evidence.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.lean_measurement import build_baseline_report, build_measurement_contract, write_baseline_report
from src.core.plan_006_closure_check import run_closure_check

METRICS = {
    "mission_wall_time": "NOT_OBSERVABLE",
    "commands_executed": 4,
    "unique_tests_or_test_groups_executed": 7,
    "tests_repeated_equivalently": 0,
    "full_suite_runs": 0,
    "targeted_suite_runs": 2,
    "gates_executed": 0,
    "resolved_context_size": "NOT_OBSERVABLE",
    "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
    "context_references_count": 8,
    "context_expansions": 0,
    "delegation_decision": "DELEGATE",
    "additional_actors_used": 2,
    "delegated_context_size": "NOT_OBSERVABLE",
    "delegation_overhead": "NOT_OBSERVABLE",
    "parallel_or_sequential": "PARALLEL",
    "repair_iterations": 2,
    "revalidation_iterations": 2,
    "findings_before_completion": 3,
    "findings_after_completion": 0,
    "false_convergence_events": 0,
    "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "actual_git_diff_files": 3,
    "staged_files": 0,
    "commit_count": 0,
}

PHASES = {
    "context_discovery": {"present": True, "delegated": True},
    "planning_reasoning": {"present": True},
    "implementation": {"present": True, "topology": "PRIMARY"},
    "deterministic_validation": {"present": True},
    "independent_review": {"status": "PENDING"},
    "repair": {"iterations": 2},
    "revalidation": {"present": True},
    "git_operations": {"status": "PENDING"},
}

CONTRACTS = [
    build_measurement_contract(
        metric="delegation_decision",
        baseline="INLINE/DELEGATE/ESCALATE bounded by T5 authorization",
        comparison_unit="decision",
        capture_method="measured pilot: 2 temporary explore subagents in parallel, primary implementation, depth 1",
        observability="MEASURED",
        decision_rule="DELEGATE valid only inside T5 pilot; ends with T5; no persistent agents; no functional authority",
        evidence_reference="reports/implementation/plan_006/T5_PILOT.json",
    ),
    build_measurement_contract(
        metric="pilot_topology",
        baseline="temporary subagents decided dynamically by orchestrator",
        comparison_unit="topology",
        capture_method="OpenCode native Task/explore/general; no .opencode/agents/* created",
        observability="MEASURED",
        decision_rule="max depth 1; parallel only for independent discovery; review independent",
        evidence_reference="reports/implementation/plan_006/T5_PILOT.json",
    ),
]

CLOSURE_FINDINGS_JSON = {
    "closure_overall": None,
    "closure_findings": [],
}


def main() -> None:
    closure = run_closure_check(ROOT, mission_id="PLAN_006_T5_MEASURED_OPENCODE_PILOT")
    CLOSURE_FINDINGS_JSON["closure_overall"] = closure.overall
    CLOSURE_FINDINGS_JSON["closure_findings"] = closure.to_dict()["findings"]

    payload = build_baseline_report(
        ROOT,
        mission_id="PLAN_006_T5_MEASURED_OPENCODE_PILOT",
        increment="T5",
        metrics=METRICS,
        phases=PHASES,
        measurement_contracts=CONTRACTS,
        source_paths=[
            "plans/001_CONTROL_OPERATIVO.md",
            "plans/plan_006/PLAN_006_T5_AUTHORIZATION.json",
            "plans/plan_006/PLAN_006_T5_AUTHORITY.json",
            "src/core/plan_006_closure_check.py",
            "tests/core/test_plan_006_t5_closure_check.py",
        ],
        authority={"live_state_path": "plans/001_CONTROL_OPERATIVO.md"},
        limitations=[
            "Pilot scoped to T5; DELEGATE validity ends with T5; no persistent agents or agent catalogs created",
            "wall_time/context sizes recorded NOT_OBSERVABLE (harness does not surface them deterministically)",
        ],
    )
    payload["metrics"]["closure_report_json"] = json.dumps(CLOSURE_FINDINGS_JSON, sort_keys=True)
    payload["evidence_identity_sha256"] = _identity(payload)
    report_path = write_baseline_report(
        ROOT,
        payload,
        artifact_ref="reports/implementation/plan_006/T5_PILOT.json",
    )
    errors = validate_against_schema(payload, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {report_path}")
    print("CLOSURE OVERALL:", closure.overall)


def _identity(payload: dict) -> str:
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    main()