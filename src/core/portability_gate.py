"""Structural portability checks for functional versus operational data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FUNCTIONAL_IDENTITY_KEYS = {
    "functional_owner",
    "functional_owner_role",
    "domain_authority",
    "provider_authority",
    "model_authority",
    "functional_provider",
    "functional_model",
}
OPERATIONAL_ROOTS = {"provenance", "operational_telemetry", "runtime_values", "telemetry"}
FUNCTIONAL_ROOTS = {"functional", "functional_identity", "functional_authority", "policy", "rubric", "acceptance_criteria", "authority"}


OPERATIONAL_KEYS = {
    "provider", "model", "model_version", "actual_provider", "actual_model", "provider_or_adapter",
    "model_or_evaluator", "input_tokens", "output_tokens", "cached_tokens", "cost", "currency",
    "latency", "rate_limit", "context_limit", "fallback", "benchmark",
}


@dataclass(frozen=True)
class PortabilityGateResult:
    status: str
    violations: tuple[str, ...]
    operational_metadata: tuple[str, ...]


def _walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path + (str(key),), child
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))


def evaluate_portability(payload: dict[str, Any]) -> PortabilityGateResult:
    violations: list[str] = []
    operational: list[str] = []
    for path, value in _walk(payload):
        if not path:
            continue
        key = path[-1]
        parent_roots = set(path[:-1])
        if key in OPERATIONAL_KEYS and parent_roots.intersection(OPERATIONAL_ROOTS):
            operational.append(".".join(path))
        if key in FUNCTIONAL_IDENTITY_KEYS:
            violations.append(f"FUNCTIONAL_IDENTITY_DEPENDENCY:{'.'.join(path)}")
        if key in OPERATIONAL_KEYS and not parent_roots.intersection(OPERATIONAL_ROOTS):
            if any(part in FUNCTIONAL_ROOTS for part in path[:-1]):
                violations.append(f"FUNCTIONAL_IDENTITY_DEPENDENCY:{'.'.join(path)}")
    return PortabilityGateResult(
        status="PASS" if not violations else "FAIL",
        violations=tuple(sorted(set(violations))),
        operational_metadata=tuple(sorted(set(operational))),
    )
