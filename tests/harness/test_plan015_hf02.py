from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from src.ai.execution import editorial_only_payload
from src.application.contracts import HumanInput
from src.application.research_m7 import ResearchM7SyntheticRunner
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError, VaultEpisodeStore
from tests.core.test_all_schemas import VALID_FIXTURES
from tests.harness.test_plan011_m3_b5_i3 import _cognitive
from tests.harness.test_plan009_p2_roundtrip import _result_for


ROOT = Path(__file__).resolve().parents[2]


class _ResearchReadyWorkflow:
    def preflight(self) -> None:
        return None

    def start(self, handle, human_input, handoff, run_id):
        return {
            "workflow_id": "PLAN015_HF02_FIXTURE_BOUNDARY",
            "status": "LEGITIMATE_STOP",
            "episode_id": handle.episode_id,
            "stop_boundary": "RESEARCH_EXTERNAL_COGNITIVE_SEAM",
            "next_action": "IMPORT_EXTERNAL_COGNITIVE_RESULT",
        }


def _outputs() -> dict[str, dict]:
    audit = editorial_only_payload(copy.deepcopy(VALID_FIXTURES["final_editorial_audit"]), "final_editorial_audit")
    return {
        "viewer_journey": _cognitive("viewer_journey"),
        "opening_design": _cognitive("opening_design"),
        "closing_design": _cognitive("closing_design"),
        "narrative_plan": _cognitive("narrative_plan"),
        "script_draft": {"content": "Un borrador sintético trazable."},
        "edited_script": {"content": "Una edición sintética trazable."},
        "editorial_edit_report": {
            "edit_type": "RESTRUCTURE",
            "changes_by_category": {"structure": ["Reorganizacion del argumento."]},
            "continuity_findings": [],
            "redundancy_findings": [],
            "line_findings": [],
            "orality_findings": [],
            "unresolved_issues": [],
            "invalidated_artifacts": [],
        },
        "final_editorial_audit": audit,
    }


def _service(tmp_path: Path) -> tuple[EpisodeApplicationService, object]:
    store = VaultEpisodeStore(ROOT / ".runtime-tmp" / f"p15-{tmp_path.name[-8:]}" / "v", "CHANNEL")
    service = EpisodeApplicationService(store, workflow=_ResearchReadyWorkflow(), synthetic_outputs=_outputs())
    started = service.start(
        HumanInput.create(
            mode="tema",
            content="Fenómeno sintético controlado",
            initial_question="¿Qué puede sostenerse con evidencia?",
            works=["REAL-A", "REAL-B", "REAL-C"],
            duration_target_minutes=18,
            target_language="es",
        )
    )
    ResearchM7SyntheticRunner(started.episode.folder).run(
        {
            "episode_id": started.episode.episode_id,
            "topic": "Fenómeno sintético controlado",
            "initial_question": "¿Qué puede sostenerse con evidencia?",
            "context": "SYNTHETIC_E2E",
            "works": ["REAL-A", "REAL-B", "REAL-C"],
            "target_final_works": 3,
            "selected_work_ids": ["REAL-A", "REAL-B", "REAL-C"],
        }
    )
    return service, started.episode


def test_plan015_hf02_normal_service_completes_downstream_chain(tmp_path: Path) -> None:
    service, episode = _service(tmp_path)

    result = service.resume(episode.episode_id)
    workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
    manifest = json.loads((episode.folder / "plan015_downstream_manifest.json").read_text(encoding="utf-8"))

    assert result["state"]["status"] == "LEGITIMATE_STOP"
    assert workflow["stop_boundary"] == "FINAL_VALIDATIONS_COMPLETE"
    assert workflow["next_action"] == "REQUEST_HUMAN_APPROVAL"
    assert workflow["human_approval_pending"] is True
    assert workflow["script_lifecycle"]["status"] == "WORKING_CURRENT"
    assert workflow["edited_script_lifecycle"]["status"] == "WORKING_CURRENT"
    assert service.resume(episode.episode_id)["state"]["status"] == "LEGITIMATE_STOP"
    assert set(manifest["artifact_records"]) == {
        "script_draft", "script_version_manifest", "edited_script", "editorial_edit_report",
        "edited_script_version_manifest", "final_editorial_audit", "final_script_review",
    }
    assert not (episode.folder / "editorial_script_approval.json").exists()
    assert not (episode.folder / "plan013_editorial_closure.json").exists()

    handoff_path = Path(workflow["research_v2_b5_i3_handoff_ref"]["path"])
    handoff_path.unlink()
    with pytest.raises(StorageError, match="PLAN015_DOWNSTREAM_RESEARCH_BINDING_STALE"):
        service.resume(episode.episode_id)


def test_plan015_hf02_blocks_stale_research_input_before_b5_i3(tmp_path: Path) -> None:
    service, episode = _service(tmp_path)
    handoff = json.loads((episode.folder / "canonical_g1" / "b5_i3_handoff.json").read_text(encoding="utf-8"))
    stale_path = Path(handoff["b5_i3_input_refs"][0]["path"])
    stale_payload = json.loads(stale_path.read_text(encoding="utf-8"))
    stale_payload["content"] = stale_payload.get("content", "") + " alterado"
    stale_path.write_text(json.dumps(stale_payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(StorageError, match="PLAN015_HF02_BLOCKED"):
        service.resume(episode.episode_id)

    assert not (episode.folder / "06_viewer_journey.json").exists()
    assert not (episode.folder / "plan015_downstream_manifest.json").exists()


def test_plan015_hf02_real_agent_handoff_roundtrip_reaches_final_validations(tmp_path: Path, request) -> None:
    fixture_service, episode = _service(tmp_path)
    handoff_dir = ROOT / "handoff" / f"plan015-{tmp_path.name[-12:]}"
    request.addfinalizer(lambda: shutil.rmtree(handoff_dir, ignore_errors=True))
    service = EpisodeApplicationService(
        fixture_service.store,
        workflow=fixture_service.workflow,
        plan015_handoff_directory=handoff_dir,
    )
    outputs = _outputs()
    ordered_schemas = (
        "viewer_journey",
        "opening_design",
        "closing_design",
        "narrative_plan",
        "script_draft",
        "edited_script",
        "editorial_edit_report",
        "final_editorial_audit",
    )

    pending = service.resume(episode.episode_id)
    for index, schema in enumerate(ordered_schemas, start=1):
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert pending["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        assert workflow["output_schema"] == schema
        package_path = Path(workflow["handoff_package_ref"])
        result_path = _result_for(
            package_path,
            outputs[schema],
            f"PLAN015-REAL-ROUNDTRIP-{index}",
            tmp_path / f"{index:02d}-{schema}.json",
            executor_identity=f"plan015-executor-{index}",
        )
        imported = service.import_result(episode.episode_id, result_path)
        assert imported["state"]["status"] == "LEGITIMATE_STOP"
        if index == 1:
            duplicate = service.import_result(episode.episode_id, result_path)
            assert duplicate["state"]["status"] == "LEGITIMATE_STOP"
        pending = service.resume(episode.episode_id)

    workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
    assert pending["state"]["status"] == "LEGITIMATE_STOP"
    assert workflow["stop_boundary"] == "FINAL_VALIDATIONS_COMPLETE"
    assert workflow["next_action"] == "REQUEST_HUMAN_APPROVAL"
    assert (episode.folder / "plan015_downstream_manifest.json").is_file()
