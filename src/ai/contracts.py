"""Contratos independientes de proveedor para el harness híbrido de IA."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ExecutionStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED_BY_SEMANTIC_EVALUATOR = "BLOCKED_BY_SEMANTIC_EVALUATOR"
    HANDOFF_PREPARED = "HANDOFF_PREPARED"


@dataclass(frozen=True)
class InputArtifact:
    artifact_kind: str
    artifact_id: str
    path: Path
    producer_run_id: str = ""


@dataclass
class ExecutionRequest:
    capability_id: str
    skill_id: str
    skill_version: str
    input_artifacts: list[InputArtifact]
    output_schema: str
    execution_mode: str = "auto"
    provider: str | None = None
    model: str | None = None
    executor: str | None = None
    execution_route: str | None = None
    timeout: float = 30.0
    privacy: str = "normal"
    output_artifact_kind: str = ""
    output_artifact_id: str = ""
    output_artifact_path: Path | None = None
    output_artifact_ref: str = ""
    mock_output: dict[str, Any] | None = None
    handoff_directory: Path | None = None
    config: dict[str, Any] = field(default_factory=dict)
    episode_id: str = ""
    role: str = ""


@dataclass
class ExecutionResult:
    run_id: str
    status: ExecutionStatus
    executor_type: str
    provider: str
    model: str
    input_manifest_checksum: str
    output: dict[str, Any] | None
    output_checksum: str | None
    started_at: str
    completed_at: str
    error: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    episode_id: str = ""
    output_artifact_id: str = ""
    output_artifact_kind: str = ""
    output_artifact_path: Path | None = None
    output_artifact_ref: str = ""
    is_real_editorial_execution: bool = False
