from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai.runtime_profiles import AgentRuntimePort, UNAVAILABLE, inventory_executor, load_execution_profiles, resolve_execution_route
from src.core.contract_validation import validate_against_schema

ROOT = Path(__file__).parents[2]
ROLES = ("SCRIPT_PRODUCT_PRODUCER", "SCRIPT_PRODUCT_AUDITOR")


def test_hybrid_profile_contract_is_valid_and_has_independent_routes():
    data = json.loads((ROOT / "config/agent_execution_profiles.json").read_text(encoding="utf-8"))
    assert not validate_against_schema(data, "agent_execution_profiles")
    assert data["providers"]["ollama"]["api_base_env"] == "OLLAMA_API_BASE"
    assert data["providers"]["deepseek"]["api_key_env"] == "DEEPSEEK_API_KEY"
    assert {item["role_id"] for item in data["agent_profiles"]} == set(ROLES)
    for profile in data["agent_profiles"]:
        assert {route["execution_route"] for route in profile["routes"]} >= {"native:ollama", "native:deepseek", "executor:codex_cli", "executor:opencode", "executor:antigravity"}


def test_missing_model_and_credentials_cannot_become_ready(tmp_path: Path):
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    ollama = resolve_execution_route("SCRIPT_PRODUCT_PRODUCER", "native:ollama", profiles=profiles, environ={})
    deepseek = resolve_execution_route("SCRIPT_PRODUCT_AUDITOR", "native:deepseek", profiles=profiles, environ={})
    assert ollama.status == "MODEL_UNAVAILABLE"
    assert ollama.model == UNAVAILABLE
    assert deepseek.status == "CREDENTIALS_MISSING"


def test_controlled_executor_requires_actual_provider_and_model(monkeypatch: pytest.MonkeyPatch):
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: "C:/tools/" + command)
    route = resolve_execution_route("SCRIPT_PRODUCT_PRODUCER", "executor:codex_cli", profiles=profiles, environ={"CODEX_MODEL": "reported-model"})
    assert inventory_executor("codex_cli", profiles) == "HANDOFF_ONLY"
    assert route.status == "HANDOFF_ONLY"
    assert route.provider == UNAVAILABLE
    assert route.model == UNAVAILABLE


def test_configured_executor_capability_and_runtime_availability_are_distinct(monkeypatch: pytest.MonkeyPatch):
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    configured = profiles["executors"]["antigravity"]["status"]
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: None)
    runtime = inventory_executor("antigravity", profiles)
    assert configured == "HANDOFF_ONLY"
    assert runtime == "UNAVAILABLE"


def test_unknown_role_or_route_is_rejected():
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    with pytest.raises(ValueError):
        resolve_execution_route("UNKNOWN", "native:ollama", profiles=profiles, environ={})
    with pytest.raises(ValueError):
        resolve_execution_route("SCRIPT_PRODUCT_PRODUCER", "native:unknown", profiles=profiles, environ={})


def test_profile_file_contains_no_secrets():
    text = (ROOT / "config/agent_execution_profiles.json").read_text(encoding="utf-8")
    assert "sk-" not in text


def test_agent_runtime_port_resolves_profiles_from_the_common_entrypoint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OLLAMA_MODEL", "local-model")
    port = AgentRuntimePort(ROOT / "config" / "agent_execution_profiles.json")
    resolved = port.resolve("SCRIPT_PRODUCT_PRODUCER", "native:ollama")
    assert resolved.executor == "native_provider"
    assert resolved.provider == "ollama"
    assert resolved.model == "local-model"
    assert resolved.timeout_seconds == 30
    assert resolved.cost_policy == "LOCAL_FREE"


def test_ai_providers_example_is_aligned_with_hybrid_profiles():
    text = (ROOT / "config/ai_providers.example.yaml").read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY" in text
    assert "OLLAMA_MODEL" in text
    assert "selection_source: config/agent_execution_profiles.json" in text


def test_env_example_exists_and_documents_required_variables_without_secrets():
    env_example = ROOT / ".env.example"
    assert env_example.exists()
    text = env_example.read_text(encoding="utf-8")
    for token in (
        "OLLAMA_API_BASE=",
        "OLLAMA_MODEL=",
        "DEEPSEEK_API_BASE=",
        "DEEPSEEK_API_KEY=",
        "DEEPSEEK_MODEL=",
        "CODEX_MODEL=",
        "OPENCODE_MODEL=",
        "ANTIGRAVITY_MODEL=",
    ):
        assert token in text
    assert "sk-" not in text
    assert "Bearer " not in text
    assert "-----BEGIN" not in text


def test_gitignore_keeps_env_ignored_but_allows_env_example():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in gitignore
    assert ".env.*" in gitignore
    assert "!.env.example" in gitignore