from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import copy
from pathlib import Path

import pytest
import src.application.topic_belonging as topic_belonging

from src.application.contracts import HumanInput
from src.application.handoff import build_editorial_handoff
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError, VaultEpisodeStore
from src.application.topic_belonging import (
    ExecutionCognitiveBoundary,
    M1_ALLOWED_EPISODE_ARTIFACTS,
    TopicBelongingExecutionError,
    TopicBelongingTechnicalWorkflow,
    _expected_input_manifest_checksum,
    _validate_enrichment_binding,
    _validate_human_handoff_binding,
)
from src.ai.contracts import ExecutionRequest, ExecutionStatus
from src.ai.execution import execute
from src.core.mission_authorization import scope_checksum
from src.scripts.channel_intelligence import canonical_checksum, active_profile, validate_assessment, validate_capability_registry
from src.core.cross_registry_integrity import audit_cross_registry
import src.cli as cli

ROOT = Path(__file__).resolve().parents[2]
TRIGGER_KEYS = [
    "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change",
    "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change",
    "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mission_authorization(
    tmp_path: Path,
    *,
    execution_interface: str = "TOPIC_BELONGING_TEST",
    execution_mode: str = "SYNTHETIC_TEST",
    execution_profile: str = "ollama_local",
    allowed_routes: list[str] | None = None,
    single_use: bool = False,
    mission_id: str | None = None,
    live_state_path: str = "plans/001_CONTROL_OPERATIVO.md",
) -> str:
    directory = ROOT / ".runtime-tmp" / f"plan009-m1-{tmp_path.name}"
    directory.mkdir(parents=True, exist_ok=True)
    auth_ref = directory.relative_to(ROOT).as_posix() + "/mission-authorization.json"
    authority_ref = directory.relative_to(ROOT).as_posix() + "/authority.json"
    control = ROOT / "plans/001_CONTROL_OPERATIVO.md"
    material_registry = json.loads((ROOT / "docs/legacy/material_decision_registry.json").read_text(encoding="utf-8"))
    material = next(item for item in material_registry["decisions"] if item["decision_id"] == "MD-CI-001")
    live_state = ROOT / live_state_path
    state_sha = _sha(live_state)
    current_mission = next(
        line.split(":", 1)[1].strip()
        for line in live_state.read_text(encoding="utf-8").splitlines()
        if line.startswith("CURRENT_MISSION:")
    )
    scope = {
        "mission_id": mission_id or current_mission,
        "capability_ids": ["TOPIC_BELONGING_ASSESSMENT"],
        "role_ids": ["CHANNEL_INTELLIGENCE_PRODUCER", "CHANNEL_INTELLIGENCE_REVIEWER"],
        "execution_profile_ids": [execution_profile],
        "execution_interface": execution_interface,
        "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": [],
        "allowed_routes": allowed_routes or ["local_model"],
        "execution_mode": execution_mode,
        "live_state_sha256": state_sha,
        "contains_material_repair": False,
        "repair_integrity_evidence_path": "NONE",
    }
    authority = {
        "mission_id": scope["mission_id"],
        "decision": "APPROVE",
        "artifact_version": "1.0.0",
        "authorized_scope_sha256": scope_checksum(scope),
        "material_decision_binding": {
            "registry_path": "docs/legacy/material_decision_registry.json",
            "decision_id": "MD-CI-001",
            "subject_ref": "capability:TOPIC_BELONGING_ASSESSMENT",
            "decision_sha256": scope_checksum(material),
        },
    }
    authority_path = ROOT / authority_ref
    authority_path.write_text(json.dumps(authority, ensure_ascii=False), encoding="utf-8")
    authorization = {
        "mission_id": scope["mission_id"],
        "authorization": {
            **scope,
            "live_state_path": live_state_path,
            "authority_ref": authority_ref,
            "authority_sha256": _sha(authority_path),
            "authorized_scope_sha256": scope_checksum(scope),
            "single_use": single_use,
            "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
        },
    }
    (ROOT / auth_ref).write_text(json.dumps(authorization, ensure_ascii=False), encoding="utf-8")
    return auth_ref


@pytest.fixture
def mission_auth(tmp_path: Path):
    ref = _mission_authorization(tmp_path)
    yield ref
    shutil.rmtree(ROOT / Path(ref).parent, ignore_errors=True)


def _input() -> dict:
    profile = active_profile()
    return {
        "topic_input_id": "TBI-M1-FIXTURE",
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        "topic": "Tema sintético de prueba",
        "entry_mode": "TOPIC_FIRST",
        "central_question": "¿Qué revela este conflicto sobre vivir con otros?",
        "proposed_angle": "Observar la tensión entre identidad y pertenencia sin convertirla en consejo.",
        "proposed_territory": "Individuo e identidad",
        "initial_evidence": ["fixture://topic-belonging/initial-evidence"],
        "strategic_triggers": {key: False for key in TRIGGER_KEYS},
        "submitted_at": "2026-08-23T10:00:00Z",
    }


