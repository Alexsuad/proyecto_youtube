"""Deterministic B3/M4 routing for Research V2.

M4 extends the sequential B2 boundary without invoking a provider.  Human
or delegated selection, deep research, deep fidelity and ResearchStop
decisions all return to Software before they are accepted or persisted.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
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
    _write_json_atomic,
    utc_now,
)
from src.core.contract_validation import (
    validate_against_schema,
    validate_claims_ledger,
    validate_contradiction_disposition,
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
M5_CLAIMS_USE = "M5_POST_DEEP_CLAIMS_CONSOLIDATION"
M5_COMPARISON_STAGE = "POST_DEEP_REEVALUATION"
M5_PROVISIONAL_DISPOSITIONS = {"CONFIRMED", "MODIFIED", "REJECTED", "LIMITED"}

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
    "comparison_id",
    "comparison_version",
    "ledger_id",
    "contract_version",
    "ledger_stage",
    "semantic_audit_id",
    "curation_id",
    "owner_scope",
    "provisional_thesis_id",
    "claims_ledger_id",
    "research_comparison_id",
    "research_stop_decision_refs",
    "analysis_ids",
    "provisional_disposition",
    "decision_ref",
    "selection_authority_ref",
    "authorized_candidate_set",
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
        "M5_CLAIMS_LEDGER": "claims_ledger_m5.json",
        "M5_CLAIM_SUFFICIENCY": "research_stop_m5_claims.json",
        "M5_POST_DEEP_COMPARISON": "research_comparison_m5_post_deep.json",
        "M5_REFINED_THESIS": "refined_thesis_m5.json",
        "M5_SELECTION_CHANGE_REQUEST": "m5_selection_change_request.json",
        "M5_SELECTION_CHANGE_PENDING": "m5_selection_change_pending.json",
        "M5_SELECTION_CHANGE_DECISION": "m5_selection_change_decision.json",
        "M5_DELEGATED_POST_DEEP_DECISION": "m5_delegated_post_deep_decision.json",
        "M5_APPROVED_CHANGE_RESEARCH": "research_stop_m5_approved_change.json",
        "M5_EXECUTION_MANIFEST": "research_m5_execution.json",
    }

    def load_existing(
        self, stage: str, *, artifact_id: str, artifact_kind: str,
    ) -> tuple[dict[str, str], Any] | None:
        """Recover one persisted artifact without reopening its write slot."""
        filename = self._FILENAMES.get(stage)
        if filename is None:
            raise ResearchB3Error(f"B2_UNKNOWN_PERSISTENCE_STAGE: {stage}")
        path = self.root / filename
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchB3Error(f"{stage}_RECOVERY_UNREADABLE") from exc
        ref = {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "artifact_version": CONTRACT_VERSION,
            "path": str(path),
            "checksum": _checksum(payload),
        }
        self._persisted[stage] = ref
        return ref, payload

    def update_existing(
        self,
        stage: str,
        payload: Any,
        *,
        existing_ref: Mapping[str, Any],
        artifact_kind: str,
    ) -> dict[str, str]:
        """Atomically advance an existing state artifact, never its inputs."""
        filename = self._FILENAMES.get(stage)
        if filename is None:
            raise ResearchB3Error(f"B2_UNKNOWN_PERSISTENCE_STAGE: {stage}")
        path = self.root / filename
        if not path.is_file() or str(existing_ref.get("path")) != str(path):
            raise ResearchB3Error(f"{stage}_RECOVERY_REFERENCE_INVALID")
        document = payload if isinstance(payload, dict) else {"dossiers": payload}
        _write_json_atomic(path, document)
        ref = {
            "artifact_id": str(existing_ref.get("artifact_id")),
            "artifact_kind": artifact_kind,
            "artifact_version": CONTRACT_VERSION,
            "path": str(path),
            "checksum": _checksum(document),
        }
        self._persisted[stage] = ref
        return ref


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

    def run_m5(
        self,
        baseline: Mapping[str, Any],
        m4_result: Mapping[str, Any],
        *,
        context: Mapping[str, Any],
        selection_change_decision: HumanDecision | Mapping[str, Any] | None = None,
        selection_change_delegation: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the second half of B3 over persisted, verified M4 outputs.

        M5 deliberately starts from the M4 references rather than from an
        in-memory cognitive projection.  Every M5 cognitive step receives
        those references and returns through the same Software validation and
        persistence boundary.  The method never creates a readiness manifest,
        narrative artifact, or final narrative selection.
        """
        data = _as_dict(baseline, "M5_BASELINE")
        result = _as_dict(m4_result, "M4_RESULT")
        ctx = _as_dict(context, "M5_CONTEXT")
        plan = _as_dict(data.get("research_plan"), "RESEARCH_PLAN")
        provisional_thesis = _as_dict(data.get("provisional_thesis"), "PROVISIONAL_THESIS")
        plan_errors = validate_research_plan(plan)
        thesis_errors = validate_against_schema(provisional_thesis, "thesis_artifact")
        if plan_errors or thesis_errors or provisional_thesis.get("stage") != "THESIS_PROVISIONAL":
            raise ResearchB3Error("M5_PROVISIONAL_THESIS_INVALID")
        if not ctx.get("topic") or not ctx.get("source_access") or not ctx.get("brief") or not ctx.get("channel_context"):
            raise ResearchB3Error("M5_CONTEXT_INVALID")

        m4_manifest_ref = result.get("execution_manifest")
        m4_manifest = self._load_persisted_json(m4_manifest_ref, "M4_EXECUTION_MANIFEST")
        self._validate_m4_handoff(m4_manifest)
        m4_thesis_ref = (m4_manifest.get("b2_inputs") or {}).get("provisional_thesis_ref")
        expected_thesis_ref = self._artifact_ref(provisional_thesis, "ThesisArtifact")
        if (
            not isinstance(m4_thesis_ref, Mapping)
            or m4_thesis_ref.get("artifact_id") != expected_thesis_ref["artifact_id"]
            or m4_thesis_ref.get("checksum") != expected_thesis_ref["checksum"]
            or m4_thesis_ref.get("artifact_version") != expected_thesis_ref["artifact_version"]
            or provisional_thesis.get("version") != expected_thesis_ref["artifact_version"]
        ):
            raise ResearchB3Error("M5_PROVISIONAL_THESIS_M4_BINDING_INVALID")
        m4_refs = {
            name: result.get(name)
            for name in (
                "deep_phenomenon_research",
                "deep_phenomenon_sufficiency",
                "deep_work_research",
                "deep_fidelity",
                "deep_work_sufficiency",
            )
        }
        m4_payloads = {
            name: self._load_persisted_json(ref, name.upper())
            for name, ref in m4_refs.items()
        }
        declared_m4_artifact_ids = {
            str(item.get("artifact_id"))
            for item in m4_manifest.get("artifacts", [])
            if isinstance(item, Mapping) and item.get("artifact_id")
        }
        for name, ref in m4_refs.items():
            if not isinstance(ref, Mapping) or str(ref.get("artifact_id")) not in declared_m4_artifact_ids:
                raise ResearchB3Error(f"M5_M4_ARTIFACT_NOT_DECLARED: {name}")
        selected_ids = [str(item) for item in m4_manifest["selection"]["selected_work_ids"]]
        if not selected_ids or len(selected_ids) != len(set(selected_ids)):
            raise ResearchB3Error("M5_SELECTED_WORK_IDS_INVALID")
        deep_dossiers = self._document_list(m4_payloads["deep_work_research"], "DEEP_WORK_RESEARCH")
        deep_fidelity = self._document_list(m4_payloads["deep_fidelity"], "DEEP_FIDELITY")
        work_stops = self._document_list(m4_payloads["deep_work_sufficiency"], "DEEP_WORK_SUFFICIENCY")
        if {str(item.get("work", {}).get("material_id")) for item in deep_dossiers} != set(selected_ids):
            raise ResearchB3Error("M5_M4_DEEP_WORKS_MISMATCH")
        if {str(item.get("work", {}).get("material_id")) for item in deep_fidelity} != set(selected_ids):
            raise ResearchB3Error("M5_M4_DEEP_FIDELITY_MISMATCH")
        if {str(item.get("subject_ref")) for item in work_stops} != {str(item.get("dossier_id")) for item in deep_fidelity}:
            raise ResearchB3Error("M5_M4_WORK_STOPS_MISMATCH")

        known_evidence_refs = _evidence_reference_values(data)
        for payload in m4_payloads.values():
            known_evidence_refs.update(_evidence_reference_values(payload))
        known_evidence_refs.update(_valid_acquisition_reference_values(self.acquisition_adapter.bindings))
        known_evidence_refs.update(_valid_acquisition_reference_values(self.acquisition_adapter.work_bindings))
        known_evidence_refs.update(_valid_acquisition_reference_values(self.acquisition_adapter.work_representation_bindings))
        m4_delegation_ref = None
        m4_delegation_payload = None
        if m4_manifest["selection"]["mode"] == "DELEGATED_SELECTION":
            m4_delegation_ref, m4_delegation_payload = self._m4_delegation_authorization(
                m4_manifest, known_evidence_refs,
            )
            if selection_change_delegation is not None and _checksum(dict(selection_change_delegation)) != _checksum(m4_delegation_payload):
                raise ResearchB3Error("M5_DELEGATION_AUTHORIZATION_MISMATCH")
        ctx["_known_evidence_refs"] = known_evidence_refs
        ctx["selected_work_ids"] = selected_ids
        ctx["provisional_thesis"] = copy.deepcopy(provisional_thesis)
        ctx["selection_mode"] = m4_manifest["selection"]["mode"]
        ctx["selection_authority_ref"] = m4_manifest["selection"].get("authority_ref")
        ctx["_m4_delegation_ref"] = copy.deepcopy(m4_delegation_ref)
        ctx["_m4_delegation_payload"] = copy.deepcopy(m4_delegation_payload)
        ctx["_m5_subject_ids"] = {
            "PHENOMENON": {str(plan["research_plan_id"])},
            "WORK_RESEARCH_DOSSIER": {str(item.get("dossier_id")) for item in deep_dossiers if item.get("dossier_id")},
            "WORK_INTERPRETATION": set(selected_ids),
            "MATERIAL_CLAIM": set(),
        }

        existing_m5 = self.persistence.load_existing(
            "M5_EXECUTION_MANIFEST",
            artifact_id=f"{plan['research_plan_id']}:M5",
            artifact_kind="ResearchM5ExecutionManifest",
        )
        if existing_m5 is not None:
            existing_m5_ref, existing_m5_manifest = existing_m5
            return self._resume_m5(
                plan=plan,
                provisional_thesis=provisional_thesis,
                m4_manifest=m4_manifest,
                m4_manifest_ref=m4_manifest_ref,
                selected_ids=selected_ids,
                known_evidence_refs=known_evidence_refs,
                context=ctx,
                existing_m5_ref=existing_m5_ref,
                existing_m5_manifest=existing_m5_manifest,
                selection_change_decision=selection_change_decision,
                selection_change_delegation=selection_change_delegation,
            )

        m4_input_refs = [m4_manifest_ref, *[ref for ref in m4_refs.values()]]
        claims = self._m5_step(
            "M5_CLAIMS_EVIDENCE_CONSOLIDATION",
            "claims_ledger",
            plan,
            ctx,
            m4_input_refs,
            [
                {"name": name, "payload": copy.deepcopy(payload)}
                for name, payload in m4_payloads.items()
            ] + [{"name": "provisional_thesis", "payload": copy.deepcopy(provisional_thesis)}],
            lambda value: self._validate_m5_claims(value, known_evidence_refs, plan, ctx["_m5_subject_ids"]),
        )
        claim_stops = self._materialize_m5_claim_stops(claims, plan, known_evidence_refs)
        for claim in claims["claims"]:
            if isinstance(claim.get("materiality"), Mapping) and claim["materiality"].get("is_material"):
                claim["materiality"]["decision_ref"] = next(
                    item["decision_id"] for item in claim_stops if item["subject_ref"] == claim["claim_id"]
                )
        ledger_errors = validate_claims_ledger(claims)
        if ledger_errors:
            raise ResearchB3Error("M5_CLAIMS_LEDGER_INVALID: " + " | ".join(ledger_errors))
        claims_ref = self.persistence.persist(
            "M5_CLAIMS_LEDGER", claims,
            artifact_id=f"{plan['research_plan_id']}:M5:CLAIMS",
            artifact_kind="ClaimsLedger",
        )
        claim_stops_ref = self.persistence.persist(
            "M5_CLAIM_SUFFICIENCY", {"decisions": claim_stops},
            artifact_id=f"{plan['research_plan_id']}:M5:RSD:CLAIMS",
            artifact_kind="ResearchStopDecisionCollection",
        )

        comparison = self._m5_step(
            "M5_POST_DEEP_SET_REEVALUATION",
            "research_comparison",
            plan,
            ctx,
            [claims_ref, m4_manifest_ref, *[ref for ref in m4_refs.values()]],
            [
                {"name": "claims_ledger", "payload": copy.deepcopy(claims)},
                {"name": "m4_manifest", "payload": copy.deepcopy(m4_manifest)},
            ] + [
                {"name": name, "payload": copy.deepcopy(payload)}
                for name, payload in m4_payloads.items()
            ],
            lambda value: self._validate_m5_comparison(
                value, selected_ids, known_evidence_refs, m4_manifest["selection"]["mode"]
            ),
        )
        comparison_ref = self.persistence.persist(
            "M5_POST_DEEP_COMPARISON", comparison,
            artifact_id=f"{plan['research_plan_id']}:COMPARISON:POST_DEEP",
            artifact_kind="ResearchComparison",
        )

        selection_change_request_ref = None
        selection_change_pending_ref = None
        selection_change_decision_ref = None
        selection_change_decision_payload = None
        selection_change_delegation_ref = None
        selection_change_delegation_payload = None
        material_selection_change = self._m5_comparison_requires_decision(comparison)
        if material_selection_change:
            selection_mode = m4_manifest["selection"]["mode"]
            selection_change_request = None
            if selection_mode == "USER_SELECTION":
                selection_change_request = self._build_m5_selection_change_request(
                    plan, comparison, comparison_ref, selection_mode
                )
                selection_change_request_ref = self.persistence.persist(
                    "M5_SELECTION_CHANGE_REQUEST",
                    selection_change_request.to_dict(),
                    artifact_id=f"{plan['research_plan_id']}:M5:SELECTION_CHANGE:REQUEST",
                    artifact_kind="HumanDecisionRequest",
                )
            supplied_change_decision = selection_change_decision if selection_mode == "USER_SELECTION" else selection_change_delegation
            if selection_mode == "USER_SELECTION":
                selection_change_pending = {
                    "state": "PENDING_HUMAN_DECISION",
                    "request_ref": selection_change_request_ref,
                    "comparison_ref": comparison_ref,
                    "recommendation_ids": [str(item["recommendation_id"]) for item in comparison["set_recommendations"]],
                    "substitute_research_required": True,
                    "continuation": "M5_REFINED_THESIS_AFTER_DECISION",
                    "selection_mode": selection_mode,
                    "delegated_route": False,
                }
                selection_change_pending_ref = self.persistence.persist(
                    "M5_SELECTION_CHANGE_PENDING",
                    selection_change_pending,
                    artifact_id=f"{plan['research_plan_id']}:M5:SELECTION_CHANGE:PENDING",
                    artifact_kind="HumanDecisionPendingState",
                )
                if supplied_change_decision is None:
                    pending_manifest = self._m5_pending_manifest(
                        plan, m4_manifest_ref, claims_ref, claim_stops_ref, comparison_ref,
                        selection_change_request_ref, selection_change_pending_ref, ctx,
                        selection_mode=selection_mode,
                        state=selection_change_pending["state"],
                    )
                    manifest_ref = self.persistence.persist(
                        "M5_EXECUTION_MANIFEST", pending_manifest,
                        artifact_id=f"{plan['research_plan_id']}:M5",
                        artifact_kind="ResearchM5ExecutionManifest",
                    )
                    return {
                        "status": pending_manifest["status"],
                        "claims_ledger": claims_ref,
                        "claim_sufficiency": claim_stops_ref,
                        "post_deep_comparison": comparison_ref,
                        "human_decision_request": selection_change_request_ref,
                        "selection_change_pending": selection_change_pending_ref,
                        "execution_manifest": manifest_ref,
                        "events": pending_manifest["events"],
                    }
            if selection_mode == "USER_SELECTION":
                selection_change_decision_model = self._materialize_m5_selection_change_decision(
                    selection_change_request, supplied_change_decision, plan["episode_id"]
                )
                selection_change_decision_payload = selection_change_decision_model.to_dict()
                selection_change_decision_ref = self.persistence.persist(
                    "M5_SELECTION_CHANGE_DECISION",
                    selection_change_decision_payload,
                    artifact_id=f"{plan['research_plan_id']}:M5:SELECTION_CHANGE:DECISION",
                    artifact_kind="HumanDecision",
                )
            else:
                if m4_delegation_ref is None or m4_delegation_payload is None:
                    raise ResearchB3Error("M5_M4_DELEGATION_AUTHORIZATION_MISSING")
                selection_change_delegation_payload = self._m5_step(
                    "M5_DELEGATED_POST_DEEP_DECISION",
                    "work_lifecycle",
                    plan,
                    ctx,
                    [comparison_ref, m4_delegation_ref],
                    [
                        {"name": "post_deep_comparison", "payload": copy.deepcopy(comparison)},
                        {"name": "m4_delegation_authorization", "payload": copy.deepcopy(m4_delegation_payload)},
                    ],
                    lambda value: self._validate_m5_delegated_post_deep_decision(
                        value,
                        comparison,
                        comparison_ref,
                        m4_delegation_ref,
                        m4_delegation_payload,
                        selected_ids,
                        known_evidence_refs,
                    ),
                )
                selection_change_delegation_ref = self.persistence.persist(
                    "M5_DELEGATED_POST_DEEP_DECISION",
                    selection_change_delegation_payload,
                    artifact_id=f"{plan['research_plan_id']}:M5:DELEGATED_POST_DEEP:DECISION",
                    artifact_kind="DelegatedSelectionDecision",
                )
            ctx["_selection_change_decision"] = copy.deepcopy(selection_change_decision_payload)
            ctx["_delegated_post_deep_decision"] = copy.deepcopy(selection_change_delegation_payload)

        return self._finish_m5(
            plan=plan,
            provisional_thesis=provisional_thesis,
            m4_manifest=m4_manifest,
            m4_manifest_ref=m4_manifest_ref,
            claims=claims,
            claims_ref=claims_ref,
            claim_stops=claim_stops,
            claim_stops_ref=claim_stops_ref,
            comparison=comparison,
            comparison_ref=comparison_ref,
            known_evidence_refs=known_evidence_refs,
            context=ctx,
            selection_change_request_ref=selection_change_request_ref,
            selection_change_pending_ref=selection_change_pending_ref,
            selection_change_decision_ref=selection_change_decision_ref,
            selection_change_decision_payload=selection_change_decision_payload,
            selection_change_delegation_ref=selection_change_delegation_ref,
            selection_change_delegation_payload=selection_change_delegation_payload,
        )

    @staticmethod
    def _m5_comparison_requires_decision(comparison: Mapping[str, Any]) -> bool:
        return any(
            item.get("action") != "MAINTAIN" or item.get("material_change") is True
            for item in comparison.get("set_recommendations", [])
            if isinstance(item, Mapping)
        )

    @staticmethod
    def _build_m5_selection_change_request(
        plan: Mapping[str, Any],
        comparison: Mapping[str, Any],
        comparison_ref: Mapping[str, Any],
        selection_mode: str,
    ) -> HumanDecisionRequest:
        expected_actor = "OWNER" if selection_mode == "USER_SELECTION" else None
        return HumanDecisionRequest(
            request_id=f"{plan['research_plan_id']}:M5:SELECTION_CHANGE:REQUEST",
            prompt="Revisar la recomendación post-deep de cambio material del conjunto antes de continuar M5.",
            options=(
                {"id": "APPROVE", "label": "Aceptar recomendación"},
                {"id": "REJECT", "label": "Mantener selección humana"},
            ),
            recommendation=json.dumps(comparison.get("set_recommendations", []), ensure_ascii=False, sort_keys=True),
            episode_id=str(plan["episode_id"]),
            subject_ref=str(comparison_ref["artifact_id"]),
            subject_version=str(comparison_ref.get("artifact_version", M4_CONTRACT_VERSION)),
            subject_checksum=str(comparison_ref["checksum"]),
            workflow_ref=f"{plan['research_plan_id']}:M5",
            expected_actor_ref=expected_actor,
            expected_channel="TERMINAL",
        )

    @staticmethod
    def _materialize_m5_selection_change_decision(
        request: HumanDecisionRequest,
        supplied: HumanDecision | Mapping[str, Any],
        episode_id: str,
    ) -> HumanDecision:
        if isinstance(supplied, HumanDecision):
            decision = supplied
        elif isinstance(supplied, Mapping):
            raw_action = supplied.get("action") or supplied.get("decision")
            action = {"ACCEPT": "APPROVE", "REJECT": "REJECT"}.get(str(raw_action), str(raw_action))
            try:
                decision = HumanDecision(
                    request_id=request.request_id,
                    action=action,
                    selected_option=supplied.get("selected_option"),
                    correction=supplied.get("correction"),
                    actor_ref=str(supplied.get("actor_ref", "OWNER")),
                    channel=str(supplied.get("channel", "TERMINAL")),
                )
            except (TypeError, ValueError) as exc:
                raise ResearchB3Error("M5_SELECTION_CHANGE_DECISION_INVALID") from exc
        else:
            raise ResearchB3Error("M5_SELECTION_CHANGE_DECISION_INVALID")
        try:
            bound = decision.bind_request(request)
            validate_human_decision(request, bound, episode_id)
        except (TypeError, ValueError, PermissionError) as exc:
            raise ResearchB3Error("M5_SELECTION_CHANGE_DECISION_INVALID") from exc
        if bound.action not in {"APPROVE", "REJECT"}:
            raise ResearchB3Error("M5_SELECTION_CHANGE_DECISION_INVALID")
        return bound

    def _m4_delegation_authorization(
        self,
        m4_manifest: Mapping[str, Any],
        known_evidence_refs: set[str],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load M4 authorization; it is never treated as the M5 answer."""
        for artifact in m4_manifest.get("artifacts", []):
            if isinstance(artifact, Mapping) and artifact.get("artifact_kind") == "DelegationDecision":
                payload = self._load_persisted_json(artifact, "M4_DELEGATION_DECISION")
                errors = validate_against_schema(payload, "delegation_decision")
                if errors or payload.get("decision") != "DELEGATE":
                    raise ResearchB3Error("M5_M4_DELEGATION_AUTHORIZATION_INVALID")
                self._known_refs(
                    payload.get("evidence_refs"), known_evidence_refs,
                    "M5_M4_DELEGATION_AUTHORIZATION", allow_empty=False,
                )
                authorized = {str(item) for item in payload.get("authorized_candidate_set", [])}
                candidate_ids = {str(item) for item in m4_manifest.get("selection", {}).get("candidate_work_ids", [])}
                if not authorized or not authorized.issubset(candidate_ids):
                    raise ResearchB3Error("M5_M4_DELEGATION_SCOPE_INVALID")
                return copy.deepcopy(dict(artifact)), payload
        raise ResearchB3Error("M5_M4_DELEGATION_AUTHORIZATION_MISSING")

    @classmethod
    def _validate_m5_delegated_post_deep_decision(
        cls,
        value: Any,
        comparison: Mapping[str, Any],
        comparison_ref: Mapping[str, Any],
        authorization_ref: Mapping[str, Any],
        authorization: Mapping[str, Any],
        selected_ids: Sequence[str],
        known_evidence_refs: set[str],
    ) -> None:
        if not isinstance(value, Mapping):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_DECISION_REQUIRED")
        if value.get("decision") not in {"APPROVE", "REJECT"}:
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_DECISION_INVALID")
        if value.get("selection_mode") != "DELEGATED_SELECTION" or value.get("narrative_decision_made") is not False:
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_STAGE_INVALID")
        recommendation_ids = {str(item.get("recommendation_id")) for item in comparison.get("set_recommendations", [])}
        if (
            value.get("comparison_id") != comparison_ref.get("artifact_id")
            or value.get("comparison_version") != comparison_ref.get("artifact_version")
            or value.get("comparison_checksum") != comparison_ref.get("checksum")
            or value.get("authorization_ref") != authorization_ref.get("artifact_id")
            or value.get("authorized_candidate_set") != sorted({str(item) for item in authorization.get("authorized_candidate_set", [])})
        ):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_BINDING_INVALID")
        supplied_recommendations = {str(item) for item in value.get("recommendation_ids", [])}
        if not supplied_recommendations or not supplied_recommendations.issubset(recommendation_ids):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_RECOMMENDATION_REF_INVALID")
        if not isinstance(value.get("action"), str) or not value.get("action"):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_ACTION_REQUIRED")
        referenced_recommendations = [
            item for item in comparison.get("set_recommendations", [])
            if isinstance(item, Mapping) and str(item.get("recommendation_id")) in supplied_recommendations
        ]
        recommendation_actions = {str(item.get("action")) for item in referenced_recommendations}
        if value.get("decision") == "APPROVE" and value.get("action") not in recommendation_actions:
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_ACTION_MISMATCH")
        if value.get("decision") == "REJECT" and value.get("action") != "REJECT":
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_REJECT_ACTION_INVALID")
        result_ids = value.get("resulting_work_ids")
        if not isinstance(result_ids, list) or not result_ids or len(result_ids) != len(set(result_ids)) or not all(isinstance(item, str) and item.strip() for item in result_ids):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_RESULT_INVALID")
        authorized = {str(item) for item in authorization.get("authorized_candidate_set", [])}
        if not set(result_ids).issubset(authorized):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_SCOPE_INVALID")
        if value.get("decision") == "APPROVE" and value.get("action") in {"REPLACE", "ADD"}:
            implicated_work_ids = {
                str(item.get("work_id"))
                for item in comparison.get("substitution_research_requirements", [])
                if isinstance(item, Mapping) and item.get("work_id")
            }
            if value.get("action") == "ADD":
                implicated_work_ids.update(
                    str(work_id)
                    for recommendation in referenced_recommendations
                    for work_id in recommendation.get("affected_work_ids", [])
                    if str(work_id) not in set(selected_ids)
                )
            if not implicated_work_ids.issubset(authorized):
                raise ResearchB3Error("M5_DELEGATED_POST_DEEP_SCOPE_INVALID")
        if value.get("decision") == "REJECT" and result_ids != list(selected_ids):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_REJECT_MUST_PRESERVE_SELECTION")
        if value.get("decision") == "APPROVE":
            if value.get("action") in {"REMOVE", "REDUCE"} and not set(result_ids).issubset(set(selected_ids)):
                raise ResearchB3Error("M5_DELEGATED_POST_DEEP_RESULT_SCOPE_INVALID")
            if value.get("action") in {"REMOVE", "REDUCE"}:
                affected_ids = {
                    str(work_id)
                    for recommendation in referenced_recommendations
                    for work_id in recommendation.get("affected_work_ids", [])
                }
                expected_ids = [str(work_id) for work_id in selected_ids if str(work_id) not in affected_ids]
                if result_ids != expected_ids:
                    raise ResearchB3Error("M5_DELEGATED_POST_DEEP_RESULT_NOT_APPLIED")
            if value.get("action") in {"REPLACE", "ADD"} and result_ids != list(selected_ids):
                raise ResearchB3Error("M5_DELEGATED_POST_DEEP_RESEARCH_REQUIRED")
        if not value.get("rationale"):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_RATIONALE_REQUIRED")
        cls._known_refs(
            value.get("evidence_refs"), known_evidence_refs,
            "M5_DELEGATED_POST_DEEP", allow_empty=False,
        )
        if not isinstance(value.get("criteria_used"), list) or not value["criteria_used"]:
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_CRITERIA_REQUIRED")
        if not isinstance(value.get("limitations"), list):
            raise ResearchB3Error("M5_DELEGATED_POST_DEEP_LIMITATIONS_REQUIRED")

    @staticmethod
    def _m5_requires_new_research(
        comparison: Mapping[str, Any], decision_action: str | None,
    ) -> bool:
        if decision_action != "APPROVE":
            return False
        return any(
            item.get("action") in {"REPLACE", "ADD"}
            and any(
                isinstance(requirement, Mapping)
                and requirement.get("status") == "RESEARCH_REQUIRED"
                for requirement in comparison.get("substitution_research_requirements", [])
            )
            for item in comparison.get("set_recommendations", [])
            if isinstance(item, Mapping)
        )

    def _materialize_m5_approved_change_stop(
        self,
        comparison: Mapping[str, Any],
        plan: Mapping[str, Any],
        known_evidence_refs: set[str],
    ) -> list[dict[str, Any]]:
        requirements = comparison.get("substitution_research_requirements", [])
        decisions: list[dict[str, Any]] = []
        for requirement in requirements:
            if not isinstance(requirement, Mapping) or requirement.get("status") != "RESEARCH_REQUIRED":
                continue
            work_id = str(requirement.get("work_id"))
            evidence_refs = [
                str(ref)
                for recommendation in comparison.get("set_recommendations", [])
                if isinstance(recommendation, Mapping)
                for ref in recommendation.get("evidence_refs", [])
            ]
            self._known_refs(evidence_refs, known_evidence_refs, "M5_APPROVED_CHANGE", allow_empty=False)
            stop = {
                "decision_id": f"{plan['research_plan_id']}:M5:RSD:APPROVED_CHANGE:{work_id}",
                "decision_version": M4_CONTRACT_VERSION,
                "subject_kind": "WORK_RESEARCH_DOSSIER",
                "subject_ref": f"{plan['research_plan_id']}:M5:RESEARCH_REQUIRED:{work_id}",
                "intended_use": "M5_POST_DEEP_CLAIMS_CONSOLIDATION",
                "evidence_refs": sorted(set(evidence_refs)),
                "claim_decision": None,
                "sufficiency_status": "MORE_RESEARCH_REQUIRED",
                "limitations": ["La obra nueva o sustituta no tiene deep research ni deep fidelity en M5."],
                "pending_matters": ["DEEP_RESEARCH", "DEEP_FIDELITY"],
                "unresolved_material_contradiction_refs": [],
                "invalidators": ["La obra debe completar investigación profunda antes de incorporarse."],
                "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"],
                "return_route": "RETURN_TO_RESEARCH",
                "return_route_code": "RETURN_TO_RESEARCH",
                "decision_basis": "La recomendación aprobada requiere investigar la obra antes de incorporarla.",
            }
            errors = validate_research_stop_decision(stop)
            if errors:
                raise ResearchB3Error("M5_APPROVED_CHANGE_STOP_INVALID: " + " | ".join(errors))
            decisions.append(stop)
        if not decisions:
            raise ResearchB3Error("M5_APPROVED_CHANGE_RESEARCH_REQUIREMENT_MISSING")
        return decisions

    @staticmethod
    def _m5_pending_manifest(
        plan: Mapping[str, Any],
        m4_manifest_ref: Mapping[str, Any],
        claims_ref: Mapping[str, Any],
        claim_stops_ref: Mapping[str, Any],
        comparison_ref: Mapping[str, Any],
        request_ref: Mapping[str, Any],
        pending_ref: Mapping[str, Any],
        context: Mapping[str, Any],
        *,
        selection_mode: str,
        state: str,
    ) -> dict[str, Any]:
        events = [
            {"stage": "M5_CLAIMS_EVIDENCE_CONSOLIDATION", "boundary": "SOFTWARE_PERSIST", "artifact_id": claims_ref["artifact_id"]},
            {"stage": "M5_CLAIM_SUFFICIENCY", "boundary": "SOFTWARE_PERSIST", "artifact_id": claim_stops_ref["artifact_id"]},
            {"stage": "M5_POST_DEEP_SET_REEVALUATION", "boundary": "SOFTWARE_PERSIST", "artifact_id": comparison_ref["artifact_id"]},
            *([{"stage": "M5_SELECTION_CHANGE_REQUEST", "boundary": "SOFTWARE_PERSIST", "artifact_id": request_ref["artifact_id"]}] if request_ref else []),
            {"stage": "M5_SELECTION_CHANGE_PENDING", "boundary": "SOFTWARE_PERSIST", "artifact_id": pending_ref["artifact_id"]},
        ] + list(context.get("_m5_events", []))
        return {
            "manifest_type": "RESEARCH_M5_EXECUTION",
            "manifest_version": M4_CONTRACT_VERSION,
            "status": state,
            "real_ai_execution": False,
            "real_research": False,
            "product_use": False,
            "m4_inputs_verified": True,
            "m4_manifest_ref": m4_manifest_ref["artifact_id"],
            "m5_outputs": [
                claims_ref, claim_stops_ref, comparison_ref,
                *([request_ref] if request_ref else []), pending_ref,
            ],
            "refined_thesis_not_produced": True,
            "research_ready_manifest_not_produced": True,
            "research_ready": False,
            "b5_i3_outputs_not_produced": True,
            "narrative_decisions_not_made": True,
            "final_narrative_selection": False,
            "human_selection_protected": selection_mode == "USER_SELECTION",
            "selection_mode": selection_mode,
            "selection_change_request_ref": request_ref["artifact_id"] if request_ref else None,
            "selection_change_pending_ref": pending_ref["artifact_id"],
            "m6_status": "NOT_AUTHORIZED",
            "technical_review": "PENDING",
            "methodological_review": "PENDING",
            "events": events,
            "lineage": [
                m4_manifest_ref["artifact_id"], claims_ref["artifact_id"],
                claim_stops_ref["artifact_id"], comparison_ref["artifact_id"],
                *([request_ref["artifact_id"]] if request_ref else []), pending_ref["artifact_id"],
            ],
            "continuation": "M5_REFINED_THESIS_AFTER_DECISION",
            "episode_id": plan["episode_id"],
        }

    @staticmethod
    def _m5_manifest_output(manifest: Mapping[str, Any], *, artifact_kind: str) -> dict[str, Any] | None:
        for ref in manifest.get("m5_outputs", []):
            if isinstance(ref, Mapping) and ref.get("artifact_kind") == artifact_kind:
                return copy.deepcopy(dict(ref))
        return None

    def _m5_result_from_manifest(
        self, manifest_ref: Mapping[str, Any], manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": manifest.get("status"),
            "execution_manifest": copy.deepcopy(dict(manifest_ref)),
            "events": copy.deepcopy(manifest.get("events", [])),
        }
        for key, kind in (
            ("claims_ledger", "ClaimsLedger"),
            ("claim_sufficiency", "ResearchStopDecisionCollection"),
            ("post_deep_comparison", "ResearchComparison"),
            ("refined_thesis", "RefinedThesis"),
            ("human_decision_request", "HumanDecisionRequest"),
            ("selection_change_pending", "HumanDecisionPendingState"),
            ("selection_change_decision", "HumanDecision"),
            ("selection_change_delegation", "DelegatedSelectionDecision"),
            ("approved_change_research", "ApprovedChangeResearchStopCollection"),
        ):
            ref = self._m5_manifest_output(manifest, artifact_kind=kind)
            if ref is not None:
                if key == "claim_sufficiency" and ":M5:RSD:CLAIMS" not in str(ref.get("artifact_id")):
                    continue
                result[key] = ref
        return result

    def _resume_m5(
        self,
        *,
        plan: Mapping[str, Any],
        provisional_thesis: Mapping[str, Any],
        m4_manifest: Mapping[str, Any],
        m4_manifest_ref: Mapping[str, Any],
        selected_ids: list[str],
        known_evidence_refs: set[str],
        context: dict[str, Any],
        existing_m5_ref: Mapping[str, Any],
        existing_m5_manifest: Mapping[str, Any],
        selection_change_decision: HumanDecision | Mapping[str, Any] | None,
        selection_change_delegation: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        manifest = _as_dict(existing_m5_manifest, "M5_EXECUTION_MANIFEST_RECOVERY")
        if manifest.get("manifest_type") != "RESEARCH_M5_EXECUTION":
            raise ResearchB3Error("M5_EXECUTION_MANIFEST_RECOVERY_INVALID")
        if manifest.get("m4_manifest_ref") != m4_manifest_ref.get("artifact_id"):
            raise ResearchB3Error("M5_EXECUTION_MANIFEST_M4_BINDING_INVALID")
        status = manifest.get("status")
        if status in {"READY_FOR_OWNER_REVIEW", "PENDING_RESEARCH"}:
            return self._m5_result_from_manifest(existing_m5_ref, manifest)
        if status not in {"PENDING_HUMAN_DECISION", "PENDING_DELEGATED_DECISION"}:
            raise ResearchB3Error("M5_EXECUTION_MANIFEST_RECOVERY_STATE_INVALID")

        claims_ref = self._m5_manifest_output(manifest, artifact_kind="ClaimsLedger")
        claim_stops_ref = next(
            (
                copy.deepcopy(dict(ref))
                for ref in manifest.get("m5_outputs", [])
                if isinstance(ref, Mapping)
                and ref.get("artifact_kind") == "ResearchStopDecisionCollection"
                and ":M5:RSD:CLAIMS" in str(ref.get("artifact_id"))
            ),
            None,
        )
        comparison_ref = self._m5_manifest_output(manifest, artifact_kind="ResearchComparison")
        pending_ref = self._m5_manifest_output(manifest, artifact_kind="HumanDecisionPendingState")
        if not claims_ref or not claim_stops_ref or not comparison_ref or not pending_ref:
            raise ResearchB3Error("M5_PENDING_ARTIFACTS_INCOMPLETE")
        claims = self._load_persisted_json(claims_ref, "M5_CLAIMS_LEDGER_RECOVERY")
        claim_stop_payload = self._load_persisted_json(claim_stops_ref, "M5_CLAIM_SUFFICIENCY_RECOVERY")
        comparison = self._load_persisted_json(comparison_ref, "M5_COMPARISON_RECOVERY")
        pending = self._load_persisted_json(pending_ref, "M5_SELECTION_CHANGE_PENDING_RECOVERY")
        errors = validate_claims_ledger(claims)
        if errors:
            raise ResearchB3Error("M5_CLAIMS_LEDGER_RECOVERY_INVALID: " + " | ".join(errors))
        claim_stops = self._document_list(claim_stop_payload, "M5_CLAIM_SUFFICIENCY_RECOVERY")
        if pending.get("state") != status or pending.get("selection_mode") != m4_manifest["selection"]["mode"]:
            raise ResearchB3Error("M5_PENDING_STATE_BINDING_INVALID")
        self._validate_m5_comparison(
            comparison, selected_ids, known_evidence_refs, m4_manifest["selection"]["mode"]
        )
        context["_m5_events"] = copy.deepcopy(manifest.get("events", []))

        request_ref = self._m5_manifest_output(manifest, artifact_kind="HumanDecisionRequest")
        decision_ref = self._m5_manifest_output(manifest, artifact_kind="HumanDecision")
        delegation_ref = self._m5_manifest_output(manifest, artifact_kind="DelegationDecision")
        decision_payload = None
        delegation_payload = None
        if status == "PENDING_HUMAN_DECISION":
            if request_ref is None:
                raise ResearchB3Error("M5_HUMAN_DECISION_REQUEST_RECOVERY_MISSING")
            request_payload = self._load_persisted_json(request_ref, "M5_SELECTION_CHANGE_REQUEST_RECOVERY")
            try:
                request = HumanDecisionRequest.from_dict(request_payload, require_contract=True)
            except (KeyError, TypeError, ValueError) as exc:
                raise ResearchB3Error("M5_SELECTION_CHANGE_REQUEST_RECOVERY_INVALID") from exc
            if request.status != "PENDING" or request_payload.get("request_checksum") != request.checksum():
                raise ResearchB3Error("M5_SELECTION_CHANGE_REQUEST_RECOVERY_INVALID")
            if (
                request.subject_ref != comparison_ref.get("artifact_id")
                or request.subject_version != comparison_ref.get("artifact_version")
                or request.subject_checksum != comparison_ref.get("checksum")
                or request.workflow_ref != f"{plan['research_plan_id']}:M5"
            ):
                raise ResearchB3Error("M5_SELECTION_CHANGE_REQUEST_RECOVERY_BINDING_INVALID")
            if decision_ref is not None:
                decision_payload = self._load_persisted_json(decision_ref, "M5_SELECTION_CHANGE_DECISION_RECOVERY")
                try:
                    persisted_decision = HumanDecision.from_dict(decision_payload, require_bound_metadata=True)
                    validate_human_decision(request, persisted_decision, str(plan["episode_id"]), require_bound_metadata=True)
                except (KeyError, TypeError, ValueError, PermissionError) as exc:
                    raise ResearchB3Error("M5_SELECTION_CHANGE_DECISION_RECOVERY_INVALID") from exc
                if persisted_decision.action not in {"APPROVE", "REJECT"}:
                    raise ResearchB3Error("M5_SELECTION_CHANGE_DECISION_RECOVERY_INVALID")
            elif selection_change_decision is not None:
                decision = self._materialize_m5_selection_change_decision(
                    request, selection_change_decision, str(plan["episode_id"])
                )
                decision_payload = decision.to_dict()
                decision_ref = self.persistence.persist(
                    "M5_SELECTION_CHANGE_DECISION",
                    decision_payload,
                    artifact_id=f"{plan['research_plan_id']}:M5:SELECTION_CHANGE:DECISION",
                    artifact_kind="HumanDecision",
                )
            else:
                return self._m5_result_from_manifest(existing_m5_ref, manifest)
        else:
            raise ResearchB3Error("M5_LEGACY_DELEGATED_PENDING_REQUIRES_CONCRETE_DECISION")

        context["selected_work_ids"] = list(selected_ids)
        context["_selection_change_decision"] = copy.deepcopy(decision_payload)
        return self._finish_m5(
            plan=plan,
            provisional_thesis=provisional_thesis,
            m4_manifest=m4_manifest,
            m4_manifest_ref=m4_manifest_ref,
            claims=claims,
            claims_ref=claims_ref,
            claim_stops=claim_stops,
            claim_stops_ref=claim_stops_ref,
            comparison=comparison,
            comparison_ref=comparison_ref,
            known_evidence_refs=known_evidence_refs,
            context=context,
            selection_change_request_ref=request_ref,
            selection_change_pending_ref=pending_ref,
            selection_change_decision_ref=decision_ref,
            selection_change_decision_payload=decision_payload,
            selection_change_delegation_ref=delegation_ref,
            selection_change_delegation_payload=delegation_payload,
            existing_manifest_ref=existing_m5_ref,
        )

    def _finish_m5(
        self,
        *,
        plan: Mapping[str, Any],
        provisional_thesis: Mapping[str, Any],
        m4_manifest: Mapping[str, Any],
        m4_manifest_ref: Mapping[str, Any],
        claims: Mapping[str, Any],
        claims_ref: Mapping[str, Any],
        claim_stops: list[dict[str, Any]],
        claim_stops_ref: Mapping[str, Any],
        comparison: Mapping[str, Any],
        comparison_ref: Mapping[str, Any],
        known_evidence_refs: set[str],
        context: dict[str, Any],
        selection_change_request_ref: Mapping[str, Any] | None,
        selection_change_pending_ref: Mapping[str, Any] | None,
        selection_change_decision_ref: Mapping[str, Any] | None,
        selection_change_decision_payload: Mapping[str, Any] | None,
        selection_change_delegation_ref: Mapping[str, Any] | None,
        selection_change_delegation_payload: Mapping[str, Any] | None,
        existing_manifest_ref: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        decision_action = None
        if isinstance(selection_change_decision_payload, Mapping):
            decision_action = str(selection_change_decision_payload.get("action"))
        elif isinstance(selection_change_delegation_payload, Mapping):
            decision_action = str(selection_change_delegation_payload.get("decision"))
            resulting_work_ids = selection_change_delegation_payload.get("resulting_work_ids")
            if isinstance(resulting_work_ids, list):
                context["effective_selected_work_ids"] = list(resulting_work_ids)
                context["selected_work_ids"] = list(resulting_work_ids)
        if self._m5_requires_new_research(comparison, decision_action):
            approved_stop = self._materialize_m5_approved_change_stop(comparison, plan, known_evidence_refs)
            approved_stop_ref = self.persistence.persist(
                "M5_APPROVED_CHANGE_RESEARCH",
                {"decisions": approved_stop},
                artifact_id=f"{plan['research_plan_id']}:M5:RSD:APPROVED_CHANGE",
                artifact_kind="ApprovedChangeResearchStopCollection",
            )
            manifest = self._m5_manifest_for_completion(
                plan, m4_manifest_ref, m4_manifest, context,
                [claims_ref, claim_stops_ref, comparison_ref],
                selection_change_request_ref, selection_change_pending_ref,
                selection_change_decision_ref, selection_change_delegation_ref,
                status="PENDING_RESEARCH",
                refined_thesis_not_produced=True,
                extra_refs=[approved_stop_ref],
                extra_events=[{"stage": "M5_APPROVED_CHANGE_RESEARCH", "boundary": "SOFTWARE_PERSIST", "artifact_id": approved_stop_ref["artifact_id"]}],
            )
            manifest_ref = self._persist_or_update_m5_manifest(manifest, existing_manifest_ref)
            result = {
                "status": "PENDING_RESEARCH",
                "claims_ledger": claims_ref,
                "claim_sufficiency": claim_stops_ref,
                "post_deep_comparison": comparison_ref,
                "delegated_post_deep_decision": selection_change_delegation_ref,
                "approved_change_research": approved_stop_ref,
                "execution_manifest": manifest_ref,
                "events": manifest["events"],
            }
            if selection_change_request_ref is not None:
                result["human_decision_request"] = selection_change_request_ref
            if selection_change_pending_ref is not None:
                result["selection_change_pending"] = selection_change_pending_ref
            if selection_change_decision_ref is not None:
                result["selection_change_decision"] = selection_change_decision_ref
            if selection_change_delegation_ref is not None:
                result["selection_change_delegation"] = selection_change_delegation_ref
            return result

        thesis = self._m5_step(
            "M5_REFINED_THESIS", "refined_thesis", plan, context,
            [claims_ref, claim_stops_ref, comparison_ref, m4_manifest_ref],
            [
                {"name": "provisional_thesis", "payload": copy.deepcopy(dict(provisional_thesis))},
                {"name": "claims_ledger", "payload": copy.deepcopy(dict(claims))},
                {"name": "claim_stops", "payload": copy.deepcopy(claim_stops)},
                {"name": "post_deep_comparison", "payload": copy.deepcopy(dict(comparison))},
            ],
            lambda value: self._validate_m5_thesis(
                value, provisional_thesis, claims, comparison, claim_stops, known_evidence_refs, plan,
                claims_ref, comparison_ref, claim_stops_ref,
            ),
        )
        thesis_ref = self.persistence.persist(
            "M5_REFINED_THESIS", thesis,
            artifact_id=f"{plan['research_plan_id']}:THESIS:REFINED",
            artifact_kind="RefinedThesis",
        )
        manifest = self._m5_manifest_for_completion(
            plan, m4_manifest_ref, m4_manifest, context,
            [claims_ref, claim_stops_ref, comparison_ref, thesis_ref],
            selection_change_request_ref, selection_change_pending_ref,
            selection_change_decision_ref, selection_change_delegation_ref,
            status="READY_FOR_OWNER_REVIEW",
            refined_thesis_not_produced=False,
            extra_events=[{"stage": "M5_REFINED_THESIS", "boundary": "SOFTWARE_PERSIST", "artifact_id": thesis_ref["artifact_id"]}],
        )
        manifest_ref = self._persist_or_update_m5_manifest(manifest, existing_manifest_ref)
        result = {
            "status": "READY_FOR_OWNER_REVIEW",
            "claims_ledger": claims_ref,
            "claim_sufficiency": claim_stops_ref,
            "post_deep_comparison": comparison_ref,
            "refined_thesis": thesis_ref,
            "execution_manifest": manifest_ref,
            "events": manifest["events"],
        }
        if selection_change_request_ref is not None:
            result["human_decision_request"] = selection_change_request_ref
        if selection_change_pending_ref is not None:
            result["selection_change_pending"] = selection_change_pending_ref
        if selection_change_decision_ref is not None:
            result["selection_change_decision"] = selection_change_decision_ref
        if selection_change_delegation_ref is not None:
            result["selection_change_delegation"] = selection_change_delegation_ref
            result["delegated_post_deep_decision"] = selection_change_delegation_ref
        return result

    def _m5_manifest_for_completion(
        self,
        plan: Mapping[str, Any],
        m4_manifest_ref: Mapping[str, Any],
        m4_manifest: Mapping[str, Any],
        context: Mapping[str, Any],
        output_refs: list[Mapping[str, Any]],
        request_ref: Mapping[str, Any] | None,
        pending_ref: Mapping[str, Any] | None,
        decision_ref: Mapping[str, Any] | None,
        delegation_ref: Mapping[str, Any] | None,
        *,
        status: str,
        refined_thesis_not_produced: bool,
        extra_refs: list[Mapping[str, Any]] | None = None,
        extra_events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        refs = [copy.deepcopy(dict(ref)) for ref in output_refs]
        events = copy.deepcopy(list(context.get("_m5_events", [])))
        for ref in (request_ref, pending_ref, decision_ref, delegation_ref, *(extra_refs or [])):
            if ref is not None:
                refs.append(copy.deepcopy(dict(ref)))
        events.extend(copy.deepcopy(extra_events or []))
        return {
            "manifest_type": "RESEARCH_M5_EXECUTION",
            "manifest_version": M4_CONTRACT_VERSION,
            "research_id": plan["research_plan_id"],
            "status": status,
            "real_ai_execution": False,
            "real_research": False,
            "product_use": False,
            "m4_inputs_verified": True,
            "m4_manifest_ref": m4_manifest_ref["artifact_id"],
            "m5_outputs": refs,
            "refined_thesis_not_produced": refined_thesis_not_produced,
            "research_ready_manifest_not_produced": True,
            "research_ready": False,
            "b5_i3_outputs_not_produced": True,
            "narrative_decisions_not_made": True,
            "final_narrative_selection": False,
            "human_selection_protected": m4_manifest["selection"]["mode"] == "USER_SELECTION",
            "selection_mode": m4_manifest["selection"]["mode"],
            "effective_selected_work_ids": list(context.get("effective_selected_work_ids", context.get("selected_work_ids", []))),
            "selection_change_decision": copy.deepcopy(context.get("_selection_change_decision")),
            "selection_change_request_ref": request_ref.get("artifact_id") if request_ref else None,
            "selection_change_pending_ref": pending_ref.get("artifact_id") if pending_ref else None,
            "selection_change_decision_ref": decision_ref.get("artifact_id") if decision_ref else None,
            "selection_change_delegation_ref": delegation_ref.get("artifact_id") if delegation_ref else None,
            "delegated_post_deep_decision_ref": delegation_ref.get("artifact_id") if delegation_ref else None,
            "m6_status": "NOT_AUTHORIZED",
            "technical_review": "PENDING",
            "methodological_review": "PENDING",
            "events": events,
            "lineage": [m4_manifest_ref["artifact_id"], *[str(ref["artifact_id"]) for ref in refs]],
            "continuation": "M5_RESEARCH_REQUIRED" if status == "PENDING_RESEARCH" else "M5_COMPLETE",
            "episode_id": plan["episode_id"],
        }

    def _persist_or_update_m5_manifest(
        self, manifest: Mapping[str, Any], existing_ref: Mapping[str, Any] | None,
    ) -> dict[str, str]:
        if existing_ref is None:
            return self.persistence.persist(
                "M5_EXECUTION_MANIFEST", dict(manifest),
                artifact_id=f"{manifest['research_id']}:M5",
                artifact_kind="ResearchM5ExecutionManifest",
            )
        return self.persistence.update_existing(
            "M5_EXECUTION_MANIFEST", dict(manifest),
            existing_ref=existing_ref,
            artifact_kind="ResearchM5ExecutionManifest",
        )

    def _m5_step(
        self,
        stage: str,
        output_schema: str,
        plan: dict[str, Any],
        context: Mapping[str, Any],
        input_refs: list[dict[str, Any]],
        input_payload_artifacts: list[dict[str, Any]],
        validator: Callable[[Any], None],
    ) -> Any:
        events = context.setdefault("_m5_events", []) if isinstance(context, dict) else []
        events.append({"stage": stage, "boundary": "SOFTWARE_PREPARE", "input_artifacts": copy.deepcopy(input_refs)})
        payload = {
            "topic": context["topic"],
            "source_access": context["source_access"],
            "brief": context["brief"],
            "channel_context": context["channel_context"],
            "research_plan": plan,
            "stage": stage,
            "input_artifacts": copy.deepcopy(input_refs),
            "selected_work_ids": list(context.get("selected_work_ids", [])),
            "m4_outputs": copy.deepcopy(input_payload_artifacts),
        }
        prepared = resolve_role_execution_contract(
            ROLE_ID, output_schema, payload,
            {"stage": stage, "real_ai_execution": False, "real_research": False},
        )
        request = B2CognitiveRequest(stage, output_schema, tuple(copy.deepcopy(input_refs)), prepared)
        events.append({"stage": stage, "boundary": "IA_COGNITIVE_STEP", "output_schema": output_schema})
        output = self.cognitive_executor(request)
        output = self._software_project_m5(stage, output, plan, context, input_refs)
        try:
            validator(output)
        except (TypeError, KeyError, ValueError) as exc:
            raise ResearchB3Error(f"{stage}_OUTPUT_INVALID: {exc}") from exc
        events.append({"stage": stage, "boundary": "SOFTWARE_VALIDATE", "validated": True})
        guard = self.no_progress_guard.observe(
            gap=f"M5:{stage}", evidence_refs=[str(item["artifact_id"]) for item in input_refs],
            state=_state_of(output), result=output,
        )
        events.append({"stage": stage, "boundary": "SOFTWARE_ITERATION_GUARD", **guard.__dict__})
        if guard.status == "NO_PROGRESS":
            raise ResearchB3Error(f"{stage}_NO_PROGRESS: {guard.reason}:{guard.route}")
        return output

    def _software_project_m5(
        self, stage: str, output: Any, plan: dict[str, Any], context: Mapping[str, Any], input_refs: list[dict[str, Any]]
    ) -> Any:
        raw_output = copy.deepcopy(output)
        value = _strip_cognitive_technical(raw_output)
        if stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _as_dict(value, stage)
            value.update({
                "ledger_id": f"{plan['research_plan_id']}:M5:CLAIMS",
                "contract_version": M4_CONTRACT_VERSION,
                "ledger_stage": "RESEARCH_PRE_SCRIPT",
                "consolidation_stage": "POST_DEEP",
                "research_id": plan["research_plan_id"],
                "episode_id": plan["episode_id"],
                "artifact_version": M4_CONTRACT_VERSION,
                "created_at": utc_now(),
                "lineage": sorted({f"software:m5:claims", *[str(item["artifact_id"]) for item in input_refs]}),
            })
            return value
        if stage == "M5_POST_DEEP_SET_REEVALUATION":
            raw_comparison = _as_dict(raw_output, stage)
            if "selected_work_ids" in raw_comparison and raw_comparison.get("selected_work_ids") != list(context.get("selected_work_ids", [])):
                raise ResearchB3Error("M5_SILENT_SELECTION_CHANGE")
            value = _as_dict(value, stage)
            value.update({
                "comparison_id": f"{plan['research_plan_id']}:COMPARISON:POST_DEEP",
                "comparison_version": M4_CONTRACT_VERSION,
                "episode_id": plan["episode_id"],
                "research_id": plan["research_plan_id"],
                "candidate_work_ids": list(context.get("selected_work_ids", [])),
                "selected_work_ids": list(context.get("selected_work_ids", [])),
                "selection_mode": context.get("selection_mode"),
                "selection_authority_ref": context.get("selection_authority_ref"),
                "decision_stage": M5_COMPARISON_STAGE,
                "narrative_decision_made": False,
                "created_at": utc_now(),
            })
            return value
        if stage == "M5_DELEGATED_POST_DEEP_DECISION":
            value = _as_dict(value, stage)
            comparison_ref = input_refs[0]
            authorization_ref = input_refs[1]
            authorization = context.get("_m4_delegation_payload") or {}
            value.update({
                "decision_id": f"{plan['research_plan_id']}:M5:DELEGATED_POST_DEEP:DECISION",
                "decision_version": M4_CONTRACT_VERSION,
                "comparison_id": comparison_ref["artifact_id"],
                "comparison_version": comparison_ref.get("artifact_version", M4_CONTRACT_VERSION),
                "comparison_checksum": comparison_ref["checksum"],
                "authorization_ref": authorization_ref["artifact_id"],
                "authorized_candidate_set": sorted({str(item) for item in authorization.get("authorized_candidate_set", [])}),
                "selection_mode": "DELEGATED_SELECTION",
                "decision_stage": "POST_DEEP_DELEGATED_SELECTION",
                "narrative_decision_made": False,
                "created_at": utc_now(),
                "lineage": sorted({
                    f"software:m5:delegated-post-deep-decision",
                    str(comparison_ref["artifact_id"]),
                    str(authorization_ref["artifact_id"]),
                }),
            })
            return value
        if stage == "M5_REFINED_THESIS":
            cognitive_thesis = _as_dict(raw_output, stage)
            disposition = cognitive_thesis.get("provisional_disposition")
            if disposition not in M5_PROVISIONAL_DISPOSITIONS:
                raise ResearchB3Error("M5_PROVISIONAL_DISPOSITION_INVALID")
            value = _strip_cognitive_technical(cognitive_thesis)
            value.update({
                "thesis_id": f"{plan['research_plan_id']}:THESIS:REFINED",
                "episode_id": plan["episode_id"],
                "brief_version": plan["brief_version"],
                "research_id": plan["research_plan_id"],
                "evidence_report_id": self._source_report_id(context, plan),
                "semantic_audit_id": "NOT_PERFORMED_M6_PENDING",
                "provisional_thesis_id": context["provisional_thesis"]["thesis_id"],
                "provisional_disposition": disposition,
                "analysis_ids": ["NOT_APPLICABLE_M5_RESEARCH_SCOPE"],
                "curation_id": "NOT_APPLICABLE_M5_RESEARCH_SCOPE",
                "stage": "THESIS_REFINED",
                "research_contract_version": M4_CONTRACT_VERSION,
                "thesis_stage": "REFINED",
                "artifact_validity": "VALID",
                "owner_scope": "RESEARCH",
                "created_at": utc_now(),
                "lineage": sorted({
                    f"software:m5:thesis",
                    context["provisional_thesis"]["thesis_id"],
                    *[str(item["artifact_id"]) for item in input_refs],
                    f"software:m5:provisional-disposition:{disposition}",
                }),
            })
            return value
        raise ResearchB3Error(f"M5_UNKNOWN_STAGE: {stage}")

    @staticmethod
    def _load_persisted_json(ref: Any, label: str) -> dict[str, Any]:
        if not isinstance(ref, Mapping) or not ref.get("path") or not ref.get("artifact_id"):
            raise ResearchB3Error(f"{label}_REFERENCE_INVALID")
        path = Path(str(ref["path"]))
        if not path.is_file():
            raise ResearchB3Error(f"{label}_OUTPUT_MISSING: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchB3Error(f"{label}_OUTPUT_UNREADABLE") from exc
        if not isinstance(payload, dict):
            raise ResearchB3Error(f"{label}_OUTPUT_NOT_OBJECT")
        if ref.get("checksum") and _checksum(payload) != ref.get("checksum"):
            raise ResearchB3Error(f"{label}_CHECKSUM_MISMATCH")
        return payload

    @staticmethod
    def _document_list(payload: Mapping[str, Any], label: str) -> list[dict[str, Any]]:
        items = payload.get("dossiers") if isinstance(payload.get("dossiers"), list) else payload.get("decisions")
        if not isinstance(items, list) or not items or not all(isinstance(item, Mapping) for item in items):
            raise ResearchB3Error(f"{label}_COLLECTION_INVALID")
        return [copy.deepcopy(dict(item)) for item in items]

    @staticmethod
    def _validate_m4_handoff(manifest: Mapping[str, Any]) -> None:
        if manifest.get("manifest_type") != "RESEARCH_M4_EXECUTION":
            raise ResearchB3Error("M5_M4_MANIFEST_TYPE_INVALID")
        if manifest.get("m5_outputs_not_produced") is not True:
            raise ResearchB3Error("M5_M4_HANDOFF_NOT_CLOSED")
        if any(manifest.get(field) is not False for field in ("real_ai_execution", "real_research", "product_use")):
            raise ResearchB3Error("M5_M4_PROHIBITED_EXECUTION_STATE")
        selection = manifest.get("selection")
        if not isinstance(selection, Mapping) or selection.get("final_narrative_selection") is not False:
            raise ResearchB3Error("M5_M4_NARRATIVE_SELECTION_FORBIDDEN")

    @staticmethod
    def _known_refs(value: Any, known: set[str], label: str, *, allow_empty: bool = True) -> set[str]:
        refs = value if isinstance(value, list) else []
        if not allow_empty and not refs:
            raise ResearchB3Error(f"{label}_EVIDENCE_REQUIRED")
        if not all(isinstance(item, str) and item.strip() for item in refs):
            raise ResearchB3Error(f"{label}_EVIDENCE_REF_INVALID")
        unresolved = sorted(set(refs) - known)
        if unresolved:
            raise ResearchB3Error(f"{label}_EVIDENCE_REF_UNRESOLVED: {', '.join(unresolved)}")
        return set(refs)

    @classmethod
    def _validate_m5_evidence_separation(cls, value: Mapping[str, Any], known: set[str], label: str) -> set[str]:
        separation = value.get("evidence_type_separation")
        if not isinstance(separation, Mapping):
            raise ResearchB3Error(f"{label}_EVIDENCE_TYPE_SEPARATION_REQUIRED")
        work = cls._known_refs(separation.get("work_evidence_refs"), known, f"{label}_WORK", allow_empty=True)
        external = cls._known_refs(separation.get("external_reality_evidence_refs"), known, f"{label}_EXTERNAL", allow_empty=True)
        if work & external:
            raise ResearchB3Error(f"{label}_EVIDENCE_TYPES_MIXED")
        return work | external

    @classmethod
    def _validate_m5_claims(
        cls,
        value: Any,
        known: set[str],
        plan: Mapping[str, Any],
        known_subject_ids: Mapping[str, set[str]] | None = None,
    ) -> None:
        if not isinstance(value, Mapping) or not isinstance(value.get("claims"), list) or not value["claims"]:
            raise ResearchB3Error("M5_CLAIMS_REQUIRED")
        domain_refs = cls._validate_m5_evidence_separation(value, known, "M5_CLAIMS")
        claim_ids = {str(item.get("claim_id")) for item in value["claims"] if isinstance(item, Mapping)}
        if len(claim_ids) != len(value["claims"]) or "None" in claim_ids:
            raise ResearchB3Error("M5_CLAIM_IDS_INVALID")
        material_count = 0
        for claim in value["claims"]:
            if not isinstance(claim, Mapping):
                raise ResearchB3Error("M5_CLAIM_INVALID")
            source_refs = cls._known_refs(claim.get("source_refs"), known, f"CLAIM:{claim.get('claim_id')}", allow_empty=False)
            work = cls._known_refs(claim.get("work_evidence_refs"), known, f"CLAIM:{claim.get('claim_id')}:WORK", allow_empty=True)
            external = cls._known_refs(claim.get("external_reality_evidence_refs"), known, f"CLAIM:{claim.get('claim_id')}:EXTERNAL", allow_empty=True)
            if "supporting_evidence_refs" not in claim:
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_SUPPORTING_EVIDENCE_REQUIRED")
            supporting = cls._known_refs(
                claim.get("supporting_evidence_refs"), known,
                f"CLAIM:{claim.get('claim_id')}:SUPPORTING", allow_empty=True,
            )
            if work & external or source_refs != work | external:
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_EVIDENCE_TYPES_MIXED")
            if not supporting.issubset(source_refs):
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_SUPPORTING_EVIDENCE_NOT_IN_SOURCE_REFS")
            top_separation = value["evidence_type_separation"]
            if not work.issubset(set(top_separation.get("work_evidence_refs", []))) or not external.issubset(set(top_separation.get("external_reality_evidence_refs", []))):
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_EVIDENCE_TYPES_MIXED")
            if not (source_refs <= domain_refs):
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_EVIDENCE_DOMAIN_UNDECLARED")
            for evidence_field in ("limiting_evidence_refs", "refuting_evidence_refs"):
                classified = cls._known_refs(claim.get(evidence_field), known, f"CLAIM:{claim.get('claim_id')}:{evidence_field}", allow_empty=True)
                if not classified.issubset(source_refs):
                    raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_{evidence_field.upper()}_NOT_IN_SOURCE_REFS")
            materiality = claim.get("materiality")
            if isinstance(materiality, Mapping) and materiality.get("is_material"):
                material_count += 1
                if not claim.get("decision_basis") or not claim.get("return_route"):
                    raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_RESEARCH_STOP_BASIS_REQUIRED")
                if not claim.get("contradiction_refs"):
                    claim["contradiction_refs"] = []
        if not material_count:
            raise ResearchB3Error("M5_MATERIAL_CLAIM_REQUIRED")
        for section, id_field in (("rival_explanations", "rival_id"), ("contradictions", "contradiction_id"), ("gaps", "gap_id")):
            entries = value.get(section)
            if not isinstance(entries, list):
                raise ResearchB3Error(f"M5_{section.upper()}_REQUIRED")
            for entry in entries:
                if not isinstance(entry, Mapping) or not entry.get(id_field) or not entry.get("statement"):
                    raise ResearchB3Error(f"M5_{section.upper()}_ENTRY_INVALID")
                cls._known_refs(entry.get("evidence_refs"), known, f"{section}:{entry.get(id_field)}", allow_empty=section == "gaps")
                affected = entry.get("affected_claim_ids")
                if section == "contradictions":
                    if "affected_claim_ids" not in entry or not isinstance(affected, list):
                        raise ResearchB3Error(f"{section}:{entry.get(id_field)}_CLAIM_LINKAGE_REQUIRED")
                    if not set(map(str, affected)).issubset(claim_ids):
                        raise ResearchB3Error(f"{section}:{entry.get(id_field)}_CLAIM_REF_INVALID")
                    subject_ids = dict(known_subject_ids or {})
                    subject_ids["MATERIAL_CLAIM"] = claim_ids
                    contradiction_errors = validate_contradiction_disposition(
                        dict(entry), known, known, claim_ids, subject_ids
                    )
                    if contradiction_errors:
                        raise ResearchB3Error(
                            f"{section}:{entry.get(id_field)}_CANONICAL_INVALID: "
                            + " | ".join(contradiction_errors)
                        )
                elif not isinstance(affected, list) or not set(map(str, affected)).issubset(claim_ids):
                    raise ResearchB3Error(f"{section}:{entry.get(id_field)}_CLAIM_REF_INVALID")
                if section == "gaps" and entry.get("status") == "RESOLVED" and not entry.get("evidence_refs"):
                    raise ResearchB3Error(f"{section}:{entry.get(id_field)}_CANNOT_CLOSE_WITHOUT_EVIDENCE")

    @classmethod
    def _materialize_m5_claim_stops(cls, ledger: Mapping[str, Any], plan: Mapping[str, Any], known: set[str]) -> list[dict[str, Any]]:
        decisions = []
        for claim in ledger["claims"]:
            materiality = claim.get("materiality") if isinstance(claim.get("materiality"), Mapping) else {}
            if not materiality.get("is_material"):
                continue
            status = claim.get("research_sufficiency")
            decision = claim.get("claim_decision")
            if status not in {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE", "MORE_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE"}:
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_SUFFICIENCY_INVALID")
            route_code = materiality.get("return_route_code")
            if not route_code:
                raise ResearchB3Error(f"CLAIM:{claim.get('claim_id')}_RETURN_ROUTE_CODE_REQUIRED")
            pending = [str(item) for item in claim.get("pending_matters", [])]
            contradictions = [str(item) for item in claim.get("contradiction_refs", [])]
            stop = {
                "decision_id": f"{plan['research_plan_id']}:M5:RSD:CLAIM:{claim['claim_id']}",
                "decision_version": M4_CONTRACT_VERSION,
                "subject_kind": "MATERIAL_CLAIM",
                "subject_ref": claim["claim_id"],
                "intended_use": claim.get("intended_use") or M5_CLAIMS_USE,
                "evidence_refs": sorted(cls._known_refs(claim["source_refs"], known, f"CLAIM:{claim['claim_id']}", allow_empty=False)),
                "claim_decision": decision,
                "sufficiency_status": status,
                "limitations": [str(claim["limitations"])] if isinstance(claim.get("limitations"), str) and claim["limitations"].strip() else list(claim.get("limitations") or []),
                "pending_matters": pending,
                "unresolved_material_contradiction_refs": contradictions,
                "invalidators": list(materiality.get("invalidator_codes") or []),
                "invalidator_codes": list(materiality.get("invalidator_codes") or []),
                "return_route": str(claim["return_route"]),
                "return_route_code": route_code,
                "decision_basis": str(claim["decision_basis"]),
                "research_contract_version": M4_CONTRACT_VERSION,
                "artifact_validity": "VALID",
                "research_stage": "SYNTHESIS",
                "operational_guard_ref": f"software:iteration-guard:{plan['research_plan_id']}",
            }
            errors = validate_research_stop_decision(stop)
            if errors:
                raise ResearchB3Error("M5_CLAIM_STOP_INVALID: " + " | ".join(errors))
            decisions.append(stop)
        return decisions

    @classmethod
    def _validate_m5_comparison(
        cls, value: Any, selected_ids: list[str], known: set[str], selection_mode: str,
    ) -> None:
        if not isinstance(value, Mapping):
            raise ResearchB3Error("M5_COMPARISON_REQUIRED")
        errors = validate_against_schema(dict(value), "research_comparison")
        if errors:
            raise ResearchB3Error("M5_COMPARISON_INVALID: " + " | ".join(errors))
        if value.get("decision_stage") != M5_COMPARISON_STAGE or value.get("narrative_decision_made") is not False:
            raise ResearchB3Error("M5_COMPARISON_STAGE_OR_NARRATIVE_INVALID")
        if value.get("selection_mode") != selection_mode:
            raise ResearchB3Error("M5_SELECTION_MODE_LINEAGE_INVALID")
        if value.get("selected_work_ids") != selected_ids:
            raise ResearchB3Error("M5_SILENT_SELECTION_CHANGE")
        entry_ids = {str(item.get("work_id")) for item in value.get("entries", [])}
        if entry_ids != set(selected_ids):
            raise ResearchB3Error("M5_COMPARISON_WORK_SET_INVALID")
        for entry in value["entries"]:
            if "missing_perspectives" not in entry or not isinstance(entry.get("missing_perspectives"), list):
                raise ResearchB3Error(f"M5_COMPARISON_MISSING_PERSPECTIVES_REQUIRED:{entry.get('work_id')}")
            if not all(isinstance(item, str) and item.strip() for item in entry["missing_perspectives"]):
                raise ResearchB3Error(f"M5_COMPARISON_MISSING_PERSPECTIVES_INVALID:{entry.get('work_id')}")
            if not isinstance(entry.get("overinterpretation_risk"), str) or not entry["overinterpretation_risk"].strip():
                raise ResearchB3Error(f"M5_COMPARISON_OVERINTERPRETATION_RISK_REQUIRED:{entry.get('work_id')}")
            cls._known_refs(entry.get("evidence_refs"), known, f"M5_COMPARISON:{entry.get('work_id')}", allow_empty=False)
        recommendations = value.get("set_recommendations")
        if not isinstance(recommendations, list) or not recommendations:
            raise ResearchB3Error("M5_SET_RECOMMENDATIONS_REQUIRED")
        changed = False
        for recommendation in recommendations:
            if not isinstance(recommendation, Mapping) or recommendation.get("action") not in {"MAINTAIN", "REDUCE", "REMOVE", "REPLACE", "ADD"}:
                raise ResearchB3Error("M5_SET_RECOMMENDATION_INVALID")
            affected_work_ids = recommendation.get("affected_work_ids")
            if not isinstance(affected_work_ids, list):
                raise ResearchB3Error("M5_SET_RECOMMENDATION_WORK_REF_INVALID")
            affected_ids = set(map(str, affected_work_ids))
            if recommendation.get("action") != "ADD" and not affected_ids.issubset(set(selected_ids)):
                raise ResearchB3Error("M5_SET_RECOMMENDATION_WORK_REF_INVALID")
            if recommendation.get("action") == "ADD":
                requirements = value.get("substitution_research_requirements")
                required_work_ids = {
                    str(item.get("work_id")) for item in requirements or []
                    if isinstance(item, Mapping) and item.get("status") == "RESEARCH_REQUIRED"
                }
                if not affected_ids - set(selected_ids) or not (affected_ids - set(selected_ids)).issubset(required_work_ids):
                    raise ResearchB3Error("M5_SUBSTITUTE_CANNOT_ENTER_AS_EQUIVALENT")
            if not recommendation.get("rationale"):
                raise ResearchB3Error("M5_SET_RECOMMENDATION_RATIONALE_REQUIRED")
            cls._known_refs(recommendation.get("evidence_refs"), known, "M5_SET_RECOMMENDATION", allow_empty=False)
            if recommendation.get("action") != "MAINTAIN" or recommendation.get("material_change") is True:
                changed = True
        if changed and value.get("human_decision_required") is not True:
            raise ResearchB3Error("M5_SELECTION_CHANGE_HUMAN_DECISION_FLAG_REQUIRED")
        if not changed and value.get("human_decision_required") is True:
            raise ResearchB3Error("M5_SELECTION_CHANGE_HUMAN_DECISION_FLAG_INVALID")
        if changed and selection_mode not in {"USER_SELECTION", "DELEGATED_SELECTION"}:
            raise ResearchB3Error("M5_SELECTION_CHANGE_MODE_INVALID")
        if changed:
            if any(item.get("action") in {"REPLACE", "ADD"} for item in recommendations):
                requirements = value.get("substitution_research_requirements")
                if not isinstance(requirements, list) or not requirements:
                    raise ResearchB3Error("M5_SUBSTITUTE_RESEARCH_REQUIRED")
                if not all(isinstance(item, Mapping) and item.get("status") == "RESEARCH_REQUIRED" and item.get("work_id") for item in requirements):
                    raise ResearchB3Error("M5_SUBSTITUTE_CANNOT_ENTER_AS_EQUIVALENT")

    @classmethod
    def _validate_m5_thesis(
        cls, value: Any, provisional: Mapping[str, Any], ledger: Mapping[str, Any], comparison: Mapping[str, Any],
        claim_stops: list[dict[str, Any]], known: set[str], plan: Mapping[str, Any], claims_ref: Mapping[str, Any],
        comparison_ref: Mapping[str, Any], claim_stops_ref: Mapping[str, Any],
    ) -> None:
        if not isinstance(value, Mapping):
            raise ResearchB3Error("M5_REFINED_THESIS_REQUIRED")
        errors = validate_against_schema(dict(value), "refined_thesis")
        if errors:
            raise ResearchB3Error("M5_REFINED_THESIS_INVALID: " + " | ".join(errors))
        if value.get("provisional_thesis_id") != provisional.get("thesis_id"):
            raise ResearchB3Error("M5_PROVISIONAL_THESIS_LINEAGE_INVALID")
        if value.get("owner_scope") != "RESEARCH" or value.get("semantic_audit_id") != "NOT_PERFORMED_M6_PENDING" or value.get("curation_id") != "NOT_APPLICABLE_M5_RESEARCH_SCOPE":
            raise ResearchB3Error("M5_THESIS_SCOPE_OR_AUDIT_INVALID")
        disposition = value.get("provisional_disposition")
        if disposition not in M5_PROVISIONAL_DISPOSITIONS:
            raise ResearchB3Error("M5_PROVISIONAL_DISPOSITION_INVALID")
        if f"software:m5:provisional-disposition:{disposition}" not in set(value.get("lineage", [])):
            raise ResearchB3Error("M5_PROVISIONAL_DISPOSITION_LINEAGE_INVALID")
        for field in ("supporting_evidence_refs", "counterevidence_refs"):
            cls._known_refs(value.get(field), known, f"M5_THESIS_{field.upper()}", allow_empty=False)
        for dimension in value.get("refinement_dimensions", []):
            cls._known_refs(dimension.get("evidence_refs"), known, "M5_THESIS_DIMENSION", allow_empty=False)
        expected_lineage = {provisional.get("thesis_id"), claims_ref.get("artifact_id"), comparison_ref.get("artifact_id"), claim_stops_ref.get("artifact_id")}
        if not expected_lineage.issubset(set(value.get("lineage", []))):
            raise ResearchB3Error("M5_THESIS_LINEAGE_INCOMPLETE")
        if any(field in value for field in {"hook", "viewer_journey", "narrative_plan", "opening_design", "closing_design", "pacing", "climax", "cta", "title", "thumbnail"}):
            raise ResearchB3Error("M5_NARRATIVE_OUTPUT_FORBIDDEN")

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
        artifact_id = str(value.get("thesis_id") or value.get("dossier_id") or value.get("lifecycle_id") or value.get("research_id") or kind)
        return {
            "artifact_id": artifact_id,
            "artifact_kind": kind,
            "artifact_version": str(value.get("version") or value.get("artifact_version") or CONTRACT_VERSION),
            "checksum": _checksum(value),
        }


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
