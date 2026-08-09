from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

import src.scripts.channel_intelligence as ci
from src.scripts.channel_intelligence import (
    active_profile,
    canonical_checksum,
    check_agents_profile_consistency,
    evaluate_topic_belonging_gate,
    validate_assessment,
    validate_capability_registry,
    validate_decision,
    validate_owner_decision,
    validate_topic_input,
)

ROOT = Path(__file__).parents[2]
TRIGGER_KEYS = ["political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change", "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change", "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory"]


def bind(data, kind, field):
    checksum = canonical_checksum(data, kind)
    if field != "unused": data[field] = checksum
    data["provenance"]["output_checksum"] = checksum
    return data


def topic_input(**overrides):
    profile = active_profile()
    data = {"topic_input_id":"TBI-001", **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")}, "topic":"Tema ordinario", "entry_mode":"ANCHOR_WORK_FIRST", "narrative_work":"Obra", "central_question":"Pregunta humana", "proposed_angle":"Ángulo interpretativo", "proposed_territory":"Individuo e identidad", "initial_evidence":["source-1"], "strategic_triggers":{key:False for key in TRIGGER_KEYS}, "submitted_at":"2026-07-31T10:00:00Z"}
    data.update(overrides); return data


def assessment(inp=None, **overrides):
    inp = inp or topic_input(); profile = active_profile()
    data = {"assessment_id":"TBA-001", "topic_input_id":inp["topic_input_id"], "producer_actor_id":"producer-1", "producer_run_id":"run-producer", "producer_role_id":"CHANNEL_INTELLIGENCE_PRODUCER", **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")}, **{key: inp[key] for key in ("topic", "narrative_work", "central_question", "proposed_angle", "proposed_territory", "initial_evidence", "strategic_triggers", "entry_mode")}, "sensitive_risks":[], "territory_classification":"ACTIVE", "identity_alignment":"ALIGNED", "promise_alignment":"ALIGNED", "risks":[], "recommended_conditions":[], "recommended_exclusions":[], "owner_escalation_recommended":False, "evidence":["source-1"], "status":"CLOSED_FOR_REVIEW", "artifact_checksum":"", "provenance":{"actor_id":"producer-1", "run_id":"run-producer", "role_id":"CHANNEL_INTELLIGENCE_PRODUCER", "input_checksums":["a"*64], "output_checksum":""}}
    data.update(overrides); return bind(data, "assessment", "artifact_checksum")


def decision(a, **overrides):
    profile = active_profile()
    data = {"decision_id":"TBD-001", "assessment_id":a["assessment_id"], **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")}, "producer_artifact_checksum":a["artifact_checksum"], "reviewer_actor_id":"reviewer-1", "reviewer_run_id":"run-reviewer", "reviewer_role_id":"CHANNEL_INTELLIGENCE_REVIEWER", "reviewer_input_checksum":a["artifact_checksum"], "decision":"APPROVE", "conditions":[], "exclusions":[], "risks":[], "owner_escalation_required":False, "owner_escalation_reason":"", "strategic_dimensions_affected":[], "temporary_or_permanent_effect":"NONE", "precedent_risk":"LOW", "evidence":["source-1"], "decided_at":"2026-07-31T10:00:00Z", "provenance":{"actor_id":"reviewer-1", "run_id":"run-reviewer", "role_id":"CHANNEL_INTELLIGENCE_REVIEWER", "input_checksum":a["artifact_checksum"], "output_checksum":""}}
    data.update(overrides); return bind(data, "decision", "unused")


def owner(inp, a, d, **overrides):
    profile=active_profile()
    data={"owner_decision_id":"TBO-001", "topic_input_id":inp["topic_input_id"], "assessment_id":a["assessment_id"], "review_decision_id":d["decision_id"], **{key:profile[key] for key in ("profile_id","profile_version","profile_checksum")}, "assessment_checksum":a["artifact_checksum"], "review_decision_checksum":d["provenance"]["output_checksum"], "owner_actor_id":"owner-1", "decision":"OWNER_APPROVE", "conditions":[], "limitations":[], "decided_at":"2026-07-31T10:00:00Z", "owner_decision_checksum":"", "provenance":{"actor_id":"owner-1","output_checksum":""}}
    data.update(overrides); return bind(data,"owner_decision","owner_decision_checksum")


def test_active_profile_documentation_is_consistent(): assert check_agents_profile_consistency() == []
def test_topic_input_is_dynamic_but_bound_to_active_pointer():
    assert validate_topic_input(topic_input()) == []
    assert "INPUT_PROFILE_VERSION_MISMATCH" in validate_topic_input(topic_input(profile_version="9.9.9"))
def test_ordinary_topic_has_valid_segregated_flow():
    inp=topic_input(); a=assessment(inp); d=decision(a)
    assert validate_assessment(a, inp) == []
    assert validate_decision(d, a) == []
    assert evaluate_topic_belonging_gate(d,a,inp)["status"] == "PASS"
def test_self_approval_same_run_and_checksum_mismatch_are_blocked():
    a=assessment(); d=decision(a, reviewer_actor_id=a["producer_actor_id"], reviewer_run_id=a["producer_run_id"], reviewer_input_checksum="b"*64)
    d["provenance"]["input_checksum"]="b"*64; d=bind(d,"decision","unused")
    violations=validate_decision(d,a)
    assert "SELF_APPROVAL_BLOCKED" in violations and "SAME_RUN_REVIEW_BLOCKED" in violations
    assert "DECISION_REVIEWER_INPUT_CHECKSUM_MISMATCH" in violations
def test_tampering_assessment_or_decision_is_blocked():
    a=assessment(); a["topic"]="modificado"; assert "ASSESSMENT_ARTIFACT_CHECKSUM_INVALID" in validate_assessment(a)
    a=assessment(); d=decision(a); d["evidence"].append("other"); assert "DECISION_PROVENANCE_OUTPUT_CHECKSUM_INVALID" in validate_decision(d,a)
def test_each_structured_strategic_trigger_requires_escalation():
    for trigger in TRIGGER_KEYS:
        inp=topic_input(strategic_triggers={key:key==trigger for key in TRIGGER_KEYS}); a=assessment(inp, owner_escalation_recommended=True); d=decision(a)
        violations=validate_decision(d,a)
        assert any(v.startswith("OWNER_ESCALATION_REQUIRED") for v in violations), trigger
        assert any(v.startswith("OWNER_ESCALATION_DECISION_REQUIRED") for v in violations), trigger
def test_owner_decision_completes_only_escalated_flow():
    inp=topic_input(strategic_triggers={key:key=="experimental_territory" for key in TRIGGER_KEYS}); a=assessment(inp, territory_classification="EXPERIMENTAL", owner_escalation_recommended=True); d=decision(a, decision="ESCALATE_TO_OWNER", owner_escalation_required=True, owner_escalation_reason="Territorio experimental")
    o=owner(inp,a,d)
    assert validate_owner_decision(o,inp,a,d) == []
    result=evaluate_topic_belonging_gate(d,a,inp,o)
    assert result["status"] == "PASS" and result["production_authorized"] is False and result["publication_authorized"] is False
def test_non_approval_outcomes_never_pass_gate():
    a=assessment(); inp=topic_input()
    for outcome in ("REQUEST_MORE_EVIDENCE","REJECT","BLOCK"):
        assert evaluate_topic_belonging_gate(decision(a,decision=outcome),a,inp)["status"] == "BLOCKED"
def test_approval_with_conditions_requires_conditions():
    a=assessment(); inp=topic_input()
    assert evaluate_topic_belonging_gate(decision(a,decision="APPROVE_WITH_CONDITIONS"),a,inp)["status"] == "BLOCKED"
    assert evaluate_topic_belonging_gate(decision(a,decision="APPROVE_WITH_CONDITIONS",conditions=["Mantener el Ángulo dentro del territorio activo"]),a,inp)["status"] == "PASS"
def test_capability_registry_is_operational_and_routing_exists():
    assert validate_capability_registry() == []
    routing=yaml.safe_load((ROOT/'config/capability_routing.yaml').read_text(encoding='utf-8'))
    assert (ROOT/routing['capabilities']['TOPIC_BELONGING_ASSESSMENT']['entrypoint']).is_file()
def test_policy_and_prompts_reference_active_compiled_profile():
    policy=(ROOT/'policies/channel_intelligence/topic_belonging_policy.md').read_text(encoding='utf-8')
    assert 'compiled_profile_path' in policy and 'ESCALATE_TO_OWNER' in policy
    for role in ('CHANNEL_INTELLIGENCE_PRODUCER','CHANNEL_INTELLIGENCE_REVIEWER'):
        prompt=(ROOT/f'prompts/roles/{role}/1.0.0.md').read_text(encoding='utf-8')
        assert 'topic_belonging_policy.md' in prompt and 'perfil' in prompt
