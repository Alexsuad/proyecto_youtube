"""Ejecución común: routing, comprobación de schema y metadatos reproducibles."""
from __future__ import annotations

import hashlib
import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.ai.manifest import canonical_json, file_checksum, manifest_checksum as canonical_manifest_checksum
from src.ai.providers import AgentExecutorProvider, AgentHandoffProvider, DeepSeekProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider
from src.ai.router import KNOWN_PROVIDERS, resolve_provider
from src.ai.runtime_profiles import AgentRuntimePort, READY, _VERIFIED_ROUTE_TOKEN
from src.core.contract_validation import load_schema, validate_against_schema
from src.core.execution_preflight import preflight_controlled_execution
from src.core.replay_protection import mark_mission_reservation

REAL_EXTERNAL_PROVIDERS = {"ollama", "deepseek", "openai_compatible"}
TECHNICAL_HARNESS_PROVIDERS = {"mock", "agent_handoff", "agent_executor"}

B5_I2_ROLE_ARTIFACT_COMPATIBILITY = {
    "ANALYSIS_PRODUCER": {"analysis"},
    "CURATION_PRODUCER": {"curation"},
    "THESIS_PRODUCER": {"refined_thesis"},
    "SCRIPT_PROMISE_PRODUCER": {"script_promise"},
    "INDEPENDENT_EDITORIAL_AUDITOR": {"semantic_audit"},
    "SCRIPT_PRODUCT_PRODUCER": {
        "analysis", "curation", "refined_thesis", "script_promise",
        "claims_ledger", "work_lifecycle", "work_research_dossier",
    },
}
EDITORIAL_RUNTIME_FIELDS = {
    "analysis_id",
    "analysis_ids",
    "artifact_id",
    "artifact_checksum",
    "active_profile_reference",
    "episode_id",
    "evidence_report_id",
    "input_references",
    "material_checksum",
    "package_id",
    "producer_run_id",
    "provisional_thesis_id",
    "promise_id",
    "refined_thesis_checksum",
    "refined_thesis_id",
    "research_id",
    "review_id",
    "semantic_audit_id",
    "thesis_id",
    "brief_version",
    "artifact_version",
    "version",
    "checksum",
    "brief_checksum",
    "packaging_id",
    "profile_id",
    "profile_version",
    "profile_checksum",
    "run_id",
    "independence_check",
    "auditor_role",
    "auditor_run_id",
    "auditor_skill_id",
    "auditor_skill_version",
    "provider_or_adapter",
    "model_or_evaluator",
    "execution_timestamp",
    "input_manifest_checksum",
    "artifact_checksums",
    "created_at",
    "audit_method",
    "readiness",
    "artifact_references",
    "producer_run_reference",
    "auditor_run_reference",
    "producer_actor_id",
    "auditor_actor_id",
    "auditor_input_checksum",
    "auditor_write_scope",
    "independence_result",
    "viewer_journey_id",
    "opening_design_id",
    "closing_design_id",
    "script_plan_id",
    "schema_version",
    "lineage",
    "input_checksums",
    "target_duration",
    "duration_target_minutes",
    "target_language",
    "user_instructions",
    "original_user_text",
    "source_ids",
    "claims_ids",
    "estimated_words",
    "estimated_time",
    "wpm_target",
    "word_budget_total",
}
# These fields are semantic findings, not runtime metadata.  They must remain
# in the cognitive projection and are later carried into the software-owned
# final audit envelope.
EDITORIAL_RUNTIME_NORMALIZED_FIELDS: set[str] = set()
EDITORIAL_ONLY_SCHEMAS = {
    "narrative_human_analysis",
    "material_curation",
    "refined_thesis",
    "editorial_script_promise",
    "b5_i2_semantic_sufficiency_audit",
    "early_packaging_hypothesis",
    "youtube_adaptation_b5_i2_package",
    "youtube_adaptation_review",
    "viewer_journey",
    "opening_design",
    "closing_design",
    "narrative_plan",
}
M3_NARRATIVE_SCHEMAS = {"viewer_journey", "opening_design", "closing_design", "narrative_plan"}
M3_REQUIRED_INPUT_KINDS = {
    "human_input",
    "active_editorial_profile_reference",
    "episode_brief",
    "research_pack",
    "claims_ledger",
    "source_access_and_evidence_report",
    "narrative_human_analysis",
    "material_curation",
    "refined_thesis",
    "editorial_script_promise",
    "early_packaging_hypothesis",
    "b5_i2_semantic_audit",
    "youtube_adaptation_review",
}
M3_INPUT_SCHEMA_BY_KIND = {
    "human_input": "human_episode_input",
    "active_editorial_profile_reference": "active_editorial_profile",
    "episode_brief": "episode_brief",
    "research_pack": "research_pack",
    "claims_ledger": "claims_ledger",
    "source_access_and_evidence_report": "source_access_and_evidence_report",
    "narrative_human_analysis": "narrative_human_analysis",
    "material_curation": "material_curation",
    "refined_thesis": "refined_thesis",
    "editorial_script_promise": "editorial_script_promise",
    "early_packaging_hypothesis": "early_packaging_hypothesis",
    "b5_i2_semantic_audit": "b5_i2_semantic_sufficiency_audit",
    "youtube_adaptation_review": "youtube_adaptation_review",
}
M3_CANONICAL_ID_FIELDS = {
    "human_input": "interaction_id",
    "research_pack": "research_id",
    "claims_ledger": "ledger_id",
    "source_access_and_evidence_report": "report_id",
    "narrative_human_analysis": "analysis_id",
    "material_curation": "curation_id",
    "refined_thesis": "thesis_id",
    "editorial_script_promise": "promise_id",
    "early_packaging_hypothesis": "packaging_id",
    "b5_i2_semantic_audit": "audit_id",
    "youtube_adaptation_review": "review_id",
}


def _classify_provider_kind(provider: str, request: ExecutionRequest, usage: dict[str, Any]) -> str:
    explicit = str(usage.get("provider_kind") or "").strip().upper()
    if explicit in {"REAL", "SYNTHETIC"}:
        return explicit
    if usage.get("synthetic"):
        return "SYNTHETIC"
    if provider in TECHNICAL_HARNESS_PROVIDERS or (request.execution_mode or "").lower() == "mock":
        return "SYNTHETIC"
    return "REAL"


