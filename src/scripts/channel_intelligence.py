from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.capability_governance import validate_capability_registry as validate_capability_registry_core

ACTIVE = ROOT / "config" / "active_editorial_profile.json"
REGISTRY = ROOT / "config" / "editorial_profile_registry.json"
CORPUS = ROOT / "profiles" / "voice" / "corpus_manifest.json"
AGENTS = ROOT / "AGENTS.md"
CAPABILITIES = ROOT / "config" / "capability_registry.json"
ROUTING = ROOT / "config" / "capability_routing.yaml"
RESPONSIBILITIES = ROOT / "config" / "responsibility_registry.json"
PROMPTS = ROOT / "config" / "agent_prompt_registry.json"
RUNTIME = ROOT / "config" / "ai_runtime.example.json"
EXECUTION_PROFILES = ROOT / "config" / "agent_execution_profiles.json"
STRATEGIC_TERRITORIES = {"EXPERIMENTAL"}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_payload(data: dict[str, Any], artifact_kind: str) -> dict[str, Any]:
    payload = copy.deepcopy(data)
    provenance = payload.get("provenance")
    if artifact_kind == "assessment":
        payload.pop("artifact_checksum", None)
    elif artifact_kind == "owner_decision":
        payload.pop("owner_decision_checksum", None)
    elif artifact_kind == "input":
        pass
    elif artifact_kind != "decision":
        raise ValueError(f"Unsupported artifact kind: {artifact_kind}")
    if isinstance(provenance, dict):
        provenance.pop("output_checksum", None)
    return payload


