from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute, persist_execution_result
from src.ai.registry import load_registry
from src.ai.subagents import assert_no_self_approval, assert_not_immutable_target, get_agent_definition
from src.core.contract_validation import validate_against_schema
from tests.ai.test_hybrid_runtime import _completion_gate_config

ROOT = Path(__file__).parents[2]
R6_ROLE_IDS = [
    "SCRIPT_PRODUCT_PRODUCER",
    "SCRIPT_PRODUCT_AUDITOR",
    "YOUTUBE_ADAPTATION_PRODUCER",
    "YOUTUBE_ADAPTATION_AUDITOR",
]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_provenance_schema_supports_r6_registry_file() -> None:
    data = _read_json(ROOT / "output" / "execution_provenance_registry.json")
    violations = validate_against_schema(data, "execution_provenance_registry")
    assert not violations

def test_r6_prompt_registry_entries_and_files_exist() -> None:
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    roles = {item["role_id"] for item in registry["prompts"]}
    for role_id in R6_ROLE_IDS:
        assert role_id in roles
        entry = next(item for item in registry["prompts"] if item["role_id"] == role_id)
        assert entry["status"] == "ACTIVE"
        prompt_file = ROOT / "prompts" / "roles" / role_id / f"{entry['prompt_version']}.md"
        assert prompt_file.exists()


def test_r6_prompt_text_mentions_active_profile_and_forbids_silent_modification() -> None:
    for role_id in R6_ROLE_IDS:
        content = (ROOT / "prompts" / "roles" / role_id / "1.0.0.md").read_text(encoding="utf-8").lower()
        assert "config/active_editorial_profile.json" in content
        assert "exact" in content or "exacto" in content
        assert "subagentes anidados" in content
        if "AUDITOR" in role_id:
            assert "modificar silenciosamente" in content
            assert "autoaprobar" in content


def test_r6_subagent_registry_uses_agent_handoff_and_is_not_activatable() -> None:
    expected_maturity = {
        "SCRIPT_PRODUCT_PRODUCER": "AGENT_IMPLEMENTED",
        "SCRIPT_PRODUCT_AUDITOR": "AGENT_IMPLEMENTED",
        "YOUTUBE_ADAPTATION_PRODUCER": "AGENT_TESTED_IN_ISOLATION",
        "YOUTUBE_ADAPTATION_AUDITOR": "AGENT_TESTED_IN_ISOLATION",
    }
    for role_id in R6_ROLE_IDS:
        agent = get_agent_definition(role_id)
        assert agent["provider"] == "agent_handoff"
        assert agent["model"] == "handoff_only"
        assert agent["maturity_status"] == expected_maturity[role_id]
        assert agent["synthetic_policy"]["can_authorize_readiness"] is False
        assert agent["provenance"]["registry_path"] == "output/execution_provenance_registry.json"
        assert any("subagentes anidados" in item for item in agent["failure_conditions"])

