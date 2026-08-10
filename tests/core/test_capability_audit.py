from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.core.capability_audit import (
    DELTA_OPERATIONS,
    FORBIDDEN_DELTA_OPERATIONS,
    TH04_SEED_PATHS,
    build_capability_audit_universe,
    build_capability_discovery_scope,
    build_registry_delta_proposal,
    validate_capability_audit_universe,
    write_th04_artifacts,
)


def _write_json(root: Path, relative: str, data: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _seed_repository(root: Path) -> None:
    _write_json(root, "config/capability_registry.json", {
        "capabilities": [{
            "capability_id": "KNOWN_CAP", "implementation_kind": "SEMANTIC", "maturity_status": "IMPLEMENTED",
            "functional_authority_domain": "CHANNEL_INTELLIGENCE", "decision_authority": "REVIEWER",
            "assigned_role": ["ROLE_A"], "prompt_reference": ["PROMPT_A"],
            "profile_refs": ["config/agent_execution_profiles.json"], "execution_profile_refs": [],
            "contract_refs": ["schemas/contract.json"], "implementation_refs": ["src/known.py"],
            "routing_ref": "config/capability_routing.yaml",
        }, {
            "capability_id": "DEFERRED_CAP", "implementation_kind": "DEFERRED", "maturity_status": "DEFINED",
            "functional_authority_domain": None, "decision_authority": None,
        }, {
            "capability_id": "MISSING_IMPL", "implementation_kind": "DETERMINISTIC", "maturity_status": "IMPLEMENTED",
            "functional_authority_domain": "INFRASTRUCTURE_GOVERNANCE", "decision_authority": "OWNER",
            "implementation_refs": ["src/missing.py"],
        }],
    })
    _write_json(root, "config/responsibility_registry.json", {"responsibilities": [{"role_id": "ROLE_A", "functional_owner": "CHANNEL_INTELLIGENCE"}]})
    _write_json(root, "config/agent_prompt_registry.json", {"prompts": [{"prompt_id": "PROMPT_A"}]})
    _write_json(root, "config/agent_execution_profiles.json", {"role_defaults": {"ROLE_A": "ANY"}, "profiles": []})
    _write_json(root, "config/subagent_registry.json", {"agents": [{"agent_id": "AGENT_A"}]})
    routing = {"capabilities": {
        "known-cap": {"entrypoint": "src/known.py"},
        "UNREGISTERED_CAP": {"entrypoint": "src/unregistered.py"},
        "UNRESOLVED_ROUTE": {"output_schema": "missing"},
    }}
    (root / "config/capability_routing.yaml").write_text(yaml.safe_dump(routing), encoding="utf-8")
    _write_json(root, "config/skill_catalog.json", {"skills": [{"skill_id": "SKILL_A", "path": ".agent/skills/skill_a.md"}]})
    for relative in ("src/known.py", "src/unregistered.py", "src/unrelated.py", "schemas/contract.json", ".agent/skills/skill_a.md"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")


def _candidate(universe: dict, candidate_id: str) -> dict:
    return next(item for item in universe["candidates"] if item["candidate_id"] == candidate_id)


def test_scope_is_closed_to_canonical_seeds(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    scope = build_capability_discovery_scope(tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert scope["seed_paths"] == list(TH04_SEED_PATHS)
    assert "NO_RECURSIVE_ROOT_SCAN" in scope["rules"]
    assert scope["result"] == "PASS"


def test_universe_classifies_candidates_without_scanning_unreferenced_source(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert validate_capability_audit_universe(universe) == []
    known = _candidate(universe, "KNOWN_CAP")
    assert known["object_class"] == "EXECUTABLE_CAPABILITY"
    assert known["registry_state"] == "REGISTERED"
    assert known["owner_observation"]["status"] == "RESOLVED_FROM_CANONICAL_FIELD"
    assert "known-cap" in known["aliases"]
    assert _candidate(universe, "ROLE:ROLE_A")["object_class"] == "NON_EXECUTABLE_RESPONSIBILITY"
    assert _candidate(universe, "PROMPT:PROMPT_A")["object_class"] == "UTILITY"
    assert all("unrelated" not in item["candidate_id"].lower() for item in universe["candidates"])


def test_unregistered_and_incomplete_candidates_become_findings_without_registry_mutation(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    unregistered = _candidate(universe, "UNREGISTERED_CAP")
    assert unregistered["object_class"] == "EXECUTABLE_CAPABILITY"
    assert unregistered["registry_state"] == "UNREGISTERED"
    assert _candidate(universe, "DEFERRED_CAP")["disposition"] == "DEFERRED"
    missing = _candidate(universe, "MISSING_IMPL")
    assert "UNRESOLVED_REFERENCE:src/missing.py" in missing["inconsistencies"]
    assert _candidate(universe, "UNRESOLVED_ROUTE")["object_class"] == "UNRESOLVED_CANDIDATE"
    delta = build_registry_delta_proposal(universe)
    proposal = next(item for item in delta["operations"] if item["candidate_id"] == "UNREGISTERED_CAP")
    assert proposal["operation"] == "ADD"
    assert all(item["operation"] in DELTA_OPERATIONS for item in delta["operations"])
    assert not ({item["operation"] for item in delta["operations"]} & FORBIDDEN_DELTA_OPERATIONS)
    assert delta["registry_write_mode"] == "READ_ONLY"


def test_writer_materializes_only_structured_th04_evidence(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    artifacts = write_th04_artifacts(tmp_path / "reports/implementation/plan_004", root=tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert {path.name for path in artifacts.values()} == {
        "TH04_capability_discovery_scope.json", "TH04_capability_audit_universe.json", "TH04_registry_delta_proposal.json",
    }
    universe = json.loads(artifacts["universe"].read_text(encoding="utf-8"))
    assert validate_capability_audit_universe(universe) == []
