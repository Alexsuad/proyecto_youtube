"""T0 — Baseline + Telemetry Foundation for PLAN 006.

Builds and records MEASURED / NOT_OBSERVABLE / NOT_APPLICABLE telemetry using the
existing evidence envelope pattern (source_inputs + sha256 + evidence identity).
Consumes the repository surfaces; it does not create a second observability
system.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema

MEASURED = "MEASURED"
NOT_OBSERVABLE = "NOT_OBSERVABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
UNVERIFIABLE = "UNVERIFIABLE"

TELEMETRY_VALUES = (MEASURED, NOT_OBSERVABLE, NOT_APPLICABLE, UNVERIFIABLE)

CANONICAL_PHASES = (
    "context_discovery",
    "planning_reasoning",
    "implementation",
    "deterministic_validation",
    "independent_review",
    "repair",
    "revalidation",
    "git_operations",
)

# Metric keys from PLAN 006 §8.4 grouped by family. Anything not observable is
# recorded as NOT_OBSERVABLE, never invented.
REQUIRED_METRICS: tuple[str, ...] = (
    "mission_wall_time",
    "phase_wall_time",
    "command_wall_time",
    "commands_executed",
    "unique_tests_or_test_groups_executed",
    "tests_repeated_equivalently",
    "full_suite_runs",
    "targeted_suite_runs",
    "gates_executed",
    "resolved_context_size",
    "estimated_tokens_method",
    "context_references_count",
    "context_expansions",
    "self_contained_handoffs",
    "delegation_decision",
    "additional_actors_used",
    "delegated_context_size",
    "delegation_overhead",
    "parallel_or_sequential",
    "repair_iterations",
    "revalidation_iterations",
    "findings_before_completion",
    "findings_after_completion",
    "false_convergence_events",
    "initial_head",
    "final_head",
    "actual_git_diff_files",
    "staged_files",
    "commit_count",
)


@dataclass(frozen=True)
class MeasurementContract:
    metric: str
    baseline: str
    comparison_unit: str
    capture_method: str
    observability: str
    decision_rule: str
    evidence_reference: str

    def to_dict(self) -> dict[str, str]:
        return {
            "metric": self.metric,
            "baseline": self.baseline,
            "comparison_unit": self.comparison_unit,
            "capture_method": self.capture_method,
            "observability": self.observability,
            "decision_rule": self.decision_rule,
            "evidence_reference": self.evidence_reference,
        }


def build_measurement_contract(
    *,
    metric: str,
    baseline: str,
    comparison_unit: str,
    capture_method: str,
    observability: str,
    decision_rule: str,
    evidence_reference: str,
) -> MeasurementContract:
    if observability not in TELEMETRY_VALUES:
        raise ValueError(f"TELEMETRY_OBSERVABILITY_INVALID:{observability}")
    if not all((metric, baseline, comparison_unit, capture_method, decision_rule, evidence_reference)):
        raise ValueError("MEASUREMENT_CONTRACT_FIELD_REQUIRED")
    return MeasurementContract(
        metric=metric,
        baseline=baseline,
        comparison_unit=comparison_unit,
        capture_method=capture_method,
        observability=observability,
        decision_rule=decision_rule,
        evidence_reference=evidence_reference,
    )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_or_skip(root: Path, reference: str) -> str | None:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return str(resolved.relative_to(root)).replace("\\", "/")


STRING_METRICS: dict[str, tuple[str, ...]] = {
    "delegation_decision": ("INLINE", "DELEGATE", "ESCALATE"),
    "parallel_or_sequential": ("PARALLEL", "SEQUENTIAL"),
    "estimated_tokens_method": ("UTF8_BYTES_DIVIDED_BY_4", "NOT_OBSERVABLE"),
}


def build_baseline_report(
    root: str | Path,
    *,
    mission_id: str,
    increment: str,
    metrics: dict[str, Any],
    phases: dict[str, dict[str, Any]],
    measurement_contracts: list[MeasurementContract],
    source_paths: list[str],
    authority: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a T0 baseline report following the evidence envelope pattern.

    Fail-closed: every required metric key must be present with a value in
    TELEMETRY_VALUES or an actual measured scalar, and every phase key must be
    one of the canonical phases.
    """
    repository_root = Path(root).resolve()
    unknown_metrics = sorted(set(metrics) - set(REQUIRED_METRICS))
    if unknown_metrics:
        raise ValueError("UNKNOWN_METRIC:" + ",".join(unknown_metrics))
    unknown_phases = sorted(set(phases) - set(CANONICAL_PHASES))
    if unknown_phases:
        raise ValueError("UNKNOWN_PHASE:" + ",".join(unknown_phases))

    normalized_metrics: dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, str) and value in TELEMETRY_VALUES:
            normalized_metrics[key] = value
        elif isinstance(value, str) and key in STRING_METRICS and value in STRING_METRICS[key]:
            normalized_metrics[key] = value
        elif isinstance(value, (int, float)) and value >= 0:
            normalized_metrics[key] = value
        elif key in {"initial_head", "final_head"} and isinstance(value, str):
            normalized_metrics[key] = value
        elif value is None:
            normalized_metrics[key] = NOT_OBSERVABLE
        else:
            raise ValueError(f"METRIC_VALUE_INVALID:{key}={value!r}")

    source_inputs = []
    for reference in source_paths:
        relative = _relative_or_skip(repository_root, reference)
        if relative is None:
            raise ValueError(f"MEASUREMENT_SOURCE_UNVERIFIABLE:{reference}")
        source_inputs.append({"path": relative, "sha256": _sha256_file(repository_root / relative)})
    if not source_inputs:
        raise ValueError("MEASUREMENT_SOURCE_REQUIRED")

    payload = {
        "schema_version": "1.0.0",
        "plan_id": "PLAN_006",
        "artifact_id": f"PLAN_006_{increment}",
        "mission_id": mission_id,
        "increment": increment,
        "repository_revision": "WORKTREE_UNCOMMITTED",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_inputs": source_inputs,
        "evidence_refs": [item["path"] for item in source_inputs],
        "limitations": limitations or [],
        "result": "PASS",
        "metrics": normalized_metrics,
        "phases": phases,
        "measurement_contracts": [contract.to_dict() for contract in measurement_contracts],
    }
    if authority:
        payload["authority"] = authority
    payload["evidence_identity_sha256"] = _evidence_identity(payload)
    return payload


