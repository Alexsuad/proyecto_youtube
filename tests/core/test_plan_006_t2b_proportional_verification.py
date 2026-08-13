"""T2-B tests — targeted invalidation + proportional verification (PLAN 006)."""
from __future__ import annotations

from src.core.proportional_verification import (
    DIRECT_IMPACT,
    FULL_REASSESSMENT_REQUIRED,
    NO_MATERIAL_IMPACT,
    PARTIAL_DEPENDENCY_IMPACT,
    STEP_AFFECTED,
    STEP_BROADER,
    STEP_DIRECT,
    STEP_TARGETED,
    build_verification_plan,
    justify_broader_suite,
    normalize_repeated_work,
)


def test_direct_owner_materiality_is_respected():
    plan = build_verification_plan(
        touched_surface="src/core/x.py",
        shared_utility=False,
        schema_consumers=0,
        core_harness_touched=False,
        targeted_covers_consumers=True,
        repair_showed_broad_damage=False,
        closure_needs_distinct_evidence=False,
        owner_materiality=DIRECT_IMPACT,
    )
    assert plan.materiality == DIRECT_IMPACT


def test_fan_in_triggers_broader_suite():
    plan = build_verification_plan(
        touched_surface="schemas/mission_contract.json",
        shared_utility=False,
        schema_consumers=6,
        core_harness_touched=False,
        targeted_covers_consumers=True,
        repair_showed_broad_damage=False,
        closure_needs_distinct_evidence=False,
    )
    steps = [step.step for step in plan.steps]
    assert steps == [STEP_DIRECT, STEP_TARGETED, STEP_AFFECTED, STEP_BROADER, "GIT_DIFF_CHECK"]


def test_core_harness_touch_justifies_broader():
    justified, reasons = justify_broader_suite(
        shared_utility=False,
        schema_consumers=0,
        core_harness_touched=True,
        targeted_covers_consumers=True,
        repair_showed_broad_damage=False,
        closure_needs_distinct_evidence=False,
    )
    assert justified
    assert "MISSION_AUTHORIZATION_COMPLETION_CORE" in reasons


def test_no_fan_in_stays_targeted():
    plan = build_verification_plan(
        touched_surface="src/core/x.py",
        shared_utility=False,
        schema_consumers=0,
        core_harness_touched=False,
        targeted_covers_consumers=True,
        repair_showed_broad_damage=False,
        closure_needs_distinct_evidence=False,
    )
    steps = [step.step for step in plan.steps]
    assert STEP_BROADER not in steps
    assert plan.materiality == PARTIAL_DEPENDENCY_IMPACT


def test_repeated_equivalent_work_detector():
    runs = [
        "tests/core/test_x.py::test_a",
        "tests/core/test_x.py::test_a",
        "tests/core/test_x.py::test_b",
        "tests/core/test_y.py::test_c",
    ]
    result = normalize_repeated_work(runs)
    assert result["total_runs"] == 4
    assert result["unique_material_tests"] == 3
    assert result["repeated_equivalently"] == ["tests/core/test_x.py::test_a"]
    assert result["occurrences"]["tests/core/test_x.py::test_a"] == 2


def test_no_material_impact_when_nothing_touched():
    plan = build_verification_plan(
        touched_surface="",
        shared_utility=False,
        schema_consumers=0,
        core_harness_touched=False,
        targeted_covers_consumers=True,
        repair_showed_broad_damage=False,
        closure_needs_distinct_evidence=False,
    )
    assert plan.materiality == NO_MATERIAL_IMPACT


def test_repair_broad_damage_triggers_broader():
    justified, reasons = justify_broader_suite(
        shared_utility=False,
        schema_consumers=0,
        core_harness_touched=False,
        targeted_covers_consumers=True,
        repair_showed_broad_damage=True,
        closure_needs_distinct_evidence=False,
    )
    assert justified
    assert "REPAIR_SHOWED_BROADER_DAMAGE" in reasons