import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.editorial_profile_registry import EditorialProfileRegistry


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CHECKSUM = "ff45c54267dd2c5f36896c802846322e57476820ed1fd9e81a5f9556b528c2cd"


def test_active_profile_1_1_matches_approved_artifacts():
    payload = json.loads((ROOT / "profiles/editorial/mas_alla_del_guion/1.1.0/profile_payload.json").read_text())
    compiled = json.loads((ROOT / "profiles/editorial/mas_alla_del_guion/1.1.0/editorial_profile.json").read_text())
    approval = json.loads((ROOT / "profiles/editorial/mas_alla_del_guion/1.1.0/functional_approval.json").read_text())
    technical = json.loads((ROOT / "profiles/editorial/mas_alla_del_guion/1.1.0/technical_validation.json").read_text())
    active = json.loads((ROOT / "config/active_editorial_profile.json").read_text())

    assert validate_against_schema(payload, "editorial_profile") == []
    assert validate_against_schema(compiled["profile"], "editorial_profile") == []
    assert payload == compiled["profile"]
    assert EditorialProfileRegistry.verify_activation(compiled["profile"], approval, technical) == EXPECTED_CHECKSUM
    assert validate_against_schema(active, "active_editorial_profile") == []
    assert (active["ACTIVE_PROFILE_ID"], active["ACTIVE_PROFILE_VERSION"], active["profile_checksum"]) == (
        "mas_alla_del_guion", "1.1.0", EXPECTED_CHECKSUM,
    )
