"""Deterministic B2 routing for Research V2.

This module owns the software boundary around the existing
``RESEARCH_AND_CURATION`` responsibility.  It accepts an injected cognitive
result for tests or a later runtime integration; it never calls an AI
provider itself.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ai.role_execution import resolve_role_execution_contract
from src.application.storage import _write_json_atomic
from src.core.contract_validation import (
    validate_against_schema,
    validate_research_pack,
    validate_research_plan,
    validate_research_stop_decision,
    validate_source_access_and_evidence_report,
    validate_thesis_artifact,
    validate_work_lifecycle,
    validate_work_research_dossier,
)


ROLE_ID = "RESEARCH_AND_CURATION"
CONTRACT_VERSION = "2.0.0"
NARRATIVE_FIELDS = {
    "hook",
    "viewer_journey",
    "narrative_plan",
    "opening_design",
    "closing_design",
    "pacing",
    "climax",
    "cta",
    "title",
    "thumbnail",
    "narrative_opportunities",
    "editorial_uses",
    "candidate_editorial_function_analysis_ref",
}


class ResearchB2Error(ValueError):
    """A deterministic B2 contract, routing, or persistence failure."""


@dataclass(frozen=True)
class B2CognitiveRequest:
    """The only payload handed from Software to an injected cognitive step."""

    stage: str
    output_schema: str
    input_artifacts: tuple[dict[str, str], ...]
    prepared_contract: dict[str, Any]


class ResearchB2Persistence:
    """Small B2 adapter that reuses the repository's atomic JSON writer."""

    _FILENAMES = {
        "RESEARCH_PLAN": "research_plan.json",
        "PHENOMENON_BASE_RESEARCH": "phenomenon_base_research.json",
        "WORK_DISCOVERY": "work_discovery.json",
        "BASE_RESEARCH_POOL": "base_research_pool.json",
        "PRELIMINARY_FIDELITY": "preliminary_fidelity.json",
        "INITIAL_SUFFICIENCY": "initial_sufficiency.json",
        "PROVISIONAL_THESIS": "provisional_thesis.json",
        "RESEARCH_COMPARISON": "research_comparison.json",
        "EXECUTION_MANIFEST": "research_b2_execution.json",
    }

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._persisted: dict[str, dict[str, str]] = {}

    def persist(self, stage: str, payload: Any, *, artifact_id: str, artifact_kind: str) -> dict[str, str]:
        if stage in self._persisted:
            raise ResearchB2Error(f"B2_ARTIFACT_ALREADY_PERSISTED: {stage}")
        filename = self._FILENAMES.get(stage)
        if filename is None:
            raise ResearchB2Error(f"B2_UNKNOWN_PERSISTENCE_STAGE: {stage}")
        document = payload if isinstance(payload, dict) else {"dossiers": payload}
        path = self.root / filename
        if path.exists():
            raise ResearchB2Error(f"B2_ARTIFACT_ALREADY_EXISTS: {path}")
        _write_json_atomic(path, document)
        checksum = _checksum(document)
        ref = {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "artifact_version": CONTRACT_VERSION,
            "path": str(path),
            "checksum": checksum,
        }
        self._persisted[stage] = ref
        return ref


