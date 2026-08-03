import json
from uuid import uuid4
from pathlib import Path

import pytest

from src.core.editorial_profile_registry import EditorialProfileRegistry
from src.core.version_manifest import compute_checksum

ROOT = Path(__file__).resolve().parents[2]


def payload(version="1.2.0"):
    return json.loads((ROOT / "profiles" / "editorial" / "mas_alla_del_guion" / version / "profile_payload.json").read_text())


def approval(profile, checksum):
    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["version"],
        "profile_checksum": checksum,
        "decision": "APPROVE",
        "approval_status": "APPROVE",
        "reviewer_role": "CHANNEL_INTELLIGENCE",
        "approval_timestamp": "2026-07-27T12:00:00Z",
        "review_scope": ["identidad", "voz", "límites"],
        "functional_owner_role": "CHANNEL_INTELLIGENCE",
        "voice_evidence_level": "AUTHENTIC_CORPUS_PARTIAL",
        "evidence_summary": "Aprobación final de fixture sintético.",
        "limitations": ["Fixture de validación."],
        "approved_by": "channel_intelligence_owner",
        "approved_at": "2026-07-27T12:00:00Z",
    }


def gate(profile, checksum):
    return {
        "gate_id": "B3_TECHNICAL_PROFILE_VALIDATION",
        "artifact_id": profile["profile_id"],
        "artifact_version": profile["version"],
        "status": "PASS",
        "summary": "ok",
        "violations": [],
        "warnings": [],
        "evidence": {"profile_checksum": checksum},
        "checked_at": "2026-07-27T12:15:00Z",
        "checker_version": "1.2.0",
        "exit_code": 0,
    }


def test_registration_is_deterministic_and_rejects_overwrite(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    checksum = registry.register(profile, profile_path="payload.json", compiled_profile_path="compiled.json")
    assert checksum == registry.register(profile, profile_path="payload.json", compiled_profile_path="compiled.json")
    profile["identity_stable"]["identity"] = "other"
    with pytest.raises(ValueError):
        registry.register(profile, profile_path="payload.json", compiled_profile_path="compiled.json")


def test_activation_requires_matching_evidence_and_updates_registry(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    checksum = compute_checksum(profile)
    approval_record = approval(profile, checksum)
    technical = gate(profile, checksum)
    assert registry.record_activation(
        profile,
        approval_record,
        technical,
        actor="TECHNICAL_GOVERNANCE",
        profile_path="payload.json",
        compiled_profile_path="compiled.json",
        approval_path="approval.json",
        technical_validation_path="technical.json",
    ) == checksum
    saved = json.loads(registry.path.read_text())
    key = "mas_alla_del_guion@1.2.0"
    assert saved["active_profile_key"] == key
    assert saved["profiles"][key]["status"] == "ACTIVE"
    assert saved["profiles"][key]["active"] is True
    technical["profile_checksum"] = "b" * 64
    with pytest.raises(ValueError):
        EditorialProfileRegistry.verify_activation(profile, approval_record, technical)


def test_invalid_approval_chain_is_recorded_without_mutating_profile_files(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload("1.1.0")
    observed = compute_checksum(profile)
    registry.mark_invalid_approval_chain(
        profile,
        reason="profile checksum does not match functional approval checksum",
        approval_checksum="dbe94dbfcee5e9e30a956dab20097f62216e4fb58beddb3ef8fa3086fd95ee8c",
        technical_validation_checksum="dbe94dbfcee5e9e30a956dab20097f62216e4fb58beddb3ef8fa3086fd95ee8c",
        profile_path="profiles/editorial/mas_alla_del_guion/1.1.0/profile_payload.json",
        compiled_profile_path="profiles/editorial/mas_alla_del_guion/1.1.0/editorial_profile.json",
        approval_path="profiles/editorial/mas_alla_del_guion/1.1.0/functional_approval.json",
        technical_validation_path="profiles/editorial/mas_alla_del_guion/1.1.0/technical_validation.json",
        superseded_by="mas_alla_del_guion@1.2.0",
    )
    saved = json.loads(registry.path.read_text())
    key = "mas_alla_del_guion@1.1.0"
    assert saved["profiles"][key]["checksum"] == observed
    assert saved["profiles"][key]["status"] == "INVALID_APPROVAL_CHAIN"
    assert saved["profiles"][key]["active"] is False


def test_pending_profile_state_can_be_registered_without_active_pointer(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    profile["status"] = "PENDING_FUNCTIONAL_APPROVAL"
    checksum = registry.register(profile, profile_path="payload.json", compiled_profile_path="compiled.json")
    key = "mas_alla_del_guion@1.2.0"
    registry.data["profiles"][key]["status"] = "PENDING_FUNCTIONAL_APPROVAL"
    registry.data["profiles"][key]["active"] = False
    registry.save()
    saved = json.loads(registry.path.read_text())
    assert saved["profiles"][key]["checksum"] == checksum
    assert saved["profiles"][key]["status"] == "PENDING_FUNCTIONAL_APPROVAL"
    assert saved["profiles"][key]["active"] is False
    assert saved["active_profile_key"] is None
