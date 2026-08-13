"""Generate PLAN 006 T4 evidence report (resource-aware orchestration decision).

Reproducible from the repo root:  python -3 tools/plan_006_gen_t4_evidence.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.lean_measurement import build_baseline_report, build_measurement_contract, write_baseline_report
from src.core.resource_aware_decision import make_execution_decision

METRICS = {
    "mission_wall_time": "NOT_OBSERVABLE",
    "commands_executed": 2,
    "unique_tests_or_test_groups_executed": 18,
    "tests_repeated_equivalently": 0,
    "full_suite_runs": 0,
    "targeted_suite_runs": 1,
    "gates_executed": 0,
    "resolved_context_size": "NOT_OBSERVABLE",
    "estimated_tokens_method": "UTF8_BYTES_DIVIDED_BY_4",
    "context_references_count": 6,
    "context_expansions": 0,
    "delegation_decision": "INLINE",
    "findings_before_completion": 3,
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
    "repair": {"iterations": 1},
    "revalidation": {"present": True},
    "git_operations": {"status": "PENDING"},
}

CONTRACTS = [
    build_measurement_contract(
        metric="execution_topology",
        baseline="INLINE/DELEGATE/ESCALATE bounded by authorization",
        comparison_unit="decision",
        capture_method="make_execution_decision composing choose_delegation + review + verification",
        observability="MEASURED",
        decision_rule="reproducible; never creates functional authority; review floor never degrades",
        evidence_reference="reports/implementation/plan_006/T4_RESOURCE_AWARE_DECISION.json",
    )
]

TASK = {
    "trivial": True,
    "deterministic": True,
    "separable": False,
    "risk": "LOW",
    "sensitive": False,
    "findings": False,
    "touched_surface": "src/core/resource_aware_decision.py",
    "targeted_covers_consumers": True,
    "shared_utility": False,
    "schema_consumers": 0,
    "core_harness_touched": False,
    "repair_showed_broad_damage": False,
    "closure_needs_distinct_evidence": False,
    "authorized_candidate_set": ["opencode_free"],
    "execution_profile_id": "opencode_free",
    "owner_route_selection_authority": False,
    "resolved_context_size": 512,
    "context_budget_bytes": 1024,
    "delegation_depth": 0,
    "max_delegation_depth": 1,
}


def main() -> None:
    decision = make_execution_decision(task=TASK).to_dict()
    payload = build_baseline_report(
        ROOT,
        mission_id="PLAN_006_T4_RESOURCE_AWARE_DECISION",
        increment="T4",
        metrics=METRICS,
        phases=PHASES,
        measurement_contracts=CONTRACTS,
        source_paths=[
            "plans/001_CONTROL_OPERATIVO.md",
            "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md",
            "src/core/resource_aware_decision.py",
            "src/core/delegation_policy.py",
            "src/core/review_workload.py",
            "src/core/routing_policy.py",
            "config/agent_execution_profiles.json",
        ],
        authority={"live_state_path": "plans/001_CONTROL_OPERATIVO.md"},
        limitations=["T5 pilot not yet executed; decision validated in controlled tests only"],
    )
    payload["metrics"]["execution_decision_json"] = json.dumps(decision, sort_keys=True)
    payload["evidence_identity_sha256"] = _identity(payload)
    report_path = write_baseline_report(
        ROOT,
        payload,
        artifact_ref="reports/implementation/plan_006/T4_RESOURCE_AWARE_DECISION.json",
    )
    errors = validate_against_schema(payload, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {report_path}")
    print("TOPOLOGY:", decision["topology"], "REVIEW:", decision["review_floor"])


def _identity(payload: dict) -> str:
    import hashlib

    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    main()
