from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai.runtime_profiles import AgentRuntimePort, MANAGED_BY_EXECUTOR, UNAVAILABLE, UNAVAILABLE_FROM_EXECUTOR, inventory_executor, load_execution_family_selection, load_execution_profiles, resolve_profile_family, resolve_run_configuration, selected_execution_family
from src.core.mission_authorization import load_mission_authorization
from src.ai.providers.agent_executor import AgentExecutorProvider
from src.ai.role_execution import build_model_prompt, resolve_role_execution_contract
from src.core.contract_validation import validate_against_schema
from src.core.prompt_resolver import resolve_prompt

ROOT = Path(__file__).parents[2]


def _selection_path(tmp_path: Path, family: str) -> str:
    path = tmp_path / "execution-family-selection.json"
    path.write_text(json.dumps({
        "selection_version": "1.0.0",
        "families": {name: name == family for name in ("AGENT_HARNESS", "API_PROVIDER", "LOCAL_MODEL")},
    }), encoding="utf-8")
    return str(path)


def test_hybrid_profile_contract_declares_owner_authority_and_extensible_profiles() -> None:
    data = json.loads((ROOT / "config/agent_execution_profiles.json").read_text(encoding="utf-8"))
    assert not validate_against_schema(data, "agent_execution_profiles")
    policy = data["policy"]
    assert policy["model_selection_authority"] == "OWNER"
    assert policy["execution_route_selection_authority"] == "OWNER"
    assert policy["per_run_override_required"] is True
    assert policy["defaults_are_non_binding"] is True
    assert set(data["execution_profiles"]) >= {"ollama_local", "deepseek_chat", "codex_current", "opencode_free", "antigravity_current"}


def test_mvp_execution_family_selection_has_exactly_one_active_family() -> None:
    selection = load_execution_family_selection(ROOT / "config/execution_family_selection.json")
    assert selection["families"] == {"AGENT_HARNESS": True, "API_PROVIDER": False, "LOCAL_MODEL": False}
    assert selected_execution_family(ROOT / "config/execution_family_selection.json") == "AGENT_HARNESS"


def test_agent_harness_family_does_not_select_concrete_runtime_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: pytest.fail("family route must not inspect a concrete executor"))
    resolved = resolve_run_configuration({
        "role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "execution_route": "agent_harness",
        "execution_profile": None, "execution_family": "AGENT_HARNESS",
        "executor_override": None, "provider_override": None, "model_override": None,
        "reasoning_effort": None, "timeout_seconds": 180, "max_retries": 1,
        "temperature": None, "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
    }, profiles=profiles, environ={})
    assert resolved.status == "READY"
    assert resolved.execution_family == "AGENT_HARNESS"
    assert resolved.execution_profile is None
    assert resolved.executor == "OWNER_MANAGED"
    assert resolved.provider == MANAGED_BY_EXECUTOR
    assert resolved.model == UNAVAILABLE_FROM_EXECUTOR


