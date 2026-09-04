from copy import deepcopy
import json

import pytest

from src.application.interaction import HumanDecision
from src.application.research_b2 import SoftwareAcquisitionAdapter
from src.application.research_b3 import ResearchB3Error, ResearchB3Orchestrator, ResearchB3Persistence
from src.core.contract_validation import validate_work_research_dossier
from src.core.mission_completion_gate import MissionContract
from tests.core.test_plan012_m3_b2_base_research import (
    _context,
    _dossier,
    _phenomenon,
    _run,
    _software_binding,
    _sufficiency,
    _work_binding,
)


def _json(ref):
    return json.loads(open(ref["path"], encoding="utf-8").read())


def _baseline(tmp_path, *, fidelity="APTA", work_ids=("W1", "W2", "W3")):
    b2_root = tmp_path / "b2"
    b2_root.mkdir(parents=True, exist_ok=True)
    result, _ = _run(b2_root, work_ids=work_ids, fidelity=fidelity)
    pool = _json(result["base_research_pool"])["dossiers"]
    plan = _json(result["research_plan"])
    plan["target_final_works_decision"] = {
        "status": "CONFIRMED",
        "requested_count": len(work_ids),
        "decision_basis": "Resolución explícita de fixture para el formato vigente.",
        "decision_ref": "decision:fixture-target-final-works",
    }
    return {
        "research_plan": plan,
        "phenomenon_base_research": _json(result["phenomenon_base_research"]),
        "work_discovery": _json(result["work_discovery"]),
        "base_research_pool": pool,
        "preliminary_fidelity": _json(result["preliminary_fidelity"])["dossiers"],
        "initial_sufficiency": _json(result["initial_sufficiency"])["dossiers"],
        "provisional_thesis": _json(result["provisional_thesis"]),
        "research_comparison": _json(result["research_comparison"]),
        "deepening_targets": result["deepening_targets"],
        "lifecycle": result["lifecycle_projection"],
    }


def _m4_context():
    return _context()


