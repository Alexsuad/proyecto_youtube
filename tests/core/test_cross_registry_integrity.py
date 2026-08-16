from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.core.cross_registry_integrity import audit_cross_registry

ROOT = Path(__file__).resolve().parents[2]


def _fixture(tmp_path: Path) -> Path:
    for name in ("capability_registry.json", "responsibility_registry.json", "agent_prompt_registry.json", "agent_execution_profiles.json"):
        target = tmp_path / "config" / name; target.parent.mkdir(exist_ok=True); shutil.copy(ROOT / "config" / name, target)
    shutil.copy(ROOT / "config/capability_routing.yaml", tmp_path / "config/capability_routing.yaml")
    shutil.copytree(ROOT / "reports", tmp_path / "reports")
    for path in ("src/scripts/channel_intelligence.py", "schemas/topic_belonging_input.json", "schemas/topic_belonging_decision.json"):
        target = tmp_path / path; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / path, target)
    return tmp_path


def test_semantic_implemented_capability_resolves_canonical_links(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    integrity, authority = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    topic = next(item for item in integrity["capabilities"] if item["capability_id"] == "TOPIC_BELONGING_ASSESSMENT")
    assert all(topic["references"][key] == "RESOLVED" for key in ("ROLE", "PROMPT", "PROFILE", "IMPLEMENTATION", "CONTRACT", "ROUTE"))
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
    data["capabilities"][1]["functional_authority_domain"] = "INVENTED_DOMAIN_X"
    registry.write_text(json.dumps(data), encoding="utf-8")
    integrity, authority = audit_cross_registry(root, "2026-08-11T00:00:00Z")
    assert "CAP_OWNER_UNRESOLVED:STRATEGIC_IDENTITY_CHANGE_ASSESSMENT" in integrity["findings"]
    assert next(item for item in authority["authorities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")["authority_resolution"] == "UNRESOLVED"


def test_defined_capability_with_canonical_role_owner_resolves(tmp_path: Path) -> None:
    integrity, authority = audit_cross_registry(_fixture(tmp_path), "2026-08-11T00:00:00Z")
    item = next(item for item in authority["authorities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")
    assert item["authority_resolution"] == "RESOLVED"
    assert next(item for item in integrity["capabilities"] if item["capability_id"] == "STRATEGIC_IDENTITY_CHANGE_ASSESSMENT")["authority_resolution"] == "RESOLVED"


def test_orphaned_routing_entry_is_reported(tmp_path: Path) -> None:
    integrity, _ = audit_cross_registry(_fixture(tmp_path), "2026-08-11T00:00:00Z")
    assert "ROUTE_UNRESOLVED_STOP_LOCAL:B5_I2_SEMANTIC_AUDITOR" in integrity["findings"]
