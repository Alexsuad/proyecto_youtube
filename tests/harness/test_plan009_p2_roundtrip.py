from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.application.contracts import HumanInput
from src.application.service import EpisodeApplicationService
from src.application.storage import VaultEpisodeStore
from src.application.topic_belonging import (
    ExecutionCognitiveBoundary,
    TopicBelongingExecutionError,
    TopicBelongingTechnicalWorkflow,
)
from src.scripts.channel_intelligence import active_profile, canonical_checksum


ROOT = Path(__file__).resolve().parents[2]
AUTH = "plans/plan_009/p2_roundtrip_integration/mission/mission-authorization.json"
CONTRACT = "plans/plan_009/p2_roundtrip_integration/mission/mission_contract.json"
TRIGGER_KEYS = [
    "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change",
    "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change",
    "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory",
]


@pytest.fixture(autouse=True)
def _remove_test_handoffs():
    handoff_dir = ROOT / "handoff"
    before = set(handoff_dir.glob("*.json")) if handoff_dir.is_dir() else set()
    yield
    for path in handoff_dir.glob("*.json") if handoff_dir.is_dir() else ():
        if path not in before:
            path.unlink(missing_ok=True)
    if handoff_dir.is_dir() and not any(handoff_dir.iterdir()):
        handoff_dir.rmdir()


def _topic_input() -> dict:
    profile = active_profile()
    return {
        "topic_input_id": "TBI-P2-FIXTURE",
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        "topic": "T",
        "entry_mode": "TOPIC_FIRST",
        "central_question": "¿Qué revela esta tensión sobre vivir con otros?",
        "proposed_angle": "Observar la tensión sin convertirla en consejo.",
        "proposed_territory": "Individuo e identidad",
        "initial_evidence": ["fixture://p2/initial"],
        "strategic_triggers": {key: False for key in TRIGGER_KEYS},
        "submitted_at": "2026-08-30T10:00:00Z",
    }


