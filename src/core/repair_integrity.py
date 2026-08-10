"""Deterministic validation for verifiable repair evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.capability_governance import CANONICAL_CAPABILITY_REGISTRY, validate_capability_registry
from src.core.invalidation import InvalidationEngine
from src.core.provenance_policy import ProvenancePolicyError, canonical_registry_path
from src.core.version_manifest import compute_checksum

DEPTHS = {
    "L0_PRESENTATION": 0,
    "L1_OUTPUT": 1,
    "L2_STRUCTURE": 2,
    "L3_DECISION": 3,
    "L4_EVIDENCE": 4,
    "L5_REQUIREMENT_OR_POLICY": 5,
}
SUCCESS_STATUSES = {"SUCCEEDED", "COMPLETED", "PASS", "APPROVED"}


def evidence_checksum(evidence: dict[str, Any]) -> str:
    payload = dict(evidence)
    payload.pop("evidence_sha256", None)
    return compute_checksum(payload)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json_sha256(path: Path) -> str | None:
    if path.suffix.lower() != ".json":
        return None
    return hashlib.sha256(
        json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _safe_resolve(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts or not relative:
        return None
    try:
        resolved = (root / candidate).resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _declared_artifact_version(path: Path) -> str:
    if path.suffix.lower() != ".json":
        return "UNDECLARED"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "UNDECLARED"
    if isinstance(payload, dict):
        for key in ("artifact_version", "version", "schema_version", "registry_version"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return "UNDECLARED"


def _resolve_ref(ref: dict[str, Any], root: Path, *, evidence_code: str) -> list[str]:
    resolved = _safe_resolve(root, str(ref.get("artifact_path", "")))
    if resolved is None:
        return [evidence_code]
    try:
        raw_checksum = _file_sha256(resolved)
        if raw_checksum.lower() != str(ref.get("artifact_sha256", "")).lower():
            return [evidence_code]
        expected_canonical = ref.get("canonical_sha256")
        if expected_canonical:
            if _canonical_json_sha256(resolved) != str(expected_canonical).lower():
                return [evidence_code]
        if str(ref.get("artifact_version")) != _declared_artifact_version(resolved):
            return ["REPAIR_ARTIFACT_VERSION_MISMATCH"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return [evidence_code]
    return []


def _run_output_tokens(run: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in ("output_artifact_ids", "output_checksums", "modified_artifact_ids", "modified_artifact_paths"):
        tokens.update(str(value) for value in run.get(key, []))
    for output in run.get("outputs", []):
        if isinstance(output, dict):
            for key in ("artifact_id", "artifact_ref", "artifact_path", "checksum"):
                if output.get(key):
                    tokens.add(str(output[key]))
    return tokens


def _protected_review_tokens(evidence: dict[str, Any], protected_paths: tuple[str, ...] = ()) -> set[str]:
    tokens = {
        str(evidence["origin_artifact"][key])
        for key in ("ref_id", "artifact_path", "artifact_sha256")
        if evidence["origin_artifact"].get(key)
    }
    tokens.update(str(value) for value in evidence.get("affected_artifacts", []))
    for section in ("regression_evidence",):
        for ref in evidence.get(section, {}).get("evidence_refs", []):
            tokens.update(str(ref[key]) for key in ("ref_id", "artifact_path", "artifact_sha256") if ref.get(key))
    for ref in evidence.get("sensitive_detector_changes", {}).get("regression_evidence_ref", []):
        tokens.update(str(ref[key]) for key in ("ref_id", "artifact_path", "artifact_sha256") if ref.get(key))
    for section in ("downstream_invalidations", "downstream_revalidations"):
        for item in evidence.get(section, []):
            tokens.add(str(item.get("artifact_id")))
            ref = item.get("evidence_ref", {})
            tokens.update(str(ref[key]) for key in ("ref_id", "artifact_path", "artifact_sha256") if ref.get(key))
    for ref in evidence.get("review_evidence", {}).get("protected_artifact_refs", []):
        tokens.update(str(ref[key]) for key in ("ref_id", "artifact_path", "artifact_sha256") if ref.get(key))
    tokens.update(str(path) for path in protected_paths)
    for change in evidence.get("detector_changes", []):
        if change.get("path"):
            tokens.add(str(change["path"]))
    return tokens


def _review_outputs_resolve(run: dict[str, Any], root: Path) -> list[str]:
    violations: list[str] = []
    outputs = run.get("outputs", [])
    if not outputs:
        violations.append("REPAIR_REVIEW_OUTPUT_UNRESOLVED")
    if run.get("modification_manifest_source") != "RUNTIME_PRE_POST_DIFF":
        violations.append("REPAIR_REVIEW_PROVENANCE_INCOMPLETE")
    if "modified_artifact_ids" not in run or "modified_artifact_paths" not in run:
        violations.append("REPAIR_REVIEW_PROVENANCE_INCOMPLETE")
    for output in outputs:
        raw_path = str(output.get("artifact_path") or "")
        if Path(raw_path).is_absolute():
            try:
                path = Path(raw_path).resolve(strict=True)
                path.relative_to(root.resolve())
            except (OSError, ValueError):
                path = None
        else:
            path = _safe_resolve(root, raw_path)
        try:
            if path is None or _file_sha256(path).lower() != str(output.get("checksum", "")).lower():
                violations.append("REPAIR_REVIEW_OUTPUT_UNRESOLVED")
        except OSError:
            violations.append("REPAIR_REVIEW_OUTPUT_UNRESOLVED")
    return violations


def _resolve_l5_capability(root: Path, capability_id: str) -> dict[str, Any] | None:
    registry_path = root / CANONICAL_CAPABILITY_REGISTRY
    try:
        if not registry_path.is_file() or validate_capability_registry(registry_path):
            return None
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        capability = next(
            (item for item in registry.get("capabilities", []) if item.get("capability_id") == capability_id),
            None,
        )
        if not isinstance(capability, dict):
            return None
        if not capability.get("functional_authority_domain") or not capability.get("decision_authority"):
            return None
        return capability
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _validate_l5_authority(
    resolution: dict[str, Any],
    evidence: dict[str, Any],
    root: Path,
    provenance: dict[str, Any] | None,
    repair_evidence_path: str | None,
) -> list[str]:
    """Validate L5 through capability governance plus execution authorization."""
    violations: list[str] = []
    capability = _resolve_l5_capability(root, str(evidence.get("capability_id", "")))
    if capability is None:
        return ["GOVERNANCE_CAPABILITY_UNRESOLVED"]
    expected_authority = str(capability["decision_authority"])
    expected_domain = str(capability["functional_authority_domain"])
    approval_path = _safe_resolve(root, str(resolution.get("approval_ref", {}).get("artifact_path", "")))
    authority_path = _safe_resolve(root, str(resolution.get("authority_ref", "")))
    if approval_path is None or authority_path is None or authority_path.suffix.lower() != ".json":
        return ["GOVERNANCE_RESOLUTION_UNRESOLVED"]
    try:
        approval_data = json.loads(approval_path.read_text(encoding="utf-8"))
        approved_ref = resolution["approved_artifact_ref"]
        origin_ref = evidence["origin_artifact"]
        approval_matches_exact_artifact = all(
            approved_ref.get(key) == origin_ref.get(key)
            for key in ("ref_id", "artifact_path", "artifact_version", "artifact_sha256")
        )
        approved_ref_resolves = not _resolve_ref(approved_ref, root, evidence_code="GOVERNANCE_RESOLUTION_UNRESOLVED")
        if (
            not isinstance(approval_data, dict)
            or approval_data.get("authority_type") != "GOVERNANCE_APPROVAL"
            or approval_data.get("authority_identity") != expected_authority
            or approval_data.get("functional_authority_domain") != expected_domain
            or approval_data.get("decision") not in {"APPROVE", "AUTHORIZED"}
            or approval_data.get("mission_id") != evidence["mission_id"]
            or approval_data.get("requirement_ref") != resolution["requirement_ref"]
            or approval_data.get("artifact_version") != resolution["approved_version"]
            or approval_data.get("approved_artifact_ref") != approved_ref
            or resolution["approved_version"] != approved_ref.get("artifact_version")
            or resolution["approved_artifact_sha256"].lower() != str(approved_ref.get("artifact_sha256", "")).lower()
            or not approval_matches_exact_artifact
            or not approved_ref_resolves
        ):
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        if _file_sha256(approval_path).lower() != resolution["approval_sha256"].lower() or _file_sha256(approval_path).lower() != str(resolution["approval_ref"].get("artifact_sha256", "")).lower():
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        if _file_sha256(authority_path).lower() != resolution["authority_sha256"].lower():
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        authority_contract = json.loads(authority_path.read_text(encoding="utf-8"))
        if not isinstance(authority_contract, dict) or authority_contract.get("mission_id") != evidence["mission_id"]:
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        from src.core.mission_authorization import load_mission_authorization

        authorization = load_mission_authorization(authority_path)
        if not authorization.contains_material_repair:
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        if repair_evidence_path and authorization.repair_integrity_evidence_path != repair_evidence_path:
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        decision_path = _safe_resolve(root, authorization.authority_ref)
        if decision_path is None or _file_sha256(decision_path).lower() != authorization.authority_sha256.lower():
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        else:
            decision_data = json.loads(decision_path.read_text(encoding="utf-8"))
            if (
                not isinstance(decision_data, dict)
                or decision_data.get("authority_type") != "MISSION_AUTHORIZATION"
                or decision_data.get("decision") not in {"APPROVE", "AUTHORIZED"}
                or decision_data.get("mission_id") != evidence["mission_id"]
                or decision_data.get("requirement_ref") != resolution["requirement_ref"]
                or decision_data.get("artifact_version") != resolution["approved_version"]
            ):
                violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        if provenance:
            repair_run = provenance["repair"]
            authorization.verify(
                root,
                capability_id=evidence["capability_id"],
                role_id=str(repair_run.get("role_id", "")),
                operation="EXECUTE_CAPABILITY",
                execution_mode=str(repair_run.get("execution_mode", "")),
                execution_route=str(repair_run.get("execution_route", "")),
                execution_profile_id=str(repair_run.get("execution_profile", "")),
                execution_interface=str(repair_run.get("execution_interface", "ANY")),
            )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError, PermissionError):
        violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
    return list(dict.fromkeys(violations))


def _load_provenance(evidence: dict[str, Any], root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    provenance = evidence["provenance"]
    try:
        canonical_path = canonical_registry_path(root)
    except ProvenancePolicyError as exc:
        return None, [str(exc)]
    if Path(str(provenance["registry_path"])).as_posix() != canonical_path:
        return None, ["REPAIR_NONCANONICAL_PROVENANCE_REGISTRY"]
    path = _safe_resolve(root, canonical_path)
    if path is None:
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    try:
        if _file_sha256(path).lower() != provenance["registry_sha256"].lower():
            return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    schema_errors = validate_against_schema(registry, "execution_provenance_registry")
    if schema_errors:
        if any("modification_manifest_source" in item or "modified_artifact_" in item for item in schema_errors):
            return None, ["REPAIR_REVIEW_PROVENANCE_INCOMPLETE"]
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    runs = {run.get("run_id"): run for run in registry.get("runs", [])}
    repair_run = runs.get(provenance["repair_run_id"])
    review_run = runs.get(provenance["review_run_id"])
    if not repair_run or not review_run:
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    if repair_run is review_run or provenance["repair_run_id"] == provenance["review_run_id"]:
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    if repair_run.get("status") not in SUCCESS_STATUSES or review_run.get("status") not in SUCCESS_STATUSES:
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    repair_identity = repair_run.get("actual_executor") or repair_run.get("agent_id")
    review_identity = review_run.get("actual_executor") or review_run.get("agent_id")
    if not repair_identity or not review_identity:
        return None, ["REPAIR_PROVENANCE_UNRESOLVED"]
    if evidence["executor_id"] != repair_identity or evidence["reviewer_id"] != review_identity:
        return None, ["REPAIR_PROVENANCE_IDENTITY_MISMATCH"]
    if repair_identity == review_identity:
        return None, ["REPAIR_SELF_REVIEW"]
    return {"repair": repair_run, "review": review_run, "registry": registry}, _review_outputs_resolve(review_run, root)


def resolve_canonical_downstream(
    evidence: dict[str, Any],
    root: str | Path = ".",
) -> tuple[dict[str, list[str]] | None, list[str]]:
    """Read dependency lineage from the checksum-bound execution registry."""
    repository_root = Path(root).resolve()
    provenance = evidence.get("provenance", {})
    try:
        canonical_path = canonical_registry_path(repository_root)
    except ProvenancePolicyError as exc:
        return None, [str(exc)]
    if Path(str(provenance.get("registry_path", ""))).as_posix() != canonical_path:
        return None, ["REPAIR_NONCANONICAL_PROVENANCE_REGISTRY"]
    path = _safe_resolve(repository_root, canonical_path)
    if path is None:
        return None, ["REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN"]
    try:
        if _file_sha256(path).lower() != str(provenance.get("registry_sha256", "")).lower():
            return None, ["REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN"]
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, ["REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN"]
    if validate_against_schema(registry, "execution_provenance_registry"):
        return None, ["REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN"]
    if "dependencies" not in registry:
        return None, ["REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN"]
    try:
        engine = InvalidationEngine(registry)
        resolved: dict[str, list[str]] = {}
        for origin in engine.dependencies:
            descendants: set[str] = set()
            pending = list(engine.dependencies.get(origin, set()))
            while pending:
                child = pending.pop()
                if child in descendants:
                    continue
                descendants.add(child)
                pending.extend(engine.dependencies.get(child, set()))
            resolved[origin] = sorted(descendants)
        return resolved, []
    except (AttributeError, TypeError, ValueError):
        return None, ["REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN"]


def validate_repair_integrity(
    evidence: dict[str, Any],
    repo_root: str | Path = ".",
    *,
    expected_mission_id: str | None = None,
    expected_contract_sha256: str | None = None,
    known_downstream: dict[str, list[str]] | None = None,
    protected_paths: tuple[str, ...] = (),
    repair_evidence_path: str | None = None,
) -> list[str]:
    root = Path(repo_root).resolve()
    violations: list[str] = []
    if not evidence.get("root_cause"):
        violations.append("REPAIR_ROOT_CAUSE_MISSING")
    if evidence.get("root_cause_class") not in DEPTHS:
        violations.append("REPAIR_ROOT_CAUSE_CLASS_INVALID")
    schema_violations = validate_against_schema(evidence, "repair_integrity_evidence")
    if schema_violations:
        return list(dict.fromkeys(violations + schema_violations))

    if expected_mission_id and evidence["mission_id"] != expected_mission_id:
        violations.append("REPAIR_MISSION_BINDING_MISMATCH")
    if expected_contract_sha256 and evidence["mission_contract_sha256"].lower() != expected_contract_sha256.lower():
        violations.append("REPAIR_CONTRACT_BINDING_MISMATCH")
    if DEPTHS[evidence["repair_depth"]] < DEPTHS[evidence["root_cause_class"]]:
        violations.append("REPAIR_TOO_SHALLOW")

    violations.extend(_resolve_ref(evidence["origin_artifact"], root, evidence_code="REPAIR_ORIGIN_ARTIFACT_UNRESOLVED"))
    provenance, provenance_errors = _load_provenance(evidence, root)
    violations.extend(provenance_errors)
    if provenance:
        if provenance["repair"].get("mission_id") and provenance["repair"]["mission_id"] != evidence["mission_id"]:
            violations.append("REPAIR_PROVENANCE_MISSION_MISMATCH")
        if provenance["review"].get("mission_id") and provenance["review"]["mission_id"] != evidence["mission_id"]:
            violations.append("REPAIR_PROVENANCE_MISSION_MISMATCH")
        registered_capability = provenance["repair"].get("capability_id")
        if registered_capability is None:
            registry = provenance.get("registry", {})
            linked_records = list(registry.get("attempts", [])) + list(registry.get("handoffs", []))
            linked = [
                record.get("capability_id")
                for record in linked_records
                if record.get("run_id") == evidence["provenance"]["repair_run_id"] and record.get("capability_id")
            ]
            if linked:
                registered_capability = linked[0]
        if registered_capability is not None and registered_capability != evidence["capability_id"]:
            violations.append("REPAIR_CAPABILITY_PROVENANCE_MISMATCH")

    for ref in evidence["regression_evidence"]["evidence_refs"]:
        violations.extend(_resolve_ref(ref, root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))
    for ref in evidence["review_evidence"]["evidence_refs"]:
        violations.extend(_resolve_ref(ref, root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))
    for ref in evidence["sensitive_detector_changes"]["regression_evidence_ref"]:
        violations.extend(_resolve_ref(ref, root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))
    for ref in evidence["review_evidence"]["protected_artifact_refs"]:
        violations.extend(_resolve_ref(ref, root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))

    affected = set(evidence["downstream_impact"]["affected_artifacts"])
    if known_downstream is not None:
        origin_id = evidence["origin_artifact"]["ref_id"]
        known = set(known_downstream.get(origin_id, []))
        missing = known.difference(affected)
        if missing:
            violations.append("REPAIR_DOWNSTREAM_DEPENDENCY_OMITTED")
        affected.update(known)

    invalidated = set()
    revalidated = set()
    for item in evidence["downstream_invalidations"]:
        if item["status"] == "COMPLETED":
            invalidated.add(item["artifact_id"])
        elif not item["justification"].strip():
            violations.append("REPAIR_NOT_REQUIRED_UNJUSTIFIED")
        violations.extend(_resolve_ref(item["evidence_ref"], root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))
    for item in evidence["downstream_revalidations"]:
        if item["status"] == "COMPLETED":
            revalidated.add(item["artifact_id"])
        elif not item["justification"].strip():
            violations.append("REPAIR_NOT_REQUIRED_UNJUSTIFIED")
        violations.extend(_resolve_ref(item["evidence_ref"], root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))
    if affected and not affected.issubset(invalidated):
        violations.append("REPAIR_DOWNSTREAM_NOT_INVALIDATED")
    if affected and not affected.issubset(revalidated):
        violations.append("REPAIR_DOWNSTREAM_NOT_REVALIDATED")
    if not affected and not evidence["downstream_impact"]["no_impact_justification"].strip():
        violations.append("REPAIR_DOWNSTREAM_IMPACT_MISSING")

    detector_impact = evidence["detector_impact"]
    detector_required = evidence["detector_change_required"]
    if detector_impact == "YES" and detector_required != "YES":
        violations.append("REPAIR_DETECTOR_CHANGE_REQUIRED")
    if detector_required == "YES" and not evidence["detector_changes"]:
        violations.append("REPAIR_DETECTOR_CHANGE_REQUIRED")
    if detector_required == "NO" and not evidence["sensitive_detector_changes"]["justification"].strip():
        violations.append("REPAIR_SENSITIVE_DETECTOR_CHANGE_UNJUSTIFIED")
    regression = evidence["regression_evidence"]
    if not regression["defect_no_longer_occurs"] or not regression["neighboring_valid_behavior"]:
        violations.append("REPAIR_REGRESSION_MISSING")
    if evidence["sensitive_detector_changes"]["changed"] and not evidence["sensitive_detector_changes"]["regression_evidence_ref"]:
        violations.append("REPAIR_REGRESSION_MISSING")

    if evidence["executor_id"] == evidence["reviewer_id"]:
        violations.append("REPAIR_SELF_REVIEW")
    review = evidence["review_evidence"]
    reviewer_mutations = set()
    if provenance:
        reviewer_mutations = _run_output_tokens(provenance["review"]).intersection(_protected_review_tokens(evidence, protected_paths))
    if review["reviewer_id"] != evidence["reviewer_id"] or review["reviewer_modified_under_review"] or reviewer_mutations:
        violations.append("REPAIR_REVIEW_INVALIDATED")
    if evidence["review_status"] != "APPROVED" or review["decision"] != "APPROVED":
        violations.append("REPAIR_REVIEW_INVALIDATED")

    if evidence["root_cause_class"] == "L5_REQUIREMENT_OR_POLICY" or evidence["governance_change_requested"]:
        resolution = evidence["governance_resolution"]
        if resolution is None:
            violations.append("REPAIR_GOVERNANCE_CHANGE_REQUIRED")
            violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
        else:
            violations.extend(_resolve_ref(resolution["approval_ref"], root, evidence_code="GOVERNANCE_RESOLUTION_UNRESOLVED"))
            if resolution["approved_version"] != resolution["approval_ref"]["artifact_version"]:
                violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
            if resolution["approval_sha256"].lower() != resolution["approval_ref"]["artifact_sha256"].lower():
                violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
            if resolution["resolved_at"] > evidence["created_at"]:
                violations.append("GOVERNANCE_RESOLUTION_UNRESOLVED")
            violations.extend(_validate_l5_authority(resolution, evidence, root, provenance, repair_evidence_path))
    if evidence["compensating_changes"]:
        for change in evidence["compensating_changes"]:
            if change["review_result"] != "APPROVED" or not change["evidence_refs"] or not change["regression_refs"]:
                violations.append("REPAIR_COMPENSATING_PATCH_UNJUSTIFIED")
            for ref in change["evidence_refs"] + change["regression_refs"]:
                violations.extend(_resolve_ref(ref, root, evidence_code="REPAIR_EVIDENCE_UNRESOLVED"))

    if evidence["evidence_sha256"] != evidence_checksum(evidence):
        violations.append("REPAIR_EVIDENCE_CHECKSUM_MISMATCH")
    return list(dict.fromkeys(violations))
