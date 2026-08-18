"""Adversarial contract tests for R1-M6 claims and R1-M8 editorial memory."""

from copy import deepcopy
import hashlib
from pathlib import Path
import unittest

from src.core.contract_validation import (
    validate_claims_ledger,
    validate_editorial_semantic_memory,
    _source_dimension_universe,
    validate_against_schema,
    validate_research_stop_decision,
)
from src.core.editorial_semantic_memory import CHECKPOINT_INTEGRATION_STATUS, EditorialSemanticMemoryStore, current_artifacts_from_paths


def _decision(**overrides):
    value = {
        "decision_id": "RSD-1", "decision_version": "1.0.0", "subject_kind": "MATERIAL_CLAIM",
        "subject_ref": "C-1", "intended_use": "CENTRAL_CLAIM_SUPPORT", "evidence_refs": ["S-1"],
        "claim_decision": "CLAIM_ALLOWED", "sufficiency_status": "SUFFICIENT_FOR_INTENDED_USE",
        "limitations": [], "pending_matters": [], "unresolved_material_contradiction_refs": [], "invalidators": ["CLAIM_OR_USE_CHANGED"],
        "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"], "return_route": "Revalidar el claim.", "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_basis": "Cobertura y acceso primario suficientes.",
    }
    value.update(overrides)
    return value


def _memory(**overrides):
    ref = {"artifact_ref": "episode:EP-1", "version": "1.0.0", "checksum": "a" * 64}
    dimensions = {"topic": "tema", "central_question": "pregunta", "thesis": "tesis", "explanatory_mechanism": "mecanismo", "conclusion": "conclusion", "works": ["obra"], "scenes_or_passages": ["escena"], "work_functions": ["funcion"], "work_order": ["1"], "work_combination": "combinacion", "claims": ["claim"], "interpretations": ["interpretacion"], "specialists": ["especialista"], "sources": ["fuente"], "narrative_architecture": "arquitectura", "analogies": ["analogia"], "opening_unit": None, "editorial_promise": None}
    value = {
        "memory_id": "MEM-1", "memory_version": "1.0.0", "history_source": "REPOSITORY_GOVERNED_ARTIFACTS",
        "consultation_points": ["PROPOSAL", "PRE_FINAL_CURATION", "PRE_THESIS_OR_ARCHITECTURE", "OPENING_UNIT_REVIEW", "PRE_FINAL_SCRIPT"],
        "checkpoint_integration": {"PROPOSAL": "CONNECTED", "PRE_FINAL_CURATION": "CONNECTED", "PRE_THESIS_OR_ARCHITECTURE": "CONNECTED", "OPENING_UNIT_REVIEW": "PREPARED_DEFERRED_UNTIL_CANONICAL_OPENING_UNIT_REVIEW", "PRE_FINAL_SCRIPT": "PREPARED_DEFERRED_UNTIL_CANONICAL_FINAL_SCRIPT_APPROVAL"},
        "episode_entries": [{"episode_id": "EP-1", "artifact_refs": [ref], "dimensions": dimensions}, {"episode_id": "EP-2", "artifact_refs": [{**ref, "artifact_ref": "episode:EP-2"}], "dimensions": dimensions}],
        "comparison_decisions": [{"decision_id": "CMP-1", "candidate_episode_ref": {**ref, "artifact_ref": "episode:EP-2"}, "compared_episode_refs": [ref], "evidence_refs": ["thesis:T-1"], "comparison_dimensions": ["thesis", "works"], "decision": "RELATED_BUT_DISTINCT", "recommended_action": "NO_ACTION", "justification": "La tesis difiere aunque comparte tema.", "invalidators": ["THESIS_CHANGED"]}],
        "functional_dimension_sources": {"CHANNEL_INTELLIGENCE": {"sources": [{"artifact_ref": "policies/channel_intelligence/topic_belonging_policy.md", "version": "1.0.0", "checksum": "a" * 64}], "dimensions": ["identity_alignment"]}, "SCRIPT_PRODUCT": {"sources": [{"artifact_ref": "policies/script_product/main_episode_format_policy.md", "version": "1.0.0", "checksum": "b" * 64}], "dimensions": ["CANDIDATE_WORKS"]}, "YOUTUBE_ADAPTATION": {"sources": [{"artifact_ref": "config/youtube_adaptation_r3_traceability.json", "version": "1.0.0", "checksum": "c" * 64}], "dimensions": ["YT_VISIBLE_PROMISE"]}}, "semantic_assurance": {"status": "PASS", "evaluated_dimensions": {"CHANNEL_INTELLIGENCE": [{"dimension": "identity_alignment", "status": "EVALUATED", "evidence_refs": ["ci:1"]}], "SCRIPT_PRODUCT": [{"dimension": "CANDIDATE_WORKS", "status": "EVALUATED", "evidence_refs": ["sp:1"]}], "YOUTUBE_ADAPTATION": [{"dimension": "YT_VISIBLE_PROMISE", "status": "EVALUATED", "evidence_refs": ["ya:1"]}]}},
        "created_at": "2026-08-13T10:00:00Z",
    }
    for owner, source in (("CHANNEL_INTELLIGENCE", "policies/channel_intelligence/topic_belonging_policy.md"), ("SCRIPT_PRODUCT", "policies/script_product/main_episode_format_policy.md"), ("YOUTUBE_ADAPTATION", "config/youtube_adaptation_r3_traceability.json")):
        value["functional_dimension_sources"][owner]["sources"][0]["checksum"] = hashlib.sha256((Path(__file__).resolve().parents[2] / source).read_bytes()).hexdigest()
    value["functional_dimension_sources"]["SCRIPT_PRODUCT"]["sources"].append({"artifact_ref": "policies/script_product/episode_discovery_and_material_curation_policy.md", "version": "1.0.0", "checksum": hashlib.sha256((Path(__file__).resolve().parents[2] / "policies/script_product/episode_discovery_and_material_curation_policy.md").read_bytes()).hexdigest()})
    for owner, binding in value["functional_dimension_sources"].items():
        paths = [Path(__file__).resolve().parents[2] / source["artifact_ref"] for source in binding["sources"]]
        dimensions = sorted(_source_dimension_universe(owner, paths))
        binding["dimensions"] = ["producer-declared-value-is-ignored"]
        value["semantic_assurance"]["evaluated_dimensions"][owner] = [{"dimension": dimension, "status": "EVALUATED", "evidence_refs": [f"{owner}:evidence"]} for dimension in dimensions]
    value.update(overrides)
    return value


