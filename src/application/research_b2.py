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

# Cognitive responses may contain proposed content only.  These fields are
# bound by Software after the response crosses the seam and must never be
# accepted as external authority.
SOFTWARE_OWNED_FIELDS = {
    "artifact_id", "artifact_version", "dossier_id", "dossier_version",
    "decision_id", "decision_version", "lifecycle_id", "lifecycle_version",
    "thesis_id", "version", "created_at", "artifact_validity",
    "research_contract_version",
    "software_controlled", "recovery_artifact_ref", "retrieval_request_ref",
    "request_ref", "execution_ref", "checksum", "checksums",
    "operational_guard_ref", "research_stop_decision_ref", "research_id",
    "episode_id", "evidence_report_id", "comparison_id", "comparison_version",
    "ledger_id", "contract_version", "ledger_stage", "semantic_audit_id",
    "curation_id", "owner_scope", "provisional_thesis_id", "claims_ledger_id",
    "research_comparison_id", "research_stop_decision_refs", "analysis_ids",
    "provisional_disposition", "decision_ref", "selection_authority_ref",
    "authorized_candidate_set",
}


def _strip_cognitive_technical(value: Any, *, top_level_only: bool = False, _depth: int = 0) -> Any:
    """Remove Software-owned authority before canonical B2 projection."""
    if isinstance(value, dict):
        return {
            key: _strip_cognitive_technical(item, top_level_only=top_level_only, _depth=_depth + 1)
            for key, item in value.items()
            if not (key in SOFTWARE_OWNED_FIELDS and (not top_level_only or _depth == 0))
        }
    if isinstance(value, list):
        return [_strip_cognitive_technical(item, top_level_only=top_level_only, _depth=_depth + 1) for item in value]
    return copy.deepcopy(value)


class ResearchB2Error(ValueError):
    """A deterministic B2 contract, routing, or persistence failure."""


@dataclass(frozen=True)
class B2CognitiveRequest:
    """The only payload handed from Software to an injected cognitive step."""

    stage: str
    output_schema: str
    input_artifacts: tuple[dict[str, str], ...]
    prepared_contract: dict[str, Any]
    # The producer of the cognitive request is authoritative for the role.
    # The external boundary only transports this binding; it must not infer
    # roles from stage names.
    role_id: str = "RESEARCH_AND_CURATION"


