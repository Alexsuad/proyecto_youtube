"""T0 tests — baseline + telemetry foundation (PLAN 006)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.core.contract_validation import validate_against_schema
from src.core.lean_measurement import (
    NOT_OBSERVABLE,
    REQUIRED_METRICS,
    build_baseline_report,
    build_measurement_contract,
    build_mission_record,
    load_baseline_report,
    write_baseline_report,
)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "reports/implementation/plan_006").mkdir(parents=True)
    (repo / "plans").mkdir(parents=True)
    (repo / "src/core").mkdir(parents=True)
    (repo / "plans/001_CONTROL_OPERATIVO.md").write_text("state", encoding="utf-8")
    (repo / "src/core/lean_measurement.py").write_text("module", encoding="utf-8")
    return repo


def test_measurement_contract_valid():
    contract = build_measurement_contract(
        metric="full_suite_runs",
        baseline="1",
        comparison_unit="runs_per_mission",
        capture_method="count",
        observability=NOT_OBSERVABLE,
        decision_rule="reduce_repeated_full_suite_runs",
        evidence_reference="reports/implementation/plan_006/T0_BASELINE.json",
    )
    assert contract.to_dict()["metric"] == "full_suite_runs"


def test_measurement_contract_rejects_invalid_observability():
    with pytest.raises(ValueError):
        build_measurement_contract(
            metric="x", baseline="1", comparison_unit="unit", capture_method="m",
            observability="INVENTED", decision_rule="d", evidence_reference="e",
        )


def test_build_baseline_report_has_all_required_metrics(tmp_path):
    repo = _repo(tmp_path)
    source_paths = ["plans/001_CONTROL_OPERATIVO.md", "src/core/lean_measurement.py"]
    record = build_mission_record(
        mission_id="T0_TEST",
        wall_time=None,
        delegation_decision="INLINE",
        additional_actors=0,
        repair_iterations=0,
        revalidation_iterations=0,
        commands_executed=4,
        gates_executed=1,
        parallel_or_sequential="SEQUENTIAL",
        findings_before_completion=0,
        findings_after_completion=0,
        initial_head="abc",
        final_head="abc",
        actual_git_diff_files=0,
        staged_files=0,
        commit_count=0,
    )
    report = build_baseline_report(
        repo,
        mission_id="T0_TEST",
        increment="T0",
        metrics=record,
        phases={},
        measurement_contracts=[],
        source_paths=source_paths,
    )
    assert report["result"] == "PASS"
    assert report["plan_id"] == "PLAN_006"
    assert set(REQUIRED_METRICS).issubset(report["metrics"].keys())
    assert report["metrics"]["mission_wall_time"] == NOT_OBSERVABLE


def test_build_baseline_report_rejects_unknown_metric(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(ValueError):
        build_baseline_report(
            repo,
            mission_id="T0_TEST",
            increment="T0",
            metrics={"not_a_real_metric": 1},
            phases={},
            measurement_contracts=[],
            source_paths=["plans/001_CONTROL_OPERATIVO.md"],
        )


def test_build_baseline_report_rejects_invented_value(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(ValueError):
        build_baseline_report(
            repo,
            mission_id="T0_TEST",
            increment="T0",
            metrics={"commands_executed": "INVENTED_NUMBER"},
            phases={},
            measurement_contracts=[],
            source_paths=["plans/001_CONTROL_OPERATIVO.md"],
        )


def test_write_and_load_baseline_roundtrip(tmp_path):
    repo = _repo(tmp_path)
    record = build_mission_record(
        mission_id="T0_ROUNDTRIP",
        wall_time=None,
        delegation_decision="INLINE",
        additional_actors=0,
        repair_iterations=0,
        revalidation_iterations=0,
        commands_executed=2,
        gates_executed=1,
        parallel_or_sequential="SEQUENTIAL",
        findings_before_completion=0,
        findings_after_completion=0,
        initial_head="h1",
        final_head="h1",
        actual_git_diff_files=1,
        staged_files=0,
        commit_count=0,
    )
    payload = build_baseline_report(
        repo,
        mission_id="T0_ROUNDTRIP",
        increment="T0",
        metrics=record,
        phases={},
        measurement_contracts=[],
        source_paths=["plans/001_CONTROL_OPERATIVO.md"],
    )
    write_baseline_report(repo, payload, artifact_ref="reports/implementation/plan_006/T0_ROUNDTRIP.json")
    loaded = load_baseline_report(repo, "reports/implementation/plan_006/T0_ROUNDTRIP.json")
    assert loaded["mission_id"] == "T0_ROUNDTRIP"
    assert loaded["evidence_identity_sha256"] == payload["evidence_identity_sha256"]


def test_baseline_report_validates_against_schema(tmp_path):
    repo = _repo(tmp_path)
    record = build_mission_record(
        mission_id="T0_SCHEMA",
        wall_time=None,
        delegation_decision="INLINE",
        additional_actors=0,
        repair_iterations=0,
        revalidation_iterations=0,
        commands_executed=2,
        gates_executed=1,
        parallel_or_sequential="SEQUENTIAL",
        findings_before_completion=0,
        findings_after_completion=0,
        initial_head="h",
        final_head="h",
        actual_git_diff_files=0,
        staged_files=0,
        commit_count=0,
    )
    payload = build_baseline_report(
        repo,
        mission_id="T0_SCHEMA",
        increment="T0",
        metrics=record,
        phases={},
        measurement_contracts=[],
        source_paths=["plans/001_CONTROL_OPERATIVO.md"],
    )
    assert validate_against_schema(payload, "plan_006_evidence_envelope") == []