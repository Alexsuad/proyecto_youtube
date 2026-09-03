from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.application.research_b2 import (
    ResearchB2Error,
    ResearchB2NoProgressGuard,
    ResearchB2Orchestrator,
    ResearchB2Persistence,
    SoftwareAcquisitionAdapter,
)
from src.core.contract_validation import validate_work_research_dossier
from tests.core.test_all_schemas import VALID_FIXTURES


def _plan() -> dict:
    return deepcopy(VALID_FIXTURES["research_plan"])


def _phenomenon() -> dict:
    value = deepcopy(VALID_FIXTURES["research_pack"])
    value.pop("narrative_opportunities", None)
    value.pop("editorial_uses", None)
    value.update(
        {
            "research_pack_kind": "PHENOMENON",
            "research_contract_version": "2.0.0",
            "research_stage": "BASE_RESEARCH",
            "research_sufficiency": "LIMITED_BUT_USABLE",
            "artifact_validity": "VALID",
            "thesis_stage": "NONE",
            "evidence_type_separation": {
                "work_evidence_refs": ["WORK-1"],
                "external_reality_evidence_refs": ["EXT-1"],
            },
        }
    )
    value["source_registry"][0].update(
        {
            "evidence_status": None,
            "retrieval_status": None,
            "recovery_artifact_ref": None,
            "retrieval_request_ref": None,
        }
    )
    value.pop("acquisition_bindings", None)
    return value


def _software_binding(**overrides) -> dict:
    binding = {
        "request_ref": "REQ-SOFTWARE-1",
        "execution_ref": "EXEC-SOFTWARE-1",
        "recovery_artifact_ref": "recovery:S1",
        "retrieval_status": "RECOVERED",
        "evidence_status": "VERIFIED",
        "software_controlled": True,
    }
    binding.update(overrides)
    return binding


def _sufficiency(status="SUFFICIENT_FOR_INTENDED_USE") -> dict:
    return {
        "decision_id": "RSD-B2-1",
        "decision_version": "2.0.0",
        "subject_kind": "PHENOMENON",
        "subject_ref": "RP-FIXTURE",
        "intended_use": "FORMULAR_TESIS_PROVISIONAL",
        "evidence_refs": ["S1"],
        "claim_decision": None,
        "sufficiency_status": status,
        "limitations": ["Alcance controlado."] if status == "LIMITED_BUT_USABLE" else [],
        "pending_matters": ["Investigar el punto pendiente."] if status == "MORE_RESEARCH_REQUIRED" else [],
        "unresolved_material_contradiction_refs": [],
        "invalidators": ["NEW_MATERIAL_EVIDENCE"],
        "return_route": "Continuar según el uso declarado.",
        "decision_basis": "Decisión basada en cobertura y evidencia recuperada.",
        "research_contract_version": "2.0.0",
        "artifact_validity": "VALID",
        "research_stage": "BASE_RESEARCH",
    }


def _work_sufficiency(work_id: str, status="SUFFICIENT_FOR_INTENDED_USE") -> dict:
    return {
        "decision_id": f"RSD-B2-{work_id}",
        "decision_version": "2.0.0",
        "subject_kind": "WORK_RESEARCH_DOSSIER",
        "subject_ref": f"RP-FIXTURE:DOSSIER:{work_id}",
        "intended_use": "RESEARCH_COMPARISON",
        "evidence_refs": [f"D-{work_id}"],
        "claim_decision": None,
        "sufficiency_status": status,
        "limitations": ["Límite controlado."] if status == "LIMITED_BUT_USABLE" else [],
        "pending_matters": ["Investigar el punto pendiente."] if status == "MORE_RESEARCH_REQUIRED" else [],
        "unresolved_material_contradiction_refs": [],
        "invalidators": ["NEW_MATERIAL_EVIDENCE"],
        "return_route": "Continuar según el uso declarado.",
        "decision_basis": "Decisión basada en evidencia recuperada de la obra.",
        "research_contract_version": "2.0.0",
        "artifact_validity": "VALID",
        "research_stage": "BASE_RESEARCH",
    }