def _assessment(topic_input: dict, run_id: str) -> dict:
    profile = active_profile()
    data = {
        "assessment_id": "TBA-P2-FIXTURE",
        "topic_input_id": topic_input["topic_input_id"],
        "producer_actor_id": "actor-p2-producer",
        "producer_role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
        "producer_run_id": run_id,
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        **{key: topic_input[key] for key in ("topic", "central_question", "proposed_angle", "proposed_territory", "initial_evidence", "strategic_triggers", "entry_mode")},
        "sensitive_risks": [], "territory_classification": "ACTIVE", "identity_alignment": "ALIGNED",
        "promise_alignment": "ALIGNED", "risks": [], "recommended_conditions": [],
        "recommended_exclusions": [], "owner_escalation_recommended": False,
        "evidence": ["fixture://p2/assessment"], "status": "CLOSED_FOR_REVIEW", "artifact_checksum": "",
        "provenance": {"actor_id": "actor-p2-producer", "role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "run_id": run_id, "input_checksums": [canonical_checksum(topic_input, "input")], "output_checksum": ""},
    }
    checksum = canonical_checksum(data, "assessment")
    data["artifact_checksum"] = checksum
    data["provenance"]["output_checksum"] = checksum
    return data


def _decision(assessment: dict, run_id: str) -> dict:
    profile = active_profile()
    data = {
        "decision_id": "TBD-P2-FIXTURE", "assessment_id": assessment["assessment_id"],
        "reviewer_run_id": run_id,
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        "producer_artifact_checksum": assessment["artifact_checksum"], "reviewer_actor_id": "actor-p2-reviewer",
        "reviewer_role_id": "CHANNEL_INTELLIGENCE_REVIEWER", "reviewer_input_checksum": assessment["artifact_checksum"],
        "decision": "REQUEST_MORE_EVIDENCE", "conditions": [], "exclusions": [], "risks": [],
        "owner_escalation_required": False, "owner_escalation_reason": "", "strategic_dimensions_affected": [],
        "temporary_or_permanent_effect": "NONE", "precedent_risk": "LOW", "evidence": ["fixture://p2/review"],
        "decided_at": "2026-08-30T10:01:00Z",
        "provenance": {"actor_id": "actor-p2-reviewer", "role_id": "CHANNEL_INTELLIGENCE_REVIEWER", "run_id": run_id, "input_checksum": assessment["artifact_checksum"], "output_checksum": ""},
    }
    data["provenance"]["output_checksum"] = canonical_checksum(data, "decision")
    return data


def _human_input() -> HumanInput:
    return HumanInput.create(
        mode="TOPIC_FIRST",
        content="T",
        initial_question="¿Qué revela esta tensión sobre vivir con otros?",
        context="Fixture técnico; no es un episodio real.",
        channel="TERMINAL",
    )


def _service(tmp_path: Path, vault_root: Path | None = None) -> EpisodeApplicationService:
    vault_root = vault_root or Path(tempfile.mkdtemp(prefix="p2-vault-"))
    store = VaultEpisodeStore(vault_root, "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=AUTH,
        mission_contract_path=CONTRACT,
        execution_mode="REAL",
        execution_family="AGENT_HARNESS",
        handoff_directory=ROOT / "handoff",
    )
    service = EpisodeApplicationService(store, workflow=TopicBelongingTechnicalWorkflow(store, boundary=boundary))
    service._p2_test_vault_root = vault_root
    return service


def _result_for(package_path: Path, output: dict, result_run_id: str, path: Path) -> Path:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    output_checksum = hashlib.sha256(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    payload = {
        "handoff_id": package["handoff_id"], "package_checksum": package["package_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"], "skill_id": package["skill_id"],
        "skill_version": package["skill_version"], "mission_id": package["mission_id"],
        "episode_id": package["episode_id"], "capability_id": package["capability_id"],
        "stage": package["stage"], "role": package["role"], "result_run_id": result_run_id,
        "output": output, "output_checksum": output_checksum,
        "provenance": {"mission_id": package["mission_id"], "episode_id": package["episode_id"], "capability_id": package["capability_id"], "stage": package["stage"], "role": package["role"], "run_id": result_run_id},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _cleanup_handoffs(paths: list[Path], service: EpisodeApplicationService | None = None) -> None:
    for path in paths:
        path.unlink(missing_ok=True)
    handoff_dir = ROOT / "handoff"
    if handoff_dir.is_dir() and not any(handoff_dir.iterdir()):
        handoff_dir.rmdir()
    if service is not None:
        shutil.rmtree(getattr(service, "_p2_test_vault_root", ""), ignore_errors=True)


def _start(tmp_path: Path):
    service = _service(tmp_path)
    result = service.start(_human_input())
    package = Path(json.loads((result.episode.folder / "workflow_state.json").read_text(encoding="utf-8"))["handoff_package_ref"])
    return service, result.episode, package


def test_roundtrip_three_stages_persists_and_stops(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        assert json.loads((episode.folder / "workflow_state.json").read_text()) ["status"] == "PENDING_EXTERNAL_RESULT"

        topic = _topic_input()
        result_path = _result_for(package, topic, "RESULT-ENRICHMENT-P2", tmp_path / "enrichment.json")
        service.import_result(episode.episode_id, result_path)
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)

        assessment = _assessment(topic, "RESULT-PRODUCER-P2")
        result_path = _result_for(package, assessment, "RESULT-PRODUCER-P2", tmp_path / "producer.json")
        service.import_result(episode.episode_id, result_path)
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)

        decision = _decision(assessment, "RESULT-REVIEWER-P2")
        result_path = _result_for(package, decision, "RESULT-REVIEWER-P2", tmp_path / "reviewer.json")
        service.import_result(episode.episode_id, result_path)
        final = service.resume(episode.episode_id)
        assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        assert json.loads((episode.folder / "roundtrip_results.json").read_text())["results"]
        execution = json.loads((episode.folder / "topic_belonging_execution.json").read_text())["executions"]
        assert [item["stage"] for item in execution] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
        assert all(item["execution_family"] == "AGENT_HARNESS" and item["execution_mode"] == "SYNTHETIC" for item in execution)
        results = json.loads((episode.folder / "roundtrip_results.json").read_text())["results"]
        assert len({item["handoff_id"] for item in results}) == 3
        assert [item["stage"] for item in results] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
    finally:
        _cleanup_handoffs(created, service)


def _pending_package(episode):
    workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
    return workflow["stage"], episode, Path(workflow["handoff_package_ref"])


def _finish_roundtrip(service, episode, tmp_path: Path) -> list[Path]:
    created: list[Path] = []
    _, _, package = _pending_package(episode)
    created.append(package)
    topic = _topic_input()
    service.import_result(
        episode.episode_id,
        _result_for(package, topic, "RESULT-FIX-ENRICHMENT", tmp_path / "fix-enrichment.json"),
    )
    service.resume(episode.episode_id)
    _, _, package = _pending_package(episode)
    created.append(package)
    assessment = _assessment(topic, "RESULT-FIX-PRODUCER")
    service.import_result(
        episode.episode_id,
        _result_for(package, assessment, "RESULT-FIX-PRODUCER", tmp_path / "fix-producer.json"),
    )
    service.resume(episode.episode_id)
    _, _, package = _pending_package(episode)
    created.append(package)
    decision = _decision(assessment, "RESULT-FIX-REVIEWER")
    service.import_result(
        episode.episode_id,
        _result_for(package, decision, "RESULT-FIX-REVIEWER", tmp_path / "fix-reviewer.json"),
    )
    service.resume(episode.episode_id)
    return created


def test_roundtrip_duplicate_import_is_idempotent(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _topic_input(), "RESULT-DUPLICATE-P2", tmp_path / "duplicate.json")
        service.import_result(episode.episode_id, result_path)
        count_before = len(json.loads((episode.folder / "roundtrip_results.json").read_text())["results"])
        service.import_result(episode.episode_id, result_path)
        count_after = len(json.loads((episode.folder / "roundtrip_results.json").read_text())["results"])
        assert count_before == count_after == 1
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_without_provenance_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _topic_input(), "RESULT-DUPLICATE-MISSING-PROVENANCE", tmp_path / "duplicate-missing-provenance.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered.pop("provenance")
        altered_path = tmp_path / "duplicate-missing-provenance-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_BLOCKED"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_with_provenance_run_mismatch_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _topic_input(), "RESULT-DUPLICATE-PROVENANCE-RUN", tmp_path / "duplicate-provenance-run.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered["provenance"]["run_id"] = "RESULT-DUPLICATE-PROVENANCE-RUN-OTHER"
        altered_path = tmp_path / "duplicate-provenance-run-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_BLOCKED"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_with_changed_result_run_id_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _topic_input(), "RESULT-DUPLICATE-RUN", tmp_path / "duplicate-run.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered["result_run_id"] = "RESULT-DUPLICATE-RUN-ALTERED"
        altered["provenance"]["run_id"] = altered["result_run_id"]
        altered_path = tmp_path / "duplicate-run-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_CONFLICT"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_with_changed_mission_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _topic_input(), "RESULT-DUPLICATE-MISSION", tmp_path / "duplicate-mission.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered["mission_id"] = "OTHER-MISSION"
        altered["provenance"]["mission_id"] = "OTHER-MISSION"
        altered_path = tmp_path / "duplicate-mission-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_CONFLICT"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_conflicting_duplicate_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _topic_input(), "RESULT-CONFLICT-P2", tmp_path / "original.json")
        service.import_result(episode.episode_id, original)
        conflicting = json.loads(original.read_text(encoding="utf-8"))
        conflicting["output"]["topic"] = "conflicto"
        conflicting["output_checksum"] = "0" * 64
        conflict_path = tmp_path / "conflict.json"
        conflict_path.write_text(json.dumps(conflicting), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="CONFLICT"):
            service.import_result(episode.episode_id, conflict_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_returns_stop_without_new_effects(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        before_results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
        before_handoffs = sorted(path.name for path in (ROOT / "handoff").glob("*.json"))
        first = service.resume(episode.episode_id)
        second = service.resume(episode.episode_id)
        after_results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
        after_handoffs = sorted(path.name for path in (ROOT / "handoff").glob("*.json"))
        assert first["state"]["status"] == second["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        assert before_results == after_results
        assert before_handoffs == after_handoffs
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_deleted_envelope(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        reviewer = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][2]
        (episode.folder / reviewer["result_path"]).unlink()
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED_ENVELOPE_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_tampered_envelope(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        reviewer = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][2]
        result_path = episode.folder / reviewer["result_path"]
        envelope = json.loads(result_path.read_text(encoding="utf-8"))
        envelope["output"]["decision"] = "APPROVE"
        result_path.write_text(json.dumps(envelope), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED_ENVELOPE_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_tampered_result_index(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        results_path = episode.folder / "roundtrip_results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        results["results"][1]["role"] = "CHANNEL_INTELLIGENCE_REVIEWER"
        results_path.write_text(json.dumps(results), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_tampered_execution_evidence(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        execution_path = episode.folder / "topic_belonging_execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["executions"][2]["artifact_checksum"] = "0" * 64
        execution_path.write_text(json.dumps(execution), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_import_rejects_wrong_stage_binding(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _topic_input(), "RESULT-WRONG-STAGE-P2", tmp_path / "wrong.json")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["stage"] = "REVIEWER"
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_valid_result_with_wrong_persisted_checkpoint_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        workflow_path = episode.folder / "workflow_state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["handoff_id"] = "HANDOFF-WRONG-CHECKPOINT"
        workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
        result_path = _result_for(package, _topic_input(), "RESULT-WRONG-CHECKPOINT-P2", tmp_path / "wrong-checkpoint.json")
        with pytest.raises(TopicBelongingExecutionError, match="CHECKPOINT_BINDING"):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_result_run_id_mismatch_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        topic = _topic_input()
        service.import_result(episode.episode_id, _result_for(package, topic, "RESULT-ENRICHMENT-RUN", tmp_path / "enrichment.json"))
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)
        assessment = _assessment(topic, "RESULT-PRODUCER-DECLARED")
        result_path = _result_for(package, assessment, "RESULT-PRODUCER-ACTUAL", tmp_path / "producer.json")
        with pytest.raises(TopicBelongingExecutionError, match="PRODUCER_RESULT_RUN_BINDING_INVALID"):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_new_service_revalidates_tampered_persisted_envelope(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    restarted = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _topic_input(), "RESULT-RESTART-P2", tmp_path / "restart.json")
        service.import_result(episode.episode_id, result_path)
        persisted = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][0]
        stored_result = episode.folder / persisted["result_path"]
        envelope = json.loads(stored_result.read_text(encoding="utf-8"))
        envelope["output"]["topic"] = "altered-after-import"
        stored_result.write_text(json.dumps(envelope), encoding="utf-8")
        restarted = _service(tmp_path, getattr(service, "_p2_test_vault_root"))
        with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_ENVELOPE"):
            restarted.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, restarted or service)


def test_roundtrip_new_service_continues_from_persisted_checkpoint(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    restarted = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _topic_input(), "RESULT-RESTART-CONTINUE", tmp_path / "restart-continue.json"))
        restarted = _service(tmp_path, getattr(service, "_p2_test_vault_root"))
        resumed = restarted.resume(episode.episode_id)
        assert resumed["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow["stage"] == "PRODUCER"
        created.append(Path(workflow["handoff_package_ref"]))
    finally:
        _cleanup_handoffs(created, restarted or service)


def test_roundtrip_resume_rejects_incompatible_next_stage(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _topic_input(), "RESULT-BAD-NEXT-STAGE", tmp_path / "bad-next-stage.json"))
        workflow_path = episode.folder / "workflow_state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["next_stage"] = "UNKNOWN"
        workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="NEXT_STAGE_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_resume_is_idempotent_while_next_handoff_is_pending(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _topic_input(), "RESULT-RESUME-IDEMPOTENT", tmp_path / "resume.json"))
        first = service.resume(episode.episode_id)
        first_package = first["state"].get("handoff_package_ref")
        second = service.resume(episode.episode_id)
        assert second["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        assert second["state"].get("handoff_package_ref") == first_package
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_handoff_has_no_completion_gate_or_model_selection(tmp_path: Path) -> None:
    created: list[Path] = []
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        data = json.loads(package.read_text(encoding="utf-8"))
        assert "completion_gate" not in data
        assert data["execution_family"] == "AGENT_HARNESS"
        assert data["execution_route"] == "agent_harness"
        assert data["model_override"] is None
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_convergence_callbacks_fail_closed_for_invalid_boundary() -> None:
    callbacks = TopicBelongingTechnicalWorkflow._convergence_callbacks(
        "roundtrip:test:invalid",
        stage="unknown",
        output_schema="unknown",
        inputs=[],
        mock_output={"fixture": True},
    )
    assert callbacks["implement"]()["passed"] is False
    assert callbacks["verify"]()["passed"] is False
    assert callbacks["adversarial_review"]()["passed"] is False
    assert callbacks["repair"]({"stage": "unknown"})["passed"] is False
