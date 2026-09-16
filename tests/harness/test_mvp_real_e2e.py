from __future__ import annotations

import json
from pathlib import Path

from src.application.topic_belonging import ExecutionCognitiveBoundary
from src.core.capability_governance import validate_capability_registry
from src.core.mission_authorization import load_mission_authorization
from src.core.mission_completion_gate import load_mission_contract


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "plans/mvp_real_e2e_script_01/mission_contract.json"
AUTHORIZATION = ROOT / "plans/mvp_real_e2e_script_01/mission-authorization.json"


def test_mvp_real_e2e_bundle_is_coherent() -> None:
    contract = load_mission_contract(CONTRACT)
    authorization = load_mission_authorization(AUTHORIZATION)

    assert contract.mission_id == "MVP_REAL_E2E_SCRIPT_01"
    assert authorization.mission_id == contract.mission_id
    assert authorization.execution_family_ids == ("AGENT_HARNESS",)
    assert authorization.allowed_routes == ("agent_harness",)
    assert validate_capability_registry(ROOT / "config/capability_registry.json") == []


def test_agent_harness_preflight_does_not_select_provider_or_model() -> None:
    configuration = json.loads(
        (ROOT / "plans/mvp_real_e2e_script_01/run_configuration.json").read_text(encoding="utf-8")
    )
    assert configuration["execution_family"] == "AGENT_HARNESS"
    assert configuration["provider_override"] is None
    assert configuration["model_override"] is None

    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=str(AUTHORIZATION.relative_to(ROOT)),
        mission_contract_path=str(CONTRACT.relative_to(ROOT)),
        execution_mode="REAL",
        execution_family="AGENT_HARNESS",
        execution_interface="MVP_REAL_E2E_TERMINAL",
        capability_id="MVP_REAL_E2E_TOPIC_BELONGING",
    )

    assert boundary.preflight() == "MVP_REAL_E2E_SCRIPT_01"