def test_agent_harness_family_rejects_concrete_identity_overrides() -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    with pytest.raises(ValueError, match="AGENT_HARNESS_DOES_NOT_SELECT"):
        resolve_run_configuration({
            "role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "execution_route": "agent_harness",
            "execution_profile": "opencode_free", "execution_family": "AGENT_HARNESS",
            "executor_override": None, "provider_override": None, "model_override": None,
            "reasoning_effort": None, "timeout_seconds": 180, "max_retries": 1,
            "temperature": None, "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        }, profiles=profiles, environ={})


def test_explicit_execution_family_must_match_operational_selector(tmp_path: Path) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({
        "selection_version": "1.0.0",
        "families": {"AGENT_HARNESS": True, "API_PROVIDER": False, "LOCAL_MODEL": False},
    }), encoding="utf-8")
    configuration = {
        "role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "execution_route": "agent_harness",
        "execution_profile": None, "execution_family": "AGENT_HARNESS",
        "executor_override": None, "provider_override": None, "model_override": None,
        "reasoning_effort": None, "timeout_seconds": 180, "max_retries": 1,
        "temperature": None, "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        "execution_family_selection_path": str(selection),
    }
    resolved = resolve_run_configuration(configuration, profiles=profiles, environ={})
    assert resolved.execution_family == "AGENT_HARNESS"

    selection.write_text(json.dumps({
        "selection_version": "1.0.0",
        "families": {"AGENT_HARNESS": False, "API_PROVIDER": True, "LOCAL_MODEL": False},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="EXECUTION_FAMILY_SELECTION_MISMATCH"):
        resolve_run_configuration(configuration, profiles=profiles, environ={})


def test_explicit_profile_must_match_operational_selector(tmp_path: Path) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({
        "selection_version": "1.0.0",
        "families": {"AGENT_HARNESS": True, "API_PROVIDER": False, "LOCAL_MODEL": False},
    }), encoding="utf-8")
    configuration = {
        "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model",
        "execution_profile": "ollama_local", "execution_family": None,
        "executor_override": None, "provider_override": None, "model_override": "owner-selected-model",
        "reasoning_effort": None, "timeout_seconds": 30, "max_retries": 0,
        "temperature": None, "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        "execution_family_selection_path": str(selection),
    }
    assert resolve_profile_family("ollama_local", profiles=profiles) == "LOCAL_MODEL"
    with pytest.raises(ValueError, match="EXECUTION_FAMILY_SELECTION_PROFILE_MISMATCH"):
        resolve_run_configuration(configuration, profiles=profiles, environ={})

    selection.write_text(json.dumps({
        "selection_version": "1.0.0",
        "families": {"AGENT_HARNESS": False, "API_PROVIDER": False, "LOCAL_MODEL": True},
    }), encoding="utf-8")
    resolved = resolve_run_configuration(configuration, profiles=profiles, environ={})
    assert resolved.execution_profile == "ollama_local"


def test_profile_without_selector_path_uses_canonical_selector() -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    with pytest.raises(ValueError, match="EXECUTION_FAMILY_SELECTION_PROFILE_MISMATCH"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model",
            "execution_profile": "ollama_local", "execution_family": None,
            "executor_override": None, "provider_override": None, "model_override": "owner-selected-model",
            "reasoning_effort": None, "timeout_seconds": 30, "max_retries": 0,
            "temperature": None, "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
        }, profiles=profiles, environ={})


def test_active_execution_family_must_be_authorized_for_mission() -> None:
    authorization = load_mission_authorization(
        ROOT / "plans/plan_009/p2_real_roundtrip/mission/mission-authorization.json"
    )
    with pytest.raises(PermissionError, match="execution family scope"):
        authorization.verify(
            ROOT,
            capability_id="TOPIC_BELONGING_ASSESSMENT",
            role_id="CHANNEL_INTELLIGENCE_PRODUCER",
            operation="EXECUTE_CAPABILITY",
            execution_mode="REAL",
            execution_route="agent_harness",
            execution_family="API_PROVIDER",
            execution_interface="TOPIC_BELONGING_TERMINAL",
        )


@pytest.mark.parametrize("families", [
    {"AGENT_HARNESS": False, "API_PROVIDER": False, "LOCAL_MODEL": False},
    {"AGENT_HARNESS": True, "API_PROVIDER": True, "LOCAL_MODEL": False},
])
def test_execution_family_selection_rejects_zero_or_multiple_active_families(tmp_path: Path, families: dict[str, bool]) -> None:
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({"selection_version": "1.0.0", "families": families}), encoding="utf-8")
    with pytest.raises(ValueError, match="EXACTLY_ONE_ACTIVE_FAMILY"):
        load_execution_family_selection(selection)


def test_editorial_roles_traverse_canonical_profile_and_prompt_route(tmp_path: Path) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    registry = json.loads((ROOT / "config/agent_prompt_registry.json").read_text(encoding="utf-8"))
    roles = ("RESEARCH_AND_CURATION", "NARRATIVE_ARCHITECTURE", "WRITING", "EDITOR")
    registered = {entry["role_id"]: entry for entry in registry["prompts"]}
    for role_id in roles:
        prompt_entry = registered[role_id]
        assert prompt_entry["status"] == "ACTIVE"
        route = resolve_run_configuration(
            {
                "role_id": role_id,
                "execution_route": "local_model",
                "execution_profile": "ollama_local",
                "executor_override": None,
                "provider_override": None,
                "model_override": "owner-selected-free-model",
                "timeout_seconds": 30,
                "max_retries": 0,
                "temperature": None,
                    "max_tokens": None,
                    "budget_limit": None,
                    "paid_cost_approved": False,
                    "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
                },
            profiles=profiles,
            environ={},
        )
        assert route.execution_profile == "ollama_local"
        resolved_prompt = resolve_prompt(role_id)
        assert resolved_prompt["prompt_id"] == prompt_entry["prompt_id"]
        contract = resolve_role_execution_contract(
            role_id,
            "execution_smoke_report",
            {},
            {
                "role_id": role_id,
                "execution_profile": route.execution_profile,
                "execution_route": route.execution_route,
            },
        )
        model_prompt = build_model_prompt(contract)
        assert model_prompt.strip()
        assert prompt_entry["prompt_id"] in model_prompt


def test_resolution_priority_is_per_run_then_profile_then_role_then_global(tmp_path: Path) -> None:
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
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
        },
        profiles=profiles,
        environ={},
    )
    assert resolved.model == "override-model"
    assert resolved.timeout_seconds == 99
    assert resolved.max_retries == 5


def test_local_model_override_switches_models_without_code_change(tmp_path: Path) -> None:
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
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
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
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
        },
        profiles=profiles,
        environ={},
    )
    assert llama.provider == "ollama"
    assert llama.model == "llama3.2:latest"
    assert qwen.model == "Qwen2.5-Coder:latest"


def test_api_provider_override_and_paid_guard_work_without_code_changes(tmp_path: Path) -> None:
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
            "execution_family_selection_path": _selection_path(tmp_path, "API_PROVIDER"),
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


