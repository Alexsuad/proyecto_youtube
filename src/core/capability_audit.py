"""Deterministic TH-04 capability inventory derived from canonical seeds."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from src.core.capability_governance import validate_capability_registry
from src.core.contract_validation import validate_against_schema

TH04_SEED_PATHS = (
    "config/capability_registry.json",
    "config/responsibility_registry.json",
    "config/agent_prompt_registry.json",
    "config/agent_execution_profiles.json",
    "config/subagent_registry.json",
    "config/capability_routing.yaml",
    "config/skill_catalog.json",
)
RESOLVABLE_ROOTS = ("schemas", "src", "prompts", ".agent/skills", ".agents/skills")
OBJECT_CLASSES = {
    "EXECUTABLE_CAPABILITY", "NON_EXECUTABLE_RESPONSIBILITY", "POLICY", "GATE",
    "UTILITY", "ORCHESTRATION_ONLY", "UNRESOLVED_CANDIDATE",
}
DISPOSITIONS = {"CURRENT", "DEFERRED", "DUPLICATE", "OBSOLETE"}
REGISTRY_STATES = {"REGISTERED", "UNREGISTERED", "NOT_OBSERVED", "UNRESOLVED", "CONFLICTING"}
MATURITY_VALUES = {"DEFINED", "REGISTERED", "IMPLEMENTED", "DEMONSTRATED"}
DELTA_OPERATIONS = {"ADD", "CORRECT_METADATA", "ADD_ALIAS", "MERGE_CANDIDATE", "DEPRECATE_CANDIDATE", "NO_CHANGE"}
FORBIDDEN_DELTA_OPERATIONS = {
    "ACTIVATE", "FUNCTIONALLY_APPROVE", "PROMOTE_TO_DEMONSTRATED", "CHANGE_FUNCTIONAL_AUTHORITY",
}
JSON_SEED_SCHEMAS = {
    "config/responsibility_registry.json": "responsibility_registry",
    "config/agent_prompt_registry.json": "agent_prompt_registry",
    "config/agent_execution_profiles.json": "agent_execution_profiles",
    "config/subagent_registry.json": "subagent_registry",
    "config/skill_catalog.json": "skill_catalog",
}
REFERENCE_SUFFIXES = (".json", ".yaml", ".yml", ".py", ".md")


class CapabilityAuditInputError(ValueError):
    """Raised when an authorized TH-04 seed cannot be trusted as input."""


def _normalize(value: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in value.upper())
    return "_".join(part for part in normalized.split("_") if part)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _safe_reference(root: Path, reference: str) -> str | None:
    candidate = Path(reference.split("#", 1)[0])
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return _relative(root, resolved) if resolved.is_file() else None


def _resolve_reference_path(root: Path, reference: str, source_path: str | None = None) -> str | None:
    raw_reference = reference.split("#", 1)[0]
    resolved = _safe_reference(root, raw_reference)
    if resolved:
        return resolved
    if not source_path:
        return None
    candidate = Path(source_path).parent / raw_reference
    if candidate.is_absolute():
        return None
    resolved_path = (root / candidate).resolve()
    try:
        resolved_path.relative_to(root.resolve())
    except ValueError:
        return None
    return _relative(root, resolved_path) if resolved_path.is_file() else None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNRESOLVED"


def _generated_at(value: str | None) -> str:
    return value or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _source_inputs(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    inputs: list[dict[str, Any]] = []
    limitations: list[str] = []
    for reference in TH04_SEED_PATHS:
        path = root / reference
        if path.is_file():
            inputs.append({"path": reference, "sha256": _sha256(path)})
        else:
            inputs.append({"path": reference, "sha256": None})
            limitations.append(f"MISSING_SEED:{reference}")
    return inputs, limitations


def _envelope(root: Path, *, generated_at: str | None, source_inputs: list[dict[str, Any]], limitations: list[str], result: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "plan_id": "PLAN_004",
        "mission_id": "TH-04",
        "repository_revision": _revision(root),
        "generated_at": _generated_at(generated_at),
        "source_inputs": source_inputs,
        "evidence_refs": [entry["path"] for entry in source_inputs if entry["sha256"]],
        "limitations": sorted(set(limitations)),
        "result": result,
    }


def _validate_yaml_seed(data: Any, path: str) -> list[str]:
    if not isinstance(data, dict):
        return [f"SEED_SCHEMA_INVALID:{path}:root must be an object"]
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        return [f"SEED_SCHEMA_INVALID:{path}:capabilities must be a non-empty object"]
    errors: list[str] = []
    for identifier, route in capabilities.items():
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"SEED_SCHEMA_INVALID:{path}:capability identifier must be a non-empty string")
        if not isinstance(route, dict):
            errors.append(f"SEED_SCHEMA_INVALID:{path}#{identifier}:route must be an object")
    return errors


def _validated_seed_data(root: Path) -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = {}
    errors: list[str] = []
    for reference in TH04_SEED_PATHS:
        path = root / reference
        if not path.is_file():
            errors.append(f"MISSING_SEED:{reference}")
            continue
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) if reference.endswith((".yaml", ".yml")) else _load_json(path)
        except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
            errors.append(f"SEED_UNREADABLE:{reference}:{type(exc).__name__}")
            continue
        data[reference] = loaded
        if reference == "config/capability_registry.json":
            violations = validate_capability_registry(path)
        else:
            schema_name = JSON_SEED_SCHEMAS.get(reference)
            violations = validate_against_schema(loaded, schema_name) if schema_name else _validate_yaml_seed(loaded, reference)
        errors.extend(f"SEED_INVALID:{reference}:{violation}" for violation in violations)
    return data, sorted(set(errors))


def build_capability_discovery_scope(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    source_inputs, limitations = _source_inputs(repository)
    _, seed_errors = _validated_seed_data(repository)
    scope = _envelope(repository, generated_at=generated_at, source_inputs=source_inputs,
                      limitations=limitations + seed_errors,
                      result="PASS" if not limitations and not seed_errors else "INVALID")
    scope.update({
        "artifact_type": "CAPABILITY_DISCOVERY_SCOPE",
        "seed_paths": list(TH04_SEED_PATHS),
        "resolvable_roots": list(RESOLVABLE_ROOTS),
        "seed_validation_errors": seed_errors,
        "rules": [
            "VALIDATE_SEEDS_BEFORE_DISCOVERY",
            "FOLLOW_EXPLICIT_REFERENCES_ONLY",
            "PRESERVE_ORIGINAL_IDENTIFIER",
            "NORMALIZE_FOR_COMPARISON_ONLY",
            "NO_RECURSIVE_ROOT_SCAN",
            "ENGINEERING_SKILLS_ARE_NOT_PRODUCT_CAPABILITIES",
        ],
    })
    return scope


def _candidate(identifier: str, source_type: str, source_ref: str, *, object_class: str,
               disposition: str = "CURRENT", registry_state: str = "NOT_OBSERVED",
               reason: str, registry_presence: bool = False, maturity: Any = None) -> dict[str, Any]:
    raw_maturity = maturity if maturity is not None else None
    canonical_maturity = raw_maturity if raw_maturity in MATURITY_VALUES else None
    item = {
        "candidate_id": identifier,
        "canonical_identity": _normalize(identifier),
        "aliases": [identifier],
        "source_type": source_type,
        "source_refs": [source_ref],
        "current_registry_presence": registry_presence,
        "object_class": object_class,
        "disposition": disposition,
        "registry_state": registry_state,
        "classification_reason": reason,
        "owner_observation": {"status": "UNRESOLVED"},
        "maturity_observed": canonical_maturity,
        "maturity_observed_raw": raw_maturity,
        "observed_refs": {"roles": [], "prompts": [], "profiles": [], "routes": [], "contracts": [], "implementation": [], "tests": []},
        "observed_tests": [],
        "resolved_artifacts": [],
        "inconsistencies": [],
        "evidence_refs": [source_ref],
        "_alias_targets": [],
        "_duplicate_targets": [],
    }
    if raw_maturity is not None and canonical_maturity is None:
        item["inconsistencies"].append(f"NON_CANONICAL_MATURITY:{raw_maturity}")
    return item


def _merge_candidate(records: dict[str, dict[str, Any]], item: dict[str, Any]) -> dict[str, Any]:
    key = item["candidate_id"]
    existing = records.get(key)
    if existing is None:
        records[key] = item
        return item
    for field in ("aliases", "source_refs", "evidence_refs", "resolved_artifacts", "inconsistencies", "observed_tests", "_alias_targets", "_duplicate_targets"):
        existing[field] = sorted(set(existing[field]) | set(item[field]))
    for field in existing["observed_refs"]:
        existing["observed_refs"][field] = sorted(set(existing["observed_refs"][field]) | set(item["observed_refs"][field]))
    existing["current_registry_presence"] = existing["current_registry_presence"] or item["current_registry_presence"]
    if item["registry_state"] == "REGISTERED":
        existing["registry_state"] = "REGISTERED"
        existing["object_class"] = item["object_class"]
        existing["disposition"] = item["disposition"]
        existing["classification_reason"] = item["classification_reason"]
        existing["owner_observation"] = item["owner_observation"]
        existing["maturity_observed"] = item["maturity_observed"]
        existing["maturity_observed_raw"] = item["maturity_observed_raw"]
    return existing


def _field_for_reference_key(key: str) -> str:
    value = key.lower()
    if "test" in value:
        return "tests"
    if "role" in value or "responsib" in value:
        return "roles"
    if "prompt" in value:
        return "prompts"
    if "profile" in value:
        return "profiles"
    if "route" in value or "routing" in value:
        return "routes"
    if any(token in value for token in ("contract", "schema", "requirement", "policy", "gate")):
        return "contracts"
    return "implementation"


def _record_reference(root: Path, candidate: dict[str, Any], field: str, reference: str) -> None:
    candidate["observed_refs"][field].append(reference)
    candidate["evidence_refs"].append(reference)
    if field == "tests" or reference.replace("\\", "/").startswith("tests/"):
        candidate["observed_tests"].append(reference)
    resolved = _safe_reference(root, reference)
    if resolved:
        candidate["resolved_artifacts"].append(resolved)
    elif _looks_like_reference(reference):
        candidate["inconsistencies"].append(f"UNRESOLVED_REFERENCE:{reference}")


def _looks_like_reference(value: str) -> bool:
    lowered = value.lower()
    return (
        not lowered.startswith(("http://", "https://"))
        and ("/" in value or "\\" in value or lowered.endswith(REFERENCE_SUFFIXES))
    )


def _iter_explicit_references(value: Any, location: str = "") -> Iterable[tuple[str, str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}" if location else str(key)
            yield from _iter_explicit_references(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_explicit_references(child, f"{location}[{index}]")
    elif isinstance(value, str) and _looks_like_reference(value):
        key = location.rsplit(".", 1)[-1].split("[", 1)[0]
        yield location, key, value


def _reference_kind(key: str, reference: str) -> str | None:
    value = f"{key}:{reference}".lower().replace("\\", "/")
    if "policy" in value:
        return "POLICY"
    if "gate" in value:
        return "GATE"
    return None


def _load_reachable_structured_artifact(root: Path, relative_path: str) -> Any | None:
    path = root / relative_path
    if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError):
        return None


def _resolved_reference_records(root: Path, seed_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve explicit references transitively without scanning filesystem roots."""
    resolved: list[dict[str, Any]] = []
    visited: set[str] = set(seed_data)
    pending: list[tuple[str, Any, list[str]]] = [
        (seed_path, data, [seed_path]) for seed_path, data in sorted(seed_data.items())
    ]
    while pending:
        source_path, data, provenance_chain = pending.pop(0)
        for location, key, reference in _iter_explicit_references(data):
            source_ref = f"{source_path}#{location}"
            path = _resolve_reference_path(root, reference, source_path)
            record = {
                "source_ref": source_ref,
                "reference": reference,
                "resolved_path": path,
                "status": "RESOLVED" if path else "UNRESOLVED",
                "object_class": _reference_kind(key, reference),
                "provenance_chain": provenance_chain + [source_ref] + ([path] if path else []),
            }
            resolved.append(record)
            if not path or path in visited:
                continue
            visited.add(path)
            reached_data = _load_reachable_structured_artifact(root, path)
            if reached_data is not None:
                pending.append((path, reached_data, record["provenance_chain"]))
    return sorted(resolved, key=lambda item: (item["source_ref"], item["reference"]))


