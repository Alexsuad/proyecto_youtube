"""Focal acceptance tests for the canonical PLAN012 M7 coordinator."""

import copy
import hashlib
import json
import shutil
import tempfile
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.ai.contracts import ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import M3_REQUIRED_INPUT_KINDS, execute
from src.ai.registry import register_software_outputs
from src.application.research_b2 import ResearchB2Orchestrator, SoftwareAcquisitionAdapter
from src.application.research_b3 import ResearchB3Orchestrator
from src.application.research_b4 import M6_REQUIRED_AUDIT_CRITERIA, ResearchB4Orchestrator
from src.application.contracts import HumanInput
from src.application.interaction import HumanDecision, HumanDecisionRequest
from src.application.research_m7 import (
    REAL_EXTERNAL_HANDOFF_AUTHORIZATION,
    REAL_EXTERNAL_HANDOFF_CONTRACT,
    ExternalResearchCognitiveExecutor,
    import_and_resume_external_research,
    respond_to_research_human_decision,
    PersistedResearchEpisode,
    ProductiveResearchStageAdapters,
    RealResearchRoutePreparation,
    ResearchM7Error,
    ResearchM7SyntheticRunner,
    ResearchV2B5I3Adapter,
)
from src.application.research_planning import ResearchPlanningService
from src.application.storage import VaultEpisodeStore
from src.application.research_m7_fixture import (
    SyntheticResearchExecutor,
    audit,
    discovery,
    phenomenon,
    research_plan_proposal,
    sufficiency,
)
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.mission_authorization import (
    MissionAuthorizationError,
    load_mission_authorization,
    scope_checksum,
    sha256_file,
)
from src.cli import build_parser, main


ROOT = Path(__file__).resolve().parents[2]


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
    proposal_ref = state["canonical_refs"]["ResearchPlanProposal"][0]
    assert proposal_ref["artifact_kind"] == "ResearchPlanProposal"
    assert Path(proposal_ref["path"]).is_file()
    b2_manifest = _read_stage(state, "B2")
    assert b2_manifest["evidence_report"]["artifact_kind"] == "SourceAccessAndEvidenceReport"
    m4_manifest = _read_stage(state, "M4")
    m5_manifest = _read_stage(state, "M5")
    assert any(item["artifact_kind"] == "SourceAccessAndEvidenceReport" for item in m4_manifest["artifacts"])
    assert any(item["artifact_kind"] == "SourceAccessAndEvidenceReport" for item in m5_manifest["m5_outputs"])
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


def _real_route_config(**overrides):
    config = {
        "episode_id": "EP-REAL-M1",
        "topic": "Tema real preparado",
        "question": "¿Qué puede afirmarse?",
        "budget_limit": 25,
        "max_iterations": 2,
        "max_retries": 1,
        "timeout_seconds": 30,
    }
    config.update(overrides)
    return config


def _persisted_real_episode(tmp_path):
    store = VaultEpisodeStore(tmp_path / "vault", "MAS_ALLA_DEL_GUION")
    profile = load_active_profile_authority()
    human = HumanInput.create(
        mode="tema",
        content="Tema persistido de Research V2",
        initial_question="¿Qué puede sostenerse?",
        works=["Obra A", "Obra B", "Obra C"],
        research_role="ANCLA",
        editorial_intent="PREFERIDA",
        user_instructions=[{
            "category": "MUST_INCLUDE",
            "text": "Conservar la restricción del OWNER.",
        }],
        work_intents=[
            {"work_ref": "Obra A", "editorial_intent": "PREFERIDA"},
            {"work_ref": "Obra B", "editorial_intent": "REQUERIDA"},
            {"work_ref": "Obra C", "editorial_intent": "NO_DECLARADA"},
        ],
        selection_authority="OWNER_DECIDES",
    )
    handle = store.create_episode(
        human,
        handoff={}, profile=profile, run_id="RUN-REAL-ROUTE",
    )
    planning = ResearchPlanningService()
    brief = planning.build_episode_brief(
        episode_id=handle.episode_id,
        topic=human.content,
        question=human.initial_question,
        intended_use="OWNER_DECLARED_RESEARCH",
        profile=profile,
        work_intents=[dict(item) for item in human.work_intents],
        selection_authority=human.selection_authority,
        material_refs=[],
        owner_restrictions=["MUST_INCLUDE: Conservar la restricción del OWNER."],
        brief_version="2.0.0",
        origin_ref=f"human-input:{handle.episode_id}",
    )
    channel_context = planning.build_channel_context(
        episode_id=handle.episode_id, profile=profile, origin_ref=f"human-input:{handle.episode_id}",
    )
    source_access = planning.build_source_access(
        episode_id=handle.episode_id,
        brief_version=brief["brief_version"],
        materials=[],
        origin_refs=[f"human-input:{handle.episode_id}"],
    )
    store.record_research_preparation(
        handle, brief=brief, channel_context=channel_context, source_access=source_access,
    )
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"vault_root": str(tmp_path / "vault"), "channel_id": "MAS_ALLA_DEL_GUION"}), encoding="utf-8")
    return handle, settings


def _real_cli_args(handle, settings, *, handoff_directory=None):
    handoff_directory = handoff_directory or (
        Path("plans/extend_01/m2/b4_handoff/packages") / f".pytest-{Path(settings).stem}"
    )
    return [
        "--episodio-id", handle.episode_id,
        "--config", str(settings),
        "--budget", "25",
        "--max-iterations", "2",
        "--max-retries", "1",
        "--timeout", "30",
        "--handoff-directory", str(handoff_directory),
    ]


def _isolated_external_handoff_bundle(tmp_path):
    """Build a historical EXTEND bundle without mutating live repository state."""
    bundle_root = ROOT / ".runtime-tmp" / f"plan012-m7-{hashlib.sha256(str(tmp_path).encode()).hexdigest()[:12]}"
    bundle_root.mkdir(parents=True, exist_ok=False)
    live_state = bundle_root / "live-control.md"
    authority_path = bundle_root / "authority.json"
    authorization_path = bundle_root / "mission-authorization.json"
    contract_path = bundle_root / "mission_contract.json"
    handoff_directory = bundle_root / "packages"
    provenance_root = bundle_root / "provenance"
    provenance_registry = provenance_root / "output" / "execution_provenance_registry.json"

    live_control = (ROOT / "plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8")
    current_line = next(line for line in live_control.splitlines() if line.startswith("CURRENT_MISSION:"))
    live_state.write_text(
        live_control.replace(current_line, "CURRENT_MISSION: EXTEND_01_M2_REAL_E2E"),
        encoding="utf-8",
    )
    live_ref = live_state.relative_to(ROOT).as_posix()
    authority_ref = authority_path.relative_to(ROOT).as_posix()
    authorization_ref = authorization_path.relative_to(ROOT).as_posix()
    contract_ref = contract_path.relative_to(ROOT).as_posix()
    handoff_ref = handoff_directory.relative_to(ROOT).as_posix() + "/"

    authorization = json.loads(
        (ROOT / REAL_EXTERNAL_HANDOFF_AUTHORIZATION).read_text(encoding="utf-8")
    )
    authorization_data = authorization["authorization"]
    authorization_data.update({
        "live_state_path": live_ref,
        "live_state_sha256": sha256_file(live_state),
        "authority_ref": authority_ref,
        "allowed_paths": [handoff_ref],
    })
    scope = {
        "mission_id": authorization["mission_id"],
        "capability_ids": authorization_data["capability_ids"],
        "role_ids": authorization_data["role_ids"],
        "execution_profile_ids": authorization_data.get("execution_profile_ids", []),
        "execution_interface": authorization_data["execution_interface"],
        "allowed_operations": authorization_data["allowed_operations"],
        "allowed_paths": authorization_data["allowed_paths"],
        "allowed_routes": authorization_data["allowed_routes"],
        "execution_mode": authorization_data["execution_mode"],
        "live_state_sha256": authorization_data["live_state_sha256"],
        "contains_material_repair": authorization_data["contains_material_repair"],
        "repair_integrity_evidence_path": authorization_data["repair_integrity_evidence_path"],
    }
    if authorization_data.get("execution_family_ids"):
        scope["execution_family_ids"] = authorization_data["execution_family_ids"]
    authorization_data["authorized_scope_sha256"] = scope_checksum(scope)
    authority = {
        "mission_id": authorization["mission_id"],
        "decision": "APPROVE",
        "artifact_version": "1.0.0",
        "authorized_scope_sha256": authorization_data["authorized_scope_sha256"],
    }
    authority_path.write_text(json.dumps(authority), encoding="utf-8")
    authorization_data["authority_sha256"] = sha256_file(authority_path)
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")

    contract = json.loads((ROOT / REAL_EXTERNAL_HANDOFF_CONTRACT).read_text(encoding="utf-8"))
    contract.update({
        "authorized_paths": [handoff_ref],
        "mission_authorization_path": authorization_ref,
        "state_requirements": {
            **contract["state_requirements"],
            "control_path": live_ref,
            "required": {
                **contract["state_requirements"]["required"],
                "CURRENT_MISSION": "EXTEND_01_M2_REAL_E2E",
            },
        },
    })
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    provenance_registry.parent.mkdir(parents=True, exist_ok=True)
    provenance_registry.write_text(
        json.dumps({"registry_version": "1.0.0", "runs": [], "handoffs": [], "attempts": []}),
        encoding="utf-8",
    )
    return SimpleNamespace(
        root=bundle_root,
        live_state=live_state,
        authority=authority_path,
        authorization=authorization_path,
        authorization_ref=authorization_ref,
        contract=contract_path,
        contract_ref=contract_ref,
        handoff_directory=handoff_directory,
        provenance_root=provenance_root,
    )


