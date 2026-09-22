from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from src.application.interaction import HumanDecision, HumanDecisionRequest
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError
from src.cli import main
from tests.harness.test_plan015_hf02 import _outputs, _service


@dataclass
class _FinalDecisionInteraction:
    action: str = "APPROVE"
    actor_ref: str = "editor_jefe_01"
    correction: str | None = None
    channel: str = "TERMINAL"

    def decide(self, request: HumanDecisionRequest) -> HumanDecision:
        return HumanDecision(
            request.request_id,
            self.action,
            correction=self.correction,
            actor_ref=self.actor_ref,
            channel=self.channel,
        )


def _approval_service(base: EpisodeApplicationService, interaction: _FinalDecisionInteraction) -> EpisodeApplicationService:
    return EpisodeApplicationService(
        base.store,
        workflow=base.workflow,
        synthetic_outputs=_outputs(),
        interaction=interaction,
        editorial_approval_actor_ref="editor_jefe_01",
        editorial_approval_role="EDITORIAL_LEAD",
    )


def test_plan015_hf03_materializes_exact_approval_closure_and_current(tmp_path) -> None:
    service, episode = _service(tmp_path)
    assert service.resume(episode.episode_id)["state"]["status"] == "LEGITIMATE_STOP"

    result = _approval_service(service, _FinalDecisionInteraction()).resume(episode.episode_id)

    approval = json.loads((episode.folder / "editorial_script_approval.json").read_text(encoding="utf-8"))
    approved_current = json.loads((episode.folder / "approved_current.json").read_text(encoding="utf-8"))
    closure = json.loads((episode.folder / "plan013_editorial_closure.json").read_text(encoding="utf-8"))
    versions = json.loads((episode.folder / "plan013_script_versions.json").read_text(encoding="utf-8"))
    requests = json.loads((episode.folder / "human_decision_requests.json").read_text(encoding="utf-8"))

    assert result["state"]["status"] == "EDITORIAL_SCRIPT_APPROVED"
    assert result["state"]["approved_current"] == approved_current
    assert approval["approved_by"] == "editor_jefe_01"
    assert approval["approved_role"] == "EDITORIAL_LEAD"
    assert closure["human_approval"] == approval
    assert closure["approved_current"] == approved_current
    assert requests["requests"][0]["expected_actor_ref"] == "editor_jefe_01"
    assert requests["requests"][0]["expected_approval_role"] == "EDITORIAL_LEAD"
    approved_versions = [item for item in versions["versions"] if item["status"] == "APPROVED_CURRENT"]
    assert len(approved_versions) == 1
    assert approved_versions[0]["script_artifact_id"] == approved_current["artifact_id"]
    assert approved_versions[0]["script_version"] == approved_current["script_version"]
    assert approved_versions[0]["script_checksum"] == approved_current["checksum"]

    repeated = _approval_service(service, _FinalDecisionInteraction()).resume(episode.episode_id)
    assert repeated["state"]["approved_current"] == approved_current


def test_plan015_hf03_rejects_wrong_actor_without_materializing_approval(tmp_path) -> None:
    service, episode = _service(tmp_path)
    service.resume(episode.episode_id)

    with pytest.raises(PermissionError, match="actor esperado"):
        _approval_service(
            service,
            _FinalDecisionInteraction(actor_ref="editor_jefe_editorial_01"),
        ).resume(episode.episode_id)

    assert not (episode.folder / "editorial_script_approval.json").exists()
    assert not (episode.folder / "approved_current.json").exists()
    assert not (episode.folder / "plan013_editorial_closure.json").exists()