def _add_reachable_policy_or_gate(records: dict[str, dict[str, Any]], reference_record: dict[str, Any]) -> None:
    object_class = reference_record["object_class"]
    if object_class not in {"POLICY", "GATE"}:
        return
    identifier = f"{object_class}:{reference_record['reference']}"
    item = _candidate(identifier, "EXPLICIT_REACHABLE_REFERENCE", reference_record["source_ref"],
                      object_class=object_class,
                      registry_state="NOT_OBSERVED" if reference_record["resolved_path"] else "UNRESOLVED",
                      reason=f"Explicitly reachable {object_class.lower()} reference; not a capability.")
    if reference_record["resolved_path"]:
        item["resolved_artifacts"].append(reference_record["resolved_path"])
    else:
        item["inconsistencies"].append(f"UNRESOLVED_REFERENCE:{reference_record['reference']}")
    _merge_candidate(records, item)


def _merge_alias(target: dict[str, Any], alias: dict[str, Any], evidence: str) -> None:
    target["aliases"] = sorted(set(target["aliases"] + alias["aliases"]))
    for field in ("source_refs", "evidence_refs", "resolved_artifacts", "inconsistencies", "observed_tests"):
        target[field] = sorted(set(target[field]) | set(alias[field]))
    for field in target["observed_refs"]:
        target["observed_refs"][field] = sorted(set(target["observed_refs"][field]) | set(alias["observed_refs"][field]))
    target["evidence_refs"].append(evidence)


