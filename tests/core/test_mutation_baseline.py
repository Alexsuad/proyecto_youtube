from pathlib import Path

from src.core.mutation_baseline import (
    BASELINE_VALID, EQUIVALENT_MUTANT, INFRASTRUCTURE_ERROR, KILLED, SURVIVED,
    MUTATIONS, _run_probe, build_mutation_report, evaluate_mutation,
)

ROOT = Path(__file__).resolve().parents[2]


def test_base_probe_runs_against_the_isolated_base_module():
    source = (ROOT / "src/core/context_resolution.py").read_text(encoding="utf-8")
    result = _run_probe(source, path_mode="inside", checksum_mode="bad", expected="BLOCKED")
    assert result.status == BASELINE_VALID
    assert result.imported_module and "context_resolution.py" in result.imported_module


def test_real_security_mutation_is_killed_only_after_valid_baseline():
    result = evaluate_mutation(MUTATIONS[0])
    assert result["baseline"]["status"] == BASELINE_VALID
    assert result["status"] == KILLED


def test_undetected_mutation_is_a_survivor_not_a_kill():
    result = evaluate_mutation(MUTATIONS[2])
    assert result["status"] == SURVIVED
    assert result["classification"] == "LOW_VALUE_MUTATION"


def test_equivalent_mutant_is_not_counted_as_a_weakness():
    result = evaluate_mutation(MUTATIONS[3])
    assert result["status"] == EQUIVALENT_MUTANT
    assert result["classification"] == "EQUIVALENT_MUTANT"


def test_infrastructure_failure_is_never_counted_as_killed():
    source = (ROOT / "src/core/context_resolution.py").read_text(encoding="utf-8")
    failed = _run_probe(source, path_mode="inside", checksum_mode="valid", expected="BLOCKED", force_error=True)
    assert failed.status == INFRASTRUCTURE_ERROR
    report = build_mutation_report(ROOT)
    assert all(record["status"] != KILLED for record in report["infrastructure_errors"])


def test_report_counts_are_reproducible_and_derived_from_records():
    first = build_mutation_report(ROOT)
    second = build_mutation_report(ROOT)
    assert [(row["mutant_id"], row["status"], row.get("classification")) for row in first["mutation_records"]] == [(row["mutant_id"], row["status"], row.get("classification")) for row in second["mutation_records"]]
    assert first["mutants_killed"] == sum(row["status"] == KILLED for row in first["mutation_records"])
    assert all(row["status"] != KILLED for row in first["infrastructure_errors"])
