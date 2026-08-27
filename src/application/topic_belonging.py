"""Controlled Topic Belonging vertical between intake and the episode stop gate."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import hashlib
import json
import re
from pathlib import Path
import tempfile
from typing import Any, Protocol
from uuid import uuid4

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute
from src.ai.manifest import file_checksum, manifest_checksum
from src.ai.role_execution import RoleExecutionContractError, build_model_prompt, resolve_role_execution_contract
from src.ai.runtime_profiles import load_execution_profiles
from src.application.contracts import HumanInput
from src.application.storage import EpisodeHandle, StorageError, VaultEpisodeStore
from src.application.authority import load_operational_authority
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.contract_validation import validate_against_schema
from src.core.execution_preflight import preflight_controlled_execution
from src.core.path_resolution import REPO_ROOT
from src.core.prompt_resolver import resolve_prompt
from src.scripts.channel_intelligence import (
    canonical_checksum,
    validate_assessment,
    validate_decision,
    validate_topic_input,
)
from src.scripts.topic_belonging_flow import evaluate_topic_belonging_gate


CAPABILITY_ID = "TOPIC_BELONGING_ASSESSMENT"
PRODUCER_ROLE = "CHANNEL_INTELLIGENCE_PRODUCER"
REVIEWER_ROLE = "CHANNEL_INTELLIGENCE_REVIEWER"
LEGACY_M1_LINEAGE_ID = "PLAN010_M1_TOPIC_BELONGING_INTEGRATION_CLOSURE"
EPISODE_ORIGIN_FIELDS = frozenset(
    {
        "episode_id",
        "origin",
        "state_anchor_sha256",
        "index_anchor_sha256",
        "origin_checksum",
    }
)
PROMPT_ROLES = {
    "enrich": PRODUCER_ROLE,
    "produce": PRODUCER_ROLE,
    "review": REVIEWER_ROLE,
}

# The six artifacts persisted atomically by VaultEpisodeStore.record_topic_belonging_vertical.
VERTICAL_ARTIFACTS = (
    "02_topic_belonging_input.json",
    "03_topic_belonging_assessment.json",
    "04_topic_belonging_decision.json",
    "05_topic_belonging_gate.json",
    "topic_belonging_lineage.json",
    "topic_belonging_execution.json",
)
M1_ALLOWED_EPISODE_ARTIFACTS = frozenset(
    {
        "00_human_input.json",
        "01_editorial_intake_handoff.json",
        *VERTICAL_ARTIFACTS,
        "episode_origin.json",
        "episode_state.json",
        "workflow_state.json",
    }
)

STOP_STATUS = "TOPIC_BELONGING_TECHNICAL_STOP"


def _prompt_contract_for_stage(stage: str) -> dict[str, Any]:
    return resolve_prompt(PROMPT_ROLES[stage])


class TopicBelongingExecutionError(PermissionError):
    """A cognitive boundary execution did not produce a contractual output."""


class CognitiveBoundary(Protocol):
    def preflight(self) -> str: ...

    def enrich(self, handoff: dict[str, Any], human_input: HumanInput, profile: dict[str, Any], episode_id: str) -> tuple[dict[str, Any], ExecutionResult]: ...

    def produce(self, topic_input: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "") -> tuple[dict[str, Any], ExecutionResult]: ...

    def review(self, topic_input: dict[str, Any], assessment: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "") -> tuple[dict[str, Any], ExecutionResult]: ...


def _json_checksum(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _expected_raw_output_checksum(
    stage: str,
    topic_input: dict[str, Any],
    assessment: dict[str, Any],
    decision: dict[str, Any],
) -> str:
    """Reconstruct the synthetic runtime payload before provenance normalization."""
    if stage == "ENRICHMENT":
        return _json_checksum(topic_input)
    if stage == "PRODUCER":
        raw = copy.deepcopy(assessment)
        base = copy.deepcopy(raw)
        base.pop("producer_run_id", None)
        base.setdefault("provenance", {}).pop("run_id", None)
        checksum = canonical_checksum(base, "assessment")
        provenance = raw.setdefault("provenance", {})
        raw["artifact_checksum"] = checksum
        provenance["output_checksum"] = checksum
        return _json_checksum(raw)
    raw = copy.deepcopy(decision)
    provenance = raw.setdefault("provenance", {})
    raw_assessment = copy.deepcopy(assessment)
    raw_assessment.pop("producer_run_id", None)
    raw_assessment.setdefault("provenance", {}).pop("run_id", None)
    raw_assessment_checksum = canonical_checksum(raw_assessment, "assessment")
    base = copy.deepcopy(raw)
    base["producer_artifact_checksum"] = raw_assessment_checksum
    base["reviewer_input_checksum"] = raw_assessment_checksum
    base.setdefault("provenance", {})["input_checksum"] = raw_assessment_checksum
    base.pop("reviewer_run_id", None)
    base.setdefault("provenance", {}).pop("run_id", None)
    provenance["output_checksum"] = canonical_checksum(base, "decision")
    return _json_checksum(raw)


def _expected_input_manifest_checksum(
    episode_id: str,
    stage: str,
    handoff: dict[str, Any],
    topic_input: dict[str, Any],
    assessment: dict[str, Any],
) -> str:
    """Rebuild the runtime manifest from the persisted stage inputs."""
    stage_inputs = {
        "ENRICHMENT": [
            ("editorial_intake_handoff", handoff["source_interaction_id"], handoff),
        ],
        "PRODUCER": [
            ("topic_belonging_input", topic_input["topic_input_id"], topic_input),
        ],
        "REVIEWER": [
            ("topic_belonging_input", topic_input["topic_input_id"], topic_input),
            ("topic_belonging_assessment", assessment["assessment_id"], assessment),
        ],
    }[stage]
    with tempfile.TemporaryDirectory(prefix="topic-belonging-manifest-") as temp_dir:
        artifacts: list[dict[str, Any]] = []
        for index, (kind, artifact_id, payload) in enumerate(stage_inputs):
            path = Path(temp_dir) / f"{index}-{kind}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            artifacts.append(
                {
                    "artifact_kind": kind,
                    "artifact_id": artifact_id,
                    "artifact_checksum": file_checksum(path),
                }
            )
        return manifest_checksum(episode_id, artifacts)


def _validate_enrichment_binding(topic_input: dict[str, Any], handoff: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    bindings = handoff.get("field_bindings", {})
    for input_key, handoff_key in (
        ("topic", "topic"),
        ("central_question", "central_question"),
        ("narrative_work", "narrative_work"),
        ("corpus_ref", "corpus_ref"),
        ("candidate_work_refs", "candidate_work_refs"),
    ):
        supplied = bindings.get(handoff_key)
        if supplied not in (None, "", []) and topic_input.get(input_key) != supplied:
            violations.append(f"ENRICHMENT_{input_key.upper()}_MISMATCH")
    if topic_input.get("entry_mode") != handoff.get("entry_mode"):
        violations.append("ENRICHMENT_ENTRY_MODE_MISMATCH")
    profile = handoff.get("profile_binding", {})
    for key in ("profile_id", "profile_version", "profile_checksum"):
        if topic_input.get(key) != profile.get(key):
            violations.append(f"ENRICHMENT_{key.upper()}_MISMATCH")
    return violations


def _validate_human_handoff_binding(human_input: dict[str, Any], handoff: dict[str, Any]) -> list[str]:
    """Verify that the persisted intake remains the source of its handoff."""
    violations: list[str] = []
    if human_input.get("interaction_id") != handoff.get("source_interaction_id"):
        violations.append("HUMAN_INPUT_INTERACTION_ID_MISMATCH")
    if human_input.get("channel") != handoff.get("source_channel"):
        violations.append("HUMAN_INPUT_CHANNEL_MISMATCH")
    if human_input.get("mode") != handoff.get("entry_mode"):
        violations.append("HUMAN_INPUT_MODE_MISMATCH")

    bindings = handoff.get("field_bindings", {})
    mode = human_input.get("mode")
    expected_content_key = {
        "TOPIC_FIRST": "topic",
        "ANCHOR_WORK_FIRST": "narrative_work",
        "CORPUS_FIRST": "corpus_ref",
    }.get(mode)
    if expected_content_key == "corpus_ref":
        expected_content = f"human-input:{human_input.get('interaction_id')}"
    elif expected_content_key:
        expected_content = human_input.get("content")
    else:
        expected_content = None
    if expected_content is not None and bindings.get(expected_content_key) != expected_content:
        violations.append(f"HUMAN_INPUT_{expected_content_key.upper()}_MISMATCH")
    for human_key, handoff_key in (
        ("initial_question", "central_question"),
        ("initial_question", "initial_question"),
        ("context", "context"),
        ("works", "candidate_work_refs"),
    ):
        if human_input.get(human_key) != bindings.get(handoff_key):
            violations.append(f"HUMAN_INPUT_{handoff_key.upper()}_MISMATCH")
    return violations


@dataclass
class ExecutionCognitiveBoundary:
    """Use the shared execution runtime; ``mock_outputs`` is test-only injection."""

    repository_root: Path = REPO_ROOT
    mission_authorization_path: str | None = None
    execution_mode: str = "REAL"
    execution_interface: str = "TOPIC_BELONGING_TERMINAL"
    mock_outputs: dict[str, dict[str, Any]] | None = None
    execution_route: str | None = None
    execution_profile: str | None = None
    model_override: str | None = None
    reasoning_effort: str | None = None
    paid_cost_approved: bool = False
    execution_registry_path: str | None = None
    operational_authority_path: str | None = None
    resolved_mission_id: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.mock_outputs is not None and self.execution_mode != "SYNTHETIC_TEST":
            raise PermissionError("MOCK_OUTPUTS_REQUIRE_SYNTHETIC_TEST_MODE")
        if self.execution_mode == "SYNTHETIC_TEST" and self.execution_profile is None:
            self.execution_profile = "ollama_local"
        if self.execution_mode == "SYNTHETIC_TEST" and self.execution_route is None:
            self.execution_route = "local_model"

    def _resolve_profile_route(self) -> None:
        """Bind the route declared by an explicitly selected profile only.

        A profile is an owner selection, not a global/default provider.  The
        route is a structural property of that selected profile and is needed
        for MissionAuthorization scope checks before the shared runtime runs.
        """
        if not self.execution_profile:
            return
        profiles_path = self.repository_root / "config" / "agent_execution_profiles.json"
        try:
            profiles = load_execution_profiles(profiles_path)
            profile = profiles.get("execution_profiles", {}).get(self.execution_profile)
            profile_route = str(profile.get("execution_route") or "").strip() if isinstance(profile, dict) else ""
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise PermissionError("EXECUTION_PROFILES_UNAVAILABLE") from exc
        if not profile_route:
            raise PermissionError(f"EXECUTION_PROFILE_INVALID:{self.execution_profile}")
        if self.execution_route is None:
            self.execution_route = profile_route

    def preflight(self) -> str:
        if not self.mission_authorization_path:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED:TOPIC_BELONGING_ASSESSMENT")
        if self.execution_mode == "REAL" and not self.execution_profile:
            raise PermissionError("REAL_EXECUTION_PROFILE_REQUIRED")
        self._resolve_profile_route()
        if self.execution_mode == "SYNTHETIC_TEST" and (
            self.mock_outputs is None or any(
                stage not in self.mock_outputs or not isinstance(self.mock_outputs.get(stage), dict)
                for stage in ("enrich", "produce", "review")
            )
        ):
            raise PermissionError("SYNTHETIC_MOCK_OUTPUTS_REQUIRED: real provider is not authorized")
        authority = load_operational_authority(self._operational_authority_path())
        live_mission_id = str(authority.values.get("CURRENT_MISSION") or "").strip()
        if not live_mission_id:
            raise PermissionError("CURRENT_MISSION_REQUIRED: authority has no current mission")
        enrich_prompt = _prompt_contract_for_stage("enrich")
        probe = ExecutionRequest(
            capability_id=CAPABILITY_ID,
            skill_id="topic_belonging",
            skill_version="1.0.0",
            input_artifacts=[],
            output_schema="topic_belonging_input",
            execution_mode=self.execution_mode,
            model=self.model_override,
            reasoning_effort=self.reasoning_effort,
            execution_route=self.execution_route,
            execution_profile=self.execution_profile,
            output_artifact_kind="topic_belonging_input",
            output_artifact_id="PREFLIGHT",
            output_artifact_ref="topic_belonging_input:PREFLIGHT",
            role=PRODUCER_ROLE,
            config={
                "repository_root": str(self.repository_root),
                "mission_authorization_path": self.mission_authorization_path,
                "mission_operation": "EXECUTE_CAPABILITY",
                "execution_interface": self.execution_interface,
                "paid_cost_approved": self.paid_cost_approved,
                "reasoning_effort": self.reasoning_effort,
                "context_policy_path": "config/context_resolution_policy.json",
                "context_references": self._context_references("enrich"),
                "output_refs": ["topic_belonging_input:PREFLIGHT"],
                "prompt_id": enrich_prompt["prompt_id"],
                "prompt_version": enrich_prompt["prompt_version"],
                "run_id": "PREFLIGHT-TOPIC-BELONGING",
                "execution_registry_path": self.execution_registry_path,
            },
        )
        try:
            result = preflight_controlled_execution(probe, root=self.repository_root, reserve_mission=False)
        except (PermissionError, ValueError) as exc:
            detail = str(exc)
            if "authorization path outside repository" in detail:
                detail = "MISSION_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY"
            raise PermissionError(f"MISSION_AUTHORIZATION_INVALID:{detail}") from exc
        authorization = result.get("authorization")
        if authorization is None:
            raise PermissionError("MISSION_SCOPE_AUTHORIZATION_MISMATCH")
        if authorization.mission_id != live_mission_id:
            raise PermissionError("MISSION_SCOPE_AUTHORIZATION_MISMATCH:CURRENT_MISSION")
        self.resolved_mission_id = authorization.mission_id
        return authorization.mission_id

    def _operational_authority_path(self) -> Path:
        if self.operational_authority_path:
            candidate = Path(self.operational_authority_path)
            return candidate if candidate.is_absolute() else self.repository_root / candidate
        return self.repository_root / "plans/001_CONTROL_OPERATIVO.md"

    def _context_references(self, stage: str) -> list[dict[str, Any]]:
        registry = json.loads((self.repository_root / "config/editorial_profile_registry.json").read_text(encoding="utf-8"))
        active_key = registry["active_profile_key"]
        compiled = registry["profiles"][active_key]["compiled_profile_path"]
        prompt_contract = _prompt_contract_for_stage(stage)
        prompt_path = f"prompts/roles/{PROMPT_ROLES[stage]}/{prompt_contract['prompt_version']}.md"
        return [
            {"ref_id": "active-profile", "context_class": "NORMATIVE", "precedence_layer": "NORMATIVE_CONTEXT", "artifact_path": "config/active_editorial_profile.json", "artifact_type": "json", "authority_domain": "CHANNEL_INTELLIGENCE", "required": True},
            {"ref_id": "profile-registry", "context_class": "NORMATIVE", "precedence_layer": "NORMATIVE_CONTEXT", "artifact_path": "config/editorial_profile_registry.json", "artifact_type": "json", "authority_domain": "CHANNEL_INTELLIGENCE", "required": True},
            {"ref_id": "compiled-profile", "context_class": "NORMATIVE", "precedence_layer": "NORMATIVE_CONTEXT", "artifact_path": compiled, "artifact_type": "json", "authority_domain": "CHANNEL_INTELLIGENCE", "required": True},
            {"ref_id": "topic-policy", "context_class": "NORMATIVE", "precedence_layer": "NORMATIVE_CONTEXT", "artifact_path": "policies/channel_intelligence/topic_belonging_policy.md", "artifact_type": "markdown", "authority_domain": "CHANNEL_INTELLIGENCE", "required": True},
            {"ref_id": f"prompt-{stage}", "context_class": "NORMATIVE", "precedence_layer": "NORMATIVE_CONTEXT", "artifact_path": prompt_path, "artifact_type": "markdown", "authority_domain": "CHANNEL_INTELLIGENCE", "required": True},
        ]

    def _run(
        self,
        *,
        stage: str,
        role: str,
        output_schema: str,
        output_kind: str,
        output_id: str,
        episode_id: str,
        inputs: list[tuple[str, str, dict[str, Any], str]],
        mock_output: dict[str, Any] | None,
        role_input_payload: dict[str, Any],
    ) -> tuple[dict[str, Any], ExecutionResult]:
        request_run_id = f"REQUEST-{stage.upper()}-{uuid4().hex}"
        role_id = role
        try:
            prompt_contract = resolve_role_execution_contract(
                role_id,
                output_schema,
                role_input_payload,
                {
                    "episode_id": episode_id,
                    "stage": stage.upper(),
                    "execution_mode": self.execution_mode,
                    "execution_route": self.execution_route,
                    "execution_profile": self.execution_profile,
                    "mission_id": self.resolved_mission_id or "UNRESOLVED_MISSION",
                },
            )
            model_prompt = build_model_prompt(prompt_contract)
        except RoleExecutionContractError as exc:
            raise TopicBelongingExecutionError(f"{stage.upper()}_PROMPT_CONTRACT_INVALID:{exc}") from exc
        if not model_prompt.strip():
            raise TopicBelongingExecutionError(f"{stage.upper()}_PROMPT_EMPTY")
        with tempfile.TemporaryDirectory(prefix="topic-belonging-input-") as temp_dir:
            input_artifacts: list[InputArtifact] = []
            for index, (kind, artifact_id, payload, producer_run_id) in enumerate(inputs):
                path = Path(temp_dir) / f"{index}-{kind}.json"
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                input_artifacts.append(InputArtifact(kind, artifact_id, path, producer_run_id))
            request = ExecutionRequest(
                capability_id=CAPABILITY_ID,
                skill_id="topic_belonging",
                skill_version="1.0.0",
                input_artifacts=input_artifacts,
                output_schema=output_schema,
            execution_mode=self.execution_mode,
            model=("synthetic-structural-test" if self.execution_mode == "SYNTHETIC_TEST" else self.model_override),
            reasoning_effort=self.reasoning_effort,
            provider="mock" if mock_output is not None else None,
                mock_output=mock_output,
                output_artifact_kind=output_kind,
                output_artifact_id=output_id,
                output_artifact_ref=f"{output_kind}:{output_id}",
                execution_route=self.execution_route,
                execution_profile=self.execution_profile,
                episode_id=episode_id,
                role=role,
                config={
                    "repository_root": str(self.repository_root),
                    "mission_authorization_path": self.mission_authorization_path,
                    "execution_profiles_path": str(
                        (self.repository_root / "config/agent_execution_profiles.json").resolve()
                    ),
                    "execution_registry_path": self.execution_registry_path,
                    "mission_operation": "EXECUTE_CAPABILITY",
                    "execution_interface": self.execution_interface,
                    "paid_cost_approved": self.paid_cost_approved,
                    "reasoning_effort": self.reasoning_effort,
                    "context_policy_path": "config/context_resolution_policy.json",
                    "context_references": self._context_references(stage),
                    "input_refs": [f"{kind}:{item_id}" for kind, item_id, _, _ in inputs],
                    "output_refs": [f"{output_kind}:{output_id}"],
                    "prompt_id": prompt_contract["prompt_id"],
                    "prompt_version": prompt_contract["prompt_version"],
                    "prompt_checksum": prompt_contract["prompt_checksum"],
                    "prompt_input_checksum": prompt_contract["input_checksum"],
                    "prompt": model_prompt,
                    "prompt_contract": {
                        "role_id": prompt_contract["role_id"],
                        "prompt_id": prompt_contract["prompt_id"],
                        "prompt_version": prompt_contract["prompt_version"],
                        "output_schema_name": prompt_contract["output_schema_name"],
                    },
                    "run_id": request_run_id,
                    "handoff_target": REVIEWER_ROLE if stage == "produce" else CAPABILITY_ID,
                },
            )
            result = execute(request)
            result.usage.update(
                {
                    "prompt_id": prompt_contract["prompt_id"],
                    "prompt_version": prompt_contract["prompt_version"],
                    "prompt_checksum": prompt_contract["prompt_checksum"],
                    "prompt_input_checksum": prompt_contract["input_checksum"],
                }
            )
        if result.status is not ExecutionStatus.SUCCEEDED or not isinstance(result.output, dict):
            raise TopicBelongingExecutionError(
                f"{stage.upper()}_EXECUTION_BLOCKED:{result.error or result.status.value}"
            )
        output = copy.deepcopy(result.output)
        run_key = "producer_run_id" if stage == "produce" else "reviewer_run_id" if stage == "review" else None
        if run_key:
            declared_run_id = output.get(run_key)
            declared_provenance_run_id = output.get("provenance", {}).get("run_id")
            for declared in (declared_run_id, declared_provenance_run_id):
                if declared not in (None, "") and declared != result.run_id:
                    label = "PRODUCER" if stage == "produce" else "REVIEWER"
                    raise TopicBelongingExecutionError(f"{label}_RUNTIME_PROVENANCE_MISMATCH")
            output[run_key] = result.run_id
            provenance = output.setdefault("provenance", {})
            provenance["run_id"] = result.run_id
            artifact_kind = "assessment" if stage == "produce" else "decision"
            checksum = canonical_checksum(output, artifact_kind)
            if stage == "produce":
                output["artifact_checksum"] = checksum
            provenance["output_checksum"] = checksum
        return output, result

    def enrich(self, handoff: dict[str, Any], human_input: HumanInput, profile: dict[str, Any], episode_id: str) -> tuple[dict[str, Any], ExecutionResult]:
        output = self.mock_outputs.get("enrich") if self.mock_outputs is not None else None
        return self._run(
            stage="enrich",
            role=PRODUCER_ROLE,
            output_schema="topic_belonging_input",
            output_kind="topic_belonging_input",
            output_id=str((output or {}).get("topic_input_id") or f"TBI-{uuid4().hex}"),
            episode_id=episode_id,
            inputs=[("editorial_intake_handoff", handoff["source_interaction_id"], handoff, "")],
            mock_output=output,
            role_input_payload={
                "EditorialIntakeHandoff": handoff,
                "active_editorial_profile": profile,
                "initial_evidence": handoff.get("evidence_refs", []),
            },
        )

    def produce(self, topic_input: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "") -> tuple[dict[str, Any], ExecutionResult]:
        output = self.mock_outputs.get("produce") if self.mock_outputs is not None else None
        return self._run(
            stage="produce",
            role=PRODUCER_ROLE,
            output_schema="topic_belonging_assessment",
            output_kind="topic_belonging_assessment",
            output_id=str((output or {}).get("assessment_id") or f"TBA-{uuid4().hex}"),
            episode_id=episode_id,
            inputs=[("topic_belonging_input", topic_input["topic_input_id"], topic_input, input_producer_run_id)],
            mock_output=output,
            role_input_payload={
                "TopicBelongingInput": topic_input,
                "active_editorial_profile": profile,
                "initial_evidence": topic_input.get("initial_evidence", []),
            },
        )

    def review(self, topic_input: dict[str, Any], assessment: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "") -> tuple[dict[str, Any], ExecutionResult]:
        output = self.mock_outputs.get("review") if self.mock_outputs is not None else None
        if output is not None:
            output = copy.deepcopy(output)
            output["producer_artifact_checksum"] = assessment["artifact_checksum"]
            output["reviewer_input_checksum"] = assessment["artifact_checksum"]
            if isinstance(output.get("provenance"), dict):
                output["provenance"]["input_checksum"] = assessment["artifact_checksum"]
        return self._run(
            stage="review",
            role=REVIEWER_ROLE,
            output_schema="topic_belonging_decision",
            output_kind="topic_belonging_decision",
            output_id=str((output or {}).get("decision_id") or f"TBD-{uuid4().hex}"),
            episode_id=episode_id,
            inputs=[
                ("topic_belonging_input", topic_input["topic_input_id"], topic_input, input_producer_run_id),
                ("topic_belonging_assessment", assessment["assessment_id"], assessment, assessment["producer_run_id"]),
            ],
            mock_output=output,
            role_input_payload={
                "TopicBelongingInput": topic_input,
                "TopicBelongingAssessment": assessment,
                "active_editorial_profile": profile,
            },
        )


class TopicBelongingTechnicalWorkflow:
    """Application workflow for M1; it stops after the Topic Belonging gate."""

    def __init__(
        self,
        store: VaultEpisodeStore,
        *,
        boundary: CognitiveBoundary,
        profile_loader=load_active_profile_authority,
    ):
        self.store = store
        self.boundary = boundary
        self.profile_loader = profile_loader
        self._mission_id: str | None = None

    def preflight(self) -> str:
        repository_root = Path(getattr(self.boundary, "repository_root", REPO_ROOT))
        authority_path = getattr(self.boundary, "operational_authority_path", None)
        if authority_path:
            candidate = Path(authority_path)
            authority_path = candidate if candidate.is_absolute() else repository_root / candidate
        else:
            authority_path = repository_root / "plans/001_CONTROL_OPERATIVO.md"
        authority = load_operational_authority(authority_path)
        live_mission_id = str(authority.values.get("CURRENT_MISSION") or "").strip()
        if not live_mission_id:
            raise PermissionError("CURRENT_MISSION_REQUIRED: authority has no current mission")
        authorized_mission_id = self.boundary.preflight()
        if authorized_mission_id != live_mission_id:
            raise PermissionError("MISSION_SCOPE_AUTHORIZATION_MISMATCH:CURRENT_MISSION")
        self._mission_id = live_mission_id
        return live_mission_id

    def start(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], run_id: str) -> dict[str, Any]:
        self.preflight()
        profile = self.profile_loader()
        handoff_violations = _validate_human_handoff_binding(human_input.to_dict(), handoff)
        if handoff_violations:
            raise TopicBelongingExecutionError("HANDOFF_INVALID: " + "; ".join(handoff_violations))
        topic_input, enrich_result = self.boundary.enrich(handoff, human_input, profile, handle.episode_id)
        enrichment_violations = _validate_enrichment_binding(topic_input, handoff)
        if enrichment_violations:
            raise TopicBelongingExecutionError("ENRICHMENT_INVALID: " + "; ".join(enrichment_violations))
        input_violations = validate_topic_input(topic_input)
        if input_violations:
            raise TopicBelongingExecutionError("TOPIC_INPUT_INVALID: " + "; ".join(input_violations))

        assessment, producer_result = self.boundary.produce(topic_input, profile, handle.episode_id, input_producer_run_id=enrich_result.run_id)
        assessment_violations = validate_assessment(assessment, topic_input)
        if assessment_violations:
            raise TopicBelongingExecutionError("ASSESSMENT_INVALID: " + "; ".join(assessment_violations))
        if assessment.get("producer_actor_id") != assessment.get("provenance", {}).get("actor_id"):
            raise TopicBelongingExecutionError("ASSESSMENT_INVALID: PRODUCER_ACTOR_PROVENANCE_MISMATCH")

        decision, reviewer_result = self.boundary.review(topic_input, assessment, profile, handle.episode_id, input_producer_run_id=enrich_result.run_id)
        if producer_result.run_id == reviewer_result.run_id:
            raise TopicBelongingExecutionError("EXECUTION_INDEPENDENCE_INVALID:SAME_RUNTIME_RUN_ID")
        decision_violations = validate_decision(decision, assessment)
        if decision_violations:
            raise TopicBelongingExecutionError("DECISION_INVALID: " + "; ".join(decision_violations))
        if decision.get("reviewer_actor_id") != decision.get("provenance", {}).get("actor_id"):
            raise TopicBelongingExecutionError("DECISION_INVALID: REVIEWER_ACTOR_PROVENANCE_MISMATCH")

        gate = evaluate_topic_belonging_gate(decision, assessment, topic_input)
        lineage = {
            "mission_id": self._mission_id,
            "episode_id": handle.episode_id,
            "human_input_ref": f"episode:{handle.episode_id}/00_human_input.json",
            "handoff_ref": f"episode:{handle.episode_id}/01_editorial_intake_handoff.json",
            "topic_input_ref": f"episode:{handle.episode_id}/02_topic_belonging_input.json",
            "assessment_ref": f"episode:{handle.episode_id}/03_topic_belonging_assessment.json",
            "decision_ref": f"episode:{handle.episode_id}/04_topic_belonging_decision.json",
            "gate_ref": f"episode:{handle.episode_id}/05_topic_belonging_gate.json",
            "handoff_checksum": _json_checksum(handoff),
            "topic_input_checksum": canonical_checksum(topic_input, "input"),
            "assessment_checksum": assessment["artifact_checksum"],
            "decision_checksum": decision["provenance"]["output_checksum"],
            "enrichment_run_id": enrich_result.run_id,
            "producer_run_id": producer_result.run_id,
            "reviewer_run_id": reviewer_result.run_id,
            "producer_actor_id": assessment["producer_actor_id"],
            "reviewer_actor_id": decision["reviewer_actor_id"],
            "stop_after": "TOPIC_BELONGING_GATE",
        }
        executions = [
            self._execution_record(
                "ENRICHMENT",
                PRODUCER_ROLE,
                enrich_result,
                canonical_checksum(topic_input, "input"),
                [f"editorial_intake_handoff:{handoff['source_interaction_id']}"],
                [],
            ),
            self._execution_record(
                "PRODUCER",
                PRODUCER_ROLE,
                producer_result,
                assessment["artifact_checksum"],
                [f"topic_belonging_input:{topic_input['topic_input_id']}"],
                [enrich_result.run_id],
            ),
            self._execution_record(
                "REVIEWER",
                REVIEWER_ROLE,
                reviewer_result,
                decision["provenance"]["output_checksum"],
                [
                    f"topic_belonging_input:{topic_input['topic_input_id']}",
                    f"topic_belonging_assessment:{assessment['assessment_id']}",
                ],
                [enrich_result.run_id, producer_result.run_id],
            ),
        ]
        self.store.record_topic_belonging_vertical(
            handle,
            topic_input=topic_input,
            assessment=assessment,
            decision=decision,
            gate_result=gate,
            lineage=lineage,
            executions=executions,
        )
        return self._build_stop_state(handle, run_id, gate, decision)

    @staticmethod
    def _build_stop_state(handle: EpisodeHandle, run_id: str, gate: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "workflow_id": "R2_M1_TOPIC_BELONGING_TECHNICAL_VERTICAL",
            "status": STOP_STATUS,
            "episode_id": handle.episode_id,
            "run_id": run_id,
            "vertical_gate_status": gate.get("status"),
            "editorial_decision": decision.get("decision"),
            "downstream_execution_started": False,
            "stop_boundary": "TOPIC_BELONGING_GATE",
            "blocked_capabilities": ["RESEARCH_PACK", "B5_I2", "B5_I3", "B5.5", "B6", "S5_REAL_EXECUTION", "PUBLICATION"],
        }

    def complete(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], run_id: str) -> dict[str, Any] | None:
        """Complete an incomplete M1 vertical; idempotent when already stopped.

        The intake persists the episode (``READY_FOR_EDITORIAL_ENRICHMENT``) before
        the vertical runs, so a cognitive or persistence failure can leave the
        episode recoverable but unfinished. This method re-runs the vertical from
        scratch when no valid artifacts exist, finalizes the stop state when the
        artifacts were persisted but the workflow state was not recorded, and does
        nothing when the vertical is already recorded.
        """
        if self._vertical_complete(handle):
            self._validate_persisted_vertical(handle)
            if self._workflow_status(handle) == STOP_STATUS:
                return None
            return self._final_state_from_persisted(handle, run_id)
        if self._workflow_status(handle) == STOP_STATUS:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:INCOMPLETE_VERTICAL_WITH_STOP_STATE"
            )
        self._validate_persisted_origin_binding(handle)
        state_mission_id, index_mission_id, lineage_mission_id = self._persisted_mission_bindings(handle)
        if bool(state_mission_id) != bool(index_mission_id):
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:MODERN_MISSION_BINDING_INCOMPLETE"
            )
        if not state_mission_id and not index_mission_id:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:MODERN_MISSION_BINDING_MISSING:STATE_INDEX"
            )
        if lineage_mission_id is None and state_mission_id != self._mission_id:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:HISTORICAL_INCOMPLETE_REQUIRES_SAME_MISSION"
            )
        if state_mission_id and state_mission_id != index_mission_id:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:MODERN_MISSION_BINDING_MISMATCH"
            )
        if lineage_mission_id and lineage_mission_id != state_mission_id:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:MODERN_MISSION_BINDING_MISMATCH"
            )
        if state_mission_id and state_mission_id != self._mission_id:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:HISTORICAL_INCOMPLETE_REQUIRES_SAME_MISSION"
            )
        self._clear_partial_vertical(handle)
        return self.start(handle, human_input, handoff, run_id)

    def _vertical_complete(self, handle: EpisodeHandle) -> bool:
        return all((handle.folder / name).is_file() for name in VERTICAL_ARTIFACTS)

    def _workflow_status(self, handle: EpisodeHandle) -> str | None:
        data = self._read_episode_file(handle, "workflow_state.json")
        return data.get("status")

    def _persisted_mission_bindings(self, handle: EpisodeHandle) -> tuple[Any, Any, Any]:
        try:
            state = self._read_episode_file(handle, "episode_state.json")
            index = json.loads(handle.index_path.read_text(encoding="utf-8"))
            entry = next(item for item in index.get("episodes", []) if item.get("ep_id") == handle.episode_id)
            lineage_path = handle.folder / "topic_belonging_lineage.json"
            lineage = json.loads(lineage_path.read_text(encoding="utf-8")) if lineage_path.is_file() else {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StopIteration, AttributeError) as exc:
            raise TopicBelongingExecutionError(
                f"PERSISTED_VERTICAL_INTEGRITY_INVALID:MISSION_BINDING_READ:{exc}"
            ) from exc
        return state.get("mission_id"), entry.get("mission_id"), lineage.get("mission_id")

    def _validate_persisted_origin_binding(self, handle: EpisodeHandle) -> None:
        try:
            origin = self._read_episode_file(handle, "episode_origin.json")
            state = self._read_episode_file(handle, "episode_state.json")
            index = json.loads(handle.index_path.read_text(encoding="utf-8"))
            entry = next(item for item in index.get("episodes", []) if item.get("ep_id") == handle.episode_id)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StopIteration, AttributeError) as exc:
            raise TopicBelongingExecutionError(
                f"PERSISTED_VERTICAL_INTEGRITY_INVALID:ORIGIN_READ:{exc}"
            ) from exc
        if not isinstance(origin, dict) or set(origin) != EPISODE_ORIGIN_FIELDS:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:EPISODE_ORIGIN_SCHEMA_INVALID"
            )
        state_anchor = {
            key: value
            for key, value in state.items()
            if key not in {"status", "updated_at", "administrative_closure_ref"}
        }
        index_anchor = {
            key: value
            for key, value in entry.items()
            if key not in {"estado", "application_status", "cerrado", "administrative_closure_ref", "administrative_closure"}
        }
        origin_payload = {
            "episode_id": origin.get("episode_id"),
            "origin": origin.get("origin"),
            "state_anchor_sha256": origin.get("state_anchor_sha256"),
            "index_anchor_sha256": origin.get("index_anchor_sha256"),
        }
        valid = (
            origin.get("episode_id") == handle.episode_id
            and origin.get("state_anchor_sha256") == hashlib.sha256(
                json.dumps(state_anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            and origin.get("index_anchor_sha256") == hashlib.sha256(
                json.dumps(index_anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            and origin.get("origin_checksum") == hashlib.sha256(
                json.dumps(origin_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        )
        if not valid:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:EPISODE_ORIGIN_BINDING_INVALID"
            )
        if not isinstance(origin.get("origin"), str) or origin.get("origin") not in {"LEGACY_M1", "MODERN_M1"}:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:EPISODE_ORIGIN_KIND_INVALID"
            )
        legacy_storage = (
            state.get("status") == "LEGACY_TECHNICAL_INITIALIZATION"
            and state.get("provenance", {}).get("source") == "LEGACY_SCRIPT"
            and entry.get("input_origin") == "LEGACY_SCRIPT_TECHNICAL"
            and entry.get("application_status") == "LEGACY_TECHNICAL_INITIALIZATION"
        )
        if state.get("status") != entry.get("application_status"):
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:EPISODE_ORIGIN_STORAGE_STATUS_MISMATCH"
            )
        if origin.get("origin") == "LEGACY_M1" and not legacy_storage:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:LEGACY_ORIGIN_STORAGE_BINDING_INVALID"
            )
        if origin.get("origin") == "MODERN_M1" and legacy_storage:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID:MODERN_ORIGIN_STORAGE_BINDING_INVALID"
            )

    def _validate_persisted_vertical(self, handle: EpisodeHandle) -> dict[str, dict[str, Any]]:
        """Validate every persisted M1 binding before recovering the technical stop.

        ``_vertical_complete`` only establishes physical presence. This method
        establishes that the six files still describe one valid, coherent M1
        execution and raises before any workflow state is reconstructed.
        """
        try:
            persisted = {
                name: self._read_episode_file(handle, name)
                for name in VERTICAL_ARTIFACTS
            }
            handoff = self._read_episode_file(handle, "01_editorial_intake_handoff.json")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise TopicBelongingExecutionError(
                f"PERSISTED_VERTICAL_INTEGRITY_INVALID:FILE_READ:{exc}"
            ) from exc

        violations: list[str] = []
        if any(not isinstance(value, dict) for value in persisted.values()):
            violations.append("PERSISTED_VERTICAL_ARTIFACT_NOT_OBJECT")
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID: " + "; ".join(violations)
            )

        for required_name in ("00_human_input.json", "01_editorial_intake_handoff.json"):
            if not (handle.folder / required_name).is_file():
                violations.append(f"REQUIRED_INTAKE_ARTIFACT_MISSING:{required_name}")
        for downstream_name in (
            "episode_brief.json",
            "research_pack.json",
            "thesis_provisional.json",
            "script.json",
        ):
            if (handle.folder / downstream_name).exists():
                violations.append(f"DOWNSTREAM_ARTIFACT_PRESENT:{downstream_name}")
        unexpected = sorted(
            path.name
            for path in handle.folder.iterdir()
            if path.name not in M1_ALLOWED_EPISODE_ARTIFACTS
            and not any(
                re.fullmatch(rf"r\d*-{re.escape(artifact)}", path.name)
                for artifact in VERTICAL_ARTIFACTS
            )
        )
        violations.extend(f"UNEXPECTED_M1_ARTIFACT_PRESENT:{name}" for name in unexpected)

        human_input = self._read_episode_file(handle, "00_human_input.json")
        topic_input = persisted["02_topic_belonging_input.json"]
        assessment = persisted["03_topic_belonging_assessment.json"]
        decision = persisted["04_topic_belonging_decision.json"]
        gate = persisted["05_topic_belonging_gate.json"]
        lineage = persisted["topic_belonging_lineage.json"]
        execution_payload = persisted["topic_belonging_execution.json"]
        episode_state = self._read_episode_file(handle, "episode_state.json")
        try:
            index_data = json.loads(handle.index_path.read_text(encoding="utf-8"))
            index_entry = next(
                item for item in index_data.get("episodes", []) if item.get("ep_id") == handle.episode_id
            )
            index_mission_id = index_entry.get("mission_id")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StopIteration, AttributeError) as exc:
            raise TopicBelongingExecutionError(
                f"PERSISTED_VERTICAL_INTEGRITY_INVALID:INDEX_READ:{exc}"
            ) from exc
        origin_path = handle.folder / "episode_origin.json"
        try:
            origin = self._read_episode_file(handle, "episode_origin.json") if origin_path.is_file() else {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise TopicBelongingExecutionError(
                f"PERSISTED_VERTICAL_INTEGRITY_INVALID:ORIGIN_READ:{exc}"
            ) from exc
        if not isinstance(origin, dict):
            violations.append("EPISODE_ORIGIN_SCHEMA_INVALID")
            origin = {}
        elif set(origin) != EPISODE_ORIGIN_FIELDS:
            violations.append("EPISODE_ORIGIN_SCHEMA_INVALID")
        state_anchor = {
            key: value
            for key, value in episode_state.items()
            if key not in {"status", "updated_at", "administrative_closure_ref"}
        }
        index_anchor = {
            key: value
            for key, value in index_entry.items()
            if key not in {"estado", "application_status", "cerrado", "administrative_closure_ref", "administrative_closure"}
        }
        origin_payload = {
            "episode_id": origin.get("episode_id"),
            "origin": origin.get("origin"),
            "state_anchor_sha256": origin.get("state_anchor_sha256"),
            "index_anchor_sha256": origin.get("index_anchor_sha256"),
        }
        expected_origin_checksum = hashlib.sha256(
            json.dumps(origin_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        origin_valid = (
            bool(origin)
            and origin.get("episode_id") == handle.episode_id
            and origin.get("state_anchor_sha256") == hashlib.sha256(
                json.dumps(state_anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            and origin.get("index_anchor_sha256") == hashlib.sha256(
                json.dumps(index_anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            and origin.get("origin_checksum") == expected_origin_checksum
        )
        origin_kind = origin.get("origin") if origin_valid else None
        legacy_storage = (
            episode_state.get("status") == "LEGACY_TECHNICAL_INITIALIZATION"
            and episode_state.get("provenance", {}).get("source") == "LEGACY_SCRIPT"
            and index_entry.get("input_origin") == "LEGACY_SCRIPT_TECHNICAL"
            and index_entry.get("application_status") == "LEGACY_TECHNICAL_INITIALIZATION"
            and origin_kind == "LEGACY_M1"
        )
        legacy_vertical = lineage.get("mission_id") == LEGACY_M1_LINEAGE_ID and legacy_storage

        violations.extend(
            f"HANDOFF_SCHEMA_INVALID: {violation}"
            for violation in validate_against_schema(handoff, "editorial_intake_handoff")
        )
        violations.extend(_validate_human_handoff_binding(human_input, handoff))
        violations.extend(
            f"ENRICHMENT_BINDING_INVALID: {violation}"
            for violation in _validate_enrichment_binding(topic_input, handoff)
        )
        violations.extend(
            f"TOPIC_INPUT_INVALID: {violation}"
            for violation in validate_topic_input(topic_input)
        )
        violations.extend(
            f"ASSESSMENT_INVALID: {violation}"
            for violation in validate_assessment(assessment, topic_input)
        )
        violations.extend(
            f"DECISION_INVALID: {violation}"
            for violation in validate_decision(decision, assessment)
        )

        expected_gate = evaluate_topic_belonging_gate(decision, assessment, topic_input)
        if gate != expected_gate:
            violations.append("GATE_BINDING_INVALID")

        expected_lineage = {
            "episode_id": handle.episode_id,
            "human_input_ref": f"episode:{handle.episode_id}/00_human_input.json",
            "handoff_ref": f"episode:{handle.episode_id}/01_editorial_intake_handoff.json",
            "topic_input_ref": f"episode:{handle.episode_id}/02_topic_belonging_input.json",
            "assessment_ref": f"episode:{handle.episode_id}/03_topic_belonging_assessment.json",
            "decision_ref": f"episode:{handle.episode_id}/04_topic_belonging_decision.json",
            "gate_ref": f"episode:{handle.episode_id}/05_topic_belonging_gate.json",
            "handoff_checksum": _json_checksum(handoff),
            "topic_input_checksum": canonical_checksum(topic_input, "input"),
            "assessment_checksum": assessment.get("artifact_checksum"),
            "decision_checksum": decision.get("provenance", {}).get("output_checksum"),
            "enrichment_run_id": lineage.get("enrichment_run_id"),
            "producer_run_id": lineage.get("producer_run_id"),
            "reviewer_run_id": lineage.get("reviewer_run_id"),
            "producer_actor_id": assessment.get("producer_actor_id"),
            "reviewer_actor_id": decision.get("reviewer_actor_id"),
            "stop_after": "TOPIC_BELONGING_GATE",
        }
        lineage_mission_id = lineage.get("mission_id")
        state_mission_id = episode_state.get("mission_id")
        if not origin:
            violations.append("EPISODE_ORIGIN_BINDING_MISSING")
        elif not origin_valid:
            violations.append("EPISODE_ORIGIN_BINDING_INVALID")
        elif origin_kind not in {"LEGACY_M1", "MODERN_M1"}:
            violations.append("EPISODE_ORIGIN_KIND_INVALID")
        elif legacy_vertical and origin_kind != "LEGACY_M1":
            violations.append("LEGACY_LINEAGE_HAS_MODERN_ORIGIN")
        elif not legacy_vertical and origin_kind != "MODERN_M1":
            violations.append("MODERN_LINEAGE_HAS_LEGACY_ORIGIN")
        if origin_kind == "MODERN_M1" and lineage_mission_id == LEGACY_M1_LINEAGE_ID:
            violations.append("LEGACY_LINEAGE_HAS_MODERN_ORIGIN")
        if lineage_mission_id == LEGACY_M1_LINEAGE_ID and not legacy_storage:
            violations.append("LEGACY_LINEAGE_STORAGE_BINDING_INVALID")
        if legacy_vertical:
            if state_mission_id or index_mission_id:
                violations.append("LEGACY_LINEAGE_HAS_MODERN_MISSION_BINDING")
        else:
            for label, value in (
                ("STATE", state_mission_id),
                ("INDEX", index_mission_id),
                ("LINEAGE", lineage_mission_id),
            ):
                if not isinstance(value, str) or not value.strip():
                    violations.append(f"MODERN_MISSION_BINDING_MISSING:{label}")
            modern_ids = {value for value in (state_mission_id, index_mission_id, lineage_mission_id) if isinstance(value, str) and value.strip()}
            if len(modern_ids) > 1:
                violations.append("MODERN_MISSION_BINDING_MISMATCH")
        for key, expected in expected_lineage.items():
            if lineage.get(key) != expected:
                violations.append(f"LINEAGE_{key.upper()}_MISMATCH")

        enrichment_run_id = lineage.get("enrichment_run_id")
        producer_run_id = lineage.get("producer_run_id")
        reviewer_run_id = lineage.get("reviewer_run_id")
        if not all(isinstance(value, str) and value.strip() and value != "UNKNOWN" for value in (enrichment_run_id, producer_run_id, reviewer_run_id)):
            violations.append("LINEAGE_RUNTIME_RUN_ID_MISSING")
        if producer_run_id == reviewer_run_id:
            violations.append("LINEAGE_EXECUTION_INDEPENDENCE_INVALID")
        if assessment.get("producer_run_id") != producer_run_id:
            violations.append("LINEAGE_ASSESSMENT_PRODUCER_RUN_MISMATCH")
        if assessment.get("provenance", {}).get("run_id") != producer_run_id:
            violations.append("LINEAGE_ASSESSMENT_PROVENANCE_RUN_MISMATCH")
        if assessment.get("producer_actor_id") != assessment.get("provenance", {}).get("actor_id"):
            violations.append("LINEAGE_ASSESSMENT_PRODUCER_ACTOR_MISMATCH")
        if decision.get("reviewer_run_id") != reviewer_run_id:
            violations.append("LINEAGE_DECISION_REVIEWER_RUN_MISMATCH")
        if decision.get("provenance", {}).get("run_id") != reviewer_run_id:
            violations.append("LINEAGE_DECISION_PROVENANCE_RUN_MISMATCH")
        if decision.get("reviewer_actor_id") != decision.get("provenance", {}).get("actor_id"):
            violations.append("LINEAGE_DECISION_REVIEWER_ACTOR_MISMATCH")

        executions = execution_payload.get("executions")
        expected_stages = ("ENRICHMENT", "PRODUCER", "REVIEWER")
        if not isinstance(executions, list) or len(executions) != len(expected_stages):
            violations.append("EXECUTION_RECORDS_COUNT_INVALID")
            executions = []
        elif tuple(item.get("stage") for item in executions if isinstance(item, dict)) != expected_stages:
            violations.append("EXECUTION_RECORDS_STAGES_INVALID")

        expected_execution_bindings = {
            "ENRICHMENT": {
                "role": PRODUCER_ROLE,
                "run_id": enrichment_run_id,
                "artifact_ref": f"topic_belonging_input:{topic_input.get('topic_input_id')}",
                "artifact_checksum": canonical_checksum(topic_input, "input"),
                "input_artifact_ids": [f"editorial_intake_handoff:{handoff.get('source_interaction_id')}"],
                "input_versions": [],
            },
            "PRODUCER": {
                "role": PRODUCER_ROLE,
                "run_id": producer_run_id,
                "artifact_ref": f"topic_belonging_assessment:{assessment.get('assessment_id')}",
                "artifact_checksum": assessment.get("artifact_checksum"),
                "input_artifact_ids": [f"topic_belonging_input:{topic_input.get('topic_input_id')}"],
                "input_versions": [enrichment_run_id],
            },
            "REVIEWER": {
                "role": REVIEWER_ROLE,
                "run_id": reviewer_run_id,
                "artifact_ref": f"topic_belonging_decision:{decision.get('decision_id')}",
                "artifact_checksum": decision.get("provenance", {}).get("output_checksum"),
                "input_artifact_ids": [
                    f"topic_belonging_input:{topic_input.get('topic_input_id')}",
                    f"topic_belonging_assessment:{assessment.get('assessment_id')}",
                ],
                "input_versions": [enrichment_run_id, producer_run_id],
            },
        }
        expected_input_manifests = {
            stage: _expected_input_manifest_checksum(
                handle.episode_id,
                stage,
                handoff,
                topic_input,
                assessment,
            )
            for stage in expected_stages
        }
        expected_prompt_bindings: dict[str, dict[str, str]] = {}
        try:
            active_profile = self.profile_loader()
            prompt_inputs = {
                "ENRICHMENT": {
                    "EditorialIntakeHandoff": handoff,
                    "active_editorial_profile": active_profile,
                    "initial_evidence": handoff.get("evidence_refs", []),
                },
                "PRODUCER": {
                    "TopicBelongingInput": topic_input,
                    "active_editorial_profile": active_profile,
                    "initial_evidence": topic_input.get("initial_evidence", []),
                },
                "REVIEWER": {
                    "TopicBelongingInput": topic_input,
                    "TopicBelongingAssessment": assessment,
                    "active_editorial_profile": active_profile,
                },
            }
            prompt_schemas = {
                "ENRICHMENT": "topic_belonging_input",
                "PRODUCER": "topic_belonging_assessment",
                "REVIEWER": "topic_belonging_decision",
            }
            for stage, schema_name in prompt_schemas.items():
                role = PRODUCER_ROLE if stage != "REVIEWER" else REVIEWER_ROLE
                contract = resolve_role_execution_contract(
                    role,
                    schema_name,
                    prompt_inputs[stage],
                    {"episode_id": handle.episode_id, "stage": stage, "mission_id": lineage_mission_id},
                )
                expected_prompt_bindings[stage] = {
                    "prompt_id": contract["prompt_id"],
                    "prompt_version": contract["prompt_version"],
                    "prompt_checksum": contract["prompt_checksum"],
                    "prompt_input_checksum": contract["input_checksum"],
                }
        except (RoleExecutionContractError, OSError, ValueError) as exc:
            violations.append(f"PROMPT_PROVENANCE_EXPECTATION_INVALID:{exc}")
        for execution in executions:
            if not isinstance(execution, dict):
                violations.append("EXECUTION_RECORD_NOT_OBJECT")
                continue
            stage = execution.get("stage")
            expected = expected_execution_bindings.get(stage)
            if expected is None:
                violations.append(f"EXECUTION_RECORD_STAGE_UNKNOWN:{stage}")
                continue
            for key, expected_value in expected.items():
                if execution.get(key) != expected_value:
                    violations.append(f"EXECUTION_{stage}_{key.upper()}_MISMATCH")
            if execution.get("input_manifest_checksum") != expected_input_manifests.get(stage):
                violations.append(f"EXECUTION_{stage}_INPUT_MANIFEST_CHECKSUM_MISMATCH")
            for key, expected_value in {
                "provider_kind": "SYNTHETIC",
                "provider_or_adapter": "mock",
                "execution_mode": "SYNTHETIC",
                "execution_route": "local_model",
                "execution_profile": "ollama_local",
            }.items():
                if execution.get(key) != expected_value:
                    violations.append(f"EXECUTION_{stage}_{key.upper()}_INCOMPATIBLE")
            if not legacy_vertical:
                for key, expected_value in expected_prompt_bindings.get(stage, {}).items():
                    if execution.get(key) != expected_value:
                        violations.append(f"EXECUTION_{stage}_{key.upper()}_MISMATCH")
            if execution.get("status") != ExecutionStatus.SUCCEEDED.value:
                violations.append(f"EXECUTION_{stage}_STATUS_INVALID")
            for checksum_key in ("input_manifest_checksum", "output_checksum", "artifact_checksum"):
                checksum = execution.get(checksum_key)
                if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-fA-F]{64}", checksum) is None:
                    violations.append(f"EXECUTION_{stage}_{checksum_key.upper()}_INVALID")
            expected_raw_checksum = _expected_raw_output_checksum(stage, topic_input, assessment, decision)
            if execution.get("output_checksum") != expected_raw_checksum:
                violations.append(f"EXECUTION_{stage}_RAW_OUTPUT_CHECKSUM_MISMATCH")
            if not isinstance(execution.get("execution_route"), str) or not execution.get("execution_route", "").strip():
                violations.append(f"EXECUTION_{stage}_ROUTE_INVALID")
            if not isinstance(execution.get("execution_profile"), str) or not execution.get("execution_profile", "").strip():
                violations.append(f"EXECUTION_{stage}_PROFILE_INVALID")

        if violations:
            raise TopicBelongingExecutionError(
                "PERSISTED_VERTICAL_INTEGRITY_INVALID: " + "; ".join(violations)
            )
        return persisted

    def _clear_partial_vertical(self, handle: EpisodeHandle) -> None:
        """Move partial evidence aside without deleting it before an atomic retry."""
        evidence: list[tuple[Path, bytes]] = []
        for name in VERTICAL_ARTIFACTS:
            path = handle.folder / name
            if not path.exists():
                continue
            evidence.append((path, path.read_bytes()))
        for path, content in evidence:
            target = path.with_name(f"r-{path.name}")
            suffix = 1
            while target.exists():
                target = path.with_name(f"r{suffix}-{path.name}")
                suffix += 1
            target.write_bytes(content)
            path.unlink()

    def _read_episode_file(self, handle: EpisodeHandle, name: str) -> dict[str, Any]:
        path = handle.folder / name
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _final_state_from_persisted(self, handle: EpisodeHandle, run_id: str) -> dict[str, Any]:
        gate = self._read_episode_file(handle, "05_topic_belonging_gate.json")
        decision = self._read_episode_file(handle, "04_topic_belonging_decision.json")
        return self._build_stop_state(handle, run_id, gate, decision)

    @staticmethod
    def _execution_record(
        stage: str,
        role: str,
        result: ExecutionResult,
        artifact_checksum: str,
        input_artifact_ids: list[str],
        input_versions: list[str],
    ) -> dict[str, Any]:
        return {
            "stage": stage,
            "role": role,
            "run_id": result.run_id,
            "status": result.status.value,
            "provider_kind": result.usage.get("provider_kind"),
            "provider_or_adapter": result.provider,
            "model_or_evaluator": result.model,
            "input_manifest_checksum": result.input_manifest_checksum,
            "input_artifact_ids": list(input_artifact_ids),
            "input_versions": list(input_versions),
            # Raw runtime output checksum (what the runtime produced).
            "output_checksum": result.output_checksum,
            # Canonical checksum of the persisted artifact after deterministic normalization/binding.
            "artifact_checksum": artifact_checksum,
            "artifact_ref": result.output_artifact_ref,
            "execution_mode": result.usage.get("execution_mode", "SYNTHETIC" if result.provider == "mock" else "REAL"),
            "execution_route": result.usage.get("execution_route"),
            "execution_profile": result.usage.get("execution_profile"),
            "prompt_id": result.usage.get("prompt_id"),
            "prompt_version": result.usage.get("prompt_version"),
            "prompt_checksum": result.usage.get("prompt_checksum"),
            "prompt_input_checksum": result.usage.get("prompt_input_checksum"),
        }

    def resume(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], decision: Any, request: Any) -> dict[str, Any]:
        raise StorageError("La vertical Topic Belonging no admite decisiones humanas intermedias.")


def build_topic_belonging_service(store: VaultEpisodeStore, *, boundary: CognitiveBoundary) -> TopicBelongingTechnicalWorkflow:
    """Factory kept as the single application entrypoint for the capability route."""
    return TopicBelongingTechnicalWorkflow(store, boundary=boundary)