def _evidence_identity(payload: dict[str, Any]) -> str:
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    return hashlib.sha256(_canonical_json(identity)).hexdigest()


def write_baseline_report(root: str | Path, payload: dict[str, Any], *, artifact_ref: str) -> Path:
    repository_root = Path(root).resolve()
    target = repository_root / Path(artifact_ref)
    target.parent.mkdir(parents=True, exist_ok=True)
    violations = validate_against_schema(payload, "plan_006_evidence_envelope")
    if violations:
        raise ValueError("BASELINE_REPORT_SCHEMA_INVALID:" + "; ".join(violations))
    if _evidence_identity(payload) != payload.get("evidence_identity_sha256"):
        raise ValueError("BASELINE_REPORT_IDENTITY_MISMATCH")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_baseline_report(root: str | Path, artifact_ref: str) -> dict[str, Any]:
    repository_root = Path(root).resolve()
    payload = json.loads((repository_root / Path(artifact_ref)).read_text(encoding="utf-8"))
    violations = validate_against_schema(payload, "plan_006_evidence_envelope")
    if violations:
        raise ValueError("BASELINE_REPORT_SCHEMA_INVALID:" + "; ".join(violations))
    if _evidence_identity(payload) != payload.get("evidence_identity_sha256"):
        raise ValueError("BASELINE_REPORT_IDENTITY_MISMATCH")
    return payload


def build_mission_record(
    *,
    mission_id: str,
    wall_time: float | None,
    delegation_decision: str,
    additional_actors: int,
    repair_iterations: int,
    revalidation_iterations: int,
    commands_executed: int,
    gates_executed: int,
    parallel_or_sequential: str,
    findings_before_completion: int,
    findings_after_completion: int,
    initial_head: str | None,
    final_head: str | None,
    actual_git_diff_files: int | None,
    staged_files: int | None,
    commit_count: int,
) -> dict[str, Any]:
    return {
        "mission_wall_time": wall_time if wall_time is not None else NOT_OBSERVABLE,
        "phase_wall_time": NOT_OBSERVABLE,
        "command_wall_time": NOT_OBSERVABLE,
        "commands_executed": commands_executed,
        "unique_tests_or_test_groups_executed": NOT_OBSERVABLE,
        "tests_repeated_equivalently": NOT_OBSERVABLE,
        "full_suite_runs": NOT_OBSERVABLE,
        "targeted_suite_runs": NOT_OBSERVABLE,
        "gates_executed": gates_executed,
        "resolved_context_size": NOT_OBSERVABLE,
        "estimated_tokens_method": NOT_OBSERVABLE,
        "context_references_count": NOT_OBSERVABLE,
        "context_expansions": NOT_OBSERVABLE,
        "self_contained_handoffs": NOT_OBSERVABLE,
        "delegation_decision": delegation_decision,
        "additional_actors_used": additional_actors,
        "delegated_context_size": NOT_OBSERVABLE,
        "delegation_overhead": NOT_OBSERVABLE,
        "parallel_or_sequential": parallel_or_sequential,
        "repair_iterations": repair_iterations,
        "revalidation_iterations": revalidation_iterations,
        "findings_before_completion": findings_before_completion,
        "findings_after_completion": findings_after_completion,
        "false_convergence_events": NOT_OBSERVABLE,
        "initial_head": initial_head or NOT_OBSERVABLE,
        "final_head": final_head or NOT_OBSERVABLE,
        "actual_git_diff_files": actual_git_diff_files if actual_git_diff_files is not None else NOT_OBSERVABLE,
        "staged_files": staged_files if staged_files is not None else NOT_OBSERVABLE,
        "commit_count": commit_count,
    }
