from copy import deepcopy
import hashlib
import json

from src.core.contract_validation import validate_against_schema, validate_work_lifecycle


POLICY_REF = "policies/script_product/main_episode_format_policy.md"


def _work(work_id, state="SCREENED_WORK", *, anchor=False, **refs):
    return {
        "work_id": work_id,
        "state": state,
        "state_version": "1.0.0",
        "identity_ref": f"candidate:{work_id}",
        "version_ref": refs.get("version_ref"),
        "is_anchor": anchor,
        "lineage_refs": [f"candidate-set:{work_id}"],
        "stage_evidence_refs": refs.get("stage_evidence_refs", [f"evidence:{work_id}"]),
        "screening_ref": refs.get("screening_ref"),
        "dossier_ref": refs.get("dossier_ref"),
        "differentiated_function_ref": refs.get("differentiated_function_ref"),
        "comparative_decision_ref": refs.get("comparative_decision_ref"),
    }


def _transition(work_id, previous, target, transition_type="PROMOTION", **overrides):
    return {
        "transition_id": overrides.get("transition_id", f"T-{work_id}-{target}"),
        "transition_version": "1.0.0",
        "work_id": work_id,
        "previous_state": previous,
        "target_state": target,
        "transition_type": transition_type,
        "transition_reason": "Decisión trazable de etapa.",
        "evidence_refs": ["evidence:transition"],
        "input_version_refs": ["input:1.0.0"],
        "transition_authority_ref": "config/responsibility_registry.json#responsibilities/RESEARCH_AND_CURATION",
        "authority_role": "RESEARCH_AND_CURATION",
        "decision": {"decision_id": "DEC-1", "decision_version": "1.0.0", "status": "EXPLICIT"},
        "occurred_at": "2026-08-12T20:00:00Z",
        "lineage_ref": "lineage:transition",
        "previous_transition_ref": overrides.get("previous_transition_ref"),
        "authorized_return_state": overrides.get("authorized_return_state"),
    }


def _screened_pack():
    works = [_work(f"W{i}", screening_ref=f"screening:W{i}") for i in range(1, 6)]
    return {
        "lifecycle_id": "WL-001", "lifecycle_version": "1.0.0", "episode_id": "EP-1", "research_id": "R-1",
        "entry_mode": "TOPIC_FIRST", "anchor_work_id": None, "works": works,
        "transitions": [_transition(f"W{i}", "DISCOVERED_WORK", "SCREENED_WORK") for i in range(1, 6)],
        "screening": {"candidate_work_ids": [f"W{i}" for i in range(1, 6)], "format_policy_ref": POLICY_REF, "range_status": "NORMAL", "exception": None},
        "final_selection": {"selected_work_ids": [], "format_policy_ref": POLICY_REF, "range_status": "NOT_APPLICABLE", "curation_ref": None, "exception": None},
        "critical_doubts": [], "created_at": "2026-08-12T20:00:00Z",
    }


def _exception():
    return {
        "exception_ref": "owner-approved:format-exception-001",
        "exception_reason": "Excepción material preexistente y aprobada.",
        "affected_format": "MAIN_EPISODE",
        "functional_owner": "SCRIPT_PRODUCT",
        "owner_approval_ref": "owner-decision:format-exception-001",
        "duration_or_scope_impact": "Un episodio.",
        "argumentative_impact": "Reduce el conjunto sin eliminar la función central.",
        "downstream_gate_effect": "Revisión adicional antes de continuar.",
    }


def _final_pack():
    data = _screened_pack()
    selected_ids = ["W1", "W2", "W3"]
    for work_id in selected_ids:
        work = next(item for item in data["works"] if item["work_id"] == work_id)
        work.update({"state": "FINAL_SELECTED_WORK", "dossier_ref": f"D-{work_id}", "differentiated_function_ref": f"function:{work_id}", "comparative_decision_ref": f"comparison:{work_id}"})
        data["transitions"].append(_transition(work_id, "SCREENED_WORK", "FINALIST_WORK", transition_id=f"T-{work_id}-FINALIST"))
        data["transitions"].append(_transition(work_id, "FINALIST_WORK", "FINAL_SELECTED_WORK", transition_id=f"T-{work_id}-SELECTED"))
    data["final_selection"] = {"selected_work_ids": selected_ids, "format_policy_ref": POLICY_REF, "range_status": "NORMAL", "curation_ref": "C-1", "exception": None}
    curation = {
        "curation_id": "C-1", "selected_material_ids": selected_ids, "selected_materials": selected_ids,
        "candidates": [{"material_id": work_id, "selection_status": "SELECTED"} for work_id in selected_ids],
        "function_of_each_selected_material": [{"material_id": work_id, "contribution": f"Función {work_id}"} for work_id in selected_ids],
        "progression_evidence": [{"material_id": work_id, "evidence_refs": [f"evidence:{work_id}"]} for work_id in selected_ids],
    }
    return data, curation


