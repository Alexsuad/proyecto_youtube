import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.editorial_profile_registry import EditorialProfileRegistry
from src.core.version_manifest import compute_checksum

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CHECKSUM_1_2 = "b1029e85289c51d4585c555ed20566dfd6f1f6db30b875f989fc23bf46fc5977"


def test_profile_chain_preserves_1_1_invalid_and_leaves_1_2_pending():
    registry = json.loads((ROOT / "config" / "editorial_profile_registry.json").read_text())
    assert validate_against_schema(registry, "editorial_profile_registry") == []

    invalid = registry["profiles"]["mas_alla_del_guion@1.1.0"]
    assert invalid["status"] == "INVALID_APPROVAL_CHAIN"
    assert invalid["active"] is False
    assert invalid["reason"] == "profile checksum does not match functional approval checksum"
    assert invalid["checksum"] == compute_checksum(json.loads((ROOT / "profiles" / "editorial" / "mas_alla_del_guion" / "1.1.0" / "profile_payload.json").read_text()))

    payload = json.loads((ROOT / "profiles" / "editorial" / "mas_alla_del_guion" / "1.2.0" / "profile_payload.json").read_text())
    compiled = json.loads((ROOT / "profiles" / "editorial" / "mas_alla_del_guion" / "1.2.0" / "editorial_profile.json").read_text())
    approval = json.loads((ROOT / "profiles" / "editorial" / "mas_alla_del_guion" / "1.2.0" / "functional_approval.json").read_text())
    technical = json.loads((ROOT / "profiles" / "editorial" / "mas_alla_del_guion" / "1.2.0" / "technical_validation.json").read_text())

    assert validate_against_schema(payload, "editorial_profile") == []
    assert validate_against_schema(compiled["profile"], "editorial_profile") == []
    assert payload == compiled["profile"]
    assert payload["status"] == "PENDING_FUNCTIONAL_APPROVAL"
    assert compiled["checksum"] == EXPECTED_CHECKSUM_1_2
    assert approval["decision"] == "PENDING"
    assert approval["approval_status"] == "PENDING"
    assert approval["profile_checksum"] == EXPECTED_CHECKSUM_1_2
    assert technical["status"] == "BLOCKED"
    assert technical["evidence"]["profile_checksum"] == EXPECTED_CHECKSUM_1_2
    assert registry["profiles"]["mas_alla_del_guion@1.2.0"]["status"] == "FUNCTIONAL_REVIEW_BLOCKED"
    assert registry["profiles"]["mas_alla_del_guion@1.2.0"]["active"] is False
    assert registry["active_profile_key"] == "mas_alla_del_guion@1.2.1"
    assert (ROOT / "config" / "active_editorial_profile.json").exists()
