"""Deterministic B3/M4 routing for Research V2.

M4 extends the sequential B2 boundary without invoking a provider.  Human
or delegated selection, deep research, deep fidelity and ResearchStop
decisions all return to Software before they are accepted or persisted.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from src.ai.role_execution import resolve_role_execution_contract
from src.application.interaction import (
    HumanDecision,
    HumanDecisionRequest,
    validate_human_decision,
)
from src.application.research_b2 import (
    B2CognitiveRequest,
    CONTRACT_VERSION,
    ResearchB2Error,
    ResearchB2NoProgressGuard,
    ResearchB2Persistence,
    SoftwareAcquisitionAdapter,
    _checksum,
    utc_now,
)
from src.core.contract_validation import (
    validate_against_schema,
    validate_research_pack,
    validate_research_plan,
    validate_research_stop_decision,
    validate_work_lifecycle,
    validate_work_research_dossier,
)


ROLE_ID = "RESEARCH_AND_CURATION"
M4_CONTRACT_VERSION = CONTRACT_VERSION
POSITIVE_STOP_STATUSES = {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE"}
DEEP_FIDELITY_STATUSES = {
    "APROBADA",
    "APROBADA_CON_LIMITES",
    "MAS_INVESTIGACION_REQUERIDA",
    "NO_APROBADA",
}
DEEP_PHENOMENON_USE = "DEEP_PHENOMENON_RESEARCH"
DEEP_WORK_USE = "DEEP_WORK_RESEARCH"

# These values belong to Software.  Cognitive text can propose content, but
# it cannot bring identity, lifecycle, acquisition or provenance authority.
SOFTWARE_OWNED_FIELDS = {
    "artifact_id",
    "artifact_version",
    "dossier_id",
    "dossier_version",
    "decision_id",
    "decision_version",
    "lifecycle_id",
    "lifecycle_version",
    "thesis_id",
    "version",
    "created_at",
    "artifact_validity",
    "research_contract_version",
    "lineage",
    "acquisition_bindings",
    "software_controlled",
    "recovery_artifact_ref",
    "retrieval_request_ref",
    "request_ref",
    "execution_ref",
    "checksum",
    "checksums",
    "provenance",
    "operational_guard_ref",
    "research_stop_decision_ref",
    "research_id",
    "episode_id",
    "evidence_report_id",
}


class ResearchB3Error(ResearchB2Error):
    """A deterministic M4 contract, routing or boundary failure."""


class ResearchB3Persistence(ResearchB2Persistence):
    """M4 persistence extension over the atomic B2 persistence adapter."""

    _FILENAMES = {
        **ResearchB2Persistence._FILENAMES,
        "M4_SELECTION_REQUEST": "m4_selection_request.json",
        "M4_SELECTION_DECISION": "m4_selection_decision.json",
        "M4_DELEGATION_DECISION": "m4_delegation_decision.json",
        "DEEP_PHENOMENON_RESEARCH": "deep_phenomenon_research.json",
        "DEEP_PHENOMENON_SUFFICIENCY": "deep_phenomenon_sufficiency.json",
        "DEEP_WORK_RESEARCH": "deep_work_research.json",
        "DEEP_FIDELITY": "deep_fidelity.json",
        "DEEP_WORK_SUFFICIENCY": "deep_work_sufficiency.json",
        "M4_EXECUTION_MANIFEST": "research_m4_execution.json",
    }


@dataclass(frozen=True)
class M4Selection:
    """Software-owned result of the selection boundary."""

    selected_work_ids: tuple[str, ...]
    mode: str
    authority_ref: str


def _strip_cognitive_technical(value: Any) -> Any:
    """Remove technical authority from an injected cognitive projection."""
    if isinstance(value, dict):
        return {
            key: _strip_cognitive_technical(item)
            for key, item in value.items()
            if key not in SOFTWARE_OWNED_FIELDS
        }
    if isinstance(value, list):
        return [_strip_cognitive_technical(item) for item in value]
    return copy.deepcopy(value)


def _as_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResearchB3Error(f"{label}_MUST_BE_OBJECT")
    return copy.deepcopy(dict(value))


def _as_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value or not all(isinstance(item, Mapping) for item in value):
        raise ResearchB3Error(f"{label}_MUST_BE_NON_EMPTY_OBJECT_LIST")
    return [copy.deepcopy(dict(item)) for item in value]


_EVIDENCE_REFERENCE_FIELDS = frozenset(
    {
        "evidence_refs",
        "work_evidence_refs",
        "external_reality_evidence_refs",
        "source_refs",
        "stage_evidence_refs",
    }
)


def _evidence_reference_values(value: Any) -> set[str]:
    """Collect only references explicitly declared as evidence by artifacts.

    Technical identifiers are deliberately excluded.  An ``*_id`` or generic
    ``*_ref`` field can identify an artifact or execution without being
    evidence for a claim.
    """
    found: set[str] = set()

    def collect(item: Any) -> None:
        if isinstance(item, str) and item.strip():
            found.add(item.strip())
        elif isinstance(item, list):
            for entry in item:
                collect(entry)

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, item in node.items():
                if str(key) in _EVIDENCE_REFERENCE_FIELDS:
                    collect(item)
                visit(item)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    return found


def _valid_acquisition_reference_values(bindings: Mapping[str, Mapping[str, Any]], *, include_keys: bool = False) -> set[str]:
    """Return evidence refs from valid Software-owned acquisition bindings."""
    found: set[str] = set()
    for key, binding in bindings.items():
        if (
            binding.get("retrieval_status") == "RECOVERED"
            and binding.get("software_controlled") is True
            and binding.get("recovery_artifact_ref")
            and binding.get("evidence_status") in {"CONSULTED", "VERIFIED", "EVIDENCE"}
        ):
            if binding.get("source_ref"):
                found.add(str(binding["source_ref"]))
            if binding.get("evidence_ref"):
                found.add(str(binding["evidence_ref"]))
            if binding.get("recovery_artifact_ref"):
                found.add(str(binding["recovery_artifact_ref"]))
            if include_keys and key:
                found.add(str(key))
    return found


class ResearchB3Orchestrator:
    """Run the first half of B3 sequentially and without real AI."""

    def __init__(
        self,
        cognitive_executor: Callable[[B2CognitiveRequest], Any],
        persistence: ResearchB3Persistence,
        *,
        acquisition_adapter: SoftwareAcquisitionAdapter | None = None,
        no_progress_guard: ResearchB2NoProgressGuard | None = None,
    ):
        if not callable(cognitive_executor):
            raise ResearchB3Error("M4_COGNITIVE_EXECUTOR_REQUIRED")
        self.cognitive_executor = cognitive_executor
        self.persistence = persistence
        self.acquisition_adapter = acquisition_adapter or SoftwareAcquisitionAdapter()
        self.no_progress_guard = no_progress_guard or ResearchB2NoProgressGuard()

    def run(
        self,
        baseline: Mapping[str, Any],
        *,
        context: Mapping[str, Any],
        selection_mode: str = "USER_SELECTION",
        human_decision: HumanDecision | Mapping[str, Any] | None = None,
        delegation_decision: Mapping[str, Any] | None = None,
        selection_options: Sequence[Sequence[str]] | None = None,
    ) -> dict[str, Any]:
        """Execute selection, deep research and deep fidelity.

        ``baseline`` contains already materialized B2 artifacts, not paths or
        provider responses.  The executor is intentionally injected so tests
        can prove the boundary without executing real research.
        """
        data = _as_dict(baseline, "M4_BASELINE")
        ctx = _as_dict(context, "M4_CONTEXT")
        plan = _as_dict(data.get("research_plan"), "RESEARCH_PLAN")
        phenomenon = _as_dict(data.get("phenomenon_base_research"), "PHENOMENON_BASE_RESEARCH")
        discovery = _as_dict(data.get("work_discovery"), "WORK_DISCOVERY")
        pool = _as_list(data.get("base_research_pool"), "BASE_RESEARCH_POOL")
        fidelity = _as_list(data.get("preliminary_fidelity"), "PRELIMINARY_FIDELITY")
        sufficiency = _as_list(data.get("initial_sufficiency"), "INITIAL_SUFFICIENCY")
        if data.get("provisional_thesis") is None:
            raise ResearchB3Error("PROVISIONAL_THESIS_REQUIRED")
        provisional_thesis = _as_dict(data.get("provisional_thesis"), "PROVISIONAL_THESIS")
        research_comparison = _as_dict(data.get("research_comparison"), "RESEARCH_COMPARISON")
        deepening_targets = data.get("deepening_targets")
        if deepening_targets is None and isinstance(data.get("b2_execution_manifest"), Mapping):
            deepening_targets = data["b2_execution_manifest"].get("deepening_targets")
        lifecycle = _as_dict(data.get("lifecycle"), "LIFECYCLE")
        known_evidence_refs = _evidence_reference_values(data)
        known_evidence_refs.update(_valid_acquisition_reference_values(self.acquisition_adapter.bindings))
        known_evidence_refs.update(_valid_acquisition_reference_values(self.acquisition_adapter.work_bindings))
        known_evidence_refs.update(_valid_acquisition_reference_values(self.acquisition_adapter.work_representation_bindings))
        ctx["_known_evidence_refs"] = known_evidence_refs
        self._validate_baseline(
            plan, phenomenon, discovery, pool, fidelity, sufficiency,
            provisional_thesis, research_comparison, deepening_targets, lifecycle, ctx,
        )

        candidate_ids = self._eligible_candidates(pool, fidelity, sufficiency)
        events: list[dict[str, Any]] = []
        selection = self._materialize_selection(
            plan,
            lifecycle,
            candidate_ids,
            ctx,
            provisional_thesis,
            research_comparison,
            deepening_targets,
            events,
            selection_mode=selection_mode,
            human_decision=human_decision,
            delegation_decision=delegation_decision,
            selection_options=selection_options,
            known_evidence_refs=known_evidence_refs,
        )
        selected_ids = list(selection.selected_work_ids)
        for work_id in selected_ids:
            if not self._targets_for_work(deepening_targets, work_id):
                raise ResearchB3Error(f"WORK_DEEPENING_TARGETS_REQUIRED: {work_id}")
        selected_pool = [item for item in fidelity if item["work"]["material_id"] in selected_ids]
        by_work = {item["work"]["material_id"]: item for item in selected_pool}

        selection_ref = self.persistence.persist(
            "M4_SELECTION_REQUEST" if selection.mode == "USER_SELECTION" else "M4_DELEGATION_DECISION",
            self._selection_artifact,
            artifact_id=f"{plan['research_plan_id']}:M4:SELECTION_AUTHORITY",
            artifact_kind="HumanDecisionRequest" if selection.mode == "USER_SELECTION" else "DelegationDecision",
        )
        events.append({"stage": "SELECTION", "boundary": "SOFTWARE_PERSIST", "artifact_id": selection_ref["artifact_id"]})
        if selection.mode == "USER_SELECTION":
            decision_ref = self.persistence.persist(
                "M4_SELECTION_DECISION",
                self._decision_artifact,
                artifact_id=f"{plan['research_plan_id']}:M4:HUMAN_DECISION",
                artifact_kind="HumanDecision",
            )
            events.append({"stage": "SELECTION", "boundary": "SOFTWARE_PERSIST", "artifact_id": decision_ref["artifact_id"]})
            selection_authority_ref = decision_ref["artifact_id"]
        else:
            selection_decision_ref = self.persistence.persist(
                "M4_SELECTION_DECISION",
                self._delegated_selection_artifact,
                artifact_id=f"{plan['research_plan_id']}:M4:DELEGATED_SELECTION",
                artifact_kind="DelegatedSelectionDecision",
            )
            events.append({"stage": "SELECTION", "boundary": "SOFTWARE_PERSIST", "artifact_id": selection_decision_ref["artifact_id"]})
            selection_authority_ref = selection_decision_ref["artifact_id"]

        input_artifacts = [
            self._artifact_ref(phenomenon, "ResearchPack"),
            self._artifact_ref(discovery, "WorkLifecycle"),
            {"artifact_id": f"{plan['research_plan_id']}:PRELIMINARY_FIDELITY", "artifact_kind": "WorkResearchDossierCollection"},
            self._artifact_ref(provisional_thesis, "ThesisArtifact"),
            self._artifact_ref(research_comparison, "ResearchComparison"),
            {"artifact_id": f"{plan['research_plan_id']}:DEEPENING_TARGETS", "artifact_kind": "B2DeepeningTargets"},
            {"artifact_id": selection_authority_ref, "artifact_kind": "SelectionAuthority"},
        ]
        deep_phenomenon = self._step(
            "DEEP_PHENOMENON_RESEARCH",
            "research_pack",
            plan,
            ctx,
            input_artifacts,
            events,
            lambda value: self._validate_deep_phenomenon(value, phenomenon, provisional_thesis),
            base_research=phenomenon,
            stage_payload={
                "provisional_thesis": provisional_thesis,
                "research_comparison": research_comparison,
                "deepening_targets": deepening_targets,
                "base_research": phenomenon,
                "intended_use": plan.get("intended_use"),
            },
        )
        deep_phenomenon_ref = self.persistence.persist(
            "DEEP_PHENOMENON_RESEARCH",
            deep_phenomenon,
            artifact_id=f"{plan['research_plan_id']}:DEEP_PHENOMENON",
            artifact_kind="ResearchPack",
        )
        events.append({"stage": "DEEP_PHENOMENON_RESEARCH", "boundary": "SOFTWARE_PERSIST", "artifact_id": deep_phenomenon_ref["artifact_id"]})

        phenomenon_stop = self._step(
            "DEEP_PHENOMENON_SUFFICIENCY",
            "research_stop_decision",
            plan,
            ctx,
            [deep_phenomenon_ref],
            events,
            lambda value: self._validate_stop(
                value, "PHENOMENON", deep_phenomenon["research_id"],
                expected_intended_use=DEEP_PHENOMENON_USE,
            ),
            subject_kind="PHENOMENON",
            subject_ref=deep_phenomenon["research_id"],
            expected_intended_use=DEEP_PHENOMENON_USE,
        )
        phenomenon_stop_ref = self.persistence.persist(
            "DEEP_PHENOMENON_SUFFICIENCY",
            phenomenon_stop,
            artifact_id=f"{plan['research_plan_id']}:M4:RSD:PHENOMENON",
            artifact_kind="ResearchStopDecision",
        )

        deep_research: list[dict[str, Any]] = []
        for work_id in selected_ids:
            dossier = self._step(
                "DEEP_WORK_RESEARCH",
                "work_research_dossier",
                plan,
                ctx,
                [
                    selection_ref,
                    self._artifact_ref(by_work[work_id], "WorkResearchDossier"),
                    self._artifact_ref(provisional_thesis, "ThesisArtifact"),
                    self._artifact_ref(research_comparison, "ResearchComparison"),
                    {"artifact_id": f"{plan['research_plan_id']}:DEEPENING_TARGETS:{work_id}", "artifact_kind": "B2DeepeningTargets"},
                ],
                events,
                lambda value, work_id=work_id: self._validate_deep_dossier(
                    value, work_id, known_evidence_refs=known_evidence_refs
                ),
                work_id=work_id,
                base_dossier=by_work[work_id],
                stage_payload={
                    "provisional_thesis": provisional_thesis,
                    "research_comparison": research_comparison,
                    "deepening_targets": self._targets_for_work(deepening_targets, work_id),
                    "base_dossier": by_work[work_id],
                    "preliminary_risks": by_work[work_id].get("downstream_restrictions", []),
                    "intended_use": plan.get("intended_use"),
                },
                expected_intended_use=DEEP_WORK_USE,
            )
            deep_research.append(dossier)
        deep_research_ref = self.persistence.persist(
            "DEEP_WORK_RESEARCH",
            deep_research,
            artifact_id=f"{plan['research_plan_id']}:DEEP_WORK_RESEARCH",
            artifact_kind="WorkResearchDossierCollection",
        )

        deep_fidelity: list[dict[str, Any]] = []
        for dossier in deep_research:
            work_id = dossier["work"]["material_id"]
            result = self._step(
                "DEEP_FIDELITY",
                "work_research_dossier",
                plan,
                ctx,
                [deep_research_ref],
                events,
                lambda value, work_id=work_id: self._validate_deep_fidelity(
                    value, work_id, known_evidence_refs=known_evidence_refs
                ),
                work_id=work_id,
                base_dossier=dossier,
                stage_payload={
                    "provisional_thesis": provisional_thesis,
                    "research_comparison": research_comparison,
                    "deepening_targets": self._targets_for_work(deepening_targets, work_id),
                    "base_dossier": dossier,
                    "preliminary_risks": dossier.get("downstream_restrictions", []),
                    "intended_use": plan.get("intended_use"),
                },
                expected_intended_use=DEEP_WORK_USE,
            )
            deep_fidelity.append(result)
        deep_fidelity_ref = self.persistence.persist(
            "DEEP_FIDELITY",
            deep_fidelity,
            artifact_id=f"{plan['research_plan_id']}:DEEP_FIDELITY",
            artifact_kind="WorkResearchDossierCollection",
        )

        work_stops: list[dict[str, Any]] = []
        for dossier in deep_fidelity:
            work_id = dossier["work"]["material_id"]
            stop = self._step(
                "DEEP_WORK_SUFFICIENCY",
                "research_stop_decision",
                plan,
                ctx,
                [deep_fidelity_ref],
                events,
                lambda value, dossier=dossier: self._validate_stop(
                    value, "WORK_RESEARCH_DOSSIER", dossier["dossier_id"],
                    expected_intended_use=DEEP_WORK_USE,
                    expected_deep_fidelity=dossier.get("deep_fidelity"),
                ),
                subject_kind="WORK_RESEARCH_DOSSIER",
                subject_ref=dossier["dossier_id"],
                work_id=work_id,
                deep_fidelity=dossier["deep_fidelity"],
                expected_intended_use=DEEP_WORK_USE,
            )
            work_stops.append(stop)
        work_stops_ref = self.persistence.persist(
            "DEEP_WORK_SUFFICIENCY",
            work_stops,
            artifact_id=f"{plan['research_plan_id']}:M4:RSD:WORKS",
            artifact_kind="ResearchStopDecisionCollection",
        )

        manifest = {
            "manifest_type": "RESEARCH_M4_EXECUTION",
            "manifest_version": M4_CONTRACT_VERSION,
            "status": "READY_FOR_OWNER_REVIEW",
            "real_ai_execution": False,
            "real_research": False,
            "product_use": False,
            "m5_outputs_not_produced": True,
            "selection": {
                "mode": selection.mode,
                "selected_work_ids": selected_ids,
                "candidate_work_ids": sorted(candidate_ids),
                "authority_ref": selection_authority_ref,
                "final_narrative_selection": False,
            },
            "stage_order": [
                "SELECTION",
                "DEEP_PHENOMENON_RESEARCH",
                "DEEP_PHENOMENON_SUFFICIENCY",
                "DEEP_WORK_RESEARCH",
                "DEEP_FIDELITY",
                "DEEP_WORK_SUFFICIENCY",
            ],
            "artifacts": [
                selection_ref,
                deep_phenomenon_ref,
                phenomenon_stop_ref,
                deep_research_ref,
                deep_fidelity_ref,
                work_stops_ref,
            ],
            "events": events,
            "iteration_guard": self.no_progress_guard.to_dict(),
            "work_acquisition_bindings": self.acquisition_adapter.work_binding_manifest(),
            "b2_inputs": {
                "provisional_thesis_ref": self._artifact_ref(provisional_thesis, "ThesisArtifact"),
                "research_comparison_ref": self._artifact_ref(research_comparison, "ResearchComparison"),
                "deepening_targets": copy.deepcopy(deepening_targets),
            },
            "scope_outcomes": [
                self._scope_outcome("PHENOMENON", deep_phenomenon["research_id"], phenomenon_stop),
                *[
                    self._scope_outcome("WORK_RESEARCH_DOSSIER", stop["subject_ref"], stop)
                    for stop in work_stops
                ],
            ],
            "selected_lifecycle_projection": self._project_lifecycle_deep(
                lifecycle, selected_ids, candidate_ids, selection_authority_ref,
                deep_fidelity, work_stops, deep_fidelity_ref, research_comparison,
                provisional_thesis,
            ),
            "downstream_restrictions_preserved": [
                restriction
                for dossier in deep_fidelity
                for restriction in dossier.get("downstream_restrictions", [])
            ],
        }
        manifest_ref = self.persistence.persist(
            "M4_EXECUTION_MANIFEST",
            manifest,
            artifact_id=f"{plan['research_plan_id']}:M4",
            artifact_kind="ResearchM4ExecutionManifest",
        )
        return {
            "selection": self._project_lifecycle_deep(
                lifecycle, selected_ids, candidate_ids, selection_authority_ref,
                deep_fidelity, work_stops, deep_fidelity_ref, research_comparison,
                provisional_thesis,
            ),
            "deep_phenomenon_research": deep_phenomenon_ref,
            "deep_phenomenon_sufficiency": phenomenon_stop_ref,
            "deep_work_research": deep_research_ref,
            "deep_fidelity": deep_fidelity_ref,
            "deep_work_sufficiency": work_stops_ref,
            "execution_manifest": manifest_ref,
            "events": events,
        }

    def _step(
        self,
        stage: str,
        output_schema: str,
        plan: dict[str, Any],
        context: Mapping[str, Any],
        input_artifacts: list[dict[str, Any]],
        events: list[dict[str, Any]],
        validator: Callable[[Any], None],
        *,
        subject_kind: str | None = None,
        subject_ref: str | None = None,
        work_id: str | None = None,
        base_dossier: dict[str, Any] | None = None,
        base_research: dict[str, Any] | None = None,
        deep_fidelity: str | None = None,
        stage_payload: Mapping[str, Any] | None = None,
        expected_intended_use: str | None = None,
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
            "selected_work_ids": list(context.get("selected_work_ids", [])),
            "work_id": work_id,
            "subject_kind": subject_kind,
            "subject_ref": subject_ref,
            "deep_fidelity": deep_fidelity,
        }
        if stage_payload:
            input_payload.update(copy.deepcopy(dict(stage_payload)))
        prepared = resolve_role_execution_contract(
            ROLE_ID,
            output_schema,
            input_payload,
            {"stage": stage, "real_ai_execution": False, "real_research": False},
        )
        request = B2CognitiveRequest(stage, output_schema, tuple(copy.deepcopy(input_artifacts)), prepared)
        events.append({"stage": stage, "boundary": "IA_COGNITIVE_STEP", "output_schema": output_schema})
        output = self.cognitive_executor(request)
        output = self._software_project(
            stage,
            output,
            plan,
            context,
            base_dossier=base_dossier,
            base_research=base_research,
            subject_kind=subject_kind,
            subject_ref=subject_ref,
            work_id=work_id,
            expected_intended_use=expected_intended_use,
            stage_payload=stage_payload,
        )
        try:
            validator(output)
        except (TypeError, KeyError, ValueError) as exc:
            raise ResearchB3Error(f"{stage}_OUTPUT_INVALID: {exc}") from exc
        events.append({"stage": stage, "boundary": "SOFTWARE_VALIDATE", "validated": True})
        guard = self.no_progress_guard.observe(
            gap=f"M4:{stage}:{work_id or subject_ref or ''}",
            evidence_refs=[str(item["artifact_id"]) for item in input_artifacts],
            state=_state_of(output),
            result=output,
        )
        events.append({"stage": stage, "boundary": "SOFTWARE_ITERATION_GUARD", **guard.__dict__})
        if guard.status == "NO_PROGRESS":
            raise ResearchB3Error(f"{stage}_NO_PROGRESS: {guard.reason}:{guard.route}")
        return output

    def _software_project(
        self,
        stage: str,
        output: Any,
        plan: dict[str, Any],
        context: Mapping[str, Any],
        *,
        base_dossier: dict[str, Any] | None,
        base_research: dict[str, Any] | None,
        subject_kind: str | None,
        subject_ref: str | None,
        work_id: str | None,
        expected_intended_use: str | None,
        stage_payload: Mapping[str, Any] | None,
    ) -> Any:
        cognitive = _strip_cognitive_technical(output)
        if stage == "DEEP_PHENOMENON_RESEARCH":
            value = _as_dict(cognitive, stage)
            base_sources = {
                str(item.get("source_id")): item
                for item in (base_research or {}).get("source_registry", [])
                if isinstance(item, Mapping) and item.get("source_id")
            }
            for source in value.get("source_registry", []):
                if isinstance(source, dict) and source.get("source_id") in base_sources:
                    # Provenance is carried forward from the already
                    # materialized B2 source record, never trusted from IA.
                    source["provenance"] = copy.deepcopy(base_sources[source["source_id"]].get("provenance"))
            value = self.acquisition_adapter.materialize(value)
            value.update(
                {
                    "research_id": plan["research_plan_id"],
                    "episode_id": plan["episode_id"],
                    "brief_version": plan["brief_version"],
                    "research_contract_version": M4_CONTRACT_VERSION,
                    "research_stage": "DEEP_RESEARCH",
                    "artifact_validity": "VALID",
                    "thesis_stage": "PROVISIONAL",
                    "created_at": utc_now(),
                    "phenomenon_research_stop_decision_ref": f"{plan['research_plan_id']}:M4:RSD:PHENOMENON",
                }
            )
            thesis = stage_payload.get("provisional_thesis") if isinstance(stage_payload, Mapping) else None
            thesis_id = thesis.get("thesis_id") if isinstance(thesis, Mapping) else None
            value["lineage"] = sorted(
                set(value.get("lineage", [])) | {f"software:thesis:{thesis_id}"}
            )
            self._validate_known_evidence_refs(value, context, "DEEP_PHENOMENON_RESEARCH")
            return value
        if stage in {"DEEP_WORK_RESEARCH", "DEEP_FIDELITY"}:
            if base_dossier is None or not isinstance(cognitive, Mapping):
                raise ResearchB3Error(f"{stage}_BASE_DOSSIER_REQUIRED")
            cognitive_work = cognitive.get("work")
            if isinstance(cognitive_work, Mapping):
                if cognitive_work.get("material_id") != work_id:
                    raise ResearchB3Error("SELECTED_WORK_SUBSTITUTION_FORBIDDEN")
            value = copy.deepcopy(base_dossier)
            for key, item in cognitive.items():
                if key not in {"work", "dossier_id", "dossier_version", "episode_id", "research_id", "evidence_report_id"}:
                    value[key] = copy.deepcopy(item)
            if isinstance(cognitive_work, Mapping):
                # The adapter below decides whether a changed/new locator is
                # backed by a real Software acquisition binding.
                value["work"] = copy.deepcopy(dict(cognitive_work))
            actual_work_id = str(value.get("work", {}).get("material_id") or "")
            if actual_work_id != work_id:
                raise ResearchB3Error("SELECTED_WORK_SUBSTITUTION_FORBIDDEN")
            try:
                value = self.acquisition_adapter.materialize_work_dossiers([value])[0]
            except ResearchB2Error as exc:
                raise ResearchB3Error(str(exc)) from exc
            relation = value.get("provisional_thesis_relation")
            thesis = stage_payload.get("provisional_thesis") if isinstance(stage_payload, Mapping) else None
            thesis_id = thesis.get("thesis_id") if isinstance(thesis, Mapping) else None
            if not isinstance(relation, Mapping) or relation.get("thesis_ref") != thesis_id:
                raise ResearchB3Error("PROVISIONAL_THESIS_BINDING_MISMATCH")
            value.update(
                {
                    "dossier_id": f"{plan['research_plan_id']}:M4:DOSSIER:{work_id}",
                    "dossier_version": M4_CONTRACT_VERSION,
                    "episode_id": plan["episode_id"],
                    "research_id": plan["research_plan_id"],
                    "evidence_report_id": self._source_report_id(context, plan),
                    "created_at": utc_now(),
                    "research_stage": "DEEP_RESEARCH" if stage == "DEEP_WORK_RESEARCH" else "DEEP_FIDELITY",
                    "selection_state": "SELECTED",
                    "artifact_validity": "VALID",
                    "research_contract_version": M4_CONTRACT_VERSION,
                    "thesis_stage": "PROVISIONAL",
                }
            )
            value["lineage"] = sorted(
                set(base_dossier.get("lineage", []))
                | {
                    f"software:m4:{stage.lower()}",
                    f"software:selection:{plan['research_plan_id']}",
                    f"software:work-acquisition:{work_id}",
                    f"software:thesis:{thesis_id}",
                }
            )
            self._validate_known_evidence_refs(value, context, stage)
            return value
        if stage in {"DEEP_PHENOMENON_SUFFICIENCY", "DEEP_WORK_SUFFICIENCY"}:
            value = _as_dict(cognitive, stage)
            if expected_intended_use and value.get("intended_use") != expected_intended_use:
                raise ResearchB3Error("RESEARCH_STOP_INTENDED_USE_MISMATCH")
            value.update(
                {
                    "decision_id": f"{plan['research_plan_id']}:M4:RSD:{subject_kind}:{subject_ref}",
                    "decision_version": M4_CONTRACT_VERSION,
                    "subject_kind": subject_kind,
                    "subject_ref": subject_ref,
                    "research_contract_version": M4_CONTRACT_VERSION,
                    "artifact_validity": "VALID",
                    "research_stage": "DEEP_RESEARCH",
                    "operational_guard_ref": f"software:iteration-guard:{plan['research_plan_id']}",
                }
            )
            return value
        raise ResearchB3Error(f"M4_UNKNOWN_STAGE: {stage}")

    def _materialize_selection(
        self,
        plan: dict[str, Any],
        lifecycle: dict[str, Any],
        candidate_ids: set[str],
        context: dict[str, Any],
        provisional_thesis: dict[str, Any],
        research_comparison: dict[str, Any],
        deepening_targets: Any,
        events: list[dict[str, Any]],
        *,
        selection_mode: str,
        human_decision: HumanDecision | Mapping[str, Any] | None,
        delegation_decision: Mapping[str, Any] | None,
        selection_options: Sequence[Sequence[str]] | None,
        known_evidence_refs: set[str],
    ) -> M4Selection:
        mode = str(selection_mode).upper()
        context["provisional_thesis"] = copy.deepcopy(provisional_thesis)
        context["research_comparison"] = copy.deepcopy(research_comparison)
        context["deepening_targets"] = copy.deepcopy(deepening_targets)
        options = self._selection_options(candidate_ids, selection_options)
        if mode == "USER_SELECTION":
            request_options = tuple(
                {"id": self._selection_option_id(option), "label": ", ".join(option)} for option in options
            )
            recommendation = request_options[0]["id"]
            request = HumanDecisionRequest(
                request_id=f"{plan['research_plan_id']}:M4:SELECTION_REQUEST",
                prompt="Seleccionar las obras que pasarán a investigación profunda.",
                options=request_options,
                recommendation=recommendation,
                episode_id=plan["episode_id"],
                subject_ref=str(lifecycle["lifecycle_id"]),
                subject_version=str(lifecycle.get("lifecycle_version", M4_CONTRACT_VERSION)),
                subject_checksum=_checksum(lifecycle),
                workflow_ref=str(lifecycle["lifecycle_id"]),
                expected_actor_ref="OWNER",
                expected_channel="TERMINAL",
            )
            if human_decision is None:
                raise ResearchB3Error("HUMAN_SELECTION_REQUIRED")
            decision = human_decision
            if isinstance(decision, Mapping):
                decision = HumanDecision.from_dict(dict(decision))
            if not isinstance(decision, HumanDecision):
                raise ResearchB3Error("HUMAN_SELECTION_DECISION_INVALID")
            bound = decision.bind_request(request)
            try:
                validate_human_decision(request, bound, plan["episode_id"])
            except (TypeError, ValueError, PermissionError) as exc:
                raise ResearchB3Error(f"HUMAN_SELECTION_INVALID: {exc}") from exc
            if bound.action == "APPROVE":
                option_id = recommendation
            elif bound.action == "SELECT_ALTERNATIVE":
                option_id = bound.selected_option
            else:
                raise ResearchB3Error(f"HUMAN_SELECTION_NOT_ACCEPTED: {bound.action}")
            selected = self._parse_selection_option(option_id, candidate_ids)
            self._validate_selection_target_policy(plan, selected, mode, bound, None)
            self._selection_artifact = request.to_dict()
            self._decision_artifact = bound.to_dict()
            context["selected_work_ids"] = selected
            return M4Selection(tuple(selected), mode, f"{plan['research_plan_id']}:M4:HUMAN_DECISION")

        if mode == "DELEGATED_SELECTION":
            target = plan.get("target_final_works_decision") if isinstance(plan.get("target_final_works_decision"), Mapping) else {}
            if target.get("status") not in {"CONFIRMED", "DELEGATED"}:
                raise ResearchB3Error("TARGET_FINAL_WORKS_RESOLUTION_REQUIRED")
            if not isinstance(delegation_decision, Mapping):
                raise ResearchB3Error("DELEGATION_DECISION_REQUIRED")
            delegation = copy.deepcopy(dict(delegation_decision))
            errors = validate_against_schema(delegation, "delegation_decision")
            if errors:
                raise ResearchB3Error("DELEGATION_DECISION_INVALID: " + " | ".join(errors))
            if delegation.get("decision") != "DELEGATE":
                raise ResearchB3Error("DELEGATED_SELECTION_REQUIRES_EXPLICIT_DELEGATE")
            authorized = {str(item) for item in delegation.get("authorized_candidate_set", [])}
            if not authorized or not authorized.issubset(candidate_ids):
                raise ResearchB3Error("DELEGATED_SELECTION_SCOPE_INVALID")
            selection_payload = {
                "topic": context["topic"],
                "source_access": context["source_access"],
                "brief": context["brief"],
                "channel_context": context["channel_context"],
                "research_plan": plan,
                "provisional_thesis": context["provisional_thesis"],
                "research_comparison": context["research_comparison"],
                "deepening_targets": context["deepening_targets"],
                "eligible_candidate_ids": sorted(candidate_ids),
                "authorized_candidate_set": sorted(authorized),
                "selection_options": [list(option) for option in self._selection_options(authorized, selection_options)],
                "selection_policy": plan.get("selection_policy"),
                "target_final_works_decision": plan.get("target_final_works_decision"),
                "stage": "DELEGATED_SELECTION",
            }
            prepared = resolve_role_execution_contract(
                ROLE_ID,
                "work_lifecycle",
                selection_payload,
                {"stage": "DELEGATED_SELECTION", "real_ai_execution": False, "real_research": False},
            )
            delegated_request = B2CognitiveRequest(
                "DELEGATED_SELECTION",
                "work_lifecycle",
                tuple({"artifact_id": f"{plan['research_plan_id']}:RESEARCH_COMPARISON", "artifact_kind": "ResearchComparison"} for _ in [0]),
                prepared,
            )
            events.append({"stage": "DELEGATED_SELECTION", "boundary": "SOFTWARE_PREPARE"})
            events.append({"stage": "DELEGATED_SELECTION", "boundary": "IA_COGNITIVE_STEP", "output_schema": "work_lifecycle"})
            cognitive_selection = self.cognitive_executor(delegated_request)
            selected, selection_metadata = self._extract_delegated_selection(
                cognitive_selection, authorized, known_evidence_refs
            )
            events.append({
                "stage": "DELEGATED_SELECTION",
                "boundary": "SOFTWARE_VALIDATE",
                "validated": True,
                "selected_work_ids": selected,
                "cognitive_output_checksum": _checksum(cognitive_selection),
            })
            self._selection_artifact = delegation
            self._delegated_selection_artifact = {
                "selection_mode": mode,
                "selected_work_ids": selected,
                "authorized_candidate_set": sorted(authorized),
                **selection_metadata,
                "cognitive_output_checksum": _checksum(cognitive_selection),
            }
            self._validate_selection_target_policy(plan, selected, mode, None, delegation_decision)
            context["selected_work_ids"] = list(selected)
            return M4Selection(tuple(selected), mode, f"{plan['research_plan_id']}:M4:DELEGATED_SELECTION")
        raise ResearchB3Error("SELECTION_MODE_UNSUPPORTED")

    @staticmethod
    def _selection_options(candidate_ids: set[str], options: Sequence[Sequence[str]] | None) -> list[tuple[str, ...]]:
        raw = options or [sorted(candidate_ids)]
        result: list[tuple[str, ...]] = []
        for option in raw:
            normalized = tuple(sorted({str(item) for item in option if str(item)}))
            if normalized and set(normalized).issubset(candidate_ids) and normalized not in result:
                result.append(normalized)
        if not result:
            raise ResearchB3Error("SELECTION_OPTIONS_INVALID")
        return result

    @staticmethod
    def _selection_option_id(work_ids: Sequence[str]) -> str:
        return "SELECTION_SET:" + ",".join(sorted(work_ids))

    @classmethod
    def _parse_selection_option(cls, option_id: str | None, candidate_ids: set[str]) -> list[str]:
        if not isinstance(option_id, str) or not option_id.startswith("SELECTION_SET:"):
            raise ResearchB3Error("HUMAN_SELECTION_OPTION_INVALID")
        values = [item for item in option_id.removeprefix("SELECTION_SET:").split(",") if item]
        selected = sorted(set(values))
        if not selected or not set(selected).issubset(candidate_ids):
            raise ResearchB3Error("HUMAN_SELECTION_OUTSIDE_CANDIDATE_SET")
        return selected

    @staticmethod
    def _project_lifecycle_selection(
        lifecycle: dict[str, Any], selected_ids: list[str], candidate_ids: set[str], authority_ref: str
    ) -> dict[str, Any]:
        result = copy.deepcopy(lifecycle)
        for work in result.get("works", []):
            work_id = work.get("work_id")
            if work_id in selected_ids:
                work.update(
                    {
                        "state": "DISCOVERED_WORK",
                        "selection_state": "SELECTED",
                        "research_stage": "SELECTION",
                        "artifact_validity": "VALID",
                        "research_contract_version": M4_CONTRACT_VERSION,
                        "lineage_refs": sorted(set(work.get("lineage_refs", [])) | {f"software:selection:{authority_ref}"}),
                    }
                )
            elif work_id in candidate_ids:
                work["selection_state"] = "EXCLUDED"
                work["research_stage"] = "SELECTION"
                work["artifact_validity"] = "VALID"
        result["final_selection"] = {
            "selected_work_ids": [],
            "format_policy_ref": "policies/script_product/main_episode_format_policy.md",
            "range_status": "NOT_APPLICABLE",
            "curation_ref": None,
            "exception": None,
        }
        return result

    @classmethod
    def _project_lifecycle_deep(
        cls,
        lifecycle: dict[str, Any],
        selected_ids: list[str],
        candidate_ids: set[str],
        authority_ref: str,
        deep_fidelity: list[dict[str, Any]],
        work_stops: list[dict[str, Any]],
        deep_fidelity_ref: Mapping[str, Any],
        comparison: Mapping[str, Any],
        thesis: Mapping[str, Any],
    ) -> dict[str, Any]:
        result = copy.deepcopy(lifecycle)
        by_work = {item.get("work", {}).get("material_id"): item for item in deep_fidelity}
        stops = {item.get("subject_ref"): item for item in work_stops}
        for work in result.get("works", []):
            work_id = work.get("work_id")
            dossier = by_work.get(work_id)
            if work_id not in selected_ids or dossier is None:
                if work_id in candidate_ids:
                    work.update({"selection_state": "EXCLUDED", "research_stage": "SELECTION", "artifact_validity": "VALID"})
                continue
            stop = stops.get(dossier.get("dossier_id"))
            if stop is None:
                raise ResearchB3Error(f"LIFECYCLE_DEEP_STOP_MISSING: {work_id}")
            work.update(
                {
                    # The coarse lifecycle state remains discovery-owned in B3;
                    # the orthogonal research fields carry the deep progress.
                    "state": "DISCOVERED_WORK",
                    "selection_state": "SELECTED",
                    "research_stage": "DEEP_FIDELITY",
                    "preliminary_fidelity": dossier.get("preliminary_fidelity", "NOT_ASSESSED"),
                    "deep_fidelity": dossier.get("deep_fidelity", "NOT_ASSESSED"),
                    "research_sufficiency": stop.get("sufficiency_status"),
                    "artifact_validity": "VALID",
                    "thesis_stage": "PROVISIONAL",
                    "research_contract_version": M4_CONTRACT_VERSION,
                    "dossier_ref": dossier["dossier_id"],
                    "comparative_decision_ref": str(comparison.get("comparison_id")),
                    "stage_evidence_refs": sorted(
                        set(work.get("stage_evidence_refs", []))
                        | {str(deep_fidelity_ref["artifact_id"]), str(stop.get("decision_id"))}
                    ),
                    "lineage_refs": sorted(
                        set(work.get("lineage_refs", []))
                        | {
                            f"software:selection:{authority_ref}",
                            f"software:thesis:{thesis.get('thesis_id')}",
                            f"software:deep-fidelity:{dossier['dossier_id']}",
                        }
                    ),
                }
            )
        errors = validate_work_lifecycle(result)
        if errors:
            raise ResearchB3Error("Lifecycle M4 inválido: " + " | ".join(errors))
        return result

    @staticmethod
    def _extract_delegated_selection(
        output: Any, authorized: set[str], known_evidence_refs: set[str]
    ) -> tuple[list[str], dict[str, Any]]:
        if not isinstance(output, Mapping):
            raise ResearchB3Error("DELEGATED_SELECTION_OUTPUT_INVALID")
        selected = output.get("selected_work_ids")
        if selected is None and isinstance(output.get("works"), list):
            selected = [
                item.get("work_id") for item in output["works"]
                if isinstance(item, Mapping) and item.get("selection_state") == "SELECTED"
            ]
        if not isinstance(selected, list):
            raise ResearchB3Error("DELEGATED_SELECTION_IDS_REQUIRED")
        normalized = sorted({str(item) for item in selected if str(item)})
        if not normalized or not set(normalized).issubset(authorized):
            raise ResearchB3Error("DELEGATED_SELECTION_OUTSIDE_SCOPE")
        rationale = output.get("set_rationale", output.get("rationale"))
        evidence_refs = output.get("evidence_refs")
        criteria_used = output.get("criteria_used", output.get("criteria"))
        limitations = output.get("limitations")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ResearchB3Error("DELEGATED_SELECTION_RATIONALE_REQUIRED")
        if not isinstance(evidence_refs, list) or not evidence_refs or not all(str(item).strip() for item in evidence_refs):
            raise ResearchB3Error("DELEGATED_SELECTION_EVIDENCE_REQUIRED")
        unresolved = sorted({str(item) for item in evidence_refs} - known_evidence_refs)
        if unresolved:
            raise ResearchB3Error(
                "DELEGATED_SELECTION_EVIDENCE_REF_UNRESOLVED: " + ", ".join(unresolved)
            )
        if not isinstance(criteria_used, list) or not criteria_used or not all(str(item).strip() for item in criteria_used):
            raise ResearchB3Error("DELEGATED_SELECTION_CRITERIA_REQUIRED")
        if not isinstance(limitations, list) or not all(str(item).strip() for item in limitations):
            raise ResearchB3Error("DELEGATED_SELECTION_LIMITATIONS_REQUIRED")
        return normalized, {
            "set_rationale": rationale.strip(),
            "evidence_refs": sorted({str(item) for item in evidence_refs}),
            "criteria_used": [str(item).strip() for item in criteria_used],
            "limitations": [str(item).strip() for item in limitations],
        }

    @staticmethod
    def _validate_selection_target_policy(
        plan: Mapping[str, Any],
        selected: Sequence[str],
        mode: str,
        human_decision: HumanDecision | None,
        delegation_decision: Mapping[str, Any] | None,
    ) -> None:
        policy = plan.get("selection_policy") if isinstance(plan.get("selection_policy"), Mapping) else {}
        policy_mode = str(policy.get("mode") or "").upper()
        compatible = {
            "USER_SELECTION": {"USER_SELECTION", "OWNER_OR_DELEGATED"},
            "DELEGATED_SELECTION": {"DELEGATED_SELECTION", "OWNER_OR_DELEGATED"},
        }
        if policy_mode and policy_mode not in compatible.get(mode, set()):
            raise ResearchB3Error("SELECTION_POLICY_MODE_MISMATCH")
        target = plan.get("target_final_works_decision") if isinstance(plan.get("target_final_works_decision"), Mapping) else {}
        target_status = target.get("status")
        if target_status in {"CONFIRMED", "DELEGATED"}:
            requested = target.get("requested_count")
            if requested not in {3, 4, 5}:
                raise ResearchB3Error("TARGET_FINAL_WORKS_COUNT_INVALID")
            if not isinstance(requested, int) or len(selected) != requested:
                error = "DELEGATED_TARGET_COUNT_NOT_RESPECTED" if target_status == "DELEGATED" else "CONFIRMED_TARGET_COUNT_NOT_RESPECTED"
                raise ResearchB3Error(error)
            if target_status == "DELEGATED" and mode != "DELEGATED_SELECTION":
                raise ResearchB3Error("DELEGATED_TARGET_REQUIRES_DELEGATED_SELECTION")
            return

        if target_status == "NOT_DECLARED" or target_status not in {"RECOMMENDED"}:
            raise ResearchB3Error("TARGET_FINAL_WORKS_RESOLUTION_REQUIRED")
        if len(selected) not in {3, 4, 5}:
            raise ResearchB3Error("TARGET_FINAL_WORKS_COUNT_INVALID")
        if human_decision is None:
            raise ResearchB3Error("TARGET_FINAL_WORKS_RESOLUTION_REQUIRED")
        if human_decision.action == "APPROVE":
            requested = target.get("requested_count")
            if target_status != "RECOMMENDED" or not isinstance(requested, int) or len(selected) != requested:
                raise ResearchB3Error("RECOMMENDED_TARGET_COUNT_RESOLUTION_REQUIRED")
        elif human_decision.action != "SELECT_ALTERNATIVE":
            raise ResearchB3Error("TARGET_FINAL_WORKS_RESOLUTION_REQUIRED")

    @staticmethod
    def _targets_for_work(targets: Any, work_id: str) -> Any:
        if isinstance(targets, Mapping):
            works = targets.get("works") or targets.get("work_targets") or {}
            if isinstance(works, Mapping) and work_id in works:
                target = works[work_id]
                if isinstance(target, (list, tuple, Mapping)) and target:
                    return copy.deepcopy(target)
            for key in ("global", "shared", "targets"):
                if targets.get(key):
                    return copy.deepcopy(targets[key])
            if works:
                return None
        return copy.deepcopy(targets)

    @staticmethod
    def _scope_outcome(subject_kind: str, subject_ref: str, stop: Mapping[str, Any]) -> dict[str, Any]:
        status = stop.get("sufficiency_status")
        if status in POSITIVE_STOP_STATUSES:
            return {"subject_kind": subject_kind, "subject_ref": subject_ref, "outcome": "SCOPE_COMPLETE", "reopen_route": None}
        return {
            "subject_kind": subject_kind,
            "subject_ref": subject_ref,
            "outcome": "BLOCKED" if status == "BLOCKED_BY_EVIDENCE" else "SCOPE_REQUIRES_MORE_RESEARCH",
            "gap": list(stop.get("pending_matters", [])),
            "reopen_route": {"stage": "DEEP_RESEARCH", "subject_kind": subject_kind, "subject_ref": subject_ref},
        }

    @staticmethod
    def _eligible_candidates(
        pool: list[dict[str, Any]], fidelity: list[dict[str, Any]], sufficiency: list[dict[str, Any]]
    ) -> set[str]:
        fidelity_by_work = {item["work"]["material_id"]: item for item in fidelity}
        dossier_ids = {item["dossier_id"] for item in pool}
        valid_stops = {
            item["subject_ref"]
            for item in sufficiency
            if item.get("subject_kind") == "WORK_RESEARCH_DOSSIER"
            and item.get("sufficiency_status") in POSITIVE_STOP_STATUSES
            and item.get("subject_ref") in dossier_ids
        }
        return {
            work_id
            for work_id, item in fidelity_by_work.items()
            if item.get("preliminary_fidelity") in {"APTA", "APTA_CON_RIESGOS"}
            and item.get("dossier_id") in valid_stops
        }

    @classmethod
    def _validate_baseline(
        cls,
        plan: dict[str, Any],
        phenomenon: dict[str, Any],
        discovery: dict[str, Any],
        pool: list[dict[str, Any]],
        fidelity: list[dict[str, Any]],
        sufficiency: list[dict[str, Any]],
        provisional_thesis: dict[str, Any],
        research_comparison: dict[str, Any],
        deepening_targets: Any,
        lifecycle: dict[str, Any],
        context: dict[str, Any],
    ) -> None:
        plan_errors = validate_research_plan(plan)
        if plan_errors or not plan.get("research_plan_id") or not plan.get("episode_id"):
            raise ResearchB3Error("RESEARCH_PLAN_INVALID")
        if not phenomenon.get("research_id"):
            raise ResearchB3Error("PHENOMENON_RESEARCH_INVALID")
        thesis_errors = validate_against_schema(provisional_thesis, "thesis_artifact")
        if thesis_errors or provisional_thesis.get("stage") != "THESIS_PROVISIONAL":
            raise ResearchB3Error("PROVISIONAL_THESIS_REQUIRED")
        if provisional_thesis.get("packaging_alignment") or provisional_thesis.get("viewer_transformation"):
            raise ResearchB3Error("B2_THESIS_NARRATIVE_FIELDS_FORBIDDEN")
        if provisional_thesis.get("research_id") not in {None, phenomenon.get("research_id"), plan.get("research_plan_id")}:
            raise ResearchB3Error("PROVISIONAL_THESIS_SCOPE_INVALID")
        comparison_errors = validate_against_schema(research_comparison, "research_comparison")
        if comparison_errors or research_comparison.get("narrative_decision_made") is not False:
            raise ResearchB3Error("RESEARCH_COMPARISON_REQUIRED_AND_NON_NARRATIVE")
        if not deepening_targets:
            raise ResearchB3Error("DEEPENING_TARGETS_REQUIRED")
        if not cls._target_items(deepening_targets, "phenomenon"):
            raise ResearchB3Error("PHENOMENON_DEEPENING_TARGETS_REQUIRED")
        if isinstance(deepening_targets, Mapping):
            source_ref = deepening_targets.get("source_artifact_ref")
            comparison_id = research_comparison.get("comparison_id")
            if source_ref is not None and source_ref != comparison_id:
                raise ResearchB3Error("DEEPENING_TARGETS_SOURCE_MISMATCH")
            if deepening_targets.get("research_plan_id") not in {None, plan.get("research_plan_id")}:
                raise ResearchB3Error("DEEPENING_TARGETS_PLAN_MISMATCH")
        if set(item.get("work", {}).get("material_id") for item in pool) - {
            item.get("work", {}).get("material_id") for item in fidelity
        }:
            raise ResearchB3Error("PRELIMINARY_FIDELITY_MUST_COVER_BASE_POOL")
        discovered = {item.get("work_id") for item in discovery.get("works", [])}
        if not all(item.get("work", {}).get("material_id") in discovered for item in pool):
            raise ResearchB3Error("BASE_POOL_WORK_NOT_IN_DISCOVERY")
        if not context.get("topic") or not context.get("source_access") or not context.get("brief") or not context.get("channel_context"):
            raise ResearchB3Error("M4_CONTEXT_INVALID")
        if not lifecycle.get("lifecycle_id"):
            raise ResearchB3Error("LIFECYCLE_INVALID")
        if not cls._eligible_candidates(pool, fidelity, sufficiency):
            raise ResearchB3Error("NO_ELIGIBLE_WORKS_FOR_DEEP_RESEARCH")

    @staticmethod
    def _target_items(targets: Any, scope: str) -> Any:
        if isinstance(targets, Mapping):
            if scope == "phenomenon":
                for key in ("phenomenon", "phenomenon_targets", "global", "shared"):
                    if targets.get(key):
                        return targets[key]
            else:
                for key in ("works", "work_targets", "global", "shared", "targets"):
                    if targets.get(key):
                        return targets[key]
        elif isinstance(targets, (list, tuple)):
            return targets
        return None

    @staticmethod
    @staticmethod
    def _validate_known_evidence_refs(value: Mapping[str, Any], context: Mapping[str, Any], stage: str) -> None:
        known = set(context.get("_known_evidence_refs", set()))
        refs: set[str] = set()
        for container in (value.get("evidence_type_separation"), value.get("deep_research")):
            if isinstance(container, Mapping):
                for field in ("work_evidence_refs", "external_reality_evidence_refs"):
                    entries = container.get(field, [])
                    if isinstance(entries, list):
                        refs.update(str(item) for item in entries)
        unresolved = sorted(refs - known)
        if unresolved:
            raise ResearchB3Error(f"{stage}_EVIDENCE_REF_UNRESOLVED: " + ", ".join(unresolved))

    @staticmethod
    def _validate_deep_phenomenon(
        value: Any, base: dict[str, Any], provisional_thesis: dict[str, Any]
    ) -> None:
        if not isinstance(value, dict):
            raise ResearchB3Error("DEEP_PHENOMENON_RESEARCH_MUST_BE_OBJECT")
        errors = validate_research_pack(value)
        if errors:
            raise ResearchB3Error(" | ".join(errors))
        if value.get("research_id") != base.get("research_id"):
            raise ResearchB3Error("DEEP_PHENOMENON_ID_MUST_BE_SOFTWARE_OWNED")
        thesis_id = provisional_thesis.get("thesis_id")
        if (
            value.get("research_stage") != "DEEP_RESEARCH"
            or value.get("thesis_stage") != "PROVISIONAL"
            or f"software:thesis:{thesis_id}" not in value.get("lineage", [])
        ):
            raise ResearchB3Error("DEEP_PHENOMENON_STAGE_INVALID")

    @staticmethod
    def _validate_deep_dossier(
        value: Any,
        work_id: str,
        *,
        expected_stage: str = "DEEP_RESEARCH",
        known_evidence_refs: set[str] | None = None,
    ) -> None:
        if not isinstance(value, dict):
            raise ResearchB3Error("DEEP_WORK_RESEARCH_MUST_BE_OBJECT")
        errors = validate_work_research_dossier(value, known_evidence_refs=known_evidence_refs)
        if errors:
            raise ResearchB3Error(" | ".join(errors))
        if value.get("work", {}).get("material_id") != work_id or value.get("selection_state") != "SELECTED":
            raise ResearchB3Error("DEEP_WORK_RESEARCH_SELECTION_BINDING_INVALID")
        if value.get("research_stage") != expected_stage:
            raise ResearchB3Error("DEEP_WORK_RESEARCH_STAGE_INVALID")

    @staticmethod
    def _validate_deep_fidelity(
        value: Any, work_id: str, *, known_evidence_refs: set[str] | None = None
    ) -> None:
        ResearchB3Orchestrator._validate_deep_dossier(
            value, work_id, expected_stage="DEEP_FIDELITY", known_evidence_refs=known_evidence_refs
        )
        if value.get("research_stage") != "DEEP_FIDELITY":
            raise ResearchB3Error("DEEP_FIDELITY_STAGE_INVALID")
        status = value.get("deep_fidelity")
        if status not in DEEP_FIDELITY_STATUSES:
            raise ResearchB3Error("DEEP_FIDELITY_STATUS_INVALID")
        if status == "APROBADA_CON_LIMITES" and not value.get("downstream_restrictions"):
            raise ResearchB3Error("APROBADA_CON_LIMITES_REQUIRES_RESTRICTIONS")

    @staticmethod
    def _validate_stop(
        value: Any,
        subject_kind: str,
        subject_ref: str,
        *,
        expected_intended_use: str,
        expected_deep_fidelity: str | None = None,
    ) -> None:
        if not isinstance(value, dict):
            raise ResearchB3Error("RESEARCH_STOP_DECISION_MUST_BE_OBJECT")
        errors = validate_research_stop_decision(value)
        if errors:
            raise ResearchB3Error(" | ".join(errors))
        if (value.get("subject_kind"), value.get("subject_ref")) != (subject_kind, subject_ref):
            raise ResearchB3Error("RESEARCH_STOP_SUBJECT_SCOPE_MISMATCH")
        if value.get("intended_use") != expected_intended_use:
            raise ResearchB3Error("RESEARCH_STOP_INTENDED_USE_MISMATCH")
        if value.get("sufficiency_status") not in {
            "SUFFICIENT_FOR_INTENDED_USE",
            "LIMITED_BUT_USABLE",
            "MORE_RESEARCH_REQUIRED",
            "BLOCKED_BY_EVIDENCE",
        }:
            raise ResearchB3Error("RESEARCH_STOP_STATUS_INVALID")
        status = value.get("sufficiency_status")
        if status in {"MORE_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE"} and not value.get("pending_matters"):
            raise ResearchB3Error("RESEARCH_STOP_REOPEN_SCOPE_REQUIRED")
        if expected_deep_fidelity in {"APROBADA", "APROBADA_CON_LIMITES"} and status not in POSITIVE_STOP_STATUSES:
            raise ResearchB3Error("DEEP_FIDELITY_POSITIVE_STOP_REQUIRED")
        if expected_deep_fidelity == "MAS_INVESTIGACION_REQUERIDA" and status not in {"MORE_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE"}:
            raise ResearchB3Error("DEEP_FIDELITY_MORE_RESEARCH_ROUTE_REQUIRED")
        if expected_deep_fidelity == "NO_APROBADA" and status in POSITIVE_STOP_STATUSES:
            raise ResearchB3Error("DEEP_FIDELITY_NO_APPROVAL_CANNOT_BE_POSITIVE")

    @staticmethod
    def _source_report_id(context: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
        source_access = context.get("source_access")
        if isinstance(source_access, Mapping) and source_access.get("report_id"):
            return str(source_access["report_id"])
        return f"{plan['research_plan_id']}:SOURCE_ACCESS"

    @staticmethod
    def _artifact_ref(value: Mapping[str, Any], kind: str) -> dict[str, Any]:
        artifact_id = str(value.get("dossier_id") or value.get("lifecycle_id") or value.get("research_id") or kind)
        return {"artifact_id": artifact_id, "artifact_kind": kind, "checksum": _checksum(value)}


def _state_of(value: Any) -> str:
    if isinstance(value, dict):
        for field in ("research_stage", "sufficiency_status", "deep_fidelity"):
            if value.get(field):
                return str(value[field])
        if value.get("work"):
            return str(value["work"].get("material_id", "WORK"))
    if isinstance(value, list):
        return "LIST:" + ",".join(sorted(_state_of(item) for item in value))
    return type(value).__name__
