from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.core.cross_registry_integrity import audit_cross_registry

ROOT = Path(__file__).resolve().parents[2]


def _fixture(tmp_path: Path) -> Path:
    for name in ("capability_registry.json", "responsibility_registry.json", "agent_prompt_registry.json", "agent_execution_profiles.json", "skill_catalog.json"):
        target = tmp_path / "config" / name; target.parent.mkdir(exist_ok=True); shutil.copy(ROOT / "config" / name, target)
    shutil.copy(ROOT / "config/capability_routing.yaml", tmp_path / "config/capability_routing.yaml")
    shutil.copytree(ROOT / "reports", tmp_path / "reports")
    for path in (
        "src/scripts/channel_intelligence.py",
        "src/scripts/topic_belonging_flow.py",
        "src/scripts/run_b5_i2_semantic_audit.py",
        "schemas/topic_belonging_input.json",
        "schemas/topic_belonging_decision.json",
        "schemas/b5_i2_semantic_sufficiency_audit.json",
        ".agent/skills/skill_auditar_suficiencia_semantica_b5_i2.md",
    ):
        target = tmp_path / path; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / path, target)
    return tmp_path


def test_semantic_implemented_capability_resolves_canonical_links(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    integrity, authority = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    topic = next(item for item in integrity["capabilities"] if item["capability_id"] == "TOPIC_BELONGING_ASSESSMENT")
    assert all(topic["references"][key] == "RESOLVED" for key in ("ROLE", "PROMPT", "PROFILE", "IMPLEMENTATION", "CONTRACT", "ROUTE", "ROUTE_ENTRYPOINT"))
    assert topic["references"]["SKILL"] == "NOT_APPLICABLE"
    assert not any("TOPIC_BELONGING_ASSESSMENT" in finding for finding in integrity["findings"])
    assert next(item for item in authority["authorities"] if item["capability_id"] == "TOPIC_BELONGING_ASSESSMENT")["authority_resolution"] == "RESOLVED"


def test_defined_capability_does_not_require_implemented_semantic_links(tmp_path: Path) -> None:
    integrity, _ = audit_cross_registry(_fixture(tmp_path), "2026-08-11T00:00:00Z")
    deferred = next(item for item in integrity["capabilities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")
    assert deferred["references"]["PROMPT"] == "NOT_APPLICABLE"
    assert deferred["references"]["IMPLEMENTATION"] == "NOT_APPLICABLE"


def test_arbitrary_or_cross_domain_role_never_resolves_authority(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    registry = root / "config/capability_registry.json"
    data = json.loads(registry.read_text(encoding="utf-8"))
    data["capabilities"][0]["assigned_role"] = ["WRITING"]
    registry.write_text(json.dumps(data), encoding="utf-8")
    integrity, authority = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "AUTHORITY_CONTRADICTION:TOPIC_BELONGING_ASSESSMENT" in integrity["findings"]
    assert next(item for item in authority["authorities"] if item["capability_id"] == "TOPIC_BELONGING_ASSESSMENT")["authority_resolution"] == "CONFLICTING"


def test_defined_invented_domain_cannot_resolve_by_text_only(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    registry = root / "config/capability_registry.json"
    data = json.loads(registry.read_text(encoding="utf-8"))
    next(item for item in data["capabilities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")["functional_authority_domain"] = "INVENTED_DOMAIN_X"
    registry.write_text(json.dumps(data), encoding="utf-8")
    integrity, authority = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "CAP_OWNER_UNRESOLVED:STRATEGIC_IDENTITY_CHANGE_ASSESSMENT" in integrity["findings"]
    assert next(item for item in authority["authorities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")["authority_resolution"] == "UNRESOLVED"


def test_defined_capability_with_canonical_role_owner_resolves(tmp_path: Path) -> None:
    integrity, authority = audit_cross_registry(_fixture(tmp_path), "2026-08-11T00:00:00Z")
    item = next(item for item in authority["authorities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")
    assert item["authority_resolution"] == "RESOLVED"
    assert next(item for item in integrity["capabilities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")["authority_resolution"] == "RESOLVED"


def test_semantic_auditor_capability_resolves_canonical_links(tmp_path: Path) -> None:
    integrity, authority = audit_cross_registry(_fixture(tmp_path), "2026-08-11T00:00:00Z")
    auditor = next(item for item in integrity["capabilities"] if item["capability_id"] == "B5_I2_SEMANTIC_AUDITOR")
    assert all(auditor["references"][key] == "RESOLVED" for key in ("ROLE", "PROMPT", "PROFILE", "IMPLEMENTATION", "CONTRACT", "ROUTE", "ROUTE_ENTRYPOINT", "SKILL", "ROUTE_CONTRACT"))
    assert next(item for item in authority["authorities"] if item["capability_id"] == "B5_I2_SEMANTIC_AUDITOR")["authority_resolution"] == "RESOLVED"
    assert not any("B5_I2_SEMANTIC_AUDITOR" in finding for finding in integrity["findings"])


def test_semantic_auditor_fails_when_routing_skill_is_not_canonical(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    routing = root / "config/capability_routing.yaml"
    routing.write_text(routing.read_text(encoding="utf-8").replace("skill_auditar_suficiencia_semantica_b5_i2", "unknown_skill"), encoding="utf-8")
    integrity, _ = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "SKILL_UNRESOLVED:B5_I2_SEMANTIC_AUDITOR" in integrity["findings"]


def test_deterministic_route_does_not_require_semantic_links(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    registry = root / "config/capability_registry.json"
    data = json.loads(registry.read_text(encoding="utf-8"))
    capability = next(item for item in data["capabilities"] if item["capability_id"] == "TOPIC_BELONGING_ASSESSMENT")
    capability.update({"implementation_kind": "DETERMINISTIC", "routing_required": False, "prompt_reference": [], "assigned_role": []})
    registry.write_text(json.dumps(data), encoding="utf-8")
    integrity, _ = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    item = next(item for item in integrity["capabilities"] if item["capability_id"] == "TOPIC_BELONGING_ASSESSMENT")
    assert item["route_type"] == "DETERMINISTIC"
    assert item["references"]["PROMPT"] == "NOT_APPLICABLE"
    assert item["references"]["ROUTE"] == "NOT_APPLICABLE"


def test_semantic_route_entrypoint_must_match_real_implementation(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    routing = root / "config/capability_routing.yaml"
    routing.write_text(routing.read_text(encoding="utf-8").replace("src/scripts/run_b5_i2_semantic_audit.py", "src/scripts/other.py"), encoding="utf-8")
    integrity, _ = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "ROUTE_ENTRYPOINT_UNRESOLVED:B5_I2_SEMANTIC_AUDITOR" in integrity["findings"]


def test_topic_route_entrypoint_must_exist(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    routing = root / "config/capability_routing.yaml"
    routing.write_text(routing.read_text(encoding="utf-8").replace("src/scripts/topic_belonging_flow.py", "src/scripts/missing_topic_flow.py"), encoding="utf-8")
    integrity, _ = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "ROUTE_ENTRYPOINT_UNRESOLVED:TOPIC_BELONGING_ASSESSMENT" in integrity["findings"]

def test_topic_route_invalid_declared_skill_fails(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    routing = root / "config/capability_routing.yaml"
    routing.write_text(routing.read_text(encoding="utf-8").replace("  TOPIC_BELONGING_ASSESSMENT:\n", "  TOPIC_BELONGING_ASSESSMENT:\n    skill_id: unknown_topic_skill\n"), encoding="utf-8")
    integrity, _ = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "SKILL_UNRESOLVED:TOPIC_BELONGING_ASSESSMENT" in integrity["findings"]