def _work_binding(work_id: str) -> dict:
    return {
        "request_ref": f"REQ-WORK-{work_id}",
        "execution_ref": f"EXEC-WORK-{work_id}",
        "recovery_artifact_ref": f"recovery:{work_id}",
        "retrieval_status": "RECOVERED",
        "evidence_status": "VERIFIED",
        "software_controlled": True,
        "representation_kind": "ORIGINAL_WORK",
        "edition_or_version": "edición de prueba",
        "consulted_locator": f"work:{work_id}",
    }


def _comparison(work_ids: list[str]) -> dict:
    return {
        "comparison_id": "COMP-B2-1",
        "comparison_version": "2.0.0",
        "episode_id": "EP-001",
        "research_id": "RP-001",
        "candidate_work_ids": work_ids,
        "dimensions": ["CONTRIBUTION", "COVERAGE", "COMPLEMENTARITY", "REDUNDANCY", "CONTRAST", "FIDELITY", "LIMITATIONS", "EVIDENCE"],
        "entries": [
            {
                "work_id": work_id,
                "evidence_refs": [f"D-{work_id}"],
                "contribution": "Aporta evidencia propia.",
                "coverage": "Cubre una dimensión declarada.",
                "complementarity": "Complementa las demás candidatas.",
                "redundancy": "Redundancia revisada.",
                "contrast": "Permite contraste investigativo.",
                "fidelity": "Fidelidad preliminar compatible.",
                "limitations": ["Límite declarado."],
            }
            for work_id in work_ids
        ],
        "decision_stage": "INITIAL_RESEARCH_COMPARISON",
        "narrative_decision_made": False,
        "created_at": "2026-09-03T00:00:00+00:00",
    }


def _context() -> dict:
    return {
        "topic": "Fenómeno de prueba",
        "source_access": deepcopy(VALID_FIXTURES["source_access_and_evidence_report"]),
        "brief": {"brief_id": "BRIEF-1"},
        "channel_context": {"channel_id": "CHANNEL-1"},
    }


def _run(tmp_path, *, work_ids=("W1",), pool_ids=None, phenomenon=None, fidelity="APTA", sufficiency=None, acquisition_bindings=None, comparison=None, thesis=None, work_bindings=None):
    discovery = _discovery(list(work_ids))
    selected_pool_ids = list(pool_ids if pool_ids is not None else work_ids)
    pool = [_dossier(work_id) for work_id in selected_pool_ids]
    fidelity_output = []
    for item in pool:
        result = deepcopy(item)
        result["research_stage"] = "PRELIMINARY_FIDELITY"
        result["preliminary_fidelity"] = fidelity
        if fidelity == "APTA":
            result["research_sufficiency"] = "LIMITED_BUT_USABLE"
        elif fidelity == "APTA_CON_RIESGOS":
            result["downstream_restrictions"] = [
                {
                    "restriction_id": f"restriction:{item['work']['material_id']}",
                    "kind": "CLAIM_LIMITED",
                    "statement": "Usar con alcance explícito.",
                    "affected_consumers": ["B5-I3"],
                }
            ]
        fidelity_output.append(result)
    outputs = {
        "PHENOMENON_BASE_RESEARCH": phenomenon or _phenomenon(),
        "WORK_DISCOVERY": discovery,
        "BASE_RESEARCH_POOL": pool,
        "PRELIMINARY_FIDELITY": fidelity_output,
        "INITIAL_SUFFICIENCY": (
            ([sufficiency] + [_work_sufficiency(work_id) for work_id in selected_pool_ids])
            if isinstance(sufficiency, dict)
            else sufficiency
            if sufficiency is not None
            else [_sufficiency()] + [_work_sufficiency(work_id) for work_id in selected_pool_ids]
        ),
        "PROVISIONAL_THESIS": thesis or deepcopy(VALID_FIXTURES["thesis_artifact"]),
        "RESEARCH_COMPARISON": comparison or _comparison(selected_pool_ids),
    }
    seen = []

    def cognitive(request):
        seen.append(request)
        return deepcopy(outputs[request.stage])

    adapter = SoftwareAcquisitionAdapter(
        {"S1": acquisition_bindings or _software_binding()},
        work_bindings=(
            {work_id: _work_binding(work_id) for work_id in selected_pool_ids}
            if work_bindings is None
            else work_bindings
        ),
    )
    result = ResearchB2Orchestrator(
        cognitive,
        ResearchB2Persistence(tmp_path),
        acquisition_adapter=adapter,
    ).run(_plan(), context=_context())
    return result, seen


