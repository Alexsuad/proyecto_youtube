from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from src.ai.providers.agent_handoff import checksum, canonical_json
from src.application.service import EpisodeApplicationService
from src.application.storage import VaultEpisodeStore
from src.application.topic_belonging import ExecutionCognitiveBoundary, TopicBelongingTechnicalWorkflow
from tests.harness.test_plan009_p2_roundtrip import (
    _cognitive_assessment,
    _cognitive_decision,
    _cognitive_proposal,
    _human_input,
    _materialized_producer_assessment,
    _materialized_topic_input,
    _result_for,
)
from tests.harness.test_plan012_m7_b5 import _research_plan_proposal


ROOT = Path(__file__).resolve().parents[2]


def _product_service(tmp_path: Path) -> EpisodeApplicationService:
    # Keep the Windows path comfortably below MAX_PATH; tmp_path names are
    # intentionally descriptive and therefore too long for nested episode
    # artifacts.
    vault_root = ROOT / ".runtime-tmp" / f"plan015-hf01-{tmp_path.name[-8:]}" / "vault"
    store = VaultEpisodeStore(vault_root, "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        execution_mode="REAL",
        execution_family="AGENT_HARNESS",
        execution_interface="TOPIC_BELONGING_TERMINAL",
        handoff_directory=ROOT / "handoff",
        authorization_mode="PRODUCT",
    )
    workflow = TopicBelongingTechnicalWorkflow(store, boundary=boundary)
    return EpisodeApplicationService(store, workflow=workflow)


def _handoff_path(episode: object) -> Path:
    folder = episode.folder
    workflow = json.loads((folder / "workflow_state.json").read_text(encoding="utf-8"))
    return Path(workflow["handoff_package_ref"])