def _isolated_source_acquisition_adapter(bundle, episode_id):
    recovery = bundle.root / "recovery-S1.json"
    recovery.write_text(
        json.dumps({"source_id": "S1", "content": "Fixture controlado.", "locator": "fixture://S1"}),
        encoding="utf-8",
    )
    recovery_ref = {
        "artifact_id": "recovery:S1",
        "path": str(recovery),
        "checksum": sha256_file(recovery),
    }
    registry_path = bundle.provenance_root / "output" / "execution_provenance_registry.json"
    register_software_outputs(
        registry_path,
        run_id=f"PLAN012-TEST-ACQUISITION-{episode_id}",
        episode_id=episode_id,
        role="RESEARCH_ACQUISITION",
        outputs=[{
            "artifact_id": recovery_ref["artifact_id"],
            "artifact_kind": "research",
            "artifact_version": "1.0.0",
            "checksum": recovery_ref["checksum"],
        }],
    )
    return SoftwareAcquisitionAdapter(
        {"S1": {
            "request_ref": "request:S1",
            "execution_ref": f"PLAN012-TEST-ACQUISITION-{episode_id}",
            "recovery_artifact_ref": "recovery:S1",
            "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED",
            "software_controlled": True,
        }},
        recovery_artifacts={"recovery:S1": recovery_ref},
        execution_registry_path=registry_path,
    )


@pytest.fixture
def persisted_real_episode():
    with TemporaryDirectory(prefix="m2b3-") as root:
        result = _persisted_real_episode(Path(root))
        try:
            yield result
        finally:
            handoff_directory = Path("plans/extend_01/m2/b4_handoff/packages") / f".pytest-{result[1].stem}"
            if handoff_directory.is_dir():
                shutil.rmtree(handoff_directory)


@pytest.fixture
def isolated_real_episode(persisted_real_episode, tmp_path):
    handle, settings = persisted_real_episode
    bundle = _isolated_external_handoff_bundle(tmp_path)
    try:
        yield SimpleNamespace(handle=handle, settings=settings, **vars(bundle))
    finally:
        if bundle.root.is_dir():
            shutil.rmtree(bundle.root, ignore_errors=True)


