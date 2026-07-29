"""Routing explícito y sin fallbacks externos silenciosos."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from src.ai.contracts import ExecutionRequest


KNOWN_PROVIDERS = {"mock", "ollama", "deepseek", "openai_compatible", "agent_handoff"}


def load_routing_policy(path: Path | None = None) -> dict[str, Any]:
    """La YAML operativa, no el ejemplo de proveedores, es la sede de policy."""
    policy_path = path or Path("config/capability_routing.yaml")
    if not policy_path.exists():
        return {}
    loaded = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def resolve_provider(request: ExecutionRequest) -> str | None:
    policy = load_routing_policy(request.config.get("routing_policy_path"))
    explicit = request.provider
    mode = (request.execution_mode or "auto").lower()
    capability = policy.get("capabilities", {}).get(request.capability_id, {})
    routing = capability.get("routing", {}) if isinstance(capability, dict) else {}
    if mode != "auto":
        mapped = {"mock": "mock", "local": "ollama", "api": "openai_compatible", "deepseek": "deepseek", "agent": "agent_handoff", "agent_handoff": "agent_handoff"}.get(mode)
        if mode in {"api", "deepseek"} and not bool(routing.get("allow_external_api", False)):
            return None
        return explicit or mapped
    if explicit:
        if explicit in {"openai_compatible", "deepseek"} and not bool(routing.get("allow_external_api", False)):
            return None
        return explicit
    if request.privacy.lower() == "high":
        return "ollama"
    if request.config.get("local_available", True) and routing.get("auto_local", True):
        return "ollama"
    if request.config.get("agent_handoff") or routing.get("auto_agent_handoff", False):
        return "agent_handoff"
    return None
