"""Generate PLAN 006 T2-A/T2-B/T2-C/T2-D evidence reports (mission record pattern).

Reproducible from the repo root:  python -3 tools/plan_006_gen_t2_evidence.py
Consumes existing surfaces; writes into reports/implementation/plan_006 and
validates each envelope against the canonical schema.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.lean_measurement import build_baseline_report, build_measurement_contract, write_baseline_report

INCREMENT_META = {
    "T2_A": {
        "artifact": "T2_A_EVIDENCE_REUSE",
        "mission": "PLAN_006_T2_A_EVIDENCE_REUSE",
        "tests": ["tests/core/test_plan_006_t2a_evidence_reuse.py"],
    },
    "T2_B": {
        "artifact": "T2_B_PROPORTIONAL_VERIFICATION",
        "mission": "PLAN_006_T2_B_PROPORTIONAL_VERIFICATION",
        "tests": ["tests/core/test_plan_006_t2b_proportional_verification.py"],
    },
    "T2_C": {
        "artifact": "T2_C_ADVERSARIAL_ASSURANCE",
        "mission": "PLAN_006_T2_C_ADVERSARIAL_ASSURANCE",
        "tests": ["tests/core/test_plan_006_t2c_adversarial_assurance.py"],
    },
    "T2_D": {
        "artifact": "T2_D_CONTEXT_OUTPUT_ECONOMY",
        "mission": "PLAN_006_T2_D_CONTEXT_OUTPUT_ECONOMY",
        "tests": ["tests/core/test_plan_006_t2d_context_output_economy.py"],
    },
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

AUTHORITY = {"live_state_path": "plans/001_CONTROL_OPERATIVO.md"}

TEST_FILES = {
    "T2_A": "tests/core/test_plan_006_t2a_evidence_reuse.py",
    "T2_B": "tests/core/test_plan_006_t2b_proportional_verification.py",
    "T2_C": "tests/core/test_plan_006_t2c_adversarial_assurance.py",
    "T2_D": "tests/core/test_plan_006_t2d_context_output_economy.py",
}

METRICS_BY_INCREMENT: dict[str, dict] = {
    "T2_A": {
        "mission_wall_time": "NOT_OBSERVABLE",
        "commands_executed": 1,
        "unique_tests_or_test_groups_executed": 6,
        "tests_repeated_equivalently": 0,
        "full_suite_runs": 0,
        "targeted_suite_runs": 1,
        "gates_executed": 0,
        "resolved_context_size": "NOT_OBSERVABLE",
        "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
        "context_references_count": 4,
        "context_expansions": 0,
        "delegation_decision": "INLINE",
        "findings_before_completion": 2,
        "findings_after_completion": 0,
        "false_convergence_events": 0,
        "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "actual_git_diff_files": 2,
        "staged_files": 0,
        "commit_count": 0,
    },
    "T2_B": {
        "mission_wall_time": "NOT_OBSERVABLE",
        "commands_executed": 1,
        "unique_tests_or_test_groups_executed": 7,
        "tests_repeated_equivalently": 0,
        "full_suite_runs": 0,
        "targeted_suite_runs": 1,
        "gates_executed": 0,
        "resolved_context_size": "NOT_OBSERVABLE",
        "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
        "context_references_count": 4,
        "context_expansions": 0,
        "delegation_decision": "INLINE",
        "findings_before_completion": 1,
        "findings_after_completion": 0,
        "false_convergence_events": 0,
        "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "actual_git_diff_files": 2,
        "staged_files": 0,
        "commit_count": 0,
    },
    "T2_C": {
        "mission_wall_time": "NOT_OBSERVABLE",
        "commands_executed": 3,
        "unique_tests_or_test_groups_executed": 28,
        "tests_repeated_equivalently": 0,
        "full_suite_runs": 0,
        "targeted_suite_runs": 3,
        "gates_executed": 0,
        "resolved_context_size": "NOT_OBSERVABLE",
        "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
        "context_references_count": 5,
        "context_expansions": 2,
        "delegation_decision": "INLINE",
        "findings_before_completion": 2,
        "findings_after_completion": 0,
        "false_convergence_events": 0,
        "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "actual_git_diff_files": 2,
        "staged_files": 0,
        "commit_count": 0,
    },
    "T2_D": {
        "mission_wall_time": "NOT_OBSERVABLE",
        "commands_executed": 2,
        "unique_tests_or_test_groups_executed": 14,
        "tests_repeated_equivalently": 0,
        "full_suite_runs": 0,
        "targeted_suite_runs": 2,
        "gates_executed": 0,
        "resolved_context_size": "NOT_OBSERVABLE",
        "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
        "context_references_count": 4,
        "context_expansions": 0,
        "delegation_decision": "INLINE",
        "findings_before_completion": 1,
        "findings_after_completion": 0,
        "false_convergence_events": 0,
        "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
        "actual_git_diff_files": 2,
        "staged_files": 0,
        "commit_count": 0,
    },
}

CONTRACTS_BY_INCREMENT: dict[str, list[dict]] = {
    "T2_A": [
        {
            "metric": "evidence_reuse_decision",
            "baseline": "FAIL_CLOSED_ON_STALE_OR_UNCOVERED",
            "comparison_unit": "decision",
            "capture_method": "check_plan_006_report_freshness + evaluate_evidence_reuse",
            "observability": "MEASURED",
            "decision_rule": "REUSE solo si FRESH y coverage compatible",
            "evidence_reference": "reports/implementation/plan_006/T2_A_EVIDENCE_REUSE.json",
        }
    ],
    "T2_B": [
        {
            "metric": "verification_plan_step",
            "baseline": "DIRECT_IMPACT -> TARGETED_SUITE",
            "comparison_unit": "step",
            "capture_method": "build_verification_plan",
            "observability": "MEASURED",
            "decision_rule": "escalar solo si material_dependency != NO_MATERIAL_IMPACT",
            "evidence_reference": "reports/implementation/plan_006/T2_B_PROPORTIONAL_VERIFICATION.json",
        }
    ],
    "T2_C": [
        {
            "metric": "must_kill_mutants_killed",
            "baseline": "all must-kill mutants killed or justified",
            "comparison_unit": "mutant",
            "capture_method": "evaluate_must_kill_mutation",
            "observability": "MEASURED",
            "decision_rule": "survivor = ASSURANCE_GAP, never ignored",
            "evidence_reference": "reports/implementation/plan_006/T2_C_ADVERSARIAL_ASSURANCE.json",
        }
    ],
    "T2_D": [
        {
            "metric": "product_impact_check",
            "baseline": "touched surface -> known consumers -> targeted regression",
            "comparison_unit": "surface",
            "capture_method": "run_product_impact_check",
            "observability": "MEASURED",
            "decision_rule": "fail-closed si NO_KNOWN_CONSUMERS",
            "evidence_reference": "reports/implementation/plan_006/T2_D_CONTEXT_OUTPUT_ECONOMY.json",
        }
    ],
}

CONTRACT_FIELDS = (
    "metric",
    "baseline",
    "comparison_unit",
    "capture_method",
    "observability",
    "decision_rule",
    "evidence_reference",
)


def main() -> None:
    generated = []
    for increment, meta in INCREMENT_META.items():
        source_paths = [
            "plans/001_CONTROL_OPERATIVO.md",
            "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md",
            TEST_FILES[increment],
        ]
        contracts = [
            build_measurement_contract(**contract)
            for contract in CONTRACTS_BY_INCREMENT[increment]
        ]
        payload = build_baseline_report(
            ROOT,
            mission_id=meta["mission"],
            increment=increment.replace("_", "-"),
            metrics=METRICS_BY_INCREMENT[increment],
            phases=PHASES,
            measurement_contracts=contracts,
            source_paths=source_paths,
            authority=AUTHORITY,
        )
        report_path = write_baseline_report(
            ROOT,
            payload,
            artifact_ref=f"reports/implementation/plan_006/{meta['artifact']}.json",
        )
        errors = validate_against_schema(payload, "plan_006_evidence_envelope")
        if errors:
            raise SystemExit(f"SCHEMA_ERROR {increment}: {errors}")
        generated.append(str(report_path))
        print(f"OK {increment} -> {report_path}")
    print("GENERATED", len(generated))


if __name__ == "__main__":
    main()