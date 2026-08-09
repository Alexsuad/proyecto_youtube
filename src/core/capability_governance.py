"""Maturity-aware cross-registry capability governance."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.core.contract_validation import validate_against_schema

CANONICAL_CAPABILITY_REGISTRY = Path("config/capability_registry.json")
ROOT = Path(__file__).resolve().parents[2]
DOMAINS = {"CHANNEL_INTELLIGENCE", "SCRIPT_PRODUCT", "YOUTUBE_ADAPTATION", "INFRASTRUCTURE_GOVERNANCE"}
MATURITY = {"DEFINED", "REGISTERED", "IMPLEMENTED", "DEMONSTRATED"}
AVAILABILITY = {"NON_EXECUTABLE_CURRENT", "READY_NOT_AUTHORIZED", "ACTIVE", "SUSPENDED", "DEPRECATED"}
SEMANTIC = "SEMANTIC"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repository_root(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    return resolved.parent.parent if resolved.parent.name == "config" else resolved.parent


def _safe_ref(root: Path, reference: str) -> bool:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    try:
        return (root / candidate).resolve(strict=True).is_file()
    except OSError:
        return False


def _ids(data: dict[str, Any], collection: str, key: str) -> set[str]:
    return {str(item.get(key)) for item in data.get(collection, []) if isinstance(item, dict) and item.get(key)}


def _registry_files(root: Path) -> dict[str, dict[str, Any]]:
    def read(name: str) -> dict[str, Any]:
        path = root / "config" / name
        return _load(path) if path.is_file() else {}
    return {
        "responsibilities": read("responsibility_registry.json"),
        "prompts": read("agent_prompt_registry.json"),
        "profiles": read("agent_execution_profiles.json"),
        "runtime": read("ai_runtime.example.json"),
    }


def _route_for(root: Path, capability_id: str, routing_ref: str | None) -> tuple[dict[str, Any] | None, str | None]:
    if not routing_ref or not _safe_ref(root, routing_ref):
        return None, "CAP_ROUTING_REF_MISSING"
    try:
        routing = yaml.safe_load((root / routing_ref).read_text(encoding="utf-8")) or {}
        route = routing.get("capabilities", {}).get(capability_id)
        if not isinstance(route, dict):
            return None, "CAP_ROUTING_ENTRY_MISSING"
        entrypoint = route.get("entrypoint")
        if entrypoint and not _safe_ref(root, str(entrypoint)):
            return None, "CAP_ROUTING_ENTRYPOINT_MISSING"
        return route, None
    except (OSError, yaml.YAMLError, AttributeError):
        return None, "CAP_ROUTING_INVALID"


def _validate_ref_list(root: Path, capability_id: str, refs: Any, code: str, *, path_like_only: bool = False) -> list[str]:
    violations: list[str] = []
    for ref in refs if isinstance(refs, list) else []:
        value = str(ref)
        if path_like_only and "/" not in value and chr(92) not in value and "." not in value:
            continue
        if not _safe_ref(root, value):
            violations.append(f"{code}:{capability_id}:{value}")
    return violations


def validate_capability_registry(path: str | Path = CANONICAL_CAPABILITY_REGISTRY) -> list[str]:
    root_path = Path(path)
    data = _load(root_path)
    violations = validate_against_schema(data, "capability_registry")
    repository_root = _repository_root(root_path)
    registries = _registry_files(repository_root)
    responsibility_roles = _ids(registries["responsibilities"], "responsibilities", "role_id")
    prompt_ids = _ids(registries["prompts"], "prompts", "prompt_id")
    profile_ids = set(registries["profiles"].get("role_defaults", {})) | _ids(registries["profiles"], "profiles", "profile_id")

    for capability in data.get("capabilities", []):
        capability_id = str(capability.get("capability_id", "UNSPECIFIED"))
        domain = capability.get("domain")
        authority = capability.get("functional_authority_domain")
        maturity = capability.get("maturity_status")
        implementation_kind = capability.get("implementation_kind")
        availability = capability.get("availability_status")

        if domain not in DOMAINS or authority not in DOMAINS:
            violations.append(f"CAP_OWNER_UNRESOLVED:{capability_id}")
        if maturity not in MATURITY:
            violations.append(f"CAP_MATURITY_INVALID:{capability_id}")
        if availability is not None and availability not in AVAILABILITY:
            violations.append(f"CAP_AVAILABILITY_INVALID:{capability_id}")
        violations.extend(_validate_ref_list(repository_root, capability_id, capability.get("functional_requirements"), "CAP_REQUIREMENT_REF_UNRESOLVED", path_like_only=True))

        if maturity in {"IMPLEMENTED", "DEMONSTRATED"} and not capability.get("implementation_refs"):
            violations.append(f"CAP_IMPLEMENTATION_REF_MISSING:{capability_id}")
        violations.extend(_validate_ref_list(repository_root, capability_id, capability.get("implementation_refs"), "CAP_IMPLEMENTATION_REF_MISSING"))
        violations.extend(_validate_ref_list(repository_root, capability_id, capability.get("contract_refs"), "CAP_REQUIREMENT_REF_UNRESOLVED"))
        violations.extend(_validate_ref_list(repository_root, capability_id, capability.get("profile_refs"), "CAP_REQUIREMENT_REF_UNRESOLVED"))
        violations.extend(_validate_ref_list(repository_root, capability_id, capability.get("execution_profile_refs"), "CAP_EXECUTION_PROFILE_MISSING"))

        if implementation_kind == SEMANTIC and maturity in {"IMPLEMENTED", "DEMONSTRATED"}:
            roles = capability.get("assigned_role", [])
            prompts = capability.get("prompt_reference", [])
            profiles = capability.get("execution_profile_refs", [])
            if not roles:
                violations.append(f"CAP_ROLE_REQUIRED:{capability_id}")
            if not prompts:
                violations.append(f"CAP_PROMPT_REQUIRED:{capability_id}")
            if not profiles:
                violations.append(f"CAP_EXECUTION_PROFILE_REQUIRED:{capability_id}")
            for role in roles:
                if role not in responsibility_roles:
                    violations.append(f"CAP_ROLE_UNRESOLVED:{capability_id}:{role}")
            for prompt in prompts:
                if prompt not in prompt_ids:
                    violations.append(f"CAP_PROMPT_UNRESOLVED:{capability_id}:{prompt}")
            for profile in profiles:
                if profile not in profile_ids and profile != "ANY":
                    # A path reference is validated above; role-default profiles are also accepted.
                    if not _safe_ref(repository_root, str(profile)):
                        violations.append(f"CAP_EXECUTION_PROFILE_UNRESOLVED:{capability_id}:{profile}")

        route, route_error = _route_for(repository_root, capability_id, capability.get("routing_ref")) if capability.get("routing_required") else (None, None)
        if capability.get("routing_required") and route_error:
            violations.append(f"{route_error}:{capability_id}")

        assurance = capability.get("assurance", {})
        if assurance.get("functional_approval") == "APPROVED":
            approval_ref = capability.get("functional_approval_ref")
            if not approval_ref or not _safe_ref(repository_root, str(approval_ref)):
                violations.append(f"CAP_FUNCTIONAL_APPROVAL_AUTHORITY_INVALID:{capability_id}")
        if assurance.get("functional_approval") == "APPROVED" and assurance.get("technical") == "FAIL":
            violations.append(f"CAP_AVAILABILITY_CONTRADICTION:{capability_id}")

        if maturity == "DEMONSTRATED":
            if not capability.get("evidence_refs") or not capability.get("execution_evidence_refs"):
                violations.append(f"CAP_MATURITY_EVIDENCE_MISMATCH:{capability_id}")

        if availability in {"READY_NOT_AUTHORIZED", "ACTIVE"}:
            evidence = capability.get("executability_evidence", {})
            required = {"contracts_resolvable", "implementation_present", "dependencies_satisfied"}
            if implementation_kind == SEMANTIC:
                required.update({"roles_resolvable", "prompts_resolvable", "execution_profiles_resolvable"})
            if capability.get("routing_required"):
                required.add("routing_resolvable")
            if "context_resolvable" in evidence:
                required.add("context_resolvable")
            if any(evidence.get(key) is not True for key in required):
                violations.append(f"CAP_AVAILABILITY_NOT_EXECUTABLE:{capability_id}")
        if availability == "ACTIVE" and maturity != "DEMONSTRATED":
            violations.append(f"CAP_AVAILABILITY_CONTRADICTION:{capability_id}")

    return sorted(set(violations))


def find_executable_capabilities_outside_registry(
    registry_path: str | Path,
    executable_registry_paths: list[str | Path],
) -> list[str]:
    known = {item.get("capability_id") for item in _load(Path(registry_path)).get("capabilities", [])}
    findings: list[str] = []
    for path in executable_registry_paths:
        data = _load(Path(path))
        for item in data.get("capabilities", []):
            identifier = item.get("capability_id")
            if identifier and identifier not in known:
                findings.append(f"CAPABILITY_OUTSIDE_CANONICAL_REGISTRY:{identifier}")
    return sorted(set(findings))