def test_opencode_profile_requires_owner_model_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    base = {
        "role_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_route": "agent_harness",
        "execution_profile": "opencode_free",
        "executor_override": "opencode",
        "provider_override": None,
        "timeout_seconds": 180,
        "max_retries": 1,
        "temperature": None,
        "max_tokens": None,
        "budget_limit": None,
        "paid_cost_approved": False,
    }
    blocked = resolve_run_configuration({**base, "model_override": None}, profiles=profiles, environ={})
    assert blocked.status == "MODEL_UNAVAILABLE"
    selected = resolve_run_configuration({**base, "model_override": "owner-selected-free-model"}, profiles=profiles, environ={})
    assert selected.status == "READY"
    assert selected.provider == MANAGED_BY_EXECUTOR
    assert selected.model == "owner-selected-free-model"


@pytest.mark.parametrize("profile_id, executor_id, model", [
    ("codex_current", "codex_cli", None),
    ("opencode_free", "opencode", "owner-selected-free-model"),
])
def test_reasoning_effort_is_fail_closed_when_executor_does_not_declare_support(
    monkeypatch: pytest.MonkeyPatch, profile_id: str, executor_id: str, model: str | None
) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    with pytest.raises(ValueError, match="reasoning_effort no soportado"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER",
            "execution_route": "agent_harness",
            "execution_profile": profile_id,
            "executor_override": executor_id,
            "provider_override": None,
            "model_override": model,
            "reasoning_effort": "high",
            "timeout_seconds": 180,
            "max_retries": 1,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        }, profiles=profiles, environ={})


def test_reasoning_effort_is_transport_only_when_executor_declares_support(monkeypatch: pytest.MonkeyPatch) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    profiles["executors"]["codex_cli"]["supports_reasoning_effort"] = True
    profiles["execution_profiles"]["codex_current"]["supports_reasoning_effort"] = True
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    resolved = resolve_run_configuration({
        "role_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_route": "agent_harness",
        "execution_profile": "codex_current",
        "executor_override": "codex_cli",
        "provider_override": None,
        "model_override": None,
        "reasoning_effort": "medium",
        "timeout_seconds": 180,
        "max_retries": 1,
        "temperature": None,
        "max_tokens": None,
        "budget_limit": None,
        "paid_cost_approved": False,
    }, profiles=profiles, environ={})
    assert resolved.reasoning_effort == "medium"
    assert resolved.reasoning_effort_supported is True
    assert resolved.as_run_configuration()["reasoning_effort"] == "medium"


def test_agent_executor_real_mode_is_fail_closed_before_subprocess(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.ai.providers.agent_executor.shutil.which", lambda command: f"C:/tools/{command}")
    monkeypatch.setattr("src.ai.providers.agent_executor.subprocess.run", lambda *args, **kwargs: pytest.fail("real agent subprocess must not run"))
    request = type("Request", (), {
        "config": {"smoke_test": False, "isolated_workdir": str(tmp_path)},
        "executor": "codex_cli",
        "timeout": 5,
        "role": "SCRIPT_PRODUCT_PRODUCER",
        "capability_id": "SCRIPT_PRODUCT_PRODUCER",
        "execution_profile": "codex_current",
        "execution_route": "agent_harness",
        "model": None,
    })()
    with pytest.raises(PermissionError, match="AGENT_HARNESS_SMOKE_ONLY_UNTIL_R6_B_RETRY"):
        AgentExecutorProvider().execute(request)


def test_unknown_profile_route_provider_and_executor_are_rejected(tmp_path: Path) -> None:
    profiles = load_execution_profiles(ROOT / "config/agent_execution_profiles.json")
    with pytest.raises(ValueError, match="execution_profile inexistente"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model", "execution_profile": "missing", "executor_override": None,
            "provider_override": None, "model_override": None, "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
        }, profiles=profiles, environ={})
    with pytest.raises(ValueError, match="ruta incompatible"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "api_model", "execution_profile": "ollama_local", "executor_override": None,
            "provider_override": None, "model_override": None, "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
        }, profiles=profiles, environ={})
    with pytest.raises(ValueError, match="provider incompatible"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model", "execution_profile": "ollama_local", "executor_override": None,
            "provider_override": "openai", "model_override": "llama3.2:latest", "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
        }, profiles=profiles, environ={})
    with pytest.raises(ValueError, match="executor inexistente"):
        resolve_run_configuration({
            "role_id": "SCRIPT_PRODUCT_PRODUCER", "execution_route": "local_model", "execution_profile": "ollama_local", "executor_override": "ghost",
            "provider_override": None, "model_override": "llama3.2:latest", "timeout_seconds": 30, "max_retries": 0, "temperature": None,
            "max_tokens": None, "budget_limit": None, "paid_cost_approved": False,
            "execution_family_selection_path": _selection_path(tmp_path, "LOCAL_MODEL"),
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