def _duration_package_input(request: ExecutionRequest) -> Path | None:
    """Return the sole B5-I2 package consumed by a duration-review run."""
    if request.role != "YOUTUBE_ADAPTATION_AUDITOR" or request.output_artifact_kind != "youtube_adaptation_review":
        return None
    packages = [
        item.path
        for item in request.input_artifacts
        if item.artifact_kind == "youtube_adaptation_b5_i2_package"
    ]
    if len(packages) != 1:
        raise ValueError(
            "YOUTUBE_ADAPTATION_AUDITOR requiere exactamente un package B5-I2 trazable para persistir una review."
        )
    return Path(packages[0])


def _restore_registry(path: Path, prior: bytes | None) -> None:
    if prior is None:
        if path.exists():
            path.unlink()
        return
    path.write_bytes(prior)


def persist_execution_result(
    path: Path,
    result: ExecutionResult,
    request: ExecutionRequest,
    *,
    execution_mode: str,
    _allow_duration_registry_override: bool = False,
) -> None:
    from src.ai.registry import append_result
    from src.core.duration_envelope import canonical_active_profile_path, canonical_duration_registry_path, register_approved_duration_envelope
    from src.core.status import GateStatus
    from src.scripts.youtube_adaptation_b5_i2_gate import evaluate as evaluate_youtube_adaptation

    if str(execution_mode).upper() == "REAL" and request.config.get("_mission_authorization_token") is None:
        raise PermissionError("REAL_PROVENANCE_REQUIRES_VERIFIED_MISSION_AUTHORIZATION")
    package_path = _duration_package_input(request)
    registry_path = Path(path).resolve()
    configured_profile = request.config.get("active_editorial_profile_path")
    if configured_profile is not None and Path(str(configured_profile)).resolve() != canonical_active_profile_path():
        raise ValueError("request.config no puede sustituir el perfil editorial activo canónico.")
    if package_path is not None and registry_path != canonical_duration_registry_path() and not _allow_duration_registry_override:
        raise ValueError("La aprobación de duración solo puede materializarse en el registry canónico.")
    prior = registry_path.read_bytes() if registry_path.exists() else None
    append_result(path, result, execution_mode=execution_mode, role=request.role or "UNSPECIFIED_PRODUCER", request=request)
    if package_path is None:
        return
    gate = evaluate_youtube_adaptation(
        package_path,
        result.output_artifact_path,
        registry_path,
        (Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json"),
        request.episode_id,
    )
    if gate.status is not GateStatus.PASS:
        return
    try:
        register_approved_duration_envelope(
            package_path,
            result.output_artifact_path,
            registry_path,
        )
    except Exception:
        _restore_registry(registry_path, prior)
        raise


def persist_execution_attempt(path: Path, result: ExecutionResult, request: ExecutionRequest, *, execution_mode: str) -> None:
    from src.ai.registry import append_attempt

    append_attempt(path, result, execution_mode=execution_mode, role=request.role or "UNSPECIFIED_PRODUCER", request=request)


def manifest_checksum(request: ExecutionRequest) -> str:
    return canonical_manifest_checksum(
        request.episode_id,
        [
            {
                "artifact_kind": item.artifact_kind,
                "artifact_id": item.artifact_id,
                "artifact_checksum": file_checksum(item.path),
            }
            for item in request.input_artifacts
        ],
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _availability_metadata(error: str) -> dict[str, str]:
    token = str(error or "").strip()
    category = token.split(":", 1)[0]
    if category in {
        "CREDENTIALS_MISSING",
        "MODEL_UNAVAILABLE",
        "PROVIDER_UNAVAILABLE",
        "TIMEOUT",
        "INVALID_RESPONSE",
        "MODEL_INVOCATION_FAILED",
        "EMPTY_RESPONSE",
        "INVALID_JSON",
        "OUTPUT_CONTRACT_INVALID",
        "EXECUTOR_UNAVAILABLE",
        "ACTUAL_PROVIDER_AND_MODEL_REQUIRED",
        "BLOCKED_PENDING_OWNER_COST_AUTHORIZATION",
        "AGENT_HARNESS_SMOKE_ONLY_UNTIL_R6_B_RETRY",
    }:
        return {
            "availability_status": category,
            "error_category": category,
            "error_type": category,
        }
    return {"error_type": category} if category else {}


def _result(
    request: ExecutionRequest,
    provider: str,
    status: ExecutionStatus,
    started: str,
    manifest: str,
    *,
    output: dict[str, Any] | None = None,
    error: str | None = None,
    usage: dict[str, Any] | None = None,
    real: bool = False,
    run_id: str | None = None,
) -> ExecutionResult:
    usage = {**_availability_metadata(error or ""), **(usage or {})}
    model = str(usage.get("model_or_evaluator") or request.model or "unconfigured")
    actual_executor = str(
        usage.get("actual_executor")
        or request.config.get("resolved_actual_executor")
        or request.executor
        or ("NONE" if provider == "agent_handoff" else "native_provider")
    )
    actual_provider = str(usage.get("actual_provider") or request.config.get("resolved_actual_provider") or provider)
    actual_model = str(usage.get("actual_model") or request.config.get("resolved_actual_model") or (model if provider != "agent_handoff" else "NONE"))
    execution_route = str(usage.get("execution_route") or request.execution_route or f"native:{provider}")
    execution_profile = str(usage.get("execution_profile") or request.execution_profile or request.config.get("execution_profile") or "UNSPECIFIED_PROFILE")
    usage = {
        **usage,
        **({"reasoning_effort": request.reasoning_effort} if request.reasoning_effort else {}),
        "provider_kind": _classify_provider_kind(provider, request, usage),
        "actual_executor": actual_executor,
        "actual_provider": actual_provider,
        "actual_model": actual_model,
        "execution_route": execution_route,
        "execution_profile": execution_profile,
        "execution_family": str(
            usage.get("execution_family")
            or request.execution_family
            or request.config.get("execution_family")
            or "UNSPECIFIED_FAMILY"
        ),
        "error_type": str(usage.get("error_type") or usage.get("availability_status") or "NONE"),
    }
    if request.output_artifact_path and request.output_artifact_path.exists():
        output_checksum = file_checksum(request.output_artifact_path)
    else:
        output_checksum = hashlib.sha256(canonical_json(output)).hexdigest() if output is not None else None
    effective_provider = str(usage.get("provider_or_adapter") or actual_provider)
    return ExecutionResult(
        run_id or f"RUN-AI-{uuid.uuid4().hex}",
        status,
        "provider",
        effective_provider,
        model,
        manifest,
        output,
        output_checksum,
        started,
        _now(),
        error,
        {"skill_id": request.skill_id, "skill_version": request.skill_version, **usage},
        request.episode_id,
        request.output_artifact_id,
        request.output_artifact_kind,
        request.output_artifact_path,
        request.output_artifact_ref,
        real,
    )


def _bind_runtime_fields(request: ExecutionRequest, output: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Bind cognitive provenance fields to the authoritative runtime ID.

    Synthetic providers may omit IDs, but declared values remain reviewable by
    the application boundary. REAL provider output is bound to the runtime ID
    so the provider cannot choose or forge execution lineage.
    """
    if request.execution_mode == "SYNTHETIC_TEST" and request.mock_output is None:
        return output, None
    if request.execution_mode not in {"SYNTHETIC_TEST", "REAL"}:
        return output, None
    run_key = {
        "topic_belonging_assessment": "producer_run_id",
        "topic_belonging_decision": "reviewer_run_id",
    }.get(request.output_schema)
    if request.output_schema not in EDITORIAL_ONLY_SCHEMAS and run_key is None:
        return output, None
    runtime_run_id = f"RUN-AI-{uuid.uuid4().hex}"
    if request.output_schema in M3_NARRATIVE_SCHEMAS:
        return _bind_m3_runtime_fields(request, output, runtime_run_id), runtime_run_id
    if request.output_schema in EDITORIAL_ONLY_SCHEMAS:
        return _bind_b5_i2_runtime_fields(request, output, runtime_run_id), runtime_run_id
    bound = copy.deepcopy(output)
    provenance = bound.get("provenance")
    if not isinstance(provenance, dict):
        return bound, runtime_run_id
    if request.execution_mode == "REAL":
        bound[run_key] = runtime_run_id
        provenance["run_id"] = runtime_run_id
    else:
        if not bound.get(run_key):
            bound[run_key] = runtime_run_id
        if not provenance.get("run_id"):
            provenance["run_id"] = runtime_run_id
    return bound, runtime_run_id


def _input_documents(request: ExecutionRequest) -> dict[str, tuple[dict[str, Any], Path, str]]:
    documents: dict[str, tuple[dict[str, Any], Path, str]] = {}
    for item in request.input_artifacts:
        try:
            payload = json.loads(item.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        if isinstance(payload, dict):
            documents[item.artifact_kind] = (payload, item.path, item.producer_run_id)
    return documents


def _active_profile_reference() -> dict[str, str]:
    from src.core.editorial_profile_registry import load_active_profile_authority

    active = load_active_profile_authority()
    return {
        "profile_id": active["ACTIVE_PROFILE_ID"],
        "profile_version": active["ACTIVE_PROFILE_VERSION"],
        "profile_checksum": active["profile_checksum"],
    }


def _bind_b5_i2_runtime_fields(
    request: ExecutionRequest,
    output: dict[str, Any],
    runtime_run_id: str,
) -> dict[str, Any]:
    """Assemble deterministic B5-I2 fields after the cognitive projection.

    The provider sees only the projected editorial schema.  IDs, references,
    checksums, profile bindings, run bindings and timestamps are reconstructed
    from the request and canonical input files by Software.
    """
    bound = copy.deepcopy(output)
    documents = _input_documents(request)
    schema = request.output_schema
    id_key = {
        "narrative_human_analysis": "analysis_id",
        "material_curation": "curation_id",
        "refined_thesis": "thesis_id",
        "editorial_script_promise": "promise_id",
        "b5_i2_semantic_sufficiency_audit": "audit_id",
        "early_packaging_hypothesis": "packaging_id",
        "youtube_adaptation_b5_i2_package": "package_id",
        "youtube_adaptation_review": "review_id",
    }.get(schema)
    if id_key:
        bound[id_key] = request.output_artifact_id or f"{schema.upper()}-{runtime_run_id}"
    if request.episode_id:
        bound["episode_id"] = request.episode_id
    else:
        for payload, _, _ in documents.values():
            if isinstance(payload.get("episode_id"), str) and payload["episode_id"]:
                bound["episode_id"] = payload["episode_id"]
                break
    bound["created_at"] = _now()

    if schema == "narrative_human_analysis":
        for output_key, input_kind, input_key in (
            ("research_id", "research", "research_id"),
            ("evidence_report_id", "evidence_report", "report_id"),
            ("semantic_audit_id", "semantic_sufficiency_audit", "audit_id"),
        ):
            payload = documents.get(input_kind, ({}, None, ""))[0]
            if payload.get(input_key):
                bound[output_key] = payload[input_key]
        if bound.get("material_id"):
            research = documents.get("research", ({}, None, ""))[0]
            for category in ("facts", "interpretations", "hypotheses", "contradictions", "alternative_views", "narrative_evidence", "external_reality_evidence", "claims_candidates"):
                match = next((item for item in research.get(category, []) if isinstance(item, dict) and item.get("material_id") == bound["material_id"]), None)
                if match is not None:
                    bound["material_checksum"] = hashlib.sha256(canonical_json(match)).hexdigest()
                    break
    elif schema == "material_curation":
        research = documents.get("research", ({}, None, ""))[0]
        analyses = []
        for item in request.input_artifacts:
            if item.artifact_kind != "analysis":
                continue
            try:
                payload = json.loads(item.path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, ValueError):
                continue
            if isinstance(payload, dict):
                analyses.append(payload)
        if research.get("research_id"):
            bound["research_id"] = research["research_id"]
        bound["analysis_ids"] = [payload["analysis_id"] for payload in analyses if payload.get("analysis_id")]
    elif schema == "refined_thesis":
        brief = documents.get("episode_brief", ({}, None, ""))[0]
        research = documents.get("research", ({}, None, ""))[0]
        evidence = documents.get("evidence_report", ({}, None, ""))[0]
        provisional = documents.get("provisional_thesis", ({}, None, ""))[0]
        audit = documents.get("semantic_sufficiency_audit", ({}, None, ""))[0]
        curation = documents.get("curation", ({}, None, ""))[0]
        bound.update({
            "brief_version": brief.get("brief_version", ""),
            "research_id": research.get("research_id", ""),
            "evidence_report_id": evidence.get("report_id", ""),
            "provisional_thesis_id": provisional.get("thesis_id", ""),
            "semantic_audit_id": audit.get("audit_id", ""),
            "curation_id": curation.get("curation_id", ""),
            "analysis_ids": [item.artifact_id for item in request.input_artifacts if item.artifact_kind == "analysis" and item.artifact_id],
        })
    elif schema == "editorial_script_promise":
        thesis = documents.get("refined_thesis", ({}, None, ""))[0]
        thesis_document = documents.get("refined_thesis")
        bound["refined_thesis_id"] = thesis.get("thesis_id", "")
        if thesis_document is not None:
            bound["refined_thesis_checksum"] = file_checksum(thesis_document[1])
    elif schema == "early_packaging_hypothesis":
        thesis_document = documents.get("refined_thesis")
        brief_document = documents.get("episode_brief")
        thesis = thesis_document[0] if thesis_document is not None else {}
        bound["refined_thesis_id"] = thesis.get("thesis_id", "")
        if thesis_document is not None:
            bound["refined_thesis_checksum"] = file_checksum(thesis_document[1])
        bound["status"] = "PROVISIONAL_YOUTUBE_ADAPTATION_INPUT"
        audience = bound.get("audience")
        if isinstance(audience, dict):
            audience.update(_active_profile_reference())
            if brief_document is not None:
                audience["brief_checksum"] = file_checksum(brief_document[1])
    elif schema == "youtube_adaptation_b5_i2_package":
        from src.scripts.youtube_adaptation_handoff import build_structural_youtube_package

        handoff_artifacts = {}
        for field in ("episode_brief", "refined_thesis", "editorial_script_promise", "evidence_report", "claims_ledger"):
            document = documents.get(field)
            if document is None:
                raise ValueError(f"Falta el artefacto canónico requerido para handoff: {field}")
            handoff_artifacts[field] = document[1]
        bound = build_structural_youtube_package(bound, handoff_artifacts)
        bound["active_profile_reference"] = _active_profile_reference()
        bound["producer_run_id"] = runtime_run_id
    elif schema == "youtube_adaptation_review":
        package_document = documents.get("youtube_adaptation_b5_i2_package")
        package = package_document[0] if package_document else {}
        bound["active_profile_reference"] = _active_profile_reference()
        bound["auditor_run_id"] = runtime_run_id
        bound["artifact_id"] = package.get("package_id", "")
        if package_document is not None:
            bound["artifact_checksum"] = file_checksum(package_document[1])
        bound["producer_run_id"] = package.get("producer_run_id", "")
        independence = bool(
            bound["producer_run_id"]
            and bound["producer_run_id"] != runtime_run_id
            and request.config.get("independence_verified") is True
        )
        bound["independence_check"] = {
            "producer_actor_id": "YOUTUBE_ADAPTATION_PRODUCER",
            "auditor_actor_id": "YOUTUBE_ADAPTATION_AUDITOR",
            "producer_run_id": bound["producer_run_id"],
            "auditor_run_id": runtime_run_id,
            "decision": "PASS" if independence else "FAIL",
        }
    elif schema == "b5_i2_semantic_sufficiency_audit":
        artifact_checksums = [
            {
                "artifact_kind": item.artifact_kind,
                "artifact_id": item.artifact_id,
                "checksum": file_checksum(item.path),
                "producer_run_id": item.producer_run_id,
            }
            for item in request.input_artifacts
        ]
        producer_run_ids = sorted({item["producer_run_id"] for item in artifact_checksums if item["producer_run_id"]})
        producer_run_reference = producer_run_ids[0] if len(producer_run_ids) == 1 else "MULTIPLE_PRODUCER_RUNS"
        producer_actor_id = "SCRIPT_PRODUCT_PRODUCER" if len(producer_run_ids) == 1 else "MIXED_PRODUCER_ACTORS"
        independent = bool(
            producer_run_ids
            and runtime_run_id not in producer_run_ids
            and request.config.get("independence_verified") is True
        )
        bound.update({
            "auditor_role": request.role or "SCRIPT_PRODUCT_AUDITOR",
            "auditor_run_id": runtime_run_id,
            "auditor_skill_id": request.skill_id,
            "auditor_skill_version": request.skill_version,
            "provider_or_adapter": request.provider or "synthetic",
            "model_or_evaluator": request.model or "synthetic-evaluator",
            "execution_timestamp": bound["created_at"],
            "input_manifest_checksum": manifest_checksum(request),
            "auditor_input_checksum": manifest_checksum(request),
            "artifact_checksums": artifact_checksums,
            "artifact_references": [f"{item['artifact_kind']}:{item['artifact_id']}" for item in artifact_checksums],
            "producer_run_reference": producer_run_reference,
            "auditor_run_reference": runtime_run_id,
            "producer_actor_id": producer_actor_id,
            "auditor_actor_id": request.role or "SCRIPT_PRODUCT_AUDITOR",
            "auditor_write_scope": "AUDIT_ONLY",
            "independence_result": "PASS" if independent else "BLOCKED",
            "audited_artifact_ids": [
                f"{item['artifact_kind']}:{item['artifact_id']}"
                for item in artifact_checksums
                if item["artifact_kind"] in {"analysis", "curation", "refined_thesis", "script_promise"}
            ],
            "audited_artifact_versions": [
                item
                for item in artifact_checksums
                if item["artifact_kind"] in {"analysis", "curation", "refined_thesis", "script_promise"}
            ],
            "audit_method": "AI_SEMANTIC_REVIEW",
            "readiness": "BLOCKED" if str(request.execution_mode).upper() != "REAL" else bound.get("readiness", "BLOCKED"),
        })
    return bound


def _bind_m3_runtime_fields(
    request: ExecutionRequest,
    output: dict[str, Any],
    runtime_run_id: str,
) -> dict[str, Any]:
    """Build the final B5-I3 envelope from a cognitive projection."""
    from src.core.duration_envelope import resolve_narrative_budget, validate_narrative_allocation

    bound = copy.deepcopy(output)
    provided_input_kinds = {item.artifact_kind for item in request.input_artifacts}
    missing_input_kinds = sorted(M3_REQUIRED_INPUT_KINDS - provided_input_kinds)
    if missing_input_kinds:
        raise ValueError("B5-I3 inputs canónicos ausentes: " + ", ".join(missing_input_kinds))
    _validate_m3_input_artifacts(request)
    documents = _input_documents(request)
    human = documents.get("human_input", ({}, None, ""))[0]
    episode_id = request.episode_id or str(human.get("episode_id") or "")
    if not episode_id:
        for payload, _, _ in documents.values():
            if payload.get("episode_id"):
                episode_id = str(payload["episode_id"])
                break
    if not episode_id:
        raise ValueError("B5-I3 requiere episode_id canónico.")
    id_key = {
        "viewer_journey": "viewer_journey_id",
        "opening_design": "opening_design_id",
        "closing_design": "closing_design_id",
        "narrative_plan": "script_plan_id",
    }[request.output_schema]
    bound[id_key] = request.output_artifact_id or f"{request.output_schema.upper()}-{runtime_run_id}"
    bound["episode_id"] = episode_id
    bound["artifact_version"] = str(request.config.get("artifact_version") or "1.0.0")
    bound["schema_version"] = "1.0.0"
    bound["created_at"] = _now()
    parent_artifacts = []
    input_checksums: dict[str, str] = {}
    for item in request.input_artifacts:
        checksum = file_checksum(item.path)
        ref = f"{item.artifact_kind}:{item.artifact_id}"
        parent_artifacts.append({
            "artifact_kind": item.artifact_kind,
            "artifact_id": item.artifact_id,
            "checksum": checksum,
            "producer_run_id": item.producer_run_id,
        })
        input_checksums[ref] = checksum
    bound["input_checksums"] = input_checksums
    bound["lineage"] = {
        "root_episode_id": episode_id,
        "parent_artifacts": parent_artifacts,
        "generated_by": "SOFTWARE",
        "generation_run_id": runtime_run_id,
    }
    if "human_input" in documents and request.output_schema == "narrative_plan":
        bound["duration_target_minutes"] = human.get("duration_target_minutes")
        bound["target_language"] = human.get("target_language")
        bound["user_instructions"] = human.get("user_instructions", [])

    resolved = resolve_narrative_budget(
        human.get("duration_target_minutes"),
        wpm_target=int(request.config.get("wpm_target") or 150),
    )
    wpm = int(resolved["wpm_target"])
    if request.output_schema in {"opening_design", "closing_design"}:
        word_budget = bound.get("word_budget")
        if not isinstance(word_budget, int) or word_budget <= 0:
            raise ValueError(f"{request.output_schema} requiere word_budget cognitivo.")
        bound["estimated_words"] = word_budget
        bound["estimated_time"] = round(word_budget / wpm * 60, 2)
        bound["wpm_target"] = wpm
    elif request.output_schema == "narrative_plan":
        if resolved["word_budget_total"] is None:
            raise ValueError("STOP_LOCAL_DURATION_UNRESOLVED: NarrativePlan requiere duración numérica canónica")
        validate_narrative_allocation(bound.get("blocks"), int(resolved["word_budget_total"]))
        bound["word_budget_total"] = int(resolved["word_budget_total"])
        bound["wpm_target"] = wpm
    bound["checksum"] = hashlib.sha256(
        canonical_json({key: value for key, value in bound.items() if key != "checksum"})
    ).hexdigest()
    return bound


def _validate_m3_input_artifacts(request: ExecutionRequest) -> None:
    """Validate the complete canonical M1/M2 input set before cognition runs."""
    from src.core.contract_validation import validate_against_schema

    seen: set[str] = set()
    human_episode_id = str(request.episode_id or "")
    canonical_profile = None
    try:
        from src.ai.role_execution import load_active_profile_authority

        canonical_profile = load_active_profile_authority()
    except Exception as exc:
        raise ValueError("B5-I3 perfil editorial activo no resoluble") from exc
    for item in request.input_artifacts:
        if item.artifact_kind in seen:
            raise ValueError(f"B5-I3 input duplicado: {item.artifact_kind}")
        seen.add(item.artifact_kind)
        if not item.artifact_id or not item.producer_run_id:
            raise ValueError(f"B5-I3 binding incompleto: {item.artifact_kind}")
        if not item.path.is_file():
            raise ValueError(f"B5-I3 input ilegible o inexistente: {item.artifact_kind}")
        try:
            payload = json.loads(item.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"B5-I3 JSON inválido: {item.artifact_kind}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"B5-I3 payload no objeto: {item.artifact_kind}")
        canonical_id_field = M3_CANONICAL_ID_FIELDS.get(item.artifact_kind)
        if canonical_id_field and item.artifact_id != str(payload.get(canonical_id_field) or ""):
            raise ValueError(f"B5_I3_CANONICAL_ARTIFACT_ID_MISMATCH:{item.artifact_kind}")
        schema_name = M3_INPUT_SCHEMA_BY_KIND.get(item.artifact_kind)
        if schema_name:
            violations = validate_against_schema(payload, schema_name)
            if violations:
                raise ValueError(
                    f"B5-I3 schema inválido ({item.artifact_kind}): " + "; ".join(violations)
                )
        if item.artifact_kind == "active_editorial_profile_reference":
            expected_profile = {
                "profile_id": canonical_profile.get("ACTIVE_PROFILE_ID"),
                "profile_version": canonical_profile.get("ACTIVE_PROFILE_VERSION"),
                "profile_checksum": canonical_profile.get("profile_checksum"),
            }
            observed_profile = {
                "profile_id": payload.get("ACTIVE_PROFILE_ID"),
                "profile_version": payload.get("ACTIVE_PROFILE_VERSION"),
                "profile_checksum": payload.get("profile_checksum"),
            }
            if observed_profile != expected_profile:
                raise ValueError("B5-I3 perfil editorial activo no coincide con la autoridad canónica")
        payload_episode_id = payload.get("episode_id")
        if payload_episode_id is not None:
            if not human_episode_id:
                human_episode_id = str(payload_episode_id)
            elif str(payload_episode_id) != human_episode_id:
                raise ValueError(
                    f"B5-I3 episode_id inconsistente: {item.artifact_kind}={payload_episode_id}, expected={human_episode_id}"
                )
    if not human_episode_id:
        raise ValueError("B5-I3 episode_id canónico ausente")


def validate_editorial_payload(payload: dict[str, Any], schema_name: str) -> list[str]:
    errors = Draft7Validator(editorial_projection_schema(schema_name)).iter_errors(payload)
    return [
        f"[{' -> '.join(str(p) for p in error.path) if error.path else 'root'}] {error.message}"
        for error in sorted(errors, key=lambda e: e.path)
    ]


def _runtime_fields_for_schema(schema_name: str | None) -> set[str]:
    return EDITORIAL_RUNTIME_FIELDS | ({"status"} if schema_name == "early_packaging_hypothesis" else set())


def _project_nested_runtime_fields(schema_name: str | None) -> bool:
    return schema_name == "early_packaging_hypothesis"


def editorial_only_payload(payload: dict[str, Any], schema_name: str | None = None) -> dict[str, Any]:
    runtime_fields = _runtime_fields_for_schema(schema_name)
    if isinstance(payload, dict):
        return {
            key: editorial_only_payload(value, schema_name) if _project_nested_runtime_fields(schema_name) else value
            for key, value in payload.items()
            if key not in runtime_fields
        }
    if isinstance(payload, list):
        return [editorial_only_payload(value, schema_name) for value in payload] if _project_nested_runtime_fields(schema_name) else payload
    return payload


def _runtime_field_paths(value: Any, path: str = "", runtime_fields: set[str] | None = None, recursive: bool = False) -> list[str]:
    runtime_fields = runtime_fields or EDITORIAL_RUNTIME_FIELDS
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in runtime_fields:
                paths.append(child_path)
            if recursive:
                paths.extend(_runtime_field_paths(child, child_path, runtime_fields, recursive=True))
    elif recursive and isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_runtime_field_paths(child, f"{path}[{index}]", runtime_fields, recursive=True))
    return paths


def editorial_projection_schema(schema_name: str) -> dict[str, Any]:
    schema = load_schema(schema_name)
    required_exempt = _runtime_fields_for_schema(schema_name) | EDITORIAL_RUNTIME_NORMALIZED_FIELDS
    recursive = _project_nested_runtime_fields(schema_name)

    def project(node: Any, *, nested: bool = False) -> Any:
        if isinstance(node, list):
            return [project(item, nested=(nested or not recursive)) for item in node]
        if not isinstance(node, dict):
            return node
        projected = {key: project(value, nested=(nested or not recursive)) for key, value in node.items()}
        fields = required_exempt if recursive or not nested else set()
        if isinstance(node.get("required"), list) and fields:
            projected["required"] = [field for field in node["required"] if field not in required_exempt]
        if isinstance(node.get("properties"), dict) and fields:
            projected["properties"] = {
                key: project(value, nested=True)
                for key, value in node["properties"].items()
                if key not in required_exempt
            }
        return projected

    return project(schema)


def _normalized_run_configuration(request: ExecutionRequest) -> dict[str, Any] | None:
    if request.run_configuration:
        return dict(request.run_configuration)
    if not request.execution_profile and not request.execution_family and not request.config.get("execution_family"):
        return None
    selection_path = request.config.get("execution_family_selection_path")
    if str(request.execution_mode).upper() in {"SYNTHETIC", "SYNTHETIC_TEST", "MOCK"}:
        selection_path = None
    return {
        "role_id": request.role,
        "execution_route": request.execution_route or request.config.get("execution_route") or request.config.get("default_execution_route") or "local_model",
        "execution_profile": request.execution_profile,
        "execution_family": request.execution_family or request.config.get("execution_family"),
        "executor_override": request.config.get("executor_override"),
        "provider_override": request.config.get("provider_override"),
        "model_override": request.model,
        "reasoning_effort": request.reasoning_effort or request.config.get("reasoning_effort"),
        "timeout_seconds": int(request.config.get("timeout_seconds") or request.timeout or 30),
        "max_retries": int(request.config.get("max_retries") or 0),
        "temperature": request.config.get("temperature"),
        "max_tokens": request.config.get("max_tokens"),
        "budget_limit": request.config.get("budget_limit"),
        "paid_cost_approved": bool(request.config.get("paid_cost_approved", False)),
        "execution_family_selection_path": selection_path,
        "mission_contract_path": request.config.get("mission_contract_path"),
        "completion_gate_result_path": request.config.get("completion_gate_result_path"),
        "mission_repo_root": request.config.get("mission_repo_root"),
    }


def _apply_route_resolution(request: ExecutionRequest, route: Any) -> None:
    # An explicitly requested canonical handoff remains handoff-only after
    # profile resolution.  The selected profile is still resolved by
    # AgentRuntimePort; this branch prevents the HANDOFF_ONLY route from being
    # silently converted into the integrated AgentExecutorProvider.
    request.resolved_route = route
    request.resolved_route_token = _VERIFIED_ROUTE_TOKEN
    handoff_requested = (
        request.provider == "agent_handoff"
        or (request.execution_mode or "").lower() == "agent_handoff"
        or getattr(route, "execution_family", None) == "AGENT_HARNESS"
    )
    request.provider = "agent_handoff" if handoff_requested and getattr(route, "route_type", None) == "AGENT_HARNESS_RUNTIME" else route.provider_adapter
    request.model = route.model
    request.reasoning_effort = getattr(route, "reasoning_effort", None)
    request.executor = route.executor
    request.timeout = float(route.timeout_seconds)
    request.execution_route = route.execution_route
    request.execution_profile = route.execution_profile
    request.execution_family = getattr(route, "execution_family", None)
    request.config = {
        **request.config,
        "timeout_seconds": route.timeout_seconds,
        "max_retries": route.max_retries,
        "temperature": route.temperature,
        "max_tokens": route.max_tokens,
        "budget_limit": route.budget_limit,
        "paid_cost_approved": route.paid_cost_approved,
        "cost_policy": route.cost_policy,
        "provider_config_ref": route.provider_config_ref,
        "resolved_actual_executor": route.executor,
        "resolved_actual_provider": route.provider,
        "resolved_actual_model": route.model,
        "reasoning_effort": getattr(route, "reasoning_effort", None),
        "reasoning_effort_supported": getattr(route, "reasoning_effort_supported", False),
        "execution_profile": route.execution_profile,
        "execution_family": getattr(route, "execution_family", None),
        "execution_route": route.execution_route,
        "provider_label": getattr(route, "provider_label", None),
        "api_base_env": getattr(route, "api_base_env", None),
        "api_key_env": getattr(route, "api_key_env", None),
        "model_env": getattr(route, "model_env", None),
        "selected_executor": route.executor,
        "selected_provider": route.provider,
        "selected_model": route.model,
        "actual_provider": route.provider,
        "actual_model": route.model,
        "runtime_route_resolved": True,
        "model_selection": getattr(route, "model_selection", "USER_SELECTED"),
        "executor_accepts_model_override": getattr(route, "executor_accepts_model_override", False),
    }


def _execute_unfinalized(request: ExecutionRequest) -> ExecutionResult:
    started, manifest = _now(), manifest_checksum(request)
    if request.execution_mode == "SYNTHETIC_TEST" and request.mock_output is None:
        return _result(
            request,
            "none",
            ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
            started,
            manifest,
            error="SYNTHETIC_MOCK_OUTPUT_REQUIRED: real providers are unavailable in synthetic test mode",
        )
    repository_root = Path(str(request.config.get("repository_root") or Path(__file__).resolve().parents[2])).resolve()
    try:
        preflight = preflight_controlled_execution(request, root=repository_root)
        from src.ai.registry import capture_pre_run_snapshot

        if preflight.get("authorization") is not None:
            from src.ai.registry import _VERIFIED_AUTHORIZATION_TOKEN
            request.config = {
                **request.config,
                "_mission_authorization_verified": True,
                "_mission_authorization_token": _VERIFIED_AUTHORIZATION_TOKEN,
                "mission_id": getattr(preflight["authorization"], "mission_id", request.config.get("mission_id")),
                "mission_contract_sha256": getattr(preflight["authorization"], "contract_sha256", None),
            }
        capture_pre_run_snapshot(request, authorization=preflight.get("authorization"), root=repository_root)
        if preflight.get("context_manifest") is not None:
            request.config = {**request.config, "resolved_context_manifest": preflight["context_manifest"], "resolved_context_manifest_sha256": preflight["context_manifest"]["manifest_sha256"], "mission_contract_sha256": getattr(preflight.get("authorization"), "contract_sha256", None)}
    except (PermissionError, ValueError) as exc:
        return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc))
    mission_contract = preflight.get("mission_contract")
    if mission_contract is not None and mission_contract.mission_mode == "REDUCED":
        convergence_result = _execute_reduced_mission(request, started, manifest, mission_contract)
        if convergence_result.status is not ExecutionStatus.CONVERGED:
            return convergence_result
        synthetic_mode = str(request.execution_mode).upper() in {"SYNTHETIC", "SYNTHETIC_TEST", "MOCK"}
        if not synthetic_mode and request.execution_family != "AGENT_HARNESS" and request.execution_route != "agent_harness":
            return convergence_result
        request.config = {
            **request.config,
            "_mission_convergence": convergence_result.usage,
        }
    runtime_port = AgentRuntimePort(Path(request.config["execution_profiles_path"]) if request.config.get("execution_profiles_path") else None)
    run_configuration = _normalized_run_configuration(request)
    if run_configuration:
        request.config = {
            **request.config,
            **{
                key: run_configuration[key]
                for key in ("execution_family_selection_path", "mission_contract_path", "completion_gate_result_path", "mission_repo_root")
                if run_configuration.get(key) not in (None, "")
            },
        }
        try:
            route = runtime_port.resolve_run_configuration(
                run_configuration,
                enforce_selector=str(request.execution_mode).upper() not in {"SYNTHETIC", "SYNTHETIC_TEST", "MOCK"},
            )
        except ValueError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if route.status != READY:
            return _result(
                request,
                route.provider_adapter,
                ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
                started,
                manifest,
                error=str(route.blocking_reason),
                usage={
                    **_availability_metadata(str(route.blocking_reason)),
                    "timeout_seconds": route.timeout_seconds,
                    "max_retries": route.max_retries,
                    "cost_policy": route.cost_policy,
                    "provider_config_ref": route.provider_config_ref,
                    "execution_profile": route.execution_profile,
                    "actual_executor": route.executor,
                    "actual_provider": route.provider,
                    "actual_model": route.model,
                    "execution_route": route.execution_route,
                },
            )
        _apply_route_resolution(request, route)
    elif request.execution_route:
        try:
            route = runtime_port.resolve(request.role, request.execution_route)
        except ValueError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if route.status != READY:
            return _result(
                request,
                route.provider_adapter,
                ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
                started,
                manifest,
                error=str(route.blocking_reason),
                usage={
                    **_availability_metadata(str(route.blocking_reason)),
                    "timeout_seconds": route.timeout_seconds,
                    "max_retries": route.max_retries,
                    "cost_policy": route.cost_policy,
                    "provider_config_ref": route.provider_config_ref,
                    "execution_profile": route.execution_profile,
                    "actual_executor": route.executor,
                    "actual_provider": route.provider,
                    "actual_model": route.model,
                    "execution_route": route.execution_route,
                },
            )
        _apply_route_resolution(request, route)
    resolved_authorization = preflight.get("authorization")
    if resolved_authorization is not None and callable(getattr(resolved_authorization, "verify", None)) and (request.execution_profile or request.execution_family) and request.execution_route:
        try:
            resolved_authorization.verify(
                repository_root,
                capability_id=str(request.capability_id),
                role_id=str(request.role),
                operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
                execution_profile_id=request.execution_profile,
                execution_family=request.execution_family or request.config.get("execution_family"),
                execution_route=str(request.execution_route),
                execution_interface=str(request.config.get("execution_interface") or "UNSPECIFIED_INTERFACE"),
                required_material_decision_ref=preflight.get("required_material_decision_ref"),
            )
        except PermissionError as exc:
            return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=f"ROUTE_NOT_AUTHORIZED_AFTER_RESOLUTION:{exc}")
    if request.mock_output is not None and request.execution_mode == "SYNTHETIC_TEST":
        request.provider = "mock"
    provider_name = resolve_provider(request)
    if not provider_name:
        return _result(request, "none", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error="no hay ruta real configurada")
    if provider_name not in KNOWN_PROVIDERS:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, error="provider desconocido")
    if provider_name in REAL_EXTERNAL_PROVIDERS and resolved_authorization is None:
        return _result(
            request,
            provider_name,
            ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR,
            started,
            manifest,
            error=f"ENTRY_FAIL_CLOSED:REAL_PROVIDER_WITHOUT_MISSION_AUTHORIZATION:{provider_name}",
            usage=_availability_metadata("ENTRY_FAIL_CLOSED:REAL_PROVIDER_WITHOUT_MISSION_AUTHORIZATION"),
        )
    if provider_name == "agent_handoff":
        run_id = f"RUN-AI-{uuid.uuid4().hex}"
        try:
            package = AgentHandoffProvider().prepare(request, manifest, run_id)
        except PermissionError as exc:
            return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
        if request.config.get("execution_registry_path"):
            from src.ai.registry import register_handoff

            register_handoff(Path(request.config["execution_registry_path"]), package, request)
        return _result(
            request,
            provider_name,
            ExecutionStatus.HANDOFF_PREPARED,
            started,
            manifest,
            usage={"package": str(package), **request.config.get("_mission_convergence", {})},
            run_id=run_id,
        )
    provider = {
        "mock": MockProvider(),
        "ollama": OllamaProvider(),
        "deepseek": DeepSeekProvider(),
        "openai_compatible": OpenAICompatibleProvider(),
        "agent_executor": AgentExecutorProvider(),
    }[provider_name]
    try:
        output, usage = provider.execute(request)
    except PermissionError as exc:
        return _result(request, provider_name, ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=str(exc), usage=_availability_metadata(str(exc)))
    except (RuntimeError, ValueError) as exc:
        availability = _availability_metadata(str(exc))
        status = ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER if availability.get("availability_status") in {"CREDENTIALS_MISSING", "MODEL_UNAVAILABLE", "PROVIDER_UNAVAILABLE", "TIMEOUT", "MODEL_INVOCATION_FAILED"} else (ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR if availability.get("availability_status") in {"BLOCKED_PENDING_OWNER_COST_AUTHORIZATION", "EXECUTOR_UNAVAILABLE", "AGENT_HARNESS_SMOKE_ONLY_UNTIL_R6_B_RETRY"} else ExecutionStatus.FAILED)
        return _result(request, provider_name, status, started, manifest, error=str(exc), usage=availability)
    if request.output_schema in EDITORIAL_ONLY_SCHEMAS:
        provider_output = output or {}
        runtime_fields = _runtime_fields_for_schema(request.output_schema)
        output = editorial_only_payload(provider_output, request.output_schema)
        violations = validate_editorial_payload(output, request.output_schema)
        violations.extend(
            f"[root] metadata técnica de IA no permitida: {path}"
            for path in _runtime_field_paths(
                provider_output,
                runtime_fields=runtime_fields,
                recursive=_project_nested_runtime_fields(request.output_schema),
            )
        )
        if violations:
            return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, output=output, error="OUTPUT_COGNITIVE_CONTRACT_INVALID: " + "; ".join(violations), usage=usage)
        try:
            output, runtime_run_id = _bind_runtime_fields(request, output)
        except ValueError as exc:
            return _result(
                request,
                provider_name,
                ExecutionStatus.FAILED,
                started,
                manifest,
                output=output,
                error=f"OUTPUT_BINDING_INVALID: {exc}",
                usage=usage,
            )
        violations = validate_against_schema(output, request.output_schema)
    else:
        output = output or {}
        runtime_run_id = None
        violations = validate_against_schema(output, request.output_schema)
    if violations:
        return _result(request, provider_name, ExecutionStatus.FAILED, started, manifest, output=output, error="OUTPUT_CONTRACT_INVALID: " + "; ".join(violations), usage=usage)
    return _result(request, provider_name, ExecutionStatus.SUCCEEDED, started, manifest, output=output, usage=usage, real=provider_name in REAL_EXTERNAL_PROVIDERS, run_id=runtime_run_id)


def _execute_reduced_mission(request: ExecutionRequest, started: str, manifest: str, mission_contract: Any) -> ExecutionResult:
    """Run the canonical reduced-mission loop after authorization and preflight."""
    from src.core.mission_convergence import BLOCKED, CONVERGED, MAX_ITERATIONS_REACHED, run_convergence_loop

    callbacks = request.config.get("convergence_callbacks")
    required = ("implement", "verify", "adversarial_review", "repair")
    if not isinstance(callbacks, dict) or any(not callable(callbacks.get(name)) for name in required):
        return _result(request, "mission_convergence", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error="REDUCED_MISSION_CALLBACKS_REQUIRED")
    try:
        outcome = run_convergence_loop(
            implement=callbacks["implement"], verify=callbacks["verify"],
            adversarial_review=callbacks["adversarial_review"], repair=callbacks["repair"],
            max_iterations=int(request.config.get("convergence_max_iterations", 3)),
            review_policy=mission_contract.reduced_fields["review_policy"],
            sensitive_change=bool(mission_contract.contains_material_repair), governed=True,
        )
    except (TypeError, ValueError) as exc:
        return _result(request, "mission_convergence", ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR, started, manifest, error=f"MISSION_CONVERGENCE_INVALID:{exc}")
    usage = {"mission_convergence": outcome.to_dict(), "next_review_stage": outcome.review_stage, "mission_contract_mode": "REDUCED"}
    if outcome.status == CONVERGED:
        return _result(request, "mission_convergence", ExecutionStatus.CONVERGED, started, manifest, usage=usage)
    status = ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR if outcome.status == BLOCKED else ExecutionStatus.FAILED
    return _result(request, "mission_convergence", status, started, manifest, error=f"MISSION_CONVERGENCE_{outcome.status}", usage=usage)


def _finalize_mission_reservation(request: ExecutionRequest, result: ExecutionResult) -> ExecutionResult:
    reservation_id = request.config.get("_mission_reservation_id")
    registry_path = request.config.get("execution_registry_path")
    if not reservation_id or not registry_path or request.config.get("_mission_reservation_status") != "RESERVED":
        return result
    status = "CONSUMED" if result.status in {ExecutionStatus.SUCCEEDED, ExecutionStatus.HANDOFF_PREPARED, ExecutionStatus.CONVERGED} else "FAILED"
    try:
        mark_mission_reservation(registry_path, reservation_id, status)
        request.config = {**request.config, "_mission_reservation_status": status}
        result.usage["mission_reservation_status"] = status
    except (OSError, ValueError, PermissionError) as exc:
        error = f"MISSION_RESERVATION_FINALIZATION_FAILED: {exc}"
        result.status = ExecutionStatus.FAILED
        result.error = error
        result.usage["provenance_error"] = error
        result.usage["mission_reservation_status"] = "RESERVED"
    return result


def execute(request: ExecutionRequest) -> ExecutionResult:
    return _finalize_mission_reservation(request, _execute_unfinalized(request))
