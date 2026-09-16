"""PLAN012 M7 canonical Research V2 E2E coordinator.

M7 owns only coordination. B2, M4, M5 and M6 remain the authorities for
their contracts, validation, persistence, lineage, provenance and gates.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import M3_REQUIRED_INPUT_KINDS, _validate_m3_input_artifacts, manifest_checksum
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.registry import register_external_output, register_software_outputs
from src.ai.role_execution import build_model_prompt
from src.application.contracts import HumanInput, InputValidationError
from src.application.interaction import HumanDecision, HumanDecisionRequest, validate_human_decision
from src.application.research_b2 import ResearchB2NoProgressGuard, ResearchB2Orchestrator, ResearchB2Persistence, SoftwareAcquisitionAdapter, _checksum
from src.application.research_b3 import ResearchB3Error, ResearchB3Orchestrator, ResearchB3Persistence
from src.application.research_b4 import ResearchB4Orchestrator, ResearchB4Persistence
from src.application.research_m7_fixture import SyntheticResearchExecutor, b5_i3_transversal_fixtures, source_report
from src.application.research_planning import ResearchPlanningError, ResearchPlanningService
from src.application.storage import EpisodeHandle, StorageError, VaultEpisodeStore, _write_json_atomic
from src.core.contract_validation import validate_against_schema, validate_research_plan, validate_research_ready_manifest
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.gate_result import GateResult
from src.core.gate_runtime import validate_gate_result
from src.core.invalidation import InvalidationEngine

M7_VERSION = "2.0.0"
STAGES = ("INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6", "B5_I3_HANDOFF")
NARRATIVE_FIELDS = {"viewer_journey", "narrative_plan", "opening_design", "closing_design", "hook", "climax", "cta", "pacing", "title", "thumbnail"}
REAL_RESEARCH_CAPABILITY = "EXTEND_01_RESEARCH_V2_REAL_E2E"
REAL_RESEARCH_TERMINAL_STAGE = "RESEARCH_READY"
REAL_RESEARCH_CANONICAL_STAGES = ("B2", "M4", "M5", "M6")
REAL_RESEARCH_FORBIDDEN_POST_TERMINAL_STAGES = (
    "B5_I3_HANDOFF",
    "NARRATIVE",
    "SCRIPT_PRODUCT",
    "YOUTUBE_ADAPTATION",
)
REAL_EXTERNAL_HANDOFF_AUTHORIZATION = "plans/extend_01/m2/b4_handoff/mission-authorization.json"
REAL_EXTERNAL_HANDOFF_CONTRACT = "plans/extend_01/m2/b4_handoff/mission_contract.json"
REAL_EXTERNAL_HANDOFF_DIRECTORY = Path("plans/extend_01/m2/b4_handoff/packages")
REAL_EXTERNAL_HANDOFF_STATE_FILENAME = "research_external_handoff.json"
REAL_EXTERNAL_RESULT_FILENAME = "research_external_result.json"


class ResearchM7Error(RuntimeError):
    """Fail-closed M7 coordination error."""


class ExternalCognitiveHandoffPending(ResearchM7Error):
    """The canonical route stopped after preparing one external task."""

    propagate_through_execution_boundary = True

    propagate_through_execution_boundary = True

    def __init__(self, *, package_path: Path, handoff_id: str, stage: str):
        self.package_path = package_path
        self.handoff_id = handoff_id
        self.stage = stage
        super().__init__(f"PENDING_EXTERNAL_COGNITIVE_RESULT:{stage}:{handoff_id}")


class HumanDecisionPending(ResearchM7Error):
    """The canonical route is waiting for an OWNER response at M4."""

    propagate_through_execution_boundary = True

    def __init__(self, request: HumanDecisionRequest):
        self.request = request
        super().__init__(f"WAITING_FOR_HUMAN_DECISION:{request.request_id}")


@dataclass(frozen=True)
class PersistedResearchEpisode:
    """Canonical Research V2 inputs loaded from one persisted episode only."""

    store: VaultEpisodeStore
    handle: EpisodeHandle
    human_input: dict[str, Any]
    brief: dict[str, Any]
    channel_context: dict[str, Any]
    source_access: dict[str, Any]

    @classmethod
    def load(cls, store: VaultEpisodeStore, episode_id: str) -> "PersistedResearchEpisode":
        try:
            resumed = store.resume(episode_id)
            folder = Path(resumed["folder"])
            state = dict(resumed["state"])
            entry = dict(resumed["entry"])
        except (StorageError, KeyError, TypeError) as exc:
            raise ResearchM7Error("REAL_ROUTE_EPISODE_NOT_AVAILABLE") from exc
        if state.get("episode_id") != episode_id:
            raise ResearchM7Error("REAL_ROUTE_EPISODE_IDENTITY_MISMATCH")
        human_payload = _read(folder / "00_human_input.json")
        if not isinstance(human_payload, Mapping):
            raise ResearchM7Error("REAL_ROUTE_PERSISTED_HUMAN_INPUT_INVALID")
        try:
            human_input = HumanInput.from_dict(dict(human_payload))
        except (InputValidationError, TypeError, ValueError) as exc:
            raise ResearchM7Error("REAL_ROUTE_PERSISTED_HUMAN_INPUT_INVALID") from exc
        human = human_input.to_dict()
        if not str(human.get("content") or "").strip():
            raise ResearchM7Error("REAL_ROUTE_PERSISTED_TOPIC_REQUIRED")
        profile = load_active_profile_authority()
        binding = state.get("profile_binding")
        if isinstance(binding, Mapping) and any(
            binding.get(key) != profile.get(source)
            for key, source in (
                ("profile_id", "ACTIVE_PROFILE_ID"),
                ("profile_version", "ACTIVE_PROFILE_VERSION"),
                ("profile_checksum", "profile_checksum"),
            )
        ):
            raise ResearchM7Error("REAL_ROUTE_EPISODE_PROFILE_BINDING_STALE")
        paths = {
            "brief": folder / "research_episode_brief.json",
            "channel_context": folder / "research_channel_context.json",
            "source_access": folder / "research_source_access.json",
        }
        existing = {name: path.is_file() for name, path in paths.items()}
        if any(existing.values()) and not all(existing.values()):
            raise ResearchM7Error("REAL_ROUTE_PRE_RESEARCH_PARTIAL_PERSISTENCE")
        if not all(existing.values()):
            planning = ResearchPlanningService()
            handoff_path = folder / "01_editorial_intake_handoff.json"
            handoff = _read(handoff_path) if handoff_path.is_file() else {}
            if not isinstance(handoff, Mapping):
                raise ResearchM7Error("REAL_ROUTE_PERSISTED_HANDOFF_INVALID")
            intended_use = cls._persisted_intended_use(human_payload, handoff)
            material_refs = cls._owner_material_refs(
                folder, episode_id, declared=human.get("material_refs", []),
            )
            brief = planning.build_episode_brief(
                episode_id=episode_id,
                topic=str(human["content"]),
                question=human.get("initial_question"),
                intended_use=intended_use,
                profile=profile,
                work_intents=[dict(item) for item in human.get("work_intents", [])],
                selection_authority=str(human.get("selection_authority") or "NOT_DECLARED"),
                material_refs=[str(item["material_ref"]) for item in material_refs],
                owner_restrictions=cls._owner_restrictions(human),
                brief_version="2.0.0",
                origin_ref=f"human-input:{episode_id}",
            )
            channel_context = planning.build_channel_context(
                episode_id=episode_id, profile=profile, origin_ref=f"human-input:{episode_id}",
            )
            source_access = planning.build_source_access(
                episode_id=episode_id,
                brief_version=brief["brief_version"],
                materials=material_refs,
                origin_refs=[f"human-input:{episode_id}"],
            )
            handle = EpisodeHandle(episode_id, str(entry.get("slug") or "episodio"), folder, store.index_path)
            store.record_research_preparation(
                handle, brief=brief, channel_context=channel_context, source_access=source_access,
            )
        payloads = {name: _read(path) for name, path in paths.items()}
        for name, schema in (
            ("brief", "episode_brief"),
            ("channel_context", "research_channel_context"),
            ("source_access", "research_source_access"),
        ):
            if not isinstance(payloads[name], Mapping) or validate_against_schema(dict(payloads[name]), schema):
                raise ResearchM7Error(f"REAL_ROUTE_PERSISTED_{name.upper()}_INVALID")
        if not str(payloads["brief"].get("objetivo") or "").strip():
            raise ResearchM7Error("REAL_ROUTE_PRE_RESEARCH_INTENDED_USE_REQUIRED")
        return cls(
            store=store,
            handle=EpisodeHandle(episode_id, str(entry.get("slug") or "episodio"), folder, store.index_path),
            human_input=copy.deepcopy(dict(human)),
            brief=copy.deepcopy(dict(payloads["brief"])),
            channel_context=copy.deepcopy(dict(payloads["channel_context"])),
            source_access=copy.deepcopy(dict(payloads["source_access"])),
        )

    @staticmethod
    def _persisted_intended_use(human: Mapping[str, Any], handoff: Mapping[str, Any]) -> str | None:
        field_bindings = handoff.get("field_bindings") if isinstance(handoff.get("field_bindings"), Mapping) else {}
        candidates = (
            human.get("intended_use"),
            human.get("research_intended_use"),
            handoff.get("intended_use"),
            handoff.get("research_intended_use"),
            field_bindings.get("intended_use"),
            field_bindings.get("research_intended_use"),
        )
        for candidate in candidates:
            value = str(candidate or "").strip()
            if value:
                return value
        # Leave derivation to ResearchPlanningService so the persisted brief
        # records DERIVED_STANDARD rather than misclassifying it as explicit.
        return None

    @staticmethod
    def _owner_restrictions(human: Mapping[str, Any]) -> list[str]:
        restrictions: list[str] = []
        for item in human.get("user_instructions", []):
            if not isinstance(item, Mapping):
                raise ResearchM7Error("REAL_ROUTE_OWNER_INSTRUCTIONS_INVALID")
            category = str(item.get("category") or "").strip().upper()
            text = str(item.get("text") or "").strip()
            if not category or not text:
                raise ResearchM7Error("REAL_ROUTE_OWNER_INSTRUCTIONS_INVALID")
            restrictions.append(f"{category}: {text}")
        return restrictions

    @staticmethod
    def _owner_material_refs(
        folder: Path,
        episode_id: str,
        *,
        declared: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    ) -> list[dict[str, Any]]:
        provenance_path = folder / "research_material_provenance.json"
        materials: list[dict[str, Any]] = []
        by_ref: dict[str, dict[str, Any]] = {}
        if provenance_path.is_file():
            provenance = _read(provenance_path)
            if not isinstance(provenance, Mapping) or provenance.get("episode_id") != episode_id:
                raise ResearchM7Error("REAL_ROUTE_OWNER_MATERIAL_PROVENANCE_INVALID")
            for item in provenance.get("records", []):
                if not isinstance(item, Mapping):
                    raise ResearchM7Error("REAL_ROUTE_OWNER_MATERIAL_PROVENANCE_INVALID")
                snapshot = folder / str(item.get("snapshot_path") or "")
                expected = str(item.get("checksum") or "")
                if not snapshot.is_file() or hashlib.sha256(snapshot.read_bytes()).hexdigest() != expected:
                    raise ResearchM7Error("REAL_ROUTE_OWNER_MATERIAL_STALE")
                ref = str(item.get("material_ref") or "").strip()
                if not ref:
                    raise ResearchM7Error("REAL_ROUTE_OWNER_MATERIAL_PROVENANCE_INVALID")
                by_ref[ref] = {
                    "material_ref": ref,
                    "material_kind": str(item.get("material_kind") or "").upper(),
                    "availability": "AVAILABLE_LOCAL",
                    "access_mode": "DIRECT",
                    "artifact_ref": str(item.get("snapshot_path")),
                    "checksum": expected,
                    "limitations": ["Snapshot local; no búsqueda web ni fetch HTTP."],
                    "provenance_ref": f"{provenance_path.name}#{expected}",
                }
        for item in declared or []:
            if not isinstance(item, Mapping):
                raise ResearchM7Error("REAL_ROUTE_OWNER_MATERIAL_REFERENCE_INVALID")
            ref = str(item.get("material_ref") or "").strip()
            kind = str(item.get("material_kind") or "").strip().upper()
            if not ref or kind not in {"TEXT", "MARKDOWN", "JSON", "TRANSCRIPT", "OTHER"}:
                raise ResearchM7Error("REAL_ROUTE_OWNER_MATERIAL_REFERENCE_INVALID")
            by_ref.setdefault(ref, {
                "material_ref": ref,
                "material_kind": kind,
                "availability": "REFERENCED_NOT_ACQUIRED",
                "access_mode": "NONE",
                "artifact_ref": None,
                "checksum": None,
                "limitations": ["Referencia OWNER sin snapshot local; no búsqueda web ni fetch HTTP."],
                "provenance_ref": f"human-input:{episode_id}:material:{ref}",
            })
        materials.extend(by_ref.values())
        return materials

    def context(self) -> dict[str, Any]:
        return {
            "topic": str(self.brief["tema"]),
            "brief": copy.deepcopy(self.brief),
            "channel_context": copy.deepcopy(self.channel_context),
            "source_access": copy.deepcopy(self.source_access),
        }


class ExternalResearchCognitiveExecutor:
    """Transport one coordinator-emitted cognitive seam to the external side."""

    def __init__(self, episode: PersistedResearchEpisode, preparation: "RealResearchRoutePreparation"):
        self.episode = episode
        self.preparation = preparation

    @property
    def state_path(self) -> Path:
        return self.episode.handle.folder / REAL_EXTERNAL_HANDOFF_STATE_FILENAME

    def _existing_pending(self) -> ExternalCognitiveHandoffPending | None:
        if not self.state_path.is_file():
            return None
        try:
            state = _read(self.state_path)
        except (OSError, ValueError):
            return None
        if not isinstance(state, Mapping) or state.get("status") != "PENDING_EXTERNAL_COGNITIVE_RESULT":
            return None
        package_ref = Path(str(state.get("handoff_package_ref") or ""))
        if not package_ref.is_file():
            return None
        return ExternalCognitiveHandoffPending(
            package_path=package_ref,
            handoff_id=str(state.get("handoff_id") or ""),
            stage=str(state.get("stage") or ""),
        )

    def _consume_imported_result(self, request: Any) -> Any | None:
        """Return the one result authorized for the current pending seam.

        Import and resume are deliberately state-bound: an imported payload is
        consumable only when its stage is the stage emitted by this exact
        coordinator request.  Consuming it is persisted before returning so a
        restart cannot replay the same external result.
        """
        if not self.state_path.is_file():
            return None
        state = _read(self.state_path)
        if not isinstance(state, Mapping) or state.get("status") != "IMPORTED_EXTERNAL_COGNITIVE_RESULT":
            return None
        if str(state.get("imported_stage") or state.get("stage") or "") != str(getattr(request, "stage", "")):
            return None
        result_path = self.episode.handle.folder / REAL_EXTERNAL_RESULT_FILENAME
        if not result_path.is_file():
            raise ResearchM7Error("ROUNDTRIP_RESULT_BLOCKED:IMPORTED_RESULT_MISSING")
        result = _read(result_path)
        output = result.get("output") if isinstance(result, Mapping) else None
        if not isinstance(output, (Mapping, list)) or (isinstance(output, list) and not output):
            raise ResearchM7Error("ROUNDTRIP_RESULT_BLOCKED:IMPORTED_OUTPUT_MISSING")
        completed = list(state.get("completed_stages", []))
        imported_stage = str(state.get("imported_stage") or state.get("stage") or "")
        if imported_stage and imported_stage not in completed:
            completed.append(imported_stage)
        consumed = dict(state)
        consumed.update({
            "status": "RESUMING_EXTERNAL_COGNITIVE_RESULT",
            "imported_result_consumed": True,
            "completed_stages": completed,
            "next_action": "RESUME_RESEARCH_V2",
        })
        _write_json_atomic(self.state_path, consumed)
        return copy.deepcopy(output)

    @staticmethod
    def _resolve_persisted_input_path(
        episode: PersistedResearchEpisode,
        item: Mapping[str, Any],
    ) -> Path | None:
        """Resolve a canonical persisted artifact when a stage ref has no path.

        B2/B3 deliberately keep their lineage refs logical (artifact id/kind/
        checksum) rather than copying filesystem paths into every downstream
        request.  The external handoff still needs a real, already-persisted
        input file.  Resolve only against the canonical Research V2 stores and
        only for known artifact kinds; never invent a source or fall back to a
        caller-controlled path.
        """
        artifact_id = str(item.get("artifact_id") or "")
        artifact_kind = str(item.get("artifact_kind") or "")
        if not artifact_id or not artifact_kind:
            return None
        b2 = episode.handle.folder / "research_v2" / "b2"
        b3 = episode.handle.folder / "research_v2" / "b3"
        # Prefer the later M5 artifact when the logical id identifies it;
        # otherwise use the canonical B2/M4 materialization for the kind.
        candidates: list[Path] = []
        if ":M5:" in artifact_id or ":POST_DEEP" in artifact_id:
            candidates.extend((b3 / "claims_ledger_m5.json", b3 / "research_comparison_m5_post_deep.json"))
        candidates.extend({
            "ResearchPack": (b3 / "deep_phenomenon_research.json", b2 / "phenomenon_base_research.json"),
            "WorkLifecycle": (b2 / "work_discovery.json",),
            "WorkResearchDossierCollection": (b3 / "deep_work_research.json", b2 / "preliminary_fidelity.json", b2 / "base_research_pool.json"),
            "WorkResearchDossier": (b2 / "preliminary_fidelity.json", b2 / "base_research_pool.json"),
            "ThesisArtifact": (b3 / "refined_thesis_m5.json", b2 / "provisional_thesis.json"),
            "ResearchComparison": (b3 / "research_comparison_m5_post_deep.json", b2 / "research_comparison.json"),
            "B2DeepeningTargets": (b2 / "research_b2_execution.json",),
            "SelectionAuthority": (b3 / "m4_selection_decision.json", b3 / "m4_delegation_decision.json"),
            "ClaimsLedger": (b3 / "claims_ledger_m5.json",),
            "RefinedThesis": (b3 / "refined_thesis_m5.json",),
            "SourceAccessAndEvidenceReport": (b3 / "source_access_and_evidence_report_m5_refined.json", b3 / "source_access_and_evidence_report_m4_deep.json"),
        }.get(artifact_kind, ()))
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _input_artifacts(
        episode: PersistedResearchEpisode,
        request: Any,
    ) -> list[InputArtifact]:
        references = list(getattr(request, "input_artifacts", ()) or ())
        if not references:
            references = [
                {
                    "artifact_kind": "episode_brief",
                    "artifact_id": f"{episode.handle.episode_id}:episode_brief",
                    "path": str(episode.handle.folder / "research_episode_brief.json"),
                },
                {
                    "artifact_kind": "research_channel_context",
                    "artifact_id": f"{episode.handle.episode_id}:research_channel_context",
                    "path": str(episode.handle.folder / "research_channel_context.json"),
                },
                {
                    "artifact_kind": "research_source_access",
                    "artifact_id": f"{episode.handle.episode_id}:research_source_access",
                    "path": str(episode.handle.folder / "research_source_access.json"),
                },
            ]
        artifacts: list[InputArtifact] = []
        for item in references:
            if not isinstance(item, Mapping):
                raise ResearchM7Error("EXTERNAL_HANDOFF_INPUT_REFERENCE_INVALID")
            path = Path(str(item.get("path") or ""))
            if not path.is_file():
                resolved = ExternalResearchCognitiveExecutor._resolve_persisted_input_path(episode, item)
                if resolved is not None:
                    path = resolved
            if not path.is_file():
                raise ResearchM7Error("EXTERNAL_HANDOFF_INPUT_NOT_AVAILABLE")
            artifacts.append(
                InputArtifact(
                    str(item.get("artifact_kind") or "COGNITIVE_INPUT"),
                    str(item.get("artifact_id") or ""),
                    path,
                    str(item.get("producer_run_id") or ""),
                    str(item.get("artifact_version") or ""),
                )
            )
        return artifacts

    def __call__(self, request: Any) -> Any:
        existing = self._existing_pending()
        if existing is not None:
            raise existing
        imported = self._consume_imported_result(request)
        if imported is not None:
            return imported
        prepared = getattr(request, "prepared_contract", None)
        if not isinstance(prepared, Mapping):
            raise ResearchM7Error("EXTERNAL_HANDOFF_PREPARED_CONTRACT_REQUIRED")
        input_artifacts = self._input_artifacts(self.episode, request)
        run_id = f"RUN-EXTEND01-HANDOFF-{uuid4().hex}"
        mission_id = ""
        if self.preparation.mission_authorization_path:
            try:
                authorization_payload = _read(self.preparation.mission_authorization_path)
                mission_id = str(authorization_payload.get("mission_id") or "").strip()
            except ResearchM7Error:
                mission_id = ""
        if not mission_id:
            raise ResearchM7Error("REAL_ROUTE_MISSION_ID_UNRESOLVED")
        execution_request = ExecutionRequest(
            capability_id=REAL_RESEARCH_CAPABILITY,
            skill_id="extend_01_research_v2_real_e2e",
            skill_version=M7_VERSION,
            input_artifacts=input_artifacts,
            output_schema=str(request.output_schema),
            execution_mode="REAL",
            execution_route="agent_harness",
            execution_family="AGENT_HARNESS",
            timeout=float(self.preparation.timeout_seconds),
            handoff_directory=self.preparation.handoff_directory,
            episode_id=self.episode.handle.episode_id,
            role=str(getattr(request, "role_id", None) or "RESEARCH_AND_CURATION"),
            config={
                "repository_root": str(Path(__file__).resolve().parents[2]),
                "mission_repo_root": str(Path(__file__).resolve().parents[2]),
                "mission_authorization_path": self.preparation.mission_authorization_path,
                "mission_contract_path": self.preparation.mission_contract_path,
                "mission_id": mission_id,
                "mission_operation": "EXECUTE_CAPABILITY",
                "execution_interface": "MVP_REAL_E2E_TERMINAL",
                "execution_family": "AGENT_HARNESS",
                "stage": str(request.stage),
                "expected_return": str(request.output_schema),
                "expected_provider_or_agent": "OWNER_EXTERNAL_COGNITIVE_EXECUTOR",
                "prompt": build_model_prompt(dict(prepared)),
                "prompt_id": str(prepared.get("prompt_id") or ""),
                "prompt_version": str(prepared.get("prompt_version") or ""),
                "prompt_checksum": str(prepared.get("prompt_checksum") or ""),
                "prompt_input_checksum": str(prepared.get("input_checksum") or ""),
                "budget_limit": self.preparation.budget_limit,
                "max_iterations": self.preparation.max_iterations,
                "max_retries": self.preparation.max_retries,
                "timeout_seconds": self.preparation.timeout_seconds,
                "execution_controls": {
                    "budget_limit": self.preparation.budget_limit,
                    "max_iterations": self.preparation.max_iterations,
                    "max_retries": self.preparation.max_retries,
                    "timeout_seconds": self.preparation.timeout_seconds,
                    "unbounded_execution": False,
                    "telemetry": {
                        "calls": True,
                        "retries": True,
                        "failures": True,
                        "termination": True,
                        "tokens": "WHEN_AVAILABLE",
                        "cost": "WHEN_AVAILABLE",
                        "timestamps": True,
                        "executor_provider_model_runtime": "ACTUAL_METADATA_ONLY",
                    },
                },
            },
        )
        package_path = AgentHandoffProvider().prepare_external(
            execution_request,
            manifest_checksum(execution_request),
            run_id,
        )
        prior_state = _read(self.state_path) if self.state_path.is_file() else {}
        prior_completed = list(prior_state.get("completed_stages", [])) if isinstance(prior_state, Mapping) else []
        prior_lineage = {
            key: copy.deepcopy(prior_state[key])
            for key in ("research_plan_proposal", "research_plan", "provenance", "provenance_status", "producer_provenance", "external_cognitive_provenance", "auditor_provenance")
            if isinstance(prior_state, Mapping) and key in prior_state
        }
        _write_json_atomic(
            self.state_path,
            {
                **prior_lineage,
                "status": "PENDING_EXTERNAL_COGNITIVE_RESULT",
                "episode_id": self.episode.handle.episode_id,
                "capability_id": REAL_RESEARCH_CAPABILITY,
                "stage": str(request.stage),
                "handoff_id": run_id,
                "handoff_package_ref": str(package_path.resolve()),
                "handoff_package_checksum": json.loads(package_path.read_text(encoding="utf-8")).get("package_checksum"),
                "expected_return": str(request.output_schema),
                "role": str(getattr(request, "role_id", None) or "RESEARCH_AND_CURATION"),
                "input_manifest_checksum": json.loads(package_path.read_text(encoding="utf-8")).get("input_manifest_checksum"),
                "skill_id": json.loads(package_path.read_text(encoding="utf-8")).get("skill_id"),
                "skill_version": json.loads(package_path.read_text(encoding="utf-8")).get("skill_version"),
                "completed_stages": prior_completed,
                "real_ai_execution": False,
                "real_ai_calls": 0,
                "provenance": prior_state.get("provenance") if isinstance(prior_state, Mapping) else None,
                "provenance_status": prior_state.get("provenance_status") if isinstance(prior_state, Mapping) else "NOT_AVAILABLE",
                "producer_provenance": prior_state.get("producer_provenance") if isinstance(prior_state, Mapping) else None,
                "external_cognitive_provenance": prior_state.get("external_cognitive_provenance") if isinstance(prior_state, Mapping) else None,
                "auditor_provenance": prior_state.get("auditor_provenance") if isinstance(prior_state, Mapping) else None,
                "execution_controls": execution_request.config["execution_controls"],
                "next_action": "IMPORT_EXTERNAL_COGNITIVE_RESULT",
            },
        )
        raise ExternalCognitiveHandoffPending(
            package_path=package_path,
            handoff_id=run_id,
            stage=str(request.stage),
        )


class ProductiveResearchStageAdapters:
    """B3 adapters around the existing B2/M4/M5/M6 authorities.

    This is deliberately coordination only: it neither selects an execution
    provider nor replaces any stage contract.  The callable passed as
    ``cognitive_executor`` is the existing generic cognitive boundary; the
    production entrypoint supplies a neutral external-handoff callable
    without selecting an internal provider, model, runtime, or profile.
    """

    def __init__(
        self,
        episode: PersistedResearchEpisode,
        *,
        cognitive_executor: Callable[[Any], Any],
        acquisition_adapter: SoftwareAcquisitionAdapter | None = None,
        _test_provenance_repository_root: Path | None = None,
    ):
        if not callable(cognitive_executor):
            raise ResearchM7Error("REAL_ROUTE_COGNITIVE_EXECUTOR_REQUIRED")
        self.episode = episode
        self.cognitive_executor = cognitive_executor
        self.acquisition_adapter = acquisition_adapter or SoftwareAcquisitionAdapter()
        self.root = episode.handle.folder / "research_v2"
        self.planning = ResearchPlanningService()
        self.b2_persistence = ResearchB2Persistence(self.root / "b2")
        self.b3_persistence = ResearchB3Persistence(self.root / "b3")
        self.b4_persistence = ResearchB4Persistence(self.root / "b3")
        self.provenance_repository_root = (
            Path(_test_provenance_repository_root).resolve()
            if _test_provenance_repository_root is not None
            else Path(__file__).resolve().parents[2]
        )

    def _provenance_path(self) -> Path:
        path = self.provenance_repository_root / "output" / "execution_provenance_registry.json"
        if not path.is_file():
            raise ResearchM7Error("REAL_ROUTE_CANONICAL_PROVENANCE_REGISTRY_REQUIRED")
        return path

    def _software_run_id(self) -> str:
        try:
            state = self.episode.store.resume(self.episode.handle.episode_id)["state"]
        except (StorageError, KeyError, TypeError) as exc:
            raise ResearchM7Error("REAL_ROUTE_EPISODE_STATE_INVALID") from exc
        run_id = str(state.get("run_id") or "").strip()
        if not run_id:
            raise ResearchM7Error("REAL_ROUTE_SOFTWARE_PRODUCER_RUN_REQUIRED")
        return run_id

    def _register_software_stage(self, result: Mapping[str, Any], *, manifest_key: str, output_key: str, extra_results: tuple[Mapping[str, Any], ...] = ()) -> dict[str, str]:
        manifest_ref = result.get(manifest_key)
        if not isinstance(manifest_ref, Mapping):
            raise ResearchM7Error("REAL_ROUTE_STAGE_MANIFEST_REQUIRED")
        manifest = _read(manifest_ref["path"])
        raw_refs = [manifest_ref]
        for primary_key in ("research_plan", "research_plan_proposal", "evidence_report"):
            primary_ref = result.get(primary_key)
            if isinstance(primary_ref, Mapping):
                raw_refs.append(primary_ref)
        for extra in extra_results:
            extra_ref = extra.get("execution_manifest")
            if isinstance(extra_ref, Mapping):
                raw_refs.append(extra_ref)
                extra_manifest = _read(extra_ref["path"])
                raw_refs.extend(extra_manifest.get("artifacts", []))
            for primary_key in ("research_plan", "research_plan_proposal", "evidence_report"):
                primary_ref = extra.get(primary_key)
                if isinstance(primary_ref, Mapping):
                    raw_refs.append(primary_ref)
            # Some canonical stage results expose a primary artifact (notably
            # ResearchPlan) alongside, rather than inside, the execution
            # manifest artifact list.  Carry those existing refs into the same
            # Software producer run; do not derive a new checksum.
            raw_refs.extend(
                value for value in extra.values()
                if isinstance(value, Mapping)
                and value.get("artifact_id")
                and value.get("artifact_version")
                and value.get("checksum")
            )
        if output_key:
            raw_refs.extend(manifest.get(output_key, []))
        refs = []
        for ref in raw_refs:
            if not isinstance(ref, Mapping):
                raise ResearchM7Error("REAL_ROUTE_STAGE_PROVENANCE_REFERENCE_INVALID")
            persisted = dict(ref)
            persisted_path = Path(str(persisted.get("path") or ""))
            if persisted_path.is_file():
                persisted["checksum"] = _checksum(_read(persisted_path))
            refs.append({
                "artifact_id": str(persisted.get("artifact_id") or ""),
                "artifact_kind": str(persisted.get("artifact_kind") or ""),
                "artifact_version": str(persisted.get("artifact_version") or ""),
                "checksum": str(persisted.get("checksum") or ""),
            })
        refs = list({(item["artifact_id"], item["artifact_version"], item.get("artifact_kind", "")): item for item in refs}.values())
        try:
            provenance = register_software_outputs(
                self._provenance_path(),
                run_id=self._software_run_id(),
                episode_id=self.episode.handle.episode_id,
                role="RESEARCH_AND_CURATION",
                outputs=refs,
            )
        except (OSError, ValueError) as exc:
            raise ResearchM7Error("REAL_ROUTE_SOFTWARE_PROVENANCE_BINDING_FAILED") from exc
        provenance["provenance_ref"] = "output/execution_provenance_registry.json"
        provenance["artifact_ref"] = {
            "artifact_id": str(manifest_ref["artifact_id"]),
            "artifact_kind": str(manifest_ref["artifact_kind"]),
            "artifact_version": str(manifest_ref["artifact_version"]),
            "checksum": str(manifest_ref["checksum"]),
        }
        return provenance

    def _persist_producer_lineage(self, provenance: Mapping[str, Any]) -> None:
        state_path = self.episode.handle.folder / REAL_EXTERNAL_HANDOFF_STATE_FILENAME
        if not state_path.is_file():
            return
        state = _read(state_path)
        if not isinstance(state, Mapping):
            raise ResearchM7Error("REAL_ROUTE_EXTERNAL_HANDOFF_STATE_INVALID")
        updated = dict(state)
        updated["producer_provenance"] = copy.deepcopy(dict(provenance))
        updated["producer_provenance_status"] = "CANONICAL_SOFTWARE_BOUND"
        _write_json_atomic(state_path, updated)

    @staticmethod
    def canonical_authorities() -> dict[str, Callable[..., Any]]:
        return RealResearchRoutePreparation.canonical_stage_handlers()

    def stage_runners(self) -> dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]]:
        return {"B2": self.run_b2, "M4": self.run_m4, "M5": self.run_m5, "M6": self.run_m6}

    def _plan_for_b2(self) -> dict[str, Any]:
        path = self.root / "b2" / "research_plan.json"
        imported_proposal_path = self.root / "b2" / "research_plan_proposal.json"
        manifest = self.root / "b2" / "research_b2_execution.json"
        if path.is_file():
            plan = _read(path)
            if (
                not isinstance(plan, Mapping)
                or validate_research_plan(dict(plan))
                or plan.get("episode_id") != self.episode.handle.episode_id
                or plan.get("brief_version") != self.episode.brief.get("brief_version")
            ):
                raise ResearchM7Error("REAL_ROUTE_PERSISTED_RESEARCH_PLAN_INVALID")
            if not manifest.is_file():
                handoff_state = self.episode.handle.folder / REAL_EXTERNAL_HANDOFF_STATE_FILENAME
                imported = _read(handoff_state) if handoff_state.is_file() else {}
                if not isinstance(imported, Mapping) or "RESEARCH_PLANNING" not in imported.get("completed_stages", []):
                    raise ResearchM7Error("REAL_ROUTE_RESEARCH_PLAN_LINEAGE_INCOMPLETE")
            return copy.deepcopy(dict(plan))
        if imported_proposal_path.is_file():
            proposal = _read(imported_proposal_path)
            try:
                plan = self.planning.bind_research_plan(
                    proposal,
                    episode_id=self.episode.handle.episode_id,
                    brief_version=str(self.episode.brief["brief_version"]),
                    research_role=str(self.episode.human_input.get("research_role") or "NORMAL"),
                    editorial_intent=str(self.episode.human_input.get("editorial_intent") or "NO_DECLARADA"),
                    origin_ref=f"{self.episode.handle.episode_id}:RESEARCH_PLAN_PROPOSAL",
                )
                handoff_state = self.episode.handle.folder / REAL_EXTERNAL_HANDOFF_STATE_FILENAME
                state = _read(handoff_state) if handoff_state.is_file() else {}
                persisted_ref = state.get("research_plan_proposal") if isinstance(state, Mapping) else None
                if isinstance(persisted_ref, Mapping):
                    origin = plan.get("origin_artifact_refs", [{}])[0]
                    origin.update({
                        "artifact_ref": persisted_ref.get("artifact_id"),
                        "artifact_version": persisted_ref.get("artifact_version"),
                        "checksum": persisted_ref.get("checksum"),
                    })
                    if not origin.get("artifact_ref") or not origin.get("checksum"):
                        raise ResearchM7Error("REAL_ROUTE_IMPORTED_RESEARCH_PLAN_LINEAGE_INCOMPLETE")
                return plan
            except (ResearchPlanningError, KeyError, TypeError, ValueError) as exc:
                raise ResearchM7Error("REAL_ROUTE_IMPORTED_RESEARCH_PLAN_INVALID") from exc
        try:
            produced = self.planning.produce_research_plan(
                episode_brief=self.episode.brief,
                channel_context=self.episode.channel_context,
                source_access=self.episode.source_access,
                cognitive_executor=self.cognitive_executor,
                persistence=self.b2_persistence,
                research_role=str(self.episode.human_input.get("research_role") or "NORMAL"),
                editorial_intent=str(self.episode.human_input.get("editorial_intent") or "NO_DECLARADA"),
                persist_plan=False,
            )
        except ResearchPlanningError as exc:
            raise ResearchM7Error(str(exc)) from exc
        return copy.deepcopy(dict(produced["research_plan_payload"]))

    @staticmethod
    def _manifest_ref(manifest: Mapping[str, Any], filename: str) -> dict[str, Any]:
        for ref in manifest.get("artifacts", []):
            if isinstance(ref, Mapping) and Path(str(ref.get("path") or "")).name == filename:
                resolved = copy.deepcopy(dict(ref))
                path = Path(str(resolved.get("path") or ""))
                if path.is_file():
                    # The persisted file is the checksum authority after a
                    # restart; never carry a stale in-memory manifest value
                    # into the producer/auditor binding.
                    resolved["checksum"] = _checksum(_read(path))
                return resolved
        raise ResearchM7Error(f"REAL_ROUTE_PERSISTED_ARTIFACT_MISSING:{filename}")

    @staticmethod
    def _manifest_self(path: Path, manifest: Mapping[str, Any], artifact_id: str, artifact_kind: str) -> dict[str, Any]:
        return {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "artifact_version": str(manifest.get("manifest_version") or "1.0.0"),
            "path": str(path),
            "checksum": _checksum(manifest),
        }

    def _recover_b2_result(self) -> dict[str, Any] | None:
        path = self.root / "b2" / "research_b2_execution.json"
        if not path.is_file():
            return None
        manifest = _read(path)
        plan_ref = self._manifest_ref(manifest, "research_plan.json")
        plan = _read(plan_ref["path"])
        return {
            "research_plan": plan_ref,
            "phenomenon_base_research": self._manifest_ref(manifest, "phenomenon_base_research.json"),
            "evidence_report": copy.deepcopy(manifest["evidence_report"]),
            "work_discovery": self._manifest_ref(manifest, "work_discovery.json"),
            "base_research_pool": self._manifest_ref(manifest, "base_research_pool.json"),
            "preliminary_fidelity": self._manifest_ref(manifest, "preliminary_fidelity.json"),
            "initial_sufficiency": self._manifest_ref(manifest, "initial_sufficiency.json"),
            "provisional_thesis": self._manifest_ref(manifest, "provisional_thesis.json"),
            "research_comparison": self._manifest_ref(manifest, "research_comparison.json"),
            "deepening_targets": copy.deepcopy(manifest.get("deepening_targets") or {}),
            "lifecycle_projection": copy.deepcopy(manifest.get("lifecycle_projection") or {}),
            "execution_manifest": self._manifest_self(path, manifest, f"{plan['research_plan_id']}:B2", "ResearchB2ExecutionManifest"),
            "events": copy.deepcopy(manifest.get("events") or []),
        }

    def _recover_m4_result(self, b2: Mapping[str, Any]) -> dict[str, Any] | None:
        path = self.root / "b3" / "research_m4_execution.json"
        if not path.is_file():
            return None
        manifest = _read(path)
        if not isinstance(b2.get("research_plan"), Mapping):
            return None
        plan = _read(b2["research_plan"]["path"])
        return {
            "selection": copy.deepcopy(manifest.get("selected_lifecycle_projection") or manifest.get("selection") or {}),
            "deep_phenomenon_research": self._manifest_ref(manifest, "deep_phenomenon_research.json"),
            "deep_phenomenon_sufficiency": self._manifest_ref(manifest, "deep_phenomenon_sufficiency.json"),
            "deep_work_research": self._manifest_ref(manifest, "deep_work_research.json"),
            "deep_fidelity": self._manifest_ref(manifest, "deep_fidelity.json"),
            "deep_work_sufficiency": self._manifest_ref(manifest, "deep_work_sufficiency.json"),
            "evidence_report": self._manifest_ref(manifest, "source_access_and_evidence_report_m4_deep.json"),
            "execution_manifest": self._manifest_self(path, manifest, f"{plan['research_plan_id']}:M4", "ResearchM4ExecutionManifest"),
            "events": copy.deepcopy(manifest.get("events") or []),
        }

    def _recover_m5_result(self, b2: Mapping[str, Any]) -> dict[str, Any] | None:
        path = self.root / "b3" / "research_m5_execution.json"
        if not path.is_file():
            return None
        manifest = _read(path)
        required_files = {
            "claims_ledger_m5.json",
            "research_stop_m5_claims.json",
            "research_comparison_m5_post_deep.json",
            "refined_thesis_m5.json",
            "source_access_and_evidence_report_m5_refined.json",
        }
        persisted_files = {
            Path(str(ref.get("path") or "")).name
            for ref in manifest.get("artifacts", [])
            if isinstance(ref, Mapping)
        }
        # A coordinator may persist/update its M5 manifest before the first
        # external cognitive seam.  It is not a recoverable result until the
        # complete canonical artifact set exists; let the canonical M5
        # orchestrator resume its individual persisted stages instead.
        if not required_files.issubset(persisted_files) or any(
            not (self.root / "b3" / filename).is_file() for filename in required_files
        ):
            return None
        plan = _read(b2["research_plan"]["path"])
        result: dict[str, Any] = {
            "status": manifest.get("status"),
            "claims_ledger": self._manifest_ref(manifest, "claims_ledger_m5.json"),
            "claim_sufficiency": self._manifest_ref(manifest, "research_stop_m5_claims.json"),
            "post_deep_comparison": self._manifest_ref(manifest, "research_comparison_m5_post_deep.json"),
            "refined_thesis": self._manifest_ref(manifest, "refined_thesis_m5.json"),
            "evidence_report": self._manifest_ref(manifest, "source_access_and_evidence_report_m5_refined.json"),
            "execution_manifest": self._manifest_self(path, manifest, f"{plan['research_plan_id']}:M5", "ResearchM5ExecutionManifest"),
            "events": copy.deepcopy(manifest.get("events") or []),
        }
        return result

    @staticmethod
    def _baseline(b2: Mapping[str, Any]) -> dict[str, Any]:
        manifest = _read(b2["execution_manifest"]["path"])
        by_kind = {str(ref["artifact_kind"]): ref for ref in manifest["artifacts"]}
        return {
            "research_plan": _read(b2["research_plan"]["path"]),
            "phenomenon_base_research": _read(by_kind["ResearchPack"]["path"]),
            "work_discovery": _read(by_kind["WorkLifecycle"]["path"]),
            "base_research_pool": _read(next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":BASE_RESEARCH_POOL"))["path"])["dossiers"],
            "preliminary_fidelity": _read(b2["preliminary_fidelity"]["path"])["dossiers"],
            "initial_sufficiency": _read(b2["initial_sufficiency"]["path"])["dossiers"],
            "provisional_thesis": _read(by_kind["ThesisArtifact"]["path"]),
            "research_comparison": _read(by_kind["ResearchComparison"]["path"]),
            "deepening_targets": b2["deepening_targets"],
            "lifecycle": b2["lifecycle_projection"],
            "evidence_report": b2["evidence_report"],
        }

    @staticmethod
    def _research_chain(
        b2: Mapping[str, Any], m4: Mapping[str, Any], m5: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build the canonical M6 artifact seam from persisted stage outputs.

        This only transports verified artifact references already emitted by
        B2/M4/M5.  It never creates producer runs or substitutes provenance.
        """
        refs: list[Mapping[str, Any]] = []
        b2_manifest = _read(b2["execution_manifest"]["path"])
        m4_manifest = _read(m4["execution_manifest"]["path"])
        m5_manifest = _read(m5["execution_manifest"]["path"])
        refs.extend([b2["execution_manifest"], *b2_manifest.get("artifacts", [])])
        refs.extend([m4["execution_manifest"], *m4_manifest.get("artifacts", [])])
        refs.extend([m5["execution_manifest"], *m5_manifest.get("m5_outputs", [])])
        # Prefer the recovered, persisted ResearchPlan ref over any stale copy
        # embedded in an older stage manifest.
        refs.append(b2["research_plan"])
        refreshed: list[Mapping[str, Any]] = []
        for ref in refs:
            item = dict(ref)
            path = Path(str(item.get("path") or ""))
            if path.is_file():
                item["checksum"] = _checksum(_read(path))
            refreshed.append(item)
        refs = refreshed
        unique: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for ref in refs:
            if not isinstance(ref, Mapping):
                raise ResearchM7Error("REAL_ROUTE_RESEARCH_CHAIN_REFERENCE_INVALID")
            key = tuple(str(ref.get(field) or "") for field in ("artifact_id", "artifact_kind", "artifact_version"))
            if any(not value for value in key) or not ref.get("path"):
                raise ResearchM7Error("REAL_ROUTE_RESEARCH_CHAIN_REFERENCE_INVALID")
            unique[key] = copy.deepcopy(dict(ref))
        return {"artifact_refs": list(unique.values())}

    def _selection_missing_error(self) -> str:
        authority = str(self.episode.brief.get("selection_authority") or "NOT_DECLARED").upper()
        return {
            "OWNER_DECIDES": "MISSING_VALID_SELECTION:REAL_ROUTE_OWNER_SELECTION_REQUIRED",
            "DELEGATED_TO_RESEARCH": "MISSING_VALID_SELECTION:REAL_ROUTE_DELEGATED_SELECTION_REQUIRED",
            "NOT_DECLARED": "MISSING_VALID_SELECTION:REAL_ROUTE_SELECTION_AUTHORITY_REQUIRED",
        }.get(authority, "MISSING_VALID_SELECTION:REAL_ROUTE_SELECTION_AUTHORITY_INVALID")

    def _recover_persisted_selection(self, b2: Mapping[str, Any]) -> dict[str, Any] | None:
        """Load the already-authorized M4 decision from canonical B3 storage.

        The external boundary never chooses works.  It only makes a persisted
        owner/delegated decision available to the canonical B3 orchestrator;
        a missing or malformed decision remains a fail-closed wait condition.
        """
        if not isinstance(b2.get("research_plan"), Mapping):
            return None
        plan = _read(b2["research_plan"]["path"])
        authority = str(self.episode.brief.get("selection_authority") or "NOT_DECLARED").upper()
        if authority == "OWNER_DECIDES":
            mode = "USER_SELECTION"
            request_stage, request_kind = "M4_SELECTION_REQUEST", "HumanDecisionRequest"
            decision_kind = "HumanDecision"
            decision_id = f"{plan['research_plan_id']}:M4:HUMAN_DECISION"
        elif authority == "DELEGATED_TO_RESEARCH":
            mode = "DELEGATED_SELECTION"
            request_stage, request_kind = "M4_DELEGATION_DECISION", "DelegationDecision"
            decision_kind = "DelegatedSelectionDecision"
            decision_id = f"{plan['research_plan_id']}:M4:DELEGATED_SELECTION"
        else:
            return None
        request_loaded = self.b3_persistence.load_existing(
            request_stage,
            artifact_id=f"{plan['research_plan_id']}:M4:SELECTION_AUTHORITY",
            artifact_kind=request_kind,
        )
        decision_loaded = self.b3_persistence.load_existing(
            "M4_SELECTION_DECISION", artifact_id=decision_id, artifact_kind=decision_kind,
        )
        if request_loaded is None and decision_loaded is None:
            # The operational interaction store is the OWNER-facing seam.  A
            # request recorded there is bridged into B3 persistence below;
            # absence remains a clean wait condition, never an auto-selection.
            folder = self.episode.handle.folder
            request_path = folder / "human_decision_requests.json"
            if request_path.is_file():
                records = _read(request_path)
                for raw in records.get("requests", []) if isinstance(records, Mapping) else []:
                    if raw.get("episode_id") == self.episode.handle.episode_id and raw.get("status") in {"PENDING", "RESPONSE_RECORDED", "RESOLVED"}:
                        request_loaded = self.b3_persistence.persist(
                            "M4_SELECTION_REQUEST", dict(raw),
                            artifact_id=f"{plan['research_plan_id']}:M4:SELECTION_AUTHORITY",
                            artifact_kind="HumanDecisionRequest",
                        ), dict(raw)
                        break
        if request_loaded is None and decision_loaded is None:
            return None
        if request_loaded is None:
            raise ResearchM7Error("M4_SELECTION_SEAM_GAP")
        if decision_loaded is None:
            interaction = self.episode.store.interaction_record(
                self.episode.handle.episode_id,
                str(request_loaded[1].get("request_id") or ""),
            )
            stored_decision = interaction.get("decision")
            if stored_decision is None:
                return None
            decision_loaded = (
                self.b3_persistence.persist(
                    "M4_SELECTION_DECISION", dict(stored_decision),
                    artifact_id=decision_id,
                    artifact_kind=decision_kind,
                ),
                dict(stored_decision),
            )
        request_payload = request_loaded[1]
        decision_payload = decision_loaded[1]
        try:
            if mode == "USER_SELECTION":
                request = HumanDecisionRequest.from_dict(dict(request_payload), require_contract=True)
                decision = HumanDecision.from_dict(dict(decision_payload), require_bound_metadata=True)
                validate_human_decision(request, decision, self.episode.handle.episode_id, require_bound_metadata=True)
                baseline = self._baseline(b2)
                candidate_ids = ResearchB3Orchestrator._eligible_candidates(
                    baseline["base_research_pool"],
                    baseline["preliminary_fidelity"],
                    baseline["initial_sufficiency"],
                )
                selected = ResearchB3Orchestrator._parse_selection_option(
                    decision.selected_option or request.recommendation, candidate_ids,
                )
                if not selected:
                    raise ValueError("empty selection")
                return {
                    "mode": mode,
                    "human_decision": decision.to_dict(),
                    "selection_options": [selected],
                }
            if not isinstance(decision_payload, Mapping):
                raise ValueError("delegated decision must be an object")
            baseline = self._baseline(b2)
            candidate_ids = ResearchB3Orchestrator._eligible_candidates(
                baseline["base_research_pool"],
                baseline["preliminary_fidelity"],
                baseline["initial_sufficiency"],
            )
            selected = {str(item) for item in decision_payload.get("selected_work_ids", [])}
            if not selected or not selected.issubset(candidate_ids):
                raise ValueError("delegated selection outside eligible candidates")
            return {"mode": mode, "delegation_decision": copy.deepcopy(dict(decision_payload))}
        except (KeyError, TypeError, ValueError, ResearchB3Error) as exc:
            raise ResearchM7Error("MISSING_VALID_SELECTION:REAL_ROUTE_PERSISTED_SELECTION_INVALID") from exc

    def _ensure_operational_m4_request(self, b2: Mapping[str, Any]) -> HumanDecisionRequest:
        """Materialize the canonical OWNER request through the interaction store."""
        if not isinstance(b2.get("research_plan"), Mapping):
            raise ResearchM7Error("REAL_ROUTE_STAGE_CONTEXT_B2_REQUIRED")
        plan = _read(b2["research_plan"]["path"])
        try:
            baseline = self._baseline(b2)
        except (KeyError, TypeError, OSError, ValueError) as exc:
            raise ResearchM7Error(self._selection_missing_error()) from exc
        candidate_ids = ResearchB3Orchestrator._eligible_candidates(
            baseline["base_research_pool"], baseline["preliminary_fidelity"], baseline["initial_sufficiency"],
        )
        options = ResearchB3Orchestrator._selection_options(candidate_ids, None)
        request_options = tuple(
            {"id": ResearchB3Orchestrator._selection_option_id(option), "label": ", ".join(option)}
            for option in options
        )
        lifecycle = baseline.get("lifecycle") if isinstance(baseline.get("lifecycle"), Mapping) else {}
        request = HumanDecisionRequest(
            request_id=f"{plan['research_plan_id']}:M4:SELECTION_REQUEST",
            prompt="Seleccionar las obras que pasarán a investigación profunda.",
            options=request_options,
            recommendation=request_options[0]["id"],
            episode_id=self.episode.handle.episode_id,
            subject_ref=str(lifecycle.get("lifecycle_id") or plan["research_plan_id"]),
            subject_version=str(lifecycle.get("lifecycle_version") or "2.0.0"),
            subject_checksum=_checksum(lifecycle),
            workflow_ref=str(lifecycle.get("lifecycle_id") or plan["research_plan_id"]),
            expected_actor_ref="OWNER",
            expected_channel="TERMINAL",
        )
        stored = self.episode.store.record_decision_request(
            self.episode.handle.episode_id, request.to_dict(),
        )
        self.b3_persistence.persist(
            "M4_SELECTION_REQUEST", stored,
            artifact_id=f"{plan['research_plan_id']}:M4:SELECTION_AUTHORITY",
            artifact_kind="HumanDecisionRequest",
        )
        return HumanDecisionRequest.from_dict(stored, require_contract=True)

    def run_b2(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        plan = self._plan_for_b2()
        recovered = self._recover_b2_result()
        if recovered is not None:
            self._register_software_stage(recovered, manifest_key="execution_manifest", output_key="")
            if isinstance(context, dict):
                context.update({"b2_result": recovered, "research_plan": plan, "evidence_report": recovered["evidence_report"]})
            return recovered
        stage_context = self.episode.context()
        result = ResearchB2Orchestrator(
            self.cognitive_executor,
            self.b2_persistence,
            acquisition_adapter=self.acquisition_adapter,
            no_progress_guard=ResearchB2NoProgressGuard(max_iterations=int(context["request"].config["max_iterations"])),
        ).run(plan, context=stage_context)
        mutable = context if isinstance(context, dict) else None
        if mutable is not None:
            mutable["b2_result"] = result
            mutable["research_plan"] = plan
            mutable["evidence_report"] = result["evidence_report"]
        self._register_software_stage(result, manifest_key="execution_manifest", output_key="")
        return result

    def run_m4(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        b2 = context.get("b2_result") if isinstance(context, Mapping) else None
        selection = context.get("selection") if isinstance(context, Mapping) else None
        if not isinstance(b2, Mapping) or not b2:
            # Preserve the pre-existing functional blocker for callers that
            # invoke M4 before a materialized B2 result exists.
            raise ResearchM7Error("REAL_ROUTE_OWNER_SELECTION_REQUIRED")
        if not isinstance(selection, Mapping):
            selection = self._recover_persisted_selection(b2)
            if isinstance(selection, Mapping) and isinstance(context, dict):
                context["selection"] = copy.deepcopy(selection)
        if not isinstance(selection, Mapping):
            request = self._ensure_operational_m4_request(b2)
            raise HumanDecisionPending(request)
        expected_authority = str(self.episode.brief.get("selection_authority") or "NOT_DECLARED").upper()
        mode = str(selection.get("mode") or "").upper()
        if expected_authority == "OWNER_DECIDES" and mode != "USER_SELECTION":
            raise ResearchM7Error("REAL_ROUTE_OWNER_SELECTION_AUTHORITY_MISMATCH")
        if expected_authority == "DELEGATED_TO_RESEARCH" and mode != "DELEGATED_SELECTION":
            raise ResearchM7Error("REAL_ROUTE_DELEGATED_SELECTION_AUTHORITY_MISMATCH")
        if expected_authority == "NOT_DECLARED":
            raise ResearchM7Error("REAL_ROUTE_SELECTION_AUTHORITY_REQUIRED")
        recovered = self._recover_m4_result(b2)
        if recovered is not None:
            if isinstance(context, dict):
                context.update({"m4_result": recovered, "evidence_report": recovered["evidence_report"], "selection": copy.deepcopy(recovered.get("selection") or selection)})
            return recovered
        baseline = self._baseline(b2)
        stage_context = self.episode.context()
        stage_context.update({"evidence_report": _read(b2["evidence_report"]["path"]), "_evidence_report_ref": dict(b2["evidence_report"])})
        result = ResearchB3Orchestrator(
            self.cognitive_executor, self.b3_persistence,
            acquisition_adapter=self.acquisition_adapter,
            no_progress_guard=ResearchB2NoProgressGuard(max_iterations=int(context["request"].config["max_iterations"])),
        ).run(
            baseline,
            context=stage_context,
            selection_mode=str(selection.get("mode") or "USER_SELECTION"),
            human_decision=selection.get("human_decision"),
            delegation_decision=selection.get("delegation_decision"),
            selection_options=selection.get("selection_options"),
        )
        if isinstance(context, dict):
            context["m4_result"] = result
            context["evidence_report"] = result["evidence_report"]
            manifest = _read(result["execution_manifest"]["path"])
            context["selection"] = copy.deepcopy(manifest.get("selection") or dict(selection))
        return result

    def run_m5(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        b2 = context.get("b2_result") if isinstance(context, Mapping) else None
        m4 = context.get("m4_result") if isinstance(context, Mapping) else None
        if not isinstance(b2, Mapping):
            raise ResearchM7Error("REAL_ROUTE_STAGE_CONTEXT_B2_REQUIRED")
        if not isinstance(m4, Mapping):
            raise ResearchM7Error("REAL_ROUTE_STAGE_CONTEXT_M4_REQUIRED")
        recovered = self._recover_m5_result(b2)
        if recovered is not None:
            producer = self._register_software_stage(recovered, manifest_key="execution_manifest", output_key="m5_outputs", extra_results=(b2, m4))
            self._persist_producer_lineage(producer)
            if isinstance(context, dict):
                context.update({"m5_result": recovered, "evidence_report": recovered["evidence_report"], "producer_provenance": producer})
                context["research_chain"] = self._research_chain(b2, m4, recovered)
            return recovered
        baseline = self._baseline(b2)
        stage_context = self.episode.context()
        stage_context.update({"evidence_report": _read(m4["evidence_report"]["path"]), "_evidence_report_ref": dict(m4["evidence_report"])})
        result = ResearchB3Orchestrator(
            self.cognitive_executor, self.b3_persistence,
            acquisition_adapter=self.acquisition_adapter,
            no_progress_guard=ResearchB2NoProgressGuard(max_iterations=int(context["request"].config["max_iterations"])),
        ).run_m5(baseline, m4, context=stage_context)
        if isinstance(context, dict):
            context["m5_result"] = result
            # ResearchB3's M5 result intentionally exposes the M5 outputs;
            # the evidence report consumed by the next boundary remains the
            # verified M4 deep-evidence ref when M5 has not produced a new
            # report yet (including an external seam pause).
            context["evidence_report"] = copy.deepcopy(
                result.get("evidence_report") or m4.get("evidence_report")
            )
            context["research_chain"] = self._research_chain(b2, m4, result)
            producer = self._register_software_stage(result, manifest_key="execution_manifest", output_key="m5_outputs", extra_results=(b2, m4))
            self._persist_producer_lineage(producer)
            context["producer_provenance"] = producer
        return result

    def run_m6(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        m5 = context.get("m5_result") if isinstance(context, Mapping) else None
        chain = context.get("research_chain") if isinstance(context, Mapping) else None
        provenance = context.get("real_provenance") if isinstance(context, Mapping) else None
        if not isinstance(m5, Mapping):
            raise ResearchM7Error("REAL_ROUTE_STAGE_CONTEXT_M5_REQUIRED")
        if not isinstance(chain, Mapping):
            raise ResearchM7Error("REAL_ROUTE_RESEARCH_CHAIN_REQUIRED")
        producer = context.get("producer_provenance") if isinstance(context, Mapping) else None
        if not isinstance(producer, Mapping) and isinstance(provenance, Mapping):
            producer = provenance.get("producer_provenance") if isinstance(provenance.get("producer_provenance"), Mapping) else None
        if not isinstance(producer, Mapping):
            raise ResearchM7Error("REAL_ROUTE_REAL_PROVENANCE_REQUIRED")
        if context.get("external_auditor_required") and not isinstance(context.get("auditor_provenance"), Mapping):
            raise ResearchM7Error("M6_EXTERNAL_AUDITOR_PROVENANCE_REQUIRED")
        # Refresh the single canonical Software producer run from the
        # persisted chain immediately before M6 resolves it.  This binds the
        # exact post-restart checksums consumed by the auditor, including the
        # ResearchPlan file, without creating a second provenance registry.
        chain_refs = chain.get("artifact_refs", []) if isinstance(chain, Mapping) else []
        register_software_outputs(
            self._provenance_path(),
            run_id=self._software_run_id(),
            episode_id=self.episode.handle.episode_id,
            role="RESEARCH_AND_CURATION",
            outputs=[
                {
                    "artifact_id": str(ref.get("artifact_id") or ""),
                    "artifact_kind": str(ref.get("artifact_kind") or ""),
                    "artifact_version": str(ref.get("artifact_version") or ""),
                    "checksum": str(ref.get("checksum") or ""),
                }
                for ref in chain_refs
                if isinstance(ref, Mapping)
            ],
        )
        stage_context = self.episode.context()
        stage_context.update(dict(provenance) if isinstance(provenance, Mapping) else {})
        # Imported provenance is already bound by the generic handoff
        # importer.  M6 still receives it through its canonical producer /
        # auditor fields so ResearchB4 can resolve the registry-backed run
        # and enforce auditor independence; no identity is synthesized here.
        stage_context["producer_provenance"] = copy.deepcopy(dict(producer))
        auditor_provenance = context.get("auditor_provenance") if isinstance(context, Mapping) else None
        if not isinstance(auditor_provenance, Mapping) and isinstance(provenance, Mapping):
            auditor_provenance = provenance.get("auditor_provenance")
        if isinstance(auditor_provenance, Mapping):
            stage_context["auditor_provenance"] = copy.deepcopy(dict(auditor_provenance))
        return ResearchB4Orchestrator(
            self.cognitive_executor, self.b4_persistence,
            _test_provenance_repository_root=self.provenance_repository_root,
        ).run_m6(m5, context=stage_context, research_chain=chain)


def respond_to_research_human_decision(
    store: VaultEpisodeStore,
    episode_id: str,
    *,
    request_id: str,
    action: str,
    selected_option: str | None = None,
    correction: str | None = None,
    actor_ref: str = "OWNER",
    channel: str = "TERMINAL",
) -> dict[str, Any]:
    """Record an OWNER response through the canonical interaction store."""
    record = store.interaction_record(episode_id, request_id)
    request = HumanDecisionRequest.from_dict(record["request"], require_contract=True)
    decision = HumanDecision(
        request_id=request.request_id,
        action=str(action).upper(),
        selected_option=selected_option,
        correction=correction,
        actor_ref=actor_ref,
        channel=channel,
    ).bind_request(request)
    validate_human_decision(request, decision, episode_id, require_bound_metadata=True)
    store.record_decision(episode_id, decision.to_dict())
    return {
        "status": "RESPONSE_RECORDED",
        "episode_id": episode_id,
        "request_id": request_id,
        "request_checksum": request.checksum(),
        "decision": decision.to_dict(),
    }


@dataclass(frozen=True)
class RealResearchRoutePreparation:
    """Explicit M1 preparation for a future REAL Research V2 execution.

    This object only compiles a canonical request and its safety claims.  It
    never invokes the execution runtime, a provider, search, or fetch.
    """

    episode_id: str
    topic: str
    question: str | None
    budget_limit: float
    max_iterations: int
    max_retries: int
    timeout_seconds: int
    mission_authorization_path: str | None = None
    mission_contract_path: str = REAL_EXTERNAL_HANDOFF_CONTRACT
    handoff_directory: Path = REAL_EXTERNAL_HANDOFF_DIRECTORY

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "RealResearchRoutePreparation":
        if not isinstance(values, Mapping):
            raise ResearchM7Error("REAL_ROUTE_CONFIGURATION_INVALID")
        forbidden = {
            "provider", "model", "runtime", "execution_profile", "execution_route",
            "execution_family", "harness", "development_platform", "acquisition_status",
        }
        unsupported = sorted(key for key in forbidden if key in values)
        if unsupported:
            raise ResearchM7Error("REAL_ROUTE_CONFIGURATION_UNSUPPORTED_FIELDS:" + ",".join(unsupported))
        required = (
            "episode_id", "topic", "budget_limit", "max_iterations",
            "max_retries", "timeout_seconds",
        )
        missing = [key for key in required if values.get(key) in (None, "")]
        if missing:
            raise ResearchM7Error("REAL_ROUTE_CONFIGURATION_MISSING:" + ",".join(missing))
        try:
            budget = float(values["budget_limit"])
            iterations = int(values["max_iterations"])
            retries = int(values["max_retries"])
            timeout = int(values["timeout_seconds"])
        except (TypeError, ValueError) as exc:
            raise ResearchM7Error("REAL_ROUTE_CONFIGURATION_LIMITS_INVALID") from exc
        if budget <= 0 or iterations < 1 or retries < 0 or timeout <= 0:
            raise ResearchM7Error("REAL_ROUTE_CONFIGURATION_LIMITS_INVALID")
        return cls(
            episode_id=str(values["episode_id"]), topic=str(values["topic"]),
            question=(str(values["question"]) if values.get("question") else None),
            budget_limit=budget,
            max_iterations=iterations, max_retries=retries, timeout_seconds=timeout,
            mission_authorization_path=(str(values["mission_authorization_path"]) if values.get("mission_authorization_path") else None),
            mission_contract_path=str(values.get("mission_contract_path") or REAL_EXTERNAL_HANDOFF_CONTRACT),
            handoff_directory=Path(str(values.get("handoff_directory") or REAL_EXTERNAL_HANDOFF_DIRECTORY)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": REAL_RESEARCH_CAPABILITY,
            "execution_mode": "REAL",
            "episode_id": self.episode_id,
            "topic": self.topic,
            "question": self.question,
            "budget_limit": self.budget_limit,
            "max_iterations": self.max_iterations,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "mission_authorization_path": self.mission_authorization_path,
            "mission_contract_path": self.mission_contract_path,
            "handoff_directory": str(self.handoff_directory),
            "terminal_stage": REAL_RESEARCH_TERMINAL_STAGE,
            "canonical_route": self.canonical_route_descriptor(),
            "real_ai_execution": False,
            "real_ai_calls": 0,
            "real_research_quality": "NOT_DEMONSTRATED",
            "authorized_for_product_use": False,
        }

    @staticmethod
    def canonical_stage_handlers() -> dict[str, Callable[..., Any]]:
        """Return the existing Research V2 stage authorities.

        M1 does not implement another runner.  It binds the prepared route to
        the canonical B2/M4/M5/M6 orchestrator methods so M2 can provide the
        execution adapter without creating a parallel vertical.
        """
        return {
            "B2": ResearchB2Orchestrator.run,
            "M4": ResearchB3Orchestrator.run,
            "M5": ResearchB3Orchestrator.run_m5,
            "M6": ResearchB4Orchestrator.run_m6,
        }

    @classmethod
    def canonical_route_descriptor(cls) -> dict[str, Any]:
        handlers = cls.canonical_stage_handlers()
        return {
            "vertical": "RESEARCH_V2",
            "stages": list(REAL_RESEARCH_CANONICAL_STAGES),
            "invocations": {stage: handlers[stage].__qualname__ for stage in REAL_RESEARCH_CANONICAL_STAGES},
            "sequence_owner": "RealResearchRoutePreparation.run_canonical_vertical",
            "terminal_stage": REAL_RESEARCH_TERMINAL_STAGE,
            "stop_after": "M6",
            "forbidden_post_terminal_stages": list(REAL_RESEARCH_FORBIDDEN_POST_TERMINAL_STAGES),
        }

    def run_canonical_vertical(
        self,
        stage_runners: Mapping[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]],
        *,
        initial_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Own the B2 -> M4 -> M5 -> M6 control flow.

        Each value is a per-stage adapter for the existing canonical
        orchestrator.  A single opaque runner is deliberately not accepted.
        M1 never supplies provider execution; M2 can inject controlled
        dependencies for the four canonical stage authorities.
        """
        if not isinstance(stage_runners, Mapping) or set(stage_runners) != set(REAL_RESEARCH_CANONICAL_STAGES):
            raise ResearchM7Error("REAL_ROUTE_CANONICAL_STAGE_RUNNERS_REQUIRED")
        if any(not callable(stage_runners[stage]) for stage in REAL_RESEARCH_CANONICAL_STAGES):
            raise ResearchM7Error("REAL_ROUTE_CANONICAL_STAGE_RUNNER_INVALID")

        context: dict[str, Any] = {
            "request": self.build_request(),
            "completed_stages": [],
            "stage_results": {},
        }
        if initial_context is not None:
            if not isinstance(initial_context, Mapping):
                raise ResearchM7Error("REAL_ROUTE_INITIAL_CONTEXT_INVALID")
            for key, value in initial_context.items():
                if key in {"request", "completed_stages", "stage_results"}:
                    raise ResearchM7Error(f"REAL_ROUTE_INITIAL_CONTEXT_RESERVED:{key}")
                context[key] = copy.deepcopy(value)
        for stage in REAL_RESEARCH_CANONICAL_STAGES:
            try:
                stage_result = stage_runners[stage](context)
            except ExternalCognitiveHandoffPending as pending:
                return {
                    "status": "PENDING_EXTERNAL_COGNITIVE_RESULT",
                    "pending_stage": pending.stage,
                    "handoff_id": pending.handoff_id,
                    "handoff_package_ref": str(pending.package_path.resolve()),
                    "completed_stages": list(context["completed_stages"]),
                    "stage_results": context["stage_results"],
                    "terminal_stage": None,
                    "real_ai_execution": False,
                    "real_ai_calls": 0,
                    "provenance": None,
                    "post_terminal_execution": False,
                }
            except HumanDecisionPending as pending:
                return {
                    "status": "WAITING_FOR_HUMAN_DECISION",
                    "pending_stage": "M4",
                    "human_decision_request": pending.request.to_dict(),
                    "completed_stages": list(context["completed_stages"]),
                    "stage_results": context["stage_results"],
                    "terminal_stage": None,
                    "real_ai_execution": False,
                    "real_ai_calls": 0,
                    "post_terminal_execution": False,
                }
            if not isinstance(stage_result, Mapping):
                raise ResearchM7Error(f"REAL_ROUTE_{stage}_RESULT_INVALID")
            context["stage_results"][stage] = copy.deepcopy(dict(stage_result))
            context["completed_stages"].append(stage)

        # The loop ends at M6 by construction.  No downstream callable is
        # accepted or invoked by this route.
        return {
            "status": "RESEARCH_READY",
            "terminal_stage": REAL_RESEARCH_TERMINAL_STAGE,
            "completed_stages": list(context["completed_stages"]),
            "stage_results": context["stage_results"],
            "canonical_route": self.canonical_route_descriptor(),
            "post_terminal_execution": False,
        }

    def build_request(self, *, input_artifacts: list[InputArtifact] | None = None, output_schema: str = "research_pack", role: str = "RESEARCH_AND_CURATION") -> ExecutionRequest:
        """Build, but deliberately do not execute, the canonical REAL request."""
        return ExecutionRequest(
            capability_id=REAL_RESEARCH_CAPABILITY,
            skill_id="extend_01_research_v2_real_e2e",
            skill_version=M7_VERSION,
            input_artifacts=list(input_artifacts or []),
            output_schema=output_schema,
            execution_mode="REAL",
            timeout=float(self.timeout_seconds),
            episode_id=self.episode_id,
            role=role,
            config={
                "repository_root": str(Path(__file__).resolve().parents[2]),
                "mission_authorization_path": self.mission_authorization_path,
                "mission_contract_path": self.mission_contract_path,
                "handoff_directory": str(self.handoff_directory),
                "budget_limit": self.budget_limit,
                "max_iterations": self.max_iterations,
                "max_retries": self.max_retries,
                "timeout_seconds": self.timeout_seconds,
                "real_ai_execution": False,
                "real_research": False,
                "real_ai_calls": 0,
                "terminal_stage": REAL_RESEARCH_TERMINAL_STAGE,
                "canonical_route": self.canonical_route_descriptor(),
            },
        )

    @staticmethod
    def claims_from_result(result: ExecutionResult | None, *, research_ready: bool = False, provenance_verified: bool = False) -> dict[str, Any]:
        real_success = bool(
            result is not None
            and result.status is ExecutionStatus.SUCCEEDED
            and result.is_real_editorial_execution is True
        )
        return {
            "real_ai_execution": real_success,
            "real_ai_calls": 1 if real_success else 0,
            "real_research": bool(real_success and research_ready and provenance_verified),
            "real_research_quality": "NOT_DEMONSTRATED",
            "authorized_for_product_use": False,
        }

    @staticmethod
    def assert_real_provenance(provenance: Mapping[str, Any]) -> None:
        if not isinstance(provenance, Mapping):
            raise ResearchM7Error("REAL_PROVENANCE_REQUIRED")
        executor_id = str(provenance.get("executor_id") or "")
        run_id = str(provenance.get("run_id") or "")
        if not run_id or not executor_id or executor_id == "synthetic-fixture" or run_id.startswith("M7-"):
            raise ResearchM7Error("REAL_PROVENANCE_SYNTHETIC_OR_MISSING")


def import_and_resume_external_research(
    store: VaultEpisodeStore,
    result_path: str | Path,
    *,
    _test_provenance_repository_root: Path | None = None,
    _test_acquisition_adapter: SoftwareAcquisitionAdapter | None = None,
) -> dict[str, Any]:
    """Import one pending Research V2 result and resume the same route.

    The pending handoff is the only authority for the accepted stage and
    bindings.  No provider, model, runtime, search or fetch is selected.
    """
    result_file = Path(result_path)
    try:
        payload = _read(result_file)
    except ResearchM7Error as exc:
        raise ResearchM7Error(f"ROUNDTRIP_RESULT_INVALID:{exc}") from exc
    if not isinstance(payload, Mapping):
        raise ResearchM7Error("ROUNDTRIP_RESULT_INVALID: resultado no es un objeto")
    episode_id = str(payload.get("episode_id") or "").strip()
    if not episode_id:
        raise ResearchM7Error("ROUNDTRIP_RESULT_INVALID: falta episode_id")
    episode = PersistedResearchEpisode.load(store, episode_id)
    state_path = episode.handle.folder / REAL_EXTERNAL_HANDOFF_STATE_FILENAME
    if not state_path.is_file():
        raise ResearchM7Error("ROUNDTRIP_IMPORT_BLOCKED:NO_PENDING_HANDOFF")
    state = _read(state_path)
    if not isinstance(state, Mapping) or state.get("status") != "PENDING_EXTERNAL_COGNITIVE_RESULT":
        raise ResearchM7Error("ROUNDTRIP_IMPORT_BLOCKED:NO_PENDING_HANDOFF")
    package_path = Path(str(state.get("handoff_package_ref") or ""))
    if not package_path.is_file():
        raise ResearchM7Error("HANDOFF_PACKAGE_MISSING")
    try:
        package = _read(package_path)
    except ResearchM7Error as exc:
        raise ResearchM7Error(f"HANDOFF_PACKAGE_INVALID:{exc}") from exc
    if not isinstance(package, Mapping):
        raise ResearchM7Error("HANDOFF_PACKAGE_INVALID")
    # The pending package is the sole authority for the next cognitive seam.
    # There is intentionally no parallel stage list here: the coordinator
    # emitted this package and the importer accepts only that exact package.
    bindings = {
                "mission_id": str(state.get("mission_id") or package.get("mission_id") or ""),
        "episode_id": episode_id,
        "capability_id": REAL_RESEARCH_CAPABILITY,
        "handoff_id": state.get("handoff_id"),
        "package_checksum": state.get("handoff_package_checksum"),
    }
    if any(package.get(key) != value for key, value in bindings.items()):
        raise ResearchM7Error("ROUNDTRIP_CHECKPOINT_BINDING_INVALID")
    for key in ("stage", "role", "output_schema", "input_manifest_checksum", "skill_id", "skill_version"):
        state_key = {
            "output_schema": "expected_return",
        }.get(key, key)
        if state.get(state_key) not in (None, "") and package.get(key) != state.get(state_key):
            raise ResearchM7Error(f"ROUNDTRIP_CHECKPOINT_BINDING_INVALID:{key}")
    try:
        cognitive_output = AgentHandoffProvider().import_result(package_path, result_file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, PermissionError, ValueError) as exc:
        raise ResearchM7Error(f"ROUNDTRIP_RESULT_BLOCKED:{exc}") from exc
    if not isinstance(cognitive_output, (Mapping, list)) or (isinstance(cognitive_output, list) and not cognitive_output):
        raise ResearchM7Error("RESEARCH_EXTERNAL_OUTPUT_INVALID")

    provenance = payload.get("provenance")
    prior_provenance = state.get("provenance") if isinstance(state, Mapping) else None
    prior_producer_provenance = state.get("producer_provenance") if isinstance(state, Mapping) else None
    provenance_status = "NOT_AVAILABLE"
    if provenance is not None:
        if not isinstance(provenance, Mapping):
            raise ResearchM7Error("EXTERNAL_PROVENANCE_INVALID")
        for field in ("mission_id", "episode_id", "capability_id", "stage", "role", "handoff_id"):
            if field in provenance and provenance.get(field) != package.get(field):
                raise ResearchM7Error(f"EXTERNAL_PROVENANCE_BINDING_INVALID:{field}")
        if not str(provenance.get("run_id") or "") or not str(provenance.get("executor_id") or ""):
            raise ResearchM7Error("EXTERNAL_PROVENANCE_UNVERIFIABLE")
        if provenance.get("run_id") != payload.get("result_run_id"):
            raise ResearchM7Error("EXTERNAL_PROVENANCE_RUN_BINDING_INVALID")
        if str(provenance.get("run_id")).startswith("M7-") or provenance.get("executor_id") == "synthetic-fixture":
            raise ResearchM7Error("EXTERNAL_PROVENANCE_SYNTHETIC")
        provenance = copy.deepcopy(dict(provenance))
        provenance_status = "REPORTED_AND_BOUND"
    producer_provenance = copy.deepcopy(dict(prior_producer_provenance)) if isinstance(prior_producer_provenance, Mapping) else None
    external_cognitive_provenance = None
    auditor_provenance = None
    if provenance_status == "REPORTED_AND_BOUND" and isinstance(provenance, Mapping):
        declared_producer = provenance.get("producer_provenance")
        if isinstance(declared_producer, Mapping):
            external_cognitive_provenance = copy.deepcopy(dict(declared_producer))
        else:
            external_cognitive_provenance = copy.deepcopy(dict(provenance))
        if str(package.get("stage") or "") == "M6_INDEPENDENT_RESEARCH_AUDIT":
            if provenance.get("role") != "INDEPENDENT_RESEARCH_AUDITOR":
                raise ResearchM7Error("M6_EXTERNAL_AUDITOR_ROLE_INVALID")
            required_auditor = ("actor_id", "run_id", "executor_id", "role")
            if any(not str(provenance.get(field) or "").strip() for field in required_auditor):
                raise ResearchM7Error("M6_EXTERNAL_AUDITOR_PROVENANCE_UNVERIFIABLE")
            auditor_provenance = copy.deepcopy(dict(provenance))
            auditor_provenance["source"] = "EXTERNAL_COGNITIVE_RESULT"
        elif isinstance(provenance.get("producer_provenance"), Mapping):
            # Explicit nested producer metadata remains a cognitive identity;
            # the M5 Software producer is bound later from its canonical run.
            external_cognitive_provenance = copy.deepcopy(dict(provenance["producer_provenance"]))

    stage = str(package.get("stage") or "")
    b2_root = episode.handle.folder / "research_v2" / "b2"
    planning = ResearchPlanningService()
    proposal_ref = None
    if stage == "RESEARCH_PLANNING":
        if not isinstance(cognitive_output, Mapping):
            raise ResearchM7Error("RESEARCH_PLAN_PROPOSAL_INVALID")
        proposal = cognitive_output
        persistence = ResearchB2Persistence(b2_root)
        proposal_ref = persistence.persist(
            "RESEARCH_PLAN_PROPOSAL", dict(proposal),
            artifact_id=f"{episode_id}:RESEARCH_PLAN_PROPOSAL",
            artifact_kind="ResearchPlanProposal",
            replace_invalid=True,
        )
        # The persisted artifact checksum is the lineage checksum.  Do not
        # derive a replacement from a newly materialized plan representation.
        plan = planning.bind_research_plan(
            proposal,
            episode_id=episode_id,
            brief_version=str(episode.brief["brief_version"]),
            research_role=str(episode.human_input.get("research_role") or "NORMAL"),
            editorial_intent=str(episode.human_input.get("editorial_intent") or "NO_DECLARADA"),
            origin_ref=str(proposal_ref["artifact_id"]),
        )
        plan["origin_artifact_refs"][0].update({
            "artifact_ref": proposal_ref["artifact_id"],
            "artifact_version": proposal_ref["artifact_version"],
            "checksum": proposal_ref["checksum"],
        })
    else:
        plan = None
    _write_json_atomic(
        episode.handle.folder / REAL_EXTERNAL_RESULT_FILENAME,
        {
            "handoff_id": package["handoff_id"],
            "episode_id": episode_id,
            "stage": stage,
            "result_run_id": payload.get("result_run_id"),
            "output_checksum": payload.get("output_checksum"),
            "provenance": provenance,
            "provenance_status": provenance_status,
            "producer_provenance": producer_provenance,
            "external_cognitive_provenance": external_cognitive_provenance,
            "auditor_provenance": auditor_provenance,
            "output": copy.deepcopy(cognitive_output),
            **({"proposal": dict(cognitive_output)} if stage == "RESEARCH_PLANNING" else {}),
        },
    )
    imported_state = dict(state)
    imported_state.update({
        "status": "IMPORTED_EXTERNAL_COGNITIVE_RESULT",
        "result_run_id": payload.get("result_run_id"),
        "result_checksum": payload.get("output_checksum"),
        "provenance": provenance,
        "provenance_status": provenance_status,
        "producer_provenance": producer_provenance,
        "external_cognitive_provenance": external_cognitive_provenance,
        "auditor_provenance": auditor_provenance,
        "imported_stage": stage,
        "completed_stages": [stage] if stage == "RESEARCH_PLANNING" else list(state.get("completed_stages", [])),
        "next_action": "RESUME_RESEARCH_V2",
        "research_plan_proposal": proposal_ref if stage == "RESEARCH_PLANNING" else state.get("research_plan_proposal"),
        "research_plan": {"status": "WILL_BE_PERSISTED_BY_B2"} if stage == "RESEARCH_PLANNING" else state.get("research_plan"),
    })
    _write_json_atomic(state_path, imported_state)

    controls = package.get("execution_controls")
    if not isinstance(controls, Mapping):
        raise ResearchM7Error("execution_controls ausentes en handoff Research")
    preparation = RealResearchRoutePreparation.from_mapping({
        "episode_id": episode_id,
        "topic": str(episode.brief["tema"]),
        "question": episode.brief.get("initial_question"),
        "budget_limit": controls.get("budget_limit"),
        "max_iterations": controls.get("max_iterations"),
        "max_retries": controls.get("max_retries"),
        "timeout_seconds": controls.get("timeout_seconds"),
        "mission_authorization_path": package.get("mission_authorization_path"),
        "mission_contract_path": package.get("mission_contract_path"),
        "handoff_directory": str(package_path.parent),
    })
    resumed = preparation.run_canonical_vertical(
        ProductiveResearchStageAdapters(
            episode,
            cognitive_executor=ExternalResearchCognitiveExecutor(episode, preparation),
            acquisition_adapter=_test_acquisition_adapter,
            _test_provenance_repository_root=(
                _test_provenance_repository_root
                if _test_provenance_repository_root is not None
                else Path(__file__).resolve().parents[2]
            ),
        ).stage_runners(),
        initial_context=(
            {
                **({"real_provenance": copy.deepcopy(dict(external_cognitive_provenance))} if isinstance(external_cognitive_provenance, Mapping) else {}),
                **({"producer_provenance": copy.deepcopy(dict(producer_provenance))} if isinstance(producer_provenance, Mapping) else {}),
                **({"auditor_provenance": copy.deepcopy(dict(auditor_provenance)), "external_auditor_required": True} if isinstance(auditor_provenance, Mapping) else {}),
                **({"external_auditor_required": True} if stage == "M6_INDEPENDENT_RESEARCH_AUDIT" else {}),
            }
            or None
        ),
    )
    return {
        "status": "IMPORTED_AND_RESUMED",
        "episode_id": episode_id,
        "imported_stage": stage,
        "provenance_status": provenance_status,
        "resume": resumed,
    }


@dataclass(frozen=True)
class M7Artifact:
    stage: str
    artifact_id: str
    artifact_kind: str
    artifact_version: str
    path: str
    checksum: str

    def to_dict(self) -> dict[str, str]:
        return {"stage": self.stage, "artifact_id": self.artifact_id, "artifact_kind": self.artifact_kind, "artifact_version": self.artifact_version, "path": self.path, "checksum": self.checksum}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchM7Error(f"M7_STATE_UNREADABLE:{path}") from exc


def _ref_payload(ref: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(ref[key]) for key in ("artifact_id", "artifact_kind", "artifact_version", "path", "checksum")}


class M7CheckpointStore:
    """Lightweight coordination state; canonical payloads stay in B2/B3/B4."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.root / "m7_checkpoint.json"

    def exists(self) -> bool:
        return self.checkpoint_path.is_file()

    def save(self, state: Mapping[str, Any]) -> None:
        _write_json_atomic(self.checkpoint_path, dict(state))

    def load(self) -> dict[str, Any]:
        if not self.exists():
            raise ResearchM7Error("M7_CHECKPOINT_MISSING")
        state = _read(self.checkpoint_path)
        if not isinstance(state, dict) or state.get("contract") != "plan012_m7_coordination":
            raise ResearchM7Error("M7_CHECKPOINT_CONTRACT_INVALID")
        self.verify(state)
        return state

    def verify(self, state: Mapping[str, Any]) -> None:
        for raw in list(state.get("artifacts", [])) + list(state.get("recovery_artifacts", [])):
            path = Path(str(raw.get("path", "")))
            if not path.is_file():
                raise ResearchM7Error(f"M7_STALE_DEPENDENCY:{raw.get('artifact_id')}:MISSING")
            raw_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            canonical_checksum = None
            try:
                canonical_checksum = _checksum(_read(path))
            except ResearchM7Error:
                pass
            if raw_checksum != raw.get("checksum") and canonical_checksum != raw.get("checksum"):
                raise ResearchM7Error(f"M7_STALE_DEPENDENCY:{raw.get('artifact_id')}:CHECKSUM_MISMATCH")


class ResearchV2B5I3Adapter:
    """Versioned, read-only adapter into the existing B5-I3 input validator."""

    _MANIFEST_KIND_BY_INPUT = {
        "research_pack": "ResearchPack",
        "claims_ledger": "ClaimsLedger",
        "source_access_and_evidence_report": "SourceAccessAndEvidenceReport",
        "refined_thesis": "RefinedThesis",
    }

    @staticmethod
    def _input_binding(item: InputArtifact) -> dict[str, Any]:
        payload = _read(item.path)
        return {
            "artifact_kind": item.artifact_kind,
            "artifact_id": item.artifact_id,
            "artifact_version": str(item.artifact_version or payload.get("artifact_version") or payload.get("version") or "1.0.0"),
            "checksum": _checksum(payload),
            "path": str(item.path),
            "producer_run_id": item.producer_run_id,
        }

    @staticmethod
    def _manifest_ref(manifest_ref: Mapping[str, Any]) -> dict[str, str]:
        return {
            "artifact_id": str(manifest_ref["artifact_id"]),
            "artifact_kind": str(manifest_ref["artifact_kind"]),
            "artifact_version": str(manifest_ref["artifact_version"]),
            "path": str(manifest_ref["path"]),
            "checksum": str(manifest_ref["checksum"]),
        }

    @staticmethod
    def validate_full_preflight(episode_id: str, inputs: list[InputArtifact]) -> dict[str, Any]:
        provided = {item.artifact_kind for item in inputs}
        missing = sorted(M3_REQUIRED_INPUT_KINDS - provided)
        if missing:
            raise ResearchM7Error("B5_I3_REQUIRED_INPUTS_MISSING:" + ",".join(missing))
        request = ExecutionRequest(
            capability_id="B5_I3_NARRATIVE_ARCHITECTURE",
            skill_id="skill_mapa_eventos_y_outline",
            skill_version="1.0.0",
            input_artifacts=inputs,
            output_schema="viewer_journey",
            execution_mode="SYNTHETIC_TEST",
            episode_id=episode_id,
            role="NARRATIVE_ARCHITECTURE",
        )
        try:
            _validate_m3_input_artifacts(request)
        except Exception as exc:
            raise ResearchM7Error(f"B5_I3_CONSUMER_CONTRACT_INVALID:{exc}") from exc
        return {"provided_input_kinds": sorted(provided), "required_input_kinds": sorted(M3_REQUIRED_INPUT_KINDS), "status": "PASS", "cognition_executed": False}

    @classmethod
    def validate_research_v2_precondition(
        cls,
        *,
        episode_id: str,
        manifest_ref: Mapping[str, Any],
        manifest: Mapping[str, Any],
        handoff: Mapping[str, Any],
        inputs: list[InputArtifact],
    ) -> dict[str, Any]:
        """Validate the single Research V2 -> B5-I3 consumability boundary."""
        expected_manifest_ref = cls._manifest_ref(manifest_ref)
        manifest_errors = validate_research_ready_manifest(dict(manifest))
        if manifest_errors:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_INVALID:" + " | ".join(manifest_errors))
        if expected_manifest_ref["artifact_kind"] != "ResearchReadyManifest" or expected_manifest_ref["artifact_id"] != str(manifest.get("manifest_id")):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_REF_MISMATCH")
        if expected_manifest_ref["artifact_version"] != str(manifest.get("research_version")) or expected_manifest_ref["checksum"] != _checksum(dict(manifest)):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_CHECKSUM_MISMATCH")
        if not Path(expected_manifest_ref["path"]).is_file() or _read(expected_manifest_ref["path"]) != dict(manifest):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_PATH_MISMATCH")
        state_bindings = manifest.get("state_bindings", {})
        if manifest.get("research_ready_state") == "NOT_RESEARCH_READY" or state_bindings.get("artifact_validity") != "VALID" or state_bindings.get("research_stage") != "READY" or state_bindings.get("selection_state") != "SELECTED":
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_NOT_CURRENT")
        if handoff.get("handoff_state") != "VALID" or handoff.get("stale_reason"):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_STALE")
        validation_status = handoff.get("validation", {}).get("status")
        if validation_status not in {"PENDING", "PASS"}:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_VALIDATION_MISSING")
        if handoff.get("research_ready_manifest_ref") != expected_manifest_ref:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_MANIFEST_BINDING_MISMATCH")
        if handoff.get("research_lineage") != {
            "research_artifacts": copy.deepcopy(manifest.get("research_artifacts", [])),
            "lineage": copy.deepcopy(manifest.get("lineage", {})),
        }:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:LINEAGE_BINDING_MISMATCH")
        manifest_artifacts_by_id = {str(item["artifact_id"]): item for item in manifest.get("research_artifacts", [])}
        if any(str(item) not in manifest_artifacts_by_id for item in manifest.get("lineage", {}).get("source_refs", [])):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:LINEAGE_UNRESOLVABLE")

        restrictions = manifest.get("downstream_restrictions")
        if not isinstance(restrictions, list):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_MISSING")
        if handoff.get("downstream_restrictions") != restrictions:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_BINDING_MISMATCH")
        restriction_binding = handoff.get("downstream_restriction_binding")
        expected_restriction_binding = {
            "manifest_checksum": expected_manifest_ref["checksum"],
            "restriction_ids": [str(item.get("restriction_id")) for item in restrictions],
            "restrictions_checksum": _checksum(restrictions),
        }
        if restriction_binding != expected_restriction_binding:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_UNBOUND")
        if any("B5-I3" not in item.get("affected_consumers", []) for item in restrictions):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_NOT_RESOLVABLE")

        projection = handoff.get("research_v2_projection")
        if not isinstance(projection, Mapping):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_PROJECTION_MISSING")
        if projection.get("projection_version") != M7_VERSION:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_PROJECTION_VERSION_INVALID")
        projection_manifest = projection.get("research_ready_manifest_ref")
        if projection_manifest != expected_manifest_ref:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_PROJECTION_MANIFEST_MISMATCH")
        selected = {str(item) for item in projection.get("selected_work_ids", [])}
        resolved = {str(item) for item in projection.get("resolved_work_ids", [])}
        if not selected or selected != resolved:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_WORK_SET_MISMATCH")
        research_refs = projection.get("research_refs")
        if not isinstance(research_refs, Mapping):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_REFS_MISSING")
        for label in ("deep_phenomenon_research", "deep_work_research", "deep_fidelity", "claims_ledger", "claim_sufficiency", "post_deep_comparison", "refined_thesis"):
            ref = research_refs.get(label)
            if not isinstance(ref, Mapping) or not Path(str(ref.get("path") or "")).is_file():
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_REF_UNRESOLVED:{label}")
            payload = _read(str(ref["path"]))
            if _checksum(payload) != str(ref.get("checksum")):
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_REF_CHECKSUM_MISMATCH:{label}")
        deep_work = _read(str(research_refs["deep_work_research"]["path"]))
        deep_fidelity = _read(str(research_refs["deep_fidelity"]["path"]))
        dossier_ids = {
            str(item.get("work", {}).get("material_id"))
            for item in [*(deep_work.get("dossiers", []) if isinstance(deep_work, Mapping) else []), *(deep_fidelity.get("dossiers", []) if isinstance(deep_fidelity, Mapping) else [])]
            if isinstance(item, Mapping) and isinstance(item.get("work"), Mapping)
        }
        if not selected.issubset(dossier_ids):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_V2_DOSSIERS_INCOMPLETE")
        semantic_context = handoff.get("research_v2_semantic_context")
        if semantic_context != projection:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:SEMANTIC_CONTEXT_PROJECTION_MISMATCH")
        legacy_boundary = handoff.get("legacy_b5_i3_preflight")
        if not isinstance(legacy_boundary, Mapping) or legacy_boundary.get("classification") != "LEGACY_TRANSVERSAL_FIXTURE" or legacy_boundary.get("non_authoritative") is not True:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:LEGACY_BOUNDARY_INVALID")
        forbidden_research_fields = {"function", "narrative_use", "expected_order", "sequence_rationale", "progression_map", "viewer_journey"}
        if forbidden_research_fields.intersection(json.dumps(semantic_context, ensure_ascii=False).lower().split('"')):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:NARRATIVE_FIELDS_IN_RESEARCH_CONTEXT")

        expected_input_bindings = [cls._input_binding(item) for item in inputs]
        if handoff.get("b5_i3_input_bindings") != expected_input_bindings:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:INPUT_BINDING_MISMATCH")
        if handoff.get("b5_i3_input_set_checksum") != _checksum(expected_input_bindings):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:INPUT_SET_CHECKSUM_MISMATCH")
        manifest_artifacts = {
            (str(item["artifact_id"]), str(item["artifact_kind"]), str(item["artifact_version"]), str(item["checksum"]))
            for item in manifest.get("research_artifacts", [])
        }
        for input_kind, manifest_kind in cls._MANIFEST_KIND_BY_INPUT.items():
            binding = next((item for item in expected_input_bindings if item["artifact_kind"] == input_kind), None)
            projection_ref = research_refs.get("deep_phenomenon_research") if input_kind == "research_pack" else None
            projection_binding = bool(
                binding and isinstance(projection_ref, Mapping)
                and binding["artifact_version"] == str(projection_ref.get("artifact_version"))
                and binding["checksum"] == str(projection_ref.get("checksum"))
                and str(projection_ref.get("artifact_kind")) == manifest_kind
            )
            if binding is None or ((binding["artifact_id"], manifest_kind, binding["artifact_version"], binding["checksum"]) not in manifest_artifacts and not projection_binding):
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_INPUT_UNBOUND:{input_kind}")
            expected_owned = projection_ref if projection_binding else manifest_artifacts_by_id.get(binding["artifact_id"])
            if handoff.get("research_owned_inputs", {}).get(input_kind) != expected_owned:
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_OWNED_INPUT_BINDING:{input_kind}")
        preflight = cls.validate_full_preflight(episode_id, inputs)
        return {
            **preflight,
            "research_handoff_precondition": "PASS",
            "research_ready_manifest_current": True,
            "downstream_restrictions_count": len(restrictions),
            "downstream_restrictions_resolvable": True,
            "input_binding_checksum": _checksum(expected_input_bindings),
        }

    @classmethod
    def build(cls, manifest: Mapping[str, Any], *, manifest_ref: Mapping[str, Any], research_pack: Mapping[str, Any], claims: Mapping[str, Any], source_access: Mapping[str, Any], refined_thesis: Mapping[str, Any], refs: list[InputArtifact], selected_work_ids: list[str], research_v2_projection: Mapping[str, Any]) -> dict[str, Any]:
        errors = validate_research_ready_manifest(dict(manifest))
        if errors:
            raise ResearchM7Error("B5_I3_HANDOFF_MANIFEST_INVALID:" + " | ".join(errors))
        if manifest.get("research_ready_state") == "NOT_RESEARCH_READY":
            raise ResearchM7Error("B5_I3_HANDOFF_NOT_READY")
        manifest_reference = cls._manifest_ref(manifest_ref)
        input_bindings = [cls._input_binding(item) for item in refs]
        restriction_binding = {
            "manifest_checksum": manifest_reference["checksum"],
            "restriction_ids": [str(item.get("restriction_id")) for item in manifest.get("downstream_restrictions", [])],
            "restrictions_checksum": _checksum(manifest.get("downstream_restrictions", [])),
        }
        manifest_artifacts_by_id = {str(item["artifact_id"]): item for item in manifest.get("research_artifacts", [])}
        projection = dict(research_v2_projection)
        projection_refs = projection.get("research_refs", {})
        research_owned_inputs: dict[str, dict[str, Any]] = {}
        for input_kind, manifest_kind in cls._MANIFEST_KIND_BY_INPUT.items():
            binding = next((item for item in input_bindings if item["artifact_kind"] == input_kind), None)
            owned = manifest_artifacts_by_id.get(str(binding["artifact_id"])) if binding else None
            if input_kind == "research_pack" and isinstance(projection_refs.get("deep_phenomenon_research"), Mapping):
                deep_ref = projection_refs["deep_phenomenon_research"]
                if binding and binding["artifact_version"] == str(deep_ref.get("artifact_version")) and binding["checksum"] == str(deep_ref.get("checksum")):
                    owned = copy.deepcopy(dict(deep_ref))
            if binding is None or not owned or owned.get("artifact_kind") != manifest_kind or owned.get("artifact_version") != binding["artifact_version"] or owned.get("checksum") != binding["checksum"]:
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_INPUT_UNBOUND:{input_kind}")
            research_owned_inputs[input_kind] = copy.deepcopy(owned)
        handoff = {
            "contract": "research_v2_b5_i3_handoff",
            "contract_version": M7_VERSION,
            "consumer": "B5-I3",
            "handoff_state": "VALID",
            "research_ready_manifest_ref": manifest_reference,
            "research_input_refs": [{"artifact_kind": ref.artifact_kind, "artifact_id": ref.artifact_id, "path": str(ref.path), "producer_run_id": ref.producer_run_id} if isinstance(ref, InputArtifact) else dict(ref) for ref in refs],
            "b5_i3_input_refs": copy.deepcopy(input_bindings),
            "b5_i3_input_bindings": copy.deepcopy(input_bindings),
            "b5_i3_input_set_checksum": _checksum(input_bindings),
            "required_input_kinds": sorted(M3_REQUIRED_INPUT_KINDS),
            "research_owned_inputs": research_owned_inputs,
            "selected_work_ids": list(selected_work_ids),
            "research_v2_projection": copy.deepcopy(dict(research_v2_projection)),
            "research_v2_semantic_context": copy.deepcopy(dict(research_v2_projection)),
            "legacy_b5_i3_preflight": {
                "classification": "LEGACY_TRANSVERSAL_FIXTURE",
                "status": "COMPATIBILITY_ONLY",
                "non_authoritative": True,
                "input_kinds": ["narrative_human_analysis", "material_curation"],
                "not_included_in_research_v2_semantic_context": True,
            },
            "downstream_restrictions": copy.deepcopy(manifest.get("downstream_restrictions", [])),
            "downstream_restriction_binding": restriction_binding,
            "research_lineage": {"research_artifacts": copy.deepcopy(manifest.get("research_artifacts", [])), "lineage": copy.deepcopy(manifest.get("lineage", {}))},
            "narrative_decisions_not_made": True,
            "validation": {"status": "PENDING"},
        }
        preflight = cls.validate_research_v2_precondition(episode_id=str(manifest.get("episode_id")), manifest_ref=manifest_ref, manifest=manifest, handoff=handoff, inputs=refs)
        handoff["validation"] = {"consumer": "ResearchV2B5I3Adapter.validate_research_v2_precondition", **preflight}
        if any(key in handoff for key in NARRATIVE_FIELDS):
            raise ResearchM7Error("B5_I3_HANDOFF_NARRATIVE_FIELD_FORBIDDEN")
        return handoff


class ResearchM7SyntheticRunner:
    """Coordinate a canonical B2→M4→M5→M6 run with synthetic cognition."""

    def __init__(self, root: str | Path, *, selection_mode: str = "MANUAL", delegated_scope: list[str] | None = None, max_iterations: int = 3):
        if selection_mode not in {"MANUAL", "DELEGATED"}:
            raise ResearchM7Error("M7_SELECTION_MODE_INVALID")
        if int(max_iterations) < 1:
            raise ResearchM7Error("M7_MAX_ITERATIONS_INVALID")
        self.root = Path(root)
        self.store = M7CheckpointStore(self.root)
        self.selection_mode = selection_mode
        self.delegated_scope = sorted(set(str(item) for item in (delegated_scope or [])))
        self.max_iterations = int(max_iterations)
        self.invalidation = InvalidationEngine()

    def _new_state(self, human_input: Mapping[str, Any]) -> dict[str, Any]:
        return {"contract": "plan012_m7_coordination", "contract_version": M7_VERSION, "run_id": f"M7-{human_input['episode_id']}", "generation": 1, "status": "IN_PROGRESS", "next_stage": "INTAKE", "completed_stages": [], "invalidated_stages": [], "artifacts": [], "recovery_artifacts": [], "canonical_refs": {}, "events": [], "human_input": copy.deepcopy(dict(human_input)), "selection_mode": self.selection_mode, "delegated_scope": list(self.delegated_scope), "real_ai_execution": False, "product_use_authorized": False, "p2_real_execution": False, "research_quality": "NOT_DEMONSTRATED", "created_at": _now(), "updated_at": _now()}

    @staticmethod
    def _validate_input(value: Mapping[str, Any]) -> None:
        works = value.get("works")
        if not isinstance(works, list) or not works or not all(isinstance(item, str) and item.strip() for item in works):
            raise ResearchM7Error("M7_HUMAN_WORK_INPUT_REQUIRED")
        if len(set(works)) != len(works):
            raise ResearchM7Error("M7_HUMAN_WORK_INPUT_DUPLICATE")
        target = value.get("target_final_works")
        count = target.get("requested_count") if isinstance(target, Mapping) else target
        if not isinstance(count, int) or count < 3 or count > 5:
            raise ResearchM7Error("M7_TARGET_FINAL_WORKS_EXPLICIT_AND_VALID_REQUIRED")
        if count > len(works):
            raise ResearchM7Error("M7_TARGET_FINAL_WORKS_EXCEEDS_INPUT")
        selected = value.get("selected_work_ids")
        if not isinstance(selected, list) or not selected or not set(selected).issubset(set(works)):
            raise ResearchM7Error("M7_SELECTION_INPUT_REQUIRED")
        if len(selected) != count:
            raise ResearchM7Error("M7_SELECTION_COUNT_MISMATCH")
        if value.get("episode_id") is None or value.get("topic") is None:
            raise ResearchM7Error("M7_HUMAN_INPUT_REQUIRED")

    def _state(self, human_input: Mapping[str, Any] | None, resume: bool) -> dict[str, Any]:
        if self.store.exists():
            state = self.store.load()
            if human_input is not None and dict(human_input) != state.get("human_input"):
                raise ResearchM7Error("M7_RESUME_INPUT_MISMATCH")
            return state
        if resume:
            raise ResearchM7Error("M7_RESUME_CHECKPOINT_MISSING")
        if not isinstance(human_input, Mapping):
            raise ResearchM7Error("M7_HUMAN_INPUT_REQUIRED")
        self._validate_input(human_input)
        state = self._new_state(human_input)
        self.store.save(state)
        return state

    @staticmethod
    def _event(state: dict[str, Any], boundary: str, stage: str, **extra: Any) -> None:
        state.setdefault("events", []).append({"boundary": boundary, "stage": stage, "at": _now(), **extra})

    def _synthetic_run_for(
        self,
        state: Mapping[str, Any],
        base: Mapping[str, Any],
        ref: Mapping[str, Any],
        run_id: str,
        *,
        role: str = "RESEARCH_AND_CURATION",
        output_kind: str = "semantic_audit",
    ) -> dict[str, Any]:
        """Project a materialized synthetic artifact into the canonical registry."""
        run = copy.deepcopy(dict(base))
        artifact_ref = f"{ref['artifact_kind']}:{ref['artifact_id']}"
        run.update({
            "run_id": run_id,
            "episode_id": state["human_input"]["episode_id"],
            "role": role,
            "role_id": role,
            "agent_id": run_id,
            "actual_executor": "synthetic-fixture",
            "status": "SUCCEEDED",
            "output_artifact_ids": [artifact_ref],
            "output_versions": [ref["artifact_version"]],
            "output_checksums": [ref["checksum"]],
            "outputs": [{
                "artifact_kind": output_kind,
                "artifact_id": ref["artifact_id"],
                "artifact_ref": artifact_ref,
                "checksum": ref["checksum"],
            }],
        })
        return run

    def _materialize_recovery(self, state: dict[str, Any]) -> None:
        recovery_dir = self.root / f"recovery_g{state.get('generation', 1)}"
        recovery_dir.mkdir(parents=True, exist_ok=True)
        inp = state["human_input"]
        values = [("S1", {"source_id": "S1", "content": "Fixture controlado materializado por Software.", "locator": "fixture://S1", "synthetic": True})]
        values.extend((str(work_id), {"work_id": str(work_id), "content": f"Fixture de obra {work_id}.", "locator": f"fixture://{work_id}", "synthetic": True}) for work_id in inp["works"])
        state["recovery_artifacts"] = []
        for identifier, payload in values:
            path = recovery_dir / f"{identifier}.json"
            _write_json_atomic(path, payload)
            state["recovery_artifacts"].append({"artifact_id": f"recovery:{identifier}", "artifact_kind": "RecoveredSourceFixture" if identifier == "S1" else "RecoveredWorkFixture", "artifact_version": "1.0.0", "path": str(path), "checksum": hashlib.sha256(path.read_bytes()).hexdigest()})
        repo_root = self.root / "canonical_repo"
        registry_source = Path(__file__).resolve().parents[2] / "output" / "execution_provenance_registry.json"
        registry = _read(registry_source)
        base = copy.deepcopy(registry["runs"][0])
        registry["runs"] = [
            self._synthetic_run_for(
                state,
                base,
                artifact,
                f"M7-ACQUISITION-{artifact['artifact_id'].split(':', 1)[1]}",
                role="RESEARCH_ACQUISITION",
                output_kind="research",
            )
            for artifact in state["recovery_artifacts"]
        ]
        _write_json_atomic(repo_root / "config" / "execution_provenance_policy.json", {"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"})
        _write_json_atomic(repo_root / "output" / "execution_provenance_registry.json", registry)

    def _adapter(self, state: Mapping[str, Any]) -> SoftwareAcquisitionAdapter:
        bindings = {"S1": {"request_ref": "request:S1", "execution_ref": "M7-ACQUISITION-S1", "recovery_artifact_ref": "recovery:S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}}
        work_bindings = {str(work_id): {"request_ref": f"request:{work_id}", "execution_ref": f"M7-ACQUISITION-{work_id}", "recovery_artifact_ref": f"recovery:{work_id}", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True, "representation_kind": "ORIGINAL_WORK", "edition_or_version": "fixture-1", "consulted_locator": f"fixture://{work_id}"} for work_id in state["human_input"]["works"]}
        recovery_artifacts = {
            str(item["artifact_id"]): dict(item)
            for item in state.get("recovery_artifacts", [])
            if isinstance(item, Mapping) and item.get("artifact_id")
        }
        return SoftwareAcquisitionAdapter(
            bindings,
            work_bindings=work_bindings,
            recovery_artifacts=recovery_artifacts,
            execution_registry_path=self.root / "canonical_repo" / "output" / "execution_provenance_registry.json",
        )

    def _context(self, state: Mapping[str, Any]) -> dict[str, Any]:
        inp = state["human_input"]
        report = source_report(str(inp["episode_id"]), f"RP-M7-{inp['episode_id']}")
        materials = []
        for source in report.get("fuentes_primarias", []) + report.get("fuentes_secundarias", []):
            if not isinstance(source, Mapping) or not source.get("source_id"):
                continue
            source_id = str(source["source_id"])
            materials.append({
                "material_ref": source_id,
                "material_kind": "TEXT",
                "availability": "AVAILABLE_LOCAL",
                "access_mode": "DIRECT",
                "artifact_ref": f"recovery:{source_id}",
                "checksum": None,
                "limitations": [],
                "provenance_ref": f"provenance:{source_id}",
            })
        source_access = {
            "contract": "research_source_access",
            "contract_version": "1.0.0",
            "access_id": f"{inp['episode_id']}:SOURCE_ACCESS",
            "episode_id": str(inp["episode_id"]),
            "brief_version": "1.0.0",
            "capabilities": {"owner_material_ingestion": "AVAILABLE", "web_search": "UNAVAILABLE", "http_fetch": "UNAVAILABLE"},
            "materials": materials,
            "unavailable_source_types": ["WEB_SEARCH", "HTTP_FETCH"],
            "limitations": ["Fixture sintético exclusivamente para pruebas estructurales."],
            "origin_artifact_refs": [f"synthetic-input:{inp['episode_id']}"],
            "created_at": _now(),
        }
        return {"topic": str(inp["topic"]), "source_access": source_access, "brief": {"brief_id": f"BRIEF-{inp['episode_id']}"}, "channel_context": {"channel_id": "CHANNEL-M7"}}

    def _store_coord(self, state: dict[str, Any], stage: str, ref: Mapping[str, Any], *, kind: str | None = None) -> None:
        item = {"stage": stage, **_ref_payload(ref)}
        state["artifacts"] = [old for old in state.get("artifacts", []) if old.get("stage") != stage]
        state["artifacts"].append(item)
        if kind:
            state.setdefault("canonical_refs", {}).setdefault(kind, []).append(_ref_payload(ref))

    @staticmethod
    def _record_evidence(state: dict[str, Any], ref: Mapping[str, Any]) -> None:
        exact = dict(ref)
        state["source_ref"] = exact
        refs = [item for item in state.get("evidence_refs", []) if item.get("artifact_id") != exact.get("artifact_id")]
        refs.append(exact)
        state["evidence_refs"] = refs
        state.setdefault("canonical_refs", {})["SourceAccessAndEvidenceReport"] = [dict(item) for item in refs]

    def _baseline(self, b2_result: Mapping[str, Any]) -> dict[str, Any]:
        manifest = _read(b2_result["execution_manifest"]["path"])
        by_kind = {str(ref["artifact_kind"]): ref for ref in manifest["artifacts"]}
        def payload(kind: str) -> Any:
            return _read(by_kind[kind]["path"])
        return {"research_plan": _read(b2_result["research_plan"]["path"]), "phenomenon_base_research": payload("ResearchPack"), "work_discovery": payload("WorkLifecycle"), "base_research_pool": payload("WorkResearchDossierCollection")["dossiers"], "preliminary_fidelity": _read(b2_result["preliminary_fidelity"]["path"])["dossiers"], "initial_sufficiency": _read(b2_result["initial_sufficiency"]["path"])["dossiers"], "provisional_thesis": payload("ThesisArtifact"), "research_comparison": payload("ResearchComparison"), "deepening_targets": b2_result["deepening_targets"], "lifecycle": b2_result["lifecycle_projection"], "evidence_report": b2_result["evidence_report"]}

    def _m4_result(self, ref: Mapping[str, Any]) -> dict[str, Any]:
        manifest = _read(ref["path"])
        result = {"execution_manifest": dict(ref)}
        for item in manifest["artifacts"]:
            kind = str(item["artifact_kind"])
            if kind == "ResearchPack": result["deep_phenomenon_research"] = item
            elif kind in {"ResearchStopDecision", "ResearchStopDecisionCollection"}: result["deep_phenomenon_sufficiency" if ":PHENOMENON" in str(item["artifact_id"]) else "deep_work_sufficiency"] = item
            elif kind == "WorkResearchDossierCollection":
                payload = _read(item["path"])
                result["deep_fidelity" if payload.get("dossiers", [{}])[0].get("research_stage") == "DEEP_FIDELITY" else "deep_work_research"] = item
            elif kind == "SourceAccessAndEvidenceReport": result["evidence_report"] = item
        return result

    def _provenance(
        self,
        state: Mapping[str, Any],
        b2: Mapping[str, Any],
        m4: Mapping[str, Any],
        m5: Mapping[str, Any],
        *,
        execution_mode: str = "SYNTHETIC_TEST",
        real_provenance: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if str(execution_mode).upper() == "REAL":
            if not isinstance(real_provenance, Mapping):
                raise ResearchM7Error("REAL_PROVENANCE_REQUIRED")
            RealResearchRoutePreparation.assert_real_provenance(real_provenance.get("producer_provenance", real_provenance))
            return {"artifact_refs": []}, copy.deepcopy(dict(real_provenance))
        repo_root = self.root / "canonical_repo"
        local_registry_path = repo_root / "output" / "execution_provenance_registry.json"
        registry_source = local_registry_path if local_registry_path.is_file() else Path(__file__).resolve().parents[2] / "output" / "execution_provenance_registry.json"
        registry = _read(registry_source)
        prior_runs = [item for item in registry.get("runs", []) if isinstance(item, Mapping)]
        base = copy.deepcopy(registry["runs"][0])
        b2_manifest = _read(b2["execution_manifest"]["path"])
        m4_manifest = _read(m4["execution_manifest"]["path"])
        m5_manifest = _read(m5["execution_manifest"]["path"])
        evidence_refs = list(state.get("evidence_refs", [state["source_ref"]]))
        refs = [b2["execution_manifest"], *b2_manifest["artifacts"], m4["execution_manifest"], *m4_manifest["artifacts"], m5["execution_manifest"], *m5_manifest["m5_outputs"], *evidence_refs]
        unique = {(r["artifact_id"], r["artifact_kind"], r["checksum"]): r for r in refs}
        producer = self._synthetic_run_for(state, base, m5["execution_manifest"], "M7-M5-PRODUCER")
        upstream = [self._synthetic_run_for(state, base, ref, f"M7-UPSTREAM-{index:03d}") for index, ref in enumerate(unique.values(), start=1) if ref is not m5["execution_manifest"]]
        preserved_runs = [
            run for run in prior_runs
            if run.get("role") in {"INDEPENDENT_RESEARCH_AUDITOR", "RESEARCH_ACQUISITION"}
            and run.get("run_id") not in {producer.get("run_id"), *(item.get("run_id") for item in upstream)}
        ]
        registry["runs"] = [producer, *upstream, *preserved_runs]
        _write_json_atomic(repo_root / "config" / "execution_provenance_policy.json", {"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"})
        _write_json_atomic(repo_root / "output" / "execution_provenance_registry.json", registry)
        provenance = {"producer_provenance": {"actor_id": "M7-M5-PRODUCER", "run_id": "M7-M5-PRODUCER", "executor_id": "synthetic-fixture", "role": "RESEARCH_AND_CURATION", "provenance_ref": "output/execution_provenance_registry.json", "artifact_ref": {key: m5["execution_manifest"][key] for key in ("artifact_id", "artifact_kind", "artifact_version", "checksum")}}, "repository_root": str(repo_root), "execution_provenance_registry_ref": "output/execution_provenance_registry.json"}
        return {"artifact_refs": [b2["execution_manifest"], *b2_manifest["artifacts"], m4["execution_manifest"], *m4_manifest["artifacts"], *evidence_refs]}, provenance

    def _research_v2_projection(self, state: Mapping[str, Any], manifest: Mapping[str, Any], manifest_ref: Mapping[str, Any], m4: Mapping[str, Any], m5: Mapping[str, Any], selected_work_ids: list[str]) -> dict[str, Any]:
        refs = {
            "deep_phenomenon_research": m4["deep_phenomenon_research"],
            "deep_work_research": m4["deep_work_research"],
            "deep_fidelity": m4["deep_fidelity"],
            "claims_ledger": m5["claims_ledger"],
            "claim_sufficiency": m5["claim_sufficiency"],
            "post_deep_comparison": m5["post_deep_comparison"],
            "refined_thesis": m5["refined_thesis"],
        }
        selected = [str(item) for item in selected_work_ids]
        dossier_ids: set[str] = set()
        for label in ("deep_work_research", "deep_fidelity"):
            payload = _read(refs[label]["path"])
            dossier_ids.update(
                str(item.get("work", {}).get("material_id"))
                for item in payload.get("dossiers", [])
                if isinstance(item, Mapping) and isinstance(item.get("work"), Mapping)
            )
        if set(selected) != dossier_ids:
            raise ResearchM7Error("B5_I3_RESEARCH_V2_PROJECTION_WORK_SET_INVALID")
        thesis_payload = _read(refs["refined_thesis"]["path"])
        thesis_work_ids = {
            str(item.get("material_id"))
            for item in thesis_payload.get("material_contributions", [])
            if isinstance(item, Mapping) and item.get("material_id")
        }
        if thesis_work_ids != set(selected):
            raise ResearchM7Error("B5_I3_RESEARCH_V2_REFINED_THESIS_CONTRIBUTIONS_INVALID")
        return {
            "projection_version": M7_VERSION,
            "authority": "RESEARCH_V2",
            "selected_work_ids": selected,
            "resolved_work_ids": sorted(dossier_ids),
            "research_ready_manifest_ref": ResearchV2B5I3Adapter._manifest_ref(manifest_ref),
            "research_refs": {key: _ref_payload(value) for key, value in refs.items()},
            "research_stop_refs": {
                "claim_sufficiency": _ref_payload(m5["claim_sufficiency"]),
            },
            "downstream_restrictions": copy.deepcopy(manifest.get("downstream_restrictions", [])),
            "lineage": copy.deepcopy(manifest.get("lineage", {})),
            "refined_thesis_material_work_ids": sorted(thesis_work_ids),
            "refined_thesis_contribution_binding": {
                "artifact_id": str(refs["refined_thesis"]["artifact_id"]),
                "checksum": str(refs["refined_thesis"]["checksum"]),
                "work_ids": sorted(thesis_work_ids),
            },
            "legacy_compatibility_inputs_not_authoritative": ["narrative_human_analysis", "material_curation"],
        }

    def _materialize_b5_i3_inputs(self, state: dict[str, Any], baseline: Mapping[str, Any], m4: Mapping[str, Any], m5: Mapping[str, Any]) -> list[InputArtifact]:
        source = _read(state["source_ref"]["path"])
        claims = _read(m5["claims_ledger"]["path"])
        thesis = _read(m5["refined_thesis"]["path"])
        profile = _read(Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json")
        fixtures = b5_i3_transversal_fixtures(
            episode_id=str(state["human_input"]["episode_id"]),
            topic=str(state["human_input"]["topic"]),
            works=[str(item) for item in state["human_input"]["works"]],
            profile=profile,
            research_pack=_read(m4["deep_phenomenon_research"]["path"]),
            source_report_payload=source,
            claims_ledger=claims,
            refined_thesis_payload=thesis,
            refined_thesis_checksum=hashlib.sha256(Path(m5["refined_thesis"]["path"]).read_bytes()).hexdigest(),
        )
        b2_manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "B2")
        b2_manifest = _read(b2_manifest_ref["path"])
        research_ref = dict(m4["deep_phenomenon_research"])
        refs: list[InputArtifact] = [
            InputArtifact("human_input", str(fixtures["human_input"]["interaction_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "human_input.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("active_editorial_profile_reference", "ACTIVE_PROFILE_REFERENCE", self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "active_editorial_profile_reference.json", "M7-PROFILE"),
            InputArtifact("episode_brief", str(fixtures["episode_brief"]["episode_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "episode_brief.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("research_pack", str(_read(research_ref["path"])["research_id"]), Path(research_ref["path"]), "M7-M4", str(research_ref["artifact_version"])),
            InputArtifact("claims_ledger", str(claims["ledger_id"]), Path(m5["claims_ledger"]["path"]), "M7-M5", str(m5["claims_ledger"]["artifact_version"])),
            InputArtifact("source_access_and_evidence_report", str(source["report_id"]), Path(state["source_ref"]["path"]), "M7-SOURCE", str(state["source_ref"]["artifact_version"])),
            InputArtifact("narrative_human_analysis", str(fixtures["narrative_human_analysis"]["analysis_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "narrative_human_analysis.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("material_curation", str(fixtures["material_curation"]["curation_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "material_curation.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("refined_thesis", str(thesis["thesis_id"]), Path(m5["refined_thesis"]["path"]), "M7-M5", str(m5["refined_thesis"]["artifact_version"])),
            InputArtifact("editorial_script_promise", str(fixtures["editorial_script_promise"]["promise_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "editorial_script_promise.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("early_packaging_hypothesis", str(fixtures["early_packaging_hypothesis"]["packaging_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "early_packaging_hypothesis.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("b5_i2_semantic_audit", str(fixtures["b5_i2_semantic_audit"]["audit_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "b5_i2_semantic_audit.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("youtube_adaptation_review", str(fixtures["youtube_adaptation_review"]["review_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "youtube_adaptation_review.json", "M7-TRANSVERSAL-FIXTURE"),
        ]
        directory = self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}"
        directory.mkdir(parents=True, exist_ok=True)
        for item in refs:
            if item.artifact_kind in {"research_pack", "claims_ledger", "source_access_and_evidence_report", "refined_thesis"}:
                continue
            payload = fixtures[item.artifact_kind]
            schema_by_kind = {
                "human_input": "human_episode_input",
                "active_editorial_profile_reference": "active_editorial_profile",
                "b5_i2_semantic_audit": "b5_i2_semantic_sufficiency_audit",
            }
            errors = validate_against_schema(payload, schema_by_kind.get(item.artifact_kind, item.artifact_kind))
            if errors:
                raise ResearchM7Error(f"B5_I3_TRANSVERSAL_FIXTURE_INVALID:{item.artifact_kind}:" + " | ".join(errors))
            _write_json_atomic(item.path, payload)
        return refs

    def _validate_consumer(self, state: dict[str, Any], manifest: Mapping[str, Any], baseline: Mapping[str, Any], m4: Mapping[str, Any], m5: Mapping[str, Any]) -> dict[str, Any]:
        source = self._context(state)["source_access"]
        claims = _read(m5["claims_ledger"]["path"])
        thesis = _read(m5["refined_thesis"]["path"])
        inputs = self._materialize_b5_i3_inputs(state, baseline, m4, m5)
        manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "M6")
        comparison = _read(m5["post_deep_comparison"]["path"])
        m4_ref = next(item for item in state["artifacts"] if item["stage"] == "M4")
        m4_result = self._m4_result(m4_ref)
        selected = [str(item) for item in comparison["selected_work_ids"]]
        projection = self._research_v2_projection(state, manifest, manifest_ref, m4_result, m5, selected)
        return ResearchV2B5I3Adapter.build(manifest, manifest_ref=manifest_ref, research_pack=_read(m4_result["deep_phenomenon_research"]["path"]), claims=claims, source_access=source, refined_thesis=thesis, refs=inputs, selected_work_ids=selected, research_v2_projection=projection)

    def _b2_result_from_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "B2")
        plan_ref = next(item for item in state["artifacts"] if item["stage"] == "RESEARCH_PLAN")
        manifest = _read(manifest_ref["path"])
        by_kind = {str(ref["artifact_kind"]): ref for ref in manifest["artifacts"]}
        return {"research_plan": plan_ref, "phenomenon_base_research": by_kind["ResearchPack"], "work_discovery": by_kind["WorkLifecycle"], "base_research_pool": next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":BASE_RESEARCH_POOL")), "preliminary_fidelity": next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":PRELIMINARY_FIDELITY")), "initial_sufficiency": next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":INITIAL_SUFFICIENCY")), "provisional_thesis": by_kind["ThesisArtifact"], "research_comparison": by_kind["ResearchComparison"], "evidence_report": by_kind["SourceAccessAndEvidenceReport"], "deepening_targets": manifest["deepening_targets"], "lifecycle_projection": manifest["lifecycle_projection"], "execution_manifest": manifest_ref}

    def _m5_result_from_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        m5_ref = next(item for item in state["artifacts"] if item["stage"] == "M5")
        manifest = _read(m5_ref["path"])
        result = {"execution_manifest": m5_ref}
        output_names = {
            "ClaimsLedger": "claims_ledger",
            "ResearchStopDecisionCollection": "claim_sufficiency",
            "ResearchComparison": "post_deep_comparison",
            "RefinedThesis": "refined_thesis",
            "SourceAccessAndEvidenceReport": "evidence_report",
        }
        for item in manifest["m5_outputs"]:
            name = output_names.get(item["artifact_kind"])
            if name:
                result[name] = item
        return result

    @staticmethod
    def _coord_ref(path: Path, *, artifact_id: str, artifact_kind: str, artifact_version: str = M7_VERSION) -> dict[str, str]:
        payload = _read(path)
        return {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "artifact_version": artifact_version,
            "path": str(path),
            "checksum": _checksum(payload),
        }

    @staticmethod
    def _verify_coord_ref(ref: Mapping[str, Any], label: str) -> None:
        path = Path(str(ref.get("path") or ""))
        if not path.is_file():
            raise ResearchM7Error(f"M7_RECOVERY_{label}_MISSING")
        payload_checksum = _checksum(_read(path))
        if payload_checksum != str(ref.get("checksum") or ""):
            raise ResearchM7Error(f"M7_RECOVERY_{label}_CHECKSUM_MISMATCH")

    def _reconcile_persisted_stages(self, state: dict[str, Any]) -> None:
        """Promote valid canonical files when the coordination checkpoint lagged."""
        root = self.root / f"canonical_g{state.get('generation', 1)}"
        b2_root = root / "b2"
        b3_root = root / "b3"
        artifacts = {str(item.get("stage")): item for item in state.get("artifacts", [])}
        changed = False

        b2_manifest_path = b2_root / "research_b2_execution.json"
        if b2_manifest_path.is_file():
            manifest = _read(b2_manifest_path)
            if manifest.get("manifest_type") != "RESEARCH_B2_EXECUTION":
                raise ResearchM7Error("M7_RECOVERY_B2_MANIFEST_INVALID")
            plan_path = b2_root / "research_plan.json"
            if not plan_path.is_file():
                raise ResearchM7Error("M7_RECOVERY_B2_RESEARCH_PLAN_MISSING")
            plan = _read(plan_path)
            plan_ref = self._coord_ref(
                plan_path,
                artifact_id=str(plan.get("research_plan_id") or ""),
                artifact_kind="ResearchPlan",
                artifact_version=str(plan.get("research_contract_version") or M7_VERSION),
            )
            if not plan_ref["artifact_id"]:
                raise ResearchM7Error("M7_RECOVERY_B2_RESEARCH_PLAN_INVALID")
            for item in manifest.get("artifacts", []):
                self._verify_coord_ref(item, "B2_ARTIFACT")
            b2_ref = self._coord_ref(
                b2_manifest_path,
                artifact_id=str(manifest.get("research_plan_id") or f"{plan_ref['artifact_id']}:B2"),
                artifact_kind="ResearchB2ExecutionManifest",
                artifact_version=str(manifest.get("manifest_version") or M7_VERSION),
            )
            if "RESEARCH_PLAN" not in artifacts:
                self._store_coord(state, "RESEARCH_PLAN", plan_ref, kind="ResearchPlan")
                artifacts["RESEARCH_PLAN"] = state["artifacts"][-1]
                changed = True
            else:
                self._verify_coord_ref(artifacts["RESEARCH_PLAN"], "RESEARCH_PLAN")
            if "B2" not in artifacts:
                self._store_coord(state, "B2", b2_ref, kind="ResearchB2ExecutionManifest")
                artifacts["B2"] = state["artifacts"][-1]
                changed = True
            else:
                self._verify_coord_ref(artifacts["B2"], "B2")
            source_ref = next(
                (dict(item) for item in manifest.get("artifacts", [])
                 if item.get("artifact_kind") == "SourceAccessAndEvidenceReport"),
                None,
            )
            if source_ref is not None:
                self._verify_coord_ref(source_ref, "B2_EVIDENCE_REPORT")
                before = state.get("source_ref")
                self._record_evidence(state, source_ref)
                if before != state.get("source_ref"):
                    changed = True

        for stage, filename, kind, suffix in (
            ("M4", "research_m4_execution.json", "ResearchM4ExecutionManifest", ":M4"),
            ("M5", "research_m5_execution.json", "ResearchM5ExecutionManifest", ":M5"),
        ):
            path = b3_root / filename
            if not path.is_file():
                continue
            manifest = _read(path)
            expected_type = f"RESEARCH_{stage}_EXECUTION"
            if manifest.get("manifest_type") != expected_type:
                raise ResearchM7Error(f"M7_RECOVERY_{stage}_MANIFEST_INVALID")
            if stage not in artifacts:
                plan_id = str(_read(b2_root / "research_plan.json").get("research_plan_id") or "")
                ref = self._coord_ref(
                    path,
                    artifact_id=f"{plan_id}{suffix}",
                    artifact_kind=kind,
                    artifact_version=str(manifest.get("manifest_version") or M7_VERSION),
                )
                self._store_coord(state, stage, ref, kind=kind)
                artifacts[stage] = state["artifacts"][-1]
                changed = True
            else:
                self._verify_coord_ref(artifacts[stage], stage)
            manifest_refs = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else manifest.get("m5_outputs", [])
            evidence_ref = next(
                (dict(item) for item in manifest_refs
                 if item.get("artifact_kind") == "SourceAccessAndEvidenceReport"),
                None,
            )
            if evidence_ref is not None:
                self._verify_coord_ref(evidence_ref, f"{stage}_EVIDENCE_REPORT")
                self._record_evidence(state, evidence_ref)
                changed = True

        if changed:
            completed = list(state.get("completed_stages", []))
            for stage in ("INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"):
                if stage in artifacts and stage not in completed:
                    completed.append(stage)
            state["completed_stages"] = [stage for stage in STAGES if stage in completed]
            state.update({"status": "INTERRUPTED", "updated_at": _now()})
            self.store.save(state)

    def _mark_handoff_stale(self, state: dict[str, Any], reason: str) -> None:
        ref = next((item for item in state.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF"), None)
        if ref is None:
            return
        payload = _read(ref["path"])
        payload.update({"handoff_state": "STALE", "stale_reason": reason, "validation": {**payload.get("validation", {}), "status": "STALE", "cognition_executed": False}})
        _write_json_atomic(Path(ref["path"]), payload)
        ref["checksum"] = hashlib.sha256(Path(ref["path"]).read_bytes()).hexdigest()

    def assert_handoff_consumable(self, state: Mapping[str, Any] | None = None) -> None:
        current = dict(state) if state is not None else self.store.load()
        if current.get("stale_handoff") or current.get("invalidated_stages"):
            raise ResearchM7Error("B5_I3_HANDOFF_STALE_OR_INVALIDATED")
        ref = next((item for item in current.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF"), None)
        if ref is None:
            raise ResearchM7Error("B5_I3_HANDOFF_MISSING")
        payload = _read(ref["path"])
        if payload.get("handoff_state") != "VALID" or payload.get("validation", {}).get("status") != "PASS":
            raise ResearchM7Error("B5_I3_HANDOFF_NOT_CONSUMABLE")

    def _resume_m6_and_handoff(self, state: dict[str, Any]) -> dict[str, Any]:
        b2 = self._b2_result_from_state(state)
        baseline = self._baseline(b2)
        m4_ref = next(item for item in state["artifacts"] if item["stage"] == "M4")
        m5_ref = next(item for item in state["artifacts"] if item["stage"] == "M5")
        m4 = self._m4_result(m4_ref)
        m5 = self._m5_result_from_state(state)
        executor = SyntheticResearchExecutor(state["human_input"])
        executor.research_id = str(baseline["research_plan"]["research_plan_id"])
        chain, provenance = self._provenance(state, b2, m4, m5)
        context = self._context(state)
        context.update(provenance)
        execution_root = self.root / f"canonical_g{state.get('generation', 1)}"
        m6_persistence = ResearchB4Persistence(execution_root / "b3")
        manifest_path = execution_root / "b3" / "research_ready_manifest_m6.json"
        gate_path = execution_root / "b3" / "research_ready_gate.json"
        if manifest_path.is_file() and gate_path.is_file():
            manifest = _read(manifest_path)
            gate = _read(gate_path)
            manifest_errors = validate_research_ready_manifest(manifest)
            if manifest_errors:
                raise ResearchM7Error("M7_RECOVERY_M6_MANIFEST_INVALID:" + " | ".join(manifest_errors))
            try:
                validate_gate_result(GateResult.from_dict(gate))
            except (KeyError, TypeError, ValueError) as exc:
                raise ResearchM7Error("M7_RECOVERY_M6_GATE_INVALID") from exc
            m6 = {
                "status": manifest.get("research_ready_state"),
                "research_ready_manifest": {"artifact_id": manifest["manifest_id"], "artifact_kind": "ResearchReadyManifest", "artifact_version": str(manifest.get("research_version", M7_VERSION)), "path": str(manifest_path), "checksum": _checksum(manifest)},
                "research_ready_gate": {"artifact_id": f"{m5['execution_manifest']['artifact_id']}:M6:RESEARCH_READY_GATE", "artifact_kind": "GateResult", "artifact_version": M7_VERSION, "path": str(gate_path), "checksum": _checksum(gate)},
            }
        else:
            m6 = ResearchB4Orchestrator(executor, m6_persistence, _test_provenance_repository_root=Path(provenance["repository_root"])).run_m6(m5, context=context, research_chain=chain, invalidation_engine=self.invalidation)
            manifest = _read(m6["research_ready_manifest"]["path"])
        self._store_coord(state, "M6", m6["research_ready_manifest"], kind="ResearchReadyManifest")
        state["canonical_refs"]["M6Gate"] = [m6["research_ready_gate"]]
        state["canonical_invocations"] = {**state.get("canonical_invocations", {}), "M6": "ResearchB4Orchestrator.run_m6"}
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6"]
        self.store.save(state)
        handoff = self._validate_consumer(state, manifest, baseline, m4, m5)
        handoff_path = execution_root / "b5_i3_handoff.json"
        _write_json_atomic(handoff_path, handoff)
        self._store_coord(state, "B5_I3_HANDOFF", {"artifact_id": f"{manifest['manifest_id']}:B5_I3", "artifact_kind": "ResearchV2B5I3Handoff", "artifact_version": M7_VERSION, "path": str(handoff_path), "checksum": hashlib.sha256(handoff_path.read_bytes()).hexdigest()}, kind="ResearchV2B5I3Handoff")
        state["completed_stages"] = list(STAGES)
        state.update({"status": "COMPLETED", "next_stage": None, "m7_status": "READY_FOR_OWNER_REVIEW", "research_vertical_e2e": "PASS", "invalidated_stages": [], "stale_handoff": False, "updated_at": _now()})
        self._bind_dependencies(state)
        self.store.save(state)
        return state

    def _bind_dependencies(self, state: dict[str, Any]) -> None:
        by_stage = {item["stage"]: item for item in state.get("artifacts", [])}
        for parent, children in (("B2", ["M4", "M5", "M6", "B5_I3_HANDOFF"]), ("M4", ["M5", "M6", "B5_I3_HANDOFF"]), ("M5", ["M6", "B5_I3_HANDOFF"]), ("M6", ["B5_I3_HANDOFF"])):
            if parent not in by_stage:
                continue
            for child in children:
                if child in by_stage:
                    self.invalidation.register_dependency(by_stage[parent]["artifact_id"], by_stage[child]["artifact_id"])
        state["dependency_graph"] = {key: sorted(value) for key, value in self.invalidation.dependencies.items()}

    def _execute_from_stage(self, state: dict[str, Any], start_stage: str) -> dict[str, Any]:
        """Reopen one invalidated stage and only its downstream dependents."""
        if start_stage not in {"M4", "M5", "M6"}:
            raise ResearchM7Error("M7_FOCAL_START_STAGE_INVALID")
        inp = state["human_input"]
        execution_root = self.root / f"canonical_g{state.get('generation', 1)}"
        executor = SyntheticResearchExecutor(copy.deepcopy(inp))
        adapter = self._adapter(state)
        context = self._context(state)
        b2 = self._b2_result_from_state(state)
        context["evidence_report"] = _read(b2["evidence_report"]["path"])
        context["_evidence_report_ref"] = dict(b2["evidence_report"])
        baseline = self._baseline(b2)
        plan = _read(b2["research_plan"]["path"])
        executor.research_id = str(plan["research_plan_id"])
        m4 = self._m4_result(next(item for item in state["artifacts"] if item["stage"] == "M4")) if start_stage != "M4" else None
        if start_stage == "M4":
            selected = list(inp["selected_work_ids"])
            if self.selection_mode == "DELEGATED" and inp.get("replace_work_id") and inp.get("substitute_work_id"):
                selected = [work_id for work_id in selected if work_id != inp["replace_work_id"]] + [str(inp["substitute_work_id"])]
            if self.selection_mode == "DELEGATED" and not set(selected).issubset(set(self.delegated_scope)):
                raise ResearchM7Error("M7_DELEGATED_SELECTION_SCOPE_INVALID")
            executor.input["_effective_selected_work_ids"] = list(selected)
            executor.input["selection_mode"] = self.selection_mode
            selection_mode = "DELEGATED_SELECTION" if self.selection_mode == "DELEGATED" else "USER_SELECTION"
            human = HumanDecision(request_id=f"{plan['research_plan_id']}:M4:SELECTION_REQUEST", action="APPROVE", actor_ref="OWNER", channel="TERMINAL") if selection_mode == "USER_SELECTION" else None
            delegation = {"decision": "DELEGATE", "reasons": ["scope explícito"], "policy_version": "1.0.0", "evidence_refs": [f"D-{work_id}" for work_id in selected], "authorized_candidate_set": selected} if selection_mode == "DELEGATED_SELECTION" else None
            m4 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter, no_progress_guard=ResearchB2NoProgressGuard(max_iterations=self.max_iterations)).run(baseline, context=context, selection_mode=selection_mode, human_decision=human, delegation_decision=delegation, selection_options=[selected])
            state.setdefault("canonical_invocations", {}).update({"M4": "ResearchB3Orchestrator.run"})
            self._record_evidence(state, m4["evidence_report"])
            self._store_coord(state, "M4", m4["execution_manifest"], kind="ResearchM4ExecutionManifest")
            context["evidence_report"] = _read(m4["evidence_report"]["path"])
            context["_evidence_report_ref"] = dict(m4["evidence_report"])
            state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4"]
            self.store.save(state)
        m5 = self._m5_result_from_state(state) if start_stage == "M6" else None
        if start_stage in {"M4", "M5"}:
            if start_stage == "M5":
                context["evidence_report"] = _read(m4["evidence_report"]["path"])
                context["_evidence_report_ref"] = dict(m4["evidence_report"])
            executor.input["_effective_selected_work_ids"] = list(_read(m4["execution_manifest"]["path"])["selection"]["selected_work_ids"])
            executor.input["selection_mode"] = self.selection_mode
            m5 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter, no_progress_guard=ResearchB2NoProgressGuard(max_iterations=self.max_iterations)).run_m5(baseline, m4, context=context)
            state.setdefault("canonical_invocations", {}).update({"M5": "ResearchB3Orchestrator.run_m5"})
            self._record_evidence(state, m5["evidence_report"])
            self._store_coord(state, "M5", m5["execution_manifest"], kind="ResearchM5ExecutionManifest")
            context["evidence_report"] = _read(m5["evidence_report"]["path"])
            context["_evidence_report_ref"] = dict(m5["evidence_report"])
            state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"]
            self.store.save(state)
        assert m5 is not None
        chain, provenance = self._provenance(state, b2, m4, m5)
        context.update(provenance)
        m6 = ResearchB4Orchestrator(executor, ResearchB4Persistence(execution_root / "b3"), _test_provenance_repository_root=Path(provenance["repository_root"])).run_m6(m5, context=context, research_chain=chain, invalidation_engine=self.invalidation)
        state.setdefault("canonical_invocations", {}).update({"M6": "ResearchB4Orchestrator.run_m6"})
        manifest = _read(m6["research_ready_manifest"]["path"])
        self._store_coord(state, "M6", m6["research_ready_manifest"], kind="ResearchReadyManifest")
        state["canonical_refs"]["M6Gate"] = [m6["research_ready_gate"]]
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6"]
        self.store.save(state)
        handoff = self._validate_consumer(state, manifest, baseline, m4, m5)
        handoff_path = execution_root / "b5_i3_handoff.json"
        _write_json_atomic(handoff_path, handoff)
        self._store_coord(state, "B5_I3_HANDOFF", {"artifact_id": f"{manifest['manifest_id']}:B5_I3", "artifact_kind": "ResearchV2B5I3Handoff", "artifact_version": M7_VERSION, "path": str(handoff_path), "checksum": hashlib.sha256(handoff_path.read_bytes()).hexdigest()}, kind="ResearchV2B5I3Handoff")
        state["completed_stages"] = list(STAGES)
        state.update({"status": "COMPLETED", "next_stage": None, "m7_status": "READY_FOR_OWNER_REVIEW", "research_vertical_e2e": "PASS", "invalidated_stages": [], "stale_handoff": False, "updated_at": _now()})
        self._bind_dependencies(state)
        self.store.save(state)
        return state

    def _execute(self, state: dict[str, Any], *, stop_after_stage: str | None = None, simulate_no_progress: bool = False) -> dict[str, Any]:
        self._materialize_recovery(state)
        inp = state["human_input"]
        execution_root = self.root / f"canonical_g{state.get('generation', 1)}"
        executor = SyntheticResearchExecutor(copy.deepcopy(inp))
        adapter = self._adapter(state)
        context = self._context(state)
        if simulate_no_progress:
            guard = ResearchB2NoProgressGuard(max_iterations=self.max_iterations)
            guard.observe(gap="M7:synthetic-iteration", evidence_refs=["recovery:S1"], state="OPEN", result={"status": "UNCHANGED"})
            observation = guard.observe(gap="M7:synthetic-iteration", evidence_refs=["recovery:S1"], state="OPEN", result={"status": "UNCHANGED"})
            state["iteration_guard"] = guard.to_dict()
            if observation.status != "NO_PROGRESS":
                raise ResearchM7Error("M7_NO_PROGRESS_PROBE_DID_NOT_STOP")
            state.update({"status": "BLOCKED_NO_PROGRESS", "no_progress_terminal": "NO_PROGRESS / ITERATION_GUARD", "updated_at": _now()})
            self.store.save(state)
            raise ResearchM7Error("NO_PROGRESS / ITERATION_GUARD")
        intake_path = execution_root / "editorial_intake.json"
        intake = {
            "contract": "plan012_m7_synthetic_intake",
            "contract_version": "1.0.0",
            "episode_id": str(inp["episode_id"]),
            "topic": str(inp["topic"]),
            "question": str(inp["initial_question"]),
            "works": list(inp["works"]),
            "profile_binding": {"profile_id": "M7-SYNTHETIC", "profile_version": "1.0.0", "profile_checksum": "synthetic"},
            "editorial_decisions_made": False,
        }
        _write_json_atomic(intake_path, intake)
        self._store_coord(state, "INTAKE", {"artifact_id": f"intake:{inp['episode_id']}", "artifact_kind": "EditorialIntakeHandoff", "artifact_version": "1.0.0", "path": str(intake_path), "checksum": hashlib.sha256(intake_path.read_bytes()).hexdigest()}, kind="EditorialIntakeHandoff")
        state["completed_stages"] = ["INTAKE"]
        self.store.save(state)
        planning = ResearchPlanningService()
        profile = _read(Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json")
        work_intents = [{"work_ref": str(work_id), "editorial_intent": "NO_DECLARADA"} for work_id in inp["works"]]
        brief = planning.build_episode_brief(
            episode_id=str(inp["episode_id"]), topic=str(inp["topic"]),
            question=str(inp["initial_question"]), intended_use="RESEARCH_AND_THESIS",
            profile=profile, work_intents=work_intents,
            selection_authority="OWNER_DECIDES" if self.selection_mode == "MANUAL" else "DELEGATED_TO_RESEARCH",
            brief_version="1.0.0", origin_ref=f"human-input:{inp['episode_id']}",
        )
        channel_context = planning.build_channel_context(
            episode_id=str(inp["episode_id"]), profile=profile,
            origin_ref=f"human-input:{inp['episode_id']}",
        )
        plan_result = planning.produce_research_plan(
            episode_brief=brief, channel_context=channel_context,
            source_access=context["source_access"], cognitive_executor=executor,
            persistence=ResearchB2Persistence(execution_root / "b2"),
            research_role="NORMAL", editorial_intent="NO_DECLARADA",
            persist_plan=False,
        )
        plan = plan_result["research_plan_payload"]
        executor.research_id = str(plan["research_plan_id"])
        state.setdefault("canonical_refs", {})["ResearchPlanProposal"] = [plan_result["research_plan_proposal"]]
        if validate_research_plan(plan):
            raise ResearchM7Error("M7_RESEARCH_PLAN_INVALID")
        context["brief"] = brief
        context["channel_context"] = channel_context
        b2 = ResearchB2Orchestrator(executor, ResearchB2Persistence(execution_root / "b2"), acquisition_adapter=adapter, no_progress_guard=ResearchB2NoProgressGuard(max_iterations=self.max_iterations)).run(plan, context=context)
        state["canonical_invocations"] = {"B2": "ResearchB2Orchestrator.run"}
        state["source_ref"] = dict(b2["evidence_report"])
        state["evidence_refs"] = [dict(b2["evidence_report"])]
        context["evidence_report"] = _read(b2["evidence_report"]["path"])
        context["_evidence_report_ref"] = dict(b2["evidence_report"])
        b2_manifest = _read(b2["execution_manifest"]["path"])
        self._store_coord(state, "RESEARCH_PLAN", b2["research_plan"], kind="ResearchPlan")
        self._store_coord(state, "B2", b2["execution_manifest"], kind="ResearchB2ExecutionManifest")
        state["canonical_refs"]["ResearchPack"] = [ref for ref in b2_manifest["artifacts"] if ref["artifact_kind"] == "ResearchPack"]
        state["canonical_refs"]["SourceAccessAndEvidenceReport"] = [state["source_ref"]]
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2"]
        self.store.save(state)
        if stop_after_stage == "B2":
            state.update({"status": "INTERRUPTED", "next_stage": "M4", "updated_at": _now()})
            self.store.save(state)
            return state
        selected = list(inp["selected_work_ids"])
        if self.selection_mode == "DELEGATED" and inp.get("replace_work_id") and inp.get("substitute_work_id"):
            selected = [work_id for work_id in selected if work_id != inp["replace_work_id"]] + [str(inp["substitute_work_id"])]
        if self.selection_mode == "DELEGATED" and not set(selected).issubset(set(self.delegated_scope)):
            raise ResearchM7Error("M7_DELEGATED_SELECTION_SCOPE_INVALID")
        executor.input["_effective_selected_work_ids"] = list(selected)
        executor.input["selection_mode"] = self.selection_mode
        selection_mode = "DELEGATED_SELECTION" if self.selection_mode == "DELEGATED" else "USER_SELECTION"
        human = HumanDecision(request_id=f"{plan['research_plan_id']}:M4:SELECTION_REQUEST", action="APPROVE", actor_ref="OWNER", channel="TERMINAL") if selection_mode == "USER_SELECTION" else None
        delegation = {"decision": "DELEGATE", "reasons": ["scope explícito"], "policy_version": "1.0.0", "evidence_refs": [f"D-{work_id}" for work_id in selected], "authorized_candidate_set": selected} if selection_mode == "DELEGATED_SELECTION" else None
        baseline = self._baseline(b2)
        m4 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter, no_progress_guard=ResearchB2NoProgressGuard(max_iterations=self.max_iterations)).run(baseline, context=context, selection_mode=selection_mode, human_decision=human, delegation_decision=delegation, selection_options=[selected])
        state.setdefault("canonical_invocations", {}).update({"M4": "ResearchB3Orchestrator.run"})
        state["source_ref"] = dict(m4["evidence_report"])
        state["evidence_refs"].append(dict(m4["evidence_report"]))
        context["evidence_report"] = _read(m4["evidence_report"]["path"])
        context["_evidence_report_ref"] = dict(m4["evidence_report"])
        self._store_coord(state, "M4", m4["execution_manifest"], kind="ResearchM4ExecutionManifest")
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4"]
        self.store.save(state)
        if stop_after_stage == "M4":
            state.update({"status": "INTERRUPTED", "next_stage": "M5", "updated_at": _now()})
            self.store.save(state)
            return state
        if inp.get("deep_stop_status") == "MORE_RESEARCH_REQUIRED" and not inp.get("_research_stop_reopened"):
            state.update({"status": "INTERRUPTED", "next_stage": "M4", "research_stop_route": "REOPEN_FOCAL", "updated_at": _now()})
            self.store.save(state)
            return state
        m5 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter, no_progress_guard=ResearchB2NoProgressGuard(max_iterations=self.max_iterations)).run_m5(baseline, m4, context=context)
        state.setdefault("canonical_invocations", {}).update({"M5": "ResearchB3Orchestrator.run_m5"})
        state["source_ref"] = dict(m5["evidence_report"])
        state["evidence_refs"].append(dict(m5["evidence_report"]))
        context["evidence_report"] = _read(m5["evidence_report"]["path"])
        context["_evidence_report_ref"] = dict(m5["evidence_report"])
        self._store_coord(state, "M5", m5["execution_manifest"], kind="ResearchM5ExecutionManifest")
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"]
        self.store.save(state)
        if stop_after_stage == "M5":
            state.update({"status": "INTERRUPTED", "next_stage": "M6", "updated_at": _now()})
            self.store.save(state)
            return state
        chain, provenance = self._provenance(state, b2, m4, m5)
        context.update(provenance)
        m6 = ResearchB4Orchestrator(executor, ResearchB4Persistence(execution_root / "b3"), _test_provenance_repository_root=Path(provenance["repository_root"])).run_m6(m5, context=context, research_chain=chain, invalidation_engine=self.invalidation)
        state.setdefault("canonical_invocations", {}).update({"M6": "ResearchB4Orchestrator.run_m6"})
        manifest = _read(m6["research_ready_manifest"]["path"])
        self._store_coord(state, "M6", m6["research_ready_manifest"], kind="ResearchReadyManifest")
        state["canonical_refs"]["M6Gate"] = [m6["research_ready_gate"]]
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6"]
        self.store.save(state)
        handoff = self._validate_consumer(state, manifest, baseline, m4, m5)
        handoff_path = execution_root / "b5_i3_handoff.json"
        _write_json_atomic(handoff_path, handoff)
        self._store_coord(state, "B5_I3_HANDOFF", {"artifact_id": f"{manifest['manifest_id']}:B5_I3", "artifact_kind": "ResearchV2B5I3Handoff", "artifact_version": M7_VERSION, "path": str(handoff_path), "checksum": hashlib.sha256(handoff_path.read_bytes()).hexdigest()}, kind="ResearchV2B5I3Handoff")
        state["completed_stages"] = list(STAGES)
        state.update({"status": "COMPLETED", "next_stage": None, "m7_status": "READY_FOR_OWNER_REVIEW", "research_vertical_e2e": "PASS", "invalidated_stages": [], "stale_handoff": False, "updated_at": _now()})
        self._bind_dependencies(state)
        self.store.save(state)
        return state

    def run(self, human_input: Mapping[str, Any] | None = None, *, resume: bool = False, stop_after_stage: str | None = None, simulate_no_progress: bool = False) -> dict[str, Any]:
        if resume:
            return self.resume(human_input=human_input)
        state = self._state(human_input, resume)
        if state.get("status") == "COMPLETED":
            return state
        if stop_after_stage not in {None, "INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"}:
            raise ResearchM7Error("M7_STOP_STAGE_INVALID")
        if stop_after_stage in {"INTAKE", "RESEARCH_PLAN"}:
            raise ResearchM7Error("M7_STOP_STAGE_NOT_IMPLEMENTED_AT_CANONICAL_BOUNDARY")
        return self._execute(state, stop_after_stage=stop_after_stage, simulate_no_progress=simulate_no_progress)

    def resume(self, human_input: Mapping[str, Any] | None = None) -> dict[str, Any]:
        state = self._state(human_input, True)
        if state.get("status") == "COMPLETED":
            return state
        self._reconcile_persisted_stages(state)
        if state.get("completed_stages", [])[-1:] == ["M5"]:
            return self._resume_m6_and_handoff(state)
        if state.get("completed_stages", [])[-1:] == ["M4"]:
            return self._execute_from_stage(state, "M5")
        if state.get("completed_stages", [])[-1:] == ["B2"]:
            return self._execute_from_stage(state, "M4")
        if state.get("invalidated_stages"):
            start_stage = next((stage for stage in STAGES if stage in set(state["invalidated_stages"])), None)
            if start_stage == "B2":
                return self._execute(state)
            if start_stage in {"M4", "M5", "M6"}:
                return self._execute_from_stage(state, start_stage)
            raise ResearchM7Error("M7_FOCAL_RESUME_STAGE_UNKNOWN")
        raise ResearchM7Error("M7_RESUME_REQUIRES_LAST_CANONICAL_STAGE")

    def invalidate(self, stage: str) -> dict[str, Any]:
        state = self.store.load()
        if stage not in STAGES[2:]:
            raise ResearchM7Error("M7_INVALIDATION_STAGE_INVALID")
        self._bind_dependencies(state)
        target = next(item for item in state["artifacts"] if item["stage"] == stage)
        self.invalidation.invalidate_artifact(target["artifact_id"], target["artifact_version"], f"M7 focal invalidation {stage}", "PLAN012_M7")
        affected = {entry.target_artifact_id for entry in self.invalidation.invalidation_log}
        state["invalidated_stages"] = [item["stage"] for item in state["artifacts"] if item["artifact_id"] in affected]
        state["generation"] = int(state.get("generation", 1)) + 1
        self._mark_handoff_stale(state, f"M7 focal invalidation {stage}")
        state.update({"status": "IN_PROGRESS", "next_stage": stage, "research_vertical_e2e": "NOT_DEMONSTRATED", "stale_handoff": "B5_I3_HANDOFF" in state["invalidated_stages"], "updated_at": _now()})
        self.store.save(state)
        return state

    def reopen_focal(self, dependency_artifact_id: str) -> dict[str, Any]:
        state = self.store.load()
        stages = {item["artifact_id"]: item["stage"] for item in state["artifacts"]}
        if dependency_artifact_id not in stages:
            raise ResearchM7Error("M7_REOPEN_DEPENDENCY_UNKNOWN")
        result = self.invalidate(stages[dependency_artifact_id])
        if result.get("human_input", {}).get("deep_stop_status") == "MORE_RESEARCH_REQUIRED":
            recovery_dir = self.root / f"recovery_g{result.get('generation', 1)}"
            recovery_dir.mkdir(parents=True, exist_ok=True)
            evidence_path = recovery_dir / "focal_research_evidence.json"
            evidence = {
                "evidence_id": f"{result['run_id']}:FOCAL:NEW-EVIDENCE",
                "episode_id": result["human_input"]["episode_id"],
                "source_id": "S1",
                "content": "Fixture adicional materializado para reabrir ResearchStop.",
                "synthetic": True,
                "materialization": "SOFTWARE_CONTROLLED_RECOVERY",
            }
            _write_json_atomic(evidence_path, evidence)
            evidence_ref = {
                "artifact_id": f"recovery:{evidence['evidence_id']}",
                "artifact_kind": "RecoveredFocalResearchEvidence",
                "artifact_version": "1.0.0",
                "path": str(evidence_path),
                "checksum": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            }
            result.setdefault("recovery_artifacts", []).append(evidence_ref)
            result["human_input"]["_research_stop_new_evidence_ref"] = evidence_ref
            result["research_stop_route"] = "REOPENED_PENDING_NEW_COGNITION"
            self.store.save(result)
        return result

    def assert_software_boundaries(self, state: Mapping[str, Any]) -> None:
        if state.get("real_ai_execution") is not False or state.get("product_use_authorized") is not False or state.get("p2_real_execution") is not False:
            raise ResearchM7Error("M7_PROHIBITED_EXECUTION_STATE")
        handoff = next((item for item in state.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF"), None)
        if handoff and any(key in _read(handoff["path"]) for key in NARRATIVE_FIELDS):
            raise ResearchM7Error("M7_NARRATIVE_OUTPUT_PRESENT")
