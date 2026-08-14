"""T2-C — adversarial assurance + selective must-kill mutation tests (PLAN 006 §10C)."""
import copy
import json
from pathlib import Path

import pytest

from src.core.adversarial_assurance import (
    ADVERSARIAL_CHECKS,
    MUST_KILL_MUTATIONS,
    REQUIRED_TRANSITIONS,
    evaluate_must_kill_mutation,
    verify_adversarial,
    verify_all_adversarial,
)
from src.core.contract_validation import validate_contradiction_disposition

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"
WORK_LIFECYCLE_SCHEMA = SCHEMAS / "work_lifecycle.json"


def _lifecycle(**overrides):
    lifecycle = {
        "lifecycle_id": "LC-001",
        "lifecycle_version": "1.0.0",
        "episode_id": "EP-001",
        "research_id": "RP-001",
        "entry_mode": "TOPIC_FIRST",
        "anchor_work_id": "W-ANCHOR",
        "works": [
            {
                "work_id": "W-001",
                "state": "SCREENED_WORK",
                "state_version": "1.0.0",
                "identity_ref": "research/work_identity/W-001.json",
                "version_ref": "research/work_identity/W-001.json",
                "is_anchor": False,
                "lineage_refs": ["LC-001/T-000"],
                "stage_evidence_refs": ["research/screening/W-001.json"],
                "screening_ref": "research/screening/W-001.json",
            }
        ],
        "transitions": [
            {
                "transition_id": "LC-001/T-000",
                "transition_version": "1.0.0",
                "work_id": "W-001",
                "previous_state": "DISCOVERED_WORK",
                "target_state": "SCREENED_WORK",
                "transition_type": "SCREENING_DECISION",
                "transition_reason": "candidate fits episode format",
                "evidence_refs": ["research/screening/W-001.json"],
                "input_version_refs": ["research/work_identity/W-001.json"],
                "transition_authority_ref": "config/responsibility_registry.json#responsibilities/SCRIPT_PRODUCT",
                "authority_role": "SCRIPT_PRODUCT",
                "decision": {"decision_id": "DEC-001", "decision_version": "1.0.0", "status": "EXPLICIT"},
                "occurred_at": "2026-01-01T00:00:00Z",
                "lineage_ref": None,
            }
        ],
        "screening": {
            "candidate_work_ids": ["W-001"],
            "format_policy_ref": "policies/script_product/main_episode_format_policy.md",
            "range_status": "NORMAL",
            "exception": None,
        },
        "final_selection": {
            "selected_work_ids": [],
            "format_policy_ref": "policies/script_product/main_episode_format_policy.md",
            "range_status": "NOT_APPLICABLE",
            "curation_ref": None,
            "exception": None,
        },
        "critical_doubts": [],
        "responsibility_registry": {
            "responsibilities": [{"role_id": "SCRIPT_PRODUCT"}],
        },
        "created_at": "2026-01-01T00:00:00Z",
    }
    lifecycle.update(overrides)
    return lifecycle


def _doubt(**overrides):
    doubt = {
        "doubt_id": "CD-001",
        "decision_id": "SP-IR0-CRITICAL_WORK_DOUBT",
        "decision_version": "1.0.0",
        "work_id": "W-001",
        "authorization_status": "ACTIVE",
        "activation_criteria": ["VERSION_OR_ADAPTATION_UNCERTAINTY"],
        "non_trigger_examples": ["GENERAL_CURIOSITY"],
        "invalidators": ["QUESTION_RESOLVED"],
        "evidence_refs": ["research/dossier/W-001.json"],
        "scope": "version uncertainty for W-001",
        "authorized_actions": ["REQUIRE_MORE_TARGETED_RESEARCH"],
        "authorization_ref": "approvals/script_product/critical_doubt.json",
        "outcome": "NOT_APPLICABLE",
        "return_route": "CHANNEL_INTELLIGENCE_REVIEW_REQUIRED",
        "return_trigger": None,
    }
    doubt.update(overrides)
    return doubt


