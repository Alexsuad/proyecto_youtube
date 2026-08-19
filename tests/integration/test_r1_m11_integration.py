"""Controlled technical integration cases for R1-M11."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from src.core.contract_validation import (
    validate_claims_ledger,
    validate_research_pack,
    validate_research_stop_decision,
    validate_work_lifecycle,
)
from src.core.editorial_semantic_memory import EditorialSemanticMemoryStore
from src.core.invalidation import InvalidationEngine
from src.core.plan_005_invariants import verify_invariants
from src.core.research_adapter import validate_optional_research_adapter
from src.core.research_audit import resolve_correction_routes, validate_independent_research_audit
from tests.core.test_r1_m6_m8 import _decision, _memory
from tests.core.test_r1_m7 import _contradiction
from tests.core.test_r1_m9 import _specialist
from tests.core.test_work_lifecycle import _doubt, _final_pack, _screened_pack
from tests.fixtures.synthetic_contracts import VALID_RESEARCH_PACK


def _derived_source(source_id: str, kind: str, parent: str, *, verified: bool, language: str) -> dict:
    return {
        "source_id": source_id,
        "title": f"{kind} fixture",
        "source_type": kind,
        "url": None,
        "access_type": "DIRECT",
        "locator": f"locator:{source_id}",
        "confidence": "HIGH",
        "provenance": {
            "source_kind": kind,
            "original_source_ref": "S1",
            "derived_from_source_ref": parent,
            "version": "1.0.0",
            "original_language": language,
            "derivative_language": "es" if kind == "TRANSLATION" else None,
            "locator": f"locator:{source_id}",
            "timestamp": {"start": "00:10", "end": "00:20"} if kind == "TRANSCRIPT" else None,
            "acquisition_method": "CONTROLLED_FIXTURE",
            "transformation_method": "MANUAL_TRANSCRIPTION" if kind == "TRANSCRIPT" else "CONTROLLED_TRANSLATION",
            "transcription_type": "MANUAL" if kind == "TRANSCRIPT" else "NOT_APPLICABLE",
            "verification_status": "PRIMARY_VERIFIED" if verified else "NOT_REVIEWED",
            "translation_transcription_risk": "LOW" if verified else "MATERIAL",
            "material_transcription_error": False,
            "limitations": [] if verified else ["Original wording not independently verified."],
            "permitted_uses": ["CONTEXT_ONLY"],
            "primary_verification_required": not verified,
            "primary_verification_performed": verified,
            "claim_authority": "PRIMARY" if verified else "SECONDARY",
            "authority_domain": "GENERAL",
            "official_primary": False,
        },
    }


def _integrated_research_pack() -> dict:
    pack = deepcopy(VALID_RESEARCH_PACK)
    original = deepcopy(pack["source_registry"][0])
    original["source_id"] = "S1"
    original["provenance"]["original_language"] = "en"
    pack["source_registry"] = [
        original,
        _derived_source("S2", "TRANSCRIPT", "S1", verified=True, language="en"),
        _derived_source("S3", "TRANSLATION", "S1", verified=False, language="en"),
    ]
    pack["facts"][0]["source_refs"] = ["S1"]
    pack["interpretations"][0]["source_refs"] = ["S1"]
    pack["narrative_evidence"][0]["source_refs"] = ["S1"]
    pack["external_reality_evidence"][0]["source_refs"] = ["S1"]
    pack["claims_candidates"] = [{
        "item_id": "C1",
        "statement": "Claim material de fixture.",
        "source_refs": ["S1"],
        "locator": "p. 10",
        "confidence": "HIGH",
    }]
    pack["critical_claims_assessment"] = {
        "status": "IDENTIFIED",
        "claim_ids": ["C1"],
        "justification": "El claim condiciona la tesis controlada.",
        "editorial_impact": "MATERIAL",
    }
    pack["alternative_views"] = [{
        "item_id": "RV1",
        "statement": "La lectura rival atribuye el efecto a una causa distinta.",
        "source_refs": ["S2"],
        "locator": "transcript:00:10",
        "confidence": "MEDIUM",
    }]
    pack["rival_analysis"] = [{
        "rival_explanation_id": "RIVAL-1",
        "statement": "La lectura rival conserva una explicacion causal alternativa.",
        "agreement_status": "DISAGREEMENT",
        "disagreement_kind": "RIVAL_OPEN",
        "claim_ids": ["C1"],
        "source_refs": ["S1", "S2"],
    }]
    pack["contradictions"] = [_contradiction()]
    pack["multilingual_research"] = {
        "activation_status": "ACTIVATED",
        "triggers": ["ORIGINAL_SOURCE_NOT_IN_SPANISH"],
        "non_trigger_examples": [],
        "affected_source_ids": ["S3"],
        "affected_claim_ids": ["C1"],
        "required_language": "en",
        "material_risk": ["CLAIM_VALIDITY", "WORK_INTERPRETATION"],
        "consultation_result": "LIMITED_BUT_USABLE",
        "limitations": ["La traduccion no sustituye el original para formulacion exacta."],
        "invalidators": ["TRANSLATED_CONTENT_NOT_VERIFIABLE"],
        "return_route": "LIMITED_BUT_USABLE",
        "decision_basis": "La formulacion original puede cambiar el uso previsto.",
    }
    pack["specialist_research"] = [_specialist()]
    return pack


def _material_claim_decision(**overrides) -> dict:
    return _decision(
        decision_id="RSD-C1",
        subject_ref="C1",
        evidence_refs=["S1"],
        **overrides,
    )


def _aggregate_decision(component: dict, **overrides) -> dict:
    fields = {
        "decision_id": "RSD-AGG",
        "subject_kind": "AGGREGATE_RESEARCH_PACK",
        "subject_ref": "RP-001",
        "claim_decision": None,
        "component_decision_refs": [component["decision_id"]],
        "required_component_decision_refs": [component["decision_id"]],
    }
    fields.update(overrides)
    return _decision(
        **fields,
    )


def _audit(**overrides) -> dict:
    value = {
        "audit_id": "AUDIT-R1-M11",
        "audit_version": "1.0.0",
        "episode_id": "EP-001",
        "audit_type": "RESEARCH_PACKAGE",
        "audited_artifacts": [{"artifact_id": "WORK-DOSSIER-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}],
        "producer": {"actor_id": "PRODUCER-1", "run_id": "RUN-P"},
        "auditor": {"actor_id": "AUDITOR-1", "run_id": "RUN-A"},
        "auditor_write_scope": "AUDIT_ONLY",
        "independence_result": "PASS",
        "findings": [{"criterion": "SCRIPT_PRODUCT_DEFINED_CRITERION", "status": "SATISFIED", "evidence_refs": ["WORK-DOSSIER-1"], "limitations": ["Fixture only."]}],
        "evidence_refs": ["WORK-DOSSIER-1"],
        "limitations": ["Synthetic fixture; no functional approval."],
        "defects": [],
        "correction_routes": [],
        "decision": "PASS",
        "created_at": "2026-08-18T12:00:00Z",
    }
    value.update(overrides)
    return value


def _adapter(**overrides) -> dict:
    value = {
        "adapter_id": "ADAPTER-FIXTURE-1",
        "contract_version": "1.0.0",
        "provider": "fixture-provider",
        "availability": "AVAILABLE",
        "source_refs": ["S1"],
        "findings": [{"finding_id": "AF-1", "statement": "Contexto recuperado.", "evidence_refs": ["S1"], "status": "LIMITED"}],
        "limitations": ["No convierte el hallazgo en verdad canonica."],
        "canonicality": "NOT_CANONICAL_MEMORY",
        "veracity_authority": "NOT_VERACITY_AUTHORITY",
        "gate_behavior": "NOT_REQUIRED_GATE",
        "decision_authority": "SCRIPT_PRODUCT",
    }
    value.update(overrides)
    return value


def test_case_a_positive_composes_r1_capabilities_without_editorial_approval() -> None:
    pack = _integrated_research_pack()
    assert validate_research_pack(pack) == []
    assert validate_research_pack(pack, research_adapter=_adapter()) == []

    ledger = {
        "ledger_id": "CL-001",
        "script_version": "1.0.0",
        "claims": [{
            "claim_id": "C1", "script_location": "controlled", "claim_text": "Claim material de fixture.",
            "claim_type": "FACT", "source_refs": ["S1"], "verification_status": "VERIFIED",
            "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT",
            "provenance_evidence_refs": ["S1"], "provenance_status": "PRIMARY_VERIFIED", "authority_basis": "PRIMARY_SOURCE",
            "claim_decision": "CLAIM_ALLOWED", "research_sufficiency": "SUFFICIENT_FOR_INTENDED_USE",
            "materiality": {"is_material": True, "activation_criteria": ["THESIS_DEPENDENCY"], "non_trigger_examples": ["Fixture detail"], "invalidator_codes": ["NEW_MATERIAL_EVIDENCE"], "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_ref": "RSD-C1"},
        }],
    }
    assert validate_claims_ledger(ledger) == []
    claim_decision = _material_claim_decision()
    aggregate = _aggregate_decision(claim_decision)
    assert validate_research_stop_decision(claim_decision) == []
    assert validate_research_stop_decision(aggregate, [claim_decision]) == []

    lifecycle, curation = _final_pack()
    lifecycle["critical_doubts"] = [_doubt(work_id="W4")]
    assert validate_work_lifecycle(lifecycle, material_curation=curation) == []
    assert validate_optional_research_adapter(None) == []

    memory = _memory()
    assert EditorialSemanticMemoryStore(memory).consult(
        memory["comparison_decisions"][0]["candidate_episode_ref"],
        "PROPOSAL",
        {"episode:EP-1": {"version": "1.0.0", "checksum": "a" * 64}, "episode:EP-2": {"version": "1.0.0", "checksum": "a" * 64}},
    )["status"] == "READY_FOR_FUNCTIONAL_REVIEW"
    assert validate_independent_research_audit(_audit()) == []


def test_case_b_limited_is_preserved_across_claims_multilingual_and_audit() -> None:
    pack = _integrated_research_pack()
    assert validate_research_pack(pack) == []
    decision = _material_claim_decision(
        claim_decision="CLAIM_LIMITED",
        sufficiency_status="LIMITED_BUT_USABLE",
        limitations=["Solo uso contextual; traduccion no verificada."],
        return_route="Restringir formulacion y divulgar limitacion.",
        return_route_code="RESTRICT_FORMULATION_AND_DISCLOSE",
    )
    assert validate_research_stop_decision(decision) == []
    audit = _audit(findings=[{"criterion": "SCRIPT_PRODUCT_DEFINED_CRITERION", "status": "LIMITED", "evidence_refs": ["WORK-DOSSIER-1"], "limitations": ["Uso limitado."]}])
    assert validate_independent_research_audit(audit) == []
    assert decision["sufficiency_status"] == "LIMITED_BUT_USABLE"
    assert decision["claim_decision"] == "CLAIM_LIMITED"


def test_case_c_blocked_material_claim_and_open_contradiction_fail_closed() -> None:
    decision = _material_claim_decision(
        claim_decision="CLAIM_BLOCKED",
        sufficiency_status="BLOCKED_BY_EVIDENCE",
        limitations=["La evidencia primaria no alcanza el uso previsto."],
        unresolved_material_contradiction_refs=["CONTRADICTION-1"],
        invalidator_codes=["MATERIAL_CONTRADICTION_FOUND"],
        return_route="Retirar o reformular el claim.",
        return_route_code="REMOVE_REPLACE_OR_REFORMULATE",
    )
    assert validate_research_stop_decision(decision) == []
    aggregate = _aggregate_decision(decision, sufficiency_status="BLOCKED_BY_EVIDENCE", required_component_decision_refs=[])
    violations = validate_research_stop_decision(aggregate, [decision])
    assert any("componente material bloqueado" in item for item in violations)


def test_case_d_provenance_and_critical_doubt_keep_original_derived_and_return_routes() -> None:
    pack = _integrated_research_pack()
    assert validate_research_pack(pack) == []
    no_language_need = deepcopy(pack)
    no_language_need["multilingual_research"] = {
        "activation_status": "NOT_ACTIVATED",
        "triggers": [],
        "non_trigger_examples": ["TECHNICAL_CAPABILITY_DEMO"],
        "affected_source_ids": [],
        "affected_claim_ids": [],
        "required_language": None,
        "material_risk": [],
        "consultation_result": "NOT_APPLICABLE",
        "limitations": [],
        "invalidators": [],
        "return_route": "NOT_APPLICABLE",
        "decision_basis": "La diferencia linguistica no aporta valor material al uso controlado.",
    }
    assert validate_research_pack(no_language_need) == []
    source_by_id = {item["source_id"]: item for item in pack["source_registry"]}
    assert source_by_id["S2"]["provenance"]["source_kind"] == "TRANSCRIPT"
    assert source_by_id["S2"]["provenance"]["derived_from_source_ref"] == "S1"
    assert source_by_id["S3"]["provenance"]["source_kind"] == "TRANSLATION"
    assert source_by_id["S3"]["provenance"]["primary_verification_performed"] is False

    for doubt in (
        _doubt(),
        _doubt("NOT_ACTIVATED"),
        _doubt("RESOLVED", activation_criteria=["SCREENING_DECISION_BLOCKED"], authorization_ref="authorization:doubt-1", authorized_actions=["CONTINUE_SCREENING"], evidence_refs=["evidence:doubt-resolved"], outcome="CONTINUE_SCREENING", return_route="RETURN_TO_SCREENING"),
        _doubt("INVALIDATED", invalidators=["IDENTITY_OR_SCOPE_REVIEW_REQUIRED"], return_trigger="MATERIAL_QUESTION_INTENT_TERRITORY_CHANGE", return_route="CHANNEL_INTELLIGENCE_REVIEW_REQUIRED"),
    ):
        lifecycle = _screened_pack()
        lifecycle["critical_doubts"] = [doubt]
        assert validate_work_lifecycle(lifecycle) == []


def test_case_e_reuse_specialist_audit_correction_and_invalidation_preserve_origin() -> None:
    pack = _integrated_research_pack()
    assert validate_research_pack(pack) == []
    memory = _memory()
    assert memory["comparison_decisions"][0]["decision"] == "RELATED_BUT_DISTINCT"
    assert memory["comparison_decisions"][0]["recommended_action"] == "NO_ACTION"
    specialist = pack["specialist_research"][0]
    assert specialist["authority_status"] == "SPECIALIST_CONTRIBUTION_ONLY"
    assert "RESEARCH_SUFFICIENCY" in specialist["does_not_establish"]

    audit = _audit(
        findings=[{"criterion": "SCRIPT_PRODUCT_DEFINED_CRITERION", "status": "NOT_SATISFIED", "evidence_refs": ["WORK-DOSSIER-1"], "limitations": ["Defecto de fixture."]}],
        defects=[{"defect_id": "DEF-1", "defect_type": "LOCATOR_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "description": "Locator defect."}],
        correction_routes=[{"defect_id": "DEF-1", "defect_type": "LOCATOR_DEFECT", "severity": "MAJOR", "origin_artifact": "WORK-DOSSIER-1", "invalidated_artifacts": ["RSD-C1"], "return_state": "RESEARCH_REVIEW_PENDING", "required_revalidation": "RESEARCH_PACKAGE", "suggested_role": "SCRIPT_PRODUCT"}],
        decision="REQUEST_CHANGES",
    )
    assert validate_independent_research_audit(audit) == []
    producer_output = {"artifact_id": "WORK-DOSSIER-1", "status": "ORIGINAL"}
    before = deepcopy(producer_output)
    routes = resolve_correction_routes(audit)
    assert routes[0]["origin_artifact"] == "WORK-DOSSIER-1"
    assert producer_output == before

    engine = InvalidationEngine()
    engine.resolve_correction_route(audit["correction_routes"][0])
    engine.invalidate_artifact("WORK-DOSSIER-1", "1.0.0", "New material evidence", "SCRIPT_PRODUCT")
    assert {record.target_artifact_id for record in engine.invalidation_log} == {"WORK-DOSSIER-1", "RSD-C1"}


def test_adapter_is_optional_neutral_and_cannot_become_authority_or_gate() -> None:
    assert validate_optional_research_adapter(None) == []
    assert validate_optional_research_adapter(_adapter()) == []
    assert validate_optional_research_adapter(_adapter(availability="UNAVAILABLE", source_refs=[], findings=[])) == []
    invalid_source = _adapter(source_refs=["UNKNOWN"])
    assert "ADAPTER_SOURCE_UNKNOWN:UNKNOWN" in validate_optional_research_adapter(invalid_source, {"S1"})
    assert any("ADAPTER_SOURCE_UNKNOWN:UNKNOWN" in item for item in validate_research_pack(_integrated_research_pack(), research_adapter=invalid_source))
    duplicate_finding = _adapter(findings=[_adapter()["findings"][0], _adapter()["findings"][0]])
    assert "ADAPTER_FINDING_ID_DUPLICATE" in validate_optional_research_adapter(duplicate_finding)
    for field, value in (("canonicality", "CANONICAL_MEMORY"), ("veracity_authority", "PRIMARY"), ("gate_behavior", "REQUIRED_GATE"), ("decision_authority", "ADAPTER")):
        invalid = _adapter(**{field: value})
        assert validate_optional_research_adapter(invalid)


def test_controlled_integration_cannot_promote_technical_result_to_higher_state() -> None:
    assert verify_invariants(["CONTROLLED_DEMO_NOT_PROMOTION"], {
        "demonstration_class": "CONTROLLED_TECHNICAL_HARNESS_E2E",
        "real_operational_subagents_promotion": False,
        "real_multiagent_runtime_promotion": False,
        "functional_readiness_claim": False,
        "real_product_operation": False,
    }) == []
    violations = verify_invariants(["CONTROLLED_DEMO_NOT_PROMOTION"], {
        "demonstration_class": "CONTROLLED_TECHNICAL_HARNESS_E2E",
        "functional_readiness_claim": True,
    })
    assert "PROMOTION_FLAG:functional_readiness_claim" in violations

    registry = json.loads(Path("config/capability_registry.json").read_text(encoding="utf-8"))
    auditor = next(item for item in registry["capabilities"] if item["capability_id"] == "B5_I2_SEMANTIC_AUDITOR")
    assert auditor["maturity_status"] == "IMPLEMENTED"
    assert auditor["availability_status"] == "NON_EXECUTABLE_CURRENT"
    assert auditor["assurance"]["functional_approval"] == "PENDING"
    control = Path("plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8")
    assert "R1_M11_STATUS: COMPLETED" in control
    assert "R1_M11_TECHNICAL_APPROVAL: APPROVED" in control
    assert [line for line in control.splitlines() if line.startswith("CURRENT_MISSION:")] == ["CURRENT_MISSION: NONE"]
    assert "R2_EXECUTION: NOT_AUTHORIZED" in control
    assert "REAL_RESEARCH_VERTICAL: NOT_DEMONSTRATED" in control
    assert 'AUTHORIZED_FOR_PRODUCT_USE: "NO"' in control
