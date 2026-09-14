"""Controlled Topic Belonging vertical between intake and the episode stop gate."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from typing import Any, Protocol
from uuid import uuid4

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute
from src.ai.manifest import file_checksum, manifest_checksum
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.role_execution import RoleExecutionContractError, build_model_prompt, resolve_role_execution_contract
from src.ai.runtime_profiles import (
    EXECUTION_FAMILY_SELECTION_PATH,
    load_execution_profiles,
    validate_execution_family_selection,
)
from src.application.contracts import EntryMode, HumanInput
from src.application.storage import EpisodeHandle, StorageError, VaultEpisodeStore
from src.application.authority import load_operational_authority, resolve_active_mission_bundle
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
ROUNDTRIP_STATE_FILENAME = "roundtrip_state.json"
ROUNDTRIP_RESULTS_FILENAME = "roundtrip_results.json"
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
P2_ALLOWED_EPISODE_ARTIFACTS = M1_ALLOWED_EPISODE_ARTIFACTS | frozenset(
    {
        ROUNDTRIP_STATE_FILENAME,
        ROUNDTRIP_RESULTS_FILENAME,
        "roundtrip_results",
        "topic_belonging_reassessments.json",
    }
)

STOP_STATUS = "TOPIC_BELONGING_TECHNICAL_STOP"
COGNITIVE_PROPOSAL_SCHEMA = "topic_belonging_cognitive_proposal"
COGNITIVE_ASSESSMENT_FIELDS = frozenset(
    {
        "strategic_triggers",
        "sensitive_risks",
        "territory_classification",
        "identity_alignment",
        "promise_alignment",
        "risks",
        "recommended_conditions",
        "recommended_exclusions",
        "owner_escalation_recommended",
        "evidence",
        "status",
    }
)
COGNITIVE_DECISION_FIELDS = frozenset(
    {
        "decision",
        "conditions",
        "exclusions",
        "risks",
        "owner_escalation_required",
        "owner_escalation_reason",
        "strategic_dimensions_affected",
        "temporary_or_permanent_effect",
        "precedent_risk",
        "evidence",
        "pre_b5_i1_evidence",
    }
)
REQUIRED_COGNITIVE_DECISION_FIELDS = COGNITIVE_DECISION_FIELDS - {"pre_b5_i1_evidence"}
EXTERNAL_PRODUCER_ACTOR_ID = "AGENT_HARNESS_EXTERNAL_PRODUCER"
EXTERNAL_REVIEWER_ACTOR_ID = "AGENT_HARNESS_EXTERNAL_REVIEWER"


def _prompt_contract_for_stage(stage: str) -> dict[str, Any]:
    return resolve_prompt(PROMPT_ROLES[stage])


class TopicBelongingExecutionError(PermissionError):
    """A cognitive boundary execution did not produce a contractual output."""


class CognitiveBoundary(Protocol):
    def preflight(self) -> str: ...

    def enrich(self, handoff: dict[str, Any], human_input: HumanInput, profile: dict[str, Any], episode_id: str) -> tuple[dict[str, Any], ExecutionResult]: ...

    def produce(self, topic_input: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "") -> tuple[dict[str, Any], ExecutionResult]: ...

    def review(self, topic_input: dict[str, Any], assessment: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "", additional_evidence: dict[str, Any] | None = None) -> tuple[dict[str, Any], ExecutionResult]: ...


def _json_checksum(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _expected_raw_output_checksum(
    stage: str,
    topic_input: dict[str, Any],
    assessment: dict[str, Any],
    decision: dict[str, Any],
    enrichment_proposal: dict[str, Any] | None = None,
) -> str:
    """Reconstruct the synthetic runtime payload before provenance normalization."""
    if stage == "ENRICHMENT":
        return _json_checksum(enrichment_proposal or topic_input)
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
    # Reconstruct the provider payload before the application boundary
    # normalized ``provenance.output_checksum``.  The execution layer hashes
    # the runtime-bound payload, while the persisted decision stores the
    # canonical checksum of that payload (which excludes output_checksum).
    raw = copy.deepcopy(decision)
    reviewer_run_id = raw.pop("reviewer_run_id", None)
    provenance = raw.setdefault("provenance", {})
    reviewer_provenance_run_id = provenance.pop("run_id", None)
    pre_runtime_checksum = canonical_checksum(raw, "decision")
    raw["reviewer_run_id"] = reviewer_run_id
    raw["provenance"]["run_id"] = reviewer_provenance_run_id
    raw["provenance"]["output_checksum"] = pre_runtime_checksum
    return _json_checksum(raw)


def _expected_input_manifest_checksum(
    episode_id: str,
    stage: str,
    handoff: dict[str, Any],
    topic_input: dict[str, Any],
    assessment: dict[str, Any],
    additional_evidence: dict[str, Any] | None = None,
) -> str:
    """Rebuild the runtime manifest from the persisted stage inputs."""
    if stage == "ENRICHMENT":
        stage_inputs = [
            ("editorial_intake_handoff", handoff["source_interaction_id"], handoff),
        ]
    elif stage == "PRODUCER":
        stage_inputs = [
            ("topic_belonging_input", topic_input["topic_input_id"], topic_input),
        ]
    elif stage == "REVIEWER":
        stage_inputs = [
            ("topic_belonging_input", topic_input["topic_input_id"], topic_input),
            ("topic_belonging_assessment", assessment["assessment_id"], assessment),
        ]
        if additional_evidence is not None:
            stage_inputs.append(
                (
                    "topic_belonging_reassessment_evidence",
                    additional_evidence["evidence_id"],
                    additional_evidence,
                )
            )
    else:
        raise TopicBelongingExecutionError(f"ROUNDTRIP_STAGE_INVALID:{stage}")
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
        ("user_instructions", "user_instructions"),
    ):
        supplied = bindings.get(handoff_key)
        if supplied not in (None, "", []) and topic_input.get(input_key) != supplied:
            violations.append(f"ENRICHMENT_{input_key.upper()}_MISMATCH")
    for input_key in ("duration_target_minutes", "target_language"):
        if input_key in bindings and topic_input.get(input_key) != bindings.get(input_key):
            violations.append(f"ENRICHMENT_{input_key.upper()}_MISMATCH")
    if topic_input.get("entry_mode") != handoff.get("entry_mode"):
        violations.append("ENRICHMENT_ENTRY_MODE_MISMATCH")
    profile = handoff.get("profile_binding", {})
    for key in ("profile_id", "profile_version", "profile_checksum"):
        if topic_input.get(key) != profile.get(key):
            violations.append(f"ENRICHMENT_{key.upper()}_MISMATCH")
    return violations


def _validate_cognitive_proposal(proposal: dict[str, Any]) -> list[str]:
    return validate_against_schema(proposal, COGNITIVE_PROPOSAL_SCHEMA)


def _validate_cognitive_proposal_binding(proposal: dict[str, Any], handoff: dict[str, Any]) -> list[str]:
    """Reject cognitive claims for protected human-provided fields."""
    bindings = handoff.get("field_bindings", {})
    violations: list[str] = []
    if bindings.get("central_question") and "proposed_central_question" in proposal:
        violations.append("ENRICHMENT_CENTRAL_QUESTION_PROTECTED")
    if handoff.get("entry_mode") == EntryMode.TOPIC_FIRST.value and "proposed_topic" in proposal:
        violations.append("ENRICHMENT_TOPIC_PROTECTED")
    if bindings.get("topic") and "proposed_topic" in proposal:
        violations.append("ENRICHMENT_TOPIC_PROTECTED")
    return violations


def _validate_cognitive_proposal_result(
    proposal: dict[str, Any], topic_input: dict[str, Any]
) -> list[str]:
    """Keep persisted cognitive values bound to the final input they formed."""
    violations: list[str] = []
    for proposal_key, input_key in (
        ("proposed_topic", "topic"),
        ("proposed_angle", "proposed_angle"),
        ("proposed_territory", "proposed_territory"),
        ("initial_evidence", "initial_evidence"),
        ("strategic_triggers", "strategic_triggers"),
        ("proposed_central_question", "central_question"),
    ):
        if proposal_key in proposal and proposal.get(proposal_key) != topic_input.get(input_key):
            violations.append(f"COGNITIVE_PROPOSAL_{proposal_key.upper()}_MISMATCH")
    return violations


def _field_ownership(topic_input: dict[str, Any], handoff: dict[str, Any]) -> dict[str, list[str]]:
    """Record ownership without adding provenance fields to the final contract."""
    bindings = handoff.get("field_bindings", {})
    user_fields = {
        field
        for field in ("topic", "entry_mode", "narrative_work", "corpus_ref", "candidate_work_refs")
        if field in topic_input and bindings.get(field) not in (None, "", [])
    }
    if bindings.get("central_question") not in (None, ""):
        user_fields.add("central_question")
    if bindings.get("user_instructions") not in (None, "", []):
        user_fields.add("user_instructions")
    for field in ("duration_target_minutes", "target_language"):
        if field in topic_input and field in bindings:
            user_fields.add(field)
    ai_fields = {
        field
        for field in (
            "proposed_angle",
            "proposed_territory",
            "initial_evidence",
            "strategic_triggers",
        )
        if field in topic_input
    }
    if "central_question" in topic_input and "central_question" not in user_fields:
        ai_fields.add("central_question")
    if "topic" in topic_input and "topic" not in user_fields:
        ai_fields.add("topic")
    software_fields = set(topic_input) - user_fields - ai_fields
    return {
        "USER_PROVIDED": sorted(user_fields),
        "AI_PROPOSED": sorted(ai_fields),
        "SOFTWARE_OWNED": sorted(software_fields),
    }


def _combine_cognitive_proposal(
    proposal: dict[str, Any],
    handoff: dict[str, Any],
    profile: dict[str, Any],
    episode_id: str,
) -> dict[str, Any]:
    bindings = handoff.get("field_bindings", {})
    topic = bindings.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        if handoff.get("entry_mode") in {EntryMode.ANCHOR_WORK_FIRST.value, EntryMode.CORPUS_FIRST.value}:
            topic = proposal.get("proposed_topic")
        if not isinstance(topic, str) or not topic.strip():
            raise TopicBelongingExecutionError("ENRICHMENT_TOPIC_REQUIRED_FOR_FINAL_CONTRACT")
    central_question = bindings.get("central_question") or proposal.get("proposed_central_question")
    if not isinstance(central_question, str) or not central_question.strip():
        raise TopicBelongingExecutionError("ENRICHMENT_CENTRAL_QUESTION_REQUIRED")
    topic_input = {
        "topic_input_id": f"TBI-{uuid4().hex}",
        "profile_id": profile["ACTIVE_PROFILE_ID"],
        "profile_version": profile["ACTIVE_PROFILE_VERSION"],
        "profile_checksum": profile["profile_checksum"],
        "topic": topic,
        "entry_mode": handoff["entry_mode"],
        "central_question": central_question,
        "proposed_angle": proposal["proposed_angle"],
        "proposed_territory": proposal["proposed_territory"],
        "initial_evidence": proposal["initial_evidence"],
        "strategic_triggers": proposal["strategic_triggers"],
        "submitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "user_instructions": copy.deepcopy(bindings.get("user_instructions", [])),
        "duration_target_minutes": bindings.get("duration_target_minutes"),
        "target_language": bindings.get("target_language"),
    }
    for field_name in ("corpus_ref", "narrative_work", "candidate_work_refs"):
        value = bindings.get(field_name)
        if value not in (None, "", []):
            topic_input[field_name] = copy.deepcopy(value)
    return topic_input


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
        ("user_instructions", "user_instructions"),
        ("duration_target_minutes", "duration_target_minutes"),
        ("target_language", "target_language"),
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
    execution_family: str | None = None
    execution_family_selection_path: str | None = None
    model_override: str | None = None
    reasoning_effort: str | None = None
    paid_cost_approved: bool = False
    execution_registry_path: str | None = None
    operational_authority_path: str | None = None
    mission_contract_path: str | None = None
    completion_gate_result_path: str | None = None
    mission_repo_root: str | None = None
    handoff_directory: Path | None = None
    resolved_mission_id: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.mock_outputs is not None and self.execution_mode != "SYNTHETIC_TEST":
            raise PermissionError("MOCK_OUTPUTS_REQUIRE_SYNTHETIC_TEST_MODE")
        if self.execution_mode == "SYNTHETIC_TEST" and self.execution_profile is None:
            self.execution_profile = "ollama_local"
        if self.execution_mode == "SYNTHETIC_TEST" and self.execution_route is None:
            self.execution_route = "local_model"
        if self.execution_mode == "REAL":
            selection_path = Path(self.execution_family_selection_path) if self.execution_family_selection_path else EXECUTION_FAMILY_SELECTION_PATH
            if selection_path is not None and not selection_path.is_absolute():
                selection_path = self.repository_root / selection_path
            try:
                selected_family = validate_execution_family_selection(
                    self.execution_family,
                    selection_path,
                    requested_profile=self.execution_profile if self.execution_family else None,
                    profiles=load_execution_profiles(self.repository_root / "config/agent_execution_profiles.json"),
                )
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise PermissionError("EXECUTION_FAMILY_SELECTION_INVALID") from exc
            if self.execution_family is None and self.execution_profile is None:
                self.execution_family = selected_family
        if self.execution_family == "AGENT_HARNESS" and self.execution_profile:
            raise PermissionError("AGENT_HARNESS_DOES_NOT_SELECT_PROFILE_EXECUTOR_PROVIDER_OR_MODEL")
        if self.execution_family == "AGENT_HARNESS" and self.execution_route is None:
            self.execution_route = "agent_harness"

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
            bundle = resolve_active_mission_bundle(
                self._operational_authority_path(),
                repository_root=self.repository_root,
            )
            self.mission_authorization_path = bundle.mission_authorization_path
            self.mission_contract_path = bundle.mission_contract_path
        if self.execution_mode == "REAL" and not self.execution_family and not self.execution_profile:
            raise PermissionError("EXECUTION_FAMILY_REQUIRED")
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
                     "mission_id": live_mission_id,
                "execution_interface": self.execution_interface,
                "execution_family": self.execution_family,
                "mission_contract_path": self.mission_contract_path,
                "execution_family_selection_path": self.execution_family_selection_path or str(EXECUTION_FAMILY_SELECTION_PATH),
                "mission_repo_root": self.mission_repo_root or str(self.repository_root),
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
        synthetic_cognitive_executor = None
        synthetic_output_binder = None
        if self.execution_mode == "SYNTHETIC_TEST" and mock_output is not None:
            def synthetic_cognitive_executor(_request: ExecutionRequest) -> dict[str, Any]:
                return copy.deepcopy(mock_output)

            def synthetic_output_binder(
                cognitive_output: dict[str, Any], runtime: dict[str, Any]
            ) -> dict[str, Any]:
                bound = copy.deepcopy(cognitive_output)
                if stage == "produce":
                    bound.setdefault("producer_run_id", runtime["run_id"])
                    bound.setdefault("provenance", {}).setdefault("run_id", runtime["run_id"])
                elif stage == "review":
                    bound.setdefault("reviewer_run_id", runtime["run_id"])
                    bound.setdefault("provenance", {}).setdefault("run_id", runtime["run_id"])
                return bound

        with tempfile.TemporaryDirectory(prefix="topic-belonging-input-") as temp_dir:
            input_artifacts: list[InputArtifact] = []
            for index, (kind, artifact_id, payload, producer_run_id) in enumerate(inputs):
                path = Path(temp_dir) / f"{index}-{kind}.json"
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                input_artifacts.append(InputArtifact(kind, artifact_id, path, producer_run_id))
            convergence_ref = f"roundtrip:{episode_id}:{stage}"
            convergence_callbacks = TopicBelongingTechnicalWorkflow._convergence_callbacks(
                convergence_ref,
                stage=stage,
                output_schema=output_schema,
                inputs=input_artifacts,
                mock_output=mock_output,
            )
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
                execution_family=self.execution_family,
                episode_id=episode_id,
                role=role,
                config={
                    "repository_root": str(self.repository_root),
                    "mission_authorization_path": self.mission_authorization_path,
                    "mission_contract_path": self.mission_contract_path,
                    "completion_gate_result_path": self.completion_gate_result_path,
                    "mission_repo_root": self.mission_repo_root or str(self.repository_root),
                    "execution_profiles_path": str(
                        (self.repository_root / "config/agent_execution_profiles.json").resolve()
                    ),
                    "execution_registry_path": self.execution_registry_path,
                     "mission_operation": "EXECUTE_CAPABILITY",
                     "mission_id": self.resolved_mission_id or "UNRESOLVED_MISSION",
                    "execution_interface": self.execution_interface,
                    "execution_family": self.execution_family,
                    "execution_family_selection_path": self.execution_family_selection_path or str(EXECUTION_FAMILY_SELECTION_PATH),
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
                     "stage": {"enrich": "ENRICHMENT", "produce": "PRODUCER", "review": "REVIEWER"}[stage],
                     "expected_return": output_schema,
                     "convergence_callbacks": convergence_callbacks,
                     "_synthetic_cognitive_executor": synthetic_cognitive_executor,
                     "_synthetic_output_binder": synthetic_output_binder,
                  },
                 handoff_directory=self.handoff_directory,
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
        if result.status is ExecutionStatus.HANDOFF_PREPARED:
            return None, result
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
        output_id = f"PROPOSAL-{uuid4().hex}"
        if isinstance(output, dict):
            output_id = str(output.get("proposal_id") or output_id)
        return self._run(
            stage="enrich",
            role=PRODUCER_ROLE,
            output_schema=COGNITIVE_PROPOSAL_SCHEMA,
            output_kind=COGNITIVE_PROPOSAL_SCHEMA,
            output_id=output_id,
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
        if output is not None:
            output = copy.deepcopy(output)
            # The final input identity is software-owned; a synthetic fixture
            # cannot choose a different input artifact for the producer stage.
            output["topic_input_id"] = topic_input["topic_input_id"]
            output["artifact_checksum"] = canonical_checksum(output, "assessment")
            output.setdefault("provenance", {})["output_checksum"] = output["artifact_checksum"]
        return self._run(
            stage="produce",
            role=PRODUCER_ROLE,
            output_schema=(
                "topic_belonging_cognitive_assessment"
                if self.execution_mode == "REAL"
                else "topic_belonging_assessment"
            ),
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

    def review(self, topic_input: dict[str, Any], assessment: dict[str, Any], profile: dict[str, Any], episode_id: str, *, input_producer_run_id: str = "", additional_evidence: dict[str, Any] | None = None) -> tuple[dict[str, Any], ExecutionResult]:
        output = self.mock_outputs.get("review") if self.mock_outputs is not None else None
        if output is not None:
            output = copy.deepcopy(output)
            output["producer_artifact_checksum"] = assessment["artifact_checksum"]
            output["reviewer_input_checksum"] = assessment["artifact_checksum"]
            if isinstance(output.get("provenance"), dict):
                output["provenance"]["input_checksum"] = assessment["artifact_checksum"]
            if isinstance(output.get("provenance"), dict):
                output["provenance"]["output_checksum"] = canonical_checksum(output, "decision")
        review_inputs = [
            ("topic_belonging_input", topic_input["topic_input_id"], topic_input, input_producer_run_id),
            ("topic_belonging_assessment", assessment["assessment_id"], assessment, assessment["producer_run_id"]),
        ]
        if additional_evidence is not None:
            review_inputs.append(
                (
                    "topic_belonging_reassessment_evidence",
                    additional_evidence["evidence_id"],
                    additional_evidence,
                    "",
                )
            )
        return self._run(
            stage="review",
            role=REVIEWER_ROLE,
            output_schema=(
                "topic_belonging_cognitive_decision"
                if self.execution_mode == "REAL"
                else "topic_belonging_decision"
            ),
            output_kind="topic_belonging_decision",
            output_id=str((output or {}).get("decision_id") or f"TBD-{uuid4().hex}"),
            episode_id=episode_id,
            inputs=review_inputs,
            mock_output=output,
            role_input_payload={
                "TopicBelongingInput": topic_input,
                "TopicBelongingAssessment": assessment,
                "active_editorial_profile": profile,
                **({"additional_topic_belonging_evidence": additional_evidence} if additional_evidence is not None else {}),
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
        cognitive_proposal, enrich_result = self.boundary.enrich(handoff, human_input, profile, handle.episode_id)
        if enrich_result.status is ExecutionStatus.HANDOFF_PREPARED:
            return self._pending_handoff_state(handle, run_id, enrich_result, "ENRICHMENT")
        enrichment_violations = _validate_cognitive_proposal(cognitive_proposal)
        if enrichment_violations:
            raise TopicBelongingExecutionError("COGNITIVE_PROPOSAL_INVALID: " + "; ".join(enrichment_violations))
        enrichment_violations = _validate_cognitive_proposal_binding(cognitive_proposal, handoff)
        if enrichment_violations:
            raise TopicBelongingExecutionError("COGNITIVE_PROPOSAL_INVALID: " + "; ".join(enrichment_violations))
        topic_input = _combine_cognitive_proposal(cognitive_proposal, handoff, profile, handle.episode_id)
        enrichment_violations = _validate_enrichment_binding(topic_input, handoff)
        if enrichment_violations:
            raise TopicBelongingExecutionError("ENRICHMENT_INVALID: " + "; ".join(enrichment_violations))
        input_violations = validate_topic_input(topic_input)
        if input_violations:
            raise TopicBelongingExecutionError("TOPIC_INPUT_INVALID: " + "; ".join(input_violations))

        assessment, producer_result = self.boundary.produce(topic_input, profile, handle.episode_id, input_producer_run_id=enrich_result.run_id)
        if producer_result.status is ExecutionStatus.HANDOFF_PREPARED:
            return self._pending_handoff_state(handle, run_id, producer_result, "PRODUCER")
        assessment_violations = validate_assessment(assessment, topic_input)
        if assessment_violations:
            raise TopicBelongingExecutionError("ASSESSMENT_INVALID: " + "; ".join(assessment_violations))
        if assessment.get("producer_actor_id") != assessment.get("provenance", {}).get("actor_id"):
            raise TopicBelongingExecutionError("ASSESSMENT_INVALID: PRODUCER_ACTOR_PROVENANCE_MISMATCH")

        decision, reviewer_result = self.boundary.review(topic_input, assessment, profile, handle.episode_id, input_producer_run_id=enrich_result.run_id)
        if reviewer_result.status is ExecutionStatus.HANDOFF_PREPARED:
            return self._pending_handoff_state(handle, run_id, reviewer_result, "REVIEWER")
        if producer_result.run_id == reviewer_result.run_id:
            raise TopicBelongingExecutionError("EXECUTION_INDEPENDENCE_INVALID:SAME_RUNTIME_RUN_ID")
        if self.boundary.execution_mode == "REAL":
            producer_executor = assessment.get("provenance", {}).get("executor_identity")
            reviewer_executor = decision.get("provenance", {}).get("executor_identity")
            if not producer_executor or not reviewer_executor or producer_executor == reviewer_executor:
                raise TopicBelongingExecutionError("EXECUTION_INDEPENDENCE_INVALID:EXECUTOR_IDENTITY")
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
            "field_ownership": _field_ownership(topic_input, handoff),
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
                artifact_ref=f"topic_belonging_input:{topic_input['topic_input_id']}",
                cognitive_proposal=cognitive_proposal,
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
    def _build_stop_state(
        handle: EpisodeHandle,
        run_id: str,
        gate: dict[str, Any],
        decision: dict[str, Any],
        *,
        decision_binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = {
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
        if decision_binding is not None:
            state.update(
                {
                    "effective_decision_ref": decision_binding["decision_ref"],
                    "effective_decision_checksum": decision_binding["decision_checksum"],
                    "effective_decision_source_attempt": decision_binding["source_attempt"],
                }
            )
        return state

    @staticmethod
    def _pending_handoff_state(
        handle: EpisodeHandle,
        run_id: str,
        result: ExecutionResult,
        stage: str,
    ) -> dict[str, Any]:
        package_path = Path(str(result.usage.get("package") or ""))
        if not package_path.is_file():
            raise TopicBelongingExecutionError("HANDOFF_PACKAGE_MISSING")
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TopicBelongingExecutionError(f"HANDOFF_PACKAGE_INVALID:{exc}") from exc
        return {
            "workflow_id": "P2_TOPIC_BELONGING_ROUNDTRIP",
            "status": "PENDING_EXTERNAL_RESULT",
            "episode_id": handle.episode_id,
            "run_id": run_id,
            "stage": stage,
            "role": package.get("role"),
            "handoff_id": package.get("handoff_id"),
            "handoff_package_ref": str(package_path),
            "handoff_package_checksum": package.get("package_checksum"),
            "expected_return": package.get("expected_return") or package.get("output_schema"),
            "execution_family": package.get("execution_family"),
            "execution_route": package.get("execution_route"),
            "execution_profile": package.get("execution_profile"),
            "model_override": package.get("model_override"),
            "completed_stages": [],
            "next_stage": stage,
            "real_cognitive_execution": "NOT_DEMONSTRATED",
            "fixture_policy": "TEST_FIXTURE_ONLY",
            "downstream_execution_started": False,
        }

    def import_result(self, handle: EpisodeHandle, result_path: Path) -> dict[str, Any]:
        """Validate and persist the result for the currently pending stage."""
        workflow = self._read_episode_file(handle, "workflow_state.json")
        try:
            raw_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_INVALID:{exc}") from exc
        results_index = self._read_episode_file(handle, ROUNDTRIP_RESULTS_FILENAME)
        existing = next(
            (item for item in results_index.get("results", []) if item.get("handoff_id") == raw_payload.get("handoff_id")),
            None,
        )
        if existing is not None:
            identity_fields = (
                "mission_id",
                "episode_id",
                "capability_id",
                "stage",
                "role",
                "handoff_id",
                "package_checksum",
                "output_checksum",
                "result_run_id",
            )
            if all(existing.get(field) == raw_payload.get(field) for field in identity_fields):
                stored_package_path = Path(str(existing.get("handoff_package_ref") or ""))
                if not stored_package_path.is_file():
                    raise TopicBelongingExecutionError("HANDOFF_PACKAGE_MISSING: persisted duplicate")
                try:
                    package = json.loads(stored_package_path.read_text(encoding="utf-8"))
                    self._validate_result_provenance_bindings(package, raw_payload)
                    content = AgentHandoffProvider().import_result(stored_package_path, result_path)
                    if package.get("stage") == "ENRICHMENT":
                        self._read_materialized_enrichment_input(
                            handle,
                            existing,
                            package,
                            content,
                        )
                except TopicBelongingExecutionError as exc:
                    raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_BLOCKED:{exc}") from exc
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, PermissionError, ValueError) as exc:
                    raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_BLOCKED:{exc}") from exc
                return {"status": "ALREADY_IMPORTED", "episode_id": handle.episode_id, "handoff_id": raw_payload.get("handoff_id")}
            raise TopicBelongingExecutionError("ROUNDTRIP_RESULT_CONFLICT: imported handoff already has another result")
        package_path = Path(str(workflow.get("handoff_package_ref") or ""))
        if not package_path.is_file():
            raise TopicBelongingExecutionError("HANDOFF_PACKAGE_MISSING")
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TopicBelongingExecutionError(f"HANDOFF_PACKAGE_INVALID:{exc}") from exc
        expected_bindings = {
            "mission_id": self._mission_id,
            "episode_id": handle.episode_id,
            "capability_id": CAPABILITY_ID,
            "stage": workflow.get("stage"),
            "role": workflow.get("role"),
            "handoff_id": workflow.get("handoff_id"),
            "package_checksum": workflow.get("handoff_package_checksum"),
        }
        actual_bindings = {
            "mission_id": package.get("mission_id"),
            "episode_id": package.get("episode_id"),
            "capability_id": package.get("capability_id"),
            "stage": package.get("stage"),
            "role": package.get("role"),
            "handoff_id": package.get("handoff_id"),
            "package_checksum": package.get("package_checksum"),
        }
        if workflow.get("status") != "PENDING_EXTERNAL_RESULT":
            raise TopicBelongingExecutionError("ROUNDTRIP_IMPORT_BLOCKED:NO_PENDING_HANDOFF")
        if any(actual_bindings[key] != expected for key, expected in expected_bindings.items()):
            raise TopicBelongingExecutionError("ROUNDTRIP_CHECKPOINT_BINDING_INVALID")
        self._validate_result_provenance_bindings(package, raw_payload)
        try:
            content = AgentHandoffProvider().import_result(package_path, result_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, PermissionError, ValueError) as exc:
            prefix = "COGNITIVE_PROPOSAL_INVALID" if package.get("stage") == "ENRICHMENT" else "ROUNDTRIP_RESULT_BLOCKED"
            raise TopicBelongingExecutionError(f"{prefix}:{exc}") from exc
        if not isinstance(content, dict):
            raise TopicBelongingExecutionError("ROUNDTRIP_RESULT_OUTPUT_INVALID")
        stage = str(package.get("stage") or "")
        result_run_id = str(raw_payload.get("result_run_id") or "")
        materialized_output = None
        if stage == "ENRICHMENT":
            materialized_output = self._materialize_enrichment_input(handle, package, content)
            next_stage = "PRODUCER"
        elif stage == "PRODUCER":
            materialized_output = self._materialize_producer_assessment(
                handle,
                package,
                content,
                result_run_id,
                raw_payload.get("provenance", {}),
            )
            next_stage = "REVIEWER"
        elif stage == "REVIEWER":
            topic_input = self._read_roundtrip_output(handle, "ENRICHMENT")
            assessment = self._read_roundtrip_output(handle, "PRODUCER")
            additional_evidence = self._read_reassessment_for_workflow(handle, workflow)
            materialized_output = self._materialize_reviewer_decision(
                handle,
                package,
                content,
                result_run_id,
                assessment,
                raw_payload.get("provenance", {}),
                additional_evidence,
            )
            violations = validate_decision(materialized_output, assessment)
            if materialized_output.get("reviewer_run_id") != result_run_id or materialized_output.get("provenance", {}).get("run_id") != result_run_id:
                violations.append("REVIEWER_RESULT_RUN_BINDING_INVALID")
            if materialized_output.get("reviewer_run_id") == assessment.get("producer_run_id"):
                violations.append("PRODUCER_REVIEWER_INDEPENDENCE_INVALID")
            producer_executor = assessment.get("provenance", {}).get("executor_identity")
            reviewer_executor = raw_payload.get("provenance", {}).get("executor_identity")
            if not producer_executor or not reviewer_executor or producer_executor == reviewer_executor:
                violations.append("PRODUCER_REVIEWER_EXECUTOR_INDEPENDENCE_INVALID")
            if violations:
                raise TopicBelongingExecutionError("DECISION_INVALID: " + "; ".join(violations))
            next_stage = "FINALIZE"
        else:
            raise TopicBelongingExecutionError("ROUNDTRIP_STAGE_INVALID")

        completed = list(workflow.get("completed_stages", []))
        if stage not in completed:
            completed.append(stage)
        persisted_state = {
            "workflow_id": "P2_TOPIC_BELONGING_ROUNDTRIP",
            "status": "PERSISTED",
            "episode_id": handle.episode_id,
            "run_id": workflow.get("run_id"),
            "stage": stage,
            "role": package.get("role"),
            "handoff_id": package.get("handoff_id"),
            "handoff_package_ref": str(package_path),
            "handoff_package_checksum": package.get("package_checksum"),
            "result_run_id": result_run_id,
            "result_checksum": raw_payload.get("output_checksum"),
            "completed_stages": completed,
            "next_stage": next_stage,
            "real_cognitive_execution": "NOT_DEMONSTRATED",
            "fixture_policy": "TEST_FIXTURE_ONLY",
            "downstream_execution_started": False,
        }
        for key in ("reassessment_id", "attempt_number", "prior_decision_checksum"):
            if key in workflow:
                persisted_state[key] = workflow[key]
        status = self.store.record_roundtrip_result(
            handle,
            envelope=raw_payload,
            workflow_state=persisted_state,
            materialized_output=materialized_output,
        )
        if status == "ALREADY_IMPORTED":
            return {"status": status, "episode_id": handle.episode_id, "handoff_id": package.get("handoff_id")}
        return persisted_state

    @staticmethod
    def _validate_result_provenance_bindings(
        package: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        """Apply the same complete envelope rule to first and duplicate imports."""
        required_result_bindings = (
            "mission_id",
            "episode_id",
            "capability_id",
            "stage",
            "role",
            "handoff_id",
            "package_checksum",
            "input_manifest_checksum",
            "skill_id",
            "skill_version",
            "result_run_id",
            "output_checksum",
        )
        if any(not str(payload.get(field) or "") for field in required_result_bindings):
            raise TopicBelongingExecutionError("ROUNDTRIP_RESULT_BINDING_INCOMPLETE")
        if any(
            payload.get(field) != package.get(field)
            for field in (
                "mission_id", "episode_id", "capability_id", "stage", "role",
                "handoff_id", "package_checksum", "input_manifest_checksum", "skill_id", "skill_version",
            )
        ):
            raise TopicBelongingExecutionError("ROUNDTRIP_RESULT_PACKAGE_BINDING_INVALID")
        provenance = payload.get("provenance")
        if not isinstance(provenance, dict) or any(
            provenance.get(field) != package.get(field)
            for field in ("mission_id", "episode_id", "capability_id", "stage", "role")
        ) or provenance.get("run_id") != payload.get("result_run_id"):
            raise TopicBelongingExecutionError("ROUNDTRIP_RESULT_PROVENANCE_BINDING_INVALID")
        if package.get("output_schema") in {
            "topic_belonging_cognitive_proposal",
            "topic_belonging_cognitive_assessment",
            "topic_belonging_cognitive_decision",
        } and not str(provenance.get("executor_identity") or "").strip():
            raise TopicBelongingExecutionError("EXTERNAL_EXECUTOR_IDENTITY_REQUIRED")

    @staticmethod
    def _convergence_callbacks(
        convergence_ref: str,
        *,
        stage: str,
        output_schema: str,
        inputs: list[InputArtifact],
        mock_output: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Bound reduced convergence to handoff structure; never to cognition."""
        def implement() -> dict[str, Any]:
            passed = output_schema in {
                COGNITIVE_PROPOSAL_SCHEMA,
                "topic_belonging_input",
                "topic_belonging_cognitive_assessment",
                "topic_belonging_cognitive_decision",
            }
            return {
                "passed": passed,
                "evidence": [{"kind": "ROUNDTRIP_HANDOFF_IMPLEMENTATION", "ref": convergence_ref}],
                **({"reason": "UNSUPPORTED_ROUNDTRIP_OUTPUT_SCHEMA"} if not passed else {}),
            }

        def verify() -> dict[str, Any]:
            passed = (
                mock_output is None
                and stage in {"enrich", "produce", "review"}
                and bool(inputs)
                and all(item.path.is_file() and bool(item.artifact_id) for item in inputs)
            )
            return {
                "passed": passed,
                "evidence": [{"kind": "ROUNDTRIP_HANDOFF_VERIFICATION", "ref": convergence_ref}],
                **({"reason": "HANDOFF_INPUT_BOUNDARY_INVALID"} if not passed else {}),
            }

        def adversarial_review() -> dict[str, Any]:
            passed = stage in {"enrich", "produce", "review"} and output_schema.startswith("topic_belonging_")
            return {
                "passed": passed,
                "evidence": [{"kind": "ROUNDTRIP_HANDOFF_SELF_REVIEW", "ref": convergence_ref}],
                **({"reason": "ROUNDTRIP_BOUNDARY_SELF_REVIEW_FAILED"} if not passed else {}),
            }

        def repair(finding: dict[str, Any]) -> dict[str, Any]:
            return {
                "passed": False,
                "evidence": [{"kind": "ROUNDTRIP_HANDOFF_REPAIR", "ref": convergence_ref}],
                "reason": f"ROUNDTRIP_REPAIR_NOT_AUTOMATIC:{finding.get('stage', 'UNKNOWN')}",
            }

        return {
            "implement": implement,
            "verify": verify,
            "adversarial_review": adversarial_review,
            "repair": repair,
        }

    def _roundtrip_record_for_stage(self, handle: EpisodeHandle, stage: str) -> dict[str, Any] | None:
        results = self._read_episode_file(handle, ROUNDTRIP_RESULTS_FILENAME).get("results", [])
        workflow = self._read_episode_file(handle, "workflow_state.json")
        current_handoff = workflow.get("handoff_id")
        record = next(
            (
                item
                for item in reversed(results)
                if item.get("stage") == stage and (
                    not current_handoff or item.get("handoff_id") == current_handoff
                )
            ),
            None,
        )
        if record is None:
            record = next((item for item in reversed(results) if item.get("stage") == stage), None)
        return record if isinstance(record, dict) else None

    def _read_roundtrip_output(self, handle: EpisodeHandle, stage: str) -> dict[str, Any]:
        record = self._roundtrip_record_for_stage(handle, stage)
        if not isinstance(record, dict):
            raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_MISSING:{stage}")
        package, envelope, output = self._revalidate_roundtrip_record(handle, record)
        if stage == "ENRICHMENT":
            output = self._read_materialized_enrichment_input(handle, record, package, output)
            violations = validate_topic_input(output)
        elif stage == "PRODUCER":
            output = self._read_materialized_producer_assessment(handle, record, package, output)
            violations = validate_assessment(output, self._read_roundtrip_output(handle, "ENRICHMENT"))
        elif stage == "REVIEWER":
            output = self._read_materialized_reviewer_decision(
                handle,
                record,
                package,
                output,
                self._read_roundtrip_output(handle, "PRODUCER"),
            )
            violations = validate_decision(output, self._read_roundtrip_output(handle, "PRODUCER"))
        else:
            violations = ["ROUNDTRIP_STAGE_INVALID"]
        if violations:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_PERSISTED_OUTPUT_INVALID:{stage}:" + ";".join(violations))
        if package.get("stage") != stage or envelope.get("stage") != stage:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_PERSISTED_STAGE_INVALID:{stage}")
        return output

    def _enrichment_source_context(
        self,
        handle: EpisodeHandle,
        package: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Resolve the persisted intake and active profile for enrichment."""
        human_input_data = self._read_episode_file(handle, "00_human_input.json")
        handoff = self._read_episode_file(handle, "01_editorial_intake_handoff.json")
        if not human_input_data or not handoff:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_MISSING")
        try:
            human_input = HumanInput.from_dict(human_input_data)
        except (TypeError, ValueError) as exc:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_INVALID") from exc
        handoff_violations = _validate_human_handoff_binding(human_input.to_dict(), handoff)
        if handoff_violations:
            raise TopicBelongingExecutionError(
                "HANDOFF_INVALID: " + "; ".join(handoff_violations)
            )
        expected_manifest = _expected_input_manifest_checksum(
            handle.episode_id,
            "ENRICHMENT",
            handoff,
            {},
            {},
        )
        if package.get("input_manifest_checksum") != expected_manifest:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_STALE")
        profile = self.profile_loader()
        profile_binding = handoff.get("profile_binding", {})
        expected_profile = {
            "profile_id": profile.get("ACTIVE_PROFILE_ID"),
            "profile_version": profile.get("ACTIVE_PROFILE_VERSION"),
            "profile_checksum": profile.get("profile_checksum"),
        }
        if any(profile_binding.get(key) != value for key, value in expected_profile.items()):
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_PROFILE_STALE")
        return handoff, profile

    def _materialize_enrichment_input(
        self,
        handle: EpisodeHandle,
        package: dict[str, Any],
        proposal: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine an external proposal with software-owned persisted inputs."""
        handoff, profile = self._enrichment_source_context(handle, package)
        proposal_violations = _validate_cognitive_proposal(proposal)
        proposal_violations.extend(_validate_cognitive_proposal_binding(proposal, handoff))
        if proposal_violations:
            raise TopicBelongingExecutionError(
                "COGNITIVE_PROPOSAL_INVALID: " + "; ".join(proposal_violations)
            )
        topic_input = _combine_cognitive_proposal(
            proposal,
            handoff,
            profile,
            handle.episode_id,
        )
        violations = _validate_enrichment_binding(topic_input, handoff)
        violations.extend(validate_topic_input(topic_input))
        if violations:
            raise TopicBelongingExecutionError("ENRICHMENT_INVALID: " + "; ".join(violations))
        return topic_input

    def _read_materialized_enrichment_input(
        self,
        handle: EpisodeHandle,
        record: dict[str, Any],
        package: dict[str, Any],
        proposal: dict[str, Any],
    ) -> dict[str, Any]:
        """Read and revalidate the software-owned enrichment envelope."""
        handoff, _ = self._enrichment_source_context(handle, package)
        proposal_violations = _validate_cognitive_proposal(proposal)
        proposal_violations.extend(_validate_cognitive_proposal_binding(proposal, handoff))
        if proposal_violations:
            raise TopicBelongingExecutionError(
                "COGNITIVE_PROPOSAL_INVALID: " + "; ".join(proposal_violations)
            )
        materialized_ref = str(record.get("materialized_output_path") or "")
        if not materialized_ref:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_MISSING")
        materialized_path = (handle.folder / materialized_ref).resolve()
        try:
            materialized_path.relative_to(handle.folder.resolve())
            materialized = json.loads(materialized_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_MISSING") from exc
        if not isinstance(materialized, dict):
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_INVALID")
        if hashlib.sha256(materialized_path.read_bytes()).hexdigest() != record.get("materialized_output_checksum"):
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_STALE")
        violations = _validate_enrichment_binding(materialized, handoff)
        violations.extend(_validate_cognitive_proposal_result(proposal, materialized))
        violations.extend(validate_topic_input(materialized))
        if violations:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_INVALID: " + "; ".join(violations))
        return materialized

    def _materialize_producer_assessment(
        self,
        handle: EpisodeHandle,
        package: dict[str, Any],
        cognitive_assessment: dict[str, Any],
        result_run_id: str,
        external_provenance: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the assessment envelope from canonical input and cognition."""
        topic_input = self._read_roundtrip_output(handle, "ENRICHMENT")
        unknown_fields = set(cognitive_assessment) - COGNITIVE_ASSESSMENT_FIELDS
        missing_fields = COGNITIVE_ASSESSMENT_FIELDS - set(cognitive_assessment)
        if unknown_fields or missing_fields:
            details = []
            if unknown_fields:
                details.append("RESERVED_FIELDS:" + ",".join(sorted(unknown_fields)))
            if missing_fields:
                details.append("COGNITIVE_FIELDS_MISSING:" + ",".join(sorted(missing_fields)))
            raise TopicBelongingExecutionError("COGNITIVE_ASSESSMENT_INVALID: " + "; ".join(details))
        if cognitive_assessment["strategic_triggers"] != topic_input["strategic_triggers"]:
            raise TopicBelongingExecutionError("COGNITIVE_ASSESSMENT_INPUT_BINDING_INVALID: strategic_triggers")
        if cognitive_assessment["status"] != "CLOSED_FOR_REVIEW":
            raise TopicBelongingExecutionError("COGNITIVE_ASSESSMENT_INVALID: status")
        expected_manifest = _expected_input_manifest_checksum(
            handle.episode_id,
            "PRODUCER",
            self._read_episode_file(handle, "01_editorial_intake_handoff.json"),
            topic_input,
            {},
        )
        if package.get("input_manifest_checksum") != expected_manifest:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_STALE")
        assessment = {
            "assessment_id": f"TBA-{uuid4().hex}",
            "strategic_triggers": copy.deepcopy(topic_input["strategic_triggers"]),
            "topic_input_id": topic_input["topic_input_id"],
            "producer_actor_id": EXTERNAL_PRODUCER_ACTOR_ID,
            "producer_run_id": result_run_id,
            "producer_role_id": PRODUCER_ROLE,
            "profile_id": topic_input["profile_id"],
            "profile_version": topic_input["profile_version"],
            "profile_checksum": topic_input["profile_checksum"],
            "topic": topic_input["topic"],
            "entry_mode": topic_input["entry_mode"],
            "central_question": topic_input["central_question"],
            "proposed_angle": topic_input["proposed_angle"],
            "proposed_territory": topic_input["proposed_territory"],
            "initial_evidence": copy.deepcopy(topic_input["initial_evidence"]),
            **{
                key: copy.deepcopy(cognitive_assessment[key])
                for key in COGNITIVE_ASSESSMENT_FIELDS
                if key != "strategic_triggers"
            },
            "status": "CLOSED_FOR_REVIEW",
            "artifact_checksum": "",
            "provenance": {
                "actor_id": EXTERNAL_PRODUCER_ACTOR_ID,
                "run_id": result_run_id,
                "role_id": PRODUCER_ROLE,
                "input_checksums": [canonical_checksum(topic_input, "input")],
                "output_checksum": "",
                "executor_identity": external_provenance.get("executor_identity"),
                **{
                    key: external_provenance[key]
                    for key in ("provider", "model", "session_id")
                    if external_provenance.get(key)
                },
            },
        }
        for field_name in ("corpus_ref", "narrative_work"):
            if field_name in topic_input:
                assessment[field_name] = copy.deepcopy(topic_input[field_name])
        checksum = canonical_checksum(assessment, "assessment")
        assessment["artifact_checksum"] = checksum
        assessment["provenance"]["output_checksum"] = checksum
        violations = validate_assessment(assessment, topic_input)
        if violations:
            raise TopicBelongingExecutionError("ASSESSMENT_INVALID: " + "; ".join(violations))
        return assessment

    def _read_materialized_producer_assessment(
        self,
        handle: EpisodeHandle,
        record: dict[str, Any],
        package: dict[str, Any],
        cognitive_assessment: dict[str, Any],
    ) -> dict[str, Any]:
        """Read and verify the persisted software-owned assessment envelope."""
        materialized_ref = str(record.get("materialized_output_path") or "")
        if not materialized_ref:
            raise TopicBelongingExecutionError("ROUNDTRIP_ASSESSMENT_CANONICAL_MISSING")
        materialized_path = (handle.folder / materialized_ref).resolve()
        try:
            materialized_path.relative_to(handle.folder.resolve())
            materialized = json.loads(materialized_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise TopicBelongingExecutionError("ROUNDTRIP_ASSESSMENT_CANONICAL_MISSING") from exc
        if not isinstance(materialized, dict):
            raise TopicBelongingExecutionError("ROUNDTRIP_ASSESSMENT_CANONICAL_INVALID")
        if hashlib.sha256(materialized_path.read_bytes()).hexdigest() != record.get("materialized_output_checksum"):
            raise TopicBelongingExecutionError("ROUNDTRIP_ASSESSMENT_CANONICAL_STALE")
        unknown_fields = set(cognitive_assessment) - COGNITIVE_ASSESSMENT_FIELDS
        if unknown_fields:
            raise TopicBelongingExecutionError(
                "COGNITIVE_ASSESSMENT_INVALID: RESERVED_FIELDS:" + ",".join(sorted(unknown_fields))
            )
        for field in COGNITIVE_ASSESSMENT_FIELDS:
            if materialized.get(field) != cognitive_assessment.get(field):
                raise TopicBelongingExecutionError(
                    f"ROUNDTRIP_ASSESSMENT_COGNITIVE_BINDING_INVALID:{field}"
                )
        topic_input = self._read_roundtrip_output(handle, "ENRICHMENT")
        expected_manifest = _expected_input_manifest_checksum(
            handle.episode_id,
            "PRODUCER",
            self._read_episode_file(handle, "01_editorial_intake_handoff.json"),
            topic_input,
            {},
        )
        if package.get("input_manifest_checksum") != expected_manifest:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_STALE")
        violations = validate_assessment(materialized, topic_input)
        if violations:
            raise TopicBelongingExecutionError("ROUNDTRIP_ASSESSMENT_CANONICAL_INVALID: " + "; ".join(violations))
        return materialized

    def _read_reassessment_for_workflow(
        self,
        handle: EpisodeHandle,
        workflow: dict[str, Any],
    ) -> dict[str, Any] | None:
        reassessment_id = workflow.get("reassessment_id")
        if not reassessment_id:
            return None
        return self._read_reassessment(handle, str(reassessment_id))

    def _read_reassessment_for_package(
        self,
        handle: EpisodeHandle,
        package: dict[str, Any],
    ) -> dict[str, Any] | None:
        artifacts = package.get("input_manifest", {}).get("artifacts", [])
        evidence_id = next(
            (
                item.get("artifact_id")
                for item in artifacts
                if item.get("artifact_kind") == "topic_belonging_reassessment_evidence"
            ),
            None,
        )
        return self._read_reassessment(handle, str(evidence_id)) if evidence_id else None

    def _read_reassessment(self, handle: EpisodeHandle, reassessment_id: str) -> dict[str, Any]:
        try:
            data = self._read_episode_file(handle, "topic_belonging_reassessments.json")
            record = next(
                item for item in data.get("reassessments", [])
                if item.get("reassessment_id") == reassessment_id or item.get("evidence_id") == reassessment_id
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StopIteration, AttributeError) as exc:
            raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_MISSING") from exc
        return record

    @staticmethod
    def _episode_artifact_binding(handle: EpisodeHandle, relative_path: str) -> dict[str, str]:
        path = (handle.folder / relative_path).resolve()
        try:
            path.relative_to(handle.folder.resolve())
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, ValueError) as exc:
            raise TopicBelongingExecutionError("TOPIC_BELONGING_PRIOR_DECISION_REF_INVALID") from exc
        return {
            "decision_ref": f"episode:{handle.episode_id}/{path.relative_to(handle.folder).as_posix()}",
            "decision_checksum": checksum,
        }

    def _effective_decision_binding(self, handle: EpisodeHandle) -> dict[str, Any]:
        """Resolve and verify the immutable decision chain across re-evaluations."""
        original = self._episode_artifact_binding(handle, "04_topic_belonging_decision.json")
        binding: dict[str, Any] = {
            "decision": self._read_episode_file(handle, "04_topic_belonging_decision.json"),
            **original,
            "source_attempt": 1,
        }
        reassessments = self._read_episode_file(handle, "topic_belonging_reassessments.json")
        entries = [
            item for item in reassessments.get("reassessments", [])
            if isinstance(item, dict)
        ]
        attempts: set[int] = set()
        try:
            ordered_entries = sorted(entries, key=lambda item: int(item.get("attempt_number", 0)))
        except (TypeError, ValueError) as exc:
            raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_ATTEMPT_INVALID") from exc
        for record in ordered_entries:
            try:
                attempt = int(record["attempt_number"])
            except (KeyError, TypeError, ValueError) as exc:
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_ATTEMPT_INVALID") from exc
            if attempt in attempts or attempt != binding["source_attempt"] + 1:
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_ATTEMPT_CHAIN_INVALID")
            attempts.add(attempt)
            if (
                record.get("prior_decision_ref") != binding["decision_ref"]
                or record.get("prior_decision_checksum") != binding["decision_checksum"]
            ):
                raise TopicBelongingExecutionError("TOPIC_BELONGING_PRIOR_DECISION_BINDING_INVALID")
            if record.get("status") != "COMPLETED":
                continue
            decision = record.get("decision")
            if not isinstance(decision, dict):
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_DECISION_MISSING")
            if not isinstance(record.get("decision_ref"), str) or not isinstance(record.get("decision_checksum"), str):
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_DECISION_BINDING_MISSING")
            decision_path = record["decision_ref"].split(f"episode:{handle.episode_id}/", 1)
            if len(decision_path) != 2:
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_DECISION_REF_INVALID")
            actual = self._episode_artifact_binding(handle, decision_path[1])
            if actual["decision_ref"] != record["decision_ref"] or actual["decision_checksum"] != record["decision_checksum"]:
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_DECISION_BINDING_INVALID")
            assessment = self._read_episode_file(handle, "03_topic_belonging_assessment.json")
            if validate_decision(decision, assessment):
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_DECISION_INVALID")
            gate = record.get("gate")
            topic_input = self._read_episode_file(handle, "02_topic_belonging_input.json")
            if not isinstance(gate, dict) or gate != evaluate_topic_belonging_gate(decision, assessment, topic_input):
                raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_GATE_INVALID")
            binding = {
                "decision": decision,
                "decision_ref": record["decision_ref"],
                "decision_checksum": record["decision_checksum"],
                "source_attempt": attempt,
            }
        return binding

    def _effective_decision(self, handle: EpisodeHandle) -> dict[str, Any]:
        return self._effective_decision_binding(handle)["decision"]

    def _materialize_reviewer_decision(
        self,
        handle: EpisodeHandle,
        package: dict[str, Any],
        cognitive_decision: dict[str, Any],
        result_run_id: str,
        assessment: dict[str, Any],
        external_provenance: dict[str, Any],
        additional_evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the decision envelope from reviewer cognition and canonical assessment."""
        unknown_fields = set(cognitive_decision) - COGNITIVE_DECISION_FIELDS
        missing_fields = REQUIRED_COGNITIVE_DECISION_FIELDS - set(cognitive_decision)
        if unknown_fields or missing_fields:
            details = []
            if unknown_fields:
                details.append("RESERVED_FIELDS:" + ",".join(sorted(unknown_fields)))
            if missing_fields:
                details.append("COGNITIVE_FIELDS_MISSING:" + ",".join(sorted(missing_fields)))
            raise TopicBelongingExecutionError("COGNITIVE_DECISION_INVALID: " + "; ".join(details))
        expected_manifest = _expected_input_manifest_checksum(
            handle.episode_id,
            "REVIEWER",
            self._read_episode_file(handle, "01_editorial_intake_handoff.json"),
            self._read_roundtrip_output(handle, "ENRICHMENT"),
            assessment,
            additional_evidence,
        )
        if package.get("input_manifest_checksum") != expected_manifest:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_STALE")
        decision = copy.deepcopy(cognitive_decision)
        decision.update(
            {
                "decision_id": f"TBD-{uuid4().hex}",
                "assessment_id": assessment["assessment_id"],
                "profile_id": assessment["profile_id"],
                "profile_version": assessment["profile_version"],
                "profile_checksum": assessment["profile_checksum"],
                "producer_artifact_checksum": assessment["artifact_checksum"],
                "reviewer_actor_id": EXTERNAL_REVIEWER_ACTOR_ID,
                "reviewer_run_id": result_run_id,
                "reviewer_role_id": REVIEWER_ROLE,
                "reviewer_input_checksum": assessment["artifact_checksum"],
                "decided_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "provenance": {
                    "actor_id": EXTERNAL_REVIEWER_ACTOR_ID,
                    "run_id": result_run_id,
                    "role_id": REVIEWER_ROLE,
                    "input_checksum": assessment["artifact_checksum"],
                    "output_checksum": "",
                    "executor_identity": external_provenance.get("executor_identity"),
                    **{
                        key: external_provenance[key]
                        for key in ("provider", "model", "session_id")
                        if external_provenance.get(key)
                    },
                },
            }
        )
        decision["provenance"]["output_checksum"] = canonical_checksum(decision, "decision")
        violations = validate_decision(decision, assessment)
        if violations:
            raise TopicBelongingExecutionError("DECISION_INVALID: " + "; ".join(violations))
        return decision

    def _read_materialized_reviewer_decision(
        self,
        handle: EpisodeHandle,
        record: dict[str, Any],
        package: dict[str, Any],
        cognitive_decision: dict[str, Any],
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        """Read and verify the persisted software-owned decision envelope."""
        materialized_ref = str(record.get("materialized_output_path") or "")
        if not materialized_ref:
            raise TopicBelongingExecutionError("ROUNDTRIP_DECISION_CANONICAL_MISSING")
        materialized_path = (handle.folder / materialized_ref).resolve()
        try:
            materialized_path.relative_to(handle.folder.resolve())
            materialized = json.loads(materialized_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise TopicBelongingExecutionError("ROUNDTRIP_DECISION_CANONICAL_MISSING") from exc
        if not isinstance(materialized, dict):
            raise TopicBelongingExecutionError("ROUNDTRIP_DECISION_CANONICAL_INVALID")
        if hashlib.sha256(materialized_path.read_bytes()).hexdigest() != record.get("materialized_output_checksum"):
            raise TopicBelongingExecutionError("ROUNDTRIP_DECISION_CANONICAL_STALE")
        unknown_fields = set(cognitive_decision) - COGNITIVE_DECISION_FIELDS
        if unknown_fields:
            raise TopicBelongingExecutionError(
                "COGNITIVE_DECISION_INVALID: RESERVED_FIELDS:" + ",".join(sorted(unknown_fields))
            )
        for field in COGNITIVE_DECISION_FIELDS:
            if materialized.get(field) != cognitive_decision.get(field):
                raise TopicBelongingExecutionError(
                    f"ROUNDTRIP_DECISION_COGNITIVE_BINDING_INVALID:{field}"
                )
        additional_evidence = self._read_reassessment_for_package(handle, package)
        expected_manifest = _expected_input_manifest_checksum(
            handle.episode_id,
            "REVIEWER",
            self._read_episode_file(handle, "01_editorial_intake_handoff.json"),
            self._read_roundtrip_output(handle, "ENRICHMENT"),
            assessment,
            additional_evidence,
        )
        if package.get("input_manifest_checksum") != expected_manifest:
            raise TopicBelongingExecutionError("ROUNDTRIP_INPUT_CANONICAL_STALE")
        violations = validate_decision(materialized, assessment)
        if violations:
            raise TopicBelongingExecutionError("ROUNDTRIP_DECISION_CANONICAL_INVALID: " + "; ".join(violations))
        return materialized

    def _revalidate_roundtrip_record(
        self,
        handle: EpisodeHandle,
        record: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Revalidate a stored package/result pair before any resume transition."""
        try:
            result_path = (handle.folder / str(record.get("result_path") or "")).resolve()
            result_path.relative_to(handle.folder.resolve())
            package_path = Path(str(record.get("handoff_package_ref") or "")).resolve(strict=True)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            envelope = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_PERSISTED_ENVELOPE_INVALID:{exc}") from exc
        expected = {
            "mission_id": self._mission_id,
            "episode_id": handle.episode_id,
            "capability_id": CAPABILITY_ID,
            "stage": record.get("stage"),
            "role": record.get("role"),
            "handoff_id": record.get("handoff_id"),
            "package_checksum": record.get("package_checksum"),
            "input_manifest_checksum": record.get("input_manifest_checksum"),
            "skill_id": record.get("skill_id"),
            "skill_version": record.get("skill_version"),
            "result_run_id": record.get("result_run_id"),
            "output_checksum": record.get("output_checksum"),
        }
        actual = {
            "mission_id": envelope.get("mission_id"),
            "episode_id": envelope.get("episode_id"),
            "capability_id": envelope.get("capability_id"),
            "stage": envelope.get("stage"),
            "role": envelope.get("role"),
            "handoff_id": envelope.get("handoff_id"),
            "package_checksum": envelope.get("package_checksum"),
            "input_manifest_checksum": envelope.get("input_manifest_checksum"),
            "skill_id": envelope.get("skill_id"),
            "skill_version": envelope.get("skill_version"),
            "result_run_id": envelope.get("result_run_id"),
            "output_checksum": envelope.get("output_checksum"),
        }
        expected_role = {
            "ENRICHMENT": PRODUCER_ROLE,
            "PRODUCER": PRODUCER_ROLE,
            "REVIEWER": REVIEWER_ROLE,
        }.get(str(record.get("stage") or ""))
        if expected_role is None or package.get("role") != expected_role:
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_PACKAGE_ROLE_INVALID")
        package_identity = {
            "mission_id": package.get("mission_id"),
            "episode_id": package.get("episode_id"),
            "capability_id": package.get("capability_id"),
            "stage": package.get("stage"),
            "role": package.get("role"),
            "handoff_id": package.get("handoff_id"),
            "package_checksum": package.get("package_checksum"),
            "input_manifest_checksum": package.get("input_manifest_checksum"),
            "skill_id": package.get("skill_id"),
            "skill_version": package.get("skill_version"),
        }
        if any(expected.get(key) != value for key, value in package_identity.items()):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_CHECKPOINT_BINDING_INVALID")
        if any(actual[key] != value for key, value in expected.items()):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_ENVELOPE_BINDING_INVALID")
        provenance = envelope.get("provenance")
        if not isinstance(provenance, dict) or any(
            provenance.get(key) != package_identity[key]
            for key in ("mission_id", "episode_id", "capability_id", "stage", "role")
        ) or provenance.get("run_id") != envelope.get("result_run_id"):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_PROVENANCE_INVALID")
        try:
            output = AgentHandoffProvider().import_result(package_path, result_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, PermissionError, ValueError) as exc:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_PERSISTED_ENVELOPE_INVALID:{exc}") from exc
        if not isinstance(output, dict):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_OUTPUT_INVALID")
        return package, envelope, output

    def _roundtrip_result_run_id(self, handle: EpisodeHandle, stage: str) -> str:
        record = self._roundtrip_record_for_stage(handle, stage)
        result_run_id = record.get("result_run_id") if isinstance(record, dict) else None
        if not result_run_id:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_RUN_ID_MISSING:{stage}")
        return str(result_run_id)

    def submit_additional_evidence(
        self,
        handle: EpisodeHandle,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist owner evidence without mutating the completed first attempt."""
        workflow = self._read_episode_file(handle, "workflow_state.json")
        if workflow.get("status") != STOP_STATUS:
            raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_REQUIRES_TECHNICAL_STOP")
        violations = validate_against_schema(evidence, "topic_belonging_reassessment_evidence")
        if violations:
            raise TopicBelongingExecutionError("REASSESSMENT_EVIDENCE_INVALID: " + "; ".join(violations))
        previous = self._read_episode_file(handle, "topic_belonging_reassessments.json")
        evidence_checksum = _json_checksum(evidence)
        existing = next(
            (
                item for item in previous.get("reassessments", [])
                if item.get("evidence_checksum") == evidence_checksum
            ),
            None,
        )
        if isinstance(existing, dict):
            if existing.get("status") == "COMPLETED":
                existing_decision = existing.get("decision")
                existing_gate = existing.get("gate")
                if not isinstance(existing_decision, dict) or not isinstance(existing_gate, dict):
                    raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_IDEMPOTENCY_RECORD_INVALID")
                return self._build_stop_state(
                    handle,
                    str(workflow.get("run_id")),
                    existing_gate,
                    existing_decision,
                    decision_binding=self._effective_decision_binding(handle),
                ) | {
                    "reassessment_id": existing.get("reassessment_id"),
                    "attempt_number": existing.get("attempt_number"),
                    "idempotent": True,
                }
        decision_binding = self._effective_decision_binding(handle)
        decision = decision_binding["decision"]
        if decision.get("decision") != "REQUEST_MORE_EVIDENCE":
            raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_NOT_REQUESTED")
        if isinstance(existing, dict):
            return {
                "workflow_id": "P2_TOPIC_BELONGING_ROUNDTRIP",
                "status": "READY_FOR_REASSESSMENT",
                "episode_id": handle.episode_id,
                "run_id": workflow.get("run_id"),
                "reassessment_id": existing["reassessment_id"],
                "attempt_number": existing.get("attempt_number"),
                "completed_stages": ["ENRICHMENT", "PRODUCER", "REVIEWER"],
                "prior_decision_checksum": existing.get("prior_decision_checksum"),
                "downstream_execution_started": False,
            }
        attempt_number = int(decision_binding["source_attempt"]) + 1
        reassessment = {
            "reassessment_id": f"TBR-{uuid4().hex}",
            "evidence_id": f"TBE-{uuid4().hex}",
            "attempt_number": attempt_number,
            "episode_id": handle.episode_id,
            "prior_decision_ref": decision_binding["decision_ref"],
            "prior_decision_checksum": decision_binding["decision_checksum"],
            "prior_decision_source_attempt": decision_binding["source_attempt"],
            "evidence_checksum": evidence_checksum,
            "status": "EVIDENCE_RECEIVED",
            "submitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            **copy.deepcopy(evidence),
        }
        self.store.append_topic_belonging_reassessment(handle, reassessment=reassessment)
        return {
            "workflow_id": "P2_TOPIC_BELONGING_ROUNDTRIP",
            "status": "READY_FOR_REASSESSMENT",
            "episode_id": handle.episode_id,
            "run_id": workflow.get("run_id"),
            "reassessment_id": reassessment["reassessment_id"],
            "attempt_number": attempt_number,
            "completed_stages": ["ENRICHMENT", "PRODUCER", "REVIEWER"],
            "prior_decision_ref": reassessment["prior_decision_ref"],
            "prior_decision_checksum": reassessment["prior_decision_checksum"],
            "downstream_execution_started": False,
        }

    def prepare_reassessment(self, handle: EpisodeHandle) -> dict[str, Any]:
        """Prepare a new reviewer handoff using versioned additional evidence."""
        workflow = self._read_episode_file(handle, "workflow_state.json")
        if workflow.get("status") != "READY_FOR_REASSESSMENT":
            raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_NOT_READY")
        self._effective_decision_binding(handle)
        evidence = self._read_reassessment(handle, str(workflow.get("reassessment_id")))
        topic_input = self._read_episode_file(handle, "02_topic_belonging_input.json")
        assessment = self._read_episode_file(handle, "03_topic_belonging_assessment.json")
        profile = self.profile_loader()
        _, result = self.boundary.review(
            topic_input,
            assessment,
            profile,
            handle.episode_id,
            input_producer_run_id=assessment["producer_run_id"],
            additional_evidence=evidence,
        )
        if result.status is not ExecutionStatus.HANDOFF_PREPARED:
            raise TopicBelongingExecutionError("REASSESSMENT_HANDOFF_NOT_PREPARED")
        pending = self._pending_handoff_state(handle, str(workflow.get("run_id")), result, "REVIEWER")
        pending.update(
            {
                "completed_stages": ["ENRICHMENT", "PRODUCER", "REVIEWER"],
                "reassessment_id": evidence["reassessment_id"],
                "attempt_number": evidence["attempt_number"],
                "prior_decision_checksum": evidence["prior_decision_checksum"],
            }
        )
        return pending

    def archive_completed_handoffs(self, handle: EpisodeHandle, history_root: str | Path) -> dict[str, Any]:
        """Mueve a Historial los handoffs brutos de una ejecución ya terminada.

        Solo archiva handoffs cuyo ``handoff_id`` ya está persistido en
        ``roundtrip_results.json`` con workflow en STOP técnico. Los pendientes
        permanecen visibles en ``handoff/``. Tras mover cada paquete, su
        ``handoff_package_ref`` se reubica al destino verificado para que las
        revalidaciones post-STOP sigan resolviendo el mismo contenido.
        """
        import tempfile

        from src.application.handoff_archive import archive_episode_handoffs_from_vault

        configured = getattr(self.boundary, "handoff_directory", None)
        if configured is not None:
            candidate = Path(str(configured))
            handoff_dir = candidate if candidate.is_absolute() else REPO_ROOT / candidate
        else:
            handoff_dir = REPO_ROOT / "handoff"
        history_dir = Path(history_root) / handle.episode_id / "handoffs"
        source_snapshots = (
            {
                path.name: path.read_bytes()
                for path in handoff_dir.iterdir()
                if path.is_file()
                and (path.name.startswith("RUN-AI-") or path.name.startswith("RESULT-"))
                and path.suffix == ".json"
            }
            if handoff_dir.is_dir()
            else {}
        )
        destination_existed = {
            name: (history_dir / name).exists() for name in source_snapshots
        }
        report = archive_episode_handoffs_from_vault(
            handoff_dir=handoff_dir,
            history_root=history_root,
            episode_folder=handle.folder,
        )
        archived = [str(name) for name in report.get("archived", [])]
        refs_updated = 0
        if archived:
            history_dir = Path(str(report["history_dir"]))
            tmp_path: Path | None = None
            try:
                results_path = handle.folder / ROUNDTRIP_RESULTS_FILENAME
                data = self._read_episode_file(handle, ROUNDTRIP_RESULTS_FILENAME)
                results = data.get("results", [])
                if not isinstance(results, list):
                    raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_RESULTS_INDEX_INVALID")
                for record in results:
                    if not isinstance(record, dict):
                        continue
                    current_ref = str(record.get("handoff_package_ref") or "")
                    if Path(current_ref).name in archived:
                        record["handoff_package_ref"] = str(history_dir / Path(current_ref).name)
                        refs_updated += 1
                payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=str(handle.folder), delete=False
                ) as tmp:
                    tmp.write(payload)
                    tmp_path = Path(tmp.name)
                os.replace(tmp_path, results_path)
            except Exception as exc:
                if tmp_path is not None:
                    tmp_path.unlink(missing_ok=True)
                self._rollback_handoff_archive(
                    handoff_dir,
                    history_dir,
                    source_snapshots,
                    destination_existed,
                )
                if isinstance(exc, TopicBelongingExecutionError):
                    raise
                raise TopicBelongingExecutionError(f"ROUNDTRIP_PACKAGE_REF_RELOCATION_FAILED:{exc}") from exc
        report["refs_updated"] = refs_updated
        return report

    @staticmethod
    def _rollback_handoff_archive(
        handoff_dir: Path,
        history_dir: Path,
        source_snapshots: dict[str, bytes],
        destination_existed: dict[str, bool],
    ) -> None:
        errors: list[str] = []
        for name, content in source_snapshots.items():
            source = handoff_dir / name
            destination = history_dir / name
            try:
                if not source.exists():
                    handoff_dir.mkdir(parents=True, exist_ok=True)
                    source.write_bytes(content)
                if not destination_existed.get(name, False) and destination.exists():
                    destination.unlink()
            except OSError as exc:
                errors.append(f"{name}:{exc}")
        if errors:
            raise TopicBelongingExecutionError(
                "HANDOFF_ARCHIVE_ROLLBACK_FAILED:" + ";".join(errors)
            )

    def _read_episode_file_path(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_READ_FAILED:{exc}") from exc

    def resume_roundtrip(self, handle: EpisodeHandle) -> dict[str, Any] | None:
        """Resume the next stage from persisted results, never from memory."""
        workflow = self._read_episode_file(handle, "workflow_state.json")
        if workflow.get("status") != "PERSISTED":
            return None
        next_stage = workflow.get("next_stage")
        profile = self.profile_loader()
        if next_stage == "PRODUCER":
            topic_input = self._read_roundtrip_output(handle, "ENRICHMENT")
            _, result = self.boundary.produce(
                topic_input,
                profile,
                handle.episode_id,
                input_producer_run_id=self._roundtrip_result_run_id(handle, "ENRICHMENT"),
            )
            if result.status is not ExecutionStatus.HANDOFF_PREPARED:
                raise TopicBelongingExecutionError("PRODUCER_HANDOFF_NOT_PREPARED")
            return self._pending_handoff_state(handle, str(workflow.get("run_id")), result, "PRODUCER") | {
                "completed_stages": list(workflow.get("completed_stages", [])),
            }
        if next_stage == "REVIEWER":
            topic_input = self._read_roundtrip_output(handle, "ENRICHMENT")
            assessment = self._read_roundtrip_output(handle, "PRODUCER")
            _, result = self.boundary.review(
                topic_input,
                assessment,
                profile,
                handle.episode_id,
                input_producer_run_id=self._roundtrip_result_run_id(handle, "ENRICHMENT"),
            )
            if result.status is not ExecutionStatus.HANDOFF_PREPARED:
                raise TopicBelongingExecutionError("REVIEWER_HANDOFF_NOT_PREPARED")
            return self._pending_handoff_state(handle, str(workflow.get("run_id")), result, "REVIEWER") | {
                "completed_stages": list(workflow.get("completed_stages", [])),
            }
        if next_stage == "FINALIZE":
            topic_input = self._read_roundtrip_output(handle, "ENRICHMENT")
            assessment = self._read_roundtrip_output(handle, "PRODUCER")
            decision = self._read_roundtrip_output(handle, "REVIEWER")
            gate = evaluate_topic_belonging_gate(decision, assessment, topic_input)
            reviewer_record = self._roundtrip_record_for_stage(handle, "REVIEWER")
            lineage = self._roundtrip_lineage(
                handle, topic_input, assessment, decision, reviewer_record=reviewer_record
            )
            executions = self._roundtrip_execution_records(
                handle, topic_input, assessment, decision, reviewer_record=reviewer_record
            )
            if workflow.get("reassessment_id"):
                if not isinstance(reviewer_record, dict) or not reviewer_record.get("materialized_output_path"):
                    raise TopicBelongingExecutionError("TOPIC_BELONGING_REASSESSMENT_DECISION_REF_INVALID")
                decision_binding = self._episode_artifact_binding(
                    handle, str(reviewer_record["materialized_output_path"])
                )
                self.store.complete_topic_belonging_reassessment(
                    handle,
                    reassessment_id=str(workflow["reassessment_id"]),
                    result={
                        "status": "COMPLETED",
                        "decision": decision,
                        "gate": gate,
                        "lineage": lineage,
                        "executions": executions,
                        "decision_ref": decision_binding["decision_ref"],
                        "decision_checksum": decision_binding["decision_checksum"],
                        "decision_source_attempt": workflow.get("attempt_number"),
                    },
                )
                effective_binding = self._effective_decision_binding(handle)
                return self._build_stop_state(
                    handle,
                    str(workflow.get("run_id")),
                    gate,
                    decision,
                    decision_binding=effective_binding,
                ) | {
                    "reassessment_id": workflow["reassessment_id"],
                    "attempt_number": workflow.get("attempt_number"),
                }
            self.store.record_topic_belonging_vertical(
                handle,
                topic_input=topic_input,
                assessment=assessment,
                decision=decision,
                gate_result=gate,
                lineage=lineage,
                executions=executions,
            )
            return self._build_stop_state(handle, str(workflow.get("run_id")), gate, decision)
        raise TopicBelongingExecutionError(f"ROUNDTRIP_NEXT_STAGE_INVALID:{next_stage}")

    def _roundtrip_lineage(
        self,
        handle: EpisodeHandle,
        topic_input: dict[str, Any],
        assessment: dict[str, Any],
        decision: dict[str, Any],
        *,
        reviewer_record: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        results = self._read_episode_file(handle, ROUNDTRIP_RESULTS_FILENAME).get("results", [])
        by_stage = {item.get("stage"): item for item in results}
        if reviewer_record is not None:
            by_stage["REVIEWER"] = reviewer_record
        return {
            "mission_id": self._mission_id,
            "episode_id": handle.episode_id,
            "human_input_ref": f"episode:{handle.episode_id}/00_human_input.json",
            "human_input_checksum": _json_checksum(self._read_episode_file(handle, "00_human_input.json")),
            "handoff_ref": f"episode:{handle.episode_id}/01_editorial_intake_handoff.json",
            "topic_input_ref": f"episode:{handle.episode_id}/02_topic_belonging_input.json",
            "assessment_ref": f"episode:{handle.episode_id}/03_topic_belonging_assessment.json",
            "decision_ref": f"episode:{handle.episode_id}/04_topic_belonging_decision.json",
            "gate_ref": f"episode:{handle.episode_id}/05_topic_belonging_gate.json",
            "handoff_checksum": _json_checksum(self._read_episode_file(handle, "01_editorial_intake_handoff.json")),
            "topic_input_checksum": canonical_checksum(topic_input, "input"),
            "assessment_checksum": assessment["artifact_checksum"],
            "decision_checksum": decision["provenance"]["output_checksum"],
            "enrichment_run_id": by_stage["ENRICHMENT"].get("result_run_id"),
            "producer_run_id": by_stage["PRODUCER"].get("result_run_id"),
            "reviewer_run_id": by_stage["REVIEWER"].get("result_run_id"),
            "producer_actor_id": assessment["producer_actor_id"],
            "reviewer_actor_id": decision["reviewer_actor_id"],
            "producer_executor_identity": assessment.get("provenance", {}).get("executor_identity"),
            "reviewer_executor_identity": decision.get("provenance", {}).get("executor_identity"),
            "independence_status": (
                "VERIFIED"
                if assessment.get("provenance", {}).get("executor_identity")
                and decision.get("provenance", {}).get("executor_identity")
                and assessment.get("provenance", {}).get("executor_identity")
                != decision.get("provenance", {}).get("executor_identity")
                else "INDEPENDENCE_UNVERIFIED"
            ),
            "roundtrip_kind": "AGENT_HARNESS_ROUNDTRIP",
            "stop_after": "TOPIC_BELONGING_GATE",
        }

    def _roundtrip_execution_records(
        self,
        handle: EpisodeHandle,
        topic_input: dict[str, Any],
        assessment: dict[str, Any],
        decision: dict[str, Any],
        *,
        reviewer_record: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        results = self._read_episode_file(handle, ROUNDTRIP_RESULTS_FILENAME).get("results", [])
        envelopes = {item.get("stage"): self._read_episode_file_path(handle.folder / str(item.get("result_path"))) for item in results}
        if reviewer_record is not None:
            envelopes["REVIEWER"] = self._read_episode_file_path(handle.folder / str(reviewer_record.get("result_path")))
        outputs = {"ENRICHMENT": topic_input, "PRODUCER": assessment, "REVIEWER": decision}
        roles = {"ENRICHMENT": PRODUCER_ROLE, "PRODUCER": PRODUCER_ROLE, "REVIEWER": REVIEWER_ROLE}
        refs = {
            "ENRICHMENT": f"topic_belonging_input:{topic_input['topic_input_id']}",
            "PRODUCER": f"topic_belonging_assessment:{assessment['assessment_id']}",
            "REVIEWER": f"topic_belonging_decision:{decision['decision_id']}",
        }
        artifact_checksums = {
            "ENRICHMENT": canonical_checksum(topic_input, "input"),
            "PRODUCER": assessment["artifact_checksum"],
            "REVIEWER": decision["provenance"]["output_checksum"],
        }
        records: list[dict[str, Any]] = []
        for stage in ("ENRICHMENT", "PRODUCER", "REVIEWER"):
            package_record = reviewer_record if stage == "REVIEWER" else None
            package = json.loads(self._find_package_for_result(handle, stage, package_record).read_text(encoding="utf-8"))
            envelope = envelopes[stage]
            package_inputs = package.get("input_manifest", {}).get("artifacts", [])
            provenance = envelope.get("provenance", {})
            records.append({
                "stage": stage,
                "role": roles[stage],
                "run_id": envelope["result_run_id"],
                "status": "SUCCEEDED",
                "provider_kind": "EXTERNAL" if provenance.get("executor_identity") else "UNVERIFIED_EXTERNAL",
                "provider_or_adapter": str(provenance.get("provider") or "supervised_external"),
                "model_or_evaluator": str(provenance.get("model") or "UNAVAILABLE_FROM_EXECUTOR"),
                "input_manifest_checksum": package["input_manifest_checksum"],
                "input_artifact_ids": [f"{item.get('artifact_kind')}:{item.get('artifact_id')}" for item in package_inputs],
                "input_versions": [],
                "output_checksum": envelope["output_checksum"],
                "artifact_checksum": artifact_checksums[stage],
                "artifact_ref": refs[stage],
                "execution_mode": str(package.get("execution_mode") or "REAL"),
                "execution_family": "AGENT_HARNESS",
                "execution_route": "agent_harness",
                "execution_profile": None,
                "prompt_id": package.get("prompt_id"),
                "prompt_version": package.get("prompt_version"),
                "prompt_checksum": package.get("prompt_checksum"),
                "prompt_input_checksum": package.get("prompt_input_checksum"),
                "fixture_policy": "EXTERNAL_RESULT",
                "executor_identity": provenance.get("executor_identity"),
                "session_id": provenance.get("session_id"),
            })
        return records

    def _find_package_for_result(
        self,
        handle: EpisodeHandle,
        stage: str,
        record: dict[str, Any] | None = None,
    ) -> Path:
        result = record or self._roundtrip_record_for_stage(handle, stage)
        if not isinstance(result, dict):
            raise TopicBelongingExecutionError(f"ROUNDTRIP_RESULT_MISSING:{stage}")
        package_ref = str(result.get("handoff_package_ref") or "")
        path = Path(package_ref)
        if not path.is_file():
            raise TopicBelongingExecutionError(f"HANDOFF_PACKAGE_MISSING:{stage}")
        return path

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
            if path.name not in (
                P2_ALLOWED_EPISODE_ARTIFACTS
                if (handle.folder / ROUNDTRIP_RESULTS_FILENAME).is_file()
                else M1_ALLOWED_EPISODE_ARTIFACTS
            )
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

        if lineage.get("roundtrip_kind") == "AGENT_HARNESS_ROUNDTRIP":
            try:
                self._validate_persisted_roundtrip(
                    handle,
                    workflow=self._read_episode_file(handle, "workflow_state.json"),
                    persisted=persisted,
                    handoff=handoff,
                    human_input=human_input,
                    lineage=lineage,
                    execution_payload=execution_payload,
                    episode_state=episode_state,
                    index_entry=index_entry,
                )
            except TopicBelongingExecutionError as exc:
                violations.append(str(exc))
            if not violations:
                return persisted

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
        enrichment_execution = next(
            (item for item in executions or [] if isinstance(item, dict) and item.get("stage") == "ENRICHMENT"),
            {},
        )
        stored_enrichment_proposal = enrichment_execution.get("cognitive_proposal")
        if isinstance(stored_enrichment_proposal, dict):
            proposal_violations = _validate_cognitive_proposal(stored_enrichment_proposal)
            proposal_violations.extend(
                _validate_cognitive_proposal_binding(stored_enrichment_proposal, handoff)
            )
            proposal_violations.extend(
                _validate_cognitive_proposal_result(stored_enrichment_proposal, topic_input)
            )
            proposal_provenance = enrichment_execution.get("cognitive_proposal_provenance")
            if proposal_provenance != {
                "source": "AI_PROPOSED",
                "fields": sorted(stored_enrichment_proposal),
            }:
                proposal_violations.append("COGNITIVE_PROPOSAL_PROVENANCE_INVALID")
            if lineage.get("field_ownership") != _field_ownership(topic_input, handoff):
                proposal_violations.append("FIELD_OWNERSHIP_INVALID")
            violations.extend(
                f"COGNITIVE_PROPOSAL_INVALID: {violation}"
                for violation in proposal_violations
            )
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
            enrichment_uses_proposal = isinstance(stored_enrichment_proposal, dict)
            prompt_schemas = {
                "ENRICHMENT": COGNITIVE_PROPOSAL_SCHEMA if enrichment_uses_proposal else "topic_belonging_input",
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
            stored_proposal = stored_enrichment_proposal if stage == "ENRICHMENT" else None
            expected_raw_checksum = _expected_raw_output_checksum(
                stage, topic_input, assessment, decision, stored_proposal
            )
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

    def _validate_persisted_roundtrip(
        self,
        handle: EpisodeHandle,
        *,
        workflow: dict[str, Any],
        persisted: dict[str, dict[str, Any]],
        handoff: dict[str, Any],
        human_input: dict[str, Any],
        lineage: dict[str, Any],
        execution_payload: dict[str, Any],
        episode_state: dict[str, Any],
        index_entry: dict[str, Any],
    ) -> None:
        """Revalidate the complete persisted P2 evidence before final resume."""
        if workflow.get("episode_id") != handle.episode_id:
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_WORKFLOW_EPISODE_MISMATCH")
        if workflow.get("status") not in {"PERSISTED", STOP_STATUS}:
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_WORKFLOW_STATUS_INVALID")
        if workflow.get("status") == "PERSISTED" and workflow.get("next_stage") != "FINALIZE":
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_WORKFLOW_NEXT_STAGE_INVALID")

        results_index = self._read_episode_file(handle, ROUNDTRIP_RESULTS_FILENAME)
        results = results_index.get("results")
        expected_stages = ("ENRICHMENT", "PRODUCER", "REVIEWER")
        if not isinstance(results, list):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_RESULTS_INDEX_INVALID")
        stages = [item.get("stage") for item in results if isinstance(item, dict)]
        if (
            len(stages) < len(expected_stages)
            or stages[: len(expected_stages)] != list(expected_stages)
            or any(stage != "REVIEWER" for stage in stages[len(expected_stages):])
            or (len(stages) > len(expected_stages) and not workflow.get("reassessment_id"))
        ):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_RESULTS_INDEX_INVALID")
        selected_results = [
            next(item for item in results if isinstance(item, dict) and item.get("stage") == "ENRICHMENT"),
            next(item for item in results if isinstance(item, dict) and item.get("stage") == "PRODUCER"),
            next(item for item in reversed(results) if isinstance(item, dict) and item.get("stage") == "REVIEWER"),
        ]

        role_by_stage = {
            "ENRICHMENT": PRODUCER_ROLE,
            "PRODUCER": PRODUCER_ROLE,
            "REVIEWER": REVIEWER_ROLE,
        }
        outputs: dict[str, dict[str, Any]] = {}
        result_run_ids: set[str] = set()
        for stage, record in zip(expected_stages, selected_results):
            if not isinstance(record, dict):
                raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_RESULT_RECORD_INVALID")
            try:
                package, envelope, _ = self._revalidate_roundtrip_record(handle, record)
            except TopicBelongingExecutionError:
                raise
            expected_manifest = _expected_input_manifest_checksum(
                handle.episode_id,
                stage,
                handoff,
                outputs.get("ENRICHMENT", persisted["02_topic_belonging_input.json"]),
                outputs.get("PRODUCER", persisted["03_topic_belonging_assessment.json"]),
                self._read_reassessment_for_package(handle, record) if stage == "REVIEWER" else None,
            )
            expected_identity = {
                "mission_id": self._mission_id,
                "episode_id": handle.episode_id,
                "capability_id": CAPABILITY_ID,
                "stage": stage,
                "role": role_by_stage[stage],
                "handoff_id": package.get("handoff_id"),
                "package_checksum": package.get("package_checksum"),
                "result_run_id": envelope.get("result_run_id"),
                "output_checksum": envelope.get("output_checksum"),
            }
            if any(record.get(key) != value for key, value in expected_identity.items()):
                raise TopicBelongingExecutionError(
                    f"ROUNDTRIP_PERSISTED_RESULT_RECORD_BINDING_INVALID:{stage}"
                )
            if package.get("stage") != stage or package.get("role") != role_by_stage[stage]:
                raise TopicBelongingExecutionError(f"ROUNDTRIP_PERSISTED_PACKAGE_BINDING_INVALID:{stage}")
            if package.get("input_manifest_checksum") != expected_manifest:
                raise TopicBelongingExecutionError(
                    f"ROUNDTRIP_PERSISTED_INPUT_MANIFEST_INVALID:{stage}"
                )
            provenance = envelope.get("provenance")
            if not isinstance(provenance, dict) or any(
                provenance.get(key) != expected_identity[key]
                for key in ("mission_id", "episode_id", "capability_id", "stage", "role")
            ) or provenance.get("run_id") != envelope.get("result_run_id"):
                raise TopicBelongingExecutionError(
                    f"ROUNDTRIP_PERSISTED_PROVENANCE_INVALID:{stage}"
                )
            if envelope.get("result_run_id") in result_run_ids:
                raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_RESULT_RUN_COLLISION")
            result_run_ids.add(str(envelope.get("result_run_id")))
            outputs[stage] = self._read_roundtrip_output(handle, stage)

        if workflow.get("reassessment_id") and len(results) > len(expected_stages):
            canonical_reviewer = selected_results[2]
            canonical_ref = str(canonical_reviewer.get("materialized_output_path") or "")
            if not canonical_ref:
                raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_CANONICAL_REVIEWER_MISSING")
            canonical_path = (handle.folder / canonical_ref).resolve()
            try:
                canonical_path.relative_to(handle.folder.resolve())
                canonical_decision = self._read_episode_file_path(canonical_path)
            except (OSError, ValueError, TopicBelongingExecutionError) as exc:
                raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_CANONICAL_REVIEWER_INVALID") from exc
            if hashlib.sha256(canonical_path.read_bytes()).hexdigest() != canonical_reviewer.get("materialized_output_checksum"):
                raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_CANONICAL_REVIEWER_STALE")
            canonical_violations = validate_decision(canonical_decision, outputs["PRODUCER"])
            if canonical_violations:
                raise TopicBelongingExecutionError(
                    "ROUNDTRIP_PERSISTED_OUTPUT_INVALID:REVIEWER:" + ";".join(canonical_violations)
                )
            outputs["REVIEWER"] = canonical_decision
            latest_reviewer = next(
                item for item in reversed(results)
                if isinstance(item, dict) and item.get("stage") == "REVIEWER"
            )
            if latest_reviewer.get("reassessment_id") != workflow.get("reassessment_id"):
                raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_REASSESSMENT_BINDING_INVALID")
            self._read_roundtrip_output(handle, "REVIEWER")

        if workflow.get("status") == "PERSISTED" and workflow.get("completed_stages") != list(expected_stages):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_COMPLETED_STAGES_INVALID")

        expected_artifacts = {
            "02_topic_belonging_input.json": outputs["ENRICHMENT"],
            "03_topic_belonging_assessment.json": outputs["PRODUCER"],
            "04_topic_belonging_decision.json": outputs["REVIEWER"],
            "05_topic_belonging_gate.json": evaluate_topic_belonging_gate(
                outputs["REVIEWER"], outputs["PRODUCER"], outputs["ENRICHMENT"]
            ),
        }
        for name, expected in expected_artifacts.items():
            if persisted[name] != expected:
                raise TopicBelongingExecutionError(f"ROUNDTRIP_PERSISTED_ARTIFACT_MISMATCH:{name}")

        canonical_reviewer = selected_results[2]
        expected_lineage = self._roundtrip_lineage(
            handle,
            outputs["ENRICHMENT"],
            outputs["PRODUCER"],
            outputs["REVIEWER"],
            reviewer_record=canonical_reviewer,
        )
        if lineage != expected_lineage:
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_LINEAGE_MISMATCH")
        expected_executions = self._roundtrip_execution_records(
            handle,
            outputs["ENRICHMENT"],
            outputs["PRODUCER"],
            outputs["REVIEWER"],
            reviewer_record=canonical_reviewer,
        )
        if execution_payload.get("executions") != expected_executions:
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_EXECUTION_EVIDENCE_MISMATCH")

        self._validate_persisted_origin_binding(handle)
        state_mission_id, index_mission_id, lineage_mission_id = self._persisted_mission_bindings(handle)
        if {state_mission_id, index_mission_id, lineage_mission_id} != {self._mission_id}:
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_MISSION_BINDING_INVALID")
        if episode_state.get("status") != index_entry.get("application_status"):
            raise TopicBelongingExecutionError("ROUNDTRIP_PERSISTED_STORAGE_STATUS_INVALID")

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
        decision = self._effective_decision(handle)
        gate = evaluate_topic_belonging_gate(
            decision,
            self._read_episode_file(handle, "03_topic_belonging_assessment.json"),
            self._read_episode_file(handle, "02_topic_belonging_input.json"),
        )
        return self._build_stop_state(handle, run_id, gate, decision)

    @staticmethod
    def _execution_record(
        stage: str,
        role: str,
        result: ExecutionResult,
        artifact_checksum: str,
        input_artifact_ids: list[str],
        input_versions: list[str],
        *,
        artifact_ref: str | None = None,
        cognitive_proposal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
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
            "artifact_ref": artifact_ref or result.output_artifact_ref,
            "execution_mode": result.usage.get("execution_mode", "SYNTHETIC" if result.provider == "mock" else "REAL"),
            "execution_route": result.usage.get("execution_route"),
            "execution_profile": result.usage.get("execution_profile"),
            "prompt_id": result.usage.get("prompt_id"),
            "prompt_version": result.usage.get("prompt_version"),
            "prompt_checksum": result.usage.get("prompt_checksum"),
            "prompt_input_checksum": result.usage.get("prompt_input_checksum"),
        }
        if cognitive_proposal is not None:
            record["cognitive_proposal"] = copy.deepcopy(cognitive_proposal)
            record["cognitive_proposal_provenance"] = {
                "source": "AI_PROPOSED",
                "fields": sorted(cognitive_proposal),
            }
        return record

    def resume(self, handle: EpisodeHandle, human_input: HumanInput, handoff: dict[str, Any], decision: Any, request: Any) -> dict[str, Any]:
        raise StorageError("La vertical Topic Belonging no admite decisiones humanas intermedias.")


def build_topic_belonging_service(store: VaultEpisodeStore, *, boundary: CognitiveBoundary) -> TopicBelongingTechnicalWorkflow:
    """Factory kept as the single application entrypoint for the capability route."""
    return TopicBelongingTechnicalWorkflow(store, boundary=boundary)
