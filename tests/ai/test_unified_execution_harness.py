from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ai.providers.agent_executor import AgentExecutorProvider
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
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_agent_role.py",
            "--role", "SCRIPT_PRODUCT_PRODUCER",
            "--profile", profile_id,
            "--route", "agent_harness",
            "--executor", executor_id,
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
