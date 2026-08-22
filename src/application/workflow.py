"""Workflow boundary kept intentionally separate from interaction and storage."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from src.application.contracts import HumanInput
from src.application.storage import EpisodeHandle
from src.core.path_resolution import REPO_ROOT
from src.application.authority import load_operational_authority


class WorkflowCoordinator(Protocol):
    def preflight(self) -> None: ...
    def start(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], run_id: str) -> dict[str, Any]: ...
    def resume(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], decision: Any, request: Any) -> dict[str, Any]: ...


class WorkflowDecisionStale(PermissionError):
    """The approved subject changed before the decision was consumed."""


class ControlledB5I1Preparation:
    """Records the authorized handoff without running an editorial vertical."""

    CONTROL_PATH = REPO_ROOT / "plans" / "001_CONTROL_OPERATIVO.md"

    def preflight(self) -> None:
        load_operational_authority(self.CONTROL_PATH)

    def start(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], run_id: str) -> dict[str, Any]:
        self.preflight()
        return {
            "workflow_id": "B5_I1_CONTROLLED_EXECUTION",
            "status": "READY_FOR_AUTHORIZED_WORKFLOW",
            "episode_id": handle.episode_id,
            "run_id": run_id,
            "entry_mode": human_input.mode.value,
            "handoff_contract": handoff["target_contract"],
            "downstream_execution_started": False,
            "authorization_boundary": "R2_SCOPE_B5_I1_CONTROLLED_EXECUTION",
            "blocked_capabilities": ["B5_I2", "B5_I3", "B5.5", "B6", "S5_REAL_EXECUTION", "PUBLICATION"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def resume(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], decision: Any, request: Any) -> dict[str, Any]:
        """Controlled infrastructure has no editorial consequence to decide."""
        return {
            "workflow_id": "B5_I1_CONTROLLED_EXECUTION",
            "status": "READY_FOR_AUTHORIZED_WORKFLOW",
            "episode_id": handle.episode_id,
            "run_id": request.get("run_id") if isinstance(request, dict) else None,
            "decision_consumed": True,
            "consequence": "HUMAN_DECISION_RECORDED_FOR_CONTROLLED_WORKFLOW",
            "transition": {
                "transition_id": f"TRANSITION-{request['request_id']}",
                "request_id": request["request_id"],
                "from_status": "WAITING_FOR_HUMAN_DECISION",
                "to_status": "READY_FOR_AUTHORIZED_WORKFLOW",
                "consequence": "HUMAN_DECISION_RECORDED_FOR_CONTROLLED_WORKFLOW",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        }
