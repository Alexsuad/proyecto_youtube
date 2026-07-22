"""Contratos y payload inicial de la misión B3-I1."""

import copy
import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema


ROOT = Path(__file__).resolve().parents[2]


def load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_initial_profile_payload_is_a_valid_draft_without_activation():
    payload = load_json("profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json")
    assert validate_against_schema(payload, "editorial_profile") == []
    assert payload["status"] == "DRAFT"
    assert payload["voice_profile"]["corpus_status"] == "SPECIFICATION_BASED"
    assert payload["voice_profile"]["approved_sample_ids"] == []


def test_profile_rejects_rigid_audience_and_platform_policy_in_stable_identity():
    payload = load_json("profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json")
    rigid_audience = copy.deepcopy(payload)
    rigid_audience["audience_hypotheses"][0]["status"] = "CONFIRMED"
    assert validate_against_schema(rigid_audience, "editorial_profile")

    platform_inside_identity = copy.deepcopy(payload)
    platform_inside_identity["identity_stable"]["youtube_algorithm_policy"] = "fixed"
    assert validate_against_schema(platform_inside_identity, "editorial_profile")


def test_voice_sample_requires_authorship_authorization_and_checksum():
    sample = {
        "sample_id": "SAMPLE-001", "locator": "secure://sample", "checksum": "a" * 64,
        "authorship": "OWNER", "text_type": "PERSONAL_TEXT", "classification": "AUTHENTIC",
        "usage_authorization": "AUTHORIZED", "representativeness": "HIGH",
        "recorded_at": "2026-07-22T20:00:00Z", "lineage": ["OWNER_PROVIDED"],
        "inclusion_reason": "Muestra autorizada",
    }
    assert validate_against_schema(sample, "voice_sample") == []
    canonical = copy.deepcopy(sample)
    canonical["classification"] = "CANONICAL"
    assert validate_against_schema(canonical, "voice_sample")
    for field in ("authorship", "usage_authorization", "checksum"):
        invalid = copy.deepcopy(sample)
        invalid.pop(field)
        assert validate_against_schema(invalid, "voice_sample")

    excluded = copy.deepcopy(sample)
    excluded["classification"] = "EXCLUDED"
    excluded.pop("inclusion_reason")
    excluded["exclusion_reason"] = "No representa la voz del propietario"
    assert validate_against_schema(excluded, "voice_sample") == []
    excluded.pop("exclusion_reason")
    assert validate_against_schema(excluded, "voice_sample")


def test_learning_candidate_requires_evidence_and_lineage():
    candidate = {
        "learning_id": "LEARN-001", "target_profile_id": "MADG-EDITORIAL-PROFILE", "target_profile_version": "1.0.0",
        "observed_change": "Ajuste de voz", "scope": "VOICE", "lineage": ["SAMPLE-001"],
        "evidence_items": [{"source_id": "SAMPLE-001", "locator": "secure://sample", "checksum": "a" * 64, "observation": "Patrón repetido"}],
        "confidence": 0.6, "examples": ["Ejemplo"], "counterexamples": ["Contraejemplo"], "exceptions": [],
        "functional_decision": {"status": "PENDING"},
        "status_history": [{"status": "CANDIDATE", "recorded_at": "2026-07-22T20:00:00Z"}],
    }
    assert validate_against_schema(candidate, "editorial_learning_candidate") == []
    candidate.pop("lineage")
    assert validate_against_schema(candidate, "editorial_learning_candidate")