def test_extend01_isolated_authority_is_valid_but_live_and_tampered_state_fail(tmp_path):
    bundle = _isolated_external_handoff_bundle(tmp_path)
    try:
        isolated = load_mission_authorization(bundle.authorization)
        isolated.verify(
            ROOT,
            capability_id="EXTEND_01_RESEARCH_V2_REAL_E2E",
            role_id="RESEARCH_AND_CURATION",
            operation="EXECUTE_CAPABILITY",
            execution_mode="REAL",
            execution_route="agent_harness",
            execution_family="AGENT_HARNESS",
            execution_interface="EXTEND_01_M2_B4_HANDOFF",
            path=bundle.handoff_directory.relative_to(ROOT).as_posix() + "/",
        )

        live = load_mission_authorization(ROOT / REAL_EXTERNAL_HANDOFF_AUTHORIZATION)
        with pytest.raises(MissionAuthorizationError, match="MISSION_STALE_AGAINST_LIVE_STATE"):
            live.verify(
                ROOT,
                capability_id="EXTEND_01_RESEARCH_V2_REAL_E2E",
                role_id="RESEARCH_AND_CURATION",
                operation="EXECUTE_CAPABILITY",
                execution_mode="REAL",
                execution_route="agent_harness",
                execution_family="AGENT_HARNESS",
                execution_interface="EXTEND_01_M2_B4_HANDOFF",
            )

        bundle.live_state.write_text(
            bundle.live_state.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        with pytest.raises(MissionAuthorizationError, match="MISSION_STALE_AGAINST_LIVE_STATE"):
            isolated.verify(
                ROOT,
                capability_id="EXTEND_01_RESEARCH_V2_REAL_E2E",
                role_id="RESEARCH_AND_CURATION",
                operation="EXECUTE_CAPABILITY",
                execution_mode="REAL",
                execution_route="agent_harness",
                execution_family="AGENT_HARNESS",
                execution_interface="EXTEND_01_M2_B4_HANDOFF",
            )
    finally:
        if bundle.root.is_dir():
            shutil.rmtree(bundle.root, ignore_errors=True)


def test_extend01_real_without_authorization_blocks_before_provider():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    result = execute(preparation.build_request())
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert any(token in str(result.error) for token in ("MISSION_AUTHORIZATION_REQUIRED", "CAPABILITY_UNAVAILABLE"))


def test_extend01_mvp_preparation_loads_only_the_persisted_episode(persisted_real_episode, capsys):
    handle, settings = persisted_real_episode
    exit_code = main([
        "preparar-ruta-real",
        *_real_cli_args(handle, settings),
        "--mission-authorization", "mission-auth.json",
    ])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "REAL_ROUTE_PREPARED: YES" in output
    assert "REAL_AI_EXECUTION: NO" in output
    preparation = RealResearchRoutePreparation.from_mapping({
        "episode_id": handle.episode_id,
        "topic": "Tema persistido de Research V2",
        "question": "¿Qué puede sostenerse?",
        "budget_limit": 25,
        "max_iterations": 2,
        "max_retries": 1,
        "timeout_seconds": 30,
    })
    prepared = preparation.to_dict()
    request = preparation.build_request()
    for field in ("provider", "model", "runtime", "execution_profile", "execution_route", "execution_family", "harness", "development_platform", "acquisition_status"):
        assert field not in prepared
        assert field not in request.config
    assert request.provider is None
    assert request.model is None
    assert request.execution_profile is None
    assert request.execution_route is None
    assert request.execution_family is None
    with pytest.raises(SystemExit):
        build_parser().parse_args([
            "preparar-ruta-real",
            *_real_cli_args(handle, settings),
            "--provider", "provider-a",
        ])
    with pytest.raises(SystemExit):
        build_parser().parse_args([
            "preparar-ruta-real",
            *_real_cli_args(handle, settings),
            "--tema", "Autoridad duplicada",
        ])


def test_extend01_real_entrypoint_is_episode_bound_and_blocks_without_b4_authorization(persisted_real_episode, capsys):
    handle, settings = persisted_real_episode
    parser = build_parser()
    parsed = parser.parse_args([
        "investigar-real",
        *_real_cli_args(handle, settings),
    ])
    assert parsed.command == "investigar-real"
    assert parsed.handler.__name__ == "_investigate_research_m7_real"
    assert main([
        "investigar-real",
        *_real_cli_args(handle, settings),
    ]) == 2
    output = capsys.readouterr().out
    assert "MISSION_AUTHORIZATION_REQUIRED" in output
    assert "REAL_AI_ROUTE_SELECTION_REQUIRED_FOR_B4" not in output


def test_extend01_b4_prepares_external_handoff_and_stops_before_b2(isolated_real_episode, capsys):
    handle, settings = isolated_real_episode.handle, isolated_real_episode.settings
    package_path = None
    try:
        assert main([
            "investigar-real",
            *_real_cli_args(handle, settings, handoff_directory=isolated_real_episode.handoff_directory),
            "--mission-authorization", isolated_real_episode.authorization_ref,
            "--mission-contract", isolated_real_episode.contract_ref,
        ]) == 0
        output = capsys.readouterr().out
        assert "EXTERNAL_HANDOFF: PREPARED" in output
        assert "PENDING_EXTERNAL_COGNITIVE_RESULT: YES" in output
        assert "REAL_AI_EXECUTION: NO" in output
        assert "REAL_AI_CALLS: 0" in output
        assert "REAL_ROUTE_RESULT: RESEARCH_READY" not in output
        package_path = Path(next(line.split(": ", 1)[1] for line in output.splitlines() if line.startswith("HANDOFF_PACKAGE: ")))
        package = json.loads(package_path.read_text(encoding="utf-8"))
        assert package["episode_id"] == handle.episode_id
        assert package["capability_id"] == "EXTEND_01_RESEARCH_V2_REAL_E2E"
        assert package["stage"] == "RESEARCH_PLANNING"
        assert package["output_schema"] == "research_plan_proposal"
        assert package["execution_family"] == "AGENT_HARNESS"
        assert package["execution_interface"] == "EXTEND_01_M2_B4_HANDOFF"
        assert package["model_override"] is None
        state = json.loads((handle.folder / "research_external_handoff.json").read_text(encoding="utf-8"))
        assert state["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        assert state["real_ai_execution"] is False
        assert state["real_ai_calls"] == 0
        assert state["provenance"] is None
    finally:
        if package_path is not None:
            package_path.unlink(missing_ok=True)


def _research_plan_proposal():
    return {
        "contract": "research_plan_proposal",
        "contract_version": "1.0.0",
        "central_question": "¿Qué puede sostenerse?",
        "intended_use": "OWNER_DECLARED_RESEARCH",
        "scope": "Tema y materiales suministrados",
        "dimensions": ["controlled"],
        "subquestions": ["¿Qué evidencia existe?"],
        "evidence_requirements": ["Evidencia verificable."],
        "source_strategy": "Material local",
        "critical_claims": ["No exceder la evidencia."],
        "rival_refutation": ["Considerar alternativas."],
        "gaps_risks": [],
        "potential_specialists": [],
        "sufficiency_criteria": ["Evidencia suficiente."],
        "target_final_works_decision": {},
        "supplied_works": [],
        "selection_policy": {},
        "planned_stages": ["PLANNING"],
    }


def test_extend01_b4_r1_imports_research_planning_and_resumes_without_replanning(isolated_real_episode, capsys):
    handle, settings = isolated_real_episode.handle, isolated_real_episode.settings
    assert main([
        "investigar-real", *_real_cli_args(handle, settings, handoff_directory=isolated_real_episode.handoff_directory),
        "--mission-authorization", isolated_real_episode.authorization_ref,
        "--mission-contract", isolated_real_episode.contract_ref,
    ]) == 0
    output = capsys.readouterr().out
    package_path = Path(next(line.split(": ", 1)[1] for line in output.splitlines() if line.startswith("HANDOFF_PACKAGE: ")))
    package = json.loads(package_path.read_text(encoding="utf-8"))
    assert package["stage"] == "RESEARCH_PLANNING"
    assert package["execution_controls"]["max_iterations"] == 2
    assert package["execution_controls"]["max_retries"] == 1
    assert package["execution_controls"]["timeout_seconds"] == 30
    assert package["execution_controls"]["unbounded_execution"] is False
    proposal = _research_plan_proposal()
    result_path = handle.folder / "owner-research-plan-result.json"
    encoded = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    result_path.write_text(json.dumps({
        "handoff_id": package["handoff_id"],
        "mission_id": package["mission_id"],
        "episode_id": package["episode_id"],
        "capability_id": package["capability_id"],
        "stage": package["stage"],
        "role": package["role"],
        "result_run_id": "OWNER-REAL-RUN-1",
        "package_checksum": package["package_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"],
        "skill_id": package["skill_id"],
        "skill_version": package["skill_version"],
        "output": proposal,
        "output_checksum": hashlib.sha256(encoded).hexdigest(),
    }), encoding="utf-8")
    try:
        assert main(["importar-resultado", str(result_path), "--config", str(settings)]) == 0
        imported = capsys.readouterr().out
        assert "RESEARCH_PLANNING_IMPORTED: YES" in imported
        assert "RESEARCH_RESUMED: YES" in imported
        state = json.loads((handle.folder / "research_external_handoff.json").read_text(encoding="utf-8"))
        assert state["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        assert state["completed_stages"] == ["RESEARCH_PLANNING"]
        assert state["provenance_status"] == "NOT_AVAILABLE"
        assert (handle.folder / "research_external_result.json").is_file()
        plan_path = handle.folder / "research_v2" / "b2" / "research_plan.json"
        assert plan_path.is_file()
        proposal_ref = state["research_plan_proposal"]
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        origin = plan["origin_artifact_refs"][0]
        assert origin["artifact_ref"] == proposal_ref["artifact_id"]
        assert origin["artifact_version"] == proposal_ref["artifact_version"]
        assert origin["checksum"] == proposal_ref["checksum"]
        assert origin["checksum"]
        # Reload the persisted episode before inspecting lineage again: the
        # checksum must survive the restart/resume boundary, not only memory.
        reloaded = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
        reloaded_plan = json.loads((reloaded.handle.folder / "research_v2" / "b2" / "research_plan.json").read_text(encoding="utf-8"))
        assert reloaded_plan["origin_artifact_refs"][0]["checksum"] == proposal_ref["checksum"]
        next_package = Path(state["handoff_package_ref"])
        assert json.loads(next_package.read_text(encoding="utf-8"))["stage"] != "RESEARCH_PLANNING"
    finally:
        result_path.unlink(missing_ok=True)
        package_path.unlink(missing_ok=True)


def test_extend01_verified_external_provenance_reenters_resume_context(
    isolated_real_episode, monkeypatch, capsys,
):
    handle, settings = isolated_real_episode.handle, isolated_real_episode.settings
    assert main([
        "investigar-real", *_real_cli_args(handle, settings, handoff_directory=isolated_real_episode.handoff_directory),
        "--mission-authorization", isolated_real_episode.authorization_ref,
        "--mission-contract", isolated_real_episode.contract_ref,
    ]) == 0
    output = capsys.readouterr().out
    package_path = Path(next(line.split(": ", 1)[1] for line in output.splitlines() if line.startswith("HANDOFF_PACKAGE: ")))
    package = json.loads(package_path.read_text(encoding="utf-8"))
    proposal = _research_plan_proposal()
    result_path = handle.folder / "owner-research-plan-provenance.json"
    encoded = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    provenance = {
        "mission_id": package["mission_id"],
        "episode_id": package["episode_id"],
        "capability_id": package["capability_id"],
        "stage": package["stage"],
        "role": package["role"],
        "handoff_id": package["handoff_id"],
        "run_id": "OWNER-VERIFIED-PLANNING",
        "executor_id": "owner-external-cognitive",
        "producer_provenance": {
            "actor_id": "OWNER-EXTERNAL",
            "run_id": "OWNER-VERIFIED-PLANNING",
            "executor_id": "owner-external-cognitive",
            "role": package["role"],
            "provenance_ref": "test-only-provenance",
        },
    }
    result_path.write_text(json.dumps({
        "handoff_id": package["handoff_id"], "mission_id": package["mission_id"],
        "episode_id": package["episode_id"], "capability_id": package["capability_id"],
        "stage": package["stage"], "role": package["role"],
        "result_run_id": "OWNER-VERIFIED-PLANNING", "package_checksum": package["package_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"],
        "skill_id": package["skill_id"], "skill_version": package["skill_version"],
        "output": proposal, "output_checksum": hashlib.sha256(encoded).hexdigest(),
        "provenance": provenance,
    }), encoding="utf-8")
    captured = {}

    def fake_resume(self, runners, *, initial_context=None):
        captured["initial_context"] = initial_context
        return {"status": "RESEARCH_READY", "completed_stages": ["B2", "M4", "M5", "M6"]}

    monkeypatch.setattr(RealResearchRoutePreparation, "run_canonical_vertical", fake_resume)
    try:
        imported = import_and_resume_external_research(
            VaultEpisodeStore.from_settings(settings), result_path,
            _test_provenance_repository_root=isolated_real_episode.provenance_root,
        )
        assert imported["provenance_status"] == "REPORTED_AND_BOUND"
        assert captured["initial_context"]["real_provenance"]["run_id"] == "OWNER-VERIFIED-PLANNING"
        state = json.loads((handle.folder / "research_external_handoff.json").read_text(encoding="utf-8"))
        assert state["provenance_status"] == "REPORTED_AND_BOUND"
    finally:
        result_path.unlink(missing_ok=True)
        package_path.unlink(missing_ok=True)


def test_extend01_b4_r3_imports_consecutive_cognitive_seams_without_repeating_b2(
    isolated_real_episode, capsys,
):
    """Planning and the next external seam resume the same B2 persistence."""
    handle, settings = isolated_real_episode.handle, isolated_real_episode.settings
    acquisition_adapter = _isolated_source_acquisition_adapter(isolated_real_episode, handle.episode_id)
    assert main([
        "investigar-real", *_real_cli_args(handle, settings, handoff_directory=isolated_real_episode.handoff_directory),
        "--mission-authorization", isolated_real_episode.authorization_ref,
        "--mission-contract", isolated_real_episode.contract_ref,
    ]) == 0
    output = capsys.readouterr().out
    planning_package_path = Path(next(line.split(": ", 1)[1] for line in output.splitlines() if line.startswith("HANDOFF_PACKAGE: ")))
    planning_package = json.loads(planning_package_path.read_text(encoding="utf-8"))
    result_paths = []
    try:
        proposal = _research_plan_proposal()
        planning_result = handle.folder / "owner-research-plan-r3.json"
        result_paths.append(planning_result)
        encoded = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        planning_result.write_text(json.dumps({
            "handoff_id": planning_package["handoff_id"], "mission_id": planning_package["mission_id"],
            "episode_id": planning_package["episode_id"], "capability_id": planning_package["capability_id"],
            "stage": planning_package["stage"], "role": planning_package["role"],
            "result_run_id": "OWNER-REAL-R3-PLANNING", "package_checksum": planning_package["package_checksum"],
            "input_manifest_checksum": planning_package["input_manifest_checksum"],
            "skill_id": planning_package["skill_id"], "skill_version": planning_package["skill_version"],
            "output": proposal, "output_checksum": hashlib.sha256(encoded).hexdigest(),
        }), encoding="utf-8")
        first = import_and_resume_external_research(
            VaultEpisodeStore.from_settings(settings), planning_result,
            _test_provenance_repository_root=isolated_real_episode.provenance_root,
            _test_acquisition_adapter=acquisition_adapter,
        )
        assert first["resume"]["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        phenomenon_package_path = Path(first["resume"]["handoff_package_ref"])
        phenomenon_package = json.loads(phenomenon_package_path.read_text(encoding="utf-8"))
        assert phenomenon_package["stage"] == "PHENOMENON_BASE_RESEARCH"

        plan = json.loads((handle.folder / "research_v2" / "b2" / "research_plan.json").read_text(encoding="utf-8"))
        cognitive = phenomenon(handle.episode_id, plan["research_plan_id"], str(plan.get("topic") or "Tema sintético"))
        # Deliberately omit Software-owned identity/runtime fields: the
        # canonical B2 projection must recreate them before validation.
        for field in ("research_id", "episode_id", "brief_version", "research_contract_version", "artifact_validity", "created_at"):
            cognitive.pop(field, None)
        phenomenon_result = handle.folder / "owner-phenomenon-r3.json"
        result_paths.append(phenomenon_result)
        encoded = json.dumps(cognitive, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        phenomenon_result.write_text(json.dumps({
            "handoff_id": phenomenon_package["handoff_id"], "mission_id": phenomenon_package["mission_id"],
            "episode_id": phenomenon_package["episode_id"], "capability_id": phenomenon_package["capability_id"],
            "stage": phenomenon_package["stage"], "role": phenomenon_package["role"],
            "result_run_id": "OWNER-REAL-R3-PHENOMENON", "package_checksum": phenomenon_package["package_checksum"],
            "input_manifest_checksum": phenomenon_package["input_manifest_checksum"],
            "skill_id": phenomenon_package["skill_id"], "skill_version": phenomenon_package["skill_version"],
            "output": cognitive, "output_checksum": hashlib.sha256(encoded).hexdigest(),
        }), encoding="utf-8")
        second = import_and_resume_external_research(
            VaultEpisodeStore.from_settings(settings), phenomenon_result,
            _test_provenance_repository_root=isolated_real_episode.provenance_root,
            _test_acquisition_adapter=acquisition_adapter,
        )
        assert second["resume"]["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        assert second["resume"]["pending_stage"] == "WORK_DISCOVERY"
        assert (handle.folder / "research_v2" / "b2" / "research_plan.json").is_file()
        assert (handle.folder / "research_v2" / "b2" / "phenomenon_base_research.json").is_file()
        assert "ARTIFACT_ALREADY_EXISTS" not in json.dumps(second, ensure_ascii=False)
        discovery_package_path = Path(second["resume"]["handoff_package_ref"])
        discovery_package = json.loads(discovery_package_path.read_text(encoding="utf-8"))
        work_ids = ["EXT-WORK-A", "EXT-WORK-B"]
        cognitive_discovery = discovery(handle.episode_id, plan["research_plan_id"], work_ids)
        for field in ("lifecycle_id", "lifecycle_version", "episode_id", "research_id", "created_at", "research_contract_version"):
            cognitive_discovery.pop(field, None)
        discovery_result = handle.folder / "owner-discovery-r3.json"
        result_paths.append(discovery_result)
        encoded = json.dumps(cognitive_discovery, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        discovery_result.write_text(json.dumps({
            "handoff_id": discovery_package["handoff_id"], "mission_id": discovery_package["mission_id"],
            "episode_id": discovery_package["episode_id"], "capability_id": discovery_package["capability_id"],
            "stage": discovery_package["stage"], "role": discovery_package["role"],
            "result_run_id": "OWNER-REAL-R3-DISCOVERY", "package_checksum": discovery_package["package_checksum"],
            "input_manifest_checksum": discovery_package["input_manifest_checksum"],
            "skill_id": discovery_package["skill_id"], "skill_version": discovery_package["skill_version"],
            "output": cognitive_discovery, "output_checksum": hashlib.sha256(encoded).hexdigest(),
        }), encoding="utf-8")
        third = import_and_resume_external_research(
            VaultEpisodeStore.from_settings(settings), discovery_result,
            _test_provenance_repository_root=isolated_real_episode.provenance_root,
            _test_acquisition_adapter=acquisition_adapter,
        )
        assert third["resume"]["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        assert third["resume"]["pending_stage"] == "BASE_RESEARCH_POOL"
        assert "ARTIFACT_ALREADY_EXISTS" not in json.dumps(third, ensure_ascii=False)
    finally:
        for path in result_paths:
            path.unlink(missing_ok=True)
        planning_package_path.unlink(missing_ok=True)


def test_extend01_b4_r1_rejects_tampered_execution_controls(isolated_real_episode, capsys):
    handle, settings = isolated_real_episode.handle, isolated_real_episode.settings
    assert main([
        "investigar-real", *_real_cli_args(handle, settings, handoff_directory=isolated_real_episode.handoff_directory),
        "--mission-authorization", isolated_real_episode.authorization_ref,
        "--mission-contract", isolated_real_episode.contract_ref,
    ]) == 0
    output = capsys.readouterr().out
    package_path = Path(next(line.split(": ", 1)[1] for line in output.splitlines() if line.startswith("HANDOFF_PACKAGE: ")))
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["execution_controls"]["max_iterations"] = 999
    package_path.write_text(json.dumps(package), encoding="utf-8")
    result_path = handle.folder / "tampered-result.json"
    result_path.write_text(json.dumps({"episode_id": handle.episode_id}), encoding="utf-8")
    try:
        with pytest.raises(ResearchM7Error, match="ROUNDTRIP_RESULT_BLOCKED"):
            import_and_resume_external_research(
                VaultEpisodeStore.from_settings(settings), result_path,
                _test_provenance_repository_root=isolated_real_episode.provenance_root,
            )
    finally:
        package_path.unlink(missing_ok=True)
        result_path.unlink(missing_ok=True)


def test_extend01_preparation_and_investigation_commands_have_distinct_dispatch(persisted_real_episode, monkeypatch, capsys):
    handle, settings = persisted_real_episode
    calls = []

    def stage_runner(stage):
        def run(_context):
            calls.append(stage)
            return {"stage": stage}
        return run

    monkeypatch.setattr(
        "src.cli._real_stage_runners_for_entrypoint",
        lambda _episode, _preparation=None: {stage: stage_runner(stage) for stage in ("B2", "M4", "M5", "M6")},
    )
    preparation_args = _real_cli_args(handle, settings)
    assert main(["preparar-ruta-real", *preparation_args]) == 0
    preparation_output = capsys.readouterr().out
    assert "REAL_ROUTE_PREPARED: YES" in preparation_output
    assert calls == []

    assert main(["investigar-real", *preparation_args]) == 0
    investigation_output = capsys.readouterr().out
    assert "REAL_ENTRYPOINT_OPERATIONAL: NO" in investigation_output
    assert "REAL_ROUTE_RESULT: RESEARCH_READY" in investigation_output
    assert calls == ["B2", "M4", "M5", "M6"]


def test_extend01_investigar_real_invokes_canonical_coordinator(persisted_real_episode, monkeypatch, capsys):
    handle, settings = persisted_real_episode
    invoked = []

    def dispatch(self, stage_runners):
        invoked.append((self.episode_id, tuple(stage_runners)))
        return {
            "status": "RESEARCH_READY",
            "completed_stages": ["B2", "M4", "M5", "M6"],
        }

    monkeypatch.setattr(RealResearchRoutePreparation, "run_canonical_vertical", dispatch)
    assert main([
        "investigar-real",
        *_real_cli_args(handle, settings),
    ]) == 0
    output = capsys.readouterr().out
    assert "REAL_ROUTE_RESULT: RESEARCH_READY" in output
    assert invoked == [(handle.episode_id, ("B2", "M4", "M5", "M6"))]


def test_extend01_b4_external_boundary_has_no_internal_runtime_selection():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    request = preparation.build_request()
    assert request.provider is None
    assert request.model is None
    assert request.executor is None
    assert request.execution_profile is None
    assert request.execution_family is None
    assert request.execution_route is None
    assert "provider" not in preparation.to_dict()
    assert "model" not in preparation.to_dict()
    assert "runtime" not in preparation.to_dict()
    assert "harness" not in preparation.to_dict()


def test_extend01_b4_bundle_is_separate_from_b1_b3_preparation():
    authorization = Path(REAL_EXTERNAL_HANDOFF_AUTHORIZATION)
    contract = Path(REAL_EXTERNAL_HANDOFF_CONTRACT)
    assert authorization.is_file()
    assert contract.is_file()
    authorization_payload = json.loads(authorization.read_text(encoding="utf-8"))
    contract_payload = json.loads(contract.read_text(encoding="utf-8"))
    assert authorization_payload["authorization"]["execution_mode"] == "REAL"
    assert authorization_payload["authorization"]["execution_family_ids"] == ["AGENT_HARNESS"]
    assert authorization_payload["authorization"]["execution_interface"] == "EXTEND_01_M2_B4_HANDOFF"
    assert contract_payload["mission_id"] == "EXTEND_01_M2_REAL_E2E"
    assert contract_payload["mission_authorization_path"] == REAL_EXTERNAL_HANDOFF_AUTHORIZATION
    assert json.loads(Path("plans/extend_01/m2/mission-authorization-preparation.json").read_text(encoding="utf-8"))["authorization"]["execution_mode"] == "SYNTHETIC_TEST"


def test_extend01_pending_boundary_does_not_claim_real_provenance():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    pending = {
        "status": "PENDING_EXTERNAL_COGNITIVE_RESULT",
        "real_ai_execution": False,
        "real_ai_calls": 0,
        "provenance": None,
    }
    assert pending["status"] != "RESEARCH_READY"
    assert pending["real_ai_execution"] is False
    assert pending["real_ai_calls"] == 0
    assert pending["provenance"] is None


def test_extend01_investigar_real_requires_operational_limits_but_not_topic_or_question(persisted_real_episode):
    handle, settings = persisted_real_episode
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "investigar-real",
            "--episodio-id", handle.episode_id,
            "--config", str(settings),
            "--max-iterations", "2",
            "--max-retries", "1",
            "--timeout", "30",
        ])


def test_extend01_productive_adapters_bind_each_canonical_stage(persisted_real_episode):
    handle, settings = persisted_real_episode
    episode = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
    adapters = ProductiveResearchStageAdapters(episode, cognitive_executor=lambda _request: None)
    assert {stage: authority.__qualname__ for stage, authority in adapters.canonical_authorities().items()} == {
        "B2": "ResearchB2Orchestrator.run",
        "M4": "ResearchB3Orchestrator.run",
        "M5": "ResearchB3Orchestrator.run_m5",
        "M6": "ResearchB4Orchestrator.run_m6",
    }
    assert all(callable(runner) for runner in adapters.stage_runners().values())


def test_extend01_persisted_episode_preserves_owner_research_bindings(persisted_real_episode):
    handle, settings = persisted_real_episode
    episode = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
    assert episode.human_input["initial_question"] == "¿Qué puede sostenerse?"
    assert episode.human_input["research_role"] == "ANCLA"
    assert episode.human_input["editorial_intent"] == "PREFERIDA"
    assert episode.brief["selection_authority"] == "OWNER_DECIDES"
    assert episode.brief["work_intents"] == [
        {"work_ref": "Obra A", "editorial_intent": "PREFERIDA"},
        {"work_ref": "Obra B", "editorial_intent": "REQUERIDA"},
        {"work_ref": "Obra C", "editorial_intent": "NO_DECLARADA"},
    ]
    assert episode.brief["owner_restrictions"] == ["MUST_INCLUDE: Conservar la restricción del OWNER."]
    assert episode.brief["objetivo"] == "OWNER_DECLARED_RESEARCH"


def test_extend01_persisted_episode_derives_standard_objective_when_unambiguous(persisted_real_episode):
    handle, settings = persisted_real_episode
    for name in ("research_episode_brief.json", "research_channel_context.json", "research_source_access.json"):
        (handle.folder / name).unlink()
    store = VaultEpisodeStore.from_settings(settings)
    episode = PersistedResearchEpisode.load(store, handle.episode_id)
    assert episode.brief["objetivo"] == "RESEARCH_AND_THESIS"
    assert (handle.folder / "research_episode_brief.json").is_file()


def test_extend01_real_adapters_transport_selection_chain_and_provenance(
    persisted_real_episode, monkeypatch, tmp_path,
):
    handle, settings = persisted_real_episode
    episode = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
    executor_calls = []

    def executor(request):
        executor_calls.append(request)
        return {"dimensions": ["controlled"]}

    canonical_root = tmp_path / "canonical_repo"
    (canonical_root / "output").mkdir(parents=True)
    (canonical_root / "output" / "execution_provenance_registry.json").write_text(
        json.dumps({"registry_version": "1.0.0", "runs": [], "handoffs": [], "attempts": []}),
        encoding="utf-8",
    )
    adapters = ProductiveResearchStageAdapters(
        episode,
        cognitive_executor=executor,
        _test_provenance_repository_root=canonical_root,
    )
    root = adapters.root
    root.mkdir(parents=True, exist_ok=True)

    def write_payload(name, payload):
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def ref(stage, kind, name, payload, *, id_suffix=None):
        path = write_payload(name, payload)
        return {
            "artifact_id": f"{handle.episode_id}:{stage}:{id_suffix or kind}",
            "artifact_kind": kind,
            "artifact_version": "1.0.0",
            "path": str(path),
            "checksum": hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }

    b2_artifacts = [
        ref("B2", "ResearchPack", "b2_research_pack.json", {}),
        ref("B2", "WorkLifecycle", "b2_work_lifecycle.json", {}),
        ref("B2", "WorkResearchDossierCollection", "b2_pool.json", {"dossiers": []}, id_suffix="BASE_RESEARCH_POOL"),
        ref("B2", "ThesisArtifact", "b2_thesis.json", {}),
        ref("B2", "ResearchComparison", "b2_comparison.json", {}),
    ]
    b2_manifest = ref("B2", "ResearchB2ExecutionManifest", "b2_manifest.json", {"artifacts": b2_artifacts})
    plan_ref = ref("B2", "ResearchPlan", "b2_plan.json", {})
    evidence_ref = ref("B2", "SourceAccessAndEvidenceReport", "b2_evidence.json", {})
    b2_result = {
        "execution_manifest": b2_manifest,
        "research_plan": plan_ref,
        "preliminary_fidelity": ref("B2", "WorkResearchDossierCollection", "b2_fidelity.json", {"dossiers": []}),
        "initial_sufficiency": ref("B2", "ResearchStopDecisionCollection", "b2_sufficiency.json", {"dossiers": []}),
        "deepening_targets": [],
        "lifecycle_projection": {},
        "evidence_report": evidence_ref,
    }
    m4_artifact = ref("M4", "ResearchStopDecision", "m4_artifact.json", {})
    m4_manifest = ref("M4", "ResearchM4ExecutionManifest", "m4_manifest.json", {"artifacts": [m4_artifact], "selection": {"mode": "USER_SELECTION"}})
    m4_result = {"execution_manifest": m4_manifest, "evidence_report": ref("M4", "SourceAccessAndEvidenceReport", "m4_evidence.json", {})}
    m5_output = ref("M5", "ClaimsLedger", "m5_artifact.json", {})
    m5_manifest = ref("M5", "ResearchM5ExecutionManifest", "m5_manifest.json", {"m5_outputs": [m5_output]})
    m5_result = {"execution_manifest": m5_manifest, "evidence_report": ref("M5", "SourceAccessAndEvidenceReport", "m5_evidence.json", {})}
    adapters._plan_for_b2 = lambda: {}
    calls = []

    def fake_b2(self, plan, *, context):
        calls.append(("B2", context))
        self.cognitive_executor({"stage": "B2"})
        return b2_result

    def fake_m4(self, baseline, *, context, selection_mode, human_decision, delegation_decision, selection_options):
        calls.append(("M4", context, selection_mode))
        return m4_result

    def fake_m5(self, baseline, m4, *, context, selection_change_decision=None, selection_change_delegation=None):
        calls.append(("M5", context))
        return m5_result

    def fake_m6(self, m5, *, context, research_chain=None, invalidation_engine=None):
        calls.append(("M6", context, research_chain))
        return {"stage": "M6", "research_chain": research_chain}

    monkeypatch.setattr(ResearchB2Orchestrator, "run", fake_b2)
    monkeypatch.setattr(ResearchB3Orchestrator, "run", fake_m4)
    monkeypatch.setattr(ResearchB3Orchestrator, "run_m5", fake_m5)
    monkeypatch.setattr(ResearchB4Orchestrator, "run_m6", fake_m6)
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config(episode_id=handle.episode_id))
    result = preparation.run_canonical_vertical(
        adapters.stage_runners(),
        initial_context={
            "selection": {"mode": "USER_SELECTION"},
            "real_provenance": {"run_id": "REAL-RUN-1", "executor_id": "controlled-executor"},
        },
    )
    assert result["completed_stages"] == ["B2", "M4", "M5", "M6"]
    assert [item[0] for item in calls] == ["B2", "M4", "M5", "M6"]
    assert calls[1][2] == "USER_SELECTION"
    assert calls[3][1]["executor_id"] == "controlled-executor"
    assert {ref["artifact_id"] for ref in calls[3][2]["artifact_refs"]} >= {
        b2_manifest["artifact_id"], m4_manifest["artifact_id"], m5_manifest["artifact_id"],
    }
    assert executor_calls == [{"stage": "B2"}]
    registry = json.loads((canonical_root / "output" / "execution_provenance_registry.json").read_text(encoding="utf-8"))
    outputs = [output for run in registry["runs"] for output in run["outputs"]]
    by_binding = {(output["artifact_id"], output["artifact_kind"]): output for output in outputs}
    assert by_binding[(plan_ref["artifact_id"], "ResearchPlan")]["artifact_kind"] == "ResearchPlan"
    assert by_binding[(m5_manifest["artifact_id"], "ResearchM5ExecutionManifest")]["artifact_kind"] == "ResearchM5ExecutionManifest"
    assert all(output["artifact_kind"] != "semantic_audit" for output in outputs)


def test_extend01_adapters_keep_functional_blockers_distinct(persisted_real_episode):
    handle, settings = persisted_real_episode
    episode = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
    adapters = ProductiveResearchStageAdapters(episode, cognitive_executor=lambda _request: None)
    with pytest.raises(ResearchM7Error, match="REAL_ROUTE_OWNER_SELECTION_REQUIRED"):
        adapters.run_m4({"b2_result": {}})
    with pytest.raises(ResearchM7Error, match="REAL_ROUTE_RESEARCH_CHAIN_REQUIRED"):
        adapters.run_m6({"m5_result": {}})
    with pytest.raises(ResearchM7Error, match="REAL_ROUTE_REAL_PROVENANCE_REQUIRED"):
        adapters.run_m6({"m5_result": {}, "research_chain": {}})


def test_extend01_m4_missing_selection_fails_closed_after_b2(persisted_real_episode):
    handle, settings = persisted_real_episode
    episode = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
    adapters = ProductiveResearchStageAdapters(episode, cognitive_executor=lambda _request: None)
    plan_path = adapters.root / "b2" / "missing-plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({"research_plan_id": "PLAN-EXTEND01", "episode_id": handle.episode_id}), encoding="utf-8")
    with pytest.raises(ResearchM7Error, match="MISSING_VALID_SELECTION"):
        adapters.run_m4({"b2_result": {"research_plan": {"path": str(plan_path)}}})


def test_extend01_m4_recovers_valid_persisted_owner_selection(persisted_real_episode, monkeypatch):
    handle, settings = persisted_real_episode
    episode = PersistedResearchEpisode.load(VaultEpisodeStore.from_settings(settings), handle.episode_id)
    adapters = ProductiveResearchStageAdapters(episode, cognitive_executor=lambda _request: None)
    plan_path = adapters.root / "b2" / "research_plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({"research_plan_id": "PLAN-EXTEND01", "episode_id": handle.episode_id}), encoding="utf-8")
    request = HumanDecisionRequest(
        request_id="PLAN-EXTEND01:M4:REQUEST",
        prompt="Seleccionar obras",
        options=({"id": "SELECTION_SET:W1", "label": "W1"},),
        recommendation="SELECTION_SET:W1",
        episode_id=handle.episode_id,
    )
    decision = HumanDecision(
        request_id=request.request_id,
        action="SELECT_ALTERNATIVE",
        selected_option="SELECTION_SET:W1",
        actor_ref="OWNER",
        channel="TERMINAL",
        episode_id=handle.episode_id,
        occurred_at="2026-09-10T00:00:00+00:00",
        request_checksum=request.checksum(),
    )
    adapters.b3_persistence.persist(
        "M4_SELECTION_REQUEST", request.to_dict(),
        artifact_id="PLAN-EXTEND01:M4:SELECTION_AUTHORITY", artifact_kind="HumanDecisionRequest",
    )
    adapters.b3_persistence.persist(
        "M4_SELECTION_DECISION", decision.to_dict(),
        artifact_id="PLAN-EXTEND01:M4:HUMAN_DECISION", artifact_kind="HumanDecision",
    )
    adapters._baseline = lambda _b2: {
        "base_research_pool": [], "preliminary_fidelity": [], "initial_sufficiency": [],
        "research_plan": {}, "phenomenon_base_research": {}, "work_discovery": {},
        "provisional_thesis": {}, "research_comparison": {}, "deepening_targets": [],
        "lifecycle": {}, "evidence_report": {},
    }
    monkeypatch.setattr(ResearchB3Orchestrator, "_eligible_candidates", staticmethod(lambda *_args: {"W1"}))
    calls = []

    def fake_m4(self, baseline, *, context, selection_mode, human_decision, delegation_decision, selection_options):
        calls.append((selection_mode, human_decision, selection_options))
        return {"execution_manifest": {"path": str(plan_path)}, "evidence_report": {}}

    monkeypatch.setattr(ResearchB3Orchestrator, "run", fake_m4)
    monkeypatch.setattr(adapters, "_recover_m4_result", lambda _b2: None)
    evidence_path = adapters.root / "b2" / "evidence.json"
    evidence_path.write_text(json.dumps({"research_stage": "BASE_RESEARCH"}), encoding="utf-8")
    request_runtime = RealResearchRoutePreparation.from_mapping(_real_route_config(episode_id=handle.episode_id)).build_request()
    result = adapters.run_m4({
        "b2_result": {
            "research_plan": {"path": str(plan_path)},
            "evidence_report": {"path": str(evidence_path)},
        },
        "request": request_runtime,
    })
    assert result["execution_manifest"]["path"] == str(plan_path)
    assert calls and calls[0][0] == "USER_SELECTION"
    assert calls[0][1]["selected_option"] == "SELECTION_SET:W1"


def test_extend01_mock_and_failed_real_do_not_claim_real_execution():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    assert preparation.claims_from_result(None) == {
        "real_ai_execution": False,
        "real_ai_calls": 0,
        "real_research": False,
        "real_research_quality": "NOT_DEMONSTRATED",
        "authorized_for_product_use": False,
    }
    failed = ExecutionResult(
        run_id="RUN-FAILED",
        status=ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER,
        executor_type="native-provider",
        provider="provider-a",
        model="model-a",
        input_manifest_checksum="input",
        output=None,
        output_checksum=None,
        started_at="2026-09-07T00:00:00Z",
        completed_at="2026-09-07T00:00:00Z",
        error="provider unavailable",
        is_real_editorial_execution=False,
    )
    assert preparation.claims_from_result(failed)["real_ai_execution"] is False


def test_extend01_real_provenance_rejects_synthetic_fixture():
    with pytest.raises(ResearchM7Error, match="REAL_PROVENANCE_SYNTHETIC_OR_MISSING"):
        RealResearchRoutePreparation.assert_real_provenance({"run_id": "M7-M5-PRODUCER", "executor_id": "synthetic-fixture"})


def test_extend01_real_route_runs_without_acquisition_selection():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    calls = []

    stage_runners = {
        stage: (lambda _context, stage=stage: calls.append(stage) or {"stage": stage})
        for stage in ("B2", "M4", "M5", "M6")
    }

    result = preparation.run_canonical_vertical(stage_runners)
    assert result["status"] == "RESEARCH_READY"
    assert result["completed_stages"] == ["B2", "M4", "M5", "M6"]
    assert calls == ["B2", "M4", "M5", "M6"]


def test_extend01_real_route_binds_canonical_vertical_and_stops_at_m6():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    calls = []

    def stage_runner(stage):
        def run(context):
            calls.append(stage)
            assert context["request"].capability_id == "EXTEND_01_RESEARCH_V2_REAL_E2E"
            return {"stage": stage}
        return run

    result = preparation.run_canonical_vertical({stage: stage_runner(stage) for stage in ("B2", "M4", "M5", "M6")})
    assert calls == ["B2", "M4", "M5", "M6"]
    assert result["stage_results"]["M6"] == {"stage": "M6"}
    route = result["canonical_route"]
    assert route["stages"] == ["B2", "M4", "M5", "M6"]
    assert route["sequence_owner"] == "RealResearchRoutePreparation.run_canonical_vertical"
    assert route["stop_after"] == "M6"
    assert route["invocations"] == {
        "B2": "ResearchB2Orchestrator.run",
        "M4": "ResearchB3Orchestrator.run",
        "M5": "ResearchB3Orchestrator.run_m5",
        "M6": "ResearchB4Orchestrator.run_m6",
    }
    assert result["terminal_stage"] == "RESEARCH_READY"
    assert result["post_terminal_execution"] is False


def test_extend01_real_route_rejects_post_m6_continuation():
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    post_m6_calls = []
    stage_runners = {
        stage: (lambda _context, stage=stage: {"stage": stage})
        for stage in ("B2", "M4", "M5", "M6")
    }
    result = preparation.run_canonical_vertical(stage_runners)
    assert result["terminal_stage"] == "RESEARCH_READY"
    assert result["completed_stages"] == ["B2", "M4", "M5", "M6"]


def test_extend01_b4_r5_integrated_external_roundtrip_m4_m6(tmp_path):
    """Drive the production handoff/import/resume seams through ResearchReady."""
    test_root = Path(tempfile.mkdtemp(prefix="r5-"))
    bundle = _isolated_external_handoff_bundle(tmp_path)
    episode_root = test_root / "episode"
    episode_root.mkdir()
    handle, settings = _persisted_real_episode(episode_root)
    handoff_directory = bundle.handoff_directory
    canonical_root = tmp_path / "canonical_repo"
    (canonical_root / "config").mkdir(parents=True)
    (canonical_root / "output").mkdir()
    (canonical_root / "config" / "execution_provenance_policy.json").write_text(
        json.dumps({"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"}),
        encoding="utf-8",
    )
    (canonical_root / "output" / "execution_provenance_registry.json").write_text(
        json.dumps({"registry_version": "1.0.0", "runs": [], "handoffs": [], "attempts": []}),
        encoding="utf-8",
    )
    store = VaultEpisodeStore.from_settings(settings)
    episode = PersistedResearchEpisode.load(store, handle.episode_id)
    productive_registry = Path(__file__).resolve().parents[2] / "output" / "execution_provenance_registry.json"
    productive_registry_before = productive_registry.read_bytes()
    preparation = RealResearchRoutePreparation.from_mapping({
        "episode_id": handle.episode_id,
        "topic": "Tema persistido de Research V2",
        "question": "¿Qué puede sostenerse?",
        "budget_limit": 25, "max_iterations": 2, "max_retries": 1, "timeout_seconds": 30,
        "mission_authorization_path": bundle.authorization_ref,
        "mission_contract_path": bundle.contract_ref,
        "handoff_directory": handoff_directory,
    })
    completed_packages: list[str] = []
    result_paths: list[Path] = []
    works = ["EXT-WORK-A", "EXT-WORK-B"]
    acquisition_root = tmp_path / "acquisition"
    acquisition_root.mkdir()
    source_recovery = acquisition_root / "S1.json"
    source_recovery.write_text(
        json.dumps({"source_id": "S1", "content": "Fixture controlado.", "locator": "fixture://S1"}),
        encoding="utf-8",
    )
    source_checksum = hashlib.sha256(source_recovery.read_bytes()).hexdigest()
    source_execution_ref = "R5-ACQ-S1"
    register_software_outputs(
        canonical_root / "output" / "execution_provenance_registry.json",
        run_id=source_execution_ref,
        episode_id=handle.episode_id,
        role="RESEARCH_ACQUISITION",
        outputs=[{"artifact_id": str(source_recovery), "artifact_kind": "research", "artifact_version": "1.0.0", "checksum": source_checksum}],
    )
    work_bindings = {}
    for work_id in works:
        recovery = acquisition_root / f"{work_id}.json"
        recovery.write_text(json.dumps({"work_id": work_id}), encoding="utf-8")
        recovery_checksum = hashlib.sha256(recovery.read_bytes()).hexdigest()
        execution_ref = f"R5-ACQ-{work_id}"
        register_software_outputs(
            canonical_root / "output" / "execution_provenance_registry.json",
            run_id=execution_ref,
            episode_id=handle.episode_id,
            role="RESEARCH_AND_CURATION",
            outputs=[{"artifact_id": str(recovery), "artifact_kind": "research", "artifact_version": "1.0.0", "checksum": recovery_checksum}],
        )
        work_bindings[work_id] = {
            "retrieval_status": "RECOVERED", "software_controlled": True,
            "recovery_artifact_ref": str(recovery), "request_ref": f"software:request:{work_id}",
            "execution_ref": execution_ref, "evidence_status": "VERIFIED", "source_ref": work_id,
            "representation_kind": "ORIGINAL_WORK", "edition_or_version": "fixture-1",
            "consulted_locator": f"fixture://{work_id}",
        }
    acquisition_adapter = SoftwareAcquisitionAdapter(
        bindings={"S1": {
            "request_ref": "software:request:S1", "execution_ref": source_execution_ref,
            "recovery_artifact_ref": str(source_recovery), "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED", "software_controlled": True,
        }},
        work_bindings=work_bindings,
        recovery_artifacts={
            str(source_recovery): {"path": str(source_recovery), "checksum": source_checksum},
            **{str(acquisition_root / f"{work_id}.json"): {"path": str(acquisition_root / f"{work_id}.json"), "checksum": hashlib.sha256((acquisition_root / f"{work_id}.json").read_bytes()).hexdigest()} for work_id in works},
        },
        execution_registry_path=canonical_root / "output" / "execution_provenance_registry.json",
    )
    research_id = None
    stage_work_cursor = {"DEEP_WORK_RESEARCH": 0, "DEEP_FIDELITY": 0}

    def cognitive_output(package):
        nonlocal research_id
        stage = package["stage"]
        if stage == "RESEARCH_PLANNING":
            return _research_plan_proposal()
        plan = json.loads((handle.folder / "research_v2" / "b2" / "research_plan.json").read_text(encoding="utf-8"))
        research_id = str(plan["research_plan_id"])
        synthetic = SyntheticResearchExecutor({
            "episode_id": handle.episode_id, "topic": "Tema persistido de Research V2", "works": works,
            "_effective_selected_work_ids": works,
            "selection_mode": "MANUAL",
            "_selection_authority_ref": f"{research_id}:M4:HUMAN_DECISION",
        })
        # The planning fixture is the canonical source of the ResearchPlan
        # id in this route; keep the deterministic test double bound to it
        # instead of its historical standalone fixture id.
        synthetic.research_id = research_id
        manifest_text = json.dumps(package.get("input_manifest", {}), ensure_ascii=False)
        work_id = next((item for item in works if item in manifest_text), None)
        if work_id is None and stage in stage_work_cursor:
            index = stage_work_cursor[stage]
            work_id = works[min(index, len(works) - 1)]
            stage_work_cursor[stage] = index + 1
        work_id = work_id or works[0]
        prepared = {
            "input_payload": {
                "work_id": work_id,
                "subject_ref": f"{research_id}:M4:DOSSIER:{work_id}",
                "audit_scope": {"required_criteria": sorted(M6_REQUIRED_AUDIT_CRITERIA)},
            }
        }
        request = SimpleNamespace(
            stage=stage,
            prepared_contract=prepared,
            input_artifacts=[
                {"artifact_id": item["artifact_id"]}
                for item in package.get("input_manifest", {}).get("artifacts", [])
            ],
        )
        if stage == "M6_INDEPENDENT_RESEARCH_AUDIT":
            return audit(request)
        if stage == "INITIAL_SUFFICIENCY":
            pool_payload = json.loads((handle.folder / "research_v2" / "b2" / "base_research_pool.json").read_text(encoding="utf-8"))
            dossiers = pool_payload["dossiers"] if isinstance(pool_payload, dict) else pool_payload
            return [
                sufficiency(research_id, "PHENOMENON", research_id, "FORMULAR_TESIS_PROVISIONAL")
            ] + [
                sufficiency(research_id, "WORK_RESEARCH_DOSSIER", item["dossier_id"], "RESEARCH_COMPARISON")
                for item in dossiers
            ]
        return synthetic(request)

    try:
        preparation_result = preparation.run_canonical_vertical(
            ProductiveResearchStageAdapters(
                episode,
                cognitive_executor=ExternalResearchCognitiveExecutor(episode, preparation),
                acquisition_adapter=acquisition_adapter,
                _test_provenance_repository_root=canonical_root,
            ).stage_runners(),
        )
        assert preparation_result["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        package_path = Path(preparation_result["handoff_package_ref"])
        for _ in range(50):
            package = json.loads(package_path.read_text(encoding="utf-8"))
            completed_packages.append(package["stage"])
            output_value = cognitive_output(package)
            encoded = json.dumps(output_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            result_path = handle.folder / f"r5-{len(result_paths)}.json"
            result_paths.append(result_path)
            result_run_id = f"R5-EXTERNAL-{len(result_paths)}"
            provenance = {
                "mission_id": package["mission_id"], "episode_id": handle.episode_id,
                "capability_id": package["capability_id"], "stage": package["stage"],
                "role": package["role"], "handoff_id": package["handoff_id"],
                "run_id": result_run_id, "executor_id": f"r5-external-{package['stage'].lower()}",
                "actor_id": f"R5-ACTOR-{package['stage']}",
                "provenance_ref": "output/execution_provenance_registry.json",
            }
            result_path.write_text(json.dumps({
                "handoff_id": package["handoff_id"], "mission_id": package["mission_id"],
                "episode_id": handle.episode_id, "capability_id": package["capability_id"],
                "stage": package["stage"], "role": package["role"],
                "result_run_id": result_run_id, "package_checksum": package["package_checksum"],
                "input_manifest_checksum": package["input_manifest_checksum"],
                "skill_id": package["skill_id"], "skill_version": package["skill_version"],
                "output": output_value, "output_checksum": hashlib.sha256(encoded).hexdigest(),
                "provenance": provenance,
            }), encoding="utf-8")
            imported = import_and_resume_external_research(
                store, result_path, _test_provenance_repository_root=canonical_root,
                _test_acquisition_adapter=acquisition_adapter,
            )
            resume = imported["resume"]
            if resume["status"] == "WAITING_FOR_HUMAN_DECISION":
                request = resume["human_decision_request"]
                response = respond_to_research_human_decision(
                    store, handle.episode_id, request_id=request["request_id"], action="APPROVE",
                )
                assert response["status"] == "RESPONSE_RECORDED"
                episode = PersistedResearchEpisode.load(store, handle.episode_id)
                runners = ProductiveResearchStageAdapters(
                    episode,
                    cognitive_executor=ExternalResearchCognitiveExecutor(episode, preparation),
                    acquisition_adapter=acquisition_adapter,
                    _test_provenance_repository_root=canonical_root,
                ).stage_runners()
                resume = preparation.run_canonical_vertical(runners)
            if resume["status"] == "RESEARCH_READY":
                break
            assert resume["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
            package_path = Path(resume["handoff_package_ref"])
        else:
            pytest.fail("external roundtrip did not reach ResearchReady")
        assert completed_packages[0] == "RESEARCH_PLANNING"
        assert completed_packages.count("RESEARCH_PLANNING") == 1
        assert completed_packages.count("PHENOMENON_BASE_RESEARCH") == 1
        assert completed_packages.count("WORK_DISCOVERY") == 1
        assert ":M4:SELECTION_REQUEST" in json.loads((handle.folder / "human_decision_requests.json").read_text(encoding="utf-8"))["requests"][0]["request_id"]
        assert completed_packages[-1] == "M6_INDEPENDENT_RESEARCH_AUDIT"
        assert resume["completed_stages"] == ["B2", "M4", "M5", "M6"]
        registry = json.loads((canonical_root / "output" / "execution_provenance_registry.json").read_text(encoding="utf-8"))
        assert any(run["role"] == "RESEARCH_AND_CURATION" and run["episode_id"] == handle.episode_id for run in registry["runs"])
        auditor_runs = [run for run in registry["runs"] if run["role"] == "INDEPENDENT_RESEARCH_AUDITOR"]
        assert len(auditor_runs) == 1
        assert auditor_runs[0]["actual_executor"].startswith("r5-external-m6")
        assert auditor_runs[0]["provider_kind"] == "REAL"
        assert auditor_runs[0]["provider"] == "UNAVAILABLE_FROM_PROVIDER"
        assert auditor_runs[0]["model"] == "UNAVAILABLE_FROM_PROVIDER"
        assert auditor_runs[0]["actual_provider"] == "UNAVAILABLE_FROM_PROVIDER"
        assert auditor_runs[0]["actual_model"] == "UNAVAILABLE_FROM_PROVIDER"
        assert productive_registry.read_bytes() == productive_registry_before
        json.loads(productive_registry.read_text(encoding="utf-8"))
    finally:
        for path in result_paths:
            path.unlink(missing_ok=True)
        if handoff_directory.is_dir():
            shutil.rmtree(handoff_directory, ignore_errors=True)
        if bundle.root.is_dir():
            shutil.rmtree(bundle.root, ignore_errors=True)
        if test_root.is_dir():
            shutil.rmtree(test_root, ignore_errors=True)
def test_acquisition_is_neutral_and_preserves_provenance_and_status(tmp_path):
    from src.application.research_b2 import SoftwareAcquisitionAdapter
    import hashlib, json

    # Minimal phenomenon pack for adapter
    pack = {
        "research_id": "RP-ACQ-NEUTRAL",
        "source_registry": [
            {"source_id": "S-POSITIVE", "locator": "loc:positive", "role": "EVIDENCE"},
            {"source_id": "S-NEGATIVE", "locator": "loc:negative", "role": "EVIDENCE"},
        ],
        "evidence_type_separation": {"work_evidence_refs": [], "external_reality_evidence_refs": []},
    }
    # Positive requires physical recovery and execution provenance
    recovery = tmp_path / "S-POSITIVE.json"
    recovery.write_text(json.dumps({"source_id": "S-POSITIVE", "content": "evidencia positiva"}), encoding="utf-8")
    ref = {"artifact_id": "recovery:S-POSITIVE", "path": str(recovery), "checksum": hashlib.sha256(recovery.read_bytes()).hexdigest()}
    # Execution registry provenance
    registry_path = Path(__file__).resolve().parents[2] / "output" / "execution_provenance_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    run = copy.deepcopy(registry["runs"][0])
    exec_ref = "RUN-POSITIVE-NEUTRAL"
    run.update({
        "run_id": exec_ref,
        "status": "SUCCEEDED",
        "outputs": [{"artifact_kind": "research", "artifact_id": "recovery:S-POSITIVE", "artifact_ref": "research:recovery:S-POSITIVE", "checksum": ref["checksum"]}],
        "output_artifact_ids": ["research:recovery:S-POSITIVE"],
        "output_versions": ["fixture-1"],
        "output_checksums": [ref["checksum"]],
    })
    registry["runs"] = [run]
    exec_registry = tmp_path / "execution_provenance_registry.json"
    exec_registry.write_text(json.dumps(registry), encoding="utf-8")
    binding_positive = {
        "request_ref": "request:S-POSITIVE",
        "execution_ref": exec_ref,
        "recovery_artifact_ref": "recovery:S-POSITIVE",
        "retrieval_status": "RECOVERED",
        "evidence_status": "VERIFIED",
        "software_controlled": True,
    }
    # Negative is UNAVAILABLE without recovery artifact
    adapter = SoftwareAcquisitionAdapter(
        {"S-POSITIVE": binding_positive},
        recovery_artifacts={"recovery:S-POSITIVE": ref},
        execution_registry_path=exec_registry,
    )
    result = adapter.materialize(pack)
    positive_source = next(s for s in result["source_registry"] if s["source_id"] == "S-POSITIVE")
    negative_source = next(s for s in result["source_registry"] if s["source_id"] == "S-NEGATIVE")
    # Positive preserves RECOVERED and VERIFIED with provenance REVIEWED
    assert positive_source["retrieval_status"] == "RECOVERED"
    assert positive_source["evidence_status"] == "VERIFIED"
    assert positive_source["provenance"]["verification_status"] == "REVIEWED"
    assert positive_source["provenance"]["acquisition_method"] == "SOFTWARE_CONTROLLED_ACQUISITION"
    assert result["acquisition_bindings"][0]["recovery_artifact_ref"] == "recovery:S-POSITIVE"
    # Negative remains NOT_RECOVERED/PENDING and NOT_REVIEWED, no recovery artifact
    assert negative_source["retrieval_status"] == "NOT_RECOVERED"
    assert negative_source["evidence_status"] == "PENDING"
    assert negative_source["provenance"]["verification_status"] == "NOT_REVIEWED"
    assert negative_source["provenance"]["acquisition_method"] == "SOFTWARE_CONTROLLED_ACQUISITION"
    # Unavailable acquisition blocks only required scope: RESEARCH_READY with negative alone must still be evaluable but not produce DIRECT
    from src.application.research_b2 import ResearchB2Orchestrator, ResearchB2Persistence
    # The adapter itself is neutral: no provider selection, no model authority
    assert adapter.bindings["S-POSITIVE"]["software_controlled"] is True


def test_research_to_script_handoff_preserves_consultative_fields_as_non_authoritative(tmp_path):
    # Use synthetic runner to get a real handoff and verify consultative preservation
    state = ResearchM7SyntheticRunner(tmp_path).run(_input())
    handoff = json.loads(Path(next(item for item in state["artifacts"] if item["stage"] == "B5_I3_HANDOFF")["path"]).read_text(encoding="utf-8"))
    projection = handoff["research_v2_projection"]
    # Consultative fields must be preserved via projection refs and lineage
    assert projection["authority"] == "RESEARCH_V2"
    assert "downstream_restrictions" in projection
    assert "lineage" in projection
    # Refined thesis payload must contain consultative contributions
    refined_ref = projection["research_refs"]["refined_thesis"]
    refined_payload = json.loads(Path(refined_ref["path"]).read_text(encoding="utf-8"))
    assert "material_contributions" in refined_payload
    assert "limits" in refined_payload
    assert "counterevidence_refs" in refined_payload or "counterevidence" in json.dumps(refined_payload).lower()
    assert "remaining_uncertainties" in refined_payload or "uncertaint" in json.dumps(refined_payload).lower()
    assert "rival_interpretations" in refined_payload or "rival" in json.dumps(refined_payload).lower()
    # Provenance must be present (checksum is canonical json hash, not raw file bytes)
    from src.application.research_b2 import _checksum as _b2_checksum
    assert refined_ref["checksum"] == _b2_checksum(refined_payload)
    # Handoff must be consultative-only: narrative decisions not made
    assert handoff["narrative_decisions_not_made"] is True
    # Restrictions must be bound to manifest and resolvable
    manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "M6")
    manifest = json.loads(Path(manifest_ref["path"]).read_text(encoding="utf-8"))
    assert handoff["downstream_restrictions"] == manifest["downstream_restrictions"]
    assert handoff["research_lineage"]["lineage"] == manifest["lineage"]
    # Semantic context must equal projection (no divergence) and must not contain narrative authority
    assert handoff["research_v2_semantic_context"] == projection
    assert "viewer_journey" not in json.dumps(projection).lower()
    assert "narrative_use" not in json.dumps(projection).lower()


def test_extend01_max_iterations_is_bound_to_existing_guard_and_stops_before_editorial(tmp_path):
    runner = ResearchM7SyntheticRunner(tmp_path, max_iterations=2)
    with pytest.raises(ResearchM7Error, match="NO_PROGRESS / ITERATION_GUARD"):
        runner.run(_input(), simulate_no_progress=True)
    state = runner.store.load()
    assert state["iteration_guard"]["max_iterations"] == 2
    preparation = RealResearchRoutePreparation.from_mapping(_real_route_config())
    prepared = preparation.to_dict()
    assert prepared["terminal_stage"] == "RESEARCH_READY"
    assert "B5_I3_HANDOFF" not in prepared
