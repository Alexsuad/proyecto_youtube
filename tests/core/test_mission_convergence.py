from src.core.mission_convergence import BLOCKED, CONVERGED, MAX_ITERATIONS_REACHED, run_convergence_loop, required_review_stage


def _result(passed: bool, ref: str) -> dict:
    return {"passed": passed, "evidence": [{"kind": "TEST", "ref": ref}]}


def test_loop_repairs_deterministic_and_adversarial_failures_until_converged():
    calls = {"verify": 0, "adversarial": 0, "repair": 0}

    def verify():
        calls["verify"] += 1
        return _result(calls["verify"] > 1, f"verify-{calls['verify']}")

    def adversarial():
        calls["adversarial"] += 1
        return _result(calls["adversarial"] > 1, f"adversarial-{calls['adversarial']}")

    def repair(_failure):
        calls["repair"] += 1
        return _result(True, f"repair-{calls['repair']}")

    outcome = run_convergence_loop(
        implement=lambda: _result(True, "implementation"), verify=verify,
        adversarial_review=adversarial, repair=repair, max_iterations=3,
        review_policy={"required_review": "SELF_ONLY"},
    )
    assert outcome.status == CONVERGED
    assert outcome.iterations == 3
    assert outcome.review_stage == "SELF_ONLY"
    assert calls["repair"] == 2
    assert {event["stage"] for event in outcome.events} >= {"IMPLEMENT", "VERIFY", "REVERIFY", "SELF_ADVERSARIAL_REVIEW", "REPAIR"}


def test_failed_implementation_never_converges_without_repair_evidence():
    outcome = run_convergence_loop(
        implement=lambda: _result(False, "implement-failed"), verify=lambda: _result(True, "verify"),
        adversarial_review=lambda: _result(True, "review"), repair=lambda _failure: _result(False, "repair-failed"),
        review_policy={"required_review": "SELF_ONLY"},
    )
    assert outcome.status == BLOCKED
    assert outcome.review_stage == "SELF_ONLY"
    assert outcome.events[0]["stage"] == "IMPLEMENT"


def test_failed_implementation_cannot_converge_after_declared_repair():
    outcome = run_convergence_loop(
        implement=lambda: _result(False, "implement-failed"), verify=lambda: _result(True, "verify"),
        adversarial_review=lambda: _result(True, "review"), repair=lambda _failure: _result(True, "repair"),
        review_policy={"required_review": "SELF_ONLY"},
    )
    assert outcome.status == BLOCKED
    assert [event["stage"] for event in outcome.events] == ["IMPLEMENT", "REPAIR"]


def test_boolean_or_evidence_free_pass_cannot_converge_in_governed_mode():
    outcome = run_convergence_loop(
        implement=lambda: _result(True, "implement"), verify=lambda: {"passed": True}, adversarial_review=lambda: _result(True, "review"),
        repair=lambda _failure: _result(True, "repair"), max_iterations=2, review_policy={"required_review": "SELF_ONLY"},
    )
    assert outcome.status == MAX_ITERATIONS_REACHED
    assert any(event["result"].get("reason") in {"STRUCTURED_RESULT_REQUIRED", "EVIDENCE_REQUIRED"} for event in outcome.events)


def test_legacy_boolean_helpers_remain_available_only_when_explicit():
    outcome = run_convergence_loop(
        implement=lambda: True, verify=lambda: True, adversarial_review=lambda: True, repair=lambda _failure: True,
        review_policy={"required_review": "SELF_ONLY"}, governed=False,
    )
    assert outcome.status == CONVERGED


def test_iterations_exhausted_preserves_history_and_escalates_when_required():
    outcome = run_convergence_loop(
        implement=lambda: _result(True, "implement"), verify=lambda: _result(False, "verify"),
        adversarial_review=lambda: _result(True, "review"), repair=lambda _failure: _result(True, "repair"),
        max_iterations=2, review_policy={"required_review": "INDEPENDENT_REVIEW"},
    )
    assert outcome.status == MAX_ITERATIONS_REACHED
    assert outcome.review_stage == "INDEPENDENT_REVIEW"
    assert len(outcome.events) >= 5


def test_sensitive_change_always_escalates_to_independent_review():
    assert required_review_stage({"required_review": "SELF_ONLY"}, sensitive_change=True) == "INDEPENDENT_REVIEW"


def test_reduced_mission_contract_requires_useful_structured_minimum():
    from src.core.mission_completion_gate import MissionContract, MissionContractError
    from src.core.contract_validation import validate_against_schema

    base = {
        "mission_id": "M-REDUCED", "artifact_id": "artifact", "artifact_version": "1.0.0",
        "authorized_paths": ["src/"], "protected_untracked_paths": [], "protected_untracked_baseline": [],
        "required_tests": [], "push_allowed": False,
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "a" * 40},
        "contains_material_repair": False,
        "state_requirements": {"control_path": "control.md", "required": {}, "forbidden": {}}, "schema_checks": [],
        "mission_mode": "REDUCED", "objective": "Objetivo mínimo.", "canonical_inputs": ["plans/001_CONTROL_OPERATIVO.md"],
        "allowed_files": ["src/"], "expected_outputs": ["evidence.json"], "deterministic_validations": ["pytest"],
        "stop_conditions": ["contradiction canonical"], "review_policy": {"required_review": "SELF_ONLY"},
        "owner_closure": {"required": True, "artifact": "control.md"},
    }
    contract = MissionContract.from_dict(base)
    assert contract.mission_mode == "REDUCED"
    assert validate_against_schema(base, "mission_contract") == []
    empty = {**base, "canonical_inputs": []}
    assert validate_against_schema(empty, "mission_contract")
    try:
        MissionContract.from_dict(empty)
    except MissionContractError as exc:
        assert "canonical_inputs" in str(exc)
    else:
        raise AssertionError("empty essential reduced field was accepted")
    legacy = {key: value for key, value in base.items() if key not in {"mission_mode", "objective", "canonical_inputs", "allowed_files", "expected_outputs", "deterministic_validations", "stop_conditions", "review_policy", "owner_closure"}}
    assert MissionContract.from_dict(legacy).mission_mode == "LEGACY"