def _assessment(topic_input: dict, run_id: str | None = None) -> dict:
    profile = active_profile()
    data = {
        "assessment_id": "TBA-M1-FIXTURE",
        "topic_input_id": topic_input["topic_input_id"],
        "producer_actor_id": "actor-producer-m1",
        "producer_role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        **{key: topic_input[key] for key in ("topic", "central_question", "proposed_angle", "proposed_territory", "initial_evidence", "strategic_triggers", "entry_mode")},
        "sensitive_risks": [],
        "territory_classification": "ACTIVE",
        "identity_alignment": "ALIGNED",
        "promise_alignment": "ALIGNED",
        "risks": [],
        "recommended_conditions": [],
        "recommended_exclusions": [],
        "owner_escalation_recommended": False,
        "evidence": ["fixture://topic-belonging/assessment-evidence"],
        "status": "CLOSED_FOR_REVIEW",
        "artifact_checksum": "",
        "provenance": {
            "actor_id": "actor-producer-m1",
            "role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
            "input_checksums": [canonical_checksum(topic_input, "input")],
            "output_checksum": "",
        },
    }
    checksum = canonical_checksum(data, "assessment")
    data["artifact_checksum"] = checksum
    data["provenance"]["output_checksum"] = checksum
    return data


def _decision(assessment: dict, run_id: str | None = None) -> dict:
    profile = active_profile()
    data = {
        "decision_id": "TBD-M1-FIXTURE",
        "assessment_id": assessment["assessment_id"],
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        "producer_artifact_checksum": assessment["artifact_checksum"],
        "reviewer_actor_id": "actor-reviewer-m1",
        "reviewer_role_id": "CHANNEL_INTELLIGENCE_REVIEWER",
        "reviewer_input_checksum": assessment["artifact_checksum"],
        "decision": "REQUEST_MORE_EVIDENCE",
        "conditions": [],
        "exclusions": [],
        "risks": [],
        "owner_escalation_required": False,
        "owner_escalation_reason": "",
        "strategic_dimensions_affected": [],
        "temporary_or_permanent_effect": "NONE",
        "precedent_risk": "LOW",
        "evidence": ["fixture://topic-belonging/reviewer-evidence"],
        "decided_at": "2026-08-23T10:01:00Z",
        "provenance": {
            "actor_id": "actor-reviewer-m1",
            "role_id": "CHANNEL_INTELLIGENCE_REVIEWER",
            "input_checksum": assessment["artifact_checksum"],
            "output_checksum": "",
        },
    }
    data["provenance"]["output_checksum"] = canonical_checksum(data, "decision")
    return data


def _service(
    tmp_path: Path,
    mission_auth: str,
    outputs: dict[str, dict],
    *,
    channel: str = "CHANNEL",
    operational_authority_path: str | None = None,
) -> EpisodeApplicationService:
    tmp_path.mkdir(parents=True, exist_ok=True)
    store = VaultEpisodeStore(tmp_path / "vault", channel)
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="SYNTHETIC_TEST",
        execution_interface="TOPIC_BELONGING_TEST",
        mock_outputs=outputs,
        operational_authority_path=operational_authority_path,
    )
    return EpisodeApplicationService(
        store,
        workflow=TopicBelongingTechnicalWorkflow(store, boundary=boundary),
    )


def _outputs(*, invalid_stage: str | None = None, same_reviewer_run: bool = False) -> dict[str, dict]:
    topic_input = _input()
    assessment = _assessment(topic_input)
    decision = _decision(assessment)
    outputs = {"enrich": topic_input, "produce": assessment, "review": decision}
    if invalid_stage:
        outputs[invalid_stage] = {"invalid": True}
    return outputs


