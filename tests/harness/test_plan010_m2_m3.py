from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path

import pytest

import src.application.topic_belonging as topic_belonging
import src.application.storage as storage_module
import src.ai.role_execution as role_execution
from src.application.contracts import HumanInput
from src.application.handoff import build_editorial_handoff
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError, VaultEpisodeStore
from src.application.topic_belonging import TopicBelongingExecutionError
from src.core.editorial_profile_registry import load_active_profile_authority
from src.scripts.channel_intelligence import active_profile
import src.cli as cli
from tests.harness.test_plan009_m1_vertical import (
    ExecutionCognitiveBoundary,
    TopicBelongingTechnicalWorkflow,
    _assessment as _m1_assessment,
    _decision as _m1_decision,
    _input as _m1_topic_input,
    _mission_authorization as _m1_mission_authorization,
    _outputs as _m1_outputs,
    _service as _m1_service,
)


ROOT = Path(__file__).resolve().parents[2]


def _human_input() -> HumanInput:
    return HumanInput.create(
        mode="tema",
        content="Tema administrativo de prueba",
        initial_question="¿Qué demuestra la prueba?",
        context="Fixture técnico; no es un episodio real.",
        channel="TERMINAL",
    )


def _profile() -> dict:
    return load_active_profile_authority()


def _handoff(human_input: HumanInput) -> dict:
    return build_editorial_handoff(human_input, _profile())


def _synthetic_mission_setup(tmp_path: Path, label: str, mission_id: str) -> tuple[str, str, Path]:
    live_state_path = f".runtime-tmp/plan010-m2-m3/{tmp_path.name}-{label}-live.md"
    live_state = ROOT / live_state_path
    live_state.parent.mkdir(parents=True, exist_ok=True)
    live_control = (ROOT / "plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8")
    current_line = next(line for line in live_control.splitlines() if line.startswith("CURRENT_MISSION:"))
    live_state.write_text(live_control.replace(current_line, f"CURRENT_MISSION: {mission_id}"), encoding="utf-8")
    authorization = _m1_mission_authorization(
        tmp_path / f"authorization-{label}",
        execution_interface="TOPIC_BELONGING_TEST",
        mission_id=mission_id,
        live_state_path=live_state_path,
    )
    return authorization, live_state_path, live_state


def _cleanup_synthetic_mission(authorization: str, live_state: Path) -> None:
    shutil.rmtree(ROOT / Path(authorization).parent, ignore_errors=True)
    live_state.unlink(missing_ok=True)


def _legacy_service(tmp_path: Path) -> tuple[VaultEpisodeStore, EpisodeApplicationService]:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    store.channel_path.mkdir(parents=True)
    return store, EpisodeApplicationService(store)


def test_m2_closes_only_irrecoverable_legacy_episode_and_unblocks_new_start(tmp_path: Path) -> None:
    store, service = _legacy_service(tmp_path)
    legacy = store.create_legacy_episode(episode_number=1, slug="legacy-interrumpido")
    origin_before = (legacy.folder / "episode_origin.json").read_bytes()

    closure = service.administratively_close_irrecoverable_episode(
        legacy.episode_id,
        reason="La inicialización legacy no dejó input recuperable.",
        actor="owner-recovery-test",
    )

    assert closure["operation"] == "ADMINISTRATIVE_RECOVERY_CLOSE"
    assert closure["source"] == "APPLICATION_ADMINISTRATIVE_RECOVERY"
    assert "PLAN010" not in closure["source"]
    assert closure["irrecoverability"]["basis"] == "REQUIRED_ARTIFACT_MISSING"
    assert legacy.folder.is_dir()
    assert (legacy.folder / "episode_state.json").is_file()
    assert (legacy.folder / "administrative_recovery.json").is_file()
    assert (legacy.folder / "episode_origin.json").read_bytes() == origin_before

    index = json.loads(store.index_path.read_text(encoding="utf-8"))
    entry = next(item for item in index["episodes"] if item["ep_id"] == legacy.episode_id)
    assert entry["estado"] == store.ADMINISTRATIVE_CLOSED_INDEX_STATUS
    assert entry["application_status"] == store.ADMINISTRATIVE_CLOSED_STATE

    new_episode = store.create_episode(
        _human_input(),
        handoff=_handoff(_human_input()),
        profile=_profile(),
        run_id="RUN-M2-NEW-EPISODE",
        episode_number=2,
        slug_override="m2-new",
    )
    assert new_episode.episode_id == "ep_0002"

    assert service.administratively_close_irrecoverable_episode(
        legacy.episode_id,
        reason="different text is ignored by idempotent replay",
        actor="another-actor",
    ) == closure