def test_plan015_hf03_rejects_unauthorized_role_without_materializing_approval(tmp_path) -> None:
    service, episode = _service(tmp_path)
    service.resume(episode.episode_id)
    invalid = EpisodeApplicationService(
        service.store,
        workflow=service.workflow,
        synthetic_outputs=_outputs(),
        interaction=_FinalDecisionInteraction(),
        editorial_approval_actor_ref="editor_jefe_01",
        editorial_approval_role="PRODUCTION_LEAD",
    )

    with pytest.raises(StorageError, match="PLAN015_EDITORIAL_APPROVAL_INVALID"):
        invalid.resume(episode.episode_id)

    assert not (episode.folder / "editorial_script_approval.json").exists()
    assert not (episode.folder / "approved_current.json").exists()
    assert not (episode.folder / "plan013_editorial_closure.json").exists()


def test_plan015_hf03_correction_never_creates_approval_or_closure(tmp_path) -> None:
    service, episode = _service(tmp_path)
    service.resume(episode.episode_id)

    result = _approval_service(
        service,
        _FinalDecisionInteraction(action="CORRECT", correction="Reformular el cierre."),
    ).resume(episode.episode_id)

    workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
    assert result["state"]["status"] == "IN_REVIEW"
    assert workflow["human_correction"] == "Reformular el cierre."
    assert not (episode.folder / "editorial_script_approval.json").exists()
    assert not (episode.folder / "approved_current.json").exists()
    assert not (episode.folder / "plan013_editorial_closure.json").exists()


def test_plan015_working_version_preserves_unique_approved_current_and_history(tmp_path) -> None:
    service, episode = _service(tmp_path)
    service.resume(episode.episode_id)
    _approval_service(service, _FinalDecisionInteraction()).resume(episode.episode_id)
    approved_before = json.loads((episode.folder / "approved_current.json").read_text(encoding="utf-8"))

    service.store.register_plan013_script_version(
        episode,
        script_artifact_id="SCRIPT-WORKING-NEXT",
        script_version="2.0.0",
        script_checksum="d" * 64,
    )

    resumed = service.store.resume(episode.episode_id)
    closure = json.loads((episode.folder / "plan013_editorial_closure.json").read_text(encoding="utf-8"))
    versions = json.loads((episode.folder / "plan013_script_versions.json").read_text(encoding="utf-8"))["versions"]
    assert resumed["state"]["status"] == "IN_REVIEW"
    assert resumed["state"]["approved_current"] == approved_before
    assert resumed["state"]["current_script"]["status"] == "WORKING_CURRENT"
    assert closure["status"] == "EDITORIAL_SCRIPT_APPROVED"
    assert len([item for item in versions if item["status"] == "APPROVED_CURRENT"]) == 1
    assert len([item for item in versions if item["status"] == "WORKING_CURRENT"]) == 1


def test_plan015_ambiguous_version_history_fails_closed_before_current(tmp_path) -> None:
    service, episode = _service(tmp_path)
    service.resume(episode.episode_id)
    versions_path = episode.folder / "plan013_script_versions.json"
    versions = json.loads(versions_path.read_text(encoding="utf-8"))
    versions["versions"].append(dict(versions["versions"][-1]))
    versions_path.write_text(json.dumps(versions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(StorageError, match="PLAN015_APPROVED_CURRENT_IDENTITY_AMBIGUOUS"):
        _approval_service(service, _FinalDecisionInteraction()).resume(episode.episode_id)

    assert not (episode.folder / "editorial_script_approval.json").exists()
    assert not (episode.folder / "approved_current.json").exists()


def test_plan015_hf03_cli_surface_approves_and_displays_exact_current(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    service, episode = _service(tmp_path)
    service.resume(episode.episode_id)
    settings = tmp_path / "local_settings.json"
    settings.write_text(
        json.dumps({"vault_root": str(service.store.vault_root), "channel_id": service.store.channel_id}),
        encoding="utf-8",
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "A")

    exit_code = main(
        [
            "reanudar",
            episode.episode_id,
            "--config",
            str(settings),
            "--approval-actor",
            "editor_jefe_01",
            "--approval-role",
            "EDITORIAL_LEAD",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Estado: EDITORIAL_SCRIPT_APPROVED" in output
    assert "Guion aprobado CURRENT:" in output
    assert "SCRIPT-EDITED-" in output