def _dossier(work_id, stage="RESEARCH_REVIEW_PENDING", *, episode_id="EP-1", research_id="R-1"):
    dossier = {
        "dossier_id": f"D-{work_id}", "dossier_version": "1.0.0", "episode_id": episode_id,
        "research_id": research_id, "evidence_report_id": f"ER-{work_id}",
        "work": {"material_id": work_id, "title": f"Obra {work_id}", "creator": "Autor", "consulted_representations": [{"representation_kind": "ORIGINAL_WORK", "edition_or_version": "fixture-1", "consulted_locator": f"fixture://{work_id}"}]},
        "dossier_stage": stage, "pending_items": [], "confidence": "HIGH", "created_at": "2026-08-12T20:00:00Z",
    }
    if stage == "RESEARCH_REVIEW_PENDING":
        dossier.update({
            "analysis_references": [{"analysis_id": f"A-{work_id}", "material_id": work_id}],
            "question_and_thesis_relation": {"central_question_ref": "question:EP-1", "provisional_thesis_ref": "thesis:1", "demonstrates_analysis_ref": f"A-{work_id}", "does_not_establish_analysis_ref": f"A-{work_id}", "main_interpretation_analysis_ref": f"A-{work_id}", "rival_interpretation_analysis_refs": [f"A-{work_id}"]},
            "claim_dispositions": {"claims_ledger_id": "CL-1", "authority_status": "REPRESENTATION_ONLY_IR4_PENDING", "candidate_allowed_claim_ids": ["C-1"], "candidate_limited_claim_ids": [], "candidate_blocked_claim_ids": []},
            "overinterpretation_risk": {"level": "LOW", "rationale": "Fixture técnica."},
            "candidate_editorial_function_analysis_ref": f"A-{work_id}", "locators": [{"analysis_id": f"A-{work_id}", "locator": f"fixture://{work_id}/scene"}],
            "work_use_sufficiency": {"intended_use": "B5_I2_CONTROLLED_HARNESS", "status": "IR7_FIDELITY_AUDIT_REQUIRED"},
            "research_stop_decision_ref": f"RSD-{work_id}", "independent_fidelity_audit": {"audit_reference": None, "dependency": "FUNCTIONAL_DECISION_REQUIRED"},
        })
    return dossier


def _final_dossiers():
    return [_dossier(work_id) for work_id in ("W1", "W2", "W3")]


def _dossier_artifacts(work_id="W1"):
    analysis = {
        "analysis_id": f"A-{work_id}", "artifact_version": "1.0.0", "episode_id": "EP-1", "research_id": "R-1",
        "evidence_report_id": f"ER-{work_id}", "semantic_audit_id": f"SA-{work_id}", "material_id": work_id,
        "material_checksum": "a" * 64, "inherited_constraint_ids": [],
        "findings": [{"finding_id": f"F-{work_id}", "claim_type": "INTERPRETATION", "statement": "Lectura.", "narrative_evidence_refs": ["NE-1"], "source_refs": ["S-1"], "human_dimension": "BELIEF", "causal_relation": "Relación.", "confidence": "HIGH"}],
        "rival_interpretations": ["Rival."], "rival_interpretation_status": "PRESENT", "rival_interpretation_justification": None,
        "limitations": ["Límite."], "limits_status": "PRESENT", "limits_justification": None,
        "demonstrates": "Demuestra.", "does_not_establish": "No demuestra.", "material_function_candidate": "Complicación",
        "specific_scene_or_passage": "Escena 3", "observable_decision_or_action": "Decisión.", "conflict": "Conflicto.",
        "consequence": "Consecuencia.", "main_interpretation": "Interpretación.", "supporting_evidence": [f"F-{work_id}"],
        "interpretive_limit": "Límite.", "relationship_to_provisional_thesis": "Relación.",
        "potential_contribution_to_progression": "Aporta.", "created_at": "2026-08-12T20:00:00Z",
    }
    ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{
        "claim_id": "C-1", "script_location": "B1", "claim_text": "Claim", "claim_type": "FACT",
        "source_refs": ["S-1"], "verification_status": "VERIFIED", "materiality": {
            "is_material": True, "activation_criteria": ["THESIS_DEPENDENCY"], "non_trigger_examples": ["Fixture"],
            "invalidator_codes": ["NEW_MATERIAL_EVIDENCE"], "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_ref": "DEC-1",
        },
    }]}
    return {"claims_ledger": ledger, "narrative_analyses": [analysis]}


