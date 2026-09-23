"""Application orchestration without editorial or channel-specific rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping
from uuid import uuid4

from src.ai.contracts import ExecutionRequest, ExecutionStatus, InputArtifact
from src.ai.execution import _bind_runtime_fields, editorial_only_payload, execute, validate_editorial_payload
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.role_execution import resolve_role_execution_contract
from src.application.contracts import HumanInput
from src.application.handoff import build_editorial_handoff
from src.application.interaction import (
    DecisionRequest,
    HumanDecision,
    HumanInteraction,
    UserCancelled,
    validate_human_decision,
)
from src.application.storage import EpisodeHandle, StorageError, VaultEpisodeStore, _write_json_atomic
from src.application.workflow import ControlledB5I1Preparation, WorkflowCoordinator, WorkflowDecisionStale
from src.application.plan013_script_coordinator import coordinate_script_pipeline
from src.application.research_m7 import ResearchM7Error, ResearchV2B5I3Adapter
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.final_script_review import build_final_script_review, measure_duration_telemetry
from src.core.contract_validation import (
    validate_editorial_script_approval,
    validate_work_lifecycle,
    validate_work_research_dossier,
)


@dataclass(frozen=True)
class IntakeResult:
    episode: EpisodeHandle
    handoff: dict[str, Any]
    workflow: dict[str, Any]


@dataclass(frozen=True)
class _Plan015StageResult:
    output: dict[str, Any]
    run_id: str


class _Plan015HandoffPending(RuntimeError):
    def __init__(self, schema: str, result: Any):
        super().__init__(schema)
        self.schema = schema
        self.result = result


class EpisodeApplicationService:
    def __init__(
        self,
        store: VaultEpisodeStore,
        *,
        workflow: WorkflowCoordinator | None = None,
        profile_loader=load_active_profile_authority,
        interaction: HumanInteraction | None = None,
        synthetic_outputs: Mapping[str, dict[str, Any]] | None = None,
        editorial_approval_actor_ref: str | None = None,
        editorial_approval_role: str | None = None,
        plan015_handoff_directory: str | Path | None = None,
    ):
        self.store = store
        self.workflow = workflow or ControlledB5I1Preparation()
        self.profile_loader = profile_loader
        self.interaction = interaction
        self.synthetic_outputs = dict(synthetic_outputs or {})
        self.editorial_approval_actor_ref = editorial_approval_actor_ref
        self.editorial_approval_role = editorial_approval_role
        self.plan015_handoff_directory = Path(plan015_handoff_directory) if plan015_handoff_directory is not None else None

    def start(self, human_input: HumanInput) -> IntakeResult:
        preflight = getattr(self.workflow, "preflight", None)
        mission_id = None
        if callable(preflight):
            mission_id = preflight()
        boundary = getattr(self.workflow, "boundary", None)
        authorization_id = getattr(boundary, "resolved_authorization_id", None)
        profile = self.profile_loader()
        run_id = f"RUN-{uuid4().hex}"
        handoff = build_editorial_handoff(human_input, profile)
        episode = self.store.create_episode(
            human_input,
            handoff=handoff,
            profile=profile,
            run_id=run_id,
            mission_id=mission_id if isinstance(mission_id, str) and mission_id.strip() else None,
            authorization_id=authorization_id if isinstance(authorization_id, str) and authorization_id.strip() else None,
        )
        try:
            workflow_state = self._run_workflow(episode, human_input, handoff, run_id)
            workflow_state = self._advance_plan015_research(episode, workflow_state)
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
        if current["state"].get("status") == "EDITORIAL_SCRIPT_APPROVED":
            self.store.validate_plan015_editorial_closure(
                EpisodeHandle(
                    episode_id,
                    current["entry"].get("slug", "episodio"),
                    Path(current["folder"]),
                    self.store.index_path,
                )
            )
            return current
        stop_boundary = current["state"].get("stop_boundary")
        if stop_boundary is None and current["state"].get("status") == "LEGITIMATE_STOP":
            workflow_path = Path(current["folder"]) / "workflow_state.json"
            workflow_snapshot = json.loads(workflow_path.read_text(encoding="utf-8")) if workflow_path.is_file() else {}
            stop_boundary = workflow_snapshot.get("stop_boundary")
        if (
            current["state"].get("status") == "LEGITIMATE_STOP"
            and stop_boundary == "RESEARCH_EXTERNAL_COGNITIVE_SEAM"
        ):
            checkpoint = Path(current["folder"]) / "m7_checkpoint.json"
            if checkpoint.is_file() and self._is_research_ready_checkpoint(Path(current["folder"])):
                try:
                    return self._resume_plan015_downstream(current, synthetic_outputs=self.synthetic_outputs)
                except _Plan015HandoffPending as pending:
                    return self._persist_plan015_handoff_stop(current, pending)
            return current
        if (
            current["state"].get("status") == "LEGITIMATE_STOP"
            and stop_boundary == "PLAN015_DOWNSTREAM_EXTERNAL_RESULT_IMPORTED"
        ):
            try:
                return self._resume_plan015_downstream(current, synthetic_outputs=self.synthetic_outputs)
            except _Plan015HandoffPending as pending:
                return self._persist_plan015_handoff_stop(current, pending)
        if (
            current["state"].get("status") == "LEGITIMATE_STOP"
            and stop_boundary == "TOPIC_CONDITIONS_PENDING"
        ):
            workflow_path = Path(current["folder"]) / "workflow_state.json"
            workflow = json.loads(workflow_path.read_text(encoding="utf-8")) if workflow_path.is_file() else {}
            handle = EpisodeHandle(
                episode_id,
                current["entry"].get("slug", "episodio"),
                Path(current["folder"]),
                self.store.index_path,
            )
            advanced = self._advance_plan015_research(
                handle,
                {**workflow, "status": "TOPIC_BELONGING_TECHNICAL_STOP"},
            )
            if advanced != workflow:
                self.store.record_workflow(handle, advanced)
            return self.store.resume(episode_id)
        if current["state"].get("status") == "LEGITIMATE_STOP" and stop_boundary == "FINAL_VALIDATIONS_COMPLETE":
            return self._resume_plan015_final_approval(current)
        if current["state"].get("status") == "READY_FOR_REASSESSMENT":
            prepare_reassessment = getattr(self.workflow, "prepare_reassessment", None)
            if not callable(prepare_reassessment):
                raise StorageError("TOPIC_BELONGING_REASSESSMENT_UNAVAILABLE")
            handle = EpisodeHandle(
                episode_id,
                current["entry"].get("slug", "episodio"),
                Path(current["folder"]),
                self.store.index_path,
            )
            outcome = prepare_reassessment(handle)
            outcome = self._advance_plan015_research(handle, outcome)
            self.store.record_workflow(handle, outcome)
            return self.store.resume(episode_id)
        roundtrip_resume = getattr(self.workflow, "resume_roundtrip", None)
        if callable(roundtrip_resume) and current["state"].get("status") == "PERSISTED":
            folder = Path(current["folder"])
            handle = EpisodeHandle(
                episode_id,
                current["entry"].get("slug", "episodio"),
                folder,
                self.store.index_path,
            )
            outcome = roundtrip_resume(handle)
            if outcome is not None:
                outcome = self._advance_plan015_research(handle, outcome)
                self.store.record_workflow(handle, outcome)
                if str(outcome.get("status") or "") == "TOPIC_BELONGING_TECHNICAL_STOP":
                    self._archive_terminated_handoffs(handle)
                return self.store.resume(episode_id)
            return current
        if callable(roundtrip_resume) and current["state"].get("status") in {"PENDING_EXTERNAL_RESULT", "VALIDATED"}:
            return current
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
                    outcome = self._advance_plan015_research(handle, outcome)
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
                    outcome = self._advance_plan015_research(handle, outcome)
                    self.store.record_workflow(handle, outcome)
                    if str(outcome.get("status") or "") == "TOPIC_BELONGING_TECHNICAL_STOP":
                        self._archive_terminated_handoffs(handle)
                    return self.store.resume(episode_id)
            if current["state"].get("status") == "TOPIC_BELONGING_TECHNICAL_STOP":
                handle = EpisodeHandle(
                    episode_id,
                    current["entry"].get("slug", "episodio"),
                    Path(current["folder"]),
                    self.store.index_path,
                )
                advanced = self._advance_plan015_research(handle, current["state"])
                if advanced != current["state"]:
                    self.store.record_workflow(handle, advanced)
                    return self.store.resume(episode_id)
                self._archive_terminated_handoffs(handle)
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
                outcome = self._advance_plan015_research(handle, outcome)
                self.store.record_workflow(handle, outcome)
            return self.store.resume(episode_id)
        workflow_state = self._consume_decision(handle, human_input, handoff, request, record["decision"])
        workflow_state = self._advance_plan015_research(handle, workflow_state)
        self.store.record_workflow(handle, workflow_state)
        return self.store.resume(episode_id)

    def _resume_plan015_final_approval(self, current: Mapping[str, Any]) -> dict[str, Any]:
        """Consume one exact human decision and materialize the canonical approval."""
        episode_id = str(current["entry"]["ep_id"])
        folder = Path(str(current["folder"]))
        handle = EpisodeHandle(
            episode_id,
            str(current["entry"].get("slug") or "episodio"),
            folder,
            self.store.index_path,
        )
        self.store.validate_plan015_downstream(handle)
        actor_ref = str(self.editorial_approval_actor_ref or "").strip()
        approval_role = str(self.editorial_approval_role or "").strip().upper()
        if not actor_ref or not approval_role:
            return self.store.resume(episode_id)
        if self.interaction is None:
            raise StorageError("PLAN015_FINAL_APPROVAL_INTERACTION_REQUIRED")

        edited = self._read_object(folder / "12_edited_script.json", "EDITED_SCRIPT")
        audit = self._read_object(folder / "15_final_editorial_audit.json", "FINAL_EDITORIAL_AUDIT")
        review = self._read_object(folder / "16_final_script_review.json", "FINAL_SCRIPT_REVIEW")
        identity = (
            str(edited.get("script_id") or ""),
            str(edited.get("artifact_version") or ""),
            str(edited.get("checksum") or ""),
        )
        if not all(identity) or identity != (
            str(audit.get("artifact_id") or ""),
            str(audit.get("script_version") or ""),
            str(audit.get("script_checksum") or ""),
        ) or identity != (
            str(review.get("artifact_id") or ""),
            str(review.get("script_version") or ""),
            str(review.get("script_checksum") or ""),
        ):
            raise StorageError("PLAN015_FINAL_APPROVAL_SUBJECT_STALE")
        if review.get("decision") not in {"PASS", "WARN"}:
            raise StorageError("PLAN015_FINAL_APPROVAL_REVIEW_NOT_ELIGIBLE")

        request_id = f"PLAN015-FINAL-APPROVAL-{episode_id}-{identity[2][:12]}"
        request_path = folder / "human_decision_requests.json"
        existing_request: dict[str, Any] | None = None
        if request_path.is_file():
            request_records = self._read_object(request_path, "HUMAN_DECISION_REQUESTS").get("requests", [])
            existing_request = next(
                (item for item in request_records if item.get("request_id") == request_id),
                None,
            )
        if existing_request is not None:
            request = DecisionRequest.from_dict(existing_request, require_contract=True)
        else:
            request = DecisionRequest(
                request_id=request_id,
                episode_id=episode_id,
                prompt=(
                    f"¿Apruebas editorialmente el guion {identity[0]} "
                    f"versión {identity[1]} con checksum {identity[2]}?"
                ),
                subject_ref=identity[0],
                subject_version=identity[1],
                subject_checksum=identity[2],
                workflow_ref="PLAN015_FINAL_EDITORIAL_APPROVAL",
                expected_actor_ref=actor_ref,
                expected_approval_role=approval_role,
                expected_channel=getattr(self.interaction, "channel", None),
            )
        if (
            request.episode_id != episode_id
            or request.subject_ref != identity[0]
            or request.subject_version != identity[1]
            or request.subject_checksum != identity[2]
            or request.expected_actor_ref != actor_ref
            or request.expected_approval_role != approval_role
            or request.expected_channel != getattr(self.interaction, "channel", None)
        ):
            raise StorageError("PLAN015_FINAL_APPROVAL_REQUEST_STALE")

        stored_request = self.store.record_decision_request(episode_id, request.to_dict())
        request = DecisionRequest.from_dict(stored_request, require_contract=True)
        record = self.store.interaction_record(episode_id, request.request_id)
        if record.get("decision_error") is not None:
            raise StorageError("PLAN015_FINAL_APPROVAL_DECISION_ORPHANED")
        if record.get("decision") is None:
            try:
                self.request_human_decision(episode_id, request, self.interaction)
            except UserCancelled:
                record = self.store.interaction_record(episode_id, request.request_id)
            else:
                record = self.store.interaction_record(episode_id, request.request_id)
        decision_payload = record.get("decision")
        if not isinstance(decision_payload, dict):
            return self.store.resume(episode_id)
        decision = HumanDecision.from_dict(decision_payload, require_bound_metadata=True)
        validate_human_decision(request, decision, episode_id, require_bound_metadata=True)

        decision_ref = {
            "request_id": request.request_id,
            "request_checksum": request.checksum(),
            "actor_ref": decision.actor_ref,
            "channel": decision.channel,
            "occurred_at": decision.occurred_at,
            "action": decision.action,
        }
        if decision.action == "APPROVE":
            approval = {
                "artifact_id": identity[0],
                "script_version": identity[1],
                "checksum": identity[2],
                "decision": "APPROVED",
                "approved_by": decision.actor_ref,
                "approved_role": approval_role,
                "approved_at": decision.occurred_at,
            }
            violations = validate_editorial_script_approval(approval)
            if violations:
                raise StorageError("PLAN015_EDITORIAL_APPROVAL_INVALID:" + ";".join(violations))
            workflow_state = self._read_object(folder / "workflow_state.json", "WORKFLOW_STATE")
            episode_state = self._read_object(folder / "episode_state.json", "EPISODE_STATE")
            closure = {
                "episode_id": episode_id,
                "script_artifact_id": identity[0],
                "script_version": identity[1],
                "script_checksum": identity[2],
                "final_audit": audit,
                "final_script_review": review,
                "human_approval": approval,
                "human_decision_ref": decision_ref,
            }
            self.store.record_plan013_editorial_closure(
                handle,
                closure=closure,
                workflow_state=workflow_state,
                episode_state=episode_state,
            )
            self.store.set_request_status(episode_id, request.request_id, "RESOLVED")
            return self.store.resume(episode_id)

        if decision.action == "CORRECT":
            outcome = {
                **self._read_object(folder / "workflow_state.json", "WORKFLOW_STATE"),
                "status": "IN_REVIEW",
                "stop_boundary": "CORRECTION_REQUIRED",
                "next_action": "APPLY_HUMAN_CORRECTION",
                "approval_status": "NOT_APPROVED",
                "human_decision_ref": decision_ref,
                "human_correction": decision.correction,
            }
        elif decision.action == "REJECT":
            outcome = {
                **self._read_object(folder / "workflow_state.json", "WORKFLOW_STATE"),
                "status": "BLOCKED",
                "stop_boundary": "HUMAN_EDITORIAL_REJECTION",
                "next_action": "OWNER_REVIEW_REQUIRED",
                "approval_status": "REJECTED",
                "human_decision_ref": decision_ref,
            }
        elif decision.action == "CANCEL":
            self.store.set_request_status(episode_id, request.request_id, "CANCELLED")
            return self.store.resume(episode_id)
        else:
            raise StorageError("PLAN015_FINAL_APPROVAL_ACTION_UNSUPPORTED")
        self.store.record_workflow(handle, outcome)
        self.store.set_request_status(episode_id, request.request_id, "RESOLVED")
        return self.store.resume(episode_id)

    @staticmethod
    def _checksum(payload: Any) -> str:
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _read_object(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"PLAN015_HF02_{label}_UNREADABLE") from exc
        if not isinstance(value, dict):
            raise StorageError(f"PLAN015_HF02_{label}_INVALID")
        return value

    def _resolve_topic_conditions(
        self,
        handle: EpisodeHandle,
        *,
        decision: Mapping[str, Any],
        assessment: Mapping[str, Any],
        topic_input: Mapping[str, Any],
        decision_ref: str,
        decision_checksum: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Verify only condition evidence already persisted by the owner.

        Conditions are intentionally not interpreted or completed by the
        application.  The only supported machine-readable form is a condition
        object carrying durable evidence references with exact file checksums.
        Anything else remains pending rather than being inferred.
        """
        conditions = decision.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            return None, None
        evidence_by_kind: dict[str, dict[str, Any]] = {}
        verified_conditions: list[dict[str, Any]] = []
        for condition in conditions:
            if not isinstance(condition, dict):
                return None, None
            condition_id = str(condition.get("condition_id") or "").strip()
            refs = condition.get("evidence_refs")
            if not condition_id or not isinstance(refs, list) or not refs:
                return None, None
            verified_refs: list[dict[str, Any]] = []
            for ref in refs:
                if not isinstance(ref, dict):
                    return None, None
                kind = str(ref.get("kind") or "").strip()
                raw_path = str(ref.get("path") or "").strip()
                expected_checksum = str(ref.get("checksum") or "").strip()
                if kind not in {"work_lifecycle", "research_dossier"} or not raw_path or not expected_checksum:
                    return None, None
                prefix = f"episode:{handle.episode_id}/"
                if not raw_path.startswith(prefix):
                    return None, None
                relative = raw_path[len(prefix):]
                path = (handle.folder / relative).resolve()
                try:
                    path.relative_to(handle.folder.resolve())
                except ValueError:
                    return None, None
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_checksum:
                    return None, None
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    return None, None
                if not isinstance(payload, dict) or payload.get("episode_id") != handle.episode_id or kind in evidence_by_kind:
                    return None, None
                schema_violations = (
                    validate_work_lifecycle(payload)
                    if kind == "work_lifecycle"
                    else validate_work_research_dossier(payload)
                )
                if schema_violations:
                    return None, None
                evidence_by_kind[kind] = payload
                verified_refs.append({"kind": kind, "path": raw_path, "checksum": expected_checksum})
            verified_conditions.append({"condition_id": condition_id, "evidence_refs": verified_refs})
        if set(evidence_by_kind) != {"work_lifecycle", "research_dossier"}:
            return None, None
        from src.scripts.channel_intelligence import canonical_checksum
        from src.scripts.topic_belonging_flow import evaluate_topic_belonging_gate

        resolved_topic_input = dict(topic_input)
        lifecycle_screening = evidence_by_kind["work_lifecycle"].get("screening", {})
        candidate_work_refs = lifecycle_screening.get("candidate_work_ids") if isinstance(lifecycle_screening, dict) else None
        research_ref = evidence_by_kind["research_dossier"].get("research_id")
        evidence_report_id = evidence_by_kind["research_dossier"].get("evidence_report_id")
        if (
            not isinstance(candidate_work_refs, list)
            or not candidate_work_refs
            or not isinstance(research_ref, str)
            or not research_ref.strip()
            or not isinstance(evidence_report_id, str)
            or not evidence_report_id.strip()
        ):
            return None, None
        resolved_topic_input.update(
            {
                "research_ref": research_ref,
                "narrative_door_evidence_refs": [evidence_report_id],
                "candidate_work_refs": copy.deepcopy(candidate_work_refs),
            }
        )
        resolved_decision = copy.deepcopy(dict(decision))
        resolved_decision["pre_b5_i1_evidence"] = {
            "topic_input_checksum": self._checksum(resolved_topic_input),
            "research_ref": research_ref,
            "narrative_door_evidence_refs": [evidence_report_id],
            "candidate_work_refs": copy.deepcopy(candidate_work_refs),
        }
        resolved_decision["provenance"]["output_checksum"] = canonical_checksum(resolved_decision, "decision")

        gate = evaluate_topic_belonging_gate(
            resolved_decision,
            dict(assessment),
            resolved_topic_input,
            work_lifecycle=evidence_by_kind["work_lifecycle"],
            research_dossier=evidence_by_kind["research_dossier"],
        )
        if gate.get("topic_approved") is not True:
            return None, gate
        resolution = {
            "contract": "plan015_topic_conditions_resolution",
            "contract_version": "1.0.0",
            "episode_id": handle.episode_id,
            "status": "SATISFIED",
            "decision_ref": decision_ref,
            "decision_checksum": decision_checksum,
            "conditions": verified_conditions,
            "gate": gate,
        }
        resolution_path = handle.folder / "topic_conditions_resolution.json"
        if resolution_path.is_file():
            existing = self._read_object(resolution_path, "TOPIC_CONDITIONS_RESOLUTION")
            if existing != resolution:
                raise StorageError("TOPIC_CONDITIONS_RESOLUTION_CONFLICT")
        else:
            _write_json_atomic(resolution_path, resolution)
        return resolution, gate

    @classmethod
    def _is_research_ready_checkpoint(cls, folder: Path) -> bool:
        try:
            checkpoint = cls._read_object(folder / "m7_checkpoint.json", "RESEARCH_CHECKPOINT")
            manifest_ref = next(item for item in checkpoint.get("artifacts", []) if item.get("stage") == "M6")
            handoff_ref = next(item for item in checkpoint.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF")
            manifest = cls._read_object(Path(str(manifest_ref["path"])), "RESEARCH_READY_MANIFEST")
            handoff = cls._read_object(Path(str(handoff_ref["path"])), "B5_I3_HANDOFF")
        except (StorageError, StopIteration, KeyError, TypeError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        return (
            manifest.get("research_ready_state") in {"RESEARCH_READY", "RESEARCH_READY_WITH_LIMITATIONS"}
            and handoff.get("handoff_state") == "VALID"
            and isinstance(handoff.get("validation"), dict)
            and handoff["validation"].get("status") in {"PENDING", "PASS"}
        )

    def _persist_plan015_handoff_stop(
        self,
        current: Mapping[str, Any],
        pending: _Plan015HandoffPending,
    ) -> dict[str, Any]:
        episode_id = str(current["entry"]["ep_id"])
        folder = Path(str(current["folder"]))
        handle = EpisodeHandle(
            episode_id,
            str(current["entry"].get("slug") or "episodio"),
            folder,
            self.store.index_path,
        )
        package_path = Path(str(pending.result.usage.get("package") or ""))
        if not package_path.is_file():
            raise StorageError("PLAN015_DOWNSTREAM_HANDOFF_PACKAGE_MISSING")
        package = self._read_object(package_path, "PLAN015_DOWNSTREAM_HANDOFF_PACKAGE")
        prior = self._read_object(folder / "workflow_state.json", "WORKFLOW_STATE")
        imported = self._load_plan015_imported_outputs(folder)
        workflow = {
            **prior,
            "workflow_id": "PLAN015_DOWNSTREAM_ROUNDTRIP",
            "status": "PENDING_EXTERNAL_RESULT",
            "episode_id": episode_id,
            "stop_boundary": "PLAN015_DOWNSTREAM_EXTERNAL_COGNITIVE_SEAM",
            "next_action": "IMPORT_EXTERNAL_COGNITIVE_RESULT",
            "stage": package.get("stage"),
            "output_schema": pending.schema,
            "role": package.get("role"),
            "handoff_id": package.get("handoff_id"),
            "handoff_package_ref": str(package_path),
            "handoff_package_checksum": package.get("package_checksum"),
            "execution_family": package.get("execution_family"),
            "execution_route": package.get("execution_route"),
            "execution_profile": package.get("execution_profile"),
            "completed_downstream_stages": sorted(imported),
            "downstream_execution_started": True,
            "real_cognitive_execution": "PENDING_EXTERNAL_RESULT",
        }
        self.store.record_workflow(handle, workflow)
        return self.store.resume(episode_id)

    def _load_plan015_imported_outputs(self, folder: Path) -> dict[str, _Plan015StageResult]:
        results_path = folder / "roundtrip_results.json"
        if not results_path.is_file():
            return {}
        records = self._read_object(results_path, "ROUNDTRIP_RESULTS").get("results", [])
        outputs: dict[str, _Plan015StageResult] = {}
        for record in records:
            if not isinstance(record, dict) or not str(record.get("stage") or "").startswith("PLAN015_"):
                continue
            schema = str(record.get("stage"))[len("PLAN015_"):].lower()
            relative_path = str(record.get("materialized_output_path") or "")
            if not relative_path:
                raise StorageError(f"PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_MISSING:{schema}")
            path = folder / relative_path
            if not path.is_file() or self.store._file_checksum(path) != record.get("materialized_output_checksum"):
                raise StorageError(f"PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_STALE:{schema}")
            outputs[schema] = _Plan015StageResult(
                self._read_object(path, f"PLAN015_IMPORTED_{schema.upper()}"),
                str(record.get("result_run_id") or ""),
            )
        return outputs

    def _resume_plan015_downstream(
        self,
        current: Mapping[str, Any],
        *,
        synthetic_outputs: Mapping[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Consume a durable M7 ResearchReady checkpoint through the normal service."""
        folder = Path(str(current["folder"]))
        episode_id = str(current["entry"]["ep_id"])
        handle = EpisodeHandle(
            episode_id,
            str(current["entry"].get("slug") or "episodio"),
            folder,
            self.store.index_path,
        )
        m7_state = self._read_object(folder / "m7_checkpoint.json", "RESEARCH_CHECKPOINT")
        try:
            manifest_ref = next(item for item in m7_state.get("artifacts", []) if item.get("stage") == "M6")
            handoff_ref = next(item for item in m7_state.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF")
        except (StopIteration, TypeError):
            raise StorageError("PLAN015_HF02_RESEARCH_READY_BOUNDARY_INCOMPLETE")
        manifest_path = Path(str(manifest_ref.get("path") or ""))
        handoff_path = Path(str(handoff_ref.get("path") or ""))
        manifest = self._read_object(manifest_path, "RESEARCH_READY_MANIFEST")
        handoff = self._read_object(handoff_path, "B5_I3_HANDOFF")
        manifest_binding = {
            "artifact_id": str(manifest_ref.get("artifact_id") or manifest.get("manifest_id") or ""),
            "artifact_kind": "ResearchReadyManifest",
            "artifact_version": str(manifest_ref.get("artifact_version") or manifest.get("research_version") or ""),
            "path": str(manifest_path),
            "checksum": str(manifest_ref.get("checksum") or ""),
        }
        try:
            refs = [
                InputArtifact(
                    str(item["artifact_kind"]),
                    str(item["artifact_id"]),
                    Path(str(item["path"])),
                    str(item.get("producer_run_id") or ""),
                    str(item.get("artifact_version") or ""),
                )
                for item in handoff.get("b5_i3_input_refs", [])
            ]
            ResearchV2B5I3Adapter.validate_research_v2_precondition(
                episode_id=episode_id,
                manifest_ref=manifest_binding,
                manifest=manifest,
                handoff=handoff,
                inputs=refs,
            )
        except (ResearchM7Error, KeyError, TypeError, ValueError, OSError) as exc:
            raise StorageError(f"PLAN015_HF02_BLOCKED:{exc}") from exc
        imported_outputs = self._load_plan015_imported_outputs(folder)

        payloads = {item.artifact_kind: self._read_object(item.path, item.artifact_kind) for item in refs}
        human_payload = payloads["human_input"]
        narrative_payload = {
            **payloads,
            "user_instructions": human_payload.get("user_instructions", []),
            "target_duration": human_payload.get("duration_target_minutes"),
            "target_language": human_payload.get("target_language"),
            "wpm_target": human_payload.get("wpm_target"),
            "wpm_provenance": human_payload.get("wpm_provenance"),
        }
        with TemporaryDirectory(prefix="plan015-hf02-", dir=folder) as staging_name:
            staging = Path(staging_name)
            b5_artifacts: dict[str, dict[str, Any]] = {}
            b5_runs: dict[str, str] = {}
            b5_manifest_path = folder / "b5_i3_design_manifest.json"
            if b5_manifest_path.is_file():
                recovered = self.store.recover_b5_i3_design(
                    handle,
                    dependency_paths={item.artifact_id: item.path for item in refs},
                )
                b5_manifest = recovered["manifest"]
                b5_artifacts = recovered["artifacts"]
                recovered_run = str(b5_artifacts["narrative_plan"].get("lineage", {}).get("generation_run_id") or "RECOVERED-B5-I3")
                b5_runs = {schema: recovered_run for schema in b5_artifacts}
            else:
                for schema in ("viewer_journey", "opening_design", "closing_design", "narrative_plan"):
                    result = self._execute_plan015_stage(
                        capability_id="B5_I3_NARRATIVE_ARCHITECTURE",
                        role="NARRATIVE_ARCHITECTURE",
                        schema=schema,
                        input_artifacts=refs,
                        input_payload=narrative_payload,
                        synthetic_output=self._synthetic_output(synthetic_outputs, schema),
                        imported_result=imported_outputs.get(schema),
                        output_artifact_id=f"HF02-{schema.upper()}-{episode_id}",
                        episode_id=episode_id,
                        config={
                            "artifact_version": "1.0.0",
                            "wpm_target": human_payload.get("wpm_target"),
                            "wpm_provenance": human_payload.get("wpm_provenance"),
                        },
                    )
                    b5_artifacts[schema] = result.output or {}
                    b5_runs[schema] = result.run_id
                b5_manifest = self.store.record_b5_i3_design(
                    handle,
                    artifacts=b5_artifacts,
                    dependency_snapshot=[
                        {
                            "artifact_id": item.artifact_id,
                            "artifact_version": item.artifact_version or payloads[item.artifact_kind].get("artifact_version", "1.0.0"),
                            "checksum": self._checksum(payloads[item.artifact_kind]),
                            "artifact_path": str(item.path),
                        }
                        for item in refs
                    ],
                )

            profile = payloads["active_editorial_profile_reference"]
            brief = payloads["episode_brief"]
            claims = payloads["claims_ledger"]
            thesis = payloads["refined_thesis"]
            profile_ref = next(item for item in refs if item.artifact_kind == "active_editorial_profile_reference")
            brief_ref = next(item for item in refs if item.artifact_kind == "episode_brief")
            claims_ref = next(item for item in refs if item.artifact_kind == "claims_ledger")
            thesis_ref = next(item for item in refs if item.artifact_kind == "refined_thesis")
            plan = b5_artifacts["narrative_plan"]
            plan_ref = InputArtifact("narrative_plan", plan["script_plan_id"], folder / "09_narrative_plan.json", b5_runs["narrative_plan"], plan["artifact_version"])
            thesis_input = InputArtifact("thesis_artifact", thesis["thesis_id"], thesis_ref.path, thesis_ref.producer_run_id, thesis_ref.artifact_version)
            writing_payload = {"narrative_plan": plan, "thesis_artifact": thesis, "editorial_profile": profile, "research_pack": payloads["research_pack"]}
            writing = self._execute_plan015_stage(
                capability_id="PLAN013_WRITING_SCRIPT_DRAFT", role="WRITING", schema="script_draft",
                input_artifacts=[plan_ref, thesis_input, InputArtifact("editorial_profile", profile_ref.artifact_id, profile_ref.path, profile_ref.producer_run_id, profile_ref.artifact_version), next(item for item in refs if item.artifact_kind == "research_pack")],
                input_payload=writing_payload,
                synthetic_output=self._synthetic_output(synthetic_outputs, "script_draft"),
                imported_result=imported_outputs.get("script_draft"),
                output_artifact_id=f"SCRIPT-DRAFT-{episode_id}", episode_id=episode_id,
                config={"artifact_version": "1.0.0"},
            )
            draft = writing.output or {}
            draft_path = staging / "script_draft.json"
            _write_json_atomic(draft_path, draft)
            draft_ref = InputArtifact("script_draft", draft["script_id"], draft_path, writing.run_id, draft["artifact_version"])
            editor_inputs = [draft_ref, InputArtifact("editorial_profile", profile_ref.artifact_id, profile_ref.path, profile_ref.producer_run_id, profile_ref.artifact_version), InputArtifact("brief", brief_ref.artifact_id, brief_ref.path, brief_ref.producer_run_id, brief_ref.artifact_version), claims_ref]
            edited = self._execute_plan015_stage(
                capability_id="PLAN013_EDITOR_EDITED_SCRIPT", role="EDITOR", schema="edited_script",
                input_artifacts=editor_inputs,
                input_payload={"script_draft": draft, "editorial_profile": profile, "brief": brief, "claims_ledger": claims},
                synthetic_output=self._synthetic_output(synthetic_outputs, "edited_script"),
                imported_result=imported_outputs.get("edited_script"),
                output_artifact_id=f"SCRIPT-EDITED-{episode_id}", episode_id=episode_id,
                config={"artifact_version": "1.1.0", "edit_report_ref": f"editorial_edit_report:{episode_id}"},
            )
            edited_payload = edited.output or {}
            edited_path = staging / "edited_script.json"
            _write_json_atomic(edited_path, edited_payload)
            edited_ref = InputArtifact("edited_script", edited_payload["script_id"], edited_path, edited.run_id, edited_payload["artifact_version"])
            report_result = self._execute_plan015_stage(
                capability_id="PLAN013_EDITOR_EDITED_SCRIPT", role="EDITOR", schema="editorial_edit_report",
                input_artifacts=[draft_ref, edited_ref],
                input_payload={"script_draft": draft, "editorial_profile": profile, "brief": brief, "claims_ledger": claims},
                synthetic_output=self._synthetic_output(synthetic_outputs, "editorial_edit_report"),
                imported_result=imported_outputs.get("editorial_edit_report"),
                output_artifact_id=f"EDIT-{episode_id}", episode_id=episode_id, config={},
            )
            report = report_result.output or {}
            report_path = staging / "editorial_edit_report.json"
            _write_json_atomic(report_path, report)
            report_ref = InputArtifact("EditorialEditReport", report.get("output_artifact_id", edited_payload["script_id"]), report_path, report_result.run_id, report.get("output_version", edited_payload["artifact_version"]))
            audit = self._execute_plan015_stage(
                capability_id="PLAN013_FINAL_EDITORIAL_AUDIT", role="FINAL_EDITORIAL_AUDITOR", schema="final_editorial_audit",
                input_artifacts=[edited_ref, report_ref, InputArtifact("editorial_profile", profile_ref.artifact_id, profile_ref.path, profile_ref.producer_run_id, profile_ref.artifact_version), InputArtifact("brief", brief_ref.artifact_id, brief_ref.path, brief_ref.producer_run_id, brief_ref.artifact_version), claims_ref],
                input_payload={"edited_script": edited_payload, "EditorialEditReport": report, "editorial_profile": profile, "brief": brief, "claims_ledger": claims},
                synthetic_output=self._synthetic_output(synthetic_outputs, "final_editorial_audit"),
                imported_result=imported_outputs.get("final_editorial_audit"),
                output_artifact_id=f"AUDIT-{episode_id}", episode_id=episode_id,
                config={"independence_verified": True},
            )
            audit_payload = audit.output or {}
            mandatory_dimensions = {
                "profile_compliance", "brief_compliance", "packaging_promise_compliance", "evidence_sufficiency",
                "thesis_quality", "viewer_journey", "opening_quality", "progression", "coherence", "originality",
                "source_transformation", "voice", "orality", "closing_quality", "factual_traceability",
            }
            if (
                audit_payload.get("decision") not in {"PASS", "WARN"}
                or audit_payload.get("independence_result") != "PASS"
                or any(audit_payload.get(key) in {"BLOCK", "REQUEST_CHANGES"} for key in mandatory_dimensions)
            ):
                raise StorageError("PLAN015_HF02_BLOCKED:FINAL_EDITORIAL_AUDIT_NOT_ELIGIBLE")
            trace = coordinate_script_pipeline(
                episode_id=episode_id, narrative_plan=plan, thesis_artifact=thesis, script_draft=draft,
                edited_script=edited_payload, edit_report=report, final_audit=audit_payload,
                producer_run_id=writing.run_id, editor_run_id=edited.run_id, auditor_run_id=audit_payload["auditor_run_id"],
            )
            active = self.profile_loader()
            profile_identity = {"profile_id": active["ACTIVE_PROFILE_ID"], "profile_version": active["ACTIVE_PROFILE_VERSION"], "profile_checksum": active["profile_checksum"]}
            duration_telemetry = measure_duration_telemetry(
                edited_payload,
                plan,
                script_draft=draft,
            )
            review = build_final_script_review(
                review_id=f"FSR-{episode_id}", episode_id=episode_id, artifact_id=edited_payload["script_id"],
                script_version=edited_payload["artifact_version"], script_checksum=edited_payload["checksum"],
                profile_reference=profile_identity,
                visible_promise_ref=f"editorial_script_promise:{payloads['editorial_script_promise']['promise_id']}@{payloads['editorial_script_promise'].get('artifact_version', '1.0.0')}",
                final_audit_ref=f"final_editorial_audit:{edited_payload['script_id']}@{edited_payload['artifact_version']}",
                final_audit_checksum=self._checksum(audit_payload), review_run_id=f"HF02-REVIEW-{episode_id}",
                producer_run_id=writing.run_id, editor_run_id=edited.run_id, auditor_run_id=audit_payload["auditor_run_id"],
                review_actor_id="FINAL_SCRIPT_REVIEW", producer_actor_id="WRITING", editor_actor_id="EDITOR", auditor_actor_id="FINAL_EDITORIAL_AUDITOR",
                evidence_refs=[f"final_editorial_audit:{edited_payload['script_id']}@{edited_payload['artifact_version']}"],
                duration_telemetry=duration_telemetry,
            )
            draft_manifest = self._script_manifest(draft, plan, "DRAFT")
            edited_manifest = self._script_manifest(edited_payload, plan, "IN_REVIEW")
            artifacts = {
                "script_draft": draft, "script_version_manifest": draft_manifest,
                "edited_script": edited_payload, "editorial_edit_report": report,
                "edited_script_version_manifest": edited_manifest,
                "final_editorial_audit": audit_payload, "final_script_review": review,
            }
            bindings = {
                kind: self._downstream_binding(kind, value, filename)
                for kind, value, filename in (
                    ("script_draft", draft, "10_script_draft.json"),
                    ("script_version_manifest", draft_manifest, "11_script_version_manifest.json"),
                    ("edited_script", edited_payload, "12_edited_script.json"),
                    ("editorial_edit_report", report, "13_editorial_edit_report.json"),
                    ("edited_script_version_manifest", edited_manifest, "14_edited_script_version_manifest.json"),
                    ("final_editorial_audit", audit_payload, "15_final_editorial_audit.json"),
                    ("final_script_review", review, "16_final_script_review.json"),
                )
            }
            workflow = {
                "workflow_id": "PLAN015_DOWNSTREAM_EDITORIAL_CHAIN",
                "status": "LEGITIMATE_STOP",
                "episode_id": episode_id,
                "downstream_execution_started": True,
                "stop_boundary": "FINAL_VALIDATIONS_COMPLETE",
                "next_action": "REQUEST_HUMAN_APPROVAL",
                "human_approval_pending": True,
                "research_ready_manifest_ref": manifest_binding,
                "research_v2_b5_i3_handoff_ref": {"path": str(handoff_path), "checksum": str(handoff_ref.get("checksum") or self._checksum(handoff))},
                "b5_i3_status": "B5_I3_COMPLETE",
                "b5_i3_manifest": b5_manifest,
                "script_lifecycle": {"status": "WORKING_CURRENT", "artifact": bindings["script_draft"]},
                "edited_script_lifecycle": {"status": "WORKING_CURRENT", "artifact": bindings["edited_script"]},
                "downstream_artifacts": bindings,
                "bindings": bindings,
                "final_validations": {"final_editorial_audit": bindings["final_editorial_audit"], "final_script_review": bindings["final_script_review"]},
                "trace": trace,
                "real_ai_execution": False,
            }
            self.store.record_plan015_downstream(handle, artifacts=artifacts, bindings=bindings, workflow=workflow)
        return self.store.resume(episode_id)

    @staticmethod
    def _synthetic_output(outputs: Mapping[str, dict[str, Any]], schema: str) -> dict[str, Any] | None:
        value = outputs.get(schema)
        if value is None:
            return None
        if not isinstance(value, dict):
            raise StorageError(f"PLAN015_HF02_SYNTHETIC_OUTPUT_INVALID:{schema}")
        return json.loads(json.dumps(value, ensure_ascii=False))

    def _execute_plan015_stage(
        self, *, capability_id: str, role: str, schema: str, input_artifacts: list[InputArtifact],
        input_payload: dict[str, Any], synthetic_output: dict[str, Any] | None,
        imported_result: _Plan015StageResult | None,
        output_artifact_id: str,
        episode_id: str, config: dict[str, Any],
    ):
        runtime_values = {"clean_session": True, "required_context": {"quality_criteria": "PLAN015_HF02", "audit_criteria": "PLAN015_HF02"}}
        contract = resolve_role_execution_contract(role, schema, input_payload, runtime_values)
        execution_mode = "SYNTHETIC_TEST" if synthetic_output is not None else "REAL"
        request = ExecutionRequest(
            capability_id=capability_id, skill_id=f"plan015_{schema}", skill_version="1.0.0",
            input_artifacts=input_artifacts, output_schema=schema, execution_mode=execution_mode,
            provider=None, execution_route="agent_harness", execution_family="AGENT_HARNESS",
            output_artifact_kind=schema, output_artifact_id=output_artifact_id,
            mock_output=editorial_only_payload(synthetic_output, schema) if synthetic_output is not None else None,
            handoff_directory=self.plan015_handoff_directory,
            episode_id=episode_id, role=role,
            config={
                "repository_root": str(Path(__file__).resolve().parents[2]),
                "authorization_mode": "PRODUCT", "execution_interface": "PLAN015_EPISODE_TERMINAL",
                "stage": f"PLAN015_{schema.upper()}",
                "context_references": [], "prompt_id": contract["prompt_id"], "execution_family": "AGENT_HARNESS",
                **config,
            },
        )
        if imported_result is not None:
            try:
                bound, runtime_run_id = _bind_runtime_fields(
                    request,
                    editorial_only_payload(imported_result.output, schema),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise StorageError(f"PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_BINDING_INVALID:{schema}:{exc}") from exc
            violations = validate_editorial_payload(editorial_only_payload(bound, schema), schema)
            if violations:
                raise StorageError(
                    f"PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_INVALID:{schema}:" + ";".join(violations)
                )
            return _Plan015StageResult(bound, runtime_run_id or imported_result.run_id)
        result = execute(request)
        if result.status is ExecutionStatus.HANDOFF_PREPARED:
            raise _Plan015HandoffPending(schema, result)
        if result.status is not ExecutionStatus.SUCCEEDED or not isinstance(result.output, dict):
            raise StorageError(f"PLAN015_HF02_STAGE_BLOCKED:{schema}:{result.error}")
        return result

    @staticmethod
    def _script_manifest(script: Mapping[str, Any], plan: Mapping[str, Any], status: str) -> dict[str, Any]:
        return {
            "script_id": script["script_id"], "version": script["artifact_version"],
            "checksum": script["checksum"], "narrative_plan_version": plan["artifact_version"], "status": status,
        }

    def _downstream_binding(self, kind: str, payload: Mapping[str, Any], filename: str) -> dict[str, Any]:
        if kind in {"script_draft", "edited_script"}:
            artifact_id, version, checksum = payload["script_id"], payload["artifact_version"], payload["checksum"]
        elif kind in {"script_version_manifest", "edited_script_version_manifest"}:
            artifact_id, version, checksum = payload["script_id"], payload["version"], payload["checksum"]
        elif kind == "editorial_edit_report":
            artifact_id, version, checksum = payload["output_artifact_id"], payload["output_version"], payload["output_checksum"]
        elif kind == "final_editorial_audit":
            artifact_id, version, checksum = payload["artifact_id"], payload["script_version"], payload["script_checksum"]
        else:
            artifact_id, version, checksum = payload["artifact_id"], payload["script_version"], payload["script_checksum"]
        return {"artifact_id": str(artifact_id), "artifact_version": str(version), "checksum": str(checksum), "artifact_path": filename}

    def import_result(self, episode_id: str, result_path: str | Path) -> dict[str, Any]:
        """Import one external handoff result through the active workflow."""
        preflight = getattr(self.workflow, "preflight", None)
        if callable(preflight):
            preflight()
        current = self.store.resume(episode_id)
        if current["entry"].get("estado") == self.store.ADMINISTRATIVE_CLOSED_INDEX_STATUS:
            raise StorageError("EPISODE_ADMINISTRATIVELY_CLOSED: no se importa resultado")
        try:
            external_payload = json.loads(Path(result_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"ROUNDTRIP_RESULT_INVALID:{exc}") from exc
        if isinstance(external_payload, dict) and external_payload.get("capability_id") == "EXTEND_01_RESEARCH_V2_REAL_E2E":
            if str(external_payload.get("episode_id") or "") != episode_id:
                raise StorageError("RESEARCH_ROUNDTRIP_IMPORT_BLOCKED:EPISODE_BINDING_MISMATCH")
            from src.application.research_m7 import ResearchM7Error, import_and_resume_external_research

            try:
                resumed = import_and_resume_external_research(self.store, result_path)
            except ResearchM7Error as exc:
                raise StorageError(f"RESEARCH_ROUNDTRIP_IMPORT_BLOCKED:{exc}") from exc
            workflow_path = Path(current["folder"]) / "workflow_state.json"
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
            if isinstance(workflow, dict):
                updated = {
                    **workflow,
                    "status": "LEGITIMATE_STOP",
                    "stop_boundary": "RESEARCH_EXTERNAL_COGNITIVE_SEAM",
                    "next_action": "IMPORT_EXTERNAL_COGNITIVE_RESULT",
                    "research_route": resumed.get("resume", resumed),
                }
                handle = EpisodeHandle(
                    episode_id,
                    current["entry"].get("slug", "episodio"),
                    Path(current["folder"]),
                    self.store.index_path,
                )
                self.store.record_workflow(handle, updated)
            return self.store.resume(episode_id)
        folder = Path(current["folder"])
        workflow_path = folder / "workflow_state.json"
        workflow_state = self._read_object(workflow_path, "WORKFLOW_STATE") if workflow_path.is_file() else {}
        if workflow_state.get("workflow_id") == "PLAN015_DOWNSTREAM_ROUNDTRIP":
            if workflow_state.get("status") != "PENDING_EXTERNAL_RESULT" and not (
                workflow_state.get("status") == "LEGITIMATE_STOP"
                and workflow_state.get("stop_boundary") == "PLAN015_DOWNSTREAM_EXTERNAL_RESULT_IMPORTED"
            ):
                raise StorageError("PLAN015_DOWNSTREAM_IMPORT_BLOCKED:NO_PENDING_HANDOFF")
            package_path = Path(str(workflow_state.get("handoff_package_ref") or ""))
            if not package_path.is_file():
                raise StorageError("PLAN015_DOWNSTREAM_HANDOFF_PACKAGE_MISSING")
            package = self._read_object(package_path, "PLAN015_DOWNSTREAM_HANDOFF_PACKAGE")
            expected = {
                "episode_id": episode_id,
                "handoff_id": workflow_state.get("handoff_id"),
                "package_checksum": workflow_state.get("handoff_package_checksum"),
                "stage": workflow_state.get("stage"),
                "role": workflow_state.get("role"),
            }
            if any(package.get(field) != value for field, value in expected.items()):
                raise StorageError("PLAN015_DOWNSTREAM_HANDOFF_BINDING_STALE")
            try:
                content = AgentHandoffProvider().import_result(package_path, Path(result_path))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, PermissionError, ValueError) as exc:
                raise StorageError(f"PLAN015_DOWNSTREAM_IMPORT_BLOCKED:{exc}") from exc
            if not isinstance(content, dict):
                raise StorageError("PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_INVALID")
            schema = str(workflow_state.get("output_schema") or "")
            if package.get("output_schema") != schema or package.get("stage") != f"PLAN015_{schema.upper()}":
                raise StorageError("PLAN015_DOWNSTREAM_OUTPUT_SCHEMA_BINDING_INVALID")
            try:
                materialized = editorial_only_payload(content, schema)
                projection_violations = validate_editorial_payload(materialized, schema)
            except (KeyError, TypeError, ValueError) as exc:
                raise StorageError(f"PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_INVALID:{exc}") from exc
            if projection_violations:
                raise StorageError(
                    "PLAN015_DOWNSTREAM_IMPORTED_OUTPUT_INVALID:" + ";".join(projection_violations)
                )
            handle = EpisodeHandle(
                episode_id,
                current["entry"].get("slug", "episodio"),
                folder,
                self.store.index_path,
            )
            imported_state = {
                **workflow_state,
                "status": "LEGITIMATE_STOP",
                "stop_boundary": "PLAN015_DOWNSTREAM_EXTERNAL_RESULT_IMPORTED",
                "next_action": "RESUME_DOWNSTREAM_EDITORIAL_CHAIN",
                "result_run_id": external_payload.get("result_run_id"),
                "result_checksum": external_payload.get("output_checksum"),
                "real_cognitive_execution": "IMPORTED_AND_VALIDATED",
            }
            status = self.store.record_roundtrip_result(
                handle,
                envelope=external_payload,
                workflow_state=imported_state,
                materialized_output=materialized,
            )
            if status not in {"PERSISTED", "ALREADY_IMPORTED"}:
                raise StorageError("PLAN015_DOWNSTREAM_IMPORT_PERSISTENCE_FAILED")
            return self.store.resume(episode_id)
        importer = getattr(self.workflow, "import_result", None)
        if not callable(importer):
            raise StorageError("ROUNDTRIP_IMPORT_UNAVAILABLE")
        handle = EpisodeHandle(
            episode_id,
            current["entry"].get("slug", "episodio"),
            folder,
            self.store.index_path,
        )
        outcome = importer(handle, Path(result_path))
        if not isinstance(outcome, dict):
            raise StorageError("ROUNDTRIP_IMPORT_INVALID_OUTCOME")
        if outcome.get("status") == "ALREADY_IMPORTED":
            return self.store.resume(episode_id)
        return self.store.resume(episode_id)

    def import_external_result(self, result_path: str | Path) -> dict[str, Any]:
        """Route a user-supplied result to its persisted episode and import it."""
        path = Path(result_path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"ROUNDTRIP_RESULT_INVALID:{exc}") from exc
        if not isinstance(payload, dict):
            raise StorageError("ROUNDTRIP_RESULT_INVALID: el resultado debe ser un objeto JSON.")
        episode_id = payload.get("episode_id")
        if not isinstance(episode_id, str) or not episode_id.strip():
            raise StorageError("ROUNDTRIP_RESULT_INVALID: falta episode_id.")
        return self.import_result(episode_id.strip(), path)

    def submit_topic_belonging_evidence(
        self,
        episode_id: str,
        evidence_path: str | Path,
    ) -> dict[str, Any]:
        """Submit owner-provided evidence through the Topic Belonging recovery port."""
        preflight = getattr(self.workflow, "preflight", None)
        if callable(preflight):
            preflight()
        current = self.store.resume(episode_id)
        if not current.get("folder"):
            raise StorageError("TOPIC_BELONGING_REASSESSMENT_EPISODE_MISSING")
        try:
            evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"REASSESSMENT_EVIDENCE_INVALID:{exc}") from exc
        folder = Path(current["folder"])
        handle = EpisodeHandle(
            episode_id,
            current["entry"].get("slug", "episodio"),
            folder,
            self.store.index_path,
        )
        workflow = getattr(self.workflow, "submit_additional_evidence", None)
        if not callable(workflow):
            raise StorageError("TOPIC_BELONGING_REASSESSMENT_UNAVAILABLE")
        outcome = workflow(handle, evidence)
        outcome = self._advance_plan015_research(handle, outcome)
        self.store.record_workflow(handle, outcome)
        return self.store.resume(episode_id)

    def prepare_topic_belonging_reassessment(self, episode_id: str) -> dict[str, Any]:
        """Create the next reviewer handoff after evidence has been persisted."""
        preflight = getattr(self.workflow, "preflight", None)
        if callable(preflight):
            preflight()
        current = self.store.resume(episode_id)
        if not current.get("folder"):
            raise StorageError("TOPIC_BELONGING_REASSESSMENT_EPISODE_MISSING")
        folder = Path(current["folder"])
        handle = EpisodeHandle(
            episode_id,
            current["entry"].get("slug", "episodio"),
            folder,
            self.store.index_path,
        )
        workflow = getattr(self.workflow, "prepare_reassessment", None)
        if not callable(workflow):
            raise StorageError("TOPIC_BELONGING_REASSESSMENT_UNAVAILABLE")
        outcome = workflow(handle)
        outcome = self._advance_plan015_research(handle, outcome)
        self.store.record_workflow(handle, outcome)
        return {"state": outcome, "folder": str(folder), "entry": current["entry"]}

    def archive_completed_topic_belonging_handoffs(
        self,
        episode_id: str,
        history_root: str | Path,
    ) -> dict[str, Any]:
        """Archive raw handoffs of a terminated execution into Historial.

        Future runs invoke this once the workflow reaches its technical STOP;
        pending handoffs stay visible in ``handoff/`` by design.
        """
        current = self.store.resume(episode_id)
        if not current.get("folder"):
            raise StorageError("HANDOFF_ARCHIVE_EPISODE_MISSING")
        folder = Path(current["folder"])
        handle = EpisodeHandle(
            episode_id,
            current["entry"].get("slug", "episodio"),
            folder,
            self.store.index_path,
        )
        archiver = getattr(self.workflow, "archive_completed_handoffs", None)
        if not callable(archiver):
            raise StorageError("HANDOFF_ARCHIVE_UNAVAILABLE")
        return archiver(handle, Path(history_root))

    def _archive_terminated_handoffs(self, handle: EpisodeHandle) -> None:
        """Archive raw handoffs automatically once the STOP state is persisted.

        Runs strictly after IMPORT → VALIDATE → PERSIST → UPDATE STATE. Only
        workflows exposing ``archive_completed_handoffs`` trigger it; pending
        executions are left visible by the archiver itself. Archive failures
        propagate as explicit operational errors without deleting sources.
        """
        archiver = getattr(self.workflow, "archive_completed_handoffs", None)
        if not callable(archiver):
            return
        channel_path = getattr(self.store, "channel_path", None)
        if channel_path is None:
            raise StorageError("HANDOFF_ARCHIVE_CHANNEL_PATH_MISSING")
        archiver(handle, Path(channel_path) / "Historial")

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

    def _advance_plan015_research(
        self,
        handle: EpisodeHandle,
        workflow_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Continue an approved PLAN015 topic stop into the canonical Research seam."""
        if not isinstance(workflow_state, dict) or workflow_state.get("status") != "TOPIC_BELONGING_TECHNICAL_STOP":
            return workflow_state
        boundary = getattr(self.workflow, "boundary", None)
        if str(getattr(boundary, "authorization_mode", "MISSION") or "MISSION").upper() != "PRODUCT":
            return workflow_state
        effective_bundle_reader = getattr(self.workflow, "_effective_topic_bundle", None)
        if not callable(effective_bundle_reader):
            raise StorageError("PLAN015_RESEARCH_CONTINUATION_BLOCKED:EFFECTIVE_TOPIC_DECISION_UNAVAILABLE")
        try:
            resolved = effective_bundle_reader(handle)
            decision = resolved["decision"]
            topic_input = resolved["topic_input"]
            assessment = resolved["assessment"]
            effective_gate = resolved["gate"]
        except Exception as exc:
            raise StorageError(f"PLAN015_RESEARCH_CONTINUATION_BLOCKED:EFFECTIVE_TOPIC_DECISION_INVALID:{exc}") from exc
        gate = effective_gate
        decision_outcome = str(decision.get("decision") or "")
        if decision_outcome == "APPROVE_WITH_CONDITIONS":
            resolution, condition_gate = self._resolve_topic_conditions(
                handle,
                decision=decision,
                assessment=assessment,
                topic_input=topic_input,
                decision_ref=str(resolved.get("decision_ref") or ""),
                decision_checksum=str(resolved.get("decision_checksum") or ""),
            )
            if resolution is None or condition_gate is None:
                return {
                    **workflow_state,
                    "status": "LEGITIMATE_STOP",
                    "stop_boundary": "TOPIC_CONDITIONS_PENDING",
                    "next_action": "RESOLVE_TOPIC_CONDITIONS",
                    "topic_conditions_status": "PENDING",
                    "topic_conditions": copy.deepcopy(decision.get("conditions", [])),
                    "downstream_execution_started": False,
                }
            gate = condition_gate
            research_boundary_allowed = gate.get("topic_approved") is True
        else:
            pre_research_block = all(
                str(violation).startswith("PRE_B5_I1_")
                for violation in effective_gate.get("violations", [])
            )
            research_boundary_allowed = (
                decision_outcome == "APPROVE"
                and effective_gate.get("decision") == decision_outcome
                and bool(effective_gate.get("violations"))
                and pre_research_block
            )
        if decision_outcome not in {"APPROVE", "APPROVE_WITH_CONDITIONS"} or not research_boundary_allowed:
            return workflow_state
        if workflow_state.get("research_route") is not None:
            return workflow_state
        persisted_validator = getattr(self.workflow, "_validate_persisted_vertical", None)
        if (
            decision_outcome != "APPROVE_WITH_CONDITIONS"
            and int(resolved.get("source_attempt") or 1) == 1
            and callable(persisted_validator)
        ):
            try:
                persisted_validator(handle)
            except Exception as exc:
                raise StorageError(f"PLAN015_RESEARCH_CONTINUATION_BLOCKED:TOPIC_VERTICAL_INVALID:{exc}") from exc

        from src.application.research_m7 import (
            ExternalResearchCognitiveExecutor,
            PersistedResearchEpisode,
            ProductiveResearchStageAdapters,
            RealResearchRoutePreparation,
            ResearchM7Error,
        )

        try:
            episode = PersistedResearchEpisode.load(self.store, handle.episode_id)
            preparation = RealResearchRoutePreparation.from_mapping(
                {
                    "episode_id": handle.episode_id,
                    "topic": str(episode.human_input.get("content") or ""),
                    "question": episode.human_input.get("initial_question"),
                    "budget_limit": 1.0,
                    "max_iterations": 1,
                    "max_retries": 0,
                    "timeout_seconds": 300,
                    "handoff_directory": "handoff",
                    "authorization_mode": "PRODUCT",
                }
            )
            executor = ExternalResearchCognitiveExecutor(episode, preparation)
            research_result = preparation.run_canonical_vertical(
                ProductiveResearchStageAdapters(
                    episode,
                    cognitive_executor=executor,
                ).stage_runners()
            )
        except ResearchM7Error as exc:
            raise StorageError(f"PLAN015_RESEARCH_CONTINUATION_BLOCKED:{exc}") from exc

        return {
            **workflow_state,
            "workflow_id": "PLAN015_TOPIC_TO_RESEARCH_VERTICAL",
            "status": "LEGITIMATE_STOP",
            "downstream_execution_started": True,
            "stop_boundary": "RESEARCH_EXTERNAL_COGNITIVE_SEAM",
            "next_action": "IMPORT_EXTERNAL_COGNITIVE_RESULT",
            "topic_decision_ref": str(resolved.get("decision_ref") or ""),
            "topic_decision_checksum": str(resolved.get("decision_checksum") or ""),
            "topic_decision_source_attempt": int(resolved.get("source_attempt") or 1),
            **(
                {
                    "topic_conditions_status": "SATISFIED",
                    "topic_conditions_resolution_ref": "episode:%s/topic_conditions_resolution.json" % handle.episode_id,
                }
                if decision_outcome == "APPROVE_WITH_CONDITIONS"
                else {}
            ),
            "research_route": research_result,
        }

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
