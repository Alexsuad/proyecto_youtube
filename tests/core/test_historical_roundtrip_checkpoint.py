from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ai.providers.agent_handoff import AgentHandoffProvider, canonical_json, checksum
from src.application.topic_belonging import (
    CAPABILITY_ID,
    REVIEWER_ROLE,
    TopicBelongingExecutionError,
    TopicBelongingTechnicalWorkflow,
)


def _checkpoint(tmp_path: Path, *, episode_id: str = "ep_0003") -> tuple[object, Path, Path, dict]:
    episode = tmp_path / "episode"
    results = episode / "roundtrip_results"
    handoff = tmp_path / "handoff"
    results.mkdir(parents=True)
    handoff.mkdir()
    output = {
        "decision": "REQUEST_MORE_EVIDENCE",
        "conditions": [],
        "exclusions": [],
        "risks": [],
        "owner_escalation_required": False,
        "owner_escalation_reason": "",
        "strategic_dimensions_affected": [],
        "temporary_or_permanent_effect": "NONE",
        "precedent_risk": "LOW",
        "evidence": ["historical-checkpoint"],
    }
    package = {
        "handoff_id": "RUN-AI-HISTORICAL-001",
        "capability_id": CAPABILITY_ID,
        "episode_id": episode_id,
        "skill_id": "topic_belonging",
        "skill_version": "1.0.0",
        "input_manifest_checksum": "a" * 64,
        "output_schema": "topic_belonging_cognitive_decision",
        "execution_mode": "REAL",
        "execution_family": "AGENT_HARNESS",
        "execution_route": "agent_harness",
        "stage": "REVIEWER",
        "role": REVIEWER_ROLE,
        "mission_id": "EXTEND_01_M2_REAL_E2E",
    }
    package["package_checksum"] = checksum(canonical_json(package))
    package_path = handoff / "RUN-AI-HISTORICAL-001.json"
    package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
    envelope = {
        "handoff_id": package["handoff_id"],
        "package_checksum": package["package_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"],
        "skill_id": package["skill_id"],
        "skill_version": package["skill_version"],
        "mission_id": package["mission_id"],
        "episode_id": episode_id,
        "capability_id": package["capability_id"],
        "stage": package["stage"],
        "role": package["role"],
        "result_run_id": "RUN-RESULT-HISTORICAL-001",
        "output": output,
        "output_checksum": checksum(canonical_json(output)),
        "provenance": {
            "mission_id": package["mission_id"],
            "episode_id": episode_id,
            "capability_id": package["capability_id"],
            "stage": package["stage"],
            "role": package["role"],
            "run_id": "RUN-RESULT-HISTORICAL-001",
            "executor_identity": "historical-executor",
        },
    }
    result_path = results / "reviewer-RUN-AI-HISTORICAL-001.json"
    result_path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
    materialized_path = results / "reviewer-materialized-historical.json"
    materialized_path.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
    record = {
        **{key: package[key] for key in ("mission_id", "episode_id", "capability_id", "stage", "role", "handoff_id", "package_checksum", "input_manifest_checksum", "skill_id", "skill_version")},
        "result_run_id": envelope["result_run_id"],
        "output_checksum": envelope["output_checksum"],
        "handoff_package_ref": str(package_path),
        "result_path": "roundtrip_results/reviewer-RUN-AI-HISTORICAL-001.json",
        "materialized_output_path": "roundtrip_results/reviewer-materialized-historical.json",
        "materialized_output_checksum": hashlib.sha256(materialized_path.read_bytes()).hexdigest(),
    }
    workflow = object.__new__(TopicBelongingTechnicalWorkflow)
    workflow._mission_id = "PLAN015"
    workflow.boundary = SimpleNamespace(capability_id=CAPABILITY_ID)
    handle = SimpleNamespace(episode_id=episode_id, folder=episode)
    return handle, package_path, result_path, record, workflow


def test_integral_historical_checkpoint_passes_without_reactivating_mission(tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)
    package, envelope, output = workflow._revalidate_roundtrip_record(handle, record)
    assert package["mission_id"] == "EXTEND_01_M2_REAL_E2E"
    assert envelope["mission_id"] == package["mission_id"]
    assert output["decision"] == "REQUEST_MORE_EVIDENCE"


def test_committed_legacy_envelope_without_current_executor_field_still_passes(tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)
    envelope = json.loads(result_path.read_text(encoding="utf-8"))
    envelope["provenance"].pop("executor_identity")
    result_path.write_text(json.dumps(envelope), encoding="utf-8")
    _, _, output = workflow._revalidate_roundtrip_record(handle, record)
    assert output["decision"] == "REQUEST_MORE_EVIDENCE"


def test_historical_checkpoint_package_checksum_tamper_is_blocked(tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["execution_mode"] = "TAMPERED"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PACKAGE_CHECKSUM_INVALID"):
        workflow._revalidate_roundtrip_record(handle, record)


def test_historical_checkpoint_other_episode_is_blocked(tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path, episode_id="ep_other")
    record["episode_id"] = "ep_0003"
    with pytest.raises(TopicBelongingExecutionError, match="EPISODE_BINDING_INVALID"):
        workflow._revalidate_roundtrip_record(handle, record)


def test_historical_checkpoint_without_materialization_evidence_is_blocked(tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)
    record.pop("materialized_output_path")
    with pytest.raises(TopicBelongingExecutionError, match="COMMIT_EVIDENCE_INCOMPLETE"):
        workflow._revalidate_roundtrip_record(handle, record)


def test_historical_authorization_cannot_authorize_new_execution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)
    called = []

    def blocked(*args, **kwargs):
        called.append(True)
        raise PermissionError("historical authorization is not current execution authority")

    monkeypatch.setattr(AgentHandoffProvider, "_verify_import_authorization", staticmethod(blocked))
    with pytest.raises(PermissionError, match="not current execution"):
        AgentHandoffProvider().import_result(package_path, result_path)
    assert called == [True]


def test_historical_result_replay_does_not_use_checkpoint_bypass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)

    def blocked(*args, **kwargs):
        raise PermissionError("replay requires current execution authority")

    monkeypatch.setattr(AgentHandoffProvider, "_verify_import_authorization", staticmethod(blocked))
    with pytest.raises(PermissionError, match="replay requires current"):
        AgentHandoffProvider().import_result(package_path, result_path, historical_checkpoint=False)


def test_new_result_path_still_requires_and_uses_current_authority(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    handle, package_path, result_path, record, workflow = _checkpoint(tmp_path)
    calls = []

    def current_authority(*args, **kwargs):
        calls.append(True)

    monkeypatch.setattr(AgentHandoffProvider, "_verify_import_authorization", staticmethod(current_authority))
    output = AgentHandoffProvider().import_result(package_path, result_path)
    assert output["decision"] == "REQUEST_MORE_EVIDENCE"
    assert calls == [True]
