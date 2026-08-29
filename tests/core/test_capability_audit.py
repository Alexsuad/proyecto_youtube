from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.core.capability_audit import (
    DELTA_OPERATIONS,
    FORBIDDEN_DELTA_OPERATIONS,
    TH04_SEED_PATHS,
    CapabilityAuditInputError,
    build_capability_audit_universe,
    build_capability_discovery_scope,
    build_registry_delta_proposal,
    validate_capability_audit_universe,
    validate_registry_delta_against_universe,
    write_th04_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]


def _write_json(root: Path, relative: str, data: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _seed_repository(root: Path) -> None:
    for relative in TH04_SEED_PATHS:
        source = ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    _write_json(root, "config/capability_registry.json", {
        "registry_version": "1.0.0",
        "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "config/capability_routing.yaml",
        "compatibility_tokens": {"maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {}},
        "capabilities": [
            {
                "capability_id": "KNOWN_CAP",
                "domain": "CHANNEL_INTELLIGENCE",
                "functional_authority_domain": "CHANNEL_INTELLIGENCE",
                "purpose": "Fixture capability",
                "functional_requirements": [],
                "implementation_kind": "DEFERRED",
                "maturity_status": "DEFINED",
                "decision_authority": "REVIEWER",
                "routing_ref": "config/capability_routing.yaml",
            },
            {
                "capability_id": "DEFERRED_CAP",
                "domain": "SCRIPT_PRODUCT",
                "functional_authority_domain": "SCRIPT_PRODUCT",
                "purpose": "Fixture deferred capability",
                "functional_requirements": [],
                "implementation_kind": "DEFERRED",
                "maturity_status": "DEFINED",
            },
        ],
    })

    routing = {"capabilities": {
        "known-cap": {
            "entrypoint": "src/known.py",
            "policy_ref": "policies/known_policy.json",
            "gate_ref": "src/scripts/known_gate.py",
            "schema_ref": "schemas/known.json",
            "profile_ref": "config/agent_execution_profiles.json",
            "observed_tests": ["tests/test_known.py"],
        },
        "UNREGISTERED_CAP": {"entrypoint": "src/unregistered.py"},
        "UNRESOLVED_ROUTE": {"schema_ref": "schemas/missing.json"},
        "BROKEN-REF": {"entrypoint": "src/broken.py", "policy_ref": "config/missing_policy.json"},
        "ALIAS-B": {"entrypoint": "src/alias_a.py"},
        "ALIAS_B": {"entrypoint": "src/alias_b.py", "alias_of": "ALIAS-B"},
        "DUP-A": {"entrypoint": "src/duplicate_a.py"},
        "DUP_A": {"entrypoint": "src/duplicate_b.py", "duplicate_of": "DUP-A"},
        "A-B": {"entrypoint": "src/collision_a.py"},
        "A_B": {"entrypoint": "src/collision_b.py"},
    }}
    (root / "config/capability_routing.yaml").write_text(yaml.safe_dump(routing), encoding="utf-8")

    subagent_path = root / "config/subagent_registry.json"
    subagents = json.loads(subagent_path.read_text(encoding="utf-8"))
    subagents["agents"][0]["maturity_status"] = "AGENT_TESTED_IN_ISOLATION"
    subagent_path.write_text(json.dumps(subagents), encoding="utf-8")

    for relative in (
        "src/known.py", "src/unregistered.py", "src/broken.py", "src/alias_a.py", "src/alias_b.py",
        "src/duplicate_a.py", "src/duplicate_b.py", "src/collision_a.py", "src/collision_b.py",
        "src/unrelated.py", "policies/known_policy.json", "src/scripts/known_gate.py",
        "src/scripts/transitive_gate.py", "src/scripts/unreferenced_gate.py",
        "schemas/known.json", "tests/test_known.py", ".agents/skills/unrelated.md",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    _write_json(root, "policies/known_policy.json", {"gate_ref": "src/scripts/transitive_gate.py"})


def _candidate(universe: dict, candidate_id: str) -> dict:
    return next(item for item in universe["candidates"] if item["candidate_id"] == candidate_id)


def test_scope_validates_all_seeds_before_discovery(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    scope = build_capability_discovery_scope(tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert scope["seed_paths"] == list(TH04_SEED_PATHS)
    assert "VALIDATE_SEEDS_BEFORE_DISCOVERY" in scope["rules"]
    assert scope["result"] == "PASS"
    assert scope["seed_validation_errors"] == []


def test_empty_or_invalid_seed_cannot_produce_zero_candidate_pass(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    (tmp_path / "config/agent_prompt_registry.json").write_text("{}", encoding="utf-8")
    scope = build_capability_discovery_scope(tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert scope["result"] == "INVALID"
    assert any("SEED_INVALID:config/agent_prompt_registry.json" in item for item in scope["seed_validation_errors"])
    with pytest.raises(CapabilityAuditInputError, match="TH04_INVALID_SEEDS"):
        build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")


def test_universe_resolves_explicit_references_without_root_scan(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert validate_capability_audit_universe(universe) == []
    known = _candidate(universe, "KNOWN_CAP")
    assert known["object_class"] == "EXECUTABLE_CAPABILITY"
    assert known["registry_state"] == "REGISTERED"
    assert "known-cap" in known["aliases"]
    assert "tests/test_known.py" in known["observed_tests"]
    assert _candidate(universe, "ROLE:CHANNEL_INTELLIGENCE_PRODUCER")["object_class"] == "NON_EXECUTABLE_RESPONSIBILITY"
    assert all(item["object_class"] == "ORCHESTRATION_ONLY" for item in universe["candidates"] if item["candidate_id"].startswith("PROFILE:"))
    assert all("unrelated" not in item["candidate_id"].lower() for item in universe["candidates"])
    resolved = {item["reference"]: item for item in universe["resolved_references"]}
    assert resolved["policies/known_policy.json"]["status"] == "RESOLVED"
    assert resolved["schemas/known.json"]["status"] == "RESOLVED"
    assert resolved["config/missing_policy.json"]["status"] == "UNRESOLVED"


def test_detector_patterns_are_not_treated_as_artifact_references(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    _write_json(tmp_path, "policies/known_policy.json", {
        "gate_ref": "src/scripts/transitive_gate.py",
        "patterns": [{"pattern": "docs/ALCANCE_Y_COORDINACION_EQUIPOS\\.md"}],
    })

    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")

    assert not any("ALCANCE_Y_COORDINACION_EQUIPOS" in item["reference"] for item in universe["resolved_references"])


def test_policy_and_gate_are_reachable_non_capability_classes(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    policy = _candidate(universe, "POLICY:policies/known_policy.json")
    gate = _candidate(universe, "GATE:src/scripts/known_gate.py")
    assert policy["object_class"] == "POLICY"
    assert gate["object_class"] == "GATE"
    assert policy["object_class"] != "EXECUTABLE_CAPABILITY"
    assert gate["object_class"] != "EXECUTABLE_CAPABILITY"


def test_transitive_policy_to_gate_resolution_preserves_provenance_and_avoids_sibling_scan(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    gate = _candidate(universe, "GATE:src/scripts/transitive_gate.py")
    assert gate["object_class"] == "GATE"
    assert gate["registry_state"] == "NOT_OBSERVED"
    hop = next(
        item for item in universe["resolved_references"]
        if item["reference"] == "src/scripts/transitive_gate.py"
    )
    assert hop["source_ref"].startswith("policies/known_policy.json#")
    assert "config/capability_routing.yaml" in hop["provenance_chain"][0]
    assert "policies/known_policy.json" in hop["provenance_chain"]
    assert not any("unreferenced_gate" in item["candidate_id"] for item in universe["candidates"])


def test_identity_alias_duplicate_and_unproven_collision_are_distinct_cases(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    alias = _candidate(universe, "ALIAS-B")
    assert "ALIAS_B" in alias["aliases"]
    assert not any(item["candidate_id"] == "ALIAS_B" for item in universe["candidates"])
    duplicate = _candidate(universe, "DUP_A")
    assert duplicate["disposition"] == "DUPLICATE"
    collision_a = _candidate(universe, "A-B")
    collision_b = _candidate(universe, "A_B")
    assert collision_a["canonical_identity"] == collision_b["canonical_identity"]
    assert collision_a["registry_state"] == "CONFLICTING"
    assert collision_b["registry_state"] == "CONFLICTING"
    assert any("IDENTITY_NORMALIZATION_COLLISION" in item for item in collision_a["inconsistencies"])


def test_broken_reference_is_a_finding_and_not_hidden(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    broken = _candidate(universe, "BROKEN-REF")
    assert "UNRESOLVED_REFERENCE:config/missing_policy.json" in broken["inconsistencies"]
    assert _candidate(universe, "POLICY:config/missing_policy.json")["registry_state"] == "UNRESOLVED"
    assert "BROKEN-REF" in universe["unresolved_candidates"]


def test_noncanonical_maturity_is_not_accepted_as_canonical(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    candidate = _candidate(universe, "SUBAGENT:" + json.loads((tmp_path / "config/subagent_registry.json").read_text())["agents"][0]["agent_id"])
    assert candidate["maturity_observed"] is None
    assert candidate["maturity_observed_raw"] == "AGENT_TESTED_IN_ISOLATION"
    assert "NON_CANONICAL_MATURITY:AGENT_TESTED_IN_ISOLATION" in candidate["inconsistencies"]
    assert validate_capability_audit_universe(universe) == []
    assert candidate["candidate_id"] in universe["unresolved_candidates"]


def test_deferred_and_non_executable_objects_do_not_become_current_capabilities(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert _candidate(universe, "DEFERRED_CAP")["disposition"] == "DEFERRED"
    assert _candidate(universe, "ROLE:CHANNEL_INTELLIGENCE_PRODUCER")["object_class"] == "NON_EXECUTABLE_RESPONSIBILITY"
    assert _candidate(universe, "PROFILE:SCRIPT_PRODUCT_PRODUCER")["object_class"] == "ORCHESTRATION_ONLY"


def test_delta_matches_universe_and_never_writes_registry(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    universe = build_capability_audit_universe(tmp_path, generated_at="2026-08-10T00:00:00Z")
    delta = build_registry_delta_proposal(universe)
    assert validate_registry_delta_against_universe(universe, delta) == []
    assert all(item["operation"] in DELTA_OPERATIONS for item in delta["operations"])
    assert not ({item["operation"] for item in delta["operations"]} & FORBIDDEN_DELTA_OPERATIONS)
    assert delta["registry_write_mode"] == "READ_ONLY"


def test_writer_materializes_three_structured_artifacts(tmp_path: Path) -> None:
    _seed_repository(tmp_path)
    artifacts = write_th04_artifacts(tmp_path / "reports/implementation/plan_004", root=tmp_path, generated_at="2026-08-10T00:00:00Z")
    assert {path.name for path in artifacts.values()} == {
        "TH04_capability_discovery_scope.json", "TH04_capability_audit_universe.json", "TH04_registry_delta_proposal.json",
    }
    universe = json.loads(artifacts["universe"].read_text(encoding="utf-8"))
    assert validate_capability_audit_universe(universe) == []
