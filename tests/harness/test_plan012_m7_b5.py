"""Focal acceptance tests for the canonical PLAN012 M7 coordinator."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.ai.contracts import InputArtifact
from src.ai.execution import M3_REQUIRED_INPUT_KINDS
from src.application.research_b2 import SoftwareAcquisitionAdapter
from src.application.research_m7 import ResearchM7Error, ResearchM7SyntheticRunner, ResearchV2B5I3Adapter
from src.application.research_m7_fixture import phenomenon
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
    producer_ids = {
        item["artifact_kind"]: item["producer_run_id"]
        for item in handoff["b5_i3_input_bindings"]
    }
    assert producer_ids == {
        "human_input": "M7-TRANSVERSAL-FIXTURE",
        "active_editorial_profile_reference": "M7-PROFILE",
        "episode_brief": "M7-TRANSVERSAL-FIXTURE",
        "research_pack": "M7-M4",
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


def test_resume_reconciles_persisted_m6_manifest_before_handoff(tmp_path):
    runner = ResearchM7SyntheticRunner(tmp_path)
    completed = runner.run(_input())
    checkpoint = runner.store.load()
    checkpoint["artifacts"] = [item for item in checkpoint["artifacts"] if item["stage"] != "B5_I3_HANDOFF"]
    checkpoint["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"]
    checkpoint.update({"status": "INTERRUPTED", "next_stage": "M6"})
    runner.store.save(checkpoint)
    resumed = runner.resume()
    assert resumed["status"] == "COMPLETED"
    assert next(item for item in resumed["artifacts"] if item["stage"] == "M6")["path"] == next(item for item in completed["artifacts"] if item["stage"] == "M6")["path"]


@pytest.mark.parametrize("stop_stage", ["B2", "M4"])
def test_resume_cli_path_reuses_completed_b2_or_m4_artifact(tmp_path, stop_stage):
    runner = ResearchM7SyntheticRunner(tmp_path)
    interrupted = runner.run(_input(), stop_after_stage=stop_stage)
    preserved = {item["stage"]: dict(item) for item in interrupted["artifacts"]}
    resumed = runner.run(resume=True)
    assert resumed["status"] == "COMPLETED"
    stages = ("B2", "M4") if stop_stage == "M4" else ("B2",)
    for stage in stages:
        current = next(item for item in resumed["artifacts"] if item["stage"] == stage)
        assert current["path"] == preserved[stage]["path"]
        assert current["checksum"] == preserved[stage]["checksum"]


def test_research_v2_projection_resolves_all_selected_work_without_narrative_decisions(tmp_path):
    state = ResearchM7SyntheticRunner(tmp_path).run(_input())
    handoff = _read_stage(state, "B5_I3_HANDOFF")
    projection = handoff["research_v2_projection"]
    semantic = handoff["research_v2_semantic_context"]
    assert semantic == projection
    assert handoff["legacy_b5_i3_preflight"] == {
        "classification": "LEGACY_TRANSVERSAL_FIXTURE",
        "status": "COMPATIBILITY_ONLY",
        "non_authoritative": True,
        "input_kinds": ["narrative_human_analysis", "material_curation"],
        "not_included_in_research_v2_semantic_context": True,
    }
    assert projection["authority"] == "RESEARCH_V2"
    assert set(projection["selected_work_ids"]) == {"REAL-A", "REAL-B", "REAL-C"}
    assert projection["selected_work_ids"] == projection["resolved_work_ids"]
    assert projection["refined_thesis_material_work_ids"] == sorted(projection["selected_work_ids"])
    for label in ("deep_phenomenon_research", "deep_work_research", "deep_fidelity", "claims_ledger", "claim_sufficiency", "post_deep_comparison", "refined_thesis"):
        ref = projection["research_refs"][label]
        assert Path(ref["path"]).is_file()
    serialized = json.dumps(projection).lower()
    assert all(token not in serialized for token in ("function", "expected_order", "sequence_rationale", "viewer_journey"))
    assert all(token not in json.dumps(semantic).lower() for token in ("function", "narrative_use", "expected_order", "sequence_rationale", "progression_map", "viewer_journey"))


def test_r1_authority_catalog_and_legacy_curation_are_explicit():
    catalog = json.loads(Path("config/skill_catalog.json").read_text(encoding="utf-8"))
    thesis_skill = next(item for item in catalog["skills"] if item["skill_id"] == "skill_sintesis_tesis")
    assert thesis_skill["canonical_owner"] == "RESEARCH_AND_CURATION"
    assert thesis_skill["target_or_merge_destination"] == "RESEARCH_AND_CURATION"
    assert "legacy_compatibility" not in thesis_skill
    assert "non-authoritative" in thesis_skill["rationale"]
    curation = Path(".agent/skills/skill_curation_obras.md").read_text(encoding="utf-8")
    assert "Modo RESEARCH_V2" in curation
    assert "Modo LEGACY_B5_I2" in curation


def test_resume_reconciles_lagging_b2_checkpoint_without_rerunning_b2(tmp_path):
    runner = ResearchM7SyntheticRunner(tmp_path)
    interrupted = runner.run(_input(), stop_after_stage="B2")
    b2_before = next(item for item in interrupted["artifacts"] if item["stage"] == "B2")
    checkpoint = runner.store.load()
    checkpoint["artifacts"] = [item for item in checkpoint["artifacts"] if item["stage"] not in {"RESEARCH_PLAN", "B2"}]
    checkpoint["completed_stages"] = ["INTAKE"]
    checkpoint.update({"status": "INTERRUPTED", "next_stage": "M4"})
    runner.store.save(checkpoint)
    resumed = runner.resume()
    b2_after = next(item for item in resumed["artifacts"] if item["stage"] == "B2")
    assert b2_after["path"] == b2_before["path"]
    assert b2_after["checksum"] == b2_before["checksum"]
    assert resumed["status"] == "COMPLETED"


def test_resume_reconciles_lagging_m4_checkpoint_without_rerunning_m4(tmp_path):
    runner = ResearchM7SyntheticRunner(tmp_path)
    interrupted = runner.run(_input(), stop_after_stage="M4")
    m4_before = next(item for item in interrupted["artifacts"] if item["stage"] == "M4")
    checkpoint = runner.store.load()
    checkpoint["artifacts"] = [item for item in checkpoint["artifacts"] if item["stage"] != "M4"]
    checkpoint["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2"]
    checkpoint.update({"status": "INTERRUPTED", "next_stage": "M4"})
    runner.store.save(checkpoint)
    resumed = runner.resume()
    m4_after = next(item for item in resumed["artifacts"] if item["stage"] == "M4")
    assert m4_after["path"] == m4_before["path"]
    assert m4_after["checksum"] == m4_before["checksum"]
    assert resumed["status"] == "COMPLETED"


@pytest.mark.parametrize("missing", ["manifest", "gate"])
def test_resume_reuses_m6_audit_and_materializes_only_missing_downstream_artifact(tmp_path, missing):
    runner = ResearchM7SyntheticRunner(tmp_path)
    completed = runner.run(_input())
    checkpoint = runner.store.load()
    m6_ref = next(item for item in checkpoint["artifacts"] if item["stage"] == "M6")
    audit_path = tmp_path / "canonical_g1" / "b3" / "independent_research_audit_m6.json"
    manifest_path = Path(m6_ref["path"])
    gate_path = tmp_path / "canonical_g1" / "b3" / "research_ready_gate.json"
    assert audit_path.is_file()
    if missing == "manifest":
        manifest_path.unlink()
    else:
        gate_path.unlink()
    checkpoint["artifacts"] = [item for item in checkpoint["artifacts"] if item["stage"] not in {"M6", "B5_I3_HANDOFF"}]
    checkpoint["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"]
    checkpoint.update({"status": "INTERRUPTED", "next_stage": "M6"})
    runner.store.save(checkpoint)
    resumed = runner.resume()
    assert resumed["status"] == "COMPLETED"
    assert audit_path.is_file()
    assert manifest_path.is_file()
    assert gate_path.is_file()
    assert next(item for item in resumed["artifacts"] if item["stage"] == "B5_I3_HANDOFF")["path"]


def _execution_registry_for_recovery(tmp_path, ref, execution_ref, *, status="SUCCEEDED"):
    registry_path = Path(__file__).resolve().parents[2] / "output" / "execution_provenance_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    run = copy.deepcopy(registry["runs"][0])
    run.update({
        "run_id": execution_ref,
        "status": status,
        "outputs": [{
            "artifact_kind": "research",
            "artifact_id": ref["artifact_id"],
            "artifact_ref": f"research:{ref['artifact_id']}",
            "checksum": ref["checksum"],
        }],
        "output_artifact_ids": [f"research:{ref['artifact_id']}"],
        "output_versions": ["fixture-1"],
        "output_checksums": [ref["checksum"]],
    })
    registry["runs"] = [run]
    path = tmp_path / "execution_provenance_registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    return path


def test_strict_acquisition_requires_physical_recovery_identity_and_checksum(tmp_path):
    pack = phenomenon("EP-ACQ", "RP-ACQ", "Tema")
    recovery = tmp_path / "S1.json"
    recovery.write_text(json.dumps({"source_id": "S1", "content": "fixture"}), encoding="utf-8")
    ref = {"artifact_id": "recovery:S1", "path": str(recovery), "checksum": hashlib.sha256(recovery.read_bytes()).hexdigest()}
    binding = {"request_ref": "request:S1", "execution_ref": "RUN-RECOVERY-S1", "recovery_artifact_ref": "recovery:S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}
    registry_path = _execution_registry_for_recovery(tmp_path, ref, binding["execution_ref"])
    adapter = SoftwareAcquisitionAdapter({"S1": binding}, recovery_artifacts={"recovery:S1": ref}, execution_registry_path=registry_path)
    assert adapter.materialize(pack)["acquisition_bindings"][0]["recovery_artifact_ref"] == "recovery:S1"
    with pytest.raises(ValueError, match="UNRESOLVED"):
        unresolved = dict(binding, execution_ref="RUN-FABRICATED")
        SoftwareAcquisitionAdapter({"S1": unresolved}, recovery_artifacts={"recovery:S1": ref}, execution_registry_path=registry_path).materialize(pack)
    failed_registry = _execution_registry_for_recovery(tmp_path, ref, binding["execution_ref"], status="FAILED")
    with pytest.raises(ValueError, match="NOT_SUCCEEDED"):
        SoftwareAcquisitionAdapter({"S1": binding}, recovery_artifacts={"recovery:S1": ref}, execution_registry_path=failed_registry).materialize(pack)
    with pytest.raises(ValueError, match="UNRESOLVED"):
        SoftwareAcquisitionAdapter({"S1": binding}, recovery_artifacts={}, execution_registry_path=registry_path).materialize(pack)
    bad = dict(ref, checksum="0" * 64)
    with pytest.raises(ValueError, match="CHECKSUM_MISMATCH"):
        SoftwareAcquisitionAdapter({"S1": binding}, recovery_artifacts={"recovery:S1": bad}, execution_registry_path=registry_path).materialize(pack)
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"source_id": "OTHER", "content": "fixture"}), encoding="utf-8")
    wrong_ref = {"artifact_id": "recovery:S1", "path": str(wrong), "checksum": hashlib.sha256(wrong.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="SOURCE_MISMATCH"):
        wrong_registry = _execution_registry_for_recovery(tmp_path, wrong_ref, binding["execution_ref"])
        SoftwareAcquisitionAdapter({"S1": binding}, recovery_artifacts={"recovery:S1": wrong_ref}, execution_registry_path=wrong_registry).materialize(pack)


def test_default_acquisition_is_fail_closed_for_positive_unresolved_binding():
    pack = phenomenon("EP-ACQ-DEFAULT", "RP-ACQ-DEFAULT", "Tema")
    binding = {
        "request_ref": "request:S1",
        "execution_ref": "execution:S1",
        "recovery_artifact_ref": "recovery:S1",
        "retrieval_status": "RECOVERED",
        "evidence_status": "CONSULTED",
        "software_controlled": True,
    }
    with pytest.raises(ValueError, match="UNRESOLVED"):
        SoftwareAcquisitionAdapter({"S1": binding}).materialize(pack)


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
    assert reopened["research_stop_route"] == "REOPENED_PENDING_NEW_COGNITION"
    assert reopened["human_input"]["deep_stop_status"] == "MORE_RESEARCH_REQUIRED"
    evidence_ref = reopened["human_input"]["_research_stop_new_evidence_ref"]
    assert Path(evidence_ref["path"]).is_file()
    assert evidence_ref in reopened["recovery_artifacts"]
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
