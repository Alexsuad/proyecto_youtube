"""Deterministic M6/B4 handoff from the closed M5 research package.

The cognitive step supplies semantic audit judgments.  Software owns the
audited artifact bindings, provenance, checksums, readiness state, manifest
and gate result.  No provider is called by this module.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Mapping
from pathlib import Path

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute, persist_execution_result
from src.ai.registry import load_registry
from src.ai.role_execution import resolve_role_execution_contract
from src.application.research_b2 import B2CognitiveRequest, CONTRACT_VERSION
from src.application.research_b3 import (
    ResearchB3Error,
    ResearchB3Orchestrator,
    ResearchB3Persistence,
    _checksum,
    _evidence_reference_values,
    utc_now,
)
from src.core.contract_validation import (
    validate_against_schema,
    validate_research_ready_manifest,
)
from src.core.gate_result import GateResult
from src.core.gate_runtime import validate_gate_result
from src.core.invalidation import InvalidationEngine
from src.core.provenance_policy import canonical_registry_path
from src.core.research_audit import validate_independent_research_audit
from src.core.status import GateStatus


M6_AUDIT_STAGE = "M6_INDEPENDENT_RESEARCH_AUDIT"
M6_AUDIT_SCHEMA = "independent_research_audit"
M6_MANIFEST_VERSION = CONTRACT_VERSION
M6_AUDITOR_ROLE = "INDEPENDENT_RESEARCH_AUDITOR"
M6_AUDIT_SEMANTIC_FIELDS = (
    "independence_result",
    "findings",
    "evidence_refs",
    "limitations",
    "defects",
    "correction_routes",
    "decision",
)
M6_REQUIRED_AUDIT_CRITERIA = frozenset({
    "RESEARCH_PLAN_COVERAGE",
    "RESEARCH_STOP_SUFFICIENCY",
    "DEEP_FIDELITY",
    "CLAIMS_EVIDENCE",
    "SOURCE_APPROPRIATENESS_AND_INDEPENDENCE",
    "CLAIM_STRENGTH_VS_EVIDENCE",
    "MATERIAL_PHENOMENON_DEEPENING",
    "RIVALS_CONTRADICTIONS_GAPS",
    "CONFIRMATION_BIAS",
    "SELECTION_AUTHORITY",
    "POST_DEEP_SET_REEVALUATION",
    "SET_DIVERSITY_MISSING_PERSPECTIVES_OVERINTERPRETATION",
    "CLAIM_BLOCKED_DEPENDENCY",
    "THESIS_EVOLUTION",
    "EVIDENCE_DOMAIN_SEPARATION",
    "DOWNSTREAM_LIMITATIONS",
    "RESEARCH_METHOD_REASONABLENESS",
})
M6_REQUIRED_CHAIN_KINDS = frozenset({
    "ResearchPlan",
    "ResearchPack",
    "SourceAccessAndEvidenceReport",
    "ResearchM4ExecutionManifest",
    "ResearchB2ExecutionManifest",
    "ThesisArtifact",
    "WorkResearchDossierCollection",
})
M6_REQUIRED_M4_INPUT_KINDS = frozenset({
    "ResearchM4ExecutionManifest",
    "ResearchStopDecisionCollection",
    "WorkResearchDossierCollection",
})


class ResearchB4Error(ResearchB3Error):
    """Deterministic M6 contract, integrity or readiness failure."""


class ResearchB4Persistence(ResearchB3Persistence):
    """M6 persistence extension over the canonical M4/M5 adapter."""

    _FILENAMES = {
        **ResearchB3Persistence._FILENAMES,
        "M6_INDEPENDENT_RESEARCH_AUDIT": "independent_research_audit_m6.json",
        "M6_RESEARCH_READY_MANIFEST": "research_ready_manifest_m6.json",
        "M6_RESEARCH_READY_GATE": "research_ready_gate.json",
    }


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResearchB4Error(f"{label}_MUST_BE_OBJECT")
    return copy.deepcopy(dict(value))


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _exact_ref(ref: Mapping[str, Any]) -> dict[str, str]:
    return {
        "artifact_id": str(ref["artifact_id"]),
        "artifact_kind": str(ref["artifact_kind"]),
        "artifact_version": str(ref["artifact_version"]),
        "checksum": str(ref["checksum"]),
    }


def _same_ref(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(left.get(field) == right.get(field) for field in (
        "artifact_id", "artifact_kind", "artifact_version", "checksum",
    ))


def _ref_key(ref: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return tuple(str(ref[field]) for field in (
        "artifact_id", "artifact_kind", "artifact_version", "checksum",
    ))


class ResearchB4Orchestrator:
    """Run the independent audit and deterministic ResearchReady gate."""

    def __init__(
        self,
        cognitive_executor: Callable[[B2CognitiveRequest], Any],
        persistence: ResearchB4Persistence,
        *,
        _test_provenance_repository_root: Path | None = None,
    ):
        if not callable(cognitive_executor):
            raise ResearchB4Error("M6_COGNITIVE_EXECUTOR_REQUIRED")
        self.cognitive_executor = cognitive_executor
        self.persistence = persistence
        # Operational M6 always resolves the repository from this module.  A
        # private constructor dependency is retained solely for isolated
        # temporary-repository fixtures; functional context cannot replace it.
        self._provenance_repository_root = (
            Path(_test_provenance_repository_root).resolve()
            if _test_provenance_repository_root is not None
            else Path(__file__).resolve().parents[2]
        )

    @staticmethod
    def _validate_context(context: Mapping[str, Any]) -> dict[str, Any]:
        ctx = _as_mapping(context, "M6_CONTEXT")
        required = ("topic", "source_access", "brief", "channel_context")
        if any(not ctx.get(field) for field in required):
            raise ResearchB4Error("M6_CONTEXT_INVALID")
        return ctx

    @staticmethod
    def _validate_ref(ref: Any, label: str, *, expected_kind: str | None = None) -> None:
        if not isinstance(ref, Mapping):
            raise ResearchB4Error(f"{label}_REFERENCE_METADATA_INVALID")
        fields = ("artifact_id", "artifact_kind", "artifact_version", "checksum", "path")
        if any(not ref.get(field) for field in fields):
            raise ResearchB4Error(f"{label}_REFERENCE_METADATA_INVALID")
        if expected_kind is not None and ref.get("artifact_kind") != expected_kind:
            raise ResearchB4Error(f"{label}_KIND_INVALID")
        if len(str(ref["checksum"])) != 64:
            raise ResearchB4Error(f"{label}_CHECKSUM_INVALID")

    def _load_m5_package(
        self, m5_result: Mapping[str, Any], *, invalidation_engine: InvalidationEngine | None,
    ) -> tuple[dict[str, Any], dict[str, str], dict[str, dict[str, Any]], list[dict[str, str]]]:
        m5_manifest_ref = m5_result.get("execution_manifest")
        self._validate_ref(m5_manifest_ref, "M6_M5_EXECUTION_MANIFEST", expected_kind="ResearchM5ExecutionManifest")
        m5_manifest = ResearchB3Orchestrator._load_persisted_json(m5_manifest_ref, "M6_M5_EXECUTION_MANIFEST")
        if m5_manifest.get("manifest_type") != "RESEARCH_M5_EXECUTION":
            raise ResearchB4Error("M6_M5_MANIFEST_TYPE_INVALID")
        if m5_manifest.get("status") != "READY_FOR_OWNER_REVIEW":
            raise ResearchB4Error("M6_M5_HANDOFF_NOT_COMPLETE")
        required_flags = {
            "real_ai_execution": False,
            "real_research": False,
            "product_use": False,
            "m4_inputs_verified": True,
            "refined_thesis_not_produced": False,
            "research_ready_manifest_not_produced": True,
            "research_ready": False,
            "b5_i3_outputs_not_produced": True,
            "narrative_decisions_not_made": True,
            "final_narrative_selection": False,
        }
        for field, expected in required_flags.items():
            if m5_manifest.get(field) is not expected:
                raise ResearchB4Error(f"M6_M5_MANIFEST_FLAG_INVALID:{field}")

        canonical_by_kind: dict[str, dict[str, str]] = {}
        raw_outputs = m5_manifest.get("m5_outputs")
        if not isinstance(raw_outputs, list) or not raw_outputs:
            raise ResearchB4Error("M6_M5_OUTPUT_REGISTRY_INVALID")
        for raw_ref in raw_outputs:
            self._validate_ref(raw_ref, "M6_M5_OUTPUT")
            ref = _exact_ref(raw_ref) | {"path": str(raw_ref["path"])}
            if ref["artifact_kind"] in canonical_by_kind:
                raise ResearchB4Error(f"M6_M5_OUTPUT_DUPLICATE:{ref['artifact_kind']}")
            payload = ResearchB3Orchestrator._load_persisted_json(ref, f"M6_{ref['artifact_kind']}")
            if payload.get("artifact_validity") in {"STALE", "INVALID", "PENDING_VALIDATION"}:
                raise ResearchB4Error(f"M6_STALE_OR_INVALID_ARTIFACT:{ref['artifact_id']}")
            canonical_by_kind[ref["artifact_kind"]] = ref

        required_outputs = {
            "claims_ledger": "ClaimsLedger",
            "claim_sufficiency": "ResearchStopDecisionCollection",
            "post_deep_comparison": "ResearchComparison",
            "refined_thesis": "RefinedThesis",
        }
        for result_key, artifact_kind in required_outputs.items():
            result_ref = m5_result.get(result_key)
            canonical_ref = canonical_by_kind.get(artifact_kind)
            if not isinstance(result_ref, Mapping) or canonical_ref is None:
                raise ResearchB4Error(f"M6_M5_MATERIAL_ARTIFACT_MISSING:{artifact_kind}")
            self._validate_ref(result_ref, f"M6_M5_RESULT_{result_key}", expected_kind=artifact_kind)
            if not _same_ref(result_ref, canonical_ref):
                raise ResearchB4Error(f"M6_M5_CANONICAL_BINDING_INVALID:{artifact_kind}")

        # Optional M5 decision artifacts are also bound exactly when present.
        for result_key in (
            "human_decision_request", "selection_change_pending",
            "selection_change_decision", "selection_change_delegation",
            "delegated_post_deep_decision", "approved_change_research",
        ):
            result_ref = m5_result.get(result_key)
            if not isinstance(result_ref, Mapping):
                continue
            self._validate_ref(result_ref, f"M6_M5_RESULT_{result_key}")
            canonical_ref = next(
                (item for item in canonical_by_kind.values() if _same_ref(item, result_ref)), None
            )
            if canonical_ref is None:
                raise ResearchB4Error(f"M6_M5_CANONICAL_BINDING_INVALID:{result_key}")

        all_artifact_refs = [_exact_ref(m5_manifest_ref)] + list(canonical_by_kind.values())
        if invalidation_engine is not None:
            invalidated = {
                str(record.target_artifact_id)
                for record in invalidation_engine.invalidation_log
            }
            affected = sorted({ref["artifact_id"] for ref in all_artifact_refs} & invalidated)
            if affected:
                raise ResearchB4Error("M6_DEPENDENCY_INVALIDATED:" + ",".join(affected))

        exact_m5_ref = _exact_ref(m5_manifest_ref) | {"path": str(m5_manifest_ref["path"])}
        all_artifact_refs = [exact_m5_ref] + list(canonical_by_kind.values())
        return m5_manifest, exact_m5_ref, canonical_by_kind, all_artifact_refs

    def _load_canonical_provenance_registry(self, context: Mapping[str, Any]) -> tuple[dict[str, Any], Path, str]:
        if "execution_provenance_registry" in context:
            raise ResearchB4Error("M6_EXECUTION_PROVENANCE_REGISTRY_CALLER_OVERRIDE_FORBIDDEN")
        repository_root = self._provenance_repository_root
        try:
            relative_path = canonical_registry_path(repository_root)
        except Exception as exc:
            raise ResearchB4Error("M6_EXECUTION_PROVENANCE_POLICY_UNRESOLVED") from exc
        declared_ref = str(context.get("execution_provenance_registry_ref") or "").replace("\\", "/").strip()
        if declared_ref and declared_ref != relative_path:
            raise ResearchB4Error("M6_PROVENANCE_REGISTRY_BINDING_INVALID")
        registry_path = (repository_root / relative_path).resolve()
        try:
            registry_path.relative_to(repository_root)
        except ValueError as exc:
            raise ResearchB4Error("M6_PROVENANCE_REGISTRY_BINDING_INVALID") from exc
        if not registry_path.is_file():
            raise ResearchB4Error("M6_EXECUTION_PROVENANCE_REGISTRY_REQUIRED")
        try:
            registry = load_registry(registry_path)
        except (OSError, ValueError) as exc:
            raise ResearchB4Error("M6_EXECUTION_PROVENANCE_REGISTRY_INVALID") from exc
        if validate_against_schema(registry, "execution_provenance_registry"):
            raise ResearchB4Error("M6_EXECUTION_PROVENANCE_REGISTRY_INVALID")
        return registry, registry_path, relative_path

    @staticmethod
    def _matching_run_output(run: Mapping[str, Any], ref: Mapping[str, Any]) -> bool:
        artifact_id = str(ref["artifact_id"])
        checksum = str(ref["checksum"])
        for output in run.get("outputs", []):
            if not isinstance(output, Mapping):
                continue
            if output.get("artifact_id") == artifact_id and output.get("checksum") == checksum:
                return True
        output_ids = [str(item) for item in run.get("output_artifact_ids", [])]
        output_checksums = [str(item) for item in run.get("output_checksums", [])]
        return any(
            index < len(output_checksums)
            and output_id in {artifact_id, f"{ref['artifact_kind']}:{artifact_id}"}
            and output_checksums[index] == checksum
            for index, output_id in enumerate(output_ids)
        )

    @classmethod
    def _resolve_producer_run(
        cls, registry: Mapping[str, Any], ref: Mapping[str, Any], *, label: str,
    ) -> dict[str, Any]:
        candidates = [
            run for run in registry.get("runs", [])
            if isinstance(run, Mapping)
            and run.get("status") == "SUCCEEDED"
            and cls._matching_run_output(run, ref)
        ]
        if len(candidates) != 1:
            raise ResearchB4Error(f"M6_PRODUCER_PROVENANCE_{label}_UNKNOWN")
        return copy.deepcopy(dict(candidates[0]))

    @classmethod
    def _resolve_artifact_producers(
        cls, registry: Mapping[str, Any], refs: list[Mapping[str, Any]],
    ) -> dict[tuple[str, str, str, str], dict[str, Any]]:
        resolved: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for ref in refs:
            resolved[_ref_key(ref)] = cls._resolve_producer_run(
                registry, ref, label=str(ref["artifact_kind"]),
            )
        return resolved

    @classmethod
    def _validate_provenance(
        cls,
        context: Mapping[str, Any],
        m5_manifest_ref: Mapping[str, Any],
        m5_manifest: Mapping[str, Any],
        registry: Mapping[str, Any],
        registry_ref: str,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        declared_producer = context.get("producer_provenance")
        declared_auditor = context.get("auditor_provenance")
        if not isinstance(declared_producer, Mapping):
            raise ResearchB4Error("M6_PROVENANCE_REQUIRED")
        if declared_auditor is not None and not isinstance(declared_auditor, Mapping):
            raise ResearchB4Error("M6_AUDITOR_PROVENANCE_INVALID")
        producer_run = cls._resolve_producer_run(registry, m5_manifest_ref, label="M5_MANIFEST")
        if producer_run.get("episode_id") != m5_manifest.get("episode_id"):
            raise ResearchB4Error("M6_PRODUCER_PROVENANCE_EPISODE_MISMATCH")
        if declared_producer.get("run_id") != producer_run.get("run_id"):
            raise ResearchB4Error("M6_PRODUCER_RUN_PROVENANCE_MISMATCH")
        for field, run_field in (("actor_id", "agent_id"), ("role", "role"), ("executor_id", "actual_executor")):
            if declared_producer.get(field) != producer_run.get(run_field):
                raise ResearchB4Error(f"M6_PRODUCER_{field.upper()}_PROVENANCE_MISMATCH")
        if declared_producer.get("provenance_ref") != registry_ref:
            raise ResearchB4Error("M6_PROVENANCE_REGISTRY_BINDING_INVALID")
        producer_artifact_ref = declared_producer.get("artifact_ref")
        if not isinstance(producer_artifact_ref, Mapping) or not _same_ref(producer_artifact_ref, m5_manifest_ref):
            raise ResearchB4Error("M6_PRODUCER_PROVENANCE_BINDING_INVALID")

        producer = {
            "actor_id": str(producer_run["agent_id"]),
            "run_id": str(producer_run["run_id"]),
            "role": str(producer_run["role"]),
            "executor_id": str(producer_run["actual_executor"]),
            "provenance_ref": registry_ref,
        }
        return producer, copy.deepcopy(dict(declared_auditor or {})), copy.deepcopy(dict(producer_run))

    @staticmethod
    def _validate_declared_auditor(
        declared: Mapping[str, Any], actual: Mapping[str, Any], *, producer_run: Mapping[str, Any],
    ) -> None:
        fields = ("actor_id", "run_id", "executor_id", "role", "provenance_ref")
        if any(field in declared and declared.get(field) != actual.get(field) for field in fields):
            raise ResearchB4Error("M6_AUDITOR_RUNTIME_PROVENANCE_MISMATCH")
        if producer_run.get("run_id") == actual.get("run_id"):
            raise ResearchB4Error("AUDITOR_EQUALS_PRODUCER_RUN")
        if producer_run.get("agent_id") == actual.get("actor_id"):
            raise ResearchB4Error("AUDITOR_EQUALS_PRODUCER_ACTOR")
        if producer_run.get("actual_executor") == actual.get("executor_id"):
            raise ResearchB4Error("M6_AUDITOR_EXECUTOR_NOT_INDEPENDENT")

    @classmethod
    def _m5_declared_m4_inputs(cls, m5_manifest: Mapping[str, Any]) -> list[dict[str, str]]:
        declared: dict[tuple[str, str, str, str], dict[str, str]] = {}
        events = m5_manifest.get("events")
        if not isinstance(events, list):
            raise ResearchB4Error("M6_M5_EVENTS_REQUIRED_FOR_M4_BINDING")
        for event in events:
            if not isinstance(event, Mapping):
                continue
            for raw_ref in event.get("input_artifacts", []):
                if not isinstance(raw_ref, Mapping) or raw_ref.get("artifact_kind") not in M6_REQUIRED_M4_INPUT_KINDS:
                    continue
                if raw_ref.get("artifact_kind") == "ResearchStopDecisionCollection" and ":M5:" in str(raw_ref.get("artifact_id")):
                    continue
                cls._validate_ref(raw_ref, "M6_M5_DECLARED_M4_INPUT")
                ref = _exact_ref(raw_ref) | {"path": str(raw_ref["path"])}
                declared[_ref_key(ref)] = ref
        if not any(ref["artifact_kind"] == "ResearchM4ExecutionManifest" for ref in declared.values()):
            raise ResearchB4Error("M6_M5_M4_MANIFEST_INPUT_MISSING")
        return list(declared.values())

    @staticmethod
    def _validate_m5_m4_inputs(
        declared_refs: list[Mapping[str, Any]],
        chain_refs: Mapping[Any, Mapping[str, Any]],
    ) -> None:
        received = {_ref_key(ref) for ref in chain_refs.values()}
        missing = [ref["artifact_id"] for ref in declared_refs if _ref_key(ref) not in received]
        if missing:
            raise ResearchB4Error("M6_M4_INPUT_BINDING_INVALID:" + ",".join(sorted(set(missing))))

    @staticmethod
    def _verify_manifest_membership(
        manifest: Mapping[str, Any], refs_by_binding: Mapping[Any, Mapping[str, Any]], label: str,
    ) -> None:
        for raw_ref in manifest.get("artifacts", []):
            if not isinstance(raw_ref, Mapping) or not raw_ref.get("artifact_id"):
                raise ResearchB4Error(f"M6_{label}_MANIFEST_ARTIFACT_INVALID")
            if not any(_same_ref(ref, raw_ref) for ref in refs_by_binding.values()):
                raise ResearchB4Error(f"M6_{label}_CANONICAL_BINDING_INVALID:{raw_ref['artifact_id']}")

    def _load_research_chain(
        self, research_chain: Mapping[str, Any], *, m5_manifest_ref: Mapping[str, Any],
        m5_manifest: Mapping[str, Any],
        invalidation_engine: InvalidationEngine | None,
    ) -> tuple[dict[tuple[str, str, str, str], dict[str, str]], dict[tuple[str, str, str, str], dict[str, Any]], list[dict[str, str]]]:
        if not isinstance(research_chain, Mapping):
            raise ResearchB4Error("M6_RESEARCH_CHAIN_REQUIRED")
        raw_refs = research_chain.get("artifact_refs")
        if not isinstance(raw_refs, list) or not raw_refs:
            raise ResearchB4Error("M6_RESEARCH_CHAIN_ARTIFACTS_REQUIRED")
        refs_by_binding: dict[tuple[str, str, str, str], dict[str, str]] = {}
        payloads: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for raw_ref in raw_refs:
            self._validate_ref(raw_ref, "M6_RESEARCH_CHAIN_ARTIFACT")
            ref = _exact_ref(raw_ref) | {"path": str(raw_ref["path"])}
            binding_key = _ref_key(ref)
            if binding_key in refs_by_binding:
                continue
            refs_by_binding[binding_key] = ref
            payload = ResearchB3Orchestrator._load_persisted_json(ref, f"M6_CHAIN_{ref['artifact_kind']}")
            if payload.get("artifact_validity") in {"STALE", "INVALID", "PENDING_VALIDATION"}:
                raise ResearchB4Error(f"M6_STALE_OR_INVALID_ARTIFACT:{ref['artifact_id']}")
            payloads[binding_key] = payload

        kinds = {ref["artifact_kind"] for ref in refs_by_binding.values()}
        missing_kinds = sorted(M6_REQUIRED_CHAIN_KINDS - kinds)
        if missing_kinds:
            raise ResearchB4Error("M6_RESEARCH_CHAIN_INCOMPLETE:" + ",".join(missing_kinds))
        if not any("DEEP_WORK_RESEARCH" in ref["artifact_id"] for ref in refs_by_binding.values()):
            raise ResearchB4Error("M6_DEEP_WORK_RESEARCH_REF_REQUIRED")
        if not any("DEEP_FIDELITY" in ref["artifact_id"] for ref in refs_by_binding.values()):
            raise ResearchB4Error("M6_DEEP_FIDELITY_REF_REQUIRED")

        b2_refs = [ref for ref in refs_by_binding.values() if ref["artifact_kind"] == "ResearchB2ExecutionManifest"]
        m4_refs = [ref for ref in refs_by_binding.values() if ref["artifact_kind"] == "ResearchM4ExecutionManifest"]
        if len(b2_refs) != 1 or len(m4_refs) != 1:
            raise ResearchB4Error("M6_RESEARCH_CHAIN_MANIFESTS_INVALID")
        b2_manifest = payloads[_ref_key(b2_refs[0])]
        m4_manifest = payloads[_ref_key(m4_refs[0])]
        self._verify_manifest_membership(b2_manifest, refs_by_binding, "B2")
        self._verify_manifest_membership(m4_manifest, refs_by_binding, "M4")
        if m4_manifest.get("m5_outputs_not_produced") is not True:
            raise ResearchB4Error("M6_M4_HANDOFF_INVALID")
        source_refs = [
            ref for ref in refs_by_binding.values()
            if ref["artifact_kind"] == "SourceAccessAndEvidenceReport"
        ]
        if not source_refs:
            raise ResearchB4Error("M6_SOURCE_ACCESS_REPORT_REQUIRED")
        plan_refs = [ref for ref in refs_by_binding.values() if ref["artifact_kind"] == "ResearchPlan"]
        if len(plan_refs) != 1:
            raise ResearchB4Error("M6_RESEARCH_PLAN_BINDING_INVALID")
        plan_payload = payloads[_ref_key(plan_refs[0])]
        plan_research_id = plan_payload.get("research_id") or plan_payload.get("research_plan_id")
        for source_ref in source_refs:
            source_payload = payloads[_ref_key(source_ref)]
            source_errors = validate_against_schema(source_payload, "source_access_and_evidence_report")
            if source_errors:
                raise ResearchB4Error("M6_SOURCE_ACCESS_REPORT_INVALID")
            for field in ("episode_id", "research_id", "brief_version"):
                plan_value = plan_research_id if field == "research_id" else plan_payload.get(field)
                expected = m5_manifest.get(field) or m4_manifest.get(field) or plan_value
                if expected is not None and source_payload.get(field) != expected:
                    raise ResearchB4Error(f"M6_SOURCE_ACCESS_BINDING_INVALID:{field}")
            for field in ("episode_id", "research_id"):
                plan_value = plan_research_id if field == "research_id" else plan_payload.get(field)
                if m5_manifest.get(field) != plan_value:
                    raise ResearchB4Error(f"M6_RESEARCH_PLAN_BINDING_INVALID:{field}")

        if invalidation_engine is not None:
            invalidated = {str(record.target_artifact_id) for record in invalidation_engine.invalidation_log}
            affected = sorted({ref["artifact_id"] for ref in refs_by_binding.values()} & invalidated)
            if affected:
                raise ResearchB4Error("M6_DEPENDENCY_INVALIDATED:" + ",".join(affected))
        return refs_by_binding, payloads, list(refs_by_binding.values())

    @staticmethod
    def _known_references(
        m5_manifest_ref: Mapping[str, Any],
        canonical_by_kind: Mapping[str, Mapping[str, Any]],
        payloads: Mapping[str, Mapping[str, Any]],
    ) -> set[str]:
        known = {str(m5_manifest_ref["artifact_id"])}
        known.update(str(ref["artifact_id"]) for ref in canonical_by_kind.values())
        for payload in payloads.values():
            known.update(_evidence_reference_values(payload))
        return known

    @staticmethod
    def _validate_audit_evidence(audit: Mapping[str, Any], known_refs: set[str]) -> None:
        refs = set(str(ref) for ref in audit.get("evidence_refs", []))
        for finding in audit.get("findings", []):
            refs.update(str(ref) for ref in finding.get("evidence_refs", []))
        missing = sorted(ref for ref in refs if ref not in known_refs)
        if missing:
            raise ResearchB4Error("M6_AUDIT_EVIDENCE_REF_UNRESOLVED:" + ",".join(missing))

    @staticmethod
    def _validate_audit_coverage(audit: Mapping[str, Any]) -> None:
        findings = audit.get("findings")
        if not isinstance(findings, list) or not findings:
            raise ResearchB4Error("M6_AUDIT_COVERAGE_EMPTY")
        criteria = {str(item.get("criterion")) for item in findings if isinstance(item, Mapping)}
        missing = sorted(M6_REQUIRED_AUDIT_CRITERIA - criteria)
        if missing:
            raise ResearchB4Error("M6_AUDIT_COVERAGE_INCOMPLETE:" + ",".join(missing))
        for finding in findings:
            if not isinstance(finding, Mapping) or not str(finding.get("judgment_basis") or "").strip():
                raise ResearchB4Error("M6_AUDIT_JUDGMENT_BASIS_REQUIRED")
            if finding.get("status") == "LIMITED" and not _text_list(finding.get("limitations")):
                raise ResearchB4Error(
                    "M6_AUDIT_LIMITATION_REQUIRED:" + str(finding.get("criterion") or "UNSPECIFIED")
                )

    def _build_audit(
        self,
        raw_output: Any,
        *,
        m5_manifest: Mapping[str, Any],
        m5_manifest_ref: Mapping[str, Any],
        all_artifact_refs: list[dict[str, str]],
        known_refs: set[str],
        artifact_producers: Mapping[tuple[str, str, str, str], Mapping[str, Any]],
        auditor: Mapping[str, Any],
    ) -> dict[str, Any]:
        semantic = _as_mapping(raw_output, "M6_AUDIT_OUTPUT")
        missing = [field for field in ("independence_result", "decision") if field not in semantic]
        if missing:
            raise ResearchB4Error("M6_AUDIT_SEMANTIC_FIELDS_MISSING:" + ",".join(missing))
        producer_run_ids = sorted({
            str(artifact_producers[_ref_key(ref)]["run_id"])
            for ref in all_artifact_refs
        })
        if not producer_run_ids:
            raise ResearchB4Error("M6_PRODUCER_PROVENANCE_UNKNOWN")
        producer_actor_ids = sorted({
            str(artifact_producers[_ref_key(ref)].get("agent_id") or "UNKNOWN")
            for ref in all_artifact_refs
        })
        audit = {
            "audit_id": f"{m5_manifest['research_id']}:M6:INDEPENDENT_AUDIT",
            "audit_version": CONTRACT_VERSION,
            "episode_id": str(m5_manifest["episode_id"]),
            "audit_type": "RESEARCH_PACKAGE",
            "audited_artifacts": [
                {
                    "artifact_id": ref["artifact_id"],
                    "checksum": ref["checksum"],
                    "producer_run_id": str(artifact_producers[_ref_key(ref)]["run_id"]),
                }
                for ref in all_artifact_refs
            ],
            "producer": {
                "actor_id": producer_actor_ids[0] if len(producer_actor_ids) == 1 else "MULTIPLE_PRODUCER_ACTORS",
                "run_id": producer_run_ids[0] if len(producer_run_ids) == 1 else "MULTIPLE_PRODUCER_RUNS",
            },
            "auditor": {
                "actor_id": str(auditor["actor_id"]),
                "run_id": str(auditor["run_id"]),
            },
            "auditor_write_scope": "AUDIT_ONLY",
        }
        for field in M6_AUDIT_SEMANTIC_FIELDS:
            value = semantic.get(field, [] if field in {"findings", "evidence_refs", "limitations", "defects", "correction_routes"} else None)
            if value is not None:
                audit[field] = copy.deepcopy(value)
        audit["created_at"] = utc_now()
        self._validate_audit_evidence(audit, known_refs)
        self._validate_audit_coverage(audit)
        schema_errors = validate_against_schema(audit, M6_AUDIT_SCHEMA)
        if schema_errors:
            raise ResearchB4Error("M6_INDEPENDENT_AUDIT_SCHEMA_INVALID:" + " | ".join(schema_errors))
        audit_errors = validate_independent_research_audit(audit)
        if audit_errors:
            raise ResearchB4Error("M6_INDEPENDENT_AUDIT_INVALID:" + " | ".join(audit_errors))
        return audit

    @staticmethod
    def _research_stop_status(payload: Mapping[str, Any]) -> str:
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            decisions = payload.get("dossiers")
        if not isinstance(decisions, list) or not decisions:
            raise ResearchB4Error("M6_RESEARCH_STOP_MATERIAL_DECISION_MISSING")
        statuses = {str(item.get("sufficiency_status")) for item in decisions if isinstance(item, Mapping)}
        if not statuses or any(status not in {
            "SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE",
            "MORE_RESEARCH_REQUIRED", "BLOCKED_BY_EVIDENCE",
        } for status in statuses):
            raise ResearchB4Error("M6_RESEARCH_STOP_STATUS_INVALID")
        if "BLOCKED_BY_EVIDENCE" in statuses:
            return "BLOCKED_BY_EVIDENCE"
        if "MORE_RESEARCH_REQUIRED" in statuses:
            return "MORE_RESEARCH_REQUIRED"
        if "LIMITED_BUT_USABLE" in statuses:
            return "LIMITED_BUT_USABLE"
        return "SUFFICIENT_FOR_INTENDED_USE"

    @staticmethod
    def _restriction(statement: str, index: int, *, kind: str = "CONDITION_REQUIRED") -> dict[str, Any]:
        return {
            "restriction_id": f"M6-RESTRICTION-{index}",
            "kind": kind,
            "statement": statement,
            "affected_consumers": ["B5-I3"],
        }

    def _build_manifest(
        self,
        audit: Mapping[str, Any],
        *,
        m5_manifest: Mapping[str, Any],
        m5_manifest_ref: Mapping[str, Any],
        canonical_by_kind: Mapping[str, Mapping[str, Any]],
        chain_refs: Mapping[str, Mapping[str, Any]],
        chain_payloads: Mapping[str, Mapping[str, Any]],
    ) -> tuple[dict[str, Any], list[str]]:
        claim_stop_ref = canonical_by_kind["ResearchStopDecisionCollection"]
        claim_stop = ResearchB3Orchestrator._load_persisted_json(claim_stop_ref, "M6_CLAIM_RESEARCH_STOP")
        stop_status = self._research_stop_status(claim_stop)
        material_stop_statuses: list[tuple[str, str, bool]] = [
            (claim_stop_ref["artifact_id"], stop_status, True),
        ]
        for binding_key, ref in chain_refs.items():
            if ref["artifact_kind"] != "ResearchStopDecisionCollection":
                continue
            payload = chain_payloads.get(binding_key)
            if not isinstance(payload, Mapping):
                raise ResearchB4Error("M6_RESEARCH_STOP_PAYLOAD_INVALID")
            material_stop_statuses.append((ref["artifact_id"], self._research_stop_status(payload), False))
        refined_thesis = ResearchB3Orchestrator._load_persisted_json(
            canonical_by_kind["RefinedThesis"], "M6_REFINED_THESIS"
        )
        claims_ledger = ResearchB3Orchestrator._load_persisted_json(
            canonical_by_kind["ClaimsLedger"], "M6_CLAIMS_LEDGER"
        )
        limitations: list[str] = []
        limitations.extend(str(item) for item in audit.get("limitations", []) if str(item).strip())
        for finding in audit.get("findings", []):
            if finding.get("status") == "LIMITED":
                limitations.extend(str(item) for item in finding.get("limitations", []) if str(item).strip())
        thesis_restrictions = [
            copy.deepcopy(dict(item))
            for item in refined_thesis.get("downstream_restrictions", [])
            if isinstance(item, Mapping)
        ]
        thesis_limit_restrictions = [
            self._restriction(
                f"RefinedThesis limitation: {limit}", index, kind="CONDITION_REQUIRED",
            ) | {"restriction_id": f"M6-THESIS-LIMIT-{index}"}
            for index, limit in enumerate(_text_list(refined_thesis.get("limits")), start=1)
        ]
        if stop_status == "LIMITED_BUT_USABLE":
            for decision in claim_stop.get("decisions", []):
                if isinstance(decision, Mapping):
                    limitations.extend(_text_list(decision.get("limitations")))
        for artifact_id, status, _ in material_stop_statuses:
            if status == "LIMITED_BUT_USABLE":
                limitations.append(f"ResearchStop limitado conservado: {artifact_id}.")
        # RefinedThesis always preserves residual limits and uncertainty.  They
        # become downstream restrictions only when the independent audit or a
        # material ResearchStop judges them limiting for the intended use;
        # otherwise a documented uncertainty is not a false blocker.
        limitations = list(dict.fromkeys(limitations))

        claim_restrictions: list[dict[str, Any]] = []
        for claim in claims_ledger.get("claims", []):
            if not isinstance(claim, Mapping):
                continue
            materiality = claim.get("materiality")
            if not isinstance(materiality, Mapping) or materiality.get("is_material") is not True:
                continue
            decision = str(claim.get("claim_decision") or "")
            claim_id = str(claim.get("claim_id") or "")
            if decision not in {"CLAIM_ALLOWED", "CLAIM_LIMITED", "CLAIM_BLOCKED"} or not claim_id:
                continue
            statement_parts = [f"{decision}: {claim_id}."]
            if str(claim.get("claim_text") or "").strip():
                statement_parts.append(f"Claim: {str(claim['claim_text']).strip()}")
            if str(claim.get("decision_basis") or "").strip():
                statement_parts.append(f"Base: {str(claim['decision_basis']).strip()}")
            claim_limits = _text_list(claim.get("limitations"))
            if claim_limits:
                statement_parts.append(f"Limitación: {' '.join(claim_limits)}")
                if decision == "CLAIM_LIMITED":
                    limitations.extend(claim_limits)
            if decision == "CLAIM_BLOCKED":
                limitations.append(f"Claim retirado y no permitido para uso downstream: {claim_id}.")
            if str(claim.get("return_route") or "").strip():
                statement_parts.append(f"Ruta: {str(claim['return_route']).strip()}")
            claim_restrictions.append(
                self._restriction(
                    " ".join(statement_parts), len(claim_restrictions) + 1, kind=decision,
                ) | {"restriction_id": f"M6-CLAIM-{claim_id}"}
            )

        deep_fidelity_statuses: set[str] = set()
        deep_fidelity_restrictions: list[dict[str, Any]] = []
        for payload in chain_payloads.values():
            nodes = [payload]
            if isinstance(payload.get("dossiers"), list):
                nodes.extend(item for item in payload["dossiers"] if isinstance(item, Mapping))
            for node in nodes:
                if node.get("deep_fidelity"):
                    deep_fidelity_statuses.add(str(node["deep_fidelity"]))
                if isinstance(node, Mapping):
                    for restriction in node.get("downstream_restrictions", []):
                        if isinstance(restriction, Mapping):
                            deep_fidelity_restrictions.append(copy.deepcopy(dict(restriction)))
        if not deep_fidelity_statuses:
            raise ResearchB4Error("M6_DEEP_FIDELITY_STATUS_REQUIRED")
        deep_fidelity_binding = "APROBADA"
        if "NO_APROBADA" in deep_fidelity_statuses or "MAS_INVESTIGACION_REQUERIDA" in deep_fidelity_statuses:
            deep_fidelity_binding = "NO_APROBADA" if "NO_APROBADA" in deep_fidelity_statuses else "MAS_INVESTIGACION_REQUERIDA"
        elif "APROBADA_CON_LIMITES" in deep_fidelity_statuses:
            deep_fidelity_binding = "APROBADA_CON_LIMITES"
            if not deep_fidelity_restrictions:
                raise ResearchB4Error("M6_DEEP_FIDELITY_RESTRICTIONS_MISSING")

        blockers: list[str] = []
        if audit.get("decision") != "PASS":
            blockers.append(f"INDEPENDENT_AUDIT_{audit['decision']}")
        pending_findings = [
            str(item.get("criterion"))
            for item in audit.get("findings", [])
            if item.get("status") in {"NOT_SATISFIED", "UNRESOLVED"}
        ]
        blockers.extend(f"AUDIT_FINDING_PENDING:{item}" for item in pending_findings)
        blockers.extend(f"AUDIT_DEFECT:{item['defect_id']}" for item in audit.get("defects", []))
        for artifact_id, status, claim_scoped in material_stop_statuses:
            if status == "MORE_RESEARCH_REQUIRED" or (
                not claim_scoped and status == "BLOCKED_BY_EVIDENCE"
            ):
                blockers.append(f"RESEARCH_STOP_{status}:{artifact_id}")
        if deep_fidelity_binding in {"NO_APROBADA", "MAS_INVESTIGACION_REQUERIDA"}:
            blockers.append(f"DEEP_FIDELITY_{deep_fidelity_binding}")
        if blockers:
            state = "NOT_RESEARCH_READY"
            sufficiency = "BLOCKED_BY_EVIDENCE" if stop_status == "BLOCKED_BY_EVIDENCE" or audit.get("decision") != "PASS" else "MORE_RESEARCH_REQUIRED"
        elif any(status == "LIMITED_BUT_USABLE" for _, status, _ in material_stop_statuses) or limitations or thesis_restrictions or deep_fidelity_binding == "APROBADA_CON_LIMITES":
            state = "RESEARCH_READY_WITH_LIMITATIONS"
            sufficiency = "LIMITED_BUT_USABLE"
            if not limitations:
                limitations.append("La investigación es utilizable, pero conserva límites explícitos.")
        else:
            state = "RESEARCH_READY"
            sufficiency = "SUFFICIENT_FOR_INTENDED_USE"

        restrictions = [self._restriction(statement, index) for index, statement in enumerate(limitations, start=1)]
        for restriction in claim_restrictions + thesis_restrictions + thesis_limit_restrictions:
            if restriction.get("restriction_id") not in {item.get("restriction_id") for item in restrictions}:
                restrictions.append(restriction)
        for restriction in deep_fidelity_restrictions:
            if restriction.get("restriction_id") not in {item.get("restriction_id") for item in restrictions}:
                restrictions.append(restriction)
        if blockers:
            restrictions.extend(self._restriction(statement, len(restrictions) + 1, kind="NOT_AUTHORIZED") for statement in blockers)
        artifacts: list[dict[str, str]] = []
        artifact_bindings: set[tuple[str, str, str, str]] = set()

        def add_artifact(ref: Mapping[str, Any]) -> None:
            exact = _exact_ref(ref)
            binding_key = _ref_key(exact)
            if binding_key not in artifact_bindings:
                artifact_bindings.add(binding_key)
                artifacts.append(exact)

        add_artifact(m5_manifest_ref)
        for ref in chain_refs.values():
            add_artifact(ref)
        for ref in canonical_by_kind.values():
            add_artifact(ref)
        audit_ref = {
            "artifact_id": audit["audit_id"],
            "artifact_kind": "IndependentResearchAudit",
            "artifact_version": audit["audit_version"],
            "checksum": _checksum(audit),
        }
        add_artifact(audit_ref)
        source_refs = list(dict.fromkeys(item["artifact_id"] for item in artifacts))
        manifest = {
            "contract": "research_ready_manifest",
            "contract_version": M6_MANIFEST_VERSION,
            "manifest_id": f"{m5_manifest['research_id']}:RESEARCH_READY_MANIFEST",
            "episode_id": str(m5_manifest["episode_id"]),
            "research_id": str(m5_manifest["research_id"]),
            "research_version": M6_MANIFEST_VERSION,
            "research_ready_state": state,
            "state_bindings": {
                "research_stage": "READY" if state != "NOT_RESEARCH_READY" else "REFINED",
                "research_sufficiency": sufficiency,
                "artifact_validity": "VALID",
                "selection_state": "SELECTED",
                "deep_fidelity": deep_fidelity_binding,
            },
            "research_artifacts": artifacts,
            "downstream_restrictions": restrictions,
            "lineage": {
                "source_refs": source_refs,
                "producer_contract": "RESEARCH_B4",
                "producer_version": M6_MANIFEST_VERSION,
            },
            "created_at": utc_now(),
        }
        errors = validate_research_ready_manifest(manifest)
        if errors:
            raise ResearchB4Error("M6_RESEARCH_READY_MANIFEST_INVALID:" + " | ".join(errors))
        return manifest, blockers

    @staticmethod
    def _persist_auditor_execution_result(
        registry_path: Path, result: ExecutionResult, request: ExecutionRequest,
    ) -> None:
        persist_execution_result(registry_path, result, request, execution_mode="SYNTHETIC")

    @classmethod
    def _validate_auditor_output(
        cls, registry_path: Path, *, audit: Mapping[str, Any], audit_ref: Mapping[str, Any], auditor: Mapping[str, Any], episode_id: str,
    ) -> None:
        try:
            registry = load_registry(registry_path)
        except (OSError, ValueError) as exc:
            raise ResearchB4Error("M6_EXECUTION_PROVENANCE_REGISTRY_INVALID") from exc
        run = next(
            (item for item in registry.get("runs", []) if isinstance(item, Mapping) and item.get("run_id") == auditor.get("run_id")),
            None,
        )
        if run is None or run.get("status") != "SUCCEEDED":
            raise ResearchB4Error("M6_AUDITOR_RUN_NOT_REGISTERED")
        if run.get("episode_id") != episode_id:
            raise ResearchB4Error("M6_AUDITOR_PROVENANCE_EPISODE_MISMATCH")
        if run.get("role") != M6_AUDITOR_ROLE or run.get("role_id") != M6_AUDITOR_ROLE:
            raise ResearchB4Error("M6_AUDITOR_RUNTIME_ROLE_MISMATCH")
        if run.get("agent_id") != auditor.get("actor_id"):
            raise ResearchB4Error("M6_AUDITOR_RUNTIME_ACTOR_MISMATCH")
        if run.get("actual_executor") != auditor.get("executor_id"):
            raise ResearchB4Error("M6_AUDITOR_RUNTIME_EXECUTOR_MISMATCH")
        if not cls._matching_run_output(run, audit_ref):
            raise ResearchB4Error("M6_AUDITOR_OUTPUT_BINDING_INVALID")
        expected_ref = f"independent_research_audit:{audit['audit_id']}"
        if expected_ref not in {str(item) for item in run.get("output_artifact_ids", [])}:
            raise ResearchB4Error("M6_AUDITOR_OUTPUT_REFERENCE_INVALID")
        if str(audit_ref["checksum"]) not in {str(item) for item in run.get("output_checksums", [])}:
            raise ResearchB4Error("M6_AUDITOR_OUTPUT_CHECKSUM_INVALID")

    def run_m6(
        self,
        m5_result: Mapping[str, Any],
        *,
        context: Mapping[str, Any],
        research_chain: Mapping[str, Any] | None = None,
        invalidation_engine: InvalidationEngine | None = None,
    ) -> dict[str, Any]:
        """Audit M5 and emit the canonical ResearchReady manifest and gate."""
        result = _as_mapping(m5_result, "M5_RESULT")
        ctx = self._validate_context(context)
        m5_manifest, m5_manifest_ref, canonical_by_kind, all_artifact_refs = self._load_m5_package(
            result, invalidation_engine=invalidation_engine,
        )
        registry, registry_path, registry_ref = self._load_canonical_provenance_registry(ctx)
        producer, declared_auditor, producer_run = self._validate_provenance(
            ctx, m5_manifest_ref, m5_manifest, registry, registry_ref,
        )
        declared_m4_inputs = self._m5_declared_m4_inputs(m5_manifest)
        chain_refs, chain_payloads, chain_artifacts = self._load_research_chain(
            research_chain or {},
            m5_manifest_ref=m5_manifest_ref,
            m5_manifest=m5_manifest,
            invalidation_engine=invalidation_engine,
        )
        self._validate_m5_m4_inputs(declared_m4_inputs, chain_refs)
        m5_payloads = {
            ref["artifact_id"]: ResearchB3Orchestrator._load_persisted_json(ref, f"M6_{kind}")
            for kind, ref in canonical_by_kind.items()
        }
        payloads = {**chain_payloads, **m5_payloads}
        known_refs = self._known_references(m5_manifest_ref, canonical_by_kind, payloads)
        known_refs.update(str(ref["artifact_id"]) for ref in chain_refs.values())
        input_artifacts: list[dict[str, str]] = []
        seen_bindings: set[tuple[str, str, str, str]] = set()
        for ref in [*chain_artifacts, *all_artifact_refs]:
            binding_key = _ref_key(ref)
            if binding_key not in seen_bindings:
                seen_bindings.add(binding_key)
                input_artifacts.append(dict(ref))
        all_artifact_refs = input_artifacts
        artifact_producers = self._resolve_artifact_producers(registry, all_artifact_refs)
        prepared_payload = {
            "topic": ctx["topic"],
            "source_access": ctx["source_access"],
            "brief": ctx["brief"],
            "channel_context": ctx["channel_context"],
            "stage": M6_AUDIT_STAGE,
            "input_artifacts": copy.deepcopy(input_artifacts),
            "m5_execution_manifest": copy.deepcopy(m5_manifest),
            "research_chain": {
                "|".join(binding_key): copy.deepcopy(payload)
                for binding_key, payload in payloads.items()
            },
            "audit_scope": {
                "research_id": m5_manifest["research_id"],
                "episode_id": m5_manifest["episode_id"],
                "known_evidence_refs": sorted(known_refs),
                "required_criteria": sorted(M6_REQUIRED_AUDIT_CRITERIA),
                "producer_provenance": copy.deepcopy(producer),
                "auditor_provenance": copy.deepcopy(declared_auditor),
            },
        }
        prepared = resolve_role_execution_contract(
            M6_AUDITOR_ROLE,
            M6_AUDIT_SCHEMA,
            prepared_payload,
            {
                "stage": M6_AUDIT_STAGE,
                "responsibility": "INDEPENDENT_RESEARCH_AUDIT",
                "auditor_provenance": copy.deepcopy(declared_auditor),
                "real_ai_execution": False,
                "real_research": False,
                "product_use": False,
            },
        )
        request = B2CognitiveRequest(M6_AUDIT_STAGE, M6_AUDIT_SCHEMA, tuple(input_artifacts), prepared)
        execution_input_artifacts = [
            InputArtifact(
                artifact_kind=str(ref["artifact_kind"]),
                artifact_id=str(ref["artifact_id"]),
                path=Path(str(ref["path"])),
                producer_run_id=str(artifact_producers[_ref_key(ref)]["run_id"]),
            )
            for ref in all_artifact_refs
        ]
        audit_id = f"{m5_manifest['research_id']}:M6:INDEPENDENT_AUDIT"

        def invoke_cognition(_runtime_request: ExecutionRequest) -> Any:
            return self.cognitive_executor(request)

        def bind_audit(raw_output: Any, runtime: Mapping[str, Any]) -> dict[str, Any]:
            runtime_auditor = {
                "actor_id": str(runtime["actor_id"]),
                "run_id": str(runtime["run_id"]),
                "executor_id": str(runtime["actual_executor"]),
                "role": str(runtime["role"]),
                "provenance_ref": registry_ref,
            }
            return self._build_audit(
                raw_output,
                m5_manifest=m5_manifest,
                m5_manifest_ref=m5_manifest_ref,
                all_artifact_refs=all_artifact_refs,
                known_refs=known_refs,
                artifact_producers=artifact_producers,
                auditor=runtime_auditor,
            )

        execution_request = ExecutionRequest(
            capability_id="PLAN012_M6_INDEPENDENT_RESEARCH_AUDIT",
            skill_id="plan012_m6_independent_research_audit",
            skill_version=M6_MANIFEST_VERSION,
            input_artifacts=execution_input_artifacts,
            output_schema=M6_AUDIT_SCHEMA,
            execution_mode="SYNTHETIC_TEST",
            provider="mock",
            model="structural-test-double",
            output_artifact_kind="independent_research_audit",
            output_artifact_id=audit_id,
            output_artifact_ref=f"independent_research_audit:{audit_id}",
            episode_id=str(m5_manifest["episode_id"]),
            role=M6_AUDITOR_ROLE,
            config={
                "_synthetic_cognitive_executor": invoke_cognition,
                "_synthetic_output_binder": bind_audit,
            },
        )
        execution_result = execute(execution_request)
        if execution_result.status is not ExecutionStatus.SUCCEEDED:
            raise ResearchB4Error(
                "M6_AUDITOR_EXECUTION_FAILED:"
                + str(execution_result.error or execution_result.status.value)
            )
        if not isinstance(execution_result.output, Mapping):
            raise ResearchB4Error("M6_AUDITOR_EXECUTION_OUTPUT_INVALID")
        audit = copy.deepcopy(dict(execution_result.output))
        auditor = {
            "actor_id": str(execution_request.role),
            "run_id": str(execution_result.run_id),
            "executor_id": str(execution_result.usage.get("actual_executor") or ""),
            "role": str(execution_request.role),
            "provenance_ref": registry_ref,
        }
        self._validate_declared_auditor(declared_auditor, auditor, producer_run=producer_run)
        if execution_result.output_checksum != _checksum(audit):
            raise ResearchB4Error("M6_AUDITOR_EXECUTION_OUTPUT_CHECKSUM_INVALID")
        audit_ref = self.persistence.persist(
            "M6_INDEPENDENT_RESEARCH_AUDIT",
            audit,
            artifact_id=audit["audit_id"],
            artifact_kind="IndependentResearchAudit",
        )
        self._persist_auditor_execution_result(registry_path, execution_result, execution_request)
        self._validate_auditor_output(
            registry_path,
            audit=audit,
            audit_ref=audit_ref,
            auditor=auditor,
            episode_id=str(m5_manifest["episode_id"]),
        )
        manifest, blockers = self._build_manifest(
            audit,
            m5_manifest=m5_manifest,
            m5_manifest_ref=m5_manifest_ref,
            canonical_by_kind=canonical_by_kind,
            chain_refs=chain_refs,
            chain_payloads=chain_payloads,
        )
        manifest["research_artifacts"][-1] = {
            "artifact_id": audit_ref["artifact_id"],
            "artifact_kind": audit_ref["artifact_kind"],
            "artifact_version": audit_ref["artifact_version"],
            "checksum": audit_ref["checksum"],
        }
        manifest_errors = validate_research_ready_manifest(manifest)
        if manifest_errors:
            raise ResearchB4Error("M6_RESEARCH_READY_MANIFEST_INVALID:" + " | ".join(manifest_errors))
        manifest_ref = self.persistence.persist(
            "M6_RESEARCH_READY_MANIFEST",
            manifest,
            artifact_id=manifest["manifest_id"],
            artifact_kind="ResearchReadyManifest",
        )
        if manifest_ref["checksum"] != _checksum(manifest):
            raise ResearchB4Error("M6_RESEARCH_READY_MANIFEST_CHECKSUM_INVALID")

        state = manifest["research_ready_state"]
        status = {
            "RESEARCH_READY": GateStatus.PASS,
            "RESEARCH_READY_WITH_LIMITATIONS": GateStatus.WARN,
            "NOT_RESEARCH_READY": GateStatus.BLOCKED,
        }[state]
        gate = GateResult(
            gate_id="research_ready_gate",
            artifact_id=manifest_ref["artifact_id"],
            artifact_version=manifest_ref["artifact_version"],
            status=status,
            summary=f"M6 ResearchReady state: {state}",
            violations=list(blockers),
            warnings=list(manifest.get("downstream_restrictions", [])) if status == GateStatus.WARN else [],
            evidence={
                "research_ready_manifest": _exact_ref(manifest_ref),
                "independent_research_audit": _exact_ref(audit_ref),
                "m5_execution_manifest": _exact_ref(m5_manifest_ref),
                "research_ready_state": state,
            },
            checker_version=M6_MANIFEST_VERSION,
        )
        # GateResult warnings are strings; retain the structured restrictions
        # in the manifest and expose concise warning IDs in the gate.
        gate.warnings = [item["restriction_id"] for item in manifest.get("downstream_restrictions", [])] if status == GateStatus.WARN else []
        validate_gate_result(gate)
        gate_ref = self.persistence.persist(
            "M6_RESEARCH_READY_GATE",
            gate.to_dict(),
            artifact_id=f"{m5_manifest['research_id']}:M6:RESEARCH_READY_GATE",
            artifact_kind="GateResult",
        )
        return {
            "status": state,
            "independent_research_audit": audit_ref,
            "research_ready_manifest": manifest_ref,
            "research_ready_gate": gate_ref,
            "m5_execution_manifest": m5_manifest_ref,
            "events": [
                {"stage": M6_AUDIT_STAGE, "boundary": "IA_COGNITIVE_STEP"},
                {"stage": "M6_INDEPENDENT_RESEARCH_AUDIT", "boundary": "SOFTWARE_PERSIST"},
                {"stage": "M6_RESEARCH_READY_MANIFEST", "boundary": "SOFTWARE_PERSIST"},
                {"stage": "M6_RESEARCH_READY_GATE", "boundary": "SOFTWARE_PERSIST", "status": status.value},
            ],
        }
