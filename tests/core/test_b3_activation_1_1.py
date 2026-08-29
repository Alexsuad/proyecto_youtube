import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.version_manifest import compute_checksum


ROOT = Path(__file__).resolve().parents[2]


def test_active_profile_is_registered_with_exact_pointer_checksum():
    registry = json.loads((ROOT / "config" / "editorial_profile_registry.json").read_text(encoding="utf-8"))
    pointer = load_active_profile_authority()
    key = "mas_alla_del_guion@1.2.2"
    assert pointer["ACTIVE_PROFILE_VERSION"] == "1.2.2"
    assert registry["active_profile_key"] == key
    assert set(registry["profiles"]) == {key}
    entry = registry["profiles"][key]
    payload = json.loads((ROOT / entry["profile_path"]).read_text(encoding="utf-8"))
    assert validate_against_schema(registry, "editorial_profile_registry") == []
    assert validate_against_schema(payload, "editorial_profile") == []
    assert entry["status"] == "ACTIVE"
    assert entry["active"] is True
    assert compute_checksum(payload) == pointer["profile_checksum"] == entry["checksum"]
    assert len(entry["profile"]["source_lineage"]) == 1
    assert entry["profile"]["source_lineage"][0]["source_id"] == "B3-FUNCTIONAL-SPEC-CANONICAL"