def _replace_text(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_replace_text(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: _replace_text(item, old, new) for key, item in value.items()}
    return value


def _run_m4(
    tmp_path,
    *,
    fidelity="APTA",
    cognitive=None,
    selection=None,
    work_bindings=None,
    work_representation_bindings=None,
    baseline=None,
    selection_mode="USER_SELECTION",
    delegation_decision=None,
    selection_options=None,
):
    baseline = baseline or _baseline(tmp_path, fidelity=fidelity)
    selected_work_ids = sorted(item["work"]["material_id"] for item in baseline["base_research_pool"])
    deep_fidelity = {}
    for work_id in selected_work_ids:
        value = _deep_dossier(work_id, stage="DEEP_FIDELITY", fidelity=fidelity)
        value["deep_fidelity"] = "APROBADA_CON_LIMITES" if fidelity == "APTA_CON_RIESGOS" else "APROBADA"
        if fidelity == "APTA_CON_RIESGOS":
            value["downstream_restrictions"] = [
                {
                    "restriction_id": f"restriction:{work_id}:deep",
                    "kind": "CLAIM_LIMITED",
                    "statement": "Usar con alcance explícito.",
                    "affected_consumers": ["B5-I3"],
                }
            ]
        deep_fidelity[work_id] = value
    seen = []

    def default_cognitive(request):
        seen.append(request)
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DELEGATED_SELECTION":
            return {
                "selected_work_ids": selected_work_ids,
                "set_rationale": "Conjunto delegado dentro del alcance autorizado.",
                "evidence_refs": [f"D-{work_id}" for work_id in selected_work_ids],
                "criteria_used": ["evidencia", "fidelidad", "complementariedad"],
                "limitations": ["No es decisión narrativa final."],
            }
        if request.stage == "DEEP_WORK_RESEARCH":
            return _deep_dossier(_request_work_id(request))
        if request.stage == "DEEP_FIDELITY":
            return deep_fidelity[_request_work_id(request)]
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    adapter = SoftwareAcquisitionAdapter(
        {"S1": _software_binding()},
        work_bindings=(
            {work_id: _work_binding(work_id) for work_id in selected_work_ids}
            if work_bindings is None
            else work_bindings
        ),
        work_representation_bindings=work_representation_bindings,
    )
    decision = selection or HumanDecision(
        request_id="RP-FIXTURE:M4:SELECTION_REQUEST",
        action="APPROVE",
        selected_option=None,
        actor_ref="OWNER",
        channel="TERMINAL",
    )
    def executor(request):
        value = (cognitive or default_cognitive)(request)
        if cognitive and request.stage in {"DEEP_WORK_RESEARCH", "DEEP_FIDELITY"}:
            requested_work_id = _request_work_id(request)
            actual_work_id = value.get("work", {}).get("material_id") if isinstance(value, dict) else None
            if actual_work_id == "W1" and requested_work_id != "W1":
                value = _replace_text(value, "W1", requested_work_id)
        return value
    result = ResearchB3Orchestrator(
        executor,
        ResearchB3Persistence(tmp_path / "m4"),
        acquisition_adapter=adapter,
    ).run(
        baseline,
        context=_m4_context(),
        human_decision=decision,
        selection_mode=selection_mode,
        delegation_decision=delegation_decision,
        selection_options=selection_options,
    )
    return result, seen


def _request_work_id(request):
    return request.prepared_contract.get("input_payload", {}).get("work_id") or request.prepared_contract.get("runtime_values", {}).get("work_id")


def _deep_dossier(work_id: str, stage: str = "DEEP_RESEARCH", fidelity: str = "NOT_ASSESSED") -> dict:
    value = _dossier(work_id, stage=stage, fidelity=fidelity)
    value.update(
        {
            "evidence_type_separation": {
                "work_evidence_refs": [f"D-{work_id}"],
                "external_reality_evidence_refs": ["S1"],
            },
            "deep_research": {
                "facts": [f"Hecho verificable de {work_id}."],
                "actions": [f"Acción observable de {work_id}."],
                "decisions": [f"Decisión observable de {work_id}."],
                "consequences": [f"Consecuencia documentada de {work_id}."],
                "interpretations": [f"Interpretación limitada de {work_id}."],
                "rival_readings": [f"Lectura rival de {work_id}."],
                "contradictions": [],
                "limits": ["La evidencia no permite afirmar más allá de lo documentado."],
                "risks": ["Riesgo de sobreinterpretación controlado."],
                "pending_questions": [],
                "work_evidence_refs": [f"D-{work_id}"],
                "external_reality_evidence_refs": ["S1"],
            },
            "provisional_thesis_relation": {
                "thesis_ref": "RP-FIXTURE:THESIS:PROVISIONAL",
                "supports": [f"La evidencia de {work_id} apoya parcialmente la tesis."],
                "qualifies": ["La relación queda limitada por el alcance de la evidencia."],
                "does_not_establish": ["No demuestra causalidad por sí sola."],
                "refutation_signals": ["Evidencia contraria material."],
            },
        }
    )
    return value


def test_m4_runs_selection_deep_research_and_fidelity_without_m5(tmp_path):
    result, seen = _run_m4(tmp_path)

    manifest = _json(result["execution_manifest"])
    assert manifest["selection"]["selected_work_ids"] == ["W1", "W2", "W3"]
    assert manifest["b2_inputs"]["deepening_targets"]["source_artifact_ref"] == "RP-FIXTURE:COMPARISON:INITIAL"
    assert manifest["selection"]["final_narrative_selection"] is False
    assert manifest["m5_outputs_not_produced"] is True
    assert [request.stage for request in seen] == [
        "DEEP_PHENOMENON_RESEARCH",
        "DEEP_PHENOMENON_SUFFICIENCY",
        "DEEP_WORK_RESEARCH",
        "DEEP_WORK_RESEARCH",
        "DEEP_WORK_RESEARCH",
        "DEEP_FIDELITY",
        "DEEP_FIDELITY",
        "DEEP_FIDELITY",
        "DEEP_WORK_SUFFICIENCY",
        "DEEP_WORK_SUFFICIENCY",
        "DEEP_WORK_SUFFICIENCY",
    ]
    assert manifest["stage_order"] == [
        "SELECTION",
        "DEEP_PHENOMENON_RESEARCH",
        "DEEP_PHENOMENON_SUFFICIENCY",
        "DEEP_WORK_RESEARCH",
        "DEEP_FIDELITY",
        "DEEP_WORK_SUFFICIENCY",
    ]


def test_m4_mission_contract_is_loadable_by_runtime_model():
    contract_path = "plans/plan_012/b1_contract_boundary/m4_deep_research/mission_contract.json"
    contract = json.loads(open(contract_path, encoding="utf-8").read())
    loaded = MissionContract.from_dict(contract)
    assert loaded.mission_id == "PLAN012_M4_B3_SELECTION_DEEP_RESEARCH"
    assert loaded.contains_material_repair is True
    assert "src/application/research_b2.py" in loaded.reduced_fields["allowed_files"]
    assert "src/core/contract_validation.py" in loaded.reduced_fields["allowed_files"]


def test_m4_preserves_explicit_risks_and_deep_limitations(tmp_path):
    result, _ = _run_m4(tmp_path, fidelity="APTA_CON_RIESGOS")
    deep = _json(result["deep_fidelity"])["dossiers"][0]

    assert deep["preliminary_fidelity"] == "APTA_CON_RIESGOS"
    assert deep["deep_fidelity"] == "APROBADA_CON_LIMITES"
    assert deep["downstream_restrictions"]


def test_m4_rejects_human_substitution_outside_candidate_set(tmp_path):
    baseline = _baseline(tmp_path)
    decision = HumanDecision(
        request_id="RP-FIXTURE:M4:SELECTION_REQUEST",
        action="SELECT_ALTERNATIVE",
        selected_option="SELECTION_SET:W2",
        actor_ref="OWNER",
        channel="TERMINAL",
    )
    with pytest.raises(ResearchB3Error, match="HUMAN_SELECTION_INVALID"):
        ResearchB3Orchestrator(
            lambda request: _phenomenon(),
            ResearchB3Persistence(tmp_path / "m4"),
            acquisition_adapter=SoftwareAcquisitionAdapter(
                {"S1": _software_binding()}, work_bindings={"W1": _work_binding("W1")}
            ),
        ).run(baseline, context=_m4_context(), human_decision=decision)


def test_m4_delegated_selection_is_scoped(tmp_path):
    baseline = _baseline(tmp_path)
    result, _ = _run_m4(
        tmp_path,
        baseline=baseline,
        selection_mode="DELEGATED_SELECTION",
        delegation_decision={
            "decision": "DELEGATE",
            "reasons": ["scope explícito"],
            "policy_version": "1.0.0",
            "evidence_refs": ["D-W1", "D-W2", "D-W3"],
            "authorized_candidate_set": ["W1", "W2", "W3"],
        },
    )
    selected = [item["work_id"] for item in result["selection"]["works"] if item["selection_state"] == "SELECTED"]
    assert selected == ["W1", "W2", "W3"]
    delegated_artifact = _json({"path": str(tmp_path / "m4" / "m4_selection_decision.json")})
    assert delegated_artifact["set_rationale"]
    assert delegated_artifact["authorized_candidate_set"] == ["W1", "W2", "W3"]
    assert delegated_artifact["criteria_used"]


def test_m4_software_owns_invented_identity_and_timestamp(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            value = _phenomenon()
            value.update({"research_id": "invented", "created_at": "not-a-date", "artifact_validity": "VALID"})
            return value
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier("W1")
            value.update({"dossier_id": "invented", "dossier_version": "99.0.0", "created_at": "bad"})
            return value
        if request.stage == "DEEP_FIDELITY":
            value = _deep_dossier("W1", stage="DEEP_FIDELITY")
            value["deep_fidelity"] = "APROBADA"
            return value
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    result, _ = _run_m4(tmp_path, cognitive=cognitive)
    phenomenon = _json(result["deep_phenomenon_research"])
    dossier = _json(result["deep_work_research"])["dossiers"][0]
    assert phenomenon["research_id"] == "RP-FIXTURE"
    assert phenomenon["created_at"] != "not-a-date"
    assert dossier["dossier_id"] == "RP-FIXTURE:M4:DOSSIER:W1"
    assert dossier["dossier_version"] == "2.0.0"
    assert dossier["lineage"] and "software:work-acquisition:W1" in dossier["lineage"]


def test_m4_requires_software_work_acquisition_binding(tmp_path):
    with pytest.raises(Exception, match="WORK_ACQUISITION_BINDING_REQUIRED"):
        _run_m4(tmp_path, work_bindings={})


def test_m4_binds_research_stop_to_real_deep_scopes(tmp_path):
    result, _ = _run_m4(tmp_path)
    phenomenon_stop = _json(result["deep_phenomenon_sufficiency"])
    work_stop = _json(result["deep_work_sufficiency"])["dossiers"][0]
    dossier = _json(result["deep_fidelity"])["dossiers"][0]

    assert phenomenon_stop["subject_kind"] == "PHENOMENON"
    assert phenomenon_stop["subject_ref"] == "RP-FIXTURE"
    assert work_stop["subject_kind"] == "WORK_RESEARCH_DOSSIER"
    assert work_stop["subject_ref"] == dossier["dossier_id"]


def test_m4_requires_provisional_thesis_and_deepening_targets(tmp_path):
    baseline = _baseline(tmp_path / "missing-thesis")
    baseline.pop("provisional_thesis")
    with pytest.raises(ResearchB3Error, match="PROVISIONAL_THESIS_REQUIRED"):
        _run_m4(tmp_path / "missing-thesis-run", baseline=baseline)

    baseline = _baseline(tmp_path / "missing-targets")
    baseline["deepening_targets"] = {"phenomenon": [], "works": {"W1": []}}
    with pytest.raises(ResearchB3Error, match="PHENOMENON_DEEPENING_TARGETS_REQUIRED"):
        _run_m4(tmp_path / "missing-targets-run", baseline=baseline)

    baseline = _baseline(tmp_path / "narrative-thesis")
    baseline["provisional_thesis"]["packaging_alignment"] = "Empaquetar como promesa editorial."
    with pytest.raises(ResearchB3Error, match="B2_THESIS_NARRATIVE_FIELDS_FORBIDDEN"):
        _run_m4(tmp_path / "narrative-thesis-run", baseline=baseline)


def test_m4_enforces_selection_policy_and_confirmed_target(tmp_path):
    baseline = _baseline(tmp_path / "policy")
    baseline["research_plan"]["selection_policy"]["mode"] = "DELEGATED_SELECTION"
    with pytest.raises(ResearchB3Error, match="SELECTION_POLICY_MODE_MISMATCH"):
        _run_m4(tmp_path / "policy-run", baseline=baseline)

    baseline = _baseline(tmp_path / "target")
    baseline["research_plan"]["target_final_works_decision"] = {
        "status": "CONFIRMED",
        "requested_count": 4,
        "decision_basis": "Decisión explícita del OWNER.",
        "decision_ref": "decision:target-final-works",
    }
    with pytest.raises(ResearchB3Error, match="CONFIRMED_TARGET_COUNT_NOT_RESPECTED"):
        _run_m4(tmp_path / "target-run", baseline=baseline)


def test_m4_recommended_target_requires_explicit_acceptance_before_selection(tmp_path):
    baseline = _baseline(tmp_path)
    with pytest.raises(ResearchB3Error, match="HUMAN_SELECTION_REQUIRED"):
        ResearchB3Orchestrator(
            lambda request: pytest.fail("No debe haber cognición antes de la aceptación"),
            ResearchB3Persistence(tmp_path / "m4"),
            acquisition_adapter=SoftwareAcquisitionAdapter(
                {"S1": _software_binding()}, work_bindings={"W1": _work_binding("W1")}
            ),
        ).run(baseline, context=_m4_context(), human_decision=None)


def test_m4_recommended_target_rejects_selection_without_quantity_resolution(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["research_plan"]["target_final_works_decision"] = {
        "status": "RECOMMENDED",
        "requested_count": 4,
        "decision_basis": "Recomendación pendiente de resolución explícita.",
        "decision_ref": "decision:fixture-target-final-works-recommended",
    }
    decision = HumanDecision(
        request_id="RP-FIXTURE:M4:SELECTION_REQUEST",
        action="APPROVE",
        actor_ref="OWNER",
        channel="TERMINAL",
    )
    with pytest.raises(ResearchB3Error, match="RECOMMENDED_TARGET_COUNT_RESOLUTION_REQUIRED"):
        _run_m4(tmp_path / "recommended-count", baseline=baseline, selection=decision)


def test_m4_recommended_target_rejects_alternative_below_minimum(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["research_plan"]["target_final_works_decision"] = {
        "status": "RECOMMENDED",
        "requested_count": 4,
        "decision_basis": "Recomendación pendiente de resolución explícita.",
        "decision_ref": "decision:fixture-target-final-works-recommended",
    }
    decision = HumanDecision(
        request_id="RP-FIXTURE:M4:SELECTION_REQUEST",
        action="SELECT_ALTERNATIVE",
        selected_option="SELECTION_SET:W1",
        actor_ref="OWNER",
        channel="TERMINAL",
    )
    with pytest.raises(ResearchB3Error, match="TARGET_FINAL_WORKS_COUNT_INVALID"):
        _run_m4(
            tmp_path / "recommended-alternative-below-minimum",
            baseline=baseline,
            selection=decision,
            selection_options=[["W1"], ["W1", "W2", "W3"]],
        )


def test_m4_not_declared_rejects_human_selection(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["research_plan"]["target_final_works_decision"].update(
        {"status": "NOT_DECLARED", "requested_count": None, "decision_ref": None}
    )
    decision = HumanDecision(
        request_id="RP-FIXTURE:M4:SELECTION_REQUEST",
        action="SELECT_ALTERNATIVE",
        selected_option="SELECTION_SET:W1,W2,W3",
        actor_ref="OWNER",
        channel="TERMINAL",
    )
    with pytest.raises(ResearchB3Error, match="TARGET_FINAL_WORKS_RESOLUTION_REQUIRED"):
        _run_m4(tmp_path / "not-declared-human", baseline=baseline, selection=decision)


def test_m4_not_declared_rejects_delegated_selection(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["research_plan"]["target_final_works_decision"].update(
        {"status": "NOT_DECLARED", "requested_count": None, "decision_ref": None}
    )
    with pytest.raises(ResearchB3Error, match="TARGET_FINAL_WORKS_RESOLUTION_REQUIRED"):
        _run_m4(
            tmp_path / "not-declared-delegated",
            baseline=baseline,
            selection_mode="DELEGATED_SELECTION",
            delegation_decision={
                "decision": "DELEGATE",
                "reasons": ["scope explícito"],
                "policy_version": "1.0.0",
                "evidence_refs": ["D-W1", "D-W2", "D-W3"],
                "authorized_candidate_set": ["W1", "W2", "W3"],
            },
        )


def test_m4_explicit_target_modification_four_to_three_is_accepted(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["research_plan"]["target_final_works_decision"] = {
        "status": "CONFIRMED",
        "requested_count": 3,
        "decision_basis": "El OWNER modifica explícitamente la recomendación de 4 a 3.",
        "decision_ref": "decision:owner-modifies-4-to-3",
    }
    result, _ = _run_m4(tmp_path / "explicit-four-to-three", baseline=baseline)
    assert [item["work_id"] for item in result["selection"]["works"] if item["selection_state"] == "SELECTED"] == [
        "W1", "W2", "W3"
    ]


def test_m4_rejects_invented_deep_evidence_reference(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier("W1")
            value["deep_research"]["work_evidence_refs"] = ["AI:INVENTED:EVIDENCE:999"]
            return value
        return _phenomenon() if request.stage == "DEEP_PHENOMENON_RESEARCH" else (
            dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
            if request.stage == "DEEP_PHENOMENON_SUFFICIENCY"
            else dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")
        )

    with pytest.raises(ResearchB3Error, match="DEEP_WORK_RESEARCH_EVIDENCE_REF_UNRESOLVED"):
        _run_m4(tmp_path, cognitive=cognitive)


@pytest.mark.parametrize("technical_ref", ["W1", "RP-FIXTURE", "RP-FIXTURE:THESIS:PROVISIONAL", "RP-FIXTURE:COMPARISON:INITIAL"])
def test_m4_rejects_technical_identifiers_as_deep_evidence_refs(tmp_path, technical_ref):
    def cognitive(request):
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier(_request_work_id(request))
            value["deep_research"]["work_evidence_refs"] = [technical_ref]
            return value
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    with pytest.raises(ResearchB3Error, match="DEEP_WORK_RESEARCH_EVIDENCE_REF_UNRESOLVED"):
        _run_m4(tmp_path / technical_ref.replace(":", "-"), cognitive=cognitive)


def test_m4_rejects_invented_evidence_type_separation_reference(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier("W1")
            value["evidence_type_separation"]["external_reality_evidence_refs"] = [
                "AI:INVENTED:EXTERNAL:EVIDENCE"
            ]
            return value
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    with pytest.raises(ResearchB3Error, match="DEEP_WORK_RESEARCH_EVIDENCE_REF_UNRESOLVED"):
        _run_m4(tmp_path, cognitive=cognitive)


def test_m4_rejects_invented_delegated_selection_evidence_reference(tmp_path):
    def cognitive(request):
        if request.stage == "DELEGATED_SELECTION":
            return {
                "selected_work_ids": ["W1"],
                "set_rationale": "Selección acotada.",
                "evidence_refs": ["AI:FAKE:EVIDENCE"],
                "criteria_used": ["evidencia"],
                "limitations": [],
            }
        return _phenomenon()

    with pytest.raises(ResearchB3Error, match="DELEGATED_SELECTION_EVIDENCE_REF_UNRESOLVED"):
        _run_m4(
            tmp_path,
            cognitive=cognitive,
            selection_mode="DELEGATED_SELECTION",
            delegation_decision={
                "decision": "DELEGATE",
                "reasons": ["scope explícito"],
                "policy_version": "1.0.0",
                "evidence_refs": ["R-1"],
                "authorized_candidate_set": ["W1"],
            },
        )


def test_m4_rejects_technical_identifier_as_delegated_evidence_ref(tmp_path):
    def cognitive(request):
        if request.stage == "DELEGATED_SELECTION":
            return {
                "selected_work_ids": ["W1", "W2", "W3"],
                "set_rationale": "Selección acotada.",
                "evidence_refs": ["W1"],
                "criteria_used": ["evidencia"],
                "limitations": [],
            }
        return _phenomenon()

    with pytest.raises(ResearchB3Error, match="DELEGATED_SELECTION_EVIDENCE_REF_UNRESOLVED"):
        _run_m4(
            tmp_path,
            cognitive=cognitive,
            selection_mode="DELEGATED_SELECTION",
            delegation_decision={
                "decision": "DELEGATE",
                "reasons": ["scope explícito"],
                "policy_version": "1.0.0",
                "evidence_refs": ["D-W1", "D-W2", "D-W3"],
                "authorized_candidate_set": ["W1", "W2", "W3"],
            },
        )


def test_m4_delegated_target_count_is_not_invented_by_software(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["research_plan"]["target_final_works_decision"] = {
        "status": "DELEGATED",
        "requested_count": 4,
        "decision_basis": "Delegación explícita.",
        "decision_ref": "decision:delegated-target",
    }

    def cognitive(request):
        if request.stage == "DELEGATED_SELECTION":
            return {
                "selected_work_ids": ["W1"],
                "set_rationale": "Selección acotada.",
                "evidence_refs": ["D-W1"],
                "criteria_used": ["evidencia"],
                "limitations": [],
            }
        return _deep_dossier("W1")

    with pytest.raises(ResearchB3Error, match="DELEGATED_TARGET_COUNT_NOT_RESPECTED"):
        _run_m4(
            tmp_path / "delegated-target",
            baseline=baseline,
            cognitive=cognitive,
            selection_mode="DELEGATED_SELECTION",
            delegation_decision={
                "decision": "DELEGATE",
                "reasons": ["scope explícito"],
                "policy_version": "1.0.0",
                "evidence_refs": ["R-1"],
                "authorized_candidate_set": ["W1"],
            },
        )


def test_m4_delegated_selection_is_cognitive_and_not_first_option(tmp_path):
    baseline = _baseline(tmp_path)
    deep_fidelity = {
        work_id: _deep_dossier(work_id, stage="DEEP_FIDELITY")
        for work_id in ("W1", "W2", "W3")
    }
    for dossier in deep_fidelity.values():
        dossier["deep_fidelity"] = "APROBADA"
    calls = []

    def cognitive(request):
        calls.append(request)
        if request.stage == "DELEGATED_SELECTION":
            return {
                "selected_work_ids": ["W1", "W2", "W3"],
                "set_rationale": "El conjunto aporta contraste y cobertura diferencial.",
                "evidence_refs": ["D-W1", "D-W2", "D-W3"],
                "criteria_used": ["cobertura", "contraste", "fidelidad"],
                "limitations": ["No es decisión narrativa final."],
            }
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DEEP_WORK_RESEARCH":
            return _deep_dossier(_request_work_id(request))
        if request.stage == "DEEP_FIDELITY":
            return deep_fidelity[_request_work_id(request)]
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    result = ResearchB3Orchestrator(
        cognitive,
        ResearchB3Persistence(tmp_path / "m4"),
        acquisition_adapter=SoftwareAcquisitionAdapter(
            {"S1": _software_binding()},
            work_bindings={work_id: _work_binding(work_id) for work_id in ("W1", "W2", "W3")},
        ),
    ).run(
        baseline,
        context=_m4_context(),
        selection_mode="DELEGATED_SELECTION",
        delegation_decision={
            "decision": "DELEGATE",
            "reasons": ["scope explícito"],
            "policy_version": "1.0.0",
            "evidence_refs": ["D-W1", "D-W2", "D-W3"],
            "authorized_candidate_set": ["W1", "W2", "W3"],
        },
    )
    assert result["selection"]["works"][1]["selection_state"] == "SELECTED"
    assert [request.stage for request in calls][0] == "DELEGATED_SELECTION"


def test_m4_rejects_deep_stop_using_b2_intended_use(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return _sufficiency()
        return _sufficiency()

    with pytest.raises(ResearchB3Error, match="RESEARCH_STOP_INTENDED_USE_MISMATCH"):
        _run_m4(tmp_path, cognitive=cognitive)


def test_m4_materializes_open_scope_and_post_deep_orthogonal_states(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency("MORE_RESEARCH_REQUIRED"), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DEEP_WORK_RESEARCH":
            return _deep_dossier("W1")
        if request.stage == "DEEP_FIDELITY":
            dossier = _deep_dossier("W1", stage="DEEP_FIDELITY")
            dossier["deep_fidelity"] = "MAS_INVESTIGACION_REQUERIDA"
            return dossier
        return dict(
            _sufficiency("MORE_RESEARCH_REQUIRED"),
            intended_use="DEEP_WORK_RESEARCH",
            pending_matters=["Falta corroboración focal."],
        )

    result, _ = _run_m4(tmp_path, cognitive=cognitive)
    manifest = _json(result["execution_manifest"])
    assert all(item["outcome"] != "SCOPE_COMPLETE" for item in manifest["scope_outcomes"])
    work = result["selection"]["works"][0]
    assert work["research_stage"] == "DEEP_FIDELITY"
    assert work["selection_state"] == "SELECTED"
    assert work["deep_fidelity"] == "MAS_INVESTIGACION_REQUERIDA"
    assert work["research_sufficiency"] == "MORE_RESEARCH_REQUIRED"


def test_m4_rejects_invented_work_locator_and_keeps_dossier_identity_exact(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier("W1")
            value["work"]["consulted_representations"][0]["consulted_locator"] = "invented:locator"
            return value
        if request.stage == "DEEP_FIDELITY":
            value = _deep_dossier("W1", stage="DEEP_FIDELITY")
            value["deep_fidelity"] = "APROBADA"
            return value
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    with pytest.raises(ResearchB3Error, match="WORK_LOCATOR_BINDING_MISMATCH"):
        _run_m4(tmp_path, cognitive=cognitive)


def test_m4_accepts_new_software_recovered_work_representation(tmp_path):
    new_binding = _work_binding("W1")
    new_binding.update({
        "edition_or_version": "edición recuperada M4",
        "consulted_locator": "work:W1:m4-recovered",
        "recovery_artifact_ref": "recovery:W1:m4",
    })

    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage in {"DEEP_WORK_RESEARCH", "DEEP_FIDELITY"}:
            requested_work_id = _request_work_id(request)
            value = _deep_dossier(requested_work_id, stage="DEEP_FIDELITY" if request.stage == "DEEP_FIDELITY" else "DEEP_RESEARCH")
            if requested_work_id == "W1":
                value["work"]["consulted_representations"].append({
                "representation_kind": "ADAPTATION",
                "edition_or_version": "edición recuperada M4",
                "consulted_locator": "work:W1:m4-recovered",
                })
            if request.stage == "DEEP_FIDELITY":
                value["deep_fidelity"] = "APROBADA"
            return value
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    result, _ = _run_m4(
        tmp_path,
        cognitive=cognitive,
        work_representation_bindings={
            ("W1", "ADAPTATION", "edición recuperada M4", "work:W1:m4-recovered"): new_binding
        },
    )
    dossier = _json(result["deep_work_research"])["dossiers"][0]
    assert len(dossier["work"]["consulted_representations"]) == 2
    assert len(dossier["acquisition_bindings"]) == 2


def test_m4_persists_deep_research_without_legacy_narrative_analysis(tmp_path):
    result, _ = _run_m4(tmp_path)
    dossier = _json(result["deep_work_research"])["dossiers"][0]
    assert dossier["deep_research"]["facts"]
    assert dossier["deep_research"]["actions"]
    assert validate_work_research_dossier(dossier) == []


@pytest.mark.parametrize(
    ("category", "status"),
    [("decisions", "NOT_MATERIAL"), ("actions", "NOT_MATERIAL"), ("interpretations", "NOT_APPLICABLE")],
)
def test_m4_deep_research_categories_are_adaptive(category, status, tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier("W1")
            value["deep_research"][category] = []
            value["deep_research"].setdefault("category_status", {})[category] = status
            return value
        if request.stage == "DEEP_FIDELITY":
            value = _deep_dossier("W1", stage="DEEP_FIDELITY")
            value["deep_fidelity"] = "APROBADA"
            return value
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    result, _ = _run_m4(tmp_path, cognitive=cognitive)
    dossier = _json(result["deep_work_research"])['dossiers'][0]
    assert dossier["deep_research"][category] == []
    assert dossier["deep_research"]["category_status"][category] == status


def test_m4_rejects_empty_deep_research_category_without_materiality_status(tmp_path):
    def cognitive(request):
        if request.stage == "DEEP_PHENOMENON_RESEARCH":
            return _phenomenon()
        if request.stage == "DEEP_PHENOMENON_SUFFICIENCY":
            return dict(_sufficiency(), intended_use="DEEP_PHENOMENON_RESEARCH")
        if request.stage == "DEEP_WORK_RESEARCH":
            value = _deep_dossier("W1")
            value["deep_research"]["interpretations"] = []
            return value
        return dict(_sufficiency(), intended_use="DEEP_WORK_RESEARCH")

    with pytest.raises(ResearchB3Error, match="deep V2 debe justificar la categoría vacía 'interpretations'"):
        _run_m4(tmp_path, cognitive=cognitive)


def test_m4_rejects_selection_of_work_without_research_target(tmp_path):
    baseline = _baseline(tmp_path)
    baseline["deepening_targets"]["works"].pop("W2")
    decision = HumanDecision(
        request_id="RP-FIXTURE:M4:SELECTION_REQUEST",
        action="SELECT_ALTERNATIVE",
        selected_option="SELECTION_SET:W1,W2,W3",
        actor_ref="OWNER",
        channel="TERMINAL",
    )

    with pytest.raises(ResearchB3Error, match="WORK_DEEPENING_TARGETS_REQUIRED: W2"):
        _run_m4(
            tmp_path,
            baseline=baseline,
            selection=decision,
            selection_options=[["W1", "W2", "W3"]],
        )


def test_m4_instructions_define_delegated_selection_as_adaptive_set_optimization():
    prompt = open("prompts/roles/RESEARCH_AND_CURATION/1.0.0.md", encoding="utf-8").read().lower()
    skill = open(".agent/skills/skill_research_tema_y_obras.md", encoding="utf-8").read().lower()

    for text in (prompt, skill):
        assert "optim" in text
        assert "individual" in text
        assert "divers" in text
        assert "redund" in text
        assert "sobreinterpret" in text or "overinterpret" in text
        assert "limitaciones" in text or "limitations" in text


def test_m4_deep_output_preserves_provisional_thesis_linkage(tmp_path):
    result, _ = _run_m4(tmp_path)
    phenomenon = _json(result["deep_phenomenon_research"])
    dossier = _json(result["deep_fidelity"])["dossiers"][0]
    assert phenomenon["thesis_stage"] == "PROVISIONAL"
    assert "software:thesis:RP-FIXTURE:THESIS:PROVISIONAL" in phenomenon["lineage"]
    assert dossier["provisional_thesis_relation"]["thesis_ref"] == "RP-FIXTURE:THESIS:PROVISIONAL"
    assert "software:thesis:RP-FIXTURE:THESIS:PROVISIONAL" in dossier["lineage"]


def test_m4_passes_b2_thesis_targets_and_risks_into_deep_cognition(tmp_path):
    result, seen = _run_m4(tmp_path, fidelity="APTA_CON_RIESGOS")
    deep_work_request = next(item for item in seen if item.stage == "DEEP_WORK_RESEARCH")
    payload = deep_work_request.prepared_contract["input_payload"]
    assert payload["provisional_thesis"]["stage"] == "THESIS_PROVISIONAL"
    assert payload["deepening_targets"]
    assert payload["base_dossier"]["work"]["material_id"] == "W1"
    assert payload["preliminary_risks"]
    assert payload["intended_use"]
    assert result["selection"]["works"][0]["thesis_stage"] == "PROVISIONAL"


def test_m4_artifact_reference_prioritizes_exact_dossier_identity():
    reference = ResearchB3Orchestrator._artifact_ref(
        {"research_id": "R1", "dossier_id": "D1", "lifecycle_id": "L1"},
        "WorkResearchDossier",
    )
    assert reference["artifact_id"] == "D1"