def _finalist_pack_with_resolved_references():
    data = _screened_pack()
    work = data["works"][0]
    work.update({"state": "FINALIST_WORK", "dossier_ref": "D-W1"})
    data["transitions"].append(_transition("W1", "SCREENED_WORK", "FINALIST_WORK"))
    dossier = _dossier("W1")
    artifacts = _dossier_artifacts()
    analysis = artifacts["narrative_analyses"][0]
    dossier["analysis_references"][0].update({
        "artifact_version": analysis["artifact_version"],
        "artifact_checksum": hashlib.sha256(json.dumps(analysis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
    })
    artifacts["claims_ledger"]["claims"][0]["claim_id"] = "C-1"
    artifacts["claims_ledger"]["script_version"] = "1.0.0"
    dossier["claim_dispositions"].update({
        "claims_ledger_version": "1.0.0",
        "claims_ledger_checksum": hashlib.sha256(json.dumps(artifacts["claims_ledger"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
    })
    return data, [dossier], {"D-W1": artifacts}


def _doubt(status="ACTIVE", **overrides):
    value = {
        "doubt_id": "D-1", "decision_id": "SP-IR0-CRITICAL_WORK_DOUBT", "decision_version": "1.0.0", "work_id": "W1",
        "authorization_status": status,
        "activation_criteria": ["SCREENING_DECISION_BLOCKED"] if status == "ACTIVE" else [],
        "non_trigger_examples": ["WORK_POPULARITY"] if status == "NOT_ACTIVATED" else [],
        "invalidators": ["QUESTION_RESOLVED"] if status == "INVALIDATED" else [],
        "evidence_refs": ["evidence:doubt"] if status == "ACTIVE" else [],
        "scope": "Confirmar si la escena existe y decide el screening.",
        "authorized_actions": ["REQUIRE_MORE_TARGETED_RESEARCH"] if status == "ACTIVE" else [],
        "authorization_ref": "authorization:doubt-1" if status == "ACTIVE" else None,
        "outcome": "REQUIRE_MORE_TARGETED_RESEARCH" if status == "ACTIVE" else "NOT_APPLICABLE",
        "return_route": "MORE_TARGETED_RESEARCH_REQUIRED" if status == "ACTIVE" else "RETURN_TO_SCREENING",
        "return_trigger": None,
    }
    value.update(overrides)
    return value


def test_discovered_to_screened_is_valid():
    assert validate_work_lifecycle(_screened_pack()) == []


def test_screened_to_finalist_requires_dossier_reference():
    data = _screened_pack()
    work = data["works"][0]
    work.update({"state": "FINALIST_WORK", "screening_ref": "screening:W1"})
    data["transitions"].append(_transition("W1", "SCREENED_WORK", "FINALIST_WORK"))
    assert any("WorkResearchDossier" in item for item in validate_work_lifecycle(data))


def test_finalist_to_final_selected_requires_curation_and_function():
    data, curation = _final_pack(); dossiers = _final_dossiers()
    violations = validate_work_lifecycle(data, dossiers=dossiers, material_curation=curation)
    assert any("FUNCTIONAL_DECISION_REQUIRED" in item for item in violations)


def test_finalist_promotion_is_valid_when_dossier_references_resolve():
    data, dossiers, artifacts = _finalist_pack_with_resolved_references()
    assert validate_work_lifecycle(data, dossiers=dossiers, dossier_artifacts=artifacts) == []


def test_final_selected_with_identified_dossier_fails_closed():
    data, curation = _final_pack(); dossiers = _final_dossiers()
    dossiers[0] = _dossier("W1", stage="IDENTIFIED")
    violations = validate_work_lifecycle(data, dossiers=dossiers, material_curation=curation)
    assert any("RESEARCH_REVIEW_PENDING" in item for item in violations)


def test_finalist_without_dossier_collection_fails_closed():
    data, curation = _final_pack()
    assert any("colección de WorkResearchDossier" in item for item in validate_work_lifecycle(data, material_curation=curation))


def test_final_selected_dossier_identity_and_research_context_must_match():
    data, curation = _final_pack(); dossiers = _final_dossiers()
    dossiers[0] = _dossier("OTHER", episode_id="EP-OTHER", research_id="R-OTHER")
    dossiers[0]["dossier_id"] = "D-W1"
    violations = validate_work_lifecycle(data, dossiers=dossiers, material_curation=curation)
    assert any("episode_id" in item for item in violations)
    assert any("research_id" in item for item in violations)
    assert any("difieren para la obra 'W1'" in item for item in violations)


def test_promotional_jumps_fail_closed():
    data = _screened_pack()
    data["works"][0].update({"state": "FINALIST_WORK", "dossier_ref": "D-W1"})
    data["transitions"] = [_transition("W1", "DISCOVERED_WORK", "FINALIST_WORK")]
    assert validate_work_lifecycle(data)
    data["works"][0].update({"state": "FINAL_SELECTED_WORK", "differentiated_function_ref": "f", "comparative_decision_ref": "c"})
    data["transitions"] = [_transition("W1", "SCREENED_WORK", "FINAL_SELECTED_WORK")]
    assert validate_work_lifecycle(data)


def test_anchor_does_not_promote_without_transition():
    data = _screened_pack()
    data["entry_mode"] = "ANCHOR_WORK_FIRST"
    data["anchor_work_id"] = "W1"
    data["works"][0].update({"is_anchor": True, "state": "FINALIST_WORK", "dossier_ref": "D-W1"})
    data["transitions"] = []
    assert any("promocionada" in item for item in validate_work_lifecycle(data))


def test_transition_requires_reason_evidence_authority_and_version():
    data = _screened_pack()
    transition = data["transitions"][0]
    transition.pop("transition_reason")
    transition.pop("evidence_refs")
    transition.pop("transition_authority_ref")
    transition.pop("input_version_refs")
    assert validate_work_lifecycle(data)


def test_reopened_is_not_a_primary_state():
    data = _screened_pack()
    data["works"][0]["state"] = "REOPENED"
    assert validate_against_schema(data, "work_lifecycle")


def test_reopened_preserves_lineage_and_return_state():
    data = _screened_pack()
    data["works"][0]["state"] = "SCREENED_WORK"
    other_work_transitions = [item for item in data["transitions"] if item["work_id"] != "W1"]
    data["transitions"] = other_work_transitions + [_transition("W1", "DISCOVERED_WORK", "EXCLUDED_WORK", "EXCLUSION", transition_id="T-EXCLUDED"), _transition("W1", "EXCLUDED_WORK", "SCREENED_WORK", "REOPENED", previous_transition_ref="T-EXCLUDED", authorized_return_state="SCREENED_WORK", transition_id="T-REOPENED")]
    assert validate_work_lifecycle(data) == []


def test_derived_states_require_real_history():
    for state in ("SCREENED_WORK", "EXCLUDED_WORK", "INVALIDATED_WORK"):
        data = _screened_pack()
        data["works"][0]["state"] = state
        data["transitions"] = [item for item in data["transitions"] if item["work_id"] != "W1"]
        assert validate_work_lifecycle(data)


def test_reopened_to_discovered_cannot_hide_truncated_origin_history():
    data = _screened_pack()
    other_work_transitions = [item for item in data["transitions"] if item["work_id"] != "W1"]
    data["works"][0]["state"] = "DISCOVERED_WORK"
    data["transitions"] = other_work_transitions + [
        _transition("W1", "SCREENED_WORK", "INVALIDATED_WORK", "INVALIDATION", transition_id="T-INVALIDATED"),
        _transition("W1", "INVALIDATED_WORK", "DISCOVERED_WORK", "REOPENED", previous_transition_ref="T-INVALIDATED", authorized_return_state="DISCOVERED_WORK", transition_id="T-REOPENED"),
    ]
    assert validate_work_lifecycle(data)


def test_reopened_requires_existing_same_work_prior_transition():
    data = _screened_pack()
    data["transitions"] = [
        _transition("W1", "DISCOVERED_WORK", "EXCLUDED_WORK", "EXCLUSION", transition_id="T-EXCLUDED"),
        _transition("W1", "EXCLUDED_WORK", "SCREENED_WORK", "REOPENED", previous_transition_ref="MISSING", authorized_return_state="SCREENED_WORK", transition_id="T-REOPENED"),
    ]
    assert validate_work_lifecycle(data)
    data["transitions"][1]["previous_transition_ref"] = "T-W2"
    data["transitions"].insert(1, _transition("W2", "DISCOVERED_WORK", "EXCLUDED_WORK", "EXCLUSION", transition_id="T-W2"))
    assert validate_work_lifecycle(data)


def test_reopened_must_reference_immediate_prior_transition_after_two_reopenings():
    data = _screened_pack()
    other_work_transitions = [item for item in data["transitions"] if item["work_id"] != "W1"]
    data["works"][0]["state"] = "SCREENED_WORK"
    data["transitions"] = other_work_transitions + [
        _transition("W1", "DISCOVERED_WORK", "EXCLUDED_WORK", "EXCLUSION", transition_id="T-EXCLUDED-1"),
        _transition("W1", "EXCLUDED_WORK", "SCREENED_WORK", "REOPENED", previous_transition_ref="T-EXCLUDED-1", authorized_return_state="SCREENED_WORK", transition_id="T-REOPENED-1"),
        _transition("W1", "SCREENED_WORK", "EXCLUDED_WORK", "EXCLUSION", transition_id="T-EXCLUDED-2"),
        _transition("W1", "EXCLUDED_WORK", "SCREENED_WORK", "REOPENED", previous_transition_ref="T-EXCLUDED-1", authorized_return_state="SCREENED_WORK", transition_id="T-REOPENED-2"),
    ]
    assert validate_work_lifecycle(data)


def test_transition_ids_must_be_unique():
    data = _screened_pack()
    data["transitions"][1]["transition_id"] = data["transitions"][0]["transition_id"]
    assert validate_work_lifecycle(data)


def test_transition_authority_must_resolve_to_script_product_registry_entry():
    data = _screened_pack()
    data["transitions"][0]["authority_role"] = "ANY_RANDOM_ROLE"
    data["transitions"][0]["transition_authority_ref"] = "fake:anything"
    assert validate_work_lifecycle(data)
    data["transitions"][0]["authority_role"] = "ORCHESTRATION"
    data["transitions"][0]["transition_authority_ref"] = "config/responsibility_registry.json#responsibilities/ORCHESTRATION"
    assert validate_work_lifecycle(data)
    data["transitions"][0]["authority_role"] = "RESEARCH_AND_CURATION"
    data["transitions"][0]["transition_authority_ref"] = "fake:anything"
    assert validate_work_lifecycle(data)


def test_transition_history_must_be_contiguous():
    data = _screened_pack()
    data["transitions"] = [_transition("W1", "DISCOVERED_WORK", "SCREENED_WORK", transition_id="T-1"), _transition("W1", "DISCOVERED_WORK", "FINALIST_WORK", transition_id="T-2")]
    data["works"][0].update({"state": "FINALIST_WORK", "dossier_ref": "D-W1"})
    assert any("continuidad" in item for item in validate_work_lifecycle(data))


def test_exclusion_and_invalidation_types_have_matching_targets():
    data = _screened_pack()
    data["transitions"][0] = _transition("W1", "DISCOVERED_WORK", "SCREENED_WORK", "EXCLUSION")
    assert validate_work_lifecycle(data)
    data["transitions"][0] = _transition("W1", "DISCOVERED_WORK", "SCREENED_WORK", "INVALIDATION")
    assert validate_work_lifecycle(data)


def test_stage_depth_is_progressive_and_structural():
    data = _screened_pack()
    data["works"][0]["screening_ref"] = None
    assert validate_work_lifecycle(data)
    data["works"][0].update({"state": "FINALIST_WORK", "dossier_ref": None})
    assert validate_work_lifecycle(data)
    data["works"][0].update({"state": "FINAL_SELECTED_WORK", "dossier_ref": "D-W1", "differentiated_function_ref": None, "comparative_decision_ref": None})
    assert validate_work_lifecycle(data)


def test_critical_doubt_authorizes_focused_research_only():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt()]
    assert validate_work_lifecycle(data) == []


def test_resolved_critical_doubt_requires_evidence_and_return_route():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt(
        "RESOLVED",
        activation_criteria=["SCREENING_DECISION_BLOCKED"],
        authorization_ref="authorization:doubt-1",
        authorized_actions=["CONTINUE_SCREENING"],
        evidence_refs=["evidence:doubt-resolved"],
        outcome="CONTINUE_SCREENING",
        return_route="RETURN_TO_SCREENING",
    )]
    assert validate_work_lifecycle(data) == []
    data["critical_doubts"][0]["evidence_refs"] = []
    assert validate_work_lifecycle(data)


def test_external_critical_doubt_routes_require_exact_trigger():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt(
        "INVALIDATED",
        invalidators=["IDENTITY_OR_SCOPE_REVIEW_REQUIRED"],
        return_trigger="MATERIAL_QUESTION_INTENT_TERRITORY_CHANGE",
        return_route="CHANNEL_INTELLIGENCE_REVIEW_REQUIRED",
    )]
    assert validate_work_lifecycle(data) == []
    data["critical_doubts"][0]["return_route"] = "YOUTUBE_ADAPTATION_REVIEW_REQUIRED"
    assert validate_work_lifecycle(data)
    data["critical_doubts"][0]["return_trigger"] = "VISIBLE_PROMISE_OR_EARLY_PACKAGING_IMPACT"
    assert validate_work_lifecycle(data) == []
    data["critical_doubts"][0]["return_route"] = "RETURN_TO_SCREENING"
    assert validate_work_lifecycle(data)


def test_external_route_without_trigger_cannot_pass():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt("INVALIDATED", return_route="YOUTUBE_ADAPTATION_REVIEW_REQUIRED")]
    assert validate_work_lifecycle(data)


def test_critical_doubt_return_route_must_match_outcome():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt(return_route="RETURN_TO_SCREENING")]
    assert validate_work_lifecycle(data)


