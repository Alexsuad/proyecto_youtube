from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai.runtime_profiles import AgentRuntimePort, MANAGED_BY_EXECUTOR, UNAVAILABLE, UNAVAILABLE_FROM_EXECUTOR, inventory_executor, load_execution_profiles, resolve_run_configuration
from src.core.contract_validation import validate_against_schema

ROOT = Path(__file__).parents[2]


def test_hybrid_profile_contract_declares_owner_authority_and_extensible_profiles() -> None:
    data = json.loads((ROOT / "config/agent_execution_profiles.json").read_text(encoding="utf-8"))
    assert not validate_against_schema(data, "agent_execution_profiles")
    policy = data["policy"]
    assert policy["model_selection_authority"] == "OWNER"
    assert policy["execution_route_selection_authority"] == "OWNER"
    assert policy["per_run_override_required"] is True
    assert policy["defaults_are_non_binding"] is True
    assert set(data["execution_profiles"]) >= {"ollama_local", "deepseek_chat", "codex_current", "opencode_free", "antigravity_current"}


def test_resolution_priority_is_per_run_then_profile_then_role_then_global() -> None:
    profiles = {
        "registry_version": "2.0.0",
        "policy": {
            "model_selection_authority": "OWNER",
            "execution_route_selection_authority": "OWNER",
            "per_run_override_required": True,
            "any_supported_model_allowed": True,
            "defaults_are_non_binding": True,
            "benchmarks_determine_fit": True,
            "free_or_local_first": True,
            "paid_provider_requires_owner_approval": True,
            "executors_optional": True,
            "native_provider_preferred_for_product_runtime": True,
        },
        "global_defaults": {
            "execution_route": "local_model",
            "execution_profile": "role_default",
            "default_model": "global-model",
            "timeout_seconds": 20,
            "max_retries": 0,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        "providers": {
            "ollama": {
                "route_type": "LOCAL_MODEL_RUNTIME",
                "adapter": "ollama",
                "enabled": True,
                "api_base_env": "OLLAMA_API_BASE",
                "model_env": "OLLAMA_MODEL",
                "timeout_seconds": 20,
                "max_retries": 0,
                "cost_policy": "LOCAL_FREE",
            }
        },
        "executors": {"native_provider": {"kind": "NATIVE_PROVIDER", "status": "READY"}},
        "execution_profiles": {
            "role_default": {
                "route_type": "LOCAL_MODEL_RUNTIME",
                "execution_route": "local_model",
                "executor": "native_provider",
                "provider": "ollama",
                "provider_config_ref": "ollama",
                "timeout_seconds": 45,
                "max_retries": 2,
                "cost_policy": "LOCAL_FREE",
                "supports_model_override": True,
                "default_model": "profile-model",
                "model_env": "OLLAMA_MODEL",
            }
        },
        "role_defaults": {
            "SCRIPT_PRODUCT_PRODUCER": {
                "default_execution_profile": "role_default",
                "default_execution_route": "local_model",
                "default_model": "role-model",
                "timeout_seconds": 33,
                "allowed_execution_profiles": ["role_default"],
            }
        },
    }
    resolved = resolve_run_configuration(
        {
            "role_id": "SCRIPT_PRODUCT_PRODUCER",
            "execution_route": "local_model",
            "execution_profile": "role_default",
            "executor_override": None,
            "provider_override": None,
            "model_override": "override-model",
            "timeout_seconds": 99,
            "max_retries": 5,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        profiles=profiles,
        environ={},
    )
    assert resolved.model == "override-model"
    assert resolved.timeout_seconds == 99
    assert resolved.max_retries == 5


def test_local_model_override_switches_models_without_code_change() -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    llama = resolve_run_configuration(
        {
            "role_id": "SCRIPT_PRODUCT_PRODUCER",
            "execution_route": "local_model",
            "execution_profile": "ollama_local",
            "executor_override": None,
            "provider_override": None,
            "model_override": "llama3.2:latest",
            "timeout_seconds": 30,
            "max_retries": 0,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        profiles=profiles,
        environ={},
    )
    qwen = resolve_run_configuration(
        {
            "role_id": "SCRIPT_PRODUCT_PRODUCER",
            "execution_route": "local_model",
            "execution_profile": "ollama_local",
            "executor_override": None,
            "provider_override": None,
            "model_override": "Qwen2.5-Coder:latest",
            "timeout_seconds": 30,
            "max_retries": 0,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        profiles=profiles,
        environ={},
    )
    assert llama.provider == "ollama"
    assert llama.model == "llama3.2:latest"
    assert qwen.model == "Qwen2.5-Coder:latest"


def test_api_provider_override_and_paid_guard_work_without_code_changes() -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    resolved = resolve_run_configuration(
        {
            "role_id": "SCRIPT_PRODUCT_AUDITOR",
            "execution_route": "api_model",
            "execution_profile": "deepseek_chat",
            "executor_override": None,
            "provider_override": "openai",
            "model_override": "gpt-4.1-mini",
            "timeout_seconds": 60,
            "max_retries": 1,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        profiles=profiles,
        environ={},
    )
    assert resolved.status == "BLOCKED_PENDING_OWNER_COST_AUTHORIZATION"
    assert resolved.provider == "openai"
    assert resolved.provider_adapter == "openai_compatible"
    assert resolved.model == "gpt-4.1-mini"


def test_agent_harness_route_uses_managed_provider_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    resolved = resolve_run_configuration(
        {
            "role_id": "SCRIPT_PRODUCT_PRODUCER",
            "execution_route": "agent_harness",
            "execution_profile": "codex_current",
            "executor_override": "codex_cli",
            "provider_override": None,
            "model_override": None,
            "timeout_seconds": 180,
            "max_retries": 1,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        profiles=profiles,
        environ={},
    )
    assert inventory_executor("codex_cli", profiles) == "HANDOFF_ONLY"
    assert resolved.status == "READY"
    assert resolved.provider == MANAGED_BY_EXECUTOR
    assert resolved.model == UNAVAILABLE_FROM_EXECUTOR


def test_unknown_profile_route_provider_and_executor_are_rejected() -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    with pytest.raises(ValueError, match="execution_profile inexistente"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model", "execution_profile": "missing", "executor_override": None,
            "provider_override": None, "model_override": None, "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        }, profiles=profiles, environ={})
    with pytest.raises(ValueError, match="ruta incompatible"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "api_model", "execution_profile": "ollama_local", "executor_override": None,
            "provider_override": None, "model_override": None, "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        }, profiles=profiles, environ={})
    with pytest.raises(ValueError, match="provider incompatible"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model", "execution_profile": "ollama_local", "executor_override": None,
            "provider_override": "openai", "model_override": "llama3.2:latest", "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        }, profiles=profiles, environ={})
    with pytest.raises(ValueError, match="executor inexistente"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model", "execution_profile": "ollama_local", "executor_override": "ghost",
            "provider_override": None, "model_override": "llama3.2:latest", "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        }, profiles=profiles, environ={})


def test_env_example_and_benchmark_matrix_are_ready_without_secrets() -> None:
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for token in (
        "OPENAI_API_KEY=",
        "GEMINI_API_KEY=",
        "ANTHROPIC_API_KEY=",
        "CODEX_MODEL=",
        "OPENCODE_MODEL=",
        "ANTIGRAVITY_MODEL=",
    ):
        assert token in env_example
    assert "sk-" not in env_example
    benchmark_matrix = json.loads((ROOT / "config/execution_benchmark_matrix.json").read_text(encoding="utf-8"))
    assert benchmark_matrix["metrics"] == [
        "quality", "latency", "cost", "schema_compliance", "semantic_quality", "consistency", "naturalness", "fidelity", "error_rate"
    ]
    assert any(case["execution_profile"] == "codex_current" for case in benchmark_matrix["benchmark_cases"])
