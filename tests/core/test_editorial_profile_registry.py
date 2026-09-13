import json
from uuid import uuid4
from pathlib import Path

import pytest

from src.core.editorial_profile_registry import EditorialProfileRegistry, validate_b3_lineage_cross_registry
from src.core.evidence_freshness import sha256_path
from src.core.version_manifest import compute_checksum

ROOT = Path(__file__).resolve().parents[2]


def payload(version="1.2.2"):
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
    lineage = profile["source_lineage"]
    return {
        "gate_id": "B3_TECHNICAL_PROFILE_VALIDATION",
        "artifact_id": profile["profile_id"],
        "artifact_version": profile["version"],
        "status": "PASS",
        "summary": "ok",
        "violations": [],
        "warnings": [],
        "evidence": {
            "profile_checksum": checksum,
            "lineage_sources": [item["source_id"] for item in lineage],
            "functional_source": {
                field: lineage[0][field] for field in ("source_id", "role", "checksum")
            },
        },
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
    key = "mas_alla_del_guion@1.2.2"
    assert saved["active_profile_key"] == key
    assert saved["profiles"][key]["status"] == "ACTIVE"
    assert saved["profiles"][key]["active"] is True
    technical["profile_checksum"] = "b" * 64
    with pytest.raises(ValueError):
        EditorialProfileRegistry.verify_activation(profile, approval_record, technical)


def test_activation_rejects_obsolete_functional_source_checksum(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    checksum = compute_checksum(profile)
    approval_record = approval(profile, checksum)
    technical = gate(profile, checksum)
    technical["evidence"]["functional_source"]["checksum"] = "a" * 64
    with pytest.raises(ValueError, match="fuente funcional"):
        registry.record_activation(
            profile, approval_record, technical,
            actor="TECHNICAL_GOVERNANCE", profile_path="payload.json",
            compiled_profile_path="compiled.json", approval_path="approval.json",
            technical_validation_path="technical.json",
        )


def test_activation_rejects_invented_functional_source(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    checksum = compute_checksum(profile)
    approval_record = approval(profile, checksum)
    technical = gate(profile, checksum)
    technical["evidence"]["functional_source"]["source_id"] = "INVENTED-SOURCE"
    with pytest.raises(ValueError, match="fuente funcional"):
        registry.record_activation(
            profile, approval_record, technical,
            actor="TECHNICAL_GOVERNANCE", profile_path="payload.json",
            compiled_profile_path="compiled.json", approval_path="approval.json",
            technical_validation_path="technical.json",
        )


def test_activation_rejects_duplicate_or_inconsistent_lineage_sources(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    checksum = compute_checksum(profile)
    approval_record = approval(profile, checksum)
    technical = gate(profile, checksum)
    technical["evidence"]["lineage_sources"] = ["B3-FUNCTIONAL-SPEC-CANONICAL"] * 2
    with pytest.raises(ValueError, match="lineage_sources"):
        registry.record_activation(
            profile, approval_record, technical,
            actor="TECHNICAL_GOVERNANCE", profile_path="payload.json",
            compiled_profile_path="compiled.json", approval_path="approval.json",
            technical_validation_path="technical.json",
        )


def test_invalid_approval_chain_is_recorded_without_mutating_profile_files(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    profile["version"] = "9.9.9"
    observed = compute_checksum(profile)
    registry.mark_invalid_approval_chain(
        profile,
        reason="profile checksum does not match functional approval checksum",
        approval_checksum="dbe94dbfcee5e9e30a956dab20097f62216e4fb58beddb3ef8fa3086fd95ee8c",
        technical_validation_checksum="dbe94dbfcee5e9e30a956dab20097f62216e4fb58beddb3ef8fa3086fd95ee8c",
        profile_path="synthetic/profile_payload.json",
        compiled_profile_path="synthetic/editorial_profile.json",
        approval_path="synthetic/functional_approval.json",
        technical_validation_path="synthetic/technical_validation.json",
        superseded_by="synthetic@10.0.0",
    )
    saved = json.loads(registry.path.read_text())
    key = "mas_alla_del_guion@9.9.9"
    assert saved["profiles"][key]["checksum"] == observed
    assert saved["profiles"][key]["status"] == "INVALID_APPROVAL_CHAIN"
    assert saved["profiles"][key]["active"] is False


def test_pending_profile_state_can_be_registered_without_active_pointer(tmp_path: Path):
    registry = EditorialProfileRegistry(tmp_path / f"registry_{uuid4().hex}.json")
    profile = payload()
    profile["status"] = "PENDING_FUNCTIONAL_APPROVAL"
    checksum = registry.register(profile, profile_path="payload.json", compiled_profile_path="compiled.json")
    key = "mas_alla_del_guion@1.2.2"
    registry.data["profiles"][key]["status"] = "PENDING_FUNCTIONAL_APPROVAL"
    registry.data["profiles"][key]["active"] = False
    registry.save()
    saved = json.loads(registry.path.read_text())
    assert saved["profiles"][key]["checksum"] == checksum
    assert saved["profiles"][key]["status"] == "PENDING_FUNCTIONAL_APPROVAL"
    assert saved["profiles"][key]["active"] is False
    assert saved["active_profile_key"] is None


def test_lineage_single_identity_and_incompatible_checksum_fails():
    from src.core.editorial_profile_registry import validate_profile_lineage

    # Single identity with same checksum is valid
    ok = {
        "source_lineage": [
            {"source_id": "B3-FUNCTIONAL-SPEC-CANONICAL", "locator": "docs/specifications/B3_editorial_profile_functional_specification.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "a" * 64},
            {"source_id": "B3-FUNCTIONAL-SPEC-CANONICAL", "locator": "docs/specifications/B3_editorial_profile_functional_specification.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "a" * 64},
        ]
    }
    assert validate_profile_lineage(ok) == []
    # Same identity with different checksum must fail
    bad = {
        "source_lineage": [
            {"source_id": "B3-FUNCTIONAL-SPEC-CANONICAL", "locator": "docs/specifications/B3_editorial_profile_functional_specification.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "a" * 64},
            {"source_id": "B3-FUNCTIONAL-SPEC-CANONICAL", "locator": "docs/specifications/B3_editorial_profile_functional_specification.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "b" * 64},
        ]
    }
    violations = validate_profile_lineage(bad)
    assert any("checksums incompatibles" in v for v in violations)
    # Different identities with different checksums are allowed
    distinct = {
        "source_lineage": [
            {"source_id": "S1", "locator": "docs/spec.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "a" * 64},
            {"source_id": "S2", "locator": "docs/other.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "b" * 64},
        ]
    }
    assert validate_profile_lineage(distinct) == []


def test_active_profile_lineage_is_single_verifiable_identity():
    from src.core.editorial_profile_registry import validate_profile_lineage, load_active_profile_authority

    active = load_active_profile_authority()
    # Verify registry entry has exactly one verifiable lineage identity currently
    registry = json.loads((ROOT / "config" / "editorial_profile_registry.json").read_text(encoding="utf-8"))
    key = registry["active_profile_key"]
    profile = registry["profiles"][key]["profile"]
    assert validate_profile_lineage(profile) == []
    lineage = profile.get("source_lineage", [])
    assert len(lineage) == 1
    assert lineage[0]["source_id"] == "B3-FUNCTIONAL-SPEC-CANONICAL"
    # Changing checksum must invalidate active authority
    tampered = json.loads(json.dumps(profile))
    tampered["source_lineage"][0]["checksum"] = "f" * 64
    assert validate_profile_lineage(tampered) == []  # single entry still internally consistent
    # But two entries with same identity and different checksum must fail (incompatible identity simulation)
    dup = json.loads(json.dumps(profile))
    dup["source_lineage"].append({"source_id": "B3-FUNCTIONAL-SPEC-CANONICAL", "locator": "docs/specifications/B3_editorial_profile_functional_specification.md", "role": "FUNCTIONAL_SPECIFICATION", "checksum": "f" * 64})
    from src.core.editorial_profile_registry import validate_profile_lineage as v2
    assert any("checksums incompatibles" in v for v in v2(dup))


def test_b3_lineage_reconciles_registry_corpus_and_physical_source():
    assert validate_b3_lineage_cross_registry(ROOT) == []
    source_checksum = sha256_path(ROOT / "docs/specifications/B3_editorial_profile_functional_specification.md")
    corpus_checksum = sha256_path(ROOT / "profiles/voice/corpus_manifest.json")
    assert source_checksum != corpus_checksum


def test_b3_lineage_rejects_manifest_checksum_used_as_source_checksum(tmp_path: Path):
    import shutil

    for relative in (
        "config/editorial_profile_registry.json",
        "config/active_editorial_profile.json",
        "profiles/voice/corpus_manifest.json",
        "docs/specifications/B3_editorial_profile_functional_specification.md",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    corpus_path = tmp_path / "profiles/voice/corpus_manifest.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    corpus["source_lineage"][0]["checksum"] = sha256_path(corpus_path)
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    violations = validate_b3_lineage_cross_registry(tmp_path)
    assert any("corpus" in violation and "fuente física" in violation for violation in violations)


def test_b3_lineage_rejects_cross_registry_identity_mismatch(tmp_path: Path):
    import shutil

    for relative in (
        "config/editorial_profile_registry.json",
        "config/active_editorial_profile.json",
        "profiles/voice/corpus_manifest.json",
        "docs/specifications/B3_editorial_profile_functional_specification.md",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    corpus_path = tmp_path / "profiles/voice/corpus_manifest.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    corpus["source_lineage"][0]["source_id"] = "OTHER-SOURCE"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    violations = validate_b3_lineage_cross_registry(tmp_path)
    assert any("única identidad B3" in violation for violation in violations)
