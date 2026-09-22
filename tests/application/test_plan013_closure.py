from __future__ import annotations

import copy
import hashlib
import json

import pytest

from src.application.contracts import HumanInput
from src.application.storage import StorageError, VaultEpisodeStore
from src.core.final_script_review import build_final_script_review
from src.core.editorial_profile_registry import load_active_profile_authority


ACTIVE_PROFILE_CHECKSUM = load_active_profile_authority()["profile_checksum"]


def _closure(episode_id: str) -> dict:
    checksum = "a" * 64
    audit = {
        "episode_id": episode_id, "artifact_id": "SCRIPT-EDITED-1", "script_version": "1.1.0",
        "script_checksum": checksum, "auditor_run_id": "RUN-AUDITOR-1", "independence_result": "PASS",
        "profile_compliance": "PASS", "brief_compliance": "PASS", "packaging_promise_compliance": "PASS",
        "evidence_sufficiency": "PASS", "thesis_quality": "PASS", "viewer_journey": "PASS",
        "opening_quality": "PASS", "progression": "PASS", "coherence": "PASS", "originality": "PASS",
        "source_transformation": "PASS", "voice": "PASS", "orality": "PASS", "closing_quality": "PASS",
        "factual_traceability": "PASS", "decision": "PASS", "correction_route": "NONE",
        "decision_basis": "Evaluacion cualitativa sustentada en el guion y sus artifacts de entrada.",
        "dimension_evidence": {
            field: {"observation": "Fixture cualitativo para validacion de contrato."}
            for field in (
                "profile_compliance", "brief_compliance", "packaging_promise_compliance",
                "evidence_sufficiency", "thesis_quality", "viewer_journey", "opening_quality",
                "progression", "coherence", "originality", "source_transformation", "voice",
                "orality", "closing_quality", "factual_traceability",
            )
        },
    }
    profile = {"profile_id": "mas_alla_del_guion", "profile_version": "1.2.2", "profile_checksum": ACTIVE_PROFILE_CHECKSUM}
    review = build_final_script_review(
        review_id="FSR-1", episode_id=episode_id, artifact_id="SCRIPT-EDITED-1", script_version="1.1.0",
        script_checksum=checksum, profile_reference=profile,
        visible_promise_ref="editorial_script_promise:SP-1@1.0.0", final_audit_ref="final_editorial_audit:A-1@1.1.0",
        final_audit_checksum=hashlib.sha256(json.dumps(audit, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), review_run_id="RUN-YT-REVIEW-1",
        producer_run_id="RUN-WRITING-1", editor_run_id="RUN-EDITOR-1", auditor_run_id="RUN-AUDITOR-1", review_actor_id="YOUTUBE_ADAPTATION_AUDITOR",
        producer_actor_id="WRITING", editor_actor_id="EDITOR", auditor_actor_id="FINAL_EDITORIAL_AUDITOR",
        estimated_minutes=18.0, target_range=(18, 22), created_at="2026-09-01T00:00:00Z",
    )
    return {
        "episode_id": episode_id, "script_artifact_id": "SCRIPT-EDITED-1", "script_version": "1.1.0",
        "script_checksum": checksum, "final_audit": audit, "final_script_review": review,
        "human_approval": {"decision": "APPROVED", "script_version": "1.1.0", "checksum": checksum},
        "closed_at": "2026-09-01T00:00:00Z",
    }


def test_plan013_closure_converges_and_retries_idempotently(tmp_path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    handle = store.create_episode(
        HumanInput.create(mode="tema", content="Tema sintético"),
        handoff={"target_contract": "editorial_intake_handoff"},
        profile={"ACTIVE_PROFILE_ID": "mas_alla_del_guion", "ACTIVE_PROFILE_VERSION": "1.2.2", "profile_checksum": "a" * 64},
        run_id="RUN-PLAN013",
    )
    closure = _closure(handle.episode_id)
    states = {"episode_id": handle.episode_id, "status": "IN_REVIEW"}
    first = store.record_plan013_editorial_closure(handle, closure=closure, workflow_state=states, episode_state=states)
    second = store.record_plan013_editorial_closure(handle, closure=closure, workflow_state=states, episode_state=states)
    assert first == second
    resumed = store.resume(handle.episode_id)
    assert resumed["state"]["status"] == "EDITORIAL_SCRIPT_APPROVED"
    assert resumed["entry"]["application_status"] == "EDITORIAL_SCRIPT_APPROVED"


def test_plan013_closure_rejects_identity_conflict(tmp_path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    handle = store.create_episode(
        HumanInput.create(mode="tema", content="Tema sintético"),
        handoff={"target_contract": "editorial_intake_handoff"},
        profile={"ACTIVE_PROFILE_ID": "mas_alla_del_guion", "ACTIVE_PROFILE_VERSION": "1.2.2", "profile_checksum": "a" * 64},
        run_id="RUN-PLAN013",
    )
    closure = _closure(handle.episode_id)
    closure["final_script_review"] = copy.deepcopy(closure["final_script_review"])
    closure["final_script_review"]["script_checksum"] = "b" * 64
    with pytest.raises(StorageError, match="FINAL_REVIEW"):
        store.record_plan013_editorial_closure(
            handle, closure=closure, workflow_state={}, episode_state={}
        )


def test_plan013_closure_rejects_incomplete_or_non_independent_audit(tmp_path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    handle = store.create_episode(
        HumanInput.create(mode="tema", content="Tema sintético"),
        handoff={"target_contract": "editorial_intake_handoff"},
        profile={"ACTIVE_PROFILE_ID": "mas_alla_del_guion", "ACTIVE_PROFILE_VERSION": "1.2.2", "profile_checksum": "a" * 64},
        run_id="RUN-PLAN013",
    )
    closure = _closure(handle.episode_id)
    del closure["final_audit"]["viewer_journey"]
    with pytest.raises(StorageError, match="FINAL_AUDIT_SCHEMA_INVALID"):
        store.record_plan013_editorial_closure(handle, closure=closure, workflow_state={}, episode_state={})

    closure = _closure(handle.episode_id)
    closure["final_audit"]["independence_result"] = "BLOCKED"
    with pytest.raises(StorageError, match="FINAL_AUDIT_INVALID"):
        store.record_plan013_editorial_closure(handle, closure=closure, workflow_state={}, episode_state={})


def test_plan013_closure_rejects_stale_profile_and_incompatible_youtube_review(tmp_path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    handle = store.create_episode(
        HumanInput.create(mode="tema", content="Tema sintético"),
        handoff={"target_contract": "editorial_intake_handoff"},
        profile={"ACTIVE_PROFILE_ID": "mas_alla_del_guion", "ACTIVE_PROFILE_VERSION": "1.2.2", "profile_checksum": "a" * 64},
        run_id="RUN-PLAN013",
    )
    closure = _closure(handle.episode_id)
    closure["final_script_review"]["profile_reference"]["profile_checksum"] = "b" * 64
    with pytest.raises(StorageError, match="ACTIVE_PROFILE_STALE"):
        store.record_plan013_editorial_closure(handle, closure=closure, workflow_state={}, episode_state={})

    closure = _closure(handle.episode_id)
    closure["final_script_review"]["review_actor_id"] = "EDITOR"
    with pytest.raises(StorageError, match="ACTOR_INDEPENDENCE_INVALID"):
        store.record_plan013_editorial_closure(handle, closure=closure, workflow_state={}, episode_state={})


def test_plan013_new_script_version_persists_invalidation(tmp_path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    handle = store.create_episode(
        HumanInput.create(mode="tema", content="Tema sintético"),
        handoff={"target_contract": "editorial_intake_handoff"},
        profile={"ACTIVE_PROFILE_ID": "mas_alla_del_guion", "ACTIVE_PROFILE_VERSION": "1.2.2", "profile_checksum": "a" * 64},
        run_id="RUN-PLAN013",
    )
    closure = _closure(handle.episode_id)
    store.record_plan013_editorial_closure(handle, closure=closure, workflow_state={}, episode_state={})
    store.register_plan013_script_version(handle, script_artifact_id="SCRIPT-EDITED-2", script_version="2.0.0", script_checksum="d" * 64)
    resumed = store.resume(handle.episode_id)
    assert resumed["state"]["status"] == "IN_REVIEW"
    assert resumed["state"]["approval_status"] == "STALE"
    persisted = json.loads((handle.folder / store.PLAN013_CLOSURE_FILENAME).read_text(encoding="utf-8"))
    assert persisted["status"] == "INVALIDATED"
    assert persisted["invalidation"]["current_identity"]["script_version"] == "2.0.0"
