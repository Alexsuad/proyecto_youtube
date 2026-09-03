from copy import deepcopy

import pytest

from src.application.contracts import HumanInput
from src.core.contract_validation import (
    validate_against_schema,
    validate_claims_ledger,
    validate_research_pack,
    validate_research_plan,
    validate_research_ready_manifest,
    validate_source_access_and_evidence_report,
)
from tests.core.test_all_schemas import VALID_FIXTURES


def test_research_plan_is_explicit_and_has_no_silent_three_work_default() -> None:
    plan = deepcopy(VALID_FIXTURES["research_plan"])
    assert validate_research_plan(plan) == []
    assert plan["target_final_works_decision"]["requested_count"] == 4

    plan["target_final_works_decision"] = {
        "status": "CONFIRMED",
        "requested_count": None,
        "decision_basis": "Sin cantidad explícita.",
        "decision_ref": "DEC-1",
    }
    assert validate_research_plan(plan)

    plan = deepcopy(VALID_FIXTURES["research_plan"])
    plan["dimensions"] = []
    assert validate_research_plan(plan)


def test_intake_keeps_research_role_and_editorial_intent_separate() -> None:
    without_research_fields = HumanInput.create(mode="tema", content="Fenómeno").to_dict()
    assert "research_role" not in without_research_fields
    assert "editorial_intent" not in without_research_fields
    assert validate_against_schema(without_research_fields, "human_episode_input") == []

    explicit = HumanInput.create(
        mode="tema",
        content="Fenómeno",
        research_role="ANCLA",
        editorial_intent="PREFERIDA",
    ).to_dict()
    assert explicit["research_role"] == "ANCLA"
    assert explicit["editorial_intent"] == "PREFERIDA"
    assert validate_against_schema(explicit, "human_episode_input") == []


def test_claims_ledger_can_exist_before_script() -> None:
    ledger = deepcopy(VALID_FIXTURES["claims_ledger"])
    ledger.pop("script_version")
    ledger.update({
        "contract_version": "2.0.0",
        "ledger_stage": "RESEARCH_PRE_SCRIPT",
        "research_id": "R-1",
        "episode_id": "EP-1",
        "artifact_version": "2.0.0",
    })
    for claim in ledger["claims"]:
        claim.pop("script_location", None)
    assert validate_claims_ledger(ledger) == []

    ledger["claims"][0]["script_location"] = "script.md#1"
    assert validate_claims_ledger(ledger)


def test_research_pack_v2_separates_evidence_and_states() -> None:
    research = deepcopy(VALID_FIXTURES["research_pack"])
    research.pop("narrative_opportunities", None)
    research.pop("editorial_uses", None)
    research.update({
        "research_contract_version": "2.0.0",
        "research_stage": "DEEP_RESEARCH",
        "research_sufficiency": "LIMITED_BUT_USABLE",
        "artifact_validity": "VALID",
        "thesis_stage": "PROVISIONAL",
        "evidence_type_separation": {
            "work_evidence_refs": ["WORK-1"],
            "external_reality_evidence_refs": ["EXT-1"],
        },
        "acquisition_bindings": [{
            "request_ref": "REQ-1",
            "execution_ref": "EXEC-1",
            "recovery_artifact_ref": "recovery:S-1",
            "source_ref": "S1",
            "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED",
            "software_controlled": True,
        }],
    })
    research["source_registry"][0].update({
        "evidence_status": "VERIFIED",
        "retrieval_status": "RECOVERED",
        "recovery_artifact_ref": "recovery:S1",
    })
    assert validate_research_pack(research) == []

    research["acquisition_bindings"][0].update({"recovery_artifact_ref": None, "retrieval_status": "NOT_RECOVERED"})
    assert validate_research_pack(research)


def _v2_source_report() -> dict:
    report = deepcopy(VALID_FIXTURES["source_access_and_evidence_report"])
    report.update({
        "research_contract_version": "2.0.0",
        "research_stage": "DEEP_RESEARCH",
        "research_sufficiency": "LIMITED_BUT_USABLE",
        "artifact_validity": "VALID",
        "thesis_stage": "PROVISIONAL",
        "evidence_type_separation": {"work_evidence_refs": ["WORK-1"], "external_reality_evidence_refs": ["EXT-1"]},
        "acquisition_bindings": [{
            "request_ref": "REQ-1",
            "execution_ref": "EXEC-1",
            "recovery_artifact_ref": "recovery:S1",
            "source_ref": "S1",
            "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED",
            "software_controlled": True,
        }],
    })
    report["fuentes_primarias"][0].update({
        "evidence_status": "VERIFIED",
        "retrieval_status": "RECOVERED",
        "recovery_artifact_ref": "recovery:S1",
    })
    return report