def canonical_checksum(data: dict[str, Any], artifact_kind: str) -> str:
    serialized = json.dumps(canonical_payload(data, artifact_kind), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def active_profile() -> dict[str, str]:
    active, registry = _load(ACTIVE), _load(REGISTRY)
    key = registry.get("active_profile_key", "")
    entry = registry.get("profiles", {}).get(key, {})
    return {"profile_id": active.get("ACTIVE_PROFILE_ID", ""), "profile_version": active.get("ACTIVE_PROFILE_VERSION", ""), "profile_checksum": active.get("profile_checksum", ""), "registry_key": key, "registry_checksum": entry.get("checksum", ""), "compiled_profile_path": entry.get("compiled_profile_path", "")}


def check_agents_profile_consistency() -> list[str]:
    violations: list[str] = []
    text = AGENTS.read_text(encoding="utf-8")
    if "ACTIVE_EDITORIAL_PROFILE_AUTHORITY = config/active_editorial_profile.json" not in text:
        violations.append("ACTIVE_PROFILE_DOCUMENTATION_MISMATCH: canonical pointer missing")
    if re.search(r"ACTIVE_EDITORIAL_PROFILE\s*=\s*(NONE|[A-Za-z0-9_.@-]+)", text):
        violations.append("ACTIVE_PROFILE_DOCUMENTATION_MISMATCH: mutable profile declaration duplicated")
    profile = active_profile()
    if profile["registry_key"] != f"{profile['profile_id']}@{profile['profile_version']}":
        violations.append("ACTIVE_PROFILE_REGISTRY_MISMATCH")
    if profile["registry_checksum"] != profile["profile_checksum"]:
        violations.append("ACTIVE_PROFILE_CHECKSUM_MISMATCH")
    if not profile["compiled_profile_path"] or not (ROOT / profile["compiled_profile_path"]).is_file():
        violations.append("ACTIVE_PROFILE_COMPILED_PATH_MISSING")
    corpus = _load(CORPUS)
    if corpus.get("status") != "AUTHENTIC_CORPUS_PARTIAL":
        violations.append("VOICE_CORPUS_STATE_MISMATCH")
    if corpus.get("GLOBAL_VOICE_REPRESENTATIVENESS") != "NOT_VALIDATED":
        violations.append("GLOBAL_VOICE_REPRESENTATIVENESS_MISMATCH")
    return violations


def _profile_binding(data: dict[str, Any], prefix: str) -> list[str]:
    profile = active_profile()
    return [f"{prefix}_{key.upper()}_MISMATCH" for key in ("profile_id", "profile_version", "profile_checksum") if data.get(key) != profile[key]]


def _entry_mode_violations(data: dict[str, Any]) -> list[str]:
    mode, work = data.get("entry_mode"), data.get("narrative_work")
    if not mode:
        return []
    if mode == "TOPIC_FIRST" and work in (None, "", "NO_WORK_YET"):
        return []
    if mode == "ANCHOR_WORK_FIRST" and work in (None, "", "NO_WORK_YET"):
        return ["ENTRY_MODE_REQUIRES_ANCHOR_WORK"]
    if mode == "CORPUS_FIRST" and not data.get("corpus_ref"):
        return ["ENTRY_MODE_REQUIRES_CORPUS"]
    return []

def validate_topic_input(data: dict[str, Any]) -> list[str]:
    violations = validate_against_schema(data, "topic_belonging_input")
    violations.extend(_profile_binding(data, "INPUT"))
    violations.extend(_entry_mode_violations(data))
    return violations


def strategic_trigger_names(assessment: dict[str, Any]) -> list[str]:
    triggers = assessment.get("strategic_triggers", {})
    return [name.upper() for name, value in triggers.items() if value]


def validate_assessment(data: dict[str, Any], topic_input: dict[str, Any] | None = None) -> list[str]:
    violations = validate_against_schema(data, "topic_belonging_assessment")
    violations.extend(_profile_binding(data, "ASSESSMENT"))
    violations.extend(_entry_mode_violations(data))
    provenance = data.get("provenance", {})
    if provenance.get("actor_id") != data.get("producer_actor_id") or provenance.get("run_id") != data.get("producer_run_id"):
        violations.append("ASSESSMENT_PROVENANCE_MISMATCH")
    expected = canonical_checksum(data, "assessment")
    if data.get("artifact_checksum") != expected:
        violations.append("ASSESSMENT_ARTIFACT_CHECKSUM_INVALID")
    if provenance.get("output_checksum") != expected:
        violations.append("ASSESSMENT_PROVENANCE_OUTPUT_CHECKSUM_INVALID")
    if data.get("status") != "CLOSED_FOR_REVIEW":
        violations.append("ASSESSMENT_NOT_CLOSED")
    strategic = strategic_trigger_names(data)
    if data.get("territory_classification") in STRATEGIC_TERRITORIES:
        strategic.append("EXPERIMENTAL_TERRITORY")
    if strategic and not data.get("owner_escalation_recommended"):
        violations.append("ASSESSMENT_STRATEGIC_ESCALATION_REQUIRED")
    if topic_input is not None:
        violations.extend(f"INPUT_INVALID: {v}" for v in validate_topic_input(topic_input))
        for key in ("topic_input_id", "profile_id", "profile_version", "profile_checksum", "topic", "entry_mode", "corpus_ref", "narrative_work", "central_question", "proposed_angle", "proposed_territory", "initial_evidence", "strategic_triggers"):
            if key == "narrative_work" and data.get("entry_mode") == "TOPIC_FIRST":
                # TOPIC_FIRST may acquire a work during research without changing entry mode.
                if data.get(key) not in (None, "", "NO_WORK_YET") and topic_input.get(key) not in (None, "", "NO_WORK_YET", data.get(key)):
                    violations.append(f"ASSESSMENT_INPUT_{key.upper()}_MISMATCH")
                continue
            if data.get(key) != topic_input.get(key):
                violations.append(f"ASSESSMENT_INPUT_{key.upper()}_MISMATCH")
    return violations


def escalation_reasons(decision: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    reasons = strategic_trigger_names(assessment)
    if assessment.get("territory_classification") in STRATEGIC_TERRITORIES:
        reasons.append("EXPERIMENTAL_TERRITORY")
    if assessment.get("owner_escalation_recommended"):
        reasons.append("PRODUCER_ESCALATION_RECOMMENDED")
    if decision.get("temporary_or_permanent_effect") == "PERMANENT":
        reasons.append("PERMANENT_EFFECT")
    if decision.get("precedent_risk") == "HIGH":
        reasons.append("HIGH_PRECEDENT_RISK")
    if decision.get("strategic_dimensions_affected"):
        reasons.append("STRATEGIC_DIMENSIONS_AFFECTED")
    return sorted(set(reasons))


def validate_decision(data: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    violations = validate_against_schema(data, "topic_belonging_decision")
    violations.extend(f"ASSESSMENT_INVALID: {v}" for v in validate_assessment(assessment))
    violations.extend(_profile_binding(data, "DECISION"))
    if data.get("assessment_id") != assessment.get("assessment_id"):
        violations.append("DECISION_ASSESSMENT_ID_MISMATCH")
    for key in ("producer_artifact_checksum", "reviewer_input_checksum"):
        if data.get(key) != assessment.get("artifact_checksum"):
            violations.append(f"DECISION_{key.upper()}_MISMATCH")
    if data.get("reviewer_actor_id") == assessment.get("producer_actor_id"):
        violations.append("SELF_APPROVAL_BLOCKED")
    if data.get("reviewer_run_id") == assessment.get("producer_run_id"):
        violations.append("SAME_RUN_REVIEW_BLOCKED")
    provenance = data.get("provenance", {})
    if provenance.get("input_checksum") != assessment.get("artifact_checksum"):
        violations.append("DECISION_PROVENANCE_INPUT_CHECKSUM_MISMATCH")
    expected = canonical_checksum(data, "decision")
    if provenance.get("output_checksum") != expected:
        violations.append("DECISION_PROVENANCE_OUTPUT_CHECKSUM_INVALID")
    reasons = escalation_reasons(data, assessment)
    if reasons:
        if not data.get("owner_escalation_required"):
            violations.append(f"OWNER_ESCALATION_REQUIRED: {','.join(reasons)}")
        if data.get("decision") != "ESCALATE_TO_OWNER":
            violations.append(f"OWNER_ESCALATION_DECISION_REQUIRED: {','.join(reasons)}")
        if not data.get("owner_escalation_reason", "").strip():
            violations.append("OWNER_ESCALATION_REASON_REQUIRED")
    elif data.get("owner_escalation_required") != (data.get("decision") == "ESCALATE_TO_OWNER"):
        violations.append("OWNER_ESCALATION_FLAG_DECISION_MISMATCH")
    if data.get("decision") == "APPROVE" and (assessment.get("territory_classification") != "ACTIVE" or assessment.get("identity_alignment") != "ALIGNED" or assessment.get("promise_alignment") != "ALIGNED"):
        violations.append("APPROVE_REQUIRES_ACTIVE_FULL_ALIGNMENT")
    if data.get("decision") == "APPROVE_WITH_CONDITIONS" and not data.get("conditions"):
        violations.append("APPROVE_WITH_CONDITIONS_REQUIRES_CONDITIONS")
    return violations


def validate_owner_decision(data: dict[str, Any], topic_input: dict[str, Any], assessment: dict[str, Any], decision: dict[str, Any]) -> list[str]:
    violations = validate_against_schema(data, "topic_belonging_owner_decision")
    violations.extend(_profile_binding(data, "OWNER_DECISION"))
    if decision.get("decision") != "ESCALATE_TO_OWNER":
        violations.append("OWNER_DECISION_WITHOUT_ESCALATION")
    expected_bindings = {"topic_input_id": topic_input.get("topic_input_id"), "assessment_id": assessment.get("assessment_id"), "review_decision_id": decision.get("decision_id"), "assessment_checksum": assessment.get("artifact_checksum"), "review_decision_checksum": decision.get("provenance", {}).get("output_checksum")}
    for key, value in expected_bindings.items():
        if data.get(key) != value:
            violations.append(f"OWNER_DECISION_{key.upper()}_MISMATCH")
    expected = canonical_checksum(data, "owner_decision")
    if data.get("owner_decision_checksum") != expected or data.get("provenance", {}).get("output_checksum") != expected:
        violations.append("OWNER_DECISION_CHECKSUM_INVALID")
    if data.get("provenance", {}).get("actor_id") != data.get("owner_actor_id"):
        violations.append("OWNER_DECISION_PROVENANCE_MISMATCH")
    return violations


def gate_outcome_violations(decision: dict[str, Any], owner_decision: dict[str, Any] | None) -> list[str]:
    outcome = decision.get("decision")
    if outcome == "APPROVE": return []
    if outcome == "APPROVE_WITH_CONDITIONS": return [] if decision.get("conditions") else ["APPROVE_WITH_CONDITIONS_REQUIRES_CONDITIONS"]
    if outcome == "ESCALATE_TO_OWNER" and owner_decision and owner_decision.get("decision") == "OWNER_APPROVE": return []
    return [f"TOPIC_DECISION_NOT_APPROVED: {outcome}"]


def evaluate_topic_belonging_gate(
    decision: dict[str, Any],
    assessment: dict[str, Any],
    topic_input: dict[str, Any] | None = None,
    owner_decision: dict[str, Any] | None = None,
    work_lifecycle: dict[str, Any] | None = None,
    research_dossier: dict[str, Any] | None = None,
) -> dict[str, Any]:
    violations = validate_decision(decision, assessment)
    if topic_input is not None:
        violations.extend(f"ASSESSMENT_INVALID: {v}" for v in validate_assessment(assessment, topic_input))
    if owner_decision is not None:
        if topic_input is None: violations.append("OWNER_DECISION_REQUIRES_TOPIC_INPUT")
        else: violations.extend(validate_owner_decision(owner_decision, topic_input, assessment, decision))
    if decision.get("decision") == "ESCALATE_TO_OWNER" and owner_decision is None:
        violations.append("OWNER_DECISION_REQUIRED")
    if decision.get("decision") in {"APPROVE", "APPROVE_WITH_CONDITIONS"} and assessment.get("entry_mode") == "TOPIC_FIRST":
        evidence = decision.get("pre_b5_i1_evidence")
        if not isinstance(work_lifecycle, dict) or not isinstance(research_dossier, dict):
            violations.append("PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_MATERIAL_RESEARCH_BINDING")
        door_refs = evidence.get("narrative_door_evidence_refs", []) if isinstance(evidence, dict) else []
        candidate_refs = evidence.get("candidate_work_refs", []) if isinstance(evidence, dict) else []
        research_ref = evidence.get("research_ref") if isinstance(evidence, dict) else None
        enriched_input_checksum = evidence.get("topic_input_checksum") if isinstance(evidence, dict) else None
        if not isinstance(door_refs, list) or not door_refs or not all(isinstance(ref, str) and ref.strip() for ref in door_refs):
            violations.append("PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_NARRATIVE_DOOR")
        candidate_refs_valid = isinstance(candidate_refs, list) and all(isinstance(ref, str) and ref.strip() for ref in candidate_refs)
        if not candidate_refs_valid or not candidate_refs:
            violations.append("PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_SUFFICIENT_CANDIDATE_WORKS")
        candidate_count = len(candidate_refs) if candidate_refs_valid else 0
        screening = work_lifecycle.get("screening", {}) if isinstance(work_lifecycle, dict) else {}
        exception = screening.get("exception") if isinstance(screening, dict) else None
        exception_valid = isinstance(screening, dict) and screening.get("range_status") == "EXCEPTION" and isinstance(exception, dict) and bool(exception.get("owner_approval_ref")) and exception.get("functional_owner") == "SCRIPT_PRODUCT"
        if candidate_refs_valid and candidate_count not in range(5, 9) and not exception_valid:
            violations.append("PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_NORMAL_CANDIDATE_RANGE_OR_APPROVED_EXCEPTION")
        if not isinstance(research_ref, str) or not research_ref.strip():
            violations.append("PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_RESEARCH_EVIDENCE")
        if not topic_input or enriched_input_checksum != canonical_checksum(topic_input, "input"):
            violations.append("PRE_B5_I1_BELONGING_APPROVAL_REQUIRES_CURRENT_TOPIC_INPUT_CHECKSUM")
        if isinstance(topic_input, dict) and isinstance(evidence, dict):
            for field in ("research_ref", "narrative_door_evidence_refs", "candidate_work_refs"):
                if topic_input.get(field) != evidence.get(field):
                    violations.append(f"PRE_B5_I1_EVIDENCE_{field.upper()}_MISMATCH")
        if isinstance(work_lifecycle, dict) and isinstance(evidence, dict):
            screening = work_lifecycle.get("screening", {})
            lifecycle_candidates = screening.get("candidate_work_ids", []) if isinstance(screening, dict) else []
            if evidence.get("candidate_work_refs") != lifecycle_candidates:
                violations.append("PRE_B5_I1_EVIDENCE_CANDIDATES_NOT_BOUND_TO_WORK_LIFECYCLE")
        if isinstance(research_dossier, dict) and isinstance(evidence, dict):
            if evidence.get("research_ref") != research_dossier.get("research_id"):
                violations.append("PRE_B5_I1_EVIDENCE_RESEARCH_NOT_BOUND_TO_DOSSIER")
            if research_dossier.get("dossier_stage") not in {"IDENTIFIED", "RESEARCH_IN_PROGRESS"}:
                violations.append("PRE_B5_I1_RESEARCH_DOSSIER_STAGE_NOT_PRE_B5")
            if not research_dossier.get("evidence_report_id") or not set(evidence.get("narrative_door_evidence_refs", [])).intersection({str(research_dossier.get("evidence_report_id"))}):
                violations.append("PRE_B5_I1_NARRATIVE_DOOR_NOT_BOUND_TO_RESEARCH_EVIDENCE")
        if isinstance(work_lifecycle, dict) and isinstance(evidence, dict):
            if work_lifecycle.get("entry_mode") != "TOPIC_FIRST":
                violations.append("PRE_B5_I1_LIFECYCLE_ENTRY_MODE_MISMATCH")
            if work_lifecycle.get("research_id") != evidence.get("research_ref"):
                violations.append("PRE_B5_I1_LIFECYCLE_RESEARCH_MISMATCH")
    violations.extend(gate_outcome_violations(decision, owner_decision))
    return {"status": "PASS" if not violations else "BLOCKED", "decision": decision.get("decision"), "topic_belonging_approval": "NECESSARY_NOT_SUFFICIENT", "topic_approved": not violations, "production_authorized": False, "publication_authorized": False, "b5_i3_authorized": False, "r6_c_authorized": False, "s5_authorized": False, "violations": violations}


def validate_capability_registry() -> list[str]:
    import yaml
    violations = validate_capability_registry_core(CAPABILITIES)
    capability = next((x for x in _load(CAPABILITIES).get("capabilities", []) if x.get("capability_id") == "TOPIC_BELONGING_ASSESSMENT"), None)
    if not capability: return violations + ["TOPIC_BELONGING_CAPABILITY_MISSING"]
    routing = yaml.safe_load(ROUTING.read_text(encoding="utf-8")); route = routing.get("capabilities", {}).get("TOPIC_BELONGING_ASSESSMENT", {})
    if not route:
        violations.append("CAPABILITY_ROUTING_ENTRYPOINT_MISSING")
    elif capability.get("availability_status") != "NON_EXECUTABLE_CURRENT" and not (ROOT / route.get("entrypoint", "")).is_file():
        violations.append("CAPABILITY_ROUTING_ENTRYPOINT_MISSING")
    for ref in capability.get("dependencies", []) + [capability.get("input_contract", ""), capability.get("output_contract", "")]:
        if ref and ref != "DEFERRED" and not (ROOT / ref).is_file(): violations.append(f"CAPABILITY_REFERENCE_MISSING: {ref}")
    responsibility_roles = {x.get("role_id") for x in _load(RESPONSIBILITIES).get("responsibilities", [])}
    runtime_roles = {x.get("role_id") for x in _load(RUNTIME).get("entries", [])}
    execution_roles = set(_load(EXECUTION_PROFILES).get("role_defaults", {}))
    prompt_ids = {x.get("prompt_id") for x in _load(PROMPTS).get("prompts", [])}
    for role in capability.get("assigned_role", []):
        if role not in responsibility_roles or role not in runtime_roles or role not in execution_roles: violations.append(f"CAPABILITY_ROLE_NOT_OPERATIONAL: {role}")
    for prompt in capability.get("prompt_reference", []):
        if prompt not in prompt_ids: violations.append(f"CAPABILITY_PROMPT_MISSING: {prompt}")
    if capability.get("availability_status") == "ACTIVE" and capability.get("maturity_status") != "DEMONSTRATED": violations.append("ACTIVE_REQUIRES_DEMONSTRATED")
    return violations


def _result(violations: list[str], payload: dict[str, Any] | None = None) -> int:
    print(json.dumps({"status": "PASS" if not violations else "BLOCKED", "violations": violations, "payload": payload}, ensure_ascii=False))
    return 0 if not violations else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Channel Intelligence contract checks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-agents", action="store_true"); group.add_argument("--check-capability-registry", action="store_true"); group.add_argument("--input"); group.add_argument("--assessment"); group.add_argument("--decision")
    parser.add_argument("--assessment-input"); parser.add_argument("--owner-decision")
    args = parser.parse_args()
    if args.check_agents: return _result(check_agents_profile_consistency())
    if args.check_capability_registry: return _result(validate_capability_registry())
    if args.input: return _result(validate_topic_input(_load(Path(args.input))))
    if args.assessment: return _result(validate_assessment(_load(Path(args.assessment)), _load(Path(args.assessment_input)) if args.assessment_input else None))
    if not args.assessment_input: parser.error("--decision requires --assessment-input")
    decision, assessment = _load(Path(args.decision)), _load(Path(args.assessment_input))
    return _result(validate_decision(decision, assessment), decision)

if __name__ == "__main__": raise SystemExit(main())
