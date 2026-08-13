"""Generate PLAN 006 D1 evidence (concurrency decision).

Reproducible from the repo root:  python -3 tools/plan_006_gen_d1_decision.py
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

METRICS = {
    "mission_wall_time": "NOT_OBSERVABLE",
    "commands_executed": 0,
    "unique_tests_or_test_groups_executed": 0,
    "tests_repeated_equivalently": 0,
    "full_suite_runs": 0,
    "targeted_suite_runs": 0,
    "gates_executed": 0,
    "resolved_context_size": "NOT_OBSERVABLE",
    "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
    "context_references_count": 2,
    "context_expansions": 0,
    "delegation_decision": "NOT_APPLICABLE",
    "additional_actors_used": 0,
    "parallel_or_sequential": "SEQUENTIAL",
    "repair_iterations": 0,
    "revalidation_iterations": 0,
    "findings_before_completion": 0,
    "findings_after_completion": 0,
    "false_convergence_events": 0,
    "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "actual_git_diff_files": 1,
    "staged_files": 0,
    "commit_count": 0,
}

PHASES = {
    "context_discovery": {"present": True},
    "planning_reasoning": {"present": True},
    "implementation": {"present": False},
    "deterministic_validation": {"present": True},
    "independent_review": {"status": "PENDING"},
    "repair": {"iterations": 0},
    "revalidation": {"present": True},
    "git_operations": {"status": "PENDING"},
}

CONTRACTS = [
    build_measurement_contract(
        metric="concurrency_decision",
        baseline="NO EVIDENCE OF BENEFIT -> BUILD NOTHING (PLAN 006 §14.2)",
        comparison_unit="decision",
        capture_method="D1 based on T0 baseline and T5 measured pilot; wall time/cost NOT_OBSERVABLE",
        observability="MEASURED",
        decision_rule="no scheduler/lifecycle/wave creation; NO_CONCURRENCY_NEEDED acceptable (§14.7)",
        evidence_reference="reports/implementation/plan_006/D1_CONCURRENCY_DECISION.json",
    )
]

DECISION_JSON = {
    "decision": "NO_CONCURRENCY_NEEDED",
    "question": "Does concurrency measurably reduce wall time or cost without degrading assurance, traceability or product?",
    "evidence_considered": [
        "T0_BASELINE: wall time/cost NOT_OBSERVABLE from harness",
        "T5_PILOT: parallel discovery delegated to 2 temporary subagents; benefit not measurable in wall time/cost",
    ],
    "reasoning": [
        "No measured wall-time or cost delta exists to justify a general scheduler (§14.1)",
        "Default applies: NO EVIDENCE OF BENEFIT -> BUILD NOTHING (§14.2)",
        "No ACTIVE_WAVE/ACTIVE_MISSIONS/MISSION_DEPENDENCIES/multi-mission scheduler created (§14.3)",
        "Plan may close with NO_CONCURRENCY_NEEDED without being a failure (§14.7)",
    ],
    "trade_off": "Parallel delegation may reduce wall time in some tasks but cost/overhead is not observable; measured decision deferred until observability exists",
    "outcome": "Documented as decision only; no implementation created",
}


def main() -> None:
    payload = build_baseline_report(
        ROOT,
        mission_id="PLAN_006_D1_CONCURRENCY_DECISION",
        increment="D1",
        metrics=METRICS,
        phases=PHASES,
        measurement_contracts=CONTRACTS,
        source_paths=[
            "plans/001_CONTROL_OPERATIVO.md",
            "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md",
            "reports/implementation/plan_006/T0_BASELINE.json",
            "reports/implementation/plan_006/T5_PILOT.json",
        ],
        authority={"live_state_path": "plans/001_CONTROL_OPERATIVO.md"},
        limitations=[
            "Decision documented as artifact; no canonical enum created for D1 outcomes (PLAN 006 §14.6)",
        ],
    )
    payload["metrics"]["concurrency_decision_json"] = json.dumps(DECISION_JSON, sort_keys=True)
    payload["evidence_identity_sha256"] = _identity(payload)
    report_path = write_baseline_report(
        ROOT,
        payload,
        artifact_ref="reports/implementation/plan_006/D1_CONCURRENCY_DECISION.json",
    )
    errors = validate_against_schema(payload, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {report_path}")
    print("DECISION:", DECISION_JSON["decision"])


def _identity(payload: dict) -> str:
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    main()