def _resolve_identity_collisions(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in records.values():
        groups.setdefault(item["canonical_identity"], []).append(item)
    for group in groups.values():
        if len(group) < 2:
            continue
        by_id = {item["candidate_id"]: item for item in group}
        for item in list(group):
            targets = set(item["_alias_targets"]) & set(by_id)
            if targets:
                target = by_id[sorted(targets)[0]]
                if target is not item:
                    _merge_alias(target, item, f"EXPLICIT_ALIAS_EVIDENCE:{item['candidate_id']}->{target['candidate_id']}")
                    records.pop(item["candidate_id"], None)
        remaining = [item for item in group if item["candidate_id"] in records]
        if len(remaining) < 2:
            continue
        remaining_ids = {item["candidate_id"] for item in remaining}
        duplicate_evidence_ids = {
            item["candidate_id"] for item in remaining
            if set(item["_duplicate_targets"]) & remaining_ids
        }
        if duplicate_evidence_ids:
            for item in remaining:
                if item["candidate_id"] in duplicate_evidence_ids:
                    item["disposition"] = "DUPLICATE"
                    item["classification_reason"] = "Explicit duplicate evidence; retained for auditability."
                    item["evidence_refs"].append("EXPLICIT_DUPLICATE_EVIDENCE")
            continue
        for item in remaining:
            item["registry_state"] = "CONFLICTING"
            item["inconsistencies"].append(
                f"IDENTITY_NORMALIZATION_COLLISION:{item['canonical_identity']}:{','.join(sorted(by_id))}"
            )
    return records


def _finalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    for field in ("aliases", "source_refs", "evidence_refs", "resolved_artifacts", "inconsistencies", "observed_tests"):
        candidate[field] = sorted(set(candidate[field]))
    for field in candidate["observed_refs"]:
        candidate["observed_refs"][field] = sorted(set(candidate["observed_refs"][field]))
    candidate.pop("_alias_targets", None)
    candidate.pop("_duplicate_targets", None)
    return candidate


def build_capability_audit_universe(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    source_inputs, limitations = _source_inputs(repository)
    seed_data, seed_errors = _validated_seed_data(repository)
    if limitations or seed_errors:
        raise CapabilityAuditInputError("TH04_INVALID_SEEDS: " + "; ".join(sorted(set(limitations + seed_errors))))
    records: dict[str, dict[str, Any]] = {}
    registry = seed_data[TH04_SEED_PATHS[0]]
    registry_route_refs: dict[str, set[str]] = {}
    for capability in registry["capabilities"]:
        identifier = str(capability["capability_id"])
        deferred = capability.get("implementation_kind") == "DEFERRED" or capability.get("maturity_status") == "DEFINED"
        item = _candidate(
            identifier, "CAPABILITY_REGISTRY", TH04_SEED_PATHS[0], object_class="EXECUTABLE_CAPABILITY",
            disposition="DEFERRED" if deferred else "CURRENT", registry_state="REGISTERED",
            reason="Canonical capability registry entry.", registry_presence=True,
            maturity=capability.get("maturity_status"),
        )
        authority_domain = capability.get("functional_authority_domain")
        decision_authority = capability.get("decision_authority")
        item["owner_observation"] = {
            "status": "RESOLVED_FROM_CANONICAL_FIELD" if authority_domain and decision_authority else "UNRESOLVED",
            "functional_authority_domain": authority_domain,
            "decision_authority": decision_authority,
        }
        for _, key, reference in _iter_explicit_references(capability):
            _record_reference(repository, item, _field_for_reference_key(key), reference)
        if capability.get("routing_ref"):
            registry_route_refs.setdefault(str(capability["routing_ref"]), set()).add(identifier)
        _merge_candidate(records, item)

    responsibilities = seed_data[TH04_SEED_PATHS[1]]
    for responsibility in responsibilities["responsibilities"]:
        identifier = f"ROLE:{responsibility['role_id']}"
        item = _candidate(identifier, "RESPONSIBILITY_REGISTRY", TH04_SEED_PATHS[1],
                          object_class="NON_EXECUTABLE_RESPONSIBILITY",
                          reason="Registered responsibility is not a capability by itself.")
        item["owner_observation"] = {"status": "RESOLVED_FROM_CANONICAL_FIELD" if responsibility.get("functional_owner") else "UNRESOLVED",
                                     "functional_authority_domain": responsibility.get("functional_owner")}
        _merge_candidate(records, item)

    prompts = seed_data[TH04_SEED_PATHS[2]]
    for prompt in prompts["prompts"]:
        identifier = f"PROMPT:{prompt['prompt_id']}"
        _merge_candidate(records, _candidate(identifier, "PROMPT_REGISTRY", TH04_SEED_PATHS[2], object_class="UTILITY",
                                             reason="Prompt is supporting mechanism, not a product capability."))

    profiles = seed_data[TH04_SEED_PATHS[3]]
    profile_ids = list(profiles["role_defaults"].keys()) + [entry.get("profile_id") for entry in profiles.get("profiles", []) if entry.get("profile_id")]
    for profile_id in profile_ids:
        identifier = f"PROFILE:{profile_id}"
        _merge_candidate(records, _candidate(identifier, "EXECUTION_PROFILE_REGISTRY", TH04_SEED_PATHS[3], object_class="ORCHESTRATION_ONLY",
                                             reason="Execution profile is routing configuration, not a product capability."))

    subagents = seed_data[TH04_SEED_PATHS[4]]
    for agent in subagents["agents"]:
        identifier = f"SUBAGENT:{agent['agent_id']}"
        _merge_candidate(records, _candidate(identifier, "SUBAGENT_REGISTRY", TH04_SEED_PATHS[4], object_class="ORCHESTRATION_ONLY",
                                             reason="Subagent record is an execution participant, not a product capability.",
                                             maturity=agent.get("maturity_status")))

    routing = seed_data[TH04_SEED_PATHS[5]]
    for capability_id, route in routing["capabilities"].items():
        route_ref = f"{TH04_SEED_PATHS[5]}#{capability_id}"
        entrypoint = str(route.get("entrypoint", ""))
        object_class = "EXECUTABLE_CAPABILITY" if entrypoint and _safe_reference(repository, entrypoint) else "UNRESOLVED_CANDIDATE"
        item = _candidate(str(capability_id), "CAPABILITY_ROUTING", route_ref, object_class=object_class,
                          registry_state="UNREGISTERED", reason="Routing-declared candidate absent from canonical registry.",
                          maturity=route.get("maturity_status"))
        item["observed_refs"]["routes"].append(route_ref)
        if entrypoint:
            _record_reference(repository, item, "implementation", entrypoint)
        for _, key, reference in _iter_explicit_references(route):
            if reference != entrypoint:
                _record_reference(repository, item, _field_for_reference_key(key), reference)
        if route.get("alias_of"):
            item["_alias_targets"].append(str(route["alias_of"]))
        if route.get("duplicate_of"):
            item["_duplicate_targets"].append(str(route["duplicate_of"]))
        for routing_ref, targets in registry_route_refs.items():
            if routing_ref == TH04_SEED_PATHS[5] and any(_normalize(target) == _normalize(str(capability_id)) for target in targets):
                item["_alias_targets"].extend(targets)
        _merge_candidate(records, item)

    skills = seed_data[TH04_SEED_PATHS[6]]
    for skill in skills["skills"]:
        identifier = f"SKILL:{skill['skill_id']}"
        item = _candidate(identifier, "SKILL_CATALOG", TH04_SEED_PATHS[6], object_class="UTILITY",
                          disposition="DEFERRED" if skill.get("non_executable_current") else "CURRENT",
                          reason="Product skill is a supporting artifact; engineering skills are excluded from product capability inventory.")
        if skill.get("path"):
            _record_reference(repository, item, "implementation", str(skill["path"]))
        _merge_candidate(records, item)

    resolved_references = _resolved_reference_records(repository, seed_data)
    for reference_record in resolved_references:
        _add_reachable_policy_or_gate(records, reference_record)

    records = _resolve_identity_collisions(records)
    candidates = [_finalize_candidate(item) for item in records.values()]
    candidates.sort(key=lambda item: (item["canonical_identity"], item["candidate_id"]))
    unresolved = [
        candidate["candidate_id"] for candidate in candidates
        if candidate["registry_state"] in {"CONFLICTING", "UNRESOLVED"}
        or candidate["object_class"] == "UNRESOLVED_CANDIDATE"
        or (candidate["object_class"] == "EXECUTABLE_CAPABILITY" and candidate["owner_observation"].get("status") == "UNRESOLVED")
        or candidate["inconsistencies"]
    ]
    result = "PASS" if not unresolved else "COMPLETED_WITH_FINDINGS"
    universe = _envelope(repository, generated_at=generated_at, source_inputs=source_inputs,
                         limitations=limitations, result=result)
    universe.update({
        "artifact_type": "CAPABILITY_AUDIT_UNIVERSE",
        "discovery_scope_ref": "TH04_capability_discovery_scope.json",
        "resolved_references": resolved_references,
        "candidates": candidates,
        "unresolved_candidates": sorted(set(unresolved)),
    })
    return universe


def build_registry_delta_proposal(universe: dict[str, Any]) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    for candidate in universe["candidates"]:
        operation = "NO_CHANGE"
        if candidate["registry_state"] == "UNREGISTERED" and candidate["object_class"] == "EXECUTABLE_CAPABILITY":
            operation = "ADD"
        elif candidate["disposition"] == "DUPLICATE":
            operation = "MERGE_CANDIDATE"
        elif candidate["disposition"] == "OBSOLETE":
            operation = "DEPRECATE_CANDIDATE"
        operations.append({"candidate_id": candidate["candidate_id"], "operation": operation,
                           "reason": candidate["classification_reason"], "evidence_refs": candidate["evidence_refs"]})
    if any(item["operation"] not in DELTA_OPERATIONS or item["operation"] in FORBIDDEN_DELTA_OPERATIONS for item in operations):
        raise ValueError("TH04 delta contains forbidden operation")
    delta = {key: universe[key] for key in ("schema_version", "plan_id", "mission_id", "repository_revision", "generated_at", "source_inputs", "evidence_refs", "limitations")}
    delta.update({"artifact_type": "CAPABILITY_REGISTRY_DELTA_PROPOSAL", "result": "PROPOSAL_ONLY", "operations": operations,
                  "registry_write_mode": "READ_ONLY", "forbidden_operations": sorted(FORBIDDEN_DELTA_OPERATIONS)})
    return delta


def validate_capability_audit_universe(data: dict[str, Any]) -> list[str]:
    return validate_against_schema(data, "capability_audit_universe")


def validate_registry_delta_against_universe(universe: dict[str, Any], delta: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    universe_ids = {candidate["candidate_id"] for candidate in universe.get("candidates", [])}
    delta_ids = {operation.get("candidate_id") for operation in delta.get("operations", [])}
    if universe_ids != delta_ids:
        violations.append("DELTA_UNIVERSE_CANDIDATE_SET_MISMATCH")
    operations = {operation.get("operation") for operation in delta.get("operations", [])}
    if operations & FORBIDDEN_DELTA_OPERATIONS:
        violations.append("DELTA_FORBIDDEN_OPERATION_PRESENT")
    if delta.get("registry_write_mode") != "READ_ONLY":
        violations.append("DELTA_REGISTRY_NOT_READ_ONLY")
    return violations


def write_th04_artifacts(output_root: str | Path, *, root: str | Path = ".", generated_at: str | None = None) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    scope = build_capability_discovery_scope(root, generated_at=generated_at)
    if scope["result"] != "PASS":
        raise CapabilityAuditInputError("TH04_INVALID_DISCOVERY_SCOPE: " + "; ".join(scope["limitations"]))
    universe = build_capability_audit_universe(root, generated_at=generated_at)
    violations = validate_capability_audit_universe(universe)
    if violations:
        raise ValueError("CAPABILITY_AUDIT_UNIVERSE_INVALID: " + "; ".join(violations))
    delta = build_registry_delta_proposal(universe)
    delta_violations = validate_registry_delta_against_universe(universe, delta)
    if delta_violations:
        raise ValueError("CAPABILITY_DELTA_INVALID: " + "; ".join(delta_violations))
    artifacts = {
        "scope": output / "TH04_capability_discovery_scope.json",
        "universe": output / "TH04_capability_audit_universe.json",
        "delta": output / "TH04_registry_delta_proposal.json",
    }
    for key, data in (("scope", scope), ("universe", universe), ("delta", delta)):
        artifacts[key].write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return artifacts
