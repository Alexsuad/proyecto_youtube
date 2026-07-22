"""Validación reusable de entradas declaradas por los gates."""

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

from src.core.contract_validation import validate_against_schema


@dataclass(frozen=True)
class InputRequirement:
    path: Path
    label: str
    required: bool = True
    expected_type: str = "file"
    schema: str | None = None


def validate_inputs(requirements: list[InputRequirement]) -> tuple[list[str], list[str], dict[str, Any]]:
    """Devuelve (blocked, failures, evidence) sin inferir estados desde texto."""
    blocked, failures, checked = [], [], []
    for requirement in requirements:
        path = requirement.path
        item = {"label": requirement.label, "path": str(path)}
        if not path.exists():
            if requirement.required:
                blocked.append(f"Entrada obligatoria ausente: {requirement.label}")
            item["result"] = "missing"
        elif requirement.expected_type == "file" and not path.is_file():
            failures.append(f"Entrada no es un archivo regular: {requirement.label}")
            item["result"] = "not_regular_file"
        elif requirement.expected_type == "directory" and not path.is_dir():
            failures.append(f"Entrada no es un directorio: {requirement.label}")
            item["result"] = "not_directory"
        elif requirement.expected_type == "file" and not path.read_text(encoding="utf-8").strip():
            blocked.append(f"Entrada obligatoria vacía: {requirement.label}")
            item["result"] = "empty"
        else:
            item["result"] = "valid"
            if requirement.schema:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    violations = validate_against_schema(data, requirement.schema)
                    if violations:
                        failures.extend(f"{requirement.label}: {violation}" for violation in violations)
                        item["schema"] = "invalid"
                    else:
                        item["schema"] = "valid"
                except json.JSONDecodeError as exc:
                    failures.append(f"{requirement.label}: JSON inválido ({exc.msg})")
                    item["schema"] = "invalid_json"
        checked.append(item)
    return blocked, failures, {"inputs_checked": checked}
