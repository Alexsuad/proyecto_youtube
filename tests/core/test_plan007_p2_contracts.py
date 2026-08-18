from __future__ import annotations

from src.core.contract_validation import validate_claims_ledger, validate_against_schema, validate_work_research_dossier
from src.scripts.channel_intelligence import canonical_checksum, evaluate_topic_belonging_gate, validate_assessment, validate_topic_input
from tests.core.test_channel_intelligence import assessment, decision, topic_input
from tests.core.test_work_lifecycle import _exception, _screened_pack


def test_topic_first_entry_allows_missing_work_but_pre_b5_i1_approval_requires_door():
    entry = topic_input(entry_mode="TOPIC_FIRST")
    entry.pop("narrative_work")
    assert validate_topic_input(entry) == []
    assessed = assessment(topic_input(entry_mode="TOPIC_FIRST", narrative_work="NO_WORK_YET"))
    reviewed = decision(assessed)
    result = evaluate_topic_belonging_gate(reviewed, assessed, entry)
    assert result["status"] == "BLOCKED"
    assert "PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_NARRATIVE_DOOR" in result["violations"]


def test_topic_first_requires_research_evidence_before_pre_b5_i1_approval():
    entry = topic_input(entry_mode="TOPIC_FIRST")
    entry.pop("narrative_work")
    assessed = assessment(topic_input(entry_mode="TOPIC_FIRST", narrative_work="NO_WORK_YET"))
    reviewed = decision(assessed)
    blocked = evaluate_topic_belonging_gate(reviewed, assessed, entry)
    assert blocked["status"] == "BLOCKED"
    assert "PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_NARRATIVE_DOOR" in blocked["violations"]
    assert "PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_SUFFICIENT_CANDIDATE_WORKS" in blocked["violations"]


def test_topic_first_research_enrichment_preserves_mode_and_can_cross_pre_b5_i1():
    entry = topic_input(entry_mode="TOPIC_FIRST")
    entry.pop("narrative_work")
    assessed = assessment(topic_input(entry_mode="TOPIC_FIRST", narrative_work="NO_WORK_YET"))
    enriched_entry = {**entry, "narrative_work": "Obra consolidada durante investigacion", "research_ref": "research-1", "narrative_door_evidence_refs": ["door-evidence-1"], "candidate_work_refs": ["work-1", "work-2", "work-3", "work-4", "work-5"]}
    assert validate_topic_input(enriched_entry) == []
    assert validate_assessment(assessed, enriched_entry) == []
    reviewed = decision(
        assessed,
        pre_b5_i1_evidence={
            "topic_input_checksum": canonical_checksum(enriched_entry, "input"),
            "research_ref": "research-1",
            "narrative_door_evidence_refs": ["door-evidence-1"],
            "candidate_work_refs": ["work-1", "work-2", "work-3", "work-4", "work-5"],
        },
    )
    result = evaluate_topic_belonging_gate(reviewed, assessed, enriched_entry, work_lifecycle={"entry_mode": "TOPIC_FIRST", "research_id": "research-1", "screening": {"candidate_work_ids": ["work-1", "work-2", "work-3", "work-4", "work-5"], "range_status": "NORMAL", "exception": None}}, research_dossier={"research_id": "research-1", "dossier_stage": "RESEARCH_IN_PROGRESS", "evidence_report_id": "door-evidence-1"})
    assert result["status"] == "PASS"
    assert result["topic_belonging_approval"] == "NECESSARY_NOT_SUFFICIENT"
    assert not any("TOPIC_FIRST_REAL_WORK" in violation for violation in result["violations"])