class ResearchB2Persistence:
    """Small B2 adapter that reuses the repository's atomic JSON writer."""

    _FILENAMES = {
        "RESEARCH_PLAN_PROPOSAL": "research_plan_proposal.json",
        "RESEARCH_PLAN": "research_plan.json",
        "SOURCE_ACCESS_EVIDENCE_REPORT": "source_access_and_evidence_report.json",
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

    def load_existing(
        self, stage: str, *, artifact_id: str, artifact_kind: str,
    ) -> tuple[dict[str, str], Any] | None:
        """Recover a persisted B2 artifact without reopening its write slot."""
        filename = self._FILENAMES.get(stage)
        if filename is None:
            raise ResearchB2Error(f"B2_UNKNOWN_PERSISTENCE_STAGE: {stage}")
        path = self.root / filename
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchB2Error(f"{stage}_RECOVERY_UNREADABLE") from exc
        ref = {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "artifact_version": CONTRACT_VERSION,
            "path": str(path),
            "checksum": _checksum(payload),
        }
        self._persisted[stage] = ref
        return ref, payload


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
        recovery_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
        execution_registry_path: str | Path | None = None,
    ):
        self.bindings = {str(key): dict(value) for key, value in (bindings or {}).items()}
        self.work_bindings = {str(key): dict(value) for key, value in (work_bindings or {}).items()}
        self.work_representation_bindings = {
            self._representation_key_from_mapping_key(key, value): dict(value)
            for key, value in (work_representation_bindings or {}).items()
        }
        self.recovery_artifacts = {
            str(key): dict(value) for key, value in (recovery_artifacts or {}).items()
        }
        self.execution_registry_path = (
            Path(execution_registry_path) if execution_registry_path is not None else None
        )
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

    def _resolve_recovery_artifact(
        self, binding: Mapping[str, Any], *, expected_id: str, label: str,
    ) -> None:
        """Resolve a positive binding against a physical Software artifact."""
        ref = str(binding.get("recovery_artifact_ref") or "")
        record = self.recovery_artifacts.get(ref)
        if not record:
            raise ResearchB2Error(f"{label}_RECOVERY_ARTIFACT_UNRESOLVED:{ref}")
        path = Path(str(record.get("path") or ""))
        if not path.is_file():
            raise ResearchB2Error(f"{label}_RECOVERY_ARTIFACT_MISSING:{ref}")
        raw_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        if raw_checksum != str(record.get("checksum") or ""):
            raise ResearchB2Error(f"{label}_RECOVERY_ARTIFACT_CHECKSUM_MISMATCH:{ref}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchB2Error(f"{label}_RECOVERY_ARTIFACT_INVALID:{ref}") from exc
        observed = str(payload.get("source_id") or payload.get("work_id") or "")
        if observed != expected_id:
            raise ResearchB2Error(f"{label}_RECOVERY_ARTIFACT_SOURCE_MISMATCH:{ref}")
        execution_ref = str(binding.get("execution_ref") or "")
        if not execution_ref or self.execution_registry_path is None:
            raise ResearchB2Error(f"{label}_RECOVERY_EXECUTION_UNRESOLVED:{expected_id}")
        try:
            registry = json.loads(self.execution_registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchB2Error(f"{label}_RECOVERY_EXECUTION_REGISTRY_UNRESOLVED:{execution_ref}") from exc
        violations = validate_against_schema(registry, "execution_provenance_registry")
        if violations:
            raise ResearchB2Error(f"{label}_RECOVERY_EXECUTION_REGISTRY_INVALID:{execution_ref}")
        run = next(
            (
                item for item in registry.get("runs", [])
                if isinstance(item, Mapping) and item.get("run_id") == execution_ref
            ),
            None,
        )
        if run is None:
            raise ResearchB2Error(f"{label}_RECOVERY_EXECUTION_UNRESOLVED:{execution_ref}")
        if run.get("status") != "SUCCEEDED":
            raise ResearchB2Error(f"{label}_RECOVERY_EXECUTION_NOT_SUCCEEDED:{execution_ref}")
        if not any(
            isinstance(output, Mapping)
            and output.get("artifact_id") == ref
            and output.get("checksum") == raw_checksum
            for output in run.get("outputs", [])
        ):
            raise ResearchB2Error(f"{label}_RECOVERY_EXECUTION_OUTPUT_UNRESOLVED:{execution_ref}")

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
            if positive:
                self._resolve_recovery_artifact(binding, expected_id=source_id, label="SOURCE")
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
                self._resolve_recovery_artifact(binding, expected_id=work_id, label="WORK")
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
        source_access_errors = validate_against_schema(context["source_access"], "research_source_access")
        if source_access_errors:
            raise ResearchB2Error("B2_SOURCE_ACCESS_INVALID: " + " | ".join(source_access_errors))
        if "evidence_report" in context:
            raise ResearchB2Error("B2_EVIDENCE_REPORT_PREINJECTION_FORBIDDEN")

        events: list[dict[str, Any]] = []
        persisted_order = (
            "RESEARCH_PLAN", "PHENOMENON_BASE_RESEARCH", "SOURCE_ACCESS_EVIDENCE_REPORT",
            "WORK_DISCOVERY", "BASE_RESEARCH_POOL", "PRELIMINARY_FIDELITY",
            "INITIAL_SUFFICIENCY", "PROVISIONAL_THESIS", "RESEARCH_COMPARISON",
        )
        existing_flags = [
            self.persistence.load_existing(stage, artifact_id="_probe", artifact_kind="_probe") is not None
            for stage in persisted_order
        ]
        # A later persisted seam with an absent predecessor is not a valid
        # resumable checkpoint; never skip that inconsistency silently.
        first_missing = next((index for index, exists in enumerate(existing_flags) if not exists), len(existing_flags))
        if any(existing_flags[index] for index in range(first_missing + 1, len(existing_flags))):
            raise ResearchB2Error("B2_PERSISTED_SEAM_GAP")

        def recover(
            stage: str,
            artifact_id: str,
            artifact_kind: str,
            validator: Callable[[Any], None] | None = None,
        ) -> tuple[dict[str, str], Any] | None:
            loaded = self.persistence.load_existing(stage, artifact_id=artifact_id, artifact_kind=artifact_kind)
            if loaded is None:
                return None
            ref, payload = loaded
            if validator is not None:
                try:
                    validation_payload = (
                        payload.get("dossiers")
                        if stage in {"BASE_RESEARCH_POOL", "PRELIMINARY_FIDELITY", "INITIAL_SUFFICIENCY"}
                        and isinstance(payload, Mapping) and isinstance(payload.get("dossiers"), list)
                        else payload
                    )
                    validator(validation_payload)
                except (TypeError, KeyError, ValueError) as exc:
                    raise ResearchB2Error(f"B2_PERSISTED_{stage}_INVALID") from exc
            events.append({"stage": stage, "boundary": "SOFTWARE_RECOVER", "artifact_id": ref["artifact_id"]})
            if stage in {"BASE_RESEARCH_POOL", "PRELIMINARY_FIDELITY", "INITIAL_SUFFICIENCY"} and isinstance(payload, Mapping) and isinstance(payload.get("dossiers"), list):
                return ref, payload["dossiers"]
            return ref, payload

        plan_loaded = recover("RESEARCH_PLAN", plan["research_plan_id"], "ResearchPlan", lambda value: self._validate_plan_recovery(value, plan))
        if plan_loaded is None:
            plan_ref = self.persistence.persist(
                "RESEARCH_PLAN", plan, artifact_id=plan["research_plan_id"], artifact_kind="ResearchPlan"
            )
        else:
            plan_ref, plan = plan_loaded
        artifacts = [plan_ref]

        phenomenon_loaded = recover("PHENOMENON_BASE_RESEARCH", plan["research_plan_id"], "ResearchPack", self._validate_phenomenon)
        if phenomenon_loaded is None:
            phenomenon = self._step("PHENOMENON_BASE_RESEARCH", "research_pack", plan, context, artifacts, events, self._validate_phenomenon)
            phenomenon_ref = self.persistence.persist("PHENOMENON_BASE_RESEARCH", phenomenon, artifact_id=phenomenon["research_id"], artifact_kind="ResearchPack")
            events.append({"stage": "PHENOMENON_BASE_RESEARCH", "boundary": "SOFTWARE_PERSIST", "artifact_id": phenomenon_ref["artifact_id"]})
        else:
            phenomenon_ref, phenomenon = phenomenon_loaded
        artifacts.append(phenomenon_ref)

        # Source access is PRE_RESEARCH input.  Once the base phenomenon has
        # actually been produced, Software creates the separate evidence
        # report consumed by evidence-dependent stages.  It is never stored
        # back under context["source_access"].
        evidence_report = self._build_evidence_report(
            plan=plan, context=context, phenomenon=phenomenon,
        )
        report_errors = validate_source_access_and_evidence_report(dict(evidence_report)) if isinstance(evidence_report, Mapping) else ["evidence_report debe ser un objeto"]
        if report_errors:
            raise ResearchB2Error("B2_EVIDENCE_REPORT_INVALID: " + " | ".join(report_errors))
        evidence_loaded = recover("SOURCE_ACCESS_EVIDENCE_REPORT", f"{plan['research_plan_id']}:SOURCE_ACCESS_EVIDENCE_REPORT", "SourceAccessAndEvidenceReport", lambda value: self._validate_evidence_recovery(value, plan))
        if evidence_loaded is None:
            evidence_report_ref = self.persistence.persist("SOURCE_ACCESS_EVIDENCE_REPORT", dict(evidence_report), artifact_id=str(evidence_report["report_id"]), artifact_kind="SourceAccessAndEvidenceReport")
        else:
            evidence_report_ref, evidence_report = evidence_loaded
        artifacts.append(evidence_report_ref)
        evidence_context = dict(context)
        evidence_context["evidence_report"] = dict(evidence_report)

        discovery_loaded = recover("WORK_DISCOVERY", f"{plan['research_plan_id']}:DISCOVERY", "WorkLifecycle", self._validate_discovery)
        if discovery_loaded is None:
            discovery = self._step("WORK_DISCOVERY", "work_lifecycle", plan, evidence_context, artifacts, events, self._validate_discovery)
            discovery_ref = self.persistence.persist("WORK_DISCOVERY", discovery, artifact_id=discovery["lifecycle_id"], artifact_kind="WorkLifecycle")
            events.append({"stage": "WORK_DISCOVERY", "boundary": "SOFTWARE_PERSIST", "artifact_id": discovery_ref["artifact_id"]})
        else:
            discovery_ref, discovery = discovery_loaded
        artifacts.append(discovery_ref)

        pool_validator = lambda value: self._validate_pool(value, discovery)
        pool_loaded = recover("BASE_RESEARCH_POOL", f"{plan['research_plan_id']}:BASE_RESEARCH_POOL", "WorkResearchDossierCollection", pool_validator)
        if pool_loaded is None:
            pool = self._step("BASE_RESEARCH_POOL", "work_research_dossier", plan, evidence_context, artifacts, events, pool_validator)
            pool_ref = self.persistence.persist("BASE_RESEARCH_POOL", pool, artifact_id=f"{plan['research_plan_id']}:BASE_RESEARCH_POOL", artifact_kind="WorkResearchDossierCollection")
            events.append({"stage": "BASE_RESEARCH_POOL", "boundary": "SOFTWARE_PERSIST", "artifact_id": pool_ref["artifact_id"]})
        else:
            pool_ref, pool = pool_loaded
        artifacts.append(pool_ref)

        fidelity_validator = lambda value: self._validate_fidelity(value, pool)
        fidelity_loaded = recover("PRELIMINARY_FIDELITY", f"{plan['research_plan_id']}:PRELIMINARY_FIDELITY", "WorkResearchDossierCollection", fidelity_validator)
        if fidelity_loaded is None:
            fidelity = self._step("PRELIMINARY_FIDELITY", "work_research_dossier", plan, evidence_context, artifacts, events, fidelity_validator)
            fidelity_ref = self.persistence.persist("PRELIMINARY_FIDELITY", fidelity, artifact_id=f"{plan['research_plan_id']}:PRELIMINARY_FIDELITY", artifact_kind="WorkResearchDossierCollection")
            events.append({"stage": "PRELIMINARY_FIDELITY", "boundary": "SOFTWARE_PERSIST", "artifact_id": fidelity_ref["artifact_id"]})
        else:
            fidelity_ref, fidelity = fidelity_loaded
        artifacts.append(fidelity_ref)

        sufficiency_validator = lambda value: self._validate_sufficiency(value, phenomenon, pool)
        sufficiency_loaded = recover("INITIAL_SUFFICIENCY", f"{plan['research_plan_id']}:INITIAL_SUFFICIENCY", "ResearchStopDecisionCollection", sufficiency_validator)
        if sufficiency_loaded is None:
            sufficiency = self._step("INITIAL_SUFFICIENCY", "research_stop_decision", plan, evidence_context, artifacts, events, sufficiency_validator)
            sufficiency_ref = self.persistence.persist("INITIAL_SUFFICIENCY", sufficiency, artifact_id=f"{plan['research_plan_id']}:INITIAL_SUFFICIENCY", artifact_kind="ResearchStopDecisionCollection")
            events.append({"stage": "INITIAL_SUFFICIENCY", "boundary": "SOFTWARE_PERSIST", "artifact_id": sufficiency_ref["artifact_id"]})
        else:
            sufficiency_ref, sufficiency = sufficiency_loaded
        artifacts.append(sufficiency_ref)
        if not self._sufficiency_allows_thesis(sufficiency, phenomenon):
            raise ResearchB2Error("PROVISIONAL_THESIS_BLOCKED_BY_INVALID_SUFFICIENCY")

        thesis_validator = lambda value: self._validate_provisional_thesis(value, phenomenon, evidence_context["evidence_report"])
        thesis_loaded = recover("PROVISIONAL_THESIS", f"{plan['research_plan_id']}:THESIS:PROVISIONAL", "ThesisArtifact", thesis_validator)
        if thesis_loaded is None:
            thesis = self._step("PROVISIONAL_THESIS", "thesis_artifact", plan, evidence_context, artifacts, events, thesis_validator)
            thesis_ref = self.persistence.persist("PROVISIONAL_THESIS", thesis, artifact_id=thesis["thesis_id"], artifact_kind="ThesisArtifact")
            events.append({"stage": "PROVISIONAL_THESIS", "boundary": "SOFTWARE_PERSIST", "artifact_id": thesis_ref["artifact_id"]})
        else:
            thesis_ref, thesis = thesis_loaded
        artifacts.append(thesis_ref)

        comparison_validator = lambda value: self._validate_comparison(value, fidelity, sufficiency)
        comparison_loaded = recover("RESEARCH_COMPARISON", f"{plan['research_plan_id']}:COMPARISON:INITIAL", "ResearchComparison", comparison_validator)
        if comparison_loaded is None:
            comparison = self._step("RESEARCH_COMPARISON", "research_comparison", plan, evidence_context, artifacts, events, comparison_validator)
            comparison_ref = self.persistence.persist("RESEARCH_COMPARISON", comparison, artifact_id=comparison["comparison_id"], artifact_kind="ResearchComparison")
            events.append({"stage": "RESEARCH_COMPARISON", "boundary": "SOFTWARE_PERSIST", "artifact_id": comparison_ref["artifact_id"]})
        else:
            comparison_ref, comparison = comparison_loaded
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
                "evidence_report": evidence_report_ref,
                "deepening_targets": deepening_targets,
                "lifecycle_projection": lifecycle,
            },
            artifact_id=f"{plan['research_plan_id']}:B2",
            artifact_kind="ResearchB2ExecutionManifest",
        )
        return {
            "research_plan": plan_ref,
            "phenomenon_base_research": phenomenon_ref,
            "evidence_report": evidence_report_ref,
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
    def _validate_plan_recovery(value: Any, expected: Mapping[str, Any]) -> None:
        errors = validate_research_plan(value) if isinstance(value, Mapping) else ["ResearchPlan debe ser un objeto"]
        if errors or dict(value) != dict(expected):
            raise ResearchB2Error("PERSISTED_RESEARCH_PLAN_MISMATCH")

    @staticmethod
    def _validate_evidence_recovery(value: Any, plan: Mapping[str, Any]) -> None:
        errors = validate_source_access_and_evidence_report(value) if isinstance(value, Mapping) else ["evidence_report debe ser un objeto"]
        if errors or value.get("episode_id") != plan.get("episode_id") or value.get("research_id") != plan.get("research_plan_id"):
            raise ResearchB2Error("PERSISTED_EVIDENCE_REPORT_MISMATCH")

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

    @staticmethod
    def _build_evidence_report(
        *, plan: Mapping[str, Any], context: Mapping[str, Any], phenomenon: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Project the base-research evidence boundary from verified inputs.

        The report is deliberately software-owned: source identity and
        provenance come from the ResearchPack output and the PRE_RESEARCH
        ResearchSourceAccess.  No evidence or source is invented here.
        """
        source_access = context["source_access"]
        source_entries: list[dict[str, Any]] = []
        for raw in phenomenon.get("source_registry", []):
            if not isinstance(raw, Mapping) or not raw.get("source_id"):
                continue
            provenance = raw.get("provenance")
            if not isinstance(provenance, Mapping):
                continue
            entry = {
                "source_id": str(raw["source_id"]),
                "title": str(raw.get("title") or raw.get("source_id")),
                "source_type": str(raw.get("source_type") or "RESEARCH_SOURCE"),
                "url": raw.get("url"),
                "access_type": str(raw.get("access_type") or "DIRECT"),
                "locator": str(raw.get("locator") or provenance.get("locator") or "source registry"),
                "confidence": str(raw.get("confidence") or "MEDIUM"),
                "provenance": copy.deepcopy(dict(provenance)),
            }
            for field in ("evidence_domain", "retrieval_status", "evidence_status", "recovery_artifact_ref", "retrieval_request_ref"):
                if field in raw:
                    entry[field] = copy.deepcopy(raw[field])
            source_entries.append(entry)
        materials = source_access.get("materials", []) if isinstance(source_access, Mapping) else []
        limitations = [str(item) for item in source_access.get("limitations", [])] if isinstance(source_access, Mapping) else []
        if not source_entries:
            limitations.append("La investigación base no ha producido fuentes verificables.")
        limitations = list(dict.fromkeys(limitations))
        central_question = plan.get("central_question", {})
        central_question_text = str(central_question.get("question") if isinstance(central_question, Mapping) else central_question)
        report = {
            "report_id": f"{plan['research_plan_id']}:SOURCE_ACCESS_EVIDENCE_REPORT",
            "episode_id": str(plan["episode_id"]),
            "research_id": str(plan["research_plan_id"]),
            "brief_version": str(plan["brief_version"]),
            "material_principal_disponible": bool(materials or source_entries),
            "tipo_de_acceso": "DIRECT" if source_entries else "UNAVAILABLE",
            "fuentes_primarias": source_entries,
            "fuentes_secundarias": [],
            "escenas_verificadas": [],
            "escenas_descritas_indirectamente": [],
            "claims_sostenibles": [],
            "claims_pendientes": [],
            "limitaciones": limitations,
            "nivel_de_confianza": "MEDIUM" if source_entries else "LOW",
            "can_proceed": bool(source_entries),
            "allowed_analyses": ["CONTEXTUAL_ANALYSIS"] if source_entries else [],
            "limited_analyses": [],
            "prohibited_analyses": [],
            "excluded_claims": [],
            "required_disclosures": [],
            "propagated_constraints": limitations,
            "critical_claim_assessments": [],
            "critical_claims_propagation": {
                "status": "NONE_JUSTIFIED", "claim_ids": [], "justification": "No se han materializado claims críticos en este límite de evidencia.",
                "editorial_impact": "LIMITED", "scope_decision": "RESEARCH_ONLY",
            },
            "sufficiency_basis": {
                "central_question": central_question_text or "Pregunta de investigación declarada.",
                "critical_claims": [str(item.get("statement")) for item in plan.get("critical_claims", []) if isinstance(item, Mapping) and item.get("statement")],
                "analysis_type": "CONTEXTUAL_ANALYSIS",
                "material_roles": ["PHENOMENON"],
                "requested_depth": "BASE_RESEARCH",
                "research_coverage": "Cobertura limitada al fenómeno y fuentes producidas en BASE_RESEARCH.",
            },
            "multilingual_research": {
                "activation_status": "NOT_ACTIVATED", "triggers": [], "non_trigger_examples": ["NO_LINGUISTIC_DIFFERENCE_REQUIRED"],
                "affected_source_ids": [], "affected_claim_ids": [], "required_language": None, "material_risk": [],
                "consultation_result": "NOT_APPLICABLE", "limitations": [], "invalidators": [], "return_route": "NOT_APPLICABLE",
                "decision_basis": "No se ha activado una diferencia lingüística material.",
            },
            "research_stage": "BASE_RESEARCH",
            "research_contract_version": CONTRACT_VERSION,
            "artifact_validity": "VALID",
            "evidence_type_separation": copy.deepcopy(phenomenon.get("evidence_type_separation", {
                "work_evidence_refs": [], "external_reality_evidence_refs": [entry["source_id"] for entry in source_entries],
            })),
            "acquisition_bindings": copy.deepcopy(phenomenon.get("acquisition_bindings", [])),
            "created_at": utc_now(),
        }
        return report

    @staticmethod
    def advance_evidence_report(
        previous_report: Mapping[str, Any], *, research_stage: str,
        stage_evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create the next immutable evidence boundary from accepted evidence.

        The evidence schema does not permit synthetic lineage fields.  The
        predecessor/output relationship is therefore persisted by the stage
        manifests; this payload remains only the current schema-valid report.
        """
        report = copy.deepcopy(dict(previous_report)) if isinstance(previous_report, Mapping) else None
        if not isinstance(report, dict):
            raise ResearchB2Error("EVIDENCE_REPORT_PREDECESSOR_REQUIRED")
        errors = validate_source_access_and_evidence_report(report)
        if errors:
            raise ResearchB2Error("EVIDENCE_REPORT_PREDECESSOR_INVALID: " + " | ".join(errors))
        if research_stage not in {"DEEP_RESEARCH", "REFINED"}:
            raise ResearchB2Error("EVIDENCE_REPORT_STAGE_INVALID")
        report["report_id"] = f"{report['research_id']}:SOURCE_ACCESS_EVIDENCE_REPORT:{research_stage}"
        report["research_stage"] = research_stage
        report["created_at"] = utc_now()
        basis = copy.deepcopy(dict(report.get("sufficiency_basis") or {}))
        basis["requested_depth"] = research_stage
        before_claims = {str(item.get("claim_id")): copy.deepcopy(item) for item in report.get("claims_sostenibles", []) if isinstance(item, Mapping) and item.get("claim_id")}
        before_scenes = {str(item.get("scene_id")): copy.deepcopy(item) for item in report.get("escenas_verificadas", []) if isinstance(item, Mapping) and item.get("scene_id")}
        before_pending = {str(item.get("claim_id")): copy.deepcopy(item) for item in report.get("claims_pendientes", []) if isinstance(item, Mapping) and item.get("claim_id")}
        if isinstance(stage_evidence, Mapping):
            # Carry forward only evidence explicitly emitted by the stage.
            # Identifiers are bound to the already validated source report;
            # no synthetic sources or claims are manufactured here.
            limitations = list(report.get("limitaciones") or [])
            for value in stage_evidence.get("limitations", []) if isinstance(stage_evidence.get("limitations"), list) else []:
                text = str(value).strip()
                if text and text not in limitations:
                    limitations.append(text)
            report["limitaciones"] = limitations
            separation = stage_evidence.get("evidence_type_separation")
            if isinstance(separation, Mapping):
                current = report.get("evidence_type_separation") if isinstance(report.get("evidence_type_separation"), Mapping) else {}
                report["evidence_type_separation"] = {
                    "work_evidence_refs": sorted(set(current.get("work_evidence_refs", [])) | set(separation.get("work_evidence_refs", []))),
                    "external_reality_evidence_refs": sorted(set(current.get("external_reality_evidence_refs", [])) | set(separation.get("external_reality_evidence_refs", []))),
                }
            candidates = stage_evidence.get("claims_candidates")
            if isinstance(candidates, list):
                claims = list(report.get("claims_sostenibles") or [])
                by_id = {str(item.get("claim_id")): item for item in claims if isinstance(item, Mapping) and item.get("claim_id")}
                known_sources = {
                    str(item.get("source_id")) for field in ("fuentes_primarias", "fuentes_secundarias")
                    for item in report.get(field, []) if isinstance(item, Mapping) and item.get("source_id")
                }
                for candidate in candidates:
                    if not isinstance(candidate, Mapping) or not candidate.get("source_refs"):
                        continue
                    claim_id = str(candidate.get("claim_id") or candidate.get("item_id") or "")
                    claim_text = str(candidate.get("claim_text") or candidate.get("statement") or "").strip()
                    locator = str(candidate.get("locator") or "stage output")
                    if not claim_id or not claim_text:
                        continue
                    source_refs = sorted({str(ref) for ref in candidate.get("source_refs", []) if str(ref).strip() and str(ref) in known_sources})
                    if not source_refs:
                        continue
                    raw_confidence = candidate.get("confidence")
                    if isinstance(raw_confidence, (int, float)):
                        confidence = "HIGH" if float(raw_confidence) >= 0.8 else "MEDIUM"
                    else:
                        confidence = str(raw_confidence or "MEDIUM").upper()
                        if confidence not in {"LOW", "MEDIUM", "HIGH"}:
                            confidence = "MEDIUM"
                    by_id[claim_id] = {
                        "claim_id": claim_id,
                        "claim_text": claim_text,
                        "source_refs": source_refs,
                        "locator": locator,
                        "confidence": confidence,
                    }
                report["claims_sostenibles"] = list(by_id.values())
            evidence_items = stage_evidence.get("narrative_evidence")
            if isinstance(evidence_items, list):
                scenes = list(report.get("escenas_verificadas") or [])
                by_scene = {str(item.get("scene_id")): item for item in scenes if isinstance(item, Mapping) and item.get("scene_id")}
                for item in evidence_items:
                    if not isinstance(item, Mapping) or not item.get("source_refs"):
                        continue
                    source_ref = str(item["source_refs"][0])
                    scene_id = str(item.get("scene_id") or item.get("item_id") or "")
                    description = str(item.get("description") or item.get("statement") or "").strip()
                    if scene_id and description:
                        by_scene[scene_id] = {"scene_id": scene_id, "description": description, "source_id": source_ref, "locator": str(item.get("locator") or "stage output"), "verification_mode": "DIRECT"}
                report["escenas_verificadas"] = list(by_scene.values())
            pending_items = stage_evidence.get("pending_claims")
            if isinstance(pending_items, list):
                pending = list(report.get("claims_pendientes") or [])
                by_id = {str(item.get("claim_id")): item for item in pending if isinstance(item, Mapping) and item.get("claim_id")}
                for item in pending_items:
                    if not isinstance(item, Mapping) or not item.get("claim_id") or not item.get("claim_text") or not item.get("reason"):
                        continue
                    candidate = {"claim_id": str(item["claim_id"]), "claim_text": str(item["claim_text"]), "reason": str(item["reason"])}
                    if isinstance(item.get("attempted_source_refs"), list):
                        candidate["attempted_source_refs"] = [str(ref) for ref in item["attempted_source_refs"] if str(ref).strip()]
                    if item.get("locator") is not None:
                        candidate["locator"] = str(item["locator"])
                    if str(item.get("confidence") or "").upper() in {"LOW", "MEDIUM", "HIGH"}:
                        candidate["confidence"] = str(item["confidence"]).upper()
                    by_id[candidate["claim_id"]] = candidate
                report["claims_pendientes"] = list(by_id.values())
            for field in ("propagated_constraints", "required_disclosures", "limited_analyses", "prohibited_analyses"):
                values = list(report.get(field) or [])
                additions = stage_evidence.get(field)
                if field == "propagated_constraints":
                    additions = list(additions or []) + list(stage_evidence.get("downstream_restrictions") or [])
                if isinstance(additions, list):
                    values.extend(str(value) for value in additions if str(value).strip())
                report[field] = list(dict.fromkeys(values))
            for field, identity in (("critical_claim_assessments", "claim_id"), ("coverage_gaps", "dimension"), ("reopening_conditions", "condition_id")):
                additions = stage_evidence.get(field)
                if not isinstance(additions, list):
                    continue
                existing = list(report.get(field) or [])
                by_key = {str(item.get(identity)): item for item in existing if isinstance(item, Mapping) and item.get(identity)}
                for item in additions:
                    if isinstance(item, Mapping) and item.get(identity):
                        by_key[str(item[identity])] = copy.deepcopy(dict(item))
                report[field] = list(by_key.values())
            states = [str(value) for value in stage_evidence.get("sufficiency_states", []) if str(value) in {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE", "MORE_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE"}]
            if states:
                priority = {"BLOCKED_BY_EVIDENCE": 4, "MORE_RESEARCH_REQUIRED": 3, "LIMITED_BUT_USABLE": 2, "SUFFICIENT_FOR_INTENDED_USE": 1}
                report["research_sufficiency"] = max(states, key=lambda value: priority[value])
            updated_claims = sum(before_claims.get(key) != item for key, item in {str(item.get("claim_id")): item for item in report.get("claims_sostenibles", []) if isinstance(item, Mapping) and item.get("claim_id")}.items())
            updated_scenes = sum(before_scenes.get(key) != item for key, item in {str(item.get("scene_id")): item for item in report.get("escenas_verificadas", []) if isinstance(item, Mapping) and item.get("scene_id")}.items())
            updated_pending = sum(before_pending.get(key) != item for key, item in {str(item.get("claim_id")): item for item in report.get("claims_pendientes", []) if isinstance(item, Mapping) and item.get("claim_id")}.items())
            total = len(report.get("claims_sostenibles") or []) + len(report.get("escenas_verificadas") or []) + len(report.get("claims_pendientes") or [])
            contribution = updated_claims + updated_scenes + updated_pending
            observations = stage_evidence.get("stage_observations")
            if isinstance(observations, list):
                observation_payload = [str(value) for value in observations if str(value).strip()]
                observation_digest = hashlib.sha256(
                    json.dumps(observation_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()[:12]
                observation_suffix = f"; huella semántica {observation_digest}"
            else:
                observation_suffix = ""
            basis["research_coverage"] = f"Acumulado: {total}; aportación {research_stage}: {contribution} elementos nuevos o actualizados{observation_suffix}."
        report["sufficiency_basis"] = basis
        errors = validate_source_access_and_evidence_report(report)
        if errors:
            raise ResearchB2Error("EVIDENCE_REPORT_ADVANCE_INVALID: " + " | ".join(errors))
        return report

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
        if "evidence_report" in context:
            input_payload["evidence_report"] = copy.deepcopy(context["evidence_report"])
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
        value = _strip_cognitive_technical(output, top_level_only=True)
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
            report = context.get("evidence_report")
            if isinstance(report, Mapping):
                inherited = set(value.get("inherited_constraints", []))
                for field in ("limitaciones", "excluded_claims", "required_disclosures", "prohibited_analyses", "propagated_constraints"):
                    inherited.update(str(item) for item in report.get(field, []) if item)
                value["inherited_constraints"] = sorted(inherited)
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
        evidence_report = context.get("evidence_report")
        if isinstance(evidence_report, Mapping) and evidence_report.get("report_id"):
            return str(evidence_report["report_id"])
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