class SoftwareAcquisitionAdapter:
    """Materialize technical source bindings from Software-owned records."""

    _SOURCE_TECHNICAL_FIELDS = (
        "retrieval_status",
        "evidence_status",
        "recovery_artifact_ref",
        "retrieval_request_ref",
    )

    def __init__(
        self,
        bindings: Mapping[str, Mapping[str, Any]] | None = None,
        *,
        work_bindings: Mapping[str, Mapping[str, Any]] | None = None,
        work_representation_bindings: Mapping[Any, Mapping[str, Any]] | None = None,
    ):
        self.bindings = {str(key): dict(value) for key, value in (bindings or {}).items()}
        self.work_bindings = {str(key): dict(value) for key, value in (work_bindings or {}).items()}
        self.work_representation_bindings = {
            self._representation_key_from_mapping_key(key, value): dict(value)
            for key, value in (work_representation_bindings or {}).items()
        }
        self.materialized_work_bindings: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _representation_key(work_id: str, representation: Mapping[str, Any]) -> str:
        return "|".join(
            [str(work_id)]
            + [str(representation.get(field, "")) for field in (
                "representation_kind", "edition_or_version", "consulted_locator"
            )]
        )

    @classmethod
    def _representation_key_from_mapping_key(cls, key: Any, binding: Mapping[str, Any]) -> str:
        if isinstance(key, tuple) and len(key) == 4:
            work_id, representation_kind, edition_or_version, consulted_locator = key
            return f"{work_id}|{representation_kind}|{edition_or_version}|{consulted_locator}"
        return str(key)

    @staticmethod
    def _binding_matches_representation(binding: Mapping[str, Any], representation: Mapping[str, Any]) -> bool:
        return all(binding.get(field) == representation.get(field) for field in (
            "representation_kind", "edition_or_version", "consulted_locator"
        ))

    @staticmethod
    def _validate_work_binding(binding: Mapping[str, Any], work_id: str) -> None:
        if (
            binding.get("retrieval_status") != "RECOVERED"
            or binding.get("software_controlled") is not True
            or not binding.get("recovery_artifact_ref")
            or not binding.get("request_ref")
            or not binding.get("execution_ref")
            or binding.get("evidence_status") not in {"CONSULTED", "VERIFIED", "EVIDENCE"}
        ):
            raise ResearchB2Error(f"WORK_ACQUISITION_BINDING_INVALID: {work_id}")

    def materialize(self, research_pack: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(research_pack, Mapping):
            raise ResearchB2Error("ResearchPack debe ser un objeto")
        if "acquisition_bindings" in research_pack:
            raise ResearchB2Error("COGNITIVE_OUTPUT_CANNOT_SET_ACQUISITION_BINDINGS")
        result = copy.deepcopy(dict(research_pack))
        materialized: list[dict[str, Any]] = []
        for source in result.get("source_registry", []):
            if not isinstance(source, dict) or not source.get("source_id"):
                continue
            source_id = str(source["source_id"])
            record = self.bindings.get(source_id, {})
            binding = {
                "request_ref": str(record.get("request_ref", f"software:request:{source_id}")),
                "execution_ref": str(record.get("execution_ref", f"software:execution:{source_id}")),
                "recovery_artifact_ref": record.get("recovery_artifact_ref"),
                "source_ref": source_id,
                "retrieval_status": record.get("retrieval_status", "NOT_RECOVERED"),
                "evidence_status": record.get("evidence_status", "PENDING"),
                "software_controlled": record.get("software_controlled", True),
            }
            source.update(
                {
                    "retrieval_status": binding["retrieval_status"],
                    "evidence_status": binding["evidence_status"],
                    "recovery_artifact_ref": binding["recovery_artifact_ref"],
                    "retrieval_request_ref": record.get("retrieval_request_ref", binding["request_ref"]),
                }
            )
            provenance = dict(source.get("provenance") or {})
            positive = binding["evidence_status"] in {"CONSULTED", "VERIFIED", "EVIDENCE"}
            provenance.update(
                {
                    "verification_status": "REVIEWED" if positive else "NOT_REVIEWED",
                    "acquisition_method": "SOFTWARE_CONTROLLED_ACQUISITION",
                    "primary_verification_performed": False,
                }
            )
            source["provenance"] = provenance
            materialized.append(binding)
        result["acquisition_bindings"] = materialized
        return result

    def materialize_work_dossiers(self, dossiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Bind consulted work representations to Software-owned acquisition records."""
        result = copy.deepcopy(dossiers)
        materialized: dict[str, dict[str, Any]] = {}
        for dossier in result:
            if not isinstance(dossier, dict) or not isinstance(dossier.get("work"), dict):
                raise ResearchB2Error("WorkResearchDossier debe ser un objeto")
            work = dossier["work"]
            work_id = str(work.get("material_id") or "")
            default_binding = self.work_bindings.get(work_id)
            if not default_binding:
                raise ResearchB2Error(f"WORK_ACQUISITION_BINDING_REQUIRED: {work_id}")
            self._validate_work_binding(default_binding, work_id)
            representations = work.get("consulted_representations") or []
            if not representations:
                raise ResearchB2Error(f"WORK_CONSULTED_REPRESENTATION_REQUIRED: {work_id}")
            representation_bindings: list[dict[str, Any]] = []
            manifest_bindings: list[dict[str, Any]] = []
            for representation_index, representation in enumerate(representations, start=1):
                if not isinstance(representation, dict):
                    raise ResearchB2Error(f"WORK_CONSULTED_REPRESENTATION_INVALID: {work_id}")
                binding = default_binding if self._binding_matches_representation(default_binding, representation) else None
                if binding is None:
                    key = self._representation_key(work_id, representation)
                    binding = self.work_representation_bindings.get(key)
                if not binding:
                    raise ResearchB2Error(f"WORK_LOCATOR_BINDING_MISMATCH: {work_id}:consulted_representation")
                self._validate_work_binding(binding, work_id)
                binding_ref = f"software:work-acquisition:{work_id}" if representation_index == 1 else f"software:work-acquisition:{work_id}:{representation_index}"
                record = {
                    "request_ref": binding["request_ref"],
                    "execution_ref": binding["execution_ref"],
                    "recovery_artifact_ref": binding["recovery_artifact_ref"],
                    "source_ref": binding.get("source_ref", f"{work_id}:representation:{representation_index}"),
                    "retrieval_status": binding["retrieval_status"],
                    "evidence_status": binding["evidence_status"],
                    "software_controlled": binding["software_controlled"],
                    "representation_kind": representation["representation_kind"],
                    "edition_or_version": representation["edition_or_version"],
                    "consulted_locator": representation["consulted_locator"],
                }
                representation_bindings.append(record)
                manifest_bindings.append({
                    "binding_ref": binding_ref,
                    "work_id": work_id,
                    **record,
                })
            dossier["acquisition_bindings"] = copy.deepcopy(representation_bindings)
            dossier["lineage"] = sorted(
                set(dossier.get("lineage", [])) | {item["binding_ref"] for item in manifest_bindings}
            )
            materialized[work_id] = copy.deepcopy(manifest_bindings[0])
            if len(manifest_bindings) > 1:
                materialized[work_id]["representation_bindings"] = copy.deepcopy(manifest_bindings)
        self.materialized_work_bindings.update(materialized)
        return result

    def work_binding_manifest(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(self.materialized_work_bindings[key]) for key in sorted(self.materialized_work_bindings)]


@dataclass(frozen=True)
class NoProgressObservation:
    status: str
    route: str
    reason: str
    fingerprint: str


class ResearchB2NoProgressGuard:
    """Operational loop safety, deliberately separate from ResearchStopDecision."""

    def __init__(self, max_iterations: int = 3):
        if max_iterations < 1:
            raise ResearchB2Error("ITERATION_GUARD_MAX_ITERATIONS_MUST_BE_POSITIVE")
        self.max_iterations = max_iterations
        self._state_keys: set[str] = set()
        self._states: list[tuple[str, str]] = []
        self._observations: list[dict[str, Any]] = []
        self._gap_iterations: dict[str, int] = {}

    def observe(
        self,
        *,
        gap: str,
        evidence_refs: list[str],
        state: str,
        result: Any,
        transition: str | None = None,
    ) -> NoProgressObservation:
        fingerprint = _checksum({"gap": gap, "evidence_refs": sorted(evidence_refs), "state": state, "result": result})
        state_key = _checksum({"gap": gap, "evidence_refs": sorted(evidence_refs), "state": state})
        if state_key in self._state_keys:
            outcome = NoProgressObservation("NO_PROGRESS", "HUMAN_REVIEW", "SAME_GAP_STATE_AND_EVIDENCE", fingerprint)
        elif (
            len(self._states) >= 2
            and gap == self._states[-2][0]
            and state == self._states[-2][1]
            and state != self._states[-1][1]
        ):
            outcome = NoProgressObservation("NO_PROGRESS", "STOP_LOCAL", "A_TO_B_TO_A_CYCLE", fingerprint)
        elif self._gap_iterations.get(gap, 0) >= self.max_iterations:
            outcome = NoProgressObservation("NO_PROGRESS", "STOP_LOCAL", "ITERATION_LIMIT_EXCEEDED", fingerprint)
        else:
            outcome = NoProgressObservation("PROGRESS", "CONTINUE", "NEW_STATE_OR_EVIDENCE", fingerprint)
        self._state_keys.add(state_key)
        self._states.append((gap, state))
        self._gap_iterations[gap] = self._gap_iterations.get(gap, 0) + 1
        self._observations.append({"gap": gap, "state": state, "transition": transition, **outcome.__dict__})
        return outcome

    def to_dict(self) -> dict[str, Any]:
        return {"max_iterations": self.max_iterations, "observations": copy.deepcopy(self._observations)}


class ResearchB2Orchestrator:
    """Run the sequential B2 stages with a Software checkpoint between them."""

    def __init__(
        self,
        cognitive_executor: Callable[[B2CognitiveRequest], Any],
        persistence: ResearchB2Persistence,
        *,
        acquisition_adapter: SoftwareAcquisitionAdapter | None = None,
        no_progress_guard: ResearchB2NoProgressGuard | None = None,
    ):
        if not callable(cognitive_executor):
            raise ResearchB2Error("B2_COGNITIVE_EXECUTOR_REQUIRED")
        self.cognitive_executor = cognitive_executor
        self.persistence = persistence
        self.acquisition_adapter = acquisition_adapter or SoftwareAcquisitionAdapter()
        self.no_progress_guard = no_progress_guard or ResearchB2NoProgressGuard()

    def run(self, research_plan: Mapping[str, Any], *, context: Mapping[str, Any]) -> dict[str, Any]:
        plan = copy.deepcopy(dict(research_plan)) if isinstance(research_plan, Mapping) else research_plan
        plan_errors = validate_research_plan(plan) if isinstance(plan, dict) else ["ResearchPlan debe ser un objeto."]
        if plan_errors:
            raise ResearchB2Error("RESEARCH_PLAN_INVALID: " + " | ".join(plan_errors))
        if not isinstance(context, Mapping):
            raise ResearchB2Error("B2_CONTEXT_REQUIRED")
        required_context = {"topic", "source_access", "brief", "channel_context"}
        missing = sorted(required_context - set(context))
        if missing:
            raise ResearchB2Error("B2_CONTEXT_INVALID: faltan " + ", ".join(missing))

        events: list[dict[str, Any]] = []
        plan_ref = self.persistence.persist(
            "RESEARCH_PLAN", plan, artifact_id=plan["research_plan_id"], artifact_kind="ResearchPlan"
        )
        artifacts = [plan_ref]

        phenomenon = self._step(
            "PHENOMENON_BASE_RESEARCH",
            "research_pack",
            plan,
            context,
            artifacts,
            events,
            self._validate_phenomenon,
        )
        phenomenon_ref = self.persistence.persist(
            "PHENOMENON_BASE_RESEARCH",
            phenomenon,
            artifact_id=phenomenon["research_id"],
            artifact_kind="ResearchPack",
        )
        events.append({"stage": "PHENOMENON_BASE_RESEARCH", "boundary": "SOFTWARE_PERSIST", "artifact_id": phenomenon_ref["artifact_id"]})
        artifacts.append(phenomenon_ref)

        discovery = self._step(
            "WORK_DISCOVERY",
            "work_lifecycle",
            plan,
            context,
            artifacts,
            events,
            self._validate_discovery,
        )
        discovery_ref = self.persistence.persist(
            "WORK_DISCOVERY",
            discovery,
            artifact_id=discovery["lifecycle_id"],
            artifact_kind="WorkLifecycle",
        )
        events.append({"stage": "WORK_DISCOVERY", "boundary": "SOFTWARE_PERSIST", "artifact_id": discovery_ref["artifact_id"]})
        artifacts.append(discovery_ref)

        pool = self._step(
            "BASE_RESEARCH_POOL",
            "work_research_dossier",
            plan,
            context,
            artifacts,
            events,
            lambda value: self._validate_pool(value, discovery),
        )
        pool_ref = self.persistence.persist(
            "BASE_RESEARCH_POOL",
            pool,
            artifact_id=f"{plan['research_plan_id']}:BASE_RESEARCH_POOL",
            artifact_kind="WorkResearchDossierCollection",
        )
        events.append({"stage": "BASE_RESEARCH_POOL", "boundary": "SOFTWARE_PERSIST", "artifact_id": pool_ref["artifact_id"]})
        artifacts.append(pool_ref)

        fidelity = self._step(
            "PRELIMINARY_FIDELITY",
            "work_research_dossier",
            plan,
            context,
            artifacts,
            events,
            lambda value: self._validate_fidelity(value, pool),
        )
        fidelity_ref = self.persistence.persist(
            "PRELIMINARY_FIDELITY",
            fidelity,
            artifact_id=f"{plan['research_plan_id']}:PRELIMINARY_FIDELITY",
            artifact_kind="WorkResearchDossierCollection",
        )
        events.append({"stage": "PRELIMINARY_FIDELITY", "boundary": "SOFTWARE_PERSIST", "artifact_id": fidelity_ref["artifact_id"]})
        artifacts.append(fidelity_ref)

        sufficiency = self._step(
            "INITIAL_SUFFICIENCY",
            "research_stop_decision",
            plan,
            context,
            artifacts,
            events,
            lambda value: self._validate_sufficiency(value, phenomenon, pool),
        )
        sufficiency_ref = self.persistence.persist(
            "INITIAL_SUFFICIENCY",
            sufficiency,
            artifact_id=f"{plan['research_plan_id']}:INITIAL_SUFFICIENCY",
            artifact_kind="ResearchStopDecisionCollection",
        )
        events.append({"stage": "INITIAL_SUFFICIENCY", "boundary": "SOFTWARE_PERSIST", "artifact_id": sufficiency_ref["artifact_id"]})
        artifacts.append(sufficiency_ref)
        if not self._sufficiency_allows_thesis(sufficiency, phenomenon):
            raise ResearchB2Error("PROVISIONAL_THESIS_BLOCKED_BY_INVALID_SUFFICIENCY")

        thesis = self._step(
            "PROVISIONAL_THESIS",
            "thesis_artifact",
            plan,
            context,
            artifacts,
            events,
            lambda value: self._validate_provisional_thesis(value, phenomenon, context["source_access"]),
        )
        thesis_ref = self.persistence.persist(
            "PROVISIONAL_THESIS",
            thesis,
            artifact_id=thesis["thesis_id"],
            artifact_kind="ThesisArtifact",
        )
        events.append({"stage": "PROVISIONAL_THESIS", "boundary": "SOFTWARE_PERSIST", "artifact_id": thesis_ref["artifact_id"]})
        artifacts.append(thesis_ref)

        comparison = self._step(
            "RESEARCH_COMPARISON",
            "research_comparison",
            plan,
            context,
            artifacts,
            events,
            lambda value: self._validate_comparison(value, fidelity, sufficiency),
        )
        comparison_ref = self.persistence.persist(
            "RESEARCH_COMPARISON",
            comparison,
            artifact_id=comparison["comparison_id"],
            artifact_kind="ResearchComparison",
        )
        events.append({"stage": "RESEARCH_COMPARISON", "boundary": "SOFTWARE_PERSIST", "artifact_id": comparison_ref["artifact_id"]})
        artifacts.append(comparison_ref)

        deepening_targets = self._build_deepening_targets(
            plan, phenomenon, pool, fidelity, comparison, comparison_ref
        )

        lifecycle = self._bind_fidelity_to_lifecycle(discovery, fidelity, fidelity_ref)
        lifecycle_ref = self.persistence.persist(
            "EXECUTION_MANIFEST",
            {
                "manifest_type": "RESEARCH_B2_EXECUTION",
                "manifest_version": CONTRACT_VERSION,
                "status": "READY_FOR_OWNER_REVIEW",
                "real_ai_execution": False,
                "real_research": False,
                "product_use": False,
                "stage_order": [
                    "RESEARCH_PLAN",
                    "PHENOMENON_BASE_RESEARCH",
                    "WORK_DISCOVERY",
                    "BASE_RESEARCH_POOL",
                    "PRELIMINARY_FIDELITY",
                    "INITIAL_SUFFICIENCY",
                    "PROVISIONAL_THESIS",
                    "RESEARCH_COMPARISON",
                ],
                "artifacts": artifacts,
                "events": events,
                "iteration_guard": self.no_progress_guard.to_dict(),
                "work_acquisition_bindings": self.acquisition_adapter.work_binding_manifest(),
                "deepening_targets": deepening_targets,
                "lifecycle_projection": lifecycle,
            },
            artifact_id=f"{plan['research_plan_id']}:B2",
            artifact_kind="ResearchB2ExecutionManifest",
        )
        return {
            "research_plan": plan_ref,
            "phenomenon_base_research": phenomenon_ref,
            "work_discovery": discovery_ref,
            "base_research_pool": pool_ref,
            "preliminary_fidelity": fidelity_ref,
            "initial_sufficiency": sufficiency_ref,
            "provisional_thesis": thesis_ref,
            "research_comparison": comparison_ref,
            "deepening_targets": copy.deepcopy(deepening_targets),
            "lifecycle_projection": lifecycle,
            "execution_manifest": lifecycle_ref,
            "events": events,
        }

    @staticmethod
    def _build_deepening_targets(
        plan: Mapping[str, Any],
        phenomenon: Mapping[str, Any],
        pool: list[dict[str, Any]],
        fidelity: list[dict[str, Any]],
        comparison: Mapping[str, Any],
        comparison_ref: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Materialize only the cognitive deepening targets returned by Research.

        Software owns identity, lineage and persistence metadata, but it must
        not invent the research content that a later stage should deepen.
        """
        del phenomenon, fidelity
        cognitive_targets = comparison.get("deepening_targets")
        if not isinstance(cognitive_targets, Mapping):
            raise ResearchB2Error("RESEARCH_COMPARISON debe aportar deepening_targets cognitivos")
        phenomenon_targets = cognitive_targets.get("phenomenon")
        cognitive_works = cognitive_targets.get("works")
        if not isinstance(phenomenon_targets, Mapping) or not phenomenon_targets.get("targets"):
            raise ResearchB2Error("La investigación debe identificar targets materiales del fenómeno")
        if not isinstance(cognitive_works, Mapping):
            raise ResearchB2Error("La investigación debe identificar targets materiales de las obras")
        works: dict[str, Any] = {}
        pool_ids = {str(dossier["work"]["material_id"]) for dossier in pool}
        for work_id, target in cognitive_works.items():
            if str(work_id) not in pool_ids:
                raise ResearchB2Error(f"La investigación referencia una obra inexistente: {work_id}")
            if not isinstance(target, Mapping) or not target.get("targets"):
                raise ResearchB2Error(f"La investigación debe aportar targets materiales para {work_id}")
            works[str(work_id)] = copy.deepcopy(dict(target))
            works[str(work_id)]["work_id"] = str(work_id)
        return {
            "artifact_kind": "B2DeepeningTargets",
            "artifact_version": CONTRACT_VERSION,
            "source_artifact_ref": str(comparison_ref.get("artifact_id")),
            "research_plan_id": str(plan.get("research_plan_id")),
            "phenomenon": copy.deepcopy(dict(phenomenon_targets)),
            "works": works,
        }

    def _step(
        self,
        stage: str,
        output_schema: str,
        plan: dict[str, Any],
        context: Mapping[str, Any],
        input_artifacts: list[dict[str, str]],
        events: list[dict[str, Any]],
        validator: Callable[[Any], None],
    ) -> Any:
        events.append({"stage": stage, "boundary": "SOFTWARE_PREPARE", "input_artifacts": copy.deepcopy(input_artifacts)})
        input_payload = {
            "topic": context["topic"],
            "source_access": context["source_access"],
            "brief": context["brief"],
            "channel_context": context["channel_context"],
            "research_plan": plan,
            "stage": stage,
            "input_artifacts": copy.deepcopy(input_artifacts),
        }
        prepared = resolve_role_execution_contract(
            ROLE_ID,
            output_schema,
            input_payload,
            {"stage": stage, "real_ai_execution": False, "real_research": False},
        )
        request = B2CognitiveRequest(stage, output_schema, tuple(copy.deepcopy(input_artifacts)), prepared)
        events.append({"stage": stage, "boundary": "IA_COGNITIVE_STEP", "output_schema": output_schema})
        output = self.cognitive_executor(request)
        output = self._software_project(stage, output, plan, context, input_artifacts)
        try:
            validator(output)
        except (TypeError, KeyError, ValueError) as exc:
            raise ResearchB2Error(f"{stage}_OUTPUT_INVALID: {exc}") from exc
        events.append({"stage": stage, "boundary": "SOFTWARE_VALIDATE", "validated": True})
        guard = self.no_progress_guard.observe(
            gap=stage,
            evidence_refs=[item["artifact_id"] for item in input_artifacts],
            state=_state_of(output),
            result=output,
        )
        events.append({"stage": stage, "boundary": "SOFTWARE_ITERATION_GUARD", **guard.__dict__})
        if guard.status == "NO_PROGRESS":
            raise ResearchB2Error(f"{stage}_NO_PROGRESS: {guard.reason}:{guard.route}")
        return output

    def _software_project(
        self,
        stage: str,
        output: Any,
        plan: dict[str, Any],
        context: Mapping[str, Any],
        input_artifacts: list[dict[str, str]],
    ) -> Any:
        """Project cognitive content into a Software-owned canonical payload."""
        value = copy.deepcopy(output)
        if stage == "PHENOMENON_BASE_RESEARCH":
            value = self.acquisition_adapter.materialize(value)
            self._project_common_research(value, plan, context)
            value.update(
                {
                    "research_stage": "BASE_RESEARCH",
                    "artifact_validity": "VALID",
                    "thesis_stage": "NONE",
                    "created_at": utc_now(),
                }
            )
        elif stage == "WORK_DISCOVERY":
            self._project_common_research(value, plan, context, include_brief=False)
            value.update(
                {
                    "lifecycle_id": f"{plan['research_plan_id']}:DISCOVERY",
                    "lifecycle_version": CONTRACT_VERSION,
                    "created_at": utc_now(),
                    "research_contract_version": CONTRACT_VERSION,
                }
            )
            for work in value.get("works", []):
                if isinstance(work, dict):
                    work.update(
                        {
                            "state": "DISCOVERED_WORK",
                            "state_version": CONTRACT_VERSION,
                            "research_stage": "DISCOVERY",
                            "selection_state": "NOT_EVALUATED",
                            "preliminary_fidelity": "NOT_ASSESSED",
                            "deep_fidelity": "NOT_ASSESSED",
                            "research_sufficiency": "MORE_RESEARCH_REQUIRED",
                            "artifact_validity": "VALID",
                            "thesis_stage": "NONE",
                            "research_contract_version": CONTRACT_VERSION,
                            "lineage_refs": [f"software:discovery:{plan['research_plan_id']}"],
                        }
                    )
        elif stage in {"BASE_RESEARCH_POOL", "PRELIMINARY_FIDELITY"}:
            if not isinstance(value, list):
                raise ResearchB2Error(f"{stage} debe devolver una lista")
            value = self.acquisition_adapter.materialize_work_dossiers(value)
            for dossier in value:
                if not isinstance(dossier, dict) or not isinstance(dossier.get("work"), dict):
                    continue
                work_id = dossier["work"].get("material_id")
                if not work_id:
                    continue
                declared_fidelity = dossier.get("preliminary_fidelity")
                dossier.update(
                    {
                        "dossier_id": f"{plan['research_plan_id']}:DOSSIER:{work_id}",
                        "dossier_version": CONTRACT_VERSION,
                        "episode_id": plan["episode_id"],
                        "research_id": plan["research_plan_id"],
                        "evidence_report_id": self._source_report_id(context, plan),
                        "created_at": utc_now(),
                        "research_stage": "BASE_RESEARCH" if stage == "BASE_RESEARCH_POOL" else "PRELIMINARY_FIDELITY",
                        "artifact_validity": "VALID",
                        "research_contract_version": CONTRACT_VERSION,
                        "thesis_stage": "NONE",
                    }
                )
                lineage = {
                    f"software:b2:{stage.lower()}",
                    *[f"software:input:{item['artifact_id']}" for item in input_artifacts],
                    f"software:work-acquisition:{work_id}",
                }
                dossier["lineage"] = sorted(lineage)
                if stage == "BASE_RESEARCH_POOL":
                    dossier.update(
                        {
                            "selection_state": "CANDIDATE",
                            "preliminary_fidelity": "NOT_ASSESSED",
                            "deep_fidelity": "NOT_ASSESSED",
                            "research_sufficiency": "MORE_RESEARCH_REQUIRED",
                            "thesis_stage": "NONE",
                        }
                    )
                else:
                    dossier["preliminary_fidelity"] = declared_fidelity
                    dossier["selection_state"] = "CANDIDATE"
                    dossier["deep_fidelity"] = "NOT_ASSESSED"
                    dossier["research_sufficiency"] = (
                        "MORE_RESEARCH_REQUIRED"
                        if declared_fidelity == "NO_APTA"
                        else "LIMITED_BUT_USABLE"
                    )
        elif stage == "INITIAL_SUFFICIENCY":
            if not isinstance(value, list):
                raise ResearchB2Error("INITIAL_SUFFICIENCY debe devolver decisiones no vacías")
            for decision in value:
                if isinstance(decision, dict):
                    subject_ref = decision.get("subject_ref", "UNKNOWN")
                    subject_kind = decision.get("subject_kind", "UNKNOWN")
                    decision.update(
                        {
                            "decision_id": f"{plan['research_plan_id']}:RSD:{subject_kind}:{subject_ref}",
                            "decision_version": CONTRACT_VERSION,
                            "research_contract_version": CONTRACT_VERSION,
                            "artifact_validity": "VALID",
                            "research_stage": "BASE_RESEARCH",
                            "operational_guard_ref": f"software:iteration-guard:{plan['research_plan_id']}",
                        }
                    )
        elif stage == "PROVISIONAL_THESIS":
            if not isinstance(value, dict):
                raise ResearchB2Error("ThesisArtifact debe ser un objeto")
            for field in ("packaging_alignment", "viewer_transformation"):
                value.pop(field, None)
            value.update(
                {
                    "thesis_id": f"{plan['research_plan_id']}:THESIS:PROVISIONAL",
                    "episode_id": plan["episode_id"],
                    "brief_version": plan["brief_version"],
                    "research_id": plan["research_plan_id"],
                    "evidence_report_id": self._source_report_id(context, plan),
                    "stage": "THESIS_PROVISIONAL",
                    "version": CONTRACT_VERSION,
                    "created_at": utc_now(),
                }
            )
        elif stage == "RESEARCH_COMPARISON":
            if not isinstance(value, dict):
                raise ResearchB2Error("ResearchComparison debe ser un objeto")
            value.update(
                {
                    "comparison_id": f"{plan['research_plan_id']}:COMPARISON:INITIAL",
                    "comparison_version": CONTRACT_VERSION,
                    "episode_id": plan["episode_id"],
                    "research_id": plan["research_plan_id"],
                    "decision_stage": "INITIAL_RESEARCH_COMPARISON",
                    "narrative_decision_made": False,
                    "created_at": utc_now(),
                }
            )
        return value

    @staticmethod
    def _project_common_research(
        value: dict[str, Any],
        plan: dict[str, Any],
        context: Mapping[str, Any],
        *,
        include_brief: bool = True,
    ) -> None:
        if not isinstance(value, dict):
            raise ResearchB2Error("La proyección Software requiere un objeto")
        value.update({"research_id": plan["research_plan_id"], "episode_id": plan["episode_id"], "research_contract_version": CONTRACT_VERSION})
        if include_brief:
            value["brief_version"] = plan["brief_version"]

    @staticmethod
    def _source_report_id(context: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
        source_access = context.get("source_access")
        if isinstance(source_access, Mapping) and source_access.get("report_id"):
            return str(source_access["report_id"])
        return f"{plan['research_plan_id']}:SOURCE_ACCESS"

    @staticmethod
    def _validate_phenomenon(value: Any) -> None:
        if not isinstance(value, dict):
            raise ResearchB2Error("ResearchPack debe ser un objeto")
        errors = validate_research_pack(value)
        if errors:
            raise ResearchB2Error(" | ".join(errors))
        if value.get("research_contract_version") != CONTRACT_VERSION:
            raise ResearchB2Error("ResearchPack de fenómeno requiere Research V2")
        if value.get("research_pack_kind") != "PHENOMENON":
            raise ResearchB2Error("La investigación base debe producir un ResearchPack de fenómeno")
        if value.get("research_stage") != "BASE_RESEARCH":
            raise ResearchB2Error("La investigación base no puede saltar de etapa")
        if value.get("thesis_stage", "NONE") != "NONE":
            raise ResearchB2Error("La hipótesis no puede convertirse en tesis provisional durante B2")
        _reject_narrative_fields(value)

    @staticmethod
    def _validate_discovery(value: Any) -> None:
        if not isinstance(value, dict):
            raise ResearchB2Error("WorkLifecycle debe ser un objeto")
        errors = validate_work_lifecycle(value)
        if errors:
            raise ResearchB2Error(" | ".join(errors))
        if value.get("research_contract_version") != CONTRACT_VERSION:
            raise ResearchB2Error("Discovery requiere WorkLifecycle V2")
        works = value.get("works", [])
        if not works:
            raise ResearchB2Error("Discovery debe devolver al menos una candidata")
        if value.get("screening", {}).get("candidate_work_ids") != []:
            raise ResearchB2Error("Discovery no puede convertir una cuota en gate de screening")
        if value.get("final_selection", {}).get("selected_work_ids") != []:
            raise ResearchB2Error("Discovery no puede seleccionar obras finales")
        for work in works:
            if work.get("state") != "DISCOVERED_WORK" or work.get("research_stage") != "DISCOVERY":
                raise ResearchB2Error("Discovery solo puede dejar obras en DISCOVERED_WORK/DISCOVERY")
            if work.get("selection_state") != "NOT_EVALUATED":
                raise ResearchB2Error("Discovery no puede decidir selección")

    @staticmethod
    def _validate_sufficiency(
        value: Any,
        phenomenon: dict[str, Any],
        pool: list[dict[str, Any]],
    ) -> None:
        if not isinstance(value, list) or not value:
            raise ResearchB2Error("INITIAL_SUFFICIENCY debe devolver decisiones no vacías")
        for decision in value:
            if not isinstance(decision, dict):
                raise ResearchB2Error("Cada ResearchStopDecision debe ser un objeto")
            errors = validate_research_stop_decision(decision)
            if errors:
                raise ResearchB2Error(" | ".join(errors))
            if decision.get("sufficiency_status") not in {
                "SUFFICIENT_FOR_INTENDED_USE",
                "LIMITED_BUT_USABLE",
                "MORE_RESEARCH_REQUIRED",
                "BLOCKED_BY_EVIDENCE",
            }:
                raise ResearchB2Error("ResearchStopDecision tiene suficiencia inválida")
            if decision.get("research_contract_version") == CONTRACT_VERSION and decision.get("artifact_validity") != "VALID":
                raise ResearchB2Error("ResearchStopDecision V2 debe ser válido antes de continuar")
        expected = {("PHENOMENON", phenomenon["research_id"])} | {
            ("WORK_RESEARCH_DOSSIER", dossier["dossier_id"])
            for dossier in pool
        }
        received = {(item.get("subject_kind"), item.get("subject_ref")) for item in value}
        if received != expected:
            raise ResearchB2Error("INITIAL_SUFFICIENCY debe vincular exactamente el fenómeno y cada dossier real")

    @staticmethod
    def _sufficiency_allows_thesis(value: list[dict[str, Any]], phenomenon: dict[str, Any]) -> bool:
        phenomenon_decisions = [
            item
            for item in value
            if item.get("subject_kind") == "PHENOMENON" and item.get("subject_ref") == phenomenon.get("research_id")
        ]
        return len(phenomenon_decisions) == 1 and phenomenon_decisions[0].get("sufficiency_status") in {
            "SUFFICIENT_FOR_INTENDED_USE",
            "LIMITED_BUT_USABLE",
        }

    @staticmethod
    def _validate_provisional_thesis(
        value: Any, research: dict[str, Any], evidence_report: Mapping[str, Any]
    ) -> None:
        if not isinstance(value, dict):
            raise ResearchB2Error("ThesisArtifact debe ser un objeto")
        report_errors = validate_source_access_and_evidence_report(dict(evidence_report))
        if report_errors:
            raise ResearchB2Error("SourceAccessAndEvidenceReport inválido: " + " | ".join(report_errors))
        errors = validate_thesis_artifact(value, research, dict(evidence_report))
        if errors:
            raise ResearchB2Error(" | ".join(errors))
        if value.get("stage") != "THESIS_PROVISIONAL":
            raise ResearchB2Error("B2 solo puede producir THESIS_PROVISIONAL")

    @staticmethod
    def _validate_comparison(
        value: Any,
        fidelity: list[dict[str, Any]],
        sufficiency: list[dict[str, Any]],
    ) -> None:
        if not isinstance(value, dict):
            raise ResearchB2Error("ResearchComparison debe ser un objeto")
        if value.get("narrative_decision_made") is not False:
            raise ResearchB2Error("La comparativa investigativa no puede decidir narrativa")
        if value.get("decision_stage") != "INITIAL_RESEARCH_COMPARISON":
            raise ResearchB2Error("B2 solo puede producir INITIAL_RESEARCH_COMPARISON")
        errors = validate_against_schema(value, "research_comparison")
        if errors:
            raise ResearchB2Error(" | ".join(errors))
        work_sufficiency = {
            item["subject_ref"]: item
            for item in sufficiency
            if item.get("subject_kind") == "WORK_RESEARCH_DOSSIER"
        }
        eligible = {
            item["work"]["material_id"]
            for item in fidelity
            if item.get("preliminary_fidelity") != "NO_APTA"
            and work_sufficiency.get(item.get("dossier_id"), {}).get("sufficiency_status")
            in {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE"}
        }
        for item in fidelity:
            if item.get("preliminary_fidelity") != "NO_APTA" and item.get("dossier_id") not in work_sufficiency:
                raise ResearchB2Error("La comparativa requiere ResearchStop correspondiente para cada candidata")
        if set(value.get("candidate_work_ids", [])) != eligible:
            raise ResearchB2Error("La comparativa debe cubrir exactamente las candidatas aptas o con riesgos")
        entry_ids = {item.get("work_id") for item in value.get("entries", [])}
        if entry_ids != eligible:
            raise ResearchB2Error("La comparativa debe tener una entrada por candidata elegible")
        targets = value.get("deepening_targets")
        if not isinstance(targets, Mapping) or not isinstance(targets.get("phenomenon"), Mapping):
            raise ResearchB2Error("RESEARCH_COMPARISON debe aportar targets de profundización cognitivos")
        works = targets.get("works")
        if not isinstance(works, Mapping):
            raise ResearchB2Error("RESEARCH_COMPARISON debe aportar targets por obra")
        target_work_ids = {str(item) for item in works}
        if not target_work_ids.issubset({str(item) for item in eligible}):
            raise ResearchB2Error("RESEARCH_COMPARISON solo puede aportar targets para candidatas elegibles")
        for work_id, target in works.items():
            if not isinstance(target, Mapping) or not isinstance(target.get("targets"), list) or not target["targets"]:
                raise ResearchB2Error(f"RESEARCH_COMPARISON debe aportar targets válidos para {work_id}")

    @staticmethod
    def _validate_pool(value: Any, discovery: dict[str, Any]) -> None:
        if not isinstance(value, list) or not value:
            raise ResearchB2Error("BASE_RESEARCH_POOL debe devolver una lista no vacía")
        discovered = {item["work_id"] for item in discovery["works"]}
        received: set[str] = set()
        for dossier in value:
            if not isinstance(dossier, dict):
                raise ResearchB2Error("Cada dossier debe ser un objeto")
            errors = validate_work_research_dossier(dossier)
            if errors:
                raise ResearchB2Error(" | ".join(errors))
            work_id = dossier["work"]["material_id"]
            if work_id in received:
                raise ResearchB2Error("BASE_RESEARCH_POOL no puede duplicar obras")
            received.add(work_id)
            if dossier.get("research_contract_version") != CONTRACT_VERSION or dossier.get("research_stage") != "BASE_RESEARCH":
                raise ResearchB2Error("Cada dossier debe estar en BASE_RESEARCH V2")
            if dossier.get("preliminary_fidelity") != "NOT_ASSESSED" or dossier.get("thesis_stage") != "NONE":
                raise ResearchB2Error("BASE_RESEARCH_POOL no puede adelantar fidelidad o tesis")
            _reject_narrative_fields(dossier)
        if not received.issubset(discovered):
            raise ResearchB2Error("BASE_RESEARCH_POOL solo puede contener obras del discovery")

    @staticmethod
    def _validate_fidelity(value: Any, pool: list[dict[str, Any]]) -> None:
        if not isinstance(value, list) or not value:
            raise ResearchB2Error("PRELIMINARY_FIDELITY debe devolver una lista no vacía")
        expected = {item["work"]["material_id"] for item in pool}
        received: set[str] = set()
        for dossier in value:
            if not isinstance(dossier, dict):
                raise ResearchB2Error("Cada resultado de fidelidad debe ser un objeto")
            errors = validate_work_research_dossier(dossier)
            if errors:
                raise ResearchB2Error(" | ".join(errors))
            material_id = dossier["work"]["material_id"]
            if material_id in received:
                raise ResearchB2Error("PRELIMINARY_FIDELITY no puede duplicar obras")
            received.add(material_id)
            if dossier.get("research_stage") != "PRELIMINARY_FIDELITY":
                raise ResearchB2Error("La fidelidad preliminar debe declarar su etapa")
            if dossier.get("preliminary_fidelity") not in {"APTA", "APTA_CON_RIESGOS", "NO_APTA"}:
                raise ResearchB2Error("Resultado de fidelidad preliminar inválido")
            if dossier.get("preliminary_fidelity") == "APTA_CON_RIESGOS" and not dossier.get("downstream_restrictions"):
                raise ResearchB2Error("APTA_CON_RIESGOS requiere restricciones downstream explícitas")
            if dossier.get("thesis_stage") != "NONE":
                raise ResearchB2Error("La fidelidad preliminar no puede producir tesis")
            _reject_narrative_fields(dossier)
        if received != expected:
            raise ResearchB2Error("La fidelidad preliminar debe cubrir exactamente el pool")

    @staticmethod
    def _bind_fidelity_to_lifecycle(
        discovery: dict[str, Any], fidelity: list[dict[str, Any]], fidelity_ref: dict[str, str]
    ) -> dict[str, Any]:
        by_work = {item["work"]["material_id"]: item for item in fidelity}
        result = copy.deepcopy(discovery)
        for work in result["works"]:
            if work["work_id"] not in by_work:
                # Discovery remains the source of truth for works filtered out
                # before base research; no fidelity is required for them.
                continue
            dossier = by_work[work["work_id"]]
            work.update(
                {
                    "research_stage": "PRELIMINARY_FIDELITY",
                    "selection_state": "CANDIDATE",
                    "preliminary_fidelity": dossier["preliminary_fidelity"],
                    "deep_fidelity": "NOT_ASSESSED",
                    "research_sufficiency": dossier.get("research_sufficiency", "MORE_RESEARCH_REQUIRED"),
                    "artifact_validity": "VALID",
                    "thesis_stage": "NONE",
                    "research_contract_version": CONTRACT_VERSION,
                    "dossier_ref": f"{fidelity_ref['artifact_id']}#{dossier['dossier_id']}",
                    "stage_evidence_refs": sorted(set(work.get("stage_evidence_refs", [])) | {fidelity_ref["artifact_id"]}),
                }
            )
        errors = validate_work_lifecycle(result)
        if errors:
            raise ResearchB2Error("Lifecycle B2 inválido: " + " | ".join(errors))
        return result


def _reject_narrative_fields(value: Mapping[str, Any]) -> None:
    present = sorted(NARRATIVE_FIELDS.intersection(value))
    if present:
        raise ResearchB2Error("Research B2 no puede decidir narrativa: " + ", ".join(present))


def _state_of(value: Any) -> str:
    if isinstance(value, dict):
        for field in ("research_stage", "sufficiency_status", "stage", "decision_stage"):
            if value.get(field):
                return str(value[field])
        if value.get("works"):
            return "WORKS:" + ",".join(sorted(str(item.get("work_id")) for item in value["works"] if isinstance(item, dict)))
    if isinstance(value, list):
        return "LIST:" + ",".join(sorted(_state_of(item) for item in value))
    return type(value).__name__


def _checksum(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
