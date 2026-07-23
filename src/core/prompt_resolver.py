"""PromptResolver portatil: resuelve prompt activo y configuracion runtime para un role_id."""

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]


class PromptResolutionError(Exception):
    """Error during prompt resolution."""

class ConfigResolutionError(Exception):
    """Error during runtime configuration resolution."""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_prompt(role_id: str) -> dict[str, Any]:
    """Return the active prompt contract for a given role_id.

    Reads the prompt registry, finds the ACTIVE entry for role_id,
    then loads the corresponding prompt markdown file.

    Blocks if:
    - role_id is not in the registry
    - no ACTIVE prompt exists for role_id
    - prompt_version is missing
    - the prompt markdown file does not exist
    """
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")

    prompts = registry.get("prompts", [])
    matching = [p for p in prompts if p.get("role_id") == role_id]

    if not matching:
        raise PromptResolutionError(f"role_id '{role_id}' no encontrado en agent_prompt_registry")

    active = [p for p in matching if p.get("status") == "ACTIVE"]
    if not active:
        raise PromptResolutionError(
            f"No hay prompt ACTIVE para role_id '{role_id}'. "
            f"Status encontrado(s): {[p.get('status') for p in matching]}"
        )

    if len(active) > 1:
        raise PromptResolutionError(
            f"Multiples prompts ACTIVE para role_id '{role_id}'"
        )

    entry = active[0]
    version = entry.get("prompt_version")
    if not version:
        raise PromptResolutionError(f"prompt_version ausente para role_id '{role_id}'")

    prompt_path = ROOT / "prompts" / "roles" / role_id / f"{version}.md"
    if not prompt_path.exists():
        raise PromptResolutionError(
            f"Prompt file no encontrado: {prompt_path} (version={version})"
        )

    return entry


def resolve_runtime(role_id: str, runtime_config_path: str | Path | None = None) -> dict[str, Any]:
    """Resolve a role runtime from an explicitly supplied configuration path.

    The ``ai_runtime.example.json`` file is a template only and is never
    selected implicitly. A missing or invalid explicit path blocks resolution.
    """
    if runtime_config_path is None:
        raise ConfigResolutionError(
            "Debe proporcionarse explícitamente una ruta de configuración runtime real"
        )

    config_path = Path(runtime_config_path)
    if config_path.name.endswith('.example.json'):
        raise ConfigResolutionError(
            "La configuración .example.json es solo una plantilla, no un runtime"
        )
    if not config_path.exists():
        raise ConfigResolutionError(f"Configuración runtime no encontrada: {config_path}")

    try:
        config = _read_json(config_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ConfigResolutionError(
            f"Configuración runtime inválida: {config_path}"
        ) from exc

    entries = config.get("entries", [])
    matching = [entry for entry in entries if entry.get("role_id") == role_id]
    if not matching:
        raise ConfigResolutionError(
            f"role_id '{role_id}' no encontrado en configuración runtime"
        )
    if len(matching) > 1:
        raise ConfigResolutionError(
            f"Múltiples entradas runtime para role_id '{role_id}'"
        )
    return matching[0]


def resolve_execution(
    role_id: str, runtime_config_path: str | Path | None = None
) -> dict[str, Any]:
    """Resolve prompt content and runtime without invoking external services."""
    prompt_contract = resolve_prompt(role_id)
    runtime_entry = resolve_runtime(role_id, runtime_config_path)
    prompt_path = (
        ROOT / "prompts" / "roles" / role_id / f"{prompt_contract['prompt_version']}.md"
    )
    prompt_content = prompt_path.read_text(encoding="utf-8")
    prompt_checksum = hashlib.sha256(prompt_content.encode("utf-8")).hexdigest()

    return {
        "role_id": role_id,
        "prompt_contract": prompt_contract,
        "prompt_path": str(prompt_path),
        "prompt_content": prompt_content,
        "prompt_checksum": prompt_checksum,
        "runtime": runtime_entry,
        "adapter": runtime_entry.get("adapter", "unknown"),
    }
