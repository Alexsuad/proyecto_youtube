"""Generate PLAN 006 T3 evidence report (permission model baseline verification).

Reproducible from the repo root:  python -3 tools/plan_006_gen_t3_evidence.py
Consumes existing surfaces; validates the envelope against the canonical schema.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.lean_measurement import build_baseline_report, build_measurement_contract, write_baseline_report

CONFIG = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
PERMISSION_BLOCK = CONFIG.get("permission")
GRANULAR = bool(PERMISSION_BLOCK and PERMISSION_BLOCK.get("bash") == {"rm -rf *": "deny"})

METRICS = {
    "mission_wall_time": "NOT_OBSERVABLE",
    "commands_executed": 2,
    "unique_tests_or_test_groups_executed": 4,
    "tests_repeated_equivalently": 0,
    "full_suite_runs": 0,
    "targeted_suite_runs": 2,
    "gates_executed": 0,
    "resolved_context_size": "NOT_OBSERVABLE",
    "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
    "context_references_count": 3,
    "context_expansions": 0,
    "delegation_decision": "INLINE",
    "findings_before_completion": 1,
    "findings_after_completion": 0,
    "false_convergence_events": 0,
    "initial_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "final_head": "29b5218778f045b17f2b4c9d456e0b2457c46be8",
    "actual_git_diff_files": 0,
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
        metric="permission_model",
        baseline="granular sanctioned protection, no deny-by-default, no allowlist",
        comparison_unit="config",
        capture_method="read opencode.json + run tests/opencode/test_controlled_integration.py",
        observability="MEASURED",
        decision_rule="config must match PLAN 006 11.3 (granular only)",
        evidence_reference="reports/implementation/plan_006/T3_PERMISSION_MODEL.json",
    )
]


def main() -> None:
    source_paths = [
        "plans/001_CONTROL_OPERATIVO.md",
        "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md",
        "opencode.json",
        "tests/opencode/test_controlled_integration.py",
    ]
    limitations = []
    if not GRANULAR:
        limitations.append("OPENCODE_JSON_PERMISSION_DEVIATES_FROM_SANCTIONED_GRANULAR_DENY")
    limitations.append(
        "STALE_TEST_FOREIGN_STATE:tests/opencode/test_controlled_integration.py::test_repository_does_not_impose_opencode_permissions"
        " still asserts absence of any permission block; plan 11.3 sanctions the granular 'rm -rf *' deny. "
        "Preexisting committed foreign file; not modified by PLAN 006."
    )
    payload = build_baseline_report(
        ROOT,
        mission_id="PLAN_006_T3_PERMISSION_MODEL",
        increment="T3",
        metrics=METRICS,
        phases=PHASES,
        measurement_contracts=CONTRACTS,
        source_paths=source_paths,
        authority={"live_state_path": "plans/001_CONTROL_OPERATIVO.md"},
        limitations=limitations,
    )
    payload["phases"]["git_operations"]["status"] = "PENDING"
    report_path = write_baseline_report(
        ROOT,
        payload,
        artifact_ref="reports/implementation/plan_006/T3_PERMISSION_MODEL.json",
    )
    errors = validate_against_schema(payload, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {report_path}")


if __name__ == "__main__":
    main()