def test_m1_happy_path_uses_cli_application_service_and_persists_stop(tmp_path: Path, mission_auth: str) -> None:
    result = _service(tmp_path, mission_auth, _outputs()).start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            context="Fixture técnico; no es un episodio real.",
            channel="TERMINAL",
        )
    )
    folder = result.episode.folder
    assert result.workflow["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    assert result.workflow["vertical_gate_status"] == "BLOCKED"
    assert result.workflow["editorial_decision"] == "REQUEST_MORE_EVIDENCE"
    for name in (
        "00_human_input.json", "01_editorial_intake_handoff.json", "02_topic_belonging_input.json",
        "03_topic_belonging_assessment.json", "04_topic_belonging_decision.json",
        "05_topic_belonging_gate.json", "workflow_state.json", "topic_belonging_lineage.json",
    ):
        assert (folder / name).is_file(), name
    assert not any((folder / name).exists() for name in ("episode_brief.json", "research_pack.json", "thesis_provisional.json", "script.json"))
    executions = json.loads((folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    assert [item["stage"] for item in executions] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
    assert all(item["provider_or_adapter"] == "mock" for item in executions)
    assert all(item["execution_route"] == "local_model" for item in executions)
    assert all(item["execution_profile"] == "ollama_local" for item in executions)
    lineage = json.loads((folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
    assert lineage["producer_run_id"] != lineage["reviewer_run_id"]
    assert lineage["producer_actor_id"] != lineage["reviewer_actor_id"]


def test_m1_terminal_cli_entrypoint_reaches_the_same_application_service(
    tmp_path: Path, mission_auth: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    monkeypatch.setattr(cli, "_service", lambda settings, **_kwargs: service)

    assert cli.main([
        "iniciar",
        "--modo", "tema",
        "--tema", "Tema sintético de prueba",
        "--pregunta", "¿Qué revela este conflicto sobre vivir con otros?",
    ]) == 0
    assert "Topic Belonging alcanzó su gate técnico" in capsys.readouterr().out


def test_m1_terminal_cli_entrypoint_uses_real_factory_with_explicit_synthetic_boundary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    mission_auth = _mission_authorization(tmp_path, execution_interface="TOPIC_BELONGING_TERMINAL")
    try:
        outputs_path = tmp_path / "synthetic-outputs.json"
        outputs_path.write_text(json.dumps(_outputs(), ensure_ascii=False), encoding="utf-8")
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps({"vault_root": str(tmp_path / "vault"), "channel_id": "CHANNEL"}),
            encoding="utf-8",
        )
        assert cli.main([
            "iniciar",
            "--config", str(settings),
            "--mission-authorization", mission_auth,
            "--synthetic-outputs", str(outputs_path),
            "--modo", "tema",
            "--tema", "Tema sintético de prueba",
            "--pregunta", "¿Qué revela este conflicto sobre vivir con otros?",
        ]) == 0
        assert "Topic Belonging alcanzó su gate técnico" in capsys.readouterr().out
        episode = next((tmp_path / "vault/CHANNEL/episodios").iterdir())
        assert (episode / "05_topic_belonging_gate.json").is_file()
        assert json.loads((episode / "workflow_state.json").read_text(encoding="utf-8"))["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        executions = json.loads((episode / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
        assert [item["stage"] for item in executions] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
        assert all(item["provider_or_adapter"] == "mock" for item in executions)
        assert all(item["execution_route"] == "local_model" for item in executions)
        assert all(item["execution_profile"] == "ollama_local" for item in executions)
        lineage = json.loads((episode / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
        assert lineage["producer_run_id"] != lineage["reviewer_run_id"]
        assert not any((episode / name).exists() for name in ("episode_brief.json", "research_pack.json", "script.json"))
        assert {path.name for path in episode.iterdir()} == set(M1_ALLOWED_EPISODE_ARTIFACTS)
        assert not any(
            (episode / name).exists()
            for name in (
                "episode_brief.json", "research_pack.json", "thesis_provisional.json", "script.json",
                "narrative_human_analysis.json", "material_curation.json", "refined_thesis.json",
                "editorial_script_promise.json", "b5_i2_semantic_sufficiency_audit.json",
                "youtube_adaptation_b5_i2_package.json", "youtube_adaptation_review.json",
            )
        )
        assert lineage["producer_actor_id"] != lineage["reviewer_actor_id"]
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


def test_m1_preflight_probe_does_not_reserve_single_use_authorization(tmp_path: Path) -> None:
    mission_auth = _mission_authorization(
        tmp_path, execution_interface="TOPIC_BELONGING_TEST", single_use=True
    )
    registry = tmp_path / "execution-provenance.json"
    try:
        boundary = ExecutionCognitiveBoundary(
            repository_root=ROOT,
            mission_authorization_path=mission_auth,
            execution_mode="SYNTHETIC_TEST",
            execution_interface="TOPIC_BELONGING_TEST",
            mock_outputs=_outputs(),
            execution_registry_path=str(registry),
        )
        boundary.preflight()
        assert not registry.exists()
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)


@pytest.mark.parametrize("stage", ["produce", "review"])
def test_m1_invalid_cognitive_output_blocks_without_success(tmp_path: Path, mission_auth: str, stage: str) -> None:
    with pytest.raises(TopicBelongingExecutionError):
        _service(tmp_path, mission_auth, _outputs(invalid_stage=stage)).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", initial_question="¿Qué revela este conflicto sobre vivir con otros?", channel="TERMINAL")
        )
    folders = list((tmp_path / "vault/CHANNEL/episodios").iterdir())
    assert folders and not (folders[0] / "05_topic_belonging_gate.json").exists()


def test_m1_reviewer_actor_provenance_mismatch_blocks_fresh_execution(tmp_path: Path, mission_auth: str) -> None:
    outputs = _outputs()
    outputs["review"]["provenance"]["actor_id"] = "FORGED-REVIEWER-ACTOR"
    with pytest.raises(TopicBelongingExecutionError, match="REVIEWER_ACTOR_PROVENANCE_MISMATCH"):
        _service(tmp_path, mission_auth, outputs).start(
            HumanInput.create(
                mode="TOPIC_FIRST",
                content="Tema sintético de prueba",
                initial_question="¿Qué revela este conflicto sobre vivir con otros?",
                channel="TERMINAL",
            )
        )


def test_m1_same_run_reviewer_is_blocked(tmp_path: Path, mission_auth: str) -> None:
    real_execute = topic_belonging.execute
    producer_run_id: str | None = None

    def execute_with_reused_runtime_run_id(request):
        nonlocal producer_run_id
        result = real_execute(request)
        if request.role == "CHANNEL_INTELLIGENCE_PRODUCER" and request.output_schema == "topic_belonging_assessment":
            producer_run_id = result.run_id
        elif request.role == "CHANNEL_INTELLIGENCE_REVIEWER" and producer_run_id is not None:
            result.run_id = producer_run_id
            result.output["reviewer_run_id"] = producer_run_id
            result.output["provenance"]["run_id"] = producer_run_id
        return result

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(topic_belonging, "execute", execute_with_reused_runtime_run_id)
        with pytest.raises(TopicBelongingExecutionError, match="EXECUTION_INDEPENDENCE_INVALID"):
            _service(tmp_path, mission_auth, _outputs()).start(
                HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", initial_question="¿Qué revela este conflicto sobre vivir con otros?", channel="TERMINAL")
            )


def test_m1_fake_producer_declared_run_id_cannot_override_runtime(tmp_path: Path, mission_auth: str) -> None:
    outputs = _outputs()
    outputs["produce"]["producer_run_id"] = "FAKE-PRODUCER-RUN"
    with pytest.raises(TopicBelongingExecutionError, match="PRODUCER_RUNTIME_PROVENANCE_MISMATCH"):
        _service(tmp_path, mission_auth, outputs).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )


def test_m1_fake_reviewer_declared_run_id_cannot_override_runtime(tmp_path: Path, mission_auth: str) -> None:
    outputs = _outputs()
    outputs["review"]["reviewer_run_id"] = "FAKE-REVIEWER-RUN"
    with pytest.raises(TopicBelongingExecutionError, match="REVIEWER_RUNTIME_PROVENANCE_MISMATCH"):
        _service(tmp_path, mission_auth, outputs).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )


def test_m1_missing_authorization_blocks_before_episode_creation(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    boundary = ExecutionCognitiveBoundary(repository_root=ROOT, execution_mode="SYNTHETIC_TEST", mock_outputs=_outputs())
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_REQUIRED"):
        EpisodeApplicationService(store, workflow=workflow).start(HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL"))
    assert not (tmp_path / "vault/CHANNEL/episodios").exists()


def test_m1_invalid_authorization_blocks_before_episode_creation(tmp_path: Path) -> None:
    auth_path = tmp_path / "invalid-authorization.json"
    auth_path.write_text("{\"mission_id\": \"wrong\"}", encoding="utf-8")
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=str(auth_path),
        execution_mode="SYNTHETIC_TEST",
        mock_outputs=_outputs(),
    )
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_INVALID"):
        EpisodeApplicationService(store, workflow=workflow).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )
    assert not (tmp_path / "vault/CHANNEL/episodios").exists()


def test_m1_authorization_path_outside_repository_blocks_before_episode_creation(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=str((tmp_path / "external-authorization.json").resolve()),
        execution_mode="SYNTHETIC_TEST",
        mock_outputs=_outputs(),
    )
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_INVALID:MISSION_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY"):
        EpisodeApplicationService(store, workflow=workflow).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )
    assert not (tmp_path / "vault/CHANNEL/episodios").exists()


def test_m1_real_provider_and_mock_injection_are_blocked() -> None:
    with pytest.raises(PermissionError, match="MOCK_OUTPUTS_REQUIRE_SYNTHETIC_TEST_MODE"):
        ExecutionCognitiveBoundary(execution_mode="REAL", mock_outputs=_outputs())


def test_m2_real_requires_mission_authorization_even_with_neutral_family() -> None:
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_REQUIRED"):
        ExecutionCognitiveBoundary(execution_mode="REAL").preflight()


def test_m2_real_without_authorization_blocks_before_provider() -> None:
    boundary = ExecutionCognitiveBoundary(execution_mode="REAL", execution_profile="ollama_local")
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_REQUIRED"):
        boundary.preflight()


def test_m2_real_profile_mismatch_is_fail_closed(tmp_path: Path) -> None:
    mission_auth = _mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        execution_mode="REAL",
        execution_profile="ollama_local",
    )
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="REAL",
        execution_interface="TOPIC_BELONGING_TEST",
        execution_profile="deepseek_chat",
        model_override="test-model",
    )
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_INVALID"):
        boundary.preflight()


def test_m2_explicit_agent_profile_derives_only_declared_route(tmp_path: Path) -> None:
    mission_auth = _mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        execution_mode="REAL",
        execution_profile="codex_current",
        allowed_routes=["agent_harness"],
    )
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="REAL",
        execution_interface="TOPIC_BELONGING_TEST",
        execution_profile="codex_current",
    )
    assert boundary.execution_route is None
    assert boundary.preflight()
    assert boundary.execution_route == "agent_harness"


