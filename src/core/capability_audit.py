"""Deterministic TH-04 capability inventory derived from canonical seeds."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

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
DELTA_OPERATIONS = {"ADD", "CORRECT_METADATA", "ADD_ALIAS", "MERGE_CANDIDATE", "DEPRECATE_CANDIDATE", "NO_CHANGE"}
FORBIDDEN_DELTA_OPERATIONS = {
    "ACTIVATE", "FUNCTIONALLY_APPROVE", "PROMOTE_TO_DEMONSTRATED", "CHANGE_FUNCTIONAL_AUTHORITY",
}


def _normalize(value: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in value.upper())
    return "_".join(part for part in normalized.split("_") if part)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _safe_reference(root: Path, reference: str) -> str | None:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return _relative(root, resolved) if resolved.is_file() else None


def _load_json(path: Path) -> dict[str, Any]:
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


def build_capability_discovery_scope(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    source_inputs, limitations = _source_inputs(repository)
    scope = _envelope(repository, generated_at=generated_at, source_inputs=source_inputs, limitations=limitations,
                      result="PASS" if not limitations else "LIMITATION")
    scope.update({
        "artifact_type": "CAPABILITY_DISCOVERY_SCOPE",
        "seed_paths": list(TH04_SEED_PATHS),
        "resolvable_roots": list(RESOLVABLE_ROOTS),
        "rules": [
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
               reason: str, registry_presence: bool = False) -> dict[str, Any]:
    return {
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
        "maturity_observed": None,
        "observed_refs": {"roles": [], "prompts": [], "profiles": [], "routes": [], "contracts": [], "implementation": []},
        "resolved_artifacts": [],
        "inconsistencies": [],
        "evidence_refs": [source_ref],
    }


def _merge_candidate(records: dict[str, dict[str, Any]], item: dict[str, Any]) -> dict[str, Any]:
    key = item["canonical_identity"]
    existing = records.get(key)
    if existing is None:
        records[key] = item
        return item
    for field in ("aliases", "source_refs", "evidence_refs", "resolved_artifacts", "inconsistencies"):
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
    return existing


def _record_reference(root: Path, candidate: dict[str, Any], field: str, reference: str) -> None:
    candidate["observed_refs"][field].append(reference)
    candidate["evidence_refs"].append(reference)
    resolved = _safe_reference(root, reference)
    if resolved:
        candidate["resolved_artifacts"].append(resolved)
    elif "/" in reference or "\\" in reference or reference.endswith(".json") or reference.endswith(".py"):
        candidate["inconsistencies"].append(f"UNRESOLVED_REFERENCE:{reference}")


def build_capability_audit_universe(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    scope = build_capability_discovery_scope(repository, generated_at=generated_at)
    limitations = list(scope["limitations"])
    records: dict[str, dict[str, Any]] = {}

    registry_path = repository / TH04_SEED_PATHS[0]
    registry = _load_json(registry_path) if registry_path.is_file() else {}
    for capability in registry.get("capabilities", []):
        identifier = str(capability.get("capability_id", "UNRESOLVED_CAPABILITY"))
        deferred = capability.get("implementation_kind") == "DEFERRED" or capability.get("maturity_status") == "DEFINED"
        item = _candidate(
            identifier, "CAPABILITY_REGISTRY", TH04_SEED_PATHS[0], object_class="EXECUTABLE_CAPABILITY",
            disposition="DEFERRED" if deferred else "CURRENT", registry_state="REGISTERED",
            reason="Canonical capability registry entry.", registry_presence=True,
        )
        authority_domain = capability.get("functional_authority_domain")
        decision_authority = capability.get("decision_authority")
        item["owner_observation"] = {
            "status": "RESOLVED_FROM_CANONICAL_FIELD" if authority_domain and decision_authority else "UNRESOLVED",
            "functional_authority_domain": authority_domain,
            "decision_authority": decision_authority,
        }
        item["maturity_observed"] = capability.get("maturity_status")
        for field, key in (("assigned_role", "roles"), ("prompt_reference", "prompts"),
                           ("profile_refs", "profiles"), ("execution_profile_refs", "profiles"),
                           ("contract_refs", "contracts"), ("implementation_refs", "implementation")):
            for reference in capability.get(field, []) or []:
                _record_reference(repository, item, key, str(reference))
        if capability.get("routing_ref"):
            _record_reference(repository, item, "routes", str(capability["routing_ref"]))
        if capability.get("maturity_status") in {"IMPLEMENTED", "DEMONSTRATED"} and not item["observed_refs"]["implementation"]:
            item["inconsistencies"].append("CAP_IMPLEMENTATION_REF_MISSING")
        _merge_candidate(records, item)

    responsibilities_path = repository / TH04_SEED_PATHS[1]
    responsibilities = _load_json(responsibilities_path) if responsibilities_path.is_file() else {}
    for responsibility in responsibilities.get("responsibilities", []):
        identifier = f"ROLE:{responsibility.get('role_id', 'UNRESOLVED')}"
        item = _candidate(identifier, "RESPONSIBILITY_REGISTRY", TH04_SEED_PATHS[1],
                          object_class="NON_EXECUTABLE_RESPONSIBILITY",
                          reason="Registered responsibility is not a capability by itself.")
        item["owner_observation"] = {"status": "RESOLVED_FROM_CANONICAL_FIELD" if responsibility.get("functional_owner") else "UNRESOLVED",
                                     "functional_authority_domain": responsibility.get("functional_owner")}
        _merge_candidate(records, item)

    prompts_path = repository / TH04_SEED_PATHS[2]
    prompts = _load_json(prompts_path) if prompts_path.is_file() else {}
    for prompt in prompts.get("prompts", []):
        identifier = f"PROMPT:{prompt.get('prompt_id', 'UNRESOLVED')}"
        _merge_candidate(records, _candidate(identifier, "PROMPT_REGISTRY", TH04_SEED_PATHS[2], object_class="UTILITY",
                                             reason="Prompt is supporting mechanism, not a product capability."))

    profiles_path = repository / TH04_SEED_PATHS[3]
    profiles = _load_json(profiles_path) if profiles_path.is_file() else {}
    profile_ids = list(profiles.get("role_defaults", {}).keys()) + [entry.get("profile_id") for entry in profiles.get("profiles", [])]
    for profile_id in filter(None, profile_ids):
        identifier = f"PROFILE:{profile_id}"
        _merge_candidate(records, _candidate(identifier, "EXECUTION_PROFILE_REGISTRY", TH04_SEED_PATHS[3], object_class="ORCHESTRATION_ONLY",
                                             reason="Execution profile is routing configuration, not a product capability."))

    subagents_path = repository / TH04_SEED_PATHS[4]
    subagents = _load_json(subagents_path) if subagents_path.is_file() else {}
    for agent in subagents.get("agents", []):
        identifier = f"SUBAGENT:{agent.get('agent_id', 'UNRESOLVED')}"
        _merge_candidate(records, _candidate(identifier, "SUBAGENT_REGISTRY", TH04_SEED_PATHS[4], object_class="ORCHESTRATION_ONLY",
                                             reason="Subagent record is an execution participant, not a product capability."))

    routing_path = repository / TH04_SEED_PATHS[5]
    routing = yaml.safe_load(routing_path.read_text(encoding="utf-8")) if routing_path.is_file() else {}
    for capability_id, route in (routing.get("capabilities", {}) or {}).items():
        route = route if isinstance(route, dict) else {}
        route_ref = f"{TH04_SEED_PATHS[5]}#{capability_id}"
        entrypoint = str(route.get("entrypoint", ""))
        object_class = "EXECUTABLE_CAPABILITY" if entrypoint and _safe_reference(repository, entrypoint) else "UNRESOLVED_CANDIDATE"
        item = _candidate(str(capability_id), "CAPABILITY_ROUTING", route_ref, object_class=object_class,
                          registry_state="UNREGISTERED", reason="Routing-declared candidate absent from canonical registry.")
        item["observed_refs"]["routes"].append(route_ref)
        if entrypoint:
            _record_reference(repository, item, "implementation", entrypoint)
        _merge_candidate(records, item)

    skills_path = repository / TH04_SEED_PATHS[6]
    skills = _load_json(skills_path) if skills_path.is_file() else {}
    for skill in skills.get("skills", []):
        identifier = f"SKILL:{skill.get('skill_id', 'UNRESOLVED')}"
        item = _candidate(identifier, "SKILL_CATALOG", TH04_SEED_PATHS[6], object_class="UTILITY",
                          disposition="DEFERRED" if skill.get("non_executable_current") else "CURRENT",
                          reason="Product skill is a supporting artifact; engineering skills are excluded from product capability inventory.")
        if skill.get("path"):
            _record_reference(repository, item, "implementation", str(skill["path"]))
        _merge_candidate(records, item)

    candidates = sorted(records.values(), key=lambda item: item["canonical_identity"])
    for candidate in candidates:
        for field in ("aliases", "source_refs", "evidence_refs", "resolved_artifacts", "inconsistencies"):
            candidate[field] = sorted(set(candidate[field]))
        for field in candidate["observed_refs"]:
            candidate["observed_refs"][field] = sorted(set(candidate["observed_refs"][field]))
        if candidate["object_class"] not in OBJECT_CLASSES or candidate["disposition"] not in DISPOSITIONS or candidate["registry_state"] not in REGISTRY_STATES:
            raise ValueError(f"TH04 classification contract invalid for {candidate['candidate_id']}")

    unresolved = [
        candidate["candidate_id"] for candidate in candidates
        if candidate["object_class"] == "UNRESOLVED_CANDIDATE"
        or (candidate["object_class"] == "EXECUTABLE_CAPABILITY" and candidate["owner_observation"].get("status") == "UNRESOLVED")
    ]
    result = "PASS" if not limitations and not unresolved else "COMPLETED_WITH_FINDINGS"
    universe = _envelope(repository, generated_at=generated_at, source_inputs=scope["source_inputs"], limitations=limitations, result=result)
    universe.update({"artifact_type": "CAPABILITY_AUDIT_UNIVERSE", "discovery_scope_ref": "TH04_capability_discovery_scope.json",
                     "candidates": candidates, "unresolved_candidates": sorted(set(unresolved))})
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


def write_th04_artifacts(output_root: str | Path, *, root: str | Path = ".", generated_at: str | None = None) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    scope = build_capability_discovery_scope(root, generated_at=generated_at)
    universe = build_capability_audit_universe(root, generated_at=generated_at)
    violations = validate_capability_audit_universe(universe)
    if violations:
        raise ValueError("CAPABILITY_AUDIT_UNIVERSE_INVALID: " + "; ".join(violations))
    delta = build_registry_delta_proposal(universe)
    artifacts = {
        "scope": output / "TH04_capability_discovery_scope.json",
        "universe": output / "TH04_capability_audit_universe.json",
        "delta": output / "TH04_registry_delta_proposal.json",
    }
    for key, data in (("scope", scope), ("universe", universe), ("delta", delta)):
        artifacts[key].write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return artifacts