class TestR1M6ClaimsAndSufficiency(unittest.TestCase):
    def test_material_claim_requires_explicit_decision(self):
        ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "opening", "claim_text": "Claim material", "claim_type": "FACT", "source_refs": ["S-1"], "verification_status": "VERIFIED", "materiality": {"is_material": True, "activation_criteria": ["THESIS_DEPENDENCY"], "non_trigger_examples": [], "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"], "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_ref": None}}]}
        self.assertTrue(any("ResearchStopDecision" in item for item in validate_claims_ledger(ledger)))

    def test_limited_claim_requires_explicit_limitation(self):
        ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "body", "claim_text": "Claim", "claim_type": "FACT", "source_refs": ["S-1"], "verification_status": "VERIFIED", "claim_decision": "CLAIM_LIMITED", "research_sufficiency": "LIMITED_BUT_USABLE"}]}
        self.assertTrue(any("LIMITED_BUT_USABLE" in item for item in validate_claims_ledger(ledger)))

    def test_false_materiality_cannot_carry_activation_criteria(self):
        ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "body", "claim_text": "Claim", "claim_type": "FACT", "source_refs": ["S-1"], "verification_status": "VERIFIED", "materiality": {"is_material": False, "activation_criteria": ["THESIS_DEPENDENCY"], "non_trigger_examples": [], "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"], "return_route_code": "NOT_APPLICABLE", "decision_ref": None}}]}
        self.assertTrue(any("is_material=false" in item for item in validate_claims_ledger(ledger)))

    def test_central_claim_cannot_omit_materiality_assessment(self):
        ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "body", "claim_text": "Claim central", "claim_type": "FACT", "source_refs": ["S-1"], "verification_status": "VERIFIED", "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT"}]}
        self.assertTrue(any("assessment de materialidad" in item or "materiality" in item for item in validate_claims_ledger(ledger)))

    def test_materiality_accepts_the_canonical_fifteen_criteria(self):
        criteria = ["THESIS_DEPENDENCY", "CENTRAL_ARGUMENT_DEPENDENCY", "WORK_SELECTION_DEPENDENCY", "WORK_FIDELITY", "CAUSAL_OR_PSYCHOLOGICAL_EXPLANATION", "AUTHORIAL_INTENT", "SENSITIVE_OR_HARMFUL_ASSERTION", "NUMERICAL_OR_HISTORICAL_ASSERTION", "CONTROVERSIAL_OR_DISPUTED_ASSERTION", "VISIBLE_PROMISE_DEPENDENCY", "OPENING_OR_CONCLUSION_DEPENDENCY", "REPUTATIONAL_OR_ETHICAL_RISK", "TRANSLATION_OR_TRANSCRIPTION_DEPENDENCY", "RIVAL_READING_IMPACT", "REUSE_ORIGINALITY_DEPENDENCY"]
        ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "body", "claim_text": "Claim", "claim_type": "FACT", "source_refs": ["S-1"], "verification_status": "VERIFIED", "criticality": "CENTRAL", "intended_use": "CENTRAL_CLAIM_SUPPORT", "materiality": {"is_material": True, "activation_criteria": criteria, "non_trigger_examples": ["transición retórica"], "invalidator_codes": ["CLAIM_OR_SCOPE_CHANGED"], "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY", "decision_ref": "RSD-1"}}]}
        self.assertEqual(validate_claims_ledger(ledger), [])

    def test_non_material_assessment_is_representable(self):
        ledger = {"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "body", "claim_text": "Detalle", "claim_type": "STYLE", "source_refs": ["S-1"], "verification_status": "VERIFIED", "materiality": {"is_material": False, "activation_criteria": [], "non_trigger_examples": ["detalle ambiental sin función"], "invalidator_codes": ["EDITORIAL_CONTEXT_CHANGED"], "return_route_code": "NOT_APPLICABLE", "decision_ref": None}}]}
        self.assertEqual(validate_claims_ledger(ledger), [])

    def test_blocked_claim_cannot_be_presented_as_sufficient(self):
        violations = validate_claims_ledger({"ledger_id": "CL-1", "script_version": "1.0.0", "claims": [{"claim_id": "C-1", "script_location": "body", "claim_text": "Claim", "claim_type": "FACT", "source_refs": ["S-1"], "verification_status": "REJECTED", "claim_decision": "CLAIM_BLOCKED", "research_sufficiency": "SUFFICIENT_FOR_INTENDED_USE"}]})
        self.assertTrue(any("CLAIM_BLOCKED" in item for item in violations))

    def test_more_research_requires_pending_route(self):
        self.assertTrue(any("pendientes" in item for item in validate_research_stop_decision(_decision(sufficiency_status="MORE_RESEARCH_REQUIRED", claim_decision="CLAIM_LIMITED", pending_matters=[]))))

    def test_return_route_must_match_sufficiency(self):
        decision = _decision(return_route_code="REMOVE_REPLACE_OR_REFORMULATE")
        self.assertTrue(any("return_route_code" in item for item in validate_research_stop_decision(decision)))

    def test_aggregate_cannot_ignore_blocked_material_claim(self):
        aggregate = _decision(subject_kind="AGGREGATE_RESEARCH_PACK", subject_ref="RP-1", claim_decision=None, component_decision_refs=["RSD-1"], required_component_decision_refs=["RSD-1"])
        blocked = _decision(decision_id="RSD-1", claim_decision="CLAIM_BLOCKED", sufficiency_status="BLOCKED_BY_EVIDENCE")
        self.assertTrue(any("componente material bloqueado" in item for item in validate_research_stop_decision(aggregate, [blocked])))

    def test_aggregate_without_component_decisions_fails_closed(self):
        aggregate = _decision(subject_kind="AGGREGATE_RESEARCH_PACK", subject_ref="RP-1", claim_decision=None, component_decision_refs=["RSD-1"], required_component_decision_refs=["RSD-1"])
        aggregate["sufficiency_status"] = "SUFFICIENT_FOR_INTENDED_USE"
        self.assertTrue(any("fail-open" in item for item in validate_research_stop_decision(aggregate)))

    def test_aggregate_positive_rejects_pending_component(self):
        aggregate = _decision(subject_kind="AGGREGATE_RESEARCH_PACK", subject_ref="RP-1", claim_decision=None, component_decision_refs=["RSD-1"], required_component_decision_refs=["RSD-1"])
        pending = _decision(decision_id="RSD-1", claim_decision="CLAIM_LIMITED", sufficiency_status="MORE_RESEARCH_REQUIRED", pending_matters=["verificar primaria"], return_route_code="RETURN_TO_RESEARCH")
        self.assertTrue(any("MORE_RESEARCH_REQUIRED" in item for item in validate_research_stop_decision(aggregate, [pending])))

    def test_aggregate_sufficient_rejects_limited_component(self):
        aggregate = _decision(subject_kind="AGGREGATE_RESEARCH_PACK", subject_ref="RP-1", claim_decision=None, component_decision_refs=["RSD-1"], required_component_decision_refs=["RSD-1"])
        limited = _decision(decision_id="RSD-1", claim_decision="CLAIM_LIMITED", sufficiency_status="LIMITED_BUT_USABLE", limitations=["Falta una verificación primaria."])
        violations = validate_research_stop_decision(aggregate, [limited])
        self.assertTrue(any("no puede ocultar" in item for item in violations))

    def test_aggregate_rejects_incomplete_component(self):
        aggregate = _decision(subject_kind="AGGREGATE_RESEARCH_PACK", subject_ref="RP-1", claim_decision=None, component_decision_refs=["RSD-1"], required_component_decision_refs=["RSD-1"])
        self.assertTrue(any("Componente" in item for item in validate_research_stop_decision(aggregate, [{"decision_id": "RSD-1", "sufficiency_status": "SUFFICIENT_FOR_INTENDED_USE"}])))

    def test_research_complete_stage_requires_aggregate_inventory(self):
        violations = validate_against_schema({"research_pack_stage": "RESEARCH_COMPLETE"}, "research_pack")
        self.assertTrue(any("aggregate_research_stop_decision_ref" in item for item in violations))
        self.assertTrue(any("required_component_decision_refs" in item for item in violations))

    def test_open_material_contradiction_blocks_positive_sufficiency(self):
        decision = _decision(unresolved_material_contradiction_refs=["CONTRADICTION-1"])
        self.assertTrue(any("contradicción material abierta" in item for item in validate_research_stop_decision(decision)))


class TestPlan007FamilyCSemanticAssurance(unittest.TestCase):
    def test_invented_dimension_is_rejected(self):
        memory = _memory()
        memory["semantic_assurance"]["evaluated_dimensions"]["YOUTUBE_ADAPTATION"].append({"dimension": "INVENTED", "status": "EVALUATED", "evidence_refs": ["x"]})
        self.assertIn("SEMANTIC_DIMENSION_NOT_CANONICAL:YOUTUBE_ADAPTATION:INVENTED", validate_editorial_semantic_memory(memory))

    def test_canonical_dimension_omission_is_rejected(self):
        memory = _memory()
        memory["semantic_assurance"]["evaluated_dimensions"]["YOUTUBE_ADAPTATION"].pop()
        self.assertTrue(any("SEMANTIC_DIMENSION_NOT_EVALUATED:YOUTUBE_ADAPTATION" in item for item in validate_editorial_semantic_memory(memory)))

    def test_canonical_evaluated_dimension_is_accepted(self):
        self.assertEqual(validate_editorial_semantic_memory(_memory()), [])

    def test_noncanonical_source_is_rejected(self):
        memory = _memory()
        memory["functional_dimension_sources"]["YOUTUBE_ADAPTATION"]["sources"][0]["artifact_ref"] = "policies/script_product/main_episode_format_policy.md"
        violations = validate_editorial_semantic_memory(memory)
        self.assertTrue(any("SEMANTIC_SOURCE_NON_CANONICAL:YOUTUBE_ADAPTATION" in item for item in violations))

    def test_inconsistent_published_source_version_is_rejected(self):
        memory = _memory()
        memory["functional_dimension_sources"]["YOUTUBE_ADAPTATION"]["sources"][0]["version"] = "9.9.9"
        violations = validate_editorial_semantic_memory(memory)
        self.assertTrue(any("SEMANTIC_SOURCE_VERSION_MISMATCH:YOUTUBE_ADAPTATION" in item for item in violations))
    def test_inconsistent_source_checksum_is_rejected(self):
        memory = _memory()
        memory["functional_dimension_sources"]["YOUTUBE_ADAPTATION"]["sources"][0]["checksum"] = "0" * 64
        violations = validate_editorial_semantic_memory(memory)
        self.assertTrue(any("SEMANTIC_SOURCE_CHECKSUM_MISMATCH:YOUTUBE_ADAPTATION" in item for item in violations))

class TestR1M8EditorialSemanticMemory(unittest.TestCase):
    def test_similarity_requires_multiple_editorial_dimensions(self):
        memory = _memory()
        memory["comparison_decisions"][0]["comparison_dimensions"] = ["topic"]
        self.assertTrue(validate_editorial_semantic_memory(memory))

    def test_keyword_or_score_only_evidence_is_not_editorial_evidence(self):
        memory = _memory()
        memory["comparison_decisions"][0]["evidence_refs"] = ["keyword:tema", "score:0.98"]
        self.assertTrue(any("keywords" in item for item in validate_editorial_semantic_memory(memory)))

    def test_too_similar_requires_review_not_autonomous_block(self):
        memory = _memory()
        memory["comparison_decisions"][0].update({"decision": "TOO_SIMILAR", "recommended_action": "NO_ACTION"})
        self.assertTrue(any("TOO_SIMILAR" in item for item in validate_editorial_semantic_memory(memory)))

    def test_continuation_requires_explicit_prior_reference(self):
        memory = _memory()
        memory["comparison_decisions"][0].update({"decision": "INTENTIONAL_CONTINUATION", "recommended_action": "CONTINUATION_REFERENCE_REQUIRED"})
        self.assertTrue(any("INTENTIONAL_CONTINUATION" in item for item in validate_editorial_semantic_memory(memory)))

    def test_reuse_requires_justification(self):
        memory = _memory()
        memory["comparison_decisions"][0].update({"decision": "REUSE_REQUIRES_JUSTIFICATION", "recommended_action": "NO_ACTION"})
        self.assertTrue(any("REUSE_REQUIRES_JUSTIFICATION" in item for item in validate_editorial_semantic_memory(memory)))

    def test_insufficient_history_is_not_pass(self):
        memory = _memory()
        memory["comparison_decisions"][0].update({"decision": "INSUFFICIENT_HISTORY", "compared_episode_refs": [], "recommended_action": "NO_ACTION"})
        self.assertTrue(any("INSUFFICIENT_HISTORY" in item for item in validate_editorial_semantic_memory(memory)))

    def test_external_or_synthetic_history_is_rejected_by_schema(self):
        memory = _memory(history_source="EXTERNAL_EMBEDDINGS")
        self.assertTrue(validate_editorial_semantic_memory(memory))

    def test_memory_store_consults_at_required_moment_with_fresh_artifacts(self):
        memory = _memory()
        store = EditorialSemanticMemoryStore(memory)
        current = {
            "episode:EP-1": {"version": "1.0.0", "checksum": "a" * 64},
            "episode:EP-2": {"version": "1.0.0", "checksum": "a" * 64},
        }
        result = store.consult(memory["comparison_decisions"][0]["candidate_episode_ref"], "PROPOSAL", current)
        self.assertEqual(result["status"], "READY_FOR_FUNCTIONAL_REVIEW")

    def test_memory_store_fails_closed_on_checksum_change(self):
        store = EditorialSemanticMemoryStore(_memory())
        current = {
            "episode:EP-1": {"version": "1.0.0", "checksum": "b" * 64},
            "episode:EP-2": {"version": "1.0.0", "checksum": "a" * 64},
        }
        result = store.consult(_memory()["comparison_decisions"][0]["candidate_episode_ref"], "PRE_FINAL_SCRIPT", current)
        self.assertEqual(result["status"], "INVALIDATED")

    def test_memory_checkpoint_status_distinguishes_real_hooks_from_deferred_surfaces(self):
        self.assertEqual(CHECKPOINT_INTEGRATION_STATUS["PROPOSAL"], "CONNECTED")
        self.assertTrue(CHECKPOINT_INTEGRATION_STATUS["OPENING_UNIT_REVIEW"].startswith("PREPARED_DEFERRED"))
        self.assertTrue(CHECKPOINT_INTEGRATION_STATUS["PRE_FINAL_SCRIPT"].startswith("PREPARED_DEFERRED"))

    def test_memory_current_artifacts_are_resolved_from_gate_inputs(self):
        path = Path(__file__)
        resolved = current_artifacts_from_paths({"episode:EP-1": path}, {"episode:EP-1": "1.0.0"})
        self.assertEqual(resolved["episode:EP-1"]["version"], "1.0.0")
        self.assertEqual(len(resolved["episode:EP-1"]["checksum"]), 64)


if __name__ == "__main__":
    unittest.main()