def test_m2_real_authorized_reaches_provider_boundary_without_external_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import src.ai.execution as ai_execution

    mission_auth = _mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TEST",
        execution_mode="REAL",
        execution_profile="ollama_local",
    )
    selection = tmp_path / "execution-family-selection.json"
    selection.write_text(json.dumps({
        "selection_version": "1.0.0",
        "families": {"AGENT_HARNESS": False, "API_PROVIDER": False, "LOCAL_MODEL": True},
    }), encoding="utf-8")
    outputs = _outputs()

    class ProviderDouble:
        name = "ollama"

        def execute(self, request: ExecutionRequest):
            output = copy.deepcopy({
                "topic_belonging_input": outputs["enrich"],
                "topic_belonging_assessment": outputs["produce"],
                "topic_belonging_decision": outputs["review"],
            }[request.output_schema])
            if request.output_schema == "topic_belonging_decision":
                assessment = json.loads(request.input_artifacts[1].path.read_text(encoding="utf-8"))
                output["producer_artifact_checksum"] = assessment["artifact_checksum"]
                output["reviewer_input_checksum"] = assessment["artifact_checksum"]
                output["provenance"]["input_checksum"] = assessment["artifact_checksum"]
                output["provenance"]["output_checksum"] = canonical_checksum(output, "decision")
            return output, {"provider_or_adapter": "ollama", "model_or_evaluator": request.model}

    monkeypatch.setattr(ai_execution, "OllamaProvider", ProviderDouble)
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="REAL",
        execution_interface="TOPIC_BELONGING_TEST",
        execution_profile="ollama_local",
        execution_family_selection_path=selection.relative_to(ROOT).as_posix(),
        model_override="test-double-model",
    )
    short_root = tmp_path / "r"
    short_root.mkdir()
    try:
        store = VaultEpisodeStore(short_root / "vault", "C")
        workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
        result = EpisodeApplicationService(store, workflow=workflow).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )
        executions = json.loads((result.episode.folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
        assert all(item["execution_mode"] == "REAL" for item in executions)
        assert all(item["provider_or_adapter"] == "ollama" for item in executions)
        assert all(item["model_or_evaluator"] == "test-double-model" for item in executions)
    finally:
        shutil.rmtree(short_root, ignore_errors=True)


def test_m1_real_provider_mode_is_blocked_before_episode_creation(tmp_path: Path, mission_auth: str) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="REAL",
    )
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    with pytest.raises(PermissionError, match="MISSION_AUTHORIZATION_INVALID"):
        EpisodeApplicationService(store, workflow=workflow).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )
    assert not (tmp_path / "vault/CHANNEL/episodios").exists()


