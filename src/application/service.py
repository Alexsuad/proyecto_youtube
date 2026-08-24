"""Application orchestration without editorial or channel-specific rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.application.contracts import HumanInput
from src.application.handoff import build_editorial_handoff
from src.application.interaction import (
    DecisionRequest,
    HumanDecision,
    HumanInteraction,
    UserCancelled,
    validate_human_decision,
)
from src.application.storage import EpisodeHandle, StorageError, VaultEpisodeStore
from src.application.workflow import ControlledB5I1Preparation, WorkflowCoordinator, WorkflowDecisionStale
from src.core.editorial_profile_registry import load_active_profile_authority


@dataclass(frozen=True)
class IntakeResult:
    episode: EpisodeHandle
    handoff: dict[str, Any]
    workflow: dict[str, Any]


class EpisodeApplicationService:
    def __init__(
        self,
        store: VaultEpisodeStore,
        *,
        workflow: WorkflowCoordinator | None = None,
        profile_loader=load_active_profile_authority,
        interaction: HumanInteraction | None = None,
    ):
        self.store = store
        self.workflow = workflow or ControlledB5I1Preparation()
        self.profile_loader = profile_loader
        self.interaction = interaction

    def start(self, human_input: HumanInput) -> IntakeResult:
        preflight = getattr(self.workflow, "preflight", None)
        mission_id = None
        if callable(preflight):
            mission_id = preflight()
        profile = self.profile_loader()
        run_id = f"RUN-{uuid4().hex}"
        handoff = build_editorial_handoff(human_input, profile)
        episode = self.store.create_episode(
            human_input,
            handoff=handoff,
            profile=profile,
            run_id=run_id,
            mission_id=mission_id if isinstance(mission_id, str) and mission_id.strip() else None,
        )
        try:
            workflow_state = self._run_workflow(episode, human_input, handoff, run_id)
            self.store.record_workflow(episode, workflow_state)
        except UserCancelled:
            raise
        except StorageError as exc:
            raise StorageError(
                f"El episodio {episode.episode_id} fue persistido pero no se pudo registrar el workflow: {exc}"
            ) from exc
        return IntakeResult(episode, handoff, workflow_state)

    def resume(self, episode_id: str) -> dict[str, Any]:
        preflight = getattr(self.workflow, "preflight", None)
        if callable(preflight):
            preflight()
        current = self.store.resume(episode_id)
        if current["entry"].get("estado") == self.store.ADMINISTRATIVE_CLOSED_INDEX_STATUS:
            raise StorageError("EPISODE_ADMINISTRATIVELY_CLOSED: no se reanuda un episodio cerrado por recovery")
        request_path = Path(current["folder"]) / "human_decision_requests.json"
        requests = json.loads(request_path.read_text(encoding="utf-8")).get("requests", []) if request_path.exists() else []
        pending = None
        for candidate in requests:
            record = self.store.interaction_record(episode_id, candidate["request_id"])
            if record["transition"] is not None:
                outcome = record["transition"].get("workflow_outcome")
                if isinstance(outcome, dict):
                    handle_folder = Path(current["folder"])
                    handle = EpisodeHandle(
                        episode_id,
                        current["entry"].get("slug", "episodio"),
                        handle_folder,
                        self.store.index_path,
                    )
                    self.store.record_workflow(handle, outcome)
                continue
            if candidate.get("status") in {"PENDING", "RESPONSE_RECORDED", "RESOLVED"}:
                pending = candidate
                break
        if pending is None:
            complete = getattr(self.workflow, "complete", None)
            if callable(complete):
                folder = Path(current["folder"])
                human_input = HumanInput.from_dict(
                    json.loads((folder / "00_human_input.json").read_text(encoding="utf-8"))
                )
                handoff = json.loads((folder / "01_editorial_intake_handoff.json").read_text(encoding="utf-8"))
                handle = EpisodeHandle(
                    episode_id,
                    current["entry"].get("slug", "episodio"),
                    folder,
                    self.store.index_path,
                )
                run_id = current["state"].get("run_id") or f"RUN-{uuid4().hex}"
                outcome = complete(handle, human_input, handoff, run_id)
                if outcome is not None:
                    self.store.record_workflow(handle, outcome)
                    return self.store.resume(episode_id)
            return current
        folder = Path(current["folder"])
        human_input = HumanInput.from_dict(
            json.loads((folder / "00_human_input.json").read_text(encoding="utf-8"))
        )
        handoff = json.loads((folder / "01_editorial_intake_handoff.json").read_text(encoding="utf-8"))
        handle = EpisodeHandle(
            episode_id,
            current["entry"].get("slug", "episodio"),
            folder,
            self.store.index_path,
        )
        request = DecisionRequest.from_dict(pending, require_contract=True)
        if pending.get("request_checksum") != request.checksum():
            self.store.set_request_status(episode_id, request.request_id, "STALE")
            stale = {
                "workflow_id": request.workflow_ref or "UNKNOWN_WORKFLOW",
                "status": "STALE_REQUEST",
                "episode_id": episode_id,
                "reason": "REQUEST_CHECKSUM_MISMATCH",
                "downstream_execution_started": False,
            }
            self.store.record_workflow(handle, stale)
            return self.store.resume(episode_id)
        record = self.store.interaction_record(episode_id, request.request_id)
        if record.get("decision_error") is not None:
            raise ValueError("Existe una decisión persistida que no corresponde al request.")
        if record["decision"] is None:
            if self.interaction is None:
                return current
            self.request_human_decision(episode_id, request, self.interaction)
            record = self.store.interaction_record(episode_id, request.request_id)
        if record["transition"] is not None:
            outcome = record["transition"].get("workflow_outcome")
            if isinstance(outcome, dict):
                self.store.record_workflow(handle, outcome)
            return self.store.resume(episode_id)
        workflow_state = self._consume_decision(handle, human_input, handoff, request, record["decision"])
        self.store.record_workflow(handle, workflow_state)
        return self.store.resume(episode_id)

    def administratively_close_irrecoverable_episode(
        self,
        episode_id: str,
        *,
        reason: str,
        actor: str,
        source: str = "APPLICATION_ADMINISTRATIVE_RECOVERY",
    ) -> dict[str, Any]:
        """Expose the single administrative recovery path without invoking editorial workflow."""
        return self.store.administratively_close_irrecoverable_episode(
            episode_id,
            reason=reason,
            actor=actor,
            source=source,
        )

    def _run_workflow(
        self,
        handle: EpisodeHandle,
        human_input: HumanInput,
        handoff: dict[str, Any],
        run_id: str,
    ) -> dict[str, Any]:
        workflow_state = self.workflow.start(handle, human_input, handoff, run_id)
        request_data = workflow_state.get("human_decision_request")
        if request_data is None:
            return workflow_state
        request = DecisionRequest.from_dict(
            {
                **request_data,
                "episode_id": request_data.get("episode_id") or handle.episode_id,
                "workflow_ref": request_data.get("workflow_ref") or workflow_state.get("workflow_id"),
            }
        )
        self.store.record_decision_request(handle.episode_id, request.to_dict())
        self.store.record_workflow(handle, workflow_state)
        if self.interaction is None:
            return workflow_state
        decision = self.request_human_decision(handle.episode_id, request, self.interaction)
        return self._consume_decision(handle, human_input, handoff, request, decision.to_dict())

    def _consume_decision(
        self,
        handle: EpisodeHandle,
        human_input: HumanInput,
        handoff: dict[str, Any],
        request: DecisionRequest,
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        existing = self.store.interaction_record(handle.episode_id, request.request_id)["transition"]
        if existing is not None:
            return existing.get("workflow_outcome", {"status": "RESOLVED", "transition": existing})
        decision_model = HumanDecision.from_dict(decision, require_bound_metadata=True) if isinstance(decision, dict) else decision
        validate_human_decision(request, decision_model, handle.episode_id, require_bound_metadata=True)
        decision = decision_model.to_dict()
        try:
            outcome = self.workflow.resume(handle, human_input, handoff, decision, request.to_dict())
        except WorkflowDecisionStale as exc:
            self.store.set_request_status(handle.episode_id, request.request_id, "STALE")
            self.store.record_workflow(
                handle,
                {
                    "workflow_id": request.workflow_ref or "UNKNOWN_WORKFLOW",
                    "status": "STALE_REQUEST",
                    "episode_id": handle.episode_id,
                    "reason": str(exc) or "WORKFLOW_REPORTED_STALE_SUBJECT",
                    "downstream_execution_started": False,
                },
            )
            raise
        transition = outcome.get("transition") if isinstance(outcome, dict) else None
        if not isinstance(transition, dict):
            raise StorageError("workflow.resume debe devolver una transición persistible.")
        transition = {
            **transition,
            "episode_id": handle.episode_id,
            "request_id": request.request_id,
            "status": "STALE" if outcome.get("status") in {"STALE", "STALE_DECISION"} else "RESOLVED",
            "workflow_outcome": outcome,
        }
        try:
            self.store.record_workflow_transition(handle.episode_id, transition)
        except StorageError:
            existing = self.store.interaction_record(handle.episode_id, request.request_id)["transition"]
            if existing is None:
                raise
            return existing.get("workflow_outcome", {"status": "RESOLVED", "transition": existing})
        return outcome

    def request_human_decision(
        self,
        episode_id: str,
        request: DecisionRequest,
        interaction: HumanInteraction,
    ) -> HumanDecision:
        request = replace(request, episode_id=request.episode_id or episode_id)
        stored_request = self.store.record_decision_request(episode_id, request.to_dict())
        request = DecisionRequest.from_dict(stored_request)
        try:
            decision = interaction.decide(request)
        except UserCancelled:
            decision = HumanDecision(
                request.request_id,
                "CANCEL",
                actor_ref=getattr(interaction, "actor_ref", "local-user"),
                channel=getattr(interaction, "channel", "UNKNOWN"),
            ).bind_request(request)
            self.store.record_decision(episode_id, decision.to_dict())
            raise
        validate_human_decision(request, decision, episode_id)
        decision = decision.bind_request(request)
        validate_human_decision(request, decision, episode_id, require_bound_metadata=True)
        self.store.record_decision(episode_id, decision.to_dict())
        return decision
