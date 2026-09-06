"""Focal acceptance tests for the canonical PLAN012 M7 coordinator."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.ai.contracts import InputArtifact
from src.ai.execution import M3_REQUIRED_INPUT_KINDS
from src.application.research_m7 import ResearchM7Error, ResearchM7SyntheticRunner, ResearchV2B5I3Adapter
from src.cli import main


def _input(**overrides):
    value = {
        "episode_id": "EP-M7-TEST",
        "topic": "Fenómeno sintético controlado",
        "initial_question": "¿Qué puede afirmarse con evidencia?",
        "context": "Fixture sin investigación real.",
        "works": ["REAL-A", "REAL-B", "REAL-C"],
        "target_final_works": 3,
        "selected_work_ids": ["REAL-A", "REAL-B", "REAL-C"],
    }
    value.update(overrides)
    return value


def _read_stage(state, stage):
    ref = next(item for item in state["artifacts"] if item["stage"] == stage)
    return json.loads(Path(ref["path"]).read_text(encoding="utf-8"))


def _m5_output(state, kind):
    manifest = _read_stage(state, "M5")
    ref = next(item for item in manifest["m5_outputs"] if item["artifact_kind"] == kind)
    return json.loads(Path(ref["path"]).read_text(encoding="utf-8"))


def _handoff_inputs(handoff):
    return [
        InputArtifact(
            item["artifact_kind"],
            item["artifact_id"],
            Path(item["path"]),
            item["producer_run_id"],
            item.get("artifact_version", ""),
        )
        for item in handoff["b5_i3_input_refs"]
    ]


def test_m7_e2e_invokes_canonical_b2_b3_b4_and_stops_before_narrative(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path).run(_input())
    ResearchM7SyntheticRunner(tmp_path).assert_software_boundaries(state)
    assert state["status"] == "COMPLETED"
    assert state["m7_status"] == "READY_FOR_OWNER_REVIEW"
    assert state["research_vertical_e2e"] == "PASS"
    assert state["canonical_invocations"] == {
        "B2": "ResearchB2Orchestrator.run",
        "M4": "ResearchB3Orchestrator.run",
        "M5": "ResearchB3Orchestrator.run_m5",
        "M6": "ResearchB4Orchestrator.run_m6",
    }
    manifest = _read_stage(state, "M6")
    assert manifest["research_ready_state"] != "NOT_RESEARCH_READY"
    handoff = _read_stage(state, "B5_I3_HANDOFF")
    assert handoff["consumer"] == "B5-I3"
    assert handoff["validation"]["status"] == "PASS"
    assert handoff["validation"]["cognition_executed"] is False
    assert handoff["validation"]["research_handoff_precondition"] == "PASS"
    assert handoff["validation"]["research_ready_manifest_current"] is True
    assert handoff["validation"]["downstream_restrictions_resolvable"] is True
    assert handoff["validation"]["downstream_restrictions_count"] == len(manifest["downstream_restrictions"])
    assert handoff["research_lineage"]["lineage"] == manifest["lineage"]
    assert set(handoff["validation"]["provided_input_kinds"]) == M3_REQUIRED_INPUT_KINDS
    assert set(handoff["required_input_kinds"]) == M3_REQUIRED_INPUT_KINDS
    assert all(Path(item["path"]).is_file() for item in handoff["b5_i3_input_refs"])
    assert not any(field in handoff for field in {"viewer_journey", "narrative_plan", "opening_design", "closing_design"})


def test_research_v2_precondition_rejects_stale_handoff_with_old_inputs(tmp_path):
    initial = ResearchM7SyntheticRunner(tmp_path).run(_input())
    manifest_ref = next(item for item in initial["artifacts"] if item["stage"] == "M6")
    handoff_ref = next(item for item in initial["artifacts"] if item["stage"] == "B5_I3_HANDOFF")
    manifest = _read_stage(initial, "M6")
    old_handoff = _read_stage(initial, "B5_I3_HANDOFF")
    old_inputs = _handoff_inputs(old_handoff)
    invalidated = ResearchM7SyntheticRunner(tmp_path).invalidate("M5")
    stale_handoff = json.loads(Path(handoff_ref["path"]).read_text(encoding="utf-8"))
    assert invalidated["stale_handoff"] is True
    assert ResearchV2B5I3Adapter.validate_full_preflight("EP-M7-TEST", old_inputs)["status"] == "PASS"
    with pytest.raises(ResearchM7Error, match="B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_STALE"):
        ResearchV2B5I3Adapter.validate_research_v2_precondition(
            episode_id="EP-M7-TEST",
            manifest_ref=manifest_ref,
            manifest=manifest,
            handoff=stale_handoff,
            inputs=old_inputs,
        )


def test_research_v2_precondition_rejects_missing_restriction_binding(tmp_path):
    initial = ResearchM7SyntheticRunner(tmp_path).run(_input())
    manifest_ref = next(item for item in initial["artifacts"] if item["stage"] == "M6")
    manifest = _read_stage(initial, "M6")
    handoff = _read_stage(initial, "B5_I3_HANDOFF")
    assert manifest["downstream_restrictions"]
    inputs = _handoff_inputs(handoff)
    broken_handoff = copy.deepcopy(handoff)
    broken_handoff.pop("downstream_restriction_binding")
    assert ResearchV2B5I3Adapter.validate_full_preflight("EP-M7-TEST", inputs)["status"] == "PASS"
    with pytest.raises(ResearchM7Error, match="B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_UNBOUND"):
        ResearchV2B5I3Adapter.validate_research_v2_precondition(
            episode_id="EP-M7-TEST",
            manifest_ref=manifest_ref,
            manifest=manifest,
            handoff=broken_handoff,
            inputs=inputs,
        )


def test_b5_i3_producer_run_ids_are_pure_provenance(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path).run(_input())
    handoff = _read_stage(state, "B5_I3_HANDOFF")
    manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "M6")
    manifest_token = f"{manifest_ref['artifact_id']}@{manifest_ref['checksum']}"
    producer_ids = {
        item["artifact_kind"]: item["producer_run_id"]
        for item in handoff["b5_i3_input_bindings"]
    }
    assert producer_ids == {
        "human_input": "M7-TRANSVERSAL-FIXTURE",
        "active_editorial_profile_reference": "M7-PROFILE",
        "episode_brief": "M7-TRANSVERSAL-FIXTURE",
        "research_pack": "M7-B2",
        "claims_ledger": "M7-M5",
        "source_access_and_evidence_report": "M7-SOURCE",
        "narrative_human_analysis": "M7-TRANSVERSAL-FIXTURE",
        "material_curation": "M7-TRANSVERSAL-FIXTURE",
        "refined_thesis": "M7-M5",
        "editorial_script_promise": "M7-TRANSVERSAL-FIXTURE",
        "early_packaging_hypothesis": "M7-TRANSVERSAL-FIXTURE",
        "b5_i2_semantic_audit": "M7-TRANSVERSAL-FIXTURE",
        "youtube_adaptation_review": "M7-TRANSVERSAL-FIXTURE",
    }
    assert all("|" not in producer_id for producer_id in producer_ids.values())
    assert all(manifest_token not in producer_id for producer_id in producer_ids.values())
    assert handoff["research_ready_manifest_ref"]["checksum"] == manifest_ref["checksum"]
    assert handoff["b5_i3_input_set_checksum"]
    assert handoff["downstream_restriction_binding"]["manifest_checksum"] == manifest_ref["checksum"]


def test_b5_i3_preflight_requires_every_canonical_input_kind():
    incomplete = [InputArtifact(kind, f"fixture-{kind}", Path("missing.json"), "M7-TEST") for kind in sorted(M3_REQUIRED_INPUT_KINDS - {"youtube_adaptation_review"})]
    with pytest.raises(ResearchM7Error, match="B5_I3_REQUIRED_INPUTS_MISSING:youtube_adaptation_review"):
        ResearchV2B5I3Adapter.validate_full_preflight("EP-M7-TEST", incomplete)


def test_m7_rejects_invalid_intermediate_before_m5_persistence(monkeypatch, tmp_path):
    from src.application import research_m7_fixture

    original = research_m7_fixture.SyntheticResearchExecutor.__call__

    def invalid(self, request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            return {"invalid_payload": True}
        return original(self, request)

    monkeypatch.setattr(research_m7_fixture.SyntheticResearchExecutor, "__call__", invalid)
    with pytest.raises(ValueError):
        ResearchM7SyntheticRunner(tmp_path).run(_input())
    state = ResearchM7SyntheticRunner(tmp_path).store.load()
    assert state["completed_stages"] == ["INTAKE", "RESEARCH_PLAN", "B2", "M4"]
    assert not any(item["stage"] in {"M5", "M6", "B5_I3_HANDOFF"} for item in state["artifacts"])


def test_m7_preserves_explicit_human_works_and_has_no_silent_three_default(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path).run(_input(works=["REAL-A", "REAL-B", "REAL-C", "REAL-D"], target_final_works=3, selected_work_ids=["REAL-A", "REAL-B", "REAL-C"]))
    assert {item["work_id"] for item in _read_stage(state, "B2")["lifecycle_projection"]["works"]} == {"REAL-A", "REAL-B", "REAL-C", "REAL-D"}
    assert _read_stage(state, "M4")["selection"]["selected_work_ids"] == ["REAL-A", "REAL-B", "REAL-C"]
    with pytest.raises(ResearchM7Error, match="TARGET_FINAL_WORKS"):
        ResearchM7SyntheticRunner(tmp_path / "missing-target").run(_input(target_final_works=None))


def test_manual_selection_is_preserved_end_to_end(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path).run(_input(works=["A", "B", "C", "D"], selected_work_ids=["A", "C", "D"], target_final_works=3, replace_work_id="A", substitute_work_id="B"))
    assert _read_stage(state, "M4")["selection"]["selected_work_ids"] == ["A", "C", "D"]
    comparison = _m5_output(state, "ResearchComparison")
    assert comparison["selected_work_ids"] == ["A", "C", "D"]


def test_delegated_substitution_reaches_m5_m6_and_handoff(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path, selection_mode="DELEGATED", delegated_scope=["W1", "W2", "W3", "W4"]).run(_input(episode_id="EP-M7-DELEGATED", works=["W1", "W2", "W3", "W4"], selected_work_ids=["W1", "W2", "W3"], replace_work_id="W1", substitute_work_id="W4"))
    selected = _read_stage(state, "M4")["selection"]["selected_work_ids"]
    assert selected == ["W2", "W3", "W4"]
    deep = _read_stage(state, "M4")
    deep_refs = [ref for ref in deep["artifacts"] if ref["artifact_kind"] == "WorkResearchDossierCollection"]
    deep_payloads = [json.loads(Path(ref["path"]).read_text(encoding="utf-8")) for ref in deep_refs]
    assert all({item["work"]["material_id"] for item in payload["dossiers"]} == set(selected) for payload in deep_payloads)
    assert _m5_output(state, "ResearchComparison")["selected_work_ids"] == selected
    assert "W4" in json.dumps(_read_stage(state, "B5_I3_HANDOFF"))
    assert "W1" not in _m5_output(state, "ResearchComparison")["selected_work_ids"]


def test_recovery_materialization_and_work_external_separation(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path).run(_input())
    recovery = {item["artifact_id"]: item for item in state["recovery_artifacts"]}
    assert Path(recovery["recovery:S1"]["path"]).is_file()
    recovery_path = Path(recovery["recovery:S1"]["path"])
    assert hashlib.sha256(recovery_path.read_bytes()).hexdigest() == recovery["recovery:S1"]["checksum"]
    assert json.loads(recovery_path.read_text(encoding="utf-8"))["synthetic"] is True
    b2 = _read_stage(state, "B2")
    source_ref = next(item for item in b2["artifacts"] if item["artifact_kind"] == "ResearchPack")
    pack = json.loads(Path(source_ref["path"]).read_text(encoding="utf-8"))
    source = {item["source_id"]: item for item in pack["source_registry"]}
    assert source["S1"]["retrieval_status"] == "RECOVERED"
    assert source["SUGGESTED_ONLY"]["retrieval_status"] == "NOT_RECOVERED"
    assert "SUGGESTED_ONLY" not in pack["evidence_type_separation"]["external_reality_evidence_refs"]
    assert set(pack["evidence_type_separation"]["work_evidence_refs"]).isdisjoint(pack["evidence_type_separation"]["external_reality_evidence_refs"])


def test_resume_reuses_canonical_artifacts_after_m5(tmp_path):
    interrupted = ResearchM7SyntheticRunner(tmp_path).run(_input(), stop_after_stage="M5")
    before = {item["stage"]: item["artifact_id"] for item in interrupted["artifacts"]}
    resumed = ResearchM7SyntheticRunner(tmp_path).resume()
    after = {item["stage"]: item["artifact_id"] for item in resumed["artifacts"]}
    assert resumed["status"] == "COMPLETED"
    assert all(after[stage] == before[stage] for stage in before)
    assert ResearchM7SyntheticRunner(tmp_path).resume()["status"] == "COMPLETED"


def test_upstream_invalidation_stales_and_regenerates_handoff(tmp_path):
    runner = ResearchM7SyntheticRunner(tmp_path)
    initial = runner.run(_input())
    old = next(item for item in initial["artifacts"] if item["stage"] == "B5_I3_HANDOFF")
    invalidated = ResearchM7SyntheticRunner(tmp_path).invalidate("B2")
    assert invalidated["stale_handoff"] is True
    regenerated = ResearchM7SyntheticRunner(tmp_path).resume()
    new = next(item for item in regenerated["artifacts"] if item["stage"] == "B5_I3_HANDOFF")
    assert new["checksum"] != old["checksum"]
    assert new["path"] != old["path"]
    assert regenerated["status"] == "COMPLETED"
    ResearchM7SyntheticRunner(tmp_path).assert_handoff_consumable(regenerated)


@pytest.mark.parametrize(
    ("stage", "unchanged_stages"),
    [("M5", ("B2", "M4")), ("M6", ("B2", "M4", "M5"))],
)
def test_focal_invalidation_resumes_from_first_invalidated_stage_and_rejects_old_handoff(tmp_path, stage, unchanged_stages):
    runner = ResearchM7SyntheticRunner(tmp_path)
    initial = runner.run(_input())
    before = {item["stage"]: dict(item) for item in initial["artifacts"]}
    old_handoff_path = Path(before["B5_I3_HANDOFF"]["path"])
    invalidated = ResearchM7SyntheticRunner(tmp_path).invalidate(stage)
    assert invalidated["stale_handoff"] is True
    assert stage in invalidated["invalidated_stages"]
    stale_payload = json.loads(old_handoff_path.read_text(encoding="utf-8"))
    assert stale_payload["handoff_state"] == "STALE"
    assert stale_payload["validation"]["status"] == "STALE"
    with pytest.raises(ResearchM7Error, match="STALE_OR_INVALIDATED"):
        ResearchM7SyntheticRunner(tmp_path).assert_handoff_consumable(invalidated)

    resumed = ResearchM7SyntheticRunner(tmp_path).resume()
    after = {item["stage"]: dict(item) for item in resumed["artifacts"]}
    assert resumed["status"] == "COMPLETED"
    assert resumed["invalidated_stages"] == []
    assert resumed["stale_handoff"] is False
    assert resumed["generation"] == 2
    for unchanged in unchanged_stages:
        assert after[unchanged]["artifact_id"] == before[unchanged]["artifact_id"]
        assert after[unchanged]["path"] == before[unchanged]["path"]
        assert after[unchanged]["checksum"] == before[unchanged]["checksum"]
    assert after[stage]["path"] != before[stage]["path"]
    assert after["B5_I3_HANDOFF"]["path"] != before["B5_I3_HANDOFF"]["path"]
    ResearchM7SyntheticRunner(tmp_path).assert_handoff_consumable(resumed)


def test_research_stop_more_required_reopens_focally_and_resolves(tmp_path):
    runner = ResearchM7SyntheticRunner(tmp_path)
    interrupted = runner.run(_input(deep_stop_status="MORE_RESEARCH_REQUIRED"))
    assert interrupted["research_stop_route"] == "REOPEN_FOCAL"
    m4_ref = next(item for item in interrupted["artifacts"] if item["stage"] == "M4")
    reopened = ResearchM7SyntheticRunner(tmp_path).reopen_focal(m4_ref["artifact_id"])
    assert reopened["research_stop_route"] == "REOPENED_AND_RESOLVED"
    final = ResearchM7SyntheticRunner(tmp_path).resume()
    assert final["status"] == "COMPLETED"


def test_no_progress_guard_stops_without_research_ready(tmp_path):
    with pytest.raises(ResearchM7Error, match="NO_PROGRESS / ITERATION_GUARD"):
        ResearchM7SyntheticRunner(tmp_path).run(_input(), simulate_no_progress=True)
    state = ResearchM7SyntheticRunner(tmp_path).store.load()
    assert state["status"] == "BLOCKED_NO_PROGRESS"
    assert state["no_progress_terminal"] == "NO_PROGRESS / ITERATION_GUARD"
    assert not any(item["stage"] in {"M6", "B5_I3_HANDOFF"} for item in state["artifacts"])


def test_cli_requires_explicit_works_and_reports_non_productive_pass(tmp_path, capsys):
    exit_code = main(["investigar-sintetico", "--state-dir", str(tmp_path), "--tema", "Tema CLI", "--pregunta", "¿Qué?", "--obras", "A", "B", "C", "--target-final-works", "3"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PLAN_012_RESEARCH_VERTICAL_E2E: PASS" in output
    assert "PLAN_012_REAL_AI_EXECUTION: NO" in output
    assert "PLAN_012_PRODUCT_USE_AUTHORIZED: NO" in output
    assert "PLAN_012_P2_REAL_EXECUTION: NO" in output