def test_topic_first_less_than_five_candidates_requires_approved_exception():
    entry = topic_input(entry_mode="TOPIC_FIRST")
    entry.pop("narrative_work")
    entry.update({"research_ref": "research-exception", "narrative_door_evidence_refs": ["door-exception"], "candidate_work_refs": ["W1", "W2"]})
    assessed = assessment(topic_input(entry_mode="TOPIC_FIRST", narrative_work="NO_WORK_YET"))
    reviewed = decision(assessed, pre_b5_i1_evidence={"topic_input_checksum": canonical_checksum(entry, "input"), "research_ref": entry["research_ref"], "narrative_door_evidence_refs": entry["narrative_door_evidence_refs"], "candidate_work_refs": entry["candidate_work_refs"]})
    lifecycle = _screened_pack()
    lifecycle["research_id"] = "research-exception"
    lifecycle["screening"]["candidate_work_ids"] = ["W1", "W2"]
    lifecycle["screening"]["range_status"] = "EXCEPTION"
    lifecycle["screening"]["exception"] = _exception()
    dossier = {"research_id": "research-exception", "dossier_stage": "RESEARCH_IN_PROGRESS", "evidence_report_id": "door-exception"}
    assert validate_topic_input(entry) == []
    assert evaluate_topic_belonging_gate(reviewed, assessed, entry, work_lifecycle=lifecycle, research_dossier=dossier)["status"] == "PASS"
    lifecycle["screening"]["exception"] = None
    assert evaluate_topic_belonging_gate(reviewed, assessed, entry, work_lifecycle=lifecycle, research_dossier=dossier)["status"] == "BLOCKED"


def test_topic_first_refs_without_materialized_research_cannot_approve():
    entry = topic_input(entry_mode="TOPIC_FIRST")
    entry.pop("narrative_work")
    entry.update({"research_ref": "FAKE-RP", "narrative_door_evidence_refs": ["FAKE-ER"], "candidate_work_refs": ["W1", "W2", "W3", "W4", "W5"]})
    assessed = assessment(topic_input(entry_mode="TOPIC_FIRST", narrative_work="NO_WORK_YET"))
    reviewed = decision(assessed, pre_b5_i1_evidence={"topic_input_checksum": canonical_checksum(entry, "input"), "research_ref": "FAKE-RP", "narrative_door_evidence_refs": ["FAKE-ER"], "candidate_work_refs": ["W1", "W2", "W3", "W4", "W5"]})
    result = evaluate_topic_belonging_gate(reviewed, assessed, entry)
    assert result["status"] == "BLOCKED"
    assert "PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_MATERIAL_RESEARCH_BINDING" in result["violations"]


def test_work_research_dossier_is_progressive_before_review():
    dossier = {
        "dossier_id": "D-1",
        "dossier_version": "1.0.0",
        "episode_id": "EP-1",
        "research_id": "R-1",
        "evidence_report_id": "E-1",
        "work": {
            "material_id": "W-1",
            "title": "Obra",
            "creator": "Autor",
            "consulted_representations": [{
                "representation_kind": "ORIGINAL_WORK",
                "edition_or_version": "1",
                "consulted_locator": "loc-1",
            }],
        },
        "dossier_stage": "IDENTIFIED",
        "pending_items": [],
        "confidence": "LOW",
        "created_at": "2026-08-17T10:00:00Z",
    }
    assert validate_work_research_dossier(dossier) == []
    assert validate_work_research_dossier({**dossier, "dossier_stage": "RESEARCH_IN_PROGRESS"}) == []
    mature_early = {**dossier, "dossier_stage": "RESEARCH_IN_PROGRESS", "analysis_references": [{"analysis_id": "A-1", "material_id": "W-1"}]}
    assert any("artefactos canonicos" in violation for violation in validate_work_research_dossier(mature_early))
    assert any("RESEARCH_REVIEW_PENDING" in violation or "artefactos canonicos" in violation for violation in validate_work_research_dossier({**dossier, "dossier_stage": "RESEARCH_REVIEW_PENDING"}))
    assert any("artefacto maduro" in violation for violation in validate_work_research_dossier({**dossier, "analysis_references": [{"analysis_id": "A-1", "material_id": "W-1"}]}))


def _claim(claim_id: str, text: str = "Texto verificable"):
    return {
        "claim_id": claim_id,
        "script_location": "bloque-1",
        "claim_text": text,
        "claim_type": "FACT",
        "source_refs": ["source-1"],
        "verification_status": "VERIFIED",
        "materiality": {
            "is_material": False,
            "activation_criteria": [],
            "non_trigger_examples": [],
            "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"],
            "return_route_code": "NOT_APPLICABLE",
            "decision_ref": None,
        },
    }


def test_claims_ledger_requires_non_empty_unique_ids_and_text():
    ledger = {"ledger_id": "L-1", "script_version": "1.0.0", "claims": [_claim("C-1"), _claim("C-1", "otro")]}
    violations = validate_claims_ledger(ledger)
    assert any("duplicar claim_id" in item for item in violations)
    assert validate_against_schema({"ledger_id": "", "script_version": "1.0.0", "claims": []}, "claims_ledger")