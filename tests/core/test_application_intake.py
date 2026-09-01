"""Tests for the channel-neutral product entrypoint."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.application.contracts import EntryMode, HumanInput, InputValidationError
from src.application.handoff import build_editorial_handoff
from src.application.interaction import DecisionRequest, HumanDecision, UserCancelled
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError, VaultEpisodeStore
from src.application.workflow import ControlledB5I1Preparation, WorkflowDecisionStale
from src.application.authority import (
    OperationalAuthorityError,
    resolve_active_mission_bundle,
    resolve_operational_authority,
)
from src.cli import _interactive_input, _non_interactive_input, main
from src.core.contract_validation import validate_against_schema
from src.core.mission_authorization import scope_checksum, sha256_file


ROOT = Path(__file__).resolve().parents[2]

PROFILE = {
    "ACTIVE_PROFILE_ID": "mas_alla_del_guion",
    "ACTIVE_PROFILE_VERSION": "1.2.2",
    "profile_checksum": "a" * 64,
}


def _persist_request_worker(root: str, episode_id: str, request: dict, result_queue) -> None:
    try:
        persisted = VaultEpisodeStore(root, "CHANNEL").record_decision_request(episode_id, request)
        result_queue.put(("ok", persisted["request_checksum"]))
    except Exception as exc:  # pragma: no cover - exercised in the child process
        result_queue.put(("error", repr(exc)))


def service(tmp_path: Path, workflow=None, interaction=None) -> EpisodeApplicationService:
    return EpisodeApplicationService(
        VaultEpisodeStore(tmp_path / "vault", "CHANNEL"),
        workflow=workflow,
        profile_loader=lambda: PROFILE,
        interaction=interaction,
    )


def test_three_canonical_modes_are_valid() -> None:
    topic = HumanInput.create(mode="tema", content="Tema", context="Pregunta")
    anchor = HumanInput.create(mode="obra", content="Her")
    corpus = HumanInput.create(mode="corpus", works=["Her", "Lost in Translation"])
    assert topic.mode is EntryMode.TOPIC_FIRST
    assert anchor.works == ("Her",)
    assert corpus.mode is EntryMode.CORPUS_FIRST
    assert validate_against_schema(topic.to_dict(), "human_episode_input") == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "tema", "content": ""},
        {"mode": "obra", "content": "  "},
        {"mode": "corpus", "works": []},
    ],
)
def test_empty_human_content_is_rejected(kwargs: dict) -> None:
    with pytest.raises(InputValidationError):
        HumanInput.create(**kwargs)


def test_handoff_does_not_duplicate_or_complete_topic_belonging() -> None:
    human = HumanInput.create(mode="tema", content="Tema", context="Pregunta")
    handoff = build_editorial_handoff(human, PROFILE)
    assert handoff["target_contract"] == "topic_belonging_input"
    assert handoff["status"] == "AWAITING_EDITORIAL_ENRICHMENT"
    assert handoff["provenance"]["editorial_decisions_made"] is False
    assert "proposed_angle" in handoff["unresolved_fields"]
    assert validate_against_schema(handoff, "editorial_intake_handoff") == []


def test_question_and_context_are_distinct_bindings() -> None:
    with_question = HumanInput.create(mode="tema", content="Tema", initial_question="Pregunta", context="Contexto")
    handoff = build_editorial_handoff(with_question, PROFILE)
    assert handoff["field_bindings"]["central_question"] == "Pregunta"
    assert handoff["field_bindings"]["context"] == "Contexto"
    without_question = build_editorial_handoff(
        HumanInput.create(mode="tema", content="Tema", context="Contexto"), PROFILE
    )
    assert without_question["field_bindings"]["central_question"] is None
    assert without_question["field_bindings"]["context"] == "Contexto"
    assert "central_question" in without_question["unresolved_fields"]


def test_extended_user_input_round_trips_through_handoff_without_losing_exact_instruction_text() -> None:
    human = HumanInput.create(
        mode="tema",
        content="Tema",
        user_instructions=[
            {"category": "MUST_INCLUDE_VERBATIM", "text": "  Frase original, sin reescribir.  "},
            {"category": "CONTEXT_ONLY", "text": "Contexto para orientar."},
        ],
        duration_target_minutes=20,
        target_language="español",
    )
    handoff = build_editorial_handoff(human, PROFILE)
    assert human.to_dict()["user_instructions"][0]["text"] == "  Frase original, sin reescribir.  "
    assert human.to_dict()["target_language"] == "es"
    assert handoff["field_bindings"]["user_instructions"] == human.to_dict()["user_instructions"]
    assert handoff["field_bindings"]["duration_target_minutes"] == 20
    assert handoff["field_bindings"]["target_language"] == "es"
    assert validate_against_schema(human.to_dict(), "human_episode_input") == []
    assert validate_against_schema(handoff, "editorial_intake_handoff") == []


@pytest.mark.parametrize("duration", [0, -1, True, "20"])
def test_duration_is_a_positive_integer_or_none(duration: object) -> None:
    with pytest.raises(InputValidationError):
        HumanInput.create(mode="tema", content="Tema", duration_target_minutes=duration)  # type: ignore[arg-type]


def test_instruction_category_is_closed_and_text_is_required() -> None:
    with pytest.raises(InputValidationError):
        HumanInput.create(mode="tema", content="Tema", user_instructions=[{"category": "FREEFORM", "text": "x"}])
    with pytest.raises(InputValidationError):
        HumanInput.create(mode="tema", content="Tema", user_instructions=[{"category": "CONTEXT_ONLY", "text": "  "}])


def test_non_interactive_cli_adapter_captures_duration_language_and_instruction_categories() -> None:
    human = _non_interactive_input(
        Namespace(
            modo="tema",
            tema="Tema",
            obra=None,
            obras=None,
            pregunta=None,
            contexto=None,
            indicacion=["MUST_INCLUDE_VERBATIM: No cambies esta frase."],
            duracion="personalizada",
            duracion_minutos=25,
            idioma="español",
        )
    )
    assert human.user_instructions[0].category.value == "MUST_INCLUDE_VERBATIM"
    assert human.user_instructions[0].text == " No cambies esta frase."
    assert human.duration_target_minutes == 25
    assert human.target_language == "es"


def test_live_authority_parser_rejects_duplicate_and_malformed_canonical_state() -> None:
    current = ControlledB5I1Preparation.CONTROL_PATH.read_text(encoding="utf-8")
    duplicate = current.replace(
        "R2_SCOPE: B5_I1_CONTROLLED_EXECUTION",
        "R2_SCOPE: B5_I1_CONTROLLED_EXECUTION\nR2_SCOPE: REVOKED",
        1,
    )
    with pytest.raises(OperationalAuthorityError):
        resolve_operational_authority(duplicate)
    malformed = current.replace("R2_SCOPE: B5_I1_CONTROLLED_EXECUTION", "R2_SCOPE: [", 1)
    with pytest.raises(OperationalAuthorityError):
        resolve_operational_authority(malformed)


def test_pending_request_is_recovered_and_consumed_idempotently(tmp_path: Path) -> None:
    class Workflow:
        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {
                    "request_id": "REQ-ASYNC",
                    "prompt": "Decidir",
                    "options": [],
                    "recommendation": None,
                },
            }

        def resume(self, handle, human_input, handoff, decision, request):
            return {
                "status": "READY_FOR_AUTHORIZED_WORKFLOW",
                "transition": {
                    "transition_id": "TRANSITION-REQ-ASYNC",
                    "from_status": "WAITING_FOR_HUMAN_DECISION",
                    "to_status": "READY_FOR_AUTHORIZED_WORKFLOW",
                },
            }

    class Interaction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", channel=self.channel)

    workflow = Workflow()
    pending = service(tmp_path, workflow=workflow).start(HumanInput.create(mode="tema", content="Tema"))
    requests_path = pending.episode.folder / "human_decision_requests.json"
    assert json.loads(requests_path.read_text(encoding="utf-8"))["requests"][0]["status"] == "PENDING"
    recovered = service(tmp_path, workflow=workflow, interaction=Interaction()).resume(pending.episode.episode_id)
    assert recovered["state"]["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"
    resolved = json.loads(requests_path.read_text(encoding="utf-8"))
    assert resolved["requests"][0]["status"] == "RESOLVED"
    again = service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert again["state"]["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"
    transitions = json.loads((pending.episode.folder / "workflow_transitions.json").read_text(encoding="utf-8"))
    assert len(transitions["transitions"]) == 1


def test_changed_handoff_does_not_make_service_decide_subject_staleness(tmp_path: Path) -> None:
    class Workflow:
        def start(self, handle, human_input, handoff, run_id):
            return {"status": "WAITING_FOR_HUMAN_DECISION", "human_decision_request": {"request_id": "REQ-STALE", "prompt": "Decidir", "options": []}}

        def resume(self, *args):
            raise AssertionError("No debe decidir staleness un servicio agnóstico")

    workflow = Workflow()
    pending = service(tmp_path, workflow=workflow).start(HumanInput.create(mode="tema", content="Tema"))
    handoff_path = pending.episode.folder / "01_editorial_intake_handoff.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    handoff["field_bindings"]["context"] = "cambio"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    unchanged = service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert unchanged["state"]["status"] == "WAITING_FOR_HUMAN_DECISION"


@pytest.mark.parametrize("mode", ["obra", "corpus"])
def test_work_start_modes_keep_topic_pending_and_profile_resolved(mode: str) -> None:
    human = HumanInput.create(
        mode=mode,
        content="Her" if mode == "obra" else "",
        works=["Her"] if mode == "obra" else ["Her", "Lost in Translation"],
    )
    handoff = build_editorial_handoff(human, PROFILE)
    assert handoff["field_bindings"]["topic"] is None
    assert "topic" in handoff["unresolved_fields"]
    assert "profile_binding" not in handoff["unresolved_fields"]


@pytest.mark.parametrize(
    "human",
    [
        HumanInput.create(mode="tema", content="Tema"),
        HumanInput.create(mode="obra", content="Her"),
        HumanInput.create(mode="corpus", works=["Her", "Lost in Translation"]),
    ],
)
def test_service_persists_original_input_and_index(tmp_path: Path, human: HumanInput) -> None:
    result = service(tmp_path).start(human)
    assert result.episode.folder.is_dir()
    stored = json.loads((result.episode.folder / "00_human_input.json").read_text(encoding="utf-8"))
    assert stored["interaction_id"] == human.interaction_id
    index = json.loads(result.episode.index_path.read_text(encoding="utf-8"))
    assert [item["ep_id"] for item in index["episodes"]] == [result.episode.episode_id]
    assert index["episodes"][0]["application_status"] == "READY_FOR_AUTHORIZED_WORKFLOW"
    assert result.workflow["downstream_execution_started"] is False


def test_service_resumes_registered_episode(tmp_path: Path) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))
    resumed = service(tmp_path).resume(result.episode.episode_id)
    assert resumed["state"]["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"
    assert resumed["entry"]["human_input_id"]


def test_storage_failure_does_not_report_success_or_leave_registered_folder(tmp_path: Path, monkeypatch) -> None:
    from src.application import storage

    original = storage._write_json_atomic

    def fail_index(path, payload):
        if path.name == "episodes_index.json":
            raise StorageError("fallo de prueba")
        return original(path, payload)

    monkeypatch.setattr(storage, "_write_json_atomic", fail_index)
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    with pytest.raises(StorageError):
        EpisodeApplicationService(store, profile_loader=lambda: PROFILE).start(
            HumanInput.create(mode="tema", content="Tema")
        )
    assert not list((tmp_path / "vault" / "CHANNEL" / "episodios").iterdir())
    assert not store.index_path.exists()


def test_workflow_registration_rolls_back_partial_state(tmp_path: Path, monkeypatch) -> None:
    from src.application import storage

    human = HumanInput.create(mode="tema", content="Tema")
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    handoff = build_editorial_handoff(human, PROFILE)
    handle = store.create_episode(human, handoff=handoff, profile=PROFILE, run_id="RUN-1")
    original = storage._write_json_atomic
    index_writes = 0

    def fail_workflow_index(path, payload):
        nonlocal index_writes
        if path.name == "episodes_index.json":
            index_writes += 1
            if index_writes == 1:
                raise StorageError("fallo de workflow de prueba")
        return original(path, payload)

    monkeypatch.setattr(storage, "_write_json_atomic", fail_workflow_index)
    with pytest.raises(StorageError):
        store.record_workflow(handle, {"status": "READY_FOR_AUTHORIZED_WORKFLOW"})
    persisted = json.loads((handle.folder / "episode_state.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "READY_FOR_EDITORIAL_ENRICHMENT"
    assert not (handle.folder / "workflow_state.json").exists()


def test_controlled_workflow_fails_closed_when_live_scope_is_not_available(tmp_path: Path, monkeypatch) -> None:
    control = tmp_path / "control.md"
    control.write_text("R2_SCOPE: OTHER", encoding="utf-8")
    monkeypatch.setattr(ControlledB5I1Preparation, "CONTROL_PATH", control)
    with pytest.raises(PermissionError):
        service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))
    assert not (tmp_path / "vault" / "CHANNEL" / "episodios").exists()


def test_controlled_workflow_ignores_a_later_revocation_outside_canonical_state(tmp_path: Path, monkeypatch) -> None:
    control = tmp_path / "control.md"
    current = ControlledB5I1Preparation.CONTROL_PATH.read_text(encoding="utf-8")
    control.write_text(current + "\nR2_CONTROLLED_EXECUTION: REVOKED\n", encoding="utf-8")
    monkeypatch.setattr(ControlledB5I1Preparation, "CONTROL_PATH", control)
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))
    assert result.workflow["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"


def test_authority_uses_only_canonical_state_for_allow_and_block() -> None:
    current = ControlledB5I1Preparation.CONTROL_PATH.read_text(encoding="utf-8")
    assert resolve_operational_authority(current + "\nR2_CONTROLLED_EXECUTION: AUTHORIZED\n").values["R2_STATUS"] == "AUTHORIZED_CONTROLLED_B5_I1_NOT_EXECUTED"
    assert resolve_operational_authority(current + "\nR2_CONTROLLED_EXECUTION: REVOKED\n").values["R2_STATUS"] == "AUTHORIZED_CONTROLLED_B5_I1_NOT_EXECUTED"
    canonical_revoked = current.replace("R2_CONTROLLED_EXECUTION: AUTHORIZED", "R2_CONTROLLED_EXECUTION: REVOKED", 1)
    with pytest.raises(PermissionError):
        resolve_operational_authority(canonical_revoked)
    historical_only = current.replace("R2_CONTROLLED_EXECUTION: AUTHORIZED", "R2_CONTROLLED_EXECUTION: NONE", 1)
    with pytest.raises(PermissionError):
        resolve_operational_authority(historical_only)


def test_controlled_workflow_rejects_multiline_authority_assignments(tmp_path: Path, monkeypatch) -> None:
    control = tmp_path / "control.md"
    current = ControlledB5I1Preparation.CONTROL_PATH.read_text(encoding="utf-8")
    control.write_text(
        current.replace("R2_SCOPE: B5_I1_CONTROLLED_EXECUTION", "R2_SCOPE:\nB5_I1_CONTROLLED_EXECUTION"),
        encoding="utf-8",
    )
    monkeypatch.setattr(ControlledB5I1Preparation, "CONTROL_PATH", control)
    with pytest.raises(PermissionError):
        service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))


def test_application_core_works_without_terminal(tmp_path: Path) -> None:
    class FakeWorkflow:
        def start(self, handle, human_input, handoff, run_id):
            return {"status": "READY_FOR_AUTHORIZED_WORKFLOW", "episode_id": handle.episode_id}

    result = service(tmp_path, workflow=FakeWorkflow()).start(HumanInput.create(mode="tema", content="Tema"))
    assert result.workflow["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"


def test_workflow_requests_are_consumed_and_decisions_capture_the_full_request(tmp_path: Path) -> None:
    class RequestingWorkflow:
        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {
                    "request_id": "REQ-WORKFLOW",
                    "prompt": "Selecciona una opción",
                    "options": [{"id": "one", "label": "Una propuesta"}, {"id": "two", "label": "Otra propuesta"}],
                    "recommendation": "two",
                },
            }

        def resume(self, handle, human_input, handoff, decision, request):
            return {
                "status": "READY_FOR_AUTHORIZED_WORKFLOW",
                "human_decision": decision,
                "transition": {
                    "transition_id": "TRANSITION-REQ-WORKFLOW",
                    "from_status": "WAITING_FOR_HUMAN_DECISION",
                    "to_status": "READY_FOR_AUTHORIZED_WORKFLOW",
                    "consequence": "TEST_DECISION_CONSUMED",
                },
            }

    class FakeInteraction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "SELECT_ALTERNATIVE", selected_option="two", channel=self.channel)

    result = service(tmp_path, workflow=RequestingWorkflow(), interaction=FakeInteraction()).start(
        HumanInput.create(mode="tema", content="Tema")
    )
    request = json.loads((result.episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))
    assert request["requests"][0]["prompt"] == "Selecciona una opción"
    assert request["requests"][0]["options"] == [
        {"id": "one", "label": "Una propuesta"},
        {"id": "two", "label": "Otra propuesta"},
    ]
    saved = json.loads((result.episode.folder / "human_decisions.json").read_text(encoding="utf-8"))
    assert "request" not in saved["decisions"][0]
    assert saved["decisions"][0]["request_checksum"] == request["requests"][0]["request_checksum"]
    assert result.workflow["human_decision"]["action"] == "SELECT_ALTERNATIVE"


def test_interactive_and_non_interactive_adapters_share_normalized_fields(monkeypatch) -> None:
    responses = iter(["1", "Tema", "Pregunta", "", "n", "1", "1", "s"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    interactive = _interactive_input()
    non_interactive = _non_interactive_input(
        Namespace(modo="tema", tema="Tema", obra=None, obras=None, pregunta="Pregunta", contexto=None)
    )
    assert interactive.mode == non_interactive.mode
    assert interactive.content == non_interactive.content
    assert interactive.initial_question == non_interactive.initial_question
    assert interactive.context == non_interactive.context
    assert interactive.works == non_interactive.works
    assert interactive.user_instructions == ()
    assert interactive.duration_target_minutes is None
    assert interactive.target_language is None


def test_interactive_input_captures_zero_or_more_instructions_custom_duration_and_other_language(monkeypatch) -> None:
    responses = iter(
        [
            "1", "Tema", "", "", "s", "4", "  Mantener esta frase exactamente.  ",
            "n", "6", "27", "4", "Français",
            "s",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    human = _interactive_input()
    assert human.user_instructions[0].category.value == "MUST_INCLUDE_VERBATIM"
    assert human.user_instructions[0].text == "Mantener esta frase exactamente."
    assert human.duration_target_minutes == 27
    assert human.target_language == "Français"


@pytest.mark.parametrize(
    ("duration_option", "duration_minutes", "language_option", "expected_message"),
    [
        ("6", "", "1", "respuesta no puede estar vacía"),
        ("1", "", "4", "respuesta no puede estar vacía"),
    ],
)
def test_interactive_input_rejects_missing_custom_duration_or_other_language(
    monkeypatch, duration_option: str, duration_minutes: str, language_option: str, expected_message: str
) -> None:
    responses = iter(["1", "Tema", "", "", "n", duration_option, duration_minutes])
    if language_option == "4":
        responses = iter(["1", "Tema", "", "", "n", duration_option, language_option, ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    with pytest.raises(ValueError, match=expected_message):
        _interactive_input()


def test_active_mission_bundle_requires_an_explicit_canonical_pointer(tmp_path: Path) -> None:
    control_path = tmp_path / "control.md"
    control = ControlledB5I1Preparation.CONTROL_PATH.read_text(encoding="utf-8")
    control_path.write_text(control.replace("CURRENT_MISSION: NONE", "CURRENT_MISSION: TEST_ACTIVE_MISSION"), encoding="utf-8")
    with pytest.raises(OperationalAuthorityError, match="ACTIVE_MISSION_EXECUTION_BUNDLE_REQUIRED"):
        resolve_active_mission_bundle(
            control_path,
            repository_root=tmp_path,
        )


def _temporary_entrypoint_repository(tmp_path: Path) -> tuple[Path, Path, str]:
    repo = tmp_path / "entrypoint-repo"
    for relative in (
        "src", "config", "docs/legacy", "policies", "prompts", "profiles/editorial", "schemas", ".agent/skills"
    ):
        shutil.copytree(ROOT / relative, repo / relative, ignore=shutil.ignore_patterns("__pycache__"))
    (repo / "plans").mkdir()
    (repo / "plans/001_CONTROL_OPERATIVO.md").write_text(
        (ROOT / "plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    mission_id = "PLAN009_ENTRYPOINT_TEMPORARY_MISSION"
    contract_ref = "plans/entrypoint_test/mission_contract.json"
    bundle_root = repo / "plans/entrypoint_test"
    bundle_root.mkdir(parents=True)
    control_path = repo / "plans/001_CONTROL_OPERATIVO.md"
    control = control_path.read_text(encoding="utf-8")
    current_line = next(line for line in control.splitlines() if line.startswith("CURRENT_MISSION:"))
    control = control.replace(current_line, f"CURRENT_MISSION: {mission_id}")
    control = control.replace("CURRENT_MISSION_EXECUTION_BUNDLE: NONE", f"CURRENT_MISSION_EXECUTION_BUNDLE: {contract_ref}")
    control_path.write_text(control, encoding="utf-8")

    authority_ref = "plans/entrypoint_test/authority.json"
    authorization_ref = "plans/entrypoint_test/mission-authorization.json"
    scope = {
        "mission_id": mission_id,
        "capability_ids": ["TOPIC_BELONGING_ASSESSMENT"],
        "role_ids": ["CHANNEL_INTELLIGENCE_PRODUCER", "CHANNEL_INTELLIGENCE_REVIEWER"],
        "execution_profile_ids": [],
        "execution_family_ids": ["AGENT_HARNESS"],
        "execution_interface": "TOPIC_BELONGING_TERMINAL",
        "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": ["handoff/", "output/"],
        "allowed_routes": ["agent_harness"],
        "execution_mode": "REAL",
        "live_state_sha256": sha256_file(control_path),
        "contains_material_repair": False,
        "repair_integrity_evidence_path": "NONE",
    }
    material_registry = json.loads((repo / "docs/legacy/material_decision_registry.json").read_text(encoding="utf-8"))
    material = next(item for item in material_registry["decisions"] if item["decision_id"] == "MD-CI-001")
    authority = {
        "mission_id": mission_id,
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
    authority_path = repo / authority_ref
    authority_path.write_text(json.dumps(authority, ensure_ascii=False), encoding="utf-8")
    authorization = {
        "mission_id": mission_id,
        "authorization": {
            **scope,
            "live_state_path": "plans/001_CONTROL_OPERATIVO.md",
            "authority_ref": authority_ref,
            "authority_sha256": sha256_file(authority_path),
            "authorized_scope_sha256": scope_checksum(scope),
            "single_use": False,
            "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
        },
    }
    (repo / authorization_ref).write_text(json.dumps(authorization, ensure_ascii=False), encoding="utf-8")
    contract = {
        "mission_id": mission_id,
        "mission_mode": "LEGACY",
        "artifact_id": mission_id,
        "artifact_version": "1.0.0",
        "authorized_paths": ["handoff/", "output/"],
        "protected_untracked_paths": [],
        "protected_untracked_baseline": [],
        "required_tests": [],
        "push_allowed": False,
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "0" * 40},
        "contains_material_repair": False,
        "mission_authorization_path": authorization_ref,
        "state_requirements": {
            "control_path": "plans/001_CONTROL_OPERATIVO.md",
            "required": {"CURRENT_MISSION": mission_id},
            "forbidden": {},
        },
        "schema_checks": [],
    }
    (repo / contract_ref).write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
    settings = tmp_path / "entrypoint-settings.json"
    settings.write_text(json.dumps({"vault_root": str(tmp_path / "vault"), "channel_id": "CHANNEL"}), encoding="utf-8")
    (repo / "config/local_settings.json").write_text(settings.read_text(encoding="utf-8"), encoding="utf-8")
    return repo, settings, mission_id


def test_cli_public_entrypoint_resolves_temporary_active_bundle_and_reaches_handoff(tmp_path: Path) -> None:
    repo, _, mission_id = _temporary_entrypoint_repository(tmp_path)
    bundle = resolve_active_mission_bundle(repo / "plans/001_CONTROL_OPERATIVO.md", repository_root=repo)
    assert bundle.mission_id == mission_id
    assert bundle.mission_contract_path == "plans/entrypoint_test/mission_contract.json"
    completed = subprocess.run(
        [sys.executable, "-m", "src.cli", "iniciar"],
        cwd=repo,
        input="1\nTema de entrada\nPregunta concreta\nContexto\ns\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    output = completed.stdout
    assert "Primer handoff de Topic Belonging preparado" in output
    assert "MISSION_AUTHORIZATION" not in output
    episodes = list((tmp_path / "vault/CHANNEL/episodios").iterdir())
    assert len(episodes) == 1
    workflow = json.loads((episodes[0] / "workflow_state.json").read_text(encoding="utf-8"))
    assert workflow["status"] == "PENDING_EXTERNAL_RESULT"
    episode_state = json.loads((episodes[0] / "episode_state.json").read_text(encoding="utf-8"))
    assert episode_state["mission_id"] == mission_id
    assert (repo / "handoff").is_dir()


def test_active_mission_bundle_rejects_a_contract_for_another_mission(tmp_path: Path) -> None:
    repo, _, _ = _temporary_entrypoint_repository(tmp_path)
    contract_path = repo / "plans/entrypoint_test/mission_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["mission_id"] = "OTHER_MISSION"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(OperationalAuthorityError, match="ACTIVE_MISSION_EXECUTION_BUNDLE_MISSION_MISMATCH"):
        resolve_active_mission_bundle(repo / "plans/001_CONTROL_OPERATIVO.md", repository_root=repo)


def test_cli_non_interactive_runs_the_same_application_service(tmp_path: Path, capsys) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps({"vault_root": str(tmp_path / "vault"), "channel_id": "CHANNEL"}),
        encoding="utf-8",
    )
    assert main(
        [
            "iniciar",
            "--config",
            str(settings),
            "--modo",
            "tema",
            "--tema",
            "Tema automatizable",
        ]
    ) == 2
    assert "NO_ACTIVE_CURRENT_MISSION" in capsys.readouterr().out


def test_human_decision_is_normalized_and_persisted(tmp_path: Path) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))

    class FakeInteraction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "SELECT_ALTERNATIVE", selected_option="two", channel=self.channel)

    decision = service(tmp_path).request_human_decision(
        result.episode.episode_id,
        DecisionRequest("REQ-1", "Elige", ({"id": "one", "label": "Uno"}, {"id": "two", "label": "Dos"})),
        FakeInteraction(),
    )
    assert decision.action == "SELECT_ALTERNATIVE"
    saved = json.loads((result.episode.folder / "human_decisions.json").read_text(encoding="utf-8"))
    assert saved["decisions"][0]["action"] == "SELECT_ALTERNATIVE"
    requests = json.loads((result.episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))
    assert requests["requests"][0]["options"][1]["label"] == "Dos"
    assert saved["decisions"][0]["request_checksum"] == requests["requests"][0]["request_checksum"]


@pytest.mark.parametrize(
    "decision",
    [
        HumanDecision("OTHER-REQUEST", "APPROVE"),
        HumanDecision("REQ-1", "SELECT_ALTERNATIVE", selected_option="missing"),
    ],
)
def test_invalid_adapter_decision_is_not_persisted(tmp_path: Path, decision: HumanDecision) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))

    class InvalidInteraction:
        channel = "FAKE"

        def decide(self, request):
            return decision

    with pytest.raises(ValueError):
        service(tmp_path).request_human_decision(
            result.episode.episode_id,
            DecisionRequest("REQ-1", "Elige", ({"id": "one", "label": "Uno"},)),
            InvalidInteraction(),
        )
    assert not (result.episode.folder / "human_decisions.json").exists()


def test_legacy_wrapper_storage_record_is_technical_only(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    store.channel_path.mkdir(parents=True)
    handle = store.create_legacy_episode(episode_number=1, slug="identificador_tecnico")
    assert not (handle.folder / "00_human_input.json").exists()
    state = json.loads((handle.folder / "episode_state.json").read_text(encoding="utf-8"))
    assert state["editorial_input_registered"] is False
    index = json.loads(handle.index_path.read_text(encoding="utf-8"))
    assert index["episodes"][0]["entry_mode"] is None
    assert index["episodes"][0]["input_origin"] == "LEGACY_SCRIPT_TECHNICAL"


def test_legacy_storage_requires_gate0_channel_preparation(tmp_path: Path) -> None:
    with pytest.raises(StorageError, match="Gate 0"):
        VaultEpisodeStore(tmp_path / "vault", "CHANNEL").create_legacy_episode(
            episode_number=1, slug="identificador_tecnico"
        )


def test_cancelled_decision_is_persisted_before_control_returns(tmp_path: Path) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))

    class CancelledInteraction:
        channel = "FAKE"

        def decide(self, request):
            raise UserCancelled

    with pytest.raises(UserCancelled):
        service(tmp_path).request_human_decision(
            result.episode.episode_id,
            DecisionRequest("REQ-CANCEL", "Decidir"),
            CancelledInteraction(),
        )
    saved = json.loads((result.episode.folder / "human_decisions.json").read_text(encoding="utf-8"))
    assert saved["decisions"][0]["action"] == "CANCEL"


def test_expected_actor_and_channel_are_enforced_before_persistence(tmp_path: Path) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))

    class Interaction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", actor_ref="mallory", channel=self.channel)

    request = DecisionRequest(
        "REQ-IDENTITY",
        "Aprobar",
        episode_id=result.episode.episode_id,
        expected_actor_ref="alice",
        expected_channel="TELEGRAM",
    )
    with pytest.raises(PermissionError):
        service(tmp_path).request_human_decision(result.episode.episode_id, request, Interaction())
    assert not (result.episode.folder / "human_decisions.json").exists()


def test_expected_channel_is_enforced_independently(tmp_path: Path) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))

    class Interaction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", actor_ref="alice", channel=self.channel)

    request = DecisionRequest(
        "REQ-CHANNEL",
        "Aprobar",
        episode_id=result.episode.episode_id,
        expected_actor_ref="alice",
        expected_channel="TELEGRAM",
    )
    with pytest.raises(PermissionError, match="canal"):
        service(tmp_path).request_human_decision(result.episode.episode_id, request, Interaction())


def test_expected_actor_is_enforced_independently(tmp_path: Path) -> None:
    result = service(tmp_path).start(HumanInput.create(mode="tema", content="Tema"))

    class Interaction:
        channel = "TELEGRAM"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", actor_ref="mallory", channel=self.channel)

    request = DecisionRequest(
        "REQ-ACTOR",
        "Aprobar",
        episode_id=result.episode.episode_id,
        expected_actor_ref="alice",
        expected_channel="TELEGRAM",
    )
    with pytest.raises(PermissionError, match="actor"):
        service(tmp_path).request_human_decision(result.episode.episode_id, request, Interaction())


def test_non_handoff_subject_is_delegated_to_workflow_for_staleness(tmp_path: Path) -> None:
    class Workflow:
        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {
                    "request_id": "REQ-CUSTOM-SUBJECT",
                    "prompt": "Aprobar tesis",
                    "options": [],
                    "subject_ref": "custom:thesis:1",
                    "subject_version": "2",
                    "subject_checksum": "b" * 64,
                },
            }

        def resume(self, handle, human_input, handoff, decision, request):
            assert request["subject_ref"] == "custom:thesis:1"
            assert request["subject_checksum"] == "b" * 64
            return {
                "status": "READY_FOR_AUTHORIZED_WORKFLOW",
                "transition": {
                    "transition_id": "TRANSITION-CUSTOM-SUBJECT",
                    "from_status": "WAITING_FOR_HUMAN_DECISION",
                    "to_status": "READY_FOR_AUTHORIZED_WORKFLOW",
                },
            }

    class Interaction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", channel=self.channel)

    workflow = Workflow()
    pending = service(tmp_path, workflow=workflow).start(HumanInput.create(mode="tema", content="Tema"))
    resumed = service(tmp_path, workflow=workflow, interaction=Interaction()).resume(pending.episode.episode_id)
    assert resumed["state"]["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"


def test_workflow_owns_stale_subject_decision(tmp_path: Path) -> None:
    class Workflow:
        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {
                    "request_id": "REQ-WORKFLOW-STALE",
                    "prompt": "Aprobar tesis",
                    "options": [],
                    "subject_ref": "custom:thesis:2",
                    "subject_version": "3",
                    "subject_checksum": "c" * 64,
                },
            }

        def resume(self, *args):
            raise WorkflowDecisionStale("CUSTOM_SUBJECT_CHANGED")

    class Interaction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", channel=self.channel)

    workflow = Workflow()
    pending = service(tmp_path, workflow=workflow).start(HumanInput.create(mode="tema", content="Tema"))
    with pytest.raises(WorkflowDecisionStale):
        service(tmp_path, workflow=workflow, interaction=Interaction()).resume(pending.episode.episode_id)
    assert json.loads((pending.episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))["requests"][0]["status"] == "STALE"
    assert json.loads((pending.episode.folder / "episode_state.json").read_text(encoding="utf-8"))["status"] == "STALE_REQUEST"


def _prepare_persisted_decision_case(tmp_path: Path):
    class Workflow:
        def __init__(self):
            self.resume_calls = 0

        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {
                    "request_id": "REQ-PERSISTED",
                    "prompt": "Aprobar",
                    "options": [{"id": "one", "label": "Una"}],
                    "expected_actor_ref": "alice",
                    "expected_channel": "TELEGRAM",
                },
            }

        def resume(self, *args):
            self.resume_calls += 1
            return {
                "status": "READY_FOR_AUTHORIZED_WORKFLOW",
                "transition": {
                    "transition_id": "TRANSITION-PERSISTED",
                    "from_status": "WAITING_FOR_HUMAN_DECISION",
                    "to_status": "READY_FOR_AUTHORIZED_WORKFLOW",
                },
            }

    workflow = Workflow()
    pending = service(tmp_path, workflow=workflow).start(HumanInput.create(mode="tema", content="Tema"))
    request_data = json.loads((pending.episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))["requests"][0]
    request = DecisionRequest.from_dict(request_data, require_contract=True)
    decision = HumanDecision(
        request.request_id,
        "SELECT_ALTERNATIVE",
        selected_option="one",
        actor_ref="alice",
        channel="TELEGRAM",
    ).bind_request(request).to_dict()
    decision_path = pending.episode.folder / "human_decisions.json"
    decision_path.write_text(json.dumps({"decisions": [decision]}), encoding="utf-8")
    return pending, workflow, decision_path


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor_ref", "mallory"),
        ("channel", "FAKE"),
        ("request_checksum", "a" * 64),
        ("episode_id", "ep_9999"),
        ("request_id", "REQ-OTHER"),
        ("selected_option", "missing"),
        ("action", "DO_WHATEVER"),
        ("occurred_at", "not-a-date"),
        ("correction", ["not", "text"]),
    ],
)
def test_recovery_revalidates_persisted_decision_before_workflow(
    tmp_path: Path, field: str, value: str
) -> None:
    pending, workflow, decision_path = _prepare_persisted_decision_case(tmp_path)
    decision_data = json.loads(decision_path.read_text(encoding="utf-8"))["decisions"][0]
    decision_data[field] = value
    decision_path.write_text(json.dumps({"decisions": [decision_data]}), encoding="utf-8")
    with pytest.raises((ValueError, PermissionError)):
        service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert workflow.resume_calls == 0
    assert not (pending.episode.folder / "workflow_transitions.json").exists()


def test_recovery_rejects_unknown_persisted_decision_field(tmp_path: Path) -> None:
    pending, workflow, decision_path = _prepare_persisted_decision_case(tmp_path)
    decision_data = json.loads(decision_path.read_text(encoding="utf-8"))["decisions"][0]
    decision_data["unexpected"] = "not part of the contract"
    decision_path.write_text(json.dumps({"decisions": [decision_data]}), encoding="utf-8")
    with pytest.raises(ValueError):
        service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert workflow.resume_calls == 0


def test_recovery_valid_persisted_decision_reaches_workflow_once(tmp_path: Path) -> None:
    pending, workflow, _ = _prepare_persisted_decision_case(tmp_path)
    resumed = service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert resumed["state"]["status"] == "READY_FOR_AUTHORIZED_WORKFLOW"
    assert workflow.resume_calls == 1


def test_recovery_rejects_persisted_request_without_checksum(tmp_path: Path) -> None:
    pending, workflow, _ = _prepare_persisted_decision_case(tmp_path)
    request_path = pending.episode.folder / "human_decision_requests.json"
    request_data = json.loads(request_path.read_text(encoding="utf-8"))
    request_data["requests"][0].pop("request_checksum")
    request_path.write_text(json.dumps(request_data), encoding="utf-8")
    resumed = service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert resumed["state"]["status"] == "STALE_REQUEST"
    assert workflow.resume_calls == 0


def test_synchronous_stale_is_not_wrapped_as_storage_error(tmp_path: Path) -> None:
    class Workflow:
        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {"request_id": "REQ-SYNC-STALE", "prompt": "Aprobar", "options": []},
            }

        def resume(self, *args):
            raise WorkflowDecisionStale("SYNC_SUBJECT_CHANGED")

    class Interaction:
        channel = "FAKE"

        def decide(self, request):
            return HumanDecision(request.request_id, "APPROVE", channel=self.channel)

    with pytest.raises(WorkflowDecisionStale):
        service(tmp_path, workflow=Workflow(), interaction=Interaction()).start(
            HumanInput.create(mode="tema", content="Tema")
        )


def test_resume_rechecks_workflow_authority_before_consuming_pending_request(tmp_path: Path) -> None:
    class Workflow:
        def __init__(self):
            self.revoked = False
            self.resume_calls = 0

        def preflight(self):
            if self.revoked:
                raise PermissionError("autoridad revocada")

        def start(self, handle, human_input, handoff, run_id):
            return {
                "status": "WAITING_FOR_HUMAN_DECISION",
                "human_decision_request": {"request_id": "REQ-REVOKED", "prompt": "Aprobar", "options": []},
            }

        def resume(self, *args):
            self.resume_calls += 1
            raise AssertionError("resume no debe ejecutarse con autoridad revocada")

    workflow = Workflow()
    pending = service(tmp_path, workflow=workflow).start(HumanInput.create(mode="tema", content="Tema"))
    workflow.revoked = True
    with pytest.raises(PermissionError):
        service(tmp_path, workflow=workflow).resume(pending.episode.episode_id)
    assert workflow.resume_calls == 0


def test_same_request_cannot_register_two_different_transitions(tmp_path: Path) -> None:
    store = VaultEpisodeStore(tmp_path / "vault", "CHANNEL")
    result = EpisodeApplicationService(store, profile_loader=lambda: PROFILE).start(
        HumanInput.create(mode="tema", content="Tema")
    )
    request = DecisionRequest("REQ-ONCE", "Aprobar", episode_id=result.episode.episode_id)
    store.record_decision_request(result.episode.episode_id, request.to_dict())
    decision = HumanDecision("REQ-ONCE", "APPROVE", episode_id=result.episode.episode_id).bind_request(request)
    store.record_decision(result.episode.episode_id, decision.to_dict())
    store.record_workflow_transition(result.episode.episode_id, {"request_id": "REQ-ONCE", "transition_id": "T1"})
    with pytest.raises(StorageError):
        store.record_workflow_transition(result.episode.episode_id, {"request_id": "REQ-ONCE", "transition_id": "T2"})


def test_request_persistence_is_serialized_across_store_instances(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    store = VaultEpisodeStore(root, "CHANNEL")
    result = EpisodeApplicationService(store, profile_loader=lambda: PROFILE).start(
        HumanInput.create(mode="tema", content="Tema")
    )
    request = DecisionRequest("REQ-CONCURRENT", "Aprobar", episode_id=result.episode.episode_id).to_dict()

    def persist_once() -> dict:
        return VaultEpisodeStore(root, "CHANNEL").record_decision_request(result.episode.episode_id, request)

    with ThreadPoolExecutor(max_workers=2) as executor:
        persisted = list(executor.map(lambda _: persist_once(), range(2)))
    assert persisted[0]["request_checksum"] == persisted[1]["request_checksum"]
    saved = json.loads((result.episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))
    assert len(saved["requests"]) == 1


def test_request_persistence_is_serialized_across_processes(tmp_path: Path) -> None:
    import multiprocessing

    root = tmp_path / "vault"
    store = VaultEpisodeStore(root, "CHANNEL")
    result = EpisodeApplicationService(store, profile_loader=lambda: PROFILE).start(
        HumanInput.create(mode="tema", content="Tema")
    )
    request = DecisionRequest("REQ-PROCESS", "Aprobar", episode_id=result.episode.episode_id).to_dict()
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    processes = [
        context.Process(
            target=_persist_request_worker,
            args=(str(root), result.episode.episode_id, request, result_queue),
        )
        for _ in range(2)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)
    assert [process.exitcode for process in processes] == [0, 0]
    results = [result_queue.get(timeout=5) for _ in processes]
    assert all(status == "ok" for status, _ in results), results
    assert len(json.loads((result.episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))["requests"]) == 1


def test_human_input_legacy_1_0_without_initial_question_remains_compatible() -> None:
    legacy = HumanInput.create(mode="tema", content="Tema", context="Contexto").to_dict()
    legacy.pop("initial_question")
    assert validate_against_schema(legacy, "human_episode_input") == []
    restored = HumanInput.from_dict(legacy)
    assert restored.initial_question is None
    assert restored.context == "Contexto"


def test_human_input_legacy_processing_status_round_trips() -> None:
    legacy = HumanInput.create(mode="tema", content="Tema", context="Contexto").to_dict()
    legacy.pop("initial_question")
    legacy["processing_status"] = "READY"
    restored = HumanInput.from_dict(legacy)
    assert restored.processing_status == "READY"


@pytest.mark.parametrize("status", ["RECEIVED", "REGISTERED", "READY", "CANCELLED"])
def test_processing_status_accepts_schema_vocabulary(status: str) -> None:
    human = HumanInput.create(mode="tema", content="Tema", processing_status=status)
    assert HumanInput.from_dict(human.to_dict()).processing_status == status


@pytest.mark.parametrize("status", ["BOGUS", "", "UNKNOWN"])
def test_processing_status_rejects_unknown_values(status: str) -> None:
    with pytest.raises(InputValidationError):
        HumanInput.create(mode="tema", content="Tema", processing_status=status)


def test_human_input_direct_constructor_rejects_unknown_processing_status() -> None:
    with pytest.raises(InputValidationError):
        HumanInput(
            interaction_id="INT-1",
            occurred_at="2026-08-22T00:00:00Z",
            channel="TERMINAL",
            mode=EntryMode.TOPIC_FIRST,
            content="Tema",
            processing_status="UNKNOWN",
        )