def test_append_result_records_extended_r6_provenance_fields(tmp_path: Path) -> None:
    source = _artifact(tmp_path, "research.json", {"id": "R-1", "content": "evidencia"})
    output_path = _artifact(tmp_path, "analysis.json", {"analysis_id": "A-1", "episode_id": "EP-1", "research_id": "RP-1", "evidence_report_id": "ER-1", "semantic_audit_id": "SSA-1", "material_id": "M-1", "analysis_summary": "texto"})
    request = ExecutionRequest(
        capability_id="SCRIPT_PRODUCT_PRODUCER",
        skill_id="skill_analysis",
        skill_version="1.0.0",
        input_artifacts=[InputArtifact("research", "R-1", source, "RUN-R")],
        output_schema="narrative_human_analysis",
        execution_mode="mock",
        provider="mock",
        episode_id="EP-1",
        role="SCRIPT_PRODUCT_PRODUCER",
        config={"prompt_version": "1.0.0", "handoff_target": "SCRIPT_PRODUCT_AUDITOR", "mission_id": "M-R6", "execution_profile_id": "PROFILE-R6", "mission_contract_sha256": "a" * 64, "resolved_context_manifest_sha256": "b" * 64, "input_sha256": "c" * 64, "prompt_artifact_sha256": "d" * 64},
        mock_output=_read_json(output_path),
        output_artifact_kind="analysis",
        output_artifact_id="A-1",
        output_artifact_path=output_path,
        output_artifact_ref="analysis:A-1",
    )
    result = ExecutionResult(
        run_id="RUN-R6-1",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="agent_handoff",
        model="handoff_only",
        input_manifest_checksum="a" * 64,
        output=_read_json(output_path),
        output_checksum=hashlib.sha256(output_path.read_bytes()).hexdigest(),
        started_at="2026-07-29T10:00:00Z",
        completed_at="2026-07-29T10:00:05Z",
        usage={"skill_id": "skill_analysis", "skill_version": "1.0.0", "prompt_version": "1.0.0", "retry_count": 0, "input_tokens": 12, "output_tokens": 7, "cost": 0.25, "currency": "EUR", "actual_provider": "provider-x", "actual_model": "model-y"},
        episode_id="EP-1",
        output_artifact_id="A-1",
        output_artifact_kind="analysis",
        output_artifact_path=output_path,
        output_artifact_ref="analysis:A-1",
        is_real_editorial_execution=False,
    )
    registry_path = tmp_path / "registry.json"
    persist_execution_result(registry_path, result, request, execution_mode="REAL")
    saved = load_registry(registry_path)
    run = saved["runs"][0]
    assert run["agent_id"] == "SCRIPT_PRODUCT_PRODUCER"
    assert run["provider"] == "agent_handoff"
    assert run["prompt_version"] == "1.0.0"
    assert run["input_artifact_ids"] == ["research:R-1"]
    assert run["output_artifact_ids"] == ["analysis:A-1"]
    assert run["handoff_target"] == "SCRIPT_PRODUCT_AUDITOR"
    assert run["functional_identity"] == {
        "mission_id": "M-R6", "capability_id": "SCRIPT_PRODUCT_PRODUCER", "role_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_profile_id": "PROFILE-R6",
    }
    assert run["reproducibility"]["mission_contract_sha256"] == "a" * 64
    assert run["reproducibility"]["context_manifest_sha256"] == "b" * 64
    assert run["reproducibility"]["input_sha256"] == "c" * 64
    assert run["reproducibility"]["prompt_sha256"] == "d" * 64
    assert run["operational_telemetry"]["provider"] == "agent_handoff"
    assert run["operational_telemetry"]["model"] == "handoff_only"
    assert run["operational_telemetry"]["actual_provider"] == "provider-x"
    assert run["operational_telemetry"]["actual_model"] == "model-y"
    assert run["operational_telemetry"]["cost"] == 0.25


def test_agent_handoff_registers_extended_preparation_fields(tmp_path: Path) -> None:
    source = _artifact(tmp_path, "analysis.json", {"analysis_id": "A-1", "content": "ok"})
    registry_path = tmp_path / "registry.json"
    request = ExecutionRequest(
        capability_id="SCRIPT_PRODUCT_AUDITOR",
        skill_id="skill_auditar_suficiencia_semantica_b5_i2",
        skill_version="1.0.0",
        input_artifacts=[InputArtifact("analysis", "A-1", source, "RUN-P")],
        output_schema="b5_i2_semantic_sufficiency_audit",
        execution_mode="agent_handoff",
        provider="agent_handoff",
        episode_id="EP-1",
        role="SCRIPT_PRODUCT_AUDITOR",
        config={**_completion_gate_config(tmp_path), "prompt": "auditar sin modificar", "prompt_version": "1.0.0", "execution_registry_path": str(registry_path), "handoff_target": "OWNER_REVIEW"},
        handoff_directory=tmp_path / "handoff",
    )
    result = execute(request)
    assert result.status is ExecutionStatus.HANDOFF_PREPARED
    saved = load_registry(registry_path)
    handoff = saved["handoffs"][0]
    assert handoff["agent_id"] == "SCRIPT_PRODUCT_AUDITOR"
    assert handoff["provider"] == "agent_handoff"
    assert handoff["prompt_version"] == "1.0.0"
    assert handoff["input_artifact_ids"] == ["analysis:A-1"]
    assert handoff["handoff_target"] == "OWNER_REVIEW"
    assert handoff["decision"] == "HANDOFF_PREPARED"


def test_negative_autoapproval_and_auditor_modification_remain_blocked() -> None:
    try:
        assert_no_self_approval("SCRIPT_PRODUCT_PRODUCER", "approve")
        assert False, "Debi? lanzar PermissionError"
    except AssertionError:
        raise
    except PermissionError:
        pass
    try:
        assert_not_immutable_target("SCRIPT_PRODUCT_AUDITOR", "analysis")
        assert False, "Debi? lanzar PermissionError"
    except AssertionError:
        raise
    except PermissionError:
        pass