def _contradiction(subject_kind="MATERIAL_CLAIM", subject_ref="C1", affected_claim_ids=None):
    """A structurally valid contradiction that only fails on subject resolution,
    so the differential probe isolates the local-resolution surface."""
    return {
        "item_id": "X1",
        "statement": "Las fuentes discrepan sobre la causa del hecho.",
        "source_refs": ["S1", "S2"],
        "locator": "p. 10 / p. 22",
        "confidence": "HIGH",
        "subject_kind": subject_kind,
        "subject_ref": subject_ref,
        "subject_state": "PROVISIONAL",
        "subject_version": "1.0.0",
        "subject_formulation": "La formulación afectada.",
        "affected_use": "CENTRAL_CLAIM_SUPPORT",
        "affected_claim_ids": ["C1"] if affected_claim_ids is None else affected_claim_ids,
        "conflicting_source_refs": ["S1", "S2"],
        "discrepancy_kind": "CAUSAL",
        "materiality": "MATERIAL",
        "disposition": "RESOLVED",
        "compared_positions": [
            {"position_id": "P1", "statement": "La causa es A.", "source_refs": ["S1"], "treatment": "RETAINED"},
            {"position_id": "P2", "statement": "La causa es B.", "source_refs": ["S2"], "treatment": "REJECTED"},
        ],
        "decision_evidence_refs": ["S1", "S2"],
        "contrary_evidence_refs": ["S2"],
        "disposition_justification": "Se comparan ambas posiciones y se explicita el impacto sobre el claim.",
        "remaining_limitations": [],
        "pending_matters": [],
        "return_route": "Revisar la formulación según la disposición de la contradicción.",
        "return_route_code": "AUTHORIZE_INTENDED_USE_ONLY",
        "invalidator_codes": ["MATERIAL_CONTRADICTION_FOUND"],
        "dependent_artifact_refs": ["claim:C1"],
        "revalidation_requirements": [],
    }


_PHENOMENON_REF = "EXT-PHENOMENON"


def _phenomenon_observation(known_subject_ids, *, declared=()):
    """Derive the local-resolution observation for PHENOMENON by running the real
    contradiction validator. An external phenomenon ref is only rejected once the
    kind is added to the locally-resolved surface (the R1-M7 escape)."""
    case = _contradiction(subject_kind="PHENOMENON", subject_ref=_PHENOMENON_REF, affected_claim_ids=[])
    violations = validate_contradiction_disposition(
        case, {"S1", "S2"}, {"S1", "S2", "X1"}, {"C1"}, known_subject_ids
    )
    rejected = any("subject_ref inexistente" in item for item in violations)
    return {
        "subject_resolution_rejected": ["PHENOMENON"] if rejected else [],
        "subject_resolution_accepted": [] if rejected else ["PHENOMENON"],
        "authorized_subject_resolution": sorted(declared),
    }


class TestStateHistoryFamily:
    def test_valid_screened_work_passes(self):
        assert verify_all_adversarial(_lifecycle()) == []

    def test_screened_work_without_prior_transition_fails(self):
        lifecycle = _lifecycle()
        lifecycle["transitions"] = []
        violations = verify_all_adversarial(lifecycle)
        assert any("MISSING_REQUIRED_TRANSITION:W-001:SCREENED_WORK" in v for v in violations)

    def test_excluded_work_requires_transition(self):
        lifecycle = _lifecycle()
        lifecycle["works"][0]["state"] = "EXCLUDED_WORK"
        lifecycle["transitions"] = []
        violations = verify_all_adversarial(lifecycle)
        assert any(v.startswith("MISSING_REQUIRED_TRANSITION:W-001:EXCLUDED_WORK") for v in violations)

    def test_invalidated_work_requires_transition(self):
        lifecycle = _lifecycle()
        lifecycle["works"][0]["state"] = "INVALIDATED_WORK"
        lifecycle["transitions"] = []
        violations = verify_all_adversarial(lifecycle)
        assert any(v.startswith("MISSING_REQUIRED_TRANSITION:W-001:INVALIDATED_WORK") for v in violations)

    def test_invalid_state_fails(self):
        lifecycle = _lifecycle()
        lifecycle["works"][0]["state"] = "FANTASY_STATE"
        violations = verify_all_adversarial(lifecycle)
        assert any("INVALID_WORK_STATE:W-001:FANTASY_STATE" in v for v in violations)