def test_m1_synthetic_mode_without_fake_is_blocked_before_episode_creation(tmp_path: Path, mission_auth: str) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="SYNTHETIC_TEST",
    )
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    with pytest.raises(PermissionError, match="SYNTHETIC_MOCK_OUTPUTS_REQUIRED"):
        EpisodeApplicationService(store, workflow=workflow).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )
    assert not (tmp_path / "vault/CHANNEL/episodios").exists()


def test_m1_synthetic_mode_with_partial_fake_is_blocked_before_episode_creation(tmp_path: Path, mission_auth: str) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=mission_auth,
        execution_mode="SYNTHETIC_TEST",
        mock_outputs={"enrich": _input()},
    )
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    with pytest.raises(PermissionError, match="SYNTHETIC_MOCK_OUTPUTS_REQUIRED"):
        EpisodeApplicationService(store, workflow=workflow).start(
            HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL")
        )
    assert not (tmp_path / "vault/CHANNEL/episodios").exists()


def test_m1_input_incomplete_and_tampered_provenance_block(tmp_path: Path, mission_auth: str) -> None:
    incomplete = _outputs()
    incomplete["enrich"] = {"topic_input_id": "TBI-INCOMPLETE"}
    with pytest.raises(TopicBelongingExecutionError):
        _service(tmp_path, mission_auth, incomplete).start(HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL"))

    tampered = _outputs()
    tampered["produce"]["topic"] = "tampered"
    with pytest.raises(TopicBelongingExecutionError, match="ASSESSMENT_INVALID"):
        _service(tmp_path, mission_auth, tampered, channel="T").start(HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", initial_question="¿Qué revela este conflicto sobre vivir con otros?", channel="TERMINAL"))


def test_m1_anchor_work_binding_cannot_be_replaced_by_enrichment(tmp_path: Path, mission_auth: str) -> None:
    handoff = {
        "entry_mode": "ANCHOR_WORK_FIRST",
        "field_bindings": {"narrative_work": "Obra suministrada por la persona"},
        "profile_binding": {
            "profile_id": active_profile()["profile_id"],
            "profile_version": active_profile()["profile_version"],
            "profile_checksum": active_profile()["profile_checksum"],
        },
    }
    topic_input = _input()
    topic_input.update({"entry_mode": "ANCHOR_WORK_FIRST", "narrative_work": "Obra inventada por el enriquecimiento"})
    assert "ENRICHMENT_NARRATIVE_WORK_MISMATCH" in _validate_enrichment_binding(topic_input, handoff)


@pytest.mark.parametrize(
    "human_input",
    [
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema de entrada",
            initial_question="¿Qué revela este conflicto?",
            context="Contexto de entrada",
            channel="TERMINAL",
        ),
        HumanInput.create(
            mode="ANCHOR_WORK_FIRST",
            content="Obra de entrada",
            initial_question="¿Qué revela esta obra?",
            context="Contexto de obra",
            works=["Obra de entrada"],
            channel="TERMINAL",
        ),
        HumanInput.create(
            mode="CORPUS_FIRST",
            content="",
            initial_question="¿Qué revela este corpus?",
            context="Contexto de corpus",
            works=["Obra A", "Obra B"],
            channel="TERMINAL",
        ),
    ],
)
def test_m1_human_handoff_binding_covers_all_entry_modes(human_input: HumanInput) -> None:
    profile = active_profile()
    handoff = build_editorial_handoff(
        human_input,
        {
            "ACTIVE_PROFILE_ID": profile["profile_id"],
            "ACTIVE_PROFILE_VERSION": profile["profile_version"],
            "profile_checksum": profile["profile_checksum"],
        },
    )
    assert _validate_human_handoff_binding(human_input.to_dict(), handoff) == []


def test_m1_critical_persistence_failure_does_not_report_success(tmp_path: Path, mission_auth: str, monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    monkeypatch.setattr(service.store, "record_topic_belonging_vertical", lambda *args, **kwargs: (_ for _ in ()).throw(StorageError("critical persistence failure")))
    with pytest.raises(StorageError):
        service.start(HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", initial_question="¿Qué revela este conflicto sobre vivir con otros?", channel="TERMINAL"))


@pytest.mark.parametrize(
    ("capability_id", "role", "operation", "route", "expected"),
    [
        ("UNKNOWN_CAPABILITY", "CHANNEL_INTELLIGENCE_PRODUCER", "EXECUTE_CAPABILITY", None, "CAPABILITY_UNREGISTERED"),
        ("TOPIC_BELONGING_ASSESSMENT", "WRONG_ROLE", "EXECUTE_CAPABILITY", None, "role scope"),
        ("TOPIC_BELONGING_ASSESSMENT", "CHANNEL_INTELLIGENCE_PRODUCER", "WRONG_OPERATION", None, "operation scope"),
        ("TOPIC_BELONGING_ASSESSMENT", "CHANNEL_INTELLIGENCE_PRODUCER", "EXECUTE_CAPABILITY", "WRONG_ROUTE", "routing scope"),
    ],
)
def test_m1_authorization_capability_role_scope_and_route_are_fail_closed(
    tmp_path: Path,
    mission_auth: str,
    capability_id: str,
    role: str,
    operation: str,
    route: str | None,
    expected: str,
) -> None:
    request = ExecutionRequest(
        capability_id=capability_id,
        skill_id="topic_belonging",
        skill_version="1.0.0",
        input_artifacts=[],
        output_schema="topic_belonging_decision",
        execution_mode="SYNTHETIC_TEST",
        provider="mock",
            mock_output={},
            execution_route=route or "local_model",
            execution_profile="ollama_local",
        role=role,
        config={
            "repository_root": str(ROOT),
            "mission_authorization_path": mission_auth,
            "mission_operation": operation,
            "execution_interface": "TOPIC_BELONGING_TEST",
        },
    )
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert expected in (result.error or "")


def test_m1_registry_and_routing_are_resolvable() -> None:
    assert validate_capability_registry() == []
    integrity, authority = audit_cross_registry(ROOT)
    assert not integrity["findings"]
    assert not authority["findings"]


# --- Corrective remediation: recovery, checksum binding and lineage provenance ---


def _index_episode_id(tmp_path: Path, channel: str = "CHANNEL") -> str:
    index = json.loads((tmp_path / "vault" / channel / "index" / "episodes_index.json").read_text(encoding="utf-8"))
    return index["episodes"][0]["ep_id"]


def test_m1_producer_failure_is_recoverable_via_resume(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs(invalid_stage="produce"))
    with pytest.raises(TopicBelongingExecutionError):
        service.start(HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL"))
    folders = list((tmp_path / "vault/CHANNEL/episodios").iterdir())
    assert len(folders) == 1
    assert not (folders[0] / "05_topic_belonging_gate.json").exists()

    service.workflow.boundary.mock_outputs = _outputs()
    resumed = service.resume(_index_episode_id(tmp_path))
    assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    assert (folders[0] / "05_topic_belonging_gate.json").exists()


def test_m1_reviewer_failure_is_recoverable_via_resume(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs(invalid_stage="review"))
    with pytest.raises(TopicBelongingExecutionError):
        service.start(HumanInput.create(mode="TOPIC_FIRST", content="Tema sintético de prueba", channel="TERMINAL"))
    folders = list((tmp_path / "vault/CHANNEL/episodios").iterdir())
    assert len(folders) == 1
    assert not (folders[0] / "05_topic_belonging_gate.json").exists()

    service.workflow.boundary.mock_outputs = _outputs()
    resumed = service.resume(_index_episode_id(tmp_path))
    assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"


def test_m1_persistence_failure_is_recoverable_via_resume(tmp_path: Path, mission_auth: str, monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    original = service.store.record_topic_belonging_vertical

    def fail_once(*args, **kwargs):
        monkeypatch.setattr(service.store, "record_topic_belonging_vertical", original)
        raise StorageError("critical persistence failure")

    monkeypatch.setattr(service.store, "record_topic_belonging_vertical", fail_once)
    with pytest.raises(StorageError):
        service.start(
            HumanInput.create(
                mode="TOPIC_FIRST",
                content="Tema sintético de prueba",
                initial_question="¿Qué revela este conflicto sobre vivir con otros?",
                channel="TERMINAL",
            )
        )
    folders = list((tmp_path / "vault/CHANNEL/episodios").iterdir())
    assert len(folders) == 1
    assert not (folders[0] / "05_topic_belonging_gate.json").exists()

    resumed = service.resume(_index_episode_id(tmp_path))
    assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"


def test_m1_resume_is_idempotent_and_does_not_duplicate_artifacts(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    folder = result.episode.folder
    lineage_before = json.loads((folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
    for _ in range(2):
        resumed = service.resume(result.episode.episode_id)
        assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    executions = json.loads((folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    assert [e["stage"] for e in executions] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
    assert json.loads((folder / "topic_belonging_lineage.json").read_text(encoding="utf-8")) == lineage_before
    vertical = [
        name
        for name in (
            "02_topic_belonging_input.json",
            "03_topic_belonging_assessment.json",
            "04_topic_belonging_decision.json",
            "05_topic_belonging_gate.json",
            "topic_belonging_lineage.json",
            "topic_belonging_execution.json",
        )
        if (folder / name).exists()
    ]
    assert len(vertical) == 6


def test_m1_execution_checksums_bind_to_persisted_artifacts(tmp_path: Path, mission_auth: str) -> None:
    result = _service(tmp_path, mission_auth, _outputs()).start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    folder = result.episode.folder
    executions = json.loads((folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    by_stage = {e["stage"]: e for e in executions}
    topic_input = json.loads((folder / "02_topic_belonging_input.json").read_text(encoding="utf-8"))
    assessment = json.loads((folder / "03_topic_belonging_assessment.json").read_text(encoding="utf-8"))
    decision = json.loads((folder / "04_topic_belonging_decision.json").read_text(encoding="utf-8"))
    assert by_stage["ENRICHMENT"]["artifact_checksum"] == canonical_checksum(topic_input, "input")
    assert by_stage["PRODUCER"]["artifact_checksum"] == assessment["artifact_checksum"]
    assert by_stage["REVIEWER"]["artifact_checksum"] == decision["provenance"]["output_checksum"]
    for e in executions:
        assert re.fullmatch(r"[0-9a-f]{64}", e["output_checksum"])
        assert re.fullmatch(r"[0-9a-f]{64}", e["artifact_checksum"])
        assert e["artifact_ref"]


def test_m1_tampered_persisted_artifact_fails_checksum_verification(tmp_path: Path, mission_auth: str) -> None:
    result = _service(tmp_path, mission_auth, _outputs()).start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    folder = result.episode.folder
    assessment_path = folder / "03_topic_belonging_assessment.json"
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    assessment["topic"] = "tampered-topic"
    assessment_path.write_text(json.dumps(assessment, ensure_ascii=False), encoding="utf-8")
    topic_input = json.loads((folder / "02_topic_belonging_input.json").read_text(encoding="utf-8"))
    assert "ASSESSMENT_ARTIFACT_CHECKSUM_INVALID" in validate_assessment(assessment, topic_input)


def test_m1_lineage_has_no_unjustified_unknown(tmp_path: Path, mission_auth: str) -> None:
    result = _service(tmp_path, mission_auth, _outputs()).start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    folder = result.episode.folder
    lineage = json.loads((folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
    executions = json.loads((folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    by_stage = {e["stage"]: e for e in executions}
    for key in ("enrichment_run_id", "producer_run_id", "reviewer_run_id"):
        assert lineage[key] and lineage[key] != "UNKNOWN"
    assert lineage["enrichment_run_id"] == by_stage["ENRICHMENT"]["run_id"]
    assert lineage["producer_run_id"] == by_stage["PRODUCER"]["run_id"]
    assert lineage["reviewer_run_id"] == by_stage["REVIEWER"]["run_id"]
    assert by_stage["PRODUCER"]["input_versions"] == [lineage["enrichment_run_id"]]
    assert by_stage["REVIEWER"]["input_versions"] == [lineage["enrichment_run_id"], lineage["producer_run_id"]]
    for e in executions:
        assert "UNKNOWN" not in e["input_versions"]
        assert all(v for v in e["input_versions"])


def test_m1_forged_lineage_run_id_is_detectable_against_execution_records(tmp_path: Path, mission_auth: str) -> None:
    result = _service(tmp_path, mission_auth, _outputs()).start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    folder = result.episode.folder
    lineage_path = folder / "topic_belonging_lineage.json"
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    executions = json.loads((folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    by_stage = {e["stage"]: e for e in executions}
    assert lineage["producer_run_id"] == by_stage["PRODUCER"]["run_id"]
    lineage["producer_run_id"] = "FORGED-PRODUCER-RUN"
    lineage_path.write_text(json.dumps(lineage, ensure_ascii=False), encoding="utf-8")
    tampered = json.loads(lineage_path.read_text(encoding="utf-8"))
    assert tampered["producer_run_id"] == "FORGED-PRODUCER-RUN"
    assert tampered["producer_run_id"] != by_stage["PRODUCER"]["run_id"]


def _persisted_valid_m1_without_workflow_state(tmp_path: Path, mission_auth: str):
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    (result.episode.folder / "workflow_state.json").unlink()
    return service, result


def test_m1_valid_persisted_vertical_without_workflow_state_reconstructs_stop(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    resumed = service.resume(result.episode.episode_id)
    assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    assert (result.episode.folder / "workflow_state.json").is_file()


def test_m1_existing_stop_with_corrupt_artifact_is_not_accepted_as_idempotent(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    path = result.episode.folder / "03_topic_belonging_assessment.json"
    assessment = json.loads(path.read_text(encoding="utf-8"))
    assessment["topic"] = "tampered-after-stop"
    path.write_text(json.dumps(assessment, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)


def test_m1_tampered_human_input_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    path = result.episode.folder / "00_human_input.json"
    human_input = json.loads(path.read_text(encoding="utf-8"))
    human_input["content"] = "tampered-human-input"
    path.write_text(json.dumps(human_input, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)


def test_m1_inconsistent_reviewer_actor_provenance_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "04_topic_belonging_decision.json"
    decision = json.loads(path.read_text(encoding="utf-8"))
    decision["provenance"]["actor_id"] = "FORGED-REVIEWER-ACTOR"
    path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_partial_vertical_evidence_is_preserved_when_recovery_retry_fails(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    (result.episode.folder / "workflow_state.json").unlink()
    (result.episode.folder / "05_topic_belonging_gate.json").unlink()
    service.workflow.boundary.mock_outputs["produce"] = {"invalid": True}
    with pytest.raises(TopicBelongingExecutionError):
        service.resume(result.episode.episode_id)
    assert list(result.episode.folder.glob("r*-03_topic_belonging_assessment.json"))


def test_m1_incomplete_vertical_cannot_coexist_with_recorded_stop(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    (result.episode.folder / "05_topic_belonging_gate.json").unlink()
    with pytest.raises(TopicBelongingExecutionError, match="INCOMPLETE_VERTICAL_WITH_STOP_STATE"):
        service.resume(result.episode.episode_id)
    assert (result.episode.folder / "03_topic_belonging_assessment.json").is_file()


def test_m1_partial_vertical_evidence_can_retry_atomically(tmp_path: Path, mission_auth: str) -> None:
    service = _service(tmp_path, mission_auth, _outputs())
    result = service.start(
        HumanInput.create(
            mode="TOPIC_FIRST",
            content="Tema sintético de prueba",
            initial_question="¿Qué revela este conflicto sobre vivir con otros?",
            channel="TERMINAL",
        )
    )
    (result.episode.folder / "workflow_state.json").unlink()
    (result.episode.folder / "05_topic_belonging_gate.json").unlink()
    resumed = service.resume(result.episode.episode_id)
    assert resumed["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    assert (result.episode.folder / "05_topic_belonging_gate.json").is_file()
    assert list(result.episode.folder.glob("r*-03_topic_belonging_assessment.json"))
    resumed_again = service.resume(result.episode.episode_id)
    assert resumed_again["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"


def test_m1_corrupt_assessment_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "03_topic_belonging_assessment.json"
    assessment = json.loads(path.read_text(encoding="utf-8"))
    assessment["topic"] = "tampered-after-persistence"
    path.write_text(json.dumps(assessment, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_corrupt_decision_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "04_topic_belonging_decision.json"
    decision = json.loads(path.read_text(encoding="utf-8"))
    decision["decision_id"] = "FORGED-DECISION"
    path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_corrupt_lineage_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "topic_belonging_lineage.json"
    lineage = json.loads(path.read_text(encoding="utf-8"))
    lineage["producer_run_id"] = "FORGED-PRODUCER-RUN"
    path.write_text(json.dumps(lineage, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_corrupt_execution_record_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "topic_belonging_execution.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["executions"][1]["artifact_ref"] = "topic_belonging_assessment:FORGED"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_incompatible_execution_runtime_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "topic_belonging_execution.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["executions"][0]["execution_mode"] = "REAL"
    payload["executions"][0]["provider_kind"] = "REAL"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_forged_raw_execution_checksum_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "topic_belonging_execution.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["executions"][2]["output_checksum"] = "f" * 64
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="RAW_OUTPUT_CHECKSUM_MISMATCH"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_persisted_input_manifests_match_recomputed_runtime_manifests(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    folder = result.episode.folder
    handoff = json.loads((folder / "01_editorial_intake_handoff.json").read_text(encoding="utf-8"))
    topic_input = json.loads((folder / "02_topic_belonging_input.json").read_text(encoding="utf-8"))
    assessment = json.loads((folder / "03_topic_belonging_assessment.json").read_text(encoding="utf-8"))
    executions = json.loads((folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    expected = {
        stage: _expected_input_manifest_checksum(result.episode.episode_id, stage, handoff, topic_input, assessment)
        for stage in ("ENRICHMENT", "PRODUCER", "REVIEWER")
    }
    assert {execution["stage"]: execution["input_manifest_checksum"] for execution in executions} == expected


@pytest.mark.parametrize("stage", ["ENRICHMENT", "PRODUCER", "REVIEWER"])
def test_m1_forged_input_manifest_checksum_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str, stage: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "topic_belonging_execution.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    execution = next(item for item in payload["executions"] if item["stage"] == stage)
    execution["input_manifest_checksum"] = "f" * 64
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match=f"EXECUTION_{stage}_INPUT_MANIFEST_CHECKSUM_MISMATCH"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()


def test_m1_incompatible_gate_blocks_stop_reconstruction(tmp_path: Path, mission_auth: str) -> None:
    service, result = _persisted_valid_m1_without_workflow_state(tmp_path, mission_auth)
    path = result.episode.folder / "05_topic_belonging_gate.json"
    gate = json.loads(path.read_text(encoding="utf-8"))
    gate["decision"] = "APPROVE"
    path.write_text(json.dumps(gate, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_VERTICAL_INTEGRITY_INVALID"):
        service.resume(result.episode.episode_id)
    assert not (result.episode.folder / "workflow_state.json").exists()
