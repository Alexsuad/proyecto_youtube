"""Runtime mínimo y verificable para capacidades de IA editoriales."""

from .contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from .execution import execute

__all__ = ["ExecutionRequest", "ExecutionResult", "ExecutionStatus", "execute"]