class TestLineageFamily:
    def test_previous_ref_nonexistent_fails(self):
        lifecycle = _lifecycle()
        lifecycle["transitions"][0]["lineage_ref"] = "LC-001/T-GHOST"
        violations = verify_all_adversarial(lifecycle)
        assert any("PREVIOUS_REF_NONEXISTENT" in v for v in violations)

    def test_duplicate_transition_id_fails(self):
        lifecycle = _lifecycle()
        duplicate = copy.deepcopy(lifecycle["transitions"][0])
        duplicate["transition_id"] = "LC-001/T-000"
        lifecycle["transitions"].append(duplicate)
        violations = verify_all_adversarial(lifecycle)
        assert any("DUPLICATE_TRANSITION_ID:LC-001/T-000" in v for v in violations)

    def test_lineage_state_mismatch_fails(self):
        lifecycle = _lifecycle()
        parent = {
            "transition_id": "LC-001/T-PARENT",
            "transition_version": "1.0.0",
            "work_id": "W-001",
            "previous_state": "DISCOVERED_WORK",
            "target_state": "FINALIST_WORK",
            "transition_type": "SCREENING_DECISION",
            "transition_reason": "parent",
            "evidence_refs": ["research/screening/W-001.json"],
            "input_version_refs": ["research/work_identity/W-001.json"],
            "transition_authority_ref": "config/responsibility_registry.json#responsibilities/SCRIPT_PRODUCT",
            "authority_role": "SCRIPT_PRODUCT",
            "decision": {"decision_id": "DEC-000", "decision_version": "1.0.0", "status": "EXPLICIT"},
            "occurred_at": "2026-01-01T00:00:00Z",
            "lineage_ref": None,
        }
        lifecycle["transitions"][0]["previous_state"] = "SCREENED_WORK"
        lifecycle["transitions"][0]["lineage_ref"] = "LC-001/T-PARENT"
        lifecycle["transitions"].insert(0, parent)
        violations = verify_all_adversarial(lifecycle)
        assert any("LINEAGE_STATE_MISMATCH" in v for v in violations)

    def test_invalid_previous_state_fails(self):
        lifecycle = _lifecycle()
        lifecycle["transitions"][0]["previous_state"] = "SOMETHING_ELSE"
        violations = verify_all_adversarial(lifecycle)
        assert any("PREVIOUS_STATE_INVALID" in v for v in violations)

    def test_lineage_from_another_work_fails(self):
        lifecycle = _lifecycle()
        parent = copy.deepcopy(lifecycle["transitions"][0])
        parent.update({"transition_id": "LC-001/T-OTHER", "work_id": "W-002"})
        lifecycle["transitions"][0]["lineage_ref"] = "LC-001/T-OTHER"
        lifecycle["transitions"].insert(0, parent)
        violations = verify_all_adversarial(lifecycle)
        assert any("LINEAGE_WORK_MISMATCH:LC-001/T-000:LC-001/T-OTHER" in v for v in violations)

    def test_lineage_to_future_transition_fails(self):
        lifecycle = _lifecycle()
        parent = copy.deepcopy(lifecycle["transitions"][0])
        parent.update({
            "transition_id": "LC-001/T-FUTURE",
            "occurred_at": "2026-01-02T00:00:00Z",
        })
        lifecycle["transitions"][0]["lineage_ref"] = "LC-001/T-FUTURE"
        lifecycle["transitions"].insert(0, parent)
        violations = verify_all_adversarial(lifecycle)
        assert any("LINEAGE_NOT_STRICTLY_PRIOR:LC-001/T-000:LC-001/T-FUTURE" in v for v in violations)