def _reach_topic_decision(
    tmp_path: Path,
    decision_name: str,
    *,
    valid_conditions: bool = False,
) -> tuple[EpisodeApplicationService, object]:
    service = _product_service(tmp_path)
    started = service.start(_human_input())
    episode = started.episode
    enrichment_package = _handoff_path(episode)
    enrichment = _cognitive_proposal()
    service.import_result(
        episode.episode_id,
        _result_for(enrichment_package, enrichment, "HF01-TOPIC-ENRICHMENT", tmp_path / "enrichment.json"),
    )
    service.resume(episode.episode_id)
    producer_package = _handoff_path(episode)
    topic_input = _materialized_topic_input(episode)
    service.import_result(
        episode.episode_id,
        _result_for(
            producer_package,
            _cognitive_assessment(topic_input, "HF01-TOPIC-PRODUCER"),
            "HF01-TOPIC-PRODUCER",
            tmp_path / "producer.json",
        ),
    )
    service.resume(episode.episode_id)
    reviewer_package = _handoff_path(episode)
    assessment = _materialized_producer_assessment(episode)
    decision_payload = _cognitive_decision(assessment, decision_name)
    if valid_conditions:
        evidence = {
            "work_lifecycle": {
                "lifecycle_id": "WL-001",
                "lifecycle_version": "1.0.0",
                "episode_id": episode.episode_id,
                "anchor_work_id": None,
                "entry_mode": "TOPIC_FIRST",
                "research_id": "RP-001",
                "works": [
                    {
                        "work_id": work_id,
                        "state": "DISCOVERED_WORK",
                        "state_version": "1.0.0",
                        "identity_ref": f"candidate:{work_id}",
                        "version_ref": None,
                        "is_anchor": False,
                        "lineage_refs": ["candidate-set:RP-001"],
                        "stage_evidence_refs": [],
                    }
                    for work_id in ["M1", "M2", "M3", "M4", "M5"]
                ],
                "transitions": [],
                "screening": {
                    "candidate_work_ids": ["M1", "M2", "M3", "M4", "M5"],
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
                "created_at": "2026-09-15T20:00:00Z",
            },
            "research_dossier": {
                "dossier_id": "WRD-001",
                "dossier_version": "1.0.0",
                "episode_id": episode.episode_id,
                "research_id": "RP-001",
                "work": {
                    "material_id": "M1",
                    "title": "Obra de prueba",
                    "creator": "Creador de prueba",
                    "consulted_representations": [{
                        "representation_kind": "ORIGINAL_WORK",
                        "edition_or_version": "1.0",
                        "consulted_locator": "fixture://work/M1",
                    }],
                },
                "dossier_stage": "IDENTIFIED",
                "pending_items": [],
                "confidence": "LOW",
                "evidence_report_id": "ER-001",
                "created_at": "2026-09-15T20:00:00Z",
            },
        }
        refs = []
        for kind, payload in evidence.items():
            path = episode.folder / f"topic_condition_{kind}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            refs.append(
                {
                    "kind": kind,
                    "path": f"episode:{episode.episode_id}/{path.name}",
                    "checksum": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        decision_payload["conditions"] = [{"condition_id": "C-001", "evidence_refs": refs}]
    service.import_result(
        episode.episode_id,
        _result_for(
            reviewer_package,
            decision_payload,
            "HF01-TOPIC-REVIEWER",
            tmp_path / "reviewer.json",
        ),
    )
    return service, episode


def test_plan015_hf01_product_topic_to_research_roundtrip(tmp_path: Path) -> None:
    handoff_directory = ROOT / "handoff"
    before = set(handoff_directory.glob("*.json")) if handoff_directory.is_dir() else set()
    try:
        service, episode = _reach_topic_decision(tmp_path, "APPROVE")
        stopped = service.resume(episode.episode_id)

        workflow_path = episode.folder / "workflow_state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        research_handoff_path = episode.folder / "research_external_handoff.json"
        research_handoff = json.loads(research_handoff_path.read_text(encoding="utf-8"))
        research_package_path = Path(research_handoff["handoff_package_ref"])
        research_package = json.loads(research_package_path.read_text(encoding="utf-8"))

        assert stopped["state"]["status"] == "LEGITIMATE_STOP"
        assert workflow["status"] == "LEGITIMATE_STOP"
        assert workflow["stop_boundary"] == "RESEARCH_EXTERNAL_COGNITIVE_SEAM"
        assert workflow["next_action"] == "IMPORT_EXTERNAL_COGNITIVE_RESULT"
        assert research_handoff["status"] == "PENDING_EXTERNAL_COGNITIVE_RESULT"
        assert research_handoff["stage"] == "RESEARCH_PLANNING"
        assert research_package["capability_id"] == "EXTEND_01_RESEARCH_V2_REAL_E2E"
        assert research_package["execution_family"] == "AGENT_HARNESS"
        assert research_package["selection_mode"] == "EXECUTOR_MANAGED"
        assert research_package["profile_binding"] == "EXECUTOR_MANAGED"
        assert research_package["model_override"] is None
        assert research_package["authorization_mode"] == "PRODUCT"
        assert research_package["authorization_id"] == "PCA-PLAN015-RESEARCH-001"
        assert "mission_id" not in research_package
        for name in ("episode_state.json", "workflow_state.json", "topic_belonging_lineage.json", "roundtrip_results.json"):
            persisted = json.loads((episode.folder / name).read_text(encoding="utf-8"))
            records = persisted if isinstance(persisted, list) else [persisted]
            assert all("mission_id" not in record for record in records if isinstance(record, dict))
        assert json.loads((episode.folder / "episode_state.json").read_text(encoding="utf-8"))["authorization_id"] == "PCA-PLAN015-TOPIC-001"
        assert json.loads((episode.folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))["authorization_id"] == "PCA-PLAN015-TOPIC-001"
        roundtrip_records = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"]
        assert all(record["authorization_id"] == "PCA-PLAN015-TOPIC-001" for record in roundtrip_records)

        topic_results_before = (episode.folder / "roundtrip_results.json").read_bytes()
        research_package_before = research_package_path.read_bytes()
        resumed = service.resume(episode.episode_id)
        reloaded_service = _product_service(tmp_path)
        recovered = reloaded_service.resume(episode.episode_id)
        assert resumed["state"]["status"] == recovered["state"]["status"] == "LEGITIMATE_STOP"
        assert (episode.folder / "roundtrip_results.json").read_bytes() == topic_results_before
        assert research_package_path.read_bytes() == research_package_before

        proposal = _research_plan_proposal()
        result_path = tmp_path / "research-planning-result.json"
        result_path.write_text(
            json.dumps(
                {
                    "handoff_id": research_package["handoff_id"],
                    "authorization_mode": research_package["authorization_mode"],
                    "authorization_id": research_package["authorization_id"],
                    "episode_id": research_package["episode_id"],
                    "capability_id": research_package["capability_id"],
                    "stage": research_package["stage"],
                    "role": research_package["role"],
                    "result_run_id": "HF01-RESEARCH-PLANNING",
                    "package_checksum": research_package["package_checksum"],
                    "input_manifest_checksum": research_package["input_manifest_checksum"],
                    "skill_id": research_package["skill_id"],
                    "skill_version": research_package["skill_version"],
                    "output": proposal,
                    "output_checksum": checksum(canonical_json(proposal)),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        continued = reloaded_service.import_result(episode.episode_id, result_path)
        continued_state = json.loads(research_handoff_path.read_text(encoding="utf-8"))
        next_package_path = Path(continued_state["handoff_package_ref"])
        next_package = json.loads(next_package_path.read_text(encoding="utf-8"))
        assert continued["state"]["status"] == "LEGITIMATE_STOP"
        assert continued_state["completed_stages"] == ["RESEARCH_PLANNING"]
        assert next_package["stage"] != "RESEARCH_PLANNING"
        assert next_package["authorization_mode"] == "PRODUCT"
    finally:
        if handoff_directory.is_dir():
            for path in handoff_directory.glob("*.json"):
                if path not in before:
                    path.unlink(missing_ok=True)
            if not any(handoff_directory.iterdir()):
                handoff_directory.rmdir()
        shutil.rmtree(ROOT / ".runtime-tmp" / f"plan015-hf01-{tmp_path.name[-8:]}", ignore_errors=True)


def test_plan015_approve_with_conditions_without_durable_evidence_stops(tmp_path: Path) -> None:
    handoff_directory = ROOT / "handoff"
    before = set(handoff_directory.glob("*.json")) if handoff_directory.is_dir() else set()
    try:
        service, episode = _reach_topic_decision(tmp_path, "APPROVE_WITH_CONDITIONS")
        stopped = service.resume(episode.episode_id)
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert stopped["state"]["status"] == "LEGITIMATE_STOP"
        assert workflow["stop_boundary"] == "TOPIC_CONDITIONS_PENDING"
        assert workflow["next_action"] == "RESOLVE_TOPIC_CONDITIONS"
        assert workflow["topic_conditions_status"] == "PENDING"
        assert not (episode.folder / "research_external_handoff.json").exists()
        assert service.resume(episode.episode_id)["state"]["status"] == "LEGITIMATE_STOP"
    finally:
        if handoff_directory.is_dir():
            for path in handoff_directory.glob("*.json"):
                if path not in before:
                    path.unlink(missing_ok=True)
            if not any(handoff_directory.iterdir()):
                handoff_directory.rmdir()
        shutil.rmtree(ROOT / ".runtime-tmp" / f"plan015-hf01-{tmp_path.name[-8:]}", ignore_errors=True)


def test_plan015_approve_with_conditions_with_durable_evidence_opens_research_seam(tmp_path: Path) -> None:
    handoff_directory = ROOT / "handoff"
    before = set(handoff_directory.glob("*.json")) if handoff_directory.is_dir() else set()
    try:
        service, episode = _reach_topic_decision(
            tmp_path,
            "APPROVE_WITH_CONDITIONS",
            valid_conditions=True,
        )
        stopped = service.resume(episode.episode_id)
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        resolution_path = episode.folder / "topic_conditions_resolution.json"
        assert resolution_path.is_file(), {
            key: workflow.get(key)
            for key in ("status", "stop_boundary", "next_action", "topic_conditions_status", "topic_conditions")
        }
        resolution = json.loads(resolution_path.read_text(encoding="utf-8"))
        assert stopped["state"]["status"] == "LEGITIMATE_STOP"
        assert workflow["stop_boundary"] == "RESEARCH_EXTERNAL_COGNITIVE_SEAM"
        assert workflow["topic_conditions_status"] == "SATISFIED"
        assert resolution["status"] == "SATISFIED"
        assert (episode.folder / "research_external_handoff.json").is_file()
    finally:
        if handoff_directory.is_dir():
            for path in handoff_directory.glob("*.json"):
                if path not in before:
                    path.unlink(missing_ok=True)
            if not any(handoff_directory.iterdir()):
                handoff_directory.rmdir()
        shutil.rmtree(ROOT / ".runtime-tmp" / f"plan015-hf01-{tmp_path.name[-8:]}", ignore_errors=True)