def test_non_trigger_does_not_authorize_critical_doubt():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt("NOT_ACTIVATED", authorized_actions=["REQUIRE_MORE_TARGETED_RESEARCH"])]
    assert validate_work_lifecycle(data)


def test_invalidated_doubt_cuts_authorization():
    data = _screened_pack()
    data["critical_doubts"] = [_doubt("INVALIDATED", authorization_ref="authorization:doubt-1")]
    assert validate_work_lifecycle(data)


def test_screening_normal_range_is_five_to_eight():
    assert validate_work_lifecycle(_screened_pack()) == []
    data = _screened_pack()
    data["screening"]["candidate_work_ids"] = ["W1", "W2", "W3", "W4"]
    assert validate_work_lifecycle(data)


def test_declared_set_cannot_be_not_applicable():
    data = _screened_pack()
    data["screening"]["range_status"] = "NOT_APPLICABLE"
    assert validate_work_lifecycle(data)


def test_explicit_exception_consumes_existing_authority_reference():
    data = _screened_pack()
    data["screening"]["candidate_work_ids"] = ["W1", "W2", "W3", "W4"]
    data["screening"]["range_status"] = "EXCEPTION"
    data["screening"]["exception"] = _exception()
    assert validate_work_lifecycle(data) == []


def test_implicit_exception_is_rejected():
    data = _screened_pack()
    data["screening"]["candidate_work_ids"] = ["W1", "W2", "W3", "W4"]
    assert validate_work_lifecycle(data)


def test_three_to_five_substantive_final_works_pass_with_curation():
    data, curation = _final_pack(); dossiers = _final_dossiers()
    assert any("FUNCTIONAL_DECISION_REQUIRED" in item for item in validate_work_lifecycle(data, dossiers=dossiers, material_curation=curation))


def test_decorative_work_cannot_complete_final_minimum():
    data, curation = _final_pack(); dossiers = _final_dossiers()
    curation["function_of_each_selected_material"] = curation["function_of_each_selected_material"][:2]
    assert validate_work_lifecycle(data, dossiers=dossiers, material_curation=curation)


def test_excluded_or_invalidated_work_cannot_reopen_directly_to_selected():
    data = _screened_pack()
    data["works"][0].update({"state": "FINAL_SELECTED_WORK", "dossier_ref": "D-W1", "differentiated_function_ref": "f", "comparative_decision_ref": "c"})
    data["transitions"] = [_transition("W1", "INVALIDATED_WORK", "FINAL_SELECTED_WORK", "REOPENED", previous_transition_ref="T-INVALID", authorized_return_state="FINAL_SELECTED_WORK")]
    assert validate_work_lifecycle(data)
