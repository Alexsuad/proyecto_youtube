"""Foundation neutral y reusable para agentes y subagentes."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from src.core.contract_validation import validate_against_schema


MATURE_FOR_ACTIVATION = {
    "AGENT_TESTED_IN_ISOLATION",
    "AGENT_INTEGRATED",
    "AGENT_DEMONSTRATED",
}


@dataclass(frozen=True)
class RunContext:
    agent_id: str
    run_id: str
    execution_role: str
    functional_role: str
    context_path: Path


def load_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or Path("config/subagent_registry.json")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    violations = validate_against_schema(data, "subagent_registry")
    if violations:
        raise ValueError("SubagentRegistry inválido: " + "; ".join(violations))
    return data


def get_agent_definition(agent_id: str, *, registry_path: Path | None = None) -> dict[str, Any]:
    registry = load_registry(registry_path)
    for agent in registry["agents"]:
        if agent["agent_id"] == agent_id:
            return agent
    raise ValueError(f"agent_id desconocido: {agent_id}")


def ensure_agent_activatable(agent_id: str, *, registry_path: Path | None = None) -> dict[str, Any]:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if agent["maturity_status"] not in MATURE_FOR_ACTIVATION:
        raise ValueError(f"{agent_id} no es activable con maturity_status={agent['maturity_status']}")
    return agent


def build_run_context(agent_id: str, run_id: str, *, registry_path: Path | None = None) -> RunContext:
    agent = ensure_agent_activatable(agent_id, registry_path=registry_path)
    return RunContext(
        agent_id=agent["agent_id"],
        run_id=run_id,
        execution_role=agent["execution_role"],
        functional_role=agent["functional_role"],
        context_path=Path(".runtime-tmp") / "subagents" / run_id,
    )


def _normalize_relative_path(path: str | Path) -> PurePosixPath:
    raw = str(path).replace("\\", "/").strip()
    pure = PurePosixPath(raw)
    if pure.is_absolute():
        raise PermissionError(f"ruta absoluta no permitida: {path}")
    parts = [part for part in pure.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise PermissionError(f"path traversal no permitido: {path}")
    return PurePosixPath(*parts)


def _prefix_matches(path: PurePosixPath, prefix: PurePosixPath) -> bool:
    prefix_parts = prefix.parts
    return len(path.parts) >= len(prefix_parts) and path.parts[: len(prefix_parts)] == prefix_parts


def _path_is_allowed(path: str | Path, prefixes: list[str]) -> bool:
    normalized = _normalize_relative_path(path)
    return any(_prefix_matches(normalized, _normalize_relative_path(prefix)) for prefix in prefixes)


def assert_read_allowed(agent_id: str, target: str | Path, *, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if not _path_is_allowed(target, agent["permissions"]["read"]):
        raise PermissionError(f"{agent_id} no puede leer {target}")


def assert_write_allowed(agent_id: str, target: str | Path, *, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if not _path_is_allowed(target, agent["permissions"]["write"]):
        raise PermissionError(f"{agent_id} no puede escribir {target}")


def assert_tool_allowed(agent_id: str, tool_name: str, *, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if tool_name not in agent["allowed_tools"]:
        raise PermissionError(f"{agent_id} no tiene autorizado el tool {tool_name}")


def assert_role_artifact_compatibility(agent_id: str, artifact_kind: str, *, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if artifact_kind not in agent["artifact_compatibility"]:
        raise ValueError(f"{agent_id} no es compatible con artifact_kind={artifact_kind}")


def assert_no_self_approval(agent_id: str, action: str, *, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if action == "approve" and agent["functional_role"] in {"producer", "writer", "editor", "verifier"}:
        raise PermissionError(f"{agent_id} no puede autoaprobar")


def assert_not_immutable_target(agent_id: str, artifact_kind: str, *, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if artifact_kind in agent["immutable_targets"]:
        raise PermissionError(f"{agent_id} no puede modificar {artifact_kind}")


def assert_readiness_not_synthetic(agent_id: str, *, execution_mode: str, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if execution_mode.upper() == "SYNTHETIC" and not agent["synthetic_policy"]["can_authorize_readiness"]:
        raise PermissionError(f"{agent_id} no puede autorizar readiness desde una ejecución sintética")


def assert_budget_within_limit(agent_id: str, *, consumed_tokens: int, consumed_turns: int, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    budget = agent["budget"]
    if consumed_tokens > budget["max_tokens"]:
        raise PermissionError(f"{agent_id} excede max_tokens={budget['max_tokens']}")
    if consumed_turns > budget["max_turns"]:
        raise PermissionError(f"{agent_id} excede max_turns={budget['max_turns']}")


def assert_timeout_within_limit(agent_id: str, *, timeout_seconds: int, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if timeout_seconds > agent["timeout_seconds"]:
        raise PermissionError(f"{agent_id} excede timeout_seconds={agent['timeout_seconds']}")


def assert_cycle_within_limit(agent_id: str, *, cycle_number: int, registry_path: Path | None = None) -> None:
    agent = get_agent_definition(agent_id, registry_path=registry_path)
    if cycle_number > agent["loop_policy"]["max_cycles"]:
        raise PermissionError(f"{agent_id} excede max_cycles={agent['loop_policy']['max_cycles']}")


def build_handoff_checksum(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assert_handoff_integrity(payload: dict[str, Any], expected_checksum: str) -> None:
    observed = build_handoff_checksum(payload)
    if observed != expected_checksum:
        raise ValueError("handoff checksum incorrecto")


def atomic_stage_write(target: Path, content: str, *, fail_after_stage: bool = False) -> None:
    staged = target.with_suffix(target.suffix + ".tmp")
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(content, encoding="utf-8")
    if fail_after_stage:
        staged.unlink(missing_ok=True)
        raise OSError("simulated atomic failure")
    staged.replace(target)
