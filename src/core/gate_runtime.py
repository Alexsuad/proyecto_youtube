"""Runtime canónico: GateResult JSON como fuente de verdad y exit codes estrictos."""

from collections.abc import Callable
import json
import sys
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.gate_result import GateResult, EXIT_CODE_ERROR
from src.core.path_resolution import gate_output_paths


def validate_gate_result(result: GateResult) -> None:
    violations = validate_against_schema(result.to_dict(), "gate_result")
    if violations:
        raise ValueError("GateResult inválido: " + "; ".join(violations))


def markdown(result: GateResult) -> str:
    rows = [f"# Gate {result.gate_id}", "", f"- Estado: **{result.status.value}**", f"- Resumen: {result.summary}"]
    if result.violations:
        rows.extend(["", "## Violaciones", *[f"- {item}" for item in result.violations]])
    if result.warnings:
        rows.extend(["", "## Advertencias", *[f"- {item}" for item in result.warnings]])
    return "\n".join(rows) + "\n"


def emit(result: GateResult, *, output_root: str | Path | None = None, write_markdown: bool = True) -> int:
    validate_gate_result(result)
    json_path, markdown_path = gate_output_paths(result.gate_id, result.artifact_id, output_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if write_markdown:
        markdown_path.write_text(markdown(result), encoding="utf-8")
    print(f"[{result.gate_id}] status={result.status.value} json={json_path}")
    return result.exit_code


def run_gate(callback: Callable[[], GateResult], *, output_root: str | Path | None = None) -> int:
    try:
        return emit(callback(), output_root=output_root)
    except Exception as exc:  # El error técnico no se disfraza como GateResult.
        print(f"ERROR técnico: {exc}", file=sys.stderr)
        return EXIT_CODE_ERROR