def test_m2_refuses_a_healthy_topic_belonging_stop(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    episode = store.create_episode(
        _human_input(),
        handoff=_handoff(_human_input()),
        profile=_profile(),
        run_id="RUN-M2-HEALTHY",
        slug_override="m2-healthy",
    )
    store.record_workflow(episode, {"status": "TOPIC_BELONGING_TECHNICAL_STOP"})

    with pytest.raises(StorageError, match="EPISODE_RECOVERABLE_TECHNICAL_STOP"):
        store.administratively_close_irrecoverable_episode(
            episode.episode_id,
            reason="must not close healthy stop",
            actor="owner-recovery-test",
        )

    current = store.resume(episode.episode_id)
    assert current["entry"]["estado"] == "en_progreso"
    assert not (episode.folder / "administrative_recovery.json").exists()


def test_m2_retries_after_interruption_using_the_index_recovery_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, service = _legacy_service(tmp_path)
    legacy = store.create_legacy_episode(episode_number=1, slug="legacy-journal")
    original_write = storage_module._write_json_atomic
    failed = False

    def fail_once(path: Path, payload: dict) -> None:
        nonlocal failed
        if path.name == store.ADMINISTRATIVE_CLOSURE_FILENAME and not failed:
            failed = True
            raise OSError("simulated interruption after index journal")
        original_write(path, payload)

    monkeypatch.setattr(storage_module, "_write_json_atomic", fail_once)
    with pytest.raises(OSError, match="simulated interruption"):
        service.administratively_close_irrecoverable_episode(
            legacy.episode_id,
            reason="journal retry fixture",
            actor="owner-recovery-test",
        )

    monkeypatch.setattr(storage_module, "_write_json_atomic", original_write)
    closure = service.administratively_close_irrecoverable_episode(
        legacy.episode_id,
        reason="ignored after journal commit",
        actor="another-actor",
    )
    assert closure["reason"] == "journal retry fixture"
    assert (legacy.folder / store.ADMINISTRATIVE_CLOSURE_FILENAME).is_file()
    assert json.loads((legacy.folder / "episode_state.json").read_text(encoding="utf-8"))["status"] == store.ADMINISTRATIVE_CLOSED_STATE


def test_m2_rejects_an_index_targeting_the_vault_root(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    store.episodes_path.mkdir(parents=True)
    store.index_path.parent.mkdir(parents=True, exist_ok=True)
    store.index_path.write_text(
        json.dumps(
            {
                "episodes": [
                    {
                        "ep_id": "ep_0001",
                        "ep_folder": ".",
                        "ep_path": str(store.episodes_path),
                        "estado": "en_progreso",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(StorageError, match="EPISODE_PATH_NOT_EPISODE"):
        store.administratively_close_irrecoverable_episode(
            "ep_0001",
            reason="malformed index fixture",
            actor="owner-recovery-test",
        )


def test_m2_rejects_an_index_path_escaping_the_episode_root(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    store.episodes_path.mkdir(parents=True)
    store.index_path.parent.mkdir(parents=True, exist_ok=True)
    store.index_path.write_text(
        json.dumps({"episodes": [{"ep_id": "ep_0001", "ep_folder": "..", "estado": "en_progreso"}]}),
        encoding="utf-8",
    )
    with pytest.raises(StorageError, match="EPISODE_PATH_OUTSIDE_VAULT"):
        store.administratively_close_irrecoverable_episode(
            "ep_0001",
            reason="path traversal fixture",
            actor="owner-recovery-test",
        )


def test_m2_cli_uses_the_same_administrative_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    store, service = _legacy_service(tmp_path)
    legacy = store.create_legacy_episode(episode_number=1, slug="legacy-cli")
    monkeypatch.setattr(cli, "_service", lambda settings, **kwargs: service)

    assert cli.main(
        [
            "cerrar-administrativamente",
            legacy.episode_id,
            "--motivo",
            "fixture irrecuperable",
            "--actor",
            "owner-recovery-test",
        ]
    ) == 0
    assert "Recovery administrativo registrado" in capsys.readouterr().out


def test_m3_materializes_non_empty_canonical_prompt_at_cognitive_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = active_profile()
    human_input = _human_input()
    handoff = _handoff(human_input)
    topic_input = _m1_topic_input()
    assessment = _m1_assessment(topic_input)
    decision = _m1_decision(assessment)
    outputs = {"enrich": topic_input, "produce": assessment, "review": decision}
    captured = []
    original_execute = topic_belonging.execute

    def spy(request):
        captured.append(request)
        return original_execute(request)

    monkeypatch.setattr(topic_belonging, "execute", spy)
    mission_auth = _m1_mission_authorization(tmp_path, execution_interface="TOPIC_BELONGING_TEST")
    try:
        boundary = topic_belonging.ExecutionCognitiveBoundary(
            repository_root=ROOT,
            mission_authorization_path=mission_auth,
            execution_mode="SYNTHETIC_TEST",
            execution_interface="TOPIC_BELONGING_TEST",
            mock_outputs=outputs,
        )

        _, enrichment_result = boundary.enrich(handoff, human_input, profile, "ep_m3")
        assessment, producer_result = boundary.produce(
            topic_input,
            profile,
            "ep_m3",
            input_producer_run_id=enrichment_result.run_id,
        )
        boundary.review(
            topic_input,
            assessment,
            profile,
            "ep_m3",
            input_producer_run_id=enrichment_result.run_id,
        )
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)

    assert len(captured) == 3
    assert [request.config["prompt_id"] for request in captured] == [
        "prompt_channel_intelligence_producer",
        "prompt_channel_intelligence_producer",
        "prompt_channel_intelligence_reviewer",
    ]
    for request in captured:
        assert request.config["prompt"].strip()
        assert request.config["prompt_version"] == "1.0.0"
        assert len(request.config["prompt_checksum"]) == 64
        assert len(request.config["prompt_input_checksum"]) == 64
        assert request.input_artifacts
        assert '"compiled_editorial_profile"' in request.config["prompt"]
        assert '"applicable_policies"' in request.config["prompt"]
        assert '"output_contract"' in request.config["prompt"]


def test_m3_blocks_tampered_compiled_profile_checksum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "compiled.json").write_text(
        json.dumps({"checksum": "wrong", "profile": {}}),
        encoding="utf-8",
    )
    (tmp_path / "config" / "active_editorial_profile.json").write_text(
        json.dumps({"profile_checksum": "expected"}),
        encoding="utf-8",
    )
    (tmp_path / "config" / "editorial_profile_registry.json").write_text(
        json.dumps({"active_profile_key": "profile@1.0.0", "profiles": {"profile@1.0.0": {"compiled_profile_path": "compiled.json"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(role_execution, "ROOT", tmp_path)
    monkeypatch.setattr(role_execution, "load_active_profile_authority", lambda: {})
    with pytest.raises(role_execution.RoleExecutionContractError, match="checksum mismatch"):
        role_execution._active_compiled_profile()


def test_m3_blocks_missing_required_prompt_context() -> None:
    with pytest.raises(role_execution.RoleExecutionContractError, match="required context missing"):
        role_execution._applicable_policies({"required_context": ["policies/does-not-exist.md"]})


def test_t1_modern_episode_binds_state_index_and_lineage_to_mission_a(tmp_path: Path) -> None:
    mission_a = "SYNTHETIC_MISSION_A"
    authorization, authority_path, live_state = _synthetic_mission_setup(tmp_path, "a", mission_a)
    try:
        service = _m1_service(tmp_path, authorization, _m1_outputs(), operational_authority_path=authority_path)
        result = service.start(_m1_human_input())
        state = json.loads((result.episode.folder / "episode_state.json").read_text(encoding="utf-8"))
        index = json.loads(result.episode.index_path.read_text(encoding="utf-8"))
        index_entry = next(item for item in index["episodes"] if item["ep_id"] == result.episode.episode_id)
        lineage = json.loads((result.episode.folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
        assert state["mission_id"] == index_entry["mission_id"] == lineage["mission_id"] == mission_a
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_t2_historical_provenance_survives_resume_under_mission_b(tmp_path: Path) -> None:
    mission_a = "SYNTHETIC_MISSION_A"
    mission_b = "SYNTHETIC_MISSION_B"
    authorization_a, authority_a, live_a = _synthetic_mission_setup(tmp_path, "a", mission_a)
    authorization_b, authority_b, live_b = _synthetic_mission_setup(tmp_path, "b", mission_b)
    try:
        service_a = _m1_service(tmp_path, authorization_a, _m1_outputs(), operational_authority_path=authority_a)
        result = service_a.start(_m1_human_input())
        historical_bytes = {
            "state": (result.episode.folder / "episode_state.json").read_bytes(),
            "index": result.episode.index_path.read_bytes(),
            "lineage": (result.episode.folder / "topic_belonging_lineage.json").read_bytes(),
        }
        service_b = _m1_service(tmp_path, authorization_b, _m1_outputs(), operational_authority_path=authority_b)
        resumed = service_b.resume(result.episode.episode_id)
        assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        assert (result.episode.folder / "episode_state.json").read_bytes() == historical_bytes["state"]
        assert result.episode.index_path.read_bytes() == historical_bytes["index"]
        assert (result.episode.folder / "topic_belonging_lineage.json").read_bytes() == historical_bytes["lineage"]
        state = json.loads((result.episode.folder / "episode_state.json").read_text(encoding="utf-8"))
        index = json.loads(result.episode.index_path.read_text(encoding="utf-8"))
        index_entry = next(item for item in index["episodes"] if item["ep_id"] == result.episode.episode_id)
        lineage = json.loads((result.episode.folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
        assert state["mission_id"] == index_entry["mission_id"] == lineage["mission_id"] == mission_a
    finally:
        _cleanup_synthetic_mission(authorization_a, live_a)
        _cleanup_synthetic_mission(authorization_b, live_b)


def _modern_episode_for_integrity_test(tmp_path: Path) -> tuple[EpisodeApplicationService, object, str, Path]:
    mission_a = "SYNTHETIC_MISSION_A"
    authorization, authority_path, live_state = _synthetic_mission_setup(tmp_path, "integrity", mission_a)
    service = _m1_service(tmp_path, authorization, _m1_outputs(), operational_authority_path=authority_path)
    result = service.start(_m1_human_input())
    return service, result.episode, authorization, live_state


def test_t3_state_index_inconsistency_rejects_persisted_vertical(tmp_path: Path) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        index = json.loads(episode.index_path.read_text(encoding="utf-8"))
        next(item for item in index["episodes"] if item["ep_id"] == episode.episode_id)["mission_id"] = "SYNTHETIC_MISSION_B"
        episode.index_path.write_text(json.dumps(index), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="MODERN_MISSION_BINDING_MISMATCH"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_t4_lineage_manipulation_rejects_persisted_vertical(tmp_path: Path) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        lineage_path = episode.folder / "topic_belonging_lineage.json"
        lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
        lineage["mission_id"] = "SYNTHETIC_MISSION_B"
        lineage_path.write_text(json.dumps(lineage), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="MODERN_MISSION_BINDING_MISMATCH"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_coordinated_modern_to_legacy_metadata_downgrade_rejects(tmp_path: Path) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        state_path = episode.folder / "episode_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.pop("mission_id", None)
        state["status"] = "LEGACY_TECHNICAL_INITIALIZATION"
        state["provenance"] = {"source": "LEGACY_SCRIPT", "semantic_input": False}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        index = json.loads(episode.index_path.read_text(encoding="utf-8"))
        entry = next(item for item in index["episodes"] if item["ep_id"] == episode.episode_id)
        entry.pop("mission_id", None)
        entry.update({
            "application_status": "LEGACY_TECHNICAL_INITIALIZATION",
            "input_origin": "LEGACY_SCRIPT_TECHNICAL",
        })
        episode.index_path.write_text(json.dumps(index), encoding="utf-8")
        lineage_path = episode.folder / "topic_belonging_lineage.json"
        lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
        lineage["mission_id"] = "PLAN010_M1_TOPIC_BELONGING_INTEGRATION_CLOSURE"
        lineage_path.write_text(json.dumps(lineage), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="EPISODE_ORIGIN_BINDING_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


@pytest.mark.parametrize("tamper", ["delete", "modify"])
def test_episode_origin_tamper_rejects_persisted_vertical(tmp_path: Path, tamper: str) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        origin_path = episode.folder / "episode_origin.json"
        if tamper == "delete":
            origin_path.unlink()
        else:
            origin = json.loads(origin_path.read_text(encoding="utf-8"))
            origin["origin"] = "LEGACY_M1"
            origin_path.write_text(json.dumps(origin), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="EPISODE_ORIGIN_BINDING"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_malformed_episode_origin_rejects_without_uncaught_type_error(tmp_path: Path) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        (episode.folder / "episode_origin.json").write_text(json.dumps(["malformed"]), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="EPISODE_ORIGIN_SCHEMA_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_unknown_origin_kind_rejects_incomplete_recovery_with_recomputed_checksum(tmp_path: Path) -> None:
    mission_auth = _m1_mission_authorization(tmp_path, execution_interface="TOPIC_BELONGING_TEST")
    service = _m1_service(tmp_path, mission_auth, _m1_outputs(invalid_stage="produce"))
    try:
        with pytest.raises(TopicBelongingExecutionError):
            service.start(_m1_human_input())
        episode = next(service.store.episodes_path.iterdir())
        origin_path = episode / "episode_origin.json"
        origin = json.loads(origin_path.read_text(encoding="utf-8"))
        origin["origin"] = "UNKNOWN_ORIGIN"
        payload = {
            "episode_id": origin["episode_id"],
            "origin": origin["origin"],
            "state_anchor_sha256": origin["state_anchor_sha256"],
            "index_anchor_sha256": origin["index_anchor_sha256"],
        }
        origin["origin_checksum"] = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        origin_path.write_text(json.dumps(origin), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="EPISODE_ORIGIN_KIND_INVALID"):
            service.resume("ep_0001")
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


@pytest.mark.parametrize("binding_file", ["state", "index", "lineage"])
def test_t5_missing_modern_mission_binding_rejects_instead_of_becoming_legacy(
    tmp_path: Path, binding_file: str
) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        if binding_file == "state":
            path = episode.folder / "episode_state.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload.pop("mission_id", None)
        else:
            if binding_file == "index":
                path = episode.index_path
                payload = json.loads(path.read_text(encoding="utf-8"))
                next(item for item in payload["episodes"] if item["ep_id"] == episode.episode_id).pop("mission_id", None)
            else:
                path = episode.folder / "topic_belonging_lineage.json"
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload.pop("mission_id", None)
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="MODERN_MISSION_BINDING_MISSING"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_t5_both_modern_mission_bindings_missing_rejects_before_resume(tmp_path: Path) -> None:
    service, episode, authorization, live_state = _modern_episode_for_integrity_test(tmp_path)
    try:
        state_path = episode.folder / "episode_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.pop("mission_id", None)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        index = json.loads(episode.index_path.read_text(encoding="utf-8"))
        next(item for item in index["episodes"] if item["ep_id"] == episode.episode_id).pop("mission_id", None)
        episode.index_path.write_text(json.dumps(index), encoding="utf-8")
        (episode.folder / "05_topic_belonging_gate.json").unlink()
        (episode.folder / "workflow_state.json").unlink()
        with pytest.raises(TopicBelongingExecutionError, match="EPISODE_ORIGIN_BINDING_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_synthetic_mission(authorization, live_state)


def test_t2_incomplete_modern_episode_does_not_reexecute_under_mission_b(tmp_path: Path) -> None:
    mission_a = "SYNTHETIC_MISSION_A"
    mission_b = "SYNTHETIC_MISSION_B"
    authorization_a, authority_a, live_a = _synthetic_mission_setup(tmp_path, "incomplete-a", mission_a)
    authorization_b, authority_b, live_b = _synthetic_mission_setup(tmp_path, "incomplete-b", mission_b)
    try:
        service_a = _m1_service(
            tmp_path,
            authorization_a,
            _m1_outputs(invalid_stage="produce"),
            operational_authority_path=authority_a,
        )
        with pytest.raises(TopicBelongingExecutionError):
            service_a.start(_m1_human_input())
        assert not (next(service_a.store.episodes_path.iterdir()) / "topic_belonging_lineage.json").exists()
        service_b = _m1_service(tmp_path, authorization_b, _m1_outputs(), operational_authority_path=authority_b)
        with pytest.raises(TopicBelongingExecutionError, match="HISTORICAL_INCOMPLETE_REQUIRES_SAME_MISSION"):
            service_b.resume("ep_0001")
        partial_folder = next(service_a.store.episodes_path.iterdir())
        before = {
            path.name: path.read_bytes()
            for path in [*partial_folder.iterdir(), service_a.store.index_path]
            if path.is_file()
        }
        with pytest.raises(TopicBelongingExecutionError, match="HISTORICAL_INCOMPLETE_REQUIRES_SAME_MISSION"):
            service_b.resume("ep_0001")
        after = {
            path.name: path.read_bytes()
            for path in [*partial_folder.iterdir(), service_a.store.index_path]
            if path.is_file()
        }
        assert after == before
    finally:
        _cleanup_synthetic_mission(authorization_a, live_a)
        _cleanup_synthetic_mission(authorization_b, live_b)


def test_new_execution_accepts_authorization_matching_live_current_mission(tmp_path: Path) -> None:
    mission_auth = _m1_mission_authorization(tmp_path, execution_interface="TOPIC_BELONGING_TEST")
    try:
        authorization = json.loads((ROOT / mission_auth).read_text(encoding="utf-8"))
        authorized_mission_id = authorization["mission_id"]
        live_control = (ROOT / "plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8")
        live_mission_id = next(
            line.split(":", 1)[1].strip()
            for line in live_control.splitlines()
            if line.startswith("CURRENT_MISSION:")
        )
        assert authorized_mission_id == live_mission_id
        service = _m1_service(tmp_path, mission_auth, _m1_outputs())
        result = service.start(_m1_human_input())
        lineage = json.loads((result.episode.folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
        assert lineage["mission_id"] == authorized_mission_id
        state = json.loads((result.episode.folder / "episode_state.json").read_text(encoding="utf-8"))
        assert state["mission_id"] == lineage["mission_id"]
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


def test_new_execution_rejects_none_as_inactive_current_mission(tmp_path: Path) -> None:
    mission_auth, _, live_state = _synthetic_mission_setup(tmp_path, "none-current-mission", "NONE")
    try:
        service = _m1_service(tmp_path, mission_auth, _m1_outputs())
        assert not service.store.episodes_path.exists()
        with pytest.raises(PermissionError, match="NO_ACTIVE_CURRENT_MISSION"):
            service.start(_m1_human_input())
        assert not service.store.episodes_path.exists()
    finally:
        _cleanup_synthetic_mission(mission_auth, live_state)


def test_new_execution_rejects_authorization_not_matching_live_current_mission(tmp_path: Path) -> None:
    mission_auth = _m1_mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        mission_id="FUTURE_SYNTHETIC_MISSION",
    )
    try:
        service = _m1_service(tmp_path, mission_auth, _m1_outputs())
        with pytest.raises(PermissionError, match="CURRENT_MISSION"):
            service.start(_m1_human_input())
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


def test_legacy_m1_lineage_id_is_not_valid_for_new_execution(tmp_path: Path) -> None:
    mission_auth = _m1_mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        mission_id="PLAN010_M1_TOPIC_BELONGING_INTEGRATION_CLOSURE",
    )
    try:
        service = _m1_service(tmp_path, mission_auth, _m1_outputs())
        with pytest.raises(PermissionError, match="CURRENT_MISSION"):
            service.start(_m1_human_input())
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


def test_future_aligned_mission_needs_no_runtime_mission_id_patch(tmp_path: Path) -> None:
    future_mission = "FUTURE_SYNTHETIC_MISSION"
    future_live_state_path = f".runtime-tmp/plan009-m1-{tmp_path.name}/future-live-state.md"
    future_live_state = ROOT / future_live_state_path
    future_live_state.parent.mkdir(parents=True, exist_ok=True)
    live_control = (ROOT / "plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8")
    current_line = next(line for line in live_control.splitlines() if line.startswith("CURRENT_MISSION:"))
    future_live_state.write_text(
        live_control.replace(current_line, f"CURRENT_MISSION: {future_mission}"),
        encoding="utf-8",
    )
    mission_auth = _m1_mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        mission_id=future_mission,
        live_state_path=future_live_state_path,
    )
    try:
        service = _m1_service(
            tmp_path,
            mission_auth,
            _m1_outputs(),
            operational_authority_path=future_live_state_path,
        )
        result = service.start(_m1_human_input())
        lineage = json.loads((result.episode.folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
        assert lineage["mission_id"] == future_mission
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


def test_new_execution_rejects_hash_valid_minimal_live_state(tmp_path: Path) -> None:
    live_state_path = f".runtime-tmp/plan010-m2-m3/{tmp_path.name}-minimal-live.md"
    live_state = ROOT / live_state_path
    live_state.parent.mkdir(parents=True, exist_ok=True)
    live_state.write_text("CURRENT_MISSION: OTHER_MINIMAL_MISSION\n", encoding="utf-8")
    mission_auth = _m1_mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        mission_id="STALE_HISTORICAL_MISSION",
        live_state_path=live_state_path,
    )
    try:
        service = _m1_service(tmp_path, mission_auth, _m1_outputs(), operational_authority_path="plans/001_CONTROL_OPERATIVO.md")
        with pytest.raises(PermissionError, match="mission_id does not match CURRENT_MISSION"):
            service.start(_m1_human_input())
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)
        live_state.unlink(missing_ok=True)


def test_m2_rejects_plan_specific_source_on_new_recovery(tmp_path: Path) -> None:
    store, service = _legacy_service(tmp_path)
    legacy = store.create_legacy_episode(episode_number=1, slug="legacy-source")
    with pytest.raises(StorageError, match="SOURCE_MUST_BE_NEUTRAL"):
        service.administratively_close_irrecoverable_episode(
            legacy.episode_id,
            reason="source guard fixture",
            actor="owner-recovery-test",
            source="PLAN010_M2_ADMINISTRATIVE_RECOVERY",
        )


def _m1_human_input() -> HumanInput:
    return HumanInput.create(
        mode="TOPIC_FIRST",
        content="Tema sintético de prueba",
        initial_question="¿Qué revela este conflicto sobre vivir con otros?",
        context="Fixture técnico; no es un episodio real.",
        channel="TERMINAL",
    )


@pytest.mark.parametrize("origin_present", [True, False], ids=["anchored_legacy", "pre_origin_unverifiable"])
def test_m3_legacy_persisted_execution_requires_verifiable_origin(
    tmp_path: Path, origin_present: bool
) -> None:
    mission_auth = _m1_mission_authorization(tmp_path, execution_interface="TOPIC_BELONGING_TEST")
    modern_service = _m1_service(tmp_path, mission_auth, _m1_outputs())
    modern_service.store.channel_path.mkdir(parents=True, exist_ok=True)
    modern_service.store.episodes_path.mkdir(parents=True, exist_ok=True)
    try:
        result = modern_service.start(_m1_human_input())
        legacy_store = VaultEpisodeStore(tmp_path / "legacy-vault", "CHANNEL")
        legacy_store.channel_path.mkdir(parents=True, exist_ok=True)
        legacy_episode = legacy_store.create_legacy_episode(episode_number=1, slug="legacy-m1-fixture")
        for name in [
            "00_human_input.json", "01_editorial_intake_handoff.json",
            "02_topic_belonging_input.json", "03_topic_belonging_assessment.json",
            "04_topic_belonging_decision.json", "05_topic_belonging_gate.json",
            "topic_belonging_lineage.json", "topic_belonging_execution.json", "workflow_state.json",
        ]:
            shutil.copy2(result.episode.folder / name, legacy_episode.folder / name)
        lineage_path = legacy_episode.folder / "topic_belonging_lineage.json"
        lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
        lineage["mission_id"] = "PLAN010_M1_TOPIC_BELONGING_INTEGRATION_CLOSURE"
        lineage_path.write_text(json.dumps(lineage), encoding="utf-8")
        execution_path = legacy_episode.folder / "topic_belonging_execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        for item in execution["executions"]:
            for field in ("prompt_id", "prompt_version", "prompt_checksum", "prompt_input_checksum"):
                item.pop(field, None)
        execution_path.write_text(json.dumps(execution), encoding="utf-8")
        if not origin_present:
            # This is the exact pre-origin persistence shape: legacy storage markers,
            # legacy lineage, no prompt metadata, and no episode_origin.json.
            (legacy_episode.folder / "episode_origin.json").unlink()
            assert not (legacy_episode.folder / "episode_origin.json").exists()
            legacy_state = json.loads((legacy_episode.folder / "episode_state.json").read_text(encoding="utf-8"))
            assert "mission_id" not in legacy_state
            legacy_index = json.loads(legacy_store.index_path.read_text(encoding="utf-8"))
            legacy_entry = next(item for item in legacy_index["episodes"] if item["ep_id"] == legacy_episode.episode_id)
            assert "mission_id" not in legacy_entry
            assert json.loads(lineage_path.read_text(encoding="utf-8"))["mission_id"] == "PLAN010_M1_TOPIC_BELONGING_INTEGRATION_CLOSURE"
            assert all(
                field not in item
                for item in execution["executions"]
                for field in ("prompt_id", "prompt_version", "prompt_checksum", "prompt_input_checksum")
            )

        boundary = ExecutionCognitiveBoundary(
            repository_root=ROOT,
            mission_authorization_path=mission_auth,
            execution_mode="SYNTHETIC_TEST",
            execution_interface="TOPIC_BELONGING_TEST",
            mock_outputs=_m1_outputs(),
        )
        service = EpisodeApplicationService(
            legacy_store,
            workflow=TopicBelongingTechnicalWorkflow(legacy_store, boundary=boundary),
        )
        if origin_present:
            resumed = service.resume(legacy_episode.episode_id)
            assert resumed["state"]["status"] == "LEGACY_TECHNICAL_INITIALIZATION"
            assert json.loads((legacy_episode.folder / "workflow_state.json").read_text(encoding="utf-8"))["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        else:
            with pytest.raises(TopicBelongingExecutionError, match="EPISODE_ORIGIN_BINDING_MISSING"):
                service.resume(legacy_episode.episode_id)
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


@pytest.mark.parametrize("field", ["prompt_id", "prompt_version", "prompt_checksum", "prompt_input_checksum"])
def test_m3_rejects_tampered_current_prompt_provenance(tmp_path: Path, field: str) -> None:
    mission_auth = _m1_mission_authorization(tmp_path, execution_interface="TOPIC_BELONGING_TEST")
    try:
        service = _m1_service(tmp_path, mission_auth, _m1_outputs())
        result = service.start(_m1_human_input())
        execution_path = result.episode.folder / "topic_belonging_execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["executions"][0][field] = "tampered"
        execution_path.write_text(json.dumps(execution), encoding="utf-8")

        with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
            service.resume(result.episode.episode_id)
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)