class TestAuthorityFamily:
    def test_invented_authority_fails(self):
        lifecycle = _lifecycle()
        lifecycle["transitions"][0]["transition_authority_ref"] = "approvals/definitely_fake.json"
        violations = verify_all_adversarial(lifecycle)
        assert any("AUTHORITY_REF_UNRESOLVABLE" in v for v in violations)

    def test_missing_registry_fails_closed(self):
        lifecycle = _lifecycle()
        lifecycle.pop("responsibility_registry")
        violations = verify_all_adversarial(lifecycle)
        assert "RESPONSIBILITY_REGISTRY_MISSING" in violations

    def test_authority_role_unresolvable_fails(self):
        lifecycle = _lifecycle()
        lifecycle["responsibility_registry"] = {
            "responsibilities": [{"role_id": "SCRIPT_PRODUCT"}, {"role_id": "EDITORIAL"}]
        }
        lifecycle["transitions"][0]["authority_role"] = "SELF_APPOINTED"
        violations = verify_all_adversarial(lifecycle)
        assert any("AUTHORITY_ROLE_UNRESOLVABLE" in v for v in violations)

    def test_resolvable_authority_role_passes(self):
        lifecycle = _lifecycle()
        lifecycle["responsibility_registry"] = {
            "responsibilities": [{"role_id": "SCRIPT_PRODUCT"}, {"role_id": "EDITORIAL"}]
        }
        assert verify_all_adversarial(lifecycle) == []


class TestCriticalDoubtFamily:
    def test_resolved_without_activation_fails(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(authorization_status="RESOLVED", activation_criteria=[])])
        violations = verify_all_adversarial(lifecycle)
        assert any("RESOLVED_WITHOUT_ACTIVATION:CD-001" in v for v in violations)

    def test_resolved_without_authorization_fails(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(authorization_status="RESOLVED", authorization_ref=None)])
        violations = verify_all_adversarial(lifecycle)
        assert any("RESOLVED_WITHOUT_AUTHORIZATION:CD-001" in v for v in violations)

    def test_resolved_without_evidence_fails(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(authorization_status="RESOLVED", evidence_refs=[])])
        violations = verify_all_adversarial(lifecycle)
        assert any("RESOLVED_WITHOUT_EVIDENCE:CD-001" in v for v in violations)

    def test_return_route_without_trigger_fails(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(return_route="RETURN_TO_SCREENING", return_trigger=None)])
        violations = verify_all_adversarial(lifecycle)
        assert any("RETURN_ROUTE_WITHOUT_TRIGGER:CD-001" in v for v in violations)

    def test_return_route_with_approved_trigger_passes(self):
        lifecycle = _lifecycle(
            critical_doubts=[
                _doubt(
                    authorization_status="RESOLVED",
                    return_route="RETURN_TO_SCREENING",
                    return_trigger="MATERIAL_QUESTION_INTENT_TERRITORY_CHANGE",
                )
            ]
        )
        violations = verify_all_adversarial(lifecycle)
        assert not any("RETURN_ROUTE" in v or "RESOLVED" in v for v in violations)

    def test_outcome_not_approved_fails(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(outcome="PROMOTE_ANYWAY")])
        violations = verify_all_adversarial(lifecycle)
        assert any("OUTCOME_NOT_APPROVED:CD-001:PROMOTE_ANYWAY" in v for v in violations)

    def test_invalid_doubt_status_fails(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(authorization_status="MAYBE")])
        violations = verify_all_adversarial(lifecycle)
        assert any("DOUBT_STATUS_INVALID:CD-001:MAYBE" in v for v in violations)


class TestCheckRegistry:
    def test_known_checks_resolve(self):
        assert len(ADVERSARIAL_CHECKS) == 5
        ids = {check.check_id for check in ADVERSARIAL_CHECKS}
        assert ids == {
            "STATE_HISTORY_REQUIRED_TRANSITION",
            "LINEAGE_INTEGRITY",
            "AUTHORITY_RESOLVABLE",
            "CRITICAL_DOUBT_VALID_CLOSURE",
            "SUBJECT_LOCAL_RESOLUTION_STABLE",
        }

    def test_unknown_check_fails_closed(self):
        violations = verify_adversarial(["NOT_A_REAL_CHECK"], _lifecycle())
        assert any("UNKNOWN_ADVERSARIAL_CHECK:NOT_A_REAL_CHECK" in v for v in violations)


