"""Deterministic TH-05 cross-registry and authority audit."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_STATES = {"RESOLVED", "UNRESOLVED", "CONFLICTING"}
RESOLUTION_STATES = {"RESOLVED", "MISSING", "NOT_APPLICABLE", "UNRESOLVED", "CONFLICTING"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNRESOLVED"


def _safe(root: Path, reference: str) -> bool:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    return (root / candidate).is_file()


def _route_type(capability: dict[str, Any], route: Any) -> str:
    """Resolve the existing route classification without imposing semantic links on other routes."""
    if isinstance(route, dict) and route.get("route_type"):
        return str(route["route_type"]).upper()
    declared = str(capability.get("implementation_kind") or "DEFERRED").upper()
    routed = str(route.get("route_type") or "").upper() if isinstance(route, dict) else ""
    return declared if routed and routed != declared else (routed or declared)


def _envelope(root: Path, artifact_type: str, generated_at: str | None = None) -> dict[str, Any]:
    sources = ["config/capability_registry.json", "config/responsibility_registry.json", "config/agent_prompt_registry.json", "config/agent_execution_profiles.json", "config/capability_routing.yaml", "config/skill_catalog.json", "reports/implementation/plan_004/TH04_capability_audit_universe.json", "src/core/cross_registry_integrity.py"]
    return {"schema_version": "1.0.0", "plan_id": "PLAN_004", "mission_id": "TH-05", "repository_revision": _revision(root), "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "source_inputs": [{"path": p, "sha256": _sha(root / p)} for p in sources if (root / p).is_file()], "evidence_refs": sources, "limitations": [], "result": "PASS", "artifact_type": artifact_type}


def audit_cross_registry(root: Path = ROOT, generated_at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    caps = _load(root / "config/capability_registry.json")["capabilities"]
    roles = {x["role_id"]: x for x in _load(root / "config/responsibility_registry.json")["responsibilities"]}
    prompts = {x["prompt_id"] for x in _load(root / "config/agent_prompt_registry.json")["prompts"]}
    profiles = _load(root / "config/agent_execution_profiles.json")
    skills = {item.get("skill_id"): item for item in _load(root / "config/skill_catalog.json").get("skills", []) if isinstance(item, dict)}
    routes = yaml.safe_load((root / "config/capability_routing.yaml").read_text(encoding="utf-8")) or {}
    canonical_capability_ids = {str(cap["capability_id"]) for cap in caps}
    declared_routes = routes.get("capabilities", {}) if isinstance(routes.get("capabilities", {}), dict) else {}
    canonical_owners = {str(role.get("functional_owner")) for role in roles.values() if role.get("functional_owner")}
    records, authorities, findings = [], [], []
    for route_id in declared_routes:
        if str(route_id) not in canonical_capability_ids:
            findings.append(f"ROUTE_UNRESOLVED_STOP_LOCAL:{route_id}")
    for cap in caps:
        cid, maturity, kind = cap["capability_id"], cap.get("maturity_status"), cap.get("implementation_kind")
        implemented = maturity in {"IMPLEMENTED", "DEMONSTRATED"}
        route = routes.get("capabilities", {}).get(cid)
        route_type = _route_type(cap, route)
        if isinstance(route, dict) and route.get("route_type") and str(route.get("route_type")).upper() != str(kind or "DEFERRED").upper():
            findings.append(f"ROUTE_TYPE_CONTRADICTION:{cid}")
        semantic = route_type == "SEMANTIC" and implemented
        deterministic = route_type == "DETERMINISTIC" and implemented
        route_required = bool(cap.get("routing_required")) and route_type != "DEFERRED"
        checks: dict[str, str] = {}
        def check(name: str, required: bool, values: list[str], known: set[str] | None = None, paths: bool = False) -> None:
            if not required: checks[name] = "NOT_APPLICABLE"; return
            if not values: checks[name] = "MISSING"; findings.append(f"{name}_UNRESOLVED:{cid}"); return
            valid = all((_safe(root, v) if paths else v in (known or set())) for v in values)
            checks[name] = "RESOLVED" if valid else "UNRESOLVED"
            if not valid: findings.append(f"{name}_UNRESOLVED:{cid}")
        check("ROLE", semantic, list(cap.get("assigned_role", [])), set(roles))
        check("PROMPT", semantic, list(cap.get("prompt_reference", [])), prompts)
        check("PROFILE", semantic, list(cap.get("execution_profile_refs", [])), {"config/agent_execution_profiles.json"}, True)
        check("IMPLEMENTATION", implemented, list(cap.get("implementation_refs", [])), paths=True)
        check("CONTRACT", deterministic or implemented, list(cap.get("contract_refs", [])), paths=True)
        checks["ROUTE"] = "RESOLVED" if route_required and isinstance(route, dict) else ("MISSING" if route_required else "NOT_APPLICABLE")
        if checks["ROUTE"] == "MISSING":
            findings.append(f"ROUTE_UNRESOLVED:{cid}")
        if isinstance(route, dict) and route.get("entrypoint"):
            entrypoint = str(route.get("entrypoint"))
            implementation_refs = {str(item) for item in cap.get("implementation_refs", [])}
            entrypoint_valid = _safe(root, entrypoint) and entrypoint in implementation_refs
            checks["ROUTE_ENTRYPOINT"] = "RESOLVED" if entrypoint_valid else "UNRESOLVED"
            if not entrypoint_valid:
                findings.append(f"ROUTE_ENTRYPOINT_UNRESOLVED:{cid}")
        else:
            checks["ROUTE_ENTRYPOINT"] = "NOT_APPLICABLE"
        if semantic and isinstance(route, dict):
            route_skill_id = str(route.get("skill_id") or "")
            if route_skill_id:
                skill = skills.get(route_skill_id)
                skill_valid = bool(skill) and str(skill.get("canonical_owner") or "") == cid and _safe(root, str(skill.get("path") or ""))
                checks["SKILL"] = "RESOLVED" if skill_valid else "UNRESOLVED"
                if not skill_valid:
                    findings.append(f"SKILL_UNRESOLVED:{cid}")
            else:
                checks["SKILL"] = "NOT_APPLICABLE"
            expected_schema = str(cap.get("output_contract") or "").rsplit("/", 1)[-1].removesuffix(".json")
            route_contract_valid = str(route.get("output_schema") or "") == expected_schema
            checks["ROUTE_CONTRACT"] = "RESOLVED" if route_contract_valid else "UNRESOLVED"
            if not route_contract_valid:
                findings.append(f"ROUTE_CONTRACT_UNRESOLVED:{cid}")
        elif semantic:
            checks["SKILL"] = "NOT_APPLICABLE"
            checks["ROUTE_CONTRACT"] = "UNRESOLVED"
        authority_domain = cap.get("functional_authority_domain")
        role_owners = {roles[r].get("functional_owner") for r in cap.get("assigned_role", []) if r in roles}
        assigned_roles = list(cap.get("assigned_role", []))
        unknown_roles = [role for role in assigned_roles if role not in roles]
        if not authority_domain or authority_domain not in canonical_owners or not assigned_roles or unknown_roles:
            authority_state = "UNRESOLVED"
            findings.append(f"CAP_OWNER_UNRESOLVED:{cid}")
        elif len(role_owners) != 1 or next(iter(role_owners)) != authority_domain:
            authority_state = "CONFLICTING"
            findings.append(f"AUTHORITY_CONTRADICTION:{cid}")
        else:
            authority_state = "RESOLVED"
        authorities.append({"capability_id": cid, "functional_authority_domain": authority_domain, "decision_authority": cap.get("decision_authority"), "authority_resolution": authority_state, "evidence_refs": ["config/capability_registry.json", "config/responsibility_registry.json"]})
        records.append({"capability_id": cid, "maturity_status": maturity, "implementation_kind": kind, "route_type": route_type, "references": checks, "authority_resolution": authority_state, "routing_is_execution_only": True})
    integrity = _envelope(root, "CROSS_REGISTRY_INTEGRITY", generated_at); integrity.update({"capabilities": records, "findings": sorted(set(findings))})
    authority = _envelope(root, "AUTHORITY_RESOLUTION", generated_at); authority.update({"authorities": authorities, "findings": sorted(set(findings))})
    if findings: integrity["result"] = authority["result"] = "COMPLETED_WITH_FINDINGS"
    return integrity, authority


def write_th05_artifacts(root: Path = ROOT, generated_at: str | None = None) -> tuple[Path, Path]:
    integrity, authority = audit_cross_registry(root, generated_at)
    output = root / "reports/implementation/plan_004"; output.mkdir(parents=True, exist_ok=True)
    first, second = output / "TH05_cross_registry_integrity.json", output / "TH05_authority_resolution.json"
    first.write_text(json.dumps(integrity, indent=2) + "\n", encoding="utf-8")
    second.write_text(json.dumps(authority, indent=2) + "\n", encoding="utf-8")
    return first, second
