from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from src.ai.contracts import ExecutionRequest, ExecutionStatus, InputArtifact
from src.ai.execution import editorial_only_payload, execute
from src.ai.role_execution import RoleExecutionContractError, resolve_role_execution_contract
from src.ai.runtime_profiles import AgentRuntimePort
from src.application.plan013_script_coordinator import ScriptCoordinatorError, coordinate_script_pipeline
from src.application.contracts import HumanInput
from src.application.research_m7 import ResearchM7SyntheticRunner
from src.application.research_m7 import PersistedResearchEpisode
from src.application.storage import VaultEpisodeStore
from src.core.final_script_review import build_final_script_review
from src.core.status import GateStatus
from src.scripts.evidence_sufficiency_gate import evaluate as evaluate_evidence
from tests.core.test_all_schemas import VALID_FIXTURES
from tests.harness.test_b5_i1_editorial_input import valid_report
from tests.harness.test_plan011_m3_b5_i3 import _cognitive, _inputs


ACTIVE_PROFILE_CHECKSUM = json.loads(
    (Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json").read_text(encoding="utf-8")
)["profile_checksum"]


def _canonical_checksum(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_plan013_cp01_unavailable_evidence_is_blocked_before_positive_evaluation(tmp_path) -> None:
    report = valid_report()
    report["tipo_de_acceso"] = "UNAVAILABLE"
    report_path = tmp_path / "unavailable_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = evaluate_evidence(report_path, "EP-PLAN013")
    assert result.status is GateStatus.BLOCKED
    assert result.exit_code != 0


def test_plan013_remaining_minimum_negative_cases_are_deterministic(tmp_path) -> None:
    profile = json.loads((Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json").read_text(encoding="utf-8"))
    store = VaultEpisodeStore(tmp_path / "v", "C")
    human = HumanInput.create(mode="tema", content="Tema derivable", initial_question="¿Qué puede sostenerse?")
    handle = store.create_episode(human, handoff={"target_contract": "topic_belonging_input"}, profile=profile, run_id="RUN-DERIVED-PLAN013", slug_override="derived")
    persisted = PersistedResearchEpisode.load(store, handle.episode_id)
    assert persisted.brief["objetivo"] == "RESEARCH_AND_THESIS"
    assert persisted.brief["intended_use_resolution"] == {
        "value": "RESEARCH_AND_THESIS",
        "origin": "DERIVED_STANDARD",
        "reference": f"human-input:{handle.episode_id}",
    }

    research = ResearchM7SyntheticRunner(tmp_path / "research").run({
        "episode_id": handle.episode_id, "topic": "Tema derivable", "initial_question": "¿Qué puede sostenerse?",
        "context": "SYNTHETIC_E2E", "works": ["REAL-A", "REAL-B", "REAL-C"], "target_final_works": 3,
        "selected_work_ids": ["REAL-A", "REAL-B", "REAL-C"],
    })
    m6_ref = next(item for item in research["artifacts"] if item["stage"] == "M6")
    m6 = json.loads(Path(m6_ref["path"]).read_text(encoding="utf-8"))
    assert m6["research_ready_state"] != "NOT_RESEARCH_READY"
    b2_manifest_ref = next(item for item in research["artifacts"] if item["stage"] == "B2")
    b2_manifest = json.loads(Path(b2_manifest_ref["path"]).read_text(encoding="utf-8"))
    pack_ref = next(item for item in b2_manifest["artifacts"] if item["artifact_kind"] == "ResearchPack")
    pack = json.loads(Path(pack_ref["path"]).read_text(encoding="utf-8"))
    source_status = {item["source_id"]: item["retrieval_status"] for item in pack["source_registry"]}
    assert source_status["S1"] == "RECOVERED"
    assert source_status["SUGGESTED_ONLY"] == "NOT_RECOVERED"
    assert "SUGGESTED_ONLY" not in pack["evidence_type_separation"]["external_reality_evidence_refs"]

    with pytest.raises(ValueError, match="route"):
        AgentRuntimePort().resolve("WRITING", "missing_route")
    with pytest.raises(RoleExecutionContractError, match="required context"):
        resolve_role_execution_contract(
            "FINAL_EDITORIAL_AUDITOR", "final_editorial_audit",
            {"edited_script": {}, "EditorialEditReport": {}, "editorial_profile": {}, "brief": {}, "claims_ledger": {}},
            {"required_context": {"clean_session": "true"}},
        )

    execution_profiles = json.loads((Path(__file__).resolve().parents[2] / "config" / "agent_execution_profiles.json").read_text(encoding="utf-8"))
    for provider_id, provider in execution_profiles["providers"].items():
        if provider["route_type"] == "API_MODEL_RUNTIME":
            assert provider["api_base_env"] and provider["api_key_env"] and provider["model_env"]
            assert "base_url_env" not in provider
    assert execution_profiles["providers"]["openai"]["adapter"] == "openai_compatible"
    resolved = AgentRuntimePort().resolve("WRITING", "api_model")
    assert resolved.route_type == "API_MODEL_RUNTIME" and resolved.api_base_env


def test_plan013_persisted_explicit_intended_use_wins_over_standard_derivation(tmp_path) -> None:
    profile = json.loads((Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json").read_text(encoding="utf-8"))
    store = VaultEpisodeStore(tmp_path / "v", "C")
    human = HumanInput.create(mode="tema", content="Tema explícito")
    handle = store.create_episode(
        human,
        handoff={"target_contract": "topic_belonging_input", "intended_use": "OWNER_DECLARED_RESEARCH"},
        profile=profile,
        run_id="RUN-EXPLICIT-PLAN013",
        slug_override="explicit",
    )
    persisted = PersistedResearchEpisode.load(store, handle.episode_id)
    assert persisted.brief["intended_use_resolution"] == {
        "value": "OWNER_DECLARED_RESEARCH",
        "origin": "OWNER_EXPLICIT",
        "reference": f"human-input:{handle.episode_id}",
    }


def test_plan013_synthetic_path_keeps_one_script_identity_to_youtube_review() -> None:
    checksum = "a" * 64
    thesis = {"thesis_id": "T-1", "episode_id": "EP-1", "artifact_version": "1.0.0", "checksum": "b" * 64}
    binding = {"thesis_id": "T-1", "artifact_version": "1.0.0", "checksum": "b" * 64}
    draft = {
        "script_id": "SCRIPT-DRAFT-1", "episode_id": "EP-1", "artifact_version": "1.0.0",
        "content": "Borrador sintético.", "checksum": checksum, "narrative_plan_ref": "PLAN-1",
        "thesis_binding": binding, "created_at": "2026-09-01T00:00:00Z",
    }
    edited = {
        "script_id": "SCRIPT-EDITED-1", "episode_id": "EP-1", "artifact_version": "1.1.0",
        "content": "Edición sintética.", "checksum": "c" * 64, "source_script_version": "1.0.0",
        "edit_report_ref": "EDIT-1", "thesis_binding": binding, "created_at": "2026-09-01T00:00:00Z",
    }
    audit = {
        "episode_id": "EP-1", "artifact_id": "SCRIPT-EDITED-1", "script_version": "1.1.0",
        "script_checksum": "c" * 64, "auditor_run_id": "RUN-AUDIT-1", "independence_result": "PASS",
        "profile_compliance": "PASS", "brief_compliance": "PASS", "packaging_promise_compliance": "PASS",
        "evidence_sufficiency": "PASS", "thesis_quality": "PASS", "viewer_journey": "PASS",
        "opening_quality": "PASS", "progression": "PASS", "coherence": "PASS", "originality": "PASS",
        "source_transformation": "PASS", "voice": "PASS", "orality": "PASS", "closing_quality": "PASS",
        "factual_traceability": "PASS", "decision": "PASS", "correction_route": "NONE",
        "decision_basis": "Evaluacion cualitativa sustentada en el guion y sus artifacts de entrada.",
        "dimension_evidence": {
            field: {"observation": "Fixture cualitativo para validacion de contrato."}
            for field in (
                "profile_compliance", "brief_compliance", "packaging_promise_compliance",
                "evidence_sufficiency", "thesis_quality", "viewer_journey", "opening_quality",
                "progression", "coherence", "originality", "source_transformation", "voice",
                "orality", "closing_quality", "factual_traceability",
            )
        },
    }
    report = {
        "episode_id": "EP-1", "input_artifact_id": draft["script_id"], "input_checksum": checksum,
        "output_artifact_id": edited["script_id"], "output_checksum": edited["checksum"],
        "input_version": "1.0.0", "output_version": "1.1.0", "edit_type": "RESTRUCTURE",
            "changes_by_category": {"structure": ["Reorganizacion del argumento."]}, "continuity_findings": [], "redundancy_findings": [],
        "line_findings": [], "orality_findings": [], "unresolved_issues": [], "invalidated_artifacts": [],
    }
    final_review = build_final_script_review(
        review_id="FSR-1", episode_id="EP-1", artifact_id=edited["script_id"],
        script_version=edited["artifact_version"], script_checksum=edited["checksum"],
        profile_reference={"profile_id": "mas_alla_del_guion", "profile_version": "1.2.2", "profile_checksum": ACTIVE_PROFILE_CHECKSUM},
        visible_promise_ref="editorial_script_promise:SP-1@1.0.0",
        final_audit_ref="final_editorial_audit:SCRIPT-EDITED-1@1.1.0", estimated_minutes=18.0,
        final_audit_checksum="d" * 64, review_run_id="RUN-YT-REVIEW-1", producer_run_id="RUN-WRITING-1", editor_run_id="RUN-EDITOR-1", auditor_run_id="RUN-AUDIT-1", review_actor_id="YOUTUBE_ADAPTATION_AUDITOR", producer_actor_id="WRITING", editor_actor_id="EDITOR", auditor_actor_id="FINAL_EDITORIAL_AUDITOR", target_range=(18, 22), created_at="2026-09-01T00:00:00Z",
    )
    trace = coordinate_script_pipeline(
        episode_id="EP-1", narrative_plan={"episode_id": "EP-1", "script_plan_id": "PLAN-1"},
        thesis_artifact=thesis, script_draft=draft, edited_script=edited, edit_report=report,
        final_audit=audit, producer_run_id="RUN-WRITING-1", editor_run_id="RUN-EDITOR-1", auditor_run_id="RUN-AUDIT-1",
    )
    assert trace["status"] == "HANDOFF_READY"
    assert final_review["artifact_id"] == trace["stages"][2]["artifact_ref"]
    assert final_review["script_checksum"] == edited["checksum"]
    assert final_review["decision"] == "PASS"


def test_plan013_integrated_synthetic_e2e_from_human_intake_to_convergent_close(tmp_path, monkeypatch) -> None:
    """Execute every PLAN013 stage with a synthetic cognitive provider."""
    store = VaultEpisodeStore(tmp_path / "v", "C")
    human = HumanInput.create(mode="tema", content="Fenómeno sintético controlado")
    active_profile = json.loads((Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json").read_text(encoding="utf-8"))
    handle = store.create_episode(human, handoff={"target_contract": "topic_belonging_input", "intended_use": "RESEARCH_AND_THESIS"}, profile=active_profile, run_id="RUN-HUMAN-PLAN013", slug_override="e2e")
    persisted = PersistedResearchEpisode.load(store, handle.episode_id)
    assert persisted.brief["objetivo"] == "RESEARCH_AND_THESIS"
    research = ResearchM7SyntheticRunner(tmp_path / "research").run({
        "episode_id": handle.episode_id, "topic": "Fenómeno sintético controlado", "initial_question": "¿Qué puede afirmarse con evidencia?", "context": "SYNTHETIC_E2E", "works": ["REAL-A", "REAL-B", "REAL-C"], "target_final_works": 3, "selected_work_ids": ["REAL-A", "REAL-B", "REAL-C"],
    })
    assert research["research_vertical_e2e"] == "PASS"
    monkeypatch.setattr("src.ai.execution.preflight_controlled_execution", lambda request, root: {"authorization": None, "mission_contract": None})
    b5_root = tmp_path / "b5"; b5_root.mkdir()
    b5_inputs = _inputs(b5_root, handle.episode_id, duration_target=18)
    thesis_source = next(item.path for item in b5_inputs if item.artifact_kind == "refined_thesis")
    thesis = json.loads(thesis_source.read_text(encoding="utf-8"))
    thesis_artifact_path = b5_root / "thesis_artifact.json"; thesis_artifact_path.write_text(json.dumps(thesis), encoding="utf-8")
    narrative_plan_payload = _cognitive("narrative_plan")
    for block in narrative_plan_payload["blocks"]:
        block["word_budget"] = 1
    narrative_plan_payload["blocks"][-1]["word_budget"] = 2700 - len(narrative_plan_payload["blocks"]) + 1
    b5_result = execute(ExecutionRequest(
        capability_id="B5_I3_NARRATIVE_ARCHITECTURE", skill_id="skill_mapa_eventos_y_outline", skill_version="1.0.0", input_artifacts=b5_inputs, output_schema="narrative_plan", execution_mode="SYNTHETIC_TEST", provider="mock", mock_output=narrative_plan_payload, output_artifact_id="PLAN-PLAN013", episode_id=handle.episode_id, role="NARRATIVE_ARCHITECTURE", config={"repository_root": str(tmp_path), "wpm_target": 150},
    ))
    assert b5_result.status is ExecutionStatus.SUCCEEDED, b5_result.error
    narrative_plan = b5_result.output
    plan_path = tmp_path / "narrative_plan.json"; plan_path.write_text(json.dumps(narrative_plan), encoding="utf-8")

    def run_stage(role: str, schema: str, inputs: list[InputArtifact], mock: dict, artifact_id: str, config: dict | None = None):
        result = execute(ExecutionRequest(
            capability_id=f"PLAN013_{role}_{schema}", skill_id=f"plan013-{schema}", skill_version="1.0.0", input_artifacts=inputs, output_schema=schema, execution_mode="SYNTHETIC_TEST", provider="mock", mock_output=mock, output_artifact_id=artifact_id, episode_id=handle.episode_id, role=role, config={"repository_root": str(tmp_path), **(config or {})},
        ))
        assert result.status is ExecutionStatus.SUCCEEDED, result.error
        return result

    resolve_role_execution_contract("WRITING", "script_draft", {"narrative_plan": narrative_plan, "thesis_artifact": thesis, "editorial_profile": {}, "research_pack": {}}, {"required_context": {"active_profile_identity": "profile", "voice_guidelines": "voice"}})
    writing = run_stage("WRITING", "script_draft", [InputArtifact("narrative_plan", "PLAN-PLAN013", plan_path, "RUN-B5-PLAN013"), InputArtifact("thesis_artifact", thesis["thesis_id"], thesis_artifact_path, "RUN-RESEARCH-PLAN013")], {"content": "Borrador sintético trazable."}, "SCRIPT-DRAFT-PLAN013")
    draft_path = tmp_path / "script_draft.json"; draft_path.write_text(json.dumps(writing.output), encoding="utf-8")
    draft = writing.output
    resolve_role_execution_contract("EDITOR", "edited_script", {"script_draft": draft, "editorial_profile": {}, "brief": {}, "claims_ledger": {}}, {"required_context": {"editorial_voice_profile": "voice", "quality_criteria": "quality"}})
    editing = run_stage("EDITOR", "edited_script", [InputArtifact("script_draft", draft["script_id"], draft_path, writing.run_id), InputArtifact("thesis_artifact", thesis["thesis_id"], thesis_artifact_path, "RUN-RESEARCH-PLAN013")], {"content": "Edición sintética trazable."}, "SCRIPT-EDITED-PLAN013", {"artifact_version": "1.1.0", "edit_report_ref": "editorial_edit_report:EDIT-PLAN013@1.1.0"})
    edited_path = tmp_path / "edited_script.json"; edited_path.write_text(json.dumps(editing.output), encoding="utf-8")
    edited = editing.output
    report_result = run_stage("EDITOR", "editorial_edit_report", [InputArtifact("script_draft", draft["script_id"], draft_path, writing.run_id), InputArtifact("edited_script", edited["script_id"], edited_path, editing.run_id)], {"edit_type": "RESTRUCTURE", "changes_by_category": {"structure": ["Reorganizacion del argumento."]}, "continuity_findings": [], "redundancy_findings": [], "line_findings": [], "orality_findings": [], "unresolved_issues": [], "invalidated_artifacts": []}, "EDIT-PLAN013")
    report_path = tmp_path / "editorial_edit_report.json"; report_path.write_text(json.dumps(report_result.output), encoding="utf-8")
    report = report_result.output
    audit = editorial_only_payload(copy.deepcopy(VALID_FIXTURES["final_editorial_audit"]), "final_editorial_audit")
    final_audit_result = run_stage("FINAL_EDITORIAL_AUDITOR", "final_editorial_audit", [InputArtifact("edited_script", edited["script_id"], edited_path, editing.run_id), InputArtifact("EditorialEditReport", "EDIT-PLAN013", report_path, report_result.run_id)], audit, "AUDIT-PLAN013", {"independence_verified": True})
    final_audit = final_audit_result.output
    resolve_role_execution_contract("YOUTUBE_ADAPTATION_AUDITOR", "final_script_review", {"youtube_adaptation_b5_i2_package": {}, "producer_run_reference": writing.run_id, "active_editorial_profile_reference": active_profile, "refined_thesis": thesis, "claims_ledger": {}, "evidence_report": {}}, {"clean_session": True, "required_context": {"audit_criteria": "criteria", "profile_identity": "profile", "rules of producer/auditor independence": "independence-rules", "límites de publicación": "publication-limits"}})
    audit_path = tmp_path / "final_editorial_audit.json"; audit_path.write_text(json.dumps(final_audit), encoding="utf-8")
    final_review_result = run_stage("YOUTUBE_ADAPTATION_AUDITOR", "final_script_review", [InputArtifact("edited_script", edited["script_id"], edited_path, editing.run_id), InputArtifact("final_editorial_audit", edited["script_id"], audit_path, final_audit_result.run_id)], {"evidence_refs": [], "lexical_sensor": {"status": "PASS", "findings": [], "normative": False}, "duration_telemetry": {"status": "MEASURED", "estimated_minutes": 18.0, "target_range": [18, 22], "normative": False}, "authenticity": "PASS", "reuse_context": "PASS", "decision": "PASS", "decision_basis": []}, "FSR-PLAN013", {"producer_run_id": writing.run_id, "editor_run_id": editing.run_id, "auditor_run_id": final_audit_result.run_id, "review_actor_id": "YOUTUBE_ADAPTATION_AUDITOR", "producer_actor_id": "WRITING", "editor_actor_id": "EDITOR", "auditor_actor_id": "FINAL_EDITORIAL_AUDITOR", "visible_promise_ref": "editorial_script_promise:SP-1@1.0.0"})
    final_review = final_review_result.output
    trace = coordinate_script_pipeline(episode_id=handle.episode_id, narrative_plan=narrative_plan, thesis_artifact={**thesis, "artifact_version": "1.0.0", "checksum": hashlib.sha256(thesis_artifact_path.read_bytes()).hexdigest()}, script_draft=draft, edited_script=edited, edit_report=report, final_audit=final_audit, producer_run_id=writing.run_id, editor_run_id=editing.run_id, auditor_run_id=final_audit_result.run_id)
    assert trace["status"] == "HANDOFF_READY"
    closure = {"episode_id": handle.episode_id, "script_artifact_id": edited["script_id"], "script_version": edited["artifact_version"], "script_checksum": edited["checksum"], "final_audit": final_audit, "final_script_review": final_review, "human_approval": {"decision": "APPROVED", "script_version": edited["artifact_version"], "checksum": edited["checksum"]}, "closed_at": "2026-09-01T00:00:00Z"}
    closure_path = tmp_path / "closure.json"; closure_path.write_text(json.dumps(closure), encoding="utf-8")
    config_path = tmp_path / "settings.json"; config_path.write_text(json.dumps({"vault_root": str(tmp_path / "v"), "channel_id": "C"}), encoding="utf-8")
    from src.scripts import cerrar_episodio
    monkeypatch.setattr("sys.argv", ["cerrar_episodio.py", "--ep-id", handle.episode_id, "--config", str(config_path), "--plan013-closure", str(closure_path), "--output-root", str(tmp_path / "out")])
    assert cerrar_episodio.main() == 0
    assert store.resume(handle.episode_id)["entry"]["application_status"] == "EDITORIAL_SCRIPT_APPROVED"
    assert cerrar_episodio.main() == 0
    store.register_plan013_script_version(handle, script_artifact_id="SCRIPT-EDITED-PLAN013-V2", script_version="2.0.0", script_checksum="d" * 64)
    resumed = store.resume(handle.episode_id)
    assert resumed["state"]["status"] == "IN_REVIEW"
    assert resumed["state"]["approval_status"] == "STALE"
