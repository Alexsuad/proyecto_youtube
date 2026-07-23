import json
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "docs/initiatives/schemas/initiative.schema.json").read_text(encoding="utf-8"))


def initiative():
    return yaml.safe_load((ROOT / "docs/initiatives/records/INIT-001.yaml").read_text(encoding="utf-8"))


def violations(data):
    return list(Draft7Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(data))


def test_empty_registry_and_minimal_capture_are_valid():
    registry = yaml.safe_load((ROOT / "docs/initiatives/REGISTRY.yaml").read_text(encoding="utf-8"))
    assert registry["registry_version"] == "1.0.0"
    assert ({**registry, "items": []})["items"] == []
    assert registry["items"]
    assert violations(initiative()) == []


def test_initiative_contract_rejects_unauthorized_or_incoherent_execution():
    missing_authorization = initiative()
    missing_authorization.pop("implementation_authorized")
    assert violations(missing_authorization)
    unauthorized = initiative()
    unauthorized["implementation_authorized"] = True
    assert violations(unauthorized)
    unknown_scope = initiative()
    unknown_scope["scope_recommendation"] = "UNKNOWN"
    assert violations(unknown_scope)
    blocked = initiative()
    blocked["execution_status"] = "BLOCKED"
    assert violations(blocked)
    related_without_id = initiative()
    related_without_id["relationship"] = {"type": "RELATES_TO", "related_initiative_id": None}
    assert violations(related_without_id)
    planned_without_authorization = initiative()
    planned_without_authorization["execution_status"] = "PLANNED"
    assert violations(planned_without_authorization)
    promoted_without_reference = initiative()
    promoted_without_reference["scope_recommendation"] = "PROMOTED_TO_CURRENT_SCOPE"
    assert violations(promoted_without_reference)


def test_init_001_is_a_valid_non_authorized_capture():
    record = initiative()
    assert record["initiative_id"] == "INIT-001"
    assert record["implementation_authorized"] is False
    assert record["execution_status"] == "NOT_AUTHORIZED"
    assert record["classification_status"] == "CLASSIFIED"
    assert record["scope_recommendation"] == "POST_MVP"
    assert record["recommendation"]["status"] == "PRESERVE_EXTENSION_POINT"
    assert violations(record) == []
