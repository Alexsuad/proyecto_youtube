from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ai.providers.agent_executor import AgentExecutorProvider
from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.ai.execution import _finalize_mission_reservation, persist_execution_attempt
from src.scripts import run_agent_role

ROOT = Path(__file__).parents[2]


class _Completed:
    def __init__(self, returncode: int = 0, stdout: str = "ok", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _first_harness_route() -> tuple[str, str]:
    data = json.loads((ROOT / "config/agent_execution_profiles.json").read_text(encoding="utf-8"))
    profile_id, profile = next((item for item in data["execution_profiles"].items() if item[1]["route_type"] == "AGENT_HARNESS_RUNTIME"))
    return profile_id, profile["executor"]


def test_agent_executor_provider_returns_structured_smoke_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, executor_id = _first_harness_route()
    monkeypatch.setattr("src.ai.providers.agent_executor.shutil.which", lambda command: f"C:/tools/{command}")
    monkeypatch.setattr(
        "src.ai.providers.agent_executor.subprocess.run",
        lambda *args, **kwargs: _Completed(returncode=0, stdout="usage: runner", stderr=""),
    )
    request = type("Request", (), {
        "config": {"smoke_test": True, "probe_args": ["--help"], "isolated_workdir": str(tmp_path)},
        "executor": executor_id,
        "timeout": 5,
        "role": "SCRIPT_PRODUCT_PRODUCER",
        "capability_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_profile": "managed_current",
        "execution_route": "agent_harness",
        "model": None,
    })()
    payload, usage = AgentExecutorProvider().execute(request)
    assert payload["actual_provider"] == "MANAGED_BY_EXECUTOR"
    assert payload["actual_model"] == "UNAVAILABLE_FROM_EXECUTOR"
    assert payload["result"] == "SUCCEEDED"
    assert usage["actual_executor"] == executor_id


def _contractual_producer_smoke_input() -> dict[str, object]:
    return {
        "mode": "CONTROLLED_SMOKE",
        "episode_id": "SMOKE-CONTRACTUAL",
        "active_editorial_profile_reference": {"profile_id": "mas_alla_del_guion", "version": "1.2.1"},
        "episode_brief": {"brief_id": "brief-smoke", "title": "Smoke contractual"},
        "research_pack": {"research_id": "research-smoke"},
        "source_access_and_evidence_report": {"evidence_report_id": "evidence-smoke"},
        "provisional_thesis": {"thesis_id": "thesis-smoke"},
        "semantic_sufficiency_audit": {"audit_id": "audit-smoke"},
        "claims_ledger": {"claims": []},
        "approved_material_candidates": {"materials": []},
        "excluded_claims": {"claims": []},
        "limited_claims": {"claims": []},
        "mandatory_disclosures": {"disclosures": []},
        "product_artifacts": [],
        "note": "Controlled contractual smoke; no editorial product is produced.",
    }


def test_run_agent_role_cli_writes_smoke_output_and_provenance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    profile_id, executor_id = _first_harness_route()
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    monkeypatch.setattr("src.ai.providers.agent_executor.shutil.which", lambda command: f"C:/tools/{command}")
    monkeypatch.setattr(
        "src.ai.providers.agent_executor.subprocess.run",
        lambda *args, **kwargs: _Completed(returncode=0, stdout="usage: runner", stderr=""),
    )
    output_path = tmp_path / "smoke.json"
    registry_path = tmp_path / "registry.json"
    input_path = tmp_path / "contractual_input.json"
    input_path.write_text(json.dumps(_contractual_producer_smoke_input(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_agent_role.py",
            "--role", "SCRIPT_PRODUCT_PRODUCER",
            "--profile", profile_id,
            "--route", "agent_harness",
            "--executor", executor_id,
            "--input", str(input_path),
            "--output", str(output_path),
            "--execution-registry-path", str(registry_path),
            "--model", "managed-model",
        ],
    )
    exit_code = run_agent_role.main()
    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["selected_executor"] == executor_id
    assert payload["execution_profile"] == profile_id
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["runs"][0]["execution_profile"] == profile_id
    assert registry["runs"][0]["outputs"][0]["artifact_kind"] == "execution_smoke_report"
    run = registry["runs"][0]
    assert run["role_id"] == "SCRIPT_PRODUCT_PRODUCER"
    assert run["prompt_id"] == "prompt_script_product_producer"
    assert len(run["prompt_checksum"]) == 64
    assert len(run["input_checksum"]) == 64
    assert len(run["output_checksum"]) == 64
    assert run["validation_result"] == "PASS"
    assert run["execution_mode"] == "SYNTHETIC"
    assert run["provider_kind"] == "SYNTHETIC"


def test_reservation_finalization_failure_fails_result_and_preserves_unconsumed_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    request = ExecutionRequest(
        capability_id="TEST_CAPABILITY",
        skill_id="skill_test",
        skill_version="1.0.0",
        input_artifacts=[],
        output_schema="execution_smoke_report",
        config={
            "_mission_reservation_id": "RES-TEST",
            "_mission_reservation_status": "RESERVED",
            "execution_registry_path": str(tmp_path / "registry.json"),
        },
    )
    result = ExecutionResult(
        run_id="RUN-TEST",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="mock",
        model="mock",
        input_manifest_checksum="a" * 64,
        output={},
        output_checksum="b" * 64,
        started_at="2026-08-17T00:00:00Z",
        completed_at="2026-08-17T00:00:01Z",
    )
    registry_path = Path(request.config["execution_registry_path"])
    registry_path.write_text(json.dumps({"reservations": [{"reservation_id": "RES-TEST", "status": "RESERVED"}]}), encoding="utf-8")
    def fail_finalization(*args, **kwargs):
        raise OSError("simulated finalization failure")
    monkeypatch.setattr("src.ai.execution.mark_mission_reservation", fail_finalization)

    finalized = _finalize_mission_reservation(request, result)

    assert finalized.status == ExecutionStatus.FAILED
    assert finalized.usage["mission_reservation_status"] == "RESERVED"
    assert "MISSION_RESERVATION_FINALIZATION_FAILED" in finalized.usage["provenance_error"]
    assert "MISSION_RESERVATION_FINALIZATION_FAILED" in str(finalized.error)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["reservations"][0]["status"] == "RESERVED"


def test_real_provenance_requires_verified_mission_authorization(tmp_path: Path) -> None:
    request = type("Request", (), {"role": "SCRIPT_PRODUCT_PRODUCER", "config": {"_mission_authorization_verified": True}})()
    result = ExecutionResult(
        run_id="RUN-UNAUTHORIZED-REAL",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="mock",
        model="mock",
        input_manifest_checksum="a" * 64,
        output={},
        output_checksum="b" * 64,
        started_at="2026-08-17T00:00:00Z",
        completed_at="2026-08-17T00:00:01Z",
    )
    with pytest.raises(PermissionError, match="REAL_PROVENANCE_REQUIRES_VERIFIED_MISSION_AUTHORIZATION"):
        from src.ai.execution import persist_execution_result
        persist_execution_result(tmp_path / "registry.json", result, request, execution_mode="REAL")


def test_persist_execution_attempt_writes_attempt_without_run(tmp_path: Path) -> None:
    output_path = tmp_path / "failed.json"
    output_path.write_text('{"status":"FAILED"}\n', encoding="utf-8")
    request = type("Request", (), {
        "role": "SCRIPT_PRODUCT_PRODUCER",
        "execution_profile": "ollama_local",
        "execution_route": "local_model",
        "config": {
            "prompt_id": "prompt_script_product_producer",
            "prompt_version": "1.0.0",
            "prompt_checksum": "a" * 64,
            "input_checksum": "b" * 64,
            "validation_result": "NOT_REACHED",
            "resolved_actual_executor": "native_provider",
            "resolved_actual_provider": "ollama",
            "resolved_actual_model": "Qwen2.5-Coder:latest",
        },
    })()
    result = ExecutionResult(
        run_id="RUN-AI-FAILED-1",
        status=ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER,
        executor_type="provider",
        provider="ollama",
        model="Qwen2.5-Coder:latest",
        input_manifest_checksum="c" * 64,
        output={"status": "FAILED"},
        output_checksum="d" * 64,
        started_at="2026-07-31T18:00:00Z",
        completed_at="2026-07-31T18:05:00Z",
        error="MODEL_INVOCATION_FAILED: TIMEOUT",
        usage={
            "skill_id": "skill_unified_execution_smoke",
            "skill_version": "1.0.0",
            "actual_executor": "native_provider",
            "actual_provider": "ollama",
            "actual_model": "Qwen2.5-Coder:latest",
            "execution_profile": "ollama_local",
            "execution_route": "local_model",
        },
    )
    registry_path = tmp_path / "registry.json"
    persist_execution_attempt(registry_path, result, request, execution_mode="REAL")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["runs"] == []
    assert len(registry["attempts"]) == 1
    attempt = registry["attempts"][0]
    assert attempt["status"] == "BLOCKED_BY_RUNTIME_PROVIDER"
    assert attempt["error"] == "MODEL_INVOCATION_FAILED: TIMEOUT"
    assert attempt["validation_result"] == "NOT_REACHED"

def test_agent_executor_timeout_is_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, executor_id = _first_harness_route()
    monkeypatch.setattr("src.ai.providers.agent_executor.shutil.which", lambda command: f"C:/tools/{command}")

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=[executor_id, "--help"], timeout=1)

    monkeypatch.setattr("src.ai.providers.agent_executor.subprocess.run", _timeout)
    request = type("Request", (), {
        "config": {"smoke_test": True, "probe_args": ["--help"], "isolated_workdir": str(tmp_path)},
        "executor": executor_id,
        "timeout": 1,
        "role": "SCRIPT_PRODUCT_PRODUCER",
        "capability_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_profile": "managed_current",
        "execution_route": "agent_harness",
        "model": None,
    })()
    with pytest.raises(RuntimeError, match="TIMEOUT"):
        AgentExecutorProvider().execute(request)