class TestSelectiveMustKillMutations:
    def test_mutations_target_real_checks(self):
        ids = {check.check_id for check in ADVERSARIAL_CHECKS}
        for mutant in MUST_KILL_MUTATIONS:
            assert mutant.target_check_id in ids

    def test_state_required_transition_mutant_killed(self):
        lifecycle = _lifecycle()
        lifecycle["transitions"] = []
        result = evaluate_must_kill_mutation(mutant=MUST_KILL_MUTATIONS[0], observation=lifecycle)
        assert result["classification"] == "KILLED"

    def test_duplicate_guard_mutant_killed(self):
        lifecycle = _lifecycle()
        duplicate = copy.deepcopy(lifecycle["transitions"][0])
        duplicate["transition_id"] = "LC-001/T-000"
        lifecycle["transitions"].append(duplicate)
        result = evaluate_must_kill_mutation(mutant=MUST_KILL_MUTATIONS[1], observation=lifecycle)
        assert result["classification"] == "KILLED"

    def test_invented_authority_mutant_killed(self):
        lifecycle = _lifecycle()
        lifecycle["transitions"][0]["transition_authority_ref"] = "approvals/definitely_fake.json"
        result = evaluate_must_kill_mutation(mutant=MUST_KILL_MUTATIONS[2], observation=lifecycle)
        assert result["classification"] == "KILLED"

    def test_resolved_without_evidence_mutant_killed(self):
        lifecycle = _lifecycle(critical_doubts=[_doubt(authorization_status="RESOLVED", evidence_refs=[])])
        result = evaluate_must_kill_mutation(mutant=MUST_KILL_MUTATIONS[3], observation=lifecycle)
        assert result["classification"] == "KILLED"

    def test_clean_observation_exposes_no_fault(self):
        result = evaluate_must_kill_mutation(mutant=MUST_KILL_MUTATIONS[0], observation=_lifecycle())
        assert result["classification"] == "NO_FAULT_EXPOSED"


class TestRealSchemaShape:
    def test_work_lifecycle_schema_defines_required_transition_states(self):
        schema = json.loads(WORK_LIFECYCLE_SCHEMA.read_text(encoding="utf-8"))
        states = {item for item in schema["definitions"]["state"]["enum"]}
        assert REQUIRED_TRANSITIONS.keys() - states == set()


class TestSubjectLocalResolutionFamily:
    def test_baseline_phenomenon_external_subject_is_not_falsely_resolved_locally(self):
        """Corrected surface (master): PHENOMENON is not in the local resolution map,
        so an external phenomenon ref is accepted. The schemas never changed."""
        known_subject_ids = {
            "WORK_INTERPRETATION": {"WI-1"},
            "MATERIAL_CLAIM": {"C1"},
        }
        observation = _phenomenon_observation(known_subject_ids)
        assert verify_adversarial(["SUBJECT_LOCAL_RESOLUTION_STABLE"], _lifecycle(**observation)) == []

    def test_m7_escape_non_target_subject_resolution_detected_with_identical_schemas(self):
        """Escaped surface (df3e861): PHENOMENON is silently added to the local
        resolution map, so the real validator now rejects the external phenomenon ref
        while the schemas stayed identical. T2-C flags the non-target collateral."""
        known_subject_ids = {
            "WORK_INTERPRETATION": {"WI-1"},
            "MATERIAL_CLAIM": {"C1"},
            "PHENOMENON": set(),
        }
        observation = _phenomenon_observation(known_subject_ids)
        violations = verify_adversarial(["SUBJECT_LOCAL_RESOLUTION_STABLE"], _lifecycle(**observation))
        assert any("NON_TARGET_SUBJECT_RESOLUTION:PHENOMENON" in v for v in violations)

    def test_authorized_legitimate_resolution_change_passes(self):
        """A declared/authorized extension of the local resolution surface is allowed:
        no false positive when PHENOMENON resolution is explicitly authorized."""
        known_subject_ids = {
            "WORK_INTERPRETATION": {"WI-1"},
            "MATERIAL_CLAIM": {"C1"},
            "PHENOMENON": set(),
        }
        observation = _phenomenon_observation(known_subject_ids, declared=["PHENOMENON"])
        assert verify_adversarial(["SUBJECT_LOCAL_RESOLUTION_STABLE"], _lifecycle(**observation)) == []

    def test_resolution_surface_mutant_killed(self):
        known_subject_ids = {
            "WORK_INTERPRETATION": {"WI-1"},
            "MATERIAL_CLAIM": {"C1"},
            "PHENOMENON": set(),
        }
        observation = _phenomenon_observation(known_subject_ids)
        result = evaluate_must_kill_mutation(mutant=MUST_KILL_MUTATIONS[4], observation=_lifecycle(**observation))
        assert result["classification"] == "KILLED"
