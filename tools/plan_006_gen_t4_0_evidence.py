"""Generate PLAN 006 T4.0 gap analysis evidence report.

Reproducible from the repo root:  python -3 tools/plan_006_gen_t4_0_evidence.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.gap_analysis import run_gap_analysis
from src.core.lean_measurement import build_baseline_report, build_measurement_contract, write_baseline_report, _evidence_identity

METRICS = {
    "mission_wall_time": "NOT_OBSERVABLE",
    "commands_executed": 2,
    "unique_tests_or_test_groups_executed": 13,
    "tests_repeated_equivalently": 0,
    "full_suite_runs": 0,
    "targeted_suite_runs": 1,
    "gates_executed": 0,
    "resolved_context_size": "NOT_OBSERVABLE",
    "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
    "context_references_count": 6,
    "context_expansions": 0,
    "delegation_decision": "INLINE",
    "findings_before_completion": 0,
    "findings_after_completion": 0,
    "false_convergence_events": 0,
    "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "actual_git_diff_files": 2,
    "staged_files": 0,
    "commit_count": 0,
}

PHASES = {
    "context_discovery": {"present": True},
    "planning_reasoning": {"present": True},
    "implementation": {"present": True},
    "deterministic_validation": {"present": True},
    "independent_review": {"status": "PENDING"},
    "repair": {"iterations": 0},
    "revalidation": {"present": True},
    "git_operations": {"status": "PENDING"},
}

CONTRACTS = [
    build_measurement_contract(
        metric="gap_classification",
        baseline="ALREADY_COVERED / PARTIALLY_COVERED / REAL_GAP with surface evidence",
        comparison_unit="need",
        capture_method="run_gap_analysis + analyze_gaps against live surfaces",
        observability="MEASURED",
        decision_rule="implement only REAL_GAP with minimum change and evidence",
        evidence_reference="reports/implementation/plan_006/T4_0_GAP_ANALYSIS.json",
    )
]


def main() -> None:
    result = run_gap_analysis(ROOT)
    gaps = result.to_dict()
    payload = build_baseline_report(
        ROOT,
        mission_id="PLAN_006_T4_0_GAP_ANALYSIS",
        increment="T4-0",
        metrics=METRICS,
        phases=PHASES,
        measurement_contracts=CONTRACTS,
        source_paths=[
            "plans/001_CONTROL_OPERATIVO.md",
            "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md",
            "src/core/gap_analysis.py",
            "config/delegation_policy.json",
            "config/agent_execution_profiles.json",
            "src/core/routing_policy.py",
            "src/core/context_resolution.py",
            "src/core/review_workload.py",
            "src/core/mission_authorization.py",
        ],
        authority={"live_state_path": "plans/001_CONTROL_OPERATIVO.md"},
        limitations=[],
    )
    payload["phases"] = {
        "context_discovery": {"present": True},
        "planning_reasoning": {"present": True},
        "implementation": {"present": True},
        "deterministic_validation": {"present": True},
        "independent_review": {"status": "PENDING"},
        "repair": {"iterations": 0},
        "revalidation": {"present": True},
        "git_operations": {"status": "PENDING"},
    }
    payload["metrics"]["needs_analyzed"] = len(gaps["findings"])
    payload["metrics"]["real_gap_count"] = len(gaps["real_gaps"])
    payload["metrics"]["partially_covered_count"] = len(gaps["partially_covered"])
    payload["metrics"]["gap_findings_json"] = json.dumps(gaps["findings"], sort_keys=True)
    payload["metrics"]["real_gaps_json"] = json.dumps(gaps["real_gaps"], sort_keys=True)
    payload["evidence_identity_sha256"] = _evidence_identity(payload)
    report_path = write_baseline_report(
        ROOT,
        payload,
        artifact_ref="reports/implementation/plan_006/T4_0_GAP_ANALYSIS.json",
    )
    errors = validate_against_schema(payload, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {report_path}")
    print("REAL_GAPS:", gaps["real_gaps"])
    print("PARTIAL:", gaps["partially_covered"])


if __name__ == "__main__":
    main()
