"""T1 tests — historical completion + owner closure (PLAN 006)."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from src.core.historical_completion import (
    CompletionSnapshot,
    HistoricalCompletionError,
    build_completion_record,
    completion_identity,
    evaluate_current_applicability,
    freeze_completion_snapshot,
    owner_closure,
    verify_active_execution_fail_closed,
    verify_historical_completion,
)
from src.core.mission_authorization import MissionAuthorization, MissionAuthorizationError


def _snapshot(**overrides) -> CompletionSnapshot:
    defaults = dict(
        mission_id="T1_TEST",
        mission_contract_sha256="a" * 64,
        authorization_artifact_sha256="b" * 64,
        authorized_scope_sha256="c" * 64,
        live_state_path="plans/001_CONTROL_OPERATIVO.md",
        live_state_sha256_at_execution="d" * 64,
        authority_ref="config/authority.json",
        authority_sha256="e" * 64,
        repository_revision="WORKTREE_UNCOMMITTED",
        required_test_identities=("test_a",),
        evidence_identities=("ev1",),
        git_binding={"git_head": "abc123"},
        completion_result="PASS",
    )
    defaults.update(overrides)
    return freeze_completion_snapshot(**defaults)


def test_freeze_and_identity_is_deterministic():
    a = _snapshot()
    b = _snapshot()
    assert completion_identity(a) == completion_identity(b)


def test_identity_changes_when_material_evidence_changes():
    a = _snapshot()
    b = _snapshot(evidence_identities=("ev1", "ev2"))
    assert completion_identity(a) != completion_identity(b)


def test_identity_is_frozen_from_historical_data_only():
    a = _snapshot(live_state_sha256_at_execution="d" * 64)
    record = build_completion_record(a)
    assert record["completion_identity_sha256"] == completion_identity(a)
    # The future live state value is not part of the frozen snapshot, so an
    # administrative change after completion does not alter the identity: the
    # identity only depends on the frozen live_state_sha256_at_execution.
    assert completion_identity(_snapshot(live_state_sha256_at_execution="d" * 64)) == completion_identity(a)


def test_verify_historical_completion_pass():
    record = build_completion_record(_snapshot())
    assert verify_historical_completion(record) == []


def test_verify_historical_completion_rejects_functional_claim():
    record = build_completion_record(_snapshot())
    record["functional_approval_claim"] = True
    assert "FUNCTIONAL_APPROVAL_MUST_NOT_BE_CLAIMED" in verify_historical_completion(record)


def test_verify_historical_completion_rejects_identity_tampering():
    record = build_completion_record(_snapshot())
    record["completion_identity_sha256"] = "0" * 64
    assert "COMPLETION_IDENTITY_MISMATCH" in verify_historical_completion(record)


def test_owner_closure_references_identity_without_reexecution():
    record = build_completion_record(_snapshot())
    closure = owner_closure(
        completion_record=record,
        owner_decision="ACCEPTED",
        closure_metadata={"owner": "OWNER", "note": "closed"},
    )
    assert closure["completion_identity_sha256"] == record["completion_identity_sha256"]
    assert closure["re_executes_required_tests"] is False
    assert closure["rebuilds_historical_authorization_against_current_live_state"] is False
    assert closure["functional_approval_claim"] is False


def test_owner_closure_rejects_unverified_completion():
    record = build_completion_record(_snapshot())
    record["completion_identity_sha256"] = "0" * 64
    with pytest.raises(HistoricalCompletionError):
        owner_closure(
            completion_record=record,
            owner_decision="ACCEPTED",
            closure_metadata={"owner": "OWNER"},
        )


def test_owner_closure_rejects_rejected_decision():
    record = build_completion_record(_snapshot())
    with pytest.raises(HistoricalCompletionError):
        owner_closure(
            completion_record=record,
            owner_decision="REJECTED",
            closure_metadata={"owner": "OWNER"},
        )


def test_owner_closure_requires_owner():
    record = build_completion_record(_snapshot())
    with pytest.raises(HistoricalCompletionError):
        owner_closure(
            completion_record=record,
            owner_decision="ACCEPTED",
            closure_metadata={"note": "no owner"},
        )


def test_current_applicability_degrades_when_live_state_changed():
    snapshot = _snapshot(live_state_sha256_at_execution="d" * 64)
    applicability = evaluate_current_applicability(
        snapshot=snapshot,
        current_live_state_sha256="f" * 64,
        material_dependency_hashes={},
    )
    assert applicability.decision == "TARGETED_REVERIFY_REQUIRED"
    assert applicability.applicable is False


def test_current_applicability_reuse_candidate_when_unchanged():
    snapshot = _snapshot(live_state_sha256_at_execution="d" * 64)
    applicability = evaluate_current_applicability(
        snapshot=snapshot,
        current_live_state_sha256="d" * 64,
        material_dependency_hashes={"src/core/x.py": "g" * 64},
    )
    assert applicability.decision == "REUSE_CANDIDATE"
    assert applicability.applicable is True


def _auth(repo: Path, *, live_sha: str) -> MissionAuthorization:
    from src.core.mission_authorization import scope_checksum

    (repo / "plans").mkdir(parents=True, exist_ok=True)
    (repo / "config").mkdir(parents=True, exist_ok=True)
    authority = repo / "config/authority.json"
    authority.write_text(
        json.dumps({"mission_id": "T1_TEST", "authorized_scope_sha256": "c" * 64, "artifact_version": "1.0.0", "decision": "AUTHORIZED"}),
        encoding="utf-8",
    )
    scope = {
        "mission_id": "T1_TEST",
        "capability_ids": ["CAP_T1"],
        "role_ids": ["ROLE_T1"],
        "execution_profile_ids": ["ANY"],
        "execution_interface": "ANY",
        "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": [],
        "allowed_routes": ["ANY"],
        "execution_mode": "SYNTHETIC",
        "live_state_sha256": live_sha,
        "contains_material_repair": False,
        "repair_integrity_evidence_path": "",
    }
    checksum = scope_checksum(scope)
    authority.write_text(
        json.dumps({"mission_id": "T1_TEST", "authorized_scope_sha256": checksum, "artifact_version": "1.0.0", "decision": "AUTHORIZED"}),
        encoding="utf-8",
    )
    return MissionAuthorization(
        mission_id="T1_TEST",
        contract_sha256="a" * 64,
        live_state_path="plans/001_CONTROL_OPERATIVO.md",
        live_state_sha256=live_sha,
        capability_ids=("CAP_T1",),
        role_ids=("ROLE_T1",),
        execution_profile_ids=("ANY",),
        execution_interface="ANY",
        allowed_operations=("EXECUTE_CAPABILITY",),
        allowed_paths=(),
        allowed_routes=("ANY",),
        execution_mode="SYNTHETIC",
        single_use=True,
        authority_ref="config/authority.json",
        authority_sha256=hashlib.sha256(authority.read_bytes()).hexdigest(),
        authorized_scope_sha256=checksum,
        executor_substitution_policy="INLINE",
        contains_material_repair=False,
        repair_integrity_evidence_path="",
        contract_path=None,
    )


def test_active_execution_stays_fail_closed_against_live_state_b(tmp_path):
    repo = tmp_path / "repo"
    (repo / "plans").mkdir(parents=True)
    (repo / "config").mkdir()
    state = repo / "plans/001_CONTROL_OPERATIVO.md"
    state.write_text("state version A", encoding="utf-8")
    # Authorization frozen against live state A.
    auth = _auth(repo, live_sha=hashlib.sha256(b"state version A").hexdigest())
    # Live state changes to B by an administrative action after completion.
    state.write_text("state version B", encoding="utf-8")
    # Active execution must still be blocked (fail-closed).
    with pytest.raises(MissionAuthorizationError):
        verify_active_execution_fail_closed(
            auth,
            repo,
            capability_id="CAP_T1",
            role_id="ROLE_T1",
            operation="EXECUTE_CAPABILITY",
        )


def test_active_execution_succeeds_when_live_state_matches():
    import hashlib

    repo = Path(tempfile.mkdtemp())
    (repo / "plans").mkdir(parents=True)
    (repo / "config").mkdir()
    state = repo / "plans/001_CONTROL_OPERATIVO.md"
    state_bytes = b"state version A"
    state.write_bytes(state_bytes)
    live_sha = hashlib.sha256(state_bytes).hexdigest()
    auth = _auth(repo, live_sha=live_sha)
    verify_active_execution_fail_closed(
        auth,
        repo,
        capability_id="CAP_T1",
        role_id="ROLE_T1",
        operation="EXECUTE_CAPABILITY",
    )