@pytest.mark.parametrize("kind", ["research_pack", "source_access_and_evidence_report"])
def test_v2_positive_source_requires_and_accepts_real_acquisition_binding(kind: str) -> None:
    if kind == "research_pack":
        payload = deepcopy(VALID_FIXTURES["research_pack"])
        payload.pop("narrative_opportunities", None)
        payload.pop("editorial_uses", None)
        payload.update({
            "research_contract_version": "2.0.0",
            "research_stage": "DEEP_RESEARCH",
            "research_sufficiency": "LIMITED_BUT_USABLE",
            "artifact_validity": "VALID",
            "thesis_stage": "PROVISIONAL",
            "evidence_type_separation": {"work_evidence_refs": ["WORK-1"], "external_reality_evidence_refs": ["EXT-1"]},
        })
        source = payload["source_registry"][0]
        source.update({"evidence_status": "VERIFIED", "retrieval_status": "RECOVERED", "recovery_artifact_ref": "recovery:S1"})
        payload["acquisition_bindings"] = [{"request_ref": "REQ-1", "execution_ref": "EXEC-1", "recovery_artifact_ref": "recovery:S1", "source_ref": "S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}]
        assert validate_research_pack(payload) == []
        payload.pop("acquisition_bindings")
        assert validate_research_pack(payload)
    else:
        payload = _v2_source_report()
        assert validate_source_access_and_evidence_report(payload) == []
        payload.pop("acquisition_bindings")
        assert validate_source_access_and_evidence_report(payload)


@pytest.mark.parametrize("mutation", [
    {"retrieval_status": "NOT_RECOVERED", "evidence_status": "VERIFIED"},
    {"retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": False},
    {"retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "recovery_artifact_ref": None},
])
def test_v2_acquisition_binding_rejects_positive_evidence_without_real_recovery(mutation: dict) -> None:
    for kind in ("research_pack", "source_access_and_evidence_report"):
        payload = _v2_source_report() if kind == "source_access_and_evidence_report" else deepcopy(VALID_FIXTURES["research_pack"])
        if kind == "research_pack":
            payload.pop("narrative_opportunities", None)
            payload.pop("editorial_uses", None)
            payload.update({"research_contract_version": "2.0.0", "research_stage": "DEEP_RESEARCH", "research_sufficiency": "LIMITED_BUT_USABLE", "artifact_validity": "VALID", "thesis_stage": "PROVISIONAL", "evidence_type_separation": {"work_evidence_refs": ["WORK-1"], "external_reality_evidence_refs": ["EXT-1"]}})
            payload["source_registry"][0].update({"evidence_status": "VERIFIED", "retrieval_status": "RECOVERED", "recovery_artifact_ref": "recovery:S1"})
            payload["acquisition_bindings"] = [{"request_ref": "REQ-1", "execution_ref": "EXEC-1", "recovery_artifact_ref": "recovery:S1", "source_ref": "S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}]
        payload["acquisition_bindings"][0].update(mutation)
        validator = validate_research_pack if kind == "research_pack" else validate_source_access_and_evidence_report
        assert validator(payload)


def test_research_ready_with_limitations_requires_downstream_restrictions() -> None:
    manifest = deepcopy(VALID_FIXTURES["research_ready_manifest"])
    assert validate_research_ready_manifest(manifest) == []
    manifest["downstream_restrictions"] = []
    assert validate_research_ready_manifest(manifest)


def test_research_v2_does_not_require_narrative_curation_fields() -> None:
    curation = deepcopy(VALID_FIXTURES["material_curation"])
    for field in (
        "sequence_rationale",
        "progression_evidence",
        "function_of_each_selected_material",
        "progression_map",
        "expected_order",
        "dependency_between_materials",
    ):
        curation.pop(field, None)
    curation["candidates"][0].pop("narrative_use", None)
    curation.update({"research_contract_version": "2.0.0", "selection_state": "SELECTED", "artifact_validity": "VALID"})
    assert validate_against_schema(curation, "material_curation") == []