def _discovery(work_ids: list[str]) -> dict:
    return {
        "lifecycle_id": "LC-1",
        "lifecycle_version": "2.0.0",
        "episode_id": "EP-1",
        "research_id": "R-1",
        "entry_mode": "TOPIC_FIRST",
        "anchor_work_id": None,
        "works": [
            {
                "work_id": work_id,
                "state": "DISCOVERED_WORK",
                "state_version": "2.0.0",
                "identity_ref": f"identity:{work_id}",
                "version_ref": f"version:{work_id}",
                "is_anchor": False,
                "lineage_refs": ["discovery:1"],
                "stage_evidence_refs": [],
                "research_stage": "DISCOVERY",
                "selection_state": "NOT_EVALUATED",
                "preliminary_fidelity": "NOT_ASSESSED",
                "deep_fidelity": "NOT_ASSESSED",
                "research_sufficiency": "MORE_RESEARCH_REQUIRED",
                "artifact_validity": "VALID",
                "thesis_stage": "NONE",
                "research_contract_version": "2.0.0",
            }
            for work_id in work_ids
        ],
        "transitions": [],
        "screening": {
            "candidate_work_ids": [],
            "format_policy_ref": "policies/script_product/main_episode_format_policy.md",
            "range_status": "NOT_APPLICABLE",
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
        "created_at": "2026-09-03T00:00:00+00:00",
        "research_contract_version": "2.0.0",
    }


def _dossier(work_id: str, stage: str = "BASE_RESEARCH", fidelity: str = "NOT_ASSESSED") -> dict:
    value = {
        "dossier_id": f"D-{work_id}",
        "dossier_version": "2.0.0",
        "episode_id": "EP-1",
        "research_id": "R-1",
        "evidence_report_id": "ER-1",
        "work": {
            "material_id": work_id,
            "title": f"Obra {work_id}",
            "creator": "Creador de prueba",
            "consulted_representations": [
                {
                    "representation_kind": "ORIGINAL_WORK",
                    "edition_or_version": "edición de prueba",
                    "consulted_locator": f"work:{work_id}",
                }
            ],
        },
        "dossier_stage": "RESEARCH_IN_PROGRESS",
        "pending_items": [],
        "confidence": "MEDIUM",
        "created_at": "2026-09-03T00:00:00+00:00",
        "research_stage": stage,
        "selection_state": "CANDIDATE",
        "preliminary_fidelity": fidelity,
        "deep_fidelity": "NOT_ASSESSED",
        "research_sufficiency": "MORE_RESEARCH_REQUIRED",
        "artifact_validity": "VALID",
        "thesis_stage": "NONE",
        "research_contract_version": "2.0.0",
        "lineage": ["discovery:1"],
    }
    if fidelity == "APTA_CON_RIESGOS":
        value["downstream_restrictions"] = [
            {
                "restriction_id": f"restriction:{work_id}",
                "kind": "CLAIM_LIMITED",
                "statement": "Usar solo con atribución y alcance limitado.",
                "affected_consumers": ["B5-I3"],
            }
        ]
    return value


def test_research_plan_is_required_before_any_cognitive_step(tmp_path):
    calls = []
    orchestrator = ResearchB2Orchestrator(lambda request: calls.append(request), ResearchB2Persistence(tmp_path))
    invalid = _plan()
    invalid["dimensions"] = []
    with pytest.raises(ResearchB2Error, match="RESEARCH_PLAN_INVALID"):
        orchestrator.run(invalid, context=_context())
    assert calls == []


def test_no_silent_work_count_and_dynamic_discovery_without_quota(tmp_path):
    result, seen = _run(tmp_path, work_ids=("W1",))
    assert result["work_discovery"]["artifact_id"] == "RP-FIXTURE:DISCOVERY"
    assert len(seen) == 7
    assert result["lifecycle_projection"]["works"][0]["work_id"] == "W1"


def test_research_role_and_editorial_intent_remain_separate():
    plan = _plan()
    assert plan["research_role"] != plan["editorial_intent"]
    assert "research_role" in plan and "editorial_intent" in plan


def test_hypothesis_cannot_be_promoted_to_provisional_thesis(tmp_path):
    phenomenon = _phenomenon()
    phenomenon["thesis_stage"] = "PROVISIONAL"
    _run(tmp_path, phenomenon=phenomenon)
    persisted = json.loads((tmp_path / "phenomenon_base_research.json").read_text(encoding="utf-8"))
    assert persisted["thesis_stage"] == "NONE"


def test_base_research_pool_is_heuristic_not_a_minimum_quota(tmp_path):
    result, _ = _run(tmp_path, work_ids=("W1",))
    assert result["base_research_pool"]["artifact_id"].endswith("BASE_RESEARCH_POOL")


def test_base_research_pool_accepts_subset_and_preserves_filtered_discovery(tmp_path):
    result, _ = _run(
        tmp_path,
        work_ids=("W1", "W2", "W3", "W4"),
        pool_ids=("W1", "W3"),
    )
    works = {item["work_id"]: item for item in result["lifecycle_projection"]["works"]}
    assert set(works) == {"W1", "W2", "W3", "W4"}
    assert works["W1"]["research_stage"] == "PRELIMINARY_FIDELITY"
    assert works["W3"]["research_stage"] == "PRELIMINARY_FIDELITY"
    for work_id in ("W2", "W4"):
        assert works[work_id]["research_stage"] == "DISCOVERY"
        assert works[work_id]["preliminary_fidelity"] == "NOT_ASSESSED"
        assert works[work_id].get("dossier_ref") is None


def test_preliminary_fidelity_preserves_explicit_risks(tmp_path):
    result, _ = _run(tmp_path, fidelity="APTA_CON_RIESGOS")
    assert result["lifecycle_projection"]["works"][0]["preliminary_fidelity"] == "APTA_CON_RIESGOS"


def test_fail_closed_evidence_is_reused_from_m2(tmp_path):
    with pytest.raises(ResearchB2Error, match="evidencia|recuperación"):
        _run(tmp_path, acquisition_bindings=_software_binding(software_controlled=False))


def test_software_ai_software_boundary_and_persistence_order(tmp_path):
    result, seen = _run(tmp_path)
    events = result["events"]
    assert [request.stage for request in seen] == [
        "PHENOMENON_BASE_RESEARCH",
        "WORK_DISCOVERY",
        "BASE_RESEARCH_POOL",
        "PRELIMINARY_FIDELITY",
        "INITIAL_SUFFICIENCY",
        "PROVISIONAL_THESIS",
        "RESEARCH_COMPARISON",
    ]
    for index, request in enumerate(seen):
        assert request.input_artifacts
        offset = index * 5
        assert events[offset]["boundary"] == "SOFTWARE_PREPARE"
        assert events[offset + 1]["boundary"] == "IA_COGNITIVE_STEP"
        assert events[offset + 2]["boundary"] == "SOFTWARE_VALIDATE"
        assert events[offset + 3]["boundary"] == "SOFTWARE_ITERATION_GUARD"
        assert events[offset + 4]["boundary"] == "SOFTWARE_PERSIST"
    assert (tmp_path / "research_plan.json").exists()
    assert (tmp_path / "preliminary_fidelity.json").exists()


def test_research_outputs_do_not_make_narrative_decisions(tmp_path):
    phenomenon = _phenomenon()
    phenomenon["narrative_opportunities"] = []
    with pytest.raises(ResearchB2Error, match="no puede decidir narrativa"):
        _run(tmp_path, phenomenon=phenomenon)


def test_m2_compatible_dossier_shape_passes_existing_validator():
    assert validate_work_research_dossier(_dossier("W1")) == []


def test_initial_sufficiency_reuses_research_stop_and_blocks_invalid_status(tmp_path):
    with pytest.raises(ResearchB2Error, match="PROVISIONAL_THESIS_BLOCKED_BY_INVALID_SUFFICIENCY"):
        _run(tmp_path, sufficiency=_sufficiency("MORE_RESEARCH_REQUIRED"))


def test_provisional_thesis_is_allowed_only_after_valid_sufficiency(tmp_path):
    result, _ = _run(tmp_path)
    assert result["initial_sufficiency"]["artifact_id"].endswith("INITIAL_SUFFICIENCY")
    assert result["provisional_thesis"]["artifact_id"] == "RP-FIXTURE:THESIS:PROVISIONAL"
    sufficiency = json.loads((tmp_path / "initial_sufficiency.json").read_text(encoding="utf-8"))
    assert {(item["subject_kind"], item["subject_ref"]) for item in sufficiency["dossiers"]} == {
        ("PHENOMENON", "RP-FIXTURE"),
        ("WORK_RESEARCH_DOSSIER", "RP-FIXTURE:DOSSIER:W1"),
    }


def test_research_comparison_is_investigative_and_not_narrative(tmp_path):
    result, _ = _run(tmp_path, work_ids=("W1", "W2"))
    assert result["research_comparison"]["artifact_id"] == "RP-FIXTURE:COMPARISON:INITIAL"

    narrative_comparison = _comparison(["W1", "W2"])
    narrative_comparison["narrative_decision_made"] = True
    adversarial_path = tmp_path / "adversarial"
    _run(adversarial_path, work_ids=("W1", "W2"), comparison=narrative_comparison)
    persisted = json.loads((adversarial_path / "research_comparison.json").read_text(encoding="utf-8"))
    assert persisted["narrative_decision_made"] is False


def test_no_progress_guard_detects_repetition_cycle_and_iteration_limit():
    repeated = ResearchB2NoProgressGuard()
    assert repeated.observe(gap="GAP", evidence_refs=["E1"], state="A", result={"n": 1}).status == "PROGRESS"
    same = repeated.observe(gap="GAP", evidence_refs=["E1"], state="A", result={"n": 2})
    assert (same.status, same.route, same.reason) == (
        "NO_PROGRESS",
        "HUMAN_REVIEW",
        "SAME_GAP_STATE_AND_EVIDENCE",
    )

    cycle = ResearchB2NoProgressGuard()
    cycle.observe(gap="GAP", evidence_refs=["E1"], state="A", result={})
    cycle.observe(gap="GAP", evidence_refs=["E2"], state="B", result={})
    cycle_result = cycle.observe(gap="GAP", evidence_refs=["E3"], state="A", result={})
    assert (cycle_result.status, cycle_result.route, cycle_result.reason) == (
        "NO_PROGRESS",
        "STOP_LOCAL",
        "A_TO_B_TO_A_CYCLE",
    )

    limited = ResearchB2NoProgressGuard(max_iterations=2)
    limited.observe(gap="GAP", evidence_refs=["E1"], state="A", result={})
    limited.observe(gap="GAP", evidence_refs=["E2"], state="B", result={})
    limited_result = limited.observe(gap="GAP", evidence_refs=["E3"], state="C", result={})
    assert (limited_result.status, limited_result.route, limited_result.reason) == (
        "NO_PROGRESS",
        "STOP_LOCAL",
        "ITERATION_LIMIT_EXCEEDED",
    )


def test_acquisition_metadata_is_materialized_by_software(tmp_path):
    result, _ = _run(tmp_path)
    phenomenon = json.loads((tmp_path / "phenomenon_base_research.json").read_text(encoding="utf-8"))
    binding = phenomenon["acquisition_bindings"][0]
    assert binding["software_controlled"] is True
    assert binding["recovery_artifact_ref"] == "recovery:S1"
    assert phenomenon["source_registry"][0]["retrieval_request_ref"] == "REQ-SOFTWARE-1"
    assert result["phenomenon_base_research"]["artifact_id"] == "RP-FIXTURE"
    manifest = json.loads((tmp_path / "research_b2_execution.json").read_text(encoding="utf-8"))
    assert manifest["work_acquisition_bindings"][0]["software_controlled"] is True


def test_cognitive_output_cannot_claim_acquisition_binding(tmp_path):
    phenomenon = _phenomenon()
    phenomenon["acquisition_bindings"] = [_software_binding()]
    with pytest.raises(ResearchB2Error, match="COGNITIVE_OUTPUT_CANNOT_SET_ACQUISITION_BINDINGS"):
        _run(tmp_path, phenomenon=phenomenon)


def test_software_projection_rejects_cognitive_identity_metadata(tmp_path):
    phenomenon = _phenomenon()
    phenomenon.update(
        {
            "research_id": "IA-INVENTED-ID",
            "created_at": "1900-01-01T00:00:00+00:00",
            "research_contract_version": "9.9.9",
        }
    )
    _run(tmp_path, phenomenon=phenomenon)
    persisted = json.loads((tmp_path / "phenomenon_base_research.json").read_text(encoding="utf-8"))
    assert persisted["research_id"] == "RP-FIXTURE"
    assert persisted["research_contract_version"] == "2.0.0"
    assert persisted["created_at"] != "1900-01-01T00:00:00+00:00"


def test_work_locator_requires_software_acquisition_binding(tmp_path):
    with pytest.raises(ResearchB2Error, match="WORK_ACQUISITION_BINDING_REQUIRED"):
        _run(tmp_path, work_bindings={})


def test_research_stop_must_bind_to_real_execution_scopes(tmp_path):
    wrong_phenomenon = _sufficiency()
    wrong_phenomenon["subject_ref"] = "OTHER-PHENOMENON"
    with pytest.raises(ResearchB2Error, match="vincular exactamente"):
        _run(tmp_path, sufficiency=wrong_phenomenon)

    wrong_work = _work_sufficiency("W1")
    wrong_work["subject_ref"] = "RP-FIXTURE:DOSSIER:OTHER"
    with pytest.raises(ResearchB2Error, match="vincular exactamente"):
        _run(tmp_path / "wrong-work", sufficiency=[_sufficiency(), wrong_work])


@pytest.mark.parametrize("legacy_field", ["packaging_alignment", "viewer_transformation"])
def test_b2_thesis_projection_removes_legacy_editorial_fields(tmp_path, legacy_field):
    thesis = deepcopy(VALID_FIXTURES["thesis_artifact"])
    thesis[legacy_field] = "decisión editorial inventada"
    _run(tmp_path, thesis=thesis)
    thesis_path = tmp_path / "provisional_thesis.json"
    canonical = json.loads(thesis_path.read_text(encoding="utf-8"))
    assert legacy_field not in canonical


def test_b2_prompt_and_skill_keep_research_out_of_narrative():
    prompt = Path("prompts/roles/RESEARCH_AND_CURATION/1.0.0.md").read_text(encoding="utf-8")
    skill = Path(".agent/skills/skill_research_tema_y_obras.md").read_text(encoding="utf-8")
    assert "B2 Research V2" in prompt
    assert "does not require CurationDecision" in prompt
    assert "curate by narrative function" not in prompt
    assert "Modo B2 Research V2" in skill
    assert "requisito canónico de B2 V2" in skill
