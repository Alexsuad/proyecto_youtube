"""Generate PLAN 006 T0 baseline evidence report (measurement baseline).

Reproducible from the repo root:  python -3 tools/plan_006_gen_t0_evidence.py

Preserves the observed mission metrics (including NOT_OBSERVABLE where the
harness does not surface them) and the measurement contracts. Recomputed
source_inputs hashes are bound to the current reconciled repository state.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.lean_measurement import build_baseline_report, build_measurement_contract, write_baseline_report

METRICS = {
    "mission_wall_time": "NOT_OBSERVABLE",
    "phase_wall_time": "NOT_OBSERVABLE",
    "command_wall_time": "NOT_OBSERVABLE",
    "commands_executed": 6,
    "unique_tests_or_test_groups_executed": "NOT_OBSERVABLE",
    "tests_repeated_equivalently": "NOT_OBSERVABLE",
    "full_suite_runs": "NOT_OBSERVABLE",
    "targeted_suite_runs": "NOT_OBSERVABLE",
    "gates_executed": 1,
    "resolved_context_size": "NOT_OBSERVABLE",
    "estimated_tokens_method": "NOT_OBSERVABLE",
    "context_references_count": "NOT_OBSERVABLE",
    "context_expansions": "NOT_OBSERVABLE",
    "self_contained_handoffs": "NOT_OBSERVABLE",
    "delegation_decision": "INLINE",
    "additional_actors_used": 1,
    "delegated_context_size": "NOT_OBSERVABLE",
    "delegation_overhead": "NOT_OBSERVABLE",
    "parallel_or_sequential": "SEQUENTIAL",
    "repair_iterations": 0,
    "revalidation_iterations": 0,
    "findings_before_completion": 0,
    "findings_after_completion": 0,
    "false_convergence_events": "NOT_OBSERVABLE",
    "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "actual_git_diff_files": "NOT_OBSERVABLE",
    "staged_files": "NOT_OBSERVABLE",
    "commit_count": 0,
}

PHASES = {}

CONTRACTS = [
    build_measurement_contract(
        metric="full_suite_runs",
        baseline="0",
        comparison_unit="runs_per_mission",
        capture_method="count",
        observability="NOT_OBSERVABLE",
        decision_rule="reduce_repeated_equivalent_full_suite_runs",
        evidence_reference="reports/implementation/plan_006/T0_BASELINE.json",
    ),
    build_measurement_contract(
        metric="gates_executed",
        baseline="1",
        comparison_unit="gates_per_mission",
        capture_method="count",
        observability="MEASURED",
        decision_rule="keep_proportional_to_scope",
        evidence_reference="reports/implementation/plan_006/T0_BASELINE.json",
    ),
    build_measurement_contract(
        metric="tests_repeated_equivalently",
        baseline="0",
        comparison_unit="equivalent_runs_per_mission",
        capture_method="telemetry",
        observability="NOT_OBSERVABLE",
        decision_rule="eliminate_repeated_equivalent_work",
        evidence_reference="reports/implementation/plan_006/T0_BASELINE.json",
    ),
    build_measurement_contract(
        metric="resolved_context_size",
        baseline="NOT_OBSERVABLE",
        comparison_unit="bytes",
        capture_method="resolved_context_manifest",
        observability="NOT_OBSERVABLE",
        decision_rule="minimum_sufficient_context",
        evidence_reference="reports/implementation/plan_006/T0_BASELINE.json",
    ),
    build_measurement_contract(
        metric="mission_wall_time",
        baseline="NOT_OBSERVABLE",
        comparison_unit="seconds",
        capture_method="infrastructure",
        observability="NOT_OBSERVABLE",
        decision_rule="attribute_time_to_phases_when_observable",
        evidence_reference="reports/implementation/plan_006/T0_BASELINE.json",
    ),
]

LIMITATIONS = [
    "No real operational mission was executed; wall time, tokens, cost, resolved context and repeated-equivalent-test counts remain NOT_OBSERVABLE per PLAN 006 §8.6.",
    "R1-M5 is a historical negative reference benchmark only and is never reactivated as a live phase (PLAN 006 §8.7.A).",
    "The 21 passing tests are technical harness evidence only and do not authorize product readiness.",
]


def main() -> None:
    payload = build_baseline_report(
        ROOT,
        mission_id="PLAN_006_T0_IMPLEMENTATION",
        increment="T0_BASELINE",
        metrics=METRICS,
        phases=PHASES,
        measurement_contracts=CONTRACTS,
        source_paths=[
            "plans/001_CONTROL_OPERATIVO.md",
            "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md",
            "src/core/lean_measurement.py",
            "src/core/historical_completion.py",
            "config/execution_benchmark_matrix.json",
        ],
        limitations=LIMITATIONS,
    )
    report_path = write_baseline_report(
        ROOT,
        payload,
        artifact_ref="reports/implementation/plan_006/T0_BASELINE.json",
    )
    errors = validate_against_schema(payload, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {report_path}")
    print("BASELINE RESULT:", payload["result"])


if __name__ == "__main__":
